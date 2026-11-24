"""
Tests for the Combat block on `sheet` (Body decomposition BD-T7; lock BD9).

`sheet` shows Combat Actions, Strike Rank and the Damage Modifier from
`world.body.derived(char)`, between Vital Status and Skills. Nothing is
stored (BD7), so the block follows the body as it is now: the fatigue
tests move the gauge and read the sheet again.

The numbers are typed from the book's tables (core pp. 10, 13, 90), with
Alaric's four characteristics: STR 12, DEX 13, SIZ 14, INT 16.

Hero Points (Hero Points decomposition HE-T4; HE7): a row *Hero Points n/4*
after the Damage Modifier, read from `hero_points.points` on every call and
never stored, in the block and only there -- a body without
characteristics has no block and no row (chosen at HE-T4's STOPP 0; `hero`
still shows its points). `TestHeroPointsRow` pressures a row read from the
Attribute itself (a fresh character would show None/4: HEM14), a cap typed
instead of read (HEM14b), and the row added to `status` (HEM15).
"""

import re
from unittest import mock

from evennia.utils.test_resources import EvenniaCommandTest

from commands.character_commands import CmdSheet, CmdStats, CmdStatus
from world import hero_points


def _row(out, label):
    """The value printed beside a label, or None when the row is absent."""
    found = re.search(rf"{label}\s+(\S+)", out)
    return found.group(1) if found else None


class _Alaric(EvenniaCommandTest):
    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        stats = self.char1.stats
        stats.str.base, stats.dex.base = 12, 13
        stats.siz.base, stats.int.base = 14, 16

    def sheet(self):
        return self.call(CmdSheet(), "", caller=self.char1)


class TestTheBlock(_Alaric):
    """
    Pressures what is shown: a value left out or read from the wrong
    characteristic, the block in the wrong place, and a block drawn for a
    body that has no characteristics to read.
    """

    def test_the_three_values(self):
        out = self.sheet()
        self.assertEqual(_row(out, "Combat Actions"), "3")
        self.assertEqual(_row(out, "Strike Rank"), "15")
        self.assertEqual(_row(out, "Damage Modifier"), "+1D2")

    def test_the_placeholder_body(self):
        out = self.call(CmdSheet(), "", caller=self.char2)
        self.assertEqual(_row(out, "Combat Actions"), "2")
        self.assertEqual(_row(out, "Strike Rank"), "10")
        self.assertEqual(_row(out, "Damage Modifier"), "-1D2")

    def test_the_block_stands_between_vital_status_and_skills(self):
        out = self.sheet()
        self.assertLess(out.index("Vital Status:"), out.index("Combat:"))
        self.assertLess(out.index("Combat:"), out.index("Skills:"))
        self.assertLess(out.index("Fatigue"), out.index("Combat Actions"))

    def test_the_maxima_per_location_are_not_shown(self):
        # BD9: beside a health gauge that is the only one that moves.
        out = self.sheet().lower()
        for word in ("abdomen", "right arm", "left leg", "hit points"):
            self.assertNotIn(word, out)

    def test_no_block_without_a_body_to_read(self):
        with mock.patch("world.body.derived", return_value=None):
            out = self.sheet()
        self.assertNotIn("Combat:", out)
        self.assertNotIn("Strike Rank", out)
        self.assertNotIn("Hero Points", out)   # the row follows the block (HE-T4)
        self.assertIn("Skills:", out)


class TestHeroPointsRow(_Alaric):
    def test_a_fresh_character_reads_two_of_four(self):
        self.assertIsNone(self.char1.db.hero_points)
        self.assertEqual(_row(self.sheet(), "Hero Points"), "2/4")

    def test_zero_and_four(self):
        for held in (0, 4):
            self.char1.db.hero_points = held
            self.assertEqual(_row(self.sheet(), "Hero Points"), f"{held}/4")

    def test_the_row_comes_after_the_damage_modifier(self):
        out = self.sheet()
        self.assertLess(out.index("Damage Modifier"), out.index("Hero Points"))
        self.assertLess(out.index("Hero Points"), out.index("Skills:"))

    def test_the_cap_is_read_from_cap(self):
        with mock.patch.object(hero_points, "CAP", 7):
            self.assertEqual(_row(self.sheet(), "Hero Points"), "2/7")

    def test_status_names_no_hero_point(self):
        out = self.call(CmdStatus(), "", caller=self.char1)
        self.assertIn("Health", out)   # receipt: status printed its vitals
        self.assertNotIn("hero", out.lower())


class TestTheBlockIsReadLive(_Alaric):
    """
    Pressures BD7 on the sheet: values worked out with the body taken as
    fresh (BDM17), or stored at some earlier moment.
    """

    def test_exhausted_loses_a_combat_action(self):
        self.assertEqual(_row(self.sheet(), "Combat Actions"), "3")
        self.char1.traits.fatigue.current = 10
        self.assertEqual(self.char1.fatigue_desc(), "exhausted")
        out = self.sheet()
        # DEX counts 5 lower (p. 90): the average of 8 and 16 is 12.
        self.assertEqual(_row(out, "Combat Actions"), "2")
        # And Strike Rank is 4 lower.
        self.assertEqual(_row(out, "Strike Rank"), "11")

    def test_wearied_moves_strike_rank_alone(self):
        self.char1.traits.fatigue.current = 30
        self.assertEqual(self.char1.fatigue_desc(), "wearied")
        out = self.sheet()
        self.assertEqual(_row(out, "Combat Actions"), "3")
        self.assertEqual(_row(out, "Strike Rank"), "13")

    def test_rested_again_reads_the_first_numbers(self):
        self.char1.traits.fatigue.current = 10
        self.sheet()
        self.char1.traits.fatigue.current = 100
        out = self.sheet()
        self.assertEqual(_row(out, "Combat Actions"), "3")
        self.assertEqual(_row(out, "Strike Rank"), "15")

    def test_fatigue_does_not_touch_the_damage_modifier(self):
        self.char1.traits.fatigue.current = 10
        self.assertEqual(_row(self.sheet(), "Damage Modifier"), "+1D2")


class TestTheOtherCommandsAreNotTouched(_Alaric):
    """Pressures BD9's fence: the block spreading to `stats` or `status`."""

    def test_stats_and_status_show_no_combat_values(self):
        for cmd in (CmdStats(), CmdStatus()):
            with self.subTest(cmd=cmd.key):
                out = self.call(cmd, "", caller=self.char1)
                self.assertNotIn("Combat Actions", out)
                self.assertNotIn("Strike Rank", out)
                self.assertNotIn("Damage Modifier", out)


class TestOneSpelling(_Alaric):
    """Pressures a second home for the spelling: the sheet formatting the
    modifier itself instead of asking `world.body`."""

    def test_a_modifier_of_nothing_reads_plus_zero(self):
        self.char1.stats.str.base, self.char1.stats.siz.base = 11, 11   # 22
        self.assertEqual(_row(self.sheet(), "Damage Modifier"), "+0")

    def test_the_sheet_and_the_confirmation_spell_it_alike(self):
        from world import body

        self.assertEqual(body.format_damage_modifier((1, 1, 2)), "+1D2")
        self.assertEqual(body.format_damage_modifier((-1, 1, 4)), "-1D4")
        self.assertEqual(body.format_damage_modifier((0, 0, 0)), "+0")
        self.assertEqual(
            _row(self.sheet(), "Damage Modifier"), body.damage_modifier_text(12, 14)
        )
