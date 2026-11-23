"""
Wounds: what a hit location has left, what its wound is called, what
`health` shows, which location a d20 names, and how long a bleeding body has.

Wounds Decomposition, Task WN-T2; the locks are the Combat Design's §4.4
(WN1-WN4) and the rules are *Legend* core pp. 11 and 144-146.

The arithmetic works from numbers alone. The functions that read and write a
character are the seam: `health_of` for every reader (WN-T3), and four doors
for every writer -- `damage`, `heal`, `room_to_heal`, `restore_at_respawn`
(WN-T4). Behind them are two Attributes (WN1), each a plain dict holding only
the locations that have something: `db.body_damage`, location to a whole
number (WN-T5), and `db.wound_states`, location to `DISABLED`, `MAIMED` or
`SEVERED` (WN-T8). A missing Attribute is an unhurt, unmarked body. Readers
test for a `Mapping`, never a `dict` (a stored dict comes back as a
`_SaverDict`); writers assign a fresh dict and never change one in place, and
remove the Attribute when nothing is left. The `health` trait is not read.

The damage is what is stored (WN1); Hit Points are worked out from it on
every read, against the maximum `world.body.hit_points_max` gives for the
character's CON + SIZ now. A location with no damage has no key.

What a blow's wound does (WN-T8, pp. 145-146) is answered by the call that
made it, not read back from the stored body: `damage` returns an outcome
whose `dies` says whether this call kills, because a won Resilience test
at a vital Major Wound leaves the same damage as a lost one and only the
lost one is death (Wounds WN-T8, choice A).
"""

from collections.abc import Mapping
from fractions import Fraction
from random import randint

from world import skill_base
from world.body import LOCATIONS, hit_points_max
from world.skillcheck import opposed_against

# Head, chest and abdomen: a Serious Wound there knocks out, a Major Wound
# kills at once on a lost test, and the clock is counted in rounds (p. 146).
# The other four of `body.LOCATIONS` are limbs.
VITAL = ("head", "chest", "abdomen")

# Where damage lands, besides a key of `body.LOCATIONS` (WO5): every
# location at once (starvation, thirst; WN5, WN6), or one the hit location
# table picks (pp. 144-145).
ALL = "all"
RANDOM = "random"

# The wound levels (pp. 145-146). Identifiers, not the words a player reads
# (those are OQ-WN5's).
INTACT = "intact"     # no damage
MINOR = "minor"       # Hit Points still positive
SERIOUS = "serious"   # 0 Hit Points or below
MAJOR = "major"       # a negative score equal to the starting Hit Points or worse

# The stored states (WO2), set by a lost test or a Major Wound and kept in
# `db.wound_states`. A heavier state replaces a lighter one, never the other
# way round: a maimed leg wounded again stays maimed.
DISABLED = "disabled"   # a limb useless until it is above 0 Hit Points (p. 145)
MAIMED = "maimed"       # a Major Wound, kept through death (WN9)
SEVERED = "severed"     # a limb's Major Wound, while SEVERED_ENABLED
_STATE_WEIGHT = {DISABLED: 1, MAIMED: 2, SEVERED: 3}

# roadmap Rev 20: *severed* is built and switched off. On, a limb's Major
# Wound gives it in place of *maimed* (WO2); off, every Major Wound maims.
SEVERED_ENABLED = False

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


def maxima_of(char):
    """
    The seven locations' maximum Hit Points for the character's CON + SIZ
    now (BD7, `body.hit_points_max`), or None for an object without both.
    """
    stats = getattr(char, "stats", None)
    if stats is None:
        return None
    con, siz = stats.get("con"), stats.get("siz")
    if con is None or siz is None:
        return None
    return hit_points_max(int(con.value), int(siz.value))


def damage_of(char):
    """
    The stored damage as a plain dict, location -> int; empty when unhurt.

    Only hurt locations are kept, so a key with 0 is never returned.
    """
    stored = char.attributes.get("body_damage") if hasattr(char, "attributes") else None
    if not isinstance(stored, Mapping):
        return {}
    return {key: int(value) for key, value in stored.items() if value}


