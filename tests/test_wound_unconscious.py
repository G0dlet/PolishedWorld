"""
A wound's unconsciousness: its own cause and its own waking. Wounds, Task
WN-T9 (docs/PolishedWorld_Wounds_Decomposition.md; Combat Design §4.4, WO1,
WN3, WN11; *Legend* core p. 145).

`world.wounds._now` is patched, so the stored time and every read of it
agree on a fixed now, and `world.wounds.delay` is patched, so an alarm is
seen being set and is fired by hand. `world.timed_actions.delay` is patched
too: a started action schedules nothing. Nothing in play knocks a body out
before ML; every case is a blow or a `knock_out` put on by hand.

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
- `TestKnockedOutByTheWriter`: the writer carries out what WN-T8's outcome
  calls for -- a vital Serious Wound lost is out for the damage in minutes
  (WN3: a minute is 60 real seconds), a limb's Major Wound lost the same;
  a won test is not out. The time is stored, the alarm is persistent and
  carries the body and the time, and the body and the room are told.
- `TestRefused`: WN11's one refusal with two causes. A drink and a step
  through an exit are refused with `OUT_COLD`, the walk once and quietly
  (no *You cannot go there.*); a rest -- every timed action -- is refused
  by `timed_actions.start` (choice A). **The first refusal leaves the
  timed-action slot empty**: the test of §2's third choice, red against a
  version that set `db.collapsed`, whose refusal arms fatigue's recovery.
  Knocking out interrupts what the slot held, as a collapse does.
- `TestWaking`: from the stored time, so nothing depends on the alarm -- a
  command after the time wakes the body; the alarm wakes it by itself;
  an alarm that fires a little early sets itself again; an alarm left by an
  earlier knock-out does nothing, and does not set itself again when it
  fires early (WNM36c: the waking is safe without that check, the task
  table is not); a second knock-out keeps the later time and says *goes
  dark* once.
- `TestTwoCauses`: a body collapsed and knocked out is still down when
  either ends; while a wound keeps it out, the collapse's recovery is not
  armed, and a refusal says nothing of it.
- `TestEnds`: a death ends it without a waking line (WN9); `revive` -- HL's,
  with no caller in WN -- wakes it now.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_wound_unconscious
"""

from unittest import mock

from evennia.utils.test_resources import EvenniaCommandTest

from commands.consumption_commands import CmdDrink, CmdRest
from tests.names_fixture import describe
from tests.test_fatigue import SEEN
from tests.test_wound_states import LOSE, MADE, ROLL, WIN
from typeclasses.characters import _rest_tick
from world import hero_points, timed_actions, wounds

NOW = 1_000_000.0


def _said(msg_mock):
    """What a patched `msg` received, as plain strings (a room line is a tuple)."""
    return [str(c.args[0]) if c.args else str(c.kwargs.get("text"))
            for c in msg_mock.call_args_list]


class _Out(EvenniaCommandTest):
    """char1 Fresh, with a respawn point; char2 reads char1 by description."""

    def setUp(self):
        super().setUp()
        self.char1.traits.fatigue.current = 100
        self.char1.db.respawn_location = self.room2
        # Glancing Blow off: these tests drive Major Wounds, and a body with
        # Hero Points would have each one trimmed to a Serious Wound (HE1;
        # Hero Points decomposition §4, P1, and HE-T5).
        hero_points.set_glancing(self.char1, False)
        describe(self.char1, self.char2)
        clock = mock.patch("world.wounds._now")
        self.now = clock.start()
        self.now.return_value = NOW
        alarm = mock.patch("world.wounds.delay")
        self.alarm = alarm.start()
        slot = mock.patch("world.timed_actions.delay")
        slot.start()
        for patcher in (clock, alarm, slot):
            self.addCleanup(patcher.stop)

    def at(self, seconds):
        """Move the patched clock to NOW + seconds."""
        self.now.return_value = NOW + seconds

    def stored(self):
        if not self.char1.attributes.has("wound_unconscious"):
            return None
        return dict(self.char1.db.wound_unconscious)

    def knock(self, minutes, location="head"):
        """knock_out by hand; return (char1's lines, char2's lines)."""
        with mock.patch.object(self.char1, "msg") as mine, \
                mock.patch.object(self.char2, "msg") as theirs:
            wounds.knock_out(self.char1, location, minutes)
        return _said(mine), _said(theirs)

    def slot(self):
        return timed_actions.is_busy(self.char1)


class TestKnockedOutByTheWriter(_Out):
    def blow(self, amount, location, roll):
        with mock.patch(ROLL, return_value=roll), \
                mock.patch.object(self.char1, "msg") as mine, \
                mock.patch.object(self.char2, "msg") as theirs:
            self.char1.apply_health_damage(amount, location=location, made=MADE)
        return _said(mine), _said(theirs)

    def test_a_vital_serious_wound_lost_is_out_for_the_damage_in_minutes(self):
        mine, theirs = self.blow(5, "head", LOSE)   # head 4: -1, Serious
        self.assertEqual(self.stored(), {"location": "head", "until": NOW + 300})
        self.alarm.assert_called_once_with(
            300.0, wounds._wake_due, self.char1, NOW + 300, persistent=True)
        self.assertIn(wounds.KNOCKED_OUT, mine)
        self.assertIn(f"{SEEN} crumples and lies still.", "\n".join(theirs))

    def test_a_limbs_major_wound_lost_is_out_for_the_damage_in_minutes(self):
        self.blow(8, "left_leg", LOSE)
        self.assertEqual(self.stored(), {"location": "left_leg", "until": NOW + 480})

    def test_a_won_test_is_not_out(self):
        self.blow(5, "head", WIN)
        self.assertIsNone(self.stored())
        self.alarm.assert_not_called()


