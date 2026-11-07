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
  5A  world is global; weather always; room carries `indoor`
  6B  push is per domain: a failing builder is logged and skipped
  7A  at_post_puppet always pushes all four
  8A  the spy sits on session.data_out; pw_state is reached via data_in
  M12 a second session on the puppet proves pw_state answers only the asker
"""

import json
from unittest import mock

import evennia
from evennia import create_object
from evennia.contrib.base_systems import custom_gametime as cgt
from evennia.server import sessionhandler
from evennia.utils.ansi import strip_ansi
from evennia.utils.test_resources import EvenniaTest
from evennia.utils.utils import callables_from_module

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
    second read, markup in the name, and a missing trait crashing the build.
    """

    def test_keys_and_types(self):
        snap = client_state.char_snapshot(self.char1)
        self.assertEqual(set(snap), {"name", "health", "encumbrance"})
        self.assertEqual(set(snap["health"]), {"current", "max", "desc"})
        for key in ("current", "max"):
            self.assertIs(type(snap["health"][key]), int)
        self.assertEqual(set(snap["encumbrance"]), {"carried", "limit", "band"})
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
        self.assertEqual(set(snap), {"name", "health", "encumbrance"})


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
    Pressures lock 4C: the snapshot replicates look's filters, so each list
    is checked against the look text for the same viewer -- the statue under
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