def health_of(char):
    """
    What the screens print for a character's health: (current, max, percent).

    The one reader of health for `status`, `sheet`, the `char` snapshot and
    `Character.health_desc()` (WN-T3). Since WN-T5 it is WN2's figure: the
    worst location's margin to a Major Wound, out of twice its maximum, from
    the stored damage and the maxima for CON + SIZ now. The old trait is not
    read, so a character made before WN with its trait at 3/20 and no damage
    reads 100 % (WN2b).

    Callers reach it as `wounds.health_of(...)`, through the module, so a
    test can stand in for it at one place.

    Returns:
        tuple or None: (int, int, float); None for an object with no body
            to read.
    """
    maxima = maxima_of(char)
    if maxima is None:
        return None
    return health(maxima, damage_of(char))


def states_of(char):
    """
    The stored states as a plain dict, location -> `DISABLED`, `MAIMED` or
    `SEVERED`; empty for an unmarked body (WO2, WN1).
    """
    stored = char.attributes.get("wound_states") if hasattr(char, "attributes") else None
    if not isinstance(stored, Mapping):
        return {}
    return {key: value for key, value in stored.items() if value in _STATE_WEIGHT}


def _vital_major(maxima, damages):
    """
    True when head, chest or abdomen is at a Major Wound: an `ALL` source's
    death (WO7, WN5), which has no test to win. A limb at a Major Wound is
    not death.
    """
    return any(level(maxima[key], damages.get(key, 0)) == MAJOR for key in VITAL)


def _dying(char):
    """A death in progress: `Character.at_character_death`'s own guard."""
    return bool(getattr(getattr(char, "ndb", None), "_dying", False))


def resilience_test(char, made):
    """
    The wound's Resilience test: an opposed test against the attack roll
    that made the wound (p. 145), the resisting side's modifier the whole of
    `char.physical_modifier()` read now (WN7, closing OQ-SC1).

    Returns `opposed_against`'s dict whole, `resisting` included: that is
    the winner's own `skill_check` dict WN8's improvement call will take
    when it lands with ML. No improvement call is made here yet, and nothing
    is pushed (the doors push nothing; WN-T4, choice A).
    """
    return opposed_against(
        made, skill_base.value_of(char, "resilience"), char.physical_modifier()
    )


def _wound(char, key, maximum, damage_now, amount, made):
    """
    What one blow's wound on one location calls for (pp. 145-146), or None
    for a location the blow left above 0 Hit Points.

    A wound is answered by the call that made it: a location already below 0
    is tested again when it is hit again (*Resilience rolls are not repeated
    unless the location is wounded again*). With no `made` there is no test
    (OQ-WN1) and nothing a lost test brings -- no *disabled*, no
    unconsciousness from a Serious Wound, no death at once -- while what the
    wound gives whatever the test still comes: *maimed*, and a Major Wound's
    unconsciousness and clock (Wounds WN-T8, choice B).

    Returns:
        dict: {
            "location", "level",
            "test": the test's dict, or None with no `made`,
            "state": the state this wound sets, or None,
            "unconscious" (bool), "minutes": how long, or None for as long
                as the clock runs (WN-T9 carries it out),
            "clock" (bool): a Major Wound's clock (WN-T10 starts it),
            "dies" (bool): a vital Major Wound and a lost test,
        }
    """
    wound_level = level(maximum, damage_now)
    if wound_level not in (SERIOUS, MAJOR):
        return None
    test = resilience_test(char, made) if made is not None else None
    lost = test is not None and not test["resisted"]
    vital = key in VITAL
    outcome = {"location": key, "level": wound_level, "test": test, "state": None,
               "unconscious": False, "minutes": None, "clock": False, "dies": False}
    if wound_level == SERIOUS:
        if vital:
            # Unconscious for the damage of the attack, in minutes (WN3).
            outcome.update(unconscious=lost, minutes=amount if lost else None)
        elif lost:
            outcome["state"] = DISABLED
        return outcome
    outcome["state"] = SEVERED if (SEVERED_ENABLED and not vital) else MAIMED
    if vital:
        # Drops unconscious whatever the test; a lost one is death at once.
        outcome.update(dies=lost, unconscious=not lost, clock=not lost)
    else:
        # A limb: unconscious from the agony on a lost test, for the damage
        # in minutes as a Serious Wound's (WN-T9); the clock either way.
        outcome.update(unconscious=lost, minutes=amount if lost else None, clock=True)
    return outcome


