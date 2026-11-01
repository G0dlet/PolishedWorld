"""
AC5.1 / E.1: pin the recipe catalogue's declared Craft-skill ladder.

Each test guards a different failure mode. The declaration test catches a recipe
that silently inherits the base floor or drifts from the locked 29-recipe table.
The catalogue-shape test catches a missing zero rung, a lowered ceiling, or a
progression gap too wide for the trivial band, read live from `trivial_band()`
as the E.2 gate reads it; its override twin proves the read is live, and the
ceiling test ties `ladder_top()` to the ceiling pinned here. Its negative
fixtures keep that checker honest with a band of their own, so a calibration of
the game's band cannot break them: a helper that always returns no violations
must not make the catalogue test pass. The bootstrap test protects the survival
loop from an accidental floor. Finally, the input-chain test reads real prototype
tags and catches a product whose floor sits below the recipe that makes one of
its inputs, which would make the progression depend on another crafter bypassing
the intended ladder.
"""

from django.test import override_settings
from evennia.contrib.game_systems.crafting.crafting import (
    _load_recipes,
    _RECIPE_CLASSES,
)
from evennia.prototypes.prototypes import search_prototype
from evennia.utils.test_resources import EvenniaTestCase

from world.knowledge import ladder_top, trivial_band


LADDER = {
    "twine": 0,
    "sling bullet": 0,
    "stone knife": 0,
    "bone needle": 0,
    "stone axe": 0,
    "waterskin": 0,
    "cloth": 20,
    "leather": 20,
    "hood": 20,
    "bandolier": 20,
    "scrollcase": 20,
    "sling": 20,
    "club": 20,
    "quarterstaff": 20,
    "spear": 20,
    "milling stones": 20,
    "linen shirt": 40,
    "breeches": 40,
    "sack": 40,
    "backpack": 40,
    "shoes": 40,
    "leather boots": 40,
    "robe": 60,
    "reversible clothes": 60,
    "linen cuirass": 60,
    "saddlebag": 60,
    "bone armour": 60,
    "tent": 60,
    "bow": 60,
}

# The registry's top rung today. When smithing lands a higher rung, this line
# and the registry change in the same commit; test_ladder_top_is_the_ceiling is
# what says so.
ALPHA_LADDER_CEILING = 60
# The checker fixtures' own band, not the game's: the catalogue reads the live
# SKILL_TRIVIAL_BAND through trivial_band(). The fixtures are built around 30
# (wide_gap's gap is 40, valid's is 20), so a calibration to 40 would stop
# wide_gap being bad and one below 20 would make valid bad; neither is a fault
# in the checker.
FIXTURE_BAND = 30
BOOTSTRAP = ("stone knife", "bone needle", "stone axe", "twine", "waterskin")

MATERIAL_CATEGORY = "crafting_material"


def ladder_violations(values, ceiling, band):
    """Return every way a rung collection breaks the ladder's three rules."""
    rungs = sorted(set(values))
    violations = []
    if not rungs or rungs[0] != 0:
        violations.append("the ladder must start at rung 0")
    if not rungs or rungs[-1] != ceiling:
        violations.append(f"the ladder must reach ceiling {ceiling}")
    for lower, upper in zip(rungs, rungs[1:]):
        if upper - lower > band:
            violations.append(f"rung gap {lower} -> {upper} exceeds band {band}")
    return violations


