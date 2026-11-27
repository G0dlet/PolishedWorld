"""
Tests for natural healing on the survival tick (survival loop S2.1).

Locks: A1 (`healing.accrue` writes health and pushes `char`), B1 (the table is
keyed on Resilience -- RP-L4; a trait since BD-T4, CON x 2 stood in before),
C1 (`at_post_puppet` clears the tick's stamp), D1 (one line per tick in which
a point lands), HL10 (the book's table read twelve times faster, Healing
HL-T2; a statue heals nothing and nothing names its old stamp, HL-T3).

Only the book's table is typed in hours: it is printed and never moves. The
interval a character heals by is read from `interval_for`, except in the one
test that pins its six values (Testing Reference §27.2).

Mutations each class is meant to kill are named in its docstring (SL-M13..M17,
SL-M42, SL-M43, HLM5, HLM6, HLM8..HLM10).
"""

import ast
import textwrap
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase
from evennia.utils.test_resources import EvenniaTest

from server.conf.at_server_startstop import SURVIVAL_TICK_INTERVAL
from world import client_state, healing, survival_ticker, wounds
from world.survival_buffs import Dehydrated, Starving


ROOT = Path(__file__).resolve().parent.parent
PRODUCTION = ("commands", "server", "typeclasses", "web", "world")
STAMP = "away_since"


def _names_the_stamp(tree):
    """How many times a module names the stamp: as an attribute or a key."""
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == STAMP:
            count += 1
        elif isinstance(node, ast.Constant) and node.value == STAMP:
            count += 1
    return count


def away_since_census():
    """The production files that name the stamp, as paths from the root."""
    found = set()
    for top in PRODUCTION:
        for path in sorted((ROOT / top).rglob("*.py")):
            if _names_the_stamp(ast.parse(path.read_text(encoding="utf-8"))):
                found.add(path.relative_to(ROOT).as_posix())
    return found


def _census_fixture(source):
    return _names_the_stamp(ast.parse(textwrap.dedent(source)))

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
                self.assertEqual(healing.book_interval_for(value), hours * H)


class TestTwelveTimesFaster(SimpleTestCase):
    """
    Pressures HL10: the book's rows divided by `SPEED_FACTOR`, the fastest
    row too. HLM5 (the factor 1) and HLM6 (multiplied in place of divided)
    fail the row test. The two tests after it hold the factor's bounds, so
    nobody changes it without seeing what it does to the table and the tick.
    """

    def test_each_row_in_game_seconds(self):
        # The red: the book's rows as they stood were 72 to 12 game hours.
        cases = {
            0: 21600, 10: 21600,
            11: 14400, 30: 14400,
            31: 10800, 50: 10800,
            51: 7200, 70: 7200,
            71: 5400, 90: 5400,
            91: 3600, 200: 3600,
        }
        for value, seconds in cases.items():
            with self.subTest(resilience=value):
                self.assertEqual(healing.interval_for(value), seconds)

    def test_every_row_divides_into_whole_seconds(self):
        # `//` would round a row down without a word for a factor such as 7.
        for hours in [h for _, h in healing.ROWS] + [healing.FASTEST_HOURS]:
            with self.subTest(hours=hours):
                self.assertEqual(hours * H % healing.SPEED_FACTOR, 0)

    def test_the_fastest_row_is_longer_than_one_survival_tick(self):
        # One tick is 600 real seconds at the game clock's factor, 2400 game
        # seconds at 4: a factor that put a row under it would grant more
        # than a point a tick.
        tick = SURVIVAL_TICK_INTERVAL * settings.TIME_FACTOR
        self.assertGreater(healing.interval_for(10**6), tick)


class HealingTestBase(EvenniaTest):
    """
    CON 10 -> Resilience 20 -> 48 game hours a point in the book, four at the
    keyboard (HL10); three points on every
    location (the fixture's arms, 3, stop there). `hurt()` is the largest
    damage on any location, which a heal lowers by one (WN10).
    """

    def setUp(self):
        super().setUp()
        self.char1.stats.con.base = 10
        self.char1.apply_health_damage(3, location=wounds.ALL)
        self.char1.db.heal_progress = 0
        self.interval = healing.interval_for(healing.resilience(self.char1))

    def hurt(self):
        return wounds.room_to_heal(self.char1)


