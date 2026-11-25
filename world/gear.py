"""
world/gear.py
=============
Weapons and armour as data, and the readers that answer for an item (Gear
decomposition, slice GR, task GR-T1; locks IS1, IS2, GR13-GR16; Legend core
pp. 94-109, Arms of Legend pp. 48-50 and 71 ff.).

THE ONE IDEA
------------
Being a weapon or a piece of armour is a row in a table, not a class and not
Attributes on the item (GR13, GR16). The row is found by the item's
`from_prototype` tag, the one `spawn` gives everything it makes
(evennia/prototypes/spawner.py:1013):

    weapon(obj)  -> the row in WEAPONS, or None
    armour(obj)  -> the row in ARMOUR, or None

So nothing is migrated: every club that exists has the club's row the moment
this module loads, and a corrected row corrects every club ever made. The
cost is the other way round: a prototype renamed orphans its items, because
the tag is the key (decomposition §13, 7).

THE ROWS
--------
Each row is the book's, whatever the item is made of (GR14), and was read
against the book cell by cell (decomposition §3). Every weapon row has every
field; a cell the book leaves blank is None, never a missing key:

    weapon_type      one of combat_styles.WEAPON_TYPES
    hand             ONE_HAND or TWO_HANDS (combat_styles.HANDS; AoL's Category)
    damage           the book's dice as printed, "1D8+1"
    str_min, dex_min the STR and DEX the weapon needs; None for "-"
    size             "S", "M" or "L"; a ranged weapon's is its ammunition's
    reach            "S", "M" or "L"; None for a ranged weapon
    manoeuvres       a tuple of keys; their words are ML's (CM2)
    ap, hp           the weapon's own Armour and Hit Points (IS3)
    damage_modifier  True on a ranged weapon whose row says so; None in melee,
                     where the book prints no such column
    range_m, load    a ranged weapon's range in metres and its Load; else None
    parries_ranged   footnote 3 (core p. 106): the target shield only

An armour row has `ap` (per location, IS2), `locations` (a tuple in
`world.body.LOCATIONS` order), `layer` (the item's clothing type, GR8) and
`material` (the word a player reads, GR11). ENC is not here: it stays the
item's `enc` Attribute and `world.encumbrance.item_enc` its one reader.

Rows and tables are read-only (MappingProxyType, tuples inside). A reader
hands out the shared row, and a caller that could write `row["ap"] -= 1`
would change that item for every player on the server.

Five rows got their prototypes in GR-T12: the target shield and four pieces
of armour. The rows came first, at GR-T1, so every later rule was tested
against real rows. The spawn-only metal `knife` (world/prototypes.py) has no row yet; its
row comes with BACKLOG *Metal tools + craft-station / forge*.

WHO READS THIS
--------------
`world.sdesc` reads the three layer names and `LAYERS`: which types show,
and that an armour piece without a word is passed over (GR7, OQ-GR5).
`typeclasses.clothing` asks `layer_conflict` before a garment goes on (AR3,
GR6). `world.body.derived` reads `armour_total` for Strike Rank (GR18).
`world.garment_wear` asks `fought_since` at each tick (GR20).
`typeclasses.durable` asks `describe` for the line `look` shows between an
item's description and its condition (GR23), importing this module inside
the method, since this module imports it. The hands are read by the
commands and `look`, and ML reads the rows in a fight, `armour_at` among
them.

THE HANDS
---------
What a hand holds is `db.hands` on the character, hand -> item, written and
read only here (GR3, P-2). An item is held while it is in the character's
`contents` and not worn (GR-T7's STOPP 0); an entry that fails either is
cleared at the read, so every way an item leaves -- `drop`, `give`, `put`,
barter's assignment, a delete, death's `move_hooks=False` -- empties the
hand with no hook. A hand whose arm has a wound state reads empty and keeps
its entry (GR22), so an arm that heals holds again.

    held(char)                -> {"right": item or None, "left": ...}
    hold(char, obj, hand)     -> (hands taken, None) or ((), reason)
    release(char, obj)        -> the hands it left, () if not held
    hand_state(char, hand)    -> EMPTY, HOLDING or USELESS

`HANDS` here are the two hands, `right` and `left` (GR2); the weapon row's
`hand` is `ONE_HAND` or `TWO_HANDS`, `combat_styles.HANDS`. Two words, two
tuples.

Imports `world.body`, `world.combat_styles` and `world.wounds`, whose
`states_of` is the one reader of an arm's state (GR-T7's STOPP 0).
`world.body` reaches this module from inside `derived` only, and nothing
`world.wounds` imports reaches it at all, so no import is circular (GR-T5's
and GR-T7's STOPP 0); `world.sdesc` and `typeclasses.clothing` import it at
the top. `typeclasses.durable` imports only Evennia, so its `DurableObject`
is imported here at the top as well (GR-T10's STOPP 0).

WHAT ML IS GIVEN
----------------
Four doors, and no production code opens any of them until ML: what a use
is, what a fight is, and which damage reaches a weapon are ML's (GR19, GR20).

    wear_weapon(obj)          -> the new condition, after one use
    damage_weapon(obj, dmg)   -> the new condition, after a blow it took
    usable(obj)               -> True for a weapon above condition 0
    mark_combat(char)         -> stamps a fight, for the garment wear tick

A use takes `WEAPON_WEAR_PER_USE`. A blow takes nothing at or below the
row's `ap` and otherwise `ceil(100 * (damage - ap) / hp)` (IS3): the book's
Hit Points on the one axis. Below `ap` the floor is what stops a blow from
healing the weapon; at `ap` the formula itself gives 0. Both doors raise
`ValueError` for an item with no weapon row, a caller's mistake, and return
None, touching nothing, for a weapon with no condition (an item made before
the slice, until GR-T13's migration). `usable` raises for nothing: ML asks
it of whatever is in a hand (GR-T10's STOPP 0). A broken weapon can still
be held (GR19).
"""

