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
