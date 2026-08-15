"""
world/progression.py

Skill-progression XP curve for PolishedWorld. Stage 4.5, Component A.1.

This is the single source of truth for the *shape* of skill progression: how
much lifetime XP stands between one whole percentage point and the next. Like
world/skillcheck.py and world/improvement.py it holds no Evennia objects, does
no I/O and reads no traits, so it unit-tests in isolation.

NOTHING CALLS THIS MODULE YET. That is deliberate, not an oversight. Component
A is arithmetic with an exact answer, and arithmetic with an exact answer should
be provable before anything depends on it. Component B adds storage (still with
no consumer); only Component C changes what a player experiences.

WHY XP AT ALL (roadmap Rev 14 decision log)
-------------------------------------------
Legend's Improvement Roll is built for a table that meets once a week. Measured
against the shipped system at INT 12, **43 successful crafts take a skill from
0 to 100** -- roughly 22 minutes of pure cooldown. In a world that is online
continuously that is not a pacing curve at all. This epic keeps the roll
verbatim (P-3) and changes only what its result *means*: a beat banks 2-5 XP
instead of adding 1D4+1 points, the floor banks 1 XP, and an exponential
threshold stands between each whole point.

The percentage stays the single mechanical truth. Every skill check, every
`min_skill` gate, every tool buff still reads `skill.current`; none of them
learns that XP exists. What changes is only how often `.current` moves.

THE CURVE
---------
Let ``r = 2 ** (1 / SPAN)``. The cost of the *n*-th point is ``BASE * r^(n-1)``,
so the per-point cost doubles every SPAN points (P-4). The total XP needed to
*be* at level ``L`` is the geometric sum:

    threshold(L) = BASE * (r^L - 1) / (r - 1)          threshold(0) = 0

Closed form, not a table. A table has to end somewhere and P-7 says the curve
does not; a table would also have to be regenerated on every recalibration,
which turns a settings change back into a migration -- exactly what P-1 exists
to prevent.

At the provisional calibration (BASE=6, SPAN=20):

    level   1 ->        6 XP
    level  20 ->      170 XP
    level  50 ->      792 XP
    level 100 ->    5 274 XP
    level 150 ->   30 628 XP        (P-7: above 100 is reachable, not capped)

CALIBRATION IS PROVISIONAL (P-5)
--------------------------------
The two constants live in `server/conf/settings.py` and are read on every call
(not captured at import) so that a recalibration is a `@reload` rather than a
restart, and so that tests can drive the functions through `override_settings`.
Measured cost of that choice: ~56 ns per call. A craft happens on the order of
once per 30 seconds per player.

Generous now, tightened never: lowering the curve later is free, raising it
de-levels people who already earned their number.

PURITY NOTE
-----------
Unlike skillcheck.py and improvement.py this module does import
`django.conf.settings`. That is Django, not Evennia -- the module still has no
Evennia import, no database access and no trait reads -- but the purity is one
shade lower than its two sibling modules and the difference is worth knowing
before you copy this file as a template. The precedent for reading settings
inside the call rather than at import is `world/gametime_utils.py`.

WHY THE BAR RENDERER LIVES HERE (Component D.1)
-----------------------------------------------
`render_progress_bar` is presentation, and this module is otherwise arithmetic.
It sits here anyway because the alternatives are worse: a module of its own would
import nothing this file does not already have and would exist to hold one pure
function, and putting it on the Character would make the bar untestable without
an object graph -- the exact cost the A/B split was drawn to avoid. It reads no
traits, holds no Evennia objects and does no I/O, so the claim at the top of this
docstring survives intact; what it costs is that "the shape of progression" now
includes the shape it is *drawn* as.

The renderer takes a fraction, not the `progress_within_level` tuple. Feeding it
the tuple would couple the two functions and would let a caller pass a bar's
worth of state around; a float in [0, 1] is the whole of what a bar needs.

WHY THE CORRECTION LOOPS IN level_for_xp() ARE BOUNDED
------------------------------------------------------
Two separate arguments, one per loop. They are not the same argument and
deleting either loop is not equally safe:

* **Step up (needed by construction).** `xp_threshold` floors, so
  ``thr(L) <= S(L)`` where S is the exact sum. The seed counts levels whose
  *exact* threshold is <= x; the true level counts levels whose *floored*
  threshold is <= x, a superset. Hence ``seed <= true`` always. It can never be
  low by 2: that would need S(L) and S(L+1) both inside the same unit interval
  (x, x+1), but the gap between them *is* the cost of point L+1, which is
  ``BASE * r^L >= BASE >= 1``. Impossible. One iteration, provably -- which is
  also why `_calibration()` clamps BASE to a minimum of 1: at BASE = 0 every
  threshold collapses to 0, monotonicity dies, and this loop does not terminate.

* **Step down (needed in practice).** The argument above assumes exact
  arithmetic; `log()` is not exact. Measured over 0..500: at the shipped
  (6, 20) this loop never fires, but at (6, 7) removing it fails 176 cases and
  at (1, 5) it fails 268. Since P-5 guarantees these constants will be
  recomputed, the loop stays and the calibration-matrix test exists to keep it
  honest -- at (6, 20) alone the suite passes with this loop deleted.
"""

