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

# --- Foraging: berries & berry bush ---

BERRIES = {
    "prototype_key": "berries",
    "typeclass": "typeclasses.consumables.Food",
    "key": "handful of berries",
    "desc": "A small handful of wild berries, tart and faintly sweet.",
    "restore_amount": 10,
    "consume_message": "You eat the berries. Tart, but they take the edge off your hunger.",
}

BERRY_BUSH = {
    "prototype_key": "berry_bush",
    "typeclass": "typeclasses.resources.ResourceNode",
    "key": "berry bush",
    "aliases": ["bush"],
    "desc": "A low, tangled bush, its branches dotted with small wild berries.",
    "resource_type": "berries",
    "max_yield": 5,
    "regen_interval": 3600,        # game-seconds per berry (see note)
    "available": 5,
    "yield_prototype": "berries",  # must equal BERRIES' prototype_key
}

SPRING = {
    "prototype_key": "spring",
    "typeclass": "typeclasses.resources.ResourceNode",
    "key": "natural spring",
    "aliases": ["spring", "water"],
    "desc": "Cold, clear water wells up from between mossy stones and trickles away downhill.",
    "resource_type": "water",
    "is_water_source": True,
}

PLANT_FIBER = {
    "prototype_key": "plant_fiber",
    "typeclass": "typeclasses.objects.Object",
    "key": "plant fiber",
    "aliases": ["fiber"],
    "desc": (
        "A loose bundle of tough, stringy fibres stripped from a fibrous "
        "plant. Twisted together, they could be worked into cordage."
    ),
    # The crafting contrib matches consumables by tag key within the
    # 'crafting_material' category. "fiber" is what recipes will list.
    "tags": [("fiber", "crafting_material")],
}

RAW_GOURD = {
    "prototype_key": "raw_gourd",
    "typeclass": "typeclasses.objects.Object",
    "key": "gourd",
    "aliases": ["raw gourd"],
    "desc": (
        "A hard-shelled gourd, light and hollow once dried. Fitted with a "
        "strap and a stopper, it could be made to hold water."
    ),
    "tags": [("gourd", "crafting_material")],
}

FIBER_PLANT = {
    "prototype_key": "fiber_plant",
    "typeclass": "typeclasses.resources.ResourceNode",
    "key": "fibrous plant",
    "aliases": ["plant", "fibre plant"],
    "desc": "A clump of tall, sinewy stalks whose stems peel into long, tough fibres.",
    "resource_type": "fibres",
    "max_yield": 6,
    "regen_interval": 1800,          # game-seconds per fibre; abundant (3 needed per twine)
    "available": 6,
    "yield_prototype": "plant_fiber",  # must equal PLANT_FIBER's prototype_key
}

GOURD_VINE = {
    "prototype_key": "gourd_vine",
    "typeclass": "typeclasses.resources.ResourceNode",
    "key": "gourd vine",
    "aliases": ["vine", "gourd plant"],
    "desc": "A sprawling vine heavy with hard-shelled gourds ripening along the ground.",
    "resource_type": "gourds",
    "max_yield": 3,
    "regen_interval": 7200,          # game-seconds per gourd; scarcer (1 per waterskin)
    "available": 3,
    "yield_prototype": "raw_gourd",    # must equal RAW_GOURD's prototype_key
}

TWINE = {
    "prototype_key": "twine",
    "typeclass": "typeclasses.objects.Object",
    "key": "length of twine",
    "aliases": ["twine", "cord", "cordage"],
    "desc": "A length of twine twisted from plant fibres \u2014 rough but serviceable cordage.",
    # Twine is itself a crafting material (consumed by the waterskin recipe in 3.3).
    "tags": [("twine", "crafting_material")],
}

WATERSKIN = {
    "prototype_key": "waterskin",
    "typeclass": "typeclasses.consumables.Drink",
    "key": "waterskin",
    "aliases": ["skin"],
    "desc": "A hollow gourd fitted with a twine strap and a snug stopper, light enough to carry a few draughts of water.",
    # Drink's AttributeProperty fields, set per-prototype (same pattern as BERRIES):
    "charges": 0,            # crafted EMPTY — must be filled at a water source
    "max_charges": 5,        # quality-scaling deferred to Task 4.1
    "restore_amount": 15,
    "refillable": True,
}

KNIFE = {
    "prototype_key": "knife",
    "typeclass": "typeclasses.objects.Object",
    "key": "knife",
    "aliases": ["blade"],
    "desc": "A simple bladed knife, handy for shaping and cutting.",
    "tags": [("knife", "crafting_tool")],
}
