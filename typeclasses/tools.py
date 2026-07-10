"""
typeclasses/tools.py

Crafting tools (knife, needle, ...).

Tool is a *thin* typeclass: it is DurableObject mixed onto the game's Object
base, and nothing more. That single line of inheritance is the whole point --
it gives every tool the shared 0-100 `condition` wear axis plus apply_wear /
is_broken / condition_line, identical to the axis garments already use
(ClothingWithBuffs), so tools and clothing share one wear vocabulary and one
repair target.

MRO order (DurableObject, Object) is deliberate:
    * DurableObject first, so its `condition` AttributeProperty and wear methods
      sit early in __mro__. Evennia's init_evennia_properties() walks the full
      __mro__ and reads vars(base) for every base -- including this mixin -- so
      `condition` autocreates on a real Tool instance at creation. (Verified in
      durable.py's own docstring; see Evennia Reference Rev 6 s.10.1.)
    * Object second, providing the DefaultObject machinery (attributes handler,
      hooks, locks) a mixin cannot supply on its own.

No wear *trigger* lives here on purpose. What nicks a tool's condition is a
completed craft, and that belongs to the recipe layer (Component D), not to the
tool typeclass. Keeping Tool empty of tool-specific logic is a design invariant:
a Tool is exactly "an Object that can wear down", no more.
"""

from typeclasses.durable import DurableObject
from typeclasses.objects import Object


class Tool(DurableObject, Object):
    """A durable crafting tool. Inherits condition/apply_wear/is_broken from
    DurableObject; carries no tool-specific logic of its own (Component D owns
    the wear trigger)."""

    pass
