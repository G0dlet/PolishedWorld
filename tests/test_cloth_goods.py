"""
Unit tests for the AC4.1 cloth-goods catalogue batch.

The six recipes turn real cloth prototypes into breeches, a robe, a hood,
reversible clothes, a linen cuirass and a sack. These tests inspect spawned and
crafted objects rather than comparing entries in world/prototypes.py with one
another: a broken spawn path or an Attribute that never reaches the object must
fail here.

The recipe-detail test goes through the live recipe registry and its production
renderer. It pins the cloth quantities, optional needle, durations and absence
of a skill floor from the AC4.0 brief. The crafting tests also exercise the
knowledge gate: an unlearned recipe consumes nothing, while a learned recipe
runs at Craft 0 and always yields under the inherited raw consume policy.

The garment-quality test pins the d100 to a fumble and reads the crafted
garment's condition: each of the five garments must route through
_apply_garment_quality (shoddy -> 50) like the linen shirt, rather than keep
the DurableObject default of 100. The sack is a plain Object with no wear
axis and is left out.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_cloth_goods
"""

from unittest import mock

from evennia.contrib.game_systems.crafting.crafting import craft
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaTest

from typeclasses.clothing import ClothingWithBuffs
from typeclasses.objects import Object
from world.crafting_quality import SHODDY, quality_band
from world.knowledge import render_recipe_detail_by_name


MATERIAL = "crafting_material"

# Independent expectations transcribed from Decomposition Rev 3, section 9.
# They are deliberately not imported from either production data module.
CLOTH_GOODS = (
    {
        "prototype": "breeches", "recipe": "breeches", "key": "breeches",
        "typeclass": ClothingWithBuffs, "cloth": 2, "slot": "bottom",
        "warmth": 1, "enc": 0, "duration": 40,
    },
    {
        "prototype": "robe", "recipe": "robe", "key": "robe",
        "typeclass": ClothingWithBuffs, "cloth": 3, "slot": "fullbody",
        "warmth": 1, "enc": 0, "duration": 45,
    },
    {
        "prototype": "hood", "recipe": "hood", "key": "hood",
        "typeclass": ClothingWithBuffs, "cloth": 1, "slot": "hat",
        "warmth": 1, "enc": 0, "duration": 30,
    },
    {
        "prototype": "reversible_clothes", "recipe": "reversible clothes",
        "key": "reversible clothes", "typeclass": ClothingWithBuffs,
        "cloth": 4, "slot": "top", "warmth": 1, "enc": 0, "duration": 45,
    },
    {
        "prototype": "linen_cuirass", "recipe": "linen cuirass",
        "key": "linen cuirass", "typeclass": ClothingWithBuffs,
        "cloth": 4, "slot": "top", "warmth": 1, "enc": 1, "duration": 45,
    },
    {
        "prototype": "sack", "recipe": "sack", "key": "large sack",
        "typeclass": Object, "cloth": 2, "slot": None,
        "warmth": None, "enc": 1, "duration": 40,
    },
)


