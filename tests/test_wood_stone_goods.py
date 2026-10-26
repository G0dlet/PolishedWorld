"""
Unit tests for the AC4.3 wood-and-stone catalogue batch.

The five recipes turn real wood, stone, bone, twine and cloth prototypes into a
quarterstaff, a spear, a bow, milling stones and a tent. These tests inspect
spawned and crafted objects rather than comparing entries in world/prototypes.py
with one another: a broken spawn path or an Attribute that never reaches the
object must fail here.

The recipe-detail test goes through the live recipe registry and its production
renderer. It pins material quantities, optional tools, durations and the E.1
skill floors. Only the tent is knowledge-gated. One refusal proves the recipe is
unlearned; another learns it and sits one below its floor. Both check that real
inputs and the needle survive untouched. The four tooled crafts wear their real
knife or needle, while milling stones craft with no tool at all.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_wood_stone_goods
"""

from unittest import mock

from evennia.contrib.game_systems.crafting.crafting import craft
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaTest

from typeclasses.objects import Object
from world.knowledge import render_recipe_detail_by_name


# Independent expectations transcribed from Decomposition Rev 3, section 9.
# They are deliberately not imported from either production data module.
WOOD_STONE_GOODS = (
    {
        "prototype": "quarterstaff", "recipe": "quarterstaff",
        "key": "quarterstaff", "typeclass": Object,
        "materials": (("wood", 2),), "tool": "knife",
        "tool_prototype": "stone_knife", "enc": 2, "duration": 30,
        "learnable": False, "min_skill": 20,
    },
    {
        "prototype": "spear", "recipe": "spear", "key": "spear",
        "typeclass": Object,
        "materials": (("wood", 2), ("bone", 1), ("twine", 1)),
        "tool": "knife", "tool_prototype": "stone_knife", "enc": 2,
        "duration": 30, "learnable": False, "min_skill": 20,
    },
    {
        "prototype": "bow", "recipe": "bow", "key": "bow",
        "typeclass": Object, "materials": (("wood", 1), ("twine", 1)),
        "tool": "knife", "tool_prototype": "stone_knife", "enc": 1,
        "duration": 45, "learnable": False, "min_skill": 60,
    },
    {
        "prototype": "milling_stones", "recipe": "milling stones",
        "key": "milling stones", "typeclass": Object,
        "materials": (("stone", 2),), "tool": None,
        "tool_prototype": None, "enc": 2, "duration": 30,
        "learnable": False, "min_skill": 20,
    },
    {
        "prototype": "tent", "recipe": "tent", "key": "tent",
        "typeclass": Object,
        "materials": (("cloth", 4), ("wood", 2), ("twine", 2)),
        "tool": "needle", "tool_prototype": "bone_needle", "enc": 2,
        "duration": 45, "learnable": True, "min_skill": 60,
    },
)


