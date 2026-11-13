"""
Consumable item typeclasses: Food and Drink.

Food is single-use (consumed entirely on eat). Drink is charge-based and
refillable (a waterskin holds several sips and can be refilled at a water
source). Per-item values use AttributeProperty so builders can inspect them
with `examine` and override them per prototype.

Gauge restoration is applied by the eat/drink commands (Task 4.2): Food ->
hunger, Drink -> thirst. These typeclasses only carry the data + a small
helper; they do not touch character traits themselves, keeping item and
command responsibilities separated.
"""

from evennia import AttributeProperty
from typeclasses.objects import Object


class Food(Object):
    """A single-use food item that restores hunger when eaten."""

    # How much hunger one serving restores.
    restore_amount = AttributeProperty(20, autocreate=True)
    # Message shown to the eater. {key} is replaced with the item's name.
    consume_message = AttributeProperty("You eat {key}.", autocreate=True)


class Drink(Object):
    """A charge-based, refillable drink container that restores thirst."""

    # How much thirst one sip restores.
    restore_amount = AttributeProperty(15, autocreate=True)
    # Sips remaining and capacity.
    charges = AttributeProperty(5, autocreate=True)
    max_charges = AttributeProperty(5, autocreate=True)
    # Whether this container can be refilled at a water source.
    refillable = AttributeProperty(True, autocreate=True)
    consume_message = AttributeProperty("You drink from {key}.", autocreate=True)
    # Survival Loop SL3: the kind of water inside ("fresh"; brine is Water
    # slice 3). None on a vessel filled before kinds existed reads as fresh
    # through held_kind() -- no backfill.
    water_kind = AttributeProperty(None, autocreate=False)

    def is_empty(self):
        """Return True if no sips remain."""
        return self.charges <= 0

    def held_kind(self):
        """
        The kind of water this vessel holds.

        Returns:
            str or None: None when empty; otherwise the stored kind, or
            "fresh" for a vessel filled before kinds were stored (SL3).
        """
        if self.is_empty():
            return None
        return self.water_kind or "fresh"

    def pour_out(self):
        """Empty the vessel: no sips left and no kind. Wears nothing (SL3)."""
        self.charges = 0
        self.water_kind = None

    def refill(self, kind="fresh"):
        """
        Refill to capacity with water of `kind`.

        The caller has already refused a vessel holding another kind
        (`refill`, SL3), so the kind is stamped, not compared.

        Args:
            kind (str): The source's `water_kind`.

        Returns:
            bool: True if anything was added; False if already full.
        """
        if self.charges >= self.max_charges:
            return False
        self.charges = self.max_charges
        self.water_kind = kind
        # Durability is opt-in: only containers crafted with a durability value
        # wear with use. Plain/found drinks (no durability attr) refill forever.
        if self.db.durability is not None:
            self.db.durability -= 1
        return True

    def is_worn_out(self):
        """True if this container has a durability value that has reached zero."""
        return self.db.durability is not None and self.db.durability <= 0
