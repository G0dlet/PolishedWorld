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
rarely (mostly the +1 floor). Measured over 400 simulated careers at INT 10, the
mean grain falls from 3.25 at skill 20 to 1.38 at skill 95 -- a factor of ~2.4.

SUPERSEDED (Stage 4.5, 2026-08-05): this docstring used to continue "This is the
pacing engine -- no hidden XP accumulator is needed", and that claim is now
false. It was measured and it was wrong by two orders of magnitude: 38 eligible
ticks took a Craft skill from 20 to 100, roughly 19 minutes of wall clock. A
factor of 2.4 is a texture, not a pacing curve.

The accumulator the old sentence ruled out is exactly what was built.
`Character.improve_skill_on_use` now banks this function's "gained" as lifetime
XP and derives the level from the total through the exponential curve in
`world/progression.py` (~2 931 ticks over the same span, ~77x). The self-throttle
survives as a mild *third* ramp on top of the curve rather than as the mechanism.

What this module does is unchanged either way (P-3): the roll still takes the
skill's level, still returns 1D4+1 on a beat and 1 on the floor. Only its
caller's interpretation of that number changed.

Skills above 100% -- DELIVERED (Stage 4.5, D.2, 2026-08-16):
    The rulebook's second band is now implemented in improvement_roll below.
    Above 100% the roll is tested against a flat target of 100 instead of
    against the skill, and only a fraction of INT is added: half in 101-200, a
    quarter in 201-300, and so on. The 1D4+1 / +1 gain is untouched (P-3).

    This docstring used to describe that band as "currently unreachable dead
    code" and gave the three expressions as a future instruction. Both halves
    are now false: the band is live, and there is nothing left to do. The text
    is replaced rather than annotated, because a deferral note left standing
    beside the code that fulfils it is the shape of claim this epic has had to
    retract four times.

    ⚠️ world/skillcheck.py's opposed_check has its OWN unimplemented >100% rule
    (the highest mastered skill is dropped to 100 and the excess penalises
    everyone). D.2 deliberately did not touch it. The old text above bundled the
    two deferrals into one sentence, which made them look like one decision;
    they are not, and lifting this cap does not decide that one.

Where the curve takes over from the roll:
    Nothing here caps anything any more, and nothing needs to -- the curve in
    world/progression.py has no table and no terminus, and it strangles the top
    of the scale on its own. Measured at (BASE=6, SPAN=20) with INT 12: point
    100->101 costs 192 XP (~148 eligible ticks), 150->151 costs 1 086 (~944
    ticks, ~8 h of pure 30 s cooldown), and 200->201 costs 6 144 (~44 h). A
    numeric ceiling on top of that would be a second throttle doing the curve's
    job -- the same "two knobs, one job" mistake that froze improvement_cooldown.
