"""
The healer's kit, its scroll, and `healing` (Healing Decomposition §8, HL-T6;
locks HL3, HL9).

Combat Design HL3: knowing the healer's kit's recipe is having the Healing
skill, and the trait is made at INT + POW the first time it is needed. HL9:
the kit is a durable item worn per operation. This file holds HL-T6's side:
the prototype and its typeclass, the recipe, the kit's condition by quality,
`repair` refusing it, the recipe's name as players type it, and the trait.

The numbers are transcribed here, not imported, so a change to the kit has to
change this file too (HL-T6's STOPP 0):

  * the recipe (OQ-HL8): leather, two bandages, twine and a bone, with the
    needle as its optional tool -- a needle is a tool, never consumed;
  * Craft 20 %, the floor the input chain forces (leather and the bandage
    sit at 20), and 30 seconds, rung 20's duration;
  * 10 condition per operation, and the start condition by quality --
    100, 90, 70 or 50 -- so 10, 9, 7 or 5 operations;
  * not mendable: a kit `repair` could restore would never be replaced;
  * Healing is INT + POW, from a table in world/skill_base.py and NOT from
    chargen.SKILL_BASE_PAIRS, and the trait is made by `ensure_healing`
    when a skill list is shown -- for a character who knows the recipe only.

The fixture's INT 12, DEX 9 and POW 17 give 29 by INT + POW and 21 by
INT + DEX, so the wrong pair cannot pass (tests.test_first_aid's numbers).

The scroll is placed by the seed (tests.test_seeding, a database seeded
before HL-T6 gets exactly this one) and counted as the recipe's source by
tests.test_recipe_sources.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_healers_kit
"""

from unittest import mock

from evennia.contrib.game_systems.crafting.crafting import craft
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest

from commands.character_commands import CmdProgress, CmdSheet, CmdSkills
from commands.crafting_commands import CmdCraftGated, CmdDisassemble, _resolve_recipe
from commands.repair_commands import CmdRepair
from typeclasses.healers_kit import HealersKit
from world import skill_base
from world.chargen import apply_allocation
from world.knowledge import render_recipe_detail_by_name


RECIPE = "healer's kit"
ROLL = "world.skillcheck.randint"
INPUTS = ("leather", "bandage", "bandage", "twine", "bone")
FLOOR = 20
DURATION = 30
OPERATION_WEAR = 10

# tests/test_chargen.py's legal allocation, as tests.test_first_aid reads it.
VALID = {"str": 7, "dex": 9, "con": 14, "siz": 8, "int": 12, "pow": 17, "cha": 13}
INT_POW = 29   # INT 12 + POW 17; INT + DEX would give 21

WORDS = ("butcher", "barber", "bonesetter", "physician", "surgeon", "master surgeon")

# d100 faces for each tier at Craft 20 with the needle carried (modifier 0),
# and the start condition each tier's quality band gives the kit.
FACES = (
    ("critical", 1, 100),
    ("success", 15, 90),
    ("failure", 50, 70),
    ("fumble", 100, 50),
)

HEALING_ROW = r"Healing\s+\d+%"


class _Kit(EvenniaCommandTest):
    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        for stat, value in VALID.items():
            self.char1.stats.get(stat).base = value
            self.char2.stats.get(stat).base = value

    def give(self, *prototype_keys, to=None):
        """Spawn real objects into a character's inventory."""
        holder = to or self.char1
        objs = []
        for prototype_key in prototype_keys:
            obj = spawn(prototype_key)[0]
            obj.location = holder
            objs.append(obj)
        return objs


class TestTheKit(_Kit):
    def test_the_prototype_builds_a_kit(self):
        (kit,) = spawn("healers_kit")
        self.assertIsInstance(kit, HealersKit)
        self.assertEqual(kit.key, "healer's kit")
        self.assertEqual(kit.db.enc, 1)   # Legend p. 114
        self.assertEqual(kit.condition, 100)

    def test_it_wears_ten_per_operation_and_is_never_mended(self):
        self.assertEqual(HealersKit.OPERATION_WEAR, OPERATION_WEAR)
        self.assertFalse(HealersKit.mendable)

    def test_repair_refuses_it_and_keeps_the_materials(self):
        kit, cloth, twine = self.give("healers_kit", "cloth", "twine")
        kit.condition = 50
        self.call(CmdRepair(), "kit", "You can't mend")
        self.assertEqual(kit.condition, 50)
        self.assertIsNotNone(cloth.pk)
        self.assertIsNotNone(twine.pk)


