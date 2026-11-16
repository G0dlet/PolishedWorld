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
- Automatic success and failure ("Automatic Success and Failure"): any roll
  of 01-05 is an automatic success and any roll of 96-00 an automatic
  failure, regardless of the modified skill.
- Success: any non-critical roll <= the modified skill.
- Failure: anything else.

Resolution order (Recipe Mastery MD8): fumble (99-00 below 100%, 00 at or
above) -> automatic failure (96-98; 96-99 at or above 100%) -> critical ->
automatic success (02-05; 01 is already critical) -> roll <= modified skill
-> failure. The bands decide the result only; `margin` stays target - roll,
so an automatic success at target 3 on a roll of 05 reports margin -2.

The "critical score" (modified skill // 10) is also returned, because the core
Craft skill ties a crafted item's bonus durability/value/utility to it (an 81%
crafter distributes 8 bonus points on a critical). Systems that don't need it
can ignore it.

Deliberate adaptation notes:
- A roll of 01 always criticals even when the modified skill is <= 0 (a ~1%
  fluke), per the rulebook's "01 is always a critical success". Callers that
  want to forbid this on truly impossible tasks should gate on `target`
  themselves before calling. The same holds for 02-05: the rulebook lifts the
  automatic bands when "no test is required or possible", and that ruling
  belongs to the caller (e.g. a recipe's min_skill floor refuses before any
  roll), not to this function.
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

    # Resolve in MD8's order. The fumble band owns the top of the die, so it
    # is tested first; automatic failure then takes what is left of 96-00
    # (96-98 below 100%, 96-99 at or above, where only 00 fumbles). The
    # critical band is tested before automatic success so that 01 stays a
    # critical, then 02-05 succeed whatever the target.
    if (target < 100 and roll >= 99) or roll == 100:
        result = FUMBLE
    elif roll >= 96:
        result = FAILURE
    elif roll <= crit_threshold:
        result = CRITICAL
    elif roll <= 5:
        result = SUCCESS
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


# --- Opposed resolution -----------------------------------------------------
# Outcome labels for opposed_check().
ATTACKER = "attacker"
DEFENDER = "defender"
STALEMATE = "stalemate"

# Level-of-success ranking, best -> worst (Mongoose Legend, "Levels of Success").
_LEVEL_RANK = {CRITICAL: 3, SUCCESS: 2, FAILURE: 1, FUMBLE: 0}


def _within_skill(roll, target):
    """
    The roll as it counts in an opposed tie: itself if it lies within the
    skill (roll <= target), else 0 (SC2). An automatic success at 02-05 above
    the target, or a critical 01 at a target of 0 or less, lies outside.
    """
    return roll if roll <= target else 0


def _judge(first, second, first_target=None, second_target=None):
    """
    Legend p. 45's order of resolution over two finished skill_check results.

    Args:
        first (dict): The first side's skill_check result.
        second (dict): The second side's skill_check result.
        first_target (int, optional): The target the first side's roll is
            measured against for *within the skill* and for the skill
            tie-break. Defaults to the result's own "target".
        second_target (int, optional): The same for the second side.

    Returns:
        str: ATTACKER if the first side wins, DEFENDER if the second does,
            STALEMATE if both failed.
    """
    if first_target is None:
        first_target = first["target"]
    if second_target is None:
        second_target = second["target"]

    # Both fail -> stalemate, regardless of failure vs fumble (rulebook: "if
    # both fail then a stalemate has occurred").
    if not first["success"] and not second["success"]:
        return STALEMATE

    # Different levels of success -> higher level wins.
    first_rank, second_rank = _LEVEL_RANK[first["result"]], _LEVEL_RANK[second["result"]]
    if first_rank != second_rank:
        return ATTACKER if first_rank > second_rank else DEFENDER

    # Same level (so both succeeded) -> the higher roll within the skill wins;
    # a roll outside the skill counts as 0 (SC2).
    first_roll = _within_skill(first["roll"], first_target)
    second_roll = _within_skill(second["roll"], second_target)
    if first_roll != second_roll:
        return ATTACKER if first_roll > second_roll else DEFENDER

    # Same roll too -> higher modified skill wins.
    if first_target != second_target:
        return ATTACKER if first_target > second_target else DEFENDER

    # Dead heat -> coin toss.
    return ATTACKER if randint(1, 2) == 1 else DEFENDER


def opposed_check(attacker_skill, defender_skill, attacker_mod=0, defender_mod=0):
    """
    Resolve a Mongoose Legend *opposed* skill test (core rulebook, "Opposed
    Skills", p.45).

    Both sides roll their own skill_check. Resolution, in order:
      1. Higher level of success wins (critical > success > failure > fumble).
      2. Same level (so both succeeded): higher dice roll *within skill range*
         wins. Within the skill range means roll <= target; a success outside
         it (an automatic success at 02-05 above the target, or a critical 01
         at a target of 0 or less) counts as 0 here, so it loses to any
         success within the skill (SC2, Combat Design OC1).
      3. Same level AND same roll (two rolls outside the skill both count 0):
         higher modified skill wins.
      4. Still tied: coin toss.
      5. If BOTH fail: stalemate -- the rulebook says re-roll later; callers
         decide what an inconclusive contest means in their context.

    NOTE: the "opposed skills over 100%" rule (highest mastered skill is dropped
    to 100% and the excess penalises everyone) is intentionally NOT implemented
    -- PolishedWorld caps skills at 100 for the MVP, so it is currently dead
    code. Revisit when skill progression lifts the cap.

    Args:
        attacker_skill (int): The acting side's effective skill %.
        defender_skill (int): The resisting side's effective skill %.
        attacker_mod (int): Situational modifier for the attacker.
        defender_mod (int): Situational modifier for the defender.

    Returns:
        dict: {
            "winner" (str): one of "attacker", "defender", "stalemate".
            "attacker" (dict): the attacker's full skill_check result.
            "defender" (dict): the defender's full skill_check result.
        }
    """
    a = skill_check(attacker_skill, attacker_mod)
    d = skill_check(defender_skill, defender_mod)
    return {"winner": _judge(a, d), "attacker": a, "defender": d}
