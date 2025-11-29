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

# ============================================================
# GAME TIME SYSTEM - 13 Month Fantasy Calendar
# ============================================================
# Time progression: 4x real time (1 real hour = 4 game hours)
# Calendar structure: 13 months × 28 days = 364 days/year
# Real world equivalents:
#   - 6 real hours = 1 game day
#   - 7 real days = 1 game month
#   - 91 real days = 1 game year

TIME_FACTOR = 4

TIME_UNITS = {
    "sec": 1,
    "min": 60,
    "hour": 60 * 60,                          # 3600 seconds
    "day": 60 * 60 * 24,                      # 86400 seconds (24 hours)
    "week": 60 * 60 * 24 * 7,                 # 604800 seconds (7 days)
    "month": 60 * 60 * 24 * 7 * 4,            # 2419200 seconds (28 days = 4 weeks)
    "year": 60 * 60 * 24 * 7 * 4 * 13         # 31449600 seconds (364 days = 13 months)
}

# Starting game time: Year 1, Month 1, Day 1
TIME_GAME_EPOCH = 1

# Fantasy month names for immersive calendar display
MONTH_NAMES = {
    1: "Frostmelt",      # Early Spring
    2: "Greenrise",      # Mid Spring
    3: "Bloomtide",      # Late Spring
    4: "Brightdawn",     # Early Summer
    5: "Sunpeak",        # High Summer
    6: "Harvestwarm",    # Mid Summer
    7: "Goldendays",     # Late Summer
    8: "Leaffall",       # Early Autumn
    9: "Emberwind",      # Mid Autumn
    10: "Darkening",     # Late Autumn
    11: "Frosthold",     # Early Winter
    12: "Deepsnow",      # Deep Winter
    13: "Icewane",       # Late Winter (transitions to Frostmelt)
}

# Season definitions (month numbers for each season)
# Extended summer (4 months) provides more gameplay time
SEASON_MONTHS = {
    "spring": [1, 2, 3],           # 84 days, 12 weeks
    "summer": [4, 5, 6, 7],        # 112 days, 16 weeks
    "autumn": [8, 9, 10],          # 84 days, 12 weeks
    "winter": [11, 12, 13],        # 84 days, 12 weeks
}
######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
