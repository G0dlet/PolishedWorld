"""
CC3.3: the `profession` command is retired, `help chargen` states the
contract, and the character commands show whole numbers.

Each class names the bug it pressures:

    TestProfessionCommandGone  the cmdset line (or an alias) left behind, so a
                               second door to the profession choice stays open
                               beside the menu
    TestHelpChargen            the topic not registered, `help profession`
                               answering "no help found", or a number typed
                               into the text that drifts from the constant
                               the menu enforces; a promise the code does not
                               keep (characteristics do not improve in play)
    TestWholeNumbers           a rendering line left on a raw `.value`, which
                               is `(...) * mult` and so always a float (`7.0`)
    TestHealthIsInt            `derive_health_max()` handing a float to
                               `health.base`: the gauge then stops rounding
                               its own `.current`, which the survival ticker's
                               integer damage assumes

The expected numbers are written out by hand, never computed from the code
under test (lesson 74).
"""

import re
from unittest import mock

from evennia.commands.default.help import CmdHelp
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.character_commands import (
    CmdSheet,
    CmdSkills,
    CmdStats,
    CmdStatus,
    _whole,
)
from commands.default_cmdsets import CharacterCmdSet
from world import chargen
from world.chargen import apply_allocation, derive_health_max

# chargen's fixture (tests/test_chargen.py), repeated on purpose: a test module
# importing another test module couples the two suites.
VALID = {"str": 7, "dex": 9, "con": 14, "siz": 8, "int": 12, "pow": 17, "cha": 13}


class TestProfessionCommandGone(EvenniaCommandTest):
    def test_no_command_answers_to_profession(self):
        names = set()
        for cmd in CharacterCmdSet().commands:
            names.add(cmd.key)
            names.update(cmd.aliases)
        self.assertIn("sheet", names)  # receipt: the cmdset was really built
        self.assertNotIn("profession", names)
        self.assertNotIn("professions", names)


class TestHelpChargen(EvenniaCommandTest):
    def test_every_name_reaches_the_topic(self):
        for name in ("chargen", "profession", "professions"):
            with self.subTest(name=name):
                out = self.call(CmdHelp(), name, cmdset=CharacterCmdSet())
                self.assertIn("80 points", out)
                self.assertIn("No do-overs", out)

    def test_registered_once(self):
        from world.help_entries import HELP_ENTRY_DICTS

        entries = [d for d in HELP_ENTRY_DICTS if d["key"] == "chargen"]
        self.assertEqual(len(entries), 1)

    def test_text_follows_the_constants(self):
        with mock.patch.object(chargen, "DESIGN_POINTS", 81), \
                mock.patch.object(chargen, "CHAR_MIN", 5), \
                mock.patch.object(chargen, "CHAR_MAX", 19), \
                mock.patch.dict(chargen.PROFESSIONS, {"hunter": {}}):
            text = chargen.help_text()
        self.assertIn("81 points", text)
        self.assertIn("between 5 and 19", text)
        self.assertIn("hunter", text)

    def test_shipped_values(self):
        text = chargen.help_text()
        self.assertIn("80 points", text)
        self.assertIn("between 6 and 18", text)
        self.assertIn("CON 10 gives 20", text)
        for name in ("weaver", "tanner", "cobbler", "generalist"):
            self.assertIn(name, text)

    def test_promises_no_characteristic_growth(self):
        text = chargen.help_text()
        self.assertIn("Your characteristics stay as you set them", text)
        self.assertNotRegex(text, r"characteristics? (improve|grow|rise)")


class TestWholeNumbers(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        apply_allocation(self.char1, VALID)
        # Premise: the trait reads back as a float -- the bug this class is about.
        self.assertEqual(repr(self.char1.stats.str.value), "7.0")

    def _stats_lines_whole(self, out):
        for name, number in (("Strength", 7), ("Dexterity", 9),
                             ("Constitution", 14), ("Power", 17)):
            self.assertRegex(out, rf"{name}\s+{number}(?![.\d])")

    def test_sheet(self):
        out = self.call(CmdSheet(), "", caller=self.char1)
        self._stats_lines_whole(out)
        self.assertRegex(out, r"28/28(?![.\d])")         # health, CON 14 x 2
        self.assertRegex(out, r"Crafting\s+21%")         # DEX 9 + INT 12

    def test_stats(self):
        out = self.call(CmdStats(), "", caller=self.char1)
        self._stats_lines_whole(out)

    def test_skills(self):
        out = self.call(CmdSkills(), "", caller=self.char1)
        self.assertRegex(out, r"Crafting\s+21%")
        self.assertNotRegex(out, r"\d\.\d+%")

    def test_status(self):
        out = self.call(CmdStatus(), "", caller=self.char1)
        self.assertRegex(out, r"Health:\s+28/28(?![.\d])")
        self.assertNotRegex(out, r"\d\.\d+/")         # no gauge reads 99.0/
        self.assertNotRegex(out, r"/\d+\.\d")         # nor /100.0

    def test_truncates_not_rounds(self):
        # A unit test, not a rendering one: the gauges a player sees round
        # their own `.current` (see TestHealthIsInt), so no screen reaches a
        # fraction today; the policy is pinned here for the day one does.
        self.assertEqual(_whole(99.6), 99)
        self.assertIs(type(_whole(7.0)), int)


class TestSkillBreakdownWhole(EvenniaCommandTest):
    """A fixture's Craft is stored as 20.0 (`dex.value + int.value`)."""

    def test_breakdown_base_is_whole(self):
        craft = self.char1.skills.craft
        self.assertEqual(repr(craft.base), "20.0")      # premise
        craft.mod = 5
        out = self.call(CmdSkills(), "", caller=self.char1)
        self.assertRegex(out, r"base 20 \+ current\s+\+0 \+ mod\s+\+5")


class TestHealthIsInt(EvenniaTest):
    def test_derive_returns_int(self):
        self.assertIs(type(derive_health_max(14.0)), int)
        self.assertEqual(derive_health_max(14.0), 28)

    def test_fresh_character(self):
        self.assertIs(type(self.char1.traits.health.base), int)
        self.assertEqual(self.char1.traits.health.base, 20)

    def test_int_base_makes_the_gauge_read_whole(self):
        # Evennia's GaugeTrait rounds `.current` on read only when `.base` is
        # an int -- the behaviour the survival ticker's STARVE_DAMAGE comment
        # is written against. A float base would let 17.6 through.
        self.char1.traits.health.current = 17.6
        self.assertEqual(repr(self.char1.traits.health.current), "18")

    def test_after_update_health_max(self):
        self.char1.stats.con.base = 13
        self.char1.update_health_max()
        self.assertIs(type(self.char1.traits.health.base), int)
        self.assertEqual(self.char1.traits.health.base, 26)
