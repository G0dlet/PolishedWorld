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
    "enc": 0,   # Q6: food carries no ENC (Legend core p. 111)
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
    "enc": 0,   # Q6: at least the twine it is twisted into (twine ENC 0)
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
    "enc": 1,   # Q6: at least the waterskin it is made into (waterskin ENC 1)
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
    "enc": 1,   # Q6: fist-sized; AoL p. 29 Milling Stones (a pair) ENC 2
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
    "enc": 0,   # Q6: haft-length, short of AoL p. 29 Walking Stick (ENC 1)
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
    "enc": 0,   # Q6: too light to score (AoL p. 28 Elfen Bowstring, ENC "—")
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
    "enc": 1,   # Legend core p. 119 / AoL p. 29: Waterskin, ENC 1
}

KNIFE = {
    "prototype_key": "knife",
    "typeclass": "typeclasses.tools.Tool",
    "key": "knife",
    "aliases": ["blade"],
    "desc": "A simple bladed knife, handy for shaping and cutting.",
    "tags": [("knife", "crafting_tool")],
    "enc": 0,   # Legend core p. 106: Knife, ENC "—" -- too light to score
}

# --- Bootstrap tool: crude stone knife (crafted, C.3) ---
# The zero-to-tool loop's OUTPUT: a knapped stone flake lashed to a haft. A real
# Tool typeclass (so it owns `condition` for free via DurableObject), tagged
# ("knife", "crafting_tool") -- the SAME tool-key as the metal KNIFE, so it
# satisfies every recipe that wants a knife (waterskin, leather). DISTINCT from
# KNIFE (locked decision a): a named, world-flavoured crude tool and a target for
# Component D wear balance, while start `condition` stays at the DurableObject
# default (100) -- start-condition tuning is deferred to when wear is live.
STONE_KNIFE = {
    "prototype_key": "stone_knife",
    "typeclass": "typeclasses.tools.Tool",
    "key": "stone knife",
    # NOT "knife"/"blade": individuated so it never multimatches the metal KNIFE
    # (key "knife", alias "blade"). Tool-matching is by TAG, not name, so this
    # alias choice costs nothing downstream.
    "aliases": ["stone blade"],
    "desc": (
        "A crude knife: a sharp-knapped stone flake lashed to a short wooden "
        "haft with plant fibre. Rough, but it holds an edge well enough to work."
    ),
    "tags": [("knife", "crafting_tool")],
    # Data-driven repair (D.4): a stone knife is re-hafted, not patched -- re-lash
    # the flake to a fresh stick with plant fibre. Tag-keys: STICK ("stick") +
    # PLANT_FIBER ("fiber"). Overrides CmdRepair's cloth/twine default.
    "repair_materials": ("stick", "fiber"),
    # Data-driven repair TOOL (G.2): re-hafting is bare-handed, so no tool eases
    # it -- "" means "no tool needed", read by CmdRepair._tool_modifier as a flat
    # 0 (no bonus, no penalty). This also stops a carried needle from wrongly
    # shifting a stone-knife repair (the old garment-centric bug).
    "repair_tool_tag": "",
    # Crude bootstrap tool: short-lived so wear is felt early (D.5). Overrides
    # DurableObject's autocreate-100. Metal KNIFE stays pristine (no override).
    "condition": 40,
    "enc": 0,   # Legend core p. 106: Knife, ENC "—" -- too light to score
}

# --- Felling chain: flint, stone axe, wood, tree, club (AC2.2) ---
# The second bootstrap loop. Flint (gathered bare-handed) + stick + twine make
# the stone axe; the axe is the only way to take wood from a TREE (its
# required_tool, checked and worn by `forage`, AC2.1); wood's first consumer is
# the club. Every item carries Legend ENC (`enc`, AD8): from the rulebook where
# it gives one, else Q6's rule -- too light to score is stored as 0, and the
# 20-to-1 counting is left to the weight mechanic. Nothing reads `enc` yet.
# Nodes carry none: they cannot be picked up.

FLINT = {
    "prototype_key": "flint",
    "typeclass": "typeclasses.objects.Object",
    "key": "flint nodule",
    "aliases": ["flint"],
    "desc": (
        "A knobbly nodule of flint, chalk-white outside and glassy dark within. "
        "Struck right, it flakes away in sharp-edged shells."
    ),
    # tag-key "flint" is what recipes list in consumable_tags. SOURCE: the
    # flint_scatter node. SINK: StoneAxeRecipe knaps it into the axe head.
    "tags": [("flint", "crafting_material")],
    "enc": 0,   # Q6: too light to score (AoL lists flint and tinder as "—")
}

