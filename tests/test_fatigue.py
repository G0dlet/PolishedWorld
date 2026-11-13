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
    TestPhysicalModifier     the level's penalty missing from the roll term,
                             replacing overload instead of adding (SL-M24),
                             or added with the wrong sign (SL-M25) -- S3.2
    TestPenaltyReachesCraft  the term computed but not reaching a real roll
    TestAwakeClockRules      the day's length and the hours due: CON read
                             wrong, an hour counted early or twice,
                             `fatigue_rate` ignored (SL-M29) -- S3.3
    TestAwakeTick            the tick still draining (SL-M26), rolling every
                             tick past the threshold (SL-M27), the modifier
                             read once for two rolls (SL-M48), training
                             Athletics (SL-M30), the need penalty missing or
                             read a tick late (lock D1), a line at 0
    TestRestResetsClock      the reset on any rest tick (SL-M28) or none
    TestCollapseRoll         the roll at 0 only, without its -20 (SL-M34),
                             or while resting (SL-M51); the fall interrupts
                             the slot and tells the room -- S3.4
    TestCollapsedRefusals    the refusal after the interrupt (SL-M31), the
                             exit's second line (lock B1), a teleport
                             refused, food or water spent, a wiped slot left
                             unarmed by a refusal (lock H1)
    TestCollapseRecovery     the wake at 1 (SL-M32), the flag only in ndb
                             (SL-M33), no re-arm at puppet (SL-M50), death
                             keeping the flag (SL-M35)

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
from evennia.contrib.game_systems.crafting import craft
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from evennia.utils.create import create_object

from commands.character_commands import CmdSheet, CmdStatus
from commands.consumption_commands import CmdDrink, CmdEat, CmdEmpty, CmdRest
from tests.test_encumbrance import LIMIT, _make, _PenaltyFixture
from typeclasses.characters import _collapse_tick, _rest_tick
from world import client_state, fatigue, survival_ticker, timed_actions
from world.encumbrance import carried_enc
from world.survival_buffs import ColdStress, Dehydrated, Starving
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


# --- S3.2: the penalty on physical tests -------------------------------------


class TestPhysicalModifier(EvenniaTest):
    """`physical_modifier()`: overload's term plus minus the level's penalty."""

    def at(self, value, overloaded=False):
        self.char1.traits.fatigue.current = value
        if overloaded:
            _make(self.char1, key="load", enc=LIMIT + 1)
            self.assertGreater(carried_enc(self.char1), LIMIT)   # receipt
        return self.char1.physical_modifier()

    def test_fresh_is_zero(self):
        self.assertEqual(self.at(100), 0)
        self.assertEqual(self.at(81), 0)

    def test_winded_at_its_top_is_minus_ten(self):
        self.assertEqual(self.at(80), -10)

    def test_wearied_at_forty_is_minus_thirty(self):
        self.assertEqual(self.at(40), -30)

    def test_debilitated_is_minus_fifty(self):
        self.assertEqual(self.at(0), -50)

    def test_overloaded_and_debilitated_sum_to_minus_seventy(self):
        # Rest NP2: the two penalties add.
        self.assertEqual(self.at(0, overloaded=True), -70)

    def test_overloaded_and_fresh_is_overload_alone(self):
        self.assertEqual(self.at(100, overloaded=True), -20)

    def test_no_fatigue_gauge_leaves_overload_alone(self):
        self.char1.traits.remove("fatigue")
        _make(self.char1, key="load", enc=LIMIT + 1)
        self.assertEqual(self.char1.physical_modifier(), -20)


class TestPenaltyReachesCraft(_PenaltyFixture, EvenniaCommandTest):
    """A real craft at fatigue 40 rolls with -30 (the spy reads the roll's modifier)."""

    def test_craft_at_forty(self):
        clay = spawn("clay")[0]
        clay.move_to(self.char1, quiet=True)
        self.load_to(LIMIT)   # at the limit: no overload term
        self.char1.traits.fatigue.current = 40
        modifier = self.rolled(
            "world.crafting_base.skill_check",
            lambda: craft(self.char1, "sling bullet", clay),
        )
        self.assertEqual(modifier, -30)


# --- S3.3: the awake clock ---------------------------------------------------

