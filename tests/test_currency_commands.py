"""
Unit tests for the player-facing currency commands. Stage 4, Component B.

Written to the pattern in `tests/test_knowledge.py`, the golden reference for
this project (AGENTS.md section 0A), and to the ledger-isolation pattern
established in `tests/test_currency.py`. If something here looks unusual, check
those two first -- the shape is deliberate.

WHAT IT COVERS
--------------
* commands.currency_commands.CmdWallet -- B.1, read-only balance display
* commands.currency_commands.CmdPay    -- B.2, player-to-player payment

BASE CLASS
----------
`EvenniaCommandTest` throughout: both commands are driven through `.call()`,
which needs the .char1/.char2/.room1 fixture graph *and* the command runner. The
denomination layer underneath is already covered by `tests/test_currency.py`
with the lighter `EvenniaTestCase`; none of it is re-tested here. What IS tested
here is the surface -- the wording, the guard ordering, and the side-effects on
both wallets.

⚠️ LEDGER ISOLATION -- INHERIT THE MIXIN OR THE SUITE GOES ORDER-DEPENDENT
--------------------------------------------------------------------------
`LedgerIsolationMixin` is imported from `tests.test_currency` rather than
rewritten. The ledger is a *global* Script and is NOT rebuilt per test the way
.char1/.room1 are, so its entries and running totals leak from one test into the
next. Every test class in this project that touches money must inherit it. The
funding helpers below call `add()`, which writes a ledger entry, so this applies
to every class in this file.

⚠️ FOUR FIXTURE FACTS, ALL VERIFIED FIRSTHAND IN
`evennia/utils/test_resources.py` (Evennia 6.1.0)
--------------------------------------------------
1. `self.char1.key` is **"Char"**, not "Char1" -- only char2 carries a number.
   Any test that types char1's own name (self-payment) must use "Char".
2. `setup_session()` logs in **only `self.account`** (sessid 1). `char2` has an
   account but no session, and `has_account` is `self.sessions.count()`, so
   char2 reads as a logged-out body. `CmdPay` refuses it -- correctly, and that
   is its own test below. Every *happy-path* payment test therefore needs
   `SecondSessionMixin`.
3. `.call(msg=...)` compares with `.startswith()` on the ansi-stripped output,
   so an expected string that is a substring but not a prefix fails. Passing a
   dict asserts per receiver, which is how the two-party messages are checked.
4. The separator for several `.msg()` calls to the SAME receiver is `"|"`, not
   `"||"` -- `msg_sep = "|" if noansi else "||"`, and `noansi` defaults True.
   No separator appears in this file: every command path here sends at most one
   message per receiver.

HOW TO RUN
----------
The --settings flag is not optional anywhere in this project.

    evennia test --settings settings.py tests.test_currency_commands
    evennia test --settings settings.py tests    # the whole package
"""

import evennia
from evennia.server.serversession import ServerSession
from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest

from commands.currency_commands import CmdPay, CmdWallet
from tests.test_currency import LedgerIsolationMixin
from world import economy_log
from world.currency import COPPER_PER_GOLD, COPPER_PER_SILVER


