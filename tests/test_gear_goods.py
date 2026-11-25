"""
Unit tests for Gear GR-T12: the target shield and four pieces of armour.

GR9-GR12 and GR24 add five items, each with a prototype, a recipe and -- for
the four gated pieces -- a scroll in the Old Temple. These tests follow the
goods modules' pattern (tests/test_leather_goods.py): they inspect spawned
and crafted objects, never one production dict against another, so a broken
spawn path or an Attribute that never reaches the object fails here.

The expectations below are transcribed from the Gear Decomposition, section
3 (the weapon rows, the armour rows and the recipes table), and from
GR-T12's STOPP 0 (keys, aliases, the hauberk's word, warmth 1). They are
deliberately not imported from world/prototypes.py, world/recipes.py or
world/gear.py.

WHAT EACH CLASS PRESSURES
-------------------------
- TestGearGoods: the five prototypes build with their class, key, alias,
  ENC, layer, warmth, word and repair data; the recipes read as the table
  says; the four gated recipes refuse the unlearned and keep the inputs; all
  five craft from real inputs at their floor; a fumble makes every one of
  them shoddy at 50 (GR21 for the shield, the garments' table for the four).
- TestTheItemsReadTheirRows: a made item reads its own row and only its own:
  the shield is a weapon and no garment (GRM41), each piece of armour wears
  its row's layer.
- TestTheWholeKitFromMadeItems: all six pieces, spawned, on one body: GR-T5's
  sums location by location, 17 Armour Points, Strike Rank four lower than
  bare and 16 ENC -- from made items, not the hand-tagged fixtures of
  tests/test_gear.py. The layer check and the sums read the row, not the
  item's `clothing_type`, so a hauberk of the rigid type (GRM42) changes
  none of them.
- TestTheWordTheLayersGive: what an item's `clothing_type` does decide is
  where it stands in the short description's order (GR7). Bone armour shows
  over the hauberk whichever went on first; a hauberk of the rigid type
  (GRM42) would leave the choice to the order of `contents`.

GRM43 (a scroll row dropped) is caught by tests/test_recipe_sources.py and
the seeding counts in tests/test_seeding.py, not here.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_gear_goods
"""

from unittest import mock

from evennia.contrib.game_systems.crafting.crafting import craft
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaTest

from typeclasses.clothing import ClothingWithBuffs
from typeclasses.weapons import Weapon
from world import body, gear, sdesc
from world.crafting_quality import SHODDY, quality_band
from world.encumbrance import item_enc
from world.knowledge import render_recipe_detail_by_name

# Independent expectations, transcribed from the Gear Decomposition section 3
# and GR-T12's STOPP 0.
GEAR_GOODS = (
    {
        "prototype": "target_shield", "recipe": "target shield",
        "key": "target shield", "alias": "shield", "typeclass": Weapon,
        "materials": (("wood", 2), ("leather", 1), ("bone", 1)),
        "tool": "knife", "tool_prototype": "stone_knife",
        "slot": None, "warmth": None, "look_word": None, "enc": 2,
        "repair": (("wood", "leather"), "knife"),
        "duration": 40, "learnable": False, "min_skill": 40,
    },
    {
        "prototype": "soft_leather_trews", "recipe": "soft leather trews",
        "key": "soft leather trews", "alias": "trews",
        "typeclass": ClothingWithBuffs, "materials": (("leather", 3),),
        "tool": "needle", "tool_prototype": "bone_needle",
        "slot": "armour_padding", "warmth": 1, "look_word": None, "enc": 3,
        "repair": (("leather", "twine"), "needle"),
        "duration": 40, "learnable": True, "min_skill": 40,
    },
    {
        "prototype": "bone_helm", "recipe": "bone helm",
        "key": "bone helm", "alias": "helm",
        "typeclass": ClothingWithBuffs,
        "materials": (("bone", 2), ("leather", 1)),
        "tool": "knife", "tool_prototype": "stone_knife",
        "slot": "armour_rigid", "warmth": 1, "look_word": None, "enc": 2,
        "repair": (("bone",), ""),
        "duration": 40, "learnable": True, "min_skill": 40,
    },
    {
        "prototype": "hard_leather_vambraces", "recipe": "hard leather vambraces",
        "key": "hard leather vambraces", "alias": "vambraces",
        "typeclass": ClothingWithBuffs, "materials": (("leather", 4),),
        "tool": "needle", "tool_prototype": "bone_needle",
        "slot": "armour_flexible", "warmth": 1, "look_word": None, "enc": 4,
        "repair": (("leather", "twine"), "needle"),
        "duration": 45, "learnable": True, "min_skill": 60,
    },
    {
        "prototype": "hard_leather_hauberk", "recipe": "hard leather hauberk",
        "key": "hard leather hauberk", "alias": "hauberk",
        "typeclass": ClothingWithBuffs, "materials": (("leather", 4),),
        "tool": "needle", "tool_prototype": "bone_needle",
        "slot": "armour_flexible", "warmth": 1, "look_word": "leather-clad",
        "enc": 4, "repair": (("leather", "twine"), "needle"),
        "duration": 45, "learnable": True, "min_skill": 60,
    },
)

