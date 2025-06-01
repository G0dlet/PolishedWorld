r"""
Evennia settings file.

The available options are found in the default settings file found
here:

https://www.evennia.com/docs/latest/Setup/Settings-Default.html

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "PolishedWorld"



######################################################################
# Custom Gametime Configuration
######################################################################

# Game runs at 4x real time speed
# 1 real hour = 4 game hours
# 6 real hours = 24 game hours (1 game day)
TIME_FACTOR = 4

# Fantasy calendar with 12 months of 30 days each
# Total: 360 days per year (easy math for seasons)
TIME_UNITS = {
    "sec": 1,
    "min": 60,
    "hour": 60 * 60,
    "day": 60 * 60 * 24,
    "week": 60 * 60 * 24 * 7,
    "month": 60 * 60 * 24 * 30,      # Exactly 30 days per month
    "year": 60 * 60 * 24 * 30 * 12,  # 360 days per year
}

# Fantasy month names reflecting the steampunk theme
# Winter: Months 0, 1, 2 (Frosthold, Icewind, Thawmoon)
# Spring: Months 3, 4, 5 (Seedtime, Bloomheart, Greentide)
# Summer: Months 6, 7, 8 (Sunpeak, Hearthfire, Goldfall)
# Autumn: Months 9, 10, 11 (Harvestmoon, Dimming, Darkening)
MONTH_NAMES = [
    "Frosthold",    # Month 0 - Deep winter
    "Icewind",      # Month 1 - Late winter
    "Thawmoon",     # Month 2 - Winter's end
    "Seedtime",     # Month 3 - Early spring
    "Bloomheart",   # Month 4 - Mid spring
    "Greentide",    # Month 5 - Late spring
    "Sunpeak",      # Month 6 - Early summer
    "Hearthfire",   # Month 7 - High summer
    "Goldfall",     # Month 8 - Late summer
    "Harvestmoon",  # Month 9 - Early autumn
    "Dimming",      # Month 10 - Mid autumn
    "Darkening"     # Month 11 - Late autumn
]

# Define seasons based on months
# This will be used by Extended Room later
SEASONS = {
    "winter": [11, 0, 1, 2],   # Darkening through Thawmoon
    "spring": [3, 4, 5],       # Seedtime through Greentide
    "summer": [6, 7, 8],       # Sunpeak through Goldfall
    "autumn": [9, 10]          # Harvestmoon through Dimming
}

# Time of day descriptions for immersion
TIME_OF_DAY = {
    "dawn": (5, 7),        # 05:00 - 06:59
    "morning": (7, 12),    # 07:00 - 11:59
    "noon": (12, 14),      # 12:00 - 13:59
    "afternoon": (14, 17), # 14:00 - 16:59
    "dusk": (17, 19),      # 17:00 - 18:59
    "evening": (19, 22),   # 19:00 - 21:59
    "night": (22, 5)       # 22:00 - 04:59
}

######################################################################
# Character and Traits Configuration
######################################################################

# How often survival traits should be updated (in real seconds)
# With TIME_FACTOR = 4, 900 real seconds = 1 game hour
TRAIT_UPDATE_INTERVAL = 900  # Update every game hour

# Trait decay rates per game hour
TRAIT_DECAY_RATES = {
    "hunger": -2,    # Lose 2 hunger per game hour
    "thirst": -3,    # Lose 3 thirst per game hour
    "fatigue": -1,   # Lose 1 fatigue per game hour
}

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