class TestClothGoods(EvenniaTest):
    """Drive the shipped prototypes, recipe registry and crafting pipeline."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        # WHY: every AC4.1 recipe inherits the base floor of zero. Crafting at
        # zero makes an accidental batch-specific min_skill fail behaviourally.
        self.char1.skills.get("craft").current = 0

    def give(self, *prototype_keys):
        """Spawn real inputs into char1's inventory."""
        objs = []
        for prototype_key in prototype_keys:
            obj = spawn(prototype_key)[0]
            obj.location = self.char1
            objs.append(obj)
        return objs

    def carried_cloth(self):
        return [
            obj for obj in self.char1.contents
            if obj.tags.has("cloth", category=MATERIAL)
        ]

    def crafted(self, recipe_name):
        return [
            obj for obj in self.char1.contents
            if obj.db.recipe == recipe_name
        ]

    def assert_built_good(self, obj, expected):
        """Assert properties on the built object, never on its source dict."""
        self.assertIs(type(obj), expected["typeclass"])
        self.assertEqual(obj.key, expected["key"])
        self.assertEqual(obj.db.enc, expected["enc"])
        if expected["slot"] is not None:
            # These are the same Attributes the clothing and thermal systems read.
            self.assertEqual(obj.db.clothing_type, expected["slot"])
            self.assertEqual(obj.db.warmth, expected["warmth"])

    def test_spawned_prototypes_build_with_catalogue_properties(self):
        self.assertEqual(len(CLOTH_GOODS), 6)  # guard against a vacuous loop
        for expected in CLOTH_GOODS:
            with self.subTest(prototype=expected["prototype"]):
                obj = spawn(expected["prototype"])[0]
                self.assert_built_good(obj, expected)

    def test_registered_recipe_details_match_the_brief(self):
        for expected in CLOTH_GOODS:
            with self.subTest(recipe=expected["recipe"]):
                detail = render_recipe_detail_by_name(expected["recipe"])
                self.assertIsNotNone(detail)
                self.assertIn(f"{expected['cloth']}x cloth", detail)
                self.assertIn("needle (optional", detail)
                self.assertIn(f"{expected['duration']} seconds", detail)
                self.assertIn("no minimum", detail)
                self.assertIn(expected["prototype"].replace("_", " "), detail)

    def test_unlearned_recipes_preserve_real_inputs(self):
        # A high skill ensures a refusal cannot be passing because of a skill
        # floor instead of the knowledge gate under test.
        self.char1.skills.get("craft").current = 100
        for expected in CLOTH_GOODS:
            with self.subTest(recipe=expected["recipe"]):
                cloth = self.give(*(["cloth"] * expected["cloth"]))
                (needle,) = self.give("bone_needle")
                condition = needle.condition
                # §11k: the negative case shows it is what it claims -- the
                # recipe is unlearned -- before it is used.
                self.assertFalse(self.char1.knows_recipe(expected["recipe"]))

                result = craft(self.char1, expected["recipe"], *cloth, needle)

                self.assertFalse(result)
                self.assertEqual(self.crafted(expected["recipe"]), [])
                for obj in [*cloth, needle]:
                    self.assertIsNotNone(obj.pk)
                    self.assertEqual(obj.location, self.char1)
                self.assertEqual(needle.condition, condition)

    def test_learned_recipes_craft_real_goods_and_consume_only_cloth(self):
        for expected in CLOTH_GOODS:
            with self.subTest(recipe=expected["recipe"]):
                self.assertTrue(self.char1.learn_recipe(expected["recipe"]))
                cloth = self.give(*(["cloth"] * expected["cloth"]))
                (needle,) = self.give("bone_needle")
                condition = needle.condition

                result = craft(self.char1, expected["recipe"], *cloth, needle)

                self.assertEqual(len(result), 1)
                product = result[0]
                self.assertEqual(product.location, self.char1)
                self.assertEqual(product.db.recipe, expected["recipe"])
                self.assertTrue(
                    product.tags.has(expected["prototype"], category="from_prototype")
                )
                self.assert_built_good(product, expected)
                for obj in cloth:
                    self.assertIsNone(obj.pk)
                self.assertEqual(self.carried_cloth(), [])
                self.assertIsNotNone(needle.pk)
                self.assertEqual(needle.location, self.char1)
                self.assertLess(needle.condition, condition)

    def test_fumbled_garments_are_born_shoddy_worn(self):
        """A fumbled garment starts at the shoddy condition, not the default.

        Pressures each garment recipe's _finalize_item: without it the crafted
        object keeps DurableObject's default condition of 100.
        """
        garments = [g for g in CLOTH_GOODS if g["slot"] is not None]
        self.assertEqual(len(garments), 5)  # guard against a vacuous loop
        for expected in garments:
            with self.subTest(recipe=expected["recipe"]):
                # Receipt: an uncrafted spawn sits at the default, so 50 below
                # can only come from the finalize hook.
                self.assertEqual(spawn(expected["prototype"])[0].condition, 100)
                self.assertTrue(self.char1.learn_recipe(expected["recipe"]))
                cloth = self.give(*(["cloth"] * expected["cloth"]))
                (needle,) = self.give("bone_needle")

                # 100 is the "00" face: a fumble at any target below 100.
                with mock.patch("world.skillcheck.randint", return_value=100):
                    result = craft(self.char1, expected["recipe"], *cloth, needle)

                self.assertEqual(len(result), 1)
                product = result[0]
                self.assertEqual(quality_band(product.db.quality), SHODDY)
                self.assertEqual(product.condition, 50)
