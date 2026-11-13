"""
Natural healing (survival loop S2.1, decisions SL6 and RP-L4).

Legend's Natural Healing Table (core p. 86): one hit point per a number of
hours, chosen by the Resilience value. No Resilience skill exists yet, so its
base, CON x 2 (p. 53), stands in for it (Foraging RP-L4) -- `resilience()` is
the one place that reads it, and the table below keeps the book's rows as
printed, so a real skill later changes one line and not the table.

The clock is game time: the survival tick hands `accrue()` the game seconds
since its last run (`survival_ticker._tick_game_seconds`). Seconds collect in
`db.heal_progress`; each whole interval is one hit point, the remainder is
carried. Nothing accrues while Starving or Dehydrated (p. 90), and the counter
is zeroed at full health, so an old surplus never heals a new wound at once.

This module is the one writer of health upward by natural healing; damage
stays at `Character.apply_health_damage`. It writes no activity-log line:
healing is not an economic event (SL6).
"""

import math

from world import client_state
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

# Sent by the survival tick when at least one point lands (lock D1). No
# number in it (Tone Guide section 5): the panel shows the number.
HEALED = "Your wounds ache a little less."

# Conditions that stop natural healing (Legend p. 90).
BLOCKING = (Starving, Dehydrated)


def interval_for(resilience):
    """
    Game seconds per hit point for a Resilience value (the table's row).

    Args:
        resilience (int or float): the Resilience value.

    Returns:
        int: seconds of game time per hit point.
    """
    for top, hours in ROWS:
        if resilience <= top:
            return hours * HOUR
    return FASTEST_HOURS * HOUR


def resilience(char):
    """
    The Resilience value the table is read with: CON x 2 (RP-L4).

    Deliberately not `world.chargen.derive_health_max`, which is also CON x 2
    today: hit points and Resilience share the number by coincidence, and
    Stage 5's hit locations may change the hit-point formula.

    Returns:
        int or None: None when the character has no CON.
    """
    con = char.stats.get("con")
    if con is None:
        return None
    return int(con.value * 2)


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

    The trait clamps `current` at max on its own (GaugeTrait's setter), so
    the cap here is what keeps the return value honest: callers say a line
    and S2.2 reports a login total from it.

    Pushes `char` when a point lands (the writer pushes, W4.2's census).

    Args:
        char (Character): the character.
        game_seconds (int): game seconds since the last call for them.

    Returns:
        int: hit points granted (0 or more).
    """
    health = char.traits.get("health")
    if health is None or is_blocked(char):
        return 0
    if health.current >= health.max:
        char.db.heal_progress = 0
        return 0
    res = resilience(char)
    if res is None:
        return 0
    interval = interval_for(res)
    progress = (char.db.heal_progress or 0) + max(0, int(game_seconds))
    whole, remainder = divmod(progress, interval)
    room = math.ceil(health.max - health.current)
    points = min(whole, room)
    if points <= 0:
        char.db.heal_progress = remainder
        return 0
    health.current = health.current + points
    char.db.heal_progress = 0 if health.current >= health.max else remainder
    client_state.push(char, "char")
    return points
