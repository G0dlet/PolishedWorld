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


class CmdLearn(Command):
    """
    Study an inscribed scroll and learn the recipe written on it.

    Usage:
      learn <scroll>
      learn from <scroll>

    Read the craft-notes on a scroll closely enough to keep them. The recipe
    becomes yours permanently and the scroll is used up in the studying, so a
    scroll passes knowledge to exactly one person.

    Learning a recipe is not the same as being able to make it: an advanced
    recipe may also demand a level of Craft you have yet to reach. Look at a
    scroll before you study it to see what it asks of you.
    """

    key = "learn"
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller

        target_name = self.args.strip()
        # Accept the natural-language form too: `learn from <scroll>`.
        if target_name.lower().startswith("from "):
            target_name = target_name[5:].strip()

        if not target_name:
            caller.msg("Study what? (usage: |wlearn <scroll>|n)")
            return

        # Resolve among what the caller holds -- you must have the scroll in hand
        # to study it. search() messages on a miss or multimatch, so a falsy
        # return just bails.
        target = caller.search(target_name, candidates=caller.contents)
        if not target:
            return

        # The recipe stamp. Written by `inscribe` (F.1) onto the scroll instance;
        # a blank/uninscribed scroll leaves it None. Nothing is consumed here.
        # (Component G.3 extends this command to books, which carry MANY recipes;
        # that lands as a branch here -- read the book's recipe list, pick one,
        # wear the book instead of deleting it. The single-recipe scroll path
        # below stays as-is.)
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
