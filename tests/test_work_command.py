"""
Unit tests for the temple faucet. Stage 4, Component D.1.

Written to the pattern in `tests/test_knowledge.py` (AGENTS.md section 0A) and
to the ledger-isolation and settings-override patterns already established in
`tests/test_currency.py` and `tests/test_treasury.py`.

WHAT IS ACTUALLY WORTH TESTING HERE
-----------------------------------
1. **The payout is a transfer, and money is conserved.** Both sides asserted,
   every time. A test that only checks the wallet went up would pass just as
   happily against a minting faucet, which is the one thing this component must
   never become.
2. **`add()` never appears in the module.** Asserted against the file's own
   source text. Everything else in this file tests behaviour that a future
   minting implementation could still satisfy; this is the test that could not
   be satisfied by one.
3. **A failed attempt leaves the cooldown unset.** The locked all-or-nothing
   rule. Dry Treasury, wrong room, stale marker, logged out -- four paths, and
   none of them may cost the player their next attempt.
4. **A stale callback cannot pay a later attempt.** The identity-marker
   mechanism. Without it, "start, walk out, come back, start again" pays twice
   for one chore.
5. **The place gate.** Wrong room and no Treasury configured are one answer.

⚠️ THE DELAY IS NOT DRIVEN THROUGH THE REACTOR
-----------------------------------------------
`CmdWork.func()` schedules `_finish_task` via `utils.delay` and returns. These
tests drive the two halves separately: `.call()` for the start, then a direct
call to `_finish_task(char, key, marker)` for the payout. That is why the payout
lives in a module-level function rather than a closure or a bound method -- it
makes the interesting half of the command reachable without a running reactor.

The marker the tests pass is read off `char.ndb.working`, i.e. the real one the
command minted, not a fabricated one. A test that fabricated its own marker
would pass while the identity check was broken.

⚠️ LEDGER ISOLATION -- INHERIT THE MIXIN
-----------------------------------------
The ledger is a *global* Script and is NOT rebuilt per test. Funding the
Treasury here calls `add()`, which writes an entry, so every class in this file
inherits `LedgerIsolationMixin`.

⚠️ COOLDOWN ISOLATION
----------------------
Per decomposition section 6/D and Testing Reference section 7: no helper here
calls `cooldowns.clear()`. It would wipe unrelated cooldowns and make the suite
order-dependent. Cooldown state is asserted and stamped by its specific key
only, via `_cooldown_key()` -- the same function the command uses, so a rename
cannot silently decouple test from code.

⚠️ `.call()` DOES NOT RUN COMMAND LOCKS
----------------------------------------
Evennia Reference section 11.26 / AGENTS Rev 4. `work` is `cmd:all()` so there
is no permission test to write, but the lock string is asserted directly rather
than by driving an unprivileged caller through `.call()`, which would pass
vacuously.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_work_command
    evennia test --settings settings.py tests
"""

import ast
import inspect
from contextlib import contextmanager

from django.test import override_settings

from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTestCase

from commands import work_commands
from commands.work_commands import (
    TEMPLE_TASKS,
    CmdWork,
    _cooldown_key,
    _finish_task,
    _format_wait,
    _resolve_task,
    _validate_task_table,
)
from typeclasses.treasury import Treasury
from world import economy_log

from tests.test_currency import LedgerIsolationMixin


@contextmanager
def captured_messages(obj):
    """
    Collect everything `obj.msg()` receives inside the block.

    `.call()` cannot be used for the payout half: `_finish_task` is invoked
    directly, outside any command runner, so the runner's own mock is not in
    place and `obj.msg` is still the real bound method.

    The swap-and-restore is the same manoeuvre `EvenniaCommandTestMixin.call()`
    performs on its receivers (`receiver.msg = Mock()`, restored by assignment
    afterwards), verified in `evennia/utils/test_resources.py` -- so this is the
    house mechanism applied by hand, not a new trick.

    Args:
        obj (Object): the receiver to listen to.

    Yields:
        list[str]: messages, appended as they arrive.
    """
    seen = []
    original = obj.msg

    def collect(text="", *args, **kwargs):
        seen.append(str(text))

    obj.msg = collect
    try:
        yield seen
    finally:
        obj.msg = original


