"""
Tests for world/client_state.py and the pw_state inputfunc (W4.1).

The four snapshots are the contract the browser builds on (WC5, W4.3, W5):
every class below pins one part of that contract against the reader the
text stream already uses, so a panel can never say something `status`,
`inventory` or `look` does not (WC1).

Locks (decomp Rev 5, STOPP 0 of W4.1):
  1B  the snapshot travels as args[0]: obj.msg(domain=((snap,), {}))
  2B  gauges are {"current": int, "max": int, "desc": str}, status's readers
  3A  every name is plain text (markup stripped)
  4C  room lists replicate look's filters; an equivalence test holds them
      (W5.4: both now read world.room_text.room_lists; the tests stay)
  5A  world is global; weather always; room carries `indoor`
  6B  push is per domain: a failing builder is logged and skipped
  7A  at_post_puppet always pushes all four
  8A  the spy sits on session.data_out; pw_state is reached via data_in
  M12 a second session on the puppet proves pw_state answers only the asker
"""

import json
from unittest import mock

import evennia
from django.test import SimpleTestCase
from evennia import create_object
from evennia.contrib.base_systems import custom_gametime as cgt
from evennia.server import sessionhandler
from evennia.utils.ansi import strip_ansi
from evennia.utils.test_resources import EvenniaTest
from evennia.utils.utils import callables_from_module, group_objects_by_key_and_desc

from commands.character_commands import _whole
from server.conf import inputfuncs
from world import client_state, encumbrance, gametime_utils, weather


def _json_roundtrip(snapshot):
    """What the browser gets back: only pure JSON types survive unchanged."""
    return json.loads(json.dumps(snapshot))


def _sent(spy):
    """The domains a data_out spy saw, in order, with their payloads."""
    out = []
    for call in spy.call_args_list:
        for key, value in call.kwargs.items():
            if key != "options":
                out.append((key, value))
    return out


class TestCharSnapshot(EvenniaTest):
    """
    Pressures: the health label read from trait.desc() instead of
    health_desc() (they disagree at full health: desc() reads the absolute
    value against the bounds), floats on the wire, a band computed from a
    second read, markup in the name, a missing trait crashing the build, and
    the inventory lists left out of the snapshot (W7.1 lock 1).
    """

    def test_keys_and_types(self):
        snap = client_state.char_snapshot(self.char1)
        self.assertEqual(set(snap), {"name", "health", "encumbrance", "inventory"})
        self.assertEqual(set(snap["health"]), {"current", "max", "desc"})
        for key in ("current", "max"):
            self.assertIs(type(snap["health"][key]), int)
        self.assertEqual(set(snap["encumbrance"]), {"carried", "limit", "band"})
        self.assertEqual(set(snap["inventory"]), {"carried", "worn"})
        self.assertEqual(_json_roundtrip(snap), snap)

    def test_health_reads_like_status(self):
        health = self.char1.traits.health
        snap = client_state.char_snapshot(self.char1)["health"]
        self.assertEqual(snap["current"], _whole(health.value))
        self.assertEqual(snap["max"], _whole(health.max))
        self.assertEqual(snap["desc"], self.char1.health_desc())
        # The fixture is the case that tells the two readers apart.
        self.assertNotEqual(health.desc(), self.char1.health_desc())

    def test_name_is_plain(self):
        self.assertEqual(client_state.char_snapshot(self.char1)["name"], "Char")

    def test_encumbrance_is_one_read(self):
        with mock.patch.object(encumbrance, "carried_enc", return_value=25):
            snap = client_state.char_snapshot(self.char1)["encumbrance"]
        limit = encumbrance.enc_limit(self.char1)
        self.assertEqual(snap, {"carried": 25, "limit": limit,
                                "band": encumbrance.band(25, limit)})
        self.assertEqual(snap["band"], encumbrance.OVERLOADED)

    def test_missing_health_is_null(self):
        self.char1.traits.remove("health")
        snap = client_state.char_snapshot(self.char1)
        self.assertIsNone(snap["health"])
        self.assertEqual(set(snap), {"name", "health", "encumbrance", "inventory"})


CLOTHING = "typeclasses.clothing.ClothingWithBuffs"
THING = "typeclasses.objects.Object"


class TestInventoryLists(EvenniaTest):
    """
    Pressures W7.1 locks 1-2: the lists ride in the char snapshot, not in a
    fifth domain; they split on db.worn as `inventory` does (a wear style is
    a truthy string there, contrib clothing.py:487); they group by display
    name, not by name and description as the contrib's `inventory` does --
    a garment's condition is in its description (durable.py:105) and changes
    without a push; and the names are asked for the carrier.
    """

    def _make(self, typeclass, key):
        return create_object(typeclass, key=key, location=self.char1)

    def test_in_the_char_snapshot(self):
        before = client_state.char_snapshot(self.char1)["inventory"]
        self._make(THING, "pebble")
        after = client_state.char_snapshot(self.char1)["inventory"]
        self.assertEqual([before, after],
                         [{"carried": [], "worn": []}, {"carried": ["a pebble"], "worn": []}])

    def test_not_a_fifth_domain(self):
        # A guard on lock 1, green by construction: a literal, not the list (W-z).
        self.assertEqual(client_state.DOMAINS, ("char", "survival", "world", "room"))

    def test_worn_and_carried_split(self):
        self._make(THING, "pebble")
        self._make(CLOTHING, "shirt").wear(self.char1, True, quiet=True)
        self.assertEqual(client_state.inventory_lists(self.char1),
                         {"carried": ["a pebble"], "worn": ["a shirt"]})

    def test_a_wear_style_still_counts_as_worn(self):
        self._make(CLOTHING, "shirt").wear(self.char1, "loosely", quiet=True)
        self.assertEqual(client_state.inventory_lists(self.char1),
                         {"carried": [], "worn": ["a shirt"]})

    def test_grouped_by_name_not_by_condition(self):
        worn_in, worn_out = self._make(CLOTHING, "cloak"), self._make(CLOTHING, "cloak")
        worn_in.db.condition, worn_out.db.condition = 90, 20
        # The receipt that the fixture tells the two groupings apart.
        text_rows = [key for key, _desc, _objs in
                     group_objects_by_key_and_desc([worn_in, worn_out], caller=self.char1)]
        self.assertEqual([text_rows, client_state.inventory_lists(self.char1)["carried"]],
                         [["a cloak", "a cloak"], ["two cloaks"]])

    def test_sorted_by_name_and_counted(self):
        for key in ("rope", "apple", "rope"):
            self._make(THING, key)
        self.assertEqual(client_state.inventory_lists(self.char1)["carried"],
                         ["an apple", "two ropes"])

    def test_names_are_plain(self):
        # An MXP link in a key survives get_numbered_name (colour does not),
        # so the plain text is the snapshot's own step, as in the room's.
        self._make(THING, "|lclook|ltstone|le")
        self._make(CLOTHING, "|lclook|ltshirt|le").wear(self.char1, True, quiet=True)
        self.assertEqual(client_state.inventory_lists(self.char1),
                         {"carried": ["a stone"], "worn": ["a shirt"]})

    def test_named_for_the_carrier(self):
        self._make(THING, "pebble")
        with mock.patch("typeclasses.objects.Object.get_display_name",
                        autospec=True, return_value="pebble") as name:
            client_state.inventory_lists(self.char1)
        lookers = {c.args[1] if len(c.args) > 1 else c.kwargs.get("looker")
                   for c in name.call_args_list}
        self.assertEqual(lookers, {self.char1})


