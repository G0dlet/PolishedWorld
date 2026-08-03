"""
Unit tests for the barter currency bridge. Stage 4, Component E.1.

Written to the pattern in `tests/test_knowledge.py` (the golden reference,
AGENTS.md section 0A) and to the ledger-isolation pattern established in
`tests/test_currency.py`.

WHAT IT COVERS
--------------
* world.barter.CmdPWOffer      -- segment classification, coin recording, UX guards
* world.barter.CmdPWStatus     -- the coin line, and the no-coin regression property
* world.barter.CmdPWDecline    -- the emptiness gate that upstream gets wrong
* world.barter.PWTradeHandler  -- offer(currency=) contract, teardown clearing
* the module-global patch itself -- that all seven swaps are still installed

WHAT IT DOES *NOT* COVER
------------------------
Settlement. No wallet may move anywhere in this file: E.1 records a promise and
E.2 keeps it. Several tests assert exactly that -- a wallet that moved during an
`offer` would mean the bridge had quietly become a payment.

⚠️ WHY THE HANDLER IS BUILT BY HAND, NOT VIA `trade`
----------------------------------------------------
`CmdTrade` needs two consenting parties across two sessions, which is an
integration test (Testing Reference section 10), not a unit test. Constructing
`PWTradeHandler(char1, char2)` and calling `.join(char2)` reproduces exactly
what the two-command handshake leaves behind -- both `ndb.tradehandler` back-
references, both trade cmdsets, `trade_started = True` -- and is the same state
the commands under test read. The handshake itself is already covered in play.

⚠️ LEDGER ISOLATION
-------------------
`LedgerIsolationMixin` is inherited everywhere money is funded: the ledger is a
*global* Script and is not rebuilt per test, so its totals leak between tests.
The funding helper calls `add()`, which writes an entry.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_barter_currency
    evennia test --settings settings.py tests
"""

from evennia.contrib.game_systems.barter import barter as barter_module
from evennia.contrib.game_systems.barter.barter import CmdsetTrade
from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from tests.test_currency import LedgerIsolationMixin
from world.barter import (
    CmdPWAccept,
    CmdPWDecline,
    CmdPWEvaluate,
    CmdPWOffer,
    CmdPWStatus,
    PWTradeHandler,
    PWTradeTimeout,
)
from world.currency import COPPER_PER_SILVER


class TradeFixtureMixin:
    """Put char1 and char2 into a started trade, with coin in both purses.

    `character_typeclass` is pinned to the project Character on every class in
    this file: the default fixture typeclass has no `currency` handler, and a
    coin offer would then fail on the wallet lookup rather than on the thing
    under test.
    """

    character_typeclass = "typeclasses.characters.Character"

    #: Both parties start with 10 Silver, so "afford" and "cannot afford" are
    #: both a short distance away and neither needs a magic number at the site.
    START_BALANCE = 10 * COPPER_PER_SILVER

    def setUp(self):
        super().setUp()
        self.char1.currency.add(self.START_BALANCE, source="admin_correction")
        self.char2.currency.add(self.START_BALANCE, source="admin_correction")
        self.handler = PWTradeHandler(self.char1, self.char2)
        self.handler.join(self.char2)

    def _item(self, key, location=None):
        """A plain tradeable object in someone's inventory."""
        owner = location or self.char1
        return create.create_object(key=key, location=owner, home=owner)

    def _offer(self, args, caller=None, msg=None):
        """Run `offer` and return what was said, to whoever was listening."""
        caller = caller or self.char1
        return self.call(CmdPWOffer(), args, msg, caller=caller)


