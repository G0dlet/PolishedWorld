"""
Tests for natural healing on the survival tick (survival loop S2.1).

Locks: A1 (`healing.accrue` writes health and pushes `char`), B1 (the table is
keyed on Resilience, CON x 2 standing in -- RP-L4), C1 (`at_post_puppet`
clears the tick's stamp), D1 (one line per tick in which a point lands).

Mutations each class is meant to kill are named in its docstring (SL-M13..M17,
SL-M42, SL-M43).
"""

from unittest import mock

from django.test import SimpleTestCase
from evennia.utils.test_resources import EvenniaTest

from world import client_state, healing, survival_ticker
from world.survival_buffs import Dehydrated, Starving

H = healing.HOUR


class TestTable(SimpleTestCase):
    """
    Pressures an off-by-one at a row's edge: Legend's rows are inclusive at
    their top (01-10, 11-30, ...), so 10 is the slow row and 11 the next.
    """

    def test_each_row_at_both_edges(self):
        cases = {
            0: 72, 1: 72, 10: 72,
            11: 48, 30: 48,
            31: 36, 50: 36,
            51: 24, 70: 24,
            71: 18, 90: 18,
            91: 12, 200: 12,
        }
        for value, hours in cases.items():
            with self.subTest(resilience=value):
                self.assertEqual(healing.interval_for(value), hours * H)


class HealingTestBase(EvenniaTest):
    """CON 10 -> Resilience 20 -> 48 game hours a point; health 20, wounded 3."""

    def setUp(self):
        super().setUp()
        self.char1.stats.con.base = 10
        self.char1.update_health_max()
        self.health = self.char1.traits.health
        self.health.current = self.health.max - 3
        self.char1.db.heal_progress = 0
        self.interval = healing.interval_for(healing.resilience(self.char1))


class TestResilience(HealingTestBase):
    """
    Pressures B1: the row is chosen from CON x 2, so CON 5 and 6 straddle the
    first edge and CON 15 and 16 the second (decomp S2.1's edges).
    """

    def test_con_edges_pick_their_rows(self):
        for con, hours in ((5, 72), (6, 48), (15, 48), (16, 36)):
            with self.subTest(con=con):
                self.char1.stats.con.base = con
                self.assertEqual(healing.interval_for(healing.resilience(self.char1)), hours * H)

    def test_fixture_interval(self):
        self.assertEqual(healing.resilience(self.char1), 20)
        self.assertEqual(self.interval, 48 * H)


class TestAccrue(HealingTestBase):
    """
    Pressures the counter: SL-M14 (remainder dropped on a grant), SL-M15
    (counter not zeroed at full health), SL-M17 (more points claimed than fit
    below max -- the trait's setter clamps `current`, so only the return value
    can show it).
    """

    def test_one_second_short_then_the_next_second(self):
        start = self.health.current
        self.assertEqual(healing.accrue(self.char1, self.interval - 1), 0)
        self.assertEqual(self.health.current, start)
        self.assertEqual(self.char1.db.heal_progress, self.interval - 1)
        self.assertEqual(healing.accrue(self.char1, 1), 1)
        self.assertEqual(self.health.current, start + 1)
        self.assertEqual(self.char1.db.heal_progress, 0)

    def test_the_remainder_is_carried(self):
        self.assertEqual(healing.accrue(self.char1, self.interval + 500), 1)
        self.assertEqual(self.char1.db.heal_progress, 500)

    def test_two_intervals_grant_two(self):
        start = self.health.current
        self.assertEqual(healing.accrue(self.char1, 2 * self.interval), 2)
        self.assertEqual(self.health.current, start + 2)

    def test_stops_at_max_and_says_so(self):
        self.health.current = self.health.max - 1
        self.assertEqual(healing.accrue(self.char1, 3 * self.interval + 7), 1)
        self.assertEqual(self.health.current, self.health.max)
        self.assertEqual(self.char1.db.heal_progress, 0)

    def test_full_health_zeroes_the_counter(self):
        self.health.current = self.health.max
        self.char1.db.heal_progress = self.interval - 1
        self.assertEqual(healing.accrue(self.char1, 10), 0)
        self.assertEqual(self.char1.db.heal_progress, 0)
        # Receipt that the zero matters: a new wound does not heal at once.
        self.health.current = self.health.max - 1
        self.assertEqual(healing.accrue(self.char1, 1), 0)

    def test_float_health_base_still_gains_whole_points(self):
        # BACKLOG *Dev characters keep a float `health.base`*.
        self.health.base = 20.0
        self.health.current = 18.0
        self.assertEqual(healing.accrue(self.char1, self.interval), 1)
        self.assertEqual(self.health.current, 19)
        self.assertTrue(float(self.health.current).is_integer())

    def test_pushes_char_only_when_a_point_lands(self):
        with mock.patch.object(client_state, "push") as push:
            healing.accrue(self.char1, 1)
        push.assert_not_called()
        with mock.patch.object(client_state, "push") as push:
            healing.accrue(self.char1, self.interval)
        push.assert_called_once_with(self.char1, "char")

    def test_no_health_trait_is_nothing(self):
        self.char1.traits.remove("health")
        self.assertEqual(healing.accrue(self.char1, self.interval), 0)