from math import floor, log

from django.conf import settings

# Used only if the settings are absent -- a bare `evennia shell` against a
# half-configured game, or an import from a context that never loaded our
# settings module. Kept identical to the shipped values so a missing setting
# degrades to "same behaviour" rather than "different curve, silently".
_DEFAULT_XP_BASE = 6
_DEFAULT_XP_DOUBLING_SPAN = 20


def _calibration():
    """
    Read the live curve calibration.

    Read per call rather than captured at import (locked Decision 1B) so that
    `override_settings` works in tests and a recalibration takes effect on
    `@reload`.

    Returns:
        tuple: ``(base, span, ratio)`` where ``ratio = 2 ** (1 / span)``.

    Both values are clamped to a minimum of 1. This is not cosmetic defence, and
    the two failure modes are different:

        span = 0 -> ZeroDivisionError inside the ``1 / span`` exponent.
        base = 0 -> ZeroDivisionError inside level_for_xp's seed (which divides
                    by base) and, were anything to reach past it, a
                    non-terminating step-up loop: every threshold flattens to 0,
                    so ``xp_threshold(L + 1) <= total_xp`` is true forever.

    A typo in settings.py should not be able to hang the server inside a craft.
    """
    base = max(1, int(getattr(settings, "SKILL_XP_BASE", _DEFAULT_XP_BASE)))
    span = max(1, int(getattr(settings, "SKILL_XP_DOUBLING_SPAN", _DEFAULT_XP_DOUBLING_SPAN)))
    return base, span, 2 ** (1 / span)


def xp_threshold(level):
    """
    Lifetime XP required to stand at ``level``.

    Args:
        level (int): the skill level (a permanent `.current` percentage).
            int()-coerced, mirroring the defensive coercion in skillcheck.py and
            improvement.py. Levels above 100 are legal and meaningful (P-7).

    Returns:
        int: floored cumulative XP. ``xp_threshold(0) == 0``.

        Strictly increasing: each per-point cost is ``BASE * r^(n-1) >= BASE
        >= 1``, so flooring the cumulative sum can never produce two equal
        thresholds.

    Non-positive levels clamp to 0 (locked Decision 3A) rather than raising --
    this module sits under a live craft and must not be able to abort one.
    """
    level = int(level)
    if level <= 0:
        return 0
    base, _span, ratio = _calibration()
    return floor(base * (ratio ** level - 1) / (ratio - 1))


def level_for_xp(total_xp):
    """
    The level a given lifetime XP total buys -- the inverse of xp_threshold.

    Args:
        total_xp (int): lifetime-total XP for one skill (P-1: the sole persisted
            truth). int()-coerced; non-positive clamps to level 0.

    Returns:
        int: the highest ``L`` with ``xp_threshold(L) <= total_xp``.

    Inverts the closed form for a seed, then applies two bounded corrections
    (see the module docstring for why each is bounded, and why they are bounded
    for different reasons). O(1) with no precomputed table, which is what makes
    P-7's uncapped curve free rather than a special case.
    """
    total_xp = int(total_xp)
    if total_xp <= 0:
        return 0

    base, _span, ratio = _calibration()

    # Seed: solve threshold(L) = total_xp for L, ignoring the flooring.
    level = floor(log(1 + total_xp * (ratio - 1) / base) / log(ratio))
    if level < 0:
        # Only reachable via float underflow on a tiny total_xp; the loops below
        # would fix it anyway, but a negative seed would make the step-down
        # guard read strangely.
        level = 0

    # Step up: at most one iteration, by construction (BASE >= 1).
    while xp_threshold(level + 1) <= total_xp:
        level += 1

    # Step down: guards against log()'s inexactness. Never fires at (6, 20);
    # fires at other calibrations, and P-5 promises other calibrations.
    while level > 0 and xp_threshold(level) > total_xp:
        level -= 1

    return level


