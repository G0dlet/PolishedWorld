"""
world/client_state.py
=====================
What each webclient panel shows for a character, as four snapshots, and
the one function that sends them (W4.1; decisions WC5, WC6, WC8, WC9).

Every snapshot is built only from readers the text stream already uses,
so a panel cannot say something `status`, `inventory` or `look` does not
(WC1):

    char      name, health (status's numbers and health_desc()),
              encumbrance (inventory's one read of carried/limit/band)
    survival  hunger, thirst, fatigue (status's numbers and trait.desc())
    world     absolute game seconds, TIME_FACTOR, server wall-clock ms,
              global weather, and the calendar tables the browser needs
              to advance and name the time itself (WC9)
    room      the room's name, whether it is indoors, and look's three
              lists for this viewer (exits, characters, things)

Wire format (lock 1B): `obj.msg(<domain>=((snapshot,), {}))` reaches the
browser as `[domain, [snapshot], {"options": {}}]`. The snapshot rides in
args[0] because the server adds an `options` key to every message's
kwargs (evennia/server/sessionhandler.py:280) and the webclient's
encode_default passes it on.

Every gauge is {"current": int, "max": int, "desc": str} or None when the
trait is missing; every name is plain text (markup stripped), so the
browser writes it with textContent.

`push` runs inside hooks, where an exception can turn a completed action
into a failure the player is told about (objects.py:1331, at_post_move).
It therefore never raises: each domain is built and sent on its own, and
a domain that fails is logged and skipped while the others still go out
(lock 6B).

Where a push is made (W4.2, WC8). Commands, the survival tick, chargen's
end and the weather change push at once, with `push`, after their last
write. Hooks that run in the middle of a `move_to` or a `delete()` -- the
leave hooks, `at_object_delete`, death's relocation, puppet and unpuppet --
use `push_soon` and `push_room_soon` instead, which send on the next
reactor turn (`delay(0, ...)`): `at_object_leave` runs before the object
has moved (objects.py:1290; `location` is set at :1305), so a snapshot
built there would still show it, while one built a moment later reads the
settled world through the same readers `look` and `inventory` use (W4.2
lock 1B). Pending sends are coalesced per character and domain, and per
room, in `ndb`, so a burst of moves (`drop all`) costs one snapshot each.
Every site is pinned by an AST census in tests/test_client_state.py.
"""

import time

from django.conf import settings
from evennia.contrib.base_systems import custom_gametime as _cgt
from evennia.utils import logger
from evennia.utils.ansi import strip_ansi, strip_mxp
from evennia.utils.utils import delay, inherits_from

from world import encumbrance, gametime_utils, room_text, weather

DOMAINS = ("char", "survival", "world", "room")

SURVIVAL_GAUGES = ("hunger", "thirst", "fatigue")


# ----------------------------------------------------------------------
# Shared readers
# ----------------------------------------------------------------------

def _plain(text):
    """A display string as the browser shows it: no links, no colour codes."""
    return strip_ansi(strip_mxp(str(text)))


def _gauge(trait, desc):
    """
    One gauge as `status` prints it: whole numbers, truncated (`int()` is
    what commands/character_commands.py `_whole` does), and its label.
    """
    return {"current": int(trait.value), "max": int(trait.max), "desc": desc}


def _trait(char, key):
    """The trait `key`, or None when the character has no such trait."""
    traits = getattr(char, "traits", None)
    if traits is None:
        return None
    return traits.get(key)


# ----------------------------------------------------------------------
# The four builders
# ----------------------------------------------------------------------

def inventory_lists(char):
    """
    What `inventory` lists, as the inventory panel shows it (W7.1).

    Split on `db.worn` as the clothing contrib's `inventory` splits
    (clothing.py:668, :679); a wear style is a truthy string there
    (clothing.py:487), so a restyled garment stays worn. Grouped by display
    name through `room_text.numbered_names`, the helper the room's things
    read -- not by name and description as `inventory`'s table groups: a
    garment's condition is in its description (DurableObject
    .get_display_desc) and wear changes it without a push, so two cloaks
    are one row here and two in the text (lock 2). Container contents,
    condition, wear style and covered layers are left out: `inventory`
    prints none of them, so wear, `cover` and `uncover` need no push.
    """
    carried, worn = [], []
    for obj in char.contents:
        (worn if obj.db.worn else carried).append(obj)
    return {
        "carried": [_plain(name) for name in room_text.numbered_names(carried, char)],
        "worn": [_plain(name) for name in room_text.numbered_names(worn, char)],
    }


