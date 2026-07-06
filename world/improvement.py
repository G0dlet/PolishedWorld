"""
world/improvement.py

Mongoose Legend skill-improvement primitive for PolishedWorld.

This is the single source of truth for *how much* a skill grows when it
improves. Like world/skillcheck.py it is a **pure** function (no Evennia
objects, no I/O, no trait reads) so it can be unit-tested in isolation and
reused by any system that decides a skill should get a chance to improve.

It deliberately does NOT decide *whether* a skill may improve (that eligibility
gate -- success-only, real-difficulty, cooldown -- lives one layer up on the
Character, see improve_skill_on_use). This module only resolves the roll once
that decision has been made.

Rule implemented (Mongoose Legend core rulebook, "Using Improvement Rolls",
p.70-71), verified verbatim against Legend.pdf:

    - Roll 1D100 and add the *full* INT Characteristic to the result.
      (This is the whole INT score, not a table-derived "modifier" -- the CHA
      table governs the *number* of Improvement Rolls, not this roll's bonus.)
    - If (1D100 + INT) is GREATER THAN the skill's current score, the skill
      increases by 1D4+1 points.
    - If (1D100 + INT) is EQUAL TO OR LESS THAN the current score, the skill
      increases by exactly 1 point.

So the gain is never zero: the guaranteed +1 is the floor, and beating your own
current skill with the roll earns the larger 1D4+1 jump.

Self-throttling by design: because the roll must *exceed* the current skill, a
low skill is beaten easily (frequent 1D4+1 jumps) while a high skill is beaten
rarely (mostly the +1 floor). This is the pacing engine -- no hidden XP
accumulator is needed. It is exactly why on-use improvement stays legible on the
raw percentage: the curve flattens itself as mastery grows.

Deliberate deferral -- skills above 100%:
    The rulebook adds a second band for skills over 100% (roll against a target
    of 100 instead of the skill, adding only a fraction of INT: half for
    101-200%, a quarter for 201-300%, and so on). PolishedWorld caps skills at
    100 for the MVP, so that band is currently unreachable dead code -- the same
    stance world/skillcheck.py's opposed_check takes on its own >100% rule.
    It is intentionally NOT implemented here. When the cap is lifted (skill
    progression epic), extend beat-resolution as:
        target = 100 if skill_value > 100 else skill_value
        int_applied = int_char // (2 ** max(0, (skill_value - 1) // 100))
        beat = (roll + int_applied) > target
    and keep the 1D4+1 / +1 gain unchanged.
"""

from random import randint


def improvement_roll(skill_value, int_char):
    """
    Resolve a single Mongoose Legend skill-improvement roll (<=100% band).

    Args:
        skill_value (int): The skill's current score, e.g. a Craft skill of 41.
            Coerced with int(); trait values are ints but a caller might pass a
            buff-derived float, mirroring skillcheck.py's defensive coercion.
        int_char (int): The character's INT Characteristic (the full score,
            added flat to the 1D100). Also int()-coerced.

    Returns:
        dict: A result with keys:
            - "gained" (int): points the skill should increase by. Always >= 1;
              1D4+1 (i.e. 2-5) when the roll beats the current skill, else 1.
            - "roll" (int): the raw 1D100 result (1-100).
            - "int_bonus" (int): the INT that was added to the roll.
            - "total" (int): roll + int_bonus, the value tested against the skill.
            - "beat" (bool): True if total > skill_value (the 1D4+1 outcome),
              False for the guaranteed +1 floor. Handy for messaging ("you
              learned something new" vs "steady practice").
    """
    # Defensive int() coercion: keeps the comparison well-defined if a float
    # modifier ever reaches us (same rationale as skillcheck.skill_check).
    skill_value = int(skill_value)
    int_bonus = int(int_char)

    roll = randint(1, 100)
    total = roll + int_bonus

    # The roll must strictly EXCEED the current skill for the larger jump;
    # equal-or-less earns only the guaranteed floor of +1.
    beat = total > skill_value
    gained = (randint(1, 4) + 1) if beat else 1

    return {
        "gained": gained,
        "roll": roll,
        "int_bonus": int_bonus,
        "total": total,
        "beat": beat,
    }
