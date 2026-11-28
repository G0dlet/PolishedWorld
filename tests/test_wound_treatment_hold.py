"""
A treatment under way holds a clock's death off: the alarm asks whether its
location is being treated, and while it is, waits and asks again. Healing,
Task HL-T8 (docs/PolishedWorld_Healing_Decomposition.md §2's third choice,
§9; Combat Design §4.4, HL4, WN4; *Legend* core p. 146).

The fixture is tests/test_wound_clocks.py's `_Clock`: char1 is CON 10,
POW 11 -- a head's clock of 52.5 s, a limb's of 1260 s -- with
`world.wounds._now`, `world.wounds.delay` and `world.timed_actions.delay`
patched, and each alarm fired by hand. The patient is char1. The healer is
char2, given a real session (`SecondSessionMixin`), so that its logging out
is a real one; its marker comes from a real `timed_actions.start`, whose
callback the patched `delay` never fires.

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
- `TestTheAlarmWaits`: **a due clock whose location is treated does not
  kill and sets one new alarm**, five seconds on, persistent, with the same
  deadline (red against the `_clock_due` before HL-T8: it killed); fired
  again with the treatment over, it kills once; **treating an arm does not
  hold the head's clock**; a stale marker is not believed; a note lost --
  `ndb` emptied, as a reload empties it -- leaves an alarm that kills; an
  early alarm during a treatment sets itself for what is left, not for the
  wait (a treatment buys no time); a clock stopped while the alarm waits
  sets nothing again; the body stays out while its clock is held.
- `TestTheNote`: **a second healer on a location is refused**, and accepted
  once the first is over, while another location is not refused; a healer
  who logs out protects no longer, and the slot is emptied; a patient who
  walks out of the room is no longer held; only one location is noted; the
  note is the marker itself, in `ndb`, and nothing is added to `db`.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_wound_treatment_hold
"""

from unittest import mock

from tests.test_currency_commands import SecondSessionMixin
from tests.test_wound_clocks import NOW, _Clock, _corpses, _said
from world import timed_actions, wounds


def _never(char, marker):
    """The treatment's callback; the patched `delay` never fires it."""


class _Hold(SecondSessionMixin, _Clock):
    def treat(self, location, healer=None):
        """The healer starts a timed action and notes it as this location's treatment."""
        healer = healer or self.char2
        marker = timed_actions.start(healer, "treat", 120, _never, label="treating")
        self.assertIsNotNone(marker)
        self.assertTrue(wounds.note_treatment(self.char1, location, healer, marker))
        return marker

    def ring(self, location, deadline):
        """The clock's alarm, fired by hand; returns what the patient was told."""
        with mock.patch.object(self.char1, "msg") as msg:
            wounds._clock_due(self.char1, location, deadline)
        return _said(msg)

    def dead(self, room=None):
        return len(_corpses(room or self.room1))