FLINT_SCATTER = {
    "prototype_key": "flint_scatter",
    "typeclass": "typeclasses.resources.ResourceNode",
    "key": "flint scatter",
    "aliases": ["scatter", "flints"],
    "desc": (
        "A spill of pale flint nodules weathering out of a chalky bank, the "
        "ground around them glittering with old flakes."
    ),
    "resource_type": "flint",
    "max_yield": 4,
    "regen_interval": 3600,          # game-seconds/nodule; as the stone outcrop
    "available": 4,
    "yield_prototype": "flint",      # must equal FLINT's prototype_key
}

# The felling tool. A Tool (condition via DurableObject), tagged ("axe",
# "crafting_tool"): the tag `forage` checks against TREE's required_tool, and
# what the registry's `axe` entry points at. No bare "axe" alias -- the stone
# knife's lesson: a future metal axe must never multimatch it.
STONE_AXE = {
    "prototype_key": "stone_axe",
    "typeclass": "typeclasses.tools.Tool",
    "key": "stone axe",
    "aliases": ["stone hatchet"],
    "desc": (
        "A knapped flint head seated in a split wooden haft and bound tight with "
        "twine. Heavy at the business end, and sharp enough to bite into a trunk."
    ),
    # SOURCE: StoneAxeRecipe (flint + stick + twine). Never consumed (a tool).
    # SINK: wear -- every successful `forage` from a TREE costs it
    # FORAGE_TOOL_WEAR, and a broken axe is refused until repaired.
    "tags": [("axe", "crafting_tool")],
    # Re-hafted, not patched: a fresh stick, lashed with twine (D.4). Without
    # this CmdRepair falls back to the garment default (cloth/twine + needle).
    "repair_materials": ("stick", "twine"),
    "repair_tool_tag": "",           # bare-handed: no tool eases it (G.2)
    "condition": 40,                 # crude bootstrap tool, as STONE_KNIFE (D.5)
    "enc": 1,                        # Legend core p. 106: Hatchet, ENC 1
}

WOOD = {
    "prototype_key": "wood",
    "typeclass": "typeclasses.objects.Object",
    "key": "length of wood",
    "aliases": ["wood", "log"],
    "desc": "A length of green timber hacked from a living trunk, heavy and sound.",
    # tag-key "wood" -- one generic tag, species is flavour (AD2, DECISION #10).
    # SOURCE: the tree node, axe required. SINK: ClubRecipe.
    "tags": [("wood", "crafting_material")],
    "enc": 1,   # Q6: at least the club it is shaped into (club ENC 1)
}

TREE = {
    "prototype_key": "tree",
    "typeclass": "typeclasses.resources.ResourceNode",
    "key": "tree",
    "aliases": ["trunk"],
    "desc": (
        "A tall ash, straight-grained and grey-barked, its lower limbs within "
        "reach of an axe. Nothing comes off it by hand."
    ),
    "resource_type": "wood",
    "max_yield": 3,
    "regen_interval": 7200,          # game-seconds/length; scarcer, as the gourd vine
    "available": 3,
    "yield_prototype": "wood",       # must equal WOOD's prototype_key
    "required_tool": "axe",          # crafting_tool tag-key; `forage` refuses without one
}

CLUB = {
    "prototype_key": "club",
    "typeclass": "typeclasses.objects.Object",
    "key": "club",
    "aliases": ["cudgel"],
    "desc": "A length of wood shaped to a heavy, knotted head and a grip worn smooth.",
    # SOURCE: ClubRecipe (wood). SINK: none in the alpha -- no combat (AD5's
    # "use in alpha" column; Q1 decides inert goods in AC4.0).
    "enc": 1,   # Legend core p. 106: Club, ENC 1
}

# --- Clay chain: clay, clay bank, sling bullet (AC2.3) ---
# Clay is dug bare-handed from a CLAY_BANK; its first consumer is the sling
# bullet, rolled by hand and left to dry in the sun. Sun-dried is a real stage,
# not a collapsed one (AoL's potter makes "sun-dried" jugs); the fired variant
# is BLOCKED: kiln, and no drying timer is modelled (a per-object timer, AGENTS
# section 1 rule 7). Both items carry `enc` (AD8): 0 is Q6's "too light to
# score", never weightless -- the weight mechanic counts such items 20 to 1.

