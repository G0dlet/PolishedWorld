"""
Unit tests for the AC4.2 leather-and-bone catalogue batch.

The seven recipes turn real leather and bone prototypes into a backpack, a
scrollcase, a saddlebag, shoes, a bandolier, bone armour and a sling. These
tests inspect spawned and crafted objects rather than comparing entries in
world/prototypes.py with one another: a broken spawn path or an Attribute that
never reaches the object must fail here.

The recipe-detail test goes through the live recipe registry and its production
renderer. It pins material quantities, optional tools, durations and absence of
a skill floor from the AC4.0 brief. Six recipes are knowledge-gated; the sling
is common and must craft without first being learned. Every refused craft first
proves that its recipe is unlearned, then checks that real inputs and the tool
survive untouched.

The garment-quality test pins the d100 to a fumble and reads each crafted
garment's condition: shoes, bandolier and bone armour must route through
_apply_garment_quality (shoddy -> 50) rather than keep the DurableObject default
of 100. The four plain Objects get no garment finalizer.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_leather_goods
"""

from unittest import mock

from evennia.contrib.game_systems.crafting.crafting import craft
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaTest

from typeclasses.clothing import ClothingWithBuffs
from typeclasses.objects import Object
from world.crafting_quality import SHODDY, quality_band
from world.knowledge import render_recipe_detail_by_name


# Independent expectations transcribed from Decomposition Rev 3, section 9.
# They are deliberately not imported from either production data module.
LEATHER_GOODS = (
    {
        "prototype": "backpack", "recipe": "backpack", "key": "backpack",
        "typeclass": Object, "materials": (("leather", 2),),
        "tool": "needle", "tool_prototype": "bone_needle", "slot": None,
        "warmth": None, "enc": 1, "duration": 40, "learnable": True,
    },
    {
        "prototype": "scrollcase", "recipe": "scrollcase", "key": "scrollcase",
        "typeclass": Object, "materials": (("bone", 1),),
        "tool": "knife", "tool_prototype": "stone_knife", "slot": None,
        "warmth": None, "enc": 0, "duration": 30, "learnable": True,
    },
    {
        "prototype": "saddlebag", "recipe": "saddlebag", "key": "saddlebag",
        "typeclass": Object, "materials": (("leather", 3),),
        "tool": "needle", "tool_prototype": "bone_needle", "slot": None,
        "warmth": None, "enc": 2, "duration": 45, "learnable": True,
    },
    {
        "prototype": "shoes", "recipe": "shoes", "key": "shoes",
        "typeclass": ClothingWithBuffs, "materials": (("leather", 1),),
        "tool": "needle", "tool_prototype": "bone_needle", "slot": "shoes",
        "warmth": 1, "enc": 0, "duration": 40, "learnable": True,
    },
    {
        "prototype": "bandolier", "recipe": "bandolier", "key": "bandolier",
        "typeclass": ClothingWithBuffs, "materials": (("leather", 1),),
        "tool": "needle", "tool_prototype": "bone_needle", "slot": "accessory",
        "warmth": 0, "enc": 0, "duration": 30, "learnable": True,
    },
    {
        "prototype": "bone_armour", "recipe": "bone armour", "key": "bone armour",
        "typeclass": ClothingWithBuffs,
        "materials": (("bone", 3), ("leather", 1)),
        "tool": "knife", "tool_prototype": "stone_knife", "slot": "top",
        "warmth": 1, "enc": 2, "duration": 45, "learnable": True,
    },
    {
        "prototype": "sling", "recipe": "sling", "key": "sling",
        "typeclass": Object, "materials": (("leather", 1),),
        "tool": "knife", "tool_prototype": "stone_knife", "slot": None,
        "warmth": None, "enc": 0, "duration": 30, "learnable": False,
    },
)


