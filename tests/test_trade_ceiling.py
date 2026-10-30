"""
Tests for W5.1's sixth site: a trade never completes above the ceiling.

Weight and Encumbrance, Task W5.1 (docs/PolishedWorld_Weight_Decomposition.md,
Rev 9 Q4-Q5). Upstream's finish() moves offers by assignment (barter.py:369,
371) and runs no hook, so the ceiling is a third check in
`world/barter.py::_stale_offer_reason`, before anything moves. The sum after
the swap is the reader's: `world.encumbrance.enc_after_trade`.

WHAT EACH CLASS PUTS PRESSURE ON
--------------------------------
* TestEncAfterTrade -- the reader: every leaving object is left out (not just
  the first), arriving objects count with their contents, and the
  twenty-to-one rule runs once over the merged count.
* TestTradeCeiling -- finish(): either party crossing cancels the whole trade
  with one line to both naming who; below the ceiling it completes; a trade
  that lightens a party already above the ceiling completes ("and above the
  sum before"); twenty items at enc 0 are read through the merged walk.
* TestAcceptCommandCeiling -- the other caller, CmdPWAccept, gets the check
  too and confirms nothing.

tests/test_barter_currency.py (60 tests) is the regression for trades the
ceiling does not touch.
"""

from evennia import create_object
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from tests.test_barter_currency import TradeFixtureMixin
from tests.test_currency import LedgerIsolationMixin
from tests.test_work_command import captured_messages
from world.barter import CmdPWAccept
from world.encumbrance import OVERLOAD_FACTOR, carried_enc, enc_after_trade

CHARACTER = "typeclasses.characters.Character"
OBJ = "typeclasses.objects.Object"
CEILING = OVERLOAD_FACTOR * 20   # the default character's limit is 20


def _make(location, key="thing", enc=None):
    obj = create_object(OBJ, key=key, location=location)
    if enc is not None:
        obj.db.enc = enc
    return obj


class TestEncAfterTrade(EvenniaTest):
    """`enc_after_trade(holder, leaving, arriving)` -- the arithmetic only."""

    character_typeclass = CHARACTER

    def test_every_leaving_object_is_left_out_and_arrivals_are_added(self):
        _make(self.char1, key="tcload", enc=10)
        a = _make(self.char1, key="tca", enc=2)
        b = _make(self.char1, key="tcb", enc=3)
        c = _make(self.char2, key="tcc", enc=4)
        self.assertEqual(enc_after_trade(self.char1, [a, b], [c]), 10 + 4)

    def test_an_arriving_container_counts_with_its_contents(self):
        sack = _make(self.char2, key="tcsack", enc=1)
        _make(sack, key="tcstone", enc=2)
        self.assertEqual(enc_after_trade(self.char1, [], [sack]), 3)

    def test_twenty_at_zero_are_merged_across_holder_and_arrivals(self):
        for i in range(10):
            _make(self.char1, key=f"tcmine{i}", enc=0)
        theirs = [_make(self.char2, key=f"tctheirs{i}", enc=0) for i in range(10)]
        self.assertEqual(enc_after_trade(self.char1, [], theirs), 1)

    def test_nothing_moves(self):
        a = _make(self.char1, key="tca", enc=2)
        c = _make(self.char2, key="tcc", enc=4)
        enc_after_trade(self.char1, [a], [c])
        self.assertEqual((a.location, c.location), (self.char1, self.char2))


class _TradeCeilingFixture(TradeFixtureMixin, LedgerIsolationMixin):
    def load(self, char, total, zeros=0):
        _make(char, key="tcload", enc=total)
        for i in range(zeros):
            _make(char, key=f"tcpebble{i}", enc=0)

    def line(self, *names):
        return f"Trade cancelled: {' and '.join(n.key for n in names)} cannot carry that much."

    def complete_and_listen(self):
        with captured_messages(self.char1) as one, captured_messages(self.char2) as two:
            self._complete()
        return one, two


