"""
The wound module's arithmetic: Hit Points, levels, the margin `health` shows,
the hit location table and the clocks' lengths. Wounds, Task WN-T2
(docs/PolishedWorld_Wounds_Decomposition.md; Combat Design §4.4, WN1-WN4).

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
- `TestLevel`: the book's three wounds (core pp. 145-146) at a maximum of 5,
  on both sides of each boundary. Serious is 0 Hit Points or below; Major is
  a negative score equal to the starting Hit Points or worse, so damage 10
  and not 11. A `<` where `<=` belongs moves Major one point out.
- `TestMargin` and `TestHealth`: WN2's figure is the worst location's
  margin to a Major Wound, out of TWICE its maximum, so a location at 0 reads
  50 % and 0 % always means a Major Wound. The three rows are the Combat
  Design's. The lowest fraction wins; on a tie the first location in
  `body.LOCATIONS` wins (the head before the arms when starvation has taken
  five points from everything), compared exactly, not as floats.
- `TestHitLocationTable`: every one of the twenty rolls against the book's
  table (p. 145), and the two numbers just outside it.
- `TestClocks`: (CON + POW) minutes for a limb, half (CON + POW) rounds of
  five seconds for head, chest and abdomen (p. 146; WN3, WN4). A key that is
  not a location is refused: a misspelled vital key would otherwise get the
  limb's clock, twenty-four times longer.
- `TestWordFor`: the health words read as `Character.health_desc()` reads
  them today -- each key an inclusive upper bound, anything above the top
  key the top word -- tested on every boundary and just above it.
- `TestWordsMatchTheTrait`: the copied table equals the `health` trait's own
  `descs` for as long as the trait is created (WN-T6 removes the test with
  the trait).

The maxima at CON + SIZ 21 are taken from `body.hit_points_max(10, 11)` and
not typed, so these tests follow BD's table if it is ever corrected.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_wounds
"""

from django.test import SimpleTestCase
from evennia.utils.test_resources import EvenniaTest

from world import body, wounds

MAXIMA = body.hit_points_max(10, 11)   # head 5, chest 7, abdomen 6, arms 4, legs 5


class TestTheStandardBody(SimpleTestCase):
    def test_maxima_at_con_plus_siz_21(self):
        # Receipt for the rows below: the body they are written against.
        self.assertEqual(
            [MAXIMA[key] for key in body.LOCATIONS], [5, 7, 6, 4, 4, 5, 5]
        )

    def test_vital_and_limbs_cover_the_body_once(self):
        limbs = [key for key in body.LOCATIONS if key not in wounds.VITAL]
        self.assertEqual(wounds.VITAL, ("head", "chest", "abdomen"))
        self.assertEqual(len(limbs), 4)


class TestLevel(SimpleTestCase):
    def test_hit_points_are_the_maximum_less_the_damage(self):
        self.assertEqual(wounds.hit_points(5, 0), 5)
        self.assertEqual(wounds.hit_points(5, 7), -2)

    def test_the_levels_at_a_maximum_of_five(self):
        for damage, expected in (
            (0, wounds.INTACT),
            (1, wounds.MINOR),
            (4, wounds.MINOR),     # 1 Hit Point left
            (5, wounds.SERIOUS),   # 0
            (9, wounds.SERIOUS),   # -4
            (10, wounds.MAJOR),    # -5: equal to the starting Hit Points
            (14, wounds.MAJOR),
        ):
            with self.subTest(damage=damage):
                self.assertEqual(wounds.level(5, damage), expected)


class TestMargin(SimpleTestCase):
    def test_unhurt_a_location_at_zero_and_a_major_wound(self):
        self.assertEqual(wounds.margin(5, 0), (10, 10))
        self.assertEqual(wounds.margin(5, 5), (5, 10))
        self.assertEqual(wounds.margin(5, 10), (0, 10))

    def test_past_a_major_wound_the_margin_stops_at_zero(self):
        self.assertEqual(wounds.margin(5, 12), (0, 10))


