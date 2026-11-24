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

HE-T2, the earning (HE4):

- `TestAccrue`: the day's edge on both sides (one second short earns
  nothing; the second after earns one and carries nothing -- HEM8); a span
  of several days carries its remainder (HEM5); the cap stops the points
  (HEM4) and the counter both when it is reached (HEM6) and when it was
  already reached, even with a counter stored by hand (HEM7); a span of 0
  writes nothing; a missing store is two, so a day stores three.
- `TestTheTickEarns`: through `_deplete_character`. A collapsed body earns
  (HE4 a; the collapsed branch's own call is the receipt that it ran). The
  span is the tick's own `elapsed`, tried at 3000 game seconds, not the
  usual 2400, so a constant in the call is seen (HEM9). One line however
  many points land.
- `TestHeroCensus`: HE6 as code. The module's Attributes are named and are
  exactly what `world/hero_points.py` writes; no other production file
  writes an Attribute named `hero_*` (P-2); each door has its one named
  caller. The doors push nothing on purpose: no snapshot shows Hero Points
  (HE7), and `TestCharSnapshot.test_keys_and_types` pins the snapshot's
  keys, so CL's change is seen there.

HE-T3, the command `hero` and the switch (HE3):

- `TestSetGlancing`: the door. Off stores True; on removes the Attribute
  and never stores False (HEM11), so "on" has one form; a switch already
  where it is asked to be writes nothing -- seen by spies on the handler's
  `add` and `remove`, not by reading the value back, which a needless
  write would leave the same.
- `TestHeroCommand`: the screen at 2, 0 and 4; off, then the screen; off
  twice; on again; any case; a wrong word gets the usage; on and off not
  swapped (HEM10); a collapsed body is answered, since a switch is a
  choice and not an act (HEM12). The cap on the screen and in the help is
  read from `CAP`: with CAP patched to 7 they say 7, which a typed 4 could
  not (HEM13a, HEM13b). The help is read through Evennia's own `help`
  command on the character cmdset, which also proves the command is there.

Mutations: HEM1-HEM3 in `tools/mutants/he_t1.toml`, HEM4-HEM9 in
`tools/mutants/he_t2.toml`, HEM10-HEM13b in `tools/mutants/he_t3.toml`,
run with `python tools/mutate.py <spec>`.
"""

import ast
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase
from evennia.commands.default.help import CmdHelp
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.character_commands import (
    GLANCING_ALREADY,
    GLANCING_OFF,
    GLANCING_ON,
    HERO_USAGE,
    CmdHero,
)
from commands.default_cmdsets import CharacterCmdSet

# Functions only: a TestCase imported by name would run here a second time.
from tests.test_client_state import _functions, _production_trees
from world import hero_points, survival_ticker

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


DAY = hero_points.GAME_SECONDS_PER_POINT
HOUR = 3600


class TestAccrue(EvenniaTest):
    def test_one_second_short_of_a_day_earns_nothing(self):
        self.char1.db.hero_progress = DAY - 2
        self.assertEqual(hero_points.accrue(self.char1, 1), 0)
        self.assertFalse(self.char1.attributes.has("hero_points"))
        self.assertEqual(self.char1.db.hero_progress, DAY - 1)

    def test_the_second_after_earns_one_and_carries_nothing(self):
        self.char1.db.hero_progress = DAY - 1
        self.assertEqual(hero_points.accrue(self.char1, 1), 1)
        self.assertEqual(self.char1.db.hero_points, 3)
        self.assertEqual(self.char1.db.hero_progress, 0)

    def test_two_days_and_an_hour_earn_two_and_carry_the_hour(self):
        self.char1.db.hero_points = 0
        self.assertEqual(hero_points.accrue(self.char1, 2 * DAY + HOUR), 2)
        self.assertEqual(self.char1.db.hero_points, 2)
        self.assertEqual(self.char1.db.hero_progress, HOUR)

    def test_at_three_two_days_earn_one_and_leave_no_counter(self):
        self.char1.db.hero_points = 3
        self.assertEqual(hero_points.accrue(self.char1, 2 * DAY + HOUR), 1)
        self.assertEqual(self.char1.db.hero_points, 4)
        self.assertFalse(self.char1.attributes.has("hero_progress"))

    def test_at_the_cap_a_span_adds_nothing_and_leaves_no_counter(self):
        self.char1.db.hero_points = 4
        self.assertEqual(hero_points.accrue(self.char1, DAY + HOUR), 0)
        self.assertEqual(self.char1.db.hero_points, 4)
        self.assertFalse(self.char1.attributes.has("hero_progress"))

    def test_a_counter_stored_by_hand_at_the_cap_is_removed(self):
        self.char1.db.hero_points = 4
        self.char1.db.hero_progress = DAY - 1
        self.assertEqual(hero_points.accrue(self.char1, 1), 0)
        self.assertEqual(self.char1.db.hero_points, 4)
        self.assertFalse(self.char1.attributes.has("hero_progress"))

    def test_a_span_of_zero_writes_nothing(self):
        self.assertEqual(hero_points.accrue(self.char1, 0), 0)
        self.assertFalse(self.char1.attributes.has("hero_points"))
        self.assertFalse(self.char1.attributes.has("hero_progress"))

    def test_a_missing_store_and_a_day_stores_three(self):
        self.assertEqual(hero_points.accrue(self.char1, DAY), 1)
        self.assertEqual(self.char1.attributes.get("hero_points"), 3)

    def test_the_line_names_the_points_and_carries_no_number(self):
        self.assertIn("Hero Points", hero_points.EARNED)
        self.assertFalse(any(ch.isdigit() for ch in hero_points.EARNED))


class TestTheTickEarns(EvenniaTest):
    CLOCK = "world.survival_ticker.gametime_utils.get_absolute_gametime"

    def tick(self, span):
        """One survival tick of `span` game seconds; the lines it said."""
        self.char1.ndb.survival_tick_at = 100_000
        with mock.patch(self.CLOCK, return_value=100_000 + span), \
                mock.patch.object(self.char1, "msg") as msg:
            survival_ticker._deplete_character(self.char1)
        return [c.args[0] for c in msg.call_args_list if c.args]

    def test_a_collapsed_body_earns(self):
        self.char1.db.collapsed = True
        self.char1.db.hero_progress = DAY - 3000
        with mock.patch.object(self.char1, "arm_collapse") as arm:
            lines = self.tick(3000)
        arm.assert_called_once()   # receipt: the tick took the collapsed branch
        self.assertEqual(self.char1.db.hero_points, 3)
        self.assertEqual(lines.count(hero_points.EARNED), 1)

    def test_a_span_that_lands_two_says_one_line(self):
        self.char1.db.hero_points = 0
        self.char1.db.hero_progress = DAY - 1
        lines = self.tick(DAY + 1)
        self.assertEqual(self.char1.db.hero_points, 2)
        self.assertEqual(lines.count(hero_points.EARNED), 1)

    def test_a_tick_short_of_a_point_counts_and_says_nothing(self):
        lines = self.tick(3000)
        self.assertEqual(self.char1.db.hero_progress, 3000)
        self.assertNotIn(hero_points.EARNED, lines)


def written_attributes(tree):
    """
    The Attribute names a module stores, read by AST in the wound census's
    shape: every `X.db.<name> = / += ...` and every
    `X.attributes.add/remove("<name>", ...)`.
    """
    written = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            for target in getattr(node, "targets", None) or [node.target]:
                if (isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Attribute)
                        and target.value.attr == "db"):
                    written.add(target.attr)
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr in ("remove", "add")
              and isinstance(node.func.value, ast.Attribute)
              and node.func.value.attr == "attributes"
              and node.args and isinstance(node.args[0], ast.Constant)):
            written.add(node.args[0].value)
    return written


class TestHeroCensus(SimpleTestCase):
    """
    The module is the one writer of its Attributes, and each door has one
    caller in production (HE6, P-2). The doors push nothing: no snapshot
    shows Hero Points (HE7). When CL puts them in the panel, the callers
    push `char` (decomposition §11, 8) -- `TestCharSnapshot` will fail first.
    """

    # What world/hero_points.py stores.
    HERO_ATTRIBUTES = ("hero_points", "hero_progress", "hero_glancing_off")
    # door -> its one production caller (file, qualified name).
    DOORS = {
        "accrue": ("world/survival_ticker.py", "_deplete_character"),
        "set_glancing": ("commands/character_commands.py", "CmdHero.func"),
        "take_for_glancing": ("world/wounds.py", "damage"),
    }

    def test_every_attribute_the_module_writes_is_named(self):
        tree = ast.parse((ROOT / "world" / "hero_points.py").read_text(encoding="utf-8"))
        self.assertEqual(written_attributes(tree), set(self.HERO_ATTRIBUTES))

    def test_no_other_file_writes_a_hero_attribute(self):
        offenders = {}
        for rel, tree in _production_trees():
            if rel == "world/hero_points.py":
                continue
            names = sorted(n for n in written_attributes(tree) if n.startswith("hero_"))
            if names:
                offenders[rel] = names
        self.assertEqual(
            offenders, {},
            "P-2, HE6: world/hero_points.py is the only writer of the hero_ "
            "Attributes. Go through its doors.",
        )

    @staticmethod
    def _door_calls(tree, rel):
        """{(door, rel, qualified caller): count} for the module's doors."""
        module_names, door_names = set(), set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "world":
                module_names |= {a.asname or a.name for a in node.names if a.name == "hero_points"}
            elif isinstance(node, ast.ImportFrom) and node.module == "world.hero_points":
                door_names |= {a.asname or a.name for a in node.names}
            elif isinstance(node, ast.Import):
                module_names |= {a.asname for a in node.names
                                 if a.name == "world.hero_points" and a.asname}
        found = {}
        for qual, func in _functions(tree):
            nested = {id(n) for _q, inner in _functions(func) for n in ast.walk(inner)}
            for node in ast.walk(func):
                if id(node) in nested or not isinstance(node, ast.Call):
                    continue
                target, door = node.func, None
                if (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)
                        and target.value.id in module_names):
                    door = target.attr
                elif isinstance(target, ast.Name) and target.id in door_names:
                    door = target.id
                if door in TestHeroCensus.DOORS:
                    key = (door, rel, qual)
                    found[key] = found.get(key, 0) + 1
        return found

    def test_the_census_sees_both_spellings(self):
        source = (
            "from world import hero_points\n"
            "from world.hero_points import accrue\n"
            "def a(char):\n    hero_points.accrue(char, 1)\n"
            "def b(char):\n    accrue(char, 1)\n"
        )
        self.assertEqual(
            self._door_calls(ast.parse(source), "x.py"),
            {("accrue", "x.py", "a"): 1, ("accrue", "x.py", "b"): 1},
        )

    def test_every_door_has_its_one_caller(self):
        found = {}
        for rel, tree in _production_trees():
            found.update(self._door_calls(tree, rel))
        self.assertEqual(
            found,
            {(door, rel, qual): 1 for door, (rel, qual) in self.DOORS.items()},
            "HE6: each door of world/hero_points.py has one caller in production.",
        )