CLAY = {
    "prototype_key": "clay",
    "typeclass": "typeclasses.objects.Object",
    "key": "lump of clay",
    "aliases": ["clay"],
    "desc": (
        "A fist-sized lump of grey riverbank clay, cold and slick, that keeps "
        "the print of every finger pressed into it."
    ),
    # tag-key "clay" is what recipes list in consumable_tags. SOURCE: the
    # clay_bank node. SINK: SlingBulletRecipe rolls it into a bullet.
    "tags": [("clay", "crafting_material")],
    "enc": 0,   # Q6: at least the bullet it is rolled into (bullet ENC 0)
}

CLAY_BANK = {
    "prototype_key": "clay_bank",
    "typeclass": "typeclasses.resources.ResourceNode",
    "key": "clay bank",
    "aliases": ["bank"],
    "desc": (
        "A slumped bank of grey clay where the water has cut into the slope, "
        "smooth and glistening where it is wet."
    ),
    "resource_type": "clay",
    "max_yield": 4,
    "regen_interval": 3600,          # game-seconds/lump; as the flint scatter
    "available": 4,
    "yield_prototype": "clay",       # must equal CLAY's prototype_key
}

SLING_BULLET = {
    "prototype_key": "sling_bullet",
    "typeclass": "typeclasses.objects.Object",
    "key": "sling bullet",
    "aliases": ["bullet"],
    "desc": "A hard oval of sun-dried clay, rolled smooth between the palms.",
    # SOURCE: SlingBulletRecipe (clay). SINK: none in the alpha -- the sling
    # exists, but there is no combat (AD5's "use in alpha" column; Q1 decides
    # inert goods in AC4.0).
    "enc": 0,   # AoL: Sling Bullets (10), ENC "—" -- too light to score (Q6)
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
    "enc": 0,   # Q6: at least the shirt it is sewn into (shirt ENC 0)
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
    "enc": 0,   # Q6: too light to score (Legend core p. 112: a craft-tools set is ENC 1)
}

# --- Bootstrap tool: bone needle (crafted from harvested bone, C.4) ---
# The tailoring bootstrap's OUTPUT, deliberately hunting-linked: its only input
# is `bone`, harvested from a corpse (C.4 harvest part). A real Tool (owns
# `condition` via DurableObject), tagged ("needle","crafting_tool") -- the SAME
# tool-key as the plain NEEDLE, so it satisfies every recipe that wants a needle
# (linen shirt, leather boots). DISTINCT from NEEDLE (parity with stone_knife):
# a crude, world-flavoured tool and a Component D wear target, while NEEDLE stays
# as a future bronze/metal needle. Start `condition` autocreates to 100.
BONE_NEEDLE = {
    "prototype_key": "bone_needle",
    "typeclass": "typeclasses.tools.Tool",
    "key": "bone needle",
    # NOT a bare "needle" alias: individuated so it never multimatches the plain
    # NEEDLE (alias "needle"). Tool-matching is by TAG, not name, so this costs
    # nothing downstream.
    "aliases": ["bone pin"],
    "desc": (
        "A crude needle ground from a splinter of bone, its eye bored by hand. "
        "Rough at the point, but it draws thread through cloth well enough."
    ),
    "tags": [("needle", "crafting_tool")],
    # Data-driven repair (D.4): re-grind the point from a fresh bone splinter.
    # Single-material by design (balance-tunable later); tag-key BONE ("bone").
    "repair_materials": ("bone",),
    # Data-driven repair TOOL (G.2): re-grinding the point is bare-handed, so no
    # tool eases it -- "" = "no tool needed" (flat 0 in CmdRepair._tool_modifier),
    # and a carried needle can't wrongly shift a bone-needle repair.
    "repair_tool_tag": "",
    # Crude bootstrap tool: short-lived so wear is felt early (D.5). Overrides
    # DurableObject's autocreate-100. Metal NEEDLE stays pristine (no override).
    "condition": 30,
    "enc": 0,   # Q6: too light to score (Legend core p. 112: a craft-tools set is ENC 1)
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
    "enc": 0,   # Q6: Legend core pp. 98-100 give clothing no ENC
}

WOOL_TUNIC = {
    "prototype_key": "wool_tunic",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "wool tunic",
    "aliases": ["tunic", "wool"],
    "desc": "A coarse woollen tunic, warm and hard-wearing if a little scratchy.",
    "clothing_type": "top",
    "warmth": 2,
    "enc": 0,   # Q6: Legend core pp. 98-100 give clothing no ENC
}