class TestSurvivalSnapshot(EvenniaTest):
    """
    Pressures: a gauge dropped or renamed, desc read from the wrong place,
    and a missing gauge removing its key instead of sending null.
    """

    def test_gauges_read_like_status(self):
        self.char1.traits.hunger.current = 37
        snap = client_state.survival_snapshot(self.char1)
        self.assertEqual(set(snap), {"hunger", "thirst", "fatigue"})
        for key in snap:
            trait = self.char1.traits.get(key)
            self.assertEqual(snap[key], {"current": _whole(trait.value),
                                         "max": _whole(trait.max),
                                         "desc": trait.desc()})
        self.assertEqual(snap["hunger"]["current"], 37)
        self.assertEqual(_json_roundtrip(snap), snap)

    def test_missing_gauge_is_null(self):
        self.char1.traits.remove("thirst")
        snap = client_state.survival_snapshot(self.char1)
        self.assertIsNone(snap["thirst"])
        self.assertIsNotNone(snap["hunger"])


class TestWorldSnapshot(EvenniaTest):
    """
    Pressures the calendar block: the browser (W4.3/W5.3) will compute the
    date from game_seconds with nothing but this snapshot, so each table is
    checked against the Python reader it stands in for.
    """

    # Year 6, month 8, week 3, day 4, 13:25:41.7 -- every unit non-zero.
    GAME = 5 * 31449600 + 7 * 2419200 + 2 * 604800 + 3 * 86400 + 13 * 3600 + 25 * 60 + 41.7

    def test_keys_and_types(self):
        snap = client_state.world_snapshot()
        self.assertEqual(set(snap), {"game_seconds", "time_factor", "server_ms",
                                     "weather", "calendar"})
        self.assertEqual(set(snap["calendar"]),
                         {"units", "month_names", "seasons", "times_of_day"})
        self.assertIs(type(snap["game_seconds"]), int)
        self.assertIs(type(snap["server_ms"]), int)
        self.assertEqual(snap["time_factor"], 4)
        self.assertEqual(snap["weather"], weather.get_current_weather())
        self.assertEqual(_json_roundtrip(snap), snap)

    def test_units_reproduce_custom_gametime(self):
        with mock.patch("evennia.utils.gametime.gametime", return_value=self.GAME):
            snap = client_state.world_snapshot()
            expected = cgt.custom_gametime(absolute=True)
        seconds, parts = snap["game_seconds"], []
        for _name, divisor in snap["calendar"]["units"]:
            parts.append(seconds // divisor)
            seconds %= divisor
        parts.append(seconds)
        self.assertEqual(tuple(parts), tuple(expected))
        self.assertEqual([n for n, _ in snap["calendar"]["units"]],
                         ["year", "month", "week", "day", "hour", "min"])

    def test_month_names_follow_get_month_name(self):
        names = client_state.world_snapshot()["calendar"]["month_names"]
        self.assertEqual(len(names), 13)
        for display, name in enumerate(names, start=1):
            self.assertEqual(name, gametime_utils.get_month_name(display))

    def test_seasons_follow_get_season(self):
        seasons = client_state.world_snapshot()["calendar"]["seasons"]
        for display in range(1, 14):
            with mock.patch.object(gametime_utils, "get_current_time",
                                   return_value={"month_display": display}):
                expected = gametime_utils.get_season()
            found = [s for s, months in seasons.items() if display in months]
            self.assertEqual(found, [expected], f"month {display}")

    def test_times_of_day_follow_get_time_of_day(self):
        table = client_state.world_snapshot()["calendar"]["times_of_day"]
        for hour in range(24):
            for minute in (0, 59):
                fraction = (hour * 3600 + minute * 60) / 86400
                with mock.patch.object(gametime_utils, "get_current_time",
                                       return_value={"hour": hour, "minute": minute,
                                                     "second": 0}):
                    expected = gametime_utils.get_time_of_day()
                found = next(n for n, start, end in table if start <= fraction < end)
                self.assertEqual(found, expected, f"{hour:02d}:{minute:02d}")


class TestRoomSnapshot(EvenniaTest):
    """
    Pressures lock 4C: the snapshot and look read one helper since W5.4
    (world.room_text.room_lists), and each list is still checked against
    the look text for the same viewer -- the statue under
    things (WC8/WC14), the viewer left out, grouping, and the view lock.
    """

    def _look(self):
        return strip_ansi(self.room1.return_appearance(self.char1))

    def _assert_in_look_in_order(self, names):
        look, pos = self._look(), -1
        for name in names:
            found = look.find(name, pos + 1)
            self.assertGreater(found, pos, f"{name!r} not after position {pos} in look")
            pos = found

    def test_keys_and_types(self):
        snap = client_state.room_snapshot(self.room1, self.char1)
        self.assertEqual(set(snap), {"name", "indoor", "exits", "characters", "things"})
        self.assertEqual(snap["name"], "Room")
        self.assertIs(snap["indoor"], False)
        self.assertEqual(snap["exits"], [{"name": "out", "key": "out"}])
        self.assertEqual(_json_roundtrip(snap), snap)

    def test_indoor_follows_the_room(self):
        self.room1.db.is_indoor = True
        self.assertIs(client_state.room_snapshot(self.room1, self.char1)["indoor"], True)

    def test_statue_named_as_look_names_it(self):
        snap = client_state.room_snapshot(self.room1, self.char1)
        self.assertEqual(snap["characters"], [])
        self.assertEqual(snap["things"], ["an Obj", "an Obj2", "stone statue of Char2"])
        self._assert_in_look_in_order(snap["things"])

    def test_awake_character_listed_viewer_left_out(self):
        with mock.patch.object(type(self.char2), "is_statue",
                               new_callable=mock.PropertyMock, return_value=False):
            snap = client_state.room_snapshot(self.room1, self.char1)
            self.assertEqual(snap["characters"], ["Char2"])
            self.assertIn("Characters: Char2", self._look())
        self.assertNotIn("stone statue of Char2", snap["things"])

    def test_things_grouped_as_look_groups_them(self):
        for _ in range(2):
            create_object("typeclasses.objects.Object", key="apple", location=self.room1)
        snap = client_state.room_snapshot(self.room1, self.char1)
        grouped = [t for t in snap["things"] if "apple" in t]
        self.assertEqual(len(grouped), 1)
        self._assert_in_look_in_order(snap["things"])

    def test_view_lock_agrees_with_look(self):
        hidden = create_object("typeclasses.objects.Object", key="Hidden",
                               location=self.room1, locks="view:false()")
        snap = client_state.room_snapshot(self.room1, self.char1)
        in_snap = any("Hidden" in t for t in snap["things"])
        self.assertEqual(in_snap, "Hidden" in self._look())
        self.assertTrue(hidden.pk)  # receipt: the object exists in the room

    def test_no_room_is_empty_shape(self):
        self.assertEqual(client_state.room_snapshot(None, self.char1),
                         {"name": None, "indoor": False, "exits": [],
                          "characters": [], "things": []})


class TestPush(EvenniaTest):
    """
    Pressures lock 1B (args[0], not kwargs), lock 6B (per domain, never
    raises) and the order the browser can rely on.
    """

    def test_one_domain_as_args0(self):
        with mock.patch.object(self.session, "data_out") as spy:
            client_state.push(self.char1, "survival")
        self.assertEqual(_sent(spy), [
            ("survival", ((client_state.survival_snapshot(self.char1),), {}))])

    def test_all_domains_in_order(self):
        with mock.patch.object(self.session, "data_out") as spy:
            client_state.push(self.char1, *client_state.DOMAINS)
        sent = _sent(spy)
        self.assertEqual([d for d, _ in sent], list(client_state.DOMAINS))
        room = dict(sent)["room"][0][0]
        self.assertEqual(room, client_state.room_snapshot(self.room1, self.char1))

    def test_raising_builder_skips_only_its_domain(self):
        with mock.patch.object(client_state, "survival_snapshot",
                               side_effect=RuntimeError("boom")) as builder, \
                mock.patch.object(client_state.logger, "log_trace") as trace, \
                mock.patch.object(self.session, "data_out") as spy:
            client_state.push(self.char1, "survival", "world")
        self.assertEqual([d for d, _ in _sent(spy)], ["world"])
        builder.assert_called_once()   # receipt: the builder really ran
        trace.assert_called_once()     # receipt: the except path really ran

    def test_unknown_domain_logged_not_raised(self):
        with mock.patch.object(client_state.logger, "log_trace") as trace, \
                mock.patch.object(self.session, "data_out") as spy:
            client_state.push(self.char1, "nope", "world")
        self.assertEqual([d for d, _ in _sent(spy)], ["world"])
        trace.assert_called_once()


class TestPwState(EvenniaTest):
    """
    Pressures WC6: registered under its own name, exposes nothing else to
    the client, answers only the asking session (a second browser tab on the
    same puppet does not get a copy), and sends nothing (without raising)
    when that session has no puppet.
    """

    def test_registered_and_alone(self):
        self.assertIs(sessionhandler._INPUT_FUNCS["pw_state"], inputfuncs.pw_state)
        self.assertEqual(set(callables_from_module("server.conf.inputfuncs")),
                         {"pw_state"})

    def test_with_puppet_sends_all_four(self):
        with mock.patch.object(self.session, "data_out") as spy:
            evennia.SESSION_HANDLER.data_in(self.session, pw_state=([], {}))
        sent = _sent(spy)
        self.assertEqual([d for d, _ in sent], list(client_state.DOMAINS))
        for _domain, (args, kwargs) in sent:
            self.assertIsInstance(args[0], dict)
            self.assertEqual(kwargs, {})

    def test_answers_only_the_asking_session(self):
        other = mock.Mock(name="second session on the same puppet")
        with mock.patch.object(self.char1.sessions, "all",
                               return_value=[self.session, other]), \
                mock.patch.object(self.session, "data_out") as spy:
            client_state.push(self.char1, "world")
            self.assertEqual(other.data_out.call_count, 1)  # receipt: other is reachable
            other.data_out.reset_mock()
            spy.reset_mock()
            evennia.SESSION_HANDLER.data_in(self.session, pw_state=([], {}))
        self.assertEqual(len(_sent(spy)), len(client_state.DOMAINS))
        other.data_out.assert_not_called()

    def test_without_puppet_sends_nothing(self):
        wrapped = mock.Mock(wraps=inputfuncs.pw_state)
        with mock.patch.dict(sessionhandler._INPUT_FUNCS, {"pw_state": wrapped}), \
                mock.patch.object(self.session, "puppet", None), \
                mock.patch.object(client_state.logger, "log_trace") as trace, \
                mock.patch.object(self.session, "data_out") as spy:
            evennia.SESSION_HANDLER.data_in(self.session, pw_state=([], {}))
        wrapped.assert_called_once()   # receipt: pw_state really ran
        spy.assert_not_called()
        trace.assert_not_called()      # the guard, not push's except, stopped it


class TestAtPostPuppet(EvenniaTest):
    """Pressures lock 7A: every puppet pushes all four domains to the character."""

    def test_pushes_all_domains(self):
        with mock.patch.object(client_state, "push") as push:
            self.char1.at_post_puppet()
        push.assert_called_once_with(self.char1, *client_state.DOMAINS)


# ======================================================================
# W4.2 -- the emit sites and their census (WC8)
#
# Locks (STOPP 0 of W4.2, Adam took every recommendation):
#   1B  hook sites (leave, delete, death, puppet) send on the next reactor
#       turn, coalesced per character/domain and per room in ndb
#   2A  the mover gets its new room from the destination's fan-out
#   3A  `char` on every change of `carried`, not only a band crossing
#   4A  `world` on each survival tick and each weather change, indoors too
#   5A  death, deletion, puppet/unpuppet and eat's `carried` are sites
#   6   the census pins the sites and every gauge `.current` write;
#       `push(` and `client_state.push(` are one name
#   7   fan-out via three awake characters; "sends nothing" carries a receipt
#
# W4.2b (Adam: A): three placements by `obj.location =` run no hook -- the
# barter swap, the creature spawn, the crafted products -- so each pushes
# after it; the census also pins every `.location =` in production code.
# ======================================================================

import ast
import pathlib
from contextlib import contextmanager

from commands.consumption_commands import CmdDrink, CmdEat
from evennia.utils.test_resources import EvenniaCommandTest
from tests.test_barter_currency import TradeFixtureMixin
from tests.test_chargen_menu import _MenuFixture
from tests.test_currency import LedgerIsolationMixin
from typeclasses.characters import _rest_tick
from world import survival_ticker

PUSH_NAMES = {"push", "push_soon", "push_room", "push_room_soon",
              "push_online", "push_after_removal"}
ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCTION = ("commands", "server", "typeclasses", "web", "world")


class _FakeReactor:
    """
    Stands in for the reactor: `client_state.delay` records what it is asked
    to run, and `run()` runs it -- after the code under test has returned,
    which is when the real reactor would (lock 1B). Runs until nothing is
    left, since a scheduled send may schedule another.
    """

    def __init__(self):
        self.queue = []

    def delay(self, _seconds, callback, *args, **kwargs):
        self.queue.append((callback, args, kwargs))

    def run(self):
        ran = 0
        while self.queue:
            callback, args, kwargs = self.queue.pop(0)
            callback(*args, **kwargs)
            ran += 1
        return ran


class ReactorMixin:
    """
    Installs the fake reactor BEFORE EvenniaTest builds its rooms and
    characters: their creation already schedules room pushes, and a send
    scheduled on the real reactor never runs in a test, so its pending mark
    would swallow every later push of the same kind. The fixture's own
    sends are run and then discarded at the end of setUp.
    """

    def setUp(self):
        self.reactor = _FakeReactor()
        patcher = mock.patch.object(client_state, "delay", side_effect=self.reactor.delay)
        patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()
        with mock.patch.object(client_state, "push"):
            self.reactor.run()


@contextmanager
def _awake(char, session):
    """
    Give `char` a session: the fan-out reads `sessions.all()`, and
    `is_statue` reads `has_account`, which counts them.
    """
    with mock.patch.object(char.sessions, "all", return_value=[session]), \
            mock.patch.object(char.sessions, "count", return_value=1):
        yield


class TestPushSoon(ReactorMixin, EvenniaTest):
    """
    Pressures lock 1B: a hook-site push is sent after the call returns, once
    per domain however often it was asked for, and not at all for an object
    deleted in between -- with a receipt that the scheduled call ran.
    """

    def test_sent_on_the_next_turn_not_inside_the_call(self):
        with mock.patch.object(self.session, "data_out") as spy:
            client_state.push_soon(self.char1, "char")
            spy.assert_not_called()
            self.assertEqual(self.reactor.run(), 1)
        self.assertEqual([d for d, _ in _sent(spy)], ["char"])

    def test_coalesced_until_sent_then_open_again(self):
        with mock.patch.object(self.session, "data_out") as spy:
            client_state.push_soon(self.char1, "char", "survival")
            client_state.push_soon(self.char1, "char")
            self.assertEqual(self.reactor.run(), 2)
            client_state.push_soon(self.char1, "char")
            self.assertEqual(self.reactor.run(), 1)
        self.assertEqual([d for d, _ in _sent(spy)], ["char", "survival", "char"])

    def test_room_fan_out_coalesced(self):
        client_state.push_room_soon(self.room1)
        client_state.push_room_soon(self.room1)
        self.assertEqual(len(self.reactor.queue), 1)

    def test_deleted_room_sends_nothing(self):
        doomed = create_object("typeclasses.rooms.Room", key="Doomed")
        with mock.patch.object(client_state, "push_room") as fan_out, \
                mock.patch.object(client_state.logger, "log_trace") as trace:
            client_state.push_room_soon(doomed)
            doomed.delete()
            self.assertEqual(self.reactor.run(), 1)   # receipt: the scheduled send ran
        fan_out.assert_not_called()      # the _gone guard stopped it
        trace.assert_not_called()        # not push's except

    def test_failing_schedule_is_logged_and_reopens(self):
        with mock.patch.object(client_state, "delay", side_effect=RuntimeError("no")), \
                mock.patch.object(client_state.logger, "log_trace") as trace:
            client_state.push_soon(self.char1, "char")
        trace.assert_called_once()
        self.assertNotIn("char", self.char1.ndb.client_state_pending)


class TestRoomFanOut(ReactorMixin, EvenniaTest):
    """
    Pressures WC8's "one snapshot per viewer": three awake characters see a
    fourth arrive, each through their own names; the one who leaves is gone
    from what the others get, which proves the leave push is built after the
    move (lock 1B); statues get nothing.
    """

    def setUp(self):
        super().setUp()
        self.char3 = create_object("typeclasses.characters.Character",
                                   key="Char3", location=self.room1, home=self.room1)
        self.char4 = create_object("typeclasses.characters.Character",
                                   key="Char4", location=self.room2, home=self.room2)
        self.s2 = mock.Mock(name="session of Char2")
        self.s3 = mock.Mock(name="session of Char3")
        self.s4 = mock.Mock(name="session of Char4")
        with mock.patch.object(client_state, "push"):
            self.reactor.run()   # the two creations' own room pushes

    def _room_payloads(self, session_mock):
        return [call.kwargs["room"][0][0] for call in session_mock.data_out.call_args_list
                if "room" in call.kwargs]

    def test_arrival_reaches_each_viewer_with_its_own_names(self):
        with _awake(self.char2, self.s2), _awake(self.char3, self.s3), \
                _awake(self.char4, self.s4), \
                mock.patch.object(self.session, "data_out") as spy:
            self.char4.move_to(self.room1, quiet=True)
            self.reactor.run()
            expected = {c: client_state.room_snapshot(self.room1, c)
                        for c in (self.char1, self.char2, self.char3, self.char4)}
        mine = [payload[0][0] for d, payload in _sent(spy) if d == "room"]
        self.assertEqual(mine, [expected[self.char1]])
        self.assertEqual(self._room_payloads(self.s2), [expected[self.char2]])
        self.assertEqual(self._room_payloads(self.s3), [expected[self.char3]])
        self.assertIn("Char4", expected[self.char1]["characters"])
        self.assertNotIn("Char2", expected[self.char2]["characters"])  # own names
        self.assertIn("Char2", expected[self.char3]["characters"])
        # the mover gets its new room from the same fan-out (lock 2A)
        self.assertEqual(self._room_payloads(self.s4)[-1:], [expected[self.char4]])

    def test_leaver_is_gone_from_what_the_others_get(self):
        with _awake(self.char2, self.s2), \
                mock.patch.object(self.session, "data_out") as spy:
            self.assertIn("Char2", client_state.room_snapshot(self.room1, self.char1)["characters"])
            self.char2.move_to(self.room2, quiet=True)
            self.assertGreater(self.reactor.run(), 0)
        rooms = [payload[0][0] for d, payload in _sent(spy) if d == "room"]
        self.assertEqual(len(rooms), 1)
        self.assertNotIn("Char2", rooms[0]["characters"])

    def test_statues_get_nothing(self):
        with mock.patch.object(client_state, "push") as push:
            self.char4.move_to(self.room1, quiet=True)
            self.assertGreater(self.reactor.run(), 0)     # receipt: the fan-out ran
        self.assertEqual([c.args for c in push.call_args_list], [(self.char1, "room")])

    def test_push_room_never_raises(self):
        with mock.patch.object(self.room1, "contents_get", side_effect=RuntimeError("x")), \
                mock.patch.object(client_state.logger, "log_trace") as trace:
            client_state.push_room(self.room1)
        trace.assert_called_once()


class TestHookSites(ReactorMixin, EvenniaTest):
    """
    Pressures each hook site: the right domain is scheduled from the right
    hook, including the four the decomposition did not name (death's hookless
    relocation, a deletion, puppet and unpuppet; locks 5A).
    """

    def test_room_receive_and_leave(self):
        thing = create_object("typeclasses.objects.Object", key="pebble", location=self.room2)
        with mock.patch.object(client_state, "push_room_soon") as soon:
            thing.move_to(self.room1, quiet=True)
        self.assertEqual([c.args for c in soon.call_args_list], [(self.room2,), (self.room1,)])

    def test_character_leave_and_receive_push_char(self):
        thing = create_object("typeclasses.objects.Object", key="pebble", location=self.room1)
        with mock.patch.object(client_state, "push_soon") as soon:
            thing.move_to(self.char1, quiet=True)
            self.assertIn(mock.call(self.char1, "char"), soon.call_args_list)
            soon.reset_mock()
            thing.move_to(self.room1, quiet=True)
            self.assertIn(mock.call(self.char1, "char"), soon.call_args_list)

    def test_carried_drops_in_the_char_snapshot_after_a_drop(self):
        thing = create_object("typeclasses.objects.Object", key="anvil", location=self.char1)
        thing.db.enc = 3
        with mock.patch.object(client_state, "push"):
            self.reactor.run()   # the creation's own push, so only the drop's is left
        with mock.patch.object(self.session, "data_out") as spy:
            before = client_state.char_snapshot(self.char1)["encumbrance"]["carried"]
            thing.move_to(self.room1, quiet=True)
            self.reactor.run()
        chars = [p[0][0] for d, p in _sent(spy) if d == "char"]
        self.assertEqual(len(chars), 1)
        self.assertEqual(chars[0]["encumbrance"]["carried"], before - 3)

    def test_deletion_from_inventory_pushes_char(self):
        thing = create_object("typeclasses.objects.Object", key="crumb", location=self.char1)
        with mock.patch.object(client_state, "push_soon") as soon, \
                mock.patch.object(client_state, "push_room_soon") as room_soon:
            thing.delete()
        soon.assert_called_once_with(self.char1, "char")
        room_soon.assert_not_called()

    def test_deletion_from_a_carried_sack_pushes_the_carrier(self):
        sack = create_object("typeclasses.objects.Object", key="sack", location=self.char1)
        thing = create_object("typeclasses.objects.Object", key="crumb", location=sack)
        with mock.patch.object(client_state, "push_soon") as soon:
            thing.delete()
        soon.assert_called_once_with(self.char1, "char")

    def test_deletion_of_a_worn_garment_pushes_the_wearer(self):
        # W5.1b: ClothingWithBuffs did not inherit ObjectParent, so a garment
        # deleted while carried (disassemble, @destroy) left the panel's ENC.
        garment = create_object(
            "typeclasses.clothing.ClothingWithBuffs", key="shirt", location=self.char1
        )
        garment.wear(self.char1, True, quiet=True)
        with mock.patch.object(client_state, "push_soon") as soon:
            self.assertTrue(garment.delete())
        soon.assert_called_once_with(self.char1, "char")

    def test_wear_and_remove_push_char(self):
        shirt = create_object(CLOTHING, key="shirt", location=self.char1)
        with mock.patch.object(client_state, "push_soon") as soon:
            shirt.wear(self.char1, True, quiet=True)
            worn = list(soon.call_args_list)
            soon.reset_mock()
            shirt.remove(self.char1, quiet=True)
            removed = list(soon.call_args_list)
        self.assertEqual([worn, removed], [[mock.call(self.char1, "char")]] * 2)

    def test_wear_moves_the_garment_in_the_pushed_frame(self):
        shirt = create_object(CLOTHING, key="shirt", location=self.char1)
        with mock.patch.object(client_state, "push"):
            self.reactor.run()   # the creation's own push
        frames = []
        with mock.patch.object(self.session, "data_out") as spy:
            for step in (lambda: shirt.wear(self.char1, True, quiet=True),
                         lambda: shirt.remove(self.char1, quiet=True)):
                spy.reset_mock()
                step()
                self.reactor.run()
                frames.append([p[0][0]["inventory"] for d, p in _sent(spy) if d == "char"])
        self.assertEqual(frames, [[{"carried": [], "worn": ["a shirt"]}],
                                  [{"carried": ["a shirt"], "worn": []}]])

    def test_a_worn_garment_given_away_is_one_frame(self):
        # The leave hook and remove() (via the garment's at_post_move) both
        # ask; push_soon makes it one frame, built after both have run.
        shirt = create_object(CLOTHING, key="shirt", location=self.char1)
        shirt.wear(self.char1, True, quiet=True)
        with mock.patch.object(client_state, "push"):
            self.reactor.run()
        with mock.patch.object(self.session, "data_out") as spy:
            shirt.move_to(self.char2, quiet=True)
            self.reactor.run()
        frames = [p[0][0]["inventory"] for d, p in _sent(spy) if d == "char"]
        self.assertEqual(frames, [{"carried": [], "worn": []}])

    def test_another_character_gets_no_frame(self):
        shirt = create_object(CLOTHING, key="shirt", location=self.char1)
        with mock.patch.object(client_state, "push"):
            self.reactor.run()
        with mock.patch.object(self.char1, "msg") as mine, \
                mock.patch.object(self.char2, "msg") as theirs:
            shirt.wear(self.char1, True, quiet=True)
            self.reactor.run()
        frames = [len([c for c in m.call_args_list if "char" in c.kwargs]) for m in (mine, theirs)]
        self.assertEqual(frames, [1, 0])

    def test_deletion_from_a_room_pushes_the_room(self):
        thing = create_object("typeclasses.objects.Object", key="crumb", location=self.room1)
        with mock.patch.object(client_state, "push_soon") as soon, \
                mock.patch.object(client_state, "push_room_soon") as room_soon:
            self.assertTrue(thing.delete())   # never vetoes
        room_soon.assert_called_once_with(self.room1)
        soon.assert_not_called()

    def test_puppet_and_unpuppet_push_the_room(self):
        with mock.patch.object(client_state, "push_room_soon") as soon:
            self.char1.at_post_puppet()
            self.assertIn(mock.call(self.room1), soon.call_args_list)
            soon.reset_mock()
            with mock.patch.object(self.char1.sessions, "count", return_value=0):
                self.char1.at_post_unpuppet()
            soon.assert_called_once_with(self.room1)

    def test_death_pushes_all_four_and_both_rooms(self):
        self.char1.db.respawn_location = self.room2
        with mock.patch.object(client_state, "push_soon") as soon, \
                mock.patch.object(client_state, "push_room_soon") as room_soon, \
                mock.patch.object(client_state, "push"):
            self.char1.apply_health_damage(self.char1.traits.health.current)
        self.assertEqual(self.char1.location, self.room2)
        self.assertIn(mock.call(self.char1, *client_state.DOMAINS), soon.call_args_list)
        rooms = {c.args[0] for c in room_soon.call_args_list}
        self.assertTrue({self.room1, self.room2} <= rooms)


class TestImmediateSites(EvenniaTest):
    """Pressures the synchronous sites: tick, rest, overload step, health."""

    def _pushed(self, push):
        return [c.args for c in push.call_args_list]

    def test_tick_pushes_survival_and_world_after_the_warnings(self):
        order = []
        with mock.patch.object(survival_ticker, "_check_survival_warnings",
                               side_effect=lambda c: order.append("warn")), \
                mock.patch.object(client_state, "push",
                                  side_effect=lambda *a, **k: order.append(a)):
            survival_ticker._deplete_character(self.char1)
        self.assertEqual(order[-2:], ["warn", (self.char1, "survival", "world")])

    def test_rest_tick_pushes_survival(self):
        with mock.patch("typeclasses.characters.timed_actions.is_current", return_value=True), \
                mock.patch("typeclasses.characters.timed_actions.claim"), \
                mock.patch("typeclasses.characters.delay"), \
                mock.patch.object(client_state, "push") as push:
            _rest_tick(self.char1, object())
        self.assertIn((self.char1, "survival"), self._pushed(push))

    def test_overloaded_step_pushes_survival(self):
        with mock.patch.object(type(self.char1), "encumbrance_state",
                               new_callable=mock.PropertyMock,
                               return_value=encumbrance.OVERLOADED), \
                mock.patch.object(client_state, "push") as push:
            self.char1.at_post_move(self.room2, move_type="traverse")
        self.assertEqual(self._pushed(push), [(self.char1, "survival")])

    def test_free_step_pushes_nothing(self):
        with mock.patch.object(client_state, "push") as push, \
                mock.patch.object(survival_ticker, "_check_survival_warnings") as warn:
            self.char1.at_post_move(self.room2, move_type="traverse")
        warn.assert_not_called()   # receipt: the FREE return stopped it
        push.assert_not_called()

    def test_health_max_and_damage_push_char(self):
        with mock.patch.object(client_state, "push") as push:
            self.char1.update_health_max()
            self.char1.apply_health_damage(1)
        self.assertEqual(self._pushed(push), [(self.char1, "char"), (self.char1, "char")])

    def test_weather_change_reaches_indoors_even_without_a_message(self):
        self.room1.db.is_indoor = True
        with mock.patch.dict(weather.WEATHER_MESSAGES, {}, clear=True), \
                mock.patch.object(client_state, "push") as push:
            weather.broadcast_weather_change("foggy")
        self.assertEqual(self._pushed(push), [(self.char1, "world")])

    def test_push_online_once_per_puppet(self):
        twin = mock.Mock(name="second session", puppet=self.char1)
        with mock.patch.object(evennia.SESSION_HANDLER, "get_sessions",
                               return_value=[self.session, twin]), \
                mock.patch.object(client_state, "push") as push:
            client_state.push_online("world")
        self.assertEqual(self._pushed(push), [(self.char1, "world")])


class TestCommandSites(EvenniaCommandTest):
    """Pressures eat and drink: the gauge they move, and eat's `carried`."""

    character_typeclass = "typeclasses.characters.Character"

    def test_eat_pushes_survival_and_char(self):
        create_object("typeclasses.consumables.Food", key="w42bread", location=self.char1)
        self.char1.traits.hunger.current = 50  # S1.2b: no eating at full hunger
        with mock.patch.object(client_state, "push") as push:
            self.call(CmdEat(), "w42bread", caller=self.char1)
        self.assertIn(mock.call(self.char1, "survival", "char"), push.call_args_list)

    def test_drink_pushes_survival(self):
        create_object("typeclasses.consumables.Drink", key="w42skin", location=self.char1)
        self.char1.traits.thirst.current = 50  # S1.2b: no drinking at full thirst
        with mock.patch.object(client_state, "push") as push:
            self.call(CmdDrink(), "w42skin", caller=self.char1)
        self.assertIn(mock.call(self.char1, "survival"), push.call_args_list)


class TestChargenEnd(_MenuFixture):
    """Pressures the Rev 5 site: the final values follow the placeholders."""

    def test_node_done_pushes_all_four_last(self):
        self.walk_to_last_confirm()
        with mock.patch.object(client_state, "push") as push:
            self.send("yes")
        self.assertTrue(self.char1.db.chargen_complete)   # receipt: node_done ran
        self.assertEqual(push.call_args_list[-1:],
                         [mock.call(self.char1, *client_state.DOMAINS)])


def _production_trees():
    """(relative path, AST) for every production module (WC8's census)."""
    for top in PRODUCTION:
        for path in sorted((ROOT / top).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            if "/migrations/" in rel or rel == "world/client_state.py":
                continue
            yield rel, ast.parse(path.read_text(encoding="utf-8"))


def _functions(tree):
    """(qualified name, FunctionDef) for every function, methods as Class.method."""
    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                yield from walk(child, f"{prefix}{child.name}.")
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield f"{prefix}{child.name}", child
                yield from walk(child, f"{prefix}{child.name}.")
            else:   # a def inside `if`/`try` is still found
                yield from walk(child, prefix)
    yield from walk(tree, "")


def _push_calls(func):
    """The push-family calls made directly in `func`: (name, Call)."""
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            target = node.func
            name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", None)
            if name in PUSH_NAMES:
                yield name, node


def _domains(call):
    """The domains a push call names: string constants; `*...DOMAINS` is all four."""
    named = set()
    for arg in call.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            named.add(arg.value)
        elif isinstance(arg, ast.Starred) and ast.unparse(arg.value).endswith("DOMAINS"):
            named.update(client_state.DOMAINS)
    return named


class TestPushCensus(EvenniaTest):
    """
    Pressures WC8: the push sites are exactly the ones W4.2 placed, and every
    write to a panel gauge's `.current` sits in a function that pushes that
    gauge's domain. A new writer, or a site removed, fails here first.
    `push(` and `client_state.push(` are one name (lock 6).
    """

    SITES = {
        ("commands/consumption_commands.py", "CmdEat.func", "push"): 1,
        ("commands/consumption_commands.py", "CmdDrink.func", "push"): 1,
        ("server/conf/inputfuncs.py", "pw_state", "push"): 1,
        ("typeclasses/characters.py", "Character.at_post_unpuppet", "push_room_soon"): 1,
        ("typeclasses/characters.py", "Character.at_post_puppet", "push"): 1,
        ("typeclasses/characters.py", "Character.at_post_puppet", "push_room_soon"): 1,
        ("typeclasses/characters.py", "Character.update_health_max", "push"): 1,
        ("typeclasses/characters.py", "Character.apply_health_damage", "push"): 1,
        ("typeclasses/characters.py", "Character.at_character_death", "push_soon"): 1,
        ("typeclasses/characters.py", "Character.at_character_death", "push_room_soon"): 2,
        ("typeclasses/characters.py", "Character.at_post_move", "push"): 1,
        ("typeclasses/characters.py", "Character.at_object_leave", "push_soon"): 1,
        ("typeclasses/characters.py", "Character.at_object_receive", "push_soon"): 1,
        ("typeclasses/characters.py", "_rest_tick", "push"): 1,
        ("typeclasses/objects.py", "ObjectParent.at_object_delete", "push_after_removal"): 1,
        ("typeclasses/rooms.py", "Room.at_object_receive", "push_room_soon"): 1,
        ("typeclasses/rooms.py", "Room.at_object_leave", "push_room_soon"): 1,
        ("world/chargen_menu.py", "node_done", "push"): 1,
        ("world/survival_ticker.py", "_deplete_character", "push"): 1,
        ("world/weather.py", "broadcast_weather_change", "push_online"): 1,
        # W4.2b: after placements by assignment (no hook runs)
        ("commands/crafting_commands.py", "_complete_craft", "push_soon"): 1,
        ("typeclasses/scripts.py", "CreatureSpawnScript._spawn_one", "push_room_soon"): 1,
        ("world/barter.py", "PWTradeHandler._finish_and_clear", "push"): 2,
        # W7.1 lock 3: the worn state changes without a move
        ("typeclasses/clothing.py", "ClothingWithBuffs.wear", "push_soon"): 1,
        ("typeclasses/clothing.py", "ClothingWithBuffs.remove", "push_soon"): 1,
        # Survival Loop S1.1: drinking at a water source
        ("commands/consumption_commands.py", "CmdDrink._drink_from_source", "push"): 1,
        # Survival Loop S2.1: natural healing lands a point
        ("world/healing.py", "accrue", "push"): 1,
    }

    # Every `.location =` in production code: it runs no move hook, so the
    # function must push itself (W4.2b).
    LOCATION_WRITES = {
        ("typeclasses/scripts.py", "CreatureSpawnScript._spawn_one", "spawned[0].location"): "room",
    }

    # Contrib code that places by assignment, and the project function that
    # runs right after it and pushes: barter.py:369/371 (finish's swap),
    # crafting.py:1098 (CmdCraft.func's products).
    CONTRIB_PLACEMENTS = {
        ("world/barter.py", "PWTradeHandler._finish_and_clear"): "char",
        ("commands/crafting_commands.py", "_complete_craft"): "char",
    }

    # (file, function, written target) -> the domain whose panel shows it
    GAUGE_WRITES = {
        ("commands/consumption_commands.py", "CmdEat.func", "caller.traits.hunger.current"): "survival",
        ("commands/consumption_commands.py", "CmdDrink.func", "caller.traits.thirst.current"): "survival",
        ("commands/consumption_commands.py", "CmdDrink._drink_from_source", "caller.traits.thirst.current"): "survival",
        ("typeclasses/characters.py", "Character.update_health_max", "self.traits.health.current"): "char",
        ("typeclasses/characters.py", "Character.apply_health_damage", "health.current"): "char",
        ("typeclasses/characters.py", "Character.at_character_death", "health.current"): "char",
        ("typeclasses/characters.py", "Character.at_character_death", "gauge.current"): "survival",
        ("typeclasses/characters.py", "Character.at_post_move", "fatigue.current"): "survival",
        ("typeclasses/characters.py", "_rest_tick", "fatigue.current"): "survival",
        ("world/survival_ticker.py", "_deplete_character", "trait.current"): "survival",
        ("world/healing.py", "accrue", "health.current"): "char",
    }

    # Skill writes: no panel yet (inventory/skills is W7's); chargen's is
    # covered by node_done's push of all four.
    NOT_PANEL = {
        ("typeclasses/characters.py", "Character.improve_skill_on_use", "skill.current"),
        ("world/chargen.py", "apply_allocation", "skill.current"),
        ("world/professions.py", "grant_profession", "skill.current"),
    }

    def setUp(self):
        super().setUp()
        self.sites = {}
        self.writes = set()
        self.locations = set()
        self.pushes = {}
        for rel, tree in _production_trees():
            for qual, func in _functions(tree):
                calls = list(_push_calls(func))
                nested = {id(n) for _q, inner in _functions(func) for n in ast.walk(inner)}
                own = [c for c in calls if id(c[1]) not in nested]
                for name, _call in own:
                    key = (rel, qual, name)
                    self.sites[key] = self.sites.get(key, 0) + 1
                self.pushes[(rel, qual)] = [call for _n, call in own]
                for node in ast.walk(func):
                    if id(node) in nested:
                        continue
                    targets = []
                    if isinstance(node, ast.Assign):
                        targets = node.targets
                    elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                        targets = [node.target]
                    for target in targets:
                        if isinstance(target, ast.Attribute) and target.attr == "current":
                            self.writes.add((rel, qual, ast.unparse(target)))
                        if isinstance(target, ast.Attribute) and target.attr in (
                                "location", "db_location"):
                            self.locations.add((rel, qual, ast.unparse(target)))

    def test_push_sites_are_pinned(self):
        self.assertEqual(self.sites, self.SITES)

    def test_every_current_write_is_known(self):
        self.assertEqual(self.writes, set(self.GAUGE_WRITES) | self.NOT_PANEL)

    def _named(self, rel, qual):
        named = set()
        for call in self.pushes.get((rel, qual), []):
            named |= _domains(call)
        if any(isinstance(c.func, (ast.Attribute, ast.Name))
               and (getattr(c.func, "attr", None) or getattr(c.func, "id", None))
               in ("push_room", "push_room_soon")
               for c in self.pushes.get((rel, qual), [])):
            named.add("room")
        return named

    def test_every_location_assignment_is_known_and_pushes(self):
        self.assertEqual(self.locations, set(self.LOCATION_WRITES))
        for (rel, qual, _target), domain in self.LOCATION_WRITES.items():
            with self.subTest(site=f"{rel}::{qual}"):
                self.assertIn(domain, self._named(rel, qual))

    def test_contrib_placements_are_followed_by_a_push(self):
        for (rel, qual), domain in self.CONTRIB_PLACEMENTS.items():
            with self.subTest(site=f"{rel}::{qual}"):
                self.assertIn(domain, self._named(rel, qual))

    def test_every_gauge_write_pushes_its_domain(self):
        for (rel, qual, target), domain in self.GAUGE_WRITES.items():
            with self.subTest(site=f"{rel}::{qual} {target}"):
                named = set()
                for call in self.pushes.get((rel, qual), []):
                    named |= _domains(call)
                self.assertIn(domain, named)


class TestAssignmentSites(ReactorMixin, EvenniaTest):
    """
    Pressures W4.2b: a placement by `obj.location =` runs no hook, so the
    function that makes it pushes -- the spawn and the craft completion here,
    the trade in TestTradePushes. Each "nothing" carries its receipt.
    """

    def test_spawn_pushes_the_room(self):
        from typeclasses import scripts

        rabbit = create_object("typeclasses.objects.Object", key="w42rabbit",
                               location=None, home=self.room1)
        with mock.patch.object(scripts, "spawn", return_value=[rabbit]), \
                mock.patch.object(client_state, "push_room_soon") as soon:
            scripts.CreatureSpawnScript._spawn_one("RABBIT", self.room1)
        self.assertEqual(rabbit.location, self.room1)
        soon.assert_called_once_with(self.room1)

    def test_unknown_species_pushes_nothing(self):
        from typeclasses import scripts

        with mock.patch.object(scripts, "spawn", return_value=[]), \
                mock.patch.object(scripts.logger, "log_err") as err, \
                mock.patch.object(client_state, "push_room_soon") as soon:
            scripts.CreatureSpawnScript._spawn_one("NOPE", self.room1)
        err.assert_called_once()   # receipt: the unknown-prototype return ran
        soon.assert_not_called()

    def test_craft_completion_pushes_char(self):
        from commands import crafting_commands as cc

        cmd = cc.CmdCraftGated()
        cmd.recipe = "w42"
        with mock.patch.object(cc.timed_actions, "claim", return_value=True), \
                mock.patch.object(cc.CmdCraft, "func") as contrib_func, \
                mock.patch.object(client_state, "push_soon") as soon:
            cc._complete_craft(self.char1, cmd, object())
        contrib_func.assert_called_once()   # receipt: the contrib half ran
        soon.assert_called_once_with(self.char1, "char")

    def test_refused_craft_pushes_nothing(self):
        from commands import crafting_commands as cc

        cmd = cc.CmdCraftGated()
        with mock.patch.object(cc.timed_actions, "claim", return_value=False) as claim, \
                mock.patch.object(client_state, "push_soon") as soon:
            cc._complete_craft(self.char1, cmd, object())
        claim.assert_called_once()   # receipt: the claim refused it
        soon.assert_not_called()


class TestTradePushes(TradeFixtureMixin, LedgerIsolationMixin, EvenniaCommandTest):
    """Pressures W4.2b's trade site: both parties' `char`, and only on a deal."""

    def test_a_completed_trade_pushes_both_parties(self):
        cup = self._item("w42cup")
        self.handler.offer(self.char1, cup)
        self.handler.offer(self.char2, currency=1)
        with mock.patch.object(client_state, "push") as push:
            self.assertTrue(self._complete())
        self.assertEqual(cup.location, self.char2)
        self.assertEqual([c.args for c in push.call_args_list],
                         [(self.char1, "char"), (self.char2, "char")])

    def test_an_unfinished_trade_pushes_nothing(self):
        cup = self._item("w42cup")
        self.handler.offer(self.char1, cup)
        self.handler.part_a_accepted = True
        with mock.patch.object(client_state, "push") as push:
            self.assertFalse(self.handler.finish())   # receipt: finish refused
        self.assertEqual(cup.location, self.char1)
        push.assert_not_called()

    def test_a_cancelled_trade_pushes_nothing(self):
        # finish(force=True) ends the trade and returns True, past the early
        # return, but nothing moved: the push belongs to the swap alone.
        cup = self._item("w42cup")
        self.handler.offer(self.char1, cup)
        with mock.patch.object(client_state, "push") as push:
            self.assertTrue(self.handler.finish(force=True))   # receipt: past `if not result`
        self.assertEqual(cup.location, self.char1)
        push.assert_not_called()


class TestObjectParentCensus(SimpleTestCase):
    """
    Pressures W5.1b: every typeclass under typeclasses/ inherits ObjectParent,
    so its at_object_delete pushes (W4.2) and its at_pre_put_in refuses a put
    into a non-container. A class built on a contrib base that does not reach
    settings.BASE_OBJECT_TYPECLASS (the clothing contrib's ContribClothing is
    a DefaultObject) misses both, silently; a new one fails here first.
    """

    # Read at runtime, not from the source: a contrib can inherit
    # BASE_OBJECT_TYPECLASS (the containers contrib does), so the bases a
    # class statement names are not its MRO.
    # A literal list the walk must find, so an empty walk cannot pass (W-z).
    KNOWN = {
        "typeclasses.characters.Character",
        "typeclasses.clothing.ClothingWithBuffs",
        "typeclasses.containers.Container",
        "typeclasses.objects.Object",
    }

    def _typeclasses(self):
        import importlib
        import inspect
        import pkgutil

        import typeclasses
        from evennia.objects.objects import DefaultObject

        found = {}
        for info in pkgutil.walk_packages(typeclasses.__path__, "typeclasses."):
            module = importlib.import_module(info.name)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if cls.__module__ == module.__name__ and issubclass(cls, DefaultObject):
                    found["%s.%s" % (module.__name__, name)] = cls
        return found

    def test_the_walk_finds_the_known_typeclasses(self):
        self.assertLessEqual(self.KNOWN, set(self._typeclasses()))

    def test_every_typeclass_inherits_object_parent(self):
        from typeclasses.objects import ObjectParent

        missing = sorted(
            path for path, cls in self._typeclasses().items() if not issubclass(cls, ObjectParent)
        )
        self.assertEqual(missing, [])

    def test_a_garment_refuses_a_put(self):
        # What B brings beside the push: the put refusal every other
        # non-container has (W4.2 Q3). Only a superuser passed get_from.
        from typeclasses.clothing import ClothingWithBuffs

        putter = mock.Mock()
        putter.ndb = mock.Mock()
        self.assertFalse(ClothingWithBuffs.at_pre_put_in(mock.Mock(), putter, mock.Mock()))
        putter.msg.assert_called_once_with("You can't put things in that.")
