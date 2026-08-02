"""
Unit tests for `commands/currency_commands.py::CmdEconomy` (Stage 4, C.2).

⚠️ THE TRAP THIS FILE EXISTS INSIDE
-----------------------------------
`@economy mint` is the only production caller of the mint primitive, so a false
pass here is a false pass on the integrity of the entire money supply. Two
specific ways that could happen, both guarded against below:

1. **The ledger is a global Script and is NOT rebuilt per test.** Entries and
   running totals leak between tests, so `total_minted()` assertions become
   order-dependent. Every class here inherits `LedgerIsolationMixin`. Mint tests
   sit exactly in the middle of this trap.

2. **`.call()` does not run command locks.** Verified in
   `evennia/utils/test_resources.py`: `call()` goes straight to
   `cmdobj.at_pre_cmd()` and then `cmdobj.func()`, with no `access()` check
   anywhere in between. A "a non-Developer is refused" test written with
   `.call()` would therefore pass *vacuously* -- the command would simply run,
   and the test would assert against whatever output it produced. The permission
   test below calls `Command.access(caller, "cmd")` directly instead, which is
   what the real cmdhandler uses.

ASSERTION STYLE
---------------
`msg` is omitted from `.call()` throughout and the returned string is inspected
with `assertIn`. `.call(msg=...)` does a *prefix* match on the ansi-stripped
output (AGENTS §0A), and every branch of this command emits a multi-line block
whose interesting content is in the middle. AGENTS explicitly sanctions omitting
`msg` and inspecting the return value; a prefix match on a banner would assert
almost nothing.

Side-effects are asserted alongside every message. For a command that creates
money, "it printed the right thing" is the least interesting half of the claim --
the tests that matter are the ones asserting that the dry run created **nothing**
and that a refusal minted **nothing**.
"""

from django.test import override_settings

from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest

from commands.currency_commands import CmdEconomy
from typeclasses.treasury import TREASURY_DBREF_SETTING, Treasury
from world import economy_log

from tests.test_currency import LedgerIsolationMixin


class EconomyCommandTestBase(LedgerIsolationMixin, EvenniaCommandTest):
    """
    One Treasury, plus a Developer-permitted caller.

    The permission grant is needed because `.call()` bypasses locks but the
    *command body* does not care about permissions at all -- so granting it here
    is about honesty rather than mechanics: these tests exercise the command as
    the only role that is ever allowed to run it. `TestEconomyPermissions` is
    where the lock itself is checked.
    """

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.char1.permissions.add("Developer")
        self.treasury = create.create_object(
            Treasury, key="temple treasury", location=self.room1, home=self.room1
        )


class ConfiguredTreasuryMixin:
    """
    Run the class's tests with `TREASURY_DBREF` pointing at `self.treasury`.

    `override_settings` is applied per test via `enable()`/`disable()` in
    setUp/tearDown rather than as a decorator, because the dbref is not known
    until the fixture object exists. tearDown disables it unconditionally so a
    failing assertion cannot leak the setting into the rest of the run.
    """

    def setUp(self):
        super().setUp()
        self._settings_override = override_settings(
            **{TREASURY_DBREF_SETTING: self.treasury.dbref}
        )
        self._settings_override.enable()

    def tearDown(self):
        self._settings_override.disable()
        super().tearDown()


class TestEconomyPermissions(EconomyCommandTestBase):
    """
    The lock, checked the way the cmdhandler checks it.

    NOT via `.call()` -- see the module docstring. This is the difference between
    a test that verifies the lock and a test that merely fails to notice it.
    """

    def test_plain_character_is_refused(self):
        self.char2.permissions.remove("Developer")
        self.assertFalse(CmdEconomy().access(self.char2, "cmd"))

    def test_developer_is_allowed(self):
        self.assertTrue(CmdEconomy().access(self.char1, "cmd"))

    def test_builder_is_not_enough(self):
        # Deliberate: CmdWeather is perm(Builder) and that is right for weather.
        # Builders build rooms; they do not create money. If this ever starts
        # passing, the lock has been loosened and the mint surface has widened.
        self.char2.permissions.remove("Developer")
        self.char2.permissions.add("Builder")
        self.assertFalse(CmdEconomy().access(self.char2, "cmd"))


