"""
typeclasses/resources.py
========================

Resource nodes for player-driven gathering (foraging, water sources).

Design: lazy simulation.
    A node never runs a ticker. It stores a `last_regen` timestamp
    (absolute game-seconds, via gametime_utils) and computes how much has
    regenerated on-demand, the moment a player interacts with it. Idle
    cost is zero regardless of how many nodes exist.

    Two interaction shapes:
      * Forageable node (e.g. berry bush): finite `available`, regenerates
        one unit per `regen_interval` game-seconds up to `max_yield`.
        Harvested via the `forage` command, which spawns `yield_prototype`.
      * Water source (e.g. spring): `is_water_source=True`. Effectively
        infinite; never depletes or regenerates. Recognised by the
        `refill` command to top up refillable Drink containers.

Persistence:
    Attributes use AttributeProperty(autocreate=False). Verified against
    evennia source: reading an unset attribute then returns the default
    WITHOUT a DB write, so read-only queries (get_available) never touch
    the DB; only state changes (harvest) persist.
"""

from evennia.typeclasses.attributes import AttributeProperty
from world.gametime_utils import get_absolute_gametime

# Assumes the standard Evennia game template typeclasses/objects.py with an
# `Object` base. If your base is named differently, adjust this import.
from typeclasses.objects import Object


class ResourceNode(Object):
    """A lazily-simulated, player-harvestable resource in the world."""

    # --- configuration (typically set per-prototype) ---
    resource_type = AttributeProperty("generic", autocreate=False)
    max_yield = AttributeProperty(5, autocreate=False)
    regen_interval = AttributeProperty(3600, autocreate=False)   # game-seconds / unit
    yield_prototype = AttributeProperty(None, autocreate=False)  # prototype spawned on harvest
    is_water_source = AttributeProperty(False, autocreate=False)

    # --- mutable state ---
    available = AttributeProperty(5, autocreate=False)
    last_regen = AttributeProperty(0, autocreate=False)          # absolute game-seconds

    def at_object_creation(self):
        super().at_object_creation()
        # CRITICAL: anchor last_regen to "now" at creation. Left at the
        # default 0, a non-full node would diff against the epoch and
        # instantly appear full on its first access.
        self.last_regen = get_absolute_gametime()
        # World fixtures: a player must not be able to pick up a bush/spring.
        self.locks.add("get:false()")

    # ------------------------------------------------------------------
    # Lazy regeneration core
    # ------------------------------------------------------------------

    def _update_regen(self, now, persist=True):
        """
        Bring `available` up to date for elapsed time.

        Args:
            now (int): absolute game-seconds (from get_absolute_gametime()).
            persist (bool): if False, return the projected value WITHOUT
                writing to the DB (read-only path).

        Returns:
            int | None: projected available amount; None for water sources.
        """
        if self.is_water_source:
            return None
        avail = self.available
        if avail >= self.max_yield:
            # Full: no regen accrues. Re-anchor so a later non-full state
            # measures elapsed time from now, not from the distant past.
            if persist and self.last_regen != now:
                self.last_regen = now
            return avail
        gained = (now - self.last_regen) // self.regen_interval
        if gained <= 0:
            return avail
        new_avail = min(self.max_yield, avail + gained)
        if persist:
            self.available = new_avail
            # Advance by whole intervals only, preserving the leftover
            # fraction — otherwise partial regen progress is silently lost.
            self.last_regen = self.last_regen + gained * self.regen_interval
        return new_avail

    def get_available(self):
        """Read-only current amount (None = infinite water). No DB write."""
        if self.is_water_source:
            return None
        return self._update_regen(get_absolute_gametime(), persist=False)

    def harvest(self, quantity=1):
        """
        Take up to `quantity` units. Persists state.

        Synchronous read-modify-write: under Evennia's reactor this runs to
        completion before any other command, so two near-simultaneous
        foragers are serialised and cannot cause a lost update.

        Returns:
            int: amount actually harvested (0 if currently empty).
        """
        if self.is_water_source:
            return quantity  # infinite; refill uses Drink.refill(), not this
        now = get_absolute_gametime()
        self._update_regen(now, persist=True)
        taken = min(quantity, self.available)
        if taken > 0:
            self.available -= taken
        return taken

    # ------------------------------------------------------------------
    # Player-facing appearance (read-only)
    # ------------------------------------------------------------------

    def _availability_phrase(self):
        """An immersive, number-free line about current stock.

        Deliberately vague: players read the world, not a spreadsheet.
        Uses get_available() (persist=False) — looking never writes.
        """
        if self.is_water_source:
            return "Clear water flows here, free for the taking."
        available = self.get_available()
        max_yield = self.max_yield
        resource = self.resource_type
        if available <= 0:
            return f"It has been picked clean; no {resource} remain for now."
        ratio = available / max_yield if max_yield else 0
        if ratio <= 1 / 3:
            return f"Only a few {resource} are left to gather."
        if ratio <= 2 / 3:
            return f"There are some {resource} here to gather."
        return f"It is heavy with {resource}, ripe for the gathering."

    def get_display_desc(self, looker, **kwargs):
        """Base description plus a live availability line. No DB write."""
        base = super().get_display_desc(looker, **kwargs)
        phrase = self._availability_phrase()
        return f"{base}\n\n{phrase}" if base else phrase
