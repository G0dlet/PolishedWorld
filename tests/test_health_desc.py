"""
Tests for Character.health_desc() (Character Creation, Task CC1.2).

Each class presses one bug:

    TestHealthDescReadsPercent  the label read from the absolute value instead
                                of percent() -- the BACKLOG bug itself
    TestHealthDescBands         the wrong bound: a lower-bound reading of the
                                same table labels a living character `dead`
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
"""

from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.character_commands import CmdSheet, CmdStatus


def _set_con(char, con):
    """Re-base CON and let the existing helper carry health with it."""
    char.stats.con.base = con
    char.update_health_max()


class TestHealthDescReadsPercent(EvenniaTest):
    """The scale: a full gauge is `healthy` whatever CON is."""

    def test_full_at_con_10_reads_healthy(self):
        health = self.char1.traits.health
        self.assertEqual((health.value, health.max), (20, 20))
        # Receipt: at this state the absolute-value reader disagrees.
        self.assertEqual(health.desc(), "critically wounded")
        self.assertEqual(self.char1.health_desc(), "healthy")

    def test_full_at_con_18_reads_healthy(self):
        _set_con(self.char1, 18)
        health = self.char1.traits.health
        self.assertEqual((health.value, health.max), (36, 36))
        self.assertEqual(self.char1.health_desc(), "healthy")

    def test_full_at_con_6_reads_healthy(self):
        _set_con(self.char1, 6)
        health = self.char1.traits.health
        self.assertEqual((health.value, health.max), (12, 12))
        self.assertEqual(self.char1.health_desc(), "healthy")


class TestHealthDescBands(EvenniaTest):
    """The bound: Evennia's inclusive upper bound, unchanged."""

    def _at(self, con, current):
        _set_con(self.char1, con)
        self.char1.traits.health.current = current
        return self.char1.health_desc()

    def test_half_reads_the_same_band_at_any_max(self):
        self.assertEqual(self._at(6, 6), "badly hurt")    # 6/12
        self.assertEqual(self._at(18, 18), "badly hurt")  # 18/36

    def test_zero_reads_dead(self):
        self.assertEqual(self._at(10, 0), "dead")

    def test_five_percent_is_near_death_not_dead(self):
        # 1/20 = 5%. A lower-bound reading puts 0-9% under key 0: `dead`.
        self.assertEqual(self._at(10, 1), "near death")

    def test_ninety_five_percent_is_healthy_not_bruised(self):
        # 19/20 = 95%. A lower-bound reading puts 90-99% under key 90.
        self.assertEqual(self._at(10, 19), "healthy")

    def test_no_descs_reads_empty(self):
        self.char1.traits.health.descs = None
        self.assertEqual(self.char1.health_desc(), "")


class TestHealthDescCallSites(EvenniaCommandTest):
    """`status` and `sheet` show the percent label, at a state where it differs."""

    def _premise(self):
        health = self.char1.traits.health
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
