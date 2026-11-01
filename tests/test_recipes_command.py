"""
Tests for the `recipes` command's mastery views (Recipe Mastery M4.2).

Covered:
* the discipline summary on bare `recipes` -- known = visible (common +
  learned), "N you can teach" through _can_transmit, the title from the highest
  single-recipe count (never the sum), highest tier only
* `recipes <discipline>` -- exact match, resolved before a recipe name, lists
  only visible recipes with "made N (+M)"
* `recipes <name>` -- the Made line after Skill and before Time, the next step
  until the cap, "you can teach this" only for a learned recipe at the
  threshold; the scroll path never shows any of it
* routine work (Trivial Work T3.1) -- the `(routine)` tag on the bare list and
  the "Teaches you:" line in `recipes <name>`, both read on `.current` through
  routine_for; per viewer, and never on a scroll

Counts are seeded with recipe_mastery.add, not driven crafts: the command only
reads the count, and crafts driven through self.call are slow and have their
own gaps (Testing Ref).

Output from self.call has colour codes stripped; the regexes allow any run of
spaces where the renderer pads a label, so the tests pin words, not columns.
"""

from unittest import mock

from evennia.contrib.game_systems.crafting.crafting import (
    _load_recipes,
    _RECIPE_CLASSES,
)
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest

from commands.crafting_commands import CmdRecipes
from typeclasses.characters import KNOWN_RECIPE_CATEGORY
from world.crafting_base import MongooseCraftRecipe
from world.recipes import (
    BackpackRecipe,
    LeatherBootsRecipe,
    LeatherRecipe,
    WaterskinRecipe,
)

LEATHER = LeatherRecipe.name
BOOTS = LeatherBootsRecipe.name
WATERSKIN = WaterskinRecipe.name
BACKPACK = BackpackRecipe.name


class _RecipesTestBase(EvenniaCommandTest):
    character_typeclass = "typeclasses.characters.Character"

    def recipes(self, args=""):
        return self.call(CmdRecipes(), args, caller=self.char1)

    def made(self, name, count):
        self.char1.recipe_mastery.add(name, count)


class TestRecipesSummary(_RecipesTestBase):
    """Bare `recipes`: one line per discipline after the list."""

    def test_fresh_character_counts_visible_recipes_in_order(self):
        out = self.recipes()
        # leatherwork: sling + waterskin are common; the seven learnable ones
        # are hidden and must not be counted.
        self.assertRegex(out, r"Leatherwork: 2 known\n")
        self.assertRegex(out, r"Stonework: 4 known\n")
        self.assertNotIn("you can teach", out)
        order = [out.index(f"{d}:") for d in
                 ("Weaving", "Leatherwork", "Stonework", "Bonework", "Woodwork")]
        self.assertEqual(order, sorted(order))

    def test_two_learned_recipes_add_to_known(self):
        self.char1.learn_recipe(LEATHER)
        self.char1.learn_recipe(BOOTS)
        self.assertRegex(self.recipes(), r"Leatherwork: 4 known\n")

    def test_teach_count_is_learned_recipes_at_threshold(self):
        self.char1.learn_recipe(LEATHER)
        self.char1.learn_recipe(BOOTS)
        self.made(LEATHER, 5)
        self.made(BOOTS, 4)
        self.made(WATERSKIN, 5)  # common: nothing to transmit, never counted
        self.assertIn("Leatherwork: 4 known, 1 you can teach.", self.recipes())

    def test_apprentice_at_five_on_one_recipe(self):
        self.made(WATERSKIN, 5)
        self.assertIn("Leatherwork: 2 known. Apprentice Leatherworker", self.recipes())

    def test_title_is_not_the_sum(self):
        # 3 + 3 = 6 would be Apprentice if counts were summed (RM21).
        self.char1.learn_recipe(LEATHER)
        self.char1.learn_recipe(BOOTS)
        self.made(LEATHER, 3)
        self.made(BOOTS, 3)
        out = self.recipes()
        self.assertRegex(out, r"Leatherwork: 4 known\n")
        self.assertNotIn("Apprentice", out)

    def test_highest_tier_only(self):
        for total, rank in ((10, "Journeyman"), (19, "Journeyman"), (20, "Master")):
            with self.subTest(total=total):
                self.char1.attributes.remove("recipe_mastery")
                self.made(WATERSKIN, total)
                out = self.recipes()
                self.assertIn(f"{rank} Leatherworker", out)
                for other in {"Apprentice", "Journeyman", "Master"} - {rank}:
                    self.assertNotIn(other, out)


