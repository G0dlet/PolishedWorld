"""
One-off character data migrations for PolishedWorld.

at_object_creation only runs for NEW objects, so any skill/attribute added
there must be backfilled separately onto characters that already exist.
These helpers are ad-hoc and meant to be run once after such a change.

Design rule: keep every migration IDEMPOTENT -- safe to run more than once
without clobbering player progress. This matters specifically because
TraitHandler.add(force=True) (the default) does remove()+recreate on an
existing trait, which would wipe a skill's `current` value. We therefore
guard each grant with an explicit "does it already exist?" check.

Run in-game (recommended -- same process as the live game):
    @py from world.character_migrations import backfill_hunting; backfill_hunting()

Run from a stopped server's shell:
    evennia shell
    >>> from world.character_migrations import backfill_hunting
    >>> print(backfill_hunting())
"""

from evennia.contrib.rpg.rpsystem import RPSystemCmdSet
from evennia.utils import logger

from typeclasses.characters import Character


# Keep in sync with the matching self.skills.add("hunting", ...) call in
# Character.at_object_creation. Single source of truth for the backfill so a
# backfilled character is byte-for-byte identical to a freshly created one.
#
# ⚠️ NO "max" KEY (Stage 4.5, D.2, P-7). It was 100 and it is deliberately
# absent, not accidentally missing. A CounterTrait with max set clamps inside
# its own setter, so a backfilled character carrying max=100 would have its
# `.current` silently pinned at 100 while its lifetime XP kept climbing --
# breaking `.current == level_for_xp(total)` in the one place no reader looks.
# Character.improve_skill_on_use repairs pre-D.2 traits on first use; this file
# must not manufacture new ones for it to repair.
HUNTING_SKILL_DEFAULTS = {
    "trait_type": "counter",
    "base": 25,
    "current": 25,
    "mod": 0,
    "min": 0,
    "descs": {
        0: "helpless",
        20: "novice",
        40: "competent",
        60: "tracker",
        80: "hunter",
        95: "master hunter",
    },
}


def backfill_hunting():
    """
    Grant the 'hunting' skill to every existing character that lacks it.

    Idempotent: characters that already have 'hunting' are skipped, preserving
    any skill progress (see module docstring re: force=True). Safe to re-run.

    all_family() is used so the migration also covers any future Character
    subclasses, not just the exact base typeclass.

    Returns:
        str: Human-readable summary (granted vs. skipped), wrapped as a string
            so it prints cleanly from @py without being parsed as (text, opts).
    """
    granted, skipped = [], []

    for char in Character.objects.all_family():
        try:
            if char.skills.get("hunting") is not None:
                skipped.append(char.key)
                continue
            char.skills.add("hunting", "Hunting", **HUNTING_SKILL_DEFAULTS)
            granted.append(char.key)
        except Exception as err:
            # One broken character must not abort the whole batch.
            skipped.append(f"{char.key} (ERROR: {err})")

    return (
        f"backfill_hunting: granted to {len(granted)} character(s) {granted}; "
        f"skipped {len(skipped)} {skipped}."
    )


# ---------------------------------------------------------------------------
# Names (Stage 5, NM-T4): the rpsystem contrib's data on older characters
# ---------------------------------------------------------------------------

# OQ-NM6: one placeholder for every character made before the short
# description had a source. Lower case, because the contrib and $You() add
# the capital where a sentence starts.
NAMES_PLACEHOLDER_SDESC = "a quiet traveller"

# The contrib's own default (rpsystem.py:1567). Nobody chose it, so a character
# that has it is treated as one that has none.
CONTRIB_DEFAULT_SDESC = "A normal person"

# What ContribRPObject / ContribRPCharacter.at_object_creation write
# (rpsystem.py:1322-1324, :1560-1562), with the values they write.
_NAMES_ATTRIBUTE_DEFAULTS = (
    ("_recog_ref2recog", dict),
    ("_recog_obj2recog", dict),
    ("pose", lambda: ""),
    ("pose_default", lambda: "is here."),
)


def backfill_names():
    """
    Give every existing character what the rpsystem contrib writes at creation.

    Names NM-T4 (Combat Decomposition NM8, OQ-NM6, Names UQ7). For each
    character in `Character.objects.all_family()`:

    * the two recog dictionaries, when missing. This is the one that matters:
      `RecogHandler.add` (rpsystem.py:836-837) writes into
      `attributes.get(name, default={})`, and with no Attribute that default
      is never saved -- a recog would last until the next reload;
    * `pose` and `pose_default`, when missing;
    * the placeholder short description, when `_sdesc` is missing, empty or
      the contrib's own *A normal person*;
    * no persistent `RPSystemCmdSet` (NM-T2 takes it off new characters).

    Idempotent: nothing a character already has is touched, and a second run
    reports `changed 0`. One broken character does not stop the batch.

    Returns:
        str: a summary for `@py ...; self.msg(backfill_names())`.
    """
    changed, unchanged, errors = [], 0, []

    for char in Character.objects.all_family():
        try:
            done = []
            for name, default in _NAMES_ATTRIBUTE_DEFAULTS:
                if not char.attributes.has(name):
                    char.attributes.add(name, default())
                    done.append(name)

            if char.attributes.get("_sdesc") in (None, "", CONTRIB_DEFAULT_SDESC):
                # Through the handler, so a loaded character's cache follows.
                char.sdesc.add(NAMES_PLACEHOLDER_SDESC)
                done.append("_sdesc")

            if char.cmdset.has(RPSystemCmdSet):
                char.cmdset.remove(RPSystemCmdSet)
                done.append("rpsystem_cmdset")

            if done:
                # A loaded character's handler may hold the unsaved dicts the
                # default gave it; read the stored ones back.
                char.recog._cache()
                changed.append(f"{char.key} ({', '.join(done)})")
            else:
                unchanged += 1
        except Exception as err:
            logger.log_trace(f"backfill_names: {getattr(char, 'key', char)!r}")
            errors.append(f"{getattr(char, 'key', char)} (ERROR: {err})")

    return (
        f"backfill_names: changed {len(changed)} {changed}; "
        f"unchanged {unchanged}; errors {len(errors)} {errors}."
    )
