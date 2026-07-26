"""
Knowledge-aware crafting commands (Stage 3, Component B.2).

CmdCraftGated overrides the contrib's stock `craft` so an advanced recipe the
caller has not learned is rejected *before* the command hunts the inventory for
ingredients -- a kinder UX than letting them gather materials for a recipe they
cannot make. This is polish only: the authoritative enforcement lives in
MongooseCraftRecipe.pre_craft (Component B.1), which blocks every code path that
reaches craft() (this command, barter-craft, scripts), so if this early reject
is ever bypassed the backstop still consumes nothing.
"""

# Stdlib time, NOT world/gametime_utils: the teach-offer window (H.1) is a
# real-time window, like every cooldown in this module. gametime_utils is the
# source of truth for *in-game* time -- world processes that tick on their own
# (node regen, corpse decay, seasons) -- whereas this measures how long a human
# player has to answer. The cooldowns contrib itself is hardcoded to time.time(),
# so mixing clocks here would put TEACH_TIMEOUT and TEACH_COOLDOWN in different
# units and quietly make their documented invariant false.
import time

from evennia import Command
from evennia.contrib.game_systems.crafting.crafting import (
    CmdCraft,
    _load_recipes,
    _RECIPE_CLASSES,
)

from world.skillcheck import skill_check
from evennia.prototypes.spawner import spawn
from evennia.utils import logger

from world.knowledge import _can_transmit, render_recipe_detail

# Real-time seconds between reverse-engineering attempts (Component E.2). A
# conservative dev value: the disassemble roll is already destructive (the item
# is consumed win or lose), so this only paces the *attempts*, keeping the item
# channel from undercutting the paid scroll/teach channels. Tune once playtesting
# shows the real cadence -> docs/BACKLOG.md.
DISASSEMBLE_COOLDOWN = 300

# Real-time seconds between inscribe attempts (Component F.1). Conservative dev
# value; the material cost (a bolt of cloth) is the real economic throttle, so
# this only stops scroll-spam. Tune once playtesting shows the cadence ->
# docs/BACKLOG.md.
INSCRIBE_COOLDOWN = 60

# crafting_material tag-key consumed as the scroll's writing surface. MVP reuse
# of the existing (EXISTS) cloth material -- a woven/linen scroll -- rather than a
# new hide-derived parchment primitive, which would pull in the unbuilt tanning
# chain (leather is DECISION-status). Parchment deferred -> docs/BACKLOG.md.
INSCRIBE_MATERIAL_TAG = "cloth"

# --- Component G.2: book scribing -------------------------------------------

# Real-time seconds between scribe attempts (Component G.2). Conservative dev
# value: double INSCRIBE_COOLDOWN, since a book is the bulk, higher-value channel
# and should not be spun out as fast as a one-use scroll. The material cost
# (cloth x2 + twine) is the real economic throttle; this only stops book-spam.
# Tune once playtesting shows the cadence -> docs/BACKLOG.md.
SCRIBE_COOLDOWN = 120

# crafting_material tag-keys consumed to bind a book (Component G.2). Duplicates
# encode quantity, the same flat-list convention MongooseCraftRecipe.consumable_tags
# uses: two bolts of cloth for the pages, one length of twine to bind them. MVP
# reuse of EXISTS materials -- a hide-derived parchment/leather cover was the
# decomposition's first shape but pulls in the unbuilt tanning chain (leather is
# DECISION-status, parchment BLOCKED), so it is deferred -> docs/BACKLOG.md.
SCRIBE_MATERIAL_TAGS = ["cloth", "cloth", "twine"]

# Human-readable "2x cloth, 1x twine" for the shortfall message, computed once
# from SCRIBE_MATERIAL_TAGS so the message can never drift from the real cost.
# dict.fromkeys preserves first-seen order and de-dupes; .count gives the qty.
_SCRIBE_MATERIAL_NEEDED = ", ".join(
    f"{SCRIBE_MATERIAL_TAGS.count(t)}x {t}" for t in dict.fromkeys(SCRIBE_MATERIAL_TAGS)
)

# Flat permanent-Craft floor to scribe a BOOK, ON TOP of the per-recipe
# _can_transmit gate (Component G.2). A book is the bulk, durable knowledge-carrier,
# so authoring one asks a "professional" standing (Legend p.72-73, professional >=
# 50%) in addition to mastering each recipe it holds. Read as permanent .current
# (like _can_transmit), NOT effective .value: a fleeting buff must not confer the
# standing to author a lasting book. Tune -> docs/BACKLOG.md.
SCRIBE_MIN_CRAFT = 50

# Result-tier -> book START-condition (Component G.2). Mirrors the craft pipeline's
# QUALITY_BY_TIER shape (world/crafting_base.py) -- a critical adds crit_score on
# top -- but tuned as a WEAR axis, not item quality: success sits at 80 (not 100)
# so a critical's superior binding (100 + crit_score, the only tier reaching
# pristine-or-above) is a visible reward that buys extra studies before the book
# crumbles. The four values map cleanly onto DurableObject's condition colour bands
# (green > 66, yellow 33-66, red < 33), so `look` reads the binding quality at a
# glance. Tuning -> docs/BACKLOG.md.
SCRIBE_CONDITION_BY_TIER = {"critical": 100, "success": 80, "failure": 50, "fumble": 25}

# Per-tier flavour for a completed scribe, echoing how well the binding went (which
# is exactly what the start-condition encodes). Mirrors crafting_base's
# RESULT_MESSAGES in spirit -- feedback the player can feel.
SCRIBE_TIER_FLAVOUR = {
    "critical": "The binding is superb -- it will bear many readings.",
    "success": "It is soundly bound.",
    "failure": "The binding is rough; it will not last many readings.",
    "fumble": "The binding is shoddy -- it may barely survive a reading or two.",
}

