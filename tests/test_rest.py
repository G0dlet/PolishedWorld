"""
Unit tests for `rest` on the shared timed-action slot. Epic A, Task TA1.3.

Until TA1.3 there were no tests for `rest` at all -- not for the toggle, not for
the tick, not for movement. Everything here is new coverage, and the classes are
arranged by the question each one answers rather than by method.

WHAT IS WORTH TESTING HERE
--------------------------
1. **The slot is the only state.** `rest` occupies `ndb.timed_action` under key
   "rest", label "resting", and there is no private flag left to drift out of
   sync with it.
2. **The tick asks without taking, and takes exactly once.** `is_current()` on
   every tick, `claim()` on the tick that ends the rest (T11). A tick that took
   the slot every time would end the rest on its first tick; a final tick that
   never took it would leave the character resting forever.
3. **Stale ticks are inert.** rest -> walk -> rest used to leave two tick loops
   on one gauge (the defect TA1.1's TestStaleMarkers names). The marker closes
   it; `TestStaleRestTicks` is the regression.
4. **Exclusion is explicit and does not interrupt** (D3). `rest` during a chore
   is answered with the chore's label and the chore still pays; `work` during a
   rest is answered with the rest's label and the rest still ticks.
5. **Every way a rest ends empties the slot**: toggle, move, full gauge, missing
   gauge, death, logout.

⚠️ THE TICK IS DRIVEN BY HAND
------------------------------
`_rest_tick(char, marker)` is module level (T10) precisely so a test can call it
without a reactor. `delay` is patched WHERE IT IS CONSUMED --
`world.timed_actions.delay` for the first tick (scheduled by `start()`),
`typeclasses.characters.delay` for every reschedule -- both to stop a real task
being queued and to observe what would have been scheduled. The marker is read
off the slot through `_marker_of`, never fabricated: a fabricated marker would
make every "stale tick is refused" test pass with the identity check deleted.

⚠️ FATIGUE IS LOWERED BY HAND IN setUp
---------------------------------------
In play only the survival ticker lowers fatigue; `_rest_tick` raises it. The
setUp write bypasses the ticker. No ticker runs in the test database, so
nothing races or repairs the value -- the invariant being suspended is "fatigue
only falls through the ticker", and it is suspended for the length of one test.

⚠️ ROOM MESSAGES
-----------------
`msg_contents()` delivers `text=(message, kwargs)`, so a captured room line is
the tuple's string form. Room assertions are therefore `assertIn` against the
joined capture, never equality. char2 stands in room1 in the stock fixture and
is the listener; it has no session, which does not stop `msg()` being called.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_rest
"""

import ast
import inspect
import textwrap
from unittest import mock

from django.test import override_settings

from evennia.utils.test_resources import EvenniaCommandTest

from commands import consumption_commands
from commands.consumption_commands import CmdRest
from commands.work_commands import CmdWork, _cooldown_key, _finish_task
from typeclasses import characters
from typeclasses.characters import _announce_getting_up, _rest_tick
from world import timed_actions

from tests.test_work_command import WorkTestBase, _marker_of, captured_messages


TIRED = 50  # well below full, well above zero: several ticks from either edge


def _joined(seen):
    return "\n".join(seen)


