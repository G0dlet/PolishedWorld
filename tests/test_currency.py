"""
Unit tests for the currency denomination layer. Stage 4, Component A.1.

Written to the pattern in `tests/test_knowledge.py`, which is the golden
reference for this project (AGENTS.md section 0A). If something here looks
unusual, check there first -- the shape is deliberate.

WHAT IT COVERS
--------------
* world.currency.to_copper            -- denominated -> Copper
* world.currency.split_denominations  -- Copper -> denominated
* world.currency.format_copper        -- Copper -> display string
* world.currency.parse_amount         -- player input -> Copper | None

BASE CLASS
----------
`EvenniaTestCase` throughout -- the lightest one available. A.1 is pure
functions with no Evennia import, no database and no typeclass, so building
the .char1/.room1 object graph (EvenniaTest) would cost setup time for fixtures
no test here touches. The handler tests in A.2 will need EvenniaTest; these
do not.

HOW TO RUN
----------
The --settings flag is NOT optional anywhere in this project (see the golden
template) even though this particular module would survive without it.

    evennia test --settings settings.py .                     # whole game dir
    evennia test --settings settings.py tests                 # just this package
    evennia test --settings settings.py tests.test_currency   # just this module
    # one test:
    evennia test --settings settings.py \
        tests.test_currency.TestSplitDenominations.test_round_trip_is_exact
"""

from evennia.utils.test_resources import EvenniaTest, EvenniaTestCase

from world import economy_log
from world.currency import (
    COPPER_PER_GOLD,
    COPPER_PER_SILVER,
    MINT_SOURCES,
    CurrencyHandler,
    format_copper,
    parse_amount,
    split_denominations,
    to_copper,
)


class TestConstants(EvenniaTestCase):
    """
    The denomination relationship is documented in three separate places
    (GameGold Economy, the Stage 4 decomposition, the module docstring). This
    pins it in executable form so a doc drifting cannot go unnoticed.
    """

    def test_documented_relationship_holds(self):
        self.assertEqual(COPPER_PER_SILVER, 100)
        self.assertEqual(COPPER_PER_GOLD, 10_000)
        # 1 Gold = 100 Silver, stated as the relationship rather than the value,
        # because that is the thing the docs actually promise.
        self.assertEqual(COPPER_PER_GOLD, 100 * COPPER_PER_SILVER)


class TestToCopper(EvenniaTestCase):
    """Denominated input -> a single Copper integer."""

    def test_each_denomination_alone(self):
        self.assertEqual(to_copper(copper=7), 7)
        self.assertEqual(to_copper(silver=1), 100)
        self.assertEqual(to_copper(gold=1), 10_000)

    def test_mixed_denominations_sum(self):
        self.assertEqual(to_copper(gold=1, silver=2, copper=3), 10_203)

    def test_defaults_are_zero(self):
        self.assertEqual(to_copper(), 0)

    def test_negative_input_passes_through(self):
        # D4: this module is arithmetic, not policy. transfer_to (S4-R1) is what
        # prevents a negative balance; audit() (A.3) is what detects one.
        self.assertEqual(to_copper(silver=-5), -500)

    def test_non_integer_is_rejected_loudly(self):
        # A float reaching the wallet Attribute would make the audit sum
        # non-exact, and the corruption would surface far from its cause -- so
        # this raises rather than coercing. Silent truncation would be worse
        # still: it destroys money without a word.
        with self.assertRaises(TypeError):
            to_copper(gold=1.5)
        with self.assertRaises(TypeError):
            to_copper(copper="5")

    def test_bool_is_rejected(self):
        # bool subclasses int in Python, so without an explicit guard
        # to_copper(True) would quietly mean one Gold.
        with self.assertRaises(TypeError):
            to_copper(gold=True)