class TestResilience(HealingTestBase):
    """
    Pressures B1: the row is chosen from Resilience, so 10 and 11 straddle
    the first edge and 30 and 31 the second -- the numbers CON 5, 6, 15 and 16
    gave while CON x 2 stood in (decomp S2.1's edges). The skill is set, not
    CON: a trait does not follow its characteristic (BD-T4).
    """

    def test_resilience_edges_pick_their_rows(self):
        for value, hours in ((10, 72), (11, 48), (30, 48), (31, 36)):
            with self.subTest(resilience=value):
                self.char1.skills.resilience.current = value
                self.assertEqual(
                    healing.book_interval_for(healing.resilience(self.char1)), hours * H)

    def test_con_alone_moves_nothing_once_the_trait_exists(self):
        # The receipt for the rewrite above: with the trait, CON 16 still
        # heals at Resilience 20's row.
        self.char1.stats.con.base = 16
        self.assertEqual(healing.resilience(self.char1), 20)

    def test_fixture_interval(self):
        self.assertEqual(healing.resilience(self.char1), 20)
        self.assertEqual(healing.book_interval_for(20), 48 * H)
        self.assertEqual(self.interval, healing.interval_for(20))


class TestResilienceThroughTheNet(HealingTestBase):
    """
    Pressures BD6: healing reads the Resilience trait when there is one and
    CON x 2 when there is not. BDM7 (the trait ignored) fails the 45 test;
    BDM8 (no trait, no value) fails the no-trait test and stops healing.

    A character has the trait from creation since BD-T4, so the tests of the
    net take it away first -- a character the backfill missed -- and the test
    of the trait sets the one that is there.
    """

    def test_without_the_trait_con_twice(self):
        self.char1.skills.remove("resilience")
        self.assertIsNone(self.char1.skills.get("resilience"))
        self.assertEqual(healing.resilience(self.char1), 20)
        self.assertEqual(healing.accrue(self.char1, self.interval), 1)

    def test_the_trait_chooses_the_row(self):
        self.char1.skills.resilience.current = 45
        self.assertEqual(healing.resilience(self.char1), 45)
        self.assertEqual(healing.book_interval_for(healing.resilience(self.char1)), 36 * H)
        # The 31-50 row's interval heals a point at 45; at 20 it would not.
        self.assertEqual(healing.accrue(self.char1, healing.interval_for(45)), 1)

    def test_neither_trait_nor_con_grants_nothing(self):
        self.char1.skills.remove("resilience")
        self.char1.stats.remove("con")
        self.assertIsNone(healing.resilience(self.char1))
        self.assertEqual(healing.accrue(self.char1, 500 * H), 0)