class TestTradeCeiling(_TradeCeilingFixture, EvenniaCommandTest):
    """finish(): the ceiling as the third stale-offer check."""

    def test_a_trade_that_puts_the_receiver_over_moves_nothing_and_tells_both(self):
        self.load(self.char2, CEILING)
        anvil = _make(self.char1, key="anvil", enc=2)
        pebble = _make(self.char2, key="pebble", enc=0)
        self.handler.offer(self.char1, anvil)
        self.handler.offer(self.char2, pebble)
        one, two = self.complete_and_listen()
        self.assertEqual((anvil.location, pebble.location), (self.char1, self.char2))
        self.assertIn(self.line(self.char2), one)
        self.assertIn(self.line(self.char2), two)

    def test_the_other_party_is_checked_too(self):
        self.load(self.char1, CEILING)
        anvil = _make(self.char2, key="anvil", enc=2)
        pebble = _make(self.char1, key="pebble", enc=0)
        self.handler.offer(self.char1, pebble)
        self.handler.offer(self.char2, anvil)
        one, two = self.complete_and_listen()
        self.assertEqual((anvil.location, pebble.location), (self.char2, self.char1))
        self.assertIn(self.line(self.char1), one)
        self.assertIn(self.line(self.char1), two)

    def test_up_to_the_ceiling_the_trade_completes(self):
        self.load(self.char2, CEILING - 2)
        anvil = _make(self.char1, key="anvil", enc=2)
        self.handler.offer(self.char1, anvil)
        self.handler.offer(self.char2, currency=100)
        self._complete()
        self.assertEqual(anvil.location, self.char2)
        self.assertEqual(carried_enc(self.char2), CEILING)

    def test_a_trade_that_lightens_a_party_above_the_ceiling_completes(self):
        # 45 + 5 = 50 before; 45 after: still above 40, but lighter.
        self.load(self.char1, CEILING + 5)
        anvil = _make(self.char1, key="anvil", enc=5)
        pebble = _make(self.char2, key="pebble", enc=0)
        self.handler.offer(self.char1, anvil)
        self.handler.offer(self.char2, pebble)
        self._complete()
        self.assertEqual((anvil.location, pebble.location), (self.char2, self.char1))

    def test_twenty_items_at_zero_are_read_through_the_merged_walk(self):
        # 40 and 19 pebbles is 40; one feather more is the twentieth item.
        self.load(self.char2, CEILING, zeros=19)
        self.assertEqual(carried_enc(self.char2), CEILING)
        feather = _make(self.char1, key="feather", enc=0)
        self.handler.offer(self.char1, feather)
        self.handler.offer(self.char2, currency=100)
        one, two = self.complete_and_listen()
        self.assertEqual(feather.location, self.char1)
        self.assertIn(self.line(self.char2), two)

    def test_a_party_giving_two_heavy_items_is_read_without_both(self):
        # 36 + 2 + 2 = 40; giving both for a 3 leaves 39.
        self.load(self.char1, CEILING - 4)
        a = _make(self.char1, key="tca", enc=2)
        b = _make(self.char1, key="tcb", enc=2)
        c = _make(self.char2, key="tcc", enc=3)
        self.handler.offer(self.char1, a, b)
        self.handler.offer(self.char2, c)
        self._complete()
        self.assertEqual(c.location, self.char1)
        self.assertEqual(carried_enc(self.char1), CEILING - 1)


class TestAcceptCommandCeiling(_TradeCeilingFixture, EvenniaCommandTest):
    """CmdPWAccept: the completing accept cancels instead of confirming."""

    def test_the_completing_accept_cancels_and_moves_nothing(self):
        self.load(self.char1, CEILING)
        anvil = _make(self.char2, key="anvil", enc=2)
        self.handler.offer(self.char1, currency=100)
        self.handler.offer(self.char2, anvil)
        self.handler.part_b_accepted = True
        returned = self.call(CmdPWAccept(), "", caller=self.char1)
        self.assertIn(self.line(self.char1), returned)
        self.assertNotIn("You accept the offer", returned)
        self.assertEqual(anvil.location, self.char2)
