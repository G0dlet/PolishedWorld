"""
Global survival ticker callback.

Registered with Evennia's TICKER_HANDLER (see server/conf/at_server_startstop.py).
A single module-level callable iterates all currently puppeted characters and
applies survival depletion. Module-level (not a closure/lambda) so the callback
is picklable, which TICKER_HANDLER requires for persistent tickers.

This task (1.2) only enumerates + logs; depletion lands in Task 2.1.
"""

from evennia import SESSION_HANDLER
from evennia.utils import logger

# Base depletion per tick, before buff modifiers. Tunable.
# Thirst bites faster than hunger (loosely echoes Legend: thirst in hours,
# starvation in days). Fatigue slowest — most of its pressure comes later
# from activity, not idle time.
BASE_RATES = {"hunger": 1, "thirst": 2, "fatigue": 1}

def deplete_all_survival_traits():
    """
    Tick callback: deplete survival gauges for every online character.

    Iterates logged-in sessions only (get_sessions() filters on logged_in),
    skips logged-in-but-OOC sessions (puppet is None), and dedupes characters
    that have more than one session connected (multisession modes 2-3) so a
    character is never depleted twice in a single tick.

    Offline characters are never touched: they have no session, so they do
    not appear in this loop and take no depletion or damage while logged out.
    """
    seen = set()
    for sess in SESSION_HANDLER.get_sessions():
        char = getattr(sess, "puppet", None)
        if not char or char.id in seen:
            continue
        seen.add(char.id)
        _deplete_character(char)


def _deplete_character(char):
    """
    Deplete one character's hunger/thirst/fatigue by the buff-modified
    base rate. Separated from the loop for readability and so it can be
    called directly on a single character in @py tests.
    """
    for key, base in BASE_RATES.items():
        trait = char.traits.get(key)
        if trait is None:
            # Defensive: a character missing a survival gauge shouldn't
            # crash the whole tick for everyone else.
            continue
        rate = char.buffs.check(base, f"{key}_rate")
        trait.current -= rate
