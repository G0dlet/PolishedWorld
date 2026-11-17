"""
world/body.py
=============
A body's derived values, read on demand (Body decomposition, slice BD,
lock BD7; Legend core pp. 10-13, 90).

Pure functions over integers. This module stores nothing and writes
nothing: every value is worked out from the characteristics and the
fatigue word at the moment of asking, so a change in fatigue (or, later,
in armour worn) shows on the next read without a writer to remember it.
It is the pattern of `world.encumbrance`.

    combat_actions(dex, int_, fatigue_word)               -> int  (p. 10, p. 90)
    strike_rank(dex, int_, armour_points, fatigue_word)   -> int  (pp. 12-13, p. 90)
    damage_modifier(str_, siz)       -> (sign, dice, sides)       (pp. 10-11)
    damage_modifier_text(str_, siz)  -> "+1D2", "-1D4", "+0"
    hit_points_max(con, siz)         -> {location: maximum}       (p. 11)
    derived(char)                    -> the four for a character, or None

The fatigue words are `world.fatigue.LEVELS`' own; an unknown word raises
`ValueError` rather than reading as fresh.

Left to other slices:
- +1 Combat Action for a shield or a weapon in the second hand (p. 124): ML.
- The sum of Armour Points worn (p. 125): GR. Until then callers pass 0.
- What a negative Strike Rank means for the opening beat (OQ-BD5): ML.
- Rolling the Damage Modifier: ML.
- The current Hit Points per location, wound levels and states: WN (WO2).
  This module gives the maximum only; `health` stays the one written
  measure of hurt until WN builds the damage path.
"""

from world.fatigue import LEVELS

FATIGUE_WORDS = frozenset(level.word for level in LEVELS)

# p. 90: DEX is "considered 5 points lower" (Exhausted) and "10 points
# lower" (Debilitated) for the purposes of determining Combat Actions.
COMBAT_ACTIONS_DEX_LOSS = {"exhausted": 5, "debilitated": 10}

# p. 90: "Strike Rank suffers a -2 / -4 / -6 penalty".
STRIKE_RANK_PENALTY = {"wearied": 2, "exhausted": 4, "debilitated": 6}


def _check_word(fatigue_word):
    if fatigue_word not in FATIGUE_WORDS:
        raise ValueError(
            f"unknown fatigue level {fatigue_word!r}; "
            f"expected one of {sorted(FATIGUE_WORDS)}"
        )