LINEN_SHIRT = {
    "prototype_key": "linen_shirt",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "linen shirt",
    "aliases": ["shirt", "linen"],
    "desc": "A plain linen shirt, light against the skin and meant to be worn beneath heavier layers.",
    "clothing_type": "undershirt",
    "warmth": 1,
    "enc": 0,   # Q6: Legend core pp. 98-100 give clothing no ENC
}

LEATHER_BOOTS = {
    "prototype_key": "leather_boots",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "leather boots",
    "aliases": ["boots"],
    "desc": "Sturdy boots of oiled leather, laced high against mud and cold.",
    "clothing_type": "shoes",
    "warmth": 1,
    "enc": 0,   # Q6: Legend core pp. 98-100 give clothing no ENC
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
    "enc": 0,   # Q6: Legend core pp. 98-100 give clothing no ENC
}

# --- Cloth goods (AC4.1) ---

BREECHES = {
    "prototype_key": "breeches",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "breeches",
    "aliases": ["pants", "trousers"],
    "desc": "A plain pair of cloth breeches, cut for movement and stitched hard at the seams.",
    # SOURCE: BreechesRecipe (cloth x2). SINK: worn for warmth (survival).
    "clothing_type": "bottom",
    "warmth": 1,
    "enc": 0,   # AoL p. 37 / Legend core pp. 98-100: no ENC for clothing
}

ROBE = {
    "prototype_key": "robe",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "robe",
    "aliases": ["dress", "gown"],
    "desc": (
        "A full-length cloth robe with a generous cut, deep sleeves and a "
        "closely stitched hem."
    ),
    # SOURCE: RobeRecipe (cloth x3). SINK: worn for warmth (survival).
    "clothing_type": "fullbody",
    "warmth": 1,
    "enc": 0,   # AoL p. 37 / Legend core pp. 98-100: no ENC for clothing
}

HOOD = {
    "prototype_key": "hood",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "hood",
    "aliases": ["cowl"],
    "desc": "A deep cloth hood with a short shoulder cape and close-stitched seams.",
    # SOURCE: HoodRecipe (cloth x1). SINK: worn for warmth (survival).
    "clothing_type": "hat",
    "warmth": 1,
    "enc": 0,   # AoL p. 37 / Legend core pp. 98-100: no ENC for clothing
}

REVERSIBLE_CLOTHES = {
    "prototype_key": "reversible_clothes",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "reversible clothes",
    "aliases": ["reversible garment", "clothes"],
    "desc": (
        "A carefully finished cloth garment with two contrasting faces and "
        "clean seams on both sides."
    ),
    # SOURCE: ReversibleClothesRecipe (cloth x4). SINK: worn for warmth (survival).
    "clothing_type": "top",
    "warmth": 1,
    "enc": 0,   # AoL p. 37 / Legend core pp. 98-100: no ENC for clothing
}

LINEN_CUIRASS = {
    "prototype_key": "linen_cuirass",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "linen cuirass",
    "aliases": ["cuirass", "linen armour"],
    "desc": (
        "Layer upon layer of linen is stitched into a close-fitting chest piece, "
        "firm to the touch without any metal fittings."
    ),
    # SOURCE: LinenCuirassRecipe (cloth x4). SINK: worn for warmth (survival); armour waits for combat (Stage 5).
    "clothing_type": "top",
    "warmth": 1,
    "enc": 1,   # AoL p. 50 / Legend core p. 96: Linen, ENC 1 per chest location
}

SACK = {
    "prototype_key": "sack",
    "typeclass": "typeclasses.objects.Object",
    "key": "large sack",
    "aliases": ["sack", "bag"],
    "desc": (
        "A broad-mouthed sack of heavy plain cloth, its seams doubled and its "
        "mouth gathered with a stitched hem."
    ),
    # SOURCE: SackRecipe (cloth x2, canvas as cloth #11). SINK: none in the alpha (containers, AD8).
    "enc": 1,   # AoL p. 29: Sack, large, ENC 1
}

# --- Leather and bone goods (AC4.2) ---

BACKPACK = {
    "prototype_key": "backpack",
    "typeclass": "typeclasses.objects.Object",
    "key": "backpack",
    "aliases": ["pack"],
    "desc": (
        "A squared leather pack with broad shoulder straps and a flap secured "
        "by a stitched thong."
    ),
    # SOURCE: BackpackRecipe (leather x2). SINK: none in the alpha (containers, AD8).
    "enc": 1,   # AoL p. 28: Backpack, ENC 1
}

