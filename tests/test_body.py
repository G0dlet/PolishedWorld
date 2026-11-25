"""
Tests for world.body -- a body's derived values (Body decomposition, slice
BD, lock BD7; Legend core pp. 10-13, 90).

Every expected number is the book's: Alaric's tale (DEX 13, INT 16; pp. 10,
13) and the edges of the tables, typed here and never computed from the
code under test.
"""

from evennia.utils.test_resources import EvenniaTest, EvenniaTestCase

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

    def test_the_armour_penalty(self):
        # Gear GR-T5: the formula Strike Rank uses, named (pp. 13, 95).
        for points, penalty in ((0, 0), (1, 1), (5, 1), (6, 2), (17, 4), (91, 19)):
            with self.subTest(points=points):
                self.assertEqual(body.armour_penalty(points), penalty)

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


class TestDamageModifier(EvenniaTestCase):
    """
    Pressures the table typed from p. 10: a band shifted by one (BDM4), a
    wrong row, and the refusal outside 1-100 (BDM5).
    """

    # Both ends of every row, typed from the book.
    BOOK = (
        (1, 5, "-1D8"), (6, 10, "-1D6"), (11, 15, "-1D4"), (16, 20, "-1D2"),
        (21, 25, "+0"), (26, 30, "+1D2"), (31, 35, "+1D4"), (36, 40, "+1D6"),
        (41, 45, "+1D8"), (46, 50, "+1D10"), (51, 60, "+1D12"),
        (61, 70, "+2D6"), (71, 80, "+2D8"), (81, 90, "+2D10"),
        (91, 100, "+2D12"),
    )

    def test_alaric(self):
        # STR 12 + SIZ 14 = 26 -> +1D2 (p. 11).
        self.assertEqual(body.damage_modifier(12, 14), (1, 1, 2))
        self.assertEqual(body.damage_modifier_text(12, 14), "+1D2")

    def test_every_row_at_both_ends(self):
        for low, high, text in self.BOOK:
            for total in (low, high):
                with self.subTest(total=total):
                    self.assertEqual(body.damage_modifier_text(total, 0), text)

    def test_the_data_form(self):
        self.assertEqual(body.damage_modifier(10, 10), (-1, 1, 2))
        self.assertEqual(body.damage_modifier(12, 12), (0, 0, 0))
        self.assertEqual(body.damage_modifier(50, 50), (1, 2, 12))

    def test_refuses_outside_the_table(self):
        for total in (0, 101):
            with self.subTest(total=total):
                with self.assertRaises(ValueError):
                    body.damage_modifier(total, 0)


class TestHitPointsMax(EvenniaTestCase):
    """
    Pressures the table on p. 11: the arm's flat first step (BDM6 gives it
    the leg's row), a band shifted by one, and the "+5 -> +1" past 40.
    """

    # The book's eight columns per row, typed, not computed.
    BOOK = {
        "leg": (1, 2, 3, 4, 5, 6, 7, 8),
        "abdomen": (2, 3, 4, 5, 6, 7, 8, 9),
        "chest": (3, 4, 5, 6, 7, 8, 9, 10),
        "arm": (1, 1, 2, 3, 4, 5, 6, 7),
        "head": (1, 2, 3, 4, 5, 6, 7, 8),
    }
    ROW = {
        "head": "head", "chest": "chest", "abdomen": "abdomen",
        "right_arm": "arm", "left_arm": "arm",
        "right_leg": "leg", "left_leg": "leg",
    }

    def test_seven_locations(self):
        self.assertEqual(set(body.hit_points_max(10, 10)), set(self.ROW))
        self.assertEqual(len(body.LOCATIONS), 7)

    def test_alaric(self):
        # CON 7 + SIZ 14 = 21 (p. 11).
        self.assertEqual(body.hit_points_max(7, 14), {
            "right_leg": 5, "left_leg": 5, "abdomen": 6, "chest": 7,
            "right_arm": 4, "left_arm": 4, "head": 5,
        })

    def test_every_cell_at_both_ends_of_its_band(self):
        for column in range(8):
            for total in (5 * column + 1, 5 * column + 5):
                result = body.hit_points_max(total, 0)
                for location, row in self.ROW.items():
                    with self.subTest(total=total, location=location):
                        self.assertEqual(result[location], self.BOOK[row][column])

    def test_past_forty(self):
        for total in (41, 45):
            with self.subTest(total=total):
                self.assertEqual(body.hit_points_max(total, 0), {
                    "head": 9, "chest": 11, "abdomen": 10,
                    "right_arm": 8, "left_arm": 8,
                    "right_leg": 9, "left_leg": 9,
                })

    def test_refuses_below_the_table(self):
        with self.assertRaises(ValueError):
            body.hit_points_max(0, 0)


class TestGeneralHitPoints(EvenniaTestCase):
    """A creature's one pool and its rating, rounded up (p. 146; CE4)."""

    def test_the_books_example(self):
        # CON 12, SIZ 16: 14, and a rating of 7 (p. 146).
        self.assertEqual(body.general_hit_points(12, 16), 14)
        self.assertEqual(body.critical_rating(14), 7)

    def test_odd_numbers_round_up(self):
        # 15 / 2 = 7.5 is 8, and 7 / 2 = 3.5 is 4.
        self.assertEqual(body.general_hit_points(11, 4), 8)
        self.assertEqual(body.critical_rating(7), 4)


class TestDerived(EvenniaTest):
    """
    Pressures BD7's "read on every read": a value stored or cached would miss
    the fatigue and the DEX changed after the first read. The placeholder
    characteristics are all 10.
    """

    PLACEHOLDER_LOCATIONS = {
        "head": 4, "chest": 6, "abdomen": 5,
        "right_arm": 3, "left_arm": 3, "right_leg": 4, "left_leg": 4,
    }

    def test_the_placeholder_body(self):
        self.assertEqual(self.char1.fatigue_desc(), "fresh")
        self.assertEqual(body.derived(self.char1), {
            "combat_actions": 2,
            "strike_rank": 10,
            "armour_penalty": 0,   # Gear GR-T5: nothing worn
            "damage_modifier": (-1, 1, 2),
            "hit_points": self.PLACEHOLDER_LOCATIONS,
        })

    def test_fatigue_is_read_from_the_gauge(self):
        for value, actions, rank in ((10, 2, 6), (0, 1, 4)):
            with self.subTest(fatigue=value):
                self.char1.traits.fatigue.current = value
                result = body.derived(self.char1)
                self.assertEqual(result["combat_actions"], actions)
                self.assertEqual(result["strike_rank"], rank)

    def test_a_changed_characteristic_shows_on_the_next_read(self):
        body.derived(self.char1)
        self.char1.stats.dex.base = 16
        self.assertEqual(body.derived(self.char1)["combat_actions"], 3)

    def test_characteristics_are_read_with_their_modifier(self):
        self.char1.stats.dex.mod = 6
        self.assertEqual(body.derived(self.char1)["combat_actions"], 3)

    def test_no_fatigue_gauge_reads_as_fresh(self):
        self.char1.traits.remove("fatigue")
        self.assertEqual(body.derived(self.char1)["strike_rank"], 10)

    def test_a_body_without_a_characteristic_reads_none(self):
        self.char1.stats.remove("siz")
        self.assertIsNone(body.derived(self.char1))
        self.assertIsNone(body.derived(self.room1))
