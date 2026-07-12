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
    List the recipes you can craft.

    Usage:
      recipes

    Shows the common recipes everyone can make plus any advanced recipes
    you have personally learned. A skill note (needs Craft N%) marks recipes
    with a hard skill floor. If the world holds crafts you have not yet
    learned, a faint hint says so -- but not what they are. Seek them out.
    """

    key = "recipes"
    aliases = ["recipe"]
    locks = "cmd:all()"
    help_category = "Crafting"

    # Tuning flag (Component C.1). Default off preserves the mystery: the hint
    # tells the player advanced crafts EXIST without leaking how many remain.
    # Flip to True during playtest/balance to surface the exact hidden count.
    SHOW_HIDDEN_COUNT = False

    def func(self):
        caller = self.caller

        # Populate the contrib's module-level registry (idempotent -- it only
        # loads once and caches; read-only here so no multiplayer race on the
        # single-threaded reactor). We iterate the *classes*, reading class
        # attributes (name / requires_knowledge / min_skill) -- no instances.
        _load_recipes()

        common = []
        known = []
        hidden = 0

        for cls in _RECIPE_CLASSES.values():
            # Defensive skip of the abstract base sentinel. It should never be
            # in the registry -- callables_from_module filters imports by
            # __module__, and our shared helpers are plain functions rather
            # than MongooseCraftRecipe subclasses -- but this keeps the list
            # honest if a future local helper-subclass ever leaks in.
            name = getattr(cls, "name", "")
            if not name or name == "mongoose craft base":
                continue

            if not getattr(cls, "requires_knowledge", False):
                common.append(cls)
            elif getattr(caller, "knows_recipe", None) and caller.knows_recipe(name):
                known.append(cls)
            else:
                # Advanced + not learned (or -- defensively -- a caller with no
                # knows_recipe helper, which never happens for a puppeted
                # Character): counted, never named.
                hidden += 1

        # known_recipes()/registry order is unspecified; sort for a stable,
        # scannable display (mirrors CmdSkills sorting its keys).
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

        if hidden > 0:
            if self.SHOW_HIDDEN_COUNT:
                plural = "craft" if hidden == 1 else "crafts"
                lines.append(
                    f"|xWhispers speak of {hidden} {plural} beyond your knowing.|n"
                )
            else:
                lines.append("|xWhispers speak of crafts beyond your knowing.|n")

        caller.msg("\n".join(lines))