SCROLLCASE = {
    "prototype_key": "scrollcase",
    "typeclass": "typeclasses.objects.Object",
    "key": "scrollcase",
    "aliases": ["scroll case"],
    "desc": (
        "A hollow bone tube fitted with a snug cap, its polished sides guarding "
        "rolled parchment from creases."
    ),
    # SOURCE: ScrollcaseRecipe (bone). SINK: none in the alpha (scroll storage, AD8).
    "enc": 0,   # AoL p. 29: Scrollcase, ENC "—" -- too light to score
}

SADDLEBAG = {
    "prototype_key": "saddlebag",
    "typeclass": "typeclasses.objects.Object",
    "key": "saddlebag",
    "aliases": ["saddle bag"],
    "desc": (
        "A deep leather bag with a reinforced spine and long straps, made to "
        "hang balanced across a mount's flank."
    ),
    # SOURCE: SaddlebagRecipe (leather x3). SINK: none in the alpha (containers, AD8).
    "enc": 2,   # AoL p. 30: Saddlebag, ENC 2
}

SHOES = {
    "prototype_key": "shoes",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "shoes",
    "aliases": ["leather shoes"],
    "desc": (
        "A pair of low leather shoes with stitched soles and soft uppers that "
        "close with narrow thongs."
    ),
    # SOURCE: ShoesRecipe (leather). SINK: worn for warmth (survival).
    "clothing_type": "shoes",
    "warmth": 1,
    "enc": 0,   # AoL p. 37 / Legend core pp. 98-100: no ENC for clothing
}

BANDOLIER = {
    "prototype_key": "bandolier",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "bandolier",
    "aliases": ["bandoleer"],
    "desc": (
        "A broad leather belt stitched with small loops, cut to cross from one "
        "shoulder to the opposite hip."
    ),
    # SOURCE: BandolierRecipe (leather). SINK: none in the alpha (item storage, AD8).
    "clothing_type": "accessory",
    "warmth": 0,
    "enc": 0,   # AoL p. 37 / Legend core pp. 98-100: no ENC for clothing
}

BONE_ARMOUR = {
    "prototype_key": "bone_armour",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "bone armour",
    "aliases": ["bone armor"],
    "desc": (
        "Plates of pale bone are lashed across a shaped leather backing, "
        "overlapping to shelter the chest without hiding their rough joints."
    ),
    # SOURCE: BoneArmourRecipe (bone x3 + leather). SINK: worn for warmth
    # (survival); armour waits for combat (Stage 5).
    "clothing_type": "top",
    "warmth": 1,
    "enc": 2,   # AoL p. 50: Bone, ENC 2 per location; the chest
}

SLING = {
    "prototype_key": "sling",
    "typeclass": "typeclasses.objects.Object",
    "key": "sling",
    "aliases": ["leather sling"],
    "desc": (
        "A supple leather pouch tapering into two long cords, one looped for a "
        "finger and the other left free to release."
    ),
    # SOURCE: SlingRecipe (leather). SINK: none in the alpha (combat, Stage 5).
    "enc": 0,   # Legend core p. 109: Sling, ENC "—" -- too light to score
}

# --- Wood and stone goods (AC4.3) ---

QUARTERSTAFF = {
    "prototype_key": "quarterstaff",
    "typeclass": "typeclasses.objects.Object",
    "key": "quarterstaff",
    "aliases": ["long staff"],
    "desc": (
        "A tall wooden staff, shaped and smoothed along its full length, with "
        "a balanced grip at its middle."
    ),
    # SOURCE: QuarterstaffRecipe (wood x2). SINK: none in the alpha (combat, Stage 5).
    "enc": 2,   # Legend core p. 107: Quarter staff, ENC 2
}

SPEAR = {
    "prototype_key": "spear",
    "typeclass": "typeclasses.objects.Object",
    "key": "spear",
    "aliases": ["short spear"],
    "desc": (
        "A bone point seated on a long wooden shaft and bound fast with twine. "
        "Simple, light and balanced for a firm grip."
    ),
    # SOURCE: SpearRecipe (wood x2 + bone + twine). SINK: none in the alpha
    # (combat, Stage 5).
    "enc": 2,   # Legend core p. 107: Short spear, ENC 2
}