class TestEconomyOverview(EconomyCommandTestBase):
    """The bare `@economy` view."""

    def test_unconfigured_treasury_names_the_setting_and_the_fix(self):
        # The error message is the documentation (this is an admin's first
        # contact with the system), so it must name the settings key rather than
        # just reporting an absence.
        output = self.call(CmdEconomy(), "")
        self.assertIn(TREASURY_DBREF_SETTING, output)
        self.assertIn("typeclasses.treasury.Treasury", output)

    def test_overview_always_shows_the_reserve_obligation(self):
        # Q3 locked: shown every time, not only at mint. A number you have to ask
        # for is a number you forget.
        output = self.call(CmdEconomy(), "")
        self.assertIn("Reserve obligation", output)
        self.assertIn("0.0000 GameGold", output)

    def test_overview_reports_ledger_totals_and_obligation_after_a_mint(self):
        self.treasury.currency.add(1_000_000, source="crypto_exchange")
        with override_settings(**{TREASURY_DBREF_SETTING: self.treasury.dbref}):
            output = self.call(CmdEconomy(), "")
        self.assertIn("100 Gold", output)
        # 1,000,000 Copper == 100 Gold == 100 GameGold. The rate is per GOLD, and
        # this is the assertion that would catch a per-Copper mistake.
        self.assertIn("100.0000 GameGold", output)

    def test_unknown_subcommand_shows_usage(self):
        output = self.call(CmdEconomy(), "frobnicate")
        self.assertIn("Unknown subcommand", output)
        self.assertIn("@economy mint", output)


class TestEconomyAudit(EconomyCommandTestBase):
    """`@economy audit` -- quiet when it holds, unmissable when it does not."""

    def test_clean_economy_reports_ok(self):
        self.treasury.currency.add(10_000, source="crypto_exchange")
        output = self.call(CmdEconomy(), "audit")
        self.assertIn("OK", output)
        self.assertNotIn("MISMATCH", output)

    def test_corrupted_wallet_produces_a_loud_failure(self):
        # Money that no mint accounts for. The command layer owns the loud
        # rendering because audit_report() is uncoloured by design (D2).
        self.char1.attributes.add("wallet", 999_999)
        output = self.call(CmdEconomy(), "audit")
        self.assertIn("ECONOMY AUDIT FAILED", output)
        self.assertIn("MISMATCH", output)


class TestEconomyMintDryRun(ConfiguredTreasuryMixin, EconomyCommandTestBase):
    """
    The confirmation mechanism: the bare form must create NOTHING.

    This is the most important class in the file. The whole argument-based
    confirmation design rests on the dry run being genuinely inert, and the only
    assertion that proves it is a side-effect assertion.
    """

    def test_preview_creates_no_money(self):
        output = self.call(CmdEconomy(), "mint 100 gold")
        self.assertIn("MINT PREVIEW", output)
        self.assertEqual(self.treasury.currency.value, 0)
        self.assertEqual(economy_log.total_minted(), 0)
        self.assertEqual(economy_log.entries(), [])

    def test_preview_shows_the_obligation_being_committed_to(self):
        # Showing the obligation BEFORE the money exists is the actual protection
        # here; the word "confirm" is only the trigger.
        output = self.call(CmdEconomy(), "mint 100 gold")
        self.assertIn("Obligation after", output)
        self.assertIn("100.0000 GameGold", output)

    def test_preview_tells_the_admin_exactly_how_to_confirm(self):
        output = self.call(CmdEconomy(), "mint 100 gold")
        self.assertIn("confirm", output)

    def test_bare_confirm_token_is_not_treated_as_a_confirmation(self):
        # `@economy mint confirm` must fail as an unreadable amount, not strip the
        # token and complain about an empty one the admin never typed -- and
        # above all must not mint.
        output = self.call(CmdEconomy(), "mint confirm")
        self.assertIn("isn't an amount I can read", output)
        self.assertEqual(economy_log.total_minted(), 0)