class TestTaskTable(EvenniaTestCase):
    """
    The table itself. Pure data, so the lightest base class that works.

    These are cheap and they guard the tuning surface: the table is explicitly
    the anchor for balance changes, and a change made there lands in a delayed
    callback where a bad value is expensive to diagnose.
    """

    def test_the_five_documented_chores_are_present(self):
        # Canonical from PolishedWorld_GameGold_Economy.md's task table.
        self.assertEqual(
            set(TEMPLE_TASKS),
            {"sweep", "water", "books", "candles", "altar"},
        )

    def test_rewards_match_the_design_document(self):
        expected = {
            "sweep": 25,
            "water": 35,
            "books": 50,
            "candles": 25,
            "altar": 35,
        }
        actual = {key: task["copper"] for key, task in TEMPLE_TASKS.items()}
        self.assertEqual(actual, expected)

    def test_cooldowns_match_the_design_document(self):
        # 1h / 1h / 2h / 1h / 2h, in real seconds.
        expected = {
            "sweep": 3600,
            "water": 3600,
            "books": 7200,
            "candles": 3600,
            "altar": 7200,
        }
        actual = {key: task["cooldown"] for key, task in TEMPLE_TASKS.items()}
        self.assertEqual(actual, expected)

    def test_the_full_chain_is_170_copper(self):
        # Deliberately allowed in one sitting: cooldowns are per task, and the
        # real brake is a finite Treasury. If this number changes, it should be
        # because someone meant it to.
        self.assertEqual(sum(t["copper"] for t in TEMPLE_TASKS.values()), 170)

    def test_a_zero_reward_is_rejected_at_import_time(self):
        # WHY THIS MATTERS: transfer_to() RAISES on a non-positive amount (D7 --
        # False means "could not afford" and nothing else), and it would raise
        # inside a delayed callback with no command context to report it. The
        # validator turns that into an import error while somebody is looking.
        with self.assertRaises(ValueError):
            _validate_task_table({"broken": dict(TEMPLE_TASKS["sweep"], copper=0)})

    def test_a_missing_flavour_string_is_rejected_at_import_time(self):
        broken = dict(TEMPLE_TASKS["sweep"])
        broken["done_room"] = ""
        with self.assertRaises(ValueError):
            _validate_task_table({"broken": broken})

    def test_a_boolean_is_not_accepted_as_a_number(self):
        # bool is a subclass of int in Python, so `isinstance(True, int)` is
        # True and `True > 0`. Without the explicit bool exclusion, a chore
        # tuned to `"copper": True` would pass validation and pay one Copper.
        with self.assertRaises(ValueError):
            _validate_task_table({"broken": dict(TEMPLE_TASKS["sweep"], copper=True)})


def _called_attributes(module):
    """
    Every dotted attribute call in a module, as strings like "currency.add".

    Parsed with `ast` rather than grepped. The first draft of these tests
    searched the raw source text and failed instantly -- against itself. This
    module's docstring *explains* that it must never call `currency.add(...)`,
    and quotes the call to do so, and a text search cannot tell the warning
    from the violation. An AST walk sees only executable code, which is the
    only place the invariant can actually be broken.

    Returns:
        set[str]: e.g. {"currency.transfer_to", "cooldowns.add", "caller.msg"}.
    """
    found = set()
    for node in ast.walk(ast.parse(inspect.getsource(module))):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        owner = func.value
        if isinstance(owner, ast.Attribute):
            found.add(f"{owner.attr}.{func.attr}")
        elif isinstance(owner, ast.Name):
            found.add(f"{owner.id}.{func.attr}")
    return found


