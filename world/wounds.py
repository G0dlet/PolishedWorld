"""
Wounds: what a hit location has left, what its wound is called, what
`health` shows, which location a d20 names, and how long a bleeding body has.

Wounds Decomposition, Task WN-T2; the locks are the Combat Design's §4.4
(WN1-WN4) and the rules are *Legend* core pp. 11 and 144-146.

The arithmetic works from numbers alone, and the module imports nothing
from Evennia. The functions that read and write a character are the seam:
`health_of` for every reader (WN-T3), and four doors for every writer --
`damage`, `heal`, `room_to_heal`, `restore_at_respawn` -- with `is_dead`
beside them (WN-T4). Until WN-T5 all of them reach the `health` trait, and
only through `_health_trait`; WN-T5 changes what is behind them.

The damage is what is stored (WN1); Hit Points are worked out from it on
every read, against the maximum `world.body.hit_points_max` gives for the
character's CON + SIZ now. A location with no damage has no key.
"""

import math
from fractions import Fraction

from world.body import LOCATIONS

# Head, chest and abdomen: a Serious Wound there knocks out, a Major Wound
# kills at once on a lost test, and the clock is counted in rounds (p. 146).
# The other four of `body.LOCATIONS` are limbs.
VITAL = ("head", "chest", "abdomen")

# Where damage lands, besides a key of `body.LOCATIONS` (WO5): every
# location at once (starvation, thirst; WN5, WN6), or one the hit location
# table picks. Checked from WN-T4; used from WN-T5.
ALL = "all"
RANDOM = "random"

# The wound levels (pp. 145-146). Identifiers, not the words a player reads
# (those are OQ-WN5's).
INTACT = "intact"     # no damage
MINOR = "minor"       # Hit Points still positive
SERIOUS = "serious"   # 0 Hit Points or below
MAJOR = "major"       # a negative score equal to the starting Hit Points or worse

# WN3: a minute is 60 real seconds. Not twelve combat rounds of CT2's
# ROUND_SECONDS: that constant is the dial for a fight's text volume, and
# must not move how long a friend has to reach a wounded body.
MINUTE = 60

# WN4: the book's five-second round, the wound module's own constant for the
# vital clock -- for the same reason it is not ROUND_SECONDS.
VITAL_ROUND_SECONDS = 5

# The 1D20 table for a humanoid (p. 145): each row's highest roll and the
# location it names, lowest first.
_HIT_LOCATION_TABLE = (
    (3, "right_leg"),
    (6, "left_leg"),
    (9, "abdomen"),
    (12, "chest"),
    (15, "right_arm"),
    (18, "left_arm"),
    (20, "head"),
)

# The health words, copied from the `health` trait's `descs`
# (typeclasses/characters.py, at_object_creation). Each key is an inclusive
# upper bound on the percentage `health` shows; above the top key, the top
# word. The trait goes in WN-T6 (WN2b) and the table lives on here.
HEALTH_WORDS = {
    0: "dead",
    10: "near death",
    25: "critically wounded",
    50: "badly hurt",
    75: "injured",
    90: "bruised",
    100: "healthy",
}


def hit_points(maximum, damage):
    """A location's Hit Points: the maximum less the damage, below 0 if so."""
    return maximum - damage


def level(maximum, damage):
    """
    The wound level of a location (pp. 145-146).

    Args:
        maximum (int): the location's maximum Hit Points.
        damage (int): the damage stored on it, 0 or more.

    Returns:
        str: INTACT, MINOR, SERIOUS or MAJOR.
    """
    if damage <= 0:
        return INTACT
    left = hit_points(maximum, damage)
    if left > 0:
        return MINOR
    if left <= -maximum:
        return MAJOR
    return SERIOUS


def margin(maximum, damage):
    """
    What a location has left before a Major Wound, out of all it had (WN2).

    A location can take twice its maximum before the Major Wound, so the
    whole is 2 x maximum: unhurt is the whole, a location at 0 is half, and
    0 is a Major Wound. Past it the margin stays at 0.

    Returns:
        tuple: (left, whole), both int.
    """
    whole = 2 * maximum
    return max(0, whole - damage), whole


def health(maxima, damages):
    """
    The figure `health` shows: the worst location's margin (WN2).

    The worst is the lowest fraction left, compared exactly; on a tie the
    first location in `body.LOCATIONS` is the one shown.

    Args:
        maxima (Mapping): location -> maximum Hit Points, for all seven.
        damages (Mapping): location -> damage; a missing key is unhurt.

    Returns:
        tuple: (left, whole, percent), the percent a float, not rounded.
    """
    worst = None
    for key in LOCATIONS:
        left, whole = margin(maxima[key], damages.get(key, 0))
        fraction = Fraction(left, whole)
        if worst is None or fraction < worst[0]:
            worst = (fraction, left, whole)
    _fraction, left, whole = worst
    return left, whole, 100 * left / whole


