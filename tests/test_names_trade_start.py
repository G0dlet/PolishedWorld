"""
The `trade` command names each party as the other knows them, and its
answer line gives a name the invitee can type. Names, Task NM-T13b
(docs/PolishedWorld_Combat_Decomposition.md, NM15; OQ-NM4 split `trade`:
NM-T13 took the trade under way, this task the command that starts one).

The contrib's `CmdTrade.func` named both parties by `.key` in thirteen
lines and told the invitee to type `trade <inviter's key> accept`. The
project's `CmdPWTrade.func` is now its own (lock 2 A of NM-T13: no `|c` on
a speaker; a capital where a name starts a sentence), with three contrib
faults fixed on the way (NM-T13b locks 2-4 A):

- `trade <someone> accept` with no proposal from them raised
  AttributeError (`None.join`); it now says there is none;
- the inviter could not take an invitation back with `trade <them>
  decline`, as the help says it can (the branch tested `part_b == caller`,
  never true for the inviter); now it can;
- `accept`/`decline` were found as substrings, so inviting someone one calls
  *the acceptor* was read as an accept (and crashed). Only the last word
  counts now.

WHAT EACH CLASS PUTS PRESSURE ON
--------------------------------
- TestNameToTypeHere -- `names.name_to_type_here` (lock 1 C): one word when
  the looker's own search with it finds only that character, else the whole
  short description; a recog whole.
- TestTradeStartStrangers / TestTradeStartKnown -- every branch's lines as
  each party reads them, as strangers and as recognisers holding lower-case
  labels (char2 knows char1 as *mia of the Ford*, char1 knows char2 as
  *bob*); the invitee types the printed answer back.
- TestTradeFaults -- the three contrib faults.

char2 is connected through `SecondSessionMixin`, its Developer permission
taken back: a Builder finds anyone by key (rpsystem.py:1339, :1346), which
would let a key in the answer line pass.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_trade_start
"""

from evennia import create_object
from evennia.utils import ansi
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from tests.names_fixture import describe
from tests.test_currency_commands import SecondSessionMixin
from tests.test_work_command import captured_messages
from world import names
from world.barter import CmdPWTrade

CHARACTER = "typeclasses.characters.Character"
ONE_SEEN_BY_TWO = ("a weathered woman", "mia of the Ford")
TWO_SEEN_BY_ONE = ("a broad-shouldered man", "bob")
ONE_TYPED_BY_TWO = ("weathered", "mia of the Ford")
TWO_TYPED_BY_ONE = ("broad-shouldered", "bob")


def _cap(name):
    return name[:1].upper() + name[1:]


class TestNameToTypeHere(EvenniaTest):
    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        describe(self.char1, self.char2)

    def test_one_word_when_it_finds_only_them(self):
        self.assertEqual(names.name_to_type_here(self.char2, self.char1), "weathered")

    def test_the_whole_description_when_the_word_finds_more(self):
        other = create_object(CHARACTER, key="Char3", location=self.room1, home=self.room1)
        other.sdesc.add("a weathered man")
        typed = names.name_to_type_here(self.char2, self.char1)
        self.assertEqual(typed, "a weathered woman")
        self.assertEqual(self.char2.search(typed, quiet=True), [self.char1])

    def test_a_recog_whole(self):
        self.char2.recog.add(self.char1, "mia of the Ford")
        self.assertEqual(names.name_to_type_here(self.char2, self.char1), "mia of the Ford")

    def test_the_word_it_gives_is_found(self):
        typed = names.name_to_type_here(self.char2, self.char1)
        self.assertEqual(self.char2.search(typed, quiet=True), [self.char1])


class _Start(SecondSessionMixin, EvenniaCommandTest):
    character_typeclass = CHARACTER
    known = False

    def setUp(self):
        super().setUp()
        self.account2.permissions.remove("Developer")
        self.assertFalse(self.char2.permissions.check("Builder"))
        describe(self.char1, self.char2)
        if self.known:
            self.char2.recog.add(self.char1, ONE_SEEN_BY_TWO[1])
            self.char1.recog.add(self.char2, TWO_SEEN_BY_ONE[1])
        pick = 1 if self.known else 0
        self.one, self.two = ONE_SEEN_BY_TWO[pick], TWO_SEEN_BY_ONE[pick]
        self.one_typed, self.two_typed = ONE_TYPED_BY_TWO[pick], TWO_TYPED_BY_ONE[pick]

    def tearDown(self):
        for char in (self.char1, self.char2):
            handler = char.ndb.tradehandler
            if handler:
                handler.finish(force=True)
        super().tearDown()

    def run_trade(self, args, caller, listener):
        """`trade <args>`; (caller's lines, listener's lines), plain."""
        with captured_messages(listener) as raw:
            said = self.call(CmdPWTrade(), args, caller=caller)
        self.raw = raw
        return ansi.strip_ansi(said or ""), [ansi.strip_ansi(line) for line in raw]

    def invite(self, emote=""):
        return self.run_trade(f"{self.two_typed}{emote}", self.char1, self.char2)

    def answer_line(self, heard):
        (line,) = [line for line in heard if "wants to trade with you" in line]
        return line.split("Use trade ", 1)[1].split(" [:emote]", 1)[0]


