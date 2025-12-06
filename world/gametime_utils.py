"""
PolishedWorld GameTime Utilities
Helper functions for working with PolishedWorld's custom 13-month calendar.

This module provides convenient functions for:
- Getting current game time
- Converting between game time and calendar dates
- Formatting time strings
- Scheduling events based on game time

Calendar Structure:
    - 13 months × 28 days = 364 days/year
    - 4 weeks per month (consistent)
    - 24 hours per day
    - TIME_FACTOR = 4 (game runs 4× faster than real time)

Seasons (configured in settings.py):
    - Spring: Months 1-3
    - Summer: Months 4-7 (extended)
    - Autumn: Months 8-10
    - Winter: Months 11-13

Usage:
    from world.gametime_utils import get_current_time, get_season, get_formatted_time

    # Get current time as dict
    time = get_current_time()
    print(f"Year {time['year']}, {time['month_name']}")

    # Get just the season
    season = get_season()

    # Get formatted string
    print(get_formatted_time())
"""

from evennia.contrib.base_systems.custom_gametime import custom_gametime
from django.conf import settings


# ============================================================================
# CALENDAR CONSTANTS (loaded from settings.py)
# ============================================================================


# Month names are loaded from settings.MONTH_NAMES
# This ensures consistency with the rest of the game
def get_month_names():
    """Get month names from settings."""
    return getattr(
        settings,
        "MONTH_NAMES",
        {
            1: "Month1",
            2: "Month2",
            3: "Month3",
            4: "Month4",
            5: "Month5",
            6: "Month6",
            7: "Month7",
            8: "Month8",
            9: "Month9",
            10: "Month10",
            11: "Month11",
            12: "Month12",
            13: "Month13",
        },
    )


def get_season_months():
    """Get season month mappings from settings."""
    return getattr(
        settings,
        "SEASON_MONTHS",
        {
            "spring": [1, 2, 3],
            "summer": [4, 5, 6, 7],
            "autumn": [8, 9, 10],
            "winter": [11, 12, 13],
        },
    )


# Time period names (hour ranges)
TIME_PERIODS = {
    (0, 4): "night",
    (4, 6): "dawn",
    (6, 9): "morning",
    (9, 12): "day",
    (12, 15): "afternoon",
    (15, 18): "evening",
    (18, 20): "dusk",
    (20, 24): "night",
}

# Calendar structure
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
WEEKS_PER_MONTH = 4
DAYS_PER_MONTH = DAYS_PER_WEEK * WEEKS_PER_MONTH  # 28
MONTHS_PER_YEAR = 13
DAYS_PER_YEAR = DAYS_PER_MONTH * MONTHS_PER_YEAR  # 364


# ============================================================================
# CORE FUNCTIONS
# ============================================================================


