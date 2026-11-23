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
- (`TestWordsMatchTheTrait`, which held the copied table to the `health`
  trait's own `descs`, went with the trait in WN-T6: the table has one
  home now.)

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

The door (WN-T4):

- `TestTheWriterNamesItsLocation`: `apply_health_damage` has no default for
  `location` (WO5), so a call that does not say where is a TypeError; a
  place that is neither `ALL`, `RANDOM` nor a key of `body.LOCATIONS` is a
  ValueError raised before the trait is touched, and raised for an amount
  of 0 too -- the tick calls with a sum that is usually 0, and a wrong
  place must fail on the first tick, not on the first starving one. `ALL`,
  `RANDOM` and a named key are accepted (`TestStoredDamage` shows where
  each lands).
- `TestTheDoors`, on the fixture's body (head 4): `heal` stops at an unhurt
  body and returns what landed (what `accrue` reports); `room_to_heal` is
  the largest damage, 0 unhurt and None for an object with no body;
  `restore_at_respawn` removes the damage; `damage` says whether it wrote,
  and writes nothing on a body already dead (a death in progress);
  `is_dead` at eight points on the head and not at seven.

The storage (WN-T5):

- `TestStoredDamage`, at CON 10 and SIZ 11: five points of `ALL` stop the
  arms at their maximum (WO7) and read 5 of 10, 50 % -- the row that read
  15 of 20, 75 % while the trait was what was written; nine leave the head
  one point from a Major Wound and ten kill, once, and the body comes back
  with no damage. A named key hurts that location alone; `RANDOM` hurts
  what the table names for the roll. A heal takes a point from every hurt
  location, drops a mended one, and removes the Attribute with the last
  point: an unhurt body has none (WN1). A raised CON keeps the damage and
  gains Hit Points. **The old trait at 3 of 20 with no damage reads
  100 %** -- WN2b's promise to every character made before WN. Only a vital
  location at a Major Wound is death (WO7, WN5), and a stored dict is read
  as the `_SaverDict` it comes back as.
- `TestHealthOf`: the fixture's unhurt body reads 8 of 8; an object without
  CON and SIZ reads None.

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
from typeclasses.corpse import PlayerCorpse
from tests.wounds_fixture import made_before_wn
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


def _stored(char):
    """The stored damage as a plain dict; None when there is no Attribute."""
    if not char.attributes.has("body_damage"):
        return None
    return dict(char.db.body_damage)


class TestANewCharacter(EvenniaTest):
    def test_has_no_health_trait_and_reads_its_body(self):
        # WN-T6: nothing creates the trait; the fixture is made after it.
        self.assertIsNone(self.char1.traits.get("health"))
        self.assertEqual(wounds.health_of(self.char1), (8, 8, 100.0))


class TestHealthOf(EvenniaTest):
    def test_an_unhurt_fixture_reads_full(self):
        # The fixture is CON 10, SIZ 10: a head of 4, whole at 8.
        self.assertEqual(wounds.health_of(self.char1), (8, 8, 100.0))

    def test_an_object_without_a_body_reads_none(self):
        self.assertIsNone(wounds.health_of(self.obj1))

    def test_a_body_missing_siz_reads_none(self):
        self.char1.stats.remove("siz")
        self.assertIsNone(wounds.health_of(self.char1))


