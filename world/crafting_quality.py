"""
world/crafting_quality.py

Single source of truth for crafting QUALITY BANDS.

A craft stamps a numeric `obj.db.quality` (world/crafting_base.py::_quality_for,
derived from the Mongoose Legend skill-check tier). Recipes are NOT meant to read
that number directly: this module owns the mapping from a raw quality value to a
named band, so every recipe classifies quality the same way and none hard-codes a
magic threshold.

Band scale (best -> worst), against the values crafting_base can actually produce
({25 fumble, 50 failure, 100 success, 100+crit_score critical}):

    superior     quality  > 100   -- a critical WITH bonus (crit_score >= 1);
                                     crit_score scales *within* this band.
    serviceable  quality == 100    -- an ordinary success.
    poor         50 <= quality < 100
    shoddy       quality  < 50

Design invariant: superior == the critical tier. ONE deliberate edge: a critical
rolled at a modified skill of 0-9 has crit_score == 0 (skillcheck:
crit_score = max(0, target // 10)), so its quality is exactly 100 and it bands as
`serviceable`. This is intentional under the "quality -> capability" principle:
that item's capability is identical to a success (quality 100), so the band
honestly reports the ITEM, not the roll -- and the player still saw the critical
flavour at craft time. Only a critical that earned bonus points (modified skill
>= 10) is superior, which is every realistic crafter.

Pure module: no Evennia objects, no I/O -- unit-testable in `evennia shell`.
"""

# Band names, best -> worst. Import these rather than bare strings so a rename is
# one edit and a typo is an ImportError, not a silent misclassification.
SUPERIOR = "superior"
SERVICEABLE = "serviceable"
POOR = "poor"
SHODDY = "shoddy"

# Anchors. superior is strictly ABOVE the success ceiling, so it has no named
# floor of its own -- it is "> SUCCESS_CEILING" in quality_band.
SUCCESS_CEILING = 100   # an ordinary success stamps exactly this
POOR_FLOOR = 50         # a failure stamps exactly this


def quality_band(quality):
    """Classify a numeric craft quality into a named band.

    Args:
        quality (int): the value stamped on obj.db.quality by crafting_base.

    Returns:
        str: one of SUPERIOR, SERVICEABLE, POOR, SHODDY.
    """
    q = int(quality)
    if q > SUCCESS_CEILING:
        return SUPERIOR
    if q >= SUCCESS_CEILING:      # only exactly the ceiling (100) reaches here
        return SERVICEABLE
    if q >= POOR_FLOOR:
        return POOR
    return SHODDY


def band_alias(band, key):
    """Distinguishing alias for a crafted item of `band`, or None.

    Only SUPERIOR items get an individuating alias ("superior <key>"), so a
    player can target the good one in a pile of otherwise-identical crafts (this
    pairs with the multimatch-disambiguation goal). Lesser bands return None --
    we don't want "poor waterskin" aliases cluttering the namespace.

    Args:
        band (str): a band name from quality_band().
        key (str): the crafted object's key, e.g. "waterskin".

    Returns:
        str | None: "superior <key>" for SUPERIOR, else None.
    """
    if band == SUPERIOR:
        return f"{SUPERIOR} {key}"
    return None
