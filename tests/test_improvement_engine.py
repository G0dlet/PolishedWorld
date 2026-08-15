"""
Unit tests for the improvement engine after the XP swap. Stage 4.5, Component C.1.

Written to the pattern in `tests/test_knowledge.py`, the golden reference for
this project (AGENTS.md section 0A).

WHAT IT COVERS
--------------
* typeclasses.characters.Character.improve_skill_on_use -- the engine C.1 rewrote
* commands.crafting_commands.CmdScribe -- the sixth call-site (P-6)

⚠️ READ THIS BEFORE TRUSTING A GREEN RUN ON THIS FILE
-----------------------------------------------------
Before C.1 there were **zero** unit tests under `improve_skill_on_use`,
`attempt_skill_improvement` or `_improvement_feedback`. The 363-test baseline
this branch inherited proved nothing whatsoever about the method C.1 rewrote --
it could have been deleted outright and the suite would still have been green.
This file is the first net under it, which means it is also the only thing
standing between a future edit and a silent regression. Add to it rather than
around it.

WHAT THESE TESTS ARE FOR, AND WHAT THEY ARE NOT FOR
---------------------------------------------------
They test the *reinterpretation*, not the roll. `world/improvement.py` is
unchanged (P-3) and already has its own maths; re-testing 1D4+1 here would only
couple this file to a module C.1 never touched. Every test below therefore
either pins the roll to a fixed grain or ignores it entirely, and asks the one
question C.1 actually answers: given a grain, what happens to the lifetime total,
and what happens to `.current`?

THE CALIBRATION IS PINNED, DELIBERATELY -- AND THIS IS THE OPPOSITE OF WHAT
tests/test_progression.py AND tests/test_skill_xp.py DO
--------------------------------------------------------------------------
Those two files sweep a calibration matrix, because what they assert (the curve's
shape, the derived floor) must hold under any constants P-5 later hands them.
This file pins (6, 20) with `override_settings` instead, because several of its
assertions are only *meaningful* at a calibration where one point costs more than
one tick's grain. At the degenerate (1, 1) a grain of 5 legitimately crosses
several thresholds at once, and "the level rises by exactly 1" would be a false
failure rather than a caught bug. Pinning states that dependency out loud instead
of inheriting whatever settings.py happens to say on the day.

BASE CLASSES
------------
`EvenniaTest` for the engine: it needs a real object graph (traits, Attributes)
but no command parsing. `EvenniaCommandTest` only for the scribe call-site, where
the whole point is that the command wiring reaches the engine.

MUTATION-VERIFIED
-----------------
Four mutations were introduced and measured, not reasoned about. Results, as run:

1. `.current` written unconditionally (drop the `if new != old:` guard).
   **1 failure**, and only one: `TestLevelIsWrittenOnlyWhenItMoves
   ::test_a_tick_that_banks_without_levelling_never_writes_current`. Worth
   noticing how narrow that is -- every value-equality assertion in this file
   stays green under this mutation, because the value written is the same value
   that was there. Only the write-spy sees it. That is exactly why decomposition
   section 5 specifies "assert the Attribute was not written, not merely that the
   value is equal", and it is why the spy exists instead of a `assertEqual`.
2. `new = min(cap, old + res["gained"])` -- i.e. reverting C.1's central line to
   the shipped behaviour while keeping the banking. **12 failures** across six of
   the seven classes; only `TestCapShortCircuit` stays green, which is correct,
   since the cap branch returns before that line. This is the mutation the file
   is densest against, and deliberately so: it is the single edit that would undo
   the epic while leaving every individual tick looking plausible.
3. The F7 floor repair deleted. **2 failures**, both in `TestFloorRepair`, and
   both are de-levellings -- craft 60 dropping to 21 on the next successful
   craft. This mutation is what the shipped code looked like before F7 was found,
   so those two tests are the whole record of why the branch exists. Note that
   `test_the_repair_is_a_no_op_on_a_consistent_total` stays green here: it pins
   the normal path, so it cannot also be the guard for the abnormal one.
4. The cap short-circuit deleted (letting a capped skill roll and bank).
   **2 failures and 1 error** in `TestCapShortCircuit`. The error rather than a
   failure is `test_a_capped_skill_does_not_roll`, where the `mock.patch` with no
   return value hands the engine a `MagicMock` and the arithmetic blows up -- a
   loud, correct signal that the roll was reached at all. The one that matters is
   `test_a_capped_skill_banks_no_xp`: without the short-circuit the invariant
   `.current == level_for_xp(total)` breaks silently at the ceiling and stays
   broken until D.2 lifts the cap, at which point the character jumps several
   points at once. Nothing else in the suite notices.

HOW TO RUN
----------
The --settings flag is NOT optional anywhere in this project.

    evennia test --settings settings.py tests                        # this package
    evennia test --settings settings.py tests.test_improvement_engine
    # one test:
    evennia test --settings settings.py \
        tests.test_improvement_engine.TestFloorRepair.test_a_hand_raised_level_is_not_de_levelled
"""

