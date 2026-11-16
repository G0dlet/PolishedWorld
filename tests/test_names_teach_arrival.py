"""
The lesson's offer names the teacher as the student knows them, the direct
lines start with a capital, and a newcomer's arrival is seen. Names, Task
NM-T12 (docs/PolishedWorld_Combat_Decomposition.md; the Names note's K5,
UP15; Arrival AV8; the Newcomer note's §15).

WHAT EACH CLASS PUTS PRESSURE ON
--------------------------------
- TestNameToType -- `world.names.name_to_type`, alone (lock 1 A): a recog
  whole and as written; else the first word of the short description after
  an article, without punctuation at its edges; else the whole description.
  Each word it gives finds the character through the project's search.
- TestTeachOffer -- the offer as the student reads it, for a stranger and
  for a recogniser with a lower-case label, and the line typed back as
  printed teaches the recipe. The key in the offer fails the stranger
  (NMM19); the recog ignored fails the recogniser.
- TestTeachLines -- the lesson's direct lines that start with a name start
  with `$You()`'s capital (lock 2 A): read by someone holding a lower-case
  label, the one reader for whom a capital and a plain format differ.
- TestPayLines -- the same for `pay`'s two lines that can be read so.
- TestArrivalLine -- `arrival.arrive` tells the room it enters, through
  `$You()`, after the move: a stranger reads the short description, a
  recogniser the label, the newcomer and the room it left nothing; no line
  when the character already stands there (Arrival's rule for the push).

The student is char2 with a real second session (`SecondSessionMixin`): the
teach path re-checks `has_account`, and a patched property would test the
patch. Its Developer permission is taken back after the puppet: a Builder
finds anyone by key, which would let the key in the offer pass.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_teach_arrival
"""

import time
from unittest import mock

from evennia import create_object
from evennia.utils import ansi
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.crafting_commands import CmdLearn, CmdTeach
from commands.currency_commands import CmdPay
from tests.names_fixture import describe, shown
from tests.test_currency import LedgerIsolationMixin
from tests.test_currency_commands import SecondSessionMixin
from world import arrival, names, seed_data
from world.recipe_mastery import MASTERY_TRANSMIT_THRESHOLD
from world.seeding import find_seeded, seed_world

CHARACTER = "typeclasses.characters.Character"
CLOTH = "cloth"               # requires_knowledge=True (test_knowledge.py)
LABEL = "mia of the Ford"     # a lower-case recog of char1
SEEN_BY_LABEL = "Mia of the Ford"
STUDENT_LABEL = "bob"         # char1's recog of char2


def _lines(char):
    """Every line `char.msg` was given, colour stripped; both call forms."""
    out = []
    for call in char.msg.call_args_list:
        text = call.kwargs.get("text", call.args[0] if call.args else None)
        text = text[0] if isinstance(text, tuple) else text
        if text:
            out.append(ansi.strip_ansi(str(text)))
    return out


class TestNameToType(EvenniaTest):
    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        describe(self.char1, self.char2)

    def test_a_recog_whole_and_as_written(self):
        self.char2.recog.add(self.char1, LABEL)
        self.assertEqual(names.name_to_type(self.char2, self.char1), LABEL)

    def test_a_stranger_gets_the_first_word_after_the_article(self):
        self.assertEqual(names.name_to_type(self.char2, self.char1), "weathered")
        self.assertEqual(names.name_to_type(self.char1, self.char2), "broad-shouldered")

    def test_punctuation_and_a_missing_article(self):
        for sdesc, word in (
            ("a scarred, grey-haired man", "scarred"),
            ("The tall stranger", "tall"),
            ("an old woman", "old"),
            ("tall, dark figure", "tall"),
        ):
            with self.subTest(sdesc=sdesc):
                self.char1.sdesc.add(sdesc)
                self.assertEqual(names.name_to_type(self.char2, self.char1), word)

    def test_nothing_but_an_article_gives_the_whole_description(self):
        self.char1.sdesc.add("the one")
        self.assertEqual(names.name_to_type(self.char2, self.char1), "one")
        self.char1.sdesc.add("a")
        self.assertEqual(names.name_to_type(self.char2, self.char1), "a")

    def test_the_word_finds_the_character(self):
        # commands/crafting_commands.py:1457 -- the student's search, over the
        # teacher alone.
        stranger = names.name_to_type(self.char2, self.char1)
        self.assertEqual(
            self.char2.search(stranger, candidates=[self.char1], quiet=True), [self.char1]
        )
        self.char2.recog.add(self.char1, LABEL)
        known = names.name_to_type(self.char2, self.char1)
        self.assertEqual(
            self.char2.search(known, candidates=[self.char1], quiet=True), [self.char1]
        )

    def test_the_key_is_never_given(self):
        self.assertNotIn("Char", names.name_to_type(self.char2, self.char1))