class TestStoredDamage(EvenniaTest):
    """CON 10, SIZ 11: the book's column 21-25 -- head 5, arms 4 (WN-T5)."""

    def setUp(self):
        super().setUp()
        self.char1.stats.siz.base = 11
        self.char1.db.respawn_location = self.room2

    def test_five_points_of_all_stop_the_arms_and_read_half(self):
        self.char1.apply_health_damage(5, location=wounds.ALL)
        self.assertEqual(_stored(self.char1), {
            "head": 5, "chest": 5, "abdomen": 5,
            "right_arm": 4, "left_arm": 4, "right_leg": 5, "left_leg": 5,
        })
        self.assertEqual(wounds.health_of(self.char1), (5, 10, 50.0))

    def test_nine_points_of_all_leave_the_head_one_from_a_major_wound(self):
        self.char1.apply_health_damage(9, location=wounds.ALL)
        self.assertFalse(wounds.is_dead(self.char1))
        self.assertEqual(wounds.health_of(self.char1), (1, 10, 10.0))
        self.assertEqual(self.char1.location, self.room1)

    def test_ten_points_of_all_kill_once_and_the_body_comes_back_unhurt(self):
        self.char1.apply_health_damage(10, location=wounds.ALL)
        corpses = [o for o in self.room1.contents if isinstance(o, PlayerCorpse)]
        self.assertEqual(len(corpses), 1)
        self.assertEqual(self.char1.location, self.room2)
        self.assertIsNone(_stored(self.char1))

    def test_a_named_leg_is_the_only_location_hurt(self):
        self.char1.apply_health_damage(3, location="left_leg")
        self.assertEqual(_stored(self.char1), {"left_leg": 3})
        self.assertEqual(wounds.health_of(self.char1), (7, 10, 70.0))

    def test_random_hurts_the_location_the_table_names(self):
        with mock.patch("world.wounds.randint", return_value=20) as roll:
            self.char1.apply_health_damage(2, location=wounds.RANDOM)
        roll.assert_called_once_with(1, 20)
        self.assertEqual(_stored(self.char1), {"head": 2})

    def test_all_adds_to_what_a_location_already_has(self):
        self.char1.apply_health_damage(2, location="chest")
        self.char1.apply_health_damage(1, location=wounds.ALL)
        self.assertEqual(_stored(self.char1)["chest"], 3)
        self.assertEqual(_stored(self.char1)["head"], 1)

    def test_a_heal_mends_every_hurt_location_by_one_and_returns_one(self):
        self.char1.apply_health_damage(5, location=wounds.ALL)
        self.assertEqual(wounds.heal(self.char1, 1), 1)
        self.assertEqual(_stored(self.char1), {
            "head": 4, "chest": 4, "abdomen": 4,
            "right_arm": 3, "left_arm": 3, "right_leg": 4, "left_leg": 4,
        })

    def test_a_heal_leaves_out_what_is_mended_and_the_last_point_removes_it(self):
        self.char1.apply_health_damage(1, location="head")
        self.char1.apply_health_damage(3, location="chest")
        self.assertEqual(wounds.heal(self.char1, 1), 1)
        self.assertEqual(_stored(self.char1), {"chest": 2})
        self.assertEqual(wounds.heal(self.char1, 5), 2)
        self.assertIsNone(_stored(self.char1))

    def test_an_unhurt_character_has_no_attribute(self):
        self.assertIsNone(_stored(self.char1))
        self.char1.apply_health_damage(3, location=wounds.ALL)
        wounds.restore_at_respawn(self.char1)
        self.assertIsNone(_stored(self.char1))

    def test_raised_con_keeps_the_damage_and_gains_hit_points(self):
        self.char1.apply_health_damage(5, location=wounds.ALL)
        self.char1.stats.con.base = 15   # CON + SIZ 26: head 6
        self.assertEqual(_stored(self.char1)["head"], 5)
        left, whole, _percent = wounds.health_of(self.char1)
        self.assertEqual((left, whole), (7, 12))

    def test_the_old_trait_at_3_of_20_and_no_damage_reads_full(self):
        # WN2b's promise to every character made before WN.
        made_before_wn(self.char1).current = 3
        self.assertEqual(wounds.health_of(self.char1), (10, 10, 100.0))
        self.assertEqual(self.char1.health_desc(), "healthy")

    def test_only_a_vital_location_at_a_major_wound_is_death(self):
        # A premise no ALL source can make: limbs past their maximum.
        self.char1.db.body_damage = {"left_arm": 8, "right_leg": 10}
        self.assertFalse(wounds.is_dead(self.char1))
        self.char1.db.body_damage = {"abdomen": 11}
        self.assertFalse(wounds.is_dead(self.char1))
        self.char1.db.body_damage = {"abdomen": 12}
        self.assertTrue(wounds.is_dead(self.char1))

    def test_a_stored_dict_is_read_as_a_mapping(self):
        # A stored dict comes back as a _SaverDict, not a dict.
        self.char1.apply_health_damage(2, location="head")
        self.assertNotEqual(type(self.char1.db.body_damage), dict)
        self.assertEqual(wounds.health_of(self.char1), (8, 10, 80.0))