class SecondSessionMixin:
    """
    Connect a real session for `self.account2`, so `self.char2.has_account` is
    true and char2 can be paid.

    WHY NOT MOCK `has_account`: it is a property computed from
    `self.sessions.count()`, and mocking it would test our patch rather than the
    guard. `CmdPay` refuses logged-out bodies deliberately (statue-logout leaves
    them standing in the room), so the difference between "connected" and "body"
    is exactly the behaviour under test. A real session keeps the two cases
    honestly distinct.

    Mirrors `EvenniaTestMixin.setup_session()` with sessid 2 instead of 1, plus
    the one step that fixture leaves undone for account2.

    ⚠️ THE PERMISSION IS THE WHOLE TRICK. `Object.sessions` counts sessions
    puppeting *that object*, and login auto-puppets `_last_puppet` -- which the
    fixture does set for account2. But char2's puppet lock is
    `puppet:pperm(Developer)` and `create_accounts()` grants Developer to
    `self.account` ONLY. So the auto-puppet fails the lock and returns
    **silently**: no exception, no message you will see, just a char2 that is
    still a body. The first run of this suite failed with "stone statue of
    Char2 is in no state to take coin" -- our own statue-logout display telling
    the exact truth about a session that never attached.

    Hence the explicit `permissions.add("Developer")`, and hence the assertion
    at the end of setUp: a mixin whose entire job is establishing a
    precondition should fail loudly if it ever stops establishing it, rather
    than quietly turning every happy-path test into a refusal test.

    The teardown is not optional either: `SESSION_HANDLER` is global like the
    ledger, and a leaked session would make later tests see a char2 that is
    sometimes connected depending on execution order -- the same bug class the
    ledger mixin exists to prevent.
    """

    _SESSID = 2

    def setUp(self):
        super().setUp()
        # Mirrors what create_accounts() does for account1, and for the same
        # reason: without it the puppet lock refuses and login quietly does
        # nothing.
        self.account2.permissions.add("Developer")

        dummysession = ServerSession()
        dummysession.init_session("telnet", ("localhost", "testmode"), evennia.SESSION_HANDLER)
        dummysession.sessid = self._SESSID
        evennia.SESSION_HANDLER.portal_connect(dummysession.get_sync_data())
        session2 = evennia.SESSION_HANDLER.session_from_sessid(self._SESSID)
        evennia.SESSION_HANDLER.login(session2, self.account2, testmode=True)
        self.session2 = session2

        # Belt and braces: puppet explicitly if the auto-puppet did not fire,
        # so the mixin does not silently depend on AUTO_PUPPET_ON_LOGIN.
        if not self.char2.sessions.count():
            self.account2.puppet_object(session2, self.char2)

        self.assertTrue(
            self.char2.has_account,
            "SecondSessionMixin failed to connect char2 -- every payment test "
            "in this class would silently become a logged-out-body test.",
        )

    def _disconnect_second_session(self):
        """Turn char2 back into a logged-out body. Used by teardown and by the
        logged-out-body test, which needs exactly this transition."""
        if getattr(self, "session2", None) is None:
            return
        self.account2.unpuppet_object(self.session2)
        del evennia.SESSION_HANDLER[self.session2.sessid]
        self.session2 = None

    def tearDown(self):
        self._disconnect_second_session()
        super().tearDown()


class TestWalletCommand(LedgerIsolationMixin, EvenniaCommandTest):
    """
    B.1. A read-only display, so every test here asserts the message -- but the
    last one asserts a side-effect too, because "read-only" is a claim about
    state and not only about output.
    """

    character_typeclass = "typeclasses.characters.Character"

    def _fund(self, copper):
        """Mint into char1's purse. Mint, not transfer: there is nowhere else
        for the money to come from in a fixture, and `admin_correction` is a
        legitimate whitelisted source (MINT_SOURCES)."""
        self.char1.currency.add(copper, source="admin_correction")

    def test_empty_purse_gets_its_own_sentence(self):
        # NOT "nothing", which is what format_copper(0) returns. An empty purse
        # is a state, and B.1 asks for it to read as one.
        self.call(CmdWallet(), "", "Purse:", caller=self.char1)
        returned = self.call(CmdWallet(), "", caller=self.char1)
        self.assertIn("Your purse is empty.", returned)
        self.assertNotIn("nothing", returned)

    def test_sub_silver_amount_renders_in_copper(self):
        self._fund(37)
        returned = self.call(CmdWallet(), "", caller=self.char1)
        self.assertIn("37 Copper", returned)

    def test_mixed_amount_renders_largest_first(self):
        # 1 Gold, 2 Silver, 3 Copper. Pins the D3 grammar as the player sees it,
        # not merely as format_copper returns it.
        self._fund(COPPER_PER_GOLD + 2 * COPPER_PER_SILVER + 3)
        returned = self.call(CmdWallet(), "", caller=self.char1)
        self.assertIn("1 Gold, 2 Silver, 3 Copper", returned)

    def test_zero_denominations_are_omitted(self):
        # 1 Gold and 5 Copper -- no Silver at all, so no "0 Silver" may appear.
        self._fund(COPPER_PER_GOLD + 5)
        returned = self.call(CmdWallet(), "", caller=self.char1)
        self.assertIn("1 Gold, 5 Copper", returned)
        self.assertNotIn("Silver", returned)

    def test_reading_the_balance_never_writes(self):
        # D6/§11.23: the wallet Attribute must not exist until a mutation. If
        # `wallet` created it just by looking, every character in the database
        # would sprout a row the first time they checked their empty purse.
        self.assertIsNone(self.char1.attributes.get("wallet"))
        self.call(CmdWallet(), "", caller=self.char1)
        self.assertIsNone(self.char1.attributes.get("wallet"))

    def test_purse_alias_is_declared(self):
        # Cheap, but it is the alias half of the key claim in decomp section 5,
        # and an alias silently dropped in an edit is invisible otherwise.
        self.assertIn("purse", CmdWallet.aliases)


