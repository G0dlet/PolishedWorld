"""
Tests for world.skillcheck.skill_check -- Legend's automatic bands (Recipe
Mastery M5.1, MD8).

The first direct tests of the primitive every skill test in the game goes
through. The die is pinned at `world.skillcheck.randint`; `skill_check(t)`
with no modifier makes the target exactly `t`.

Resolution order under test (MD8): fumble (99-00 below 100%, 00 at or above)
-> automatic failure (96-98; 96-99 at or above 100%) -> critical -> automatic
success (01-05) -> roll <= target -> failure.

Targets 0, 3, 97 and 120 sit at the edges where the bands decide; 50 is the
control where they change nothing.
"""

from unittest import mock

from evennia.utils.test_resources import EvenniaTestCase

from world.skillcheck import CRITICAL, FAILURE, FUMBLE, SUCCESS, skill_check

ROLL = "world.skillcheck.randint"


def check(target, roll):
    """skill_check at exactly `target` with the d100 showing `roll`."""
    with mock.patch(ROLL, return_value=roll):
        return skill_check(target)


class _BandTest(EvenniaTestCase):
    def assertResults(self, target, expected):
        """`expected` maps roll -> result tier at this target."""
        for roll, result in expected.items():
            with self.subTest(target=target, roll=roll):
                outcome = check(target, roll)
                self.assertEqual(outcome["result"], result)
                self.assertEqual(outcome["success"], result in (CRITICAL, SUCCESS))


class TestTargetZero(_BandTest):
    """An impossible-on-paper target: only the bands decide."""

    def test_01_is_critical(self):
        self.assertResults(0, {1: CRITICAL})

    def test_02_to_05_succeed_automatically(self):
        self.assertResults(0, {2: SUCCESS, 3: SUCCESS, 4: SUCCESS, 5: SUCCESS})

    def test_06_fails(self):
        # RM28: an automatic-success band of 01-06 would pass this roll.
        self.assertResults(0, {6: FAILURE})

    def test_96_fails_and_99_fumbles(self):
        self.assertResults(0, {96: FAILURE, 99: FUMBLE, 100: FUMBLE})


class TestTargetThree(_BandTest):
    def test_04_succeeds_above_the_target(self):
        self.assertResults(3, {4: SUCCESS})

    def test_margin_and_crit_score_are_not_adjusted(self):
        # The band decides the result only: margin stays target - roll.
        outcome = check(3, 5)
        self.assertEqual(outcome["result"], SUCCESS)
        self.assertEqual(outcome["margin"], -2)
        self.assertEqual(outcome["crit_score"], 0)
        self.assertEqual(outcome["target"], 3)
        self.assertEqual(outcome["roll"], 5)


class TestTargetNinetySeven(_BandTest):
    """Below 100%: 96-98 fail automatically, 99-00 still fumble."""

    def test_96_to_98_fail_automatically(self):
        # RM27b: a band starting above 96 would let 96 succeed.
        self.assertResults(97, {96: FAILURE, 97: FAILURE, 98: FAILURE})

    def test_99_still_fumbles(self):
        # RM25: automatic failure tested before the fumble would say failure.
        self.assertResults(97, {99: FUMBLE, 100: FUMBLE})

    def test_95_succeeds(self):
        # RM27: an automatic-failure band starting at 95 would fail this.
        self.assertResults(97, {95: SUCCESS})


class TestTargetOneTwenty(_BandTest):
    """At or above 100%: only 00 fumbles, so 96-99 are automatic failures."""

    def test_wide_critical_band(self):
        self.assertResults(120, {12: CRITICAL, 13: SUCCESS})

    def test_96_and_99_fail_automatically(self):
        self.assertResults(120, {96: FAILURE, 97: FAILURE, 98: FAILURE, 99: FAILURE})

    def test_00_fumbles(self):
        self.assertResults(120, {100: FUMBLE})


class TestTargetFifty(_BandTest):
    """The control: mid-range targets resolve exactly as before."""

    def test_01_is_critical_not_an_automatic_success(self):
        # RM26: automatic success tested before the critical would say success.
        self.assertResults(50, {1: CRITICAL, 5: CRITICAL})

    def test_boundary_unchanged(self):
        self.assertResults(50, {50: SUCCESS, 51: FAILURE})