class TestMinSkillLadder(EvenniaTestCase):
    """Check the live recipe registry, not a second hand-maintained registry."""

    def setUp(self):
        super().setUp()
        _load_recipes()
        self.recipes = dict(_RECIPE_CLASSES)

    def test_every_recipe_declares_its_rung(self):
        self.assertEqual(len(LADDER), 29)
        self.assertEqual(len(self.recipes), 29)
        self.assertEqual(set(self.recipes), set(LADDER))
        for name, expected in LADDER.items():
            with self.subTest(recipe=name):
                cls = self.recipes[name]
                self.assertIn("min_skill", cls.__dict__)
                self.assertEqual(cls.min_skill, expected)

    def catalogue_violations(self):
        """The catalogue against the band the E.2 gate reads, read now."""
        values = [cls.min_skill for cls in self.recipes.values()]
        return ladder_violations(values, ALPHA_LADDER_CEILING, trivial_band())

    def test_the_catalogue_ladders_to_its_ceiling(self):
        self.assertEqual(self.catalogue_violations(), [])

    def test_the_catalogue_reads_the_live_band(self):
        # The rungs are 20 apart, so a band of 10 opens every gap. A checker
        # that kept its own 30 would report none (TW15).
        with override_settings(SKILL_TRIVIAL_BAND=10):
            self.assertEqual(trivial_band(), 10)  # receipt: the override landed
            self.assertEqual(
                self.catalogue_violations(),
                [
                    "rung gap 0 -> 20 exceeds band 10",
                    "rung gap 20 -> 40 exceeds band 10",
                    "rung gap 40 -> 60 exceeds band 10",
                ],
            )

    def test_ladder_top_is_the_ceiling(self):
        self.assertEqual(ladder_top(), ALPHA_LADDER_CEILING)

    def test_the_checker_flags_bad_ladders(self):
        wide_gap = [0, 20, 60]
        widest_gap = max(
            upper - lower for lower, upper in zip(wide_gap, wide_gap[1:])
        )
        self.assertEqual(widest_gap, 40)
        self.assertTrue(
            ladder_violations(wide_gap, ALPHA_LADDER_CEILING, FIXTURE_BAND)
        )

        no_zero = [20, 40, 60]
        self.assertNotEqual(min(no_zero), 0)
        self.assertTrue(
            ladder_violations(no_zero, ALPHA_LADDER_CEILING, FIXTURE_BAND)
        )

        low_ceiling = [0, 20, 40]
        self.assertNotEqual(max(low_ceiling), ALPHA_LADDER_CEILING)
        self.assertTrue(
            ladder_violations(low_ceiling, ALPHA_LADDER_CEILING, FIXTURE_BAND)
        )

        valid = [0, 20, 40, 60]
        self.assertEqual((min(valid), max(valid)), (0, ALPHA_LADDER_CEILING))
        self.assertLessEqual(
            max(upper - lower for lower, upper in zip(valid, valid[1:])),
            FIXTURE_BAND,
        )
        self.assertEqual(
            ladder_violations(valid, ALPHA_LADDER_CEILING, FIXTURE_BAND),
            [],
        )

    def test_bootstrap_recipes_sit_at_zero(self):
        self.assertEqual(len(BOOTSTRAP), 5)  # guard against a vacuous loop
        for name in BOOTSTRAP:
            with self.subTest(recipe=name):
                self.assertEqual(self.recipes[name].min_skill, 0)

    def test_no_product_sits_below_a_maker_of_its_input(self):
        producers = {}
        for cls in self.recipes.values():
            for prototype_key in cls.output_prototypes or []:
                matches = search_prototype(prototype_key, no_db=True)
                self.assertEqual(
                    len(matches),
                    1,
                    f"expected one module prototype for {prototype_key}",
                )
                prototype = matches[0]
                for tag in prototype.get("tags", []):
                    if tag[1] == MATERIAL_CATEGORY:
                        producers.setdefault(tag[0], set()).add(cls.name)

        # Receipt: crafted intermediates really are in the map before the loop
        # below relies on it; otherwise missing tags would make it pass vacuously.
        self.assertEqual(producers.get("cloth"), {"cloth"})
        self.assertEqual(producers.get("leather"), {"leather"})
        self.assertEqual(producers.get("twine"), {"twine"})

        for cls in self.recipes.values():
            for tag in cls.consumable_tags or []:
                for producer_name in producers.get(tag, set()):
                    with self.subTest(
                        consumer=cls.name,
                        material=tag,
                        producer=producer_name,
                    ):
                        self.assertGreaterEqual(
                            cls.min_skill,
                            self.recipes[producer_name].min_skill,
                        )
