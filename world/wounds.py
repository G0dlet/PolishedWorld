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
`SEVERED` (WN-T8). A third, `db.wound_unconscious`, holds a wound's
unconsciousness while it lasts (WN-T9), a fourth, `db.wound_clocks`, a
Major Wound's deadline per location (WN-T10), and a fifth, `db.wound_tended`,
the set of locations that have had a won First Aid test, emptied for a
location when it is whole and for all at respawn (Healing HL-T7; HL7, 2).
One thing is kept in `ndb` and not in `db`: `ndb.wound_treatment`, the
treatments under way, which the clock's alarm asks before it kills and
which dies with the timed-action slot at a reload (Healing HL-T8; HL4).
Slice HL adds two doors for one location: `mend`, and `restore_use` for
First Aid's Serious row (HL7, 4). A missing Attribute is an unhurt,
unmarked, waking body with no clock and no mark. Readers test for a
`Mapping`, never a `dict` (a stored dict comes back as a `_SaverDict`), and
for a `Set`, never a `set` (a stored set comes back as a `_SaverSet`);
writers assign a fresh dict or set and never change one in place, and
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

from collections.abc import Mapping, Set
from fractions import Fraction
from random import randint

from evennia.utils import gametime
from evennia.utils.utils import delay

from world import hero_points, skill_base, timed_actions
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

# A wound's unconsciousness (WN-T9; OQ-WN5's lines, Adam 2026-11-23). Room
# lines name the body through `$You()`, as the collapse's do (world/fatigue.py).
KNOCKED_OUT = "The pain closes over you, and the world goes dark."
KNOCKED_OUT_ROOM = "$You() crumples and lies still."
COME_TO = "You come to on the cold ground, the pain still there."
COME_TO_ROOM = "$You() stirs and comes to."
# Every refusal while out, whatever line the caller passed: the collapse's
# "Your hands will not obey you." is a waking body's (Wounds WN-T9, choice D).
OUT_COLD = "You lie senseless where you fell."

# A Major Wound's clock (WN-T10; OQ-WN5's lines, Adam 2026-11-23): said when
# it starts -- until WN-T11 nothing else tells a player one runs -- and
# when it runs out, before the death's own lines.
CLOCK_START = "Blood comes fast, and it will not stop on its own."
CLOCK_OUT = "The cold spreads from the wound, and you stop fighting it."
CLOCK_OUT_ROOM = "$You() gives a last shudder and is still."

# WN3: a minute is 60 real seconds. Not twelve combat rounds of CT2's
# ROUND_SECONDS: that constant is the dial for a fight's text volume, and
# must not move how long a friend has to reach a wounded body.
MINUTE = 60

# WN4: the book's five-second round, the wound module's own constant for the
# vital clock -- for the same reason it is not ROUND_SECONDS.
VITAL_ROUND_SECONDS = 5

# HL4: how long a due clock's alarm waits before it asks again while its
# location is being treated -- and so how soon after a treatment lost past
# the deadline the body dies. The wound module's own constant, for the same
# reason VITAL_ROUND_SECONDS is: it must not move with the vital clock.
TREATMENT_RECHECK_SECONDS = 5

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

