"""
The haven: a room where, by PV3, no attack may begin and a player's body
stays its owner's. This module answers whether a room is one, which the
body's rule (HV-T2) reads, and whether an attack may begin (HV-T4), which
`hunt` asks from HV-T5, and ML and PJ after it.

Haven Decomposition, Tasks HV-T1 and HV-T4; the locks are the Combat
Design's §4.2 (PV1, PV3, HV1–HV3, HV5, HV7) and §4.3 (TR5).

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

THE GUARD (HV-T4; HV1, HV5, HV7)
--------------------------------
`attack_refusal(attacker, target)` answers `None`, or the line the attacker
is to be told. It asks the haven first -- the attacker's room or the
target's, so a shot into a haven and out of one are both refused -- and
player against player second, while `PVP_ENABLED` is False (PV1). It sends
nothing and writes nothing: the caller sends the line, and a creature that
attacks has nobody to tell. `PVP_ENABLED` is read here and nowhere else;
`tests/test_haven.py`'s census holds that, and another test that it is False.

This module imports nothing of the game's, so that `typeclasses/corpse.py`
(HV-T2) and anything else can import it without a cycle. A player character
is therefore known by its class's path, not by an import: the character
module imports `world.death_contract`, which imports this one.
"""

from evennia.utils.utils import inherits_from

# PV1: a player character cannot attack another, anywhere. Built and switched
# off, the form SEVERED_ENABLED has (world/wounds.py:72; HV5): only
# `attack_refusal` reads it, and tests patch this module's attribute. PV6:
# opening player against player is a decision of its own, later. It needs
# the haven in service, the series note *law/crime/bounties* written, and the
# statue question answered (Combat Design §4.2). True never opens a haven.
PVP_ENABLED = False

# Who is a player character (HV7): the game's class, a statue with it. A
# creature, the sweeper and Evennia's own DefaultCharacter are not. The path
# is commands/names_commands.py's.
_CHARACTER = "typeclasses.characters.Character"

# The haven's line names nobody; PV1's names the target as the attacker sees
# it (TR5): the recog or the short description, never the key.
HAVEN_REFUSAL = "No hand is raised in a haven."
PVP_REFUSAL = "You will not raise a hand against {name}."


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


def attack_refusal(attacker, target):
    """
    Whether `attacker` may begin an attack on `target` (HV1, HV7).

    Args:
        attacker (Object): who would attack: a character or a creature.
        target (Object): who would be attacked.

    Returns:
        str or None: None when the attack may begin, else the line that
        refuses it, for the caller to send to the attacker.

    Asks the haven before player against player, so two characters in a
    haven hear the haven's line. Sends nothing, writes nothing. An error in
    a read is not caught: the caller decides which way a failure falls.
    """
    if is_haven(attacker.location) or is_haven(target.location):
        return HAVEN_REFUSAL
    if (not PVP_ENABLED and inherits_from(attacker, _CHARACTER)
            and inherits_from(target, _CHARACTER)):
        return PVP_REFUSAL.format(name=target.get_display_name(attacker))
    return None