H = 3600
DAY = (10 + 10) * H   # the threshold at CON 10, written out by hand
CLOCK = "world.survival_ticker.gametime_utils.get_absolute_gametime"
ROLL = "world.skillcheck.randint"
PASS, FAIL = 5, 97    # 02-05 always succeed, 96-98 always fail (Athletics 25)


class _AwakeFixture:
    """char1 at CON 10 (a 20-hour day), Fresh, its clock at zero."""

    def setUp(self):
        super().setUp()
        self.char1.stats.con.base = 10
        self.fatigue = self.char1.traits.fatigue
        self.fatigue.current = 100
        fatigue.reset_clock(self.char1)


class TestAwakeClockRules(_AwakeFixture, EvenniaTest):
    """The clock's arithmetic, without the tick."""

    def due_at(self, seconds, rolled=0):
        self.char1.db.awake_seconds = seconds
        self.char1.db.awake_tests = rolled
        return fatigue.tests_due(self.char1)

    def test_the_day_is_ten_plus_con_hours(self):
        self.assertEqual(fatigue.threshold(self.char1), DAY)
        self.char1.stats.con.base = 14
        self.assertEqual(fatigue.threshold(self.char1), 24 * H)

    def test_whole_hours_past_the_threshold(self):
        self.assertEqual(self.due_at(DAY - 1), 0)
        self.assertEqual(self.due_at(DAY + H - 1), 0)
        self.assertEqual(self.due_at(DAY + H), 1)
        self.assertEqual(self.due_at(DAY + 2 * H), 2)

    def test_rolled_hours_are_not_due_again(self):
        self.assertEqual(self.due_at(DAY + 2 * H, rolled=1), 1)
        self.assertEqual(self.due_at(DAY + 2 * H, rolled=2), 0)

    def test_a_character_made_before_s33_starts_at_zero(self):
        # No backfill (A1): the attributes are absent, not zero.
        self.char1.attributes.remove("awake_seconds")
        self.char1.attributes.remove("awake_tests")
        self.assertEqual(fatigue.tests_due(self.char1), 0)
        fatigue.advance_clock(self.char1, 2400)
        self.assertEqual(self.char1.db.awake_seconds, 2400)

    def test_cold_stress_shortens_the_day(self):
        self.char1.buffs.add(ColdStress, stacks=5)   # fatigue_rate x 1.40
        fatigue.advance_clock(self.char1, 2400)
        self.assertAlmostEqual(self.char1.db.awake_seconds, 3360)

    def test_reset_zeroes_clock_and_count(self):
        self.due_at(DAY + 3 * H, rolled=2)
        fatigue.reset_clock(self.char1)
        self.assertEqual((self.char1.db.awake_seconds, self.char1.db.awake_tests), (0, 0))

    def test_need_keys_are_the_conditions_keys(self):
        self.assertEqual(fatigue.NEEDS, (Starving.key, Dehydrated.key))


class _TickDriver:
    """
    The clock on a real tick: 2400 game seconds a tick, the die pinned.

    `apply_thermal_stress` is patched out, so the room's weather cannot add a
    ColdStress stack and stretch the seconds the boundaries are set against.
    The roll is spied on through `world.fatigue.skill_check` (wraps the real
    one), so each test reads how many rolls ran and with which modifier.
    """

    def tick(self, end, roll=PASS):
        """Run one tick that leaves the clock at `end`; return (lines, modifiers)."""
        self.char1.db.awake_seconds = end - 2400
        self.char1.ndb.survival_tick_at = 100_000
        with mock.patch(CLOCK, return_value=102_400), \
                mock.patch("world.survival_ticker.apply_thermal_stress"), \
                mock.patch(ROLL, return_value=roll), \
                mock.patch.object(fatigue, "skill_check", wraps=fatigue.skill_check) as spy, \
                mock.patch.object(self.char1, "msg") as msg:
            survival_ticker._deplete_character(self.char1)
        lines = [c.args[0] for c in msg.call_args_list if c.args]
        return lines, [c.args[1] for c in spy.call_args_list]


