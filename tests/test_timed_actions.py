"""
Unit tests for the shared timed-action slot (Epic A, TA1.1).

WHAT EACH CLASS PRESSURES
-------------------------
1. TestStartOccupiesTheSlot   -- the record is filled correctly and the delay is
   scheduled with the exact argument shape every consumer will rely on.
2. TestBusyRefusal            -- D3: a second action is refused EXPLICITLY, by
   name, and does not disturb the running one.
3. TestClaimVsIsCurrent       -- the one distinction the planning sketch missed:
   `claim` empties the slot, `is_current` must not.
4. TestStaleMarkers           -- walk away, come back, start again: the first
   callback must not land on the second attempt. THE mutation target.
5. TestLoggedOutIsCleanedUp   -- statue logout leaves the body (and its ndb)
   behind, so refusing is not enough; the slot has to be emptied.
6. TestInterrupt              -- message precedence, the room hook, and the
   no-op-when-idle contract `at_pre_move` depends on.
7. TestDeletedCharacter       -- a callback outliving its character refuses
   instead of raising.

⚠️ THE DELAY IS NOT DRIVEN THROUGH THE REACTOR
-----------------------------------------------
`start()` is the only function here that schedules anything, so it is the only
one that needs `delay` mocked -- and it is mocked to be ASSERTED ON, not merely
silenced: the argument order `(seconds, callback, char, *args, marker)` is the
contract TA1.2 and TA1.3 migrate onto, and a test that did not check it would
let a reordering through. Everywhere else the functions are called directly,
which is the same manoeuvre `tests/test_work_command.py` performs on
`_finish_task`, for the same reason.

Patching targets the name where it is CONSUMED (`world.timed_actions.delay`),
not where it is defined -- the house pattern from
`tests/test_improvement_engine.py`.

⚠️ has_account IS A SESSION COUNT, NOT AN ACCOUNT
--------------------------------------------------
`self.char2` has an account but no session in the stock fixture, which IS the
logged-out state (`Object.has_account` returns `self.sessions.count()`).
`tests/test_work_command.py` uses the same fixture fact for the same purpose.
"""

from unittest import mock

from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

from world import timed_actions
from world.timed_actions import (
    claim,
    interrupt,
    is_busy,
    is_current,
    start,
)

# Reused rather than re-typed: the swap-and-restore of `obj.msg` is already
# written, commented and justified in the work tests, and two copies of a
# capture helper would be two things to keep in step. Cross-importing a test
# helper has precedent here (`tests.test_currency.LedgerIsolationMixin`).
from tests.test_work_command import captured_messages


def _noop(char, marker):
    """A callback that is never actually fired -- only scheduled and asserted on."""


class TimedActionTestBase(EvenniaTest):
    """
    Builds `.char1` (puppeted) and `.char2` (no session) in a temp db.

    `EvenniaTest` rather than `EvenniaTestCase` because every function under
    test reads `.pk`, `.ndb` and `.has_account` off a real object -- there is no
    honest way to exercise the guards against a stand-in.
    """

    def start_action(self, char=None, key="work", seconds=20, label="working",
                     interrupt_msg="You break off what you were doing.",
                     on_interrupt=None):
        """Start an action with `delay` mocked, and hand back (marker, mock)."""
        char = char or self.char1
        with mock.patch("world.timed_actions.delay") as mocked:
            marker = start(
                char, key, seconds, _noop,
                label=label,
                interrupt_msg=interrupt_msg,
                on_interrupt=on_interrupt,
            )
        return marker, mocked


class TestStartOccupiesTheSlot(TimedActionTestBase):

    def test_start_returns_a_marker_and_fills_the_record(self):
        marker, _ = self.start_action()
        self.assertIsNotNone(marker)

        record = is_busy(self.char1)
        self.assertIsNotNone(record)
        self.assertIs(record.marker, marker)
        self.assertEqual(record.key, "work")
        self.assertEqual(record.label, "working")
        self.assertEqual(record.interrupt_msg, "You break off what you were doing.")

    def test_label_defaults_to_the_key(self):
        # The busy sentence is built from `label`; without this fallback an
        # action started without one would say "You are already None."
        with mock.patch("world.timed_actions.delay"):
            start(self.char1, "resting", 10, _noop)
        self.assertEqual(is_busy(self.char1).label, "resting")

    def test_the_delay_is_scheduled_with_char_first_and_marker_last(self):
        # This argument order IS the contract: `callback(char, *args, marker)`.
        # `_finish_task(caller, task_key, marker)` already has this shape, and
        # TA1.2 is only mechanical because of it.
        with mock.patch("world.timed_actions.delay") as mocked:
            marker = start(self.char1, "work", 20, _noop, "sweep", label="working")
        mocked.assert_called_once_with(20, _noop, self.char1, "sweep", marker)

    def test_two_characters_hold_independent_slots(self):
        # The slot is per character. If it were ever module-level state, one
        # player working would block every other player in the game.
        marker1, _ = self.start_action(char=self.char1)
        marker2, _ = self.start_action(char=self.char2)
        self.assertIsNotNone(marker2)
        self.assertIsNot(marker1, marker2)
        self.assertIs(is_busy(self.char1).marker, marker1)
        self.assertIs(is_busy(self.char2).marker, marker2)