class TestS4MintInvariant(EvenniaTestCase):
    """
    The regression guard for S4-1, asserted against the module's parsed code.

    Every other test in this file describes behaviour a minting implementation
    could also produce: the player's wallet goes up either way. Only this one
    can tell the difference, and it is the reason the component exists.
    """

    def test_the_faucet_module_never_calls_the_mint_primitive(self):
        calls = _called_attributes(work_commands)
        self.assertNotIn(
            "currency.add",
            calls,
            msg="S4-1 VIOLATED: the faucet is minting. It must transfer.",
        )

    def test_the_faucet_module_never_calls_the_burn_primitive(self):
        calls = _called_attributes(work_commands)
        self.assertNotIn("currency.burn", calls)

    def test_the_payout_is_a_treasury_transfer(self):
        # The positive half. Asserting only the absence of `add` would also
        # pass against a faucet that paid nothing at all.
        calls = _called_attributes(work_commands)
        self.assertIn("currency.transfer_to", calls)

    def test_the_faucet_module_does_not_import_mint_vocabulary(self):
        # A faucet has no business knowing what a valid mint source is called.
        # Import names are code, not prose, so this one is safe to read off the
        # module namespace directly.
        self.assertFalse(hasattr(work_commands, "MINT_SOURCES"))


class TestFormatWait(EvenniaTestCase):
    """Wait rendering. `forage`'s bare `{left}s` is unreadable at two hours."""

    def test_under_a_minute_is_seconds(self):
        self.assertEqual(_format_wait(45), "45 seconds")

    def test_minutes(self):
        self.assertEqual(_format_wait(12 * 60), "12 minutes")

    def test_singular_minute(self):
        self.assertEqual(_format_wait(60), "1 minute")

    def test_hours_and_minutes(self):
        self.assertEqual(_format_wait(3600 + 54 * 60), "1 hour 54 minutes")

    def test_whole_hours_omit_the_minutes(self):
        self.assertEqual(_format_wait(7200), "2 hours")

    def test_negative_does_not_render_a_minus(self):
        # time_left() clamps at zero, but a rendering helper that produces
        # "-3 seconds" if it ever sees one is a bug waiting for a caller.
        self.assertEqual(_format_wait(-5), "0 seconds")


class TestResolveTask(EvenniaTestCase):
    """Input matching: exact key, then key prefix, then display-name substring."""

    def test_exact_key(self):
        self.assertEqual(_resolve_task("sweep"), ("sweep", []))

    def test_case_and_whitespace_insensitive(self):
        self.assertEqual(_resolve_task("  ALTAR "), ("altar", []))

    def test_unique_prefix(self):
        self.assertEqual(_resolve_task("can"), ("candles", []))

    def test_display_name_substring(self):
        # "work floors" should find the sweeping chore.
        self.assertEqual(_resolve_task("floors"), ("sweep", []))

    def test_no_match_returns_nothing(self):
        self.assertEqual(_resolve_task("brew ale"), (None, []))

    def test_empty_returns_nothing(self):
        self.assertEqual(_resolve_task("   "), (None, []))


