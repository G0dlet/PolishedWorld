"""
Tests for world/fatigue.py and the readers of the fatigue word (Survival
Loop S3.1, lock SL8; STOPP 0 locks A1-G1).

Each class presses one bug:

    TestLevelBounds          a bound read with `<` instead of `<=` (SL-M21):
                             both sides of every boundary, words and
                             penalties written out by hand
    TestNewCharacterAgrees   the stored `descs` of a new character drifting
                             away from the table (the decomposition's
                             "the two agree")
    TestFatigueDesc          the word read from the stored `descs` instead
                             of the table -- an old character says `weary`
    TestStatus               the word, and the penalty text below Fresh only
                             (SL-M23); a stored fraction reads as the number
                             the gauge itself rounds it to (lock B3)
    TestSheet                `sheet` still reading `trait.desc()` (lock C1,
                             SL-M46)
    TestSurvivalSnapshot     the client's word read from `trait.desc()`
                             (SL-M22)
    TestWarning              the tick's warning on the old path: its index
                             from `_bucket_index`, its word from
                             `trait.desc()` (SL-M47)

THE DISCRIMINATING STATE (lock F1, lesson 181)
----------------------------------------------
A character made by this commit stores `fatigue.DESCS`, so for every whole
value its `trait.desc()` says what `fatigue_desc()` says: a reader that
still calls `trait.desc()` passes every test run on it. The reader tests
therefore run on a character carrying the table every character made before
S3.1 stores (OLD_DESCS, keys 0/20/40/60/80/95 -- G0dlet's), and each one
first asserts that `trait.desc()` really says something else at its value.

Words and penalties are written out by hand, never read back from LEVELS.
"""

from unittest import mock

from django.test import SimpleTestCase
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.character_commands import CmdSheet, CmdStatus
from world import client_state, fatigue
from world.survival_ticker import _check_survival_warnings

# The fatigue `descs` every character made before S3.1 carries
# (typeclasses/characters.py at 6083de0).
OLD_DESCS = {
    0: "exhausted",
    20: "drained",
    40: "tired",
    60: "weary",
    80: "rested",
    95: "energetic",
}


class _OldDescsMixin:
    """char1 as a character made before S3.1: the old stored table."""

    def setUp(self):
        super().setUp()
        self.fatigue = self.char1.traits.fatigue
        self.fatigue.descs = dict(OLD_DESCS)

    def at(self, value):
        """Set the gauge to `value` and return what the old path says there."""
        self.fatigue.current = value
        return self.fatigue.desc()


def _line(out, label):
    """The one output line that carries `label`."""
    lines = [line for line in out.splitlines() if label in line]
    assert len(lines) == 1, (label, lines)
    return lines[0]


# --- the table ---------------------------------------------------------------


class TestLevelBounds(SimpleTestCase):
    """Both sides of every boundary (SL8: 0 / 1-20 / 21-40 / 41-60 / 61-80 / 81-100)."""

    WORDS = (
        (0, "debilitated"),
        (1, "exhausted"), (20, "exhausted"),
        (21, "wearied"), (40, "wearied"),
        (41, "tired"), (60, "tired"),
        (61, "winded"), (80, "winded"),
        (81, "fresh"), (100, "fresh"),
    )
    PENALTIES = (
        (0, 50),
        (1, 40), (20, 40),
        (21, 30), (40, 30),
        (41, 20), (60, 20),
        (61, 10), (80, 10),
        (81, 0), (100, 0),
    )

    def test_every_boundary_reads_its_word(self):
        for value, word in self.WORDS:
            with self.subTest(value=value):
                self.assertEqual(fatigue.word_for(value), word)

    def test_every_boundary_carries_its_penalty(self):
        for value, penalty in self.PENALTIES:
            with self.subTest(value=value):
                self.assertEqual(fatigue.penalty_for(value), penalty)

    def test_the_index_runs_worst_to_best(self):
        self.assertEqual(
            [fatigue.level_for(v) for v in (0, 1, 21, 41, 61, 81)],
            [0, 1, 2, 3, 4, 5],
        )

    def test_above_the_top_bound_is_fresh(self):
        # A gauge raised past 100 (a mod) reads as the top level, as
        # Evennia's Trait.desc() does with its highest key.
        self.assertEqual(fatigue.word_for(130), "fresh")
        self.assertEqual(fatigue.penalty_for(130), 0)

    def test_one_level_is_twenty_points(self):
        self.assertEqual(fatigue.LEVEL_POINTS, 20)


# --- new characters ----------------------------------------------------------