class TestWoodStoneGoods(EvenniaTest):
    """Drive the shipped prototypes, recipe registry and crafting pipeline."""

    character_typeclass = "typeclasses.characters.Character"

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
        if expected["prototype"] == "milling_stones":
            # WHY: milling stones are inert goods, not the registry's grindstone
            # or any other crafting tool, so no crafting_tool tag may leak in.
            self.assertFalse(
                obj.tags.get(category="crafting_tool", return_list=True)
            )

    def assert_crafted_good(self, result, expected, materials):
        """Check the real product and consumption shared by both craft paths."""
        # A None result must fail clearly here, not as a TypeError from len().
        self.assertIsNotNone(result)
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
        return product

    def test_spawned_prototypes_build_with_catalogue_properties(self):
        self.assertEqual(len(WOOD_STONE_GOODS), 5)  # guard against a vacuous loop
        for expected in WOOD_STONE_GOODS:
            with self.subTest(prototype=expected["prototype"]):
                obj = spawn(expected["prototype"])[0]
                self.assert_built_good(obj, expected)

    def test_registered_recipe_details_match_the_brief(self):
        for expected in WOOD_STONE_GOODS:
            with self.subTest(recipe=expected["recipe"]):
                detail = render_recipe_detail_by_name(expected["recipe"])
                self.assertIsNotNone(detail)
                for material, quantity in expected["materials"]:
                    self.assertIn(f"{quantity}x {material}", detail)
                if expected["tool"] is None:
                    self.assertIn("none needed", detail)
                else:
                    self.assertIn(f"{expected['tool']} (optional", detail)
                self.assertIn(f"{expected['duration']} seconds", detail)
                self.assertIn(f"Craft {expected['min_skill']}% minimum", detail)
                self.assertIn(expected["prototype"].replace("_", " "), detail)

    def test_unlearned_tent_preserves_real_inputs_and_needle(self):
        expected = WOOD_STONE_GOODS[-1]
        self.assertEqual(expected["prototype"], "tent")  # guard the tuple lookup
        # A high skill ensures refusal cannot pass because of a skill floor
        # instead of the knowledge gate under test.
        self.char1.skills.get("craft").current = 100
        materials = self.materials_for(expected)
        (needle,) = self.give("bone_needle")
        condition = needle.condition
        # The negative case first proves its own premise: the tent recipe is
        # unlearned, so the refusal below tests the knowledge gate.
        self.assertFalse(self.char1.knows_recipe(expected["recipe"]))

        result = craft(self.char1, expected["recipe"], *materials, needle)

        self.assertFalse(result)
        self.assertEqual(self.crafted(expected["recipe"]), [])
        for obj in [*materials, needle]:
            self.assertIsNotNone(obj.pk)
            self.assertEqual(obj.location, self.char1)
        self.assertEqual(needle.condition, condition)

    def test_tent_one_below_its_floor_is_refused_with_inputs_kept(self):
        expected = WOOD_STONE_GOODS[-1]
        self.assertEqual(expected["prototype"], "tent")  # guard the tuple lookup
        self.assertTrue(self.char1.learn_recipe(expected["recipe"]))
        # Receipt: the knowledge gate is satisfied, so only the skill floor can
        # refuse this craft. The brief pins the tent to rung 60.
        self.assertTrue(self.char1.knows_recipe(expected["recipe"]))
        self.assertEqual(expected["min_skill"], 60)
        self.char1.skills.get("craft").current = expected["min_skill"] - 1
        self.assertEqual(self.char1.skills.get("craft").value, 59)
        materials = self.materials_for(expected)
        (needle,) = self.give("bone_needle")
        condition = needle.condition

        with mock.patch.object(self.char1, "msg") as msg:
            result = craft(self.char1, expected["recipe"], *materials, needle)

        self.assertFalse(result)
        self.assertEqual(self.crafted(expected["recipe"]), [])
        for obj in [*materials, needle]:
            self.assertIsNotNone(obj.pk)
            self.assertEqual(obj.location, self.char1)
        self.assertEqual(needle.condition, condition)
        self.assertTrue(
            any(
                "Your Craft is too unskilled (need 60%)." in str(call)
                for call in msg.call_args_list
            ),
            msg.call_args_list,
        )

    def test_tooled_recipes_craft_real_goods_and_wear_only_tools(self):
        tooled = [good for good in WOOD_STONE_GOODS if good["tool"] is not None]
        self.assertEqual(len(tooled), 4)  # milling stones are deliberately absent
        for expected in tooled:
            with self.subTest(recipe=expected["recipe"]):
                # For an ungated good, this still-false knowledge assertion is
                # the premise: it must craft without first being learned.
                self.assertFalse(self.char1.knows_recipe(expected["recipe"]))
                if expected["learnable"]:
                    self.assertTrue(self.char1.learn_recipe(expected["recipe"]))
                materials = self.materials_for(expected)
                (tool,) = self.give(expected["tool_prototype"])
                condition = tool.condition

                # WHY: crafting at exactly the brief's floor proves the floor is
                # inclusive (>=), and the brief's rung, not a higher skill, admits
                # the craft.
                self.char1.skills.get("craft").current = expected["min_skill"]
                result = craft(self.char1, expected["recipe"], *materials, tool)

                self.assert_crafted_good(result, expected, materials)
                self.assertIsNotNone(tool.pk)
                self.assertEqual(tool.location, self.char1)
                self.assertLess(tool.condition, condition)

    def test_milling_stones_craft_with_no_tool(self):
        expected = WOOD_STONE_GOODS[3]
        self.assertEqual(expected["prototype"], "milling_stones")
        # The recipe is common, so no learning step may be necessary.
        self.assertFalse(self.char1.knows_recipe(expected["recipe"]))
        stones = self.give("stone", "stone")

        # No tool argument and no tool in the inventory: this is the hand-shaped
        # StoneKnifeRecipe shape, with no improvised-tool penalty.
        self.char1.skills.get("craft").current = expected["min_skill"]
        result = craft(self.char1, expected["recipe"], *stones)

        self.assert_crafted_good(result, expected, stones)
