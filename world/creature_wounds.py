"""
world/creature_wounds.py
========================
A creature's hurt (Creatures decomposition, slice CE; Combat Design CR1,
CR2). CE-T1: its numbers, read on demand. CE-T2: the door, and death at
minus the Critical Wound rating (CE5, CE9). CE-T3: the state at 0 Hit
Points, on stored points in time (CE6).

A creature has General Hit Points, not a character's seven locations: the
book keeps locational Hit Points for major villains (core p. 146). What is
stored is `con` and `siz`, set by the creature's prototype (CE3), and, for
the few species whose printed row leaves the formula, `resilience` (CE7).
Everything here is worked out at the read, and the readers write nothing.

    general_hit_points_of(creature) -> int, or None without CON  (p. 146; CE4)
    critical_rating_of(creature)    -> int, or None without CON  (p. 146)
    resilience_of(creature)         -> int, or None without CON  (Monsters p. 12)
    armour_points_of(creature)      -> int, its natural armour   (CE9)
    damage_of(creature)             -> int, the damage it carries (CE3)
    hit_points_of(creature)         -> int, what is left, or None without CON
    state_of(creature)              -> {"kind", "due"}, or None  (CE6)
    damage(creature, amount, location, made=None, *, source=None)
                                    -> the door behind Creature.apply_health_damage

A creature without CON -- the class default is None (CE13) -- has no
numbers: the first three answer None and never raise, so whatever only shows
something can show nothing for it. Armour does not depend on CON, so
`armour_points_of` always answers. Refusing to hurt such a creature is the
door's (CE-T2), not the readers'.

The arithmetic over integers is `world.body`'s, as `wounds.maxima_of` leaves
it to `body.hit_points_max`. The module is imported whole (`from world import
body`), so its readers, which end in `_of`, never shadow body's functions.

What the door stores is this module's, as `body_damage` is `world.wounds`'s,
and no class declares it (CE-T2's STOPP 0): `general_damage`, the damage
taken -- not the Hit Points left (CE3) -- and `damage_source`, the latest
blow's source. Neither row exists until the door writes it, so a creature
without `general_damage` is unhurt. Read the damage through `damage_of`,
never the row: from CE-T5 the stored figure is not yet healed.

The state at 0 (CE6) is `hurt_state`, one row holding {"kind", "due"} so
the two are never read half-changed. The kind names what happens at `due`,
a `time.time()`: STANDING tests Resilience again, DYING dies. The one
persistent alarm, `_state_due`, carries the pair it was set for and does
nothing unless the stored state is still that pair and its time has come,
as `wounds._clock_due` does; so a death, `hunt` or a later state needs no
handle on the task.
"""

import time

from evennia.objects.objects import DefaultObject
from evennia.utils.utils import delay

from world import body, wounds
from world.skillcheck import skill_check

# The door's two Attributes (CE-T2). Not `body_damage`: a creature has no
# body of seven locations, and that name is the wound module's -- the push
# census in tests/test_client_state.py holds every write to it.
DAMAGE = "general_damage"
SOURCE = "damage_source"

# CE6: two calibration constants, real seconds, the module's own -- not
# CT2's ROUND_SECONDS, the dial for a fight's text (WN3's reason). The
# book's round (core p. 125), and a Combat Action as the round at 2 (CT2);
# a species' own Combat Actions are OQ-CE2's.
ROUND_SECONDS_AT_ZERO = 5
ACTION_SECONDS_AT_ZERO = 2.5

# The state at 0 (CE-T3's STOPP 0). Identifiers, not words a player reads.
STATE = "hurt_state"
STANDING = "standing"   # at 0 or below; `due` is the next Resilience test
DYING = "dying"         # senseless at 0 or below; `due` is its death

# The room's line when the test is lost (CE12; Tone Guide §5): what someone
# there sees and hears, not the game's word. The death has its own line in
# `Creature.at_death`.
FALL_ROOM = "{key} sags onto its side, breathing fast and shallow."


def general_hit_points_of(creature):
    """
    The creature's General Hit Points, the average of CON and SIZ rounded up
    (core p. 146; Creatures CE4). The maximum: what is left is the door's.

    Returns:
        int, or None for a creature without CON (CE13).
    """
    con = creature.con
    if con is None:
        return None
    return body.general_hit_points(con, creature.siz)


def critical_rating_of(creature):
    """
    The creature's Critical Wound rating, half its General Hit Points rounded
    up (core p. 146).

    Returns:
        int, or None for a creature without CON (CE13).
    """
    hit_points = general_hit_points_of(creature)
    if hit_points is None:
        return None
    return body.critical_rating(hit_points)


def resilience_of(creature):
    """
    The creature's Resilience: its stored `resilience`, else CON x 3 + 10
    (Monsters of Legend p. 12: "generally", with some creatures higher or
    lower; Creatures CE7). Five of the book's twenty animals carry their own.

    Without CON the answer is None even if a `resilience` is stored: a
    creature without CON has no numbers, and Resilience is only tested at
    0 Hit Points, which it cannot reach.

    Returns:
        int, or None for a creature without CON (CE13).
    """
    con = creature.con
    if con is None:
        return None
    stored = creature.resilience
    if stored is not None:
        return stored
    return con * 3 + 10


def armour_points_of(creature):
    """
    The creature's Armour Points: today its natural armour, `natural_ap`
    (Creatures CE9: the one reader, which the caller asks for the blow and
    the door for the Critical Wound table). It does not depend on CON.

    Returns:
        int
    """
    return creature.natural_ap


def damage_of(creature):
    """
    The damage the creature carries: its stored `general_damage`, 0 when it
    has none (CE3: without the row it is unhurt). It writes nothing.

    Returns:
        int
    """
    return creature.attributes.get(DAMAGE, default=0)