class TestNewCharacterAgrees(EvenniaTest):
    """A character made now stores the table, so its own desc() cannot contradict."""

    def test_new_characters_store_the_table(self):
        self.assertEqual(
            dict(self.char1.traits.fatigue.descs),
            {0: "debilitated", 20: "exhausted", 40: "wearied",
             60: "tired", 80: "winded", 100: "fresh"},
        )

    def test_desc_and_fatigue_desc_agree_on_every_whole_value(self):
        # Whole values are all a gauge with an int base ever reads (B3).
        trait = self.char1.traits.fatigue
        for value in range(0, 101):
            with self.subTest(value=value):
                trait.current = value
                self.assertEqual(trait.desc(), self.char1.fatigue_desc())


# --- the readers -------------------------------------------------------------


class TestFatigueDesc(_OldDescsMixin, EvenniaTest):
    """The word comes from the table, whatever the character stores."""

    def test_old_character_at_fifty_reads_tired(self):
        self.assertEqual(self.at(50), "weary")   # receipt: the old path differs
        self.assertEqual(self.char1.fatigue_desc(), "tired")

    def test_old_character_full_reads_fresh(self):
        self.assertEqual(self.at(100), "energetic")
        self.assertEqual(self.char1.fatigue_desc(), "fresh")

    def test_old_character_at_zero_reads_debilitated(self):
        self.assertEqual(self.at(0), "exhausted")
        self.assertEqual(self.char1.fatigue_desc(), "debilitated")

    def test_no_gauge_reads_empty(self):
        self.char1.traits.remove("fatigue")
        self.assertEqual(self.char1.fatigue_desc(), "")


class TestStatus(_OldDescsMixin, EvenniaCommandTest):
    """`status` prints the level's word and, below Fresh, the penalty (lock D1)."""

    def status_line(self):
        out = self.call(CmdStatus(), "", caller=self.char1)
        return _line(out, "Fatigue:")

    def test_at_35_wearied_and_minus_30(self):
        self.assertEqual(self.at(35), "tired")
        line = self.status_line()
        self.assertTrue(
            line.rstrip().endswith("- wearied (-30% to physical tests)"), line)

    def test_at_100_fresh_and_no_penalty_text(self):
        self.assertEqual(self.at(100), "energetic")
        line = self.status_line()
        self.assertTrue(line.rstrip().endswith("- fresh"), line)
        self.assertNotIn("physical tests", line)

    def test_a_stored_fraction_reads_as_the_gauge_rounds_it(self):
        # Lock B3's premise: the drain can store 80.9, but GaugeTrait.current
        # rounds on read for an int base, so every reader sees 81 -- Fresh.
        self.fatigue.current = 80.9
        self.assertEqual(self.fatigue.value, 81)
        line = self.status_line()
        self.assertIn(" 81/100", line)
        self.assertTrue(line.rstrip().endswith("- fresh"), line)


class TestSheet(_OldDescsMixin, EvenniaCommandTest):
    """`sheet` reads the same word as `status` (lock C1)."""

    def test_at_35_wearied(self):
        self.assertEqual(self.at(35), "tired")
        out = self.call(CmdSheet(), "", caller=self.char1)
        line = _line(out, "Fatigue ")
        self.assertTrue(line.rstrip().endswith("- wearied"), line)


class TestSurvivalSnapshot(_OldDescsMixin, EvenniaTest):
    """The client's survival panel carries the word `status` prints."""

    def test_snapshot_carries_the_table_word(self):
        self.assertEqual(self.at(50), "weary")
        snap = client_state.survival_snapshot(self.char1)
        self.assertEqual(snap["fatigue"], {"current": 50, "max": 100, "desc": "tired"})


class TestWarning(_OldDescsMixin, EvenniaTest):
    """The tick's warning: once on 61 -> 60, not on 60 -> 59, in the table's word."""

    def check(self, value):
        """Set the gauge, run the warning check, return the warnings sent."""
        self.fatigue.current = value
        with mock.patch.object(self.char1, "msg") as msg:
            _check_survival_warnings(self.char1)
        return [call.args[0] for call in msg.call_args_list
                if call.args and "You feel" in str(call.args[0])]

    def test_61_to_60_warns_once_with_tired(self):
        self.assertEqual(self.check(61), [])   # the baseline
        self.assertEqual(self.at(60), "weary")   # receipt: the old word differs
        self.assertEqual(self.check(60), ["|yYou feel tired.|n"])

    def test_60_to_59_is_silent(self):
        self.check(60)
        self.assertEqual(self.check(59), [])

    def test_thirst_keeps_its_own_word(self):
        # The fatigue branch must not take the other gauges with it: thirst
        # still warns in its stored word (61 -> 60 crosses its key 60 too).
        self.check(100)
        thirst = self.char1.traits.thirst
        thirst.current = 61
        _check_survival_warnings(self.char1)
        thirst.current = 60
        with mock.patch.object(self.char1, "msg") as msg:
            _check_survival_warnings(self.char1)
        self.assertEqual([c.args[0] for c in msg.call_args_list],
                         ["|yYou feel could drink.|n"])
