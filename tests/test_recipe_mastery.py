"""
Unit tests for the per-recipe completed-craft counter. Recipe Mastery, M1.1.

Written to the pattern in `tests/test_knowledge.py` (AGENTS.md section 0A) and
shaped after `tests/test_skill_xp.py`, whose handler this one copies.

WHAT IT COVERS
--------------
* world.recipe_mastery.RecipeMasteryHandler -- the store, the formula, the one
  writer
* world.knowledge.recipe_names -- the registry read `all()` goes through
* typeclasses.characters.Character.recipe_mastery -- the lazy_property wiring
* world.recipe_mastery.DISCIPLINES and MongooseCraftRecipe.discipline -- every
  registered recipe declares one (M4.1)

BASE CLASS
----------
`EvenniaTest`: the store is an Evennia Attribute, and the `_SaverDict` it reads
back as is the thing the Mapping tests exist for. No command is added in M1.

DELIBERATE DEVIATION FROM THE DECOMPOSITION
-------------------------------------------
Decomposition section 5 lists `add` with 0, -1 and "one" as raising
ValueError. A non-int raises TypeError here (and so does a bool), as in
`SkillXPHandler` and `CurrencyHandler`: one convention across the three
handlers. Locked 2026-10-30 (M1.1, B); the decomposition text is corrected in
M6.1.

MUTATIONS (RM1-RM5, decomposition section 5)
--------------------------------------------
RM1 MASTERY_STEP_SIZE -> 4          TestModifierAndStep reddens (5 at 9)
RM2 the cap dropped                 TestModifierAndStep reddens (20 at 57)
RM3 Mapping -> dict in count()      TestStoreRoundTrip reddens
RM4 add() returns without writing   TestCountAndAdd reddens (once/twice)
RM5 amount validation dropped       TestAmountValidation reddens

MUTATIONS (RM19-RM20, decomposition section 8, M4.1)
----------------------------------------------------
RM19  one recipe's discipline removed          TestDisciplines reddens (declares)
RM19b base default set to a discipline, and    TestDisciplines reddens (declares,
      one recipe's line removed                base)
RM20  a sixth discipline with no recipe        TestDisciplines reddens (used)

The registry is read here as `tests/test_min_skill_ladder.py` reads it, and
the declaration is checked in the class's own `__dict__` as that test checks
`min_skill`: an inherited value does not count as declared. Placed here rather
than beside test (g) in `tests/test_material_registry.py`, whose tests are about
materials; `DISCIPLINES` lives in `world/recipe_mastery.py`. Locked 2026-10-31
(M4.1, L2-L3); the decomposition text is corrected in M6.1.
"""

from collections.abc import Mapping

from evennia.contrib.game_systems.crafting.crafting import (
    _load_recipes,
    _RECIPE_CLASSES,
)
from evennia.utils.test_resources import EvenniaTest, EvenniaTestCase

from world.crafting_base import MongooseCraftRecipe
from world.knowledge import recipe_names
from world.recipe_mastery import (
    DISCIPLINES,
    MASTERY_CAP,
    MASTERY_STEP,
    MASTERY_STEP_SIZE,
    MASTERY_TRANSMIT_THRESHOLD,
    RecipeMasteryHandler,
)

TWINE = "twine"
WATERSKIN = "waterskin"
ORPHAN = "a recipe that was removed"


class TestConstants(EvenniaTest):
    """
    MD3 and MD5 as numbers. The bug this presses on: a constant edited for
    balance without the decomposition's arithmetic noticing -- full mastery is
    meant to cancel `improvised_penalty = -20` exactly, and the first step is
    meant to be the transmission threshold.
    """

    def test_locked_values(self):
        self.assertEqual(
            (MASTERY_STEP, MASTERY_STEP_SIZE, MASTERY_CAP, MASTERY_TRANSMIT_THRESHOLD),
            (5, 5, 20, 5),
        )