class TestBusyRefusal(TimedActionTestBase):

    def test_a_second_start_is_refused_and_names_the_running_action(self):
        first, _ = self.start_action(label="working")
        with captured_messages(self.char1) as seen:
            with mock.patch("world.timed_actions.delay") as mocked:
                second = start(self.char1, "rest", 10, _noop, label="resting")

        self.assertIsNone(second)
        # D3: never a silent cancel, and never a vague "you are busy" -- the
        # message says WHICH action is in the way.
        self.assertTrue(seen)
        self.assertIn("already working", " ".join(seen))
        # Nothing was scheduled: an accepted-but-unscheduled start would look
        # identical from the slot's side.
        mocked.assert_not_called()
        # And the running action is untouched.
        self.assertIs(is_busy(self.char1).marker, first)


class TestClaimVsIsCurrent(TimedActionTestBase):

    def test_claim_succeeds_once_and_empties_the_slot(self):
        marker, _ = self.start_action()
        self.assertTrue(claim(self.char1, marker))
        self.assertIsNone(is_busy(self.char1))
        # One-shot: a second callback for the same attempt (a duplicated
        # schedule, a retry) must not complete it twice.
        self.assertFalse(claim(self.char1, marker))

    def test_is_current_is_repeatable_and_leaves_the_slot_standing(self):
        marker, _ = self.start_action(key="rest", label="resting")
        for _ in range(3):
            self.assertTrue(is_current(self.char1, marker))
        # This is the assertion that would have caught the sketch's claim-only
        # API: with `claim` here, rest would end on its own first tick.
        self.assertIsNotNone(is_busy(self.char1))
        self.assertIs(is_busy(self.char1).marker, marker)

    def test_is_current_is_false_once_claimed(self):
        marker, _ = self.start_action()
        claim(self.char1, marker)
        self.assertFalse(is_current(self.char1, marker))

    def test_both_refuse_an_empty_slot(self):
        self.assertIsNone(is_busy(self.char1))
        self.assertFalse(claim(self.char1, object()))
        self.assertFalse(is_current(self.char1, object()))


class TestStaleMarkers(TimedActionTestBase):
    """
    Start, leave, come back, start again.

    The first delay is still in flight and will land on the second attempt.
    Only marker IDENTITY refuses it -- the action key is identical in both
    attempts, so a key comparison would wave it through.

    This is also the class that closes a live defect the migration inherits:
    `rest` has no marker today, only a boolean `ndb.resting`, so
    rest -> walk -> rest leaves two tick loops running against one gauge.
    """

    def test_a_stale_marker_is_refused_by_claim(self):
        stale, _ = self.start_action()
        interrupt(self.char1)                      # walked away
        fresh, _ = self.start_action()             # started again

        self.assertFalse(claim(self.char1, stale))
        # The receipt that the refusal was about identity and not about an
        # empty slot: the CURRENT attempt is still intact and claimable.
        self.assertIsNotNone(is_busy(self.char1))
        self.assertTrue(claim(self.char1, fresh))

    def test_a_stale_marker_is_refused_by_is_current(self):
        stale, _ = self.start_action(key="rest", label="resting")
        interrupt(self.char1)
        fresh, _ = self.start_action(key="rest", label="resting")

        self.assertFalse(is_current(self.char1, stale))
        self.assertTrue(is_current(self.char1, fresh))

    def test_one_characters_marker_is_not_valid_on_another(self):
        # The character under test must be the PUPPETED one. Written the other
        # way round (asking char2 about char1's marker) both assertions pass
        # even with the identity check deleted, because char2's missing session
        # refuses them first -- a test that holds for a reason other than the
        # one it is named for. Found by the M1 mutant.
        self.start_action(char=self.char1)
        marker2, _ = self.start_action(char=self.char2)
        self.assertTrue(self.char1.has_account)
        self.assertFalse(claim(self.char1, marker2))
        self.assertFalse(is_current(self.char1, marker2))
        # Receipt: char1's own attempt was never touched by the refusals.
        self.assertIsNotNone(is_busy(self.char1))


