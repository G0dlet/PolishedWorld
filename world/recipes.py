"""
world/recipes.py

Concrete crafting recipes, discovered by Evennia's crafting contrib via
CRAFT_RECIPE_MODULES. Recipes subclass MongooseCraftRecipe (world/crafting_base.py)
to inherit Legend skill resolution, quality, tool modifiers and the cooldown sink.

NOTE: MongooseCraftRecipe is imported, not defined here. callables_from_module()
only registers classes whose __module__ is this module, so the imported base is
not picked up as a phantom recipe.
"""

from world.crafting_base import MongooseCraftRecipe


class TwineRecipe(MongooseCraftRecipe):
    """Twist three plant fibres into a length of twine."""

    name = "twine"
    consumable_tags = ["fiber", "fiber", "fiber"]   # three fibres, matched by tag-key
    output_prototypes = ["twine"]
    tool_tag = None                                 # handcraft; no tool benefit
    craft_cooldown = 20                             # quick craft (overrides base 30)


class WaterskinRecipe(MongooseCraftRecipe):
    """Fit a hollow gourd with a twine strap and stopper to make a waterskin."""

    name = "waterskin"
    consumable_tags = ["gourd", "twine"]   # consumed
    output_prototypes = ["waterskin"]
    tool_tag = "knife"                     # OPTIONAL: knife shapes the gourd (+20); improvised -20
    craft_cooldown = 45                    # more involved than twine

    def _finalize_item(self, obj, outcome):
        quality = obj.db.quality
        # Mongoose Legend Item Quality bands -> capacity + lifespan (in refills).
        if quality >= 125:                              # superior (critical + bonus)
            obj.db.max_charges, obj.db.durability = 6, 12
        elif quality >= 100:                            # serviceable (success)
            obj.db.max_charges, obj.db.durability = 5, 10
        elif quality >= 50:                             # poor (failure)
            obj.db.max_charges, obj.db.durability = 4, 6
        else:                                           # shoddy (fumble, q25)
            obj.db.max_charges, obj.db.durability = 3, 3
        obj.db.charges = 0                              # crafted empty regardless


class ClothRecipe(MongooseCraftRecipe):
    """Weave plant fibres into a bolt of plain cloth."""

    name = "cloth"
    consumable_tags = ["fiber", "fiber", "fiber"]   # three fibres per bolt
    output_prototypes = ["cloth"]
    tool_tag = None                                 # handwoven; no tool benefit
    craft_cooldown = 25                             # between twine (20) and waterskin (45)


class LeatherRecipe(MongooseCraftRecipe):
    """Tan two raw hides into a piece of workable leather."""

    name = "leather"                              # recipe-registry name (≠ prototype_key, separate namespace)
    consumable_tags = ["raw_hide", "raw_hide"]    # two hides per piece, matched by tag-key
    output_prototypes = ["leather"]               # the new H5.1 prototype
    tool_tag = "knife"                            # OPTIONAL: knife scrapes/cuts the hide (+20); absent = -20
    craft_cooldown = 45                           # involved work (soak/scrape/tan); overrides base 30


class LinenShirtRecipe(MongooseCraftRecipe):
    """Cut and stitch cloth into a linen shirt (undershirt layer)."""

    name = "linen shirt"
    consumable_tags = ["cloth", "cloth"]   # two bolts per shirt
    output_prototypes = ["linen_shirt"]    # the existing B.3 prototype
    tool_tag = "needle"                    # OPTIONAL: needle eases stitching (+20); improvised -20
    craft_cooldown = 40

    # NOTE: no _finalize_item override yet. db.quality is stamped by the base; a
    # future durability/wear task will read it (deferred sink, per the C.1 plan).


class LeatherBootsRecipe(MongooseCraftRecipe):
    """Stitch two pieces of leather into a pair of sturdy boots."""

    name = "leather boots"                       # space, mirroring "linen shirt"
    consumable_tags = ["leather", "leather"]     # two pieces per pair
    output_prototypes = ["leather_boots"]        # existing Component B prototype
    tool_tag = "needle"                          # OPTIONAL: needle eases stitching (+20); improvised -20
    craft_cooldown = 40                          # mirrors linen shirt
    # No _finalize_item: db.quality is stamped by the base; the H6 durability/wear
    # task will read it. Same deferred-sink stance as LinenShirtRecipe.


class StoneKnifeRecipe(MongooseCraftRecipe):
    """Knap a stone flake, haft it to a stick, lash it with fibre: a crude knife.

    The bootstrap tool of the zero-to-tool loop -- ungated and tool-free so a
    brand-new character can make their first knife from gathered primitives alone.
    """

    name = "stone knife"
    # Stone flake + wooden haft + fibre lashing, matched by crafting_material
    # tag-key. Raw `fiber` (not crafted twine) keeps this a SINGLE craft with no
    # nested sub-craft, so the very first tool stays low-friction (decision b).
    consumable_tags = ["stone", "stick", "fiber"]
    output_prototypes = ["stone_knife"]
    # tool_tag=None -> _tool_modifier() returns 0 (NO improvised penalty): a
    # bootstrap you make with your hands must not be penalised for lacking the
    # very tool it exists to give you. No min_skill: the base has no skill floor,
    # so ungated is simply the default.
    tool_tag = None
    craft_cooldown = 30                 # base default; a first-tool assembly

    # No _finalize_item: db.quality is stamped by the base for Component E to read
    # later. consume_policy inherits "raw" -> every attempt yields a knife (quality
    # scales with the roll), so a new player never loses gathered materials to a
    # bad roll and is never left tool-less.
    
# --- Future garments (one-liners once their materials have a source) ---
# class WoolTunicRecipe(MongooseCraftRecipe):   # needs a "wool" source (shearing)
# class FurCloakRecipe(MongooseCraftRecipe):    # needs "fur"/"hide" (creature harvesting)
# class LeatherBootsRecipe(MongooseCraftRecipe):# needs "leather" (creature harvesting)
