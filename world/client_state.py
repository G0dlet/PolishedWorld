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

`push` runs inside hooks (at_post_puppet now, move and receive hooks in
W4.2), where an exception can turn a completed action into a failure the
player is told about (objects.py:1331, at_post_move). It therefore never
raises: each domain is built and sent on its own, and a domain that fails
is logged and skipped while the others still go out (lock 6B).
"""

import time

from django.conf import settings
from evennia.contrib.base_systems import custom_gametime as _cgt
from evennia.utils import logger
from evennia.utils.ansi import strip_ansi, strip_mxp

from world import encumbrance, gametime_utils, weather

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

def char_snapshot(char):
    """
    Name, health and the encumbrance band (WC12).

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


def _thing_names(room, viewer):
    """
    The 'You see:' entries in look's order: other objects grouped by name
    and numbered (a copy of DefaultObject.get_display_things' loop,
    evennia/objects/objects.py), then statues of logged-out characters
    (typeclasses/rooms.py get_display_things). Lock 4C: the extraction into
    one helper both use waits for W5.4, which rewrites these methods.
    """
    things = room.filter_visible(room.contents_get(content_type="object"), viewer)
    grouped = {}
    for thing in things:
        grouped.setdefault(thing.get_display_name(viewer), []).append(thing)
    names = []
    for thingname, thinglist in sorted(grouped.items()):
        count = len(thinglist)
        singular, plural = thinglist[0].get_numbered_name(count, viewer, key=thingname)
        names.append(singular if count == 1 else plural)
    for obj in room.contents_get(content_type="character"):
        if obj != viewer and obj.access(viewer, "view") and getattr(obj, "is_statue", False):
            names.append(obj.get_display_name(viewer))
    return [_plain(name) for name in names]


def room_snapshot(room, viewer):
    """
    The viewer's location as `look` lists it for that viewer (WC8): names
    depend on the looker, so this is built once per viewer.

    exits are [{"name", "key"}] -- the key is what a click sends (W5.4);
    characters are awake characters other than the viewer; things are
    `_thing_names`. No room gives the empty shape, so the browser clears.
    """
    if room is None:
        return {"name": None, "indoor": False, "exits": [], "characters": [], "things": []}
    exits = room.filter_visible(room.contents_get(content_type="exit"), viewer)
    characters = [
        obj for obj in room.contents_get(content_type="character")
        if obj != viewer
        and obj.access(viewer, "view")
        and not getattr(obj, "is_statue", False)
    ]
    return {
        "name": _plain(room.get_display_name(viewer)),
        "indoor": bool(room.db.is_indoor),
        "exits": [{"name": _plain(ex.get_display_name(viewer)), "key": ex.key} for ex in exits],
        "characters": [_plain(c.get_display_name(viewer)) for c in characters],
        "things": _thing_names(room, viewer),
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
