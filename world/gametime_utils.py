# world/gametime_utils.py
"""
Gametime utility functions for the Fantasy Steampunk MUD.

This module provides helper functions for working with the custom
gametime system, including season detection, time formatting, and
integration with game systems.
"""

from evennia.contrib.base_systems import custom_gametime
from django.conf import settings


def get_current_season():
    """
    Get the current season based on game time.
    
    Returns:
        str: The current season name ('winter', 'spring', 'summer', 'autumn')
    """
    year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
    
    for season, months in settings.SEASONS.items():
        if month in months:
            return season
    return "unknown"


def get_time_of_day():
    """
    Get the current time of day as a descriptive string.
    
    Returns:
        str: Time of day ('dawn', 'morning', 'noon', etc.)
    """
    year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
    
    for time_name, (start, end) in settings.TIME_OF_DAY.items():
        if time_name == "night":
            if hour >= start or hour < end:
                return time_name
        else:
            if start <= hour < end:
                return time_name
    return "unknown"


def format_game_date():
    """
    Format the current game date in a readable format.
    
    Returns:
        str: Formatted date string (e.g., "15th of Bloomheart, Year 850")
    """
    year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
    
    # Get month name
    month_name = settings.MONTH_NAMES[month] if month < len(settings.MONTH_NAMES) else f"Month {month + 1}"
    
    # Format day with suffix
    day_num = day + 1  # Days are 0-indexed internally
    if 10 <= day_num % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day_num % 10, 'th')
    
    return f"{day_num}{suffix} of {month_name}, Year {year}"


def get_hours_until_next_trait_update():
    """
    Calculate how many game hours until the next trait update.
    
    Returns:
        float: Number of game hours until next update
    """
    # With our setup, traits update every game hour
    # Get current time and calculate minutes/seconds until next hour
    year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
    
    # Calculate seconds until next hour
    seconds_until_hour = (60 - minute) * 60 - second
    
    # Convert to game hours
    return seconds_until_hour / 3600.0


def is_night_time():
    """
    Check if it's currently night time in the game.
    
    Returns:
        bool: True if it's night time, False otherwise
    """
    time_of_day = get_time_of_day()
    return time_of_day in ["night", "dusk", "dawn"]


def is_winter():
    """
    Check if it's currently winter in the game.
    
    Returns:
        bool: True if it's winter, False otherwise
    """
    return get_current_season() == "winter"


def get_seasonal_modifier(season=None):
    """
    Get modifiers that should be applied based on the current season.
    
    Args:
        season (str, optional): Season to check. If None, uses current season.
        
    Returns:
        dict: Dictionary of modifiers for various game systems
    """
    if season is None:
        season = get_current_season()
    
    modifiers = {
        "winter": {
            "resource_availability": 0.5,  # Half resources available
            "fatigue_rate": 1.5,          # Tire 50% faster
            "food_decay": 0.5,            # Food lasts longer
            "visibility": 0.8,            # Reduced visibility
        },
        "spring": {
            "resource_availability": 1.2,  # More resources
            "fatigue_rate": 0.9,          # Slightly less tiring
            "food_decay": 1.0,            # Normal decay
            "visibility": 1.0,            # Normal visibility
        },
        "summer": {
            "resource_availability": 1.5,  # Abundant resources
            "fatigue_rate": 1.2,          # Tire faster in heat
            "food_decay": 1.5,            # Food spoils faster
            "visibility": 1.2,            # Excellent visibility
        },
        "autumn": {
            "resource_availability": 1.3,  # Good harvest time
            "fatigue_rate": 1.0,          # Normal fatigue
            "food_decay": 0.8,            # Cooler weather helps
            "visibility": 0.9,            # Slightly reduced
        }
    }
    
    return modifiers.get(season, {
        "resource_availability": 1.0,
        "fatigue_rate": 1.0,
        "food_decay": 1.0,
        "visibility": 1.0
    })