from collections.abc import Mapping
from contextlib import contextmanager
from unittest import mock

from django.test import override_settings

from evennia.contrib.rpg.traits.traits import CounterTrait
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.crafting_commands import CmdScribe
from world.progression import _BAR_EMPTY, _BAR_FULL, level_for_xp, xp_threshold

# The shipped calibration, pinned. See the module docstring for why this file
# pins where its two siblings sweep.
SHIPPED = dict(SKILL_XP_BASE=6, SKILL_XP_DOUBLING_SPAN=20)

CHARACTER = "typeclasses.characters.Character"

# From tests/test_knowledge.py: requires_knowledge=True and NO min_skill, so the
# per-recipe mastery floor is 0 and only scribe's own SCRIBE_MIN_CRAFT bites.
CLOTH = "cloth"


def fixed_roll(gained, beat=False):
    """
    A stand-in for `world.improvement.improvement_roll` with a known grain.

    Patched in at `typeclasses.characters.improvement_roll` -- the name the
    engine actually resolves -- not at `world.improvement.improvement_roll`,
    which `from ... import` already bound into the character module's namespace
    at import time. Patching the origin would be a test that silently tests
    nothing.

    The returned dict carries every key the real function documents, so a future
    reader of the engine cannot tell the difference and a future engine that
    starts consuming "roll" or "total" does not fail here for the wrong reason.
    """

    def _roll(skill_value, int_char):
        return {
            "gained": gained,
            "roll": 1,
            "int_bonus": int(int_char),
            "total": 1 + int(int_char),
            "beat": beat,
        }

    return _roll


@contextmanager
def watch_current_writes():
    """
    Record every assignment to `CounterTrait.current` while the block runs.

    Yields:
        list: the values assigned, in order. Empty means nothing was written.

    WHY A SPY AND NOT AN EQUALITY CHECK. Component B could assert "this read did
    not write" with `attributes.has("skill_xp")`, because the XP Attribute does
    not exist until the first bank. That trick is unavailable here: the trait
    Attribute always exists, and the value C.1 must not write is usually the same
    value that is already there. `assertEqual(skill.current, 20)` passes whether
    the guard is present or absent. Only observing the write itself distinguishes
    them, which is what decomposition section 5 (b) asks for.

    HOW IT WORKS, verified against Evennia 6.1.0 rather than assumed:
    `CounterTrait.current` is a property whose setter writes `_data["current"]`
    (traits.py:1455-1458), and `Trait.__setattr__` (traits.py:975+) dispatches
    an assignment by looking the property up on `self.__class__` and calling its
    `fset`. Replacing the class attribute with a wrapping property therefore
    catches assignments made through either path. Only `CounterTrait` is patched;
    `GaugeTrait` declares its own `current` and is left alone, so a survival tick
    running in the same test cannot pollute the record.
    """
    original = CounterTrait.current  # the property object itself
    writes = []

    def _spy(self, value):
        writes.append(value)
        original.fset(self, value)

    with mock.patch.object(
        CounterTrait, "current", property(original.fget, _spy, original.fdel)
    ):
        yield writes


