"""
world/gametime_utils.py
=======================

Single source of truth for all in-game time queries in PolishedWorld.

Why this exists:
    Evennia's ExtendedRoom has built-in get_time_of_day() and
    get_season(), but they use evennia.utils.gametime combined with
    datetime.fromtimestamp(), which assumes a 12-month real-world
    calendar. That breaks our 13-month fantasy calendar (datetime
    cannot represent month=13).

    This module wraps custom_gametime() with PolishedWorld-specific
    conventions, so every system (rooms, weather, survival, scheduled
    events) reads time through the same lens.

Indexing convention:
    custom_gametime() returns a 0-indexed tuple. Verified empirically
    via world/test_gametime.py and by inspecting the installed source
    (time_to_tuple does pure `seconds // divisor`, no +1 offset).

    For UI display we add +1 to year, month, and day-of-month so
    players see "Year 1, Frostmelt 1" instead of "Year 0, Month 0,
    Week 0, Day 0".

Public API:
    get_current_time()   -> dict   raw and display-ready parts
    get_time_of_day()    -> str    'dawn', 'morning', ...
    get_season()         -> str    'spring', 'summer', ...
    get_month_name()     -> str    'Frostmelt', ...
    get_formatted_date() -> str    'Year 1, Frostmelt 20, 10:52 (day)'
    is_daytime()         -> bool
    is_nighttime()       -> bool
"""

from django.conf import settings
from evennia.contrib.base_systems import custom_gametime as _cgt


# ----------------------------------------------------------------------
# Constants — canonical period definitions for PolishedWorld.
# ----------------------------------------------------------------------

TIMES_OF_DAY = {
    "night":     [(20 / 24, 1.0), (0.0, 4 / 24)],   # 20:00-04:00 (wraps)
    "dawn":      [(4 / 24, 6 / 24)],                # 04:00-06:00
    "morning":   [(6 / 24, 9 / 24)],                # 06:00-09:00
    "day":       [(9 / 24, 12 / 24)],               # 09:00-12:00
    "afternoon": [(12 / 24, 15 / 24)],              # 12:00-15:00
    "evening":   [(15 / 24, 18 / 24)],              # 15:00-18:00
    "dusk":      [(18 / 24, 20 / 24)],              # 18:00-20:00
}

_SEASONS = {
    "spring": {1, 2, 3},
    "summer": {4, 5, 6, 7},
    "autumn": {8, 9, 10},
    "winter": {11, 12, 13},
}

_DEFAULT_MONTH_NAMES = {i: f"Month {i}" for i in range(1, 14)}


# ----------------------------------------------------------------------
# Core query
# ----------------------------------------------------------------------

def get_current_time():
    """Return the current in-game time as a structured dict."""
    year, month, week, day, hour, minute, second = _cgt.custom_gametime(
        absolute=True
    )
    return {
        "year": year,
        "month": month,
        "week": week,
        "day": day,
        "hour": hour,
        "minute": minute,
        "second": second,
        "year_display": year + 1,
        "month_display": month + 1,
        "day_of_month_display": week * 7 + day + 1,
    }


# ----------------------------------------------------------------------
# Period detection
# ----------------------------------------------------------------------

def get_time_of_day():
    """Return the current time-of-day period (e.g. 'morning')."""
    t = get_current_time()
    fraction = (t["hour"] * 3600 + t["minute"] * 60 + t["second"]) / 86400
    for period, ranges in TIMES_OF_DAY.items():
        for start, end in ranges:
            if start <= fraction < end:
                return period
    return "day"


def get_season():
    """Return the current season (one of 'spring', 'summer', 'autumn', 'winter')."""
    month_display = get_current_time()["month_display"]
    for season, months in _SEASONS.items():
        if month_display in months:
            return season
    return "spring"


def is_daytime():
    """True if current period is anything other than night."""
    return get_time_of_day() != "night"


def is_nighttime():
    """True if current period is night."""
    return get_time_of_day() == "night"


# ----------------------------------------------------------------------
# Display helpers
# ----------------------------------------------------------------------

def get_month_name(month_display=None):
    """Return the fantasy month name for a 1-indexed month, or the current month."""
    if month_display is None:
        month_display = get_current_time()["month_display"]
    names = getattr(settings, "MONTH_NAMES", _DEFAULT_MONTH_NAMES)
    return names.get(month_display, f"Month {month_display}")


def get_formatted_date():
    """Return a human-readable description of the current in-game moment."""
    t = get_current_time()
    return (
        f"Year {t['year_display']}, "
        f"{get_month_name(t['month_display'])} {t['day_of_month_display']}, "
        f"{t['hour']:02d}:{t['minute']:02d} "
        f"({get_time_of_day()})"
    )
