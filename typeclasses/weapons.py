"""
typeclasses/weapons.py

Weapons that are only weapons: club, quarterstaff, spear, bow, sling, and
the target shield GR-T12 adds (Gear decomposition GR-T2; locks GR13, GR21).

Weapon is a *thin* typeclass, as Tool is: DurableObject mixed onto the
game's Object base, and nothing more. It exists so that a pure weapon has
the shared 0-100 `condition` axis -- apply_wear, is_broken, condition_line
and `repair` -- that garments and tools already have.

**Being a weapon is not this class.** What makes an item a weapon is a row
in `world.gear.WEAPONS`, read by its prototype tag (GR13, GR16). A stone
knife or a stone axe is a weapon with a row and stays a Tool; a club is a
weapon with a row and is a Weapon only because it needs a condition and is
no tool. No code should ask `isinstance(obj, Weapon)` to learn whether an
item is a weapon: ask `gear.weapon(obj)`.

MRO order (DurableObject, Object) is Tool's, for Tool's reason: the mixin's
`condition` AttributeProperty must sit early in __mro__ to be autocreated.

No wear *trigger* lives here on purpose. What wears a weapon is a use or a
damage event (GR19), `gear.wear_weapon` and `gear.damage_weapon`, and the
fight that calls them is ML's.
"""

from typeclasses.durable import DurableObject
from typeclasses.objects import Object


class Weapon(DurableObject, Object):
    """A durable item that is only a weapon. Inherits condition, apply_wear
    and is_broken from DurableObject; carries no logic of its own (the rows
    are world.gear's, and the fight that wears it is ML's)."""

    pass