@override_settings(**SHIPPED)
class TestBankingTheGrain(EvenniaTest):
    """
    Decomposition section 5, test (a): a tick moves the lifetime total by exactly
    the roll's `gained`, no more and no less.

    This is the test that would catch the engine banking the wrong number --
    double-banking, banking the level instead of the grain, or banking through a
    path that bypasses `SkillXPHandler.add()` and so loses B.2's derived floor.
    It says nothing about levels; that is the next class's job.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.craft = self.char1.skills.get("craft")
        self.craft.current = 40

    def test_a_tick_moves_the_total_by_exactly_the_grain(self):
        before = self.char1.skill_xp.get("craft")

        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(3)):
            self.char1.improve_skill_on_use("craft")

        self.assertEqual(self.char1.skill_xp.get("craft"), before + 3)

    def test_the_first_tick_banks_onto_the_derived_floor_not_onto_zero(self):
        # The single line B.2 exists to protect, observed from C.1's side: a
        # character who has never banked stands at xp_threshold(.current), and
        # the first grain lands on top of that. Banking onto 0 instead would
        # read back through level_for_xp as level 0 -- the epic wiping everyone's
        # skills rather than shipping.
        self.assertFalse(self.char1.attributes.has("skill_xp"))

        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(2)):
            self.char1.improve_skill_on_use("craft")

        self.assertEqual(self.char1.skill_xp.get("craft"), xp_threshold(40) + 2)

    def test_the_result_reports_the_grain_and_the_resulting_total(self):
        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(4)):
            result = self.char1.improve_skill_on_use("craft")

        self.assertTrue(result["rolled"])
        self.assertEqual(result["xp_gained"], 4)
        self.assertEqual(result["xp_total"], self.char1.skill_xp.get("craft"))
        # The progress triple D.1 will draw its bar from, derived on read.
        earned, needed, fraction = result["progress"]
        self.assertGreater(needed, 0)
        self.assertEqual(earned, result["xp_total"] - xp_threshold(result["new"]))
        self.assertAlmostEqual(fraction, earned / needed)

    def test_an_unknown_skill_returns_none_and_banks_nothing(self):
        # Unchanged contract, retested because C.1 moved the early return above a
        # write it must still never reach. A shared call-site passing a key this
        # character lacks must stay a silent no-op, not create an orphan XP row.
        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(5)):
            self.assertIsNone(self.char1.improve_skill_on_use("basketweaving"))

        self.assertFalse(self.char1.attributes.has("skill_xp"))


@override_settings(**SHIPPED)
class TestLevelIsWrittenOnlyWhenItMoves(EvenniaTest):
    """
    Decomposition section 5, test (b), and the reason `watch_current_writes`
    exists: `.current` must be assigned only on a tick that actually changed the
    level. P-2 makes it a materialised cache with exactly one writer, and a write
    per craft would be churn on a value that moves once in dozens.

    Note the asymmetry in what these two tests can catch. The second would still
    pass if the guard were removed. The first is the only assertion in this file
    -- or anywhere in the suite -- that fails when it is.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.craft = self.char1.skills.get("craft")
        self.craft.current = 40

    def test_a_tick_that_banks_without_levelling_never_writes_current(self):
        # A grain of 1 against a point that costs ~21 XP at level 40: the level
        # cannot move, so nothing may be written.
        with watch_current_writes() as writes:
            with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(1)):
                result = self.char1.improve_skill_on_use("craft")

        self.assertEqual(writes, [])
        self.assertEqual(result["delta"], 0)
        self.assertEqual(result["old"], result["new"])

    def test_a_tick_that_crosses_a_threshold_writes_current_exactly_once(self):
        # Park the total one XP short of level 41, then bank a single point.
        self.char1.skill_xp.add("craft", xp_threshold(41) - 1 - xp_threshold(40))

        with watch_current_writes() as writes:
            with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(1)):
                result = self.char1.improve_skill_on_use("craft")

        self.assertEqual(writes, [41])
        self.assertEqual(result["delta"], 1)
        self.assertEqual(int(self.craft.current), 41)


