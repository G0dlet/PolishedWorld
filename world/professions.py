"""
world/professions.py

Population seed for Stage 3 (Recipe Knowledge & Discovery), Component D.

Pure data + a thin grant helper: a data-driven map of professions to the
*advanced* (knowledge-gated) crafting recipes each one seeds into a character's
known-recipe set. This is the FIRST knowledge source in Stage 3 -- it seeds
specialised knowledge across the starting player base so the later teach/scroll
economy (Components E-I) has something to trade from turn one.

Design notes:
  * KNOWLEDGE ONLY. A profession grants recipe *knowledge*, never stat/skill
    bonuses. Progression balance stays in the skill and quality systems.
  * PORTABLE DATA. `PROFESSIONS` is plain data with no dependencies; the only
    Evennia coupling is (a) grant_profession() calls character.learn_recipe()
    on whatever object the caller passes in, and (b) the unknown-key warning
    uses evennia.utils.logger -- the project's own logging convention (see
    typeclasses/scripts.py), so a bad key surfaces in the server log rather
    than a stdlib channel Evennia doesn't route.
  * SMALL, OVERLAPPING BUNDLES -> interdependence. No single profession owns a
    complete production chain, so specialists must trade. The recipe graph
    (verified against world/recipes.py):

        cloth         <- 3x fiber
        linen shirt   <- 2x cloth        (needs a weaver's cloth)
        leather       <- 2x raw_hide
        leather boots <- 2x leather       (needs a tanner's leather)

    Bundles (see PROFESSIONS):
        weaver     : cloth + linen shirt -- self-sufficient cloth line.
        tanner     : leather             -- sells leather, cannot finish boots.
        cobbler    : leather boots       -- MUST source leather (tanner/generalist).
        generalist : cloth + leather     -- raw-material hub; overlaps weaver and
                     tanner on their refine recipes but finishes nothing, so it
                     depends on weaver (shirts) and cobbler (boots) in turn.

    The overlaps (weaver n generalist = {cloth}, tanner n generalist = {leather})
    and the cobbler -> tanner leather dependency are the interdependence this
    feature exists to create.

Recipe names below are the canonical MongooseCraftRecipe.name values (NOT
prototype_keys) exactly as declared in world/recipes.py, and exactly the four
that carry requires_knowledge = True. The character's TagHandler matches them
case-insensitively; we keep them lowercase to mirror the registry.
"""

from evennia.utils import logger


# profession key -> list of advanced recipe names (MongooseCraftRecipe.name).
# Every entry MUST be a subset of the four requires_knowledge=True recipes in
# world/recipes.py: "cloth", "leather", "linen shirt", "leather boots".
PROFESSIONS = {
    "weaver": ["cloth", "linen shirt"],
    "tanner": ["leather"],
    "cobbler": ["leather boots"],
    "generalist": ["cloth", "leather"],
}


def grant_profession(character, key):
    """
    Seed a profession's advanced recipes into a character's known-recipe set.

    Idempotent by construction: it delegates to character.learn_recipe(), which
    is a guarded read-then-write on the recipe TagHandler and returns True only
    when a recipe is newly learned. Re-running this (e.g. a re-grant slipping
    through at @reload / re-puppet) re-learns nothing and returns [].

    Args:
        character: any object exposing learn_recipe(name) -> bool -- in practice
            a typeclasses.characters.Character. Deliberately NOT type-checked so
            the helper stays permissive (a test stub works too).
        key (str): a profession key from PROFESSIONS. An unknown key is a no-op
            (logged as a warning -- a bad key is almost always a caller typo).

    Returns:
        list[str]: the recipe names newly learned by THIS call, in bundle order.
            Empty when the key is unknown OR every recipe was already known. A
            caller can use a non-empty list to message the player once and stay
            silent on idempotent re-grants.

    Multiplayer note: learn_recipe() is itself concurrency-safe (single-threaded
    Twisted reactor, guarded read-then-write), so two overlapping grants at worst
    both take the "already known" path -- never a duplicate tag.
    """
    recipes = PROFESSIONS.get(key)
    if recipes is None:
        logger.log_warn(
            f"grant_profession: unknown profession key {key!r}; "
            f"known keys are {sorted(PROFESSIONS)}. No recipes granted."
        )
        return []

    learned = []
    for name in recipes:
        if character.learn_recipe(name):
            learned.append(name)
    return learned