class TestPayCommandSuccess(SecondSessionMixin, LedgerIsolationMixin, EvenniaCommandTest):
    """
    B.2, the paths where coin actually moves. Every test asserts the
    side-effect on BOTH wallets, not just the message -- a cheerful message
    over the wrong world-state is the failure mode that matters (AGENTS §0A).
    """

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.char1.currency.add(1_000, source="admin_correction")

    def test_payment_moves_coin_and_tells_both_parties(self):
        self.call(
            CmdPay(), "5 silver to Char2",
            {
                self.char1: "You pay Char2 5 Silver.",
                self.char2: "Char pays you 5 Silver.",
            },
            caller=self.char1,
        )
        self.assertEqual(self.char1.currency.value, 500)
        self.assertEqual(self.char2.currency.value, 500)

    def test_payment_conserves_the_total(self):
        # The property that makes `pay` safe to expose at all: the command layer
        # cannot create or destroy money, because it only ever calls transfer_to.
        before = self.char1.currency.value + self.char2.currency.value
        self.call(CmdPay(), "3 silver to Char2", caller=self.char1)
        after = self.char1.currency.value + self.char2.currency.value
        self.assertEqual(before, after)

    def test_paying_everything_is_allowed(self):
        # Boundary: transfer_to checks >= not >, so spending the lot must work.
        self.call(CmdPay(), "10 silver to Char2", caller=self.char1)
        self.assertEqual(self.char1.currency.value, 0)
        self.assertEqual(self.char2.currency.value, 1_000)

    def test_abbreviated_denomination_is_accepted(self):
        # "1 g" is the abbreviation branch of parse_amount reached through the
        # command, which is where players will actually meet it.
        self.char1.currency.add(COPPER_PER_GOLD, source="admin_correction")
        self.call(CmdPay(), "1 g to Char2", caller=self.char1)
        self.assertEqual(self.char2.currency.value, COPPER_PER_GOLD)

    def test_payment_is_not_ledgered(self):
        # S4-4: transfers are the normal business of the game and are not
        # logged. If this ever fails, either the command grew a mint path or
        # the ledger grew a transfer path -- both are stage-level regressions.
        before = len(economy_log.entries())
        self.call(CmdPay(), "1 silver to Char2", caller=self.char1)
        self.assertEqual(len(economy_log.entries()), before)

    def test_the_room_sees_the_act_but_not_the_amount(self):
        # The locked message surface. A bystander must be able to witness that
        # a payment happened -- with no transfer log, the room is the only
        # evidence layer -- without learning the figure.
        observer = create.create_object(
            self.character_typeclass, key="Watcher", location=self.room1, home=self.room1
        )
        seen = self.call(
            CmdPay(), "5 silver to Char2", caller=self.char1, receiver=observer
        )
        self.assertIn("Char hands Char2 some coin.", seen)
        self.assertNotIn("Silver", seen)
        self.assertNotIn("5", seen)

    def test_the_two_parties_are_excluded_from_the_room_message(self):
        # They already got a direct, fuller message; receiving the vague public
        # one as well would read as the payment having happened twice.
        returned = self.call(CmdPay(), "5 silver to Char2", caller=self.char1)
        self.assertNotIn("some coin", returned)


