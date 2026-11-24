"""
Hero Points (Combat Design §4.13, HP1-HP4 and HE1-HE8; Hero Points
decomposition, Task HE-T1).

Legend gives an Adventurer two Hero Points at the start (core p. 87) and
lets one be spent, for good, to turn a Major Wound into a Serious one
(*Glancing Blow*, p. 88). This module is where a character's points live.

What it stores, on the character, and nothing else (HE6):

- `db.hero_points` -- how many points the character holds, a whole number.
  **Missing means START**: nothing is written at creation, so a character
  made before Hero Points existed has two like any other (no backfill, no
  migration). **Zero is stored as 0** and never removed, so a character who
  has spent every point is not handed two again.
- `db.hero_progress` -- game seconds towards the next point (HE4; written
  from HE-T2).
- `db.hero_glancing_off` -- present only while the player has switched
  *Glancing Blow* off (HE3). Missing means on.

This module is the only writer of those three Attributes (P-2), through
three doors added by later tasks, each with one caller in production:
`accrue` (the survival tick, HE-T2), `set_glancing` (the `hero` command,
HE-T3) and `take_for_glancing` (`wounds.damage`, HE-T6).

It imports nothing from the game's own packages. `world.wounds` will import
this module; the other direction would be a cycle, and a census in
`tests/test_hero_points.py` holds it out (HE6).
"""

# Two Hero Points at creation, as the book (HP1; Legend core p. 87).
START = 2

# The most a character holds: the most the book awards for one story
# (HP4; p. 87 awards zero to four at a story's close and sets no cap).
CAP = 4

# One point per game day the survival tick gives the character: 24 game
# hours, 6 real hours at TIME_FACTOR 4 (HE4 c). A calibration constant
# (OQ-HE3); the length of a story behind it is this project's assumption.
GAME_SECONDS_PER_POINT = 24 * 3600


def points(char):
    """
    How many Hero Points the character holds.

    Args:
        char (Character): the character to read.

    Returns:
        int: the stored number, or START when nothing is stored. The test is
            `is None`, never `or START`: a stored 0 is a character who has
            spent every point, and must read 0 (HE6 b).
    """
    stored = char.db.hero_points
    if stored is None:
        return START
    return stored


def glancing_on(char):
    """
    Whether *Glancing Blow* is on for the character.

    On is the default, and a missing Attribute means on (HE3): the
    Attribute exists only while the player has switched it off.

    Args:
        char (Character): the character to read.

    Returns:
        bool: True unless `db.hero_glancing_off` is set.
    """
    return not char.db.hero_glancing_off
