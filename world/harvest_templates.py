"""
world/harvest_templates.py
==========================

Single source of truth for *what* a creature corpse yields when harvested.

A creature carries a flat `harvest_template` key (e.g. "rabbit"); its corpse
copies that into `db.creature_type`. This module turns that key into the actual
part data the harvest command (H4.3) needs: which skill gates each part, its
Mongoose Legend difficulty, how much it yields from the creature's SIZ, how far
into decay it survives, and which prototype to spawn.

Design (pure data + pure helpers, mirroring world/skillcheck.py):
    No Evennia objects are touched here. Everything is plain dict/int math, so
    the whole module is unit-testable in isolation and has no import-time side
    effects. The command layer (H4.3) does all the I/O -- claiming, spawning,
    messaging -- and reads its rules from here.

Skill mapping (Arms of Legend, remapped to skills that exist in PolishedWorld):
    AoL puts meat on Survival (Easy, +20) and hide on Craft Leatherworking
    (Normal, 0). "survival" is our trait-gauge category, not a skill, so meat is
    remapped to `hunting`; hide stays on the generic `craft` skill. Both skills
    are granted at character creation, so no harvest is impossible-by-default.

    The skill lives in the *data*, per part, on purpose: moving hide onto a
    future dedicated `craft_leatherworking` skill is then a one-line change here,
    not a command rewrite. That is the seam, kept honest.

Yield (from PolishedWorld_Creature_Harvesting_Design.md):
    meat = SIZ // 2, hide = SIZ // 3, floored at 1 so small prey still gives
    something. A critical extraction yields 150% (rounded up); a normal success
    yields the base; failure yields nothing (retryable); a fumble destroys the
    part (handled in the command, not here).

Decay gating:
    `max_stage` is the highest corpse decay stage at which a part is still
    harvestable. Soft parts (meat, hide) survive through STALE and are gone by
    ROTTING. Imported from typeclasses.corpse so the integers can never drift
    from the corpse's own stage definitions.
"""

from math import ceil

# Decay-stage constants owned by the Corpse typeclass. Importing them (instead of
# hardcoding 0..3) keeps max_stage tied to the single definition of those stages.
from typeclasses.corpse import FRESH, STALE, ROTTING, SKELETON  # noqa: F401

# Critical extractions yield this multiple of the base (rounded up).
CRITICAL_YIELD_MULTIPLIER = 1.5


# ---------------------------------------------------------------------------
# Template data
# ---------------------------------------------------------------------------
# Shape of a part entry:
#   "skill"        (str): Character.skills key rolled for this part.
#   "difficulty"   (int): situational modifier passed to skill_check (Legend
#                         difficulty band: Easy +20, Normal 0, Hard -40, ...).
#   "yield_divisor"(int): base yield = max(1, SIZ // divisor).
#   "max_stage"    (int): highest decay stage at which the part is harvestable.
#   "prototype"    (str): prototype_key spawned per yielded unit (world/prototypes.py).
#
# Adding a creature = adding a key here whose part prototypes exist. The command
# never changes.

HARVEST_TEMPLATES = {
    "rabbit": {
        "meat": {
            "skill": "hunting",
            "difficulty": 20,          # Easy: field-dressing small prey
            "yield_divisor": 2,        # SIZ 4 -> 2 portions
            "max_stage": STALE,        # soft part: gone once ROTTING
            "prototype": "rabbit_meat",
        },
        "hide": {
            "skill": "craft",
            "difficulty": 0,           # Normal: skinning for usable hide
            "yield_divisor": 3,        # SIZ 4 -> 1 hide
            "max_stage": STALE,        # soft part: gone once ROTTING
            "prototype": "raw_hide",
        },
    },
}


# ---------------------------------------------------------------------------
# Lookup helpers (return None rather than raising; the command decides messaging)
# ---------------------------------------------------------------------------

def get_template(template_key):
    """
    Return the parts dict for a creature template, or None if unknown.

    Args:
        template_key (str): the corpse's creature_type (e.g. "rabbit").

    Returns:
        dict | None: {part_key: part_data} or None for an unknown template.
    """
    return HARVEST_TEMPLATES.get(template_key)


def get_part(template_key, part_key):
    """
    Return a single part's data dict, or None if the template or part is unknown.

    Args:
        template_key (str): the corpse's creature_type.
        part_key (str): the requested part (e.g. "meat", "hide").

    Returns:
        dict | None: the part data, or None if not found.
    """
    template = get_template(template_key)
    if not template:
        return None
    return template.get(part_key)


def list_parts(template_key):
    """
    Return the list of part keys a template offers (empty list if unknown).

    Lets the command answer a bare `harvest <corpse>` with the available parts.
    """
    template = get_template(template_key)
    return list(template) if template else []


# ---------------------------------------------------------------------------
# Yield math (pure; floored at 1; critical scaling centralised here)
# ---------------------------------------------------------------------------

def compute_yield(part_data, siz, critical=False):
    """
    How many units of a part an extraction produces.

    Base = max(1, SIZ // yield_divisor). A critical scales it by
    CRITICAL_YIELD_MULTIPLIER, rounded up. The floor of 1 means even a SIZ so
    small that integer division gives 0 still yields a single unit -- a
    successful extraction is never empty-handed.

    Args:
        part_data (dict): a part entry from a template.
        siz (int): the dead creature's SIZ (corpse.db.creature_siz).
        critical (bool): True for a critical-success extraction.

    Returns:
        int: number of units to spawn (>= 1).
    """
    divisor = part_data.get("yield_divisor", 1)
    # Defensive: a mis-authored template with divisor 0/negative must not crash
    # a live harvest. Fall back to "whole creature = 1 unit" rather than raising.
    if divisor < 1:
        divisor = 1
    base = max(1, int(siz) // divisor)
    if critical:
        return int(ceil(base * CRITICAL_YIELD_MULTIPLIER))
    return base
