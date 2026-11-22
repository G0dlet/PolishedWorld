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
    trait_kwargs(char, key) -> how one of COMBAT_SKILL_TRAITS is added

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

SKILL_LADDERS holds the six words every skill reads as, and `ladder(key)`
makes the `descs` table a trait stores. The bands are 0-19, 20-39, 40-59,
60-79, 80-94 and 95 upward. The traits contrib reads a `descs` key as an
UPPER bound, inclusive, and gives the last word to anything above the last
key (`CounterTrait.desc`; `world.improvement.tier_for` and the skills'
"reaches a new tier" line follow the same rule), so a ladder is keyed by
each band's top: LADDER_TOPS. Keyed by band bottoms (0/20/40/60/80/95), as
the five older skills were until BD-T5b, a ladder reads one rung early: 21
as the third word, 81 as the last. A trait keeps the table it was created
with, so `world.character_migrations.backfill_skill_ladders` rewrites it on
older characters. (BACKLOG *`descs` tables are read as upper bounds but
shaped like lower bounds*, decided for the skills 2026-11-22; hunger and
thirst are still keyed the old way.)

COMBAT_SKILL_TRAITS is how the four Common skills combat reads (BD5) are
made into traits: the name and the ladder. Two writers read it and no
others, both through `trait_kwargs`: `Character.at_object_creation` and
`world.character_migrations.backfill_combat_skills` (BD-T5), so a backfilled
character cannot differ from a new one.

Pure over the character's handlers: no Django query, nothing written.
"""

from world.chargen import SKILL_BASE_PAIRS

# The top of each band, inclusive; 100 stands for "95 upward", since
# anything above the last key reads the last word.
LADDER_TOPS = (19, 39, 59, 79, 94, 100)

# Skill -> its six words, in band order (Tone Guide section 5: concrete,
# nothing epic). One table for all nine skills: creation, both backfills
# and the ladder migration read it.
SKILL_LADDERS = {
    "athletics": ("feeble", "weak", "capable", "athletic", "strong", "mighty"),
    "perception": (
        "oblivious", "unaware", "attentive", "observant", "sharp", "eagle-eyed",
    ),
    "stealth": ("clumsy", "obvious", "careful", "sneaky", "stealthy", "invisible"),
    "craft": (
        "unskilled", "novice", "apprentice", "journeyman", "skilled", "master",
    ),
    "hunting": (
        "helpless", "novice", "competent", "tracker", "hunter", "master hunter",
    ),
    "brawn": ("slight", "wiry", "sturdy", "stout", "burly", "ox-strong"),
    "evade": ("flat-footed", "slow", "wary", "nimble", "quick", "hard to hit"),
    "resilience": ("frail", "soft", "sound", "hardy", "tough", "unbroken"),
    "unarmed": (
        "harmless", "clumsy", "scrappy", "practised", "hard-fisted", "dangerous",
    ),
}


def ladder(key):
    """
    The `descs` table for a skill's trait: {top of band: word}, rising.

    A new dict on every call, because a trait stores what it is given.

    Args:
        key (str): a key of SKILL_LADDERS.

    Returns:
        dict: six entries keyed by LADDER_TOPS.

    Raises:
        KeyError: the skill has no ladder.
    """
    return dict(zip(LADDER_TOPS, SKILL_LADDERS[key]))


COMBAT_SKILL_TRAITS = {
    "brawn": {"name": "Brawn", "descs": ladder("brawn")},
    "evade": {"name": "Evade", "descs": ladder("evade")},
    "resilience": {"name": "Resilience", "descs": ladder("resilience")},
    "unarmed": {"name": "Unarmed", "descs": ladder("unarmed")},
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


def trait_kwargs(char, key):
    """
    What `char.skills.add(key, name, **kwargs)` takes for a combat skill.

    The one place the shape of the four traits is written, for creation and
    for the backfill. No `max`: a CounterTrait with a max clamps inside its
    own setter (D.2, P-7).

    Args:
        char: a typeclassed object with a `stats` handler.
        key (str): a key of COMBAT_SKILL_TRAITS.

    Returns:
        dict or None: the keyword arguments, with `base` and `current` at
            `base_for(char, key)`; None when that base cannot be worked out.

    Raises:
        KeyError: `key` is not one of COMBAT_SKILL_TRAITS.
    """
    COMBAT_SKILL_TRAITS[key]   # KeyError for anything but the four
    base = base_for(char, key)
    if base is None:
        return None
    return {
        "trait_type": "counter",
        "base": base,
        "current": base,
        "mod": 0,
        "min": 0,
        "descs": ladder(key),
    }
