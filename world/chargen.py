"""
Legend character creation: Points Build validation, derived skill bases, and
applying an allocation to a character (Character Creation, Task CC1.1).

The first two functions are pure -- no database, no typeclass -- which is why
they are testable with `EvenniaTestCase`. `apply_allocation()` is the one
stateful entry point and the only code in the project that re-bases a
character's characteristics.

THE RULE (Legend p.9, Points Build; decision CC1)
-------------------------------------------------
80 Characteristic Design Points over the seven characteristics, 1 point per
point, each characteristic 6-18, every point spent. p.9's optional rule that
buys values above 18 at 2 points each is NOT adopted: the ladder's rung 20 is
meant to be a choice, not something a build can purchase past. The constants
below are rules, not balance knobs, which is why they live here and not in
settings.

DERIVED SKILL BASES (decision CC5, Legend p.13-14)
--------------------------------------------------
Athletics STR+DEX, Perception INT+POW, Stealth DEX+INT and Craft DEX+INT are
Legend's own. Hunting is the project's skill; its pair is Legend's Track
(INT+CON, p.65) -- the closest canonical analogue, a pair no other skill uses,
and CON's only skill reader (OQ1, locked 2026-10-26). Derivation reads the
allocation's integers, never a trait's `.value`: a StaticTrait's value is
`(base + mod) * mult` with `mult = 1.0`, i.e. a float.

WHAT `apply_allocation()` DOES NOT DO
-------------------------------------
It writes nothing to `skill_xp` (CC5/CC7: derive, never backfill). An absent
XP entry is derived on read from the skill's `.current`, so the floor follows
the new base with no write. A *present* entry would not follow: lowering a
skill below a banked total lets the next improvement re-derive the old level
from the old XP. That is why a character with banked XP is refused -- CC7's
"no re-spec" enforced in code rather than only in prose.

Multiplayer: everything happens inside one call on one character, on
Twisted's single-threaded reactor, with MULTISESSION_MODE 0. No two writers
can meet on the same character, so no locking is needed. All checks run before
the first write, so a refused call leaves the character exactly as it was.
"""

from collections.abc import Mapping

# Legend p.9 -- rules, not knobs.
DESIGN_POINTS = 80
CHAR_MIN = 6
CHAR_MAX = 18

# The seven characteristics, keyed as in Character.at_object_creation.
STAT_KEYS = ("str", "dex", "con", "siz", "int", "pow", "cha")

# Skill -> the two characteristics its base is the sum of (CC5, OQ1).
SKILL_BASE_PAIRS = {
    "athletics": ("str", "dex"),
    "perception": ("int", "pow"),
    "stealth": ("dex", "int"),
    "craft": ("dex", "int"),
    "hunting": ("int", "con"),
}

# The Attribute SkillXPHandler stores banked XP in (typeclasses/characters.py,
# Character.skill_xp). Read directly: `skill_xp.all()` also lists *derived*
# entries, so it is never empty and cannot answer "has anything been banked?".
SKILL_XP_ATTRIBUTE = "skill_xp"


