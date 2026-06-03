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
    """Deplete one character's survival gauges, then check for worsening warnings."""
    for key, base in BASE_RATES.items():
        trait = char.traits.get(key)
        if trait is None:
            continue
        rate = char.buffs.check(base, f"{key}_rate")
        trait.current -= rate
    _check_survival_warnings(char)


def _check_survival_warnings(char):
    """
    Message the character only when a gauge drops into a *worse* descs bucket.

    Previous bucket indices are tracked in non-persistent char.ndb, so this
    costs no DB writes and resets harmlessly on reload (baseline re-established
    silently on the next tick). Recovery messages are handled by the eat/drink/
    rest commands, not here.
    """
    last = char.ndb.survival_buckets
    if last is None:
        last = {}

    for key in BASE_RATES:
        trait = char.traits.get(key)
        if trait is None:
            continue
        idx = _bucket_index(trait)
        if idx is None:
            continue
        prev = last.get(key)
        if prev is not None and idx < prev:
            # dropped into a worse bucket -> warn
            char.msg(f"|yYou feel {trait.desc()}.|n")
        last[key] = idx

    char.ndb.survival_buckets = last

def _bucket_index(trait):
    """
    Return the index of the descs bucket the trait's value currently falls in.

    Mirrors GaugeTrait.desc(): descs is an ordered {upper_bound_inclusive: text}
    map, small->big. The first bucket (lowest bound) is the *worst* state, so a
    lower index means a worse condition. Returns None if the trait has no descs.

    Indexing by position (not by label string) avoids ambiguity if two buckets
    ever share the same label.
    """
    descs = trait.descs
    if not descs:
        return None
    value = trait.value
    for i, bound in enumerate(descs.keys()):
        if value <= bound:
            return i
    return len(descs) - 1   # above the highest bound = best/last bucket
