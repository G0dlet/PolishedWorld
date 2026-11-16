"""
A character is spoken of with the pronouns its appearance gives, and nobody
is *it*. Names, Task NM-T15b (docs/PolishedWorld_Combat_Decomposition.md;
OQ-NM9 (7)).

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
`Character.gender` is a property read from the sex in `db.appearance`:
`male` and `female` give themselves, and `unstated`, no facts, or anything
else give `"plural"` -- singular *they*. Evennia's `"neutral"` is *it*
(pronouns.py:84) and is what an object without `gender` reads, so the
property must never return it (NMM27).

The seven room lines that wrote *they* by hand now go through `$pron()` and
`$pconj()` (and the barter frame through `names.pronoun`). `$pconj`, not
`$conj`: `$conj` never reads `gender` (funcparser.py:1383) and would give
*they stands*, which the no-facts lines below catch. With no facts each
reads word for word as before: those lines are pinned where the site was
pinned first, and stay unchanged there -- `test_names_commands`
(`introduce`), `test_names_statue_body` (stone, stirs),
`test_names_room_messages` and `test_fatigue` (the fall),
`test_names_trade` (a decline after an accept). Here each site is read
with `male` and `female`: the pronoun, and the verb where the pronoun is
its subject (*he stands*, *she draws*).

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_pronouns
"""

from evennia import create_object
from evennia.utils import ansi
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from tests.names_fixture import describe
from tests.test_names_commands import _Introduce
from tests.test_names_room_messages import SEEN_BY_LABEL, _Readers, _Timers
from tests.test_names_statue_body import STRANGER_SEES
from tests.test_names_trade import TWO_SEEN_BY_ONE, _cap
from tests.test_barter_currency import TradeFixtureMixin
from tests.test_currency import LedgerIsolationMixin
from tests.test_currency_commands import SecondSessionMixin
from tests.test_work_command import captured_messages
from typeclasses.characters import _Sleeper
from world import names
from world.barter import CmdPWDecline

CHARACTER = "typeclasses.characters.Character"
OBJECT = "typeclasses.objects.Object"

# (sex, subject, possessive, reflexive, the third person of "stand").
SEXES = (
    ("male", "he", "his", "himself", "stands"),
    ("female", "she", "her", "herself", "stands"),
)


def _appear(char, sex):
    # The sex alone: `gender` reads only it, and without all three facts the
    # short description is the stored one (NM-T15), so each reader names the
    # character as the fixtures do and only the pronoun changes.
    char.db.appearance = {"sex": sex}


class TestGender(EvenniaTest):
    character_typeclass = CHARACTER

    def test_without_facts_it_is_singular_they(self):
        self.assertIsNone(self.char1.db.appearance)
        self.assertEqual(self.char1.gender, "plural")

    def test_male_and_female(self):
        for sex in ("male", "female"):
            with self.subTest(sex=sex):
                _appear(self.char1, sex)
                self.assertEqual(self.char1.gender, sex)

    def test_unstated_is_singular_they(self):
        _appear(self.char1, "unstated")
        self.assertEqual(self.char1.gender, "plural")

    def test_never_neutral(self):
        for stored in (None, {}, {"sex": None}, {"sex": "unstated"}, {"sex": "neutral"},
                       {"sex": "MALE"}, "male", 7):
            with self.subTest(stored=stored):
                self.char1.db.appearance = stored
                self.assertEqual(self.char1.gender, "plural")

    def test_the_sleeper_passes_it_through(self):
        sleeper = _Sleeper(self.char1)
        self.assertEqual(sleeper.gender, "plural")
        _appear(self.char1, "female")
        self.assertEqual(sleeper.gender, "female")


class TestPronounHelper(EvenniaTest):
    character_typeclass = CHARACTER

    def test_each_form(self):
        self.assertEqual(names.pronoun(self.char1, "your"), "their")
        self.assertEqual(names.pronoun(self.char1, "yourself"), "themselves")
        _appear(self.char1, "male")
        self.assertEqual(names.pronoun(self.char1, "your"), "his")
        self.assertEqual(names.pronoun(self.char1, "you"), "he")
        _appear(self.char1, "female")
        self.assertEqual(names.pronoun(self.char1, "your"), "her")
        self.assertEqual(names.pronoun(self.char1, "yourself"), "herself")

    def test_a_thing_without_gender_is_not_it(self):
        thing = create_object(OBJECT, key="stone", location=self.room1)
        self.assertFalse(hasattr(thing, "gender"))
        self.assertEqual(names.pronoun(thing, "your"), "their")


