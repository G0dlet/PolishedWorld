"""
Tests for the cohort contract (Launch Minimum L4.2, LM7).

Each class names the bug it pressures:

    TestHelpAlphaAnswers     the entry exists in the module but `help` cannot
                             reach it -- a failed import in help_entries.py
                             skips EVERY file entry silently, and an alias
                             typo leaves `help cohort` answering "no match".
    TestContractText         the text drifts from LM7: a claim dropped, the
                             order changed, or a number that goes stale typed
                             into it (the alpha's length lives in the roadmap).
    TestConnectionScreen     the line never reaches the screen, or reaches it
                             as a SECOND screen: menu_login picks at random
                             among the module's public string globals, so a
                             public import would show the bare line on every
                             other connect.
"""

import re

from django.conf import settings
from evennia.commands.default.help import CmdHelp
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest
from evennia.utils.utils import string_from_module

from world import alpha_contract


class TestHelpAlphaAnswers(EvenniaCommandTest):
    def _help(self, topic):
        from commands.default_cmdsets import CharacterCmdSet

        return self.call(CmdHelp(), topic, cmdset=CharacterCmdSet())

    def test_help_alpha_answers(self):
        self.assertIn("closed alpha", self._help("alpha"))

    def test_both_aliases_answer(self):
        for alias in ("cohort", "contract"):
            with self.subTest(alias=alias):
                self.assertIn("closed alpha", self._help(alias))

    def test_entry_listed_once_with_its_key_aliases_and_category(self):
        from world.help_entries import HELP_ENTRY_DICTS

        entries = [d for d in HELP_ENTRY_DICTS if d["key"] == "alpha"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(sorted(entries[0]["aliases"]), ["cohort", "contract"])
        self.assertEqual(entries[0]["category"], "General")


class TestContractText(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.text = alpha_contract.help_text()

    def test_points_to_help_death(self):
        self.assertIn("help death", self.text)

    def test_claims_in_lm7_order(self):
        # wiped at close-out, death, logged, GameGold, wipe notice, staff
        markers = (
            "wiped when the alpha ends",
            "help death",
            "economic act is logged",
            "GameGold is not part of the alpha",
            "announced at least",
            "To reach staff",
        )
        positions = [self.text.find(m) for m in markers]
        self.assertNotIn(-1, positions, dict(zip(markers, positions)))
        self.assertEqual(positions, sorted(positions))

    def test_only_number_is_the_wipe_notice(self):
        self.assertEqual(
            re.findall(r"\d+", self.text), [str(alpha_contract.WIPE_NOTICE_DAYS)]
        )


class TestConnectionScreen(EvenniaTest):
    def test_one_screen_and_it_points_to_help_alpha(self):
        screens = string_from_module(settings.CONNECTION_SCREEN_MODULE)
        self.assertEqual(len(screens), 1, screens)
        self.assertIn(alpha_contract.CONNECTION_LINE, screens[0])
        self.assertIn("help alpha", screens[0])