def damage(char, amount, location, made=None):
    """
    Put `amount` of hurt on the body, at `location` (WO5), and answer for
    the wound it makes.

    The door behind `Character.apply_health_damage`, its one caller in
    production; the writer runs the death and pushes (tests/test_client_state
    holds both). The place and the roll are checked first, before the amount
    is looked at, so a wrong call fails on every call.

    `ALL` adds the amount to every location, a limb stopping at its maximum
    (Hit Points 0, WO7; a limb already past it from a blow keeps what it
    has). It sets no state and calls for no test (WN5), and kills when a
    vital location is at a Major Wound (WO7). A key of `body.LOCATIONS` adds
    to that location; `RANDOM` to the one the hit location table names for
    a 1D20. A location such a blow leaves at 0 Hit Points or below is a
    wound to answer for (`_wound`): its state is stored, the heavier
    replacing the lighter, and only a lost test at a vital Major Wound kills.

    Nothing is written for an amount of 0 or less, an object with no body,
    or a body whose death is in progress (`ndb._dying`).

    Args:
        made (dict or None): the attack roll's successful `skill_check`
            dict, when the source has one.

    Raises:
        ValueError: from `check_location`; for a `made` that is not a
            success (the book always opposes a successful roll, p. 145);
            for a `made` with `ALL`, which has no attack roll (WN5). All
            before anything is written.

    Returns:
        dict or None: None if nothing was written; else {"dies": bool,
            "wounds": [what `_wound` gives for the location wounded, if any]}.
    """
    check_location(location)
    if made is not None:
        if location == ALL:
            raise ValueError("an ALL source has no attack roll to test against (WN5)")
        if not made.get("success"):
            raise ValueError("a wound is tested against a successful attack roll")
    if amount <= 0:
        return None
    maxima = maxima_of(char)
    if maxima is None or _dying(char):
        return None
    damages = damage_of(char)
    if location == ALL:
        for key in LOCATIONS:
            total = damages.get(key, 0) + amount
            if key not in VITAL:
                total = min(total, max(damages.get(key, 0), maxima[key]))
            damages[key] = total
        char.db.body_damage = {key: value for key, value in damages.items() if value}
        return {"dies": _vital_major(maxima, damages), "wounds": []}
    key = location_for(randint(1, 20)) if location == RANDOM else location
    damages[key] = damages.get(key, 0) + amount
    char.db.body_damage = {name: value for name, value in damages.items() if value}
    wound = _wound(char, key, maxima[key], damages[key], amount, made)
    if wound is None:
        return {"dies": False, "wounds": []}
    if wound["state"]:
        states = states_of(char)
        old = states.get(key)
        if old is None or _STATE_WEIGHT[wound["state"]] > _STATE_WEIGHT[old]:
            states[key] = wound["state"]
            char.db.wound_states = states
    return {"dies": wound["dies"], "wounds": [wound]}


def room_to_heal(char):
    """
    How many intervals natural healing could still use: the largest damage
    on any location (WN10), 0 when unhurt, None for an object with no body
    to read.
    """
    if maxima_of(char) is None:
        return None
    return max(damage_of(char).values(), default=0)


def heal(char, points):
    """
    Mend `points` intervals' worth: a point from every hurt location per
    interval, never below unhurt (WN10); returns the intervals that landed.

    The door behind `world.healing.accrue`, which keeps the counter and
    pushes. What is returned is what callers report -- one for an interval
    that mended seven locations, since it is one interval's line.

    Returns:
        int: intervals that mended something (0 or more).
    """
    room = room_to_heal(char)
    if not room or points <= 0:
        return 0
    landed = min(points, room)
    left = {key: value - landed for key, value in damage_of(char).items() if value > landed}
    if left:
        char.db.body_damage = left
    else:
        char.attributes.remove("body_damage")
    # *Disabled* lasts until the location is above 0 Hit Points again
    # (p. 145); healing is what raises a location, so healing clears it.
    states = states_of(char)
    if any(state == DISABLED for state in states.values()):
        maxima = maxima_of(char)
        kept = {key: state for key, state in states.items()
                if state != DISABLED or hit_points(maxima[key], left.get(key, 0)) <= 0}
        if kept != states:
            if kept:
                char.db.wound_states = kept
            else:
                char.attributes.remove("wound_states")
    return landed


def restore_at_respawn(char):
    """
    What death gives back of the body (WN9): the damage is emptied and
    *disabled* is cleared, since every location is whole again; *maimed*
    and *severed* stay. Called from the restore block of
    `Character.at_character_death`, which knows neither Attribute and whose
    push_soon of all four domains sends it.
    """
    char.attributes.remove("body_damage")
    states = states_of(char)
    kept = {key: state for key, state in states.items() if state != DISABLED}
    if kept != states:
        if kept:
            char.db.wound_states = kept
        else:
            char.attributes.remove("wound_states")


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
