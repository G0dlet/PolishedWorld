"""
Unit tests for the player-facing currency commands. Stage 4, Component B.

Written to the pattern in `tests/test_knowledge.py`, the golden reference for
this project (AGENTS.md section 0A), and to the ledger-isolation pattern
established in `tests/test_currency.py`. If something here looks unusual, check
those two first -- the shape is deliberate.

WHAT IT COVERS
--------------
* commands.currency_commands.CmdWallet -- B.1, read-only balance display

BASE CLASS
----------
`EvenniaCommandTest`: the command is driven through `.call()`, which needs the
.char1/.room1 fixture graph *and* the command runner. The denomination layer
underneath is already covered by `tests/test_currency.py` with the lighter
`EvenniaTestCase`; none of it is re-tested here. What IS tested here is the
surface -- the wording, and the claim that reading a balance writes nothing.

⚠️ LEDGER ISOLATION -- INHERIT THE MIXIN OR THE SUITE GOES ORDER-DEPENDENT
--------------------------------------------------------------------------
`LedgerIsolationMixin` is imported from `tests.test_currency` rather than
rewritten. The ledger is a *global* Script and is NOT rebuilt per test the way
.char1/.room1 are, so its entries and running totals leak from one test into the
next. Every test class in this project that touches money must inherit it. The
funding helper below calls `add()`, which writes a ledger entry, so this applies
here.

⚠️ TWO FIXTURE FACTS, VERIFIED FIRSTHAND IN
`evennia/utils/test_resources.py` (Evennia 6.1.0)
--------------------------------------------------
1. `self.char1.key` is **"Char"**, not "Char1" -- only char2 carries a number.
2. `.call(msg=...)` compares with `.startswith()` on the ansi-stripped output,
   so an expected string that is a substring but not a prefix fails. The
   separator for several `.msg()` calls to the SAME receiver is `"|"`, not
   `"||"` -- `msg_sep = "|" if noansi else "||"`, and `noansi` defaults True.
   No separator appears in this file: every path here sends one message.

HOW TO RUN
----------
The --settings flag is not optional anywhere in this project.

    evennia test --settings settings.py tests.test_currency_commands
    evennia test --settings settings.py tests    # the whole package
"""

from evennia.utils.test_resources import EvenniaCommandTest

from commands.currency_commands import CmdWallet
from tests.test_currency import LedgerIsolationMixin
from world.currency import COPPER_PER_GOLD, COPPER_PER_SILVER


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
