"""
E.2 / T1.1: the trivial-work rule, before anything calls it.

`world.knowledge.routine_for(crafter, recipe_cls)` is the whole policy: a
recipe is routine when it sits below the registry's top rung and the crafter's
permanent skill (`.current`) stands more than `SKILL_TRIVIAL_BAND` points above
its `min_skill`. Each class below pressures one way that sentence can go wrong:

* TestLadderTop -- the top rung is read from the live registry on every call
  (a cache would freeze the exemption at today's 60).
* TestBandBoundary -- the comparison is strict, on both sides of two floors.
* TestReadsCurrentOnly -- `.value` (mods, buffs, overload) and mastery move
  nothing.
* TestTopRungExemption -- the top rung always teaches, and the exemption
  follows `ladder_top()` rather than a hard-coded 60.
* TestSettingAndFallbacks -- the band comes from settings per call, clamps at
  0, and a crafter without skills is never routine.
* TestImports -- `world.knowledge` and `world.crafting_base` import together
  (T2.1 will make the second import the first).
"""

import importlib
from types import SimpleNamespace
from unittest import mock

from django.test import override_settings
from evennia.contrib.game_systems.crafting.crafting import _RECIPE_CLASSES
from evennia.utils.test_resources import EvenniaTest

from world import knowledge
from world.knowledge import ladder_top, routine_for, trivial_band
from world.recipes import BowRecipe, ClothRecipe, TwineRecipe


class TrivialWorkTestBase(EvenniaTest):
    """char1's Craft trait with no modifier, so `.value == .current` to start."""

    def setUp(self):
        super().setUp()
        self.craft = self.char1.skills.craft
        self.craft.mod = 0

    def routine_at(self, current, recipe_cls=TwineRecipe):
        self.craft.current = current
        return routine_for(self.char1, recipe_cls)


class TestLadderTop(EvenniaTest):
    def test_live_registry_top_is_the_alpha_ceiling(self):
        self.assertEqual(ladder_top(), 60)

    def test_reads_the_registry_at_call_time(self):
        # A one-entry registry, not an empty one: _load_recipes() refills an
        # empty registry in place (lesson 194), which would read 60 again.
        with mock.patch.dict(_RECIPE_CLASSES, {"twine": TwineRecipe}, clear=True):
            self.assertEqual(ladder_top(), 0)
        self.assertEqual(ladder_top(), 60)  # receipt: the patch was what moved it


class TestBandBoundary(TrivialWorkTestBase):
    def test_twine_floor_0_turns_routine_past_30(self):
        self.assertEqual(TwineRecipe.min_skill, 0)
        self.assertFalse(self.routine_at(30))
        self.assertTrue(self.routine_at(31))

    def test_cloth_floor_20_turns_routine_past_50(self):
        self.assertEqual(ClothRecipe.min_skill, 20)
        self.assertFalse(self.routine_at(50, ClothRecipe))
        self.assertTrue(self.routine_at(51, ClothRecipe))


class TestReadsCurrentOnly(TrivialWorkTestBase):
    def test_a_bonus_on_value_does_not_make_twine_routine(self):
        self.craft.current = 25
        self.craft.mod = 40
        self.assertEqual(self.craft.value, 65)  # .value is past the band
        self.assertFalse(routine_for(self.char1, TwineRecipe))

    def test_a_penalty_on_value_does_not_make_twine_teach(self):
        # CounterTrait's mod setter clamps base + mod >= min, against *base*,
        # not current: with chargen's base (~20) a -40 mod lands as ~-20. Lift
        # base first so the full penalty applies; the gate never reads base.
        self.craft.base = 40
        self.craft.current = 40
        self.craft.mod = -40
        self.assertEqual(self.craft.value, 0)  # .value is at the floor
        self.assertTrue(routine_for(self.char1, TwineRecipe))

    def test_mastery_changes_nothing(self):
        self.char1.recipe_mastery.add("twine", 20)
        self.assertEqual(self.char1.recipe_mastery.count("twine"), 20)
        self.assertFalse(self.routine_at(25))
        self.assertTrue(self.routine_at(31))


class TestTopRungExemption(TrivialWorkTestBase):
    def test_a_rung_60_recipe_teaches_at_150(self):
        self.assertEqual(BowRecipe.min_skill, 60)
        self.assertFalse(self.routine_at(150, BowRecipe))

    def test_the_exemption_follows_ladder_top(self):
        self.assertTrue(self.routine_at(150))  # receipt: twine is routine here
        with mock.patch.object(knowledge, "ladder_top", return_value=0):
            self.assertFalse(self.routine_at(150))


class TestSettingAndFallbacks(TrivialWorkTestBase):
    def test_band_is_read_from_settings_per_call(self):
        self.assertEqual(trivial_band(), 30)
        with override_settings(SKILL_TRIVIAL_BAND=10):
            self.assertFalse(self.routine_at(10))
            self.assertTrue(self.routine_at(11))

    def test_negative_band_clamps_to_zero(self):
        with override_settings(SKILL_TRIVIAL_BAND=-5):
            self.assertEqual(trivial_band(), 0)
            self.assertFalse(self.routine_at(0))
            self.assertTrue(self.routine_at(1))

    def test_a_crafter_without_skills_is_never_routine(self):
        self.assertFalse(routine_for(SimpleNamespace(), TwineRecipe))
        self.assertFalse(routine_for(self.obj1, TwineRecipe))


class TestImports(EvenniaTest):
    def test_knowledge_and_crafting_base_import_together(self):
        crafting_base = importlib.import_module("world.crafting_base")
        knowledge_mod = importlib.import_module("world.knowledge")
        self.assertTrue(callable(knowledge_mod.routine_for))
        self.assertTrue(hasattr(crafting_base, "MongooseCraftRecipe"))