class TestLoggedOutIsCleanedUp(TimedActionTestBase):
    """
    `char2` has no session, which is exactly the statue-logout state.

    Refusing is only half of it. Because `at_post_unpuppet()` does not call
    `super()`, the body and its `ndb` survive the session, so a slot that is
    refused but not emptied is a character who can never start anything again.
    """

    def test_claim_refuses_a_logged_out_character_and_still_frees_the_slot(self):
        marker, _ = self.start_action(char=self.char2)
        self.assertFalse(self.char2.has_account)

        self.assertFalse(claim(self.char2, marker))
        self.assertIsNone(is_busy(self.char2))

    def test_is_current_refuses_a_logged_out_character_and_frees_the_slot(self):
        marker, _ = self.start_action(char=self.char2)
        self.assertFalse(is_current(self.char2, marker))
        self.assertIsNone(is_busy(self.char2))

    def test_interrupt_frees_the_slot_without_messaging_or_side_effects(self):
        fired = []
        marker, _ = self.start_action(
            char=self.char2, on_interrupt=lambda char: fired.append(char)
        )

        with captured_messages(self.char2) as seen:
            self.assertTrue(interrupt(self.char2))

        # The independent receipt that the code ran at all, rather than the
        # assertions below passing because nothing happened: the slot changed.
        self.assertIsNone(is_busy(self.char2))
        self.assertEqual(seen, [])
        self.assertEqual(fired, [])


class TestInterrupt(TimedActionTestBase):

    def test_interrupt_clears_messages_and_runs_the_room_hook(self):
        fired = []
        self.start_action(
            key="rest",
            label="resting",
            interrupt_msg="You get up, interrupting your rest.",
            on_interrupt=lambda char: fired.append(char),
        )

        with captured_messages(self.char1) as seen:
            self.assertTrue(interrupt(self.char1))

        self.assertIsNone(is_busy(self.char1))
        self.assertIn("interrupting your rest", " ".join(seen))
        # The actor message cannot carry the room's half of it; that is what
        # `on_interrupt` exists for.
        self.assertEqual(fired, [self.char1])

    def test_an_explicit_reason_overrides_the_recorded_message(self):
        # Movement uses the recorded wording; the `rest` toggle supplies its
        # own. One action, two legitimate endings.
        self.start_action(
            key="rest",
            label="resting",
            interrupt_msg="You get up, interrupting your rest.",
        )
        with captured_messages(self.char1) as seen:
            interrupt(self.char1, "You stop resting.")

        joined = " ".join(seen)
        self.assertIn("You stop resting.", joined)
        self.assertNotIn("interrupting your rest", joined)

    def test_interrupting_an_idle_character_is_a_silent_no_op(self):
        # `at_pre_move` calls this on EVERY move, so the idle path must be both
        # false and quiet -- otherwise walking around narrates itself.
        with captured_messages(self.char1) as seen:
            self.assertFalse(interrupt(self.char1))
        self.assertEqual(seen, [])

    def test_an_action_with_no_interrupt_message_is_still_cleared(self):
        marker, _ = self.start_action(interrupt_msg=None)
        with captured_messages(self.char1) as seen:
            self.assertTrue(interrupt(self.char1))
        self.assertIsNone(is_busy(self.char1))
        self.assertEqual(seen, [])
        self.assertFalse(claim(self.char1, marker))


class TestDeletedCharacter(TimedActionTestBase):
    """
    A delay outliving its character. The marker is fabricated here on purpose:
    the `pk` guard is asserted to fire BEFORE identity is ever consulted, so a
    real marker would test a different branch.
    """

    def setUp(self):
        super().setUp()
        self.ghost = create.create_object(
            self.char1.typeclass_path, key="ghost", location=self.room1
        )

    def test_all_entry_points_refuse_a_deleted_character(self):
        self.ghost.delete()
        self.assertIsNone(self.ghost.pk)

        marker = object()
        self.assertFalse(claim(self.ghost, marker))
        self.assertFalse(is_current(self.ghost, marker))
        self.assertFalse(interrupt(self.ghost))


class TestModuleLayering(TimedActionTestBase):

    def test_world_does_not_import_from_commands_or_typeclasses(self):
        # `world/` is the lower layer. `_format_wait` lives in
        # `commands/work_commands.py` and stays there; a convenience import
        # here would invert the dependency for one string helper.
        source = open(timed_actions.__file__).read()
        code = "\n".join(
            line for line in source.splitlines()
            if line.startswith(("import ", "from "))
        )
        self.assertNotIn("commands", code)
        self.assertNotIn("typeclasses", code)