class TestSplitDenominations(EvenniaTestCase):
    """Copper integer -> (gold, silver, copper)."""

    def test_round_trip_is_exact(self):
        # THE load-bearing property of this module: splitting and recombining
        # must be lossless, or the wallet's single-integer representation
        # (S4-2) leaks money at every display boundary. Spread deliberately
        # covers sub-Silver, sub-Gold, exact multiples and a large value.
        for amount in (0, 1, 99, 100, 101, 9_999, 10_000, 10_001, 123_456, 10_000_000):
            with self.subTest(amount=amount):
                self.assertEqual(to_copper(*split_denominations(amount)), amount)

    def test_round_trip_holds_for_negatives(self):
        # Not decoration: format_copper() splits abs() and re-attaches the sign,
        # so a broken negative split would surface as a wrong displayed balance
        # exactly when someone is investigating a bug.
        for amount in (-1, -500, -10_500, -123_456):
            with self.subTest(amount=amount):
                self.assertEqual(to_copper(*split_denominations(amount)), amount)

    def test_boundaries(self):
        self.assertEqual(split_denominations(0), (0, 0, 0))
        self.assertEqual(split_denominations(9_999), (0, 99, 99))
        self.assertEqual(split_denominations(10_000), (1, 0, 0))
        self.assertEqual(split_denominations(10_001), (1, 0, 1))

    def test_negative_carries_sign_on_every_component(self):
        # Python's floor division would give (-2, 95, 0) here -- arithmetically
        # true, useless to a caller, and a broken round-trip.
        self.assertEqual(split_denominations(-10_500), (-1, -5, 0))


class TestFormatCopper(EvenniaTestCase):
    """
    Copper integer -> display string. Asserts on the FULL string here (unlike
    the golden template's advice to avoid matching decorated output) because
    the grammar itself is the locked decision under test (D3): separator,
    capitalisation, omission of zero denominations and the absence of plurals
    are exactly what these tests exist to pin. There is no ASCII framing to
    break on.
    """

    def test_zero_is_a_state_not_a_quantity(self):
        self.assertEqual(format_copper(0), "nothing")

    def test_single_denomination(self):
        self.assertEqual(format_copper(3), "3 Copper")
        self.assertEqual(format_copper(500), "5 Silver")
        self.assertEqual(format_copper(10_000), "1 Gold")

    def test_zero_denominations_are_omitted(self):
        # 1 Gold 0 Silver 3 Copper -- the empty middle must not print.
        self.assertEqual(format_copper(10_003), "1 Gold, 3 Copper")

    def test_full_mixed_amount(self):
        self.assertEqual(format_copper(10_203), "1 Gold, 2 Silver, 3 Copper")

    def test_names_do_not_pluralise(self):
        # Mass-noun treatment, as in "three gold". Locked in D3.
        self.assertEqual(format_copper(2), "2 Copper")
        self.assertEqual(format_copper(20_000), "2 Gold")

    def test_negative_takes_one_leading_sign(self):
        # One minus for the whole sum, not one per component -- "-1 Gold,
        # -5 Silver" would read as two separate debts.
        self.assertEqual(format_copper(-10_500), "-1 Gold, 5 Silver")
        self.assertEqual(format_copper(-3), "-3 Copper")

    def test_output_carries_no_colour_codes(self):
        # D2. This string goes into ledger entries and exception messages as
        # well as onto a screen; markup is noise in most of those.
        self.assertNotIn("|", format_copper(10_203))

    def test_non_integer_is_rejected(self):
        with self.assertRaises(TypeError):
            format_copper(1.5)


