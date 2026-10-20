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

    def _raw_elapsed_game_hours(self):
        """
        Unscaled game-hours since death. Monotone: it only grows while the
        server runs, and it stands still while the server is down (the game
        clock is runtime-based).

        Decay does not read this directly -- it reads `_elapsed_game_hours()`.
        Anything that needs a clock the weather cannot turn back (the owner's
        loot grace on PlayerCorpse) reads this one.

        max(0, ...) guards against a death_time in the apparent future (e.g. a
        gametime reset), clamping to "just died" rather than going negative.
        """
        now = gametime_utils.get_absolute_gametime()
        return max(0, now - int(self.db.death_time)) / _SECONDS_PER_GAME_HOUR

    def _elapsed_game_hours(self):
        """
        Effective game-hours since death, scaled by the live decay modifier.

        The whole elapsed span is multiplied by the modifier as it is *now*, so
        this value can fall when the weather turns colder. That is acceptable
        for "how rotten does it look", and it is why nothing that must never
        run backwards is built on it (see `_raw_elapsed_game_hours`).
        """
        return self._raw_elapsed_game_hours() * self.decay_modifier

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
        True once even the skeleton has lingered out its window -- the no-ticker
        equivalent of the design's "crumbles to dust" cleanup.

        This property *decides*; it never deletes. The callers that act on it
        (look, harvest, a player entering the room, the ambient sweeper NPC)
        all hand the deletion to `crumble()`, the single writer for expiry.
        """
        return self._elapsed_game_hours() >= _CORPSE_EXPIRY_HOURS

    # --- Expiry -------------------------------------------------------------

    def crumble(self):
        """
        Destroy this corpse and everything inside it. The single writer (P-2)
        for corpse expiry.

        Callers decide *whether* the corpse has expired (`is_expired`); this
        method only carries that decision out, and it is the only code that
        does. Three call sites reach it and do nothing else:
        `PlayerCorpse.return_appearance` (look), `CmdHarvest` step 4 (harvest)
        and `Room.at_object_receive` (a player entering the room). There is no
        ticker.

        Contents are deleted *before* the body. `DefaultObject.delete()` does
        not delete what an object holds: `clear_contents()` teleports each item
        to its `home`. Deleting the body first therefore relocates the loot
        instead of destroying it -- the bug harvest had before this method
        existed.

        The room line is decided by state, not by which path called: the
        "lost with it" clause appears only when something was actually held.
        It is true today because a corpse holds only items. The death policy
        (roadmap, Death-consequence policy (ii)) says currency is never
        deleted, so once a `CoinPile` can lie in a corpse (Stage 5) this method
        must sweep it instead of deleting it, and the clause must stop claiming
        coin is lost (BACKLOG: `CoinPile` vs the corpse's atomic content delete).

        Multiplayer note: commands run one at a time on the reactor, so the
        risk is not parallel deletion but a stale reference -- a look and a
        harvest, or a sweep, reaching an instance that is already gone. A
        second `delete()` on the same instance raises `ObjectDoesNotExist`, and
        `is_expired` on it raises (its Attributes are cleared). The pk check
        comes first and turns a repeated call into a quiet no-op.

        Returns:
            bool: True if the corpse crumbled, False if it was already deleted.
        """
        if not self.pk:
            return False
        contents = list(self.contents)
        if self.location:
            held = ", and what it held is lost with it" if contents else ""
            self.location.msg_contents(
                f"|xThe {self.key} finally crumbles to dust{held}.|n"
            )
        # Contents first, then the carcass (see docstring). Per-item decay
        # (loot lingering after the body is gone) is a BACKLOG refinement; it
        # would land here, once.
        for obj in contents:
            obj.delete()
        self.delete()
        return True

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

    Inherited creature_type/creature_siz defaults (rabbit/4) are meaningless here,
    and autocreate stores them on every player corpse. They stay harmless only
    because CmdHarvest refuses on is_player_corpse right after its expiry check,
    before any template lookup reads them. H7.1 keeps this class
    minimal; H7.3b adds the loot-access lock (get_from) and the CmdContainerGet
    integration.
    """

    # Distinguishes player corpses from creature corpses: CmdHarvest refuses
    # on it. autocreate=True stores True on every PlayerCorpse; a creature
    # Corpse has no such Attribute, so `corpse.db.is_player_corpse` is None
    # there -- the falsy answer the harvest guard relies on.
    is_player_corpse = AttributeProperty(default=True, autocreate=True)

    # Player loot deserves a more forgiving recovery window than a rabbit
    # carcass (144h). The visual decay pace is INHERITED unchanged (skeletal at
    # 96h); only the cleanup window extends, so the corpse -- and the loot it
    # still holds -- lingers as a skeleton until this point, giving a dead player
    # time to run back, with the first claim theirs (_PLAYER_GRACE_HOURS below).
    # Env-scaled like all decay (cold slows it, heat speeds it), so the player
    # contract promises "days", never this number.
    _PLAYER_EXPIRY_HOURS = 288

    # Owner-first loot grace (roadmap, Death-consequence policy (iii)): for this
    # many game-hours after death only the owner may take from the corpse; then
    # anyone may. A calibration knob, not a contract term. UNSCALED game-hours
    # (`_raw_elapsed_game_hours`), so a cold snap can never re-lock an opened
    # corpse. 72 = 3 game days = 18 real hours at TIME_FACTOR 4, a quarter of
    # the neutral recovery window. It must stay below the FASTEST possible
    # expiry (288 / 3.0 in summer rain = 96), or a body could crumble before
    # anyone but its owner may touch it; tests/test_death_contract.py derives
    # that bound from the modifier tables.
    _PLAYER_GRACE_HOURS = 72

    def at_object_creation(self):
        """Inherit the carcass get-lock + death stamp, then lock looting owner-first."""
        super().at_object_creation()   # get:false() + death_time default
        # Owner-first looting via CmdContainerGet's get_from check. This is a
        # DIFFERENT lock from the inherited get:false(): get_from governs taking
        # items OUT of the corpse, get governs pocketing the carcass itself.
        # corpse_grace() (server/conf/lockfuncs.py) reads `owner` and the clock
        # at access time, so the lock string never changes and nothing has to
        # fire when the grace ends.
        self.locks.add("get_from:corpse_grace()")
        # The command prints this on refusal and is the only writer of that line
        # (the lockfunc stays silent). Static on purpose: the time left is shown
        # by `look`, which can compute it.
        self.db.get_from_err_msg = (
            "That body's belongings are still its owner's to reclaim. "
            "You can't take from it yet."
        )

    @property
    def grace_active(self):
        """True while only the owner may loot. Unscaled clock: never re-locks."""
        return self._raw_elapsed_game_hours() < self._PLAYER_GRACE_HOURS

    @property
    def is_expired(self):
        """Override the base 144h window with the longer player recovery window."""
        return self._elapsed_game_hours() >= self._PLAYER_EXPIRY_HOURS

    def return_appearance(self, looker, **kwargs):
        """
        Lazy expiry trigger + loot display + the owner's claim.

        On look: if the corpse has lingered past its recovery window, it -- and
        every item still inside -- crumbles away via `crumble()`, the single
        writer for expiry. This is one of three no-ticker triggers for the loot
        sink (harvest and a player entering the room are the others): items not
        recovered in time are destroyed with the body. (Coin is not an item in a
        corpse today; when it becomes one in Stage 5 it is swept, never
        destroyed -- see `crumble()`.) Otherwise we defer to the inherited
        appearance, which already lists contents via the {things} template
        slot, so a looter sees exactly what is left to take without needing
        CmdContainerLook. While the owner's grace runs, one line says whose
        claim it is and roughly how long it lasts -- the time-left half of the
        refusal that `get_from_err_msg` cannot carry.

        Multiplayer note: the first trigger past expiry crumbles the corpse;
        a later look/get finds nothing (a graceful "not found"), and a stale
        reference reaching `crumble()` again is a no-op, never a half-deleted
        corpse or a second delete.
        """
        if self.is_expired:
            self.crumble()
            return ""
        appearance = super().return_appearance(looker, **kwargs)
        if not self.grace_active:
            return appearance
        # Local import: world.death_contract imports this module.
        from world.death_contract import format_game_span

        left = self._PLAYER_GRACE_HOURS - self._raw_elapsed_game_hours()
        whose = "Your" if looker.id == self.db.owner else "Its owner's"
        return (
            f"{appearance}\n{whose} claim on what it holds lasts about "
            f"{format_game_span(left)} more."
        )
