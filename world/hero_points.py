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
- `db.hero_progress` -- game seconds towards the next point (HE4). Absent
  at CAP: the counter does not run there.
- `db.hero_glancing_off` -- present only while the player has switched
  *Glancing Blow* off (HE3). Missing means on.

This module is the only writer of those three Attributes (P-2), through
three doors, each with one caller in production:
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

# Sent by the survival tick when at least one point lands (HE7 b; OQ-HE2,
# chosen at HE-T2's STOPP 0). No number in it (Tone Guide §7) and no count,
# since a span can land two: `hero` shows the number. The second sentence
# names the book's term, so a player can find the command that shows it --
# nothing else shows Hero Points unasked (no meter, no `status` row, HE7).
EARNED = "The hard days behind you have left you steadier. Your Hero Points have grown."


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


def accrue(char, game_seconds):
    """
    Add a span of game time played to the character's counter, and turn
    whole game days into Hero Points, up to CAP (HP4, HE4).

    The module's first door; its one caller in production is the survival
    tick (`survival_ticker._deplete_character`), with the same `elapsed` it
    gives natural healing (HE4 b). Every tick counts, whatever the body is
    doing (HE4 a). Nothing is pushed: no snapshot shows Hero Points (HE7;
    CL will have to push `char` here when the panel does).

    Order matters and each step is a lock:
      1. At CAP the counter does not run: its Attribute is removed if it is
         there, and nothing is added (HE4 d). A counter that filled and
         waited would be a cap of five by another name.
      2. A span of 0 or less adds nothing and writes nothing (the first tick
         after a puppet or a reload gives 0: time is lost, never gained).
      3. The span is added; whole days become points, up to the room left
         below CAP; the remainder is carried -- unless CAP was reached, when
         the Attribute is removed (1's rule, applied at once).

    Args:
        char (Character): the character.
        game_seconds (int or float): game seconds since the last call for
            them; read as a whole number, as healing reads it.

    Returns:
        int: Hero Points that landed (0 or more). The tick says one line
            when this is above 0, however many landed.
    """
    held = points(char)
    if held >= CAP:
        if char.attributes.has("hero_progress"):
            char.attributes.remove("hero_progress")
        return 0
    span = int(game_seconds)
    if span <= 0:
        return 0
    days, remainder = divmod((char.db.hero_progress or 0) + span, GAME_SECONDS_PER_POINT)
    landed = min(days, CAP - held)
    if landed:
        char.db.hero_points = held + landed
    if held + landed >= CAP:
        char.attributes.remove("hero_progress")
    else:
        char.db.hero_progress = remainder
    return landed


def set_glancing(char, on):
    """
    Switch *Glancing Blow* on or off for the character (HE3).

    The module's second door; its one caller in production is the `hero`
    command. Off is stored as `db.hero_glancing_off = True`; on is the
    Attribute removed, never a stored False, so "on" has one form: missing
    (HE3, HE6 b). The decision is made on what `glancing_on` reads, in the
    same call as the write, and a switch already where it is asked to be
    writes nothing. It is a choice and not an act: nothing here asks whether
    the body can act (HE3). Nothing is pushed (HE7).

    Args:
        char (Character): the character.
        on (bool): True to switch it on, False to switch it off.

    Returns:
        bool: True when the switch changed, False when it already stood
            where it was asked to be (and nothing was written).
    """
    if bool(on) == glancing_on(char):
        return False
    if on:
        char.attributes.remove("hero_glancing_off")
    else:
        char.db.hero_glancing_off = True
    return True


def take_for_glancing(char):
    """
    Spend a Hero Point on *Glancing Blow*, if the character has one and has
    not switched it off (HP2, HE1, HE6 a).

    The module's third door; its one caller in production is
    `wounds.damage`, which asks only for a blow that would take a location
    from below a Major Wound to one, after every refusal, and trims the blow
    when the answer is True. The point is taken here, in the same call that
    answers, so a point taken and a blow trimmed cannot come apart. The last
    point leaves a stored 0 (HE6 b). Nothing is pushed (HE7); the writer
    behind `wounds.damage` pushes `char` for the blow.

    Args:
        char (Character): the character the blow lands on.

    Returns:
        bool: True when a point was taken (the blow is to be trimmed);
            False, with nothing written, when there is none or the switch is
            off.
    """
    held = points(char)
    if held <= 0 or not glancing_on(char):
        return False
    char.db.hero_points = held - 1
    return True