def _is_plain_int(value):
    """
    True for an int that is not a bool.

    `bool` subclasses `int`, so `isinstance(True, int)` is True -- and
    StaticTrait's base setter accepts it as 1. A str such as "12" is the
    opposite trap: the setter ignores it silently and leaves the old base.
    Both must be refused here, before anything reaches a trait.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def validate_allocation(alloc):
    """
    Check a Points Build allocation against Legend p.9.

    Every violation is reported, so a menu can print them all at once.

    Args:
        alloc (Mapping): characteristic key -> value, e.g. {"str": 12, ...}.
            Any Mapping is accepted, including Evennia's `_SaverDict`.

    Returns:
        list[str]: human-readable violations; empty means valid.
    """
    if not isinstance(alloc, Mapping):
        return [
            "An allocation must map each characteristic to a value, "
            f"not be a {type(alloc).__name__}."
        ]

    errors = []

    missing = [key for key in STAT_KEYS if key not in alloc]
    if missing:
        errors.append(
            "Missing characteristic(s): "
            + ", ".join(key.upper() for key in missing) + "."
        )

    unknown = [key for key in alloc if key not in STAT_KEYS]
    if unknown:
        errors.append(
            "Unknown characteristic(s): "
            + ", ".join(repr(key) for key in unknown) + "."
        )

    all_ints = True
    for key in STAT_KEYS:
        if key not in alloc:
            continue
        value = alloc[key]
        if not _is_plain_int(value):
            all_ints = False
            errors.append(f"{key.upper()} must be a whole number, not {value!r}.")
        elif not CHAR_MIN <= value <= CHAR_MAX:
            errors.append(
                f"{key.upper()} is {value}; a characteristic must be "
                f"{CHAR_MIN}-{CHAR_MAX}."
            )

    # The total is only meaningful when all seven are present integers;
    # otherwise it would be noise on top of the real error.
    if not missing and all_ints:
        total = sum(alloc[key] for key in STAT_KEYS)
        if total < DESIGN_POINTS:
            errors.append(
                f"{total} of {DESIGN_POINTS} points spent -- "
                f"{DESIGN_POINTS - total} left to spend."
            )
        elif total > DESIGN_POINTS:
            errors.append(
                f"{total} points spent -- {total - DESIGN_POINTS} over "
                f"the {DESIGN_POINTS} available."
            )

    return errors


def derive_skill_bases(stats):
    """
    Derive each common skill's base from the characteristics (CC5).

    Pure: reads the mapping, writes nothing, does not validate. Pass a
    validated allocation; integers in give integers out.

    Args:
        stats (Mapping): characteristic key -> value.

    Returns:
        dict: skill key -> base, e.g. {"athletics": 16, ...}.
    """
    return {
        skill: stats[first] + stats[second]
        for skill, (first, second) in SKILL_BASE_PAIRS.items()
    }


def apply_allocation(character, alloc):
    """
    Re-base a fresh character's characteristics, health and skills.

    All checks run before the first write. Then: each characteristic's
    `.base` (StaticTrait -- it has no `.current`, and a written `.current`
    would be stored silently as an extra key), health via the existing
    `update_health_max()` helper (after the stats, since it reads CON), and
    each skill's `.base` AND `.current` (CounterTrait: a later `.base = N`
    does not move `.current`).

    Args:
        character (Character): the character being created.
        alloc (Mapping): a Points Build allocation.

    Returns:
        dict: the derived skill bases, for the confirmation screen.

    Raises:
        ValueError: the allocation is invalid; the character has banked XP
            (CC7: no re-spec); the character already has a profession (its
            skill bonus sits on the bases this would overwrite -- allocation
            comes first, CC2.1); or a characteristic, health or skill trait
            the derivation writes is missing. Nothing is written in any of
            these cases.
    """
    errors = validate_allocation(alloc)
    if errors:
        raise ValueError(" ".join(errors))

    store = character.attributes.get(SKILL_XP_ATTRIBUTE, default=None)
    if isinstance(store, Mapping) and len(store) > 0:
        raise ValueError(
            f"{character.key} has banked skill XP; characteristics are set "
            "once, at creation (no re-spec)."
        )

    if character.db.profession:
        raise ValueError(
            f"{character.key} already follows a profession; characteristics "
            "are set before the profession, never after."
        )

    derived = derive_skill_bases(alloc)

    absent = [key for key in STAT_KEYS if character.stats.get(key) is None]
    if character.traits.get("health") is None:
        absent.append("health")
    absent += [key for key in derived if character.skills.get(key) is None]
    if absent:
        raise ValueError(
            f"{character.key} is missing trait(s): {', '.join(absent)}."
        )

    for key in STAT_KEYS:
        character.stats.get(key).base = alloc[key]

    character.update_health_max()

    for key, base in derived.items():
        skill = character.skills.get(key)
        skill.base = base
        skill.current = base

    return derived
