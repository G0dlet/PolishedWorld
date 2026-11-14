"""
Unit tests for `world.arrival` (Arrival Decomposition, Task AV-T1; Newcomer
Design Z1). The resolver has no caller yet; AV-T2 calls it from `node_done`.

These run the shipped `seed_data` through the shipped `seed_world()`, with
`room1` standing in for Limbo, as `tests/test_seeding.py` does: the temple
found here is the temple a fresh database builds.

WHAT EACH CLASS PRESSURES
-------------------------
- TestArrivalRoom -- the constant naming a room that is not seeded, or the
  room found by something other than its seed tag (AVM4: a key lookup finds
  nothing once the key is edited in game).
- TestArrive -- the move and the `home` write (OQ-AV1: does `home` take a
  plain assignment?), a character already in the temple, and a move that ran
  the hooks (AVM2: the first screen would show the temple twice).
- TestRespawnAfterArrival -- the reason for AV3: without the `home` write a
  made character respawns in Limbo when `DEFAULT_RESPAWN_DBREF` is unset
  (AVM1). The two answers above `home` in the order still win.
- TestRoomPushes -- the hookless move runs neither room's hook, so `arrive`
  pushes both rooms itself, as death does (AVM4b).
- TestArrivalNeverRaises -- AV6: an unseeded database, a refused move and a
  resolver that raises all end in None, a log line and no exception (AVM3: a
  miss that raised would be caught and traced, so the test reads which log
  line was written).

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_arrival
"""
from unittest import mock

from django.test import override_settings
from evennia.utils.test_resources import EvenniaTest

from world import arrival
from world import chargen_menu
from world import client_state
from world import seed_data
from world.seeding import SEED_CATEGORY, find_seeded, seed_world

TEMPLE_KEY = "Old Temple"   # seed_data's key for alpha.room.temple, by hand


class _ArrivalBase(EvenniaTest):
    """room1 stands in for Limbo; char1 is the newcomer, at home in room1."""

    character_typeclass = "typeclasses.characters.Character"

    def seed(self):
        seed_world(limbo=self.room1)
        return find_seeded(seed_data.ARRIVAL_ROOM)


class TestArrivalRoom(_ArrivalBase):

    def test_the_constant_names_a_seeded_room(self):
        self.assertIn(seed_data.ARRIVAL_ROOM, [row["seed_id"] for row in seed_data.ROOMS])

    def test_none_before_seeding(self):
        self.assertIsNone(arrival.arrival_room())

    def test_the_seeded_temple_after(self):
        temple = self.seed()
        self.assertEqual(arrival.arrival_room(), temple)
        self.assertEqual(temple.key, TEMPLE_KEY)
        self.assertTrue(temple.tags.has(seed_data.ARRIVAL_ROOM, category=SEED_CATEGORY))

    def test_found_by_seed_tag_after_its_key_is_edited(self):
        # AVM4: a building pass may rename the room in game; the tag stays.
        temple = self.seed()
        temple.key = "Hall of Pillars"
        self.assertEqual(arrival.arrive(self.char1), temple)
        self.assertEqual(self.char1.location, temple)


class TestArrive(_ArrivalBase):

    def test_location_and_home_are_the_temple(self):
        temple = self.seed()
        self.assertEqual(self.char1.home, self.room1)   # receipt: the fixture's home
        self.assertEqual(arrival.arrive(self.char1), temple)
        self.assertEqual(self.char1.location, temple)
        self.assertEqual(self.char1.home, temple)

    def test_home_survives_a_fresh_read(self):
        # OQ-AV1: the setter saves; a cache-free read sees the temple.
        temple = self.seed()
        arrival.arrive(self.char1)
        self.char1.refresh_from_db()
        self.assertEqual(self.char1.db_home, temple)

    def test_already_in_the_temple_sets_home_and_does_not_move(self):
        temple = self.seed()
        self.char1.move_to(temple, quiet=True, move_hooks=False)
        self.assertEqual(self.char1.home, self.room1)
        with mock.patch.object(self.char1, "move_to") as move:
            self.assertEqual(arrival.arrive(self.char1), temple)
        move.assert_not_called()
        self.assertEqual(self.char1.home, temple)

    def test_nothing_is_said_to_the_newcomer(self):
        # AVM2: with hooks, at_post_move would look at the room here, and the
        # menu's closing `look` would show it a second time.
        self.seed()
        with mock.patch.object(self.char1, "msg") as msg:
            arrival.arrive(self.char1)
        msg.assert_not_called()