# All six pieces of section 3, by prototype: the two that exist and the four
# GR-T12 adds.
SIX = (
    "linen_cuirass", "soft_leather_trews", "hard_leather_hauberk",
    "hard_leather_vambraces", "bone_armour", "bone_helm",
)


class TestGearGoods(EvenniaTest):
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
        """Spawn the table's real materials, expanding repeated quantities."""
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
        return [obj for obj in self.char1.contents if obj.db.recipe == recipe_name]

    def assert_built_good(self, obj, expected):
        """Assert properties on the built object, never on its source dict."""
        self.assertIs(type(obj), expected["typeclass"])
        self.assertEqual(obj.key, expected["key"])
        self.assertIn(expected["alias"], obj.aliases.all())
        self.assertEqual(obj.db.enc, expected["enc"])
        # What `repair` reads (commands/repair_commands.py): both are set, so
        # neither falls back to cloth, twine and a needle.
        materials, tool = expected["repair"]
        self.assertEqual(tuple(obj.db.repair_materials), materials)
        self.assertEqual(obj.db.repair_tool_tag, tool)
        self.assertEqual(obj.db.look_word, expected["look_word"])
        if expected["slot"] is not None:
            # These are the same Attributes the clothing and thermal systems read.
            self.assertEqual(obj.db.clothing_type, expected["slot"])
            self.assertEqual(obj.db.warmth, expected["warmth"])
        else:
            self.assertIsNone(obj.db.clothing_type)

    def test_spawned_prototypes_build_with_catalogue_properties(self):
        self.assertEqual(len(GEAR_GOODS), 5)  # guard against a vacuous loop
        for expected in GEAR_GOODS:
            with self.subTest(prototype=expected["prototype"]):
                obj = spawn(expected["prototype"])[0]
                self.assert_built_good(obj, expected)

    def test_registered_recipe_details_match_the_table(self):
        for expected in GEAR_GOODS:
            with self.subTest(recipe=expected["recipe"]):
                detail = render_recipe_detail_by_name(expected["recipe"])
                self.assertIsNotNone(detail)
                for material, quantity in expected["materials"]:
                    self.assertIn(f"{quantity}x {material}", detail)
                self.assertIn(f"{expected['tool']} (optional", detail)
                self.assertIn(f"{expected['duration']} seconds", detail)
                self.assertIn(f"Craft {expected['min_skill']}% minimum", detail)
                self.assertIn(expected["prototype"].replace("_", " "), detail)

    def test_unlearned_gated_recipes_preserve_real_inputs(self):
        learnable = [good for good in GEAR_GOODS if good["learnable"]]
        self.assertEqual(len(learnable), 4)  # the shield is a weapon, ungated
        # A high skill ensures refusal cannot pass because of a skill floor
        # instead of the knowledge gate under test.
        self.char1.skills.get("craft").current = 100
        for expected in learnable:
            with self.subTest(recipe=expected["recipe"]):
                materials = self.materials_for(expected)
                tool = self.tool_for(expected)
                condition = tool.condition
                self.assertFalse(self.char1.knows_recipe(expected["recipe"]))

                result = craft(self.char1, expected["recipe"], *materials, tool)

                self.assertFalse(result)
                self.assertEqual(self.crafted(expected["recipe"]), [])
                for obj in [*materials, tool]:
                    self.assertIsNotNone(obj.pk)
                    self.assertEqual(obj.location, self.char1)
                self.assertEqual(tool.condition, condition)

    def test_recipes_craft_real_goods_and_consume_only_materials(self):
        for expected in GEAR_GOODS:
            with self.subTest(recipe=expected["recipe"]):
                self.assertFalse(self.char1.knows_recipe(expected["recipe"]))
                if expected["learnable"]:
                    self.assertTrue(self.char1.learn_recipe(expected["recipe"]))
                # For the shield, the still-false knowledge assertion above is
                # the premise: a weapon recipe crafts without learning it.
                materials = self.materials_for(expected)
                tool = self.tool_for(expected)
                condition = tool.condition

                # At exactly the table's floor: the floor is inclusive.
                self.char1.skills.get("craft").current = expected["min_skill"]
                result = craft(self.char1, expected["recipe"], *materials, tool)

                # A refusal returns None: fail on that, not on a TypeError.
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
                self.assertIsNotNone(tool.pk)
                self.assertEqual(tool.location, self.char1)
                self.assertLess(tool.condition, condition)

    def test_fumbled_goods_are_born_shoddy_worn(self):
        """A fumble makes each of the five shoddy at 50, not the default 100.

        Pressures each recipe's _finalize_item: without the quality function
        the crafted object keeps DurableObject's default of 100 (GR21 for the
        shield; the garments' table for the four pieces).
        """
        for expected in GEAR_GOODS:
            with self.subTest(recipe=expected["recipe"]):
                # Receipt: an uncrafted spawn sits at the default, so 50 below
                # can only come from the finalize hook.
                self.assertEqual(spawn(expected["prototype"])[0].condition, 100)
                if expected["learnable"]:
                    self.assertTrue(self.char1.learn_recipe(expected["recipe"]))
                materials = self.materials_for(expected)
                tool = self.tool_for(expected)

                # 100 is the "00" face: a fumble at any target below 100.
                with mock.patch("world.skillcheck.randint", return_value=100):
                    self.char1.skills.get("craft").current = expected["min_skill"]
                    result = craft(self.char1, expected["recipe"], *materials, tool)

                self.assertIsNotNone(result)
                self.assertEqual(len(result), 1)
                product = result[0]
                self.assertEqual(quality_band(product.db.quality), SHODDY)
                self.assertEqual(product.condition, 50)