class TestParseAmount(EvenniaTestCase):
    """
    Player input -> Copper | None. Returns None rather than raising so the
    calling command owns the error wording.
    """

    def test_full_denomination_words(self):
        self.assertEqual(parse_amount("50 copper"), 50)
        self.assertEqual(parse_amount("3 silver"), 300)
        self.assertEqual(parse_amount("1 gold"), 10_000)

    def test_abbreviations(self):
        self.assertEqual(parse_amount("50 c"), 50)
        self.assertEqual(parse_amount("3 s"), 300)
        self.assertEqual(parse_amount("1 g"), 10_000)

    def test_case_and_surrounding_whitespace_are_tolerated(self):
        self.assertEqual(parse_amount("  1 GOLD  "), 10_000)
        self.assertEqual(parse_amount("1\tGold"), 10_000)

    def test_plural_full_words_are_tolerated(self):
        # Players type these. Cheap to accept, no ambiguity created.
        self.assertEqual(parse_amount("3 coppers"), 3)
        self.assertEqual(parse_amount("2 golds"), 20_000)

    def test_plural_tolerance_does_not_break_the_silver_abbreviation(self):
        # THE regression guard for the plural rule: "s" IS the Silver
        # abbreviation, so stripping a trailing "s" before the exact lookup
        # would turn a valid "3 s" into an empty token and reject it.
        self.assertEqual(parse_amount("3 s"), 300)

    def test_zero_parses_rather_than_failing(self):
        # 0 is parseable but not payable. Rejecting a payment of nothing is the
        # command's job (B.2); folding the cases together here would make `pay`
        # report a syntax error for syntactically fine input.
        self.assertEqual(parse_amount("0 copper"), 0)

    def test_bare_number_is_rejected(self):
        # D1. A default denomination would let `pay 50 to Bob` silently move
        # 1/200th of what a player meaning Silver intended, with nothing to
        # notice. The command tells them to name a denomination instead.
        self.assertIsNone(parse_amount("50"))

    def test_negative_and_fractional_numbers_are_rejected(self):
        self.assertIsNone(parse_amount("-5 copper"))
        self.assertIsNone(parse_amount("1.5 gold"))

    def test_missing_number_is_rejected(self):
        self.assertIsNone(parse_amount("gold"))

    def test_empty_input_is_rejected(self):
        self.assertIsNone(parse_amount(""))
        self.assertIsNone(parse_amount("   "))
        self.assertIsNone(parse_amount(None))

    def test_unknown_denomination_is_rejected(self):
        self.assertIsNone(parse_amount("5 platinum"))
        self.assertIsNone(parse_amount("5 x"))

    def test_compact_forms_are_out_of_scope(self):
        # Both the attached single form and the multi-denomination form are
        # deferred to BACKLOG as one feature. The rule is "exactly two
        # whitespace-separated tokens", which rejects both for the same reason.
        self.assertIsNone(parse_amount("50c"))
        self.assertIsNone(parse_amount("2g30s"))

    def test_extra_tokens_are_rejected(self):
        # Guards against a command passing an un-split argument through, e.g.
        # the whole of "50 copper to Bob".
        self.assertIsNone(parse_amount("50 copper to Bob"))

    def test_non_ascii_digits_do_not_crash(self):
        # "\u00b2".isdigit() is True but int() refuses it -- an isdigit()-only
        # check would turn bad input into a traceback. Requiring ASCII first
        # makes the check total.
        self.assertIsNone(parse_amount("\u00b2 copper"))
        self.assertIsNone(parse_amount("\u0665 copper"))

    def test_parse_and_format_agree(self):
        # The two directions share DENOMINATIONS as their single source of
        # truth; this is the test that would fail if they ever stopped.
        for text, rendered in (
            ("1 gold", "1 Gold"),
            ("3 silver", "3 Silver"),
            ("50 copper", "50 Copper"),
        ):
            with self.subTest(text=text):
                self.assertEqual(format_copper(parse_amount(text)), rendered)


class LedgerIsolationMixin:
    """
    Reset the global ledger before every test.

    ⚠️ THE gotcha for this whole component. The ledger is a *global* Script, so
    unlike .char1/.room1 it is not rebuilt per test -- entries and running
    totals leak from one test into the next, and `total_minted()` assertions
    start passing or failing depending on test execution order. Same class of
    problem as the cooldown bleed in Testing Reference section 7, and it fails
    just as confusingly.

    Attributes are cleared rather than the Script deleted: GLOBAL_SCRIPTS would
    happily re-create it, but deleting and re-creating a Script per test is far
    slower than zeroing three Attributes.
    """

    def setUp(self):
        super().setUp()
        ledger = economy_log.get_ledger()
        ledger.db.entries = []
        ledger.db.minted = 0
        ledger.db.burned = 0