# Wear points a single study spends from a book's condition (Component G.3). Flat
# per-lesson cost: the book's start-condition (set by scribe's roll) decides HOW
# MANY readers it can teach, and each study chips a fixed amount off. At 20, a
# soundly-bound book (success, condition 80) teaches 4 readers, a rough one
# (failure, 50) teaches 3, a shoddy one (fumble, 25) teaches 2, and a superior one
# (critical, 100+) teaches 5+ -- always more than a scroll's single reader, scaling
# with the binding quality. Conservative dev value (start stingy, loosen if
# playtest wants wider spread); tune -> docs/BACKLOG.md.
BOOK_WEAR_PER_STUDY = 20

# --- Component H.1: live teaching -------------------------------------------

# Real-time seconds a pending `teach` offer stays answerable (Component H.1).
# Short on purpose: an offer is a person standing in front of you saying "want me
# to show you?", not a contract. Deliberately in the same ballpark as the barter
# contrib's TRADE_TIMEOUT invite window, which is the same kind of two-party
# handshake. Tune -> docs/BACKLOG.md.
TEACH_TIMEOUT = 60

# Real-time seconds between teaching OFFERS (Component H.1). Teaching is free --
# no material, no roll -- so the cooldown is the whole economic and social
# throttle, and it is spent when the offer is SENT rather than when the lesson
# completes: an unsolicited offer is the only thing `teach` can push at an
# unwilling stranger, so that is what has to be rate-limited.
#
# INVARIANT: TEACH_COOLDOWN >= TEACH_TIMEOUT. That is what makes "one student at
# a time" (the MVP lock) structural rather than bookkeeping -- an old offer has
# always lapsed before a teacher may make a new one, so there is never more than
# one live offer per teacher and no second copy of the state to keep in sync.
# Preserve this relationship when tuning. Matches SCRIBE_COOLDOWN's cadence: a
# lesson is the bulk-transfer channel's live sibling. Tune -> docs/BACKLOG.md.
TEACH_COOLDOWN = 120


def _resolve_recipe(name):
    """
    Resolve a recipe *class* from a (lowercased) name the same way the contrib's
    module-level craft() does: exact key, else a unique `startswith`, else a
    unique substring `in` match. Returns the class or None (no instantiation --
    requires_knowledge and name are class attributes).

    NOTE: this duplicates ~5 lines of the contrib's matcher and reads its private
    _RECIPE_CLASSES/_load_recipes because the contrib exposes no public resolver.
    pre_craft (B.1) is the real backstop if this drifts; logged in docs/BACKLOG.md
    to consolidate once/if the contrib stabilises a public resolver API.
    """
    _load_recipes()
    cls = _RECIPE_CLASSES.get(name, None)
    if cls:
        return cls
    matches = [key for key in _RECIPE_CLASSES if key.startswith(name)]
    if not matches:
        matches = [key for key in _RECIPE_CLASSES if name in key]
    if len(matches) == 1:
        return _RECIPE_CLASSES[matches[0]]
    return None


class CmdCraftGated(CmdCraft):
    """
    Craft an item using ingredients and tools.

    Usage:
      craft <recipe> [from <ingredient>,...] [using <tool>, ...]

    Identical to the stock `craft`, but attempting an advanced recipe you have
    not learned is refused at once -- before the command searches your inventory
    for ingredients you would never get to use.
    """

    # key/locks/parse are inherited from CmdCraft; we only widen func().

    def func(self):
        caller = self.caller

        # parse() (inherited) has already populated self.recipe, lowercased.
        # Resolve the recipe the same way the contrib will, then reject early if
        # it is a learnable recipe this caller has not learned. If caller lacks
        # the knows_recipe helper (never true for a puppeted Character, but the
        # guard mirrors B.1's defensiveness), we fall through and let pre_craft
        # be the backstop rather than second-guessing here.
        if self.recipe:
            cls = _resolve_recipe(self.recipe)
            if (
                cls is not None
                and getattr(cls, "requires_knowledge", False)
                and getattr(caller, "knows_recipe", None)
                and not caller.knows_recipe(cls.name)
            ):
                caller.msg("You don't know how to make that.")
                return

        super().func()


