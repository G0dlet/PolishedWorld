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

Pure over the character's handlers: no Django query, nothing written.
"""

from world.chargen import SKILL_BASE_PAIRS

# Pairs the net reads before character creation writes the skill. Resilience
# is here for one task (BD-T3) so that healing can read it through the net;
# BD-T4 moves it into `chargen.SKILL_BASE_PAIRS` together with its trait and
# removes it here (OQ-BD6). Keep it empty after that.
PENDING_PAIRS = {
    "resilience": ("con", "con"),  # CON x 2 (p. 14)
}


def _pair_for(key):
    return SKILL_BASE_PAIRS.get(key) or PENDING_PAIRS.get(key)


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
    pair = _pair_for(key)
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
