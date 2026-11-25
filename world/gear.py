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

Five rows name prototypes that GR-T12 adds: the target shield and four pieces
of armour. They are here first so every later rule is tested against real
rows. The spawn-only metal `knife` (world/prototypes.py) has no row yet; its
row comes with BACKLOG *Metal tools + craft-station / forge*.

WHO READS THIS
--------------
`world.sdesc` reads the three layer names and `LAYERS`: which types show,
and that an armour piece without a word is passed over (GR7, OQ-GR5).
`typeclasses.clothing` asks `layer_conflict` before a garment goes on (AR3,
GR6). `world.body.derived` reads `armour_total` for Strike Rank (GR18).
`world.garment_wear` asks `fought_since` at each tick (GR20). GR's
later tasks read the rows (the hands, `look`), and ML reads them in a fight,
`armour_at` among them.

Imports `world.body` and `world.combat_styles`. `world.body` reaches this
module from inside `derived` only, so neither import is circular (GR-T5's
STOPP 0); `world.sdesc` and `typeclasses.clothing` import it at the top.
"""

import time
from types import MappingProxyType

from evennia.contrib.game_systems.clothing.clothing import get_worn_clothes
from evennia.utils import logger

from world import body, combat_styles

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
