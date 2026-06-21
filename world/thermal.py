# world/thermal.py
"""
Thermal comfort model: clothing vs climate.

This module is pure logic with no global ticker of its own. It exposes:

    thermal_regime(room)            -> "cold" | "temperate" | "hot"
    thermal_stress(regime, warmth)  -> (cold_stress, heat_stress)
    worn_warmth(character)          -> int

The survival ticker (Task A.3) calls these per character each tick: it reads
the character's regime, sums their worn warmth, and turns the resulting stress
into stacks on two silent buffs (ColdStress / HeatStress). Clothing pieces only
carry a db.warmth value — there are no per-garment buffs.

Design: the *penalty depends on the gap* between how warmly you are dressed and
what the climate demands. Warmth helps in cold, hurts when overdressed, and the
mismatch is graded — full winter gear is penalised in a temperate room, just
less than in a hot one. All numbers below are tunable; start conservative and
adjust empirically.
"""

# Per-regime ambient loads, as (cold_load, heat_load).
#   cold_load  = how much warmth the climate demands (underdressing -> cold stress)
#   heat_load  = baseline heat burden (overdressing pushes past COMFORT_MARGIN)
THERMAL_LOADS = {
    "cold":      (4, 0),
    "temperate": (1, 1),
    "hot":       (0, 3),
}

# Warmth you can carry before any heat stress accrues. Lets light clothing in a
# temperate room sit at zero stress (comfortable) rather than mildly penalised.
COMFORT_MARGIN = 2


def thermal_regime(room):
    """
    Determine the thermal regime a character in `room` experiences.

    Priority (most specific wins):
        1. room.db.thermal_regime  -- explicit microclimate pin (heated tavern
           -> "hot", frozen glade -> "cold").
        2. is_indoor               -- sheltered with no pin -> always temperate.
        3. effective room_states   -- derived from pinned-or-current season and
           weather. 'clear' is never present here, so we test only the regime-
           bearing states.

    Returns:
        str: "cold", "temperate", or "hot". A None room is treated as temperate.
    """
    if room is None:
        return "temperate"

    pinned = room.db.thermal_regime
    if pinned:
        return pinned

    if room.db.is_indoor:
        return "temperate"

    states = set(room.room_states)  # effective season + weather, honours pins

    # Snow can fall in autumn too, so snowing implies cold regardless of season.
    if "winter" in states or "snowing" in states:
        return "cold"
    # MVP: summer is hot regardless of weather. A future refinement could require
    # clear skies for peak heat, or soften hot when it is raining/foggy.
    if "summer" in states:
        return "hot"
    return "temperate"


def thermal_stress(regime, worn_warmth):
    """
    Convert (regime, worn warmth) into one-sided cold and heat stress values.

    Both are clamped at zero — you are either under- or over-dressed for a given
    climate, not both. These become buff stacks in Task A.3.

    Returns:
        tuple[int, int]: (cold_stress, heat_stress).
    """
    cold_load, heat_load = THERMAL_LOADS.get(regime, (0, 0))
    cold_stress = max(0, cold_load - worn_warmth)                     # underdressed
    heat_stress = max(0, worn_warmth + heat_load - COMFORT_MARGIN)    # overdressed
    return cold_stress, heat_stress


def worn_warmth(character):
    """
    Sum the db.warmth of everything `character` is currently wearing.

    Covered layers count: a shirt under a coat still insulates. Garments without
    a warmth value contribute 0. Works whether or not the clothing contrib's
    typeclasses are installed -- get_worn_clothes only inspects db.worn.
    """
    # Lazy import keeps this module import-light (mirrors weather.py's pattern).
    from evennia.contrib.game_systems.clothing.clothing import get_worn_clothes

    return sum((garment.db.warmth or 0) for garment in get_worn_clothes(character))


def apply_thermal_stress(character):
    """
    Recompute and apply the character's thermal stress buffs.

    Called by the survival ticker each tick (before gauges deplete) and, later,
    by the clothing wear/remove hooks for immediate feedback. Sets ColdStress and
    HeatStress to exact stack counts from the character's regime and worn warmth.
    Either may be zero, in which case that buff is removed.
    """
    from world.survival_buffs import ColdStress, HeatStress

    regime = thermal_regime(character.location)
    warmth = worn_warmth(character)
    cold_stress, heat_stress = thermal_stress(regime, warmth)

    _set_stress(character, ColdStress, cold_stress)
    _set_stress(character, HeatStress, heat_stress)


def _set_stress(character, buffclass, stacks):
    """
    Set a stress buff to an exact stack count.

    buffs.add() *increments* stacks on an existing buff (verified against the
    contrib), so we always remove() first to reset, then add() the fresh count.
    remove() no-ops if absent. Stress of 0 leaves the buff removed. The buffs are
    silent, so the per-tick remove/add churn produces no message spam.
    """
    character.buffs.remove(buffclass.key)
    if stacks >= 1:
        character.buffs.add(buffclass, stacks=stacks)
