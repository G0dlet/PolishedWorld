"""
Global survival ticker callback.

Registered with Evennia's TICKER_HANDLER (see server/conf/at_server_startstop.py).
A single module-level callable iterates all currently puppeted characters and
applies survival depletion and natural healing (world/healing.py). Module-level (not a closure/lambda) so the callback
is picklable, which TICKER_HANDLER requires for persistent tickers.
"""

from evennia import SESSION_HANDLER
from evennia.utils import logger
from world.survival_buffs import Starving, Dehydrated
from world.thermal import apply_thermal_stress
from world import client_state, fatigue, gametime_utils, healing

# Base depletion per tick, before buff modifiers. Tunable.
# Thirst bites faster than hunger (loosely echoes Legend: thirst in hours,
# starvation in days). Fatigue slowest — most of its pressure comes later
# from activity, not idle time.
BASE_RATES = {"hunger": 1, "thirst": 2, "fatigue": 1}

# HP lost per tick while a starvation/dehydration condition is active.
# Integer on purpose: health.base is an int (con*2), so a fractional value
# would risk the same round()-to-even "stuck" behavior we hit with fatigue.
STARVE_DAMAGE = 1

# (gauge key, condition buff) pairs that damage health at zero.
# Fatigue is deliberately absent: in Legend, exhaustion is unconsciousness /
# skill penalties, not location damage. Fatigue consequences are deferred to
# the skill-check resolver.
HEALTH_CONDITIONS = (
    ("hunger", Starving),
    ("thirst", Dehydrated),
)

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
    Recompute thermal stress, deplete gauges, apply zero-conditions, heal,
    warn.

    Healing runs after the conditions (S2.1), so a Starving or Dehydrated
    condition applied this tick already stops it, and a character the
    conditions just killed and respawned at full health only has their
    counter zeroed.
    """
    elapsed = _tick_game_seconds(char)
    apply_thermal_stress(char)
    for key, base in BASE_RATES.items():
        trait = char.traits.get(key)
        if trait is None:
            continue
        rate = char.buffs.check(base, f"{key}_rate")
        trait.current -= rate
    _apply_survival_conditions(char)
    if healing.accrue(char, elapsed):
        char.msg(healing.HEALED)
    _check_survival_warnings(char)
    # W4.2: after the warnings, so the text and the panel agree. `world`
    # rides along: Evennia's clock only runs while the server does (WC9).
    client_state.push(char, "survival", "world")


def _tick_game_seconds(char):
    """
    Game seconds since this character's previous tick, then stamp now.

    The stamp lives in ndb, so a reload loses it, and
    `Character.at_post_puppet` clears it (Evennia keeps ndb on a cached
    object through an unpuppet): the first tick after either returns 0.
    At most one tick's time is lost, never a span gained -- time away is
    S2.2's, credited at login. A clock that reads earlier than the stamp
    returns 0 rather than a negative span.

    Returns:
        int: game seconds, 0 or more.
    """
    now = gametime_utils.get_absolute_gametime()
    last = char.ndb.survival_tick_at
    char.ndb.survival_tick_at = now
    if last is None:
        return 0
    return max(0, now - last)


def _apply_survival_conditions(char):
    """
    Apply or clear starvation/dehydration conditions, then route the summed
    damage through the death chokepoint.

    At gauge minimum: ensure the condition buff is present (at_apply fires its
    onset message once, thanks to the has() guard) and accrue STARVE_DAMAGE.
    Above minimum: remove() the condition by key (no-ops if absent, only fires
    at_remove the tick it actually clears).

    We SUM across conditions and make a SINGLE apply_health_damage call. This
    keeps "one fatal tick -> one corpse" correct independently of two other
    facts (the reset-on-respawn in at_character_death, and the <=min guard in
    apply_health_damage): a per-condition reroute would only stay single-death
    by accident of those, and would silently start double-killing the day either
    changed. Summation makes the intent explicit -- a character both starving
    and dehydrated takes 2 damage and dies once.
    """
    total_damage = 0
    for key, buffclass in HEALTH_CONDITIONS:
        trait = char.traits.get(key)
        if trait is None:
            continue
        if trait.current <= trait.min:
            if not char.buffs.has(buffclass):
                char.buffs.add(buffclass)
            total_damage += STARVE_DAMAGE
        else:
            char.buffs.remove(buffclass.key)

    if total_damage:
        char.apply_health_damage(total_damage, source="survival")

def _check_survival_warnings(char):
    """
    Message the character only when a gauge drops into a *worse* descs bucket.

    Fatigue's bucket is Legend's level and its word `fatigue_desc()` (S3.1),
    both from world/fatigue.py, never the gauge's stored `descs`: characters
    made before S3.1 store the old table. Hunger and thirst keep their own.

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
        if key == "fatigue":
            idx = fatigue.level_for(trait.value)
        else:
            idx = _bucket_index(trait)
        if idx is None:
            continue
        prev = last.get(key)
        if prev is not None and idx < prev:
            # dropped into a worse bucket -> warn
            word = char.fatigue_desc() if key == "fatigue" else trait.desc()
            char.msg(f"|yYou feel {word}.|n")
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