"""

from random import randint


def improvement_roll(skill_value, int_char):
    """
    Resolve a single Mongoose Legend skill-improvement roll (both bands).

    Args:
        skill_value (int): The skill's current score, e.g. a Craft skill of 41.
            Coerced with int(); trait values are ints but a caller might pass a
            buff-derived float, mirroring skillcheck.py's defensive coercion.
            Scores above 100 are legal and select the second band -- see below.
        int_char (int): The character's INT Characteristic (the full score).
            Also int()-coerced. Note that this is the score, not necessarily the
            figure added to the roll: above 100% only a fraction of it applies.

    Returns:
        dict: A result with keys:
            - "gained" (int): points the skill should increase by. Always >= 1;
              1D4+1 (i.e. 2-5) on a beat, else 1. Identical in both bands (P-3).
            - "roll" (int): the raw 1D100 result (1-100).
            - "int_bonus" (int): the INT that was added to the roll -- the
              APPLIED figure, already divided down by the band. Below 101 it
              equals int_char; at 150 it is half of it; at 250, a quarter.
              ⚠️ D.2 chose the applied value over the raw score deliberately.
              "total" is documented as roll + int_bonus, and that identity is
              the only thing that makes these three keys readable together. A
              raw int_bonus would have quietly falsified the line above it the
              moment anyone passed 100 -- the same shape of stale claim this
              epic has retracted four times, written with open eyes.
            - "total" (int): roll + int_bonus, the value tested against the
              band's target.
            - "beat" (bool): True if total > the band's target (the 1D4+1
              outcome), False for the guaranteed +1 floor. Handy for messaging
              ("you learned something new" vs "steady practice").
    """
    # Defensive int() coercion: keeps the comparison well-defined if a float
    # modifier ever reaches us (same rationale as skillcheck.skill_check).
    skill_value = int(skill_value)
    int_char = int(int_char)

    # Legend's two bands (core rulebook, "Using Improvement Rolls", p.70-71).
    # Two things change above 100% and nothing else does:
    #
    #   1. The roll is tested against a FLAT 100, never against the skill.
    #      Without this a skill of 150 would need a 1D100 of 151 to beat itself:
    #      the band would be a hard stop wearing a curve's clothes, and lifting
    #      the trait cap would have bought nothing.
    #   2. Only a fraction of INT is added -- half in 101-200, a quarter in
    #      201-300, and so on. That is the rulebook's own throttle, and it is
    #      what stops a flat target of 100 from making the beat EASIER at 150
    #      than it was at 99. The step is abrupt by design: at INT 12 the beat
    #      chance is 12% at skill 100 and 6% at skill 101.
    #
    # ⚠️ The max(0, ...) is load-bearing for skill_value <= 0, not defensive
    # tidiness. Python floors toward negative infinity, so (0 - 1) // 100 == -1,
    # and 2 ** -1 is the FLOAT 0.5 -- `int_char // 0.5` would DOUBLE the bonus
    # and hand back a float. Remove the guard and the band inverts at the bottom
    # of the scale instead of failing loudly.
    target = 100 if skill_value > 100 else skill_value
    int_bonus = int_char // (2 ** max(0, (skill_value - 1) // 100))

    roll = randint(1, 100)
    total = roll + int_bonus

    # The roll must strictly EXCEED the band's target for the larger jump;
    # equal-or-less earns only the guaranteed floor of +1. The `>` is what puts
    # a skill of exactly 100 in the FIRST band (target 100, full INT) and 101 in
    # the second -- that boundary is a decision, not an accident of arithmetic.
    beat = total > target
    gained = (randint(1, 4) + 1) if beat else 1

    return {
        "gained": gained,
        "roll": roll,
        "int_bonus": int_bonus,
        "total": total,
        "beat": beat,
    }


def tier_for(value, descs):
    """
    Resolve which description tier an integer skill value falls in.

    Mirrors Evennia's CounterTrait.desc() upper-bound-inclusive lookup, but on
    an *explicit* integer instead of reading the trait's live ``.value``. That
    distinction is the whole point of this helper: ``.value`` is
    ``(current + mod) * mult`` and so is inflated by any active tool buff,
    whereas skill improvement -- and the "reached a new tier" celebration built
    on it -- must read the *permanent* ``.current`` level. Feeding the raw
    old/new ints from improve_skill_on_use keeps tier detection buff-proof: a
    +20 knife must never fake a rank-up, and must never mask a real one.

    Kept pure (no trait objects) like the rest of this module so it unit-tests
    in isolation, exactly as world/skillcheck.py's primitives do.

    Args:
        value (int): the skill score to classify (a permanent .current level).
            int()-coerced, mirroring improvement_roll's defensive coercion.
        descs (dict or None): the trait's {upper_bound_inclusive: label} map,
            e.g. {0: "helpless", 20: "novice", 40: "competent", ...}. Iterated
            in insertion order -- exactly as Evennia does -- and our maps are
            declared ascending, so order is meaningful and correct.

    Returns:
        str: the label for the band ``value`` falls in. A value above the
            highest bound returns the highest label (Evennia's own rule). Returns
            "" when ``descs`` is empty or None, matching desc()'s miss behaviour
            so callers can treat "" as "no tier information -> skip".
    """
    if not descs:
        return ""
    highest = ""
    value = int(value)
    for bound, label in descs.items():
        highest = label
        if value <= bound:
            return label
    # Above every bound -> the top tier (mirrors CounterTrait.desc()).
    return highest
