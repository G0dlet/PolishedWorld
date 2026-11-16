"""
A trade under way names the other party as each side knows them. Names,
Task NM-T13 (docs/PolishedWorld_Combat_Decomposition.md, NM15; OQ-NM4 split
the slice's `trade` in two: this task is the trade cmdset, NM-T13b the
`trade` command that starts one).

Every line the trade's commands send to the other party, or about them,
named a party by `.key`: the contrib's `parse` (`str_other`), `accept`,
`end trade`, and the project's `decline`, `status` and stale-offer line.
Each now names them as the reader knows them (lock 3 A: the reader's own
side by `get_display_name`, which for oneself is one's own key), with a
capital where the name starts a sentence (`names.line_start`), and without
the contrib's `|c` on a speaker (lock 2 A; NM11).

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
char1 and char2 trade, both connected (char2 through `SecondSessionMixin`:
a party with no session is a statue, named *stone statue of ...*). Each
test runs twice: as strangers, who read each
other's short description, and as recognisers holding lower-case labels
(char2 knows char1 as *mia of the Ford*, char1 knows char2 as *bob*), the
reader for whom a capital and a plain format differ. Neither may read the
other's key. A line restored to `.key` fails the stranger; one asking for
the name with no looker, or for the wrong looker, fails the recogniser.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_trade
"""

from evennia import create_object
from evennia.contrib.game_systems.barter.barter import CmdsetTrade
from evennia.utils import ansi
from evennia.utils.test_resources import EvenniaCommandTest

from tests.names_fixture import describe
from tests.test_barter_currency import TradeFixtureMixin
from tests.test_currency import LedgerIsolationMixin
from tests.test_currency_commands import SecondSessionMixin
from tests.test_work_command import captured_messages
from world.barter import (
    CmdPWAccept,
    CmdPWDecline,
    CmdPWFinish,
    CmdPWOffer,
    CmdPWStatus,
    _stale_offer_reasons,
)
from world.encumbrance import OVERLOAD_FACTOR

OBJ = "typeclasses.objects.Object"

# As each reader names the other: (stranger, recogniser).
ONE_SEEN_BY_TWO = ("a weathered woman", "mia of the Ford")
TWO_SEEN_BY_ONE = ("a broad-shouldered man", "bob")


def _cap(name):
    return name[:1].upper() + name[1:]


