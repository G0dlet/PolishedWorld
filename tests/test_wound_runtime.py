"""
A deadline is counted in the server's runtime, so it stands still while
the server is down. Healing, Task HL-T1
(docs/PolishedWorld_Healing_Decomposition.md §6; Combat Design §4.4, HL11,
and the notes at WN4 and CE6; OQ-HL5).

These tests do not patch the modules' own readers of *now*. They patch
`time.time` everywhere and the two globals Evennia's `gametime.runtime()`
is built on -- `SERVER_RUNTIME`, the counter, and
`SERVER_RUNTIME_LAST_UPDATED`, the wall-clock time it was last saved --
and drive a stop and a start the way `evennia/server/service.py` does
(:88-103): at the start the counter is read back as it was saved at the
stop, and its wall-clock time is the start's. So the modules are read
through the real `runtime()`, and a line that reads the wall clock is seen
reading it.

The fixture's char1 is CON 10, POW 11: an arm's clock is 1260 s.

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
- `TestAStop`: a clock started before a stop of 10 000 s is not due after
  it, and its alarm, fired early by the task handler, sets itself again for
  the time that was left at the stop (red against a `_clock_due` that reads
  the wall clock, HLM2); `minutes_until` reads the same time left; a
  wound's unconsciousness is still on after the stop, and `holds_body` says
  so (HLM4).
- `TestTheStoredSize`: a deadline and the end of an unconsciousness are
  stored at the runtime's size, below 10^9, and not the wall clock's (HLM1,
  HLM3).
- `TestAnOldValue`: a deadline stored in wall-clock time before HL-T1 is
  never due and holds the body for good -- the reason the listing line of
  the Healing Decomposition §6 is run before the reload (HL11, risk 2).
- `TestACreature`: a creature's state started before a stop is not due
  after it, and its alarm sets itself again for what was left; its `due` is
  stored at the runtime's size (OQ-HL5; HLM4b).

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_wound_runtime
"""

from unittest import mock

from evennia.utils import gametime
from evennia.utils.create import create_object
from evennia.utils.test_resources import EvenniaTest

from tests.names_fixture import describe
from world import creature_wounds, hero_points, wounds

WALL = 1_800_000_000.0   # the wall clock when the clock is started
RUN = 5_000.0            # the server's runtime then
DOWN = 10_000.0          # how long the server is down
UP = 10.0                # how long it ran on before the stop
ARM = 1260.0             # an arm's clock at CON + POW 21


class _Runtime(EvenniaTest):
    def setUp(self):
        super().setUp()
        for char in (self.char1, self.char2):
            char.stats.pow.base = 11
            char.traits.fatigue.current = 100
            char.db.respawn_location = self.room2
            hero_points.set_glancing(char, False)
        describe(self.char1, self.char2)
        self.wall = self._patch(mock.patch("time.time", return_value=WALL))
        self._patch(mock.patch.object(gametime, "SERVER_RUNTIME", RUN))
        self._patch(mock.patch.object(gametime, "SERVER_RUNTIME_LAST_UPDATED", WALL))
        self.alarm = self._patch(mock.patch("world.wounds.delay"))
        self.creature_alarm = self._patch(mock.patch("world.creature_wounds.delay"))
        self._patch(mock.patch("world.timed_actions.delay"))

    def _patch(self, patcher):
        found = patcher.start()
        self.addCleanup(patcher.stop)
        return found

    def stop_and_start(self):
        """
        The server runs on for UP seconds, stops, is down DOWN seconds and
        starts: the counter is read back as saved at the stop, and stamped
        with the start's wall-clock time.
        """
        start = WALL + UP + DOWN
        gametime.SERVER_RUNTIME = RUN + UP
        gametime.SERVER_RUNTIME_LAST_UPDATED = start
        self.wall.return_value = start


class TestAStop(_Runtime):
    def test_a_clock_is_not_due_after_a_stop_and_its_alarm_waits_for_what_was_left(self):
        deadline = wounds.start_clock(self.char1, "left_arm")
        self.stop_and_start()
        self.alarm.reset_mock()
        with mock.patch.object(self.char1, "at_character_death") as death:
            wounds._clock_due(self.char1, "left_arm", deadline)
        death.assert_not_called()
        self.assertEqual(wounds.clocks_of(self.char1), {"left_arm": deadline})
        self.alarm.assert_called_once_with(mock.ANY, wounds._clock_due, self.char1,
                                           "left_arm", deadline, persistent=True)
        self.assertAlmostEqual(self.alarm.call_args.args[0], ARM - UP, places=3)

    def test_the_minutes_left_are_those_at_the_stop(self):
        deadline = wounds.start_clock(self.char1, "left_arm")
        self.stop_and_start()
        self.assertAlmostEqual(wounds.minutes_until(deadline), (ARM - UP) / wounds.MINUTE,
                               places=3)

    def test_an_unconsciousness_is_still_on_after_a_stop_and_holds_the_body(self):
        wounds.knock_out(self.char1, "head", 10)
        self.stop_and_start()
        self.assertTrue(wounds.holds_body(self.char1))
        self.assertTrue(wounds.unconscious(self.char1))


class TestTheStoredSize(_Runtime):
    def test_a_deadline_is_stored_at_the_runtimes_size(self):
        deadline = wounds.start_clock(self.char1, "left_arm")
        self.assertLess(deadline, 1e9)
        self.assertAlmostEqual(deadline, RUN + ARM, places=3)

    def test_the_end_of_an_unconsciousness_is_stored_at_the_runtimes_size(self):
        wounds.knock_out(self.char1, "head", 10)
        until = self.char1.db.wound_unconscious["until"]
        self.assertLess(until, 1e9)
        self.assertAlmostEqual(until, RUN + 10 * wounds.MINUTE, places=3)


class TestAnOldValue(_Runtime):
    def test_a_wall_clock_deadline_is_never_due_and_holds_the_body(self):
        old = WALL + 60.0
        self.char1.db.wound_clocks = {"left_arm": old}
        self.stop_and_start()
        with mock.patch.object(self.char1, "at_character_death") as death:
            wounds._clock_due(self.char1, "left_arm", old)
        death.assert_not_called()
        self.assertTrue(wounds.holds_body(self.char1))


class TestACreature(_Runtime):
    def setUp(self):
        super().setUp()
        self.beast = create_object("typeclasses.creatures.Creature", key="hare",
                                   location=self.room1)

    def test_a_creatures_state_is_not_due_after_a_stop_and_waits_for_what_was_left(self):
        seconds = 12.5
        creature_wounds._set_state(self.beast, creature_wounds.DYING, seconds)
        due = creature_wounds.state_of(self.beast)["due"]
        self.stop_and_start()
        self.creature_alarm.reset_mock()
        with mock.patch.object(self.beast, "at_death") as death:
            creature_wounds._state_due(self.beast, creature_wounds.DYING, due)
        death.assert_not_called()
        self.creature_alarm.assert_called_once_with(
            mock.ANY, creature_wounds._state_due, self.beast, creature_wounds.DYING, due,
            persistent=True)
        self.assertAlmostEqual(self.creature_alarm.call_args.args[0], seconds - UP, places=3)

    def test_a_creatures_due_is_stored_at_the_runtimes_size(self):
        creature_wounds._set_state(self.beast, creature_wounds.OUT, 60)
        due = creature_wounds.state_of(self.beast)["due"]
        self.assertLess(due, 1e9)
        self.assertAlmostEqual(due, RUN + 60, places=3)