class TestTheItemsReadTheirRows(EvenniaTest):
    """
    Pressures the join between a made item and its row (GR16): the shield
    made a garment (GRM41) would read as no weapon in `wield`'s eyes only by
    accident, and could be worn; each piece of armour must carry its row's
    layer, or the layer check and the sums disagree with the row.
    """

    character_typeclass = "typeclasses.characters.Character"

    def _spawn(self, key):
        obj = spawn(key)[0]
        obj.location = self.char1
        self.addCleanup(obj.delete)
        return obj

    def test_the_shield_is_a_weapon_and_no_garment(self):
        shield = self._spawn("target_shield")
        self.assertIsInstance(shield, Weapon)
        self.assertNotIsInstance(shield, ClothingWithBuffs)
        self.assertEqual(gear.weapon(shield)["weapon_type"], "shield")
        self.assertIsNone(gear.armour(shield))

    def test_an_unwielded_shield_goes_to_the_left_hand(self):
        shield = self._spawn("target_shield")
        self.assertEqual(gear.hold(self.char1, shield), (("left",), None))

    def test_each_piece_reads_its_own_row_and_wears_its_layer(self):
        expected = {
            "soft_leather_trews": ("armour_padding", 1,
                                   ("abdomen", "right_leg", "left_leg")),
            "bone_helm": ("armour_rigid", 2, ("head",)),
            "hard_leather_vambraces": ("armour_flexible", 2,
                                       ("right_arm", "left_arm")),
            "hard_leather_hauberk": ("armour_flexible", 2, ("chest", "abdomen")),
        }
        for key, (layer, ap, locations) in expected.items():
            with self.subTest(item=key):
                piece = self._spawn(key)
                row = gear.armour(piece)
                self.assertIsNone(gear.weapon(piece))
                self.assertEqual(piece.db.clothing_type, layer)
                self.assertEqual(row["layer"], layer)
                self.assertEqual(row["ap"], ap)
                self.assertEqual(tuple(row["locations"]), locations)


