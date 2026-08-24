"""
Unit tests for the Legend improvement roll. Stage 4.5, Component D.2.

Written to the pattern in `tests/test_knowledge.py` (AGENTS.md section 0A).

WHAT IT COVERS
--------------
* world.improvement.improvement_roll -- both bands, after D.2 lifted the cap

⚠️ THIS FUNCTION HAD NO TESTS AT ALL BEFORE THIS FILE
------------------------------------------------------
Third time in this epic. `tests/test_improvement_engine.py` says outright that
it tests "the reinterpretation, not the roll" and pins the roll to a fixed grain
throughout, which was correct while C.1 left world/improvement.py untouched
(P-3). D.2 is the first change to that module since it was written, so the
416-test baseline this component inherited proved nothing whatsoever about the
arithmetic below.

BASE CLASS
----------
`EvenniaTestCase`, the lightest available: improvement_roll is pure maths with
no Evennia import, no database and no typeclass. Same call `tests/test_progression`
makes for its own pure layer.

HOW THE ROLL IS PINNED
----------------------
`randint` is patched at `world.improvement.randint` -- the name the function
actually resolves. It is called twice per beat (the d100 and the 1D4), so the
stand-in dispatches on the upper bound rather than on call order: dispatching on
order would silently break the day someone reorders two lines.

HOW TO RUN
----------
    evennia test --settings settings.py tests
    evennia test --settings settings.py tests.test_improvement_roll
"""

from unittest import mock

from evennia.utils.test_resources import EvenniaTestCase

from world.improvement import improvement_roll


def pinned(d100, d4=4):
    """A randint stand-in that dispatches on the die, not on call order."""
    def _randint(low, high):
        return d100 if high == 100 else d4
    return _randint


class TestTheBandBoundary(EvenniaTestCase):
    """
    Which band a score falls in, and what each band does to INT.

    The boundary is decided by `skill_value > 100`, so 100 is in the FIRST band
    and 101 in the second. That is a design decision (a skill of exactly 100
    still rolls against itself with its whole INT), and it is the single line a
    careless `>=` would flip without failing anything else.
    """

    def test_full_int_applies_at_exactly_100(self):
        with mock.patch("world.improvement.randint", pinned(50)):
            res = improvement_roll(100, 12)

        self.assertEqual(res["int_bonus"], 12)

    def test_int_is_halved_one_point_later(self):
        """101 is the first score in the second band -- the abrupt step is RAW."""
        with mock.patch("world.improvement.randint", pinned(50)):
            res = improvement_roll(101, 12)

        self.assertEqual(res["int_bonus"], 6)

    def test_int_is_quartered_in_the_third_band(self):
        with mock.patch("world.improvement.randint", pinned(50)):
            self.assertEqual(improvement_roll(250, 12)["int_bonus"], 3)

    def test_a_skill_at_or_below_zero_never_multiplies_the_int(self):
        """
        The mutation guard. (0 - 1) // 100 == -1 and 2 ** -1 == 0.5, so without
        max(0, ...) a skill of 0 would get `12 // 0.5` -- a DOUBLED bonus, and a
        float at that. Nothing else in this file reaches that input class.
        """
        with mock.patch("world.improvement.randint", pinned(50)):
            for skill in (0, -5):
                res = improvement_roll(skill, 12)
                self.assertEqual(res["int_bonus"], 12, f"skill {skill}")
                self.assertIsInstance(res["int_bonus"], int, f"skill {skill}")


class TestWhatTheRollIsTestedAgainst(EvenniaTestCase):
    """
    The target: the skill itself below the boundary, a flat 100 above it.

    Asserted through `beat` rather than through a "target" key, because the
    function does not expose one -- and a test that needed it exposed would be
    asking for a wider API than the caller has ever wanted.
    """

    def test_below_the_boundary_the_target_is_the_skill_itself(self):
        with mock.patch("world.improvement.randint", pinned(41)):
            self.assertTrue(improvement_roll(40, 0)["beat"])
        with mock.patch("world.improvement.randint", pinned(40)):
            self.assertFalse(improvement_roll(40, 0)["beat"])

    def test_above_the_boundary_the_target_is_100_and_not_the_skill(self):
        """
        The assertion the whole band exists for. At skill 150 a total of 102
        beats; tested against 150 it could not, and no 1D100 could -- the band
        would be a hard stop rather than a curve.
        """
        with mock.patch("world.improvement.randint", pinned(100)):
            self.assertTrue(improvement_roll(150, 4)["beat"])
            self.assertFalse(improvement_roll(150, 0)["beat"])


class TestTheReturnedShape(EvenniaTestCase):
    """
    The three reported figures have to agree with each other.

    "total" is documented as roll + int_bonus. D.2 could have reported the raw
    INT score in int_bonus and quietly falsified that line above 100; this class
    is what makes the choice enforced rather than remembered.
    """

    def test_total_is_always_the_roll_plus_the_applied_int(self):
        checked = []
        with mock.patch("world.improvement.randint", pinned(37)):
            for skill in (1, 40, 100, 101, 150, 250):
                res = improvement_roll(skill, 12)
                self.assertEqual(res["total"], res["roll"] + res["int_bonus"],
                                 f"skill {skill}")
                checked.append(skill)
        self.assertTrue(checked, "the sweep ran on nothing")

    def test_the_gain_is_untouched_by_the_band(self):
        """P-3: the band changes what you roll against, never what you win."""
        with mock.patch("world.improvement.randint", pinned(100, d4=3)):
            beaten = improvement_roll(150, 12)
        self.assertTrue(beaten["beat"])
        self.assertEqual(beaten["gained"], 4)          # 1D4 (3) + 1

        with mock.patch("world.improvement.randint", pinned(1)):
            floored = improvement_roll(150, 12)
        self.assertFalse(floored["beat"])
        self.assertEqual(floored["gained"], 1)

    def test_the_gain_is_never_zero_at_any_skill(self):
        checked = []
        for skill in (0, 50, 100, 200, 400):
            for _ in range(20):
                self.assertGreaterEqual(improvement_roll(skill, 12)["gained"], 1)
            checked.append(skill)
        self.assertTrue(checked, "the sweep ran on nothing")
