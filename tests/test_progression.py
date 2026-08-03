"""
Unit tests for the skill-progression XP curve. Stage 4.5, Component A.1.

Written to the pattern in `tests/test_knowledge.py`, the golden reference for
this project (AGENTS.md section 0A).

WHAT IT COVERS
--------------
* world.progression.xp_threshold          -- level -> lifetime XP
* world.progression.level_for_xp          -- lifetime XP -> level
* world.progression.progress_within_level -- lifetime XP -> (earned, needed, fraction)

BASE CLASS
----------
`EvenniaTestCase` throughout -- the lightest available. A.1 is pure arithmetic
with no Evennia import, no database and no typeclass, so building the
.char1/.room1 object graph (EvenniaTest) would cost setup time for fixtures no
test here touches. Same call as `tests/test_currency.py` makes for its own pure
denomination layer.

DELIBERATE DEVIATION FROM THE DECOMPOSITION
-------------------------------------------
Decomposition section 3 specifies three tests at the shipped calibration. The
invariants below are run over a *matrix* of calibrations instead, because they
are properties of the construction rather than of (6, 20), and because decision
P-5 states in writing that these constants will be recomputed.

The deviation is not stylistic; it was measured. Delete the step-down correction
loop from `level_for_xp` and run the three specified tests at (6, 20): all pass.
Run them at (6, 7): 176 failures. At (1, 5): 268. Tested only at the shipped
calibration, this suite cannot distinguish correct code from code missing half
its correction logic -- and would start failing at the exact moment someone
recalibrates, which is the worst possible moment to learn about it.

HOW TO RUN
----------
The --settings flag is NOT optional anywhere in this project.

    evennia test --settings settings.py tests                   # this package
    evennia test --settings settings.py tests.test_progression  # this module
    # one test:
    evennia test --settings settings.py \
        tests.test_progression.TestLevelForXp.test_round_trip_is_exact
"""

from django.test import override_settings

from evennia.utils.test_resources import EvenniaTestCase

from world.progression import level_for_xp, progress_within_level, xp_threshold

# The calibration matrix. (6, 20) is what ships; the rest exist because P-5
# promises recalibration and because the off-by-one correction only actually
# fires at some of these. Deliberately includes the degenerate low end
# (BASE=1, SPAN=1 doubles every single point) -- if an invariant survives that,
# it is not surviving by luck of the numbers.
CALIBRATIONS = [
    (6, 20),   # shipped
    (6, 7),    # RuneScape-like span; rejected by P-4 but arithmetically valid
    (3, 10),
    (1, 5),
    (20, 25),
    (6, 50),   # very flat
    (1, 1),    # degenerate: cost doubles every point
]

# Round-trip range. 500, not 100: P-7 makes above-cap levels real, so the
# functions must be inverses well past the old ceiling.
LEVEL_RANGE = range(0, 501)


class TestXpThreshold(EvenniaTestCase):
    """
    Pins the forward direction.

    The bug this presses on: a flooring error or an off-by-one in the geometric
    sum that makes two adjacent levels cost the same. Equal thresholds would
    break `level_for_xp`'s termination argument, so monotonicity is not a
    nicety here -- it is the precondition the inverse relies on.
    """

    def test_level_zero_costs_nothing(self):
        self.assertEqual(xp_threshold(0), 0)

    def test_strictly_increasing_at_every_calibration(self):
        for base, span in CALIBRATIONS:
            with self.subTest(base=base, span=span):
                with override_settings(
                    SKILL_XP_BASE=base, SKILL_XP_DOUBLING_SPAN=span
                ):
                    previous = xp_threshold(0)
                    for level in range(1, 501):
                        current = xp_threshold(level)
                        self.assertGreater(
                            current,
                            previous,
                            f"threshold({level}) did not exceed threshold({level - 1})",
                        )
                        previous = current

    def test_cost_doubles_over_one_span(self):
        """
        The defining property of P-4's curve shape, in executable form.

        The cost of point (n + SPAN) should be twice the cost of point n. Tested
        with a tolerance of one XP because both thresholds are floored, so the
        difference of differences carries up to two units of flooring error.
        """
        with override_settings(SKILL_XP_BASE=6, SKILL_XP_DOUBLING_SPAN=20):
            for n in (1, 10, 40, 100):
                cost_n = xp_threshold(n) - xp_threshold(n - 1)
                cost_far = xp_threshold(n + 20) - xp_threshold(n + 19)
                self.assertAlmostEqual(cost_far, 2 * cost_n, delta=2)

    def test_documented_thresholds_hold(self):
        """
        The five numbers quoted in the settings comment, the module docstring
        and the decomposition. Pinned executably so a doc drifting away from the
        code cannot go unnoticed -- same stance test_currency.py takes on the
        denomination relationship.
        """
        with override_settings(SKILL_XP_BASE=6, SKILL_XP_DOUBLING_SPAN=20):
            self.assertEqual(xp_threshold(1), 6)
            self.assertEqual(xp_threshold(20), 170)
            self.assertEqual(xp_threshold(50), 792)
            self.assertEqual(xp_threshold(100), 5274)
            self.assertEqual(xp_threshold(150), 30628)

    def test_non_positive_levels_clamp_to_zero(self):
        self.assertEqual(xp_threshold(-1), 0)
        self.assertEqual(xp_threshold(-500), 0)


