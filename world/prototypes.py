"""
Prototypes

A prototype is a simple way to create individualized instances of a
given typeclass. It is dictionary with specific key names.

For example, you might have a Sword typeclass that implements everything a
Sword would need to do. The only difference between different individual Swords
would be their key, description and some Attributes. The Prototype system
allows to create a range of such Swords with only minor variations. Prototypes
can also inherit and combine together to form entire hierarchies (such as
giving all Sabres and all Broadswords some common properties). Note that bigger
variations, such as custom commands or functionality belong in a hierarchy of
typeclasses instead.

A prototype can either be a dictionary placed into a global variable in a
python module (a 'module-prototype') or stored in the database as a dict on a
special Script (a db-prototype). The former can be created just by adding dicts
to modules Evennia looks at for prototypes, the latter is easiest created
in-game via the `olc` command/menu.

Prototypes are read and used to create new objects with the `spawn` command
or directly via `evennia.spawn` or the full path `evennia.prototypes.spawner.spawn`.

A prototype dictionary have the following keywords:

Possible keywords are:
- `prototype_key` - the name of the prototype. This is required for db-prototypes,
  for module-prototypes, the global variable name of the dict is used instead
- `prototype_parent` - string pointing to parent prototype if any. Prototype inherits
  in a similar way as classes, with children overriding values in their parents.
- `key` - string, the main object identifier.
- `typeclass` - string, if not set, will use `settings.BASE_OBJECT_TYPECLASS`.
- `location` - this should be a valid object or #dbref.
- `home` - valid object or #dbref.
- `destination` - only valid for exits (object or #dbref).
- `permissions` - string or list of permission strings.
- `locks` - a lock-string to use for the spawned object.
- `aliases` - string or list of strings.
- `attrs` - Attributes, expressed as a list of tuples on the form `(attrname, value)`,
  `(attrname, value, category)`, or `(attrname, value, category, locks)`. If using one
   of the shorter forms, defaults are used for the rest.
- `tags` - Tags, as a list of tuples `(tag,)`, `(tag, category)` or `(tag, category, data)`.
-  Any other keywords are interpreted as Attributes with no category or lock.
   These will internally be added to `attrs` (equivalent to `(attrname, value)`.

See the `spawn` command and `evennia.prototypes.spawner.spawn` for more info.

"""

## example of module-based prototypes using
## the variable name as `prototype_key` and
## simple Attributes

# from random import randint
#
# GOBLIN = {
# "key": "goblin grunt",
# "health": lambda: randint(20,30),
# "resists": ["cold", "poison"],
# "attacks": ["fists"],
# "weaknesses": ["fire", "light"],
# "tags": = [("greenskin", "monster"), ("humanoid", "monster")]
# }
#
# GOBLIN_WIZARD = {
# "prototype_parent": "GOBLIN",
# "key": "goblin wizard",
# "spells": ["fire ball", "lighting bolt"]
# }
#
# GOBLIN_ARCHER = {
# "prototype_parent": "GOBLIN",
# "key": "goblin archer",
# "attacks": ["short bow"]
# }
#
# This is an example of a prototype without a prototype
# (nor key) of its own, so it should normally only be
# used as a mix-in, as in the example of the goblin
# archwizard below.
# ARCHWIZARD_MIXIN = {
# "attacks": ["archwizard staff"],
# "spells": ["greater fire ball", "greater lighting"]
# }
#
# GOBLIN_ARCHWIZARD = {
# "key": "goblin archwizard",
# "prototype_parent" : ("GOBLIN_WIZARD", "ARCHWIZARD_MIXIN")
# }


# world/prototypes.py (lägg till dessa prototypes)

# Crafting Materials
IRON_ORE = {
    "key": "iron ore",
    "typeclass": "typeclasses.objects.Object",
    "desc": "A chunk of raw iron ore, ready for smelting.",
    "tags": [("iron_ore", "crafting_material"), ("material", "item_type")],
    "attrs": [
        ("weight", 2.0),
        ("value", 5)
    ]
}

LEATHER = {
    "key": "piece of leather",
    "typeclass": "typeclasses.objects.Object", 
    "desc": "A piece of tanned leather, supple and ready for crafting.",
    "tags": [("leather", "crafting_material"), ("material", "item_type")],
    "attrs": [
        ("weight", 0.5),
        ("value", 10),
        ("quality", 50)
    ]
}

FLOUR = {
    "key": "bag of flour",
    "typeclass": "typeclasses.objects.Object",
    "desc": "A small bag of wheat flour for baking.",
    "tags": [("flour", "crafting_material"), ("material", "item_type")],
    "attrs": [
        ("weight", 1.0),
        ("value", 3),
        ("perishable", True)
    ]
}

# Crafting Tools
OVEN = {
    "key": "brick oven",
    "typeclass": "typeclasses.objects.CraftingStation",
    "desc": "A large brick oven perfect for baking bread and other foods.",
    "tags": [("oven", "crafting_tool"), ("cooking_station", "item_type")],
    "attrs": [
        ("station_type", "cooking"),
        ("crafting_bonus", 15),
        ("portable", False),
        ("weight", 500)
    ]
}

FORGE = {
    "key": "smithing forge",
    "typeclass": "typeclasses.objects.Forge",
    "desc": "A stone forge with bellows for metalworking.",
    "tags": [("forge", "crafting_tool"), ("metalworking_station", "item_type")],
    "attrs": [
        ("station_type", "metalworking"),
        ("max_temperature", 1500),
        ("crafting_bonus", 20),
        ("portable", False),
        ("weight", 300)
    ]
}

PRECISION_TOOLS = {
    "key": "precision tool kit",
    "typeclass": "typeclasses.objects.ToolKit",
    "desc": "A leather case containing fine precision instruments.",
    "tags": [("precision_tools", "crafting_tool"), ("toolkit", "item_type")],
    "attrs": [
        ("tool_type", "precision"),
        ("engineering_bonus", 15),
        ("quality", 75),
        ("weight", 2)
    ]
}
