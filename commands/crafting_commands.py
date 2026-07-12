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
