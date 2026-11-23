"""
The clocks: a Major Wound a body survives kills it when its time is out,
unless the clock is stopped; the location does not mend while it runs; and
a body a wound holds is not a statue. Wounds, Task WN-T10
(docs/PolishedWorld_Wounds_Decomposition.md; Combat Design §4.2, §4.4, WO3,
WN4, WN9, WN10; *Legend* core pp. 87, 146).

The fixture's char1 is CON 10, POW 11 -- CON + POW 21, the decomposition's
numbers: a vital clock of 52.5 s, a limb's of 1260 s. `world.wounds.time`
and `world.wounds.delay` are patched as in tests/test_wound_unconscious.py;
an alarm is fired by hand. char2 has no session (`has_account` counts
sessions), so it is the body whose player has gone.

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
- `TestTheClockStarts`: a head's Major Wound survived starts 52.5 s and an
  arm's 1260 s (WN4), stored as a deadline with a persistent alarm that
  carries the body, the location and the deadline; the body is told. The
  survived head is unconscious until that deadline (choice A); the arm,
  won, is not. A second Major Wound on a clocked location keeps the earlier
  deadline. A Serious Wound starts nothing.
- `TestTheAlarm`: on a passed deadline the body is told and dies, once;
  **on a stopped clock nothing happens** (red against a `_clock_due` that did
  not read the deadline); an alarm left by a clock since replaced does
  nothing; with two clocks the first death removes both and **the body is
  not killed again where it came back** (WN9); an early alarm sets itself
  again, a stale one does not; the head stays maimed (OQ-WN2).
- `TestHealing`: a clocked location is not mended and the others are; when
  only clocked locations are hurt there is no room to heal and the counter
  is zeroed (WN10; p. 87).
- `TestTheStatue`: `is_statue` is False for a body with no player and a
  clock, and True once it is stopped -- which turns it to stone, the line
  and the `away_since` stamp together (choice B); a logout with a clock says
  no stone line and stamps nothing; one without does both; a wound's
  unconsciousness holds the body too, and its waking turns it to stone; a
  body that dies with no player becomes a statue where it comes back,
  stamped and without a line. `holds_body` only reads: a passed
  unconsciousness is not woken by it (choice C).

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_wound_clocks
"""

from unittest import mock

from evennia.utils.test_resources import EvenniaTest

from tests.names_fixture import describe
from tests.test_fatigue import SEEN
from tests.test_wound_states import MADE, ROLL, WIN
from typeclasses.corpse import PlayerCorpse
from world import healing, wounds

NOW = 1_000_000.0
STONE = "turns to weathered stone"


def _said(msg_mock):
    """What a patched `msg` received, as plain strings (a room line is a tuple)."""
    return [str(c.args[0]) if c.args else str(c.kwargs.get("text"))
            for c in msg_mock.call_args_list]


def _corpses(room):
    return [o for o in room.contents if isinstance(o, PlayerCorpse)]


