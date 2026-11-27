"""
Natural healing (survival loop S2.1, decisions SL6 and RP-L4).

Legend's Natural Healing Table (core p. 86): one hit point per a number of
hours, chosen by the Resilience value. `resilience()` is the one place here
that reads it, through `world.skill_base.value_of` (Body decomposition BD6):
the trait's value once the character has the skill, its base CON x 2 (p. 14)
until then. The wound's test reads it the same way (`wounds.resilience_test`). The table below keeps the book's rows as printed.

A character reads the table twelve times faster (HL10, Combat Design Rev
17): `interval_for` divides the book's interval by `SPEED_FACTOR`, the
fastest row too, because a character heals only while the player is at the
keyboard -- at Resilience 11-30 a point an hour of play. Twelve is a guess
until the alpha's data (BACKLOG *Survival loop tuning*). A creature heals
at the book's rate whether or not anyone is there (CE11), so
`world.creature_wounds` reads `book_interval_for`.

The clock is game time: the survival tick hands `accrue()` the game seconds
since its last run (`survival_ticker._tick_game_seconds`). Seconds collect in
`db.heal_progress`; each whole interval is one hit point, the remainder is
carried. Nothing accrues while Starving or Dehydrated (p. 90), and the counter
is zeroed at full health, so an old surplus never heals a new wound at once.

This module is the one writer of health upward by natural healing; damage
stays at `Character.apply_health_damage`. It writes no activity-log line:
healing is not an economic event (SL6).
"""

from world import client_state, skill_base, wounds
from world.survival_buffs import Dehydrated, Starving

HOUR = 3600

# (highest Resilience value on the row, game hours per hit point), in the
# book's order (Legend core p. 86). Values above the last row heal fastest.
ROWS = (
    (10, 72),
    (30, 48),
    (50, 36),
    (70, 24),
    (90, 18),
)
FASTEST_HOURS = 12  # 91+

# HL10: the book's intervals divided by this for a character. Every row
# divided by it must be a whole number of game seconds (a test holds it), and
# the fastest row must stay longer than one survival tick (a test holds that
# too): 3600 game seconds against the tick's 2400.
SPEED_FACTOR = 12

# Sent by the survival tick when at least one point lands (lock D1). No
# number in it (Tone Guide section 5): the panel shows the number.
HEALED = "Your wounds ache a little less."

# Conditions that stop natural healing (Legend p. 90).
BLOCKING = (Starving, Dehydrated)


def book_interval_for(resilience):
    """
    Game seconds per hit point for a Resilience value, as the book prints
    the row (p. 86). A creature heals by it (CE11).

    Args:
        resilience (int or float): the Resilience value.

    Returns:
        int: seconds of game time per hit point.
    """
    for top, hours in ROWS:
        if resilience <= top:
            return hours * HOUR
    return FASTEST_HOURS * HOUR


def interval_for(resilience):
    """
    Game seconds per hit point a character heals by: the book's row divided
    by `SPEED_FACTOR` (HL10).

    Args:
        resilience (int or float): the Resilience value.

    Returns:
        int: seconds of game time per hit point.
    """
    return book_interval_for(resilience) // SPEED_FACTOR


def resilience(char):
    """
    The Resilience value the table is read with (BD6).

    The Resilience trait's value if the character has it; its base, CON x 2
    (p. 14), if not -- `skill_base.value_of`'s safety net, so a character a
    backfill missed still heals. When Resilience improves, the character
    heals faster: the table is the book's, keyed on the skill.

    Hit Points are another number: since Wounds they follow CON + SIZ per
    location (`world.body.hit_points_max`), and the CON x 2 they once shared
    with this safety net was a coincidence.

    Returns:
        int, float or None: None when the character has neither the trait
            nor CON.
    """
    return skill_base.value_of(char, "resilience")


def is_blocked(char):
    """True while a condition stops natural healing."""
    return any(char.buffs.has(buffclass) for buffclass in BLOCKING)


def accrue(char, game_seconds):
    """
    Add `game_seconds` to the character's healing counter and grant whole
    hit points from it.

    Order matters and each step is a lock:
      1. Starving or Dehydrated: nothing is added, and what the counter
         already holds is kept (the time is lost, not the progress).
      2. At full health the counter is zeroed and nothing is granted.
      3. Whole intervals become points, capped at the room left below max;
         the remainder is carried. Reaching max zeroes the counter (2's rule,
         applied at once).

    The body is reached through the wound module (Wounds WN-T4): the room
    left from `wounds.room_to_heal`, the points through `wounds.heal`, which
    caps at the room and returns what landed -- the number the tick says its
    line for. A statue heals nothing (HL10): the tick is the only caller.

    Pushes `char` when a point lands (the door's one caller pushes, W4.2's
    census and WN-T4's).

    Args:
        char (Character): the character.
        game_seconds (int): game seconds since the last call for them.

    Returns:
        int: hit points granted (0 or more).
    """
    room = wounds.room_to_heal(char)
    if room is None or is_blocked(char):
        return 0
    if room <= 0:
        char.db.heal_progress = 0
        return 0
    res = resilience(char)
    if res is None:
        return 0
    interval = interval_for(res)
    progress = (char.db.heal_progress or 0) + max(0, int(game_seconds))
    whole, remainder = divmod(progress, interval)
    points = min(whole, room)
    if points <= 0:
        char.db.heal_progress = remainder
        return 0
    landed = wounds.heal(char, points)
    char.db.heal_progress = 0 if wounds.room_to_heal(char) == 0 else remainder
    client_state.push(char, "char")
    return landed
