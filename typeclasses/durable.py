"""
typeclasses/durable.py

Shared durability foundation.

DurableObject is a *typeclass-agnostic* mixin -- never instantiated on its own --
that owns a single 0-100 `condition` wear axis plus the vocabulary for wearing
something down (apply_wear), asking whether it is spent (is_broken), and
rendering that state (condition_line). Garments (ClothingWithBuffs, Task B.2)
and, later, tools (Tool, Component C) inherit it, so clothing and tools share one
wear axis, one repair target, and one word for "how worn is this".

No wear *trigger* lives here. What nicks a thing's condition differs per type
(garments: time/wearing via a future script; tools: per completed craft), so the
trigger belongs to those systems (Component D), not to the axis itself.

Mixin, not a typeclass: `condition` is an AttributeProperty, which only becomes a
real db-backed Attribute once this class is mixed into an actual typeclass (one
whose instances have an .attributes handler). Evennia's init_evennia_properties()
walks the full __mro__ and reads vars(base) for every base -- including this plain
mixin -- so autocreate fires normally on the host at creation. Test it through a
host object (a garment, or a throwaway DurableObject+DefaultObject subclass),
never a bare DurableObject() instance.
"""

from evennia import AttributeProperty
from evennia.utils import logger


class DurableObject:
    """
    Mixin adding a shared 0-100 `condition` wear axis.

    condition: 0-100 wear state (100 = pristine). autocreate=True so every host
        object owns a real db.condition Attribute from creation -- identical to
        the value ClothingWithBuffs used before B.2, so no already-spawned
        garment needs migrating and `examine` shows it for free.
    """

    condition = AttributeProperty(default=100, autocreate=True)

    def apply_wear(self, amount):
        """
        Wear this object down by `amount`, flooring condition at 0.

        Args:
            amount (int): wear points to subtract. Expected >= 0; a completed
                craft or a tick of wearing passes a small positive number. A
                negative amount would heal -- that path belongs to repair, not
                here -- so it is not the intended use.

        Returns:
            int: the new condition after wear.

        The read-modify-write of condition is atomic under Evennia's
        single-threaded reactor, so concurrent wear from different actors cannot
        interleave into a lost update; no lock is needed. Logs once at the moment
        the object breaks (crosses to 0) so a tool/garment shattering is visible
        in the server log for balancing.
        """
        before = self.condition
        after = max(0, before - amount)
        self.condition = after
        if after == 0 and before > 0:
            logger.log_info(
                f"DurableObject #{self.id} ({self.key}) broke: "
                f"condition {before} -> 0 (wear {amount})."
            )
        return after

    @property
    def is_broken(self):
        """True once condition has hit 0 (spent; must be repaired or discarded)."""
        return self.condition <= 0

    # Condition colour bands (Task D.3), locked once the line is first shown to
    # players. Green above 66, yellow across the middle, red below 33.
    _COND_GOOD = 66
    _COND_WORN = 33

    def condition_line(self):
        """
        One-line condition read for display, e.g. 'Condition: |g72%|n'.

        Pure formatting helper -- it renders, it does not decide *where* it is
        shown. Consumers call it explicitly: the player-facing look injection
        (get_display_desc below), repair feedback, and tool-break messages.

        Colour banded (Task D.3): green > 66, yellow 33-66, red < 33, so a
        glance at `look` reads how spent a tool or garment is. The threshold was
        deliberately kept out of the foundation until now (durable.py owns the
        axis, not display policy); this is where the line is first shown, so the
        bands land here.
        """
        cond = self.condition
        if cond > self._COND_GOOD:
            color = "|g"
        elif cond >= self._COND_WORN:
            color = "|y"
        else:
            color = "|r"
        return f"Condition: {color}{cond}%|n"

    def get_display_desc(self, looker, **kwargs):
        """Append the condition line to this object's description on `look`.

        This is the player-facing wear readout: ordinary players have no
        `examine`, so `look` is where they must see how worn a tool or garment
        is. Living on DurableObject (not Tool) means tools and garments both
        gain the line from one place -- Tool stays thin, and any future durable
        typeclass inherits it for free.

        super() walks the host's MRO to the real typeclass's get_display_desc
        (DefaultObject for a Tool; ContribClothing for a garment, whose worn
        list is preserved), so we augment that base rather than replace it. The
        mixin sits before the real base in every host's MRO, so this override
        wins while still deferring to the base via super().
        """
        base = super().get_display_desc(looker, **kwargs)
        line = self.condition_line()
        return f"{base}\n\n{line}" if base else line