class TestTradeNamesStrangers(
    SecondSessionMixin, TradeFixtureMixin, LedgerIsolationMixin, EvenniaCommandTest
):
    """char1 and char2 in a started trade, as strangers; `known` picks the readers."""

    known = False

    def setUp(self):
        super().setUp()
        describe(self.char1, self.char2)
        if self.known:
            self.char2.recog.add(self.char1, ONE_SEEN_BY_TWO[1])
            self.char1.recog.add(self.char2, TWO_SEEN_BY_ONE[1])
        pick = 1 if self.known else 0
        self.one = ONE_SEEN_BY_TWO[pick]   # char1, as char2 reads it
        self.two = TWO_SEEN_BY_ONE[pick]   # char2, as char1 reads it

    def heard(self, cmd, args, caller, listener):
        """Run `cmd`; (what the caller read, what the listener read), plain."""
        with captured_messages(listener) as raw:
            said = self.call(cmd, args, caller=caller)
        self.raw = raw
        return ansi.strip_ansi(said or ""), [ansi.strip_ansi(line) for line in raw]

    def assert_no_key(self, lines, key):
        for line in lines:
            self.assertNotIn(key, line)

    # -- offer: parse's str_other ------------------------------------------

    def test_an_offer_names_the_offerer(self):
        _, two = self.heard(CmdPWOffer(), "5 silver", self.char1, self.char2)
        self.assertEqual(two, [f"{_cap(self.one)}:s trade action: They offer 5 Silver in coin"])
        _, one = self.heard(CmdPWOffer(), "5 silver", self.char2, self.char1)
        self.assertEqual(one, [f"{_cap(self.two)}:s trade action: They offer 5 Silver in coin"])

    def test_an_offer_with_words_names_the_speaker_without_colour(self):
        _, two = self.heard(CmdPWOffer(), "5 silver : a fair price", self.char1, self.char2)
        self.assertEqual(
            two, [f'{_cap(self.one)} says, "a fair price"\n  [They offer 5 Silver in coin]']
        )
        self.assertNotIn("|c", self.raw[0])

    def test_words_with_a_percent_sign_do_not_break_the_line(self):
        _, two = self.heard(CmdPWOffer(), "5 silver : 100% fair", self.char1, self.char2)
        self.assertEqual(
            two, [f'{_cap(self.one)} says, "100% fair"\n  [They offer 5 Silver in coin]']
        )

    # -- accept --------------------------------------------------------------

    def test_a_one_sided_accept(self):
        self._offer("3 silver", caller=self.char1)
        self._offer("2 silver", caller=self.char2)
        mine, two = self.heard(CmdPWAccept(), "", self.char1, self.char2)
        self.assertIn(f"You accept the offer. {_cap(self.two)} must now also accept.", mine)
        self.assertEqual(
            two,
            [f"{_cap(self.one)}:s trade action: {_cap(self.one)} accepts the offer. "
             "You must now also accept."],
        )
        self.assert_no_key([mine], "Char2")

    def test_the_accept_that_makes_the_deal(self):
        self._offer("3 silver", caller=self.char1)
        self._offer("2 silver", caller=self.char2)
        self.handler.part_b_accepted = True
        _, two = self.heard(CmdPWAccept(), "", self.char1, self.char2)
        self.assertIn(
            f"{_cap(self.one)}:s trade action: {_cap(self.one)} accepts the deal. "
            "Deal is made and goods changed hands.",
            two,
        )

    # -- decline -------------------------------------------------------------

    def test_a_decline(self):
        self._offer("3 silver", caller=self.char1)
        self._offer("2 silver", caller=self.char2)
        _, two = self.heard(CmdPWDecline(), "", self.char1, self.char2)
        self.assertEqual(
            two,
            [f"{_cap(self.one)}:s trade action: {_cap(self.one)} declines the current offer."],
        )

    def test_a_decline_after_an_accept(self):
        self._offer("3 silver", caller=self.char1)
        self._offer("2 silver", caller=self.char2)
        self.handler.part_b_accepted = True
        _, one = self.heard(CmdPWDecline(), "", self.char2, self.char1)
        self.assertEqual(
            one,
            [f"{_cap(self.two)}:s trade action: {_cap(self.two)} changes their mind, "
             "declining the current offer."],
        )

    # -- end trade -----------------------------------------------------------

    def test_ending_the_trade(self):
        _, two = self.heard(CmdPWFinish(), "", self.char1, self.char2)
        self.assertEqual(
            two,
            [f"{_cap(self.one)}:s trade action: {_cap(self.one)} aborted trade. "
             "No deal was made."],
        )
        self.assertIsNone(self.char1.ndb.tradehandler)

    # -- status (lock 3 A: one's own side by one's own key) ------------------

    def test_status_as_each_side_reads_it(self):
        mine, _ = self.heard(CmdPWStatus(), "", self.char1, self.char2)
        self.assertIn("Offered by Char:", mine)
        self.assertIn(f"Offered by {self.two}:", mine)
        self.assertIn(f"Char agreed: No, {self.two} agreed: No", mine)
        theirs, _ = self.heard(CmdPWStatus(), "", self.char2, self.char1)
        self.assertIn(f"Offered by {self.one}:", theirs)
        self.assertIn("Offered by Char2:", theirs)
        self.assertIn(f"{_cap(self.one)} agreed: No, Char2 agreed: No", theirs)
        self.assertNotIn("Char:", theirs)

    # -- the stale offer: the ceiling names who, per reader ------------------

    def test_the_ceiling_line_names_who_as_each_reads_it(self):
        create_object(OBJ, key="tcload", location=self.char2).db.enc = OVERLOAD_FACTOR * 20
        anvil = create_object(OBJ, key="anvil", location=self.char1)
        anvil.db.enc = 2
        self.handler.offer(self.char1, anvil)
        reasons = _stale_offer_reasons(self.handler)
        self.assertEqual(
            reasons,
            {
                self.char1: f"Trade cancelled: {self.two} cannot carry that much.",
                self.char2: "Trade cancelled: Char2 cannot carry that much.",
            },
        )

    def test_a_stale_item_names_nobody(self):
        sword = self._item("iron sword")
        self.handler.offer(self.char1, sword)
        sword.location = self.room1
        reasons = _stale_offer_reasons(self.handler)
        self.assertEqual(
            set(reasons.values()), {"Trade cancelled: an offered item is no longer available."}
        )
        self.assertEqual(set(reasons), {self.char1, self.char2})

    def test_an_honest_deal_has_no_reasons(self):
        self.assertIsNone(_stale_offer_reasons(self.handler))

    def test_the_trade_cmdset_ends_a_trade_with_the_project_command(self):
        # The contrib's CmdsetTrade resolves CmdFinish from its module's
        # globals when a trade starts; world/barter.py swaps it.
        ending = [cmd for cmd in CmdsetTrade().commands if cmd.key == "end trade"]
        self.assertEqual([type(cmd) for cmd in ending], [CmdPWFinish])


class TestTradeNamesKnown(TestTradeNamesStrangers):
    """The same, read by recognisers holding lower-case labels."""

    known = True
