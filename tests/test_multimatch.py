"""
Tests for the game's multimatch form, `N-name`. Names, Task NM-T1
(docs/PolishedWorld_Combat_Decomposition.md, NM9; Names note K6, UQ6).

WHY THE FORM IS `N-name`
------------------------
The rpsystem contrib's emote parser reads `/2-tall` itself
(evennia/contrib/rpg/rpsystem/rpsystem.py:207, :423-428), and its README asks
for the same form in settings (README.md:80-81). Evennia's default is the
suffix, `fiber-2` (settings_default.py:417, :425). Without the change the
game would have two forms from NM-T2 on: one in emotes, one everywhere else.

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
* the search -- `2-fiber` is the second of two and `fiber-2` is nothing. The
  regex is compiled once, at import, in evennia/objects/manager.py:28, so this
  file reads the setting the running game reads, not an override.
* the error -- the multimatch list prints `1-fiber`. The template is the only
  place a player learns the form; a regex changed without it would teach a
  form the search no longer reads.
* the pair -- every line the template prints is read back by the regex as the
  same number and name. That is the "change together" rule of
  settings_default.py:415-416 as a test.

`offer`'s side of the change (a numbered item is not coin) is in
tests/test_barter_currency.py, TestOfferSegmentClassification.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_multimatch
"""

import re
from unittest import mock

from django.conf import settings
from evennia import create_object
from evennia.utils.test_resources import EvenniaTest


class TestNNameMultimatch(EvenniaTest):
    """Two fiber in the pack, and the three ways a player meets the form."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.fibres = [
            create_object("typeclasses.objects.Object", key="fiber", location=self.char1)
            for _ in range(2)
        ]

    def test_n_name_finds_the_nth(self):
        found = self.char1.search("2-fiber", quiet=True)
        self.assertEqual(list(found), [self.fibres[1]])

    def test_the_suffix_form_finds_nothing(self):
        # The old form must not keep working beside the new one: a protocol or a
        # habit that still types `fiber-2` should fail loudly, not by luck.
        self.assertEqual(list(self.char1.search("fiber-2", quiet=True)), [])

    def test_a_number_past_the_matches_finds_nothing(self):
        self.assertEqual(list(self.char1.search("3-fiber", quiet=True)), [])

    def test_the_error_lists_the_n_name_form(self):
        with mock.patch.object(self.char1, "msg") as msg:
            result = self.char1.search("fiber")
        self.assertIsNone(result)
        said = "\n".join(str(call.args[0]) for call in msg.call_args_list)
        self.assertIn(" 1-fiber", said)
        self.assertIn(" 2-fiber", said)
        self.assertNotIn("fiber-1", said)


class TestTheSettingsPairAgrees(EvenniaTest):
    """What the template prints, the regex reads back."""

    def test_each_printed_line_parses_to_its_number_and_name(self):
        regex = re.compile(settings.SEARCH_MULTIMATCH_REGEX, re.I + re.U)
        for number, name in ((1, "fiber"), (2, "length of twine"), (12, "corpse of tester")):
            printed = settings.SEARCH_MULTIMATCH_TEMPLATE.format(
                number=number, name=name, aliases="", info=""
            ).strip()
            with self.subTest(printed=printed):
                match = regex.match(printed)
                self.assertIsNotNone(match)
                self.assertEqual(match.group("number"), str(number))
                self.assertEqual(match.group("name"), name)
