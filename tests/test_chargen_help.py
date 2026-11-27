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

The expected numbers are written out by hand, never computed from the code
under test (lesson 74).
"""

import re
from unittest import mock

from evennia.commands.default.help import CmdHelp
from evennia.utils.test_resources import EvenniaCommandTest

from commands.character_commands import (
    CmdSheet,
    CmdSkills,
    CmdStats,
    CmdStatus,
    _whole,
)
from commands.default_cmdsets import CharacterCmdSet
from world import chargen
from world.chargen import apply_allocation

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

    def test_a_pair_of_one_characteristic_reads_x2(self):
        # BD-T4: Resilience is CON x 2 and Evade DEX x 2 (p. 14); printed as
        # every other pair they would read CON+CON and DEX+DEX (BDM10).
        text = chargen.help_text()
        self.assertIn("Resilience (CON x2)", text)
        self.assertIn("Evade (DEX x2)", text)
        self.assertIn("Brawn (STR+SIZ)", text)
        self.assertIn("Athletics (STR+DEX)", text)
        self.assertNotIn("CON+CON", text)
        self.assertNotIn("DEX+DEX", text)

    def test_a_key_of_two_words_reads_as_two(self):
        # HL-T4: the first key with an underscore; capitalize() alone gave
        # "First_aid".
        text = chargen.help_text()
        self.assertIn("First aid (INT+DEX)", text)
        self.assertNotIn("_aid", text)

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
        self.assertIn(
            "CON 10 and SIZ 10 give head 4, chest 6, abdomen 5, arms 3, legs 4", text
        )
        for name in ("weaver", "tanner", "cobbler", "generalist"):
            self.assertIn(name, text)

    def test_names_the_appearance(self):
        # Names NM-T16: the menu's third choice, and the build it does not offer.
        text = chargen.help_text()
        self.assertIn("|wAppearance|n: choose your sex, an age and one feature", text)
        self.assertIn("a build that follows your SIZ", text)
        self.assertIn("characteristics, profession and appearance are chosen once", text)

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
        self.assertRegex(out, r"Health\s+100/100(?![.\d])")   # out of 100 (WN-T11)
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
        self.assertRegex(out, r"Health:\s+100/100(?![.\d])")   # out of 100 (WN-T11)
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
