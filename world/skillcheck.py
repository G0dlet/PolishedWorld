"""
world/skillcheck.py

Mongoose Legend d100 skill-resolution primitive for PolishedWorld.

This is the single source of truth for percentile skill checks. It is a *pure*
function (no Evennia objects, no I/O) so it can be unit-tested in isolation and
reused by any system needing a Legend skill test: crafting, future combat,
creature harvesting, social rolls, and so on.

Rules implemented (Mongoose Legend core rulebook, "Skill Tests"):

- A check rolls 1d100 (1-100, where 100 represents the "00" face) against a
  *modified* skill = skill_value + modifier.
- Critical success: the roll is <= 10% of the modified skill, rounded up.
  A roll of 01 is always a critical success.
- Fumble: if the modified skill is below 100%, a roll of 99 or 00 (100) fumbles.
  If the modified skill is 100% or higher, only 00 (100) fumbles.
- Success: any non-critical roll <= the modified skill.
- Failure: anything else.

The "critical score" (modified skill // 10) is also returned, because the core
Craft skill ties a crafted item's bonus durability/value/utility to it (an 81%
crafter distributes 8 bonus points on a critical). Systems that don't need it
can ignore it.

Deliberate adaptation notes:
- A roll of 01 always criticals even when the modified skill is <= 0 (a ~1%
  fluke), per the rulebook's "01 is always a critical success". Callers that
  want to forbid this on truly impossible tasks should gate on `target`
  themselves before calling.
- `target` is never clamped; skills above 100% behave faithfully (only 00
  fumbles, and a wider critical band).
"""

from math import ceil
from random import randint

# Result tiers, ordered best -> worst.
CRITICAL = "critical"
SUCCESS = "success"
FAILURE = "failure"
FUMBLE = "fumble"


def skill_check(skill_value, modifier=0):
    """
    Resolve a single Mongoose Legend d100 skill test.

    Args:
        skill_value (int): The character's effective skill percentage before
            situational modifiers (e.g. a Craft skill of 45).
        modifier (int): Situational modifier. Positive = easier (e.g. +20 for
            good tools), negative = harder (e.g. -40 for improvised tools).

    Returns:
        dict: A result with keys:
            - "result" (str): one of "critical", "success", "failure", "fumble".
            - "success" (bool): True for critical or success, False otherwise.
            - "roll" (int): the 1d100 result (1-100; 100 == "00").
            - "target" (int): the modified skill the roll was tested against.
            - "margin" (int): target - roll. Positive on success-side rolls,
              negative on failure-side; useful for opposed tests and scaling.
            - "crit_score" (int): target // 10 (floored at 0), the magnitude the
              core Craft rules tie to critical bonuses.
    """
    # Defensive coercion: trait values are ints, but a modifier could arrive as
    # a float (e.g. derived from a buff). Integer-floor keeps the d100 math
    # well-defined and avoids surprises in the comparisons below.
    target = int(skill_value) + int(modifier)
    roll = randint(1, 100)  # 100 represents the "00" face

    # Critical band: 10% of the modified skill, rounded up. Floored at 1 so a
    # roll of 01 always lands in the critical band, matching the rulebook.
    crit_threshold = max(1, ceil(target / 10))

    # Resolve, checking the fumble band first (it owns the top of the die so it
    # must win over the success comparison when target >= 99).
    if (target < 100 and roll >= 99) or roll == 100:
        result = FUMBLE
    elif roll <= crit_threshold:
        result = CRITICAL
    elif roll <= target:
        result = SUCCESS
    else:
        result = FAILURE

    return {
        "result": result,
        "success": result in (CRITICAL, SUCCESS),
        "roll": roll,
        "target": target,
        "margin": target - roll,
        "crit_score": max(0, target // 10),
    }