class RestTestBase(EvenniaCommandTest):
    """char1 tired in room1, char2 listening in room1."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.fatigue = self.char1.traits.get("fatigue")
        self.fatigue.current = TIRED  # bypasses the survival ticker; see module docstring

    def start_rest(self, caller=None):
        """Start a rest through the real command; return the marker it minted."""
        caller = caller or self.char1
        self.call(CmdRest(), "", caller=caller)
        return _marker_of(caller)


class TestRestOccupiesTheSlot(RestTestBase):
    """
    The migration itself, asserted rather than assumed.

    A `rest` that kept a private flag next to the slot would pass every
    behavioural test below; these are the ones it would fail.
    """

    def test_rest_occupies_the_shared_slot_under_its_key_and_label(self):
        self.start_rest()
        record = timed_actions.is_busy(self.char1)
        self.assertIsNotNone(record)
        self.assertEqual(record.key, "rest")
        self.assertEqual(record.label, "resting")
        self.assertIs(record.on_interrupt, _announce_getting_up)
        self.assertIsNone(self.char1.ndb.resting)

    def test_starting_a_rest_says_so(self):
        self.call(CmdRest(), "", "You settle down to rest.", caller=self.char1)

    def test_the_first_tick_is_the_module_level_callback(self):
        # T10. start() schedules callback(char, *args, marker); with a bound
        # method this would be self + char + marker, and the tick would break
        # on its first call rather than here.
        with mock.patch("world.timed_actions.delay") as scheduled:
            marker = self.start_rest()
        scheduled.assert_called_once_with(
            self.char1.rest_interval, _rest_tick, self.char1, marker
        )

    def test_a_full_gauge_is_refused_and_occupies_nothing(self):
        # The fatigue trap from the handoff: this sentence comes from
        # start_resting(), not from the slot. It must not leave a record behind.
        self.fatigue.current = self.fatigue.max
        self.call(CmdRest(), "", "You are not tired.", caller=self.char1)
        self.assertIsNone(timed_actions.is_busy(self.char1))


class TestRestTicks(RestTestBase):
    """
    is_current() on every tick, claim() on the last (T11).

    Pressures the two ways a repeating action can mishandle its slot: taking it
    too early (the rest ends after one tick) or never taking it (the character
    is busy forever after the gauge is full).
    """

    def test_a_tick_restores_rest_recovery_and_keeps_the_slot(self):
        marker = self.start_rest()
        with mock.patch("typeclasses.characters.delay") as rescheduled:
            _rest_tick(self.char1, marker)
        self.assertEqual(self.fatigue.current, TIRED + self.char1.rest_recovery)
        self.assertIs(_marker_of(self.char1), marker)
        rescheduled.assert_called_once_with(
            self.char1.rest_interval, _rest_tick, self.char1, marker
        )

    def test_rest_ticks_to_full_then_empties_the_slot(self):
        marker = self.start_rest()
        # Ticks needed, from the source constants rather than from memory.
        needed = -(-(self.fatigue.max - TIRED) // self.char1.rest_recovery)
        self.assertGreater(needed, 1)  # otherwise "keeps the slot" is untested here

        ticks = 0
        with captured_messages(self.char1) as seen, \
                captured_messages(self.char2) as room, \
                mock.patch("typeclasses.characters.delay") as rescheduled:
            while timed_actions.is_busy(self.char1) is not None and ticks < needed + 5:
                _rest_tick(self.char1, marker)
                ticks += 1

        self.assertEqual(ticks, needed)
        self.assertEqual(self.fatigue.current, self.fatigue.max)
        self.assertIsNone(timed_actions.is_busy(self.char1))
        # Every tick but the last rescheduled; the last did not.
        self.assertEqual(rescheduled.call_count, needed - 1)
        self.assertIn("You feel fully rested.", _joined(seen))
        self.assertIn(f"{self.char1.key} gets up, looking refreshed.", _joined(room))

    def test_a_missing_gauge_ends_the_rest_and_empties_the_slot(self):
        marker = self.start_rest()
        self.char1.traits.remove("fatigue")
        with mock.patch("typeclasses.characters.delay") as rescheduled:
            _rest_tick(self.char1, marker)
        self.assertIsNone(timed_actions.is_busy(self.char1))
        rescheduled.assert_not_called()


class TestRestToggle(RestTestBase):
    """`rest` while resting ends the rest, with the toggle's own sentence."""

    def test_rest_while_resting_stops_it(self):
        self.start_rest()
        with captured_messages(self.char2) as room:
            self.call(CmdRest(), "", "You stop resting.", caller=self.char1)
        self.assertIsNone(timed_actions.is_busy(self.char1))
        self.assertIn(f"{self.char1.key} gets up.", _joined(room))

    def test_the_tick_after_a_toggle_off_changes_nothing(self):
        marker = self.start_rest()
        # Receipt that this marker's tick path is live: it moves the gauge once.
        with mock.patch("typeclasses.characters.delay"):
            _rest_tick(self.char1, marker)
        after_one_tick = self.fatigue.current
        self.assertEqual(after_one_tick, TIRED + self.char1.rest_recovery)

        self.call(CmdRest(), "", caller=self.char1)  # toggle off
        with mock.patch("typeclasses.characters.delay") as rescheduled:
            _rest_tick(self.char1, marker)
        self.assertEqual(self.fatigue.current, after_one_tick)
        rescheduled.assert_not_called()


