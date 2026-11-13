"""
world/fatigue.py
================
Legend's fatigue levels on the 0-100 fatigue gauge (Survival Loop S3.1,
lock SL8; Rest design NP1; Legend core p.90), and the awake clock that
lowers it (S3.3, lock SL9).

One table, read by everything a player sees: `Character.fatigue_desc()`
(the word `status`, `sheet`, the client's `survival` snapshot and the
tick's warning print) and `penalty_for()` (the level's penalty on physical
tests, which `Character.physical_modifier()` subtracts, S3.2).

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
Evennia's `GaugeTrait.current` rounds on read when the trait's `base` is an
int (evennia/contrib/rpg/traits/traits.py, `_update_current`), and
fatigue's base is 100. Every reader -- `desc()`, `status`'s `_whole()`,
`fatigue_desc()` -- sees the same whole number, so `level_for` reads the
value as given, Evennia's own rule, and never needs to truncate it. Since
S3.3 nothing writes a fraction to the gauge: the awake clock's fractions
(a `fatigue_rate` multiplier) live in `db.awake_seconds`, and the gauge
moves in whole levels.

THE AWAKE CLOCK (S3.3, SL9; Rest NP3, NP-L1)
--------------------------------------------
The survival tick no longer drains fatigue. It adds its game seconds, times
`fatigue_rate` (ColdStress and HeatStress spend the hours faster), to
`db.awake_seconds` (`advance_clock`). Past `threshold()` -- (10 + CON) game
hours -- each further whole hour is one Athletics test (`tests_due`, counted
in `db.awake_tests`), rolled by `awake_test` with the physical modifier and
`need_penalty()`. The tick writes the gauge: a failure costs `LEVEL_POINTS`
(lock B1). A rest that reaches full calls `reset_clock` (SL10). Both
attributes are read with a default of 0, so characters made before S3.3
need no backfill (lock A1).

The tests are involuntary: `awake_test` calls `skill_check` and never
`attempt_skill_improvement` -- standing still must not train Athletics.

Movement, Strike Rank and Combat Action effects of the levels are Stage 5's
(NP-L5). No Django or Evennia import: the character is read through its own
handlers, and `world.skillcheck` is pure.
"""

from collections import namedtuple

from world.skillcheck import skill_check

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

    The caller subtracts it: `Character.physical_modifier()` (S3.2) adds
    `-penalty_for(value)` beside overload's term.
    """
    return LEVELS[level_for(value)].penalty


# --- The awake clock (S3.3) ----------------------------------------------------

HOUR = 3600   # game seconds

# Legend's waking day before tests begin: (10 + CON) hours (Rest NP3).
DAY_BASE_HOURS = 10

# A further -20 on the awake test while Starving or Dehydrated (SL9). The
# conditions by their buff keys (lock C1), so this module imports no buff
# class; tests/test_fatigue.py pins the keys to the classes' own.
NEED_PENALTY = -20
NEEDS = ("starving", "dehydrated")

# Said when a failed test lowers the gauge (OQ-S4, lock E1); the tick's
# warning names the new level right after it.
AWAKE_FAILED = "Your eyes are gritty and your legs drag; the day has run long."


def threshold(char):
    """
    Game seconds awake before the first test: (10 + CON) hours.

    Returns:
        int or None: None when the character has no CON (no clock runs).
    """
    con = char.stats.get("con")
    if con is None:
        return None
    return int((DAY_BASE_HOURS + con.value) * HOUR)


def advance_clock(char, game_seconds):
    """
    Add a span of game time to the awake clock, at the `fatigue_rate`.

    Stored as a float: a ColdStress stack's x1.08 would be lost to rounding
    if the clock were whole seconds, as it is lost on the gauges today.

    Args:
        char (Character): the character.
        game_seconds (int): the tick's span; 0 or less adds nothing.
    """
    if game_seconds <= 0:
        return
    spent = char.buffs.check(game_seconds, "fatigue_rate")
    char.db.awake_seconds = (char.db.awake_seconds or 0) + spent


def tests_due(char):
    """
    Whole hours past the threshold not yet rolled.

    An hour is due once it is complete: one second short of
    `threshold + HOUR` none is.

    Returns:
        int: 0 or more.
    """
    limit = threshold(char)
    if limit is None:
        return 0
    past = (char.db.awake_seconds or 0) - limit
    if past < HOUR:
        return 0
    return max(0, int(past // HOUR) - (char.db.awake_tests or 0))


def need_penalty(char):
    """`NEED_PENALTY` while Starving or Dehydrated, else 0."""
    if any(char.buffs.has(key) for key in NEEDS):
        return NEED_PENALTY
    return 0


def awake_test(char):
    """
    Roll one due hour's Athletics test and count it as rolled.

    The modifier is read at the moment of the roll, so a second test in the
    same tick reads the level the first one left (SL-M48). The hour is
    counted whether or not a roll is possible, so it is never due again.

    Returns:
        dict or None: `skill_check`'s result; None without Athletics.
    """
    char.db.awake_tests = (char.db.awake_tests or 0) + 1
    athletics = char.skills.get("athletics")
    if athletics is None:
        return None
    return skill_check(athletics.value, char.physical_modifier() + need_penalty(char))


def reset_clock(char):
    """Start the day again: clock and count to zero (a rest to full, SL10)."""
    char.db.awake_seconds = 0
    char.db.awake_tests = 0


# --- Collapse at Debilitated (S3.4) ---------------------------------------------

# A Difficult test (-20, SL11) on top of the level's -50 and any overload,
# rolled on each tick that finds the gauge at 0 (lock D1).
DIFFICULT = -20

# The forced rest ends when the gauge reaches this (Tired). A placeholder:
# Rest slice 2 replaces it with NP14's "out of Debilitated, at the place's
# row" (OQ-S3).
COLLAPSE_WAKE_AT = 41

# The timed-action slot's key and label (`timed_actions.start`): the label
# is what `rest`, `craft` and `work` answer with -- "You are already lying
# where you fell." (lock I1).
COLLAPSE_KEY = "collapse"
COLLAPSE_LABEL = "lying where you fell"

# The lines (OQ-S4, lock I1). Room lines take the character's key.
FALL = "Your legs fold, and the ground comes up to meet you."
FALL_ROOM = "{name} sways and goes down where they stand."
WAKE = "You stir, and get slowly to your feet."
WAKE_ROOM = "{name} stirs and gets slowly up."
CANNOT_MOVE = "Your legs will not carry you."
CANNOT_HANDLE = "Your hands will not obey you."


def collapse_test(char):
    """
    Roll the Difficult Athletics test a Debilitated body makes each tick.

    The modifier is the physical modifier (the level's -50, overload's -20)
    plus `DIFFICULT` (lock D1: no need penalty -- SL11 names none). Like the
    awake test it never calls `attempt_skill_improvement`.

    Returns:
        dict or None: `skill_check`'s result; None without Athletics.
    """
    athletics = char.skills.get("athletics")
    if athletics is None:
        return None
    return skill_check(athletics.value, char.physical_modifier() + DIFFICULT)