class TestIntroduce(_Introduce):
    """`commands/names_commands.py`, CmdIntroduce: the three lines."""

    def _reset(self):
        for char in (self.char1, self.char3, self.char4):
            char.msg.reset_mock()

    def test_to_the_room(self):
        for sex, _, _, reflexive, _ in SEXES:
            with self.subTest(sex=sex):
                _appear(self.char2, sex)
                self._reset()
                self.char1.recog.remove(self.char2)
                self.introduce()
                self.assertEqual(
                    self.lines(self.char1),
                    [f"A broad-shouldered man introduces {reflexive} as Char2."],
                )

    def test_to_one(self):
        for sex, _, _, reflexive, _ in SEXES:
            with self.subTest(sex=sex):
                _appear(self.char2, sex)
                self._reset()
                self.char3.recog.remove(self.char2)
                self.introduce("to freckled")
                self.assertEqual(
                    self.lines(self.char3),
                    [f"A broad-shouldered man introduces {reflexive} to you as Char2."],
                )
                self.assertEqual(
                    self.lines(self.char1),
                    [f"A broad-shouldered man introduces {reflexive} to a freckled youth."],
                )


class TestStatueLines(_Readers, EvenniaCommandTest):
    """`Character.at_post_unpuppet` and `at_post_puppet`."""

    def _reset(self):
        for reader in (self.char3, self.char4):
            reader.msg.reset_mock()

    def test_turns_to_stone(self):
        for sex, _, possessive, _, _ in SEXES:
            with self.subTest(sex=sex):
                _appear(self.char1, sex)
                self._reset()
                self.account.unpuppet_object(self.session)
                self.assertTrue(self.char1.is_statue)  # receipt: from a statue
                rest = (f"body slowly turns to weathered stone, {possessive} final pose "
                        "frozen in place.")
                self.assert_read(rest, stranger=f"{STRANGER_SEES}'s {rest}",
                                 recogniser=f"{SEEN_BY_LABEL}'s {rest}")
                self.account.puppet_object(self.session, self.char1)

    def test_stirs(self):
        for sex, subject, possessive, _, _ in SEXES:
            with self.subTest(sex=sex):
                _appear(self.char1, sex)
                self.account.unpuppet_object(self.session)
                self._reset()
                self.account.puppet_object(self.session, self.char1)
                rest = (f"stirs, color flowing back into {possessive} flesh as {subject} "
                        "draws breath.")
                self.assert_read(rest, stranger=f"The stone form of a weathered woman {rest}",
                                 recogniser=f"The stone form of mia of the Ford {rest}")


class TestFalls(_Timers, _Readers, EvenniaCommandTest):
    """`Character.collapse`, `fatigue.FALL_ROOM`."""

    def test_falls(self):
        for sex, subject, _, _, stands in SEXES:
            with self.subTest(sex=sex):
                _appear(self.char1, sex)
                for reader in (self.char3, self.char4):
                    reader.msg.reset_mock()
                self.char1.db.collapsed = False
                self.char1.collapse()
                self.assertTrue(self.char1.db.collapsed)  # receipt: the fall ran
                self.assert_read(f"sways and goes down where {subject} {stands}.")


class TestDecline(SecondSessionMixin, TradeFixtureMixin, LedgerIsolationMixin,
                  EvenniaCommandTest):
    """`world/barter.py` CmdPWDecline after an accept: a %-string frame."""

    def setUp(self):
        super().setUp()
        describe(self.char1, self.char2)

    def test_changes_their_mind(self):
        self._offer("3 silver", caller=self.char1)
        self._offer("2 silver", caller=self.char2)
        two = _cap(TWO_SEEN_BY_ONE[0])
        for sex, _, possessive, _, _ in SEXES:
            with self.subTest(sex=sex):
                _appear(self.char2, sex)
                self.handler.part_b_accepted = True
                with captured_messages(self.char1) as raw:
                    self.call(CmdPWDecline(), "", caller=self.char2)
                self.assertEqual(
                    [ansi.strip_ansi(line) for line in raw],
                    [f"{two}:s trade action: {two} changes {possessive} mind, "
                     "declining the current offer."],
                )