class TestLeatherGoods(EvenniaTest):
    """Drive the shipped prototypes, recipe registry and crafting pipeline."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        # WHY: B9 leaves min_skill at the base floor of zero. Crafting at zero
        # makes an accidental batch-specific skill floor fail behaviourally.
        self.char1.skills.get("craft").current = 0

    def give(self, *prototype_keys):
        """Spawn real inputs into char1's inventory."""
        objs = []
        for prototype_key in prototype_keys:
            obj = spawn(prototype_key)[0]
            obj.location = self.char1
            objs.append(obj)
        return objs

    def materials_for(self, expected):
        """Spawn the brief's real materials, expanding repeated quantities."""
        prototype_keys = [
            prototype
            for prototype, quantity in expected["materials"]
            for _ in range(quantity)
        ]
        return self.give(*prototype_keys)

    def tool_for(self, expected):
        """Spawn the real optional tool used by this recipe."""
        return self.give(expected["tool_prototype"])[0]

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
        self.assertEqual(len(LEATHER_GOODS), 7)  # guard against a vacuous loop
        for expected in LEATHER_GOODS:
            with self.subTest(prototype=expected["prototype"]):
                obj = spawn(expected["prototype"])[0]
                self.assert_built_good(obj, expected)

    def test_registered_recipe_details_match_the_brief(self):
        for expected in LEATHER_GOODS:
            with self.subTest(recipe=expected["recipe"]):
                detail = render_recipe_detail_by_name(expected["recipe"])
                self.assertIsNotNone(detail)
                for material, quantity in expected["materials"]:
                    self.assertIn(f"{quantity}x {material}", detail)
                self.assertIn(f"{expected['tool']} (optional", detail)
                self.assertIn(f"{expected['duration']} seconds", detail)
                self.assertIn("no minimum", detail)
                self.assertIn(expected["prototype"].replace("_", " "), detail)

    def test_unlearned_learnable_recipes_preserve_real_inputs(self):
        learnable = [good for good in LEATHER_GOODS if good["learnable"]]
        self.assertEqual(len(learnable), 6)  # the sling is deliberately absent
        # A high skill ensures refusal cannot pass because of a skill floor
        # instead of the knowledge gate under test.
        self.char1.skills.get("craft").current = 100
        for expected in learnable:
            with self.subTest(recipe=expected["recipe"]):
                materials = self.materials_for(expected)
                tool = self.tool_for(expected)
                condition = tool.condition
                # The negative case first proves its own premise: this recipe
                # is unlearned, so the refusal below tests the knowledge gate.
                self.assertFalse(self.char1.knows_recipe(expected["recipe"]))

                result = craft(self.char1, expected["recipe"], *materials, tool)

                self.assertFalse(result)
                self.assertEqual(self.crafted(expected["recipe"]), [])
                for obj in [*materials, tool]:
                    self.assertIsNotNone(obj.pk)
                    self.assertEqual(obj.location, self.char1)
                self.assertEqual(tool.condition, condition)

    def test_recipes_craft_real_goods_and_consume_only_materials(self):
        for expected in LEATHER_GOODS:
            with self.subTest(recipe=expected["recipe"]):
                self.char1.skills.get("craft").current = 0
                self.assertFalse(self.char1.knows_recipe(expected["recipe"]))
                if expected["learnable"]:
                    self.assertTrue(self.char1.learn_recipe(expected["recipe"]))
                # For the sling, the still-false knowledge assertion above is
                # the premise: a common recipe must craft without learning it.
                materials = self.materials_for(expected)
                tool = self.tool_for(expected)
                condition = tool.condition

                result = craft(self.char1, expected["recipe"], *materials, tool)

                self.assertEqual(len(result), 1)
                product = result[0]
                self.assertEqual(product.location, self.char1)
                self.assertEqual(product.db.recipe, expected["recipe"])
                self.assertTrue(
                    product.tags.has(expected["prototype"], category="from_prototype")
                )
                self.assert_built_good(product, expected)
                for obj in materials:
                    self.assertIsNone(obj.pk)
                self.assertIsNotNone(tool.pk)
                self.assertEqual(tool.location, self.char1)
                self.assertLess(tool.condition, condition)

    def test_fumbled_garments_are_born_shoddy_worn(self):
        """A fumbled garment starts at shoddy condition, not the default.

        Pressures each garment recipe's _finalize_item: without it the crafted
        object keeps DurableObject's default condition of 100.
        """
        garments = [good for good in LEATHER_GOODS if good["slot"] is not None]
        self.assertEqual(len(garments), 3)  # guard against a vacuous loop
        for expected in garments:
            with self.subTest(recipe=expected["recipe"]):
                self.char1.skills.get("craft").current = 0
                # Receipt: an uncrafted spawn sits at the default, so 50 below
                # can only come from the finalize hook.
                self.assertEqual(spawn(expected["prototype"])[0].condition, 100)
                self.assertFalse(self.char1.knows_recipe(expected["recipe"]))
                self.assertTrue(self.char1.learn_recipe(expected["recipe"]))
                materials = self.materials_for(expected)
                tool = self.tool_for(expected)

                # 100 is the "00" face: a fumble at any target below 100.
                with mock.patch("world.skillcheck.randint", return_value=100):
                    result = craft(self.char1, expected["recipe"], *materials, tool)

                self.assertEqual(len(result), 1)
                product = result[0]
                self.assertEqual(quality_band(product.db.quality), SHODDY)
                self.assertEqual(product.condition, 50)