import time
from collections.abc import Mapping
from types import MappingProxyType

from evennia.contrib.game_systems.clothing.clothing import get_worn_clothes
from evennia.utils import logger
from evennia.utils.utils import iter_to_str

from typeclasses.durable import DurableObject
from world import body, combat_styles, wounds

# The tag category `spawn` writes (evennia/prototypes/prototypes.py:58),
# spelt here so this module imports nothing from Evennia's prototype system.
PROTOTYPE_TAG_CATEGORY = "from_prototype"

ONE_HAND, TWO_HANDS = combat_styles.HANDS

# The three armour layers, outermost first (GR6, GR8). Each is a clothing
# type; GR-T3 puts them in the contrib's configuration.
ARMOUR_RIGID = "armour_rigid"
ARMOUR_FLEXIBLE = "armour_flexible"
ARMOUR_PADDING = "armour_padding"
LAYERS = (ARMOUR_RIGID, ARMOUR_FLEXIBLE, ARMOUR_PADDING)

# Manoeuvre keys (core p. 101). The list and its words are ML's (CM2).
STUN_LOCATION = "stun_location"
BLEED = "bleed"
IMPALE = "impale"


def _weapon_row(
    weapon_type, hand, damage, str_min, dex_min, size, reach, manoeuvres, ap, hp,
    damage_modifier=None, range_m=None, load=None, parries_ranged=False,
):
    """One weapon row, with every field and nothing writable."""
    return MappingProxyType({
        "weapon_type": weapon_type,
        "hand": hand,
        "damage": damage,
        "str_min": str_min,
        "dex_min": dex_min,
        "size": size,
        "reach": reach,
        "manoeuvres": tuple(manoeuvres),
        "ap": ap,
        "hp": hp,
        "damage_modifier": damage_modifier,
        "range_m": range_m,
        "load": load,
        "parries_ranged": parries_ranged,
    })


def _armour_row(ap, locations, layer, material):
    """One armour row, with every field and nothing writable."""
    return MappingProxyType({
        "ap": ap,
        "locations": tuple(locations),
        "layer": layer,
        "material": material,
    })


