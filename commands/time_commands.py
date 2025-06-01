# commands/time_commands.py
"""
Time-related commands for the Fantasy Steampunk MUD.

This module contains commands that interact with the custom gametime system,
allowing players to check the current time, date, and season.
"""

from evennia import Command
from evennia.contrib.base_systems import custom_gametime
from django.conf import settings


class CmdTime(Command):
    """
    Display the current game time and date.
    
    Usage:
        time
        
    This command shows:
    - Current time of day
    - Day of the month
    - Current month and season
    - Current year
    - Real time to game time conversion info
    
    Example output:
        It is evening on the 15th day of Bloomheart, in the year 850.
        The season is spring, and the air carries the scent of new growth.
        
        (OOC: Game time moves at 4x speed. 1 real hour = 4 game hours)
    """
    
    key = "time"
    aliases = ["date", "calendar"]
    locks = "cmd:all()"
    help_category = "General"
    
    def func(self):
        """Execute the time command."""
        # Get the current game time as a tuple
        year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
        
        # Calculate derived values
        month_name = self._get_month_name(month)
        season = self._get_season(month)
        time_of_day = self._get_time_of_day(hour)
        day_suffix = self._get_day_suffix(day + 1)  # Days start from 0 internally
        
        # Build the main time message
        time_msg = (
            f"|yIt is {time_of_day} on the {day + 1}{day_suffix} day of "
            f"{month_name}, in the year {year}.|n"
        )
        
        # Add seasonal flavor text
        season_msg = self._get_season_description(season)
        
        # Add OOC information about time conversion
        ooc_msg = (
            f"\n|w(OOC: Game time moves at {settings.TIME_FACTOR}x speed. "
            f"1 real hour = {settings.TIME_FACTOR} game hours)|n"
        )
        
        # Send the complete message
        self.caller.msg(time_msg + "\n" + season_msg + ooc_msg)
        
        # Optionally show exact time for those who want it
        if "exact" in self.switches:
            exact_msg = f"\n|wExact time: {hour:02d}:{minute:02d}:{second:02d}|n"
            self.caller.msg(exact_msg)
    
    def _get_month_name(self, month_index):
        """Get the fantasy name for a month."""
        try:
            return settings.MONTH_NAMES[month_index]
        except (AttributeError, IndexError):
            return f"Month {month_index + 1}"
    
    def _get_season(self, month_index):
        """Determine the current season based on month."""
        for season, months in settings.SEASONS.items():
            if month_index in months:
                return season
        return "unknown"
    
    def _get_time_of_day(self, hour):
        """Get a descriptive name for the time of day."""
        for time_name, (start, end) in settings.TIME_OF_DAY.items():
            if time_name == "night":
                # Special handling for night (crosses midnight)
                if hour >= start or hour < end:
                    return time_name
            else:
                if start <= hour < end:
                    return time_name
        return f"{hour:02d}:00"
    
    def _get_day_suffix(self, day):
        """Get the appropriate suffix for a day number (1st, 2nd, 3rd, etc)."""
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        return suffix
    
    def _get_season_description(self, season):
        """Return flavor text based on the current season."""
        descriptions = {
            "winter": "|CThe season is winter, and frost covers the land in a crystalline blanket.|n",
            "spring": "|GThe season is spring, and the air carries the scent of new growth.|n",
            "summer": "|YThe season is summer, with warm winds carrying the buzz of industry.|n",
            "autumn": "|rThe season is autumn, as leaves turn to copper and gold.|n",
            "unknown": "|xThe season turns, marking the passage of time.|n"
        }
        return descriptions.get(season, descriptions["unknown"])


class CmdUptime(Command):
    """
    Show how long the game has been running.
    
    Usage:
        uptime
        
    This shows both real time and game time that has passed since
    the server started.
    """
    
    key = "uptime"
    locks = "cmd:all()"
    help_category = "General"
    
    def func(self):
        """Execute the uptime command."""
        from evennia.utils import gametime
        
        # Get the real uptime in seconds
        real_uptime_secs = gametime.uptime()
        game_uptime_secs = real_uptime_secs * settings.TIME_FACTOR
        
        # Convert to readable format
        real_time_str = self._format_time(real_uptime_secs)
        game_time_str = self._format_time(game_uptime_secs)
        
        msg = (
            f"|yServer Uptime:|n\n"
            f"Real time: {real_time_str}\n"
            f"Game time: {game_time_str} (at {settings.TIME_FACTOR}x speed)"
        )
        
        self.caller.msg(msg)
    
    def _format_time(self, seconds):
        """Format seconds into a readable string."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if secs > 0 or not parts:
            parts.append(f"{secs} second{'s' if secs != 1 else ''}")
        
        return ", ".join(parts)