def char_snapshot(char):
    """
    Name, health, the encumbrance band (WC12) and what is carried and worn
    (W7.1 lock 1: one snapshot, so the lists and the figure always agree).

    Health's label is `char.health_desc()`, not `trait.desc()`: the two
    disagree (desc() reads the absolute value against bounds shaped for a
    percentage), and `status` prints health_desc(). The encumbrance numbers
    are read once each and the band is computed from those reads, as the
    `inventory` command does, so the three can never disagree.
    """
    health = _trait(char, "health")
    carried = encumbrance.carried_enc(char)
    limit = encumbrance.enc_limit(char)
    return {
        "name": _plain(char.get_display_name(char)),
        "health": None if health is None else _gauge(health, char.health_desc()),
        "encumbrance": {
            "carried": carried,
            "limit": limit,
            "band": encumbrance.band(carried, limit),
        },
        "inventory": inventory_lists(char),
    }


def survival_snapshot(char):
    """Hunger, thirst and fatigue, each with the gauge's own description."""
    snap = {}
    for key in SURVIVAL_GAUGES:
        trait = _trait(char, key)
        snap[key] = None if trait is None else _gauge(trait, trait.desc())
    return snap


def _calendar():
    """
    The tables the browser needs to turn game seconds into the date the
    `world.gametime_utils` readers would give, so nothing is duplicated in
    JS (W5.3). Built as lists: JSON has no sets and only string keys.

    units         [[name, seconds], ...] largest first, the divisors
                  custom_gametime() uses (sorted, the 1-second unit dropped)
    month_names   index 0 is display month 1, from get_month_name()
    seasons       {season: [display months]}
    times_of_day  [[period, start, end], ...] day fractions, in the order
                  get_time_of_day() tries them
    """
    units = sorted(
        ((name, seconds) for name, seconds in _cgt.UNITS.items() if seconds != 1),
        key=lambda pair: pair[1],
        reverse=True,
    )
    months = _cgt.UNITS["year"] // _cgt.UNITS["month"]
    return {
        "units": [[name, seconds] for name, seconds in units],
        "month_names": [gametime_utils.get_month_name(m) for m in range(1, months + 1)],
        "seasons": {
            season: sorted(month_list)
            for season, month_list in gametime_utils._SEASONS.items()
        },
        "times_of_day": [
            [period, start, end]
            for period, ranges in gametime_utils.TIMES_OF_DAY.items()
            for start, end in ranges
        ],
    }


def world_snapshot():
    """
    The world clock and weather (WC9). The same for every character: the
    room snapshot's `indoor` tells the browser whether to show the weather.
    """
    return {
        "game_seconds": gametime_utils.get_absolute_gametime(),
        "time_factor": settings.TIME_FACTOR,
        "server_ms": int(time.time() * 1000),
        "weather": weather.get_current_weather(),
        "calendar": _calendar(),
    }


def room_snapshot(room, viewer):
    """
    The viewer's location as `look` lists it for that viewer (WC8): names
    depend on the looker, so this is built once per viewer.

    exits are [{"name", "key"}] -- the key is what a click sends (W5.4,
    web/static/polishedworld/js/pw_room.js); characters are awake characters
    other than the viewer; things are look's 'You see:' entries, grouped
    things first, then statues of logged-out characters. The lists come
    from `world.room_text.room_lists`, the one helper the Room's display
    hooks read too (W5.4 lock 4C). No room gives the empty shape, so the
    browser clears.
    """
    if room is None:
        return {"name": None, "indoor": False, "exits": [], "characters": [], "things": []}
    lists = room_text.room_lists(room, viewer)
    things = lists["things"] + [s.get_display_name(viewer) for s in lists["statues"]]
    return {
        "name": _plain(room.get_display_name(viewer)),
        "indoor": bool(room.db.is_indoor),
        "exits": [{"name": _plain(ex.get_display_name(viewer)), "key": ex.key}
                  for ex in lists["exits"]],
        "characters": [_plain(c.get_display_name(viewer)) for c in lists["characters"]],
        "things": [_plain(name) for name in things],
    }


# ----------------------------------------------------------------------
# Sending
# ----------------------------------------------------------------------

