"""
Weather system for PolishedWorld.

Provides dynamic global weather that changes based on season and time.
Weather states are applied to all rooms and affect player survival.

Based on Mongoose Legend weather mechanics.
"""

from evennia.server.models import ServerConfig

# Weather state constants
# Wind/Cloud ranges based on Mongoose Legend Core Rulebook p.232
# Wind STR ranges map to effects: 1-3=Calm, 4-7=Light Air, 8-12=Breeze,
# 13-18=Light Wind, 19-24=Moderate Wind, 25-30=Strong Wind, 31-36=Gale,
# 37-45=Strong Gale, 46-50=Hurricane
# Cloud cover: 0-10=None, 11-20=Scant, 21-30=Scattered, 31-40=Slightly Overcast,
# 41-50=Moderately Overcast, 51-65=Mostly Overcast, 66-80=Completely Overcast, 81-100=Storm
WEATHER_STATES = {
    "clear": {
        "name": "clear",
        "description": "The sky is clear and blue.",
        "message": "The clouds part, revealing clear skies.",
        "mongoose_wind": (1, 3),  # Calm (Legend p.232)
        "mongoose_cloud": (0, 10),  # No cloud cover
    },
    "partly_cloudy": {
        "name": "partly_cloudy",
        "description": "Scattered clouds drift across the sky.",
        "message": "Clouds begin to gather in the sky.",
        "mongoose_wind": (4, 12),  # Light Air to Breeze (Legend p.232)
        "mongoose_cloud": (11, 30),  # Scant to Scattered cloud
    },
    "cloudy": {
        "name": "cloudy",
        "description": "Grey clouds cover the sky.",
        "message": "The sky grows overcast with thick clouds.",
        "mongoose_wind": (8, 18),  # Breeze to Light Wind (Legend p.232)
        "mongoose_cloud": (31, 50),  # Slightly to Moderately Overcast
    },
    "raining": {
        "name": "raining",
        "description": "Rain falls steadily from dark clouds.",
        "message": "Rain begins to fall.",
        "mongoose_wind": (13, 24),  # Light to Moderate Wind (Legend p.232)
        "mongoose_cloud": (51, 80),  # Mostly to Completely Overcast
    },
    "storming": {
        "name": "storming",
        "description": "A fierce storm rages, with heavy rain and strong winds.",
        "message": "A violent storm rolls in!",
        "mongoose_wind": (25, 36),  # Strong Wind to Gale (Legend p.232)
        "mongoose_cloud": (81, 100),  # Storm clouds
    },
    "snowing": {
        "name": "snowing",
        "description": "Snow falls gently from grey clouds.",
        "message": "Snow begins to fall.",
        "mongoose_wind": (8, 18),  # Breeze to Light Wind (Legend p.232)
        "mongoose_cloud": (51, 80),  # Mostly to Completely Overcast
    },
    "blizzard": {
        "name": "blizzard",
        "description": "A howling blizzard reduces visibility to near zero.",
        "message": "A fierce blizzard strikes!",
        "mongoose_wind": (31, 45),  # Gale to Strong Gale (Legend p.232)
        "mongoose_cloud": (81, 100),  # Storm clouds
    },
    "foggy": {
        "name": "foggy",
        "description": "Thick fog reduces visibility significantly.",
        "message": "Fog rolls in, obscuring the landscape.",
        "mongoose_wind": (1, 7),  # Calm to Light Air (Legend p.232)
        "mongoose_cloud": (41, 65),  # Moderately to Mostly Overcast
    },
}

# Default starting weather
DEFAULT_WEATHER = "clear"

# ServerConfig key for persistent storage
WEATHER_CONFIG_KEY = "current_weather_state"
