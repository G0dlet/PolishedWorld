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

# Per-regime comfort band (lo, hi) of worn warmth. A character is comfortable
# (zero stress) while their summed warmth sits within [lo, hi] inclusive; below
# lo they take cold stress, above hi heat stress, each graded by the gap.
#
#   lo == the warmth the climate demands. This is the old THERMAL_LOADS cold_load
#         unchanged, so cold-side behaviour is identical to before.
#   hi == the warmth tolerated before overheating. Replaces the old flat
#         COMFORT_MARGIN, which -- being regime-independent -- punished a correctly
#         dressed character: in cold you needed warmth 4 to stop shivering, yet a
#         flat margin of 2 meant that same warmth already overheated you, so no
#         outfit ever reached zero stress and a full winter kit (warmth ~7)
#         heat-stressed in the snow. A regime-relative ceiling fixes both.
#
# All numbers are tunable; start conservative and adjust empirically. Keep
# lo <= hi per regime, or the band is empty and every warmth value stresses.
COMFORT_BANDS = {
    #            (lo, hi)
    "cold":      (4, 8),   # needs real insulation; tolerates heavy layering
    "temperate": (1, 4),   # a light layer is comfortable; wide, forgiving band
    "hot":       (0, 1),   # comfortable near-naked; overheats fast under layers
}


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

    Each regime defines a comfort band [lo, hi] of worn warmth: dress below it
    and you take cold stress, above it heat stress, inside it neither. A
    correctly dressed character is therefore comfortable, and the two are
    mutually exclusive whenever the band is non-empty. These become buff stacks
    in the survival ticker (Task A.3).

    Returns:
        tuple[int, int]: (cold_stress, heat_stress).
    """
    # Unknown regime -> a permissive band (never stress) is the safe failure mode
    # in a live game; thermal_regime only ever returns the three keys above.
    lo, hi = COMFORT_BANDS.get(regime, (0, 999))
    cold_stress = max(0, lo - worn_warmth)            # underdressed for the climate
    heat_stress = max(0, worn_warmth - hi)            # overdressed for the climate
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