class _Lesson(SecondSessionMixin, EvenniaCommandTest):
    """char1 can teach cloth; char2, connected, is the student; both listen."""

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        # SecondSessionMixin grants Developer so the puppet lock passes; the
        # session stays once puppeted. Taken back here, because the contrib's
        # search lets a Builder find anyone by key (rpsystem.py:1339, :1346):
        # a student with it would find the teacher by whatever word is printed.
        self.account2.permissions.remove("Developer")
        self.assertFalse(self.char2.permissions.check("Builder"))
        self.assertTrue(self.char2.has_account)
        describe(self.char1, self.char2)
        self.char1.learn_recipe(CLOTH)
        self.char1.recipe_mastery.add(CLOTH, MASTERY_TRANSMIT_THRESHOLD)
        self.char1.msg = mock.Mock()
        self.char2.msg = mock.Mock()

    def offer(self):
        """char1 offers cloth to char2; the offer line char2 read."""
        self.call(CmdTeach(), f"{CLOTH} to {shown(self.char2)}", caller=self.char1)
        (line,) = [line for line in _lines(self.char2) if "offers to teach you" in line]
        return line


class TestTeachOffer(_Lesson):

    def test_a_stranger_reads_the_description_and_a_word_to_type(self):
        line = self.offer()
        self.assertEqual(
            line,
            f"A weathered woman offers to teach you the {CLOTH} recipe. "
            f"Answer with learn {CLOTH} from weathered within 60s.",
        )

    def test_a_recogniser_reads_the_label_and_types_it(self):
        self.char2.recog.add(self.char1, LABEL)
        line = self.offer()
        self.assertEqual(
            line,
            f"{SEEN_BY_LABEL} offers to teach you the {CLOTH} recipe. "
            f"Answer with learn {CLOTH} from {LABEL} within 60s.",
        )

    def _type_back(self, line):
        typed = line.split("Answer with learn ", 1)[1].rsplit(" within ", 1)[0]
        self.call(CmdLearn(), typed, caller=self.char2)
        return self.char2.knows_recipe(CLOTH)

    def test_the_stranger_types_the_line_as_printed(self):
        self.assertTrue(self._type_back(self.offer()))

    def test_the_recogniser_types_the_line_as_printed(self):
        self.char2.recog.add(self.char1, LABEL)
        self.assertTrue(self._type_back(self.offer()))


class TestTeachLines(_Lesson):
    """The lesson's direct lines that start with a name (lock 2 A)."""

    def setUp(self):
        super().setUp()
        self.char2.recog.add(self.char1, LABEL)
        self.char1.recog.add(self.char2, STUDENT_LABEL)

    def _offered(self):
        self.char2.ndb.pending_teach = (self.char1, CLOTH, time.time() + 60)

    def test_a_thing_is_not_someone_you_can_teach(self):  # :1235
        create_object("typeclasses.objects.Object", key="rock", location=self.room1)
        said = self.call(CmdTeach(), f"{CLOTH} to rock", caller=self.char1)
        self.assertIn("Rock isn't someone you can teach.", ansi.strip_ansi(said))

    def test_the_wrong_recipe(self):  # :1478
        self._offered()
        said = self.call(CmdLearn(), f"leather from {LABEL}", caller=self.char2)
        self.assertIn(f"{SEEN_BY_LABEL} offered to teach you {CLOTH}, not leather.",
                      ansi.strip_ansi(said))

    def test_a_teacher_who_can_no_longer_teach(self):  # :1502
        self._offered()
        with mock.patch("commands.crafting_commands._can_transmit", return_value=False):
            said = self.call(CmdLearn(), f"{CLOTH} from {LABEL}", caller=self.char2)
        self.assertIn(f"{SEEN_BY_LABEL} can't teach you that.", ansi.strip_ansi(said))

    def test_a_student_who_already_knows(self):  # :1517
        self.char2.learn_recipe(CLOTH)
        self._offered()
        self.call(CmdLearn(), f"{CLOTH} from {LABEL}", caller=self.char2)
        self.assertIn(f"Bob already knows {CLOTH}.", _lines(self.char1))

    def test_the_lesson(self):  # :1534
        self._offered()
        said = self.call(CmdLearn(), f"{CLOTH} from {LABEL}", caller=self.char2)
        self.assertIn(
            f"{SEEN_BY_LABEL} walks you through the {CLOTH} recipe until it sticks. "
            "You have learned it.",
            ansi.strip_ansi(said),
        )


