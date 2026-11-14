"""
Where a finished character first stands, and what it calls home (Arrival
Decomposition, Task AV-T1; Newcomer Design Z1).

    from world import arrival
    arrival.arrival_room()   # -> the seeded Old Temple, or None
    arrival.arrive(char)     # -> the room it now stands in and calls home, or None

`arrive()` has one caller, character creation's last node (`node_done`, AV-T2).
It is not a teleport for staff: `@tel` and `home` already exist.

THE ROOM IS FOUND BY SEED ID (AV2)
----------------------------------
`seed_data.ARRIVAL_ROOM` names a `seed_id` in `seed_data.ROOMS`, and the room
is looked up by its seed tag, not by key and not by dbref. A dbref differs per
instance and a key can be edited in game; the seed tag is the one name the
seeder gives every instance the same way.

WHY `home` (AV3)
----------------
`Character._get_respawn_location()` reads the per-character override, then
`settings.DEFAULT_RESPAWN_DBREF`, then `home`. A character's `home` starts as
`DEFAULT_HOME`, which is Limbo, and `DEFAULT_RESPAWN_DBREF` lives in no
committed file. Writing `home` here means a made character respawns in the
temple whatever an instance's settings say; the setting stays an override.

WHY NO HOOKS (AV4)
------------------
The move is `move_to(room, quiet=True, move_hooks=False)`, death's form.
`Character.at_post_move` would look at the room, and the creation menu's
`cmd_on_exit="look"` looks again when it closes: with hooks the newcomer would
read the temple twice. `at_pre_move` would interrupt a timed action, and a
character still in the menu has none.

Skipping the hooks also skips the rooms' own: `Room.at_object_leave` and
`Room.at_object_receive` are what push every other viewer's room list
(webclient W4.2). So, as `at_character_death` does after its hookless move,
`arrive()` pushes both rooms itself. The arriving character's own panels are
the caller's to push (AV5: `node_done` pushes all four after this returns).

A MISS IS QUIET (AV6)
---------------------
A database without the seed -- every unit-test database, a scratch game dir --
has no arrival room. Then nothing moves, `home` is untouched, one warning goes
to the server log, and the function returns None. Nothing here raises: any
exception is logged with its trace and turned into None, because a broken seed
must never stop a character from being made.

MULTIPLAYER
-----------
`arrive()` writes only the character it is given, inside the command that
finished its menu, on Twisted's single thread. Ten newcomers finishing at once
each move themselves; the room pushes are coalesced per room by
`client_state.push_room_soon`.
"""

from evennia.utils import logger

from world import client_state
from world import seed_data
from world.seeding import find_seeded


def arrival_room():
    """
    The room a finished character arrives in: the object carrying the seed
    tag `seed_data.ARRIVAL_ROOM`, or None on a database without the seed.

    `find_seeded` never raises; a duplicated seed tag is warned about there
    and its first match used.
    """
    return find_seeded(seed_data.ARRIVAL_ROOM)


def arrive(character):
    """
    Make the arrival room `character`'s home and stand it there.

    Order: resolve the room; write `home`; move without hooks, unless the
    character already stands there; push the room it left and the room it
    entered.

    Args:
        character (Character): a character that has just been made.

    Returns:
        Object or None: the arrival room, now both the character's location
        and its home; None when there is no arrival room, when `move_to`
        refuses (then `home` is already written -- it is the right home either
        way), or when anything raises. Every None is logged; none raises.
    """
    try:
        room = arrival_room()
        if room is None:
            logger.log_warn(
                f"arrival: no object carries seed tag {seed_data.ARRIVAL_ROOM!r}; "
                f"{character!r} stays in {character.location!r} with home "
                f"{character.home!r}."
            )
            return None

        character.home = room
        source = character.location
        if source == room:
            return room

        if not character.move_to(room, quiet=True, move_hooks=False):
            logger.log_warn(
                f"arrival: move_to refused to move {character!r} from "
                f"{source!r} to {room!r}; its home is {room!r}."
            )
            return None

        # The hookless move ran neither room's hook (see the module docstring).
        client_state.push_room_soon(source)
        client_state.push_room_soon(room)
        return room
    except Exception:
        logger.log_trace(f"arrival: could not arrive {character!r}.")
        return None