class TestAwakeTick(_TickDriver, _AwakeFixture, EvenniaTest):
    """The awake tests on a real tick (see `_TickDriver`)."""

    def test_a_tick_does_not_drain_fatigue(self):
        hunger = self.char1.traits.hunger.current
        _lines, rolls = self.tick(2400)
        self.assertEqual(self.char1.traits.hunger.current, hunger - 1)   # receipt: the tick ran
        self.assertEqual(self.char1.db.awake_seconds, 2400)              # receipt: the clock ran
        self.assertEqual(rolls, [])
        self.assertEqual(self.fatigue.current, 100)

    def test_no_roll_a_second_short_of_the_hour(self):
        _lines, rolls = self.tick(DAY + H - 1)
        self.assertEqual(rolls, [])

    def test_one_roll_an_hour_past_the_threshold(self):
        _lines, rolls = self.tick(DAY + H)
        self.assertEqual(rolls, [0])
        self.assertEqual(self.char1.db.awake_tests, 1)

    def test_two_hours_in_one_tick_roll_twice(self):
        _lines, rolls = self.tick(DAY + 2 * H)
        self.assertEqual(len(rolls), 2)

    def test_a_rolled_hour_is_not_rolled_on_the_next_tick(self):
        self.tick(DAY + H)
        _lines, rolls = self.tick(DAY + H + 2400)
        self.assertEqual(rolls, [])

    def test_a_failure_costs_one_level_and_says_so(self):
        _check_survival_warnings(self.char1)   # the previous tick's baseline (Fresh)
        lines, _rolls = self.tick(DAY + H, roll=FAIL)
        self.assertEqual(self.fatigue.current, 80)
        self.assertEqual(lines.count(fatigue.AWAKE_FAILED), 1)
        self.assertIn("|yYou feel winded.|n", lines)   # the warning follows (G1)

    def test_a_failure_at_ten_clamps_at_zero(self):
        self.fatigue.current = 10
        lines, _rolls = self.tick(DAY + H, roll=FAIL)
        self.assertEqual(self.fatigue.current, 0)
        self.assertIn(fatigue.AWAKE_FAILED, lines)

    def test_a_failure_at_zero_says_nothing(self):
        self.fatigue.current = 0
        lines, rolls = self.tick(DAY + H, roll=FAIL)
        # Receipt: the awake test was rolled (-50, the level's); since S3.4
        # the collapse test follows it at 0 (-70), and its fall is its own line.
        self.assertEqual(rolls, [-50, -70])
        self.assertEqual(self.fatigue.current, 0)
        self.assertNotIn(fatigue.AWAKE_FAILED, lines)

    def test_the_second_roll_reads_the_new_level(self):
        _lines, rolls = self.tick(DAY + 2 * H, roll=FAIL)
        self.assertEqual(rolls, [0, -10])   # Fresh, then Winded
        self.assertEqual(self.fatigue.current, 60)

    def test_a_success_keeps_the_gauge_and_trains_nothing(self):
        self.assertTrue(self.char1.cooldowns.ready("improve_athletics"))
        with mock.patch.object(type(self.char1), "attempt_skill_improvement") as improve:
            _lines, rolls = self.tick(DAY + H, roll=PASS)
        self.assertEqual(len(rolls), 1)   # receipt: the test was rolled
        improve.assert_not_called()
        self.assertTrue(self.char1.cooldowns.ready("improve_athletics"))
        self.assertEqual(self.fatigue.current, 100)

    def test_the_tick_that_starves_adds_minus_twenty(self):
        # Hunger at 0 with no condition yet: this tick applies Starving, and
        # the roll after it already reads it (D1).
        self.char1.traits.hunger.current = 0
        self.assertFalse(self.char1.buffs.has(Starving))
        _lines, rolls = self.tick(DAY + H)
        self.assertTrue(self.char1.buffs.has(Starving))   # receipt
        self.assertEqual(rolls, [-20])

    def test_the_tick_that_dehydrates_adds_minus_twenty(self):
        self.char1.traits.thirst.current = 0
        _lines, rolls = self.tick(DAY + H)
        self.assertTrue(self.char1.buffs.has(Dehydrated))   # receipt
        self.assertEqual(rolls, [-20])


