"""
Hero Points: the store and its readers. Hero Points decomposition, Task
HE-T1 (docs/PolishedWorld_Hero_Points_Decomposition.md; Combat Design
§4.13, HP1, HP4, HE3, HE6).

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
- `TestConstants`: the book's two at creation (HP1, core p. 87), the cap of
  four (HP4) and a game day per point (HE4 c), pinned as numbers, so a
  changed constant is a decision and not a slip.
- `TestPoints`: the reader's one trap. A missing Attribute is START, and a
  stored 0 is 0. `or START` -- the plausible wrong reader -- treats the
  0 as missing and hands a spent-out character two again (HEM1). The fresh
  character's test also holds that reading writes nothing: no backfill.
- `TestGlancingOn`: on with nothing stored, off while the Attribute is set,
  on again once it is removed (HE3). A reader that ignores the Attribute
  would leave the switch with no effect (HEM3).
- `TestImports`: HE6's direction. `world.wounds` will import this module,
  so this module imports nothing from the game's own packages -- in any
  spelling, including the repository's own `from world import x`. A blind
  list (only `world.wounds`) would miss the way round through `healing` or
  `survival_ticker`, which import `wounds` themselves. The census is tried
  on spellings it must catch, so a census that sees nothing is not mistaken
  for a clean module.

Mutations (HEM1-HEM3) are in `tools/mutants/he_t1.toml`, run with
`python tools/mutate.py tools/mutants/he_t1.toml`.
"""

import ast
from pathlib import Path

from django.test import SimpleTestCase
from evennia.utils.test_resources import EvenniaTest

from world import hero_points

ROOT = Path(__file__).resolve().parent.parent
GAME_PACKAGES = ("commands", "server", "typeclasses", "web", "world")


class TestConstants(SimpleTestCase):
    def test_start_is_two(self):
        self.assertEqual(hero_points.START, 2)

    def test_cap_is_four(self):
        self.assertEqual(hero_points.CAP, 4)

    def test_a_point_is_a_game_day(self):
        self.assertEqual(hero_points.GAME_SECONDS_PER_POINT, 86400)


class TestPoints(EvenniaTest):
    def test_a_fresh_character_reads_two_and_nothing_is_written(self):
        self.assertIsNone(self.char1.db.hero_points)
        self.assertEqual(hero_points.points(self.char1), 2)
        self.assertFalse(self.char1.attributes.has("hero_points"))

    def test_stored_zero_reads_zero(self):
        self.char1.db.hero_points = 0
        self.assertEqual(hero_points.points(self.char1), 0)

    def test_stored_three_reads_three(self):
        self.char1.db.hero_points = 3
        self.assertEqual(hero_points.points(self.char1), 3)


class TestGlancingOn(EvenniaTest):
    def test_on_with_nothing_stored(self):
        self.assertFalse(self.char1.attributes.has("hero_glancing_off"))
        self.assertTrue(hero_points.glancing_on(self.char1))

    def test_off_while_the_attribute_is_set(self):
        self.char1.db.hero_glancing_off = True
        self.assertFalse(hero_points.glancing_on(self.char1))

    def test_on_again_once_the_attribute_is_removed(self):
        self.char1.db.hero_glancing_off = True
        self.char1.attributes.remove("hero_glancing_off")
        self.assertTrue(hero_points.glancing_on(self.char1))


def game_imports(tree):
    """
    Every import in `tree` that reaches one of the game's own packages, as
    the module name written: `import world.x`, `from world.x import y`,
    `from world import x` (the repository's own style) and any relative
    import.
    """
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                found.append("." * node.level + (node.module or ""))
                continue
            names = [node.module]
        else:
            continue
        for name in names:
            top = name.split(".")[0]
            if top in GAME_PACKAGES:
                found.append(name)
    return found


class TestImports(SimpleTestCase):
    def test_the_census_sees_every_spelling(self):
        source = (
            "from world import wounds\n"
            "from world.healing import accrue\n"
            "import world.body\n"
            "import typeclasses.characters as c\n"
            "from . import survival_ticker\n"
            "import math\n"
            "from evennia.utils import logger\n"
        )
        self.assertEqual(
            game_imports(ast.parse(source)),
            ["world", "world.healing", "world.body", "typeclasses.characters", "."],
        )

    def test_the_module_imports_nothing_of_the_game(self):
        tree = ast.parse((ROOT / "world" / "hero_points.py").read_text(encoding="utf-8"))
        self.assertEqual(
            game_imports(tree), [],
            "HE6: world.wounds imports hero_points, never the other way round. "
            "hero_points imports nothing from the game's own packages, so no "
            "way round through a module that imports wounds either.",
        )