def hit_points_of(creature):
    """
    The creature's Hit Points left: its General Hit Points less its damage,
    through `wounds.hit_points`, below 0 if so -- death is at minus the
    Critical Wound rating (CE5), and the state at 0 reads how far down it
    stands (CE6).

    Returns:
        int, or None for a creature without CON (CE13).
    """
    maximum = general_hit_points_of(creature)
    if maximum is None:
        return None
    return wounds.hit_points(maximum, damage_of(creature))


def state_of(creature):
    """
    The creature's state at 0 Hit Points as a plain dict, {"kind": STANDING
    or DYING, "due": a time.time()}, or None when it has none (CE6). It
    writes nothing.
    """
    stored = creature.attributes.get(STATE)
    if not stored:
        return None
    return {"kind": stored["kind"], "due": stored["due"]}


def _set_state(creature, kind, seconds):
    """Store a state due `seconds` from now and set its one alarm."""
    due = time.time() + seconds
    creature.attributes.add(STATE, {"kind": kind, "due": due})
    delay(seconds, _state_due, creature, kind, due, persistent=True)


def _test(creature):
    """
    The Resilience test at 0 (p. 146): a plain test with no modifier
    (CE6, CE7) -- not against the attack roll, as a character's wound is.
    Won, the creature stands a round more; lost, it falls senseless, the
    room is told, and it dies its rating in Combat Actions on.

    Returns:
        dict: the `skill_check` dict.
    """
    test = skill_check(resilience_of(creature))
    if test["success"]:
        _set_state(creature, STANDING, ROUND_SECONDS_AT_ZERO)
    else:
        _set_state(creature, DYING,
                   critical_rating_of(creature) * ACTION_SECONDS_AT_ZERO)
        if creature.location:
            creature.location.msg_contents(FALL_ROOM.format(key=creature.key))
    return test


def _state_due(creature, kind, due):
    """
    The alarm (persistent; module-level). It takes a creature that is gone
    -- None after a reload, a pk of None in the same process (§4, P1) --
    and does nothing unless the stored state is still `(kind, due)` and that
    time has passed; fired a little early, it sets itself again for what is
    left. Then a STANDING creature tests again, and a DYING one dies: the
    stored source is its killer only if it is an object that stands in the
    creature's room now (CE9), else nobody is.
    """
    if creature is None or not creature.pk:
        return
    state = state_of(creature)
    if state is None or state["kind"] != kind or state["due"] != due:
        return
    left = due - time.time()
    if left > 0:
        delay(left, _state_due, creature, kind, due, persistent=True)
        return
    if kind == STANDING:
        _test(creature)
        return
    source = creature.attributes.get(SOURCE)
    here = creature.location
    killer = (source if isinstance(source, DefaultObject)
              and here is not None and source.location == here else None)
    creature.at_death(killer)


def damage(creature, amount, location, made=None, *, source=None):
    """
    Put `amount` of hurt on the creature and answer for it: the door behind
    `Creature.apply_health_damage`, its one caller, which carries out the
    death (CE9). The amount is what got through the armour (WO6), and is
    written whole: a creature has no *Glancing Blow* (Hero Points are a
    character's).

    Everything is checked before anything is written, in this order, and
    all but the last whatever the amount, so a wrong call fails on every
    call: the place (`wounds.check_location`, WO5; it is checked and not
    used, since General Hit Points have no locations); an attack roll with
    `wounds.ALL`, which has none (WN5); an attack roll that is not a
    success; a creature already deleted, which answers None -- two blows in
    one tick, the first of which killed, are a race and not a wrong call;
    a creature without CON (CE13); an amount of 0 or less, which answers
    None.

    The stored damage grows by the amount, and `damage_source` becomes this
    blow's source: a None removes the row, so it always says what the
    latest call said (CE9; the alarm reads it).

    A blow that leaves the creature at 0 or below, and alive, tests
    Resilience if it has no state yet (`_test`, CE6). One that finds a state
    keeps it: no test, and no time moved -- an earlier death is not bought
    back.

    Args:
        made (dict or None): the attack roll's successful `skill_check`
            dict, when the source has one. Read only for whether the hit
            was critical (CE-T4).
        source (Object, str or None): what dealt the blow, as a character's
            door takes it.

    Raises:
        ValueError: as above, before anything is written.

    Returns:
        dict or None: None if nothing was written; else, always all four:
            {"dies": bool, at minus the Critical Wound rating or below (CE5),
             "hit_points": int, what is left after the blow,
             "test": the Resilience test's dict if this blow rolled it, else
                 None,
             "state": the kind stored after the blow, else None}.
    """
    wounds.check_location(location)
    if made is not None:
        if location == wounds.ALL:
            raise ValueError("an ALL source has no attack roll to test against (WN5)")
        if not made.get("success"):
            raise ValueError("a wound is tested against a successful attack roll")
    if not creature.pk:
        return None
    if creature.con is None:
        raise ValueError(
            f"{creature.key} has no CON and cannot be hurt (Creatures CE13): "
            "its prototype must set `con`"
        )
    if amount <= 0:
        return None
    total = damage_of(creature) + amount
    creature.attributes.add(DAMAGE, total)
    if source is None:
        creature.attributes.remove(SOURCE)
    else:
        creature.attributes.add(SOURCE, source)
    left = wounds.hit_points(general_hit_points_of(creature), total)
    answer = {"dies": left <= -critical_rating_of(creature), "hit_points": left,
              "test": None, "state": None}
    if answer["dies"]:
        return answer
    if left <= 0 and state_of(creature) is None:
        answer["test"] = _test(creature)
    state = state_of(creature)
    answer["state"] = state["kind"] if state else None
    return answer
