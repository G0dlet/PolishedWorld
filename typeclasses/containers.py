"""
Containers that hold ENC, not a count of things (Weight and Encumbrance, W4.1).

The containers contrib (`evennia.contrib.game_systems.containers`) supplies the
typeclass, the `get_from` lock and the two hooks; this module changes only what
"full" means. The contrib counts objects (`len(self.contents) >= capacity`);
here `capacity` is ENC, and a sack of twenty logs no longer weighs the same as
a sack of twenty sling bullets (WD5).

Rules (WD5; Weight decomposition Rev 7, W4.1 Q1-Q5):

- A container refuses an item that would take its own carried ENC above
  `capacity`. Its own ENC is the same walk the carrier's is
  (`world.encumbrance.enc_after_receiving`): the item's contents count, and
  twenty items at `enc` 0 count as 1 ENC (WD4).
- A container refuses another container, so nothing nests (one check, here).
- A container does not lighten its contents: the carrier counts them in full.

The hook runs where the contrib calls it -- `CmdPut` (`put <item> in <bag>`,
installed by W4.2). A bare `move_to(container)` runs no capacity check, as in
the contrib.
"""

from evennia.contrib.game_systems.containers.containers import ContribContainer
from evennia.utils.utils import inherits_from

from world import encumbrance


class Container(ContribContainer):
    """
    A container whose `capacity` is ENC (sack 10, backpack 20, saddlebag 15).

    `ObjectParent` is not listed: the contrib's base is
    `settings.BASE_OBJECT_TYPECLASS`, `typeclasses.objects.Object`, which
    already inherits it, and listing it again has no consistent MRO (Q1).

    `capacity` is the contrib's `AttributeProperty` (default 20), set per
    prototype in `world/prototypes.py`.
    """

    def at_pre_put_in(self, putter, target, **kwargs):
        """
        Refuse a container (Q3) or an item that would overfill this one (Q2).

        Replaces the contrib's check rather than extending it: `super()` would
        also refuse on the number of objects, which is what this class removes.

        Args:
            putter (Object): who is putting `target` in.
            target (Object): what is being put in.

        Returns:
            bool: True to let `target` in.
        """
        if inherits_from(target, ContribContainer):
            putter.msg("You cannot put a container inside another.")
            return False
        if encumbrance.enc_after_receiving(self, target) > self.capacity:
            putter.msg(f"The {self.key} is full.")
            return False
        return True
