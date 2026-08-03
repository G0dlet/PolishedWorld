"""
Unit tests for `typeclasses/treasury.py` (Stage 4, Component C.1).

WHAT IS ACTUALLY WORTH TESTING HERE
-----------------------------------
The Treasury typeclass is small, so the temptation is to test that it exists.
That would be worthless. The load-bearing behaviours are the ones that protect
money:

1. **The get-lock.** The wallet travels with the object, so `get treasury`
   walking off with the coffer would walk off with the entire money supply.
2. **`resolve_treasury()` distinguishes three failure modes.** They need
   different fixes, and `get_treasury()`'s single `None` cannot express that.
3. **A dbref pointing at the wrong typeclass is REFUSED, not accepted.** This is
   the test that matters most in the file. A mistyped dbref that lands on a
   Character would otherwise make `@economy mint` create money in a player's
   purse -- a second mint destination, which is exactly what S4-1 forbids.
4. **The Treasury is picked up by the audit automatically** (D9), because the
   audit enumerates by wallet Attribute rather than by typeclass. Nothing
   registers the Treasury anywhere, so this is worth an actual assertion rather
   than a comment.

SETTINGS OVERRIDE PATTERN
-------------------------
`TREASURY_DBREF` is deliberately absent from `server/conf/settings.py`, so the
default state under test is "unset". Tests that need it set use Django's
`override_settings`, which restores the previous state even if the test fails --
hand-setting and hand-restoring a settings attribute leaks into every later test
in the run when an assertion raises partway through. Same class of bleed as the
global ledger (see `LedgerIsolationMixin`), different mechanism.
"""

from django.test import override_settings

from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

from typeclasses.treasury import (
    PROBLEM_NOT_FOUND,
    PROBLEM_UNSET,
    PROBLEM_WRONG_TYPE,
    Treasury,
    get_configured_dbref,
    get_treasury,
    resolve_treasury,
)
from world import economy_log

from tests.test_currency import LedgerIsolationMixin


class TreasuryTestBase(LedgerIsolationMixin, EvenniaTest):
    """
    Shared fixture: one Treasury object, not yet configured in settings.

    LedgerIsolationMixin is inherited because these tests mint, and the ledger
    is a global Script that is NOT rebuilt per test -- totals leak between tests
    and turn `total_minted()` assertions into order-dependent coin flips.
    """

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.treasury = create.create_object(
            Treasury, key="temple treasury", location=self.room1, home=self.room1
        )


class TestTreasuryObject(TreasuryTestBase):
    """The object itself: locks, wallet, and refusal to be puppeted."""

    def test_cannot_be_picked_up(self):
        # The wallet is an Attribute ON this object, so pocketing the coffer
        # pockets the balance. Asserting the lock check rather than the lock
        # string: a typo'd lockstring ("get:False()") would still be *present*
        # and still let the object be taken.
        self.assertFalse(self.treasury.access(self.char1, "get"))

    def test_has_a_wallet_handler_reading_zero(self):
        self.assertEqual(self.treasury.currency.value, 0)

    def test_wallet_attribute_does_not_exist_until_first_mint(self):
        # D6 / Evennia Reference §11.23. A brand-new Treasury holds nothing
        # WITHOUT an Attribute row existing, which is what makes re-running
        # creation hooks harmless -- there is no starting value to clobber.
        self.assertIsNone(self.treasury.attributes.get("wallet"))
        self.treasury.currency.add(500, source="crypto_exchange")
        self.assertEqual(self.treasury.attributes.get("wallet"), 500)

    def test_refuses_puppeting(self):
        self.assertFalse(self.treasury.at_pre_puppet(self.account))