class TestTheRecipe(_Kit):
    def test_the_recipe_card(self):
        detail = render_recipe_detail_by_name(RECIPE)
        self.assertIsNotNone(detail)
        for line in ("1x leather", "2x bandage", "1x twine", "1x bone"):
            with self.subTest(line=line):
                self.assertIn(line, detail)
        self.assertIn("needle", detail)
        self.assertIn(f"Craft {FLOOR}% minimum", detail)
        self.assertIn(f"{DURATION} seconds", detail)

    def test_the_name_as_players_type_it(self):
        recipe = _resolve_recipe(RECIPE)
        self.assertIsNotNone(recipe)
        self.assertEqual(recipe.name, RECIPE)
        for typed in ("healer", "kit"):
            with self.subTest(typed=typed):
                self.assertIs(_resolve_recipe(typed), recipe)
        # Without the apostrophe it is no prefix and no substring: the
        # prototype's alias finds the kit, but no recipe resolves.
        self.assertIsNone(_resolve_recipe("healers kit"))

    def test_craft_parses_the_apostrophe(self):
        cmd = CmdCraftGated()
        cmd.args = " Healer's Kit from leather, bandage using needle"
        cmd.parse()
        self.assertEqual(cmd.recipe, RECIPE)
        self.assertEqual(cmd.ingredients, ["leather", "bandage"])

    def test_a_character_who_has_not_learned_it_is_refused(self):
        self.assertFalse(self.char1.knows_recipe(RECIPE))
        inputs = self.give(*INPUTS)
        self.char1.skills.get("craft").current = FLOOR
        with mock.patch(ROLL, return_value=15):
            result = craft(self.char1, RECIPE, *inputs)
        self.assertFalse(result)
        for obj in inputs:
            self.assertIsNotNone(obj.pk)

    def test_the_kit_starts_at_its_quality_on_every_tier(self):
        self.assertEqual(len(FACES), 4)  # guard against a vacuous loop
        self.char1.learn_recipe(RECIPE)
        (needle,) = self.give("bone_needle")
        for tier, face, condition in FACES:
            with self.subTest(tier=tier):
                inputs = self.give(*INPUTS)
                self.char1.skills.get("craft").current = FLOOR
                with mock.patch(ROLL, return_value=face), \
                        mock.patch.object(self.char1, "msg"):
                    result = craft(self.char1, RECIPE, *inputs, needle)

                # A refusal returns None: fail on that, not on a TypeError.
                self.assertIsNotNone(result)
                (kit,) = result
                self.assertIsInstance(kit, HealersKit)
                self.assertEqual(kit.db.recipe, RECIPE)
                self.assertEqual(kit.condition, condition)
                for obj in inputs:
                    self.assertIsNone(obj.pk)
                kit.delete()


class TestTheSkill(_Kit):
    def test_its_pair_is_not_a_creation_pair(self):
        # HL2: apply_allocation refuses a character with a base pair and no
        # trait, and no character has Healing at creation.
        derived = apply_allocation(self.char1, VALID)
        self.assertNotIn("healing", derived)
        self.assertIsNone(self.char1.skills.get("healing"))

    def test_a_character_who_knows_the_recipe_gets_it_at_int_plus_pow(self):
        self.char1.learn_recipe(RECIPE)
        self.assertTrue(skill_base.knows_healing(self.char1))

        trait = skill_base.ensure_healing(self.char1)

        self.assertIsNotNone(trait)
        self.assertEqual(
            (trait.name, trait.trait_type, trait.base, trait.current, trait.mod),
            ("Healing", "counter", INT_POW, INT_POW, 0),
        )

    def test_a_second_call_leaves_a_trained_value(self):
        self.char1.learn_recipe(RECIPE)
        skill_base.ensure_healing(self.char1).current = 44

        again = skill_base.ensure_healing(self.char1)

        self.assertEqual(again.current, 44)
        self.assertEqual(again.base, INT_POW)

    def test_its_six_words(self):
        self.char1.learn_recipe(RECIPE)
        trait = skill_base.ensure_healing(self.char1)
        self.assertEqual(tuple(trait.descs.values()), WORDS)
        trait.current = 0
        self.assertEqual(trait.desc(), "butcher")
        trait.current = 100
        self.assertEqual(trait.desc(), "master surgeon")

    def test_a_character_who_does_not_know_it_gets_nothing(self):
        self.assertFalse(skill_base.knows_healing(self.char1))
        self.assertIsNone(skill_base.ensure_healing(self.char1))
        self.assertIsNone(self.char1.skills.get("healing"))

    def test_every_skill_list_makes_it_for_one_who_knows(self):
        self.char1.learn_recipe(RECIPE)
        for cmd in (CmdSkills, CmdProgress, CmdSheet):
            with self.subTest(command=cmd.key):
                if self.char1.skills.get("healing") is not None:
                    self.char1.skills.remove("healing")
                self.assertIsNone(self.char1.skills.get("healing"))
                shown = self.call(cmd(), "")
                self.assertRegex(shown, HEALING_ROW)
                self.assertEqual(self.char1.skills.get("healing").base, INT_POW)

    def test_no_skill_list_makes_it_for_one_who_does_not(self):
        for cmd in (CmdSkills, CmdProgress, CmdSheet):
            with self.subTest(command=cmd.key):
                shown = self.call(cmd(), "")
                self.assertNotRegex(shown, HEALING_ROW)
                self.assertIsNone(self.char1.skills.get("healing"))

    def test_a_spent_kit_taken_apart_can_teach_the_skill(self):
        # disassemble reads no condition: the last use of a broken kit.
        (kit,) = self.give("healers_kit")
        kit.db.recipe = RECIPE          # the stamp a crafted kit carries
        kit.condition = 0
        self.char1.skills.get("craft").current = 60
        with mock.patch(ROLL, return_value=1):
            self.call(CmdDisassemble(), "kit")
        self.assertTrue(self.char1.knows_recipe(RECIPE))
        self.assertRegex(self.call(CmdSheet(), ""), HEALING_ROW)
