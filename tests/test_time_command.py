"""
Tests for the player `time` command (webclient decomposition W5.3, WC1).

The world panel and `time` must say the same thing: the panel computes the
date in the browser from the `world` snapshot (pw_world.js), the command
reads world.gametime_utils. Both are pinned to one committed table,
tests/js/fixtures/world_cases.json: this module checks the table against
gametime_utils, tests/js/test_pw_world.js checks pw_world.js against it.

Each class names the bug it pressures:

    TestParityTable     the table drifts from the calendar the server uses
                        (a month renamed, a period moved, the snapshot's
                        calendar changed), or shrinks until it proves
                        nothing (W-z: the case count is a literal).
    TestTimeLines       a line differs from what gametime_utils says at the
                        same second, Date and Time stop composing the
                        existing get_formatted_date(), or the weather is
                        shown indoors or without a room.
    TestTimeCommand     the command prints something other than its lines,
                        one per row, label and value as the panel shows them.
    TestTimeIsTheKey    typed `time` still reaches the extended_room
                        contrib's command (which the project's cmdset also
                        installs), `date` or `clock` reach something else,
                        or `@time` stops reaching Evennia's server clock.
"""

import json
from pathlib import Path
from unittest import mock

from django.conf import settings
from evennia.commands.cmdparser import cmdparser
from evennia.commands.default import system
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.world_commands import CmdTime, time_lines
from world import client_state, gametime_utils, weather

FIXTURE = Path(settings.GAME_DIR) / "tests" / "js" / "fixtures" / "world_cases.json"
GAMETIME = "evennia.utils.gametime.gametime"
# Frostmelt 8, 10:52 -- a date whose week, day, hour and minute are all
# non-zero, so a swapped unit shows.
PINNED = 604800 + 10 * 3600 + 52 * 60 + 17


def _table():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class TestParityTable(EvenniaTest):
    def test_case_count(self):
        # A literal (W-z): an emptied table would make every loop below pass.
        self.assertEqual(len(_table()["cases"]), 16)

    def test_calendar_is_the_snapshots(self):
        self.assertEqual(_table()["calendar"], client_state._calendar())

    def test_each_case_is_what_time_prints(self):
        self.room1.db.is_indoor = True   # Weather is not in the table
        for case in _table()["cases"]:
            with mock.patch(GAMETIME, return_value=case["seconds"]):
                lines = time_lines(self.room1)
            self.assertEqual(
                lines,
                [("Date", case["date"]), ("Time", case["time"]), ("Season", case["season"])],
                case["seconds"],
            )


class TestTimeLines(EvenniaTest):
    def test_date_and_time_follow_gametime_utils(self):
        with mock.patch(GAMETIME, return_value=PINNED):
            lines = dict(time_lines(self.room1))
            t = gametime_utils.get_current_time()
            period = gametime_utils.get_time_of_day()
            season = gametime_utils.get_season()
        self.assertEqual(lines["Date"], "Year 1, Frostmelt 8")
        self.assertEqual(lines["Time"], "10:52 (%s)" % period)
        self.assertEqual((t["hour"], t["minute"]), (10, 52))
        self.assertEqual(lines["Season"], season)

    def test_date_and_time_compose_get_formatted_date(self):
        with mock.patch(GAMETIME, return_value=PINNED):
            lines = dict(time_lines(self.room1))
            formatted = gametime_utils.get_formatted_date()
        self.assertEqual(lines["Date"] + ", " + lines["Time"], formatted)

    def test_weather_outdoors(self):
        self.room1.db.is_indoor = False
        with mock.patch.object(weather, "get_current_weather", return_value="snowing"):
            lines = time_lines(self.room1)
        self.assertEqual([label for label, _ in lines], ["Date", "Time", "Season", "Weather"])
        self.assertEqual(lines[-1], ("Weather", "snowing"))

    def test_no_weather_indoors(self):
        self.room1.db.is_indoor = True
        lines = time_lines(self.room1)
        self.assertEqual([label for label, _ in lines], ["Date", "Time", "Season"])

    def test_no_weather_without_a_room(self):
        lines = time_lines(None)
        self.assertEqual([label for label, _ in lines], ["Date", "Time", "Season"])


class TestTimeCommand(EvenniaCommandTest):
    def test_prints_one_line_per_row(self):
        self.room1.db.is_indoor = False
        with mock.patch(GAMETIME, return_value=PINNED), \
                mock.patch.object(weather, "get_current_weather", return_value="foggy"):
            expected = "\n".join("%s: %s" % row for row in time_lines(self.room1))
            out = self.call(CmdTime(), "")
        self.assertEqual(out, expected)
        self.assertEqual(out.splitlines()[-1], "Weather: foggy")

    def test_indoors_prints_no_weather(self):
        self.room1.db.is_indoor = True
        out = self.call(CmdTime(), "")
        self.assertEqual(len(out.splitlines()), 3)
        self.assertNotIn("Weather", out)


class TestTimeIsTheKey(EvenniaTest):
    def setUp(self):
        super().setUp()
        from commands.default_cmdsets import CharacterCmdSet

        self.cmdset = CharacterCmdSet()
        self.cmdset.at_cmdset_creation()

    def _reached(self, typed):
        matches = cmdparser(typed, self.cmdset, self.char1)
        self.assertEqual(len(matches), 1, typed)
        return matches[0][2]

    def test_time_date_and_clock_reach_this_command(self):
        for typed in ("time", "date", "clock"):
            self.assertIsInstance(self._reached(typed), CmdTime, typed)

    def test_the_contrib_time_is_gone(self):
        # Classes, not names: Evennia's @time is also called CmdTime.
        owners = [type(cmd) for cmd in self.cmdset.commands if "time" in cmd._keyaliases]
        self.assertEqual(owners, [CmdTime])
        self.assertIs(type(self.cmdset.get("time")), CmdTime)

    def test_at_time_still_reaches_evennias(self):
        self.assertIsInstance(self._reached("@time"), system.CmdTime)