class TestTheWriterNamesItsLocation(EvenniaTest):
    def test_a_call_that_does_not_say_where_is_refused(self):
        with self.assertRaises(TypeError) as caught:
            self.char1.apply_health_damage(1)
        self.assertIn("location", str(caught.exception))
        self.assertIsNone(_stored(self.char1))

    def test_an_unknown_place_is_refused_before_anything_is_written(self):
        for place in ("arm", "ALL", "Head", "", None):
            with self.subTest(place=place):
                with self.assertRaises(ValueError):
                    self.char1.apply_health_damage(3, location=place)
                self.assertIsNone(_stored(self.char1))

    def test_an_unknown_place_is_refused_when_there_is_no_damage(self):
        with self.assertRaises(ValueError):
            self.char1.apply_health_damage(0, location="arm")


class TestTheDoors(EvenniaTest):
    """The fixture's body, CON + SIZ 20: head 4, chest 6, abdomen 5, arms 3, legs 4."""

    def test_heal_stops_at_an_unhurt_body_and_returns_what_landed(self):
        self.char1.apply_health_damage(3, location=wounds.ALL)
        self.assertEqual(wounds.heal(self.char1, 5), 3)
        self.assertIsNone(_stored(self.char1))
        self.assertEqual(wounds.heal(self.char1, 1), 0)

    def test_heal_of_less_than_the_room(self):
        self.char1.apply_health_damage(3, location=wounds.ALL)
        self.assertEqual(wounds.heal(self.char1, 2), 2)
        self.assertEqual(set(_stored(self.char1).values()), {1})

    def test_room_to_heal_is_the_largest_damage(self):
        self.assertEqual(wounds.room_to_heal(self.char1), 0)
        self.char1.apply_health_damage(2, location="chest")
        self.char1.apply_health_damage(1, location=wounds.ALL)
        self.assertEqual(wounds.room_to_heal(self.char1), 3)
        self.assertIsNone(wounds.room_to_heal(self.obj1))

    def test_restore_at_respawn_removes_the_damage(self):
        self.char1.apply_health_damage(7, location=wounds.ALL)
        wounds.restore_at_respawn(self.char1)
        self.assertIsNone(_stored(self.char1))

    def test_is_dead_at_a_major_wound_on_the_head_and_not_one_before(self):
        # The door itself, not the writer: the writer would run the death
        # and the restore, and the body would never be seen dead.
        self.assertFalse(wounds.is_dead(self.char1))
        self.assertTrue(wounds.damage(self.char1, 7, wounds.ALL))
        self.assertFalse(wounds.is_dead(self.char1))
        self.assertTrue(wounds.damage(self.char1, 1, wounds.ALL))
        self.assertTrue(wounds.is_dead(self.char1))
        self.assertFalse(wounds.damage(self.char1, 1, wounds.ALL))   # a death in progress
        self.assertEqual(_stored(self.char1)["head"], 8)
        self.assertFalse(wounds.is_dead(self.obj1))


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

    # After WN-T6: nothing creates, rescales, asks for or reads the trait.
    # Characters made before WN keep theirs, and it stays unread (WN2b).
    EXPECTED = {}

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
            "A reach into the health trait, which nothing may read since WN2b: "
            "a character made before WN keeps a stale one. Go through world.wounds.",
        )