class TestAccrue(HealingTestBase):
    """
    Pressures the counter: SL-M14 (remainder dropped on a grant), SL-M15
    (counter not zeroed at full health), SL-M17 (more points claimed than fit
    below max -- the trait's setter clamps `current`, so only the return value
    can show it).
    """

    def test_one_second_short_then_the_next_second(self):
        start = self.hurt()
        self.assertEqual(healing.accrue(self.char1, self.interval - 1), 0)
        self.assertEqual(self.hurt(), start)
        self.assertEqual(self.char1.db.heal_progress, self.interval - 1)
        self.assertEqual(healing.accrue(self.char1, 1), 1)
        self.assertEqual(self.hurt(), start - 1)
        self.assertEqual(self.char1.db.heal_progress, 0)

    def test_the_remainder_is_carried(self):
        self.assertEqual(healing.accrue(self.char1, self.interval + 500), 1)
        self.assertEqual(self.char1.db.heal_progress, 500)

    def test_two_intervals_grant_two(self):
        start = self.hurt()
        self.assertEqual(healing.accrue(self.char1, 2 * self.interval), 2)
        self.assertEqual(self.hurt(), start - 2)

    def test_stops_at_max_and_says_so(self):
        wounds.heal(self.char1, 2)   # 3 hurt -> 1
        self.assertEqual(healing.accrue(self.char1, 3 * self.interval + 7), 1)
        self.assertEqual(self.hurt(), 0)
        self.assertEqual(self.char1.db.heal_progress, 0)

    def test_full_health_zeroes_the_counter(self):
        wounds.heal(self.char1, 3)   # 3 hurt -> full
        self.char1.db.heal_progress = self.interval - 1
        self.assertEqual(healing.accrue(self.char1, 10), 0)
        self.assertEqual(self.char1.db.heal_progress, 0)
        # Receipt that the zero matters: a new wound does not heal at once.
        self.char1.apply_health_damage(1, location=wounds.ALL)
        self.assertEqual(healing.accrue(self.char1, 1), 0)

    def test_pushes_char_only_when_a_point_lands(self):
        with mock.patch.object(client_state, "push") as push:
            healing.accrue(self.char1, 1)
        push.assert_not_called()
        with mock.patch.object(client_state, "push") as push:
            healing.accrue(self.char1, self.interval)
        push.assert_called_once_with(self.char1, "char")

    def test_no_body_to_read_is_nothing(self):
        self.char1.stats.remove("siz")
        self.assertEqual(healing.accrue(self.char1, self.interval), 0)


class TestConditionsBlock(HealingTestBase):
    """
    Pressures Legend p. 90: SL-M13 (Dehydrated ignored) and a Starving check
    that also wipes the progress already made.
    """

    def _blocked_by(self, buffclass):
        self.char1.buffs.add(buffclass)
        self.char1.db.heal_progress = self.interval - 1
        start = self.hurt()
        self.assertEqual(healing.accrue(self.char1, 10 * self.interval), 0)
        self.assertEqual(self.hurt(), start)
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
        start = self.hurt()
        lines = self._tick()
        self.assertEqual(self.hurt(), start - 1)
        self.assertEqual(lines.count(healing.HEALED), 1)

    def test_a_tick_short_of_a_point_says_nothing(self):
        self.char1.db.heal_progress = self.interval - 2401
        start = self.hurt()
        lines = self._tick()
        self.assertEqual(self.hurt(), start)
        self.assertEqual(self.char1.db.heal_progress, self.interval - 1)
        self.assertNotIn(healing.HEALED, lines)

    def test_the_tick_that_dehydrates_does_not_heal(self):
        thirst = self.char1.traits.thirst
        thirst.current = thirst.min
        self.char1.db.heal_progress = self.interval - 2400
        start = self.hurt()
        lines = self._tick()
        self.assertTrue(self.char1.buffs.has(Dehydrated))  # receipt: the condition landed
        self.assertEqual(self.hurt(), start)   # one tick of one condition: no point yet (WN6)
        self.assertEqual(self.char1.db.heal_progress, self.interval - 2400)
        self.assertNotIn(healing.HEALED, lines)


