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

The opposed forms (Skill-Check Forms decomposition, slice SC) follow the band
tests. Their dice are pinned with `side_effect` in the order the code rolls
them: attacker, defender, then the coin if one is tossed.
"""

from unittest import mock

from evennia.utils.test_resources import EvenniaTestCase

from world.skillcheck import (
    ATTACKER,
    CRITICAL,
    DEFENDER,
    FAILURE,
    FUMBLE,
    STALEMATE,
    SUCCESS,
    opposed_check,
    skill_check,
)

ROLL = "world.skillcheck.randint"


def check(target, roll):
    """skill_check at exactly `target` with the d100 showing `roll`."""
    with mock.patch(ROLL, return_value=roll):
        return skill_check(target)


def opposed(attacker, defender, dice, **mods):
    """opposed_check with the dice in rolling order; returns (result, dice used)."""
    with mock.patch(ROLL, side_effect=list(dice)) as die:
        result = opposed_check(attacker, defender, **mods)
    return result, die.call_count


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


class _OpposedTest(EvenniaTestCase):
    def assertWinner(self, attacker, defender, dice, winner, **mods):
        """The winner, and that exactly the dice given were rolled."""
        result, used = opposed(attacker, defender, dice, **mods)
        self.assertEqual(result["winner"], winner)
        self.assertEqual(used, len(dice))
        return result


class TestOpposedOrder(_OpposedTest):
    """
    Legend p. 45's order: both fail -> stalemate; the higher level; the higher
    roll within the skill; the higher skill; a coin. Every test here passed
    before SC-T1 too: they pin the order so that the refactor cannot move it.
    """

    def test_book_stealth_beats_perception_on_the_higher_roll(self):
        # p. 45: Stealth 75 % rolling 71 against Perception 60 % rolling 59.
        self.assertWinner(75, 60, [71, 59], ATTACKER)

    def test_book_perception_beats_stealth_on_the_higher_roll(self):
        # p. 45: the guard's 59 against the thief's 54.
        self.assertWinner(75, 60, [54, 59], DEFENDER)

    def test_book_critical_beats_a_higher_success(self):
        # p. 45: Athletics 35 % rolling 02 (a critical) against 95 % rolling 94.
        self.assertWinner(35, 95, [2, 94], ATTACKER)

    def test_same_roll_goes_to_the_higher_skill(self):
        # SCM3: a reversed skill tie-break would give it to the defender.
        self.assertWinner(50, 40, [20, 20], ATTACKER)

    def test_dead_heat_is_a_coin(self):
        self.assertWinner(50, 50, [20, 20, 1], ATTACKER)
        self.assertWinner(50, 50, [20, 20, 2], DEFENDER)

    def test_failure_against_fumble_is_a_stalemate(self):
        # SCM4: without the both-failed check, failure outranks fumble.
        result = self.assertWinner(50, 40, [80, 99], STALEMATE)
        self.assertEqual(result["attacker"]["result"], FAILURE)
        self.assertEqual(result["defender"]["result"], FUMBLE)


class TestOutsideTheSkill(_OpposedTest):
    """
    OC1 (SC2): between two successes of the same level the roll counts only
    if it lies within the skill (roll <= target); a roll outside it counts as
    0. Before SC-T1 the tie went to the higher raw roll, so an automatic
    success at 02-05 could beat a success within the skill.
    """

    def test_automatic_success_loses_to_a_success_within_the_skill(self):
        # Target 3 rolling 05 against target 30 rolling 04.
        self.assertWinner(3, 30, [5, 4], DEFENDER)

    def test_both_outside_goes_to_the_higher_skill(self):
        # Target 3 rolling 04 against target 2 rolling 05: both count 0.
        self.assertWinner(3, 2, [4, 5], ATTACKER)

    def test_a_roll_equal_to_the_target_is_within_the_skill(self):
        # SCM2: with `<` the attacker's 30 would count 0 and lose to 29.
        self.assertWinner(30, 60, [30, 29], ATTACKER)

    def test_automatic_success_still_beats_a_failure(self):
        # The level decides before the roll does.
        self.assertWinner(3, 30, [5, 80], ATTACKER)