BOW = {
    "prototype_key": "bow",
    "typeclass": "typeclasses.objects.Object",
    "key": "bow",
    "aliases": ["short bow"],
    "desc": (
        "A supple wooden stave bent into a short bow and strung with taut "
        "plant-fibre twine."
    ),
    # SOURCE: BowRecipe (wood + twine). SINK: none in the alpha (combat, Stage 5).
    "enc": 1,   # Legend core p. 109: Short bow, ENC 1
}

MILLING_STONES = {
    "prototype_key": "milling_stones",
    "typeclass": "typeclasses.objects.Object",
    "key": "milling stones",
    "aliases": ["quern"],
    "desc": (
        "A matched pair of heavy stones, one dished and one rounded, their "
        "grinding faces pecked rough by hand."
    ),
    # Plain inert Object, not the registry's separate grindstone tool entry.
    # SOURCE: MillingStonesRecipe (stone x2). SINK: none in the alpha
    # (milling, unscheduled).
    "enc": 2,   # AoL p. 29: Milling Stones, ENC 2
}

TENT = {
    "prototype_key": "tent",
    "typeclass": "typeclasses.objects.Object",
    "key": "tent",
    "aliases": ["four-person tent"],
    "desc": (
        "Four panels of heavy cloth make a low, broad shelter, held taut over "
        "wooden poles by doubled twine guys."
    ),
    # SOURCE: TentRecipe (cloth x4 + wood x2 + twine x2). SINK: none in the
    # alpha (shelter, unscheduled).
    "enc": 2,   # AoL p. 29: Tent, 4 person, ENC 2
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
    "enc": 0,   # Q6: food carries no ENC (Legend core p. 111)
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
    "enc": 0,   # Q6: at least the leather it is tanned into (leather ENC 0)
}

BONE = {
    "prototype_key": "bone",
    "typeclass": "typeclasses.objects.Object",
    "key": "bone",
    "aliases": ["small bone"],
    "desc": (
        "A slender, clean-picked bone, hard and pale. Ground to a point and "
        "eyed, it could serve as a crude sewing needle."
    ),
    # crafting_material tag-key "bone" -> BoneNeedleRecipe consumable_tags.
    # Same convention as RAW_HIDE's "raw_hide" and PLANT_FIBER's "fiber".
    "tags": [("bone", "crafting_material")],
    "enc": 0,   # Q6: at least the needle it is carved into (needle ENC 0)
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
    "enc": 0,   # Q6: at least the boots it is sewn into (boots ENC 0)
}


SCROLL = {
    "prototype_key": "scroll",
    # F.3: Scroll subclass adds a readable recipe-detail block on `look` (via
    # get_display_desc). inscribe still spawns "scroll" and stamps db.recipe; the
    # instance is now a Scroll, so looking at it shows what it teaches.
    "typeclass": "typeclasses.scroll.Scroll",
    "key": "recipe scroll",
    "aliases": ["scroll"],
    "desc": (
        "A blank scroll of woven cloth. Inscribed with a recipe, it can teach "
        "that craft to whoever studies it -- once."
    ),
    # No crafting_material tag: a scroll is a finished knowledge-carrier consumed
    # by `learn` (Component F.2), not an ingredient for any recipe. The recipe it
    # teaches is stamped onto the spawned instance by `inscribe`
    # (obj.db.recipe = <name>), NOT baked into the prototype.
    "enc": 0,   # Q6: lighter than its case (AoL p. 29 Scrollcase, ENC "—")
}

BOOK = {
    "prototype_key": "book",
    # G.1: Book(DurableObject, Object) -- carries a `condition` wear axis and a
    # list of recipes (db.recipes). `scribe` (G.2) spawns "book", stamps the
    # recipe list + a barter-searchable key, and sets the start condition from
    # the author's craft outcome; `learn ... from <book>` (G.3) wears it down.
    "typeclass": "typeclasses.books.Book",
    "key": "recipe book",
    "aliases": ["book"],
    "desc": (
        "A blank book of bound cloth pages. Scribed with recipes, it can teach "
        "those crafts to whoever studies it -- each reading wears it a little."
    ),
    # No crafting_material tag and no baked db.recipes/condition: a book is a
    # finished knowledge-carrier, not an ingredient. Its recipe list and start
    # condition are stamped/set onto the spawned instance by `scribe` (G.2),
    # NOT baked into the prototype -- the same split the SCROLL prototype uses.
    "enc": 1,   # Legend core p. 112 / AoL p. 28: Codex, ENC 1
}
