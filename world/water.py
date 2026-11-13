"""
Water in the world: where a character can drink or fill a vessel.

Survival Loop S1.1 (decomposition SL2). `drink` and `refill` both ask this
module whether a room has water, so the answer lives in one place; when
Stage 6 gives terrain its own water (Water design VP8), `source_in` is the
one function that learns about it.

A source is a `ResourceNode` with `is_water_source` set: the seeded spring
(`world/prototypes.py`, `SPRING`). It never runs dry.
"""

# One draught from a vessel: `Drink.restore_amount`'s default. It is written
# out here because an AttributeProperty cannot be read off the class (its
# __get__ needs an instance); tests/test_water.py pins the two together.
DRAUGHT = 15

# Drinking at the source is three draughts at once (SL2, Water VQ8). Tuned by
# play, not yet: OQ-S3.
SOURCE_DRAUGHTS = 3
SOURCE_RESTORE = SOURCE_DRAUGHTS * DRAUGHT

_NODE = "typeclasses.resources.ResourceNode"


def is_source(obj):
    """
    Whether `obj` is somewhere a character can drink and fill a vessel.

    Args:
        obj (Object or None): Anything; `None` is not a source.

    Returns:
        bool: True for a `ResourceNode` with `is_water_source` set.
    """
    if obj is None:
        return False
    return bool(obj.is_typeclass(_NODE, exact=False) and obj.is_water_source)


def source_in(room):
    """
    The first water source in a room.

    Args:
        room (Object or None): The room to look in; `None` (a character in
            no location) has no water.

    Returns:
        Object or None: The source, or `None` if the room has none.
    """
    if room is None:
        return None
    for obj in room.contents:
        if is_source(obj):
            return obj
    return None