class TestResolveTreasury(TreasuryTestBase):
    """
    The lookup, and the three ways it can fail.

    Each failure needs a different fix, so each gets its own problem code. A
    single boolean "no Treasury" would leave an admin guessing which of the
    three situations they are in.
    """

    def test_unset_is_a_supported_state(self):
        # No override: this is the shipped default. Not an error -- a fresh
        # database genuinely has no Treasury.
        treasury, problem = resolve_treasury()
        self.assertIsNone(treasury)
        self.assertEqual(problem, PROBLEM_UNSET)
        self.assertIsNone(get_configured_dbref())

    def test_resolves_a_configured_dbref(self):
        with override_settings(TREASURY_DBREF=self.treasury.dbref):
            treasury, problem = resolve_treasury()
            self.assertIsNone(problem)
            self.assertEqual(treasury, self.treasury)

    def test_dangling_dbref_reports_not_found(self):
        # A dbref far beyond anything the test database created. Distinct from
        # "unset": the admin DID configure something, and the fix is to correct
        # the number rather than to create a Treasury.
        with override_settings(TREASURY_DBREF="#999999"):
            treasury, problem = resolve_treasury()
            self.assertIsNone(treasury)
            self.assertEqual(problem, PROBLEM_NOT_FOUND)

    def test_dbref_pointing_at_a_character_is_refused(self):
        # THE test of this file. If this ever passes the object through,
        # `@economy mint` mints straight into a player's purse and S4-1's
        # single-mint-destination guarantee is silently gone. char1 resolves
        # fine and has a `currency` handler, so nothing downstream would notice.
        with override_settings(TREASURY_DBREF=self.char1.dbref):
            treasury, problem = resolve_treasury()
            self.assertIsNone(treasury)
            self.assertEqual(problem, PROBLEM_WRONG_TYPE)

    def test_malformed_setting_value_does_not_raise(self):
        # A configuration error must not surface as a traceback in an admin
        # command. Anything unusable resolves to a problem code.
        with override_settings(TREASURY_DBREF=["not", "a", "dbref"]):
            treasury, problem = resolve_treasury()
            self.assertIsNone(treasury)
            self.assertIn(problem, (PROBLEM_NOT_FOUND, PROBLEM_WRONG_TYPE))

    def test_get_treasury_collapses_every_problem_to_none(self):
        # The narrow contract `economy_log._read_treasury` depends on.
        self.assertIsNone(get_treasury())
        with override_settings(TREASURY_DBREF="#999999"):
            self.assertIsNone(get_treasury())
        with override_settings(TREASURY_DBREF=self.treasury.dbref):
            self.assertEqual(get_treasury(), self.treasury)


class TestTreasuryAndTheAudit(TreasuryTestBase):
    """
    D9: the audit enumerates by wallet Attribute, not by typeclass, so the
    Treasury is included with no registration step anywhere.
    """

    def test_treasury_balance_is_counted_even_when_unconfigured(self):
        # Unconfigured means "not separately reportable", NOT "excluded from the
        # invariant". If the balance fell out of the sum, an unconfigured
        # Treasury would make the audit report money as missing.
        self.treasury.currency.add(10_000, source="crypto_exchange")
        result = economy_log.audit()
        self.assertIsNone(result["treasury"])
        self.assertEqual(result["wallet_sum"], 10_000)
        self.assertEqual(result["held"], 10_000)
        self.assertEqual(result["delta"], 0)
        self.assertTrue(result["ok"])

    def test_configured_treasury_is_reported_on_its_own_line(self):
        self.treasury.currency.add(10_000, source="crypto_exchange")
        self.char1.currency.add(500, source="crypto_exchange")
        with override_settings(TREASURY_DBREF=self.treasury.dbref):
            result = economy_log.audit()
            # Split out of wallet_sum, not double-counted into it.
            self.assertEqual(result["treasury"], 10_000)
            self.assertEqual(result["wallet_sum"], 500)
            self.assertEqual(result["held"], 10_500)
            self.assertTrue(result["ok"])

    def test_configured_but_never_minted_treasury_reports_zero_not_none(self):
        # It has no wallet Attribute, so the enumeration never sees it -- but it
        # exists and holds nothing, and None would wrongly read as "no Treasury".
        with override_settings(TREASURY_DBREF=self.treasury.dbref):
            self.assertEqual(economy_log.audit()["treasury"], 0)

    def test_faucet_direction_conserves_and_keeps_the_audit_green(self):
        # A rehearsal of the whole S4-1 pattern in three lines: mint ONCE into
        # the Treasury, then move money out by transfer. The invariant holding
        # afterwards is what proves the faucet (D.1) will not need to mint.
        self.treasury.currency.add(10_000, source="crypto_exchange")
        self.assertTrue(self.treasury.currency.transfer_to(self.char1, 250))
        self.assertEqual(self.treasury.currency.value, 9_750)
        self.assertEqual(self.char1.currency.value, 250)
        self.assertEqual(economy_log.total_minted(), 10_000)
        self.assertTrue(economy_log.audit()["ok"])