# GR14: the close combat rows (core pp. 106-107) and the ranged ones (p. 109);
# the hand from AoL's close combat table (pp. 71 ff.). Keyed by prototype_key,
# in lower case: Evennia lowers every tag key (typeclasses/tags.py:377).
WEAPONS = MappingProxyType({
    "club": _weapon_row(
        "bludgeon", ONE_HAND, "1D6", 7, None, "M", "S", (STUN_LOCATION,), 4, 4),
    # Two-handed (AoL pp. 71 ff.), hence its own style (GR15).
    "quarterstaff": _weapon_row(
        "bludgeon", TWO_HANDS, "1D8", 7, 7, "M", "L", (STUN_LOCATION,), 4, 8),
    # The book's Shortspear. Footnotes 1 (set against a charge, ML) and 2 (no
    # penalty thrown, PJ) are not fields until something reads them.
    "spear": _weapon_row(
        "spear", ONE_HAND, "1D8+1", 5, 5, "M", "L", (IMPALE,), 4, 5),
    # The book's Knife: "metal, stone, bone or even glass" (core p. 103). Its
    # frailty is its starting condition, 40, not a weaker row (GR14).
    "stone_knife": _weapon_row(
        "knife", ONE_HAND, "1D3", None, None, "S", "S", (BLEED, IMPALE), 5, 4),
    # The book's Hatchet. The ranged table's AP/HP cell does not read in the
    # extracted text; the close combat row's 3/6 is the one used (§3).
    "stone_axe": _weapon_row(
        "axe", ONE_HAND, "1D6", None, 9, "S", "S", (BLEED,), 3, 6),
    # The book's Target (GR10), added as a prototype by GR-T12.
    "target_shield": _weapon_row(
        "shield", ONE_HAND, "1D6", 9, None, "L", "S", (IMPALE,), 4, 12,
        parries_ranged=True),
    # The book's Short bow.
    "bow": _weapon_row(
        "bow", TWO_HANDS, "1D6", 9, 11, "L", None, (IMPALE,), 4, 4,
        damage_modifier=True, range_m=80, load=1),
    "sling": _weapon_row(
        "sling", ONE_HAND, "1D8", None, 11, "L", None, (STUN_LOCATION,), 1, 2,
        damage_modifier=True, range_m=200, load=1),
})

# GR8, GR12: Armour Points per location (core pp. 95-96; AoL p. 50). Four of
# the six are added as prototypes by GR-T12.
ARMOUR = MappingProxyType({
    "linen_cuirass": _armour_row(2, ("chest",), ARMOUR_PADDING, "linen"),
    "soft_leather_trews": _armour_row(
        1, ("abdomen", "right_leg", "left_leg"), ARMOUR_PADDING, "soft leather"),
    "hard_leather_hauberk": _armour_row(
        2, ("chest", "abdomen"), ARMOUR_FLEXIBLE, "hard leather"),
    "hard_leather_vambraces": _armour_row(
        2, ("right_arm", "left_arm"), ARMOUR_FLEXIBLE, "hard leather"),
    "bone_armour": _armour_row(2, ("chest",), ARMOUR_RIGID, "bone"),
    "bone_helm": _armour_row(2, ("head",), ARMOUR_RIGID, "bone"),
})


def _prototype_key(obj):
    """
    The one prototype an item was spawned from, or None.

    No tag is the common case (an object made with `create_object`) and is
    silent. Two or more cannot come from `spawn`, which writes one, nor from
    `batch_update_objects_with_prototype`, which clears the category first
    (spawner.py:801-802): only a hand-added tag makes them. That reads None,
    as Evennia's own reader calls it no unambiguous prototype
    (spawner.py:312-316), and is logged, so a club with two tags does not
    pass for a stone in silence. Never raises: `look` and `inventory` read
    this for whoever is looking.

    Args:
        obj (Object): any typeclassed object.

    Returns:
        str or None: the tag's key.
    """
    keys = obj.tags.get(category=PROTOTYPE_TAG_CATEGORY, return_list=True)
    if not keys:
        return None
    if len(keys) > 1:
        logger.log_warn(
            f"gear: {obj.key}(#{obj.id}) has {len(keys)} prototype tags "
            f"{sorted(keys)}; read as no row."
        )
        return None
    return keys[0]


def weapon(obj):
    """
    An item's weapon row (GR13, GR16).

    Args:
        obj (Object): any typeclassed object.

    Returns:
        MappingProxyType or None: the row, read-only; None for an item with
            no row, no prototype tag, or more than one.
    """
    key = _prototype_key(obj)
    return WEAPONS.get(key) if key else None


def armour(obj):
    """
    An item's armour row (IS2, GR16).

    Args:
        obj (Object): any typeclassed object.

    Returns:
        MappingProxyType or None: the row, read-only; None for an item with
            no row, no prototype tag, or more than one.
    """
    key = _prototype_key(obj)
    return ARMOUR.get(key) if key else None