class _Clock(EvenniaTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.stats.pow.base = 11
            char.traits.fatigue.current = 100
            char.db.respawn_location = self.room2
        describe(self.char1, self.char2)
        clock = mock.patch("world.wounds.time")
        self.time = clock.start()
        self.time.time.return_value = NOW
        alarm = mock.patch("world.wounds.delay")
        self.alarm = alarm.start()
        slot = mock.patch("world.timed_actions.delay")
        slot.start()
        for patcher in (clock, alarm, slot):
            self.addCleanup(patcher.stop)

    def at(self, seconds):
        self.time.time.return_value = NOW + seconds

    def blow(self, amount, location, char=None, roll=WIN):
        """The writer, with the die fixed; returns what the body was told."""
        char = char or self.char1
        with mock.patch(ROLL, return_value=roll), mock.patch.object(char, "msg") as msg:
            char.apply_health_damage(amount, location=location, made=MADE)
        return _said(msg)

    def clocks(self, char=None):
        char = char or self.char1
        if not char.attributes.has("wound_clocks"):
            return None
        return dict(char.db.wound_clocks)


class TestTheClockStarts(_Clock):
    def test_a_survived_head_starts_52_and_a_half_seconds_and_is_out_until_then(self):
        said = self.blow(8, "head")
        self.assertEqual(self.clocks(), {"head": NOW + 52.5})
        self.alarm.assert_any_call(52.5, wounds._clock_due, self.char1, "head", NOW + 52.5,
                                   persistent=True)
        self.assertIn(wounds.CLOCK_START, said)
        self.assertEqual(dict(self.char1.db.wound_unconscious)["until"], NOW + 52.5)

    def test_an_arm_starts_1260_seconds_and_a_won_test_is_not_out(self):
        self.blow(6, "left_arm")   # arm 3: -3, Major
        self.assertEqual(self.clocks(), {"left_arm": NOW + 1260})
        self.assertFalse(self.char1.attributes.has("wound_unconscious"))

    def test_a_second_major_wound_keeps_the_earlier_deadline(self):
        self.blow(6, "left_arm")
        self.at(100)
        said = self.blow(1, "left_arm")
        self.assertEqual(self.clocks(), {"left_arm": NOW + 1260})
        self.assertNotIn(wounds.CLOCK_START, said)

    def test_a_serious_wound_starts_nothing(self):
        self.blow(3, "left_arm")
        self.assertIsNone(self.clocks())


class TestTheAlarm(_Clock):
    def test_a_passed_deadline_kills_once(self):
        self.blow(8, "head")
        self.at(52.5)
        with mock.patch.object(self.char1, "msg") as mine, \
                mock.patch.object(self.char2, "msg") as theirs:
            wounds._clock_due(self.char1, "head", NOW + 52.5)
        self.assertEqual(_said(mine)[0], wounds.CLOCK_OUT)
        self.assertIn(f"{SEEN} gives a last shudder and is still.", "\n".join(_said(theirs)))
        self.assertEqual(len(_corpses(self.room1)), 1)
        self.assertEqual(self.char1.location, self.room2)
        self.assertIsNone(self.clocks())
        self.assertFalse(self.char1.attributes.has("wound_unconscious"))
        self.assertEqual(dict(self.char1.db.wound_states), {"head": "maimed"})

    def test_a_stopped_clock_does_nothing(self):
        self.blow(6, "left_arm")
        self.assertTrue(wounds.stop_clock(self.char1, "left_arm"))
        self.assertFalse(wounds.stop_clock(self.char1, "left_arm"))
        self.at(1260)
        wounds._clock_due(self.char1, "left_arm", NOW + 1260)
        self.assertEqual(_corpses(self.room1), [])
        self.assertEqual(self.char1.location, self.room1)

    def test_an_alarm_from_a_replaced_clock_does_nothing(self):
        self.blow(6, "left_arm")
        wounds.stop_clock(self.char1, "left_arm")
        self.at(10)
        self.blow(1, "left_arm")   # wounded again: a new clock
        self.assertEqual(self.clocks(), {"left_arm": NOW + 1270})
        self.at(1260)
        wounds._clock_due(self.char1, "left_arm", NOW + 1260)
        self.assertEqual(_corpses(self.room1), [])

    def test_two_clocks_one_death_and_no_second_at_the_respawn_point(self):
        self.blow(6, "left_arm")
        self.blow(8, "head")
        self.at(52.5)
        wounds._clock_due(self.char1, "head", NOW + 52.5)
        self.assertIsNone(self.clocks())
        self.at(1260)
        wounds._clock_due(self.char1, "left_arm", NOW + 1260)
        self.assertEqual(len(_corpses(self.room1)), 1)
        self.assertEqual(_corpses(self.room2), [])
        self.assertEqual(self.char1.location, self.room2)

    def test_an_early_alarm_sets_itself_again_and_a_stale_one_does_not(self):
        self.blow(6, "left_arm")
        self.at(1259.5)
        calls = self.alarm.call_count
        wounds._clock_due(self.char1, "left_arm", NOW + 1260)
        self.assertEqual(self.alarm.call_count, calls + 1)
        wounds._clock_due(self.char1, "left_arm", NOW + 1000)   # not the stored one
        self.assertEqual(self.alarm.call_count, calls + 1)
        self.assertEqual(self.char1.location, self.room1)


class TestHealing(_Clock):
    def test_a_clocked_location_is_not_mended_and_the_others_are(self):
        self.blow(6, "left_arm")
        self.blow(2, "chest")
        self.assertEqual(wounds.room_to_heal(self.char1), 2)
        self.assertEqual(wounds.heal(self.char1, 1), 1)
        self.assertEqual(dict(self.char1.db.body_damage), {"left_arm": 6, "chest": 1})

    def test_only_clocked_hurt_has_no_room_and_zeroes_the_counter(self):
        self.blow(6, "left_arm")
        self.char1.db.heal_progress = 500
        self.assertEqual(wounds.room_to_heal(self.char1), 0)
        self.assertEqual(healing.accrue(self.char1, 100), 0)
        self.assertEqual(self.char1.db.heal_progress, 0)
        self.assertEqual(dict(self.char1.db.body_damage), {"left_arm": 6})


class TestTheStatue(_Clock):
    def test_no_player_and_a_clock_is_no_statue_until_it_is_stopped(self):
        self.blow(6, "left_arm", char=self.char2)
        self.assertFalse(self.char2.has_account)
        self.assertFalse(self.char2.is_statue)
        self.char2.db.away_since = None
        with mock.patch.object(self.char1, "msg") as witness:
            wounds.stop_clock(self.char2, "left_arm")
        self.assertTrue(self.char2.is_statue)
        self.assertIn(STONE, "\n".join(_said(witness)))
        self.assertIsNotNone(self.char2.db.away_since)

    def test_a_logout_with_a_clock_says_no_stone_line_and_stamps_nothing(self):
        self.blow(6, "left_arm", char=self.char2)
        self.char2.db.away_since = None
        with mock.patch.object(self.char1, "msg") as witness:
            self.char2.at_post_unpuppet()
        self.assertNotIn(STONE, "\n".join(_said(witness)))
        self.assertIsNone(self.char2.db.away_since)

    def test_a_logout_without_a_hold_turns_to_stone_and_stamps(self):
        self.char2.db.away_since = None
        with mock.patch.object(self.char1, "msg") as witness:
            self.char2.at_post_unpuppet()
        self.assertIn(STONE, "\n".join(_said(witness)))
        self.assertIsNotNone(self.char2.db.away_since)

    def test_unconsciousness_holds_the_body_and_its_waking_turns_it_to_stone(self):
        wounds.knock_out(self.char2, "head", 1)
        self.assertFalse(self.char2.is_statue)
        self.at(60)
        with mock.patch.object(self.char1, "msg") as witness:
            self.assertFalse(wounds.unconscious(self.char2))
        self.assertTrue(self.char2.is_statue)
        self.assertIn(STONE, "\n".join(_said(witness)))

    def test_a_death_with_no_player_is_a_statue_where_it_comes_back_without_a_line(self):
        self.blow(8, "head", char=self.char2)
        self.char1.move_to(self.room2, quiet=True)
        self.char2.db.away_since = None
        self.at(52.5)
        with mock.patch.object(self.char1, "msg") as witness:
            wounds._clock_due(self.char2, "head", NOW + 52.5)
        self.assertEqual(self.char2.location, self.room2)
        self.assertTrue(self.char2.is_statue)
        self.assertIsNotNone(self.char2.db.away_since)
        self.assertNotIn(STONE, "\n".join(_said(witness)))

    def test_holds_body_only_reads(self):
        wounds.knock_out(self.char2, "head", 1)
        self.at(60)
        self.assertFalse(wounds.holds_body(self.char2))
        self.assertTrue(self.char2.attributes.has("wound_unconscious"))   # not woken by the read