# The health words, first the `health` trait's `descs` (gone with the trait,
# WN-T6, WN2b). Each key is an inclusive upper bound on the percentage
# `health` shows; above the top key, the top word. 0 % is a Major Wound
# somewhere (WN2), which a living body can carry since WN-T8 -- and still
# after a clock is stopped -- so its word is not *dead* (OQ-WN5, WN-T11).
HEALTH_WORDS = {
    0: "grievously wounded",
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


def health_shown(char):
    """
    What the screens print for health: (shown, 100, percent) -- `status`,
    `sheet` and the `char` snapshot's `current` and `max` (OQ-WN8 (a),
    Wounds WN-T11).

    `health_of`'s pair is the worst location's margin, and its whole is
    twice that location's maximum, so it changed its whole with the
    location it named (*8/8* to *5/6*, and *3/6* to *4/8* as a body got
    worse). Out of 100 it reads like the gauges beside it; where the hurt
    is, `report` says. The percentage is rounded down, so 100 is only an
    unhurt body and 0 only a Major Wound.

    Returns:
        tuple or None: (int, 100, float); None for an object with no body.
    """
    reading = health_of(char)
    if reading is None:
        return None
    left, whole, percent = reading
    return left * 100 // whole, 100, percent


# What `report` calls a location's level and state (OQ-WN5, WN-T11).
# Minor and intact have no word: the Hit Points say it.
LEVEL_WORDS = {SERIOUS: "serious wound", MAJOR: "major wound"}
STATE_WORDS = {DISABLED: "useless", MAIMED: "maimed", SEVERED: "severed"}
BLEEDING = "bleeding out"


def _left(deadline):
    """A running clock's time left, as the player reads it: whole minutes."""
    minutes = int(minutes_until(deadline))
    return f"{minutes} min" if minutes >= 1 else "under a minute"


def report(char):
    """
    Where a body is badly hurt, one line per location (WN11, Wounds WN-T11).

    A location is listed when it is at a Serious Wound or worse, has a
    state, or has a running clock -- in `body.LOCATIONS`' order, never the
    stored damage's. A body with only Minor Wounds has no line: a starving
    body has seven, and the health figure already says so. Each line is the
    location's name, its Hit Points (the book's, below 0 if so) and what is
    worth saying: the level, the state, the clock.

        left arm    -1/4  serious wound, useless

    Only reads: `status` and `sheet` call it while the body may be out.

    Returns:
        list of str: empty for an unhurt body or an object with no body.
    """
    maxima = maxima_of(char)
    if maxima is None:
        return []
    damages, states, clocks = damage_of(char), states_of(char), clocks_of(char)
    lines = []
    for key in LOCATIONS:
        hurt = damages.get(key, 0)
        word = LEVEL_WORDS.get(level(maxima[key], hurt))
        parts = [word] if word else []
        if key in states:
            parts.append(STATE_WORDS[states[key]])
        if key in clocks:
            parts.append(f"{BLEEDING} ({_left(clocks[key])})")
        if not parts:
            continue
        name = key.replace("_", " ")
        lines.append(f"{name:<11}{hit_points(maxima[key], hurt):>3}/{maxima[key]:<3}"
                     + ", ".join(parts))
    return lines


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

    The one reader of health for `status`, `sheet`, the `char` snapshot
    (through `health_shown`, out of 100 since WN-T11) and
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


def _wound(char, key, maximum, damage_now, amount, made, *, glancing):
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

    `amount` is the damage this blow wrote, after any *Glancing Blow* trim
    (HE1 b). A trimmed 0 -- a location already one short of a Major Wound,
    hit again -- is still a wound to answer for: the test is made, and a
    lost one knocks no one out, since nothing was sustained (HE1 c).
    `glancing` (keyword-only, no default) says whether this blow was
    trimmed, and is carried into the outcome for ML to read.

    Returns:
        dict: {
            "location", "level",
            "test": the test's dict, or None with no `made`,
            "state": the state this wound sets, or None,
            "unconscious" (bool), "minutes": how long, or None for as long
                as the clock runs (WN-T9 carries it out),
            "clock" (bool): a Major Wound's clock (WN-T10 starts it),
            "dies" (bool): a vital Major Wound and a lost test,
            "glancing" (bool): a Hero Point turned a Major Wound into this
                Serious one (HE1),
        }
    """
    wound_level = level(maximum, damage_now)
    if wound_level not in (SERIOUS, MAJOR):
        return None
    test = resilience_test(char, made) if made is not None else None
    lost = test is not None and not test["resisted"]
    vital = key in VITAL
    outcome = {"location": key, "level": wound_level, "test": test, "state": None,
               "unconscious": False, "minutes": None, "clock": False, "dies": False,
               "glancing": glancing}
    if wound_level == SERIOUS:
        if vital:
            # Unconscious for the damage of the attack, in minutes (WN3) --
            # the damage written, so none for a trimmed 0 (HE1 b, c).
            knocked = lost and amount > 0
            outcome.update(unconscious=knocked, minutes=amount if knocked else None)
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

    *Glancing Blow* (HE1, HE2, HE6 a): a blow to a named or random location
    that would take it from below a Major Wound to one asks
    `hero_points.take_for_glancing`, after every refusal above; on True the
    blow is trimmed so the location stands one short of a Major Wound
    (2 x max - 1, core p. 88), and the trimmed amount is what is written and
    what `_wound` answers for. A location already at a Major Wound, a blow
    that stays below one, and `ALL` do not ask.

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
    before = damages.get(key, 0)
    glancing = (level(maxima[key], before) != MAJOR
                and level(maxima[key], before + amount) == MAJOR
                and hero_points.take_for_glancing(char))
    if glancing:
        # One Hit Point less than a Major Wound would need (p. 88; HE1).
        amount = 2 * maxima[key] - 1 - before
    damages[key] = before + amount
    char.db.body_damage = {name: value for name, value in damages.items() if value}
    wound = _wound(char, key, maxima[key], damages[key], amount, made, glancing=glancing)
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
    on any location without a running clock (WN10; p. 87, a Major Wound does
    not heal until treated, and stopping the clock is the treatment), 0 when
    nothing of that is hurt, None for an object with no body to read.
    """
    if maxima_of(char) is None:
        return None
    clocked = clocks_of(char)
    return max((value for key, value in damage_of(char).items() if key not in clocked),
               default=0)


def heal(char, points):
    """
    Mend `points` intervals' worth: a point from every hurt location per
    interval, never below unhurt (WN10), and none from a location whose clock
    runs (WN-T10); returns the intervals that landed.

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
    clocked = clocks_of(char)
    left = {key: value if key in clocked else value - landed
            for key, value in damage_of(char).items()
            if key in clocked or value > landed}
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
    # A location made whole loses its First Aid mark (HL7, 2; Healing
    # HL-T7): *until it has fully healed* (p. 50).
    tended = tended_of(char)
    if tended - set(left):
        kept_marks = tended & set(left)
        if kept_marks:
            char.db.wound_tended = set(kept_marks)
        else:
            char.attributes.remove("wound_tended")
    return landed


def _check_one(location):
    """
    Refuse anything but one location: the doors for one location take no
    `ALL` or `RANDOM` (Healing HL-T7).

    Raises:
        ValueError: unless `location` is a key of `body.LOCATIONS`.
    """
    if location not in LOCATIONS:
        raise ValueError(f"{location!r} is not a key of world.body.LOCATIONS")


def tended_of(char):
    """
    The locations that have had a won First Aid test, as a frozenset; empty
    for an unmarked body (HL7, 2; Healing HL-T7).

    A stored set comes back as a `_SaverSet`, which is a `Set` and not a
    `set`, so the test is for the abstract class, as it is `Mapping` for the
    dicts. A stored name that is not a location is not returned. The reader
    does not filter by damage: the writers keep the mark off a whole
    location, and a test that reads the mark must see it if they do not.
    """
    stored = char.attributes.get("wound_tended") if hasattr(char, "attributes") else None
    if not isinstance(stored, Set):
        return frozenset()
    return frozenset(key for key in stored if key in LOCATIONS)


def mark_tended(char, location):
    """
    Mark a hurt location as having had its First Aid (HL7, 2: a location
    that has had First Aid *cannot benefit from First Aid again until it has
    fully healed*, p. 50). Only a won test marks; the caller (Healing HL-T9)
    decides that, and this writes.

    An unhurt location is refused, so the mark never stands on a whole
    location -- the rule `heal`, `mend` and `restore_at_respawn` keep by
    emptying it. A new blow leaves the mark as it is: the location has not
    fully healed. Nothing in the snapshot shows the mark, so the census
    keeps the write in NOT_PANEL.

    Raises:
        ValueError: for anything but a key of `body.LOCATIONS`.

    Returns:
        bool: True when the location was marked now; False when it was
            already marked or has no damage.
    """
    _check_one(location)
    tended = tended_of(char)
    if location in tended or location not in damage_of(char):
        return False
    char.db.wound_tended = set(tended | {location})
    return True


def mend(char, location, points):
    """
    Mend `points` Hit Points on one location, never past unhurt; returns the
    points that landed (HL7, 1; Healing HL-T7). First Aid's door: 1D3 on an
    injured location, 1 on a Serious Wound (Healing HL-T9).

    A location whose clock runs is refused and nothing is written, as `heal`
    skips it (WN10): the Major row stops the clock and gives no points.
    *Disabled* goes when the location is above 0 Hit Points, as in `heal`
    (p. 145); the Serious row's use of a limb at 0 or below is
    `restore_use`'s and not this door's. *Maimed* and *severed* are never
    taken. A location made whole loses its mark. Like the other doors it
    pushes nothing: its caller does (WN-T4).

    Raises:
        ValueError: for anything but a key of `body.LOCATIONS`.

    Returns:
        int: points that landed (0 when refused, unhurt, or `points` <= 0).
    """
    _check_one(location)
    maxima = maxima_of(char)
    if maxima is None or points <= 0 or location in clocks_of(char):
        return 0
    damages = damage_of(char)
    had = damages.get(location, 0)
    if not had:
        return 0
    landed = min(points, had)
    left = {key: value - landed if key == location else value
            for key, value in damages.items()
            if key != location or value > landed}
    if left:
        char.db.body_damage = left
    else:
        char.attributes.remove("body_damage")
    states = states_of(char)
    if (states.get(location) == DISABLED
            and hit_points(maxima[location], left.get(location, 0)) > 0):
        kept = {key: state for key, state in states.items() if key != location}
        if kept:
            char.db.wound_states = kept
        else:
            char.attributes.remove("wound_states")
    tended = tended_of(char)
    if location in tended and location not in left:
        kept_marks = tended - {location}
        if kept_marks:
            char.db.wound_tended = set(kept_marks)
        else:
            char.attributes.remove("wound_tended")
    return landed


def restore_use(char, location):
    """
    Give a limb its use back whatever its Hit Points: *disabled* is taken
    from the location (HL7, 4; Healing HL-T7). First Aid's Serious row --
    the limb works again (p. 50) -- with its point or without, since a
    Starving or Dehydrated body gets none (HL7, 5; Healing HL-T9).

    Two rules meet here. `heal` and `mend` let *disabled* go only above 0
    Hit Points (p. 145, the wound's own rule); the book's First Aid row
    gives the use back at 0 or below. This door is that row and nothing
    else, so its caller is the one place the second rule is applied.

    *Maimed* and *severed* are never taken: a Major Wound is surgery's
    (HL9). The damage is not touched. Nothing in the snapshot moves (the
    panel shows health, which is the damage), so the census keeps the
    writes in NOT_PANEL. `gear.held` reads an arm lazily (GR22): what the
    hand held when the arm was disabled is held again, if still carried.

    Raises:
        ValueError: for anything but a key of `body.LOCATIONS`.

    Returns:
        bool: True when *disabled* was taken.
    """
    _check_one(location)
    states = states_of(char)
    if states.get(location) != DISABLED:
        return False
    kept = {key: state for key, state in states.items() if key != location}
    if kept:
        char.db.wound_states = kept
    else:
        char.attributes.remove("wound_states")
    return True


def restore_at_respawn(char):
    """
    What death gives back of the body (WN9): the damage is emptied,
    *disabled* is cleared, since every location is whole again, and a
    wound's unconsciousness ends without a waking line -- the death says
    what happened; the marks of First Aid go with the damage (HL7, 2;
    Healing HL-T7); *maimed* and *severed* stay. Called from the restore
    block of `Character.at_character_death`, which knows none of the
    Attributes and whose push_soon of all four domains sends it.
    """
    char.attributes.remove("body_damage")
    char.attributes.remove("wound_unconscious")
    char.attributes.remove("wound_clocks")
    char.attributes.remove("wound_tended")
    states = states_of(char)
    kept = {key: state for key, state in states.items() if state != DISABLED}
    if kept != states:
        if kept:
            char.db.wound_states = kept
        else:
            char.attributes.remove("wound_states")


def _now():
    """
    The server's runtime, `gametime.runtime()`: the one reader of *now* for
    a stored deadline and the end of a wound's unconsciousness (HL11). It
    stands still while the server is down, so a stop runs no clock; while
    the server is up it passes as real time does, so `delay` keeps its
    seconds. Tests patch this function (Healing Decomposition §6, HL-T1).
    """
    return gametime.runtime()


def knock_out(char, location, minutes):
    """
    A wound knocks the body out for `minutes` real minutes (p. 145; WN3).

    The door behind `Character.apply_health_damage`, its one caller in
    production, which pushes. The time it ends is stored in
    `db.wound_unconscious` -- {"location", "until"}, `until` a `_now()`
    -- and that stored time is the truth (§2's second choice): the alarm,
    `delay(..., persistent=True)` to `_wake_due`, only wakes the check. It
    is not `db.collapsed`, whose refusal arms fatigue's recovery (§2's third
    choice): a wound's waking is its own.

    Whatever the timed-action slot held is interrupted, as `collapse()`
    does. A body already out stays out until the later of the two times,
    and is not told it goes dark a second time.

    Returns:
        bool: True when the body was not already out.
    """
    now = _now()
    until = now + minutes * MINUTE
    current = _unconscious_record(char)
    already = current is not None and current["until"] > now
    if already and current["until"] >= until:
        return False
    timed_actions.interrupt(char)
    char.db.wound_unconscious = {"location": location, "until": until}
    delay(until - now, _wake_due, char, until, persistent=True)
    if not already:
        char.msg(KNOCKED_OUT)
        if char.location:
            char.location.msg_contents(KNOCKED_OUT_ROOM, from_obj=char, exclude=char)
    return not already


def _unconscious_record(char):
    """The stored unconsciousness as a plain dict, or None."""
    stored = char.attributes.get("wound_unconscious") if hasattr(char, "attributes") else None
    if not isinstance(stored, Mapping) or "until" not in stored:
        return None
    return dict(stored)


def unconscious(char):
    """
    True while a wound keeps the body out (WN-T9).

    Answered from the stored time, so nothing depends on the alarm having
    fired: a time that has passed is cleared here, and the body comes to
    (`_come_to`) -- the first reader after the time is the one that wakes it.

    Except while a clock is due: a body whose clock has run out is dying,
    and it stays out until the clock's own alarm (`_clock_due`) kills it. A
    survived vital Major Wound is out until its deadline (WN-T10, choice A),
    so the waking and the death fall due together, and two alarms due
    together fire in either order -- WN-T10's in-game check heard the body
    come to before it died. Any location's clock counts, not only the one
    that knocked the body out. Nothing is woken and nothing is killed here.
    """
    record = _unconscious_record(char)
    if record is None:
        return False
    now = _now()
    if now < record["until"]:
        return True
    if any(deadline <= now for deadline in clocks_of(char).values()):
        return True
    _come_to(char)
    return False


def _wake_due(char, until):
    """
    The alarm (persistent; a module-level function, so the task handler can
    save it). It reads the stored time again and does nothing unless the
    time it was set for is still the stored one and has passed: a later
    knock-out, a death or a revive has made it stale. A body with a clock
    due is not woken but left to that clock's alarm (`unconscious`), and
    this alarm is not set again: the death removes what it would read.
    """
    record = _unconscious_record(char)
    if record is None or record["until"] != until:
        return
    left = until - _now()
    if left > 0:   # early: the task's wall-clock date came first (HL11)
        delay(left, _wake_due, char, until, persistent=True)
        return
    unconscious(char)


def _come_to(char):
    """
    The body wakes: the Attribute goes first, then the lines; a body whose
    player has gone turns to stone once nothing holds it (WN-T10, choice B).
    """
    char.attributes.remove("wound_unconscious")
    char.msg(COME_TO)
    if char.location:
        char.location.msg_contents(COME_TO_ROOM, from_obj=char, exclude=char)
    _stone_if_released(char)


def _stone_if_released(char):
    """A body with no player and no hold becomes the statue it would have been."""
    if not getattr(char, "has_account", True) and not holds_body(char):
        turn = getattr(char, "turn_to_stone", None)
        if turn is not None:
            turn()


def holds_body(char):
    """
    True while a wound holds the body in the world: a running clock, or a
    wound's unconsciousness whose time has not passed (WN4; OQ-WN6). Only
    reads -- it is `is_statue`'s question, asked while others look, and it
    wakes and kills no one (Wounds WN-T10, choice C).
    """
    if clocks_of(char):
        return True
    record = _unconscious_record(char)
    return record is not None and _now() < record["until"]


def minutes_until(deadline):
    """Real minutes from now to `deadline` (a `_now()`), never below 0."""
    return max(0.0, (deadline - _now()) / MINUTE)


def clocks_of(char):
    """The running clocks as a plain dict, location -> deadline (`_now()`)."""
    stored = char.attributes.get("wound_clocks") if hasattr(char, "attributes") else None
    if not isinstance(stored, Mapping):
        return {}
    return {key: float(value) for key, value in stored.items() if value is not None}


def start_clock(char, location):
    """
    A Major Wound's clock starts (p. 146; WN4): (CON + POW) minutes for a
    limb, half (CON + POW) rounds for head, chest and abdomen, as a stored
    deadline in `db.wound_clocks`, with a persistent alarm to `_clock_due`
    carrying the deadline. A location whose clock already runs keeps its
    earlier deadline: a second wound does not buy time.

    The door behind `Character.apply_health_damage`, its one caller in
    production, which pushes.

    Returns:
        float: the location's deadline.
    """
    clocks = clocks_of(char)
    if location in clocks:
        return clocks[location]
    now = _now()
    seconds = clock_seconds(int(char.stats.con.value), int(char.stats.pow.value), location)
    deadline = now + seconds
    clocks[location] = deadline
    char.db.wound_clocks = clocks
    delay(seconds, _clock_due, char, location, deadline, persistent=True)
    char.msg(CLOCK_START)
    return deadline


def _notes_of(char):
    """The treatments noted on a patient, location -> (healer, marker)."""
    notes = getattr(getattr(char, "ndb", None), "wound_treatment", None)
    return dict(notes) if isinstance(notes, Mapping) else {}


def _believed(char, note):
    """
    A note is believed while its marker is the healer's live action and the
    healer stands in the patient's room. `is_current` is asked first: it
    empties the slot of a healer with no player.
    """
    healer, marker = note
    if not timed_actions.is_current(healer, marker):
        return False
    return char.location is not None and healer.location == char.location


def being_treated(char, location):
    """
    True while `location` of `char` is being treated now (HL4; Healing
    HL-T8): a note for that location whose marker is still the healer's
    live action (`timed_actions.is_current`, which compares by `is`), with
    the healer in the patient's room -- a patient who walks away is no
    longer being treated, though the healer's time has not run out. Another
    location's note answers nothing here: treating an arm does not hold the
    head's clock.

    Not quite a pure read. `is_current` empties the slot of a healer with no
    player, so this may be the first to notice that the healer has gone and
    write that much (timed_actions.py, *what an unpuppeted character means
    here*). The note itself is not changed.
    """
    note = _notes_of(char).get(location)
    return note is not None and _believed(char, note)


def note_treatment(char, location, healer, marker):
    """
    Note on the patient that `healer` is treating `location` now, with the
    marker `timed_actions.start` gave the healer (HL4; Healing HL-T8, §2's
    third choice). The treatment's own record is the healer's slot, and the
    clock's alarm holds the patient, so the task that starts a treatment
    (HL-T10) writes this note and the alarm reads it through
    `being_treated`.

    The note is `char.ndb.wound_treatment`, location -> (healer, marker),
    a fresh dict on every write, and holds the marker object itself, since
    `is_current` compares by identity. Nothing is stored in `db`: the note
    dies with the slot at a reload, and the alarm then rings as it would
    have (HL4). A note no longer believed is dropped when the next is
    written. The census holds this function as the note's one writer
    (`TestPushCensus.WOUND_NDB_WRITES`).

    Raises:
        ValueError: for anything but a key of `body.LOCATIONS`.

    Returns:
        bool: True when the treatment was noted; False when another is
            believed for that location -- a second healer on the same
            location is refused (HL4).
    """
    _check_one(location)
    if being_treated(char, location):
        return False
    notes = {key: note for key, note in _notes_of(char).items() if _believed(char, note)}
    notes[location] = (healer, marker)
    char.ndb.wound_treatment = notes
    return True


def _clock_due(char, location, deadline):
    """
    The alarm (persistent; module-level). It reads the deadline again and
    does nothing unless that location's stored deadline is still the one it
    was set for and has passed -- a stopped clock, a death or a later clock
    has made it stale. An early alarm sets itself for what is left, so a
    treatment before the deadline buys no time. Past the deadline it asks
    whether the location is being treated now (`being_treated`); if it is,
    it sets itself again `TREATMENT_RECHECK_SECONDS` on, persistent and with
    the same deadline, and returns (HL4; Healing HL-T8). A reload empties
    the note and the alarm then kills as it would have. Otherwise the body
    is told and dies (WO3); the death's restore removes every clock, so a
    second alarm finds nothing and the body is not killed again where it
    came back (WN9).
    """
    if clocks_of(char).get(location) != deadline:
        return
    left = deadline - _now()
    if left > 0:   # early: the task's wall-clock date came first (HL11)
        delay(left, _clock_due, char, location, deadline, persistent=True)
        return
    if being_treated(char, location):   # HL4: it waits and asks again
        delay(TREATMENT_RECHECK_SECONDS, _clock_due, char, location, deadline,
              persistent=True)
        return
    char.msg(CLOCK_OUT)
    if char.location:
        char.location.msg_contents(CLOCK_OUT_ROOM, from_obj=char, exclude=char)
    char.at_character_death(killer="wound")


def stop_clock(char, location):
    """
    Stop a location's clock: the deadline is removed, so its alarm finds
    nothing (§2's second choice). The function slice HL calls (treatment,
    p. 87); nothing calls it in WN. A body with no player turns to stone once
    nothing holds it.

    Returns:
        bool: True when there was a clock.
    """
    clocks = clocks_of(char)
    if location not in clocks:
        return False
    del clocks[location]
    if clocks:
        char.db.wound_clocks = clocks
    else:
        char.attributes.remove("wound_clocks")
    _stone_if_released(char)
    return True


def revive(char):
    """
    Bring a body knocked out by a wound round now (p. 87: *the restoration
    of a single Hit Point ... will revive them*). Written here for slice HL;
    nothing calls it in WN.

    Returns:
        bool: True when there was a body to revive.
    """
    if _unconscious_record(char) is None:
        return False
    _come_to(char)
    return True


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