class TestMovementInterruptsRest(RestTestBase):
    """
    New coverage: there was no test for moving during a rest before TA1.3.

    Since TA1.3 the resting branch in at_pre_move is gone, so everything here
    goes through the single interrupt() line and the record's own messages.
    """

    def test_moving_tells_the_rester(self):
        # Positive assertion through move_to() is sound (Testing Reference
        # §11d): the arrival `look` cannot produce this sentence.
        self.start_rest()
        with captured_messages(self.char1) as seen:
            self.char1.move_to(self.room2, quiet=True)
        self.assertIn("You get up, interrupting your rest.", _joined(seen))
        self.assertIsNone(timed_actions.is_busy(self.char1))

    def test_moving_tells_the_room_left_behind(self):
        # The hook is called directly so char1 is still in room1 when
        # on_interrupt runs; its return value is the receipt that it ran.
        self.start_rest()
        with captured_messages(self.char2) as room:
            allowed = self.char1.at_pre_move(self.room2)
        self.assertTrue(allowed)
        self.assertIn(f"{self.char1.key} gets up.", _joined(room))

    def test_the_tick_after_a_move_changes_nothing(self):
        marker = self.start_rest()
        with mock.patch("typeclasses.characters.delay"):
            _rest_tick(self.char1, marker)  # receipt: the live marker moves the gauge
        after_one_tick = self.fatigue.current
        self.assertEqual(after_one_tick, TIRED + self.char1.rest_recovery)

        self.char1.at_pre_move(self.room2)
        with mock.patch("typeclasses.characters.delay") as rescheduled:
            _rest_tick(self.char1, marker)
        self.assertEqual(self.fatigue.current, after_one_tick)
        rescheduled.assert_not_called()


class TestStaleRestTicks(RestTestBase):
    """
    rest -> walk -> rest: the defect the marker closes.

    Before TA1.3 the first rest's tick was still in flight when the second rest
    set the flag again, so both loops ran against one gauge -- double recovery,
    forever. Named by TA1.1's TestStaleMarkers docstring as the rest-level
    regression; keep the class name in step with that reference.
    """

    def test_a_stale_tick_neither_recovers_nor_reschedules(self):
        stale = self.start_rest()
        self.char1.at_pre_move(self.room2)
        fresh = self.start_rest()
        self.assertIsNotNone(fresh)
        self.assertIsNot(stale, fresh)

        with mock.patch("typeclasses.characters.delay") as rescheduled:
            _rest_tick(self.char1, stale)
        self.assertEqual(self.fatigue.current, TIRED)
        rescheduled.assert_not_called()
        # The stale tick did not touch the live rest either.
        self.assertIs(_marker_of(self.char1), fresh)

    def test_only_the_fresh_rest_recovers(self):
        # The receipt for the test above: same window, the live marker DOES move
        # the gauge -- so "unchanged" there means refused, not "never ran".
        stale = self.start_rest()
        self.char1.at_pre_move(self.room2)
        fresh = self.start_rest()

        with mock.patch("typeclasses.characters.delay") as rescheduled:
            _rest_tick(self.char1, stale)
            _rest_tick(self.char1, fresh)
        self.assertEqual(self.fatigue.current, TIRED + self.char1.rest_recovery)
        rescheduled.assert_called_once_with(
            self.char1.rest_interval, _rest_tick, self.char1, fresh
        )


