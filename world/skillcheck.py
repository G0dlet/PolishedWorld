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
- The "opposed skills over 100%" rule (p. 45) belongs to the opposed forms
  below and not to skill_check: a plain test is never lowered.
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


def _excess(*targets):
    """
    The over-100% penalty of an opposed test (p. 45, SC3): what the highest
    modified target in the contest has above 100, or 0. It is taken off every
    side, so the master tests at 100 and everyone else below.
    """
    return max(0, max(targets) - 100)


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

    Opposed skills over 100% (p. 45, SC3): the side with the highest modified
    target -- found *after* every other modifier -- subtracts 100 from it and
    the remainder is a penalty to both sides. The master tests at 100 and the
    other side below its own target. The excess is 0 unless a modified target
    is above 100, so a hunter at 120% with -20 for overload gives none. Both
    sides roll against the lowered target, so the bands follow it: a roll of
    11 is a critical at 120 and a plain success at 100.

    Args:
        attacker_skill (int): The acting side's effective skill %.
        defender_skill (int): The resisting side's effective skill %.
        attacker_mod (int): Situational modifier for the attacker.
        defender_mod (int): Situational modifier for the defender.

    Returns:
        dict: {
            "winner" (str): one of "attacker", "defender", "stalemate".
            "attacker" (dict): the attacker's full skill_check result; its
                "target" is the lowered target the roll was tested against.
            "defender" (dict): the defender's, likewise.
            "excess" (int): what was taken off both sides (0 in the ordinary
                case).
        }
    """
    # The same coercion skill_check applies, so the excess is measured on the
    # targets the rolls will actually be made against.
    excess = _excess(
        int(attacker_skill) + int(attacker_mod),
        int(defender_skill) + int(defender_mod),
    )
    a = skill_check(attacker_skill, int(attacker_mod) - excess)
    d = skill_check(defender_skill, int(defender_mod) - excess)
    return {"winner": _judge(a, d), "attacker": a, "defender": d, "excess": excess}


def opposed_against(made, skill, modifier=0):
    """
    Resolve an opposed test against a roll that has already been made: only
    the resisting side rolls (core rulebook pp.145-146 and 132-133).

    The book uses this form in three places: the wound tests, where a
    Serious or Major Wound is resisted with Resilience "in an Opposed Test
    against the value of the original attack roll"; Bleed (Resilience
    against the attacker's original attack roll); and Disarm (Combat Skill
    against the original attack roll *or the original parry roll*). Because
    the roll already made can be a parry, the sides are named for what they
    are -- `made` and `resisting` -- and the answer is `resisted`, not an
    attacker or a defender.

    The book always opposes a *successful* roll, so `made` must be one: a
    failed `made` is the caller's error and raises ValueError before any die
    is rolled. A stalemate therefore cannot arise; this form always answers.

    Order of resolution as in opposed_check (p.45, SC2). Opposed skills over
    100% apply (SC3): the excess is taken from the higher of `made["target"]`
    and the resisting side's modified target, and the resisting side rolls
    against its own target less the excess. **The made roll keeps its level
    and its roll** -- a critical stays a critical -- and only whether it lies
    within the skill is asked against `made["target"] - excess`. The book is
    silent on a roll already made; this is a project rule (Combat Design
    section 5): one blow has one level, and a resisting skill above 100% is
    worth more than one of 100.

    `modifier` is the caller's to compose, as with skill_check (whether a
    wound's Resilience takes the physical modifier is OQ-SC1).

    Args:
        made (dict): A successful skill_check result, the roll being resisted.
            Returned as it came: not copied and never written to.
        skill (int): The resisting side's effective skill %.
        modifier (int): Situational modifier for the resisting side.

    Returns:
        dict: {
            "resisted" (bool): True if the resisting side won.
            "made" (dict): `made`, the same object. Its "target" is the target
                the roll was made against, not lowered.
            "resisting" (dict): the resisting side's skill_check result; its
                "target" is already lowered by the excess.
            "excess" (int): the over-100% penalty (0 in the ordinary case).
        }

    Raises:
        ValueError: if `made` is not a successful roll.
    """
    if not made.get("success"):
        raise ValueError("opposed_against needs a successful made roll; got a failed one")

    excess = _excess(made["target"], int(skill) + int(modifier))
    resisting = skill_check(skill, int(modifier) - excess)
    winner = _judge(made, resisting, first_target=made["target"] - excess)
    return {
        "resisted": winner == DEFENDER,
        "made": made,
        "resisting": resisting,
        "excess": excess,
    }


# --- Levels of success, compared -------------------------------------------
_SUCCESSES = (CRITICAL, SUCCESS)


def compare_levels(attacker_level, defender_level):
    """
    Compare two levels of success with no opposed test: attack against parry
    (core rulebook, "Levels of Success" table, p.131; pp.129, 131).

    Both sides have already rolled. If neither succeeded -- failure or fumble
    against failure or fumble -- the table's cell is "--": nobody gains a
    level, though failure outranks fumble. Otherwise the winner is the side
    with the higher level, and `levels` is the number of steps between the
    two (1-3), each worth one Combat Manoeuvre. Equal levels give nobody a
    level.

    The result is `None` and not STALEMATE when nobody wins: STALEMATE means
    *roll again later* (p.45), while "--" here only means that no manoeuvre is
    gained -- the attack may still have hit. A defender with no Combat Action
    left, or who does not parry, is treated as having automatically rolled a
    Failure (p.131): pass FAILURE for that side.

    No die is rolled and the over-100% rule does not apply: attack against
    parry is not an opposed test (Combat Design section 1, point 3; OQ-SC2).

    Args:
        attacker_level (str): CRITICAL, SUCCESS, FAILURE or FUMBLE.
        defender_level (str): The same, for the defender.

    Returns:
        dict: {
            "winner" (str or None): "attacker", "defender", or None.
            "levels" (int): 0-3, the steps the winner gained (0 if None).
        }

    Raises:
        ValueError: if either level is not one of the four constants.
    """
    for level in (attacker_level, defender_level):
        if level not in _LEVEL_RANK:
            raise ValueError(f"not a level of success: {level!r}")

    if attacker_level not in _SUCCESSES and defender_level not in _SUCCESSES:
        return {"winner": None, "levels": 0}

    difference = _LEVEL_RANK[attacker_level] - _LEVEL_RANK[defender_level]
    if difference == 0:
        return {"winner": None, "levels": 0}
    return {"winner": ATTACKER if difference > 0 else DEFENDER, "levels": abs(difference)}
