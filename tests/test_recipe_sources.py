"""
Every knowledge-gated recipe has a way into the world. Launch Minimum, Task L3.3
(decision LM9).

WHY THIS TEST EXISTS
--------------------
`requires_knowledge = True` partitions the registry: a gated recipe can be
crafted only by someone who knows it, and knowledge only moves from someone who
already has it (scroll, book and teach need a sender; reverse-engineering needs
a crafted item, BACKLOG `:779-780`). So a gated recipe needs a *bootstrap* -- a
profession that grants it at chargen, or a scroll seeded into the world. One
with neither is a sink with no source: nobody can ever learn it.

Thirteen of the seventeen gated recipes shipped that way through three
decompositions (Alpha Content B5, CC6, E.2), because nothing counted. This test
is the count, so the next recipe batch cannot ship another.

WHAT IT CHECKS
--------------
1. Every `requires_knowledge` recipe in the registry has at least one source: a
   `PROFESSIONS` grant or a `seed_data.SCROLLS` row. The failure message names
   the recipes that have none.
2. Every `SCROLLS` row names a registry recipe with `requires_knowledge = True`
   -- `learn` refuses a scroll of a common recipe, so such a row would seed an
   object nobody can use.

It reads both tables live: it is a cross-check between two tables and the
registry, not a restatement of one of them (lesson 74). The floor is one
source, not LM9's seeding rule of "fewer than two grantors": a recipe with one
profession grantor passes here with or without its scroll.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_recipe_sources
"""
from evennia.contrib.game_systems.crafting.crafting import (
    _load_recipes,
    _RECIPE_CLASSES,
)
from evennia.utils.test_resources import EvenniaTestCase

from world import seed_data
from world.professions import PROFESSIONS


def gated_recipes():
    """Names of every registry recipe with requires_knowledge = True, sorted."""
    _load_recipes()
    return sorted(
        name
        for name, cls in _RECIPE_CLASSES.items()
        if getattr(cls, "requires_knowledge", False)
    )


class TestRecipeSources(EvenniaTestCase):
    def test_the_registry_has_gated_recipes(self):
        # Vacuity guard: an empty gated set would pass the source test.
        self.assertTrue(gated_recipes())

    def test_every_knowledge_gated_recipe_has_a_source(self):
        granted = {
            recipe
            for package in PROFESSIONS.values()
            for recipe in package["recipes"]
        }
        seeded = {row["recipe"] for row in seed_data.SCROLLS}
        sourceless = [
            name for name in gated_recipes()
            if name not in granted and name not in seeded
        ]
        self.assertEqual(
            sourceless, [],
            f"knowledge-gated recipes with no profession grant and no seeded "
            f"scroll: {sourceless}",
        )

    def test_every_scroll_row_names_a_knowledge_gated_recipe(self):
        gated = set(gated_recipes())
        for row in seed_data.SCROLLS:
            with self.subTest(seed_id=row["seed_id"]):
                self.assertIn(row["recipe"], gated)
