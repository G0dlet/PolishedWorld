"""
world/skill_base.py
===================
What a character's skill is, with or without its trait (Body decomposition,
slice BD, locks BD3 and BD6; Legend core p. 14).

Every skill starts at its base, the sum of two characteristics (p. 14), so a
skill a character has no trait for is still a number that can be worked
out. One function answers for every reader:

    base_for(char, key)  -> the base from the characteristics, or None
    value_of(char, key)  -> the trait's value if the trait exists, else the base

Why a safety net (BD6): a reader that went to the trait directly would get
nothing for a character a backfill missed -- `healing.accrue` would grant
nothing, with no message. Through `value_of` the backfill decides what is
shown, not whether healing works.

The base is read from the characteristics' `.base`: it is the number
character creation would have written (`chargen.apply_allocation` sets
`.base`). A trait's `.value` is read, as every roll site and
`world.fatigue` read a skill (OQ-BD2).

Every pair lives in `chargen.SKILL_BASE_PAIRS`, and nowhere else (OQ-BD6:
Resilience's stood here for one task, until its trait existed).

COMBAT_SKILL_TRAITS is how the four Common skills combat reads (BD5) are
made into traits: the name and the six words of the trait's ladder. Two
writers read it and no others: `Character.at_object_creation` and the
backfill (BD-T5), so a backfilled character cannot differ from a new one.
The ladder's bands are 0-19, 20-39, 40-59, 60-79, 80-94 and 95 upward. The
traits contrib reads a `descs` key as an UPPER bound, inclusive, and gives
the last word to anything above the last key (`CounterTrait.desc`), so the
keys are each band's top: 19, 39, 59, 79, 94, and 100 for the open band.
Keyed 0/20/40/60/80/95 the ladder reads one rung early -- 21 as the third
word, 81 as the last -- which is how the five older skills in
`Character.at_object_creation` still read; they are corrected in a task of
their own, because a trait keeps the ladder it was created with.

Pure over the character's handlers: no Django query, nothing written.
"""

from world.chargen import SKILL_BASE_PAIRS

COMBAT_SKILL_TRAITS = {
    "brawn": {
        "name": "Brawn",
        "descs": {
            19: "slight", 39: "wiry", 59: "sturdy",
            79: "stout", 94: "burly", 100: "ox-strong",
        },
    },
    "evade": {
        "name": "Evade",
        "descs": {
            19: "flat-footed", 39: "slow", 59: "wary",
            79: "nimble", 94: "quick", 100: "hard to hit",
        },
    },
    "resilience": {
        "name": "Resilience",
        "descs": {
            19: "frail", 39: "soft", 59: "sound",
            79: "hardy", 94: "tough", 100: "unbroken",
        },
    },
    "unarmed": {
        "name": "Unarmed",
        "descs": {
            19: "harmless", 39: "clumsy", 59: "scrappy",
            79: "practised", 94: "hard-fisted", 100: "dangerous",
        },
    },
}


def base_for(char, key):
    """
    A skill's base, worked out from the character's characteristics (p. 14).

    Args:
        char: a typeclassed object with a `stats` handler.
        key (str): the skill's trait key, e.g. "resilience".

    Returns:
        int or None: the sum of the two characteristics' `.base`; None when
            the key has no pair or the character lacks a characteristic.
    """
    pair = SKILL_BASE_PAIRS.get(key)
    stats = getattr(char, "stats", None)
    if pair is None or stats is None:
        return None
    total = 0
    for stat_key in pair:
        stat = stats.get(stat_key)
        if stat is None:
            return None
        total += int(stat.base)
    return total


def value_of(char, key):
    """
    A skill's value: the trait's if the character has it, the base if not.

    Args:
        char: a typeclassed object with `skills` and `stats` handlers.
        key (str): the skill's trait key.

    Returns:
        int, float or None: the trait's `.value`; else `base_for(char, key)`.
    """
    skills = getattr(char, "skills", None)
    trait = skills.get(key) if skills is not None else None
    if trait is not None:
        return trait.value
    return base_for(char, key)
