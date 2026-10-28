"""
Tests for world/professions.py (Character Creation, Task CC2.1).

Each class presses one bug:

    TestGrantRecipes     the recipe half of the contract broken by the new
                         package shape (iterating the package teaches recipes
                         called "recipes" and "skill_bonus"); an unknown key
                         that writes anything
    TestGrantBonus       a bonus written to `.base` only -- invisible to the
                         XP floor, which reads `.current`
    TestGrantOnce        a second call that adds the bonus again; a second
                         call with another key that changes the trade
    TestGrantRefuses     a half-applied profession (recipes learned or the
                         sentinel stamped before a missing skill is found)
    TestProfessionList   the `profession` list printing the package's keys
                         instead of its recipes
    TestProfessionRegistry  a skill_bonus key that is no skill ("crafting"
                         for "craft") -- caught here, by profession name,
                         instead of as a ValueError at a player's grant (CC2.2)

These are the first tests of grant_profession(): before CC2.1 it had none.

THE FIXTURE (lesson 111)
------------------------
Each bonus test first applies chargen's VALID allocation, so Craft starts at
21 (DEX 9 + INT 12), not the default character's 20. The expected values
below are written out by hand -- 31 after the bonus -- never computed from
PROFESSIONS: a test that read the table it checks would prove nothing
(lesson 74).
"""

from unittest import mock

from evennia.utils.test_resources import (
    EvenniaCommandTest,
    EvenniaTest,
    EvenniaTestCase,
)

from commands.character_commands import CmdChooseProfession
from world.chargen import STAT_KEYS, apply_allocation, derive_skill_bases
from world.professions import PROFESSIONS, grant_profession
from world.progression import xp_threshold

# chargen's test fixture (tests/test_chargen.py), repeated here on purpose:
# a test module importing another test module couples the two suites.
VALID = {"str": 7, "dex": 9, "con": 14, "siz": 8, "int": 12, "pow": 17, "cha": 13}

CRAFT_AFTER_ALLOCATION = 21   # DEX 9 + INT 12
CRAFT_AFTER_BONUS = 31        # + 10, every profession (CC2.1, L1)

UNTOUCHED_SKILLS = ("athletics", "perception", "stealth", "hunting")

# CC2.2 guard: the four seeded professions. Fewer means the data failed to
# load and the per-profession loop would pass vacuously.
MIN_PROFESSIONS = 4


def _skill_pairs(character):
    return {
        key: (character.skills.get(key).base, character.skills.get(key).current)
        for key in character.skills.all()
    }


class TestGrantRecipes(EvenniaTest):
    """The recipe half of the contract, unchanged by the package shape."""

    def test_weaver_learns_both_recipes_in_bundle_order(self):
        learned = grant_profession(self.char1, "weaver")
        self.assertEqual(learned, ["cloth", "linen shirt"])
        self.assertTrue(self.char1.knows_recipe("cloth"))
        self.assertTrue(self.char1.knows_recipe("linen shirt"))

    def test_package_keys_are_not_learned_as_recipes(self):
        grant_profession(self.char1, "weaver")
        self.assertFalse(self.char1.knows_recipe("recipes"))
        self.assertFalse(self.char1.knows_recipe("skill_bonus"))

    def test_already_known_recipe_is_not_returned(self):
        self.char1.learn_recipe("cloth")
        self.assertEqual(grant_profession(self.char1, "generalist"), ["leather"])

    def test_unknown_key_warns_and_writes_nothing(self):
        before = _skill_pairs(self.char1)
        with mock.patch("world.professions.logger.log_warn") as warn:
            self.assertEqual(grant_profession(self.char1, "wizard"), [])
        warn.assert_called_once()
        self.assertIn("'wizard'", warn.call_args.args[0])
        self.assertEqual(self.char1.known_recipes(), [])
        self.assertEqual(_skill_pairs(self.char1), before)
        self.assertIsNone(self.char1.db.profession)