class TestLevelForXp(EvenniaTestCase):
    """
    Pins the inverse direction. This class is the load-bearing one.

    Two distinct bugs are under pressure here, and they are caught by two
    different tests:

    * `test_round_trip_is_exact` catches a wrong seed formula or a missing
      step-*up* loop -- a level silently lost or gained by passing through
      storage.
    * `test_one_xp_short_is_one_level_short` catches a missing step-*down* loop.
      This is the off-by-one that only manifests at some calibrations, so it is
      the test that most needs the matrix. At (6, 20) alone it passes with the
      loop deleted.
    """

    def test_round_trip_is_exact(self):
        for base, span in CALIBRATIONS:
            with self.subTest(base=base, span=span):
                with override_settings(
                    SKILL_XP_BASE=base, SKILL_XP_DOUBLING_SPAN=span
                ):
                    for level in LEVEL_RANGE:
                        self.assertEqual(
                            level_for_xp(xp_threshold(level)),
                            level,
                            f"round trip failed at level {level}",
                        )

    def test_one_xp_short_is_one_level_short(self):
        for base, span in CALIBRATIONS:
            with self.subTest(base=base, span=span):
                with override_settings(
                    SKILL_XP_BASE=base, SKILL_XP_DOUBLING_SPAN=span
                ):
                    for level in range(1, 501):
                        self.assertEqual(
                            level_for_xp(xp_threshold(level) - 1),
                            level - 1,
                            f"one XP below threshold({level}) did not read as "
                            f"level {level - 1}",
                        )

    def test_one_xp_over_stays_at_level(self):
        """One XP past a threshold must not advance a level early."""
        with override_settings(SKILL_XP_BASE=6, SKILL_XP_DOUBLING_SPAN=20):
            for level in range(1, 200):
                self.assertEqual(level_for_xp(xp_threshold(level) + 1), level)

    def test_zero_and_negative_xp_are_level_zero(self):
        self.assertEqual(level_for_xp(0), 0)
        self.assertEqual(level_for_xp(-1), 0)
        self.assertEqual(level_for_xp(-9999), 0)

    def test_is_monotonic_in_xp(self):
        """
        More XP never means a lower level. Cheap to state, and it is the
        property a player would notice being violated before any developer
        would: banking XP must never take a percentage point away.
        """
        with override_settings(SKILL_XP_BASE=6, SKILL_XP_DOUBLING_SPAN=20):
            previous = 0
            for total in range(0, 6000, 7):
                level = level_for_xp(total)
                self.assertGreaterEqual(level, previous)
                previous = level