class TestRecipesDiscipline(_RecipesTestBase):
    """`recipes <discipline>`."""

    def test_lists_visible_recipes_with_count(self):
        out = self.recipes("leatherwork")
        self.assertIn("Leatherwork recipes you can craft:", out)
        self.assertRegex(out, rf"{WATERSKIN}\s+made 0 \(\+0\)")
        self.assertNotIn(BACKPACK, out)
        self.assertNotIn(LEATHER + " ", out)

    def test_count_and_modifier_after_crafts(self):
        self.char1.learn_recipe(LEATHER)
        self.made(LEATHER, 5)
        out = self.recipes("leatherwork")
        self.assertRegex(out, rf"\n\s*{LEATHER}\s+made 5 \(\+5\)")
        self.assertIn("Apprentice Leatherworker", out)

    def test_recipe_prefix_of_a_discipline_is_the_recipe(self):
        # "leather" is a recipe and a prefix of "leatherwork": the discipline
        # match is exact, so this is the recipe's detail (RM23a).
        self.char1.learn_recipe(LEATHER)
        out = self.recipes("leather")
        self.assertIn("Needs:", out)
        self.assertNotIn("recipes you can craft", out)

    def test_discipline_resolves_before_a_recipe_of_the_same_name(self):
        # No real recipe is named after a discipline, so make one (RM23b).
        _load_recipes()  # loads only while the registry is empty

        class FakeWeaving(MongooseCraftRecipe):
            name = "weaving"
            requires_knowledge = False
            discipline = "weaving"
            consumable_tags = ["fiber"]
            output_prototypes = ["cloth"]

        with mock.patch.dict(_RECIPE_CLASSES, {"weaving": FakeWeaving}):
            out = self.recipes("weaving")
        self.assertIn("Weaving recipes you can craft:", out)
        self.assertNotIn("Needs:", out)

    def test_unknown_word_falls_through(self):
        self.assertIn("No recipe matches 'zzz'.", self.recipes("zzz"))


class TestRecipesDetail(_RecipesTestBase):
    """`recipes <name>`: the viewer's own lines inside the detail block."""

    def test_made_line_and_teach_at_threshold(self):
        self.char1.learn_recipe(LEATHER)
        self.made(LEATHER, 5)
        out = self.recipes(LEATHER)
        self.assertRegex(out, r"Made:\s+5, roll \+5, next step at 10")
        self.assertIn("you can teach this", out)
        self.assertLess(out.index("Skill:"), out.index("Made:"))
        self.assertLess(out.index("Made:"), out.index("Time:"))

    def test_below_threshold_no_teach(self):
        # RM24: a display that compared the count to 4 itself would say yes.
        self.char1.learn_recipe(LEATHER)
        self.made(LEATHER, 4)
        out = self.recipes(LEATHER)
        self.assertRegex(out, r"Made:\s+4, roll \+0, next step at 5")
        self.assertNotIn("you can teach this", out)

    def test_cap_has_no_next_step(self):
        self.char1.learn_recipe(LEATHER)
        self.made(LEATHER, 20)
        out = self.recipes(LEATHER)
        self.assertRegex(out, r"Made:\s+20, roll \+20\n")
        self.assertNotIn("next step", out)

    def test_common_recipe_is_never_teachable(self):
        # Force the known tag so _can_transmit alone would say yes: the
        # requires_knowledge check is what keeps it off (RM24b), the same
        # "Everyone already knows this" the teach command answers.
        self.char1.tags.add(WATERSKIN, category=KNOWN_RECIPE_CATEGORY)
        self.made(WATERSKIN, 5)
        out = self.recipes(WATERSKIN)
        self.assertRegex(out, r"Made:\s+5, roll \+5")
        self.assertNotIn("you can teach this", out)

    def test_scroll_shows_no_reader_counts(self):
        # The renderer is shared with the scroll; the count is the viewer's,
        # not the scroll's (RM24d).
        self.char1.learn_recipe(LEATHER)
        self.made(LEATHER, 5)
        scroll = spawn("scroll")[0]
        scroll.stamp(LEATHER)
        scroll.move_to(self.char1, quiet=True)
        desc = scroll.get_display_desc(self.char1)
        self.assertIn("Skill:", desc)
        self.assertNotIn("Made:", desc)
        self.assertNotIn("you can teach this", desc)


