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

from collections import Counter

from evennia import Command
from evennia.contrib.game_systems.crafting.crafting import (
    CmdCraft,
    _load_recipes,
    _RECIPE_CLASSES,
)

from world.skillcheck import skill_check

# Real-time seconds between reverse-engineering attempts (Component E.2). A
# conservative dev value: the disassemble roll is already destructive (the item
# is consumed win or lose), so this only paces the *attempts*, keeping the item
# channel from undercutting the paid scroll/teach channels. Tune once playtesting
# shows the real cadence -> docs/BACKLOG.md.
DISASSEMBLE_COOLDOWN = 300

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

        # Ingredients: consumable_tags is a flat list where duplicates encode
        # quantity (["fiber","fiber","fiber"] -> 3x fiber). Counter preserves
        # first-seen order (py3.7+), so display order matches declaration order.
        tags = list(getattr(cls, "consumable_tags", []) or [])
        if tags:
            counts = Counter(tags)
            needs = ", ".join(f"{qty}x {tag}" for tag, qty in counts.items())
        else:
            needs = "nothing"

        # Tool: a single optional tag or None. Tools are never hard-required --
        # absence only costs the -20 improvised modifier -- so we say "optional".
        tool_tag = getattr(cls, "tool_tag", None)
        tool = (
            f"{tool_tag} (optional; improvising takes a penalty)"
            if tool_tag
            else "none needed"
        )

        floor = getattr(cls, "min_skill", 0) or 0
        skill = f"Craft {floor}% minimum" if floor > 0 else "no minimum"

        # Output: output_prototypes holds prototype KEYS, not display names.
        # Prettify the key (underscores -> spaces) for now; resolving the
        # prototype's real key/desc and correct article/pluralisation (e.g.
        # "a pair of leather boots") is deferred -> docs/BACKLOG.md.
        outputs = list(getattr(cls, "output_prototypes", []) or [])
        produced = ", ".join(o.replace("_", " ") for o in outputs) if outputs else "something"

        lines = [
            f"\n|w{cls.name.title()}|n",
            "|g" + "=" * 50 + "|n",
            f"  |wNeeds:|n   {needs}",
            f"  |wTool:|n    {tool}",
            f"  |wSkill:|n   {skill}",
            f"  |wOutput:|n  {produced}",
            "|g" + "=" * 50 + "|n",
        ]
        caller.msg("\n".join(lines))


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