class WorkTestBase(LedgerIsolationMixin, EvenniaCommandTest):
    """
    A funded Treasury standing in char1's room, and `TREASURY_DBREF` pointed at
    it for the duration of each test.

    `override_settings` rather than hand-setting the attribute: it restores the
    previous state even when an assertion raises partway through, which
    hand-restoring does not, and the shipped default is deliberately unset.
    Applied at class level so every test in the subclass inherits it.
    """

    character_typeclass = "typeclasses.characters.Character"

    # Comfortably more than the 170 Copper full chain, so nothing in the happy
    # paths accidentally tests the dry-coffers branch.
    TREASURY_FUNDING = 5000

    def setUp(self):
        super().setUp()
        self.treasury = create.create_object(
            Treasury, key="temple treasury", location=self.room1, home=self.room1
        )
        # Funded through the real mint path, which is what an admin's
        # `@economy mint` does. Writes a ledger entry -- hence the mixin.
        self.treasury.currency.add(self.TREASURY_FUNDING, source="crypto_exchange")

    def start_and_finish(self, task_key="sweep", caller=None):
        """
        Drive both halves of a chore.

        Returns:
            object: the marker the command minted, so a caller can assert on
                it or reuse it for a stale-callback test.

        The marker is read off the character rather than fabricated: a
        fabricated one would pass even with the identity check removed.
        """
        caller = caller or self.char1
        self.call(CmdWork(), task_key, caller=caller)
        marker = caller.ndb.working
        _finish_task(caller, task_key, marker)
        return marker


@override_settings(TREASURY_DBREF="")
class TestWorkWithoutATemple(WorkTestBase):
    """
    The place gate. No Treasury configured, and the Treasury in another room,
    are ONE answer -- locked in the Component C session.

    `TREASURY_DBREF=""` rather than deleting the object: the object still
    exists in the room, so this asserts the gate is reading the *setting* and
    not merely tripping over an absent object.
    """

    def test_bare_work_reports_no_work_here(self):
        self.call(CmdWork(), "", "There is no work to be had here.", caller=self.char1)

    def test_a_named_chore_reports_no_work_here(self):
        self.call(
            CmdWork(), "sweep", "There is no work to be had here.", caller=self.char1
        )

    def test_nothing_is_started(self):
        self.call(CmdWork(), "sweep", caller=self.char1)
        self.assertIsNone(self.char1.ndb.working)

    def test_no_cooldown_is_consumed(self):
        self.call(CmdWork(), "sweep", caller=self.char1)
        self.assertTrue(self.char1.cooldowns.ready(_cooldown_key("sweep")))


@override_settings(TREASURY_DBREF="")
class TestTreasuryInAnotherRoom(WorkTestBase):
    """
    Same sentence, different cause. The Treasury exists and is configured, but
    the player is not standing with it.

    Uses its own override inside each test because the dbref is only known once
    the fixture has built the object.
    """

    def test_wrong_room_gives_the_same_answer_as_no_temple(self):
        self.treasury.location = self.room2
        with override_settings(TREASURY_DBREF=self.treasury.dbref):
            self.call(
                CmdWork(),
                "sweep",
                "There is no work to be had here.",
                caller=self.char1,
            )

    def test_moving_the_treasury_moves_the_faucet(self):
        # The documented consequence of the no-second-settings-key decision,
        # asserted so nobody "fixes" it by accident: the chore that failed in
        # room1 succeeds there again once the coffer comes back.
        self.treasury.location = self.room2
        with override_settings(TREASURY_DBREF=self.treasury.dbref):
            self.call(CmdWork(), "sweep", caller=self.char1)
            self.assertIsNone(self.char1.ndb.working)

            self.treasury.location = self.room1
            self.call(CmdWork(), "sweep", caller=self.char1)
            self.assertIsNotNone(self.char1.ndb.working)