class TestEconomyLog(LedgerIsolationMixin, EvenniaTest):
    """
    The ledger primitive: append, running totals, repair.

    EvenniaTest rather than EvenniaTestCase because a global Script needs a
    database. `.char1` is used only as a recipient for entry provenance.
    """

    character_typeclass = "typeclasses.characters.Character"

    def test_ledger_starts_empty(self):
        self.assertEqual(economy_log.total_minted(), 0)
        self.assertEqual(economy_log.total_burned(), 0)
        self.assertEqual(economy_log.net_issued(), 0)

    def test_append_mint_updates_running_total(self):
        economy_log.append(economy_log.KIND_MINT, 500, "crypto_exchange", recipient=self.char1)
        self.assertEqual(economy_log.total_minted(), 500)
        self.assertEqual(economy_log.total_burned(), 0)
        self.assertEqual(economy_log.net_issued(), 500)

    def test_append_burn_subtracts_from_net(self):
        economy_log.append(economy_log.KIND_MINT, 500, "crypto_exchange", recipient=self.char1)
        economy_log.append(economy_log.KIND_BURN, 200, "crypto_exchange", recipient=self.char1)
        self.assertEqual(economy_log.total_burned(), 200)
        self.assertEqual(economy_log.net_issued(), 300)

    def test_burns_are_stored_as_positive_amounts(self):
        # Storing burns negative would let a sign error in append() cancel a
        # sign error in total_burned() and still balance -- a bug that hides
        # itself. Positive amounts plus an explicit kind cannot do that.
        economy_log.append(economy_log.KIND_BURN, 200, "crypto_exchange")
        self.assertEqual(economy_log.entries()[0]["amount"], 200)

    def test_entry_records_recipient_key_and_dbref(self):
        # The dbref identifies the object exactly; the key stays readable after
        # that object is deleted.
        economy_log.append(economy_log.KIND_MINT, 500, "crypto_exchange", recipient=self.char1)
        entry = economy_log.entries()[0]
        self.assertEqual(entry["recipient_key"], self.char1.key)
        self.assertEqual(entry["recipient_dbref"], self.char1.dbref)

    def test_recipient_is_optional(self):
        economy_log.append(economy_log.KIND_MINT, 500, "crypto_exchange")
        entry = economy_log.entries()[0]
        self.assertIsNone(entry["recipient_key"])
        self.assertIsNone(entry["recipient_dbref"])

    def test_bad_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            economy_log.append("adjustment", 500, "crypto_exchange")

    def test_non_positive_amount_is_rejected(self):
        with self.assertRaises(ValueError):
            economy_log.append(economy_log.KIND_MINT, 0, "crypto_exchange")
        with self.assertRaises(ValueError):
            economy_log.append(economy_log.KIND_MINT, -500, "crypto_exchange")

    def test_entries_can_be_filtered_and_limited(self):
        economy_log.append(economy_log.KIND_MINT, 100, "crypto_exchange")
        economy_log.append(economy_log.KIND_BURN, 50, "crypto_exchange")
        economy_log.append(economy_log.KIND_MINT, 200, "crypto_exchange")
        self.assertEqual(len(economy_log.entries()), 3)
        self.assertEqual(len(economy_log.entries(kind=economy_log.KIND_MINT)), 2)
        self.assertEqual(economy_log.entries(limit=1)[0]["amount"], 200)

    def test_entries_are_copies_not_live_references(self):
        # Callers get plain dicts, not Evennia's _SaverDict, so a caller
        # mutating the result cannot write back into the ledger.
        economy_log.append(economy_log.KIND_MINT, 100, "crypto_exchange")
        got = economy_log.entries()[0]
        got["amount"] = 999_999
        self.assertEqual(economy_log.entries()[0]["amount"], 100)

    def test_recompute_totals_repairs_drift(self):
        # Simulates the failure this repair path exists for: totals and entries
        # disagreeing after an exception between the two writes, or a hand-edited
        # Attribute. audit() (A.3) is what would tell you to run it.
        economy_log.append(economy_log.KIND_MINT, 500, "crypto_exchange")
        economy_log.get_ledger().db.minted = 99_999
        economy_log.recompute_totals()
        self.assertEqual(economy_log.total_minted(), 500)