class TestHealth(SimpleTestCase):
    def test_an_unhurt_body_reads_full(self):
        self.assertEqual(wounds.health(MAXIMA, {}), (10, 10, 100.0))

    def test_a_head_at_minus_five_reads_zero(self):
        self.assertEqual(wounds.health(MAXIMA, {"head": 10}), (0, 10, 0.0))

    def test_five_points_everywhere_read_half_on_the_head(self):
        damages = {key: min(5, MAXIMA[key]) for key in body.LOCATIONS}
        self.assertEqual(damages["right_arm"], 4)   # receipt: the arms stopped at 0
        # Head 5/10, arms 4/8: a tie at 50 %, the head first in LOCATIONS.
        self.assertEqual(wounds.health(MAXIMA, damages), (5, 10, 50.0))

    def test_on_a_tie_the_first_location_is_shown(self):
        # Head 5/10 and arm 4/8 tie at 50 % and show different numbers; in
        # the row above, the legs' 5/10 would hide a tie taken by the last.
        self.assertEqual(
            wounds.health(MAXIMA, {"head": 5, "left_arm": 4}), (5, 10, 50.0)
        )

    def test_one_arm_at_zero_reads_half(self):
        self.assertEqual(wounds.health(MAXIMA, {"left_arm": 4}), (4, 8, 50.0))

    def test_the_lowest_fraction_wins_over_the_lowest_margin(self):
        # Chest 9/14 (64 %) is a larger margin than the arm's 7/8 (88 %)
        # but the lower fraction.
        reading = wounds.health(MAXIMA, {"chest": 5, "left_arm": 1})
        self.assertEqual(reading[:2], (9, 14))


class TestHitLocationTable(SimpleTestCase):
    def test_every_roll(self):
        rows = (
            (range(1, 4), "right_leg"), (range(4, 7), "left_leg"),
            (range(7, 10), "abdomen"), (range(10, 13), "chest"),
            (range(13, 16), "right_arm"), (range(16, 19), "left_arm"),
            (range(19, 21), "head"),
        )
        for rolls, expected in rows:
            for roll in rolls:
                with self.subTest(roll=roll):
                    self.assertEqual(wounds.location_for(roll), expected)

    def test_outside_the_die_is_refused(self):
        for roll in (0, 21):
            with self.subTest(roll=roll), self.assertRaises(ValueError):
                wounds.location_for(roll)


class TestClocks(SimpleTestCase):
    def test_a_limb_has_con_plus_pow_minutes(self):
        self.assertEqual(wounds.clock_seconds(10, 11, "left_arm"), 1260)
        self.assertEqual(wounds.clock_seconds(10, 11, "right_leg"), 1260)

    def test_head_chest_and_abdomen_have_half_as_many_rounds(self):
        for key in wounds.VITAL:
            with self.subTest(location=key):
                self.assertEqual(wounds.clock_seconds(10, 11, key), 52.5)

    def test_a_key_that_is_no_location_is_refused(self):
        with self.assertRaises(ValueError):
            wounds.clock_seconds(10, 11, "Head")


class TestWordFor(SimpleTestCase):
    def test_every_boundary_and_just_above_it(self):
        for percent, expected in (
            (0, "dead"), (0.1, "near death"),
            (10, "near death"), (10.1, "critically wounded"),
            (25, "critically wounded"), (25.1, "badly hurt"),
            (50, "badly hurt"), (50.1, "injured"),
            (75, "injured"), (75.1, "bruised"),
            (90, "bruised"), (90.1, "healthy"),
            (100, "healthy"),
        ):
            with self.subTest(percent=percent):
                self.assertEqual(wounds.word_for(percent), expected)


class TestWordsMatchTheTrait(EvenniaTest):
    def test_the_copied_table_is_the_traits(self):
        self.assertEqual(dict(self.char1.traits.health.descs), wounds.HEALTH_WORDS)