@override_settings(**SHIPPED)
class TestTheCurveDecidesTheLevel(EvenniaTest):
    """
    Decomposition section 5, test (c): the curve decides the level, the roll does
    not. A grain of 5 used to be +5 percentage points; it is now 5 XP, which at
    level 40 is a quarter of one point.

    This is the class that fails loudest if anyone ever "restores" the old
    behaviour, and it is deliberately written so that the maximum possible grain
    still cannot buy more than the threshold allows.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.craft = self.char1.skills.get("craft")
        self.craft.current = 40

    def test_the_biggest_grain_still_raises_the_level_by_exactly_one(self):
        # One XP short of level 41, then the largest grain Legend can roll.
        # Old behaviour: +5 points. New behaviour: +1 point, because point 42
        # costs ~21 XP and the tick bought 5.
        self.char1.skill_xp.add("craft", xp_threshold(41) - 1 - xp_threshold(40))

        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(5, beat=True)):
            result = self.char1.improve_skill_on_use("craft")

        self.assertEqual(result["new"], 41)
        self.assertEqual(result["delta"], 1)

    def test_the_biggest_grain_alone_moves_nothing_at_all(self):
        # The same maximal roll, from a level's starting floor rather than its
        # edge: 5 XP against a ~21 XP point buys nothing visible.
        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(5, beat=True)):
            result = self.char1.improve_skill_on_use("craft")

        self.assertEqual(result["new"], 40)
        self.assertEqual(result["delta"], 0)
        self.assertEqual(result["crossed"], [])
        # ... and it was not silently lost either.
        self.assertEqual(result["xp_gained"], 5)

    def test_the_level_always_matches_the_total_it_was_derived_from(self):
        # The P-2 invariant, asserted directly rather than inferred: after any
        # tick, `.current` is what `level_for_xp` says the stored total buys.
        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(3)):
            for _ in range(40):
                self.char1.improve_skill_on_use("craft")

        total = self.char1.skill_xp.get("craft")
        self.assertEqual(int(self.craft.current), level_for_xp(total))


@override_settings(**SHIPPED)
class TestDeterministicPacing(EvenniaTest):
    """
    Decomposition section 5, test (d): with the roll pinned to Legend's floor, a
    skill reaches level N after exactly `xp_threshold(N)` ticks.

    The only test in this file that measures the *system* rather than a single
    tick, and the only one that would notice the curve being bypassed while every
    individual tick still looked plausible. It is also the assertion that makes
    the 77x pacing claim in the decomposition checkable rather than a memory: at
    the floor, level 1 costs 6 ticks and level 2 costs 12.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.craft = self.char1.skills.get("craft")
        self.craft.current = 0

    def _tick(self, times):
        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(1)):
            for _ in range(times):
                self.char1.improve_skill_on_use("craft")

    def test_one_tick_short_of_the_threshold_is_still_the_old_level(self):
        self._tick(xp_threshold(1) - 1)
        self.assertEqual(int(self.craft.current), 0)

    def test_exactly_the_threshold_reaches_the_level(self):
        self._tick(xp_threshold(1))
        self.assertEqual(int(self.craft.current), 1)

    def test_the_second_point_costs_more_than_the_first(self):
        self._tick(xp_threshold(2))
        self.assertEqual(int(self.craft.current), 2)
        # The whole point of an exponential curve, stated as an assertion so a
        # linear "curve" cannot pass this class by coincidence.
        #
        # ⚠️ NOT compared against the ADJACENT point, and this is not fussiness.
        # `xp_threshold` floors, and at (6, 20) the raw cost of point 2 is 6.21
        # XP, so points 1, 2 and 3 all floor to a cost of exactly 6. An assertion
        # that each point costs strictly more than the one before it is FALSE at
        # the shipped calibration -- it was written that way first and this test
        # is what caught it. The curve is exponential in the limit, not
        # monotonically strict at integer resolution near the origin.
        self.assertGreater(
            xp_threshold(21) - xp_threshold(20), xp_threshold(1) - xp_threshold(0)
        )


