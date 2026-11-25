"""
world/gear_migrations.py

One-off migration for weapons and armour made before the Gear slice (Gear
decomposition GR-T13, lock GR17).

Before GR, the five pure weapons -- club, quarterstaff, spear, bow, sling --
were plain `Object`s, and the linen cuirass and the bone armour were worn as
`top`. Everything else an item needs is derived: its row in world/gear.py
is found by its prototype tag (GR16), so a corrected row corrects every
item. What cannot be derived is what is stored on the item itself:

- the class: a pure weapon becomes a `Weapon` (GR13), and with it a
  `condition` on the one wear axis. `swap_typeclass` runs the start hooks
  ("all"), so `condition` is stored at once, at 100, as on a spawned club;
- the repair data the prototype carries since GR-T2 (GR24): without it an
  old club is mended with cloth, twine and a needle
  (commands/repair_commands.py). Read from the prototype, never a second copy;
- the armour's clothing type: the row's layer (GR6), which the short
  description's order reads (GR7).

Nothing else is touched: no key, no alias, no description, no condition. A
tool -- the stone knife, the stone axe -- is never swapped and keeps its
condition. A pure weapon made before the slice starts at 100 whatever its
quality: GR21's table applies where it is made (GR-T13's STOPP 0).

IDEMPOTENT: an item already right is skipped, so a second run answers
(0, 0) and changes nothing -- not even a club worn to 60 in between.

Run once per existing database, in-game (the same process as the live game):
    py from world.gear_migrations import migrate_gear; self.msg(str(migrate_gear()))
The answer is a tuple, so it is sent as a string: `msg` passes a tuple on as
the `text` command's arguments, and the client shows only the first.

Multiplayer: one synchronous call on Twisted's single-threaded reactor; no
command runs between two of its writes. A held or worn item stays held or
worn: `db.hands` and `db.worn` are not touched.
"""

from evennia.prototypes.prototypes import search_prototype
from evennia.utils import logger
from evennia.utils.search import search_tag

from typeclasses.weapons import Weapon
from world import gear

# GR17: the five pure weapons and the two armours that existed before GR.
# The stone knife and the stone axe are Tools, weapons by their rows (GR13),
# and stay as they are.
WEAPON_PROTOTYPES = ("club", "quarterstaff", "spear", "bow", "sling")
ARMOUR_PROTOTYPES = ("linen_cuirass", "bone_armour")

# What `repair` reads from the item (commands/repair_commands.py).
REPAIR_KEYS = ("repair_materials", "repair_tool_tag")


def _repair_data(prototype_key):
    """The prototype's repair data, by key; raises if the prototype is not one."""
    found = [
        prototype
        for prototype in search_prototype(key=prototype_key, no_db=True)
        if prototype.get("prototype_key") == prototype_key
    ]
    if len(found) != 1:
        raise ValueError(
            f"migrate_gear: prototype {prototype_key!r} matched {len(found)} prototypes"
        )
    # search_prototype answers the normalised form: the prototype's own keys
    # are Attributes in `attrs`, as (key, value, category, lockstring).
    attrs = {attr[0]: attr[1] for attr in found[0].get("attrs", ())}
    missing = [key for key in REPAIR_KEYS if key not in attrs]
    if missing:
        raise ValueError(
            f"migrate_gear: prototype {prototype_key!r} carries no {', '.join(missing)}"
        )
    return {key: attrs[key] for key in REPAIR_KEYS}


def _migrate_weapon(obj, repair):
    """Make one old weapon what a new one is; True if anything was written."""
    changed = False
    if not isinstance(obj, Weapon):
        obj.swap_typeclass(Weapon, run_start_hooks="all")
        changed = True
    for key, value in repair.items():
        # Read with get(... ) is None, not has(): has() answers [] for a
        # missing Attribute (typeclasses/attributes.py:1198-1203). A bow's
        # tool is "" -- present, and left.
        if obj.attributes.get(key) is None:
            obj.attributes.add(key, value)
            changed = True
    return changed


def migrate_gear():
    """
    Bring every weapon and armour made before the Gear slice up to a new one.

    Finds items by their prototype tag (`from_prototype`, which `spawn` sets
    on everything it makes). A pure weapon that is not a `Weapon` is swapped
    to one; one that lacks its prototype's repair data gets it. An armour
    whose clothing type is not its row's layer gets the layer. Every
    prototype's data is read before the first write, so a missing prototype
    writes nothing.

    One broken item does not stop the batch: it is logged with its trace and
    not counted.

    Returns:
        tuple: (weapons, armours) -- how many of each were changed, not how
            many were found. A second run answers (0, 0).
    """
    repairs = {key: _repair_data(key) for key in WEAPON_PROTOTYPES}
    layers = {key: gear.ARMOUR[key]["layer"] for key in ARMOUR_PROTOTYPES}
    weapons = armours = 0

    for key in WEAPON_PROTOTYPES:
        for obj in search_tag(key, category=gear.PROTOTYPE_TAG_CATEGORY):
            try:
                if _migrate_weapon(obj, repairs[key]):
                    weapons += 1
            except Exception:
                logger.log_trace(f"migrate_gear: weapon {obj.dbref} ({key!r})")

    for key in ARMOUR_PROTOTYPES:
        for obj in search_tag(key, category=gear.PROTOTYPE_TAG_CATEGORY):
            try:
                if obj.db.clothing_type != layers[key]:
                    obj.db.clothing_type = layers[key]
                    armours += 1
            except Exception:
                logger.log_trace(f"migrate_gear: armour {obj.dbref} ({key!r})")

    return weapons, armours
