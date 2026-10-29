"""
world/professions.py

Population seed for Stage 3 (Recipe Knowledge & Discovery), Component D.

Pure data + a thin grant helper: a data-driven map of professions to the
*advanced* (knowledge-gated) crafting recipes each one seeds into a character's
known-recipe set. This is the FIRST knowledge source in Stage 3 -- it seeds
specialised knowledge across the starting player base so the later teach/scroll
economy (Components E-I) has something to trade from turn one.

Design notes:
  * KNOWLEDGE PLUS ONE SKILL BONUS (CC2.1, Character Creation decision CC6).
    A profession is one package: the recipes it teaches and a bonus to the
    Craft skill, applied once on top of the base the characteristics derive
    (world/chargen.py). Every profession carries craft +10 -- the lowest
    possible Craft base is 12 (DEX 6 + INT 6), so +10 is what puts rung 20,
    where each profession's first recipe sits, within reach of any build.
    Legend's own crafter takes Craft from Free Skill Points (p.25); those are
    out of the alpha, and this bonus is the deliberate adaptation in their
    place.
  * PORTABLE DATA. `PROFESSIONS` is plain data with no dependencies; the only
    Evennia coupling is (a) grant_profession() calls character.learn_recipe(),
    reads character.skills and stamps character.db.profession on whatever
    object the caller passes in, and (b) the unknown-key warning
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
prototype_keys) exactly as declared in world/recipes.py, each one a recipe
that carries requires_knowledge = True (the four seeded here are not the only
ones -- later stages added more knowledge-gated recipes). The character's TagHandler matches them
case-insensitively; we keep them lowercase to mirror the registry.
"""

from evennia.utils import logger


# profession key -> package:
#   "recipes":     advanced recipe names (MongooseCraftRecipe.name) taught by
#                  the profession, in the order grant_profession() returns them.
#   "skill_bonus": skill key -> points added to that skill's .base and .current,
#                  once. Every key must be a skill derive_skill_bases() derives.
# Every recipe name MUST be a requires_knowledge=True recipe in world/recipes.py.
PROFESSIONS = {
    "weaver": {"recipes": ["cloth", "linen shirt"], "skill_bonus": {"craft": 10}},
    "tanner": {"recipes": ["leather"], "skill_bonus": {"craft": 10}},
    "cobbler": {"recipes": ["leather boots"], "skill_bonus": {"craft": 10}},
    "generalist": {"recipes": ["cloth", "leather"], "skill_bonus": {"craft": 10}},
}


def grant_profession(character, key):
    """
    Give a character a profession: its recipes, its skill bonus, the sentinel.

    Once per character. `character.db.profession` is the sentinel, and this
    function is its only writer (P-2): a character that already has a
    profession gets nothing, whatever key is passed. The sentinel used to be
    stamped after the call by the `profession` command (retired in CC3.3; the
    chargen menu is the caller now); with a skill bonus in
    the package a second call would add the bonus twice, so the guard has to
    live where the bonus is applied.

    Order: every check before the first write, then recipes, then the bonus on
    each named skill's `.base` AND `.current` (CounterTrait: a later `.base`
    write does not move `.current`, and the XP floor reads `.current`), then
    the sentinel LAST. A refused call writes nothing.

    No backfill (Character Creation decision CC7): a character who chose a
    profession before CC2.1 carries the sentinel without the bonus and will
    never receive it. Only dev characters are in that state.

    Args:
        character: a typeclasses.characters.Character -- anything exposing
            learn_recipe(name) -> bool, a `skills` TraitHandler and `db`.
        key (str): a profession key from PROFESSIONS. An unknown key is a
            no-op, logged as a warning (almost always a caller typo).

    Returns:
        list[str]: the recipe names newly learned by THIS call, in bundle
            order. Empty when the key is unknown, when the character already
            has a profession, or when every recipe was already known. A
            non-empty list lets a caller message the player once.

    Raises:
        ValueError: a skill named in the package's skill_bonus is missing on
            the character. Nothing is written.

    Multiplayer note: the body never yields to the reactor (no Deferred, no
    delay), and Evennia runs commands one at a time on a single thread, so
    the check-then-write on the sentinel cannot interleave with another
    grant for the same character.
    """
    package = PROFESSIONS.get(key)
    if package is None:
        logger.log_warn(
            f"grant_profession: unknown profession key {key!r}; "
            f"known keys are {sorted(PROFESSIONS)}. Nothing granted."
        )
        return []

    current = character.db.profession
    if current:
        if current != key:
            logger.log_warn(
                f"grant_profession: {character.key} already follows "
                f"{current!r}; refusing {key!r}. Nothing granted."
            )
        return []

    bonus = package["skill_bonus"]
    absent = [skill for skill in bonus if character.skills.get(skill) is None]
    if absent:
        raise ValueError(
            f"{character.key} is missing skill(s): {', '.join(absent)}."
        )

    learned = []
    for name in package["recipes"]:
        if character.learn_recipe(name):
            learned.append(name)

    for skill_key, points in bonus.items():
        skill = character.skills.get(skill_key)
        skill.base = skill.base + points
        skill.current = skill.current + points

    character.db.profession = key
    return learned
