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

# --- Bootstrap primitives: stone & stick (gathered) + their nodes ---
# The zero-to-tool loop's raw inputs. STONE + STICK (+ fibre) feed the ungated
# StoneKnifeRecipe (C.3); STONE also anchors future toolmaking. Same shape as
# PLANT_FIBER/FIBER_PLANT: a crafting_material item, and a ResourceNode whose
# yield_prototype equals the material's prototype_key. Nodes are discovered by
# `forage` automatically (ResourceNode + yield_prototype, not a water source).

STONE = {
    "prototype_key": "stone",
    "typeclass": "typeclasses.objects.Object",
    "key": "stone",
    "aliases": ["rock"],
    "desc": (
        "A fist-sized stone, hard and angular. Struck against another, a shard "
        "could be knapped off to take a rough cutting edge."
    ),
    # Matched by tag-key "stone" within the crafting_material category, exactly
    # as PLANT_FIBER uses "fiber".
    "tags": [("stone", "crafting_material")],
}

STICK = {
    "prototype_key": "stick",
    "typeclass": "typeclasses.objects.Object",
    "key": "stick",
    "aliases": ["branch"],
    "desc": (
        "A straight length of dry wood, snapped free of a deadfall. Sound "
        "enough to serve as a handle or haft."
    ),
    "tags": [("stick", "crafting_material")],
}

STONE_OUTCROP = {
    "prototype_key": "stone_outcrop",
    "typeclass": "typeclasses.resources.ResourceNode",
    "key": "rocky outcrop",
    "aliases": ["outcrop", "rocks"],
    "desc": (
        "A shelf of weathered rock breaking through the soil, loose stones "
        "scattered at its foot for the taking."
    ),
    "resource_type": "stones",
    "max_yield": 4,
    "regen_interval": 3600,          # game-seconds/stone; quarried, slower than fibre
    "available": 4,
    "yield_prototype": "stone",      # must equal STONE's prototype_key
}

STICK_DEADFALL = {
    "prototype_key": "stick_deadfall",
    "typeclass": "typeclasses.resources.ResourceNode",
    "key": "fallen branches",
    "aliases": ["deadfall", "branches", "sticks"],
    "desc": (
        "A tangle of dead branches and dry twigs, heaped where a limb came "
        "down. Easy pickings for handles and hafts."
    ),
    "resource_type": "sticks",
    "max_yield": 6,
    "regen_interval": 1800,          # game-seconds/stick; abundant, like fibre
    "available": 6,
    "yield_prototype": "stick",      # must equal STICK's prototype_key
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
    "typeclass": "typeclasses.tools.Tool",
    "key": "knife",
    "aliases": ["blade"],
    "desc": "A simple bladed knife, handy for shaping and cutting.",
    "tags": [("knife", "crafting_tool")],
}

RABBIT = {
    "prototype_key": "rabbit",
    "typeclass": "typeclasses.creatures.Creature",
    "key": "rabbit",
    "aliases": ["bunny", "coney"],
    "desc": (
        "A small wild rabbit with a soft grey-brown coat, ears flat against "
        "its back. It freezes, watchful, ready to bolt at the first wrong move."
    ),
    # siz 4 overrides the typeclass default (8): a rabbit is small prey. This
    # value drives harvest yield (H4) and feeds the hunt difficulty (H2.2).
    "siz": 4,
    # Explicit even though it matches the default -- the rabbit is the canonical
    # owner of the "rabbit" harvest table (meat + a small hide, H4.2).
    "harvest_template": "rabbit",
    # Tag fauna by species so the spawn script (H1.3) and admin tools can query
    # creatures -- mirrors the monster-tag convention in the file's examples.
    "tags": [("rabbit", "creature")],
    # flee_skill intentionally left to the typeclass default (30); the hunt
    # difficulty knob is tuned at H2.2, not baked into the prototype here.
}

# --- Tailoring: woven cloth (intermediate material) + sewing tool ---
# CLOTH is the middle of the tailoring chain: plant fibre -> cloth -> garment.
# Its tag-key "cloth" is what garment recipes list in consumable_tags. Source =
# ClothRecipe (world/recipes.py). A durability/wear SINK is deferred (same plan
# as the waterskin: a future task adds _finalize_item + per-use wear).

CLOTH = {
    "prototype_key": "cloth",
    "typeclass": "typeclasses.objects.Object",
    "key": "bolt of cloth",
    "aliases": ["cloth"],
    "desc": (
        "A length of plain woven cloth, twisted and worked from plant fibres. "
        "Cut and stitched, it can be made into a garment."
    ),
    "tags": [("cloth", "crafting_material")],
}

NEEDLE = {
    "prototype_key": "needle",
    "typeclass": "typeclasses.tools.Tool",
    "key": "sewing needle",
    "aliases": ["needle"],
    "desc": "A slender needle for stitching cloth. Handy, but not strictly needed.",
    # crafting_tool, NOT crafting_material: tools are matched separately and are
    # never consumed. Its own crafting source (bone/bronze) is a future task; the
    # garment recipe works WITHOUT it at a -20 improvised penalty until then.
    "tags": [("needle", "crafting_tool")],
}