class TestPayLines(SecondSessionMixin, LedgerIsolationMixin, EvenniaCommandTest):
    """`pay`'s direct lines that start with a name (lock 2 A, with the coin)."""

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        describe(self.char1, self.char2)
        self.char1.currency.add(1_000, source="admin_correction")

    def test_a_thing_has_no_use_for_coin(self):  # currency_commands.py:264
        create_object("typeclasses.objects.Object", key="rock", location=self.room1)
        said = self.call(CmdPay(), "5 copper to rock", caller=self.char1)
        self.assertIn("Rock has no use for coin.", ansi.strip_ansi(said))

    def test_the_payee_reads_the_payer_with_a_capital(self):  # :308
        self.char2.recog.add(self.char1, LABEL)
        self.char2.msg = mock.Mock()
        self.call(CmdPay(), f"5 copper to {shown(self.char2)}", caller=self.char1)
        read = [line for line in _lines(self.char2) if "pays you" in line]
        self.assertEqual(read, [f"{SEEN_BY_LABEL} pays you 5 Copper."])


class TestArrivalLine(EvenniaTest):
    """room1 stands in for Limbo; char1 is the newcomer (it has a session)."""

    character_typeclass = CHARACTER
    LINE_END = ("steps unsteadily out of a shadowed corner, "
                "blinking and looking about in confusion.")

    def setUp(self):
        super().setUp()
        seed_world(limbo=self.room1)
        self.temple = find_seeded(seed_data.ARRIVAL_ROOM)
        self.char3 = create_object(CHARACTER, key="Char3", location=self.temple,
                                   home=self.temple)
        self.char2.location = self.temple
        describe(self.char1, self.char2, self.char3)
        self.char3.recog.add(self.char1, LABEL)
        self.left_behind = create_object(CHARACTER, key="Char4", location=self.room1,
                                         home=self.room1)
        for char in (self.char1, self.char2, self.char3, self.left_behind):
            char.msg = mock.Mock()

    def read(self, char):
        return [line for line in _lines(char) if line.endswith(self.LINE_END)]

    def test_each_bystander_reads_the_newcomer_as_they_know_them(self):
        self.assertEqual(arrival.arrive(self.char1), self.temple)
        self.assertEqual(self.read(self.char2), [f"A weathered woman {self.LINE_END}"])
        self.assertEqual(self.read(self.char3), [f"{SEEN_BY_LABEL} {self.LINE_END}"])

    def test_the_line_comes_after_the_move(self):
        seen = []
        self.char2.msg.side_effect = lambda *a, **k: seen.append(self.char1.location)
        arrival.arrive(self.char1)
        self.assertEqual(seen, [self.temple])

    def test_not_the_newcomer_and_not_the_room_it_left(self):
        arrival.arrive(self.char1)
        self.char1.msg.assert_not_called()
        self.left_behind.msg.assert_not_called()

    def test_no_line_when_already_there(self):
        self.char1.move_to(self.temple, quiet=True, move_hooks=False)
        self.char2.msg.reset_mock()
        self.assertEqual(arrival.arrive(self.char1), self.temple)
        self.char2.msg.assert_not_called()

    def test_a_line_that_raises_does_not_undo_the_arrival(self):
        with mock.patch.object(type(self.temple), "msg_contents", side_effect=RuntimeError):
            self.assertEqual(arrival.arrive(self.char1), self.temple)
        self.assertEqual((self.char1.location, self.char1.home), (self.temple, self.temple))