@override_settings(**SHIPPED)
class TestCapShortCircuit(EvenniaTest):
    """
    F2: the `old >= cap` early return is load-bearing, not an optimisation.

    Once `min(cap, ...)` exists a few lines below it, the short-circuit looks
    redundant and invites deletion. It is not. Without it a mastered skill keeps
    banking XP while `.current` sits at 100, the invariant
    `.current == level_for_xp(total)` breaks silently, and D.2's cap lift then
    teleports the character several points at once out of XP nobody watched
    accumulate. With it, the total freezes inside [threshold(100),
    threshold(101)) and the invariant survives until D.2 removes the ceiling
    honestly.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.craft = self.char1.skills.get("craft")
        self.craft.current = 100

    def test_a_capped_skill_does_not_roll(self):
        with mock.patch("typeclasses.characters.improvement_roll") as rolled:
            result = self.char1.improve_skill_on_use("craft")

        rolled.assert_not_called()
        self.assertFalse(result["rolled"])
        self.assertEqual(result["delta"], 0)

    def test_a_capped_skill_banks_no_xp(self):
        before = self.char1.skill_xp.get("craft")

        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(5, beat=True)):
            self.char1.improve_skill_on_use("craft")

        self.assertEqual(self.char1.skill_xp.get("craft"), before)
        # Nothing was written at all -- the Attribute is not even created.
        self.assertFalse(self.char1.attributes.has("skill_xp"))

    def test_the_capped_result_still_carries_the_new_keys(self):
        # `_improvement_feedback` and, shortly, D.1's bar read this dict without
        # checking which branch produced it. A KeyError inside a craft is not an
        # acceptable way to learn that the cap branch returns a different shape.
        result = self.char1.improve_skill_on_use("craft")

        for key in ("xp_gained", "xp_total", "progress"):
            self.assertIn(key, result)
        self.assertEqual(result["xp_gained"], 0)
        self.assertEqual(len(result["progress"]), 3)


@override_settings(**SHIPPED)
class TestFloorRepair(EvenniaTest):
    """
    F7: `.current` standing above what the stored total implies must not
    de-level the character on the next tick.

    B.2 closed this hole for a skill that has *never* banked, by deriving the
    floor on read. The hole left open is a skill that HAS banked and then had
    `.current` raised from outside -- an admin `@py`, a restored backup, a legacy
    write. Without the repair, the next successful craft reads the stale total
    back through `level_for_xp` and writes the character down to it.

    This is not a theoretical branch: the in-game protocol for this very task
    tells you to set `.current` by hand, because crafting your way to level 60
    honestly takes hours. The first person to test C.1 would have hit it.

    Deviation from decomposition section 5, which does not specify this. Recorded
    with its motivation rather than smuggled in.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.craft = self.char1.skills.get("craft")
        self.craft.current = 20

    def test_a_hand_raised_level_is_not_de_levelled(self):
        # Bank honestly at 20 (creating a real stored entry), then jump the level
        # by hand the way an admin or a restored backup would.
        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(3)):
            self.char1.improve_skill_on_use("craft")
        self.craft.current = 60

        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(1)):
            result = self.char1.improve_skill_on_use("craft")

        self.assertEqual(result["new"], 60)
        self.assertGreaterEqual(result["delta"], 0)
        self.assertEqual(int(self.craft.current), 60)

    def test_the_repair_restores_the_invariant_rather_than_hiding_the_gap(self):
        # A guard of the form `new = max(old, ...)` would also keep the level,
        # but would leave the total permanently inconsistent with it and the
        # progress bar permanently meaningless. The repair tops the total up
        # instead, so P-1's direction is restored rather than suspended.
        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(3)):
            self.char1.improve_skill_on_use("craft")
        self.craft.current = 60

        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(1)):
            self.char1.improve_skill_on_use("craft")

        total = self.char1.skill_xp.get("craft")
        self.assertGreaterEqual(total, xp_threshold(60))
        self.assertEqual(int(self.craft.current), level_for_xp(total))

    def test_the_repair_is_a_no_op_on_a_consistent_total(self):
        # The normal life of every character: the branch must cost a comparison
        # and change nothing. Asserted as "the total moved by exactly the grain",
        # which is false if the repair fires spuriously.
        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(2)):
            self.char1.improve_skill_on_use("craft")
            before = self.char1.skill_xp.get("craft")
            self.char1.improve_skill_on_use("craft")

        self.assertEqual(self.char1.skill_xp.get("craft"), before + 2)


