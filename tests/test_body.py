"""
Tests for world.body -- a body's derived values (Body decomposition, slice
BD, lock BD7; Legend core pp. 10-13, 90).

Every expected number is the book's: Alaric's tale (DEX 13, INT 16; pp. 10,
13) and the edges of the tables, typed here and never computed from the
code under test.
"""

from evennia.utils.test_resources import EvenniaTestCase

from world import body
from world.fatigue import LEVELS


class TestCombatActions(EvenniaTestCase):
    """The table on p. 10 and fatigue's lowered DEX on p. 90."""

    def test_alaric_has_three(self):
        self.assertEqual(body.combat_actions(13, 16), 3)

    def test_the_steps_of_the_table(self):
        # Average -> Combat Actions, at both ends of each step (p. 10).
        for average, expected in (
            (6, 1), (7, 2), (12, 2), (13, 3),
            (18, 3), (19, 4), (24, 4), (25, 5),
        ):
            with self.subTest(average=average):
                self.assertEqual(body.combat_actions(average, average), expected)

    def test_the_average_is_rounded_up_at_a_step(self):
        # 12 + 13 = 25, 12.5 rounds up to 13: three, not two.
        self.assertEqual(body.combat_actions(12, 13), 3)

    def test_fatigue_lowers_dex(self):
        for dex, int_, word, expected in (
            (13, 16, "exhausted", 2),     # Alaric: (8 + 16) / 2 = 12
            (13, 16, "debilitated", 2),   # Alaric: (3 + 16) / 2 = 9.5 -> 10
            (13, 13, "exhausted", 2),     # 21 / 2 -> 11
            (9, 9, "exhausted", 2),       # 13 / 2 -> 7
            (9, 9, "debilitated", 1),     # 8 / 2 = 4: the two losses differ
        ):
            with self.subTest(dex=dex, int_=int_, word=word):
                self.assertEqual(body.combat_actions(dex, int_, word), expected)

    def test_lighter_fatigue_changes_nothing(self):
        for word in ("fresh", "winded", "tired", "wearied"):
            with self.subTest(word=word):
                self.assertEqual(body.combat_actions(13, 16, word), 3)


class TestStrikeRank(EvenniaTestCase):
    """pp. 12-13, and fatigue's penalty on p. 90."""

    def test_alaric_is_fifteen(self):
        # 16 + 13 = 29 / 2 = 14.5, rounded up to 15 (p. 13).
        self.assertEqual(body.strike_rank(13, 16), 15)

    def test_alarics_jerkin(self):
        # 4 Armour Points / 5 = 0.8, rounded up to 1 (p. 13).
        self.assertEqual(body.strike_rank(13, 16, armour_points=4), 14)

    def test_armour_is_divided_by_five_and_rounded_up(self):
        for armour, expected in ((0, 15), (5, 14), (6, 13), (10, 13), (11, 12)):
            with self.subTest(armour=armour):
                self.assertEqual(body.strike_rank(13, 16, armour), expected)

    def test_fatigue_penalty(self):
        for word, expected in (
            ("fresh", 15), ("winded", 15), ("tired", 15),
            ("wearied", 13), ("exhausted", 11), ("debilitated", 9),
        ):
            with self.subTest(word=word):
                self.assertEqual(body.strike_rank(13, 16, 0, word), expected)

    def test_no_floor(self):
        # 91 Armour Points -> 19; 15 - 19 = -4 (§4 of the decomposition).
        self.assertEqual(body.strike_rank(13, 16, 91), -4)


class TestFatigueWords(EvenniaTestCase):
    """The fatigue words are world.fatigue's own; a renamed level fails here."""

    def test_every_level_is_accepted(self):
        for level in LEVELS:
            with self.subTest(word=level.word):
                body.combat_actions(13, 16, level.word)
                body.strike_rank(13, 16, 0, level.word)

    def test_every_penalty_names_a_level(self):
        words = {level.word for level in LEVELS}
        self.assertLessEqual(set(body.COMBAT_ACTIONS_DEX_LOSS), words)
        self.assertLessEqual(set(body.STRIKE_RANK_PENALTY), words)

    def test_an_unknown_word_raises(self):
        with self.assertRaises(ValueError):
            body.combat_actions(13, 16, "weary")
        with self.assertRaises(ValueError):
            body.strike_rank(13, 16, 0, "weary")
