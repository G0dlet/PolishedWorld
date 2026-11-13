"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit

from .objects import ObjectParent


class Exit(ObjectParent, DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property and overrides some hooks
    and methods to represent the exits.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects child classes like this.

    """

    def at_failed_traverse(self, traversing_object, **kwargs):
        """
        Say nothing to a collapsed body (Survival Loop S3.4, lock B1).

        `Character.at_pre_move` refused its walk and already said why (*Your
        legs will not carry you.*); Evennia's *You cannot go there.* after it
        would be a second, wrong reason. Every other failure keeps it.
        """
        if traversing_object.attributes.get("collapsed"):
            return
        super().at_failed_traverse(traversing_object, **kwargs)
