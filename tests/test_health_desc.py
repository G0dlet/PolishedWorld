"""
Tests for Character.health_desc() (Character Creation, Task CC1.2).

Each class presses one bug:

    TestHealthDescReadsPercent  the label read from the absolute value instead
                                of percent() -- the BACKLOG bug itself
    TestHealthDescBands         the wrong bound: a lower-bound reading of the
                                same table labels a lightly hurt character
                                with the 0 % word (*dead* until WN-T11,
                                *grievously wounded* since: OQ-WN5)
    TestHealthDescCallSites     a command still calling the trait's own desc()

THE DISCRIMINATING STATE (lesson 74)
------------------------------------
The decomposition's own cases -- 100%, 50% and 0% -- read the same under an
upper- and a lower-bound reading, so they cannot tell the two apart; only
values *between* keys can (1/20 and 19/20 below). Likewise a test that set
max to 100 could not tell percent from value. The default character's 20/20
is the state where the two paths disagree, and each test that relies on it
first asserts that the old reader really does say something else there.

Labels are written out by hand, never read back from the stored table.

Since Wounds WN-T5 the percentage is `health`'s: the worst location's margin
to a Major Wound (WN2), worked out from the stored damage. The bands are set
by writing `db.body_damage` on the head by hand -- 0 % is a Major Wound, which
the writer would answer with a death -- and the scale is the head's whole
(2 x its Hit Points) at three bodies. The discriminating states are the
same kind as before: 1/12 and 11/12 lie between the table's keys.
"""

from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.character_commands import CmdSheet, CmdStatus
from tests.wounds_fixture import made_before_wn
from world import wounds


def _set_body(char, con, siz):
    char.stats.con.base = con
    char.stats.siz.base = siz


class TestHealthDescReadsPercent(EvenniaTest):
    """The scale: an unhurt body is `healthy` whatever its size."""

    def test_unhurt_at_con_siz_20_reads_healthy(self):
        self.assertEqual(wounds.health_of(self.char1)[:2], (8, 8))
        # Receipt: read as an absolute value, 8 is near death.
        self.assertEqual(wounds.word_for(8), "near death")
        self.assertEqual(self.char1.health_desc(), "healthy")

    def test_unhurt_at_con_siz_28_reads_healthy(self):
        _set_body(self.char1, 18, 10)
        self.assertEqual(wounds.health_of(self.char1)[:2], (12, 12))
        self.assertEqual(self.char1.health_desc(), "healthy")

    def test_unhurt_at_con_siz_5_reads_healthy(self):
        _set_body(self.char1, 2, 3)
        self.assertEqual(wounds.health_of(self.char1)[:2], (2, 2))
        self.assertEqual(self.char1.health_desc(), "healthy")


class TestHealthDescBands(EvenniaTest):
    """The bound: Evennia's inclusive upper bound, unchanged."""

    def _at(self, con, siz, head_damage):
        _set_body(self.char1, con, siz)
        self.char1.db.body_damage = {"head": head_damage}
        return self.char1.health_desc()

    def test_half_reads_the_same_band_at_any_size(self):
        self.assertEqual(self._at(10, 10, 4), "badly hurt")   # 4/8
        self.assertEqual(self._at(18, 10, 6), "badly hurt")   # 6/12

    def test_zero_reads_grievously_wounded(self):
        self.assertEqual(self._at(10, 10, 8), "grievously wounded")   # 0/8

    def test_eight_percent_is_near_death_not_the_zero_word(self):
        # 1/12. A lower-bound reading puts 0-9% under key 0's word.
        self.assertEqual(self._at(18, 10, 11), "near death")

    def test_ninety_two_percent_is_healthy_not_bruised(self):
        # 11/12. A lower-bound reading puts 90-99% under key 90.
        self.assertEqual(self._at(18, 10, 1), "healthy")


class TestHealthDescCallSites(EvenniaCommandTest):
    """`status` and `sheet` show the percent label, at a state where it differs."""

    def _premise(self):
        health = made_before_wn(self.char1)   # a character made before WN
        self.assertEqual((health.value, health.max), (20, 20))
        self.assertEqual(health.desc(), "critically wounded")

    def test_status_shows_healthy(self):
        self._premise()
        out = self.call(CmdStatus(), "", caller=self.char1)
        self.assertIn("healthy", out)
        self.assertNotIn("critically wounded", out)

    def test_sheet_shows_healthy(self):
        self._premise()
        out = self.call(CmdSheet(), "", caller=self.char1)
        self.assertIn("healthy", out)
        self.assertNotIn("critically wounded", out)