class CmdRecipes(Command):
    """
    List the recipes you can craft, or inspect one in detail.

    Usage:
      recipes            - list common + learned recipes (hint if more exist)
      recipes <name>     - show one recipe's ingredients, tool and skill floor

    The bare list shows the common recipes everyone can make plus any advanced
    recipes you have personally learned. `recipes <name>` details a recipe you
    can see: its ingredients, whether a tool helps, any skill floor, and what it
    produces. Recipes you have not learned stay hidden -- their ingredients are
    part of what you learn, buy, or are taught.
    """

    key = "recipes"
    aliases = ["recipe"]
    locks = "cmd:all()"
    help_category = "Crafting"

    # Tuning flag (Component C.1). Default off preserves the mystery: the hint
    # says advanced crafts EXIST without leaking how many remain. Flip to True
    # during playtest/balance to surface the exact hidden count.
    SHOW_HIDDEN_COUNT = False

    def func(self):
        # `recipes` -> overview; `recipes <name>` -> one recipe's detail.
        # base Command leaves self.args raw (unstripped, unsplit), so normalise
        # here. Empty after strip -> list mode.
        name = self.args.strip().lower()
        if name:
            self._show_detail(name)
        else:
            self._show_list()

    # --- overview ------------------------------------------------------------
    def _show_list(self):
        caller = self.caller

        # Populate the contrib's module-level registry (idempotent; loads once
        # and caches). Read-only iteration over the *classes* -- no instances,
        # no state -- so no multiplayer race on the single-threaded reactor.
        _load_recipes()

        common = []
        known = []
        hidden = 0

        for cls in _RECIPE_CLASSES.values():
            # Defensive skip of the abstract base sentinel. It should never be
            # in the registry (callables_from_module filters imports by
            # __module__, and our shared helpers are plain functions, not
            # MongooseCraftRecipe subclasses), but this keeps the list honest
            # if a future local helper-subclass ever leaks in.
            rname = getattr(cls, "name", "")
            if not rname or rname == "mongoose craft base":
                continue

            if not getattr(cls, "requires_knowledge", False):
                common.append(cls)
            elif getattr(caller, "knows_recipe", None) and caller.knows_recipe(rname):
                known.append(cls)
            else:
                hidden += 1

        # Registry order is unspecified; sort for a stable, scannable display
        # (mirrors CmdSkills sorting its keys).
        common.sort(key=lambda c: c.name)
        known.sort(key=lambda c: c.name)

        lines = ["\n|wRecipes you can craft:|n", "|g" + "=" * 50 + "|n"]

        if not common and not known:
            lines.append("  You know no recipes yet.")
        else:
            for label, bucket in (("Common", common), ("Known", known)):
                if not bucket:
                    continue
                lines.append(f"  |w{label}|n")
                for cls in bucket:
                    floor = getattr(cls, "min_skill", 0) or 0
                    note = f" |x(needs Craft {floor}%)|n" if floor > 0 else ""
                    lines.append(f"    |y{cls.name}|n{note}")

        lines.append("|g" + "=" * 50 + "|n")
        lines.append("|xTip: 'recipes <name>' shows what a recipe needs.|n")

        if hidden > 0:
            if self.SHOW_HIDDEN_COUNT:
                plural = "craft" if hidden == 1 else "crafts"
                lines.append(
                    f"|xWhispers speak of {hidden} {plural} beyond your knowing.|n"
                )
            else:
                lines.append("|xWhispers speak of crafts beyond your knowing.|n")

        caller.msg("\n".join(lines))

    # --- detail --------------------------------------------------------------
    def _show_detail(self, name):
        caller = self.caller

        # _resolve_recipe (defined at module level, B.2) calls _load_recipes()
        # itself and mirrors the contrib's fuzzy match (exact -> startswith ->
        # unique substring). Returns the class or None.
        cls = _resolve_recipe(name)

        # Visibility gate -- mirror the list exactly. A recipe is visible if it
        # is common (ungated) or one this caller has learned. An advanced recipe
        # the caller has NOT learned is refused: we never reveal its ingredients,
        # because those are what the learn/buy/teach economy trades in.
        #
        # We DO name it in the refusal so a player who heard of it from a teacher
        # gets a clear nudge toward learning it. For zero existence-leak instead,
        # replace this branch's message with the "No recipe matches" one below.
        if cls is not None:
            rname = getattr(cls, "name", "")
            advanced = getattr(cls, "requires_knowledge", False)
            knows = (
                bool(getattr(caller, "knows_recipe", None))
                and caller.knows_recipe(rname)
            )
            if advanced and not knows:
                caller.msg(
                    f"You don't know the recipe for '{rname}'. "
                    "Seek someone who does."
                )
                return
        else:
            caller.msg(f"No recipe matches '{name}'.")
            return

        # Presentation extracted to world.knowledge.render_recipe_detail (F.3)
        # so `recipes <name>` and `look <scroll>` render from one place. The
        # visibility gate above stays here -- it is command policy, not layout.
        caller.msg(render_recipe_detail(cls))


class CmdDisassemble(Command):
    """
    Take a crafted item apart to try to learn how it was made.

    Usage:
      disassemble <item>
      salvage <item>

    Sacrifice a player-crafted item for a chance to work out its recipe. The
    item is destroyed whether you succeed or fail, so only take apart things
    you're willing to lose. Reverse-engineering only bites on player-crafted
    goods (a bought rival's garment teaches; loot and spawned items do not).
    Recipes everyone already knows, and ones you've already learned, can't be
    learned this way -- taking those apart is refused before anything breaks.
    """

    key = "disassemble"
    aliases = ["salvage"]
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller

        target_name = self.args.strip()
        if not target_name:
            caller.msg("Take what apart? (usage: |wdisassemble <item>|n)")
            return

        # Resolve among what the caller holds or wears; search() messages on a
        # miss or multimatch, so a falsy return just bails.
        target = caller.search(target_name, candidates=caller.contents)
        if not target:
            return

        # The recipe stamp (Component E.1). Only player-crafted output carries
        # it; spawned/loot/admin items leave db.recipe None. No stamp -> nothing
        # to learn, and nothing is destroyed.
        recipe_name = target.db.recipe
        if not recipe_name:
            caller.msg("You can't learn anything by taking this apart.")
            return

        # Resolve the stamped name to its recipe class by EXACT key: the stamp is
        # the canonical recipe name (self.name), so no fuzzy match is wanted here
        # (a prefix collision must not resolve a different recipe). A recipe that
        # has since been removed/renamed resolves to None -> treat as unlearnable
        # and DON'T destroy: no reason to burn an item for vanished knowledge.
        # (Reads the contrib's private registry, the same coupling _resolve_recipe
        # already carries -- logged in docs/BACKLOG.md.)
        _load_recipes()
        cls = _RECIPE_CLASSES.get(recipe_name)
        if cls is None:
            caller.msg("You can't learn anything by taking this apart.")
            return

        # Common (ungated) recipes, or ones already known, teach nothing new.
        # Refuse BEFORE destroying -- there's no reason to sacrifice the item.
        # (caller is always a puppeted Character here, so knows_recipe exists.)
        if not getattr(cls, "requires_knowledge", False) or caller.knows_recipe(recipe_name):
            caller.msg("You already know how these are made.")
            return

        # Anti-spam: one attempt per window. Checked only now -- the harmless
        # guards above never trip it -- and BEFORE any destruction, so a player
        # on cooldown keeps their item.
        if not caller.cooldowns.ready("disassemble"):
            left = caller.cooldowns.time_left("disassemble", use_int=True)
            caller.msg(
                f"Your hands are unsteady. Try taking something apart again in {left}s."
            )
            return

        # Difficulty scales with the recipe's skill floor: a negative modifier
        # makes an advanced recipe harder to reverse-engineer. min_skill defaults
        # to 0 (no penalty) -- read via the repo's getattr-with-default idiom.
        min_skill = getattr(cls, "min_skill", 0) or 0
        trait = caller.skills.get("craft")
        skill_value = trait.value if trait else 0     # counter .value = current + mod
        outcome = skill_check(skill_value, modifier=-min_skill)

        # Committed: the item is destroyed on every outcome and the cooldown set.
        # Capture the display name first (get_display_name needs a live object).
        # The single-threaded reactor makes read-roll-delete atomic against a
        # concurrent disassemble, and delete() runs exactly once.
        name = target.get_display_name(caller)
        target.delete()
        caller.cooldowns.add("disassemble", DISASSEMBLE_COOLDOWN)

        if outcome["success"]:
            caller.learn_recipe(recipe_name)
            caller.msg(
                f"You take the {name} apart and work out how it was made. "
                f"You now know the |y{recipe_name}|n recipe."
            )
            # Fifth on-use improvement check-site (Component B.3): route the
            # successful check through the gated path (success + cooldown gates
            # live inside attempt_skill_improvement). Placed after the result
            # message so a "your Crafting improves" line reads as the next beat.
            imp = caller.attempt_skill_improvement("craft", outcome)
            text = caller._improvement_feedback(imp)
            if text:
                caller.msg(text)
        else:
            caller.msg("The piece falls apart before you grasp how it was made.")