class TestRecipesRoutine(_RecipesTestBase):
    """
    T3.1 (E.2, TD6): the player can see which recipes still teach before
    crafting. Twine (floor 0) is the edge case at Craft 30 vs 31, leather
    (floor 20, learned) at 50 vs 51; with the band at 30 the first of each pair
    teaches and the second is routine.

    The bugs this presses on: the tag read on `.value` (TW12, from both sides),
    the verdict drawn inside the shared renderer, where a scroll would carry it
    to every reader (TW13; lesson 188), and the line computed for the wrong
    viewer. Every negative check sits beside a positive receipt that the thing
    it looks inside was drawn (the twine line, the Skill line).
    """

    TAGGED = r"(?m)^\s+twine \(routine\)$"
    PLAIN = r"(?m)^\s+twine$"

    def at(self, current, mod=0, char=None):
        """Set Craft to `current` + `mod`: base first (lesson 199)."""
        trait = (char or self.char1).skills.get("craft")
        trait.base = current
        trait.current = current
        trait.mod = mod
        self.assertEqual(trait.value, current + mod)

    def test_the_list_tags_twine_at_31_and_not_at_30(self):
        self.at(30)
        out = self.recipes()
        self.assertRegex(out, self.PLAIN)
        self.assertNotRegex(out, self.TAGGED)
        self.at(31)
        self.assertRegex(self.recipes(), self.TAGGED)

    def test_a_bonus_on_value_does_not_tag(self):
        self.at(30, mod=40)                    # .value 70 would be routine
        out = self.recipes()
        self.assertRegex(out, self.PLAIN)
        self.assertNotRegex(out, self.TAGGED)

    def test_a_penalty_on_value_does_not_untag(self):
        self.at(31, mod=-1)                    # .value 30 would teach
        self.assertRegex(self.recipes(), self.TAGGED)

    def test_the_tag_follows_the_floor_note(self):
        self.char1.learn_recipe(LEATHER)
        self.at(51)
        self.assertRegex(self.recipes(), r"(?m)^\s+leather \(needs Craft 20%\) \(routine\)$")

    def test_detail_says_yes_at_50_and_no_at_51_beside_skill(self):
        self.char1.learn_recipe(LEATHER)
        self.at(50)
        out = self.recipes(LEATHER)
        self.assertRegex(out, r"Teaches you:\s+yes\n")
        self.assertLess(out.index("Skill:"), out.index("Teaches you:"))
        self.assertLess(out.index("Teaches you:"), out.index("Made:"))
        self.assertLess(out.index("Made:"), out.index("Time:"))
        self.at(51)
        self.assertRegex(
            self.recipes(LEATHER), r"Teaches you:\s+no -- this is routine work for you\n"
        )

    def test_the_verdict_is_the_viewers_own(self):
        # One recipe, two crafters a point apart: each sees their own answer.
        for char in (self.char1, self.char2):
            char.learn_recipe(LEATHER)
        self.at(51)
        self.at(50, char=self.char2)
        mine = self.recipes(LEATHER)
        theirs = self.call(CmdRecipes(), LEATHER, caller=self.char2)
        self.assertRegex(mine, r"Teaches you:\s+no")
        self.assertRegex(theirs, r"Teaches you:\s+yes")

    def test_a_scroll_carries_no_verdict(self):
        # The renderer is shared with the scroll (lesson 188): the reader at 51
        # sees "no" in `recipes`, and the scroll says nothing either way.
        self.char1.learn_recipe(LEATHER)
        self.at(51)
        self.assertRegex(self.recipes(LEATHER), r"Teaches you:\s+no")
        scroll = spawn("scroll")[0]
        scroll.stamp(LEATHER)
        scroll.move_to(self.char1, quiet=True)
        desc = scroll.get_display_desc(self.char1)
        self.assertIn("Skill:", desc)
        self.assertNotIn("Teaches", desc)
        self.assertNotIn("routine", desc)
