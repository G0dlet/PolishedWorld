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

    def is_empty(self):
        """Return True if no sips remain."""
        return self.charges <= 0

    def refill(self):
        """Refill to capacity. Returns True if anything was added."""
        if self.charges >= self.max_charges:
            return False
        self.charges = self.max_charges
        # Durability is opt-in: only containers crafted with a durability value
        # wear with use. Plain/found drinks (no durability attr) refill forever.
        if self.db.durability is not None:
            self.db.durability -= 1
        return True

    def is_worn_out(self):
        """True if this container has a durability value that has reached zero."""
        return self.db.durability is not None and self.db.durability <= 0