class TestWorkBoard(WorkTestBase):
    """`work` with no arguments: the notice board."""

    def setUp(self):
        super().setUp()
        self.settings_override = override_settings(TREASURY_DBREF=self.treasury.dbref)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    def test_every_chore_is_listed(self):
        returned = self.call(CmdWork(), "", caller=self.char1)
        for task in TEMPLE_TASKS.values():
            self.assertIn(task["name"], returned)

    def test_rewards_are_shown(self):
        # A deliberate decision, not an accident of layout: a temple that pays
        # for chores and will not say what it pays is a puzzle. See the
        # _show_board docstring.
        returned = self.call(CmdWork(), "", caller=self.char1)
        self.assertIn("25 Copper", returned)
        self.assertIn("50 Copper", returned)

    def test_available_chores_read_as_ready(self):
        returned = self.call(CmdWork(), "", caller=self.char1)
        self.assertIn("ready", returned)

    def test_a_chore_on_cooldown_shows_its_wait(self):
        # Stamped by its specific key. No cooldowns.clear() anywhere in this
        # file -- Testing Reference section 7.
        self.char1.cooldowns.add(_cooldown_key("books"), 7200)
        returned = self.call(CmdWork(), "", caller=self.char1)
        self.assertIn("2 hours", returned)

    def test_the_board_does_not_leak_the_treasury_balance(self):
        returned = self.call(CmdWork(), "", caller=self.char1)
        self.assertNotIn(str(self.TREASURY_FUNDING), returned)

    def test_reading_the_board_moves_no_money(self):
        before = self.treasury.currency.value
        self.call(CmdWork(), "", caller=self.char1)
        self.assertEqual(self.treasury.currency.value, before)
        self.assertEqual(self.char1.currency.value, 0)

    def test_the_board_is_readable_with_a_dry_treasury(self):
        # Dryness is discovered by trying, not by a board that changes under
        # the player's feet.
        self.treasury.currency.burn(self.TREASURY_FUNDING, reason="crypto_exchange")
        returned = self.call(CmdWork(), "", caller=self.char1)
        self.assertIn("sweep the floors", returned)


class TestWorkPayout(WorkTestBase):
    """The happy path, and the conservation property that defines it."""

    def setUp(self):
        super().setUp()
        self.settings_override = override_settings(TREASURY_DBREF=self.treasury.dbref)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    def test_payout_moves_copper_from_the_treasury_to_the_wallet(self):
        # BOTH sides asserted. Checking only the wallet would pass against a
        # minting faucet, which is the failure this component exists to prevent.
        self.start_and_finish("sweep")
        self.assertEqual(self.char1.currency.value, 25)
        self.assertEqual(self.treasury.currency.value, self.TREASURY_FUNDING - 25)

    def test_the_total_is_conserved(self):
        before = self.treasury.currency.value + self.char1.currency.value
        self.start_and_finish("books")
        after = self.treasury.currency.value + self.char1.currency.value
        self.assertEqual(before, after)

    def test_no_money_is_created(self):
        # The invariant the whole stage rests on, read straight from the audit
        # rather than from the handler being tested.
        self.start_and_finish("altar")
        self.assertEqual(economy_log.audit()["delta"], 0)

    def test_the_payout_is_not_ledgered(self):
        # S4-4: transfers are not logged, and a faucet payout is a transfer.
        # Total minted must be unchanged by the chore.
        before = economy_log.total_minted()
        self.start_and_finish("sweep")
        self.assertEqual(economy_log.total_minted(), before)

    def test_nothing_is_paid_before_the_delay_elapses(self):
        # The start half must move no money at all. If it did, the "walk out
        # and earn nothing" rule would be a lie.
        self.call(CmdWork(), "sweep", caller=self.char1)
        self.assertEqual(self.char1.currency.value, 0)
        self.assertEqual(self.treasury.currency.value, self.TREASURY_FUNDING)

    def test_the_start_messages_the_worker(self):
        self.call(
            CmdWork(),
            "sweep",
            TEMPLE_TASKS["sweep"]["begin_actor"],
            caller=self.char1,
        )

    def test_the_payout_names_the_amount_to_the_worker(self):
        self.call(CmdWork(), "sweep", caller=self.char1)
        marker = self.char1.ndb.working
        with captured_messages(self.char1) as seen:
            _finish_task(self.char1, "sweep", marker)
        self.assertIn("25 Copper", "\n".join(seen))

    def test_the_worker_is_told_the_chore_is_done(self):
        self.call(CmdWork(), "sweep", caller=self.char1)
        marker = self.char1.ndb.working
        with captured_messages(self.char1) as seen:
            _finish_task(self.char1, "sweep", marker)
        self.assertIn(TEMPLE_TASKS["sweep"]["done_actor"], "\n".join(seen))

    def test_the_room_sees_the_act_but_not_the_amount(self):
        # Same line `pay` draws. A bystander learns that you worked, not what
        # you are carrying afterwards.
        observer = create.create_object(
            self.character_typeclass, key="Watcher", location=self.room1, home=self.room1
        )
        self.call(CmdWork(), "sweep", caller=self.char1)
        marker = self.char1.ndb.working
        with captured_messages(observer) as seen:
            _finish_task(self.char1, "sweep", marker)
        text = "\n".join(seen)
        self.assertIn(TEMPLE_TASKS["sweep"]["done_room"], text)
        self.assertNotIn("Copper", text)
        self.assertNotIn("25", text)

    def test_the_worker_is_excluded_from_the_room_message(self):
        # They already got a fuller message naming the sum; receiving the vague
        # public one too would read as the chore having happened twice.
        self.call(CmdWork(), "sweep", caller=self.char1)
        marker = self.char1.ndb.working
        with captured_messages(self.char1) as seen:
            _finish_task(self.char1, "sweep", marker)
        self.assertNotIn(TEMPLE_TASKS["sweep"]["done_room"], "\n".join(seen))

    def test_the_cooldown_is_set_only_after_a_successful_payout(self):
        cd_key = _cooldown_key("sweep")
        self.call(CmdWork(), "sweep", caller=self.char1)
        self.assertTrue(self.char1.cooldowns.ready(cd_key))  # not yet
        _finish_task(self.char1, "sweep", self.char1.ndb.working)
        self.assertFalse(self.char1.cooldowns.ready(cd_key))  # now

    def test_the_marker_is_cleared_on_completion(self):
        self.start_and_finish("sweep")
        self.assertIsNone(self.char1.ndb.working)

    def test_the_full_chain_of_five_chores_is_allowed(self):
        # Deliberate: cooldowns are per task, so all five are available in one
        # sitting. The brake is a finite Treasury, not the cooldown.
        for key in TEMPLE_TASKS:
            self.start_and_finish(key)
        self.assertEqual(self.char1.currency.value, 170)
        self.assertEqual(self.treasury.currency.value, self.TREASURY_FUNDING - 170)