class TestCountAndAdd(EvenniaTest):
    """
    The counter itself. The bug this presses on: an `add` that does not write,
    or that overwrites instead of adding (RM4).
    """

    def test_unset_reads_zero_and_writes_nothing(self):
        self.assertEqual(self.char1.recipe_mastery.count(TWINE), 0)
        self.assertFalse(self.char1.attributes.has("recipe_mastery"))

    def test_add_once_then_twice(self):
        self.assertEqual(self.char1.recipe_mastery.add(TWINE), 1)
        self.assertEqual(self.char1.recipe_mastery.count(TWINE), 1)
        self.assertEqual(self.char1.recipe_mastery.add(TWINE), 2)
        self.assertEqual(self.char1.recipe_mastery.count(TWINE), 2)

    def test_add_an_amount(self):
        self.assertEqual(self.char1.recipe_mastery.add(TWINE, 3), 3)
        self.assertEqual(self.char1.recipe_mastery.count(TWINE), 3)

    def test_recipes_do_not_leak_into_each_other(self):
        self.char1.recipe_mastery.add(TWINE, 4)
        self.char1.recipe_mastery.add(WATERSKIN)
        self.assertEqual(self.char1.recipe_mastery.count(TWINE), 4)
        self.assertEqual(self.char1.recipe_mastery.count(WATERSKIN), 1)


class TestAmountValidation(EvenniaTest):
    """
    MD1's *an invalid amount raises*. The bug this presses on: a bad amount
    quietly counting -- `add(name, True)` would count a craft, `add(name, 0)`
    would write an entry -- or a rejected call corrupting the store (RM5).
    """

    def test_zero_and_negative_raise_value_error(self):
        with self.assertRaises(ValueError):
            self.char1.recipe_mastery.add(TWINE, 0)
        with self.assertRaises(ValueError):
            self.char1.recipe_mastery.add(TWINE, -1)

    def test_non_int_and_bool_raise_type_error(self):
        for bad in ("one", 2.5, True):
            with self.subTest(amount=bad):
                with self.assertRaises(TypeError):
                    self.char1.recipe_mastery.add(TWINE, bad)

    def test_a_rejected_amount_creates_no_attribute(self):
        with self.assertRaises(ValueError):
            self.char1.recipe_mastery.add(TWINE, 0)
        self.assertFalse(self.char1.attributes.has("recipe_mastery"))

    def test_a_rejected_amount_leaves_the_store_unchanged(self):
        self.char1.recipe_mastery.add(TWINE, 2)
        for bad in (0, -1, "one", True):
            with self.subTest(amount=bad):
                with self.assertRaises((TypeError, ValueError)):
                    self.char1.recipe_mastery.add(TWINE, bad)
                self.assertEqual(self.char1.recipe_mastery.count(TWINE), 2)


class TestModifierAndStep(EvenniaTest):
    """
    MD3's formula. The bug this presses on: a wrong step size (RM1) or a
    missing cap (RM2). Each count is reached by `add`, the only write path.
    """

    def _at(self, count):
        if count:
            self.char1.recipe_mastery.add(TWINE, count)
        return self.char1.recipe_mastery

    def test_modifier_table(self):
        table = {0: 0, 4: 0, 5: 5, 9: 5, 10: 10, 20: 20, 57: 20}
        for count, expected in table.items():
            with self.subTest(count=count):
                self.char1.attributes.remove("recipe_mastery")
                self.assertEqual(self._at(count).modifier(TWINE), expected)

    def test_step_at_the_first_boundary(self):
        self.assertEqual(self._at(4).step(TWINE), 0)
        self.char1.recipe_mastery.add(TWINE)
        self.assertEqual(self.char1.recipe_mastery.step(TWINE), 1)

    def test_unset_recipe_has_no_modifier(self):
        self.assertEqual(self.char1.recipe_mastery.modifier(WATERSKIN), 0)
        self.assertEqual(self.char1.recipe_mastery.step(WATERSKIN), 0)


