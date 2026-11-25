"""
Tests for a weapon's wear (Gear decomposition GR-T10; locks IS3, IS5,
GR13, GR19): one use, a blow against the weapon's Armour and Hit Points,
and whether it can be used.

GR-T10's STOPP 0: the floor below `ap` is what stops a blow from healing a
weapon (at `ap` the formula itself gives 0); the row is asked before the
condition, so an item that is no weapon raises and an old weapon with no
condition is left alone; `usable` raises for nothing; the error is a
`ValueError` naming the item and its tag.

Every expected condition is worked by hand from §3's rows: the club 4/4,
the target shield 4/12.
"""

from evennia.prototypes.spawner import spawn
from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

from world import gear
from world.crafting_base import MongooseCraftRecipe

CHARACTER = "typeclasses.characters.Character"


class _Items(EvenniaTest):
    character_typeclass = CHARACTER

    def _spawn(self, prototype_key, condition=None):
        obj = spawn(prototype_key)[0]
        self.addCleanup(obj.delete)
        if condition is not None:
            obj.condition = condition
        return obj

    def _made(self, typeclass, key, prototype_key):
        """An item made by hand with the tag `spawn` gives (spawner.py:1013)."""
        obj = create.create_object(typeclass, key=key)
        obj.tags.add(prototype_key, category=gear.PROTOTYPE_TAG_CATEGORY)
        self.addCleanup(obj.delete)
        return obj

    def _old_club(self):
        """A club made before GR-T2: a plain Object, its tag and no condition."""
        return self._made("typeclasses.objects.Object", "club", "club")

    def _shield(self):
        """GR-T12 adds the prototype; until then the row, on a Weapon."""
        return self._made("typeclasses.weapons.Weapon", "target shield", "target_shield")


class TestTheConstant(_Items):
    def test_a_use_takes_one(self):
        self.assertEqual(gear.WEAPON_WEAR_PER_USE, 1)


class TestAUse(_Items):
    def test_a_use_takes_one_from_a_club(self):
        club = self._spawn("club")
        self.assertEqual(gear.wear_weapon(club), 99)
        self.assertEqual(club.attributes.get("condition"), 99)

    def test_a_knife_wears_on_one_axis_at_two_rates(self):
        # GR13: 40 from the prototype, 5 a craft, 1 a blow.
        knife = self._spawn("stone_knife")
        self.assertEqual(knife.condition, 40)
        knife.apply_wear(MongooseCraftRecipe.tool_wear)
        self.assertEqual(knife.condition, 35)
        self.assertEqual(gear.wear_weapon(knife), 34)


class TestABlow(_Items):
    def test_a_blow_below_the_armour_points_takes_nothing(self):
        # The floor's own case: without it 3 - 4 is a gain of 25.
        club = self._spawn("club")
        self.assertEqual(gear.damage_weapon(club, 3), 100)
        self.assertEqual(club.condition, 100)

    def test_a_blow_at_the_armour_points_takes_nothing(self):
        club = self._spawn("club")
        self.assertEqual(gear.damage_weapon(club, 4), 100)

    def test_one_past_the_armour_points_takes_a_quarter(self):
        # 100 x 1 / 4: the floor moved up by one would take nothing (GRM35).
        club = self._spawn("club")
        self.assertEqual(gear.damage_weapon(club, 5), 75)

    def test_two_past_takes_half(self):
        club = self._spawn("club")
        self.assertEqual(gear.damage_weapon(club, 6), 50)

    def test_four_past_breaks_it_and_no_lower(self):
        club = self._spawn("club")
        self.assertEqual(gear.damage_weapon(club, 8), 0)
        self.assertEqual(gear.damage_weapon(club, 12), 0)
        self.assertEqual(club.condition, 0)

    def test_the_share_is_of_the_hit_points_and_rounds_up(self):
        # 100 x 2 / 12 is 16.67, so 17; divided by the Armour Points it is 50.
        shield = self._shield()
        self.assertEqual(gear.damage_weapon(shield, 6), 83)

    def test_a_blow_on_a_worn_club_comes_off_what_is_left(self):
        club = self._spawn("club", condition=60)
        self.assertEqual(gear.damage_weapon(club, 6), 10)


class TestWhatIsNotAWeapon(_Items):
    def test_a_tunic_raises_and_is_not_worn(self):
        tunic = self._spawn("wool_tunic")
        for door, args in ((gear.wear_weapon, ()), (gear.damage_weapon, (6,))):
            with self.subTest(door=door.__name__):
                with self.assertRaises(ValueError) as caught:
                    door(tunic, *args)
                self.assertIn(f"#{tunic.id}", str(caught.exception))
                self.assertIn("'wool_tunic'", str(caught.exception))
        self.assertEqual(tunic.condition, 100)

    def test_an_item_with_neither_row_nor_condition_raises(self):
        # The row is asked first (STOPP 0, val 2): a stone is not passed over.
        bullet = self._spawn("sling_bullet")
        with self.assertRaises(ValueError):
            gear.wear_weapon(bullet)
        with self.assertRaises(ValueError):
            gear.damage_weapon(bullet, 6)

    def test_an_old_club_is_left_alone(self):
        club = self._old_club()
        self.assertIsNone(gear.wear_weapon(club))
        self.assertIsNone(gear.damage_weapon(club, 8))
        self.assertIsNone(club.attributes.get("condition"))


class TestUsable(_Items):
    def test_a_club_above_nought_is_usable(self):
        for condition in (100, 1):
            with self.subTest(condition=condition):
                self.assertTrue(gear.usable(self._spawn("club", condition=condition)))

    def test_a_broken_club_is_not(self):
        self.assertFalse(gear.usable(self._spawn("club", condition=0)))

    def test_a_broken_club_can_still_be_held(self):
        club = self._spawn("club", condition=0)
        club.location = self.char1
        hands, reason = gear.hold(self.char1, club)
        self.assertIsNone(reason)
        self.assertEqual(hands, (gear.RIGHT,))

    def test_what_is_no_weapon_reads_false_and_raises_nothing(self):
        for item in (self._spawn("wool_tunic"), self._spawn("stone"), self._old_club()):
            with self.subTest(item=item.key):
                self.assertFalse(gear.usable(item))
