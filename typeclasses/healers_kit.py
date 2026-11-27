"""
typeclasses/healers_kit.py

The healer's kit (Healing decomposition HL-T6; locks HL3, HL9).

A leather satchel stocked for surgery (Legend p. 114). It is what `operate`
needs carried, and it wears once per operation, won or lost (HL9, 6): the
wearing is surgery's (HL-T12), the amount is the kit's own, as a vessel's
refill wear is the vessel's (typeclasses.consumables.Drink).

Its start condition is set by the craft's quality, as a garment's is
(world/recipes.py, _apply_quality_condition): 100, 90, 70 or 50, which at
OPERATION_WEAR is 10, 9, 7 or 5 operations. A better crafter's kit lasts
longer, and a broken one is refused by `operate`.

A kit is replaced, not mended (OQ-HL8): a kit that `repair` could restore
would never need replacing, and the kit-maker's trade would have no sink.
A spent kit can still be taken apart, and `disassemble` may teach its
recipe -- and so the Healing skill (HL3) -- whatever its condition.

Thin, as Tool is: DurableObject mixed onto the game's Object, with the two
class constants that make it a kit. No wear trigger lives here.
"""

from typeclasses.durable import DurableObject
from typeclasses.objects import Object


class HealersKit(DurableObject, Object):
    """A healer's kit: durable, worn per operation, never mended."""

    # Condition lost per operation, won or lost (HL9, 6; OQ-HL8). A
    # calibration constant: nothing maims before ML, so it was set before
    # any data, at the dear end (HL-T6's STOPP 0).
    OPERATION_WEAR = 10

    # Replaced, not mended: `repair` refuses it (commands/repair_commands.py).
    mendable = False