class TestCurrencyHandlerBasics(LedgerIsolationMixin, EvenniaTest):
    """Reading and rendering a wallet."""

    character_typeclass = "typeclasses.characters.Character"

    def test_new_character_has_no_wallet_attribute_but_reads_zero(self):
        # D6, and the reason no backfill is needed anywhere: a character who has
        # never touched money simply has none, and the Attribute is not created
        # until the first mutation. Nothing exists that could clobber a live
        # balance, so the force=True shape of trap (Reference 3.5) cannot occur.
        self.assertIsNone(self.char1.attributes.get("wallet"))
        self.assertEqual(self.char1.currency.value, 0)

    def test_handler_is_wired_and_stable(self):
        # lazy_property caches, so this must be the same handler each access --
        # otherwise anything holding a reference would go stale.
        self.assertIs(self.char1.currency, self.char1.currency)
        self.assertIsInstance(self.char1.currency, CurrencyHandler)

    def test_format_renders_the_balance(self):
        self.char1.currency.add(10_203, source="admin_correction")
        self.assertEqual(self.char1.currency.format(), "1 Gold, 2 Silver, 3 Copper")

    def test_empty_wallet_formats_as_nothing(self):
        self.assertEqual(self.char1.currency.format(), "nothing")

    def test_can_afford(self):
        self.char1.currency.add(500, source="admin_correction")
        self.assertTrue(self.char1.currency.can_afford(500))
        self.assertTrue(self.char1.currency.can_afford(499))
        self.assertFalse(self.char1.currency.can_afford(501))


class TestMintSeparation(LedgerIsolationMixin, EvenniaTest):
    """
    S4-1. The structural guarantee that money enters the world only one way.
    """

    character_typeclass = "typeclasses.characters.Character"

    def test_faucet_cannot_mint(self):
        # ⭐ THE load-bearing test of Stage 4. The temple faucet (Component D)
        # looks like it hands out money and must not be able to create any --
        # it transfers from the Treasury. If this test ever goes green for the
        # wrong reason, the game has an unbounded money supply and nobody finds
        # out until inflation makes it obvious.
        with self.assertRaises(ValueError):
            self.char1.currency.add(500, source="faucet")

    def test_no_money_is_created_by_a_rejected_mint(self):
        with self.assertRaises(ValueError):
            self.char1.currency.add(500, source="faucet")
        self.assertEqual(self.char1.currency.value, 0)
        self.assertEqual(economy_log.total_minted(), 0)

    def test_source_is_mandatory(self):
        # `wallet.add(500)` must not be a working call -- someone reaching for a
        # generic "add to balance" helper should hit a TypeError, not mint.
        with self.assertRaises(TypeError):
            self.char1.currency.add(500)

    def test_valid_sources_mint_and_log(self):
        for source in sorted(MINT_SOURCES):
            with self.subTest(source=source):
                before = economy_log.total_minted()
                self.char1.currency.add(100, source=source)
                self.assertEqual(economy_log.total_minted(), before + 100)

    def test_add_returns_the_new_balance(self):
        # Not a bool: add() has no expected-failure mode. Documented so nobody
        # "fixes" it for symmetry with transfer_to.
        self.assertEqual(self.char1.currency.add(500, source="admin_correction"), 500)
        self.assertEqual(self.char1.currency.add(300, source="admin_correction"), 800)

    def test_non_positive_mint_is_rejected(self):
        with self.assertRaises(ValueError):
            self.char1.currency.add(0, source="admin_correction")
        with self.assertRaises(ValueError):
            self.char1.currency.add(-500, source="admin_correction")

    def test_bool_amount_is_rejected(self):
        # bool subclasses int; without the explicit guard this would mint 1.
        with self.assertRaises(TypeError):
            self.char1.currency.add(True, source="admin_correction")