def layer_conflict(char, obj):
    """
    The worn piece that stands in `obj`'s place, or None (AR3, GR6).

    Two pieces conflict when they share a layer and at least one Hit
    Location: a helm and a breastplate share the rigid layer and no
    location; a cuirass and bone armour share the chest and no layer.
    `obj` is never in its own way, so wearing a worn piece again is no
    conflict. An item with no armour row never conflicts, nor does a worn
    garment without one.

    Args:
        char (Object): the wearer.
        obj (Object): the piece about to be put on.

    Returns:
        Object or None: the first worn piece in the way, in the contrib's
            order of worn clothes.
    """
    row = armour(obj)
    if row is None:
        return None
    for worn in get_worn_clothes(char):
        if worn == obj:
            continue
        other = armour(worn)
        if (
            other is not None
            and other["layer"] == row["layer"]
            and set(other["locations"]) & set(row["locations"])
        ):
            return worn
    return None


def shared_locations(obj, other):
    """
    The Hit Locations two armour pieces both cover, in `body.LOCATIONS`
    order; an empty tuple when either has no row.
    """
    row, other_row = armour(obj), armour(other)
    if row is None or other_row is None:
        return ()
    return tuple(loc for loc in row["locations"] if loc in other_row["locations"])


def _worn_rows(char):
    """Each worn garment with an armour row, and its row."""
    for worn in get_worn_clothes(char):
        row = armour(worn)
        if row is not None:
            yield worn, row


def armour_at(char, location):
    """
    The Armour Points that protect one Hit Location now (AR1, GR18).

    The sum over every layer -- not the book's highest piece (core p. 95;
    AR1 departs). A piece gives its whole `ap` while its condition is above
    0 and none once it is broken; a carried piece gives nothing.

    Args:
        char (Object): the wearer.
        location (str): one of `body.LOCATIONS`.

    Returns:
        int: 0 or more.

    Raises:
        ValueError: for a location the body does not have.
    """
    if location not in body.LOCATIONS:
        raise ValueError(
            f"unknown Hit Location {location!r}; expected one of {body.LOCATIONS}"
        )
    return sum(
        row["ap"]
        for worn, row in _worn_rows(char)
        if location in row["locations"] and worn.condition > 0
    )


def armour_total(char):
    """
    The Armour Points a body carries, for the Strike Rank penalty (AR4, GR18).

    Each worn piece's nominal `ap` once for every location it covers -- the
    seven locations summed -- broken or not: a broken piece is carried all
    the same (core p. 13). `body.derived` divides it by five.

    Returns:
        int: 0 or more.
    """
    return sum(row["ap"] * len(row["locations"]) for _, row in _worn_rows(char))


# -- a fight, for the garment wear tick (GR20) -----------------------------------

def mark_combat(char):
    """
    Stamp `char` as having fought now (GR20), as `time.time()` in
    `db.fought_at` -- real time, the clock the wear tick's interval is in
    (GR-T6's STOPP 0). An Attribute, so a reload between a fight and the
    tick keeps it. No production code calls this until ML: what a fight is
    and when it begins are ML's.
    """
    char.db.fought_at = time.time()


def fought_since(char, seconds):
    """
    True when `char` was stamped by `mark_combat` less than `seconds` ago.

    Args:
        char (Object): the character.
        seconds (float): the window, in real seconds -- the wear tick's
            interval, handed in by its caller.

    Returns:
        bool: False with no stamp.
    """
    stamp = char.attributes.get("fought_at")
    return stamp is not None and time.time() - stamp < seconds


# -- a weapon's wear (IS3, IS5, GR19) --------------------------------------------

# GR19: what one use takes from a weapon's condition. Not a tool's 5 a craft
# (world/crafting_base.py, MongooseCraftRecipe.tool_wear): a craft is not a
# blow, and twenty blows is a fight or two. So a club at 100 lasts a hundred
# uses and a stone knife at 40 forty, on the one axis at two rates (GR13).
WEAPON_WEAR_PER_USE = 1

NO_WEAPON_ROW = "no weapon row for #{id} ({key}, prototype {prototype!r})"


def _weapon_row_or_raise(obj):
    """The row, or ValueError naming the item and its tag (GR-T10's STOPP 0)."""
    prototype = _prototype_key(obj)
    row = WEAPONS.get(prototype) if prototype else None
    if row is None:
        raise ValueError(
            NO_WEAPON_ROW.format(id=obj.id, key=obj.key, prototype=prototype))
    return row


