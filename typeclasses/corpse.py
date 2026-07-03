"""
Corpse typeclass -- harvestable remains of a hunted creature.

A Corpse is spawned by Creature.at_death() (Task H3.2) and bridges hunting (H2)
to harvesting (H4). It stores the dead creature's data and computes its decay
stage *lazily*, on demand -- the same pattern as ResourceNode regeneration, with
no per-corpse ticker. State is derived from elapsed in-game time whenever a
player looks at or harvests it, so an idle corpse costs nothing.

Decay timeline (game-hours, from PolishedWorld_Creature_Harvesting_Design.md;
the world runs at 4x real time, so these are ~1/4 as long in real hours):

    fresh    0-12h    all parts, full quality
    stale    12-48h   soft parts degrading
    rotting  48-96h   soft parts mostly gone, hard parts remain
    skeleton 96h+     only bones

Environmental modifiers scale how fast game-time counts against those thresholds
(cold slows it, heat/rain speed it up), read live from the current season and
global weather every time decay is queried.
"""

from evennia import AttributeProperty
from evennia.objects.objects import DefaultObject

from world import gametime_utils
from world import weather as weather_logic
from .objects import ObjectParent


# Decay stage indices.
FRESH, STALE, ROTTING, SKELETON = 0, 1, 2, 3
_STAGE_NAMES = {FRESH: "fresh", STALE: "stale", ROTTING: "rotting", SKELETON: "skeletal"}

# Game-hour thresholds for stage transitions: fresh->stale, stale->rotting,
# rotting->skeleton. Straight from the harvesting design's decay timeline.
_DECAY_THRESHOLDS_HOURS = (12, 48, 96)

# Game-hours after death at which even the skeleton is spent and the corpse
# should be cleaned up: 96 (skeleton onset) + 48 (linger window) = 144.
_CORPSE_EXPIRY_HOURS = 144

_SECONDS_PER_GAME_HOUR = 3600

# Environmental decay-rate multipliers (multiplied together). Values from the
# harvesting design's environmental modifier table. Seasons/weather not listed
# here are neutral (1.0).
_SEASON_MODIFIERS = {"winter": 0.5, "summer": 2.0}      # spring/autumn -> 1.0
_WEATHER_MODIFIERS = {"raining": 1.5, "snowing": 0.5}   # clear/foggy   -> 1.0


class Corpse(ObjectParent, DefaultObject):
    """
    The harvestable corpse of a hunted creature.

    Carries the dead creature's SIZ and harvest template (so H4 knows which parts
    it yields and how much), the in-game time of death, and a record of which
    parts have already been taken. Decay stage is *computed*, never stored as
    live state, so it is always correct without a ticker.
    """

    # --- Stored data --------------------------------------------------------
    # autocreate=True so every corpse has real db rows the harvest code reads
    # without None-guards. Defaults match the rabbit (the only creature so far).
    creature_type = AttributeProperty(default="rabbit", autocreate=True)
    creature_siz = AttributeProperty(default=4, autocreate=True)
    creature_natural_ap = AttributeProperty(default=0, autocreate=True)
    # Absolute in-game seconds at death. H3.2 MUST set this with the SAME
    # accessor (gametime_utils.get_absolute_gametime) so the diff is meaningful.
    death_time = AttributeProperty(default=0, autocreate=True)
    # {part_key: True} for parts already harvested. H4 atomic-claims into this.
    harvested = AttributeProperty(default=dict, autocreate=True)

    def at_object_creation(self):
        """Lock the corpse against pickup and default its time of death."""
        super().at_object_creation()
        # A whole carcass is not pocket loot -- you harvest parts from it in
        # place (H4). Mirrors Creature's get-lock and the design's "can't pick
        # up corpses normally".
        self.locks.add("get:false()")
        # Default death to "now" unless a caller already supplied it (H3.2 passes
        # it via create_object attributes). Guard against clobbering an explicit
        # value: passed attributes and at_object_creation can run in either order
        # depending on create path, and `not <nonzero>` keeps the real time.
        if not self.db.death_time:
            self.db.death_time = gametime_utils.get_absolute_gametime()

    # --- Lazy decay ---------------------------------------------------------

    @property
    def decay_modifier(self):
        """
        Live multiplier on decay speed (>1 faster, <1 slower) from season +
        global weather, plus an optional cold-storage room flag. Never cached, so
        a corpse moved from a summer field into a cold cellar slows immediately.
        """
        modifier = 1.0
        # Season: spring/autumn are neutral and simply absent from the map.
        modifier *= _SEASON_MODIFIERS.get(gametime_utils.get_season(), 1.0)
        # Weather is global in PolishedWorld (no per-room argument).
        modifier *= _WEATHER_MODIFIERS.get(weather_logic.get_current_weather(), 1.0)
        # Opt-in cold storage (unset attribute -> None -> falsy -> skipped).
        if self.location and self.location.db.is_cold_storage:
            modifier *= 0.25
        return modifier

    def _elapsed_game_hours(self):
        """
        Effective game-hours since death, scaled by the live decay modifier.

        max(0, ...) guards against a death_time in the apparent future (e.g. a
        gametime reset), clamping to "just died" rather than going negative.
        """
        now = gametime_utils.get_absolute_gametime()
        raw_hours = max(0, now - int(self.db.death_time)) / _SECONDS_PER_GAME_HOUR
        return raw_hours * self.decay_modifier

    @property
    def decay_stage(self):
        """Decay stage 0 (fresh) .. 3 (skeleton), computed on demand. No ticker."""
        hours = self._elapsed_game_hours()
        stage = FRESH
        for threshold in _DECAY_THRESHOLDS_HOURS:
            if hours >= threshold:
                stage += 1
            else:
                break
        return stage  # 3 thresholds -> naturally bounded at SKELETON (3)

    @property
    def decay_stage_name(self):
        """Human-readable decay stage ('fresh' .. 'skeletal')."""
        return _STAGE_NAMES[self.decay_stage]

    @property
    def is_expired(self):
        """
        True once even the skeleton has lingered out its window. Lets interaction
        code (look/harvest in H4) lazily delete spent corpses -- the no-ticker
        equivalent of the design's "crumbles to dust" cleanup.
        """
        return self._elapsed_game_hours() >= _CORPSE_EXPIRY_HOURS

    # --- Appearance ---------------------------------------------------------

    def return_appearance(self, looker, **kwargs):
        """Append the current decay state to the corpse's description."""
        appearance = super().return_appearance(looker, **kwargs)
        return f"{appearance}\nIt looks {self.decay_stage_name}."


class PlayerCorpse(Corpse):
    """
    The remains of a dead player character.

    Inherits Corpse's lazy, tickerless decay wholesale: Corpse.at_object_creation
    stamps death_time (gametime_utils.get_absolute_gametime), locks the carcass
    against pickup (get:false()), and decay_stage/is_expired compute on demand.
    Unlike a creature Corpse it holds the player's REAL dropped objects, looted
    individually via ordinary get-locks -- not harvestable parts.

    Inherited creature_type/creature_siz defaults (rabbit/4) are meaningless here
    but harmless: no player-corpse code path reads them. H7.1 keeps this class
    minimal; H7.3 adds the longer recovery window and the return_appearance
    expiry sink (crumble + delete contents).
    """

    # Distinguishes player corpses from creature corpses for search/loot rules.
    # autocreate=True so lookups never hit a None-guard.
    is_player_corpse = AttributeProperty(default=True, autocreate=True)
