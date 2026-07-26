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

from evennia.utils.test_resources import EvenniaTestCase

from world.currency import (
    COPPER_PER_GOLD,
    COPPER_PER_SILVER,
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