def get_current_time():
    """
    Get current game time as a structured dictionary.

    Returns:
        dict: Dictionary containing:
            - year (int): Current year
            - month (int): Current month (1-13)
            - month_name (str): Name of current month
            - day (int): Current day of month (1-28)
            - week (int): Current week of month (1-4)
            - day_of_week (int): Day of week (1-7, Monday=1)
            - hour (int): Current hour (0-23)
            - minute (int): Current minute (0-59)
            - second (int): Current second (0-59)
            - season (str): Current season (spring/summer/autumn/winter)
            - time_of_day (str): Time period (night/dawn/morning/etc.)

    Example:
        >>> time = get_current_time()
        >>> print(f"Year {time['year']}, {time['month_name']}")
        Year 1, Frostmelt
    """
    # Get game time in seconds since epoch
    # custom_gametime() returns (total_seconds, year, month, day, hour, min, sec)
    game_time = custom_gametime()

    # Extract total seconds from tuple if needed
    if isinstance(game_time, tuple):
        total_seconds = int(game_time[0])
    else:
        total_seconds = int(game_time)

    # Years
    seconds_per_year = DAYS_PER_YEAR * HOURS_PER_DAY * 3600
    year = total_seconds // seconds_per_year
    remaining = total_seconds % seconds_per_year

    # Months (1-13)
    seconds_per_month = DAYS_PER_MONTH * HOURS_PER_DAY * 3600
    month = (remaining // seconds_per_month) + 1
    remaining = remaining % seconds_per_month

    # Days (1-28)
    seconds_per_day = HOURS_PER_DAY * 3600
    day = (remaining // seconds_per_day) + 1
    remaining = remaining % seconds_per_day

    # Week (1-4)
    week = ((day - 1) // DAYS_PER_WEEK) + 1

    # Day of week (1-7, where 1 = Monday)
    day_of_week = ((day - 1) % DAYS_PER_WEEK) + 1

    # Hours, minutes, seconds
    hour = remaining // 3600
    remaining = remaining % 3600
    minute = remaining // 60
    second = remaining % 60

    # Get month names from settings
    month_names = get_month_names()

    return {
        "year": year,
        "month": month,
        "month_name": month_names.get(month, "Unknown"),
        "day": day,
        "week": week,
        "day_of_week": day_of_week,
        "hour": hour,
        "minute": minute,
        "second": second,
        "season": get_season_from_month(month),
        "time_of_day": get_time_of_day_from_hour(hour),
    }


def get_season():
    """
    Get current season.

    Returns:
        str: Current season ("spring", "summer", "autumn", or "winter")

    Example:
        >>> season = get_season()
        >>> print(f"It is {season}")
        It is spring
    """
    time = get_current_time()
    return time["season"]


def get_current_month():
    """
    Get current month number.

    Returns:
        int: Current month (1-13)

    Example:
        >>> month = get_current_month()
        >>> print(f"Month {month}")
        Month 1
    """
    time = get_current_time()
    return time["month"]


def get_current_day():
    """
    Get current day of month.

    Returns:
        int: Current day (1-28)

    Example:
        >>> day = get_current_day()
        >>> print(f"Day {day}")
        Day 15
    """
    time = get_current_time()
    return time["day"]


def get_current_year():
    """
    Get current year.

    Returns:
        int: Current year (starts at 0)

    Example:
        >>> year = get_current_year()
        >>> print(f"Year {year}")
        Year 1
    """
    time = get_current_time()
    return time["year"]


def get_time_of_day():
    """
    Get current time of day period.

    Returns:
        str: Time period ("night", "dawn", "morning", "day",
             "afternoon", "evening", or "dusk")

    Example:
        >>> time_period = get_time_of_day()
        >>> print(f"It is {time_period}")
        It is morning
    """
    time = get_current_time()
    return time["time_of_day"]


def get_formatted_time(short=False):
    """
    Get formatted time string.

    Args:
        short (bool): If True, return abbreviated format

    Returns:
        str: Formatted time string

    Examples:
        >>> get_formatted_time()
        'Year 1, Frostmelt (Month 1), Day 5, Morning (08:30)'

        >>> get_formatted_time(short=True)
        'Frostmelt 5, 08:30'
    """
    t = get_current_time()

    if short:
        return f"{t['month_name']} {t['day']}, {t['hour']:02d}:{t['minute']:02d}"
    else:
        return (
            f"Year {t['year']}, {t['month_name']} (Month {t['month']}), "
            f"Day {t['day']}, {t['time_of_day'].title()} "
            f"({t['hour']:02d}:{t['minute']:02d})"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_season_from_month(month):
    """
    Get season name from month number using settings.SEASON_MONTHS.

    Args:
        month (int): Month number (1-13)

    Returns:
        str: Season name

    Examples:
        >>> get_season_from_month(1)
        'spring'
        >>> get_season_from_month(5)
        'summer'
    """
    season_months = get_season_months()

    for season, months in season_months.items():
        if month in months:
            return season

    # Fallback
    return "unknown"


def get_time_of_day_from_hour(hour):
    """
    Get time of day period from hour.

    Args:
        hour (int): Hour (0-23)

    Returns:
        str: Time period name

    Examples:
        >>> get_time_of_day_from_hour(8)
        'morning'
        >>> get_time_of_day_from_hour(14)
        'afternoon'
    """
    for (start, end), period in TIME_PERIODS.items():
        if start <= hour < end:
            return period
    return "night"  # Default fallback


def get_month_name(month=None):
    """
    Get month name from number.

    Args:
        month (int, optional): Month number (1-13). If None, uses current month.

    Returns:
        str: Month name

    Examples:
        >>> get_month_name(1)
        'Frostmelt'
        >>> get_month_name()  # Current month
        'Frostmelt'
    """
    if month is None:
        month = get_current_month()

    month_names = get_month_names()
    return month_names.get(month, "Unknown")


def is_daytime():
    """
    Check if it's currently daytime.

    Returns:
        bool: True if morning, day, or afternoon

    Example:
        >>> if is_daytime():
        ...     print("The sun is up!")
    """
    time_of_day = get_time_of_day()
    return time_of_day in ["morning", "day", "afternoon"]


def is_nighttime():
    """
    Check if it's currently nighttime.

    Returns:
        bool: True if night, dawn, dusk, or evening

    Example:
        >>> if is_nighttime():
        ...     print("It's dark outside!")
    """
    time_of_day = get_time_of_day()
    return time_of_day in ["night", "dawn", "dusk", "evening"]


# ============================================================================
# TIME CALCULATION FUNCTIONS
# ============================================================================


def game_time_to_seconds(year=0, month=1, day=1, hour=0, minute=0, second=0):
    """
    Convert game time components to seconds since epoch.

    Args:
        year (int): Year number
        month (int): Month (1-13)
        day (int): Day (1-28)
        hour (int): Hour (0-23)
        minute (int): Minute (0-59)
        second (int): Second (0-59)

    Returns:
        int: Seconds since epoch

    Example:
        >>> # Calculate time for Year 1, Month 4, Day 15, 14:30
        >>> secs = game_time_to_seconds(year=1, month=4, day=15, hour=14, minute=30)
    """
    total = 0

    # Years
    total += year * DAYS_PER_YEAR * HOURS_PER_DAY * 3600

    # Months (month is 1-indexed, so subtract 1)
    total += (month - 1) * DAYS_PER_MONTH * HOURS_PER_DAY * 3600

    # Days (day is 1-indexed, so subtract 1)
    total += (day - 1) * HOURS_PER_DAY * 3600

    # Hours, minutes, seconds
    total += hour * 3600
    total += minute * 60
    total += second

    return total


# ============================================================================
# SCHEDULING FUNCTIONS
# ============================================================================


def schedule_at_time(
    callback, year=None, month=None, day=None, hour=None, minute=None, second=0
):
    """
    Schedule a callback to run at a specific game time.

    Args:
        callback (callable): Function to call
        year (int): Target year (None = current year)
        month (int): Target month (None = current month)
        day (int): Target day (None = current day)
        hour (int): Target hour (None = current hour)
        minute (int): Target minute (None = current minute)
        second (int): Target second

    Example:
        >>> # Schedule something at midnight tonight
        >>> schedule_at_time(my_function, hour=0, minute=0)
    """
    current = get_current_time()

    # Use current values if not specified
    target_year = year if year is not None else current["year"]
    target_month = month if month is not None else current["month"]
    target_day = day if day is not None else current["day"]
    target_hour = hour if hour is not None else current["hour"]
    target_minute = minute if minute is not None else current["minute"]

    # Calculate target time in seconds
    target_seconds = game_time_to_seconds(
        year=target_year,
        month=target_month,
        day=target_day,
        hour=target_hour,
        minute=target_minute,
        second=second,
    )

    # Calculate delay (in game seconds)
    game_time = custom_gametime()
    if isinstance(game_time, tuple):
        current_seconds = game_time[0]
    else:
        current_seconds = game_time

    delay = target_seconds - current_seconds

    if delay < 0:
        # Target time is in the past, add one period
        if hour is not None and day is None:
            # Next day at same hour
            delay += HOURS_PER_DAY * 3600
        elif day is not None and month is None:
            # Next month at same day
            delay += DAYS_PER_MONTH * HOURS_PER_DAY * 3600
        else:
            # Default: add one day
            delay += HOURS_PER_DAY * 3600

    # Schedule using custom_gametime
    custom_gametime.schedule(callback=callback, repeat=False, game_seconds=delay)


def schedule_every(callback, hours=0, minutes=0, seconds=0):
    """
    Schedule a callback to repeat at regular intervals.

    Args:
        callback (callable): Function to call
        hours (int): Interval in game hours
        minutes (int): Interval in game minutes
        seconds (int): Interval in game seconds

    Example:
        >>> # Run every 2 game hours
        >>> schedule_every(my_function, hours=2)

        >>> # Run every 30 game minutes
        >>> schedule_every(my_function, minutes=30)
    """
    total_seconds = hours * 3600 + minutes * 60 + seconds

    if total_seconds <= 0:
        raise ValueError("Interval must be greater than 0")

    custom_gametime.schedule(callback=callback, repeat=True, game_seconds=total_seconds)


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================


def format_time_compact(time_dict=None):
    """
    Format time in compact style for status displays.

    Args:
        time_dict (dict): Time dict from get_current_time() (or None for current)

    Returns:
        str: Compact time string

    Example:
        >>> format_time_compact()
        'Frostmelt 5, Morning'
    """
    if time_dict is None:
        time_dict = get_current_time()

    return f"{time_dict['month_name']} {time_dict['day']}, {time_dict['time_of_day'].title()}"


def format_time_verbose(time_dict=None):
    """
    Format time with full details.

    Args:
        time_dict (dict): Time dict from get_current_time() (or None for current)

    Returns:
        str: Verbose time string

    Example:
        >>> format_time_verbose()
        'Year 1, Month 1 (Frostmelt), Day 5 (Week 1, Monday),
         Morning 08:30:15, Spring'
    """
    if time_dict is None:
        time_dict = get_current_time()

    day_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    day_name = day_names[time_dict["day_of_week"] - 1]

    return (
        f"Year {time_dict['year']}, "
        f"Month {time_dict['month']} ({time_dict['month_name']}), "
        f"Day {time_dict['day']} (Week {time_dict['week']}, {day_name}), "
        f"{time_dict['time_of_day'].title()} "
        f"{time_dict['hour']:02d}:{time_dict['minute']:02d}:{time_dict['second']:02d}, "
        f"{time_dict['season'].title()}"
    )


# ============================================================================
# TIME COMMAND (Optional - for testing)
# ============================================================================


def get_time_display():
    """
    Get formatted time display for 'time' command.

    Returns:
        str: Formatted time display

    Example:
        >>> print(get_time_display())
    """
    t = get_current_time()

    lines = []
    lines.append("|w" + "=" * 60 + "|n")
    lines.append("|wCurrent Game Time|n")
    lines.append("|w" + "=" * 60 + "|n")
    lines.append("")
    lines.append(f"|cDate:|n Year {t['year']}, {t['month_name']} {t['day']}")
    lines.append(
        f"|cTime:|n {t['hour']:02d}:{t['minute']:02d} ({t['time_of_day'].title()})"
    )
    lines.append(f"|cSeason:|n {t['season'].title()}")
    lines.append("")
    lines.append("|w" + "=" * 60 + "|n")

    return "\n".join(lines)
