"""
PolishedWorld clothing typeclass.

A thin subclass of the clothing contrib's ContribClothing that carries a
`warmth` value and recomputes the wearer's thermal stress the moment a garment
is worn or removed -- so a change in what you're wearing registers immediately
instead of waiting up to a full survival tick. A worn garment that leaves its
wearer by any move (drop, give, put) is removed on the way out, so it is never
counted worn on the receiver and the wearer's stress is recomputed at once.

Garments hold data only; there are no per-garment buffs. world/thermal.py sums
db.warmth across all worn pieces (covered layers included) each tick. This
typeclass just mirrors that recompute on the wear/remove action.

Scope: survival/thermal protection only. Combat armour (Legend armour points /
encumbrance) is a later system; the reserved hooks below mark where those values
will live without wiring them into any mechanic yet.
"""

from django.conf import settings
from evennia import AttributeProperty
from evennia.contrib.game_systems.clothing.clothing import ContribClothing
from evennia.utils import logger
from evennia.utils.utils import inherits_from

from typeclasses.durable import DurableObject
from typeclasses.objects import ObjectParent
from world import client_state
from world.thermal import apply_thermal_stress


class ClothingWithBuffs(ObjectParent, DurableObject, ContribClothing):
    """
    Wearable garment with a thermal `warmth` rating and a shared wear axis.

    condition (0-100) is inherited from DurableObject: the mixin owns the
    Attribute (default 100), apply_wear/is_broken, and condition_line(). Effective
    warmth is still scaled by condition/100 in thermal.worn_warmth, so a worn-out
    garment insulates less. MRO is (ObjectParent, DurableObject, ContribClothing)
    so DurableObject's condition descriptor takes precedence while
    ContribClothing's wear/remove resolve unchanged; the default 100 matches the
    old local AttributeProperty, so no already-spawned garment needs migrating.

    ObjectParent comes first because the clothing contrib's base is a plain
    DefaultObject, not settings.BASE_OBJECT_TYPECLASS (the containers contrib's
    is), so nothing else brings it (W5.1b). It gives a garment the hooks every
    typeclass has: at_object_delete tells the carrier's panel (a disassembled
    or destroyed garment leaves its ENC), and at_pre_put_in refuses a put into
    a garment. ContribClothing defines neither, so nothing is shadowed.
    tests/test_client_state.py TestObjectParentCensus holds every typeclass to
    this.

    warmth: insulation this piece contributes, read by thermal.worn_warmth via
        db.warmth. autocreate=True so every garment has a real db.warmth
        Attribute (default 0, visible in `examine`) even before a prototype
        overrides it.

    Reserved (autocreate=False -- no db Attribute, no `examine` entry until a
    system assigns them):
        rain_protection -- future wet/exposure axis, same pattern as warmth.
        armor_points / encumbrance -- Legend combat values; owned by the combat
            system, not survival.
    """

    warmth = AttributeProperty(default=0, autocreate=True)

    rain_protection = AttributeProperty(default=0, autocreate=False)
    armor_points = AttributeProperty(default=0, autocreate=False)
    encumbrance = AttributeProperty(default=0, autocreate=False)

    def wear(self, wearer, wearstyle, quiet=False):
        """
        Wear the garment, then recompute the wearer's thermal stress.

        super().wear() sets db.worn first, so worn_warmth already counts this
        piece when we recompute -- the new warmth registers at once.

        W7.1: the garment moves to the panel's worn list without a move, so
        no move hook pushes; this does. Soon, as the move hooks push, so the
        frame is built after the wear has finished.
        """
        super().wear(wearer, wearstyle, quiet=quiet)
        apply_thermal_stress(wearer)
        client_state.push_soon(wearer, "char")

    def remove(self, wearer, quiet=False):
        """
        Remove the garment, then recompute the wearer's thermal stress.

        super().remove() clears db.worn first, so the recompute already excludes
        this piece's warmth.

        W7.1: pushes as wear() does. A garment given away also runs this, from
        at_post_move; push_soon makes it one frame with the leave hook's.
        """
        super().remove(wearer, quiet=quiet)
        apply_thermal_stress(wearer)
        client_state.push_soon(wearer, "char")

    def at_post_move(self, source_location, move_type="move", **kwargs):
        """
        A worn garment that has left its wearer is no longer worn (L3.1).

        Every command that moves a garment away from a body -- `drop`, `give`,
        `put` -- goes through move_to, which calls this hook after the garment
        has arrived. Without it the contrib clears db.worn in exactly one place,
        at_get (clothing.py:318), so a garment given away arrived still flagged
        and counted as worn on the receiver, and a covering layer that left
        kept its undershirt covered_by a garment no longer on the body.

        The wearer is `source_location` when that is a character
        (settings.BASE_CHARACTER_TYPECLASS): there the full remove() runs,
        quietly, because it is remove() that uncovers the layers this garment
        covered and recomputes the wearer's thermal stress without waiting for
        a tick. Anything else -- a room, a container, None -- has no layers and
        no stress, and the flag is cleared directly. The contrib's
        get_worn_clothes is a module function, not a character method, so it
        cannot be the test for "is a wearer".

        On `get` the contrib calls at_get *after* move_to (general.py:472-475,
        containers.py:209-224), so this hook runs first. A garment on the floor
        is normally unflagged already; one that is not (a flag that leaked
        through a direct `location =` assignment, which runs no hook) came from
        a room and is cleared here, and at_get clears it again. A trade moves by
        assignment and so never reaches this hook; world/barter.py:64 refuses a
        worn garment at finish() instead.

        An exception here would make move_to return False after the move has
        already happened (objects.py:1331), and the command would tell the
        player a drop that did happen failed. So a failing remove() is logged
        and the flag cleared directly: the garment is gone from the body either
        way.
        """
        super().at_post_move(source_location, move_type=move_type, **kwargs)
        if not self.db.worn or source_location is self.location:
            return
        if source_location is not None and inherits_from(
            source_location, settings.BASE_CHARACTER_TYPECLASS
        ):
            try:
                self.remove(source_location, quiet=True)
            except Exception:
                logger.log_trace(
                    f"ClothingWithBuffs.at_post_move: remove() failed for {self.dbref} "
                    f"leaving {source_location.dbref}; clearing db.worn directly."
                )
                self.db.worn = False
        else:
            self.db.worn = False
