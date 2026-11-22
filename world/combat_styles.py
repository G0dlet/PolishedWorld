"""
world/combat_styles.py
======================
Weapon types and Combat Styles as data (Body decomposition, slice BD, task
BD-T6; locks BD1-BD4, CS2; Legend core pp. 14, 101-109, 124).

A Combat Style is a skill for fighting with one kind of weapon, or with a
kind in each hand (p. 124: *Sword and Shield (any one-handed sword and any
shield type)*). A style names weapon TYPES, never weapons, so a new weapon
fits without any style changing (BD1).

**The types are the project's construction, not the book's.** Core says a
weapon's Category is *the type of weapon* (p. 101) and prints no such
column; *Arms of Legend* has the column and there it means the hand. All
the book gives is the substitution rule (p. 124): how the weapon is used.
WEAPON_TYPES is the twelve of BD2. The field on an item is to be called
`weapon_type`, and the hand is a field of its own; setting either on an
item is GR's (OQ-BD1). This module ships the vocabulary only.

**Who reads this.** Nothing in production calls a style until ML (the
melee slice) rolls one; `world.skill_base` reads the table so that

    skill_base.value_of(char, "style_knife")   -> the base, with no trait
    skill_base.ensure_style(char, "style_knife") -> the trait, made if missing

work today. A style becomes a trait at first use; until then its base is
read from the characteristics (BD3): STR + DEX in close combat, DEX x 2 at
range (p. 14). So a style nobody has used does not exist on the character,
and `skills` shows none.

**Trait keys (OQ-BD3).** Every style's key starts with STYLE_PREFIX. No
Common skill's key does, so a style called *Knife* can never meet a skill
or a weapon type called `knife`.

**The rule for adding a style (BD4):** *the slice that adds the first
weapon of a type adds its style in the same commit.* That is one row in
STYLES; the ladder is shared, and `skill_base` picks the row up by itself.
Players do not invent styles: the list is the server's (a departure from
p. 124).

No project imports, so `world.skill_base` can import this module.
"""

# BD2. Unarmed is a Common skill (p. 14) and no weapon type; net, garrotte
# and blowgun are left out until built.
WEAPON_TYPES = (
    "sword",
    "knife",
    "axe",
    "bludgeon",
    "flail",
    "spear",
    "polearm",
    "shield",
    "bow",
    "crossbow",
    "sling",
    "thrown",
)

# The hand a style's main weapon is held in (Arms of Legend's Category).
HANDS = ("1H", "2H")

STYLE_PREFIX = "style_"

# BD4: only types with an item today. `second` is the type in the other
# hand, or None. A style is named for the combination before the shield
# exists: whoever fights with a club trains Mace and Shield.
STYLES = {
    "style_knife": {
        "name": "Knife",
        "main": "knife", "hand": "1H", "second": None, "ranged": False,
    },
    "style_mace_shield": {
        "name": "Mace and Shield",
        "main": "bludgeon", "hand": "1H", "second": "shield", "ranged": False,
    },
    "style_axe_shield": {
        "name": "Axe and Shield",
        "main": "axe", "hand": "1H", "second": "shield", "ranged": False,
    },
    "style_spear_shield": {
        "name": "Spear and Shield",
        "main": "spear", "hand": "1H", "second": "shield", "ranged": False,
    },
    "style_bow": {
        "name": "Bow",
        "main": "bow", "hand": "2H", "second": None, "ranged": True,
    },
    "style_sling": {
        "name": "Sling",
        "main": "sling", "hand": "1H", "second": None, "ranged": True,
    },
}

# One ladder for every style, in band order: 0-19, 20-39, 40-59, 60-79,
# 80-94, 95 upward (`skill_base.LADDER_TOPS` keys it).
STYLE_LADDER = ("untried", "green", "drilled", "steady", "seasoned", "deadly")

# A style's base (p. 14).
CLOSE_PAIR = ("str", "dex")
RANGED_PAIR = ("dex", "dex")


def pair_for(style_key):
    """
    The two characteristics a style's base is the sum of (p. 14).

    Args:
        style_key (str): a key of STYLES.

    Returns:
        tuple: ("str", "dex") in close combat, ("dex", "dex") at range.

    Raises:
        KeyError: no such style.
    """
    return RANGED_PAIR if STYLES[style_key]["ranged"] else CLOSE_PAIR