class TestSetGlancing(EvenniaTest):
    def spies(self):
        handler = self.char1.attributes
        return (mock.patch.object(handler, "add", wraps=handler.add),
                mock.patch.object(handler, "remove", wraps=handler.remove))

    def test_off_stores_true_and_reports_a_change(self):
        self.assertTrue(hero_points.set_glancing(self.char1, False))
        self.assertIs(self.char1.attributes.get("hero_glancing_off"), True)
        self.assertFalse(hero_points.glancing_on(self.char1))

    def test_off_twice_writes_nothing(self):
        hero_points.set_glancing(self.char1, False)
        add, remove = self.spies()
        with add as added, remove as removed:
            self.assertFalse(hero_points.set_glancing(self.char1, False))
        added.assert_not_called()
        removed.assert_not_called()
        self.assertFalse(hero_points.glancing_on(self.char1))

    def test_on_removes_the_attribute(self):
        self.char1.db.hero_glancing_off = True
        self.assertTrue(hero_points.set_glancing(self.char1, True))
        self.assertFalse(self.char1.attributes.has("hero_glancing_off"))
        self.assertTrue(hero_points.glancing_on(self.char1))

    def test_on_when_on_writes_nothing(self):
        add, remove = self.spies()
        with add as added, remove as removed:
            self.assertFalse(hero_points.set_glancing(self.char1, True))
        added.assert_not_called()
        removed.assert_not_called()
        self.assertFalse(self.char1.attributes.has("hero_glancing_off"))