class TestTradeStartStrangers(_Start):

    def test_the_invitation(self):
        mine, theirs = self.invite()
        self.assertEqual(mine, f"You ask to trade with {self.two}. They need to accept within 60 secs.")
        self.assertEqual(
            theirs,
            [f"{_cap(self.one)} wants to trade with you. Use trade {self.one_typed} "
             "accept/decline [:emote] to answer (within 60 secs)."],
        )
        self.assertNotIn("Char", theirs[0])

    def test_the_answer_typed_as_printed_starts_the_trade(self):
        _, theirs = self.invite()
        # The line offers `accept/decline`; the invitee picks one.
        typed = self.answer_line(theirs).replace("accept/decline", "accept")
        self.assertEqual(typed, f"{self.one_typed} accept")
        mine, heard_by_one = self.run_trade(typed, self.char2, self.char1)
        self.assertTrue(self.char1.ndb.tradehandler.trade_started)
        self.assertEqual(mine, f"You start to trade with {self.one}. See trade help for aid.")
        self.assertEqual(
            heard_by_one, [f"{_cap(self.two)} starts to trade with you. See trade help for aid."]
        )

    def test_inviting_back_joins_the_trade(self):
        self.invite()
        mine, heard_by_one = self.run_trade(self.one_typed, self.char2, self.char1)
        self.assertTrue(self.char1.ndb.tradehandler.trade_started)
        self.assertEqual(mine, f"You start to trade with {self.one}. See trade help for aid.")
        self.assertEqual(
            heard_by_one, [f"{_cap(self.two)} starts to trade with you. See trade help for aid."]
        )

    def test_an_invitation_with_words_names_the_speaker_without_colour(self):
        mine, theirs = self.invite(" : a fair price")
        self.assertTrue(mine.startswith('You say, "a fair price"\n  You ask to trade with'))
        self.assertTrue(
            theirs[0].startswith(
                f'{_cap(self.one)} says, "a fair price"\n  {_cap(self.one)} wants to trade'
            )
        )
        self.assertNotIn("|c", self.raw[0])

    def test_the_invitee_declines(self):
        self.invite()
        mine, heard_by_one = self.run_trade(f"{self.one_typed} decline", self.char2, self.char1)
        self.assertEqual(mine, f"You decline trade with {self.one}.")
        self.assertEqual(heard_by_one, [f"{_cap(self.two)} declines the trade"])
        self.assertIsNone(self.char1.ndb.tradehandler)

    def test_the_inviter_takes_it_back(self):  # lock 3 A
        self.invite()
        mine, theirs = self.run_trade(f"{self.two_typed} decline", self.char1, self.char2)
        self.assertEqual(mine, f"You aborted the trade attempt with {self.two}.")
        self.assertEqual(theirs, [f"{_cap(self.one)} aborted trade attempt with you."])
        self.assertIsNone(self.char1.ndb.tradehandler)

    def test_already_in_a_trade(self):
        self.invite()
        self.run_trade(f"{self.one_typed} accept", self.char2, self.char1)
        mine, _ = self.run_trade(self.two_typed, self.char1, self.char2)
        self.assertEqual(
            mine, f"You are already in trade with {self.two}. You need to end trade first."
        )
        theirs_own, _ = self.run_trade(f"{self.one_typed} accept", self.char2, self.char1)
        self.assertEqual(
            theirs_own, f"You are already in trade with {self.one}. You need to end that first."
        )

    def test_already_inviting(self):
        self.invite()
        mine, _ = self.run_trade(self.two_typed, self.char1, self.char2)
        self.assertEqual(
            mine,
            f"You are already trying to initiate trade with {self.two}. "
            "You need to decline that trade first.",
        )


class TestTradeStartKnown(TestTradeStartStrangers):
    """The same, read by recognisers holding lower-case labels."""

    known = True


class TestTradeFaults(_Start):
    """The contrib faults fixed on the way (NM-T13b locks 2-4 A)."""

    def test_accepting_with_no_proposal_says_so(self):  # lock 2 A
        mine, _ = self.run_trade(f"{self.two_typed} accept", self.char1, self.char2)
        self.assertEqual(mine, "No trade proposal to accept.")
        self.assertIsNone(self.char1.ndb.tradehandler)

    def test_declining_with_no_proposal_says_so(self):
        mine, _ = self.run_trade(f"{self.two_typed} decline", self.char1, self.char2)
        self.assertEqual(mine, "No trade proposal to decline.")

    def test_a_name_with_accept_in_it_is_a_name(self):  # lock 4 A
        self.char1.recog.add(self.char2, "the acceptor")
        mine, _ = self.run_trade("the acceptor", self.char1, self.char2)
        self.assertTrue(mine.startswith("You ask to trade with the acceptor."))
        self.assertEqual(self.char1.ndb.tradehandler.part_b, self.char2)

    def test_a_name_with_decline_in_it_accepts(self):
        self.char2.recog.add(self.char1, "the declined one")
        self.invite()
        self.run_trade("the declined one accept", self.char2, self.char1)
        self.assertTrue(self.char1.ndb.tradehandler.trade_started)

    def test_only_the_last_word_counts(self):
        mine, _ = self.run_trade(f"{self.two_typed} accept now", self.char1, self.char2)
        self.assertIn("Could not find", mine)
        self.assertIsNone(self.char1.ndb.tradehandler)

    def test_already_in_a_trade_names_the_partner_not_the_one_typed(self):
        third = create_object(CHARACTER, key="Char3", location=self.room1, home=self.room1)
        third.sdesc.add("a freckled youth")
        self.invite()
        self.run_trade(f"{self.one_typed} accept", self.char2, self.char1)
        mine, _ = self.run_trade("freckled", self.char1, self.char2)
        self.assertEqual(
            mine, f"You are already in trade with {self.two}. You need to end trade first."
        )

    def test_yourself(self):
        mine, _ = self.run_trade("me", self.char1, self.char2)
        self.assertEqual(mine, "You play trader with yourself.")