class TestGrantBonus(EvenniaTest):
    """The bonus lands on .base AND .current, and only on craft."""

    def setUp(self):
        super().setUp()
        apply_allocation(self.char1, VALID)
        craft = self.char1.skills.get("craft")
        # The fixture differs from the default it replaces (lesson 111).
        self.assertEqual((craft.base, craft.current), (21, 21))
        self.before = _skill_pairs(self.char1)
        grant_profession(self.char1, "tanner")

    def test_craft_base_and_current_both_move(self):
        craft = self.char1.skills.get("craft")
        self.assertEqual(craft.base, CRAFT_AFTER_BONUS)
        self.assertEqual(craft.current, CRAFT_AFTER_BONUS)

    def test_xp_floor_reads_the_bonus(self):
        # Absent-entry rule (B.2): the floor is xp_threshold(.current). A
        # bonus on .base alone leaves this at xp_threshold(21).
        self.assertEqual(
            self.char1.skill_xp.get("craft"), xp_threshold(CRAFT_AFTER_BONUS)
        )
        self.assertNotEqual(
            xp_threshold(CRAFT_AFTER_BONUS), xp_threshold(CRAFT_AFTER_ALLOCATION)
        )

    def test_other_skills_untouched(self):
        after = _skill_pairs(self.char1)
        for key in UNTOUCHED_SKILLS:
            with self.subTest(skill=key):
                self.assertEqual(after[key], self.before[key])

    def test_sentinel_is_stamped(self):
        self.assertEqual(self.char1.db.profession, "tanner")


class TestGrantOnce(EvenniaTest):
    """db.profession makes the grant a once-per-character event."""

    def setUp(self):
        super().setUp()
        apply_allocation(self.char1, VALID)
        grant_profession(self.char1, "weaver")
        self.after_first = _skill_pairs(self.char1)
        self.assertEqual(self.after_first["craft"], (31, 31))

    def test_second_call_same_key_adds_nothing(self):
        with mock.patch("world.professions.logger.log_warn") as warn:
            self.assertEqual(grant_profession(self.char1, "weaver"), [])
        warn.assert_not_called()  # a re-grant is quiet, not an error
        self.assertEqual(_skill_pairs(self.char1), self.after_first)

    def test_other_key_is_refused_and_warned(self):
        with mock.patch("world.professions.logger.log_warn") as warn:
            self.assertEqual(grant_profession(self.char1, "tanner"), [])
        warn.assert_called_once()
        self.assertEqual(self.char1.db.profession, "weaver")
        self.assertFalse(self.char1.knows_recipe("leather"))
        self.assertEqual(_skill_pairs(self.char1), self.after_first)


class TestGrantRefuses(EvenniaTest):
    """A missing bonus skill is found before the first write."""

    def test_missing_skill_raises_and_writes_nothing(self):
        self.char1.skills.remove("craft")
        self.assertIsNone(self.char1.skills.get("craft"))  # §11k
        with self.assertRaises(ValueError) as caught:
            grant_profession(self.char1, "weaver")
        self.assertIn("craft", str(caught.exception))
        self.assertEqual(self.char1.known_recipes(), [])
        self.assertIsNone(self.char1.db.profession)


class TestProfessionList(EvenniaCommandTest):
    """`profession` with no argument lists recipes and bonus, not dict keys."""

    def test_list_shows_recipes_and_bonus(self):
        out = self.call(CmdChooseProfession(), "", caller=self.char1)
        self.assertIn("weaver: cloth, linen shirt (craft +10)", out)
        self.assertIn("generalist: cloth, leather (craft +10)", out)
        self.assertNotIn("skill_bonus", out)

    def test_command_grants_bonus_once(self):
        self.call(CmdChooseProfession(), "cobbler", caller=self.char1)
        self.assertEqual(self.char1.db.profession, "cobbler")
        after_first = _skill_pairs(self.char1)
        self.assertEqual(after_first["craft"], (30, 30))  # default 20 + 10
        self.call(
            CmdChooseProfession(), "cobbler", "You have already taken up",
            caller=self.char1,
        )
        self.assertEqual(_skill_pairs(self.char1), after_first)


class TestProfessionRegistry(EvenniaTestCase):
    """Every skill_bonus key is a skill chargen derives (CC2.2)."""

    def setUp(self):
        super().setUp()
        # The key set comes from the derivation, not from PROFESSIONS: a test
        # that read the table it checks would prove nothing (lesson 74). Any
        # allocation gives the same keys; the values are irrelevant here.
        self.skill_keys = set(derive_skill_bases({key: 10 for key in STAT_KEYS}))

    def test_guard_data_is_not_empty(self):
        """Without data the loop below passes vacuously -- refuse that."""
        self.assertGreaterEqual(len(PROFESSIONS), MIN_PROFESSIONS)
        self.assertIn("craft", self.skill_keys)

    def test_every_bonus_key_is_a_derived_skill(self):
        for profession, package in sorted(PROFESSIONS.items()):
            for skill in package["skill_bonus"]:
                with self.subTest(profession=profession, skill=skill):
                    self.assertIn(skill, self.skill_keys)