class TestHeroCommand(EvenniaCommandTest):
    character_typeclass = "typeclasses.characters.Character"

    def hero(self, args=""):
        return self.call(CmdHero(), args, caller=self.char1)

    def test_the_screen_at_two(self):
        out = self.hero()
        self.assertRegex(out, r"Hero Points\s+2/4(?!\d)")
        self.assertRegex(out, r"Glancing Blow\s+on\b")

    def test_the_screen_at_zero_and_four(self):
        for held in (0, 4):
            with self.subTest(held=held):
                self.char1.db.hero_points = held
                self.assertRegex(self.hero(), rf"Hero Points\s+{held}/4(?!\d)")

    def test_off_then_the_screen(self):
        self.assertIn(GLANCING_OFF, self.hero("glancing off"))
        self.assertIs(self.char1.db.hero_glancing_off, True)
        self.assertRegex(self.hero(), r"Glancing Blow\s+off\b")

    def test_off_twice_says_so(self):
        self.hero("glancing off")
        self.assertIn(GLANCING_ALREADY.format("off"), self.hero("glancing off"))

    def test_on_again(self):
        self.hero("glancing off")
        self.assertIn(GLANCING_ON, self.hero("glancing on"))
        self.assertFalse(self.char1.attributes.has("hero_glancing_off"))
        self.assertIn(GLANCING_ALREADY.format("on"), self.hero("glancing on"))

    def test_the_words_are_read_in_any_case(self):
        self.assertIn(GLANCING_OFF, self.hero("Glancing OFF"))
        self.assertIs(self.char1.db.hero_glancing_off, True)

    def test_a_wrong_word_gets_the_usage_and_writes_nothing(self):
        for args in ("glancing", "glancing maybe", "points", "glancing off now"):
            with self.subTest(args=args):
                self.assertIn(HERO_USAGE, self.hero(args))
                self.assertFalse(self.char1.attributes.has("hero_glancing_off"))

    def test_a_collapsed_body_is_answered(self):
        self.char1.db.collapsed = True
        with mock.patch.object(self.char1, "arm_collapse"):
            out = self.hero("glancing off")
        self.assertIn(GLANCING_OFF, out)
        self.assertIs(self.char1.db.hero_glancing_off, True)

    def test_the_cap_on_the_screen_is_read_from_cap(self):
        with mock.patch.object(hero_points, "CAP", 7):
            self.assertRegex(self.hero(), r"Hero Points\s+2/7(?!\d)")

    def test_help_hero_names_the_cap(self):
        out = self.call(CmdHelp(), "hero", cmdset=CharacterCmdSet())
        self.assertIn("Glancing Blow", out)
        self.assertIn("up to 4, the most anyone holds", out)

    def test_the_cap_in_the_help_is_read_from_cap(self):
        with mock.patch.object(hero_points, "CAP", 7):
            out = self.call(CmdHelp(), "hero", cmdset=CharacterCmdSet())
        self.assertIn("up to 7, the most anyone holds", out)