# --- Clothing: starter garments (warmth + clothing_type) ---
# Spawn targets for testing the clothing/thermal chain. In the finished economy
# these are NOT spawned freely: their SOURCE is the Task C.1 tailoring recipes
# (player-crafted from gathered fibre/hide), and a durability SINK (same pattern
# as waterskin wear) should follow. clothing_type + warmth are plain top-level
# keys -> stored as db.clothing_type / db.warmth, which is exactly what the
# clothing contrib's `wear` and world.thermal.worn_warmth read.

FUR_CLOAK = {
    "prototype_key": "fur_cloak",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "fur cloak",
    "aliases": ["cloak", "fur"],
    "desc": "A heavy cloak of stitched animal furs, thick enough to turn aside a winter wind.",
    "clothing_type": "fullbody",
    "warmth": 3,
}

WOOL_TUNIC = {
    "prototype_key": "wool_tunic",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "wool tunic",
    "aliases": ["tunic", "wool"],
    "desc": "A coarse woollen tunic, warm and hard-wearing if a little scratchy.",
    "clothing_type": "top",
    "warmth": 2,
}

LINEN_SHIRT = {
    "prototype_key": "linen_shirt",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "linen shirt",
    "aliases": ["shirt", "linen"],
    "desc": "A plain linen shirt, light against the skin and meant to be worn beneath heavier layers.",
    "clothing_type": "undershirt",
    "warmth": 1,
}

LEATHER_BOOTS = {
    "prototype_key": "leather_boots",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "leather boots",
    "aliases": ["boots"],
    "desc": "Sturdy boots of oiled leather, laced high against mud and cold.",
    "clothing_type": "shoes",
    "warmth": 1,
}

STRAW_HAT = {
    "prototype_key": "straw_hat",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "straw hat",
    "aliases": ["hat", "straw"],
    "desc": "A broad-brimmed hat woven from straw, good for keeping sun and rain off the face.",
    "clothing_type": "hat",
    # warmth 0 on purpose: this is a sun/rain piece. Its protection will live on
    # the reserved rain_protection hook once that axis lands -- not warmth.
    "warmth": 0,
}

# --- Hunting: harvestable creature parts (H4.2) ---
# SOURCE: the harvest command (H4.3) spawns these from a corpse, gated by skill
# and decay. They are NOT spawned freely in the finished economy -- same as the
# clothing prototypes above. SINKS: rabbit_meat -> eaten (CmdEat); raw_hide ->
# consumed by the H5 tanning recipe into leather. Both prototype_keys are
# referenced by world/harvest_templates.py's rabbit template.

RABBIT_MEAT = {
    "prototype_key": "rabbit_meat",
    "typeclass": "typeclasses.consumables.Food",
    "key": "raw rabbit meat",
    "aliases": ["meat", "rabbit meat"],
    "desc": (
        "A portion of raw, dark rabbit meat, still cool to the touch. Edible as "
        "it is, though gamey and tough -- it would sit far better cooked."
    ),
    # Modest restore on purpose: this is raw small-game. The future cooking step
    # (a recipe turning rabbit_meat -> cooked_meat) is where the larger hunger
    # payoff should live, so this is left with headroom. Plain top-level keys map
    # to db.restore_amount / db.consume_message, exactly what CmdEat reads.
    "restore_amount": 15,
    "consume_message": "You eat {key}. Gamey and tough raw, but it takes the edge off your hunger.",
}

RAW_HIDE = {
    "prototype_key": "raw_hide",
    "typeclass": "typeclasses.objects.Object",
    "key": "raw hide",
    # NOTE: deliberately no "skin" alias -- that collides with the waterskin's
    # "skin" alias and would make `... skin` ambiguous for anyone carrying both.
    "aliases": ["hide", "pelt"],
    "desc": (
        "A raw animal hide, fur still on and the underside damp. Untreated it "
        "will spoil; tanned, it becomes leather fit for working."
    ),
    # crafting_material tag-key "raw_hide" is what the H5 tanning recipe lists in
    # consumable_tags. Same convention as PLANT_FIBER's "fiber" and CLOTH's "cloth".
    "tags": [("raw_hide", "crafting_material")],
}

LEATHER = {
    "prototype_key": "leather",
    "typeclass": "typeclasses.objects.Object",
    "key": "piece of leather",
    "aliases": ["leather"],
    "desc": (
        "A supple piece of tanned leather, cured from a raw hide. Worked and "
        "stitched, it becomes boots, straps and other sturdy gear."
    ),
    # crafting_material tag-key "leather" is what the leather-boots recipe (H5.2)
    # lists in consumable_tags. Same convention as CLOTH's "cloth" and
    # RAW_HIDE's "raw_hide".
    "tags": [("leather", "crafting_material")],
}
