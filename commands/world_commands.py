"""
commands/world_commands.py
==========================
The player `time` command (webclient decomposition W5.3, WC1).

Every datum the webclient's world panel shows is also reachable in text:
`time` prints the date, the time of day with its period, the season and,
outdoors, the weather -- one line per panel row, with the panel's label.
The panel computes the same lines in the browser (pw_world.js) from the
`world` snapshot; both are pinned to tests/js/fixtures/world_cases.json.

This replaces the extended_room contrib's `time` (CmdExtendedRoomGameTime,
installed with ExtendedRoomCmdSet), which printed the season and period in
a sentence: CharacterCmdSet adds this command after that cmdset, so the
later command with the same key wins. Evennia's `@time` (server uptime and
a real-calendar stamp) is untouched: CMD_IGNORE_PREFIXES strips its `@`
only when nothing matched the typed name as written (evennia/commands/cmdparser.py:162).
"""

from evennia import Command

from world import gametime_utils, weather


def time_lines(location):
    """
    The `time` command's rows as (label, value) pairs, in panel order.

    Date and Time joined with ", " are exactly
    gametime_utils.get_formatted_date(). Weather is added only with a
    location that is not indoors (room db.is_indoor), the rule the panel
    reads from the room snapshot's `indoor`. Each reader asks the game clock
    itself, as get_formatted_date() does, so a call that straddles a minute
    boundary can mix the two minutes; at four times real speed a game minute
    lasts fifteen real seconds and the next `time` agrees again.
    """
    t = gametime_utils.get_current_time()
    month = gametime_utils.get_month_name(t["month_display"])
    lines = [
        ("Date", f"Year {t['year_display']}, {month} {t['day_of_month_display']}"),
        ("Time", f"{t['hour']:02d}:{t['minute']:02d} ({gametime_utils.get_time_of_day()})"),
        ("Season", gametime_utils.get_season()),
    ]
    if location is not None and not location.db.is_indoor:
        lines.append(("Weather", weather.get_current_weather()))
    return lines


class CmdTime(Command):
    """
    See the date, the time of day, the season and the weather.

    Usage:
      time
      date
      clock

    Shows the game's date and time, the season and, when you are outdoors,
    the weather. A game day lasts six real hours. The webclient's World
    panel shows the same lines.
    """

    key = "time"
    aliases = ["date", "clock"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        lines = time_lines(self.caller.location)
        self.caller.msg("\n".join(f"{label}: {value}" for label, value in lines))