class TestWorkRefusals(WorkTestBase):
    """Everything that stops a chore, and what it must not cost the player."""

    def setUp(self):
        super().setUp()
        self.settings_override = override_settings(TREASURY_DBREF=self.treasury.dbref)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    def test_an_unknown_chore_is_refused_by_name(self):
        self.call(CmdWork(), "brew ale", "The temple has no chore like", caller=self.char1)

    def test_an_unknown_chore_starts_nothing(self):
        self.call(CmdWork(), "brew ale", caller=self.char1)
        self.assertIsNone(self.char1.ndb.working)

    def test_a_second_chore_while_busy_is_refused(self):
        # The queue guard. Without it, five `work sweep` schedule five payouts
        # and the cooldown gate never sees any of them, because none has fired.
        self.call(CmdWork(), "sweep", caller=self.char1)
        first_marker = self.char1.ndb.working
        self.call(CmdWork(), "water", "You are already busy", caller=self.char1)
        self.assertIs(self.char1.ndb.working, first_marker)

    def test_a_chore_on_cooldown_is_refused_with_the_wait(self):
        self.char1.cooldowns.add(_cooldown_key("sweep"), 3600)
        self.call(CmdWork(), "sweep", "You have done that recently", caller=self.char1)

    def test_a_chore_on_cooldown_starts_nothing(self):
        self.char1.cooldowns.add(_cooldown_key("sweep"), 3600)
        self.call(CmdWork(), "sweep", caller=self.char1)
        self.assertIsNone(self.char1.ndb.working)

    def test_an_ambiguous_prefix_lists_the_candidates(self):
        # No two current keys share a prefix, so this exercises the branch
        # against a synthetic table rather than pretending the real one is
        # ambiguous. Guards the branch for whoever adds a sixth chore.
        original = dict(TEMPLE_TASKS)
        try:
            TEMPLE_TASKS["sweeping"] = dict(original["sweep"])
            key, candidates = _resolve_task("swee")
            self.assertIsNone(key)
            self.assertEqual(sorted(candidates), ["sweep", "sweeping"])
        finally:
            TEMPLE_TASKS.clear()
            TEMPLE_TASKS.update(original)