def _average_up(a, b):
    """The average of two integers, rounded up (pp. 10, 13)."""
    return -(-(a + b) // 2)


def combat_actions(dex, int_, fatigue_word="fresh"):
    """
    How many times a body acts in a Combat Round (core p. 10).

    The average of DEX and INT, rounded up: 6 or less gives 1, 7-12 gives 2,
    13-18 gives 3, and every further 6 points one more. At Exhausted and
    Debilitated DEX counts 5 and 10 lower (p. 90).

    Not here: +1 for a shield or a second weapon (p. 124), which is ML's.

    Args:
        dex (int): DEX.
        int_ (int): INT.
        fatigue_word (str): a word from `world.fatigue.LEVELS`.

    Returns:
        int: at least 1.

    Raises:
        ValueError: for a fatigue word that is not a level.
    """
    _check_word(fatigue_word)
    dex = dex - COMBAT_ACTIONS_DEX_LOSS.get(fatigue_word, 0)
    average = _average_up(dex, int_)
    if average <= 6:
        return 1
    return 2 + (average - 7) // 6


def strike_rank(dex, int_, armour_points=0, fatigue_word="fresh"):
    """
    How soon a body acts in a Combat Round (core pp. 12-13).

    The average of INT and DEX rounded up, less the Armour Points carried
    divided by 5 and rounded up, less 2, 4 or 6 at Wearied, Exhausted and
    Debilitated (p. 90). The book sets no floor, and none is added: 91
    Armour Points give -4 on an average of 15 (OQ-BD5).

    Args:
        dex (int): DEX.
        int_ (int): INT.
        armour_points (int): the sum of Armour Points worn. Summing what is
            worn is GR's; until then the caller passes 0.
        fatigue_word (str): a word from `world.fatigue.LEVELS`.

    Returns:
        int: may be negative.

    Raises:
        ValueError: for a fatigue word that is not a level.
    """
    _check_word(fatigue_word)
    armour_penalty = -(-armour_points // 5)
    return (
        _average_up(dex, int_)
        - armour_penalty
        - STRIKE_RANK_PENALTY.get(fatigue_word, 0)
    )


# --- The Damage Modifier (core pp. 10-11) ------------------------------------

# (upper bound of STR + SIZ, sign, dice, sides), inclusive at the top, typed
# from p. 10. Bands of 5 up to 50, then of 10. The table ends at 100.
DAMAGE_MODIFIER_ROWS = (
    (5, -1, 1, 8),
    (10, -1, 1, 6),
    (15, -1, 1, 4),
    (20, -1, 1, 2),
    (25, 0, 0, 0),
    (30, 1, 1, 2),
    (35, 1, 1, 4),
    (40, 1, 1, 6),
    (45, 1, 1, 8),
    (50, 1, 1, 10),
    (60, 1, 1, 12),
    (70, 1, 2, 6),
    (80, 1, 2, 8),
    (90, 1, 2, 10),
    (100, 1, 2, 12),
)


def damage_modifier(str_, siz):
    """
    The Damage Modifier for STR + SIZ, as data (core pp. 10-11).

    A negative modifier is still rolled and subtracted (p. 11); rolling it
    is ML's.

    Args:
        str_ (int): STR.
        siz (int): SIZ.

    Returns:
        tuple: (sign, dice, sides) -- (1, 1, 2) is +1D2, (-1, 1, 4) is -1D4,
            (0, 0, 0) is +0.

    Raises:
        ValueError: below 1 or above 100. The book's table ends at 100 and
            a player character reaches 36; a creature over it (CE) needs a
            rule, not a guessed row (BD7).
    """
    total = str_ + siz
    if total < 1:
        raise ValueError(f"STR + SIZ {total} is below the table (1-100)")
    for upper, sign, dice, sides in DAMAGE_MODIFIER_ROWS:
        if total <= upper:
            return sign, dice, sides
    raise ValueError(f"STR + SIZ {total} is above the table (1-100)")


def damage_modifier_text(str_, siz):
    """The Damage Modifier for display: "+1D2", "-1D4" or "+0"."""
    sign, dice, sides = damage_modifier(str_, siz)
    if dice == 0:
        return "+0"
    return f"{'-' if sign < 0 else '+'}{dice}D{sides}"


# --- Hit Points per location (core p. 11) ------------------------------------

# Humans have seven locations (p. 11). The keys WN's current values will use.
LOCATIONS = (
    "head", "chest", "abdomen",
    "right_arm", "left_arm", "right_leg", "left_leg",
)

# Each location's value in the first column (CON + SIZ 1-5). Every further
# band of 5 adds one (the table's eight columns, then "+5 -> +1").
_FIRST_COLUMN = {
    "head": 1, "chest": 3, "abdomen": 2,
    "right_arm": 1, "left_arm": 1, "right_leg": 1, "left_leg": 1,
}
_ARMS = ("right_arm", "left_arm")


def hit_points_max(con, siz):
    """
    The maximum Hit Points of each of the seven locations (core p. 11).

    The maximum only: what is left of them is WN's.

    An arm has 1 in both of the first two columns (1, 1, 2, 3 ...); every
    other row adds one per band of five from its first column.

    Args:
        con (int): CON.
        siz (int): SIZ.

    Returns:
        dict: location key (`LOCATIONS`) -> int.

    Raises:
        ValueError: when CON + SIZ is below 1, where the table has no column.
    """
    total = con + siz
    if total < 1:
        raise ValueError(f"CON + SIZ {total} is below the table")
    band = (total - 1) // 5          # 0 for 1-5, 1 for 6-10, ...
    result = {}
    for location in LOCATIONS:
        if location in _ARMS:
            result[location] = max(1, band)
        else:
            result[location] = _FIRST_COLUMN[location] + band
    return result


# --- A character's body ------------------------------------------------------

_CHARACTERISTICS = ("str", "dex", "con", "siz", "int")


def derived(char):
    """
    The four derived values of a character, read now (BD7).

    The characteristics are read as `int(stat.value)`: these values are live
    and should follow a modifier on a characteristic if one ever exists. (A
    skill's base, BD-T3, reads `.base`: it is what creation would have
    written.) Nothing writes a characteristic's `mod` today, so the two agree.

    The fatigue word is the character's own `fatigue_desc()`; a body without
    a fatigue gauge reads as fresh. Armour Points are 0 until GR sums them.

    Args:
        char: a typeclassed object with a `stats` handler.

    Returns:
        dict or None: {"combat_actions": int, "strike_rank": int,
            "damage_modifier": (sign, dice, sides), "hit_points": {...}};
            None for a body without the five characteristics.
    """
    stats = getattr(char, "stats", None)
    if stats is None:
        return None
    values = {}
    for key in _CHARACTERISTICS:
        stat = stats.get(key)
        if stat is None:
            return None
        values[key] = int(stat.value)

    fatigue_desc = getattr(char, "fatigue_desc", None)
    word = (fatigue_desc() if callable(fatigue_desc) else "") or "fresh"

    return {
        "combat_actions": combat_actions(values["dex"], values["int"], word),
        "strike_rank": strike_rank(values["dex"], values["int"], 0, word),
        "damage_modifier": damage_modifier(values["str"], values["siz"]),
        "hit_points": hit_points_max(values["con"], values["siz"]),
    }