class TestEconomyMintExecution(ConfiguredTreasuryMixin, EconomyCommandTestBase):
    """`@economy mint ... confirm` -- the one place money is created."""

    def test_mint_raises_treasury_and_ledger_by_the_same_amount(self):
        output = self.call(CmdEconomy(), "mint 100 gold confirm")
        self.assertIn("Minted 100 Gold", output)
        self.assertEqual(self.treasury.currency.value, 1_000_000)
        # Treasury balance and ledger total moving together IS the invariant.
        self.assertEqual(economy_log.total_minted(), 1_000_000)
        self.assertEqual(economy_log.net_issued(), 1_000_000)

    def test_mint_goes_into_the_treasury_and_never_the_caller(self):
        # If this ever fails, S4-1 is gone: there would be a second mint
        # destination and the faucet's whole reason for existing would collapse.
        self.call(CmdEconomy(), "mint 100 gold confirm")
        self.assertEqual(self.char1.currency.value, 0)

    def test_audit_is_green_immediately_after_a_mint(self):
        self.call(CmdEconomy(), "mint 100 gold confirm")
        self.assertTrue(economy_log.audit()["ok"])

    def test_ledger_entry_records_the_exchange_path(self):
        # Tagged crypto_exchange even though no exchange exists yet: the tranche
        # is executed THROUGH the exchange code path against a reserve
        # obligation, which is what keeps Principle 4 literally true (S4-1).
        self.call(CmdEconomy(), "mint 1 gold confirm")
        entries = economy_log.entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["kind"], "mint")
        self.assertEqual(entries[0]["amount"], 10_000)
        self.assertEqual(entries[0]["tag"], "crypto_exchange")
        self.assertEqual(entries[0]["recipient_dbref"], self.treasury.dbref)

    def test_receipt_restates_the_obligation(self):
        output = self.call(CmdEconomy(), "mint 1 gold confirm")
        self.assertIn("1.0000 GameGold", output)

    def test_faucet_direction_works_off_a_minted_treasury(self):
        # The end-to-end rehearsal of S4-1: one mint in, then money leaves by
        # transfer. Nothing here calls add() a second time, which is the point.
        self.call(CmdEconomy(), "mint 1 gold confirm")
        self.assertTrue(self.treasury.currency.transfer_to(self.char1, 250))
        self.assertEqual(economy_log.total_minted(), 10_000)
        self.assertTrue(economy_log.audit()["ok"])