class CmdInscribe(Command):
    """
    Write a recipe you have mastered onto a scroll for another crafter.

    Usage:
      inscribe <recipe>

    Set a recipe you know well down as a one-use scroll. Another player can
    `learn` from the scroll to gain the recipe permanently -- the scroll is
    consumed in the reading. Writing one costs a bolt of cloth to inscribe on.

    You can only inscribe an advanced recipe you have learned AND are skilled
    enough to have mastered; the survival basics everyone already knows aren't
    worth writing down.
    """

    key = "inscribe"
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller

        recipe_input = self.args.strip()
        if not recipe_input:
            caller.msg("Inscribe which recipe? (usage: |winscribe <recipe>|n)")
            return

        # Resolve the typed name the same fuzzy way craft/recipes do (exact ->
        # prefix -> substring), so a prefix works. None -> no such recipe at all.
        cls = _resolve_recipe(recipe_input)
        if cls is None:
            caller.msg("You don't know of any recipe by that name.")
            return
        recipe_name = cls.name

        # Common (ungated) recipes are knowledge everyone already has -- nothing
        # to transmit. Distinct message from the mastery guard below.
        if not getattr(cls, "requires_knowledge", False):
            caller.msg("Everyone already knows this. There's nothing to inscribe.")
            return

        # Shared mastery gate (F/G/H): must KNOW it and meet its permanent-skill
        # floor. Collapses "haven't learned it" and "not skilled enough" into one
        # message on purpose -- both mean "you haven't mastered this".
        if not _can_transmit(caller, recipe_name):
            caller.msg("You can't inscribe a recipe you haven't mastered.")
            return

        # Anti-spam: checked only after the harmless guards, and BEFORE any
        # material is spent, so a player on cooldown keeps their cloth.
        if not caller.cooldowns.ready("inscribe"):
            left = caller.cooldowns.time_left("inscribe", use_int=True)
            caller.msg(
                f"Your hand is still cramped from the last one. Try again in {left}s."
            )
            return

        # Writing material: one inventory item carrying the crafting_material tag
        # we use as a writing surface (cloth by default). Matched by tag, the same
        # way the crafting contrib matches consumables -- robust to key/alias drift.
        material = next(
            (
                obj
                for obj in caller.contents
                if obj.tags.has(INSCRIBE_MATERIAL_TAG, category="crafting_material")
            ),
            None,
        )
        if material is None:
            caller.msg(
                f"You need a bolt of {INSCRIBE_MATERIAL_TAG} to inscribe a scroll on."
            )
            return

        # Commit. Spawn the scroll FIRST; consume the material only once the
        # scroll exists, so a spawn failure never eats the cloth. spawn/move_to/
        # delete run under the single-threaded reactor -> atomic against a
        # concurrent inscribe, and delete() runs exactly once.
        try:
            scroll = spawn("scroll")[0]
        except Exception:
            logger.log_trace()
            caller.msg("The inscription smears and fails; nothing is lost.")
            return

        material.delete()
        # stamp() owns the scroll's identity (recipe + searchable key); flavour
        # and the readable detail render live from the stamp in the Scroll
        # typeclass (F.4), so we set nothing else here.
        scroll.stamp(recipe_name)
        scroll.move_to(caller, quiet=True)

        caller.cooldowns.add("inscribe", INSCRIBE_COOLDOWN)
        caller.msg(
            f"You carefully inscribe the |y{recipe_name}|n recipe onto a scroll."
        )