class TestBurn(LedgerIsolationMixin, EvenniaTest):
    """The Stage 8 exchange-back primitive, built now so the ledger is whole."""

    character_typeclass = "typeclasses.characters.Character"

    def test_burn_removes_money_and_logs_it(self):
        self.char1.currency.add(500, source="admin_correction")
        self.assertTrue(self.char1.currency.burn(200, reason="crypto_exchange"))
        self.assertEqual(self.char1.currency.value, 300)
        self.assertEqual(economy_log.total_burned(), 200)

    def test_burn_beyond_balance_returns_false_and_changes_nothing(self):
        self.char1.currency.add(500, source="admin_correction")
        self.assertFalse(self.char1.currency.burn(501, reason="crypto_exchange"))
        self.assertEqual(self.char1.currency.value, 500)
        self.assertEqual(economy_log.total_burned(), 0)

    def test_unknown_reason_is_rejected(self):
        self.char1.currency.add(500, source="admin_correction")
        with self.assertRaises(ValueError):
            self.char1.currency.burn(100, reason="sink")
        self.assertEqual(self.char1.currency.value, 500)


class TestTransfer(LedgerIsolationMixin, EvenniaTest):
    """
    S4-R1 and S4-4. Transfers move money and cannot change how much exists.
    """

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.char1.currency.add(1_000, source="admin_correction")

    def test_transfer_conserves_the_total(self):
        # The property that makes transfer_to safe to use everywhere: even a
        # buggy transfer cannot change how much money exists in the world.
        before = self.char1.currency.value + self.char2.currency.value
        self.assertTrue(self.char1.currency.transfer_to(self.char2, 400))
        after = self.char1.currency.value + self.char2.currency.value
        self.assertEqual(before, after)
        self.assertEqual(self.char1.currency.value, 600)
        self.assertEqual(self.char2.currency.value, 400)

    def test_insufficient_funds_returns_false_and_moves_nothing(self):
        # Partial mutation here would be the duplication/destruction bug for the
        # whole economy, so both wallets are asserted, not just the payer's.
        self.assertFalse(self.char1.currency.transfer_to(self.char2, 1_001))
        self.assertEqual(self.char1.currency.value, 1_000)
        self.assertEqual(self.char2.currency.value, 0)

    def test_exact_balance_transfers(self):
        # Boundary: >= not >, so spending everything must succeed.
        self.assertTrue(self.char1.currency.transfer_to(self.char2, 1_000))
        self.assertEqual(self.char1.currency.value, 0)

    def test_transfers_are_not_logged(self):
        # S4-4. Transfers are the normal business of the game; logging them
        # would grow without bound for no diagnostic gain. The invariant, not a
        # transaction log, is what proves nothing was created.
        before = len(economy_log.entries())
        self.char1.currency.transfer_to(self.char2, 400)
        self.assertEqual(len(economy_log.entries()), before)

    def test_transfer_never_mints(self):
        # Guards the structural separation from the other direction: if
        # transfer_to were ever "simplified" to call add() on the recipient,
        # every payment in the game would create money and this catches it.
        before = economy_log.total_minted()
        self.char1.currency.transfer_to(self.char2, 400)
        self.assertEqual(economy_log.total_minted(), before)

    def test_self_transfer_raises(self):
        # Raises rather than returning False so it cannot be mistaken for
        # poverty (D7). B.2 catches `pay ... to me` first with a friendly
        # message; this is the backstop.
        with self.assertRaises(ValueError):
            self.char1.currency.transfer_to(self.char1, 100)
        self.assertEqual(self.char1.currency.value, 1_000)

    def test_target_without_a_wallet_raises(self):
        # .obj1 is a plain Object with no currency handler. A caller bug, not a
        # player condition.
        with self.assertRaises(TypeError):
            self.char1.currency.transfer_to(self.obj1, 100)
        self.assertEqual(self.char1.currency.value, 1_000)

    def test_non_positive_amount_is_rejected(self):
        with self.assertRaises(ValueError):
            self.char1.currency.transfer_to(self.char2, 0)
        with self.assertRaises(ValueError):
            self.char1.currency.transfer_to(self.char2, -100)

    def test_invariant_holds_across_mint_transfer_and_burn(self):
        # A miniature of the A.3 audit: everything the two characters hold must
        # equal everything the ledger says was issued. This is the assertion
        # audit() generalises to the whole world.
        self.char1.currency.transfer_to(self.char2, 400)
        self.char2.currency.burn(150, reason="crypto_exchange")
        held = self.char1.currency.value + self.char2.currency.value
        self.assertEqual(held, economy_log.net_issued())