@override_settings(DEFAULT_RESPAWN_DBREF=None)
class TestRespawnAfterArrival(_ArrivalBase):

    def test_respawns_in_the_temple_with_no_setting(self):
        temple = self.seed()
        self.assertEqual(self.char1._get_respawn_location(), self.room1)   # before: Limbo's stand-in
        arrival.arrive(self.char1)
        self.assertEqual(self.char1._get_respawn_location(), temple)

    def test_the_per_character_override_still_wins(self):
        self.seed()
        self.char1.db.respawn_location = self.room2
        arrival.arrive(self.char1)
        self.assertEqual(self.char1._get_respawn_location(), self.room2)

    def test_the_setting_still_wins(self):
        self.seed()
        arrival.arrive(self.char1)
        with override_settings(DEFAULT_RESPAWN_DBREF=self.room2.dbref):
            self.assertEqual(self.char1._get_respawn_location(), self.room2)


class TestRoomPushes(_ArrivalBase):

    def test_both_rooms_are_pushed_after_the_move(self):
        temple = self.seed()
        with mock.patch.object(client_state, "push_room_soon") as soon:
            arrival.arrive(self.char1)
        self.assertEqual(soon.call_args_list, [mock.call(self.room1), mock.call(temple)])

    def test_no_push_when_nothing_moved(self):
        temple = self.seed()
        self.char1.move_to(temple, quiet=True, move_hooks=False)
        with mock.patch.object(client_state, "push_room_soon") as soon:
            arrival.arrive(self.char1)
        soon.assert_not_called()


class TestArrivalNeverRaises(_ArrivalBase):

    def test_unseeded_returns_none_changes_nothing_and_warns(self):
        with mock.patch.object(arrival.logger, "log_warn") as warn, \
                mock.patch.object(arrival.logger, "log_trace") as trace:
            self.assertIsNone(arrival.arrive(self.char1))
        self.assertEqual(self.char1.location, self.room1)
        self.assertEqual(self.char1.home, self.room1)
        self.assertEqual(warn.call_count, 1)
        self.assertIn(seed_data.ARRIVAL_ROOM, warn.call_args.args[0])
        trace.assert_not_called()

    def test_a_refused_move_returns_none_and_keeps_the_new_home(self):
        temple = self.seed()
        with mock.patch.object(self.char1, "move_to", return_value=False), \
                mock.patch.object(client_state, "push_room_soon") as soon, \
                mock.patch.object(arrival.logger, "log_warn") as warn:
            self.assertIsNone(arrival.arrive(self.char1))
        self.assertEqual(self.char1.location, self.room1)
        self.assertEqual(self.char1.home, temple)
        self.assertEqual(warn.call_count, 1)
        soon.assert_not_called()

    def test_a_raising_resolver_returns_none_and_traces(self):
        self.seed()
        with mock.patch.object(arrival, "find_seeded", side_effect=RuntimeError("boom")), \
                mock.patch.object(arrival.logger, "log_trace") as trace:
            self.assertIsNone(arrival.arrive(self.char1))
        self.assertEqual(self.char1.location, self.room1)
        self.assertEqual(self.char1.home, self.room1)
        self.assertEqual(trace.call_count, 1)

    def test_both_modules_import_together(self):
        # AV-T2 makes chargen_menu import arrival; this module imports both at
        # the top, so a cycle would fail its collection before any test ran.
        self.assertTrue(callable(arrival.arrive))
        self.assertTrue(callable(chargen_menu.node_done))