class CmdScribe(Command):
    """
    Compile several recipes you have mastered into a book for other crafters.

    Usage:
      scribe <recipe>, <recipe>[, ...]
      scribe book of <recipe>, <recipe>[, ...]

    Bind a set of recipes you know well into a single book. Another player can
    `learn <recipe> from <book>` to gain a recipe permanently -- each study wears
    the book down a little, and it finally crumbles once it is used up. A book is
    the bulk, durable sibling of the one-use scroll: it holds MANY recipes and
    teaches MANY readers.

    You can only scribe advanced recipes you have learned AND are skilled enough
    to have mastered, and binding a book asks a professional's hand. It costs two
    bolts of cloth for the pages and a length of twine to bind them.
    """

    key = "scribe"
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller

        raw = self.args.strip()
        if not raw:
            caller.msg("Scribe which recipes? (usage: |wscribe <recipe>, <recipe>|n)")
            return

        # Accept the decomposition's documented `scribe book of <list>` form too.
        # stamp() owns the "book of " key prefix, so the user need only name the
        # recipes; stripping an optional leading "book of " keeps the longer
        # phrasing working, mirroring CmdLearn accepting `learn from <scroll>`.
        if raw.lower().startswith("book of "):
            raw = raw[8:].strip()

        # Parse the comma-separated list; drop empties so a trailing/double comma
        # does not create a blank entry.
        typed = [part.strip() for part in raw.split(",") if part.strip()]
        if not typed:
            caller.msg("Scribe which recipes? (usage: |wscribe <recipe>, <recipe>|n)")
            return

        # Resolve + validate EVERY entry before consuming anything, so one bad name
        # costs no material. Preserve author order and DE-DUPLICATE (a book listing
        # the same recipe twice is nonsense and would double it in the key).
        recipe_names = []
        for name in typed:
            cls = _resolve_recipe(name)
            if cls is None:
                caller.msg(f"You don't know of any recipe called '{name}'.")
                return
            # Common (ungated) recipes are knowledge everyone already has -- nothing
            # to bind into a book. Same distinction inscribe draws.
            if not getattr(cls, "requires_knowledge", False):
                caller.msg(
                    f"Everyone already knows |w{cls.name}|n -- there's nothing to scribe there."
                )
                return
            # Per-recipe mastery gate (shared with inscribe/teach): you must KNOW
            # each recipe and meet its permanent-skill floor to write it down.
            if not _can_transmit(caller, cls.name):
                caller.msg(f"You can't scribe |w{cls.name}|n -- you haven't mastered it.")
                return
            if cls.name not in recipe_names:
                recipe_names.append(cls.name)

        # Book-specific floor ON TOP of the per-recipe gate. Read permanent .current
        # (not effective .value), like _can_transmit: a fleeting buff must not confer
        # the standing to author a lasting book.
        trait = caller.skills.get("craft")
        craft_current = trait.current if trait else 0
        if craft_current < SCRIBE_MIN_CRAFT:
            caller.msg(
                f"Binding a book asks a steadier hand -- you need Craft "
                f"{SCRIBE_MIN_CRAFT}% to scribe one."
            )
            return

        # Anti-spam: after the harmless guards and BEFORE any material is spent, so
        # a player on cooldown keeps their cloth and twine.
        if not caller.cooldowns.ready("scribe"):
            left = caller.cooldowns.time_left("scribe", use_int=True)
            caller.msg(
                f"Your hand is still cramped from the last binding. Try again in {left}s."
            )
            return

        # Gather writing materials by tag (robust to key/alias drift, like inscribe
        # and the crafting contrib). Duplicates in SCRIBE_MATERIAL_TAGS encode
        # quantity, so we claim a DISTINCT object per required instance. Check ALL
        # are present BEFORE consuming ANY: the single-threaded reactor makes this
        # gather-then-consume atomic against a concurrent scribe -- no dupe, no
        # partial loss.
        to_consume = []
        for tag in SCRIBE_MATERIAL_TAGS:
            material = next(
                (
                    obj
                    for obj in caller.contents
                    if obj.tags.has(tag, category="crafting_material")
                    and obj not in to_consume
                ),
                None,
            )
            if material is None:
                caller.msg(f"You need {_SCRIBE_MATERIAL_NEEDED} to scribe a book.")
                return
            to_consume.append(material)

        # Roll the author's Craft to set the book's start-condition. Effective skill
        # (.value = current + mod), mirroring do_craft: a tool/situational buff can
        # lift the binding's QUALITY even though the .current gate above governs
        # PERMISSION. No tool modifier -- there is no scribing implement in the MVP
        # (a quill/pen tool is a future addition), so the roll is unmodified.
        skill_value = trait.value if trait else 0
        outcome = skill_check(skill_value)
        tier = outcome["result"]
        condition = SCRIBE_CONDITION_BY_TIER.get(tier, 50)
        if tier == "critical":
            condition += outcome["crit_score"]

        # Commit. Spawn the book FIRST; consume materials only once it exists, so a
        # spawn failure eats nothing. spawn/delete/stamp/move_to all run under the
        # single-threaded reactor -> atomic against a concurrent scribe, and each
        # delete() runs exactly once.
        try:
            book = spawn("book")[0]
        except Exception:
            logger.log_trace()
            caller.msg("The binding falls apart in your hands; nothing is lost.")
            return

        for material in to_consume:
            material.delete()

        # stamp() owns the book's identity (recipe list + searchable key); the
        # start-condition is scribe's to set (G.1 deliberately left it unset), so we
        # set it AFTER stamp. condition is a raw-int AttributeProperty -- assign it
        # directly (NOT .current).
        book.stamp(recipe_names)
        book.condition = condition
        book.move_to(caller, quiet=True)

        caller.cooldowns.add("scribe", SCRIBE_COOLDOWN)
        listed = ", ".join(recipe_names)
        tail = SCRIBE_TIER_FLAVOUR.get(tier, "")
        caller.msg(f"You bind a book of |y{listed}|n. {tail}".rstrip())