class TestConditionsBlock(HealingTestBase):
    """
    Pressures Legend p. 90: SL-M13 (Dehydrated ignored) and a Starving check
    that also wipes the progress already made.
    """

    def _blocked_by(self, buffclass):
        self.char1.buffs.add(buffclass)
        self.char1.db.heal_progress = self.interval - 1
        start = self.health.current
        self.assertEqual(healing.accrue(self.char1, 10 * self.interval), 0)
        self.assertEqual(self.health.current, start)
        self.assertEqual(self.char1.db.heal_progress, self.interval - 1)

    def test_starving_accrues_nothing_and_keeps_the_counter(self):
        self._blocked_by(Starving)

    def test_dehydrated_accrues_nothing_and_keeps_the_counter(self):
        self._blocked_by(Dehydrated)


class TestTickClock(EvenniaTest):
    """
    Pressures `_tick_game_seconds`: SL-M16 (a missing stamp read as 0, so
    the first tick credits the whole game epoch) and SL-M42 (the stamp kept
    across a puppet -- Evennia keeps ndb on a cached object through an
    unpuppet, so the first tick after login would credit the time away).
    """

    CLOCK = "world.survival_ticker.gametime_utils.get_absolute_gametime"

    def test_first_call_is_zero_then_the_difference(self):
        self.char1.ndb.survival_tick_at = None
        with mock.patch(self.CLOCK, side_effect=[100_000, 102_400]):
            self.assertEqual(survival_ticker._tick_game_seconds(self.char1), 0)
            self.assertEqual(survival_ticker._tick_game_seconds(self.char1), 2400)
        self.assertEqual(self.char1.ndb.survival_tick_at, 102_400)

    def test_a_clock_behind_the_stamp_is_zero(self):
        self.char1.ndb.survival_tick_at = 5000
        with mock.patch(self.CLOCK, return_value=4000):
            self.assertEqual(survival_ticker._tick_game_seconds(self.char1), 0)
        self.assertEqual(self.char1.ndb.survival_tick_at, 4000)

    def test_puppet_clears_the_stamp(self):
        self.char1.ndb.survival_tick_at = 12345
        self.char1.at_post_puppet()
        self.assertIsNone(self.char1.ndb.survival_tick_at)


class TestTickHeals(HealingTestBase):
    """
    Pressures the wiring in `_deplete_character`: the tick's span reaches
    `accrue`, one line is said when a point lands (D1), and SL-M43 (healing
    run before the conditions, so the tick that makes a character Dehydrated
    still heals them).
    """

    CLOCK = "world.survival_ticker.gametime_utils.get_absolute_gametime"

    def _tick(self):
        self.char1.ndb.survival_tick_at = 100_000
        with mock.patch(self.CLOCK, return_value=102_400), \
                mock.patch.object(self.char1, "msg") as msg:
            survival_ticker._deplete_character(self.char1)
        return [c.args[0] for c in msg.call_args_list if c.args]

    def test_a_tick_lands_a_point_and_says_one_line(self):
        self.char1.db.heal_progress = self.interval - 2400
        start = self.health.current
        lines = self._tick()
        self.assertEqual(self.health.current, start + 1)
        self.assertEqual(lines.count(healing.HEALED), 1)

    def test_a_tick_short_of_a_point_says_nothing(self):
        self.char1.db.heal_progress = self.interval - 2401
        start = self.health.current
        lines = self._tick()
        self.assertEqual(self.health.current, start)
        self.assertEqual(self.char1.db.heal_progress, self.interval - 1)
        self.assertNotIn(healing.HEALED, lines)

    def test_the_tick_that_dehydrates_does_not_heal(self):
        thirst = self.char1.traits.thirst
        thirst.current = thirst.min
        self.char1.db.heal_progress = self.interval - 2400
        start = self.health.current
        lines = self._tick()
        self.assertTrue(self.char1.buffs.has(Dehydrated))  # receipt: the condition landed
        self.assertEqual(self.health.current, start - survival_ticker.STARVE_DAMAGE)
        self.assertEqual(self.char1.db.heal_progress, self.interval - 2400)
        self.assertNotIn(healing.HEALED, lines)