class TestOfferSegmentClassification(TradeFixtureMixin, LedgerIsolationMixin, EvenniaCommandTest):
    """
    The digit-first rule that separates coin from items.

    This is the load-bearing decision of E.1: if a segment can be read as both,
    every other guarantee in the component is built on sand.
    """

    def test_coin_only_offer_is_recorded_on_the_handler(self):
        self._offer("5 silver")
        self.assertEqual(self.handler.part_a_currency, 5 * COPPER_PER_SILVER)
        self.assertEqual(self.handler.part_a_offers, [])

    def test_offering_coin_moves_no_money(self):
        # THE property of the handler-level bridge (S4-2). An offer is a
        # promise; if a purse moves here, E.2 would be settling twice.
        self._offer("5 silver")
        self.assertEqual(self.char1.currency.value, self.START_BALANCE)
        self.assertEqual(self.char2.currency.value, self.START_BALANCE)

    def test_mixed_offer_records_items_and_coin_together(self):
        sword = self._item("iron sword")
        self._offer("iron sword, 3 silver")
        self.assertEqual(self.handler.part_a_offers, [sword])
        self.assertEqual(self.handler.part_a_currency, 3 * COPPER_PER_SILVER)

    def test_coin_may_come_before_the_items(self):
        # Order must not matter: players type what they think of first.
        sword = self._item("iron sword")
        self._offer("3 silver, iron sword")
        self.assertEqual(self.handler.part_a_offers, [sword])
        self.assertEqual(self.handler.part_a_currency, 3 * COPPER_PER_SILVER)

    def test_multiple_coin_segments_sum(self):
        self._offer("3 silver, 20 copper")
        self.assertEqual(self.handler.part_a_currency, 3 * COPPER_PER_SILVER + 20)

    def test_an_item_keyed_like_a_denomination_is_still_an_item(self):
        # The collision that motivated the digit-first rule. `copper` is a real
        # planned material-registry key (a smelting product), so an object with
        # that key WILL exist one day. Without the rule this is ambiguous; with
        # it, `offer copper` cannot be read as money because it has no number.
        ingot = self._item("copper")
        self._offer("copper")
        self.assertEqual(self.handler.part_a_offers, [ingot])
        self.assertEqual(self.handler.part_a_currency, 0)

    def test_a_digit_led_segment_that_fails_to_parse_gets_the_currency_error(self):
        # NOT "Could not find '5 silvre'". This is why parse_amount returns
        # None instead of raising: the command owns the wording, and `offer`
        # says something different from `pay` about the same bad input.
        returned = self._offer("5 silvre")
        self.assertIn("isn't an amount of coin I can read", returned)
        self.assertEqual(self.handler.part_a_currency, 0)

    def test_zero_coin_is_refused(self):
        # "0 copper" is a perfectly good parse and not an offerable amount.
        returned = self._offer("0 copper")
        self.assertIn("Offering nothing is not an offer", returned)
        self.assertEqual(self.handler.part_a_currency, 0)

    def test_a_bad_coin_segment_does_not_move_the_items_either(self):
        # The refusal must be total. A partially-applied offer would leave the
        # player looking at a table that does not match what they typed.
        self._item("iron sword")
        self._offer("iron sword, 0 copper")
        self.assertEqual(self.handler.part_a_offers, [])


class TestOfferGuards(TradeFixtureMixin, LedgerIsolationMixin, EvenniaCommandTest):
    """Everything `offer` refuses, and the state it must leave untouched."""

    def test_offering_more_than_you_hold_is_refused_at_offer_time(self):
        # UX only -- E.2 is the guard that matters -- but a player who can put
        # an impossible number on the table will believe the deal is live.
        returned = self._offer("50 silver")
        self.assertIn("You don't have that much on you", returned)
        self.assertEqual(self.handler.part_a_currency, 0)

    def test_offering_exactly_what_you_hold_is_allowed(self):
        # Boundary: can_afford is >=, so spending the lot must be offerable.
        self._offer("10 silver")
        self.assertEqual(self.handler.part_a_currency, self.START_BALANCE)

    def test_worn_clothing_is_still_refused(self):
        # Regression guard on pre-existing behaviour: func() was reimplemented
        # in E.1, and this check had to be carried across by hand.
        shirt = self._item("linen shirt")
        shirt.db.worn = True
        returned = self._offer("linen shirt")
        self.assertIn("while you're wearing it", returned)
        self.assertEqual(self.handler.part_a_offers, [])

    def test_offer_before_the_trade_starts_is_refused(self):
        handler = PWTradeHandler(self.char1, self.char2)  # no join() -> not started
        self.char1.ndb.tradehandler = handler
        returned = self._offer("5 silver")
        self.assertIn("Wait until the other party has accepted", returned)

    def test_empty_args_show_the_usage_line(self):
        returned = self._offer("")
        self.assertIn("Usage: offer", returned)
        self.assertIn("<denomination>", returned)

    def test_separator_only_input_shows_the_usage_line(self):
        # "offer ,,," splits into three empty segments and would otherwise fall
        # through to a silent no-op offer that wipes the standing one.
        returned = self._offer(",,,")
        self.assertIn("Usage: offer", returned)


