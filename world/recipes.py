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
from world.crafting_base import MongooseCraftRecipe
from world.crafting_quality import (
    quality_band,
    band_alias,
    SUPERIOR,
    SERVICEABLE,
    POOR,
    SHODDY,
)


# --- Quality-band capability tables (Component E) --------------------------
# Recipes read a BAND (world/crafting_quality.quality_band), never a raw quality
# number. Each table says what a band MEANS for one item type; the band
# classification itself lives in crafting_quality (single source of truth).

_WATERSKIN_STATS_BY_BAND = {   # band -> (max_charges, durability-in-refills)
    SUPERIOR: (6, 12),
    SERVICEABLE: (5, 10),
    POOR: (4, 6),
    SHODDY: (3, 3),
}


GARMENT_CONDITION_BY_BAND = {  # band -> start condition on the 0-100 wear axis
    SUPERIOR: 100,
    SERVICEABLE: 90,
    POOR: 70,
    SHODDY: 50,
}


def _apply_garment_quality(obj):
    """Shared garment _finalize_item body: quality -> start condition + alias.

    A plain module-level function, NOT a CraftingRecipe subclass, so Evennia's
    _load_recipes() (which registers only issubclass(CraftingRecipeBase) classes
    *defined* in this module) never picks it up as a phantom recipe. Called from
    each garment recipe so linen shirt / leather boots share one
    quality->condition mapping instead of duplicating branches.

    Writing obj.db.condition overrides the DurableObject autocreate default
    (100); the write lands on the very Attribute apply_wear / is_broken /
    condition_line read back, so a shoddy garment is born already half-worn.
    """
    band = quality_band(obj.db.quality)
    obj.db.condition = GARMENT_CONDITION_BY_BAND[band]
    alias = band_alias(band, obj.key)
    if alias:
        obj.aliases.add(alias)


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
    tool_tag = "knife"                     # OPTIONAL: knife shapes the gourd (baseline 0); improvised -20
    craft_cooldown = 45                    # more involved than twine

    def _finalize_item(self, obj, outcome):
        # Quality -> capacity (draughts) + durability (lifespan in refills),
        # classified through the shared band helper so this recipe never
        # hard-codes a raw threshold. This replaces the old >=125 branch, which
        # was DEAD: max craft quality is 110 (skill cap 100 -> crit_score 10), so
        # no craft ever reached 125 and every critical fell into serviceable.
        band = quality_band(obj.db.quality)
        obj.db.max_charges, obj.db.durability = _WATERSKIN_STATS_BY_BAND[band]
        obj.db.charges = 0                              # crafted empty regardless
        alias = band_alias(band, obj.key)              # "superior waterskin" only
        if alias:
            obj.aliases.add(alias)                              # crafted empty regardless


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
    tool_tag = "knife"                            # OPTIONAL: knife scrapes/cuts the hide (baseline 0); absent = -20
    craft_cooldown = 45                           # involved work (soak/scrape/tan); overrides base 30


class LinenShirtRecipe(MongooseCraftRecipe):
    """Cut and stitch cloth into a linen shirt (undershirt layer)."""

    name = "linen shirt"
    consumable_tags = ["cloth", "cloth"]   # two bolts per shirt
    output_prototypes = ["linen_shirt"]    # the existing B.3 prototype
    tool_tag = "needle"                    # OPTIONAL: needle eases stitching (baseline 0); improvised -20
    craft_cooldown = 40

    def _finalize_item(self, obj, outcome):
        # E.3: quality -> garment start-condition (+ superior alias) via the
        # shared helper. Reads obj.db.quality stamped by the base; superior
        # starts pristine (100), shoddy already worn-in (50).
        _apply_garment_quality(obj)


class LeatherBootsRecipe(MongooseCraftRecipe):
    """Stitch two pieces of leather into a pair of sturdy boots."""

    name = "leather boots"                       # space, mirroring "linen shirt"
    consumable_tags = ["leather", "leather"]     # two pieces per pair
    output_prototypes = ["leather_boots"]        # existing Component B prototype
    tool_tag = "needle"                          # OPTIONAL: needle eases stitching (baseline 0); improvised -20
    craft_cooldown = 40                          # mirrors linen shirt
    min_skill = 30                               # Component F.2: HARD floor. Boots sit above
                                                 # the survival tier (hide->leather->boots), so
                                                 # a developing crafter must show competence to
                                                 # attempt them. Conservative; rebalanced vs
                                                 # Legend later. All other recipes stay ungated (0).

    def _finalize_item(self, obj, outcome):
        # E.3: same shared quality -> start-condition + superior alias as the
        # linen shirt. See _apply_garment_quality.
        _apply_garment_quality(obj)


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


class BoneNeedleRecipe(MongooseCraftRecipe):
    """Grind a harvested bone to a point and eye it: a crude sewing needle.

    The tailoring bootstrap, deliberately hunting-linked -- its only input is
    `bone`, taken from a corpse (C.4 harvest part). Ungated and tool-free so a
    single hunt can yield a needle with no prior tools.
    """

    name = "bone needle"
    consumable_tags = ["bone"]          # one harvested bone, matched by tag-key
    output_prototypes = ["bone_needle"]
    # tool_tag=None -> _tool_modifier() returns 0 (no improvised penalty). No
    # min_skill: the base has no skill floor, so ungated is the default. (A future
    # tool_tag="knife" -- carving needs a blade -- is a deliberate deferral.)
    tool_tag = None
    craft_cooldown = 30                 # small, fiddly assembly; mirrors stone knife

    # No _finalize_item: db.quality is stamped by the base for Component E to read.
    # consume_policy inherits "raw" -> a hunt is never wasted on a bad roll.
    
# --- Future garments (one-liners once their materials have a source) ---
# class WoolTunicRecipe(MongooseCraftRecipe):   # needs a "wool" source (shearing)
# class FurCloakRecipe(MongooseCraftRecipe):    # needs "fur"/"hide" (creature harvesting)
# class LeatherBootsRecipe(MongooseCraftRecipe):# needs "leather" (creature harvesting)