class TestTheStatueHealsNothing(HealingTestBase):
    """
    Pressures HL10 (Healing HL-T3): a statue is a snapshot, so the time a
    body spends logged out heals nothing -- no stamp is written at the
    logout and nothing is credited at the login. S2.2's tests (SL7's credit)
    became these. Mutations: HLM8 (the credit left in), HLM9 (the stamp still
    written), HLM10 (the login zeroing `heal_progress`).

    The clock is patched at both ends, so a credit that came back would have
    ten game days to spend: sixty intervals against three points of damage.
    """

    CLOCK = "world.gametime_utils.get_absolute_gametime"
    T = 1_000_000
    TEN_DAYS = 10 * 24 * 3600

    def _leave(self, at):
        with mock.patch(self.CLOCK, return_value=at):
            self.account.unpuppet_object(self.session)

    def _return(self, at):
        with mock.patch(self.CLOCK, return_value=at), \
                mock.patch.object(self.char1, "msg") as msg:
            self.char1.at_post_puppet()
        return [c.args[0] for c in msg.call_args_list if c.args]

    def _body(self):
        # A body made whole has no `body_damage` left: read it as {}, so a
        # credit that came back fails on the numbers and not on a None.
        return dict(self.char1.db.body_damage or {}), self.char1.db.heal_progress

    def test_ten_days_away_heal_nothing_and_say_nothing(self):
        self.char1.db.heal_progress = self.interval - 60
        before = self._body()
        self._leave(self.T)
        lines = self._return(self.T + self.TEN_DAYS)
        self.assertEqual(self._body(), before)
        self.assertNotIn(healing.HEALED, lines)

    def test_a_logout_writes_no_stamp(self):
        # A statue without a room too: S2.2 stamped it before the location
        # check, and the logout must still not raise.
        # A loop and no subTest: a parallel worker cannot send a failing
        # subTest back (Testing Reference §28.1).
        for room in (self.room1, None):
            self.char1.location = room
            self._leave(self.T)
            self.assertFalse(self.char1.attributes.has("away_since"), room)
            self.account.puppet_object(self.session, self.char1)

    def test_a_stored_stamp_is_left_unread(self):
        # Characters that logged out before the merge carry one. It stays
        # where it is and nothing is credited for it -- the one behaviour
        # that shows HLM8, since a credit with no stamp credits nothing (the
        # census sees its name too).
        self.char1.db.away_since = self.T
        self.char1.db.heal_progress = self.interval - 60
        before = self._body()
        lines = self._return(self.T + self.TEN_DAYS)
        self.assertEqual(self.char1.db.away_since, self.T)
        self.assertEqual(self._body(), before)
        self.assertNotIn(healing.HEALED, lines)

    def test_the_tick_after_login_does_not_heal_the_time_away(self):
        # S2.1's C1 seen from the end: the puppet clears the tick's stamp, so
        # the first tick after ten days away counts nothing either.
        self.char1.db.heal_progress = self.interval - 60
        before = self._body()
        self._leave(self.T)
        back = self.T + self.TEN_DAYS
        self._return(back)
        with mock.patch(self.CLOCK, return_value=back + 10):
            survival_ticker._deplete_character(self.char1)
        self.assertEqual(self._body(), before)

    def test_a_session_leaving_while_another_remains_is_no_statue(self):
        # The multisession bail in `at_post_unpuppet` (S2.2's SL-M18 read it
        # through the stamp; nothing else in the suite held it).
        self.assertEqual(self.char1.sessions.count(), 1)
        sessions = self.char1.sessions
        with mock.patch.object(sessions, "count", wraps=sessions.count) as count, \
                mock.patch.object(self.char1, "turn_to_stone") as stone:
            self.char1.at_post_unpuppet(self.account, session=self.session)
        self.assertTrue(count.called)  # receipt: the hook ran and read the sessions
        stone.assert_not_called()


class TestAwaySinceCensus(SimpleTestCase):
    """
    HL10: nothing in production names the stamp of time away. Stamps stored
    before HL stay where they are, unread (WN2b's form; HV-T1's walk).
    """

    def test_nothing_in_production_names_the_stamp(self):
        self.assertEqual(
            away_since_census(), set(),
            "HL10: a statue is a snapshot and the stamp of time away is gone. "
            "A module that reads or writes `away_since` brings the credit back.",
        )


class TestAwaySinceCensusFixtures(SimpleTestCase):
    """The census counts each form that names the stamp, and no other."""

    def test_a_read_is_found(self):
        self.assertEqual(_census_fixture("t = char.db.away_since"), 1)

    def test_a_write_is_found(self):
        self.assertEqual(_census_fixture("self.db.away_since = now"), 1)

    def test_a_read_through_an_alias_is_found(self):
        # WN2b's census was blind to a local alias; this one reads any owner.
        self.assertEqual(_census_fixture("db = self.db\nt = db.away_since"), 1)

    def test_an_attributes_call_is_found(self):
        self.assertEqual(_census_fixture("char.attributes.get('away_since')"), 1)

    def test_a_docstring_that_mentions_it_is_not(self):
        self.assertEqual(
            _census_fixture('"""Once stamped `db.away_since` at logout."""'), 0
        )

    def test_another_name_is_not(self):
        self.assertEqual(_census_fixture("char.db.away_until = 1"), 0)
