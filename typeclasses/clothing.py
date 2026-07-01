"""
PolishedWorld clothing typeclass.

A thin subclass of the clothing contrib's ContribClothing that carries a
`warmth` value and recomputes the wearer's thermal stress the moment a garment
is worn or removed -- so a change in what you're wearing registers immediately
instead of waiting up to a full survival tick.

Garments hold data only; there are no per-garment buffs. world/thermal.py sums
db.warmth across all worn pieces (covered layers included) each tick. This
typeclass just mirrors that recompute on the wear/remove action.

Scope: survival/thermal protection only. Combat armour (Legend armour points /
encumbrance) is a later system; the reserved hooks below mark where those values
will live without wiring them into any mechanic yet.
"""

from evennia import AttributeProperty
from evennia.contrib.game_systems.clothing.clothing import ContribClothing

from world.thermal import apply_thermal_stress


class ClothingWithBuffs(ContribClothing):
    """
    Wearable garment with a thermal `warmth` rating.

    warmth: insulation this piece contributes, read by thermal.worn_warmth via
        db.warmth. autocreate=True so every garment has a real db.warmth
        Attribute (default 0, visible in `examine`) even before a prototype
        overrides it.

    condition: 0-100 wear state. Effective warmth is scaled by condition/100 in
        thermal.worn_warmth, so a worn-out garment insulates less. autocreate=True
        for the same reason as warmth -- every garment owns a real db.condition
        the GarmentWearScript (H6.2) can decrement and `examine` can show.

    Reserved (autocreate=False -- no db Attribute, no `examine` entry until a
    system assigns them):
        rain_protection -- future wet/exposure axis, same pattern as warmth.
        armor_points / encumbrance -- Legend combat values; owned by the combat
            system, not survival.
    """

    warmth = AttributeProperty(default=0, autocreate=True)
    condition = AttributeProperty(default=100, autocreate=True)

    rain_protection = AttributeProperty(default=0, autocreate=False)
    armor_points = AttributeProperty(default=0, autocreate=False)
    encumbrance = AttributeProperty(default=0, autocreate=False)

    def wear(self, wearer, wearstyle, quiet=False):
        """
        Wear the garment, then recompute the wearer's thermal stress.

        super().wear() sets db.worn first, so worn_warmth already counts this
        piece when we recompute -- the new warmth registers at once.
        """
        super().wear(wearer, wearstyle, quiet=quiet)
        apply_thermal_stress(wearer)

    def remove(self, wearer, quiet=False):
        """
        Remove the garment, then recompute the wearer's thermal stress.

        super().remove() clears db.worn first, so the recompute already excludes
        this piece's warmth.
        """
        super().remove(wearer, quiet=quiet)
        apply_thermal_stress(wearer)
