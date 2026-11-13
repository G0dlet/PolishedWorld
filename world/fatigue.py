"""
world/fatigue.py
================
Legend's fatigue levels on the 0-100 fatigue gauge (Survival Loop S3.1,
lock SL8; Rest design NP1; Legend core p.90).

One table, read by everything a player sees: `Character.fatigue_desc()`
(the word `status`, `sheet`, the client's `survival` snapshot and the
tick's warning print) and `penalty_for()` (the level's penalty on physical
tests, which S3.2 adds in `Character.physical_modifier()`).

    level         gauge      penalty
    Debilitated   0          50
    Exhausted     1-20       40
    Wearied       21-40      30
    Tired         41-60      20
    Winded        61-80      10
    Fresh         81-100      0

Each row's `upper` is an inclusive upper bound, Evennia's own reading of a
trait's `descs` (`Trait.desc()`, evennia/contrib/rpg/traits/traits.py), so
`DESCS` -- the table as a `descs` dict -- gives new characters a stored
table whose `trait.desc()` agrees with this module for every whole value.
Characters made before S3.1 keep their old `descs` (keys 0/20/40/60/80/95);
nothing reads those for fatigue any more, so none of them is rewritten.

THE GAUGE'S OWN NUMBER (lock B3)
--------------------------------
The drain can be fractional (`buffs.check(1, "fatigue_rate")`, which
ColdStress multiplies), but Evennia's `GaugeTrait.current` rounds on read
when the trait's `base` is an int (evennia/contrib/rpg/traits/traits.py,
`_update_current`), and fatigue's base is 100. Every reader -- `desc()`,
`status`'s `_whole()`, `fatigue_desc()` -- sees the same whole number, so
`level_for` reads the value as given, Evennia's own rule, and never needs
to truncate it.

Movement, Strike Rank and Combat Action effects of the levels are Stage 5's
(NP-L5). No Django or Evennia import: the table is plain data.
"""

from collections import namedtuple

Level = namedtuple("Level", "upper word penalty")

# Worst first: a lower index is a worse level (the tick's warning relies on
# it, as `survival_ticker._bucket_index` does for hunger and thirst).
LEVELS = (
    Level(0, "debilitated", 50),
    Level(20, "exhausted", 40),
    Level(40, "wearied", 30),
    Level(60, "tired", 20),
    Level(80, "winded", 10),
    Level(100, "fresh", 0),
)

# Points in one level (Exhausted .. Fresh are each 20 wide). S3.3's failed
# awake test costs one level.
LEVEL_POINTS = 20

# The table as a trait `descs` dict, small to big -- what
# `Character.at_object_creation` stores on the fatigue gauge.
DESCS = {level.upper: level.word for level in LEVELS}


def level_for(value):
    """
    The index into `LEVELS` of the level `value` falls in.

    Args:
        value (int or float): the fatigue gauge's value.

    Returns:
        int: 0 (Debilitated) .. len(LEVELS) - 1 (Fresh). A value above the
            top bound reads as the top level, as `Trait.desc()` does.
    """
    for index, level in enumerate(LEVELS):
        if value <= level.upper:
            return index
    return len(LEVELS) - 1


def word_for(value):
    """The level's word for `value`, e.g. "wearied"."""
    return LEVELS[level_for(value)].word


def penalty_for(value):
    """
    The level's penalty for `value`, as a positive number of percent.

    The caller subtracts it: `physical_modifier()` (S3.2) adds
    `-penalty_for(current)` beside overload's term.
    """
    return LEVELS[level_for(value)].penalty