class TestOfferReplacesTheStandingOffer(
    TradeFixtureMixin, LedgerIsolationMixin, EvenniaCommandTest
):
    """
    An offer replaces the standing offer whole -- coin included -- and resets
    both accepts. That contrib behaviour is preserved rather than reproduced,
    by routing the amount through `handler.offer()` instead of writing the
    field from the command.
    """

    def test_reoffering_coin_replaces_rather_than_accumulates(self):
        self._offer("3 silver")
        self._offer("5 silver")
        self.assertEqual(self.handler.part_a_currency, 5 * COPPER_PER_SILVER)

    def test_reoffering_without_coin_clears_the_coin(self):
        # This is how you take money off the table. There is deliberately no
        # separate "withdraw" verb.
        self._item("iron sword")
        self._offer("3 silver")
        self._offer("iron sword")
        self.assertEqual(self.handler.part_a_currency, 0)

    def test_changing_only_the_coin_resets_both_accepts(self):
        # The case a hand-written field assignment would have missed: nothing
        # about the ITEMS changed, so a naive implementation leaves the other
        # party accepted against a deal they never saw.
        self._offer("3 silver")
        self.handler.part_a_accepted = True
        self.handler.part_b_accepted = True
        self._offer("4 silver")
        self.assertFalse(self.handler.part_a_accepted)
        self.assertFalse(self.handler.part_b_accepted)

    def test_each_side_keeps_its_own_coin(self):
        self._offer("3 silver", caller=self.char1)
        self._offer("7 silver", caller=self.char2)
        self.assertEqual(self.handler.part_a_currency, 3 * COPPER_PER_SILVER)
        self.assertEqual(self.handler.part_b_currency, 7 * COPPER_PER_SILVER)


class TestOfferMessages(TradeFixtureMixin, LedgerIsolationMixin, EvenniaCommandTest):
    """Both parties must see the same deal described the same way."""

    def test_coin_only_offer_is_announced_to_both_parties(self):
        self._offer(
            "5 silver",
            msg={
                self.char1: "Your trade action: You offer 5 Silver in coin",
                self.char2: "Char:s trade action: They offer 5 Silver in coin",
            },
        )

    def test_mixed_offer_names_items_and_coin(self):
        self._item("iron sword")
        returned = self._offer("iron sword, 5 silver")
        self.assertIn("You offer iron sword, plus 5 Silver in coin", returned)

    def test_item_only_offer_says_nothing_about_coin(self):
        self._item("iron sword")
        returned = self._offer("iron sword")
        self.assertIn("You offer iron sword", returned)
        self.assertNotIn("coin", returned)


class TestStatusRendersCoin(TradeFixtureMixin, LedgerIsolationMixin, EvenniaCommandTest):
    """
    The offer table. `CmdStatus` is NOT one of the classes the patch layer
    originally swapped, so these also prove the new global assignment took.
    """

    def test_coin_shows_under_its_owner(self):
        self._offer("3 silver", caller=self.char1)
        self._offer("7 silver", caller=self.char2)
        returned = self.call(CmdPWStatus(), "", caller=self.char1)
        self.assertIn("3 Silver in coin", returned)
        self.assertIn("7 Silver in coin", returned)

    def test_a_side_with_only_coin_does_not_read_as_nothing(self):
        self._offer("3 silver")
        returned = self.call(CmdPWStatus(), "", caller=self.char1)
        # <nothing> may still appear for char2, who has offered neither.
        self.assertIn("Offered by Char:\n   + 3 Silver in coin", returned)

    def test_the_coin_line_carries_no_index(self):
        # ⚠️ `evaluate <nr>` feeds these numbers to TradeHandler.search(index),
        # which indexes items only. A numbered coin line shifts every index
        # after it and `eval 2` silently shows the wrong object.
        sword = self._item("iron sword")
        self._offer("iron sword, 3 silver", caller=self.char1)
        self._offer("2 silver", caller=self.char2)
        returned = self.call(CmdPWStatus(), "", caller=self.char1)
        self.assertIn("1 iron sword", returned)
        self.assertNotIn("2 3 Silver", returned)
        # And the index still resolves to the item it names.
        self.assertEqual(self.handler.search(0), sword)

    def test_output_is_identical_to_the_contrib_when_no_coin_is_offered(self):
        # The regression property: if this ever fails, the patch has changed
        # the item table itself rather than only adding to it.
        self._item("iron sword")
        self._offer("iron sword")
        ours = self.call(CmdPWStatus(), "", caller=self.char1)
        # NOT `from ...barter import CmdStatus` -- importing world.barter has
        # already replaced that global, so the import would hand back our own
        # class and the comparison would be vacuous. The base class is the only
        # honest reference to the unpatched contrib command.
        contrib_status = CmdPWStatus.__bases__[0]
        theirs = self.call(contrib_status(), "", caller=self.char1)
        self.assertEqual(ours, theirs)