class TestTimeAway(HealingTestBase):
    """
    Pressures S2.2 (SL7): the stamp at the last unpuppet and the credit at the
    next puppet. Mutations: SL-M18 (stamp before the multisession bail),
    SL-M19 (stamp kept after crediting -- the next login credits it again),
    SL-M20 (stamp while Starving), SL-M44 (credit after the panel push, so
    the first snapshot shows the old health).
    """

    CLOCK = "world.gametime_utils.get_absolute_gametime"
    T = 1_000_000

    def _leave(self, at):
        with mock.patch(self.CLOCK, return_value=at):
            self.account.unpuppet_object(self.session)

    def _return(self, at):
        with mock.patch(self.CLOCK, return_value=at), \
                mock.patch.object(self.char1, "msg") as msg:
            self.char1.at_post_puppet()
        return [c.args[0] for c in msg.call_args_list if c.args]

    def test_two_intervals_away_grant_two_and_one_line(self):
        start = self.health.current
        self._leave(self.T)
        self.assertEqual(self.char1.db.away_since, self.T)
        lines = self._return(self.T + 2 * self.interval)
        self.assertEqual(self.health.current, start + 2)
        self.assertEqual(lines.count(healing.HEALED), 1)
        self.assertIsNone(self.char1.db.away_since)

    def test_the_credit_is_spent_once(self):
        self._leave(self.T)
        self._return(self.T + self.interval)
        start = self.health.current
        # A second puppet with no logout between (a reload, a second
        # session): nothing left to credit.
        lines = self._return(self.T + 3 * self.interval)
        self.assertEqual(self.health.current, start)
        self.assertNotIn(healing.HEALED, lines)

    def test_logged_out_under_a_condition_stamps_nothing(self):
        for buffclass in (Starving, Dehydrated):
            with self.subTest(condition=buffclass.key):
                self.char1.db.away_since = 123
                self.char1.buffs.add(buffclass)
                self._leave(self.T)
                self.assertIsNone(self.char1.db.away_since)
                self.char1.buffs.remove(buffclass.key)
                start = self.health.current
                self._return(self.T + 2 * self.interval)
                self.assertEqual(self.health.current, start)
                self.account.puppet_object(self.session, self.char1)

    def test_a_session_leaving_while_another_remains_stamps_nothing(self):
        self.char1.db.away_since = None
        self.assertEqual(self.char1.sessions.count(), 1)
        sessions = self.char1.sessions
        with mock.patch.object(sessions, "count", wraps=sessions.count) as count, \
                mock.patch(self.CLOCK, return_value=self.T):
            self.char1.at_post_unpuppet(self.account, session=self.session)
        self.assertTrue(count.called)  # receipt: the hook ran and read the sessions
        self.assertIsNone(self.char1.db.away_since)

    def test_no_stamp_credits_nothing(self):
        self.char1.db.away_since = None
        start = self.health.current
        lines = self._return(self.T)
        self.assertEqual(self.health.current, start)
        self.assertNotIn(healing.HEALED, lines)

    def test_the_tick_after_login_does_not_credit_the_span_again(self):
        self._leave(self.T)
        back = self.T + self.interval + 500
        self._return(back)
        progress, health = self.char1.db.heal_progress, self.health.current
        self.assertEqual(progress, 500)
        with mock.patch(self.CLOCK, return_value=back + 10):
            survival_ticker._deplete_character(self.char1)
        self.assertEqual(self.char1.db.heal_progress, progress)
        self.assertEqual(self.health.current, health)

    def test_the_credit_lands_before_the_panel_push(self):
        self.char1.db.away_since = self.T
        order = []
        with mock.patch(self.CLOCK, return_value=self.T + self.interval), \
                mock.patch.object(healing, "accrue",
                                  side_effect=lambda c, s: order.append("accrue") or 0), \
                mock.patch.object(client_state, "push",
                                  side_effect=lambda obj, *d, **k: order.append(d)):
            self.char1.at_post_puppet()
        self.assertIn(tuple(client_state.DOMAINS), order)
        self.assertLess(order.index("accrue"), order.index(tuple(client_state.DOMAINS)))

    def test_a_statue_without_a_room_is_stamped(self):
        self.char1.location = None
        self._leave(self.T)
        self.assertEqual(self.char1.db.away_since, self.T)