class TestEconomyMintRefusals(EconomyCommandTestBase):
    """
    Every way a mint must be refused -- each asserting that nothing was created.

    An admin typo must never surface as a traceback (the Component B guard
    pattern), and it must never surface as money either.
    """

    def test_unparseable_amount(self):
        output = self.call(CmdEconomy(), "mint lots confirm")
        self.assertIn("isn't an amount I can read", output)
        self.assertEqual(economy_log.total_minted(), 0)

    def test_bare_number_without_denomination_is_refused(self):
        # D1 reaching the admin surface. Guessing between Copper and Gold is
        # wrong by a factor of ten thousand.
        output = self.call(CmdEconomy(), "mint 100 confirm")
        self.assertIn("isn't an amount I can read", output)
        self.assertEqual(economy_log.total_minted(), 0)

    def test_zero_is_refused(self):
        output = self.call(CmdEconomy(), "mint 0 gold confirm")
        self.assertIn("Minting nothing", output)
        self.assertEqual(economy_log.total_minted(), 0)

    def test_no_amount_at_all_shows_usage(self):
        output = self.call(CmdEconomy(), "mint")
        self.assertIn("Usage", output)
        self.assertEqual(economy_log.total_minted(), 0)

    def test_unconfigured_treasury_refuses_rather_than_minting_anywhere(self):
        # No override here: TREASURY_DBREF ships unset. The refusal must NOT fall
        # back to the caller's own wallet.
        output = self.call(CmdEconomy(), "mint 100 gold confirm")
        self.assertIn("Cannot mint", output)
        self.assertEqual(economy_log.total_minted(), 0)
        self.assertEqual(self.char1.currency.value, 0)
        self.assertEqual(self.treasury.currency.value, 0)

    def test_dbref_pointing_at_a_character_refuses_the_mint(self):
        # THE refusal that matters most. char1 resolves fine and has a working
        # currency handler, so without the typeclass check in resolve_treasury()
        # this would mint straight into a player's purse and nothing downstream
        # would object.
        with override_settings(**{TREASURY_DBREF_SETTING: self.char1.dbref}):
            output = self.call(CmdEconomy(), "mint 100 gold confirm")
        self.assertIn("Cannot mint", output)
        self.assertIn("NOT a Treasury", output)
        self.assertEqual(self.char1.currency.value, 0)
        self.assertEqual(economy_log.total_minted(), 0)

    def test_dangling_dbref_refuses_the_mint(self):
        with override_settings(**{TREASURY_DBREF_SETTING: "#999999"}):
            output = self.call(CmdEconomy(), "mint 100 gold confirm")
        self.assertIn("Cannot mint", output)
        self.assertEqual(economy_log.total_minted(), 0)


class TestEconomyBurn(ConfiguredTreasuryMixin, EconomyCommandTestBase):
    """
    `@economy burn` -- the exit, and a flagged deviation from decomposition §6/C.

    §6/C lists only `audit` and `mint`. Burn is implemented anyway so the
    obligation figure can be observed going DOWN; a decrement path that has never
    run outside a unit test is a decrement path that does not really exist yet.
    """

    def setUp(self):
        super().setUp()
        self.treasury.currency.add(10_000, source="crypto_exchange")

    def test_preview_destroys_nothing(self):
        output = self.call(CmdEconomy(), "burn 1 gold")
        self.assertIn("BURN PREVIEW", output)
        self.assertEqual(self.treasury.currency.value, 10_000)
        self.assertEqual(economy_log.total_burned(), 0)

    def test_burn_lowers_the_treasury_and_releases_the_obligation(self):
        output = self.call(CmdEconomy(), "burn 1 gold confirm")
        self.assertIn("Burned 1 Gold", output)
        self.assertEqual(self.treasury.currency.value, 0)
        self.assertEqual(economy_log.total_burned(), 10_000)
        self.assertEqual(economy_log.net_issued(), 0)
        self.assertIn("0.0000 GameGold", output)

    def test_audit_stays_green_across_the_full_mint_burn_cycle(self):
        # The claim the whole subcommand exists to make observable: money can
        # leave the world without the invariant noticing anything wrong.
        self.call(CmdEconomy(), "burn 1 gold confirm")
        self.assertTrue(economy_log.audit()["ok"])

    def test_insufficient_treasury_funds_is_reported_not_raised(self):
        output = self.call(CmdEconomy(), "burn 5 gold confirm")
        self.assertIn("holds only", output)
        # Nothing mutated, nothing logged -- burn() returns False having touched
        # neither the balance nor the ledger (D7).
        self.assertEqual(self.treasury.currency.value, 10_000)
        self.assertEqual(economy_log.total_burned(), 0)

    def test_preview_warns_when_the_burn_would_be_refused(self):
        # Reading the balance to PHRASE a warning is safe; it is not being used
        # to authorise the later debit, which burn() re-checks under its own
        # atomic section (S4-R1).
        output = self.call(CmdEconomy(), "burn 5 gold")
        self.assertIn("would be refused", output)
        self.assertEqual(self.treasury.currency.value, 10_000)

    def test_zero_is_refused(self):
        output = self.call(CmdEconomy(), "burn 0 gold confirm")
        self.assertIn("Burning nothing", output)
        self.assertEqual(economy_log.total_burned(), 0)