@override_settings(TREASURY_DBREF="")
class TestRestAndWorkExcludeEachOther(WorkTestBase):
    """
    D3 across two commands: refused out loud, never interrupted.

    Uses the real CmdWork in a funded temple (WorkTestBase), because the point is
    the sentence each command's `label` produces through start() -- a synthetic
    record would test timed_actions, which test_timed_actions.py already does.
    """

    def setUp(self):
        super().setUp()
        self.settings_override = override_settings(TREASURY_DBREF=self.treasury.dbref)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.fatigue = self.char1.traits.get("fatigue")
        self.fatigue.current = TIRED  # bypasses the survival ticker; see module docstring

    def test_rest_during_a_chore_is_refused_with_the_chores_label(self):
        self.call(CmdWork(), "sweep", caller=self.char1)
        chore = _marker_of(self.char1)
        returned = self.call(
            CmdRest(), "", "You are already working.", caller=self.char1
        )
        # A refused rest says nothing else: no "settle down" for a rest that
        # never began.
        self.assertNotIn("settle", returned)
        self.assertIs(_marker_of(self.char1), chore)

    def test_rest_during_a_chore_leaves_the_chore_to_pay(self):
        self.call(CmdWork(), "sweep", caller=self.char1)
        chore = _marker_of(self.char1)
        self.call(CmdRest(), "", caller=self.char1)
        _finish_task(self.char1, "sweep", chore)
        self.assertEqual(self.char1.currency.value, 25)

    def test_work_during_a_rest_is_refused_with_the_rests_label(self):
        self.call(CmdRest(), "", caller=self.char1)
        rest = _marker_of(self.char1)
        self.call(CmdWork(), "sweep", "You are already resting.", caller=self.char1)
        self.assertIs(_marker_of(self.char1), rest)
        # T8 ordering: the cooldown gate passed, so nothing was stamped.
        self.assertTrue(self.char1.cooldowns.ready(_cooldown_key("sweep")))

    def test_not_tired_wins_over_busy(self):
        # T8's precedent applied to rest: the gate about the action the player
        # named answers first. Both sentences are true.
        self.call(CmdWork(), "sweep", caller=self.char1)
        chore = _marker_of(self.char1)
        self.fatigue.current = self.fatigue.max
        self.call(CmdRest(), "", "You are not tired.", caller=self.char1)
        self.assertIs(_marker_of(self.char1), chore)

    def test_stop_resting_during_a_chore_is_a_no_op(self):
        # T12. A bare interrupt() wrapper would cancel the chore here and tell
        # the worker "You stop resting.". The return value is the receipt that
        # the method ran; the payout is the receipt that the chore survived.
        self.call(CmdWork(), "sweep", caller=self.char1)
        chore = _marker_of(self.char1)
        with captured_messages(self.char1) as seen:
            ended = self.char1.stop_resting()
        self.assertFalse(ended)
        self.assertEqual(seen, [])
        self.assertIs(_marker_of(self.char1), chore)
        _finish_task(self.char1, "sweep", chore)
        self.assertEqual(self.char1.currency.value, 25)