class CmdTeach(Command):
    """
    Offer to teach a recipe you have mastered to another crafter.

    Usage:
      teach <recipe> to <player>

    Pass a recipe on face to face. A lesson costs nothing but time -- no
    materials, no roll -- but the other person has to be in the room with you
    and has to agree: they answer with `learn <recipe> from <you>` before the
    offer lapses. Nobody can have knowledge pushed on them.

    You can only teach an advanced recipe you have learned AND are skilled
    enough to have mastered; the survival basics everyone already knows aren't
    worth a lesson.
    """

    key = "teach"
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller

        raw = self.args.strip()
        if not raw:
            caller.msg("Teach what, to whom? (usage: |wteach <recipe> to <player>|n)")
            return

        # rpartition, not partition: split on the LAST " to ", so a multi-word
        # recipe could contain the separator without eating the student's name.
        recipe_input, sep, student_name = raw.rpartition(" to ")
        recipe_input, student_name = recipe_input.strip(), student_name.strip()
        if not sep or not recipe_input or not student_name:
            caller.msg("Teach what, to whom? (usage: |wteach <recipe> to <player>|n)")
            return

        # Resolve the typed name the same fuzzy way craft/recipes/inscribe do
        # (exact -> prefix -> substring). None -> no such recipe at all.
        cls = _resolve_recipe(recipe_input)
        if cls is None:
            caller.msg("You don't know of any recipe by that name.")
            return
        recipe_name = cls.name

        # Common (ungated) recipes are knowledge everyone already has -- there is
        # no lesson to give. Same distinction inscribe and scribe draw.
        if not getattr(cls, "requires_knowledge", False):
            caller.msg("Everyone already knows this. There's nothing to teach.")
            return

        # Shared mastery gate (F/G/H): must KNOW it and meet its permanent-skill
        # floor. NOTE the Teaching *skill* is deliberately NOT consulted -- Legend
        # p.72-73 treats Teaching as an amplifier, never a gate (decomposition
        # section 2(d)); a Teaching bonus is deferred -> docs/BACKLOG.md.
        if not _can_transmit(caller, recipe_name):
            caller.msg("You can't teach a recipe you haven't mastered.")
            return

        # Same-room requirement, enforced implicitly: Object.search defaults to
        # location.contents + self.contents, so a target in another room simply
        # is not found (and search emits its own miss/multimatch message).
        student = caller.search(student_name)
        if not student:
            return
        if student == caller:
            caller.msg("You know it well enough already.")
            return
        # A teachable target is a *played* character: has_account is truthy only
        # while a session is connected, and learn_recipe is the Character-side
        # knowledge chokepoint. Together they reject objects, NPCs and idle
        # unpuppeted bodies with one honest message.
        if not (student.has_account and hasattr(student, "learn_recipe")):
            caller.msg(
                f"{student.get_display_name(caller)} isn't someone you can teach."
            )
            return

        # We deliberately do NOT check whether the student already knows the
        # recipe here. Their known-set is their own business -- probing it via
        # teach would turn the command into a "who knows what" scanner, which is
        # real intelligence in a knowledge economy. They find out at accept time.

        # Anti-spam, checked before the offer is sent: an unsolicited offer is the
        # only thing `teach` can push at a stranger, so the cooldown has to gate
        # the OFFER, not the completed lesson.
        if not caller.cooldowns.ready("teach"):
            left = caller.cooldowns.time_left("teach", use_int=True)
            caller.msg(f"You've only just finished a lesson. Try again in {left}s.")
            return

        # Commit the offer. It lives on the STUDENT (they are the one who must
        # answer, so the accept path finds it in O(1) on self) and in ndb, not db:
        # a pending offer is session state and must not survive a reload, the same
        # reason barter keeps its handler on ndb.tradehandler. A fresh offer simply
        # overwrites any older one to the same student.
        student.ndb.pending_teach = (caller, recipe_name, time.time() + TEACH_TIMEOUT)

        # The cooldown lands here, and since TEACH_COOLDOWN >= TEACH_TIMEOUT a
        # teacher structurally has at most ONE live offer out at a time -- the MVP
        # "one student at a time" rule, with no second copy of the state to keep
        # in sync.
        caller.cooldowns.add("teach", TEACH_COOLDOWN)

        caller.msg(
            f"You offer to teach {student.get_display_name(caller)} the "
            f"|y{recipe_name}|n recipe. They have {TEACH_TIMEOUT}s to take you up on it."
        )
        student.msg(
            f"{caller.get_display_name(student)} offers to teach you the "
            f"|y{recipe_name}|n recipe. Answer with "
            f"|wlearn {recipe_name} from {caller.key}|n within {TEACH_TIMEOUT}s."
        )