@override_settings(**SHIPPED)
class TestScribeTrains(EvenniaCommandTest):
    """
    P-6, sixth call-site: `scribe` is a real Craft roll and must teach.

    Deliberately an end-to-end test rather than a spy on
    `attempt_skill_improvement`. A spy would prove that a line exists in
    `CmdScribe.func`; it would not prove that the line is reachable, that it sits
    after the guards that can return early, or that the outcome dict it passes
    carries the "success" key the gate reads. Those are the ways a sixth
    call-site actually gets added wrong.

    `skill_check` is patched to a deterministic success because scribe's own roll
    at Craft 50 fails half the time, and a test that passes half the time is
    worse than no test. What is NOT patched is the improvement roll: this test
    asserts that XP moved, not by how much, so the real grain is free to vary.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        # SCRIBE_MIN_CRAFT is 50; clear it with room to spare, and stay far
        # enough below 100 that the cap short-circuit is not what we are testing.
        self.char1.skills.get("craft").current = 60
        self.char1.learn_recipe(CLOTH)
        for proto in ("cloth", "cloth", "twine"):
            spawn(proto)[0].move_to(self.char1, quiet=True)

    def test_scribing_a_book_banks_craft_xp(self):
        before = self.char1.skill_xp.get("craft")

        with mock.patch(
            "commands.crafting_commands.skill_check",
            return_value={"success": True, "result": "success", "crit_score": 0},
        ):
            self.call(CmdScribe(), CLOTH, caller=self.char1)

        # The command really ran ...
        self.assertTrue([o for o in self.char1.contents if o.db.recipes])
        # ... and the sixth call-site banked.
        self.assertGreater(self.char1.skill_xp.get("craft"), before)

    def test_scribing_does_not_move_the_percentage(self):
        # The player-visible half of C.1, tested where a player would see it: one
        # tick at level 60 buys a fraction of a point, so the number does not
        # move. This is exactly the silence the ordering hazard warns about, and
        # it is why C.2 and D.1 exist.
        with mock.patch(
            "commands.crafting_commands.skill_check",
            return_value={"success": True, "result": "success", "crit_score": 0},
        ):
            self.call(CmdScribe(), CLOTH, caller=self.char1)

        self.assertEqual(int(self.char1.skills.get("craft").current), 60)

    def test_a_failed_binding_teaches_nothing(self):
        # Gate 1 (success-only) still holds at the new call-site: a fumbled
        # binding still produces its low-condition book and banks no XP.
        before = self.char1.skill_xp.get("craft")

        with mock.patch(
            "commands.crafting_commands.skill_check",
            return_value={"success": False, "result": "failure", "crit_score": 0},
        ):
            self.call(CmdScribe(), CLOTH, caller=self.char1)

        self.assertEqual(self.char1.skill_xp.get("craft"), before)


@override_settings(**SHIPPED)
class TestFeedbackCopy(EvenniaTest):
    """
    Components C.2 and D.1: `_improvement_feedback` must report each of the three
    outcomes with exactly one signal, and lie about none of them.

    Before C.1, `rolled=True` implied `delta >= 1` -- Legend's floor guaranteed
    it -- so one gate served for both "a tick happened" and "something visible
    happened". C.1 pulled those apart, and the old copy would render the newly
    common case as "(+0, now 40%)": a message whose entire content is that
    nothing changed. C.2 replaced that with a wordless practice line, explicitly
    marked as a placeholder; **D.1 replaced the placeholder with the bar it was
    standing in for**, so the tests below now describe the bar.

    ⚠️ The three assertions C.2 wrote survive D.1 untouched, and that is not a
    coincidence -- they were written against the *constraints* on the middle
    branch (no "+0", no figure, no claim of improvement) rather than against the
    string C.2 happened to ship. A test written as `assertEqual(text, "You feel
    your grasp of Crafting steady a little.")` would have had to be deleted here,
    and deleting a test to make a change pass is how a suite stops meaning
    anything.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.craft = self.char1.skills.get("craft")
        self.craft.current = 40

    def _feedback(self, gained):
        with mock.patch("typeclasses.characters.improvement_roll", fixed_roll(gained)):
            return self.char1._improvement_feedback(
                self.char1.improve_skill_on_use("craft")
            )

    def test_a_tick_that_banks_without_levelling_never_says_plus_zero(self):
        # The single assertion C.2 existed for. Still the cheapest thing to break.
        self.assertNotIn("+0", self._feedback(1))

    def test_the_banking_tick_carries_no_number_at_all(self):
        # P-8: no second progression stat is shown to the player. Asserted as
        # "no digit appears", which is stricter than checking for "%" and catches
        # a well-meaning future edit that adds an XP count "just for testing" --
        # including one added inside the bar, which is exactly what Evennia's
        # health_bar contrib does by default and why it was not used.
        text = self._feedback(1)
        self.assertTrue(text)
        self.assertFalse(any(char.isdigit() for char in text))

    def test_the_banking_tick_does_not_claim_the_skill_improved(self):
        # The word "improves" is reserved for a tick where the percentage moved.
        # Lending it to a tick where nothing visible happened teaches a meaning
        # the bar would then have to take back.
        self.assertNotIn("improves", self._feedback(1))

    def test_the_banking_tick_draws_the_bar(self):
        # D.1's own assertion: the middle branch renders progress, and it
        # renders it *labelled*, so a player who has two skills in flight can
        # tell which one moved. A bar with no label is one line of art with no
        # referent.
        text = self._feedback(1)
        self.assertIn(_BAR_EMPTY, text)
        self.assertIn(self.craft.name, text)

    def test_a_levelling_tick_still_reads_exactly_as_it_did_before(self):
        # The half of the copy neither C.2 nor D.1 may disturb. One XP short of
        # level 41, then a single point.
        self.char1.skill_xp.add("craft", xp_threshold(41) - 1 - xp_threshold(40))

        text = self._feedback(1)

        self.assertIn("improves!", text)
        self.assertIn("+1", text)
        self.assertIn("41%", text)

    def test_a_levelling_tick_draws_no_bar(self):
        """
        Locked decision D-2, pinned: one felt-progress signal per tick.

        A level-up resets the numerator, so the bar drawn here would be the *new*
        point's -- near-empty, printed directly under "improves!". Two signals
        for one tick is not a richer interface; it is two systems that then have
        to be calibrated against each other, and one of them reading as a
        demotion in the same breath as the praise.
        """
        self.char1.skill_xp.add("craft", xp_threshold(41) - 1 - xp_threshold(40))

        text = self._feedback(1)

        self.assertNotIn(_BAR_EMPTY, text)
        self.assertNotIn(_BAR_FULL, text)

    def test_a_tier_crossing_celebrates_exactly_once(self):
        # Craft's desc bands put a boundary at 40 -> the tier changes on the tick
        # that reaches 41. Crossings are strictly rarer after C.1, so this line
        # is now the rarest thing the method can say -- and it must still fire.
        self.char1.skill_xp.add("craft", xp_threshold(41) - 1 - xp_threshold(40))

        text = self._feedback(1)

        self.assertEqual(text.count("reaches a new tier"), 1)

    def test_a_gated_out_attempt_says_nothing(self):
        self.assertEqual(self.char1._improvement_feedback(None), "")

    def test_a_capped_skill_says_nothing(self):
        # rolled=False, and after C.1 it also banks nothing. Silence is correct:
        # there is no progress to report, felt or otherwise. Note that the capped
        # branch *does* carry a "progress" tuple, so this is a real gate and not
        # an accident of missing data.
        self.craft.current = 100
        self.assertEqual(
            self.char1._improvement_feedback(self.char1.improve_skill_on_use("craft")),
            "",
        )