class TestDeclineCountsCoinAsAnOffer(
    TradeFixtureMixin, LedgerIsolationMixin, EvenniaCommandTest
):
    """
    The upstream bug E.1 uncovers. `TradeHandler.list()` returns the two ITEM
    lists, so a coin-only offer leaves upstream's emptiness gate believing no
    offers exist -- and refusing to decline a deal that `status` displays.
    """

    def test_decline_works_when_one_side_offers_only_coin(self):
        self._item("iron sword")
        self._offer("iron sword", caller=self.char1)
        self._offer("5 silver", caller=self.char2)
        returned = self.call(CmdPWDecline(), "", caller=self.char1)
        self.assertNotIn("No offers have been made yet", returned)
        self.assertIn("decline", returned.lower())

    def test_decline_works_when_both_sides_offer_only_coin(self):
        self._offer("5 silver", caller=self.char1)
        self._offer("3 silver", caller=self.char2)
        returned = self.call(CmdPWDecline(), "", caller=self.char1)
        self.assertNotIn("No offers have been made yet", returned)

    def test_decline_still_refuses_when_one_side_has_offered_nothing(self):
        # The gate is widened, not removed.
        self._offer("5 silver", caller=self.char1)
        returned = self.call(CmdPWDecline(), "", caller=self.char1)
        self.assertIn("No offers have been made yet", returned)

    def test_decline_clears_a_standing_accept(self):
        self._offer("5 silver", caller=self.char1)
        self._offer("3 silver", caller=self.char2)
        self.handler.part_a_accepted = True
        self.call(CmdPWDecline(), "", caller=self.char1)
        self.assertFalse(self.handler.part_a_accepted)


class TestTradeHandlerCurrencyApi(TradeFixtureMixin, LedgerIsolationMixin, EvenniaTest):
    """
    The handler contract, tested without going through a command, because
    `offer()` is now a public API with a keyword that programmatic callers
    (E.2, and anything later) will use.
    """

    def test_a_fresh_handler_declares_both_fields(self):
        self.assertEqual(self.handler.part_a_currency, 0)
        self.assertEqual(self.handler.part_b_currency, 0)

    def test_offer_without_the_kwarg_clears_the_coin(self):
        # Upstream's own CmdOffer calls offer() with no kwarg. It must mean
        # "no coin in this offer", not "leave the old coin standing".
        self.handler.offer(self.char1, currency=500)
        self.handler.offer(self.char1)
        self.assertEqual(self.handler.part_a_currency, 0)

    def test_non_int_currency_raises(self):
        with self.assertRaises(TypeError):
            self.handler.offer(self.char1, currency="500")

    def test_bool_currency_raises(self):
        # bool subclasses int, so without the explicit check `currency=True`
        # would put one Copper on the table.
        with self.assertRaises(TypeError):
            self.handler.offer(self.char1, currency=True)

    def test_negative_currency_raises(self):
        with self.assertRaises(ValueError):
            self.handler.offer(self.char1, currency=-1)

    def test_a_rejected_currency_never_reaches_the_field(self):
        self.handler.offer(self.char1, currency=500)
        with self.assertRaises(ValueError):
            self.handler.offer(self.char1, currency=-1)
        self.assertEqual(self.handler.part_a_currency, 500)

    def test_teardown_zeroes_the_coin_fields(self):
        # Nothing to refund -- no purse was ever touched -- but a handler
        # someone still holds a reference to must read as empty rather than as
        # a live promise of coin.
        self.handler.offer(self.char1, currency=500)
        self.handler.finish(force=True)
        self.assertEqual(self.handler.part_a_currency, 0)

    def test_a_forced_teardown_moves_no_money(self):
        # Question 4 of the component, asserted rather than assumed: decline,
        # timeout and disconnect all land on force=True.
        self.handler.offer(self.char1, currency=500)
        self.handler.finish(force=True)
        self.assertEqual(self.char1.currency.value, self.START_BALANCE)
        self.assertEqual(self.char2.currency.value, self.START_BALANCE)


class TestGlobalsPatchIsInstalled(EvenniaTest):
    """
    The patch layer's single point of failure. Every corrected class reaches
    play only because the contrib resolves these names from its own module
    globals at call time; a dropped assignment is a silent no-op that no other
    test in this file would notice, because they all import our classes directly.
    """

    def test_every_swap_is_in_place(self):
        self.assertIs(barter_module.TradeTimeout, PWTradeTimeout)
        self.assertIs(barter_module.TradeHandler, PWTradeHandler)
        self.assertIs(barter_module.CmdOffer, CmdPWOffer)
        self.assertIs(barter_module.CmdAccept, CmdPWAccept)
        self.assertIs(barter_module.CmdDecline, CmdPWDecline)
        self.assertIs(barter_module.CmdEvaluate, CmdPWEvaluate)
        self.assertIs(barter_module.CmdStatus, CmdPWStatus)

    def test_the_trade_cmdset_is_built_from_our_classes(self):
        # One level closer to reality than the assertions above: CmdsetTrade is
        # what a player actually gets, and it resolves the names at
        # at_cmdset_creation time.
        keys = {type(cmd) for cmd in CmdsetTrade().commands}
        for cls in (CmdPWOffer, CmdPWAccept, CmdPWDecline, CmdPWEvaluate, CmdPWStatus):
            self.assertIn(cls, keys)