class CmdLearn(Command):
    """
    Study inscribed knowledge, or take a lesson, and learn a recipe.

    Usage:
      learn <scroll>
      learn from <scroll>
      learn <recipe> from <book>
      learn <recipe> from <teacher>

    A scroll carries one recipe and is used up in the studying, passing its
    knowledge to exactly one person. A book carries many recipes and wears down a
    little with each study, teaching several readers before its binding finally
    gives out -- name which recipe you want with `learn <recipe> from <book>`.

    A living teacher is the third source: once someone has offered to `teach` you
    something, this is how you accept. The offer lapses quickly, and both of you
    must still be in the same room when you take it up.
    """

    key = "learn"
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller

        raw = self.args.strip()
        if not raw:
            caller.msg(
                "Study what? (usage: |wlearn <scroll>|n, or |wlearn <recipe> from <book>|n)"
            )
            return

        # Two syntaxes share this command:
        #   scroll:  `learn <scroll>` / `learn from <scroll>`   (F.2/F.3, unchanged)
        #   book:    `learn <recipe> from <book>`               (G.3)
        # A book holds MANY recipes, so the book form names WHICH recipe BEFORE
        # "from". The scroll's `learn from <scroll>` has nothing before "from", so
        # we distinguish on "is there text to the LEFT of a ' from ' separator".
        recipe_request = None
        if " from " in raw:
            left, _, right = raw.partition(" from ")
            if left.strip():
                recipe_request = left.strip()
                target_name = right.strip()
            else:
                target_name = right.strip()
        else:
            target_name = raw
            if target_name.lower().startswith("from "):
                target_name = target_name[5:].strip()

        if not target_name:
            caller.msg(
                "Study what? (usage: |wlearn <scroll>|n, or |wlearn <recipe> from <book>|n)"
            )
            return

        # A living teacher is the third knowledge carrier (H.1), and the only one
        # that is not an object in the student's hands. Check for a pending offer
        # BEFORE the carrier search below, which is inventory-scoped and would
        # emit its own "could not find" for a teacher standing in the room.
        # Returns True only when the input really was a teaching handshake, so a
        # `learn cloth from tome` still finds the book while an offer is pending.
        if self._learn_from_teacher(caller, recipe_request, target_name):
            return

        # Must have the carrier in hand to study it. search() messages on a miss or
        # multimatch, so a falsy return just bails.
        target = caller.search(target_name, candidates=caller.contents)
        if not target:
            return

        # A book carries db.recipes (a LIST, G.1); a scroll carries db.recipe (a
        # single name) and leaves db.recipes None. Branch on that: the book path is
        # G.3, the scroll path below is F.2/F.3 verbatim.
        book_recipes = target.db.recipes
        if book_recipes is not None:
            self._learn_from_book(caller, target, book_recipes, recipe_request)
            return

        # The recipe stamp. Written by `inscribe` (F.1) onto the scroll instance;
        # a blank/uninscribed scroll leaves it None. Nothing is consumed here.
        recipe_name = target.db.recipe
        if not recipe_name:
            caller.msg("There's nothing to learn from that.")
            return

        # Resolve the stamped name by EXACT key: the stamp is the canonical recipe
        # name (self.name), so no fuzzy match is wanted (a prefix collision must
        # not resolve a different recipe). A recipe since removed/renamed resolves
        # to None -> nothing to learn, and the scroll is NOT consumed: no reason to
        # burn it for vanished knowledge. (Reads the contrib's private registry --
        # the same coupling _resolve_recipe and CmdDisassemble already carry,
        # logged in docs/BACKLOG.md.)
        _load_recipes()
        cls = _RECIPE_CLASSES.get(recipe_name)
        if cls is None:
            caller.msg("There's nothing to learn from that.")
            return

        # Common (ungated) recipes are knowledge everyone already has. `inscribe`
        # refuses to write one, so this only bites on a hand-stamped or seeded
        # scroll -- but the guard is what keeps the known-set's invariant intact:
        # it holds ADVANCED recipes only, so tagging a common one here would
        # double-list it in `recipes`. Refuse BEFORE learn_recipe tags anything,
        # and don't consume.
        if not getattr(cls, "requires_knowledge", False):
            caller.msg("Everyone already knows this. There's nothing to learn.")
            return

        # learn_recipe is the single chokepoint and returns False when the recipe
        # was ALREADY known -- that signal is exactly why we can be kind here and
        # leave the scroll intact for someone who can still use it. Read-then-write
        # on the tag set, serialised safely by the single-threaded reactor.
        if not caller.learn_recipe(recipe_name):
            caller.msg("You already know this recipe. You set the scroll aside, unread.")
            return

        # Committed: the knowledge is tagged, so the scroll is spent. Capture the
        # display name first (get_display_name needs a live object); delete() runs
        # exactly once, atomically against a concurrent learn.
        name = target.get_display_name(caller)
        target.delete()

        caller.msg(
            f"You study the {name} and commit the |y{recipe_name}|n recipe to "
            "memory. Its work done, the scroll crumbles away."
        )

    def _learn_from_teacher(self, caller, recipe_request, target_name):
        """Accept a pending `teach` offer from a live teacher (Component H.1).

        The offer was parked on THIS character by CmdTeach as
        ndb.pending_teach = (teacher, recipe_name, expires_at). Accepting it is
        the student's half of the consent handshake: knowledge only ever moves
        because both parties typed something.

        Everything CmdTeach checked when the offer went out is re-checked here,
        because the world moved in between -- this is the barter finish() lesson
        (world/barter.py): a handshake that validates only at offer time will
        happily complete against a teacher who has since walked out of the room.

        Args:
            caller (Character): the student, i.e. the one accepting.
            recipe_request (str | None): text left of " from ", or None for the
                `learn from <teacher>` form.
            target_name (str): text right of " from " -- who/what to study.

        Returns:
            bool: True if the input was handled as a teaching handshake (taught,
                or refused with a message). False to fall through to the
                scroll/book carrier search.
        """
        pending = caller.ndb.pending_teach
        if not pending:
            return False

        teacher, recipe_name, expires_at = pending

        # A deleted teacher leaves a dangling reference that cannot be name-matched
        # at all. Drop the offer and fall through rather than raising on it.
        if not teacher or not teacher.pk:
            caller.ndb.pending_teach = None
            return False

        # Does the typed name actually mean the teacher? Let the engine's own
        # matcher decide, over a single candidate and quietly, so a non-match says
        # nothing and simply falls through to the scroll/book path.
        if not caller.search(target_name, candidates=[teacher], quiet=True):
            return False

        # Backstop re-validation. Lapsed, teacher gone from the room, or teacher
        # logged out -> the lesson quietly does not happen. We still tell the
        # STUDENT, who just typed a command and is owed an answer; what we do not
        # do is announce anything to the room or half-apply the transfer.
        if (
            time.time() > expires_at
            or teacher.location != caller.location
            or not teacher.has_account
        ):
            caller.ndb.pending_teach = None
            caller.msg("That lesson has lapsed.")
            return True

        # `learn from <teacher>` (no recipe named) takes the one thing on offer.
        # Naming a DIFFERENT recipe is a typo, not a second offer -- say so rather
        # than silently teaching something else.
        if recipe_request and recipe_request.lower() != recipe_name.lower():
            caller.msg(
                f"{teacher.get_display_name(caller)} offered to teach you "
                f"|w{recipe_name}|n, not |w{recipe_request}|n."
            )
            return True

        # Resolve the offered name by EXACT key (same discipline as the scroll and
        # book paths -- it is a canonical name, never user input). A recipe removed
        # or turned common since the offer went out is no longer transmissible, and
        # the common-guard is what keeps the known-set's "advanced recipes only"
        # invariant intact.
        _load_recipes()
        cls = _RECIPE_CLASSES.get(recipe_name)
        if cls is None or not getattr(cls, "requires_knowledge", False):
            caller.ndb.pending_teach = None
            caller.msg("There's nothing to learn there.")
            return True

        # The teacher must STILL be qualified to pass this on -- the same shared
        # gate CmdTeach applied, re-run against the live teacher (permanent
        # .current inside _can_transmit, never buffed .value).
        if not _can_transmit(teacher, recipe_name):
            caller.ndb.pending_teach = None
            caller.msg(f"{teacher.get_display_name(caller)} can't teach you that.")
            return True

        # The offer has now been answered either way, so retire it BEFORE the
        # transfer: that makes a second accept a no-op instead of a re-run, and on
        # the single-threaded reactor no other command can interleave between this
        # clear and the tag write below.
        caller.ndb.pending_teach = None

        # learn_recipe is the single chokepoint and returns False when the recipe
        # was ALREADY known. Nothing is consumed by a lesson, so an already-known
        # recipe costs nobody anything -- we just say so to both sides.
        if not caller.learn_recipe(recipe_name):
            caller.msg("You already know this recipe. The lesson is a pleasant one anyway.")
            teacher.msg(
                f"{caller.get_display_name(teacher)} already knows |y{recipe_name}|n."
            )
            return True

        caller.msg(
            f"{teacher.get_display_name(caller)} walks you through the "
            f"|y{recipe_name}|n recipe until it sticks. You have learned it."
        )
        teacher.msg(
            f"You teach {caller.get_display_name(teacher)} the |y{recipe_name}|n recipe."
        )
        return True

    def _learn_from_book(self, caller, book, book_recipes, recipe_request):
        """Study one recipe out of a multi-recipe book (Component G.3).

        The reader names WHICH recipe (`learn <recipe> from <book>`). On a
        successful study the recipe becomes theirs and the book wears down by
        BOOK_WEAR_PER_STUDY; the study that spends the last of the binding still
        COMPLETES (the reader keeps the recipe) and only THEN does the book crumble
        -- the locked complete-then-crumble rule, so no empty husk lingers. A
        recipe the reader already knows, or one the book does not hold, wears
        nothing.
        """
        if recipe_request is None:
            held = ", ".join(book_recipes) if book_recipes else "nothing"
            caller.msg(
                "Which recipe? (usage: |wlearn <recipe> from <book>|n). "
                f"That book holds: {held}."
            )
            return

        # Match the request against the book's contents. Case-insensitive: recipe
        # names are canonical-lowercase, but a reader may type any case.
        wanted = recipe_request.lower()
        match = next((r for r in book_recipes if r.lower() == wanted), None)
        if match is None:
            held = ", ".join(book_recipes) if book_recipes else "nothing"
            caller.msg(
                f"That book doesn't hold a |w{recipe_request}|n recipe. It holds: {held}."
            )
            return

        # Resolve the canonical class by EXACT key (same discipline as the scroll
        # path). A recipe removed/renamed since the book was scribed resolves to
        # None -> nothing to learn, and the book is NOT worn: no reason to spend a
        # study on vanished knowledge.
        _load_recipes()
        cls = _RECIPE_CLASSES.get(match)
        if cls is None:
            caller.msg("There's nothing to learn from that.")
            return

        # Books are only scribed from advanced recipes (scribe enforces
        # requires_knowledge), so this only bites a hand-stamped/seeded book -- but
        # it keeps the known-set's "advanced only" invariant. Refuse before tagging,
        # and don't wear.
        if not getattr(cls, "requires_knowledge", False):
            caller.msg("Everyone already knows this. There's nothing to learn.")
            return

        # Already known -> be kind, wear nothing, leave the book for the next reader
        # (parity with the scroll's "set aside, unread").
        if not caller.learn_recipe(match):
            caller.msg(
                "You already know this recipe. You leaf past it, leaving the book untouched."
            )
            return

        # Committed: the lesson took, so it costs the binding one study. Capture the
        # display name while the book is live, wear it, then decide survival. Per
        # complete-then-crumble the reader KEEPS the recipe regardless; we only
        # decide whether the book survives. apply_wear floors at 0 and logs the
        # break; is_broken reads condition <= 0. delete() runs exactly once, atomic
        # against a concurrent study on the single-threaded reactor.
        name = book.get_display_name(caller)
        book.apply_wear(BOOK_WEAR_PER_STUDY)
        if book.is_broken:
            book.delete()
            caller.msg(
                f"You study the {name} and commit the |y{match}|n recipe to memory. "
                "The worn binding gives out as you close it, and the book crumbles away."
            )
        else:
            caller.msg(
                f"You study the |y{match}|n recipe from the {name}, committing it to "
                "memory. The book is more thumbed for it."
            )