class TestDryTreasury(WorkTestBase):
    """
    All-or-nothing, and the rule that a failed attempt is free.

    The load-bearing assertion in this class is the cooldown one, not the
    balance one: a dry payout that consumed the cooldown would take something
    from the player in exchange for nothing.
    """

    TREASURY_FUNDING = 10  # less than any chore pays

    def setUp(self):
        super().setUp()
        self.settings_override = override_settings(TREASURY_DBREF=self.treasury.dbref)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    def test_nothing_is_paid(self):
        self.start_and_finish("sweep")
        self.assertEqual(self.char1.currency.value, 0)

    def test_the_treasury_is_untouched(self):
        # No partial payment. transfer_to() returns False having moved nothing.
        self.start_and_finish("sweep")
        self.assertEqual(self.treasury.currency.value, self.TREASURY_FUNDING)

    def test_the_cooldown_is_left_unset(self):
        self.start_and_finish("sweep")
        self.assertTrue(self.char1.cooldowns.ready(_cooldown_key("sweep")))

    def test_the_player_can_immediately_try_again(self):
        self.start_and_finish("sweep")
        self.call(CmdWork(), "sweep", caller=self.char1)
        self.assertIsNotNone(self.char1.ndb.working)

    def test_the_failure_is_diegetic(self):
        # "the alms box is bare", not "TREASURY_DBREF has insufficient funds".
        # The player is not the admin.
        self.call(CmdWork(), "sweep", caller=self.char1)
        marker = self.char1.ndb.working
        with captured_messages(self.char1) as seen:
            _finish_task(self.char1, "sweep", marker)
        text = "\n".join(seen)
        self.assertIn("alms box is bare", text)
        self.assertNotIn("TREASURY_DBREF", text)

    def test_the_marker_is_still_cleared(self):
        # A dry temple must not leave the player permanently "busy".
        self.start_and_finish("sweep")
        self.assertIsNone(self.char1.ndb.working)