class TestStoreRoundTrip(EvenniaTest):
    """
    The `_SaverDict` trap. The bug this presses on: `isinstance(store, dict)`
    (RM3), which is False for what Evennia hands back, so every read after the
    first write would see nothing.
    """

    def test_the_stored_value_is_a_mapping_and_not_a_dict(self):
        # A documentation receipt for why the handler tests through Mapping.
        self.char1.recipe_mastery.add(TWINE, 2)
        store = self.char1.attributes.get("recipe_mastery")
        self.assertIsInstance(store, Mapping)
        self.assertNotIsInstance(store, dict)
        self.assertEqual(store[TWINE], 2)

    def test_a_second_handler_reads_the_first_handlers_write(self):
        self.char1.recipe_mastery.add(TWINE, 3)
        fresh = RecipeMasteryHandler(self.char1)
        self.assertEqual(fresh.count(TWINE), 3)
        self.assertEqual(fresh.add(TWINE), 4)
        self.assertEqual(self.char1.recipe_mastery.count(TWINE), 4)


class TestAll(EvenniaTest):
    """
    The union. The bug this presses on: an orphaned name hidden, or a recipe
    never crafted missing from the view M4.2 builds on.
    """

    def test_registry_recipe_with_no_store_reads_zero(self):
        everything = self.char1.recipe_mastery.all()
        self.assertEqual(everything[WATERSKIN], 0)
        self.assertFalse(self.char1.attributes.has("recipe_mastery"))

    def test_stored_orphan_stays_visible(self):
        self.char1.recipe_mastery.add(ORPHAN, 2)
        self.char1.recipe_mastery.add(TWINE)
        everything = self.char1.recipe_mastery.all()
        self.assertEqual(everything[ORPHAN], 2)
        self.assertEqual(everything[TWINE], 1)

    def test_all_covers_exactly_registry_plus_store(self):
        self.char1.recipe_mastery.add(ORPHAN)
        everything = self.char1.recipe_mastery.all()
        self.assertIs(type(everything), dict)
        self.assertEqual(list(everything), sorted(set(recipe_names()) | {ORPHAN}))

    def test_recipe_names_reads_the_registry(self):
        names = recipe_names()
        self.assertIn(TWINE, names)
        self.assertIn(WATERSKIN, names)
        self.assertEqual(names, sorted(names))


class TestCharactersAndWiring(EvenniaTest):
    """
    Two characters, two Attributes; and the lazy_property is the handler. The
    bug this presses on: shared state between characters.
    """

    def test_two_characters_are_independent(self):
        self.char1.recipe_mastery.add(TWINE, 5)
        self.char2.recipe_mastery.add(TWINE)
        self.assertEqual(self.char1.recipe_mastery.count(TWINE), 5)
        self.assertEqual(self.char2.recipe_mastery.count(TWINE), 1)

    def test_wiring(self):
        handler = self.char1.recipe_mastery
        self.assertIsInstance(handler, RecipeMasteryHandler)
        self.assertIs(self.char1.recipe_mastery, handler)
        self.assertIs(handler.obj, self.char1)


class TestDisciplines(EvenniaTestCase):
    """Every registered recipe declares a discipline from the closed set (MD6)."""

    def setUp(self):
        super().setUp()
        _load_recipes()
        self.recipes = dict(_RECIPE_CLASSES)
        self.names = [name for name, _label in DISCIPLINES]

    def test_every_recipe_declares_a_known_discipline(self):
        self.assertEqual(len(self.recipes), 29)
        for name, cls in self.recipes.items():
            with self.subTest(recipe=name):
                self.assertIn("discipline", cls.__dict__)
                self.assertIn(cls.discipline, self.names)

    def test_every_discipline_has_a_recipe(self):
        used = {cls.discipline for cls in self.recipes.values()}
        for name in self.names:
            with self.subTest(discipline=name):
                self.assertIn(name, used)

    def test_the_base_is_not_a_recipe(self):
        # None, not a discipline: a recipe that forgets its line inherits
        # nothing that could pass the first test.
        self.assertIsNone(MongooseCraftRecipe.discipline)
