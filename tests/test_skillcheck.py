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
    compare_levels,
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


class TestOpposedOverOneHundred(_OpposedTest):
    """
    OC2 (SC3), Legend p. 45: the highest modified target in the contest is
    lowered to 100 and its excess is taken off both sides. Before SC-T2 the
    targets went to skill_check as they were and the result had no "excess".
    """

    # Dice that settle every target line below without a coin.
    DICE = [50, 95]

    def assertTargets(self, attacker, defender, excess, targets, **mods):
        result, _ = opposed(attacker, defender, self.DICE, **mods)
        self.assertEqual(result["excess"], excess)
        self.assertEqual(
            (result["attacker"]["target"], result["defender"]["target"]), targets
        )

    def test_the_master_drops_to_100_and_the_lesser_side_pays(self):
        self.assertTargets(120, 30, 20, (100, 10))

    def test_the_highest_is_found_after_the_modifiers(self):
        # SCM5: taken from the skills before their modifiers, the excess would be 20.
        self.assertTargets(120, 30, 0, (100, 30), attacker_mod=-20)

    def test_the_defender_can_be_the_master(self):
        self.assertTargets(60, 130, 30, (30, 100))

    def test_both_above_100(self):
        self.assertTargets(200, 150, 100, (100, 50))

    def test_below_100_nothing_changes(self):
        # SCM7: without max(0, ...) the excess would be -20, paid out as a bonus.
        self.assertTargets(50, 30, 0, (50, 30))

    def test_the_excess_is_reported_when_it_is_0(self):
        result, _ = opposed(100, 30, self.DICE)
        self.assertIn("excess", result)
        self.assertEqual(result["excess"], 0)

    def test_a_critical_at_120_is_a_plain_success_at_100(self):
        # 11 is a critical at 120 (01-12) and a plain success at 100 (01-10);
        # the defender's 30 is the higher roll within its lowered 40.
        result = self.assertWinner(120, 60, [11, 30], DEFENDER)
        self.assertEqual(result["attacker"]["result"], SUCCESS)
        self.assertEqual(result["defender"]["result"], SUCCESS)

    def test_the_lowered_targets_decide_the_bands(self):
        # 99 is an automatic failure at 100, and a fumble at the defender's 40.
        result = self.assertWinner(120, 60, [99, 99], STALEMATE)
        self.assertEqual(result["attacker"]["result"], FAILURE)
        self.assertEqual(result["defender"]["result"], FUMBLE)


# Legend p. 131, "Levels of Success", transcribed cell for cell and not
# computed. Rows are the defender's level, columns the attacker's. None is the
# book's "--" (nobody gains a level); otherwise (winner, levels).
LEVELS_OF_SUCCESS = {
    CRITICAL: {CRITICAL: None, SUCCESS: (DEFENDER, 1), FAILURE: (DEFENDER, 2), FUMBLE: (DEFENDER, 3)},
    SUCCESS: {CRITICAL: (ATTACKER, 1), SUCCESS: None, FAILURE: (DEFENDER, 1), FUMBLE: (DEFENDER, 2)},
    FAILURE: {CRITICAL: (ATTACKER, 2), SUCCESS: (ATTACKER, 1), FAILURE: None, FUMBLE: None},
    FUMBLE: {CRITICAL: (ATTACKER, 3), SUCCESS: (ATTACKER, 2), FAILURE: None, FUMBLE: None},
}


class TestCompareLevels(EvenniaTestCase):
    """
    OC3 (SC1): attack against parry compares two levels of success by the
    table on p. 131. It is not an opposed test: nothing is rolled and the
    over-100 % rule does not apply. Where neither side succeeded the cell is
    "--", which the ranks alone would not give (failure outranks fumble).
    """

    def test_the_sixteen_cells(self):
        for defender, row in LEVELS_OF_SUCCESS.items():
            for attacker, cell in row.items():
                winner, levels = cell if cell else (None, 0)
                with self.subTest(attacker=attacker, defender=defender):
                    self.assertEqual(
                        compare_levels(attacker, defender),
                        {"winner": winner, "levels": levels},
                    )

    def test_nothing_is_rolled(self):
        with mock.patch(ROLL, side_effect=AssertionError("compare_levels rolled")) as die:
            for defender, row in LEVELS_OF_SUCCESS.items():
                for attacker in row:
                    compare_levels(attacker, defender)
        self.assertEqual(die.call_count, 0)

    def test_an_unknown_level_is_refused(self):
        with self.assertRaisesRegex(ValueError, "hit"):
            compare_levels("hit", SUCCESS)
        with self.assertRaisesRegex(ValueError, "miss"):
            compare_levels(SUCCESS, "miss")

    def test_a_defender_without_an_action(self):
        # p. 131: a defender with no Combat Action, or who does not parry, is
        # treated as having automatically rolled a Failure.
        self.assertEqual(compare_levels(SUCCESS, FAILURE), {"winner": ATTACKER, "levels": 1})