class TestTheAlarmWaits(_Hold):
    def test_a_due_clock_whose_location_is_treated_does_not_kill_and_asks_again(self):
        self.blow(8, "head")
        self.treat("head")
        self.at(52.5)
        calls = self.alarm.call_count
        said = self.ring("head", NOW + 52.5)
        self.assertEqual(self.dead(), 0)
        self.assertEqual(self.char1.location, self.room1)
        self.assertNotIn(wounds.CLOCK_OUT, said)
        self.assertEqual(self.alarm.call_count, calls + 1)
        self.alarm.assert_called_with(5, wounds._clock_due, self.char1, "head", NOW + 52.5,
                                      persistent=True)
        self.assertEqual(self.clocks(), {"head": NOW + 52.5})

    def test_fired_again_with_the_treatment_over_it_kills_once(self):
        self.blow(8, "head")
        self.treat("head")
        self.at(52.5)
        self.ring("head", NOW + 52.5)
        timed_actions.interrupt(self.char2)
        self.at(57.5)
        said = self.ring("head", NOW + 52.5)
        self.assertEqual(said[0], wounds.CLOCK_OUT)
        self.assertEqual(self.dead(), 1)
        self.assertEqual(self.char1.location, self.room2)
        self.ring("head", NOW + 52.5)
        self.assertEqual(self.dead(), 1)
        self.assertEqual(_corpses(self.room2), [])

    def test_treating_the_arm_does_not_hold_the_heads_clock(self):
        self.blow(6, "left_arm")   # won: the arm's clock, and awake
        self.treat("left_arm")
        self.blow(8, "head")
        self.at(52.5)
        self.ring("head", NOW + 52.5)
        self.assertEqual(self.dead(), 1)

    def test_a_stale_marker_is_not_believed(self):
        self.blow(8, "head")
        self.treat("head")
        timed_actions.interrupt(self.char2)
        self.assertIsNotNone(timed_actions.start(self.char2, "rest", 60, _never))
        self.assertFalse(wounds.being_treated(self.char1, "head"))
        self.at(52.5)
        self.ring("head", NOW + 52.5)
        self.assertEqual(self.dead(), 1)

    def test_a_lost_note_leaves_an_alarm_that_kills(self):
        self.blow(8, "head")
        self.treat("head")
        self.char1.ndb.wound_treatment = None   # what a reload leaves
        self.at(52.5)
        self.ring("head", NOW + 52.5)
        self.assertEqual(self.dead(), 1)

    def test_an_early_alarm_while_treated_sets_itself_for_what_is_left(self):
        self.blow(8, "head")
        self.treat("head")
        self.at(50)
        self.ring("head", NOW + 52.5)
        self.alarm.assert_called_with(2.5, wounds._clock_due, self.char1, "head", NOW + 52.5,
                                      persistent=True)
        self.assertEqual(self.dead(), 0)

    def test_a_clock_stopped_while_the_alarm_waits_sets_nothing_again(self):
        self.blow(8, "head")
        self.treat("head")
        self.at(52.5)
        self.ring("head", NOW + 52.5)
        self.assertTrue(wounds.stop_clock(self.char1, "head"))
        calls = self.alarm.call_count
        self.at(57.5)
        self.ring("head", NOW + 52.5)
        self.assertEqual(self.alarm.call_count, calls)
        self.assertEqual(self.dead(), 0)

    def test_the_body_stays_out_while_its_clock_is_held(self):
        self.blow(8, "head")
        self.treat("head")
        self.at(52.5)
        with mock.patch.object(self.char1, "msg") as mine:
            wounds._wake_due(self.char1, NOW + 52.5)
            wounds._clock_due(self.char1, "head", NOW + 52.5)
            self.assertTrue(wounds.unconscious(self.char1))
        self.assertNotIn(wounds.COME_TO, _said(mine))
        self.assertTrue(self.char1.attributes.has("wound_unconscious"))
        self.assertTrue(wounds.holds_body(self.char1))


class TestTheNote(_Hold):
    def test_a_second_healer_is_refused_and_accepted_once_the_first_is_over(self):
        self.blow(6, "left_arm")   # awake, so the patient can treat herself
        self.treat("left_arm")
        mine = timed_actions.start(self.char1, "treat", 120, _never, label="treating")
        self.assertFalse(wounds.note_treatment(self.char1, "left_arm", self.char1, mine))
        self.assertIs(self.char1.ndb.wound_treatment["left_arm"][0], self.char2)
        self.assertTrue(wounds.note_treatment(self.char1, "right_leg", self.char1, mine))
        timed_actions.interrupt(self.char2)
        self.assertTrue(wounds.note_treatment(self.char1, "left_arm", self.char1, mine))
        self.assertTrue(wounds.being_treated(self.char1, "left_arm"))

    def test_a_healer_who_logs_out_protects_no_longer(self):
        self.blow(8, "head")
        self.treat("head")
        self._disconnect_second_session()
        self.assertFalse(wounds.being_treated(self.char1, "head"))
        self.assertIsNone(self.char2.ndb.timed_action)
        self.at(52.5)
        self.ring("head", NOW + 52.5)
        self.assertEqual(self.dead(), 1)

    def test_a_patient_who_walks_out_of_the_room_is_not_held(self):
        self.blow(6, "left_arm")
        self.treat("left_arm")
        self.assertTrue(wounds.being_treated(self.char1, "left_arm"))
        self.char1.move_to(self.room2, quiet=True)
        self.assertFalse(wounds.being_treated(self.char1, "left_arm"))
        self.at(1260)
        self.ring("left_arm", NOW + 1260)
        self.assertEqual(self.dead(self.room2), 1)

    def test_only_one_location_is_noted(self):
        marker = timed_actions.start(self.char2, "treat", 120, _never)
        for word in (wounds.ALL, wounds.RANDOM, "tail"):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    wounds.note_treatment(self.char1, word, self.char2, marker)
        self.assertIsNone(self.char1.ndb.wound_treatment)

    def test_the_note_is_the_marker_itself_in_ndb_and_nothing_in_db(self):
        self.blow(8, "head")
        stored = {a.key for a in self.char1.attributes.all()}
        marker = self.treat("head")
        note = self.char1.ndb.wound_treatment
        self.assertEqual(set(note), {"head"})
        self.assertIs(note["head"][0], self.char2)
        self.assertIs(note["head"][1], marker)
        self.assertEqual({a.key for a in self.char1.attributes.all()}, stored)