class TestDeathEndsTheRest(RestTestBase):
    """
    D7: death relocates with move_hooks=False, so at_pre_move never runs.

    Before TA1.3 a rest survived death and kept ticking at the respawn point.
    at_character_death() now interrupts the slot itself, unsilenced (T13).
    """

    def test_death_empties_the_slot(self):
        self.start_rest()
        self.char1.at_character_death()
        self.assertIsNone(timed_actions.is_busy(self.char1))

    def test_the_tick_after_death_changes_nothing(self):
        marker = self.start_rest()
        with captured_messages(self.char1) as seen:
            self.char1.at_character_death()
        self.assertIn("You have died.", _joined(seen))  # receipt: death ran
        # Death restores health, hunger and thirst -- not fatigue -- so the
        # gauge is still TIRED and a live tick would move it.
        self.assertEqual(self.fatigue.current, TIRED)
        with mock.patch("typeclasses.characters.delay") as rescheduled:
            _rest_tick(self.char1, marker)
        self.assertEqual(self.fatigue.current, TIRED)
        rescheduled.assert_not_called()

    def test_the_rester_hears_the_interrupt_before_dying(self):
        # T13, asserted so a later change to it is a decision and not a drift.
        self.start_rest()
        with captured_messages(self.char1) as seen:
            self.char1.at_character_death()
        lines = [line for line in seen if "interrupting your rest" in line or "You have died." in line]
        self.assertEqual(len(lines), 2, seen)
        self.assertIn("interrupting your rest", lines[0])
        self.assertIn("You have died.", lines[1])

    def test_the_room_where_they_fell_sees_them_get_up(self):
        # The ordering claim in at_character_death ("first, so on_interrupt
        # never sees a half-moved body"), made testable: respawn somewhere
        # else, and the "gets up" must still land in the room they fell in.
        # An interrupt placed after the relocation announces it at the temple.
        self.char1.db.respawn_location = self.room2
        self.start_rest()
        with captured_messages(self.char2) as room:
            self.char1.at_character_death()
        self.assertEqual(self.char1.location, self.room2)  # receipt: they did move
        self.assertIn(f"{self.char1.key} gets up.", _joined(room))

    def test_an_idle_death_says_nothing_about_actions(self):
        # The no-op path through the new line. Death sends other lines of its
        # own (DeathWeakness announces itself), so "the capture holds only the
        # death line" is false, and "no line looks like an interrupt" would
        # pass with the interrupt() call deleted (Testing Reference §11d). The
        # spy measures exactly what was said DURING the interrupt call, and its
        # record is the receipt that the call happened: once, on an empty slot.
        real_interrupt = timed_actions.interrupt
        during = []
        with captured_messages(self.char1) as seen:

            def spy(char, *args, **kwargs):
                before = len(seen)
                result = real_interrupt(char, *args, **kwargs)
                during.append((result, seen[before:]))
                return result

            with mock.patch("world.timed_actions.interrupt", side_effect=spy):
                self.char1.at_character_death()
        self.assertEqual(during, [(False, [])])
        self.assertIn("You have died.", _joined(seen))

    def test_a_failing_interrupt_does_not_abort_death(self):
        # The inner guard. Without it an exception here would skip respawn and
        # strand the character at 0 HP -- the exact failure the corpse-spawn
        # guard further down already exists to prevent.
        self.start_rest()
        health = self.char1.traits.get("health")
        health.current = health.min
        with mock.patch("world.timed_actions.interrupt", side_effect=RuntimeError("boom")), \
                mock.patch.object(characters.logger, "log_trace") as logged, \
                captured_messages(self.char1) as seen:
            self.char1.at_character_death()
        logged.assert_called_once()
        self.assertEqual(health.current, health.max)
        self.assertIn("You have died.", _joined(seen))


class TestStatueLogoutRest(RestTestBase):
    """
    T3 through rest: an unpuppeted body's tick clears the slot and does nothing.

    char2 has an account but no session in the stock fixture -- exactly the
    statue-logout state.
    """

    def test_an_unpuppeted_rest_stops_at_its_first_tick(self):
        self.assertFalse(self.char2.has_account)
        fatigue = self.char2.traits.get("fatigue")
        fatigue.current = TIRED  # bypasses the survival ticker; see module docstring
        self.char2.start_resting()
        marker = _marker_of(self.char2)
        self.assertIsNotNone(marker)  # receipt: the rest did begin

        with captured_messages(self.char1) as room, \
                mock.patch("typeclasses.characters.delay") as rescheduled:
            _rest_tick(self.char2, marker)
        self.assertEqual(fatigue.current, TIRED)
        self.assertIsNone(timed_actions.is_busy(self.char2))
        rescheduled.assert_not_called()
        self.assertEqual(room, [])  # nobody is seen getting up


class TestOneSlotOneBranch(RestTestBase):
    """
    Structural guards for the epic's whole point (D1).

    Behaviour tests cannot see a private flag that is written but never read,
    or a second branch in at_pre_move that happens to agree with the first.
    These read the source, like TestS4MintInvariant does for add().
    """

    def test_no_private_rest_flag_remains(self):
        for module in (characters, consumption_commands):
            self.assertNotIn("ndb.resting", inspect.getsource(module), module.__name__)

    def test_at_pre_move_has_no_branches(self):
        source = inspect.getsource(characters.Character.at_pre_move)
        tree = ast.parse(textwrap.dedent(source))
        branches = [node for node in ast.walk(tree) if isinstance(node, ast.If)]
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "interrupt"
        ]
        self.assertTrue(calls, "at_pre_move no longer calls interrupt()")
        self.assertEqual(branches, [])