class TestRefused(_Out):
    def setUp(self):
        super().setUp()
        self.knock(1)

    def test_a_drink_is_refused(self):
        self.call(CmdDrink(), "", wounds.OUT_COLD, caller=self.char1)

    def test_a_step_is_refused_once_and_quietly(self):
        with mock.patch.object(self.char1, "msg") as msg:
            self.exit.at_traverse(self.char1, self.room2)
        self.assertEqual(self.char1.location, self.room1)
        self.assertEqual(_said(msg), [wounds.OUT_COLD])

    def test_the_first_refusal_leaves_the_slot_empty(self):
        self.assertTrue(self.char1.refuse_if_collapsed("Your hands will not obey you."))
        self.assertIsNone(self.slot())

    def test_a_timed_action_is_refused(self):
        self.char1.traits.fatigue.current = 50   # tired: `rest` reaches `start`
        self.call(CmdRest(), "", wounds.OUT_COLD, caller=self.char1)
        self.assertIsNone(self.slot())
        self.assertIsNone(timed_actions.start(self.char1, "work", 60, lambda *a: None))

    def test_knocking_out_interrupts_the_slot(self):
        self.char1.attributes.remove("wound_unconscious")
        timed_actions.start(self.char1, "rest", 10, _rest_tick, label="resting",
                            interrupt_msg="You get up, interrupting your rest.")
        mine, _theirs = self.knock(1)
        self.assertEqual(mine, ["You get up, interrupting your rest.", wounds.KNOCKED_OUT])
        self.assertIsNone(self.slot())


class TestWaking(_Out):
    def test_a_command_after_the_time_wakes_the_body(self):
        self.knock(1)
        self.at(60)
        out = self.call(CmdDrink(), "", caller=self.char1)
        self.assertIn(wounds.COME_TO, out)
        self.assertNotIn(wounds.OUT_COLD, out)
        self.assertIsNone(self.stored())

    def test_the_alarm_wakes_the_body_by_itself(self):
        self.knock(1)
        _seconds, callback, char, until = self.alarm.call_args.args
        self.at(60)
        with mock.patch.object(self.char1, "msg") as mine, \
                mock.patch.object(self.char2, "msg") as theirs:
            callback(char, until)
        self.assertEqual(_said(mine), [wounds.COME_TO])
        self.assertIn(f"{SEEN} stirs and comes to.", "\n".join(_said(theirs)))
        self.assertIsNone(self.stored())

    def test_an_early_alarm_sets_itself_again(self):
        self.knock(1)
        self.at(59.5)
        wounds._wake_due(self.char1, NOW + 60)
        self.assertIsNotNone(self.stored())
        self.alarm.assert_called_with(0.5, wounds._wake_due, self.char1, NOW + 60,
                                      persistent=True)

    def test_an_alarm_left_by_an_earlier_knock_out_does_nothing(self):
        self.knock(1)
        mine, _theirs = self.knock(3)
        self.assertEqual(mine, [])   # already out: not told twice
        self.assertEqual(self.stored()["until"], NOW + 180)
        self.at(60)
        wounds._wake_due(self.char1, NOW + 60)
        self.assertIsNotNone(self.stored())

    def test_a_stale_alarm_that_fires_early_does_not_set_itself_again(self):
        # Waking is already safe without the alarm's own check -- unconscious()
        # reads the stored time -- but a stale alarm must not leave another
        # persistent task behind it (WNM36c).
        self.knock(1)
        self.knock(3)
        alarms = self.alarm.call_count
        self.at(59.5)
        wounds._wake_due(self.char1, NOW + 60)
        self.assertEqual(self.alarm.call_count, alarms)

    def test_a_shorter_second_knock_out_keeps_the_later_time(self):
        self.knock(3)
        self.assertFalse(wounds.knock_out(self.char1, "chest", 1))
        self.assertEqual(self.stored(), {"location": "head", "until": NOW + 180})

    def test_before_the_time_the_body_is_still_out(self):
        self.knock(1)
        self.at(59)
        self.assertTrue(wounds.unconscious(self.char1))


class TestTwoCauses(_Out):
    def setUp(self):
        super().setUp()
        self.char1.db.collapsed = True
        self.knock(1)

    def test_while_out_the_collapse_is_not_armed_and_says_nothing(self):
        with mock.patch.object(self.char1, "msg") as msg:
            self.char1.arm_collapse()
        self.assertIsNone(self.slot())
        self.assertEqual(_said(msg), [])

    def test_awake_from_the_wound_the_collapse_still_holds(self):
        self.at(60)
        self.assertTrue(self.char1.refuse_if_collapsed("down"))
        self.assertIsNone(self.stored())
        self.assertIsNotNone(self.slot())   # the collapse's recovery, armed by that refusal

    def test_up_from_the_collapse_the_wound_still_holds(self):
        self.char1.attributes.remove("collapsed")
        self.call(CmdDrink(), "", wounds.OUT_COLD, caller=self.char1)


class TestEnds(_Out):
    def test_a_death_ends_it_without_a_waking_line(self):
        self.knock(1)
        with mock.patch.object(self.char1, "msg") as msg:
            self.char1.apply_health_damage(8, location=wounds.ALL)
        self.assertEqual(self.char1.location, self.room2)
        self.assertIsNone(self.stored())
        self.assertNotIn(wounds.COME_TO, _said(msg))

    def test_revive_wakes_it_now(self):
        self.knock(3)
        with mock.patch.object(self.char1, "msg") as msg:
            self.assertTrue(wounds.revive(self.char1))
        self.assertEqual(_said(msg), [wounds.COME_TO])
        self.assertIsNone(self.stored())
        self.assertFalse(wounds.revive(self.char1))