class TestStaleAndInterruptedCallbacks(WorkTestBase):
    """
    The identity marker, and the four ways a chore ends without paying.

    Every one of these must leave the cooldown unset.
    """

    def setUp(self):
        super().setUp()
        self.settings_override = override_settings(TREASURY_DBREF=self.treasury.dbref)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    def test_a_stale_marker_pays_nothing(self):
        # THE collision this mechanism exists for: start, abandon, start again
        # with the SAME key. A task key alone would not tell the two apart.
        self.call(CmdWork(), "sweep", caller=self.char1)
        stale = self.char1.ndb.working
        self.char1.ndb.working = None

        self.call(CmdWork(), "sweep", caller=self.char1)
        fresh = self.char1.ndb.working
        self.assertIsNot(stale, fresh)

        _finish_task(self.char1, "sweep", stale)
        self.assertEqual(self.char1.currency.value, 0)
        self.assertTrue(self.char1.cooldowns.ready(_cooldown_key("sweep")))
        # And the live attempt is untouched by the stale one firing.
        self.assertIs(self.char1.ndb.working, fresh)

    def test_the_fresh_attempt_still_pays_after_a_stale_one_fires(self):
        self.call(CmdWork(), "sweep", caller=self.char1)
        stale = self.char1.ndb.working
        self.char1.ndb.working = None
        self.call(CmdWork(), "sweep", caller=self.char1)
        fresh = self.char1.ndb.working

        _finish_task(self.char1, "sweep", stale)
        _finish_task(self.char1, "sweep", fresh)
        self.assertEqual(self.char1.currency.value, 25)

    def test_walking_out_cancels_the_chore(self):
        # at_pre_move clears the marker and says so at the moment of the move.
        self.call(CmdWork(), "sweep", caller=self.char1)
        marker = self.char1.ndb.working
        self.char1.move_to(self.room2, quiet=True)
        self.assertIsNone(self.char1.ndb.working)

        _finish_task(self.char1, "sweep", marker)
        self.assertEqual(self.char1.currency.value, 0)
        self.assertTrue(self.char1.cooldowns.ready(_cooldown_key("sweep")))

    def test_the_location_recheck_is_the_backstop(self):
        # Teleport and death bypass at_pre_move's message but not this. The
        # marker is deliberately left intact so only the re-check can refuse.
        self.call(CmdWork(), "sweep", caller=self.char1)
        marker = self.char1.ndb.working
        self.char1.location = self.room2  # direct assignment, no move hooks

        _finish_task(self.char1, "sweep", marker)
        self.assertEqual(self.char1.currency.value, 0)
        self.assertEqual(self.treasury.currency.value, self.TREASURY_FUNDING)
        self.assertTrue(self.char1.cooldowns.ready(_cooldown_key("sweep")))

    def test_the_treasury_being_moved_mid_chore_cancels_the_payout(self):
        self.call(CmdWork(), "sweep", caller=self.char1)
        marker = self.char1.ndb.working
        self.treasury.location = self.room2

        _finish_task(self.char1, "sweep", marker)
        self.assertEqual(self.char1.currency.value, 0)
        self.assertTrue(self.char1.cooldowns.ready(_cooldown_key("sweep")))

    def test_a_logged_out_worker_is_not_paid(self):
        # Statue-logout leaves the body standing in the room, so without the
        # has_account guard the temple would pay coin into an unattended purse.
        # char2 has an account but no session in the stock fixture, which is
        # exactly the state being tested.
        self.assertFalse(self.char2.has_account)
        self.call(CmdWork(), "sweep", caller=self.char2)
        marker = self.char2.ndb.working

        _finish_task(self.char2, "sweep", marker)
        self.assertEqual(self.char2.currency.value, 0)
        self.assertTrue(self.char2.cooldowns.ready(_cooldown_key("sweep")))

    def test_an_unknown_task_key_at_payout_pays_nothing(self):
        # Only reachable if the table changed under a live delay. Asserted so
        # the branch is a refusal rather than a KeyError.
        self.call(CmdWork(), "sweep", caller=self.char1)
        marker = self.char1.ndb.working
        _finish_task(self.char1, "no_such_chore", marker)
        self.assertEqual(self.char1.currency.value, 0)


class TestCommandSurface(WorkTestBase):
    """Key, lock and registration -- the things a cmdset change could break."""

    def test_the_key_is_work(self):
        self.assertEqual(CmdWork.key, "work")

    def test_no_aliases_are_claimed(self):
        # Deliberate. `job`, `chores` and `labour` have no consumer, and
        # claiming keys speculatively costs collision surface for nothing
        # (decomposition section 5).
        self.assertFalse(getattr(CmdWork, "aliases", []))

    def test_the_lock_is_open_to_everyone(self):
        # Asserted on the string, not by driving an unprivileged caller through
        # .call() -- .call() does not run command locks at all (Evennia
        # Reference section 11.26), so such a test would pass vacuously.
        self.assertEqual(CmdWork.locks, "cmd:all()")

    def test_it_is_registered_in_the_character_cmdset(self):
        from commands.default_cmdsets import CharacterCmdSet

        cmdset = CharacterCmdSet()
        cmdset.at_cmdset_creation()
        self.assertIn("work", [cmd.key for cmd in cmdset.commands])