class TestPayCommandRefusals(SecondSessionMixin, LedgerIsolationMixin, EvenniaCommandTest):
    """
    B.2, every path where coin must NOT move.

    The guards under test are the ones standing in front of `CurrencyHandler`'s
    raising conditions (D7). Each of these would be a traceback in the player's
    face if its guard were removed, so each asserts that the wallets are
    untouched as well as what was said.
    """

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.char1.currency.add(500, source="admin_correction")

    def _assert_nothing_moved(self):
        self.assertEqual(self.char1.currency.value, 500)
        self.assertEqual(self.char2.currency.value, 0)

    def test_insufficient_funds_moves_nothing_and_names_the_balance(self):
        # False from transfer_to means poverty and nothing else (D7). Both
        # wallets are asserted because a partial mutation here would be the
        # duplication bug for the whole economy.
        self.call(
            CmdPay(), "10 silver to Char2",
            "You don't have that much on you; your purse holds 5 Silver.",
            caller=self.char1,
        )
        self._assert_nothing_moved()

    def test_bare_number_is_refused(self):
        # D1, met by the player. This is the mistake the whole rule exists for:
        # meaning Silver, typing "50", and moving a hundredth of it.
        self.call(
            CmdPay(), "50 to Char2",
            "'50' isn't an amount of coin I can read.",
            caller=self.char1,
        )
        self._assert_nothing_moved()

    def test_compact_form_is_still_refused(self):
        # "50c" belongs to the compact-input feature deferred to BACKLOG. Pinned
        # so that implementing it is a visible decision rather than a silent one.
        self.call(
            CmdPay(), "50c to Char2",
            "'50c' isn't an amount of coin I can read.",
            caller=self.char1,
        )
        self._assert_nothing_moved()

    def test_zero_parses_but_is_not_payable(self):
        # parse_amount returns 0 (a fine parse), so this is the command's own
        # guard, not the parser's. Without it transfer_to raises ValueError.
        self.call(
            CmdPay(), "0 copper to Char2",
            "Paying nothing is not a payment.",
            caller=self.char1,
        )
        self._assert_nothing_moved()

    def test_negative_amount_is_refused_as_unparseable(self):
        # parse_amount's digit check rejects the leading minus, so a negative
        # never reaches the <= 0 guard -- it is a parse failure. Asserted so a
        # future compact-input parser cannot start accepting negatives unnoticed.
        self.call(
            CmdPay(), "-5 silver to Char2",
            "'-5 silver' isn't an amount of coin I can read.",
            caller=self.char1,
        )
        self._assert_nothing_moved()

    def test_self_payment_is_caught_before_the_handler_raises(self):
        # char1's key is "Char" (fixture fact 1). transfer_to raises ValueError
        # on self-payment; this guard is what keeps that off the player's screen.
        self.call(
            CmdPay(), "5 copper to Char",
            "You move coin from one hand to the other.",
            caller=self.char1,
        )
        self.assertEqual(self.char1.currency.value, 500)

    def test_non_character_target_is_refused(self):
        # self.obj1 has no currency handler -- transfer_to would raise TypeError.
        # The room itself is also a search candidate and lands on this same
        # guard, which is why it is load-bearing rather than decorative.
        self.call(
            CmdPay(), "5 copper to Obj",
            "Obj has no use for coin.",
            caller=self.char1,
        )
        self._assert_nothing_moved()

    def test_logged_out_body_is_refused(self):
        # Deliberately drops the second session first, turning char2 back into
        # the statue-logout body the stock fixture gives you. Paying it would
        # hand over coin with no witness and no chance to refuse.
        # NOTE the expected wording: get_display_name renders an unpuppeted
        # character as "stone statue of Char2" (our statue-logout), so the
        # refusal composes into "stone statue of Char2 is in no state to take
        # coin." That is the message a player actually sees, and it reads
        # correctly -- which is why the guard uses get_display_name rather than
        # .key. Asserted verbatim so a change to either half is visible here.
        self._disconnect_second_session()
        self.call(
            CmdPay(), "5 copper to Char2",
            "stone statue of Char2 is in no state to take coin.",
            caller=self.char1,
        )
        self._assert_nothing_moved()

    def test_target_in_another_room_is_not_found(self):
        # The same-room rule, which is a design pillar and not a convenience:
        # coin is carried, and carrying it is a risk that a remote `pay` would
        # cancel. room2 is part of the stock fixture.
        self.char2.location = self.room2
        self.call(CmdPay(), "5 copper to Char2", caller=self.char1)
        self._assert_nothing_moved()

    def test_absent_target_moves_nothing(self):
        self.call(CmdPay(), "5 copper to Nobody", caller=self.char1)
        self._assert_nothing_moved()

    def test_missing_separator_gets_the_usage_line(self):
        self.call(CmdPay(), "5 copper Char2", "Pay what, to whom?", caller=self.char1)
        self._assert_nothing_moved()

    def test_no_arguments_gets_the_usage_line(self):
        self.call(CmdPay(), "", "Pay what, to whom?", caller=self.char1)
        self._assert_nothing_moved()

    def test_empty_target_half_gets_the_usage_line(self):
        # "5 copper to " -- the separator is present but the name is not.
        self.call(CmdPay(), "5 copper to ", "Pay what, to whom?", caller=self.char1)
        self._assert_nothing_moved()
