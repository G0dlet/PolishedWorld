"""
The haven: a room where, by PV3, no attack may begin and a player's body
stays its owner's. This module answers whether a room is one; the body's rule
(HV-T2) and the guard (HV-T4) read it.

Haven Decomposition, Task HV-T1; the locks are the Combat Design's §4.2
(PV3, HV2, HV3).

THE FLAG (HV2)
--------------
A room is a haven when it holds a true Attribute `room.db.is_haven`. A room
without the Attribute is no haven, so no room that existed before the slice
is touched. The flag is read here and nowhere else: every other module asks
`is_haven`, and `tests/test_haven.py`'s census holds that.

Where it is set (HV3): the seed writes it on the Old Temple when it makes the
room (`world/seed_data.py`), and on no other room. Staff set it with
`@set here/is_haven = True` and take it off with `@set here/is_haven =`,
which removes the Attribute. `@set` stores whatever it is given, so
`= yes` and `= no` are both a non-empty string and both a haven; `is_haven`
answers the truth of what is stored, and its tests hold that on purpose.

This module imports nothing of the game's, so that `typeclasses/corpse.py`
(HV-T2) and anything else can import it without a cycle.
"""


def is_haven(room):
    """
    Whether `room` is a haven (HV2).

    Args:
        room (Object or None): the room asked about, usually someone's
            `location`.

    Returns:
        bool: False for no room at all, else the truth of `room.db.is_haven`
        (a missing Attribute reads None, which is False).

    An error in the read is not caught: the caller knows which way a failure
    should fall (the corpse lock fails closed, server/conf/lockfuncs.py).
    """
    if room is None:
        return False
    return bool(room.db.is_haven)
