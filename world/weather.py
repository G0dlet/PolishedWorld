"""
Global weather system — pure logic layer.

This module holds NO Evennia state. It defines the weather vocabulary,
the season -> allowed-states mapping, broadcast messages, and a pure
roll function. The stateful parts (timer, current weather) live in
typeclasses/scripts.py:WeatherScript (Task 1.2). Keeping the logic pure
makes it unit-testable via @py without a running script.

Design notes (MVP):
- v1 uses *uniform random among season-allowed states* (no probability
  weighting). For unconstrained random, point roll_weather at
  WEATHER_STATES directly. For weighted/inertia later, extend
  roll_weather (signature already accepts `current`).
- 'clear' is a real state (used for broadcasts like "skies clear up")
  but is intentionally NOT injected as a room_state in rooms.py (Task
  1.4): clear weather = the room's normal desc, no fragment.
"""

import random

# Canonical weather vocabulary. 'cloudy' deliberately omitted for MVP.
WEATHER_STATES = ("clear", "raining", "snowing", "foggy")

# Season -> which weather states may occur. Uniform random within the set.
# This is the immersion guard (no summer snow). Swap for weighted tables
# in a later phase without touching the script or rooms.
SEASON_ALLOWED_WEATHER = {
    "spring": ("clear", "raining", "foggy"),
    "summer": ("clear", "raining", "foggy"),
    "autumn": ("clear", "raining", "foggy", "snowing"),
    "winter": ("clear", "snowing", "foggy"),  # snow over rain (honors "lots of snow")
}

# Broadcast on transition to a new state. Keyed by the NEW weather state.
WEATHER_MESSAGES = {
    "clear":   "The clouds part and the sky clears.",
    "raining": "Rain begins to fall.",
    "snowing": "Snow begins to drift down from the sky.",
    "foggy":   "A thick fog rolls in, dimming your surroundings.",
}


def roll_weather(season, current=None):
    """
    Pick a new weather state for the given season.

    Args:
        season (str): one of spring/summer/autumn/winter.
        current (str|None): current weather. UNUSED in v1 (pure random);
            kept in the signature as the extension point for inertia /
            front-simulation later, so adding it stays non-breaking.

    Returns:
        str: a weather state from WEATHER_STATES.
    """
    allowed = SEASON_ALLOWED_WEATHER.get(season, WEATHER_STATES)
    return random.choice(allowed)

def broadcast_weather_change(new_state):
    """
    Send the transition message for `new_state` to every online character
    who is currently outdoors.

    Deduped by character (multi-session players get one message). Global by
    design — weather is world-wide — but characters sheltered indoors (their
    room has db.is_indoor set truthy) do not hear it. A character with no
    location is treated as outdoors, preserving prior behavior.
    """
    message = WEATHER_MESSAGES.get(new_state)
    if not message:
        return
    # Imported here so this module stays import-light and Evennia-optional
    # for the pure-logic tests in Task 1.1.
    from evennia.server.sessionhandler import SESSIONS

    seen = set()
    for sess in SESSIONS.get_sessions():
        char = sess.puppet
        if not char or char.id in seen:
            continue
        seen.add(char.id)
        location = char.location
        if location and location.db.is_indoor:
            # Sheltered indoors: weather transitions aren't seen or heard here.
            continue
        char.msg(message)

def get_current_weather():
    """Return the global current weather, or 'clear' if unavailable."""
    from evennia import GLOBAL_SCRIPTS
    try:
        return GLOBAL_SCRIPTS.weather.db.current_weather or "clear"
    except Exception:
        return "clear"
