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

from typeclasses.characters import Character


# Keep in sync with the matching self.skills.add("hunting", ...) call in
# Character.at_object_creation. Single source of truth for the backfill so a
# backfilled character is byte-for-byte identical to a freshly created one.
HUNTING_SKILL_DEFAULTS = {
    "trait_type": "counter",
    "base": 25,
    "current": 25,
    "mod": 0,
    "min": 0,
    "max": 100,
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