def check_location(location):
    """
    Refuse a place damage cannot land on (WO5).

    Raises:
        ValueError: unless `location` is `ALL`, `RANDOM` or a key of
            `body.LOCATIONS`.
    """
    if location in (ALL, RANDOM) or location in LOCATIONS:
        return
    raise ValueError(
        f"{location!r} is not a place for damage: wounds.ALL, wounds.RANDOM "
        "or a key of world.body.LOCATIONS"
    )


def _health_trait(char):
    """
    The `health` trait, or None. The module's one reach into it (WN-T3's
    census), so WN-T5 removes one line and not six.
    """
    traits = getattr(char, "traits", None)
    return traits.get("health") if traits is not None else None


def health_of(char):
    """
    What the screens print for a character's health: (current, max, percent).

    The one reader of health for `status`, `sheet`, the `char` snapshot and
    `Character.health_desc()` (WN-T3). It reads the `health` trait for now;
    WN-T5 changes what is behind it and nothing in front. Current and max
    are whole numbers, truncated as `status` has always printed them; the
    percentage is not rounded (the screens format it).

    Callers reach it as `wounds.health_of(...)`, through the module, so a
    test can stand in for it at one place.

    Returns:
        tuple or None: (int, int, float); None for an object with no health
            to read.
    """
    trait = _health_trait(char)
    if trait is None:
        return None
    return int(trait.value), int(trait.max), trait.percent(formatting=None)


def is_dead(char):
    """
    True when the body's hurt is fatal: today the trait at its minimum.

    WN-T5 makes it a vital location at a Major Wound from an `ALL` source
    (WO7, WN5). An object with no body to read is not dead.
    """
    trait = _health_trait(char)
    return trait is not None and trait.current <= trait.min


def damage(char, amount, location):
    """
    Put `amount` of hurt on the body, at `location` (WO5).

    The door behind `Character.apply_health_damage`, its one caller in
    production; the writer runs the death and pushes (tests/test_client_state
    holds both). The place is checked first, before the amount is looked at,
    so a wrong place fails on every call. Until WN-T5 every place lands on
    the trait whole: the policy is checked and not yet used.

    Nothing is written for an amount of 0 or less, an object with no body,
    or a body already dead -- a death in progress or resolved this tick.

    Raises:
        ValueError: from `check_location`, before anything is written.

    Returns:
        bool: True if hurt was written.
    """
    check_location(location)
    if amount <= 0:
        return False
    trait = _health_trait(char)
    if trait is None or trait.current <= trait.min:
        return False
    trait.current -= amount
    return True


def room_to_heal(char):
    """
    How many points natural healing could still give: 0 when unhurt, None
    for an object with no body to read (WN10 makes it the largest damage on
    any location, at WN-T5).
    """
    trait = _health_trait(char)
    if trait is None:
        return None
    return max(0, math.ceil(trait.max - trait.current))


def heal(char, points):
    """
    Mend up to `points`, never past an unhurt body; returns what landed.

    The door behind `world.healing.accrue`, which keeps the counter and
    pushes. The trait would clamp at its maximum on its own; the cap here is
    what keeps the returned number true, since callers report it.

    Returns:
        int: points mended (0 or more).
    """
    room = room_to_heal(char)
    if not room or points <= 0:
        return 0
    landed = min(points, room)
    trait = _health_trait(char)
    trait.current = trait.current + landed
    return landed


def restore_at_respawn(char):
    """
    What death gives back of the body: today, full health (WN9 at WN-T5 and
    WN-T8: the damage emptied, *maimed* and *severed* kept). Called from the
    restore block of `Character.at_character_death`, whose push_soon of all
    four domains sends it.
    """
    trait = _health_trait(char)
    if trait is not None:
        trait.current = trait.max


def location_for(roll):
    """
    The location a 1D20 roll names on the humanoid table (p. 145).

    Raises:
        ValueError: for a roll outside 1-20.
    """
    if not 1 <= roll <= 20:
        raise ValueError(f"a 1D20 roll is 1-20, not {roll}")
    for top, key in _HIT_LOCATION_TABLE:
        if roll <= top:
            return key


def clock_seconds(con, pow_, location):
    """
    How long an untreated Major Wound takes to kill, in real seconds (WN4).

    A limb: CON + POW minutes. Head, chest and abdomen: half CON + POW
    rounds (p. 146). At CON + POW 21, 1260 s and 52.5 s.

    Raises:
        ValueError: for a key that is not one of `body.LOCATIONS`.
    """
    if location not in LOCATIONS:
        raise ValueError(f"{location!r} is not a hit location")
    if location in VITAL:
        return (con + pow_) / 2 * VITAL_ROUND_SECONDS
    return (con + pow_) * MINUTE


def word_for(percent):
    """
    The health word for the percentage `health` shows.

    Read as `Character.health_desc()` reads the trait's table: the keys in
    sorted order, each an inclusive upper bound, the top word above the top
    key.
    """
    word = ""
    for bound in sorted(HEALTH_WORDS):
        word = HEALTH_WORDS[bound]
        if percent <= bound:
            return word
    return word