class TestRestResetsClock(_AwakeFixture, EvenniaTest):
    """A rest tick that reaches full starts the day again; one short of it does not."""

    def rest_tick_from(self, value):
        self.fatigue.current = value
        self.char1.db.awake_seconds = DAY + 3 * H
        self.char1.db.awake_tests = 3
        with mock.patch("typeclasses.characters.timed_actions.is_current", return_value=True), \
                mock.patch("typeclasses.characters.timed_actions.claim"), \
                mock.patch("typeclasses.characters.delay"):
            _rest_tick(self.char1, object())

    def test_rest_to_full_zeroes_clock_and_count(self):
        self.rest_tick_from(95)
        self.assertEqual(self.fatigue.current, 100)   # receipt
        self.assertEqual((self.char1.db.awake_seconds, self.char1.db.awake_tests), (0, 0))

    def test_a_rest_stopped_at_95_keeps_the_clock(self):
        self.rest_tick_from(90)
        self.assertEqual(self.fatigue.current, 95)   # receipt: a real rest tick
        self.assertEqual((self.char1.db.awake_seconds, self.char1.db.awake_tests), (DAY + 3 * H, 3))


# --- S3.4: collapse at Debilitated -------------------------------------------

FOOD = "typeclasses.consumables.Food"


def _said(msg_mock):
    """What a patched `msg` received, as plain strings (a room line is a tuple)."""
    return [str(c.args[0]) if c.args else str(c.kwargs.get("text"))
            for c in msg_mock.call_args_list]


class _CollapseFixture(_AwakeFixture):
    """
    char1 Debilitated (fatigue 0); `timed_actions.delay` patched, so a started
    action schedules nothing and each `_collapse_tick` is called by hand.
    """

    def setUp(self):
        super().setUp()
        patcher = mock.patch("world.timed_actions.delay")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.fatigue.current = 0

    def slot(self):
        return timed_actions.is_busy(self.char1)

    def fall(self):
        """char1 collapses; return (char1's lines, char2's lines)."""
        with mock.patch.object(self.char1, "msg") as mine, \
                mock.patch.object(self.char2, "msg") as theirs:
            self.char1.collapse()
        return _said(mine), _said(theirs)


class TestCollapseRoll(_TickDriver, _CollapseFixture, EvenniaTest):
    """The tick's Difficult roll at 0 (SL11)."""

    def test_a_failure_at_zero_collapses(self):
        lines, rolls = self.tick(2400, roll=FAIL)
        self.assertEqual(rolls, [-70])   # the level's -50 and Difficult's -20
        self.assertTrue(self.char1.db.collapsed)
        self.assertEqual(self.slot().key, fatigue.COLLAPSE_KEY)
        self.assertEqual(lines.count(fatigue.FALL), 1)

    def test_a_success_at_zero_stays_up(self):
        _lines, rolls = self.tick(2400, roll=PASS)
        self.assertEqual(rolls, [-70])   # receipt: the roll ran
        self.assertFalse(self.char1.db.collapsed)
        self.assertIsNone(self.slot())

    def test_at_one_no_roll(self):
        self.fatigue.current = 1
        _lines, rolls = self.tick(2400, roll=FAIL)
        self.assertEqual(rolls, [])
        self.assertFalse(self.char1.db.collapsed)

    def test_no_roll_while_resting(self):
        timed_actions.start(self.char1, "rest", 10, _rest_tick, label="resting")
        _lines, rolls = self.tick(2400, roll=FAIL)
        self.assertEqual(rolls, [])
        self.assertFalse(self.char1.db.collapsed)
        self.assertEqual(self.slot().key, "rest")   # receipt: still resting

    def test_the_fall_interrupts_a_chore_and_tells_the_room(self):
        timed_actions.start(self.char1, "work", 60, lambda *a: None, label="working",
                            interrupt_msg="You break off what you were doing.")
        mine, theirs = self.fall()
        self.assertEqual(mine, ["You break off what you were doing.", fatigue.FALL])
        self.assertIn(fatigue.FALL_ROOM.format(name=self.char1.key), "\n".join(theirs))
        self.assertEqual(self.slot().key, fatigue.COLLAPSE_KEY)


