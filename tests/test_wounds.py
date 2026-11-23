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

The seam (WN-T3):

- `TestHealthOf`: what the screens print comes from one function, which for
  now reads the trait -- current and max as whole numbers, the percentage
  unrounded -- and gives None for an object with no body to read. The
  reading at 5/20 is the one where current and max differ.
- `TestScreensReadTheModule`: `wounds.health_of` is patched to a reading no
  trait gives (7 of 9, 77.7 %), and `status`, `sheet` and the `char`
  snapshot must show it. This is the only test that sees `sheet`'s road,
  which reaches the trait through `getattr(char.traits, key)` -- a name the
  census below cannot read.
- `TestHealthTraitCensus`: the reaches into the `health` trait per module,
  read by AST (calls and attribute access, never docstrings), held against
  a table the next tasks shrink. Three shapes count: `X.traits.health`,
  `X.traits.<method>("health", ...)` and `_trait(X, "health")` /
  `getattr(X.traits, "health")`, with a local named `traits` standing for
  `X.traits`. A bare "health" string does not: the
  snapshot's key and chargen's *Feeds health* are words, not reads.

The maxima at CON + SIZ 21 are taken from `body.hit_points_max(10, 11)` and
not typed, so these tests follow BD's table if it is ever corrected.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_wounds
"""

import ast
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.character_commands import CmdSheet, CmdStatus
from world import body, client_state, wounds

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


class TestHealthOf(EvenniaTest):
    def test_the_trait_read_whole(self):
        self.char1.traits.health.current = 5
        self.assertEqual(wounds.health_of(self.char1), (5, 20, 25.0))

    def test_an_object_with_no_health_trait_reads_none(self):
        self.assertIsNone(wounds.health_of(self.obj1))


class TestScreensReadTheModule(EvenniaCommandTest):
    READING = (7, 9, 77.7)   # no trait at 20/20 gives this; the word is "bruised"

    def setUp(self):
        super().setUp()
        patcher = mock.patch("world.wounds.health_of", return_value=self.READING)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_status(self):
        out = self.call(CmdStatus(), "", caller=self.char1)
        self.assertIn("Health:    7/9   ( 77.7%) - bruised", out)

    def test_sheet(self):
        out = self.call(CmdSheet(), "", caller=self.char1)
        self.assertIn("Health           7/9   ( 77.7%) - bruised", out)

    def test_the_char_snapshot(self):
        self.assertEqual(
            client_state.char_snapshot(self.char1)["health"],
            {"current": 7, "max": 9, "desc": "bruised"},
        )


class TestHealthTraitCensus(SimpleTestCase):
    """The reaches into the `health` trait, per module (WN2b's door)."""

    # After WN-T3. WN-T4 moves the writer, the healer and the restore behind
    # the wound module; WN-T5 leaves the creation and chargen; WN-T6 empties it.
    EXPECTED = {
        "typeclasses/characters.py": 6,   # creation 1, update_health_max 3, writer 1, restore 1
        "world/chargen.py": 1,            # the refusal of a body with no trait
        "world/healing.py": 1,            # accrue
        "world/wounds.py": 1,             # health_of
    }

    @staticmethod
    def _is_traits(node):
        # `X.traits`, or a local named `traits` (`traits = char.traits`):
        # health_of reads through such a local, and a census that saw only
        # the attribute was blind to it.
        return (
            (isinstance(node, ast.Attribute) and node.attr == "traits")
            or (isinstance(node, ast.Name) and node.id == "traits")
        )

    @classmethod
    def _reaches(cls, tree):
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if node.attr == "health" and cls._is_traits(node.value):
                    count += 1
            elif isinstance(node, ast.Call):
                func, args = node.func, node.args
                named = (
                    len(args) >= 1 and isinstance(args[0], ast.Constant)
                    and args[0].value == "health"
                )
                second = (
                    len(args) >= 2 and isinstance(args[1], ast.Constant)
                    and args[1].value == "health"
                )
                if isinstance(func, ast.Attribute) and cls._is_traits(func.value) and named:
                    count += 1
                elif isinstance(func, ast.Name) and func.id == "_trait" and second:
                    count += 1
                elif (
                    isinstance(func, ast.Name) and func.id == "getattr" and second
                    and cls._is_traits(args[0])
                ):
                    count += 1
        return count

    def test_the_readers_of_the_health_trait(self):
        root = Path(__file__).resolve().parent.parent
        found = {}
        for package in ("commands", "server", "typeclasses", "web", "world"):
            for path in sorted((root / package).rglob("*.py")):
                n = self._reaches(ast.parse(path.read_text()))
                if n:
                    found[path.relative_to(root).as_posix()] = n
        self.assertEqual(
            found, self.EXPECTED,
            "A new reach into the health trait: go through world.wounds (WN2b).",
        )
