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
CMDSET_UNLOGGEDIN = "evennia.contrib.base_systems.menu_login.UnloggedinCmdSet"
# CONNECTION_SCREEN_MODULE = "evennia.contrib.base_systems.menu_login.connection_screens"

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

# Global weather system.
# interval 1800s = 30 real-min = 2 game-hours @ TIME_FACTOR 4.
# Bump interval if weather feels too twitchy (3600 = 4 game-hours is calmer).
# start_delay=True: keep the seeded 'clear' for the first cycle instead of
# rolling the instant the script is first created.
GLOBAL_SCRIPTS = {
    "weather": {
        "typeclass": "typeclasses.scripts.WeatherScript",
        "interval": 1800,
        "repeats": -1,
        "persistent": True,
        "start_delay": True,
        "desc": "Global weather system",
    },
    # Creature respawn ticker. interval 300s = 5 real-min = 20 game-min @ TIME_FACTOR 4.
    # Sparse spawn (1/species/tick): a depleted 3-rabbit room refills over ~15 real-min.
    # start_delay=False: begin topping up populations right after a restart.
    "creature_spawn": {
        "typeclass": "typeclasses.scripts.CreatureSpawnScript",
        "interval": 300,
        "repeats": -1,
        "persistent": True,
        "start_delay": False,
        "desc": "Maintains creature populations in spawn-flagged rooms",
    },
}

# Crafting contrib: where to look for CraftingRecipe subclasses.
# Verified settings key (singular RECIPE), read in crafting.py.
CRAFT_RECIPE_MODULES = ["world.recipes"]

# ============================================================
# CLOTHING CONTRIB
# evennia/contrib/game_systems/clothing/clothing.py
# ============================================================
# NOTE (verified against source): the contrib reads CLOTHING_TYPE_ORDER from
# the *misspelled* key CLOTHING_TYPE_ORDERED (extra D, clothing.py:104-106).
# This list is identical to the contrib default; we pin it because B.3's
# prototypes hardcode these clothing_type strings and we don't want an upstream
# reorder to silently shift our display order.
CLOTHING_TYPE_ORDERED = [
    "hat", "jewelry", "top", "undershirt", "gloves",
    "fullbody", "bottom", "underpants", "socks", "shoes", "accessory",
]

# One garment per physical body region. Prevents warmth-stacking exploits:
# worn_warmth() sums ALL worn pieces (covered ones included), so without a
# per-slot cap a player could wear many fullbody cloaks for runaway warmth.
# jewelry/accessory are intentionally omitted -> unlimited (decorative, warmth 0).
CLOTHING_TYPE_LIMIT = {
    "hat": 1, "top": 1, "undershirt": 1, "gloves": 1,
    "fullbody": 1, "bottom": 1, "underpants": 1, "socks": 1, "shoes": 1,
}

# Deliberately NOT overriding CLOTHING_TYPE_AUTOCOVER: the contrib reads BOTH
# autocover AND cant-cover-with from this single key (clothing.py:131-142), so
# overriding it would clobber cant-cover-with. The default autocover dict
# (top->undershirt, fullbody->undershirt+underpants, shoes->socks) is already
# what we want. CLOTHING_OVERALL_LIMIT stays at its default (20).

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
