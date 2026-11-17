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

The fatigue words are `world.fatigue.LEVELS`' own; an unknown word raises
`ValueError` rather than reading as fresh.

Left to other slices:
- +1 Combat Action for a shield or a weapon in the second hand (p. 124): ML.
- The sum of Armour Points worn (p. 125): GR. Until then callers pass 0.
- What a negative Strike Rank means for the opening beat (OQ-BD5): ML.
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