class TestProgressWithinLevel(EvenniaTestCase):
    """
    Pins the derived triple Component D's progress bar will render.

    The bug this presses on: a bar that reads full, overflows, or divides by
    zero. `fraction` must stay in [0.0, 1.0) -- 1.0 exactly is a bug, because
    reaching the next threshold means the *level* advanced and the bar resets.
    """

    def test_exactly_at_threshold_is_empty_bar(self):
        with override_settings(SKILL_XP_BASE=6, SKILL_XP_DOUBLING_SPAN=20):
            for level in (0, 1, 20, 100, 250):
                earned, needed, fraction = progress_within_level(xp_threshold(level))
                self.assertEqual(earned, 0)
                self.assertGreater(needed, 0)
                self.assertEqual(fraction, 0.0)

    def test_fraction_never_reaches_one(self):
        for base, span in CALIBRATIONS:
            with self.subTest(base=base, span=span):
                with override_settings(
                    SKILL_XP_BASE=base, SKILL_XP_DOUBLING_SPAN=span
                ):
                    for total in range(0, 4000, 11):
                        _earned, _needed, fraction = progress_within_level(total)
                        self.assertGreaterEqual(fraction, 0.0)
                        self.assertLess(fraction, 1.0)

    def test_parts_reconstruct_the_total(self):
        """earned + threshold(level) == total_xp, for any total."""
        with override_settings(SKILL_XP_BASE=6, SKILL_XP_DOUBLING_SPAN=20):
            for total in range(0, 3000, 13):
                earned, _needed, _fraction = progress_within_level(total)
                level = level_for_xp(total)
                self.assertEqual(xp_threshold(level) + earned, total)

    def test_needed_matches_the_gap_between_thresholds(self):
        with override_settings(SKILL_XP_BASE=6, SKILL_XP_DOUBLING_SPAN=20):
            for total in (0, 5, 6, 169, 170, 5273, 5274):
                _earned, needed, _fraction = progress_within_level(total)
                level = level_for_xp(total)
                self.assertEqual(
                    needed, xp_threshold(level + 1) - xp_threshold(level)
                )

    def test_negative_xp_clamps(self):
        earned, needed, fraction = progress_within_level(-50)
        self.assertEqual(earned, 0)
        self.assertGreater(needed, 0)
        self.assertEqual(fraction, 0.0)


class TestCalibrationSafety(EvenniaTestCase):
    """
    Pins the clamps in `_calibration`.

    These are not politeness. Both bad values raise ZeroDivisionError without
    the clamp -- SPAN=0 in the ``1 / span`` exponent, BASE=0 in level_for_xp's
    seed -- and BASE=0 additionally flattens every threshold to 0, which would
    make the step-up loop non-terminating for anything that got past the seed.
    A typo in settings.py should not be able to hang or crash a craft.

    Verified by mutation: removing either clamp turns the matching test below
    red.
    """

    def test_zero_span_does_not_raise(self):
        with override_settings(SKILL_XP_BASE=6, SKILL_XP_DOUBLING_SPAN=0):
            self.assertGreater(xp_threshold(1), 0)
            self.assertEqual(level_for_xp(0), 0)

    def test_zero_base_behaves_like_one(self):
        with override_settings(SKILL_XP_BASE=0, SKILL_XP_DOUBLING_SPAN=20):
            # Without the clamp the first assertion already fails (every
            # threshold is 0) and level_for_xp raises ZeroDivisionError on any
            # positive total.
            self.assertGreater(xp_threshold(1), 0)
            self.assertEqual(level_for_xp(xp_threshold(5)), 5)
            self.assertEqual(level_for_xp(37), level_for_xp(37))

    def test_module_defaults_match_shipped_settings(self):
        """
        The module's private fallbacks exist for contexts that never loaded our
        settings (a bare shell against a half-configured game). They are pinned
        equal to the shipped constants on purpose: a missing setting must
        degrade to *identical* behaviour, never to a quietly different curve.

        This test is what keeps that promise true after a recalibration -- edit
        settings.py alone and it fails, which is the reminder to edit both.
        """
        from django.conf import settings as live

        from world.progression import _DEFAULT_XP_BASE, _DEFAULT_XP_DOUBLING_SPAN

        self.assertEqual(_DEFAULT_XP_BASE, live.SKILL_XP_BASE)
        self.assertEqual(_DEFAULT_XP_DOUBLING_SPAN, live.SKILL_XP_DOUBLING_SPAN)