def progress_within_level(total_xp):
    """
    How far into the current level a lifetime XP total stands.

    Args:
        total_xp (int): lifetime-total XP for one skill.

    Returns:
        tuple: ``(earned, needed, fraction)`` where

            - ``earned`` (int): XP banked since reaching the current level.
            - ``needed`` (int): XP the current level costs end-to-end.
            - ``fraction`` (float): ``earned / needed``, in ``[0.0, 1.0)``.

    Pure arithmetic on the two surrounding thresholds. Nothing here is stored
    (P-1), and the progress bar Component D draws is computed from this on read
    -- a bar stored beside a derived value can drift out of step with it; a bar
    computed on read cannot.

    The ``needed <= 0`` branch is unreachable while xp_threshold is strictly
    increasing. It exists so that a future miscalibration degrades to "bar reads
    empty" instead of ZeroDivisionError inside a craft.
    """
    total_xp = max(0, int(total_xp))
    level = level_for_xp(total_xp)

    level_floor = xp_threshold(level)
    level_ceiling = xp_threshold(level + 1)

    needed = level_ceiling - level_floor
    earned = total_xp - level_floor
    fraction = (earned / needed) if needed > 0 else 0.0

    return (earned, needed, fraction)


# Bar glyphs. NEVER use "|" in bar art: Evennia's colour parser reads "|_" as a
# space, "|/" as a line break, "|-" as a tab and "||" as a literal pipe, so a bar
# drawn with pipes renders as garbage (decomposition §6, D.1).
#
# The partials are the reason this is not a plain "█/░" bar, and the reason is a
# measurement rather than a preference -- see render_progress_bar's docstring.
_BAR_FULL = "\u2588"        # █  FULL BLOCK
_BAR_EMPTY = "\u2591"       # ░  LIGHT SHADE
_BAR_PARTIALS = (
    "",                     # 0/8 -- no leading-edge cell at all
    "\u258f",               # ▏ 1/8
    "\u258e",               # ▎ 2/8
    "\u258d",               # ▍ 3/8
    "\u258c",               # ▌ 4/8
    "\u258b",               # ▋ 5/8
    "\u258a",               # ▊ 6/8
    "\u2589",               # ▉ 7/8
)


def render_progress_bar(fraction, length=20):
    """
    Draw a filled/empty bar for a fraction in [0, 1].

    Args:
        fraction (float): how full the bar is, normally
            `progress_within_level(total)[2]`. Clamped to [0.0, 1.0]; a
            non-numeric or NaN value degrades to an empty bar rather than
            raising, because this runs inside a live craft.
        length (int): the bar's width in terminal cells. Minimum 1.

    Returns:
        str: colour-coded bar art, e.g. ``"|g███▍|x░░░░░░░░░░░░░░░░|n"``. Always
            exactly `length` visible cells wide, at every fraction.

    WHY EIGHTH-BLOCKS AND NOT WHOLE CELLS
    -------------------------------------
    A whole-cell bar goes silent at high skill, which is the failure D.1 exists
    to cure, displaced one level down. `needed` grows exponentially while a tick
    still banks only 1-5 XP, so the share of the bar one tick moves shrinks all
    the way up the curve. Measured over 10 000 simulated ticks at INT 12, the
    proportion of ticks that change at least one cell of a 20-cell bar:

        skill 20 -> 1.00      skill 60 -> 0.69      skill 90 -> 0.23

    At skill 90 four crafts in five would produce a message identical to the
    last one. With an eighth-block leading edge the bar has 8x the resolution
    and **every single XP is visible up to needed = 160**, which the curve does
    not exceed until skill ~95:

        level  20 (needed  12) -> 12/12 distinct bars
        level  60 (needed  48) -> 48/48
        level  90 (needed 136) -> 136/136
        level  99 (needed 186) -> 160/186, so 14% of single-XP steps are invisible

    Stated honestly: above skill ~95 the bar is again coarser than the grain.
    That band is short, it is the band D.2 is about to make unbounded, and no
    fixed-width bar can resolve a `needed` that grows without limit -- so it is
    a known and accepted floor, not an oversight.
    """
    length = max(1, int(length))

    try:
        fraction = float(fraction)
    except (TypeError, ValueError):
        fraction = 0.0
    if fraction != fraction:            # NaN is the only value unequal to itself
        fraction = 0.0
    fraction = min(1.0, max(0.0, fraction))

    # Work in eighths of a cell, then split into whole cells plus a leading edge.
    eighths = min(length * 8, max(0, int(fraction * length * 8)))
    full, remainder = divmod(eighths, 8)

    filled = _BAR_FULL * full + _BAR_PARTIALS[remainder]
    # The partial glyph occupies a whole cell, so it is subtracted from the
    # empty run -- this is what keeps the rendered width constant.
    empty = _BAR_EMPTY * (length - full - (1 if remainder else 0))

    return f"|g{filled}|x{empty}|n"
