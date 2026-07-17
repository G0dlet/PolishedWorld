"""
Shared recipe-knowledge transmission gate (Stage 3, Component F).

The written and taught knowledge channels -- `inscribe` (F, scroll), `scribe`
(G, book) and `teach` (H, live) -- all answer the same question before they let
a character pass a recipe on: *are you actually qualified to teach this one?*
Rather than copy that rule into three commands, it lives here once.

The rule (locked in the decomposition, section 2 "Delad behorighets-regel"):

    a character may transmit a recipe iff they KNOW it AND their PERMANENT
    Craft skill meets the recipe's min_skill floor.

Two deliberate choices:

* Permanent skill (`trait.current`), NOT effective `trait.value`. `.value`
  folds in situational `.mod` -- a +20 tool buff, say -- and a fleeting buff
  must not confer the standing to author a lasting scroll. This mirrors
  Character.improve_skill_on_use, which reads/writes `.current` for exactly the
  same "permanent competence, not momentary boost" reason.

* A pure threshold, no roll. Mastery is a gate, not a gamble: if you meet the
  bar you always succeed at *writing it down* (the reader still needs the skill
  to craft from it). This matches the Legend "professional teacher" flavour
  (Legend.pdf p.72-73) without importing the Teaching skill as a gate (Teaching
  is an amplifier, deferred to BACKLOG).

Coupling note: `_can_transmit` reads the crafting contrib's private
`_RECIPE_CLASSES` registry (via `_load_recipes()` + an exact `.get`), the same
coupling `_resolve_recipe` (B.2) and `CmdDisassemble` (E.2) already carry. It is
the THIRD consumer of that registry -- logged as the one shared entry in
docs/BACKLOG.md, not a new one.
"""

from evennia.contrib.game_systems.crafting.crafting import (
    _load_recipes,
    _RECIPE_CLASSES,
)


def _can_transmit(char, recipe_name):
    """
    Return True if `char` may inscribe/scribe/teach the recipe `recipe_name`.

    Args:
        char (Character): the would-be author/teacher. Must expose
            knows_recipe() and a `skills` TraitHandler (a puppeted Character
            always does).
        recipe_name (str): the canonical recipe-registry name
            (MongooseCraftRecipe.name, e.g. "cloth"), NOT a prototype_key. The
            caller is expected to have already resolved a user-typed name to
            this canonical form (e.g. via _resolve_recipe).

    Returns:
        bool: True iff `char` knows the recipe AND their permanent Craft skill
            (`.current`) meets the recipe's min_skill floor. False if the recipe
            is unknown to `char`, has been removed from the registry, or the
            skill floor is not met.

    Notes:
        The "common / ungated recipe" case is intentionally NOT handled here: a
        common recipe is knowable by everyone, so there is nothing to transmit,
        which is a different message ("Everyone already knows this.") from
        "you haven't mastered this". Callers check requires_knowledge first.
    """
    if not char.knows_recipe(recipe_name):
        return False

    # Exact-key resolve: recipe_name is already canonical, so no fuzzy match is
    # wanted (a prefix collision must not resolve a different recipe). A recipe
    # since removed resolves to None -> cannot be transmitted.
    _load_recipes()
    cls = _RECIPE_CLASSES.get(recipe_name)
    if cls is None:
        return False

    min_skill = getattr(cls, "min_skill", 0) or 0

    # Permanent learned Craft (.current), not effective .value: a temporary buff
    # must not grant authoring rights. See module docstring.
    trait = char.skills.get("craft")
    skill_current = trait.current if trait else 0
    return skill_current >= min_skill