class TestImprovableSkillsSet(EvenniaTest):
    """
    D.1: hold `Character.improvable_skills` against the call-sites it claims to
    describe.

    The set is display-only -- it decides whether `progress` draws a bar or says
    "(not yet trainable)" -- so drift costs a wrong caption rather than wrong
    behaviour. It is still worth a net, because a wrong caption is *silent*: a
    seventh call-site added without touching this set would leave a skill that
    genuinely trains permanently labelled untrainable, and nothing would fail.

    Read by AST rather than by grepping the source text. A text grep matches the
    forbidden call inside a docstring that merely *quotes* it -- and
    `typeclasses/characters.py` has three docstrings that do exactly that -- so
    a grep-based version of this test would have to be written around its own
    false positives. The AST sees calls only.

    The honest gap, stated rather than hidden: `CmdHarvest` passes
    `part["skill"]`, a dict lookup the AST cannot resolve. That call-site is
    covered by the second test instead, which reads the harvest table as data.
    """

    character_typeclass = CHARACTER

    #: The modules holding the six call-sites (P-6).
    CALL_SITE_MODULES = (
        "world/crafting_base.py",
        "commands/crafting_commands.py",
        "commands/repair_commands.py",
        "commands/hunting_commands.py",
    )

    def _literal_skill_keys(self, path):
        """Every literal first argument to attempt_skill_improvement in `path`."""
        import ast

        with open(path, encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)

        keys = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name != "attempt_skill_improvement":
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                keys.add(first.value)
        return keys

    def test_every_literal_call_site_key_is_declared_improvable(self):
        found = set()
        for path in self.CALL_SITE_MODULES:
            found |= self._literal_skill_keys(path)

        # Guard against the test silently passing because the AST walk broke and
        # found nothing at all -- an absence and a clean bill of health look
        # identical otherwise (Testing Reference Rev 5 section 11).
        self.assertTrue(found, "no literal call-sites found -- the walk is broken")
        self.assertLessEqual(found, set(self.char1.improvable_skills))

    def test_every_harvestable_part_trains_a_declared_improvable_skill(self):
        # CmdHarvest's key is data, not a literal, so it is checked as data.
        from world.harvest_templates import HARVEST_TEMPLATES

        # A template maps part-name -> part-dict directly; there is no "parts"
        # wrapper. The first version of this test assumed one, found nothing, and
        # was caught by the emptiness receipt below rather than passing green on
        # an empty set -- which is the whole reason the receipt is there.
        found = {
            part["skill"]
            for template in HARVEST_TEMPLATES.values()
            for part in template.values()
            if isinstance(part, Mapping) and "skill" in part
        }
        self.assertTrue(found, "no harvest skills found -- the table shape changed")
        self.assertLessEqual(found, set(self.char1.improvable_skills))

    def test_every_declared_skill_actually_exists_on_a_character(self):
        # Drift in the other direction: a renamed skill would leave a dead key
        # here, and the row it was meant to caption would fall through to the
        # bar branch and read as trainable-but-stuck.
        self.assertLessEqual(
            set(self.char1.improvable_skills), set(self.char1.skills.all())
        )