class TestTheWholeKitFromMadeItems(EvenniaTest):
    """
    GR-T5's sums from spawned items, not the hand-tagged fixtures: a piece
    that does not go on, a prototype key that misses its row, or an `enc`
    that is not the book's moves a total.
    """

    character_typeclass = "typeclasses.characters.Character"

    BY_LOCATION = {
        "head": 2, "chest": 6, "abdomen": 3,
        "right_arm": 2, "left_arm": 2, "right_leg": 1, "left_leg": 1,
    }

    def _kit(self):
        kit = {}
        for key in SIX:
            piece = spawn(key)[0]
            piece.location = self.char1
            self.addCleanup(piece.delete)
            kit[key] = piece
        return kit

    def test_all_six_go_on_one_body(self):
        for key, piece in self._kit().items():
            with self.subTest(item=key):
                self.assertTrue(piece.wear(self.char1, True, quiet=True))

    def test_the_six_sum_location_by_location(self):
        for piece in self._kit().values():
            piece.wear(self.char1, True, quiet=True)
        self.assertEqual(
            {loc: gear.armour_at(self.char1, loc) for loc in body.LOCATIONS},
            self.BY_LOCATION,
        )
        self.assertEqual(gear.armour_total(self.char1), 17)

    def test_strike_rank_is_four_lower_than_bare(self):
        kit = self._kit()
        bare = body.derived(self.char1)["strike_rank"]
        for piece in kit.values():
            piece.wear(self.char1, True, quiet=True)
        result = body.derived(self.char1)
        self.assertEqual(result["armour_penalty"], 4)
        self.assertEqual(result["strike_rank"], bare - 4)

    def test_the_kit_is_sixteen_enc(self):
        self.assertEqual(sum(item_enc(piece) for piece in self._kit().values()), 16)


class TestTheWordTheLayersGive(EvenniaTest):
    """
    Pressures the hauberk's `clothing_type` where it is read: the short
    description's order of layers (GR7, OQ-GR5). A hauberk of the rigid type
    (GRM42) stands in the same layer as the bone armour, and which word
    shows is then the order of `contents`.
    """

    character_typeclass = "typeclasses.characters.Character"

    def _spawn(self, key):
        obj = spawn(key)[0]
        obj.location = self.char1
        self.addCleanup(obj.delete)
        return obj

    def test_a_hauberk_over_the_cuirass_reads_leather_clad(self):
        for key in ("linen_cuirass", "hard_leather_hauberk"):
            self.assertTrue(self._spawn(key).wear(self.char1, True, quiet=True))
        self.assertEqual(sdesc.garment_word(self.char1), "leather-clad")

    def test_bone_armour_shows_over_the_hauberk_whichever_went_on_first(self):
        for order in (("hard_leather_hauberk", "bone_armour"),
                      ("bone_armour", "hard_leather_hauberk")):
            with self.subTest(order=order):
                pieces = [self._spawn(key) for key in order]
                for piece in pieces:
                    self.assertTrue(piece.wear(self.char1, True, quiet=True))
                self.assertEqual(sdesc.garment_word(self.char1), "bone-clad")
                for piece in pieces:
                    piece.remove(self.char1, quiet=True)
