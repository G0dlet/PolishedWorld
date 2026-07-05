"""
Garment wear ticker: worn clothing slowly loses condition, driven by exposure.

Registered with Evennia's TICKER_HANDLER (see server/conf/at_server_startstop.py),
mirroring the survival ticker: a single module-level callable iterates all
currently puppeted characters and degrades what they are wearing. Module-level
(not a closure) so the callback is picklable, which persistent tickers require.

Model (adapted from Arms of Legend "Armour Wear Values", 1-2 AP row):
AoL's wear levels are *exposure* levels -- Protected = in storage, Rigorous =
worn day and night in harsh conditions. We derive the level from the wearer's
environment (thermal regime + shelter) and let each garment carry a baseline
`db.wear_level` (default "common") that the environment shifts. Condition drops
by a whole-integer rate per tick; at the intended prod interval of 12 game-hours
a common-worn garment lasts ~3.6 game-weeks, a rigorous one ~1.8.

Sampling: wear reads the wearer's exposure at tick time, not a time-weighted
average over the interval. A player who crosses several climates between ticks
is charged only for the climate they are in the moment the tick fires. Because
tick timing is uncorrelated with player movement, sampled exposure converges to
the true time-averaged exposure over a garment's lifetime (~25 ticks for common,
~100 for basic); the per-tick variance is deliberate, not a bug. A side benefit:
weather and season changes are sampled for free, with no hook into WeatherScript.
If playtesting shows this feels unfair, switch to a per-garment fractional
accumulator (float db.wear_accum) updated on a finer tick, subtracting whole
condition points only as it crosses 1.0 -- deferred until a real need appears.

Offline characters are never touched: no session, so they never enter the loop,
exactly like survival depletion.
"""

from evennia import SESSION_HANDLER
from evennia.utils import logger
from world.thermal import thermal_regime

# Wear levels, gentlest -> harshest. Index arithmetic below relies on this order.
TIER_ORDER = ("protected", "basic", "common", "rigorous")

# Condition points lost per worn garment per tick, by effective wear level.
# Lifted from AoL's 1-2 AP row at AP=2 (Protected 20w / Basic 10w / Common 4w /
# Rigorous 2w between repairs); tuned to whole integers at a 12 game-hour tick.
# All tunable -- change these together with WEAR_TICK_INTERVAL if you retune.
WEAR_RATES = {
    "protected": 0,   # sheltered / indoor: AoL "in storage or on display"
    "basic":     1,   # ~7 game-weeks to wear out
    "common":    2,   # ~3.6 game-weeks -- the normal outdoor adventuring life
    "rigorous":  4,   # ~1.8 game-weeks -- cold/hot extremes, day and night
}

# Downward-crossing warnings, worst-first. On a tick where condition falls from
# above `threshold` to at-or-below it, the wearer is told once (no per-tick spam,
# because the crossing only happens on one tick). First match wins, so a big drop
# that skips both thresholds reports the worse one.
WEAR_WARNINGS = (
    (10, "|rYour {name} needs urgent repair -- nearly worn through.|n"),
    (25, "|yYour {name} could use some repair.|n"),
)


def wear_all_garments():
    """
    Tick callback: degrade worn garments for every online character.

    Iterates logged-in sessions only, skips OOC sessions (puppet is None), and
    dedupes characters with multiple sessions so a character's clothes are never
    degraded twice in one tick -- identical to the survival ticker's enumeration.
    """
    seen = set()
    for sess in SESSION_HANDLER.get_sessions():
        char = getattr(sess, "puppet", None)
        if not char or char.id in seen:
            continue
        seen.add(char.id)
        _wear_character(char)


def _wear_character(char):
    """
    Degrade every worn ClothingWithBuffs on `char` by its exposure-adjusted rate.

    The environment (regime + shelter) is read once per character, since every
    garment shares the wearer's room. Only ClothingWithBuffs carry a condition;
    plain contrib garments are skipped so we never invent a condition on an item
    the durability system doesn't own.
    """
    # Lazy imports keep this module import-light (mirrors thermal.py's pattern)
    # and avoid any import-order coupling with the clothing typeclass at load.
    from evennia.contrib.game_systems.clothing.clothing import get_worn_clothes
    from typeclasses.clothing import ClothingWithBuffs

    try:
        room = char.location
        indoor = bool(room.db.is_indoor) if room else False
        # Exposure is sampled here at tick time, not averaged over the interval
        # (see module docstring "Sampling"): a snapshot of the current room.
        regime = thermal_regime(room)   # handles room=None -> "temperate"

        for garment in get_worn_clothes(char):
            if not isinstance(garment, ClothingWithBuffs):
                continue
            tier = _effective_tier(garment, indoor, regime)
            _wear_one(garment, char, tier)
    except Exception:
        # One bad character/room must never kill the ticker for everyone else.
        logger.log_trace()


def _effective_tier(garment, indoor, regime):
    """
    Resolve a garment's effective wear level from its baseline plus environment.

    Baseline is db.wear_level (default "common"); an unknown value falls back to
    "common" rather than erroring in a live tick. Indoors shifts two steps toward
    Protected (fully out of the elements); an extreme outdoor regime (cold/hot)
    shifts one step toward Rigorous. The result is clamped to the tier range.
    """
    base = garment.db.wear_level or "common"
    idx = TIER_ORDER.index(base) if base in TIER_ORDER else TIER_ORDER.index("common")

    if indoor:
        idx -= 2                       # sheltered: markedly gentler wear
    elif regime in ("cold", "hot"):
        idx += 1                       # exposed to the extremes: harsher wear

    idx = max(0, min(idx, len(TIER_ORDER) - 1))
    return TIER_ORDER[idx]


def _wear_one(garment, wearer, tier):
    """
    Subtract this tier's rate from one garment's condition, warn on threshold cross.

    condition is read raw (db.condition) and defaulted to 100 when absent, so a
    ClothingWithBuffs created before H6.1 is backfilled the first time it wears
    rather than crashing. Rate 0 (protected) is a pure no-op -- no DB write. Floor
    at 0; condition never goes negative.
    """
    rate = WEAR_RATES.get(tier, 0)
    if rate <= 0:
        return

    current = garment.db.condition
    if current is None:
        current = 100
    new = max(0, current - rate)
    garment.db.condition = new

    name = garment.get_display_name(wearer)
    for threshold, template in WEAR_WARNINGS:
        if current > threshold >= new:      # crossed downward through threshold
            wearer.msg(template.format(name=name))
            break