def _build(domain, obj):
    """The snapshot for one domain. Looked up per call, so tests can patch a builder."""
    if domain == "char":
        return char_snapshot(obj)
    if domain == "survival":
        return survival_snapshot(obj)
    if domain == "world":
        return world_snapshot()
    if domain == "room":
        return room_snapshot(getattr(obj, "location", None), obj)
    raise ValueError(f"unknown client-state domain {domain!r}")


def push(obj, *domains, session=None):
    """
    Send each named domain's snapshot to `obj` (to one session if given).

    Never raises: a domain whose builder or send fails is logged and
    skipped, the rest still go out. Domains are sent in the order given.
    """
    for domain in domains:
        try:
            obj.msg(session=session, **{domain: ((_build(domain, obj),), {})})
        except Exception:
            logger.log_trace(f"client_state: could not push {domain!r} to {obj!r}")


def push_room(room):
    """
    Push `room` to every character in it that has a session, each its own
    snapshot (names depend on the looker, WC8). Statues have no session and
    get nothing. Never raises: one viewer's failure is logged by `push`.
    """
    if room is None:
        return
    try:
        viewers = [
            obj for obj in room.contents_get(content_type="character")
            if obj.sessions.all()
        ]
    except Exception:
        logger.log_trace(f"client_state: could not list viewers in {room!r}")
        return
    for viewer in viewers:
        push(viewer, "room")


def push_online(*domains):
    """
    Push `domains` to every puppeted character, once each however many
    sessions it has (the survival ticker's dedupe). Never raises.
    """
    from evennia import SESSION_HANDLER

    seen = set()
    try:
        sessions = list(SESSION_HANDLER.get_sessions())
    except Exception:
        logger.log_trace("client_state: could not list sessions")
        return
    for sess in sessions:
        char = getattr(sess, "puppet", None)
        if not char or char.id in seen:
            continue
        seen.add(char.id)
        push(char, *domains)


# ----------------------------------------------------------------------
# Sending on the next reactor turn (hook sites, W4.2 lock 1B)
# ----------------------------------------------------------------------

def _gone(obj):
    """True when `obj` has been deleted since the send was scheduled."""
    return obj is None or getattr(obj, "id", None) is None


def _pending(obj):
    """The set of keys `obj` has a send scheduled for (in ndb, never saved)."""
    pending = obj.ndb.client_state_pending
    if pending is None:
        pending = set()
        obj.ndb.client_state_pending = pending
    return pending


def _schedule(obj, key, callback, *args):
    """Schedule `callback(*args)` once per `key` on `obj`. Never raises."""
    try:
        pending = _pending(obj)
        if key in pending:
            return
        pending.add(key)
        delay(0, callback, *args)
    except Exception:
        logger.log_trace(f"client_state: could not schedule {key!r} for {obj!r}")
        try:
            _pending(obj).discard(key)
        except Exception:
            pass


def _send_soon(obj, domain):
    """The scheduled half of `push_soon`."""
    if _gone(obj):
        return
    _pending(obj).discard(domain)
    push(obj, domain)


def _send_room_soon(room):
    """The scheduled half of `push_room_soon`."""
    if _gone(room):
        return
    _pending(room).discard("room-fan-out")
    push_room(room)


def push_soon(obj, *domains):
    """
    `push(obj, *domains)` on the next reactor turn, each domain at most
    once however often it is asked for before then. For hook sites only.
    """
    if _gone(obj):
        return
    for domain in domains:
        _schedule(obj, domain, _send_soon, obj, domain)


def push_room_soon(room):
    """`push_room(room)` on the next reactor turn, coalesced per room."""
    if _gone(room):
        return
    _schedule(room, "room-fan-out", _send_room_soon, room)


def push_after_removal(location):
    """
    Something left `location` without a leave hook (it was deleted). The
    first character up the location chain carried it, so its `char` panel
    changes; if `location` is a room, its viewers' room lists change.
    """
    try:
        holder = location
        for _depth in range(10):   # nesting is shallow (WD5); the cap is a guard
            if holder is None:
                break
            if inherits_from(holder, settings.BASE_CHARACTER_TYPECLASS):
                push_soon(holder, "char")
                break
            holder = holder.location
        if location is not None and inherits_from(location, settings.BASE_ROOM_TYPECLASS):
            push_room_soon(location)
    except Exception:
        logger.log_trace(f"client_state: could not push after removal from {location!r}")