class TestCollapsedRefusals(_CollapseFixture, EvenniaCommandTest):
    """What a collapsed body cannot do, and what it still can (SL11, A1, B1, H1)."""

    def setUp(self):
        super().setUp()
        self.fall()
        self.marker = self.slot().marker

    def test_walking_is_refused_once_and_quietly(self):
        with mock.patch.object(self.char1, "msg") as msg:
            self.exit.at_traverse(self.char1, self.room2)
        self.assertEqual(self.char1.location, self.room1)
        self.assertEqual(_said(msg), [fatigue.CANNOT_MOVE])
        self.assertIs(self.slot().marker, self.marker)   # the collapse was not interrupted

    def test_a_teleport_is_not_refused(self):
        self.assertTrue(self.char1.move_to(self.room2, move_type="teleport", quiet=True))
        self.assertEqual(self.char1.location, self.room2)

    def test_a_refusal_rearms_a_wiped_slot(self):
        self.char1.ndb.timed_action = None   # what a reload leaves
        self.exit.at_traverse(self.char1, self.room2)
        self.assertEqual(self.slot().key, fatigue.COLLAPSE_KEY)

    def test_eating_is_refused_and_the_food_kept(self):
        bread = create_object(FOOD, key="collapsebread", location=self.char1)
        self.char1.traits.hunger.current = 50
        self.call(CmdEat(), "collapsebread", fatigue.CANNOT_HANDLE, caller=self.char1)
        self.assertTrue(bread.pk)
        self.assertEqual(self.char1.traits.hunger.current, 50)

    def test_drinking_at_the_source_is_refused(self):
        spring = spawn("spring")[0]
        spring.location = self.room1
        self.char1.traits.thirst.current = 50
        self.call(CmdDrink(), "", fatigue.CANNOT_HANDLE, caller=self.char1)
        self.assertEqual(self.char1.traits.thirst.current, 50)

    def test_emptying_is_refused_and_the_water_kept(self):
        skin = spawn("waterskin")[0]
        skin.location = self.char1
        skin.charges = charges = 3   # a crafted waterskin starts empty
        self.assertFalse(skin.is_empty())   # receipt: there is water to pour out
        self.call(CmdEmpty(), "waterskin", fatigue.CANNOT_HANDLE, caller=self.char1)
        self.assertEqual(skin.charges, charges)

    def test_rest_is_answered_by_the_slot(self):
        self.call(CmdRest(), "", "You are already lying where you fell.", caller=self.char1)
        self.assertIs(self.slot().marker, self.marker)


class TestCollapseRecovery(_TickDriver, _CollapseFixture, EvenniaTest):
    """The forced rest: up at `COLLAPSE_WAKE_AT`, and kept across a reload, a relog and a death."""

    def setUp(self):
        super().setUp()
        self.fall()
        self.marker = self.slot().marker

    def step(self, start):
        """One recovery tick from `start`; return (char1's lines, char2's lines)."""
        self.fatigue.current = start
        with mock.patch.object(self.char1, "msg") as mine, \
                mock.patch.object(self.char2, "msg") as theirs:
            _collapse_tick(self.char1, self.marker)
        return _said(mine), _said(theirs)

    def test_one_step_from_zero_stays_down(self):
        self.step(0)
        self.assertEqual(self.fatigue.current, 5)   # receipt: the rest gain landed
        self.assertTrue(self.char1.db.collapsed)
        self.assertIs(self.slot().marker, self.marker)

    def test_36_stays_down_until_41(self):
        self.step(31)
        self.assertTrue(self.char1.db.collapsed)
        mine, theirs = self.step(36)
        self.assertEqual(self.fatigue.current, 41)
        self.assertFalse(self.char1.db.collapsed)
        self.assertIsNone(self.slot())
        self.assertIn(fatigue.WAKE, mine)
        self.assertIn(fatigue.WAKE_ROOM.format(name=self.char1.key), "\n".join(theirs))

    def test_awake_again_the_body_can_walk(self):
        self.step(36)
        self.exit.at_traverse(self.char1, self.room2)
        self.assertEqual(self.char1.location, self.room2)

    def test_a_reload_keeps_the_flag_and_the_tick_rearms(self):
        self.char1.nattributes.clear()   # a reload empties ndb, the slot with it
        self.assertIsNone(self.slot())
        _lines, rolls = self.tick(2400, roll=PASS)
        self.assertEqual(rolls, [])   # a collapsed body is not rolled for again
        self.assertEqual(self.slot().key, fatigue.COLLAPSE_KEY)

    def test_a_puppet_rearms(self):
        self.char1.ndb.timed_action = None   # the slot a statue logout cleared
        with mock.patch.object(self.char1, "msg"):
            self.char1.at_post_puppet()
        self.assertEqual(self.slot().key, fatigue.COLLAPSE_KEY)

    def test_death_clears_the_flag(self):
        with mock.patch.object(self.char1, "msg"):
            self.char1.at_character_death()
        self.assertFalse(self.char1.db.collapsed)
        self.assertIsNone(self.slot())