def wear_weapon(obj):
    """
    Take one use from a weapon's condition (GR19). What a use is is ML's.

    Args:
        obj (Object): an item with a weapon row.

    Returns:
        int or None: the new condition; None, and nothing done, for a weapon
            with no condition (not a DurableObject).

    Raises:
        ValueError: for an item with no weapon row.
    """
    _weapon_row_or_raise(obj)
    if not isinstance(obj, DurableObject):
        return None
    return obj.apply_wear(WEAPON_WEAR_PER_USE)


def damage_weapon(obj, damage):
    """
    Take a blow's damage from a weapon's condition (IS3, IS5, GR19).

    Nothing at or below the row's `ap`; above it, the damage past the Armour
    Points as a share of the row's `hp`, in hundredths, rounded up. Integer
    arithmetic, so no float decides a rounding.

    Args:
        obj (Object): an item with a weapon row.
        damage (int): the damage the blow did to the weapon.

    Returns:
        int or None: the new condition; None, and nothing done, for a weapon
            with no condition (not a DurableObject).

    Raises:
        ValueError: for an item with no weapon row.
    """
    row = _weapon_row_or_raise(obj)
    if not isinstance(obj, DurableObject):
        return None
    # The floor: below `ap` the share is negative, and `apply_wear` would heal.
    if damage <= row["ap"]:
        return obj.condition
    lost = -(-100 * (damage - row["ap"]) // row["hp"])
    return obj.apply_wear(lost)


def usable(obj):
    """
    True for a weapon that can be used: a row and a condition above 0 (GR19).

    Asked of whatever is in a hand, so it raises for nothing: a torch, a
    tunic or an item with no condition reads False (GR-T10's STOPP 0). A
    broken weapon can still be held; it cannot be used.

    Args:
        obj (Object): any typeclassed object.

    Returns:
        bool
    """
    return (
        weapon(obj) is not None
        and isinstance(obj, DurableObject)
        and obj.condition > 0
    )


# -- what an item says of itself (GR23) ------------------------------------------

# GR-T11's STOPP 0: the hand in words, near `wield`'s own ("needs both hands").
_HAND_WORDS = MappingProxyType({ONE_HAND: "one hand", TWO_HANDS: "two hands"})

# A need the looker does not meet is red, as a condition below 33 is.
_UNMET = "|r{}|n"


def _meets(looker, key, need):
    """
    True unless the looker's characteristic `key` is below `need`.

    Read as `body.derived` reads it, `int(stat.value)`, so a modifier would
    follow. A looker with nothing to compare -- no `stats`, or no such
    characteristic -- meets it: the line is plain (GR-T11's STOPP 0).
    """
    stats = getattr(looker, "stats", None)
    stat = stats.get(key) if stats is not None else None
    return stat is None or int(stat.value) >= need


def _weapon_line(row, looker):
    """GR23 for a weapon: type and hand; damage, Size, Reach or Range and
    Load; the STR and DEX it needs. Manoeuvres, AP/HP, the Damage Modifier
    and the shield's footnote 3 are not shown (GR-T11's STOPP 0)."""
    word = row["weapon_type"]
    article = "An" if word[0] in "aeiou" else "A"
    parts = [f"Damage {row['damage']}", f"Size {row['size']}"]
    if row["reach"] is not None:
        parts.append(f"Reach {row['reach']}")
    if row["range_m"] is not None:
        parts += [f"Range {row['range_m']} m", f"Load {row['load']}"]
    needs = []
    for label, key, field in (("STR", "str", "str_min"), ("DEX", "dex", "dex_min")):
        need = row[field]
        if need is None:
            continue
        piece = f"{label} {need}"
        needs.append(piece if _meets(looker, key, need) else _UNMET.format(piece))
    line = f"{article} {word} for {_HAND_WORDS[row['hand']]}. {', '.join(parts)}."
    if needs:
        line += f" Needs {' and '.join(needs)}."
    return line


def _armour_line(row):
    """GR23 for armour: the layer, the Armour Points and where, in the row's
    order (`world.body.LOCATIONS`). The material is in the item's name."""
    layer = row["layer"].split("_", 1)[1]
    ap = row["ap"]
    points = "Armour Point" if ap == 1 else "Armour Points"
    where = iter_to_str(location.replace("_", " ") for location in row["locations"])
    return f"{layer.capitalize()} armour: {ap} {points} on the {where}."


def describe(obj, looker):
    """
    The line `look` shows for a weapon or a piece of armour (GR23).

    Built from the row only, so the line and the table cannot drift. Never
    raises: `look` asks it for whoever is looking.

    Args:
        obj (Object): any typeclassed object.
        looker (Object or None): who looks; their STR and DEX colour a need
            they do not meet.

    Returns:
        str or None: the line; None for an item with no row.
    """
    row = weapon(obj)
    if row is not None:
        return _weapon_line(row, looker)
    row = armour(obj)
    if row is not None:
        return _armour_line(row)
    return None


# -- the hands (GR2, GR3, GR4, GR22) ---------------------------------------------

# GR2: two hands, and they are the arms. Not `combat_styles.HANDS`, which is a
# weapon's category ("1H", "2H"): these are where an item is held.
RIGHT = "right"
LEFT = "left"
HANDS = (RIGHT, LEFT)
ARM_OF = MappingProxyType({RIGHT: "right_arm", LEFT: "left_arm"})

# What a hand is, for the displays (GR-T9; GR22's *useless*).
EMPTY = "empty"
HOLDING = "holding"
USELESS = "useless"

# What `hold` says when it refuses (GR-T7's STOPP 0, A): each line names what
# is in the way, as GR-T4's layer refusal does. Every name is the holder's
# (`get_display_name(char)`); the room's line is the command's (GR-T8).
NOT_CARRIED = "You aren't carrying that."
WORN = "You are wearing your {item}."
ALREADY_HELD = "You are already holding your {item}."
HAND_FULL = "Your {hand} hand already holds your {item}."
ARM_USELESS = "Your {hand} arm is useless."
NO_HAND_FREE = "{obstacles}."
NEEDS_BOTH = "Your {item} needs both hands, and {obstacles}."

# The pieces the last two are built from, one per hand in the way.
_FULL_PART = "your {hand} hand holds your {item}"
_USELESS_PART = "your {hand} arm is useless"

_SHIELD = "shield"


def _still_held(char, obj):
    """GR3 and GR-T7's STOPP 0 (val 2): in `contents`, and not worn."""
    return obj is not None and obj in char.contents and not obj.db.worn


def _entries(char):
    """
    The entries in `db.hands` that stand, hand -> item, empty hands left out.

    Every item that has left the body, reads as None (deleted, P3) or is worn
    is cleared, and the table is written back only when something was. A
    useless arm clears nothing (GR22): that is `held`'s business. Anything
    but a Mapping stored there reads as no entries and is replaced.
    """
    raw = char.attributes.get("hands")
    if raw is None:
        return {}
    stored = {}
    if isinstance(raw, Mapping):
        stored = {h: raw.get(h) for h in HANDS if raw.get(h) is not None}
    kept = {h: obj for h, obj in stored.items() if _still_held(char, obj)}
    # `kept` is `raw` less what was cleared, so a key missing is a change.
    if not isinstance(raw, Mapping) or set(raw) != set(kept):
        _write(char, kept)
    return kept


def _write(char, entries):
    """The one writer of `db.hands` (GR3): a plain dict, empty hands left out."""
    char.db.hands = {hand: obj for hand, obj in entries.items() if obj is not None}


def _useless(char):
    """The hands whose arm has a wound state, any of the three (GR22)."""
    states = wounds.states_of(char)
    return {hand for hand in HANDS if ARM_OF[hand] in states}


def _read(entries, useless):
    """
    What each hand holds, from the entries that stand and the useless hands.

    A hand whose arm has a state reads None (GR22), and so does every hand of
    an item stored under both, once either arm is useless: a two-handed item
    needs two usable arms (GR-T9's STOPP 0, val 2). That item is known by
    being stored under both hands -- `hold` stores nothing else there -- not
    by its row, so a row corrected later cannot change the answer.
    """
    shown = {hand: (None if hand in useless else entries.get(hand)) for hand in HANDS}
    both = entries.get(RIGHT)
    if useless and both is not None and both == entries.get(LEFT):
        return {hand: None for hand in HANDS}
    return shown


def held(char):
    """
    What each hand holds now (GR3, GR22).

    An item that has left the character's `contents`, or reads as None
    (deleted), or is worn, is cleared from `db.hands` here. A hand whose arm
    is disabled, maimed or severed reads None and its entry stands; so do
    both hands of a two-handed item that has lost an arm.

    Args:
        char (Object): the character.

    Returns:
        dict: {RIGHT: item or None, LEFT: item or None}.
    """
    entries = _entries(char)
    useless = _useless(char)
    return _read(entries, useless)


def hand_state(char, hand):
    """
    EMPTY, HOLDING or USELESS, for `inventory` (GR22, GR-T9).

    Raises:
        ValueError: for a hand that is not RIGHT or LEFT.
    """
    _check_hand(hand)
    if hand in _useless(char):
        return USELESS
    return HOLDING if held(char)[hand] is not None else EMPTY


def _check_hand(hand):
    if hand not in HANDS:
        raise ValueError(f"unknown hand {hand!r}; expected one of {HANDS}")


def _obstacles(char, entries, useless, hands):
    """What stands in each of `hands`, as the lower-case pieces, in order."""
    parts = []
    for hand in hands:
        if hand in useless:
            parts.append(_USELESS_PART.format(hand=hand))
        elif entries.get(hand) is not None:
            parts.append(_FULL_PART.format(
                hand=hand, item=entries[hand].get_display_name(char)))
    return parts


def hold(char, obj, hand=None):
    """
    Put `obj` in a hand (GR4, GR22), or say why not.

    Without a hand named, an item takes the right hand if it is free and the
    left otherwise; a shield takes the left first. A two-handed row takes both
    hands, whatever hand is named, and needs both free and both arms usable.
    A full hand is refused, never swapped. An item held in a useless hand
    moves to the one asked for. Anything carried can be held but what is
    worn; the row only says whether it is a weapon.

    Args:
        char (Object): the character.
        obj (Object): the item.
        hand (str, optional): RIGHT or LEFT.

    Returns:
        tuple: (hands, None) with the hands taken, in HANDS order, or
            ((), reason) with the line for the holder.

    Raises:
        ValueError: for a hand that is not RIGHT, LEFT or None.
    """
    if hand is not None:
        _check_hand(hand)
    if obj is None or obj not in char.contents:
        return (), NOT_CARRIED
    name = obj.get_display_name(char)
    if obj.db.worn:
        return (), WORN.format(item=name)
    useless = _useless(char)
    entries = _entries(char)
    shown = _read(entries, useless)
    if obj in shown.values():
        return (), ALREADY_HELD.format(item=name)
    # Only what reads as held is in the way. An entry that does not read --
    # this item's own under a useless arm, or a two-handed item that lost an
    # arm -- gives its hand up below.
    in_the_way = {h: o for h, o in shown.items() if o is not None}
    row = weapon(obj)

    if row is not None and row["hand"] == TWO_HANDS:
        blocked = _obstacles(char, in_the_way, useless, HANDS)
        if blocked:
            return (), NEEDS_BOTH.format(item=name, obstacles=" and ".join(blocked))
        taken = HANDS
    elif hand is not None:
        if hand in useless:
            return (), ARM_USELESS.format(hand=hand)
        if in_the_way.get(hand) is not None:
            return (), HAND_FULL.format(
                hand=hand, item=in_the_way[hand].get_display_name(char))
        taken = (hand,)
    else:
        order = (LEFT, RIGHT) if row is not None and row["weapon_type"] == _SHIELD else HANDS
        free = [h for h in order if not _obstacles(char, in_the_way, useless, (h,))]
        if not free:
            blocked = _obstacles(char, in_the_way, useless, HANDS)
            line = ", and ".join(blocked)
            return (), NO_HAND_FREE.format(obstacles=line[0].upper() + line[1:])
        taken = (free[0],)

    others = {h: o for h, o in entries.items() if o != obj}
    for h in taken:
        idle = others.get(h)
        if idle is not None:
            others = {k: o for k, o in others.items() if o != idle}
    for h in taken:
        others[h] = obj
    _write(char, others)
    return taken, None


def release(char, obj):
    """
    Take `obj` out of every hand that holds it, a useless one too.

    Returns:
        tuple: the hands it left, in HANDS order; () when it was not held.
    """
    entries = _entries(char)
    freed = tuple(h for h in HANDS if entries.get(h) is not None and entries[h] == obj)
    if freed:
        _write(char, {h: o for h, o in entries.items() if h not in freed})
    return freed
