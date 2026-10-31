"""
world/recipes.py

Concrete crafting recipes, discovered by Evennia's crafting contrib via
CRAFT_RECIPE_MODULES. Recipes subclass MongooseCraftRecipe (world/crafting_base.py)
to inherit Legend skill resolution, quality and tool modifiers. A recipe's
craft_duration is how long the `craft` command waits before the craft resolves.

NOTE: MongooseCraftRecipe is imported, not defined here. callables_from_module()
only registers classes whose __module__ is this module, so the imported base is
not picked up as a phantom recipe.

Knowledge partition (Stage 3, Component A -- MongooseCraftRecipe.requires_knowledge):
  common / ungated (inherit requires_knowledge = False) -- survival, tool and
    weapon recipes nobody has to LEARN: twine, waterskin, stone knife, bone needle,
    stone axe, club, sling bullet, sling, quarterstaff, spear, bow, milling stones.
    Not having to learn a recipe is not the same as being able to make it: the
    skill ladder below still floors some of them.
  learnable / knowledge-gated (requires_knowledge = True) -- refined goods that a
    character must LEARN before crafting: cloth, leather, linen shirt, leather boots,
    breeches, robe, hood, reversible clothes, linen cuirass, sack, backpack,
    scrollcase, saddlebag, shoes, bandolier, bone armour, tent.
  Rationale: survival/tools stay ungated so no one can be locked out of staying
  alive or making a first tool; refinement/goods are where the learn-buy-sell-teach
  economy (Stage 3 B/C/D) has something to trade. The flag is declaration only --
  the enforcing gate lives in Component B.

Skill ladder (E.1, AC5.1 -- Skill Progression decomp section 7; Alpha Content
decomp Q4): every recipe declares its own min_skill on the rungs 0 / 20 / 40 /
60, ceiling 60 (journeyman). The rung follows craft_duration (20 s -> 0; 25 and
30 s -> 20; 40 s -> 40; 45 s -> 60) with three exceptions: the bootstrap tools
(stone knife, bone needle, stone axe) and the waterskin sit at 0 so no character
is locked out of survival, and leather sits at 20 because the sling and the
bandolier consume it. No product sits below a recipe that makes one of its
inputs. min_skill is read four ways: the craft floor (crafting_base, .value),
the transmission gate (world/knowledge.py, .current), disassemble's modifier
(commands/crafting_commands.py) and the recipe displays.
tests/test_min_skill_ladder.py pins the ladder.
"""

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
    each garment recipe (every ClothingWithBuffs output) so all garments share
    one quality->condition mapping instead of duplicating branches.

    Writing obj.db.condition overrides the DurableObject autocreate default
    (100); the write lands on the very Attribute apply_wear / is_broken /
    condition_line read back, so a shoddy garment is born already half-worn.
    """
    band = quality_band(obj.db.quality)
    obj.db.condition = GARMENT_CONDITION_BY_BAND[band]
    alias = band_alias(band, obj.key)
    if alias:
        obj.aliases.add(alias)


def _apply_tool_quality(obj):
    """Shared tool _finalize_item body: superior alias only (no condition table).

    A plain module-level function, NOT a CraftingRecipe subclass, so Evennia's
    _load_recipes() never registers it as a phantom recipe (same reason as
    _apply_garment_quality).

    Unlike garments, a tool's start condition is PROTOTYPE-driven (STONE_KNIFE 40,
    BONE_NEEDLE 30, STONE_AXE 40 -- the D.5 wear tuning), so this deliberately does NOT touch
    obj.db.condition. Quality is already stamped on the tool by do_craft; all this
    adds is the individuating "superior <key>" alias, so a player can target the
    good tool in a pile and it reads as superior at a glance. The +tool_bonus a
    superior tool grants when USED is read live from db.quality by
    MongooseCraftRecipe._tool_modifier -- never from this alias.
    """
    band = quality_band(obj.db.quality)
    alias = band_alias(band, obj.key)
    if alias:
        obj.aliases.add(alias)


class TwineRecipe(MongooseCraftRecipe):
    """Twist three plant fibres into a length of twine."""

    name = "twine"
    discipline = "weaving"
    consumable_tags = ["fiber", "fiber", "fiber"]   # three fibres, matched by tag-key
    output_prototypes = ["twine"]
    tool_tag = None                                 # handcraft; no tool benefit
    craft_duration = 20                             # quick craft (overrides base 30)
    min_skill = 0                                # E.1 rung 0 (AC5.1)


class WaterskinRecipe(MongooseCraftRecipe):
    """Fit a hollow gourd with a twine strap and stopper to make a waterskin."""

    name = "waterskin"
    discipline = "leatherwork"
    consumable_tags = ["gourd", "twine"]   # consumed
    output_prototypes = ["waterskin"]
    tool_tag = "knife"                     # OPTIONAL: knife shapes the gourd (baseline 0); improvised -20
    craft_duration = 45                    # more involved than twine
    min_skill = 0                          # E.1 rung 0: survival bootstrap, never floored (AC5.1)

    def _finalize_item(self, obj, outcome):
        # Quality -> capacity (draughts) + durability (lifespan in refills),
        # classified through the shared band helper so this recipe never
        # hard-codes a raw threshold. This replaces the old >=125 branch.
        #
        # ⚠️ SUPERSEDED (Stage 4.5, D.2). The removal was originally justified as
        # "max craft quality is 110 (skill cap 100 -> crit_score 10), so no craft
        # ever reached 125". The premise is gone: there is no skill cap any more,
        # crit_score is `.value // 10`, and a crafter at skill 250 stamps 125.
        # The removal still stands, for a better reason than the old one -- the
        # band helper is the single place quality is classified, and a recipe
        # reopening a raw threshold would reintroduce exactly the split
        # world/crafting_quality.py exists to prevent. Recorded rather than
        # quietly rewritten: this is the fifth claim in this epic to be undone by
        # a mechanism changing underneath it, and the first caught before it went
        # false rather than after.
        band = quality_band(obj.db.quality)
        obj.db.max_charges, obj.db.durability = _WATERSKIN_STATS_BY_BAND[band]
        obj.db.charges = 0                              # crafted empty regardless
        alias = band_alias(band, obj.key)              # "superior waterskin" only
        if alias:
            obj.aliases.add(alias)                              # crafted empty regardless


class ClothRecipe(MongooseCraftRecipe):
    """Weave plant fibres into a bolt of plain cloth."""

    name = "cloth"
    discipline = "weaving"
    requires_knowledge = True                       # refined good -> learnable (Stage 3, Component A)
    consumable_tags = ["fiber", "fiber", "fiber"]   # three fibres per bolt
    output_prototypes = ["cloth"]
    tool_tag = None                                 # handwoven; no tool benefit
    craft_duration = 25                             # between twine (20) and waterskin (45)
    min_skill = 20                               # E.1 rung 20 (AC5.1)


class LeatherRecipe(MongooseCraftRecipe):
    """Tan two raw hides into a piece of workable leather."""

    name = "leather"                              # recipe-registry name (≠ prototype_key, separate namespace)
    discipline = "leatherwork"
    requires_knowledge = True                     # refined good -> learnable (Stage 3, Component A)
    consumable_tags = ["raw_hide", "raw_hide"]    # two hides per piece, matched by tag-key
    output_prototypes = ["leather"]               # the new H5.1 prototype
    tool_tag = "knife"                            # OPTIONAL: knife scrapes/cuts the hide (baseline 0); absent = -20
    craft_duration = 45                           # involved work (soak/scrape/tan); overrides base 30
    min_skill = 20                               # E.1 rung 20 (AC5.1)


class LinenShirtRecipe(MongooseCraftRecipe):
    """Cut and stitch cloth into a linen shirt (undershirt layer)."""

    name = "linen shirt"
    discipline = "weaving"
    requires_knowledge = True              # refined good -> learnable (Stage 3, Component A)
    consumable_tags = ["cloth", "cloth"]   # two bolts per shirt
    output_prototypes = ["linen_shirt"]    # the existing B.3 prototype
    tool_tag = "needle"                    # OPTIONAL: needle eases stitching (baseline 0); improvised -20
    craft_duration = 40
    min_skill = 40                               # E.1 rung 40 (AC5.1)

    def _finalize_item(self, obj, outcome):
        # E.3: quality -> garment start-condition (+ superior alias) via the
        # shared helper. Reads obj.db.quality stamped by the base; superior
        # starts pristine (100), shoddy already worn-in (50).
        _apply_garment_quality(obj)


class LeatherBootsRecipe(MongooseCraftRecipe):
    """Stitch two pieces of leather into a pair of sturdy boots."""

    name = "leather boots"                       # space, mirroring "linen shirt"
    discipline = "leatherwork"
    requires_knowledge = True                    # refined good -> learnable (Stage 3, Component A)
    consumable_tags = ["leather", "leather"]     # two pieces per pair
    output_prototypes = ["leather_boots"]        # existing Component B prototype
    tool_tag = "needle"                          # OPTIONAL: needle eases stitching (baseline 0); improvised -20
    craft_duration = 40                          # mirrors linen shirt
    min_skill = 40                               # E.1 rung 40: cut & stitch (AC5.1). Was the
                                                 # Component F.2 placeholder 30.

    def _finalize_item(self, obj, outcome):
        # E.3: same shared quality -> start-condition + superior alias as the
        # linen shirt. See _apply_garment_quality.
        _apply_garment_quality(obj)


class BreechesRecipe(MongooseCraftRecipe):
    """Cut and stitch cloth into a pair of breeches."""

    name = "breeches"
    discipline = "weaving"
    requires_knowledge = True
    consumable_tags = ["cloth", "cloth"]
    output_prototypes = ["breeches"]
    tool_tag = "needle"
    craft_duration = 40
    min_skill = 40                               # E.1 rung 40 (AC5.1)

    def _finalize_item(self, obj, outcome):
        # Garment quality -> start condition (+ superior alias), the same
        # mapping as the linen shirt. See _apply_garment_quality.
        _apply_garment_quality(obj)


class RobeRecipe(MongooseCraftRecipe):
    """Cut and stitch cloth into a full-length robe."""

    name = "robe"
    discipline = "weaving"
    requires_knowledge = True
    consumable_tags = ["cloth", "cloth", "cloth"]
    output_prototypes = ["robe"]
    tool_tag = "needle"
    craft_duration = 45
    min_skill = 60                               # E.1 rung 60 (AC5.1)

    def _finalize_item(self, obj, outcome):
        # Garment quality -> start condition (+ superior alias), the same
        # mapping as the linen shirt. See _apply_garment_quality.
        _apply_garment_quality(obj)


class HoodRecipe(MongooseCraftRecipe):
    """Shape and stitch cloth into a hood."""

    name = "hood"
    discipline = "weaving"
    requires_knowledge = True
    consumable_tags = ["cloth"]
    output_prototypes = ["hood"]
    tool_tag = "needle"
    craft_duration = 30
    min_skill = 20                               # E.1 rung 20 (AC5.1)

    def _finalize_item(self, obj, outcome):
        # Garment quality -> start condition (+ superior alias), the same
        # mapping as the linen shirt. See _apply_garment_quality.
        _apply_garment_quality(obj)


class ReversibleClothesRecipe(MongooseCraftRecipe):
    """Sew a finished garment with two contrasting cloth faces."""

    name = "reversible clothes"
    discipline = "weaving"
    requires_knowledge = True
    consumable_tags = ["cloth", "cloth", "cloth", "cloth"]
    output_prototypes = ["reversible_clothes"]
    tool_tag = "needle"
    craft_duration = 45
    min_skill = 60                               # E.1 rung 60 (AC5.1)

    def _finalize_item(self, obj, outcome):
        # Garment quality -> start condition (+ superior alias), the same
        # mapping as the linen shirt. See _apply_garment_quality.
        _apply_garment_quality(obj)


class LinenCuirassRecipe(MongooseCraftRecipe):
    """Layer and stitch linen into a fitted cuirass."""

    name = "linen cuirass"
    discipline = "weaving"
    requires_knowledge = True
    consumable_tags = ["cloth", "cloth", "cloth", "cloth"]
    output_prototypes = ["linen_cuirass"]
    tool_tag = "needle"
    craft_duration = 45
    min_skill = 60                               # E.1 rung 60 (AC5.1)

    def _finalize_item(self, obj, outcome):
        # Garment quality -> start condition (+ superior alias), the same
        # mapping as the linen shirt. See _apply_garment_quality.
        _apply_garment_quality(obj)


class SackRecipe(MongooseCraftRecipe):
    """Cut and stitch heavy cloth into a large sack."""

    name = "sack"
    discipline = "weaving"
    requires_knowledge = True
    consumable_tags = ["cloth", "cloth"]
    output_prototypes = ["sack"]
    tool_tag = "needle"
    craft_duration = 40
    min_skill = 40                               # E.1 rung 40 (AC5.1)


class BackpackRecipe(MongooseCraftRecipe):
    """Cut and stitch leather into a strapped backpack."""

    name = "backpack"
    discipline = "leatherwork"
    requires_knowledge = True
    consumable_tags = ["leather", "leather"]
    output_prototypes = ["backpack"]
    tool_tag = "needle"
    craft_duration = 40
    min_skill = 40                               # E.1 rung 40 (AC5.1)


class ScrollcaseRecipe(MongooseCraftRecipe):
    """Carve and cap a bone tube into a scrollcase."""

    name = "scrollcase"
    discipline = "leatherwork"
    requires_knowledge = True
    consumable_tags = ["bone"]
    output_prototypes = ["scrollcase"]
    tool_tag = "knife"
    craft_duration = 30
    min_skill = 20                               # E.1 rung 20 (AC5.1)


class SaddlebagRecipe(MongooseCraftRecipe):
    """Cut, shape and stitch leather into a saddlebag."""

    name = "saddlebag"
    discipline = "leatherwork"
    requires_knowledge = True
    consumable_tags = ["leather", "leather", "leather"]
    output_prototypes = ["saddlebag"]
    tool_tag = "needle"
    craft_duration = 45
    min_skill = 60                               # E.1 rung 60 (AC5.1)


class ShoesRecipe(MongooseCraftRecipe):
    """Cut and stitch leather into a pair of shoes."""

    name = "shoes"
    discipline = "leatherwork"
    requires_knowledge = True
    consumable_tags = ["leather"]
    output_prototypes = ["shoes"]
    tool_tag = "needle"
    craft_duration = 40
    min_skill = 40                               # E.1 rung 40 (AC5.1)

    def _finalize_item(self, obj, outcome):
        # Garment quality -> start condition (+ superior alias), the same
        # mapping as the linen shirt. See _apply_garment_quality.
        _apply_garment_quality(obj)


class BandolierRecipe(MongooseCraftRecipe):
    """Cut leather and stitch its loops into a bandolier."""

    name = "bandolier"
    discipline = "leatherwork"
    requires_knowledge = True
    consumable_tags = ["leather"]
    output_prototypes = ["bandolier"]
    tool_tag = "needle"
    craft_duration = 30
    min_skill = 20                               # E.1 rung 20 (AC5.1)

    def _finalize_item(self, obj, outcome):
        # Garment quality -> start condition (+ superior alias), the same
        # mapping as the linen shirt. See _apply_garment_quality.
        _apply_garment_quality(obj)


class BoneArmourRecipe(MongooseCraftRecipe):
    """Lash shaped bone plates to a leather backing as chest armour."""

    name = "bone armour"
    discipline = "bonework"
    requires_knowledge = True
    consumable_tags = ["bone", "bone", "bone", "leather"]
    output_prototypes = ["bone_armour"]
    tool_tag = "knife"
    craft_duration = 45
    min_skill = 60                               # E.1 rung 60 (AC5.1)

    def _finalize_item(self, obj, outcome):
        # Garment quality -> start condition (+ superior alias), the same
        # mapping as the linen shirt. See _apply_garment_quality.
        _apply_garment_quality(obj)


class SlingRecipe(MongooseCraftRecipe):
    """Cut and shape a leather pouch and cords into a sling."""

    name = "sling"
    discipline = "leatherwork"
    consumable_tags = ["leather"]
    output_prototypes = ["sling"]
    tool_tag = "knife"
    craft_duration = 30
    min_skill = 20                               # E.1 rung 20 (AC5.1)


class QuarterstaffRecipe(MongooseCraftRecipe):
    """Shape two lengths of wood into a balanced quarterstaff."""

    name = "quarterstaff"
    discipline = "woodwork"
    consumable_tags = ["wood", "wood"]
    output_prototypes = ["quarterstaff"]
    tool_tag = "knife"
    craft_duration = 30
    min_skill = 20                               # E.1 rung 20 (AC5.1)


class SpearRecipe(MongooseCraftRecipe):
    """Haft a bone point on wooden shafts and lash it with twine: a spear."""

    name = "spear"
    discipline = "woodwork"
    consumable_tags = ["wood", "wood", "bone", "twine"]
    output_prototypes = ["spear"]
    tool_tag = "knife"
    craft_duration = 30
    min_skill = 20                               # E.1 rung 20 (AC5.1)


class BowRecipe(MongooseCraftRecipe):
    """Shape a wooden stave and string it with twine: a short bow."""

    name = "bow"
    discipline = "woodwork"
    consumable_tags = ["wood", "twine"]   # AD4: a fibre string, never sinew
    output_prototypes = ["bow"]
    tool_tag = "knife"
    craft_duration = 45
    min_skill = 60                               # E.1 rung 60 (AC5.1)


class MillingStonesRecipe(MongooseCraftRecipe):
    """Shape two gathered stones into a matched pair of milling stones."""

    name = "milling stones"
    discipline = "stonework"
    consumable_tags = ["stone", "stone"]
    output_prototypes = ["milling_stones"]
    # tool_tag=None -> _tool_modifier() returns 0 (NO improvised penalty): a
    # pair you shape with your hands must not be penalised for lacking a tool.
    tool_tag = None
    craft_duration = 30
    min_skill = 20                               # E.1 rung 20 (AC5.1)


class TentRecipe(MongooseCraftRecipe):
    """Stitch cloth panels, raise wooden poles and lash a tent with twine."""

    name = "tent"
    discipline = "woodwork"
    requires_knowledge = True
    consumable_tags = [
        "cloth", "cloth", "cloth", "cloth",
        "wood", "wood", "twine", "twine",
    ]
    output_prototypes = ["tent"]
    tool_tag = "needle"
    craft_duration = 45
    min_skill = 60                               # E.1 rung 60 (AC5.1)


class StoneKnifeRecipe(MongooseCraftRecipe):
    """Knap a stone flake, haft it to a stick, lash it with fibre: a crude knife.

    The bootstrap tool of the zero-to-tool loop -- ungated and tool-free so a
    brand-new character can make their first knife from gathered primitives alone.
    """

    name = "stone knife"
    discipline = "stonework"
    # Stone flake + wooden haft + fibre lashing, matched by crafting_material
    # tag-key. Raw `fiber` (not crafted twine) keeps this a SINGLE craft with no
    # nested sub-craft, so the very first tool stays low-friction (decision b).
    consumable_tags = ["stone", "stick", "fiber"]
    output_prototypes = ["stone_knife"]
    # tool_tag=None -> _tool_modifier() returns 0 (NO improvised penalty): a
    # bootstrap you make with your hands must not be penalised for lacking the
    # very tool it exists to give you.
    tool_tag = None
    craft_duration = 30                 # base default; a first-tool assembly
    min_skill = 0                       # E.1 rung 0: survival bootstrap, never floored (AC5.1)

    # consume_policy inherits "raw" -> every attempt yields a knife (quality scales
    # with the roll), so a new player never loses gathered materials to a bad roll
    # and is never left tool-less.

    def _finalize_item(self, obj, outcome):
        # Component G: a superior stone knife (critical craft, quality > 100) gains
        # a "superior stone knife" alias so it's targetable and reads as superior.
        # db.quality is already stamped by the base; the +tool_bonus it grants when
        # USED as a tool is read live from that quality by _tool_modifier, not from
        # this alias. No db.condition write -- start condition stays prototype-driven
        # (40, D.5).
        _apply_tool_quality(obj)


class BoneNeedleRecipe(MongooseCraftRecipe):
    """Grind a harvested bone to a point and eye it: a crude sewing needle.

    The tailoring bootstrap, deliberately hunting-linked -- its only input is
    `bone`, taken from a corpse (C.4 harvest part). Ungated and tool-free so a
    single hunt can yield a needle with no prior tools.
    """

    name = "bone needle"
    discipline = "bonework"
    consumable_tags = ["bone"]          # one harvested bone, matched by tag-key
    output_prototypes = ["bone_needle"]
    # tool_tag=None -> _tool_modifier() returns 0 (no improvised penalty). (A future
    # tool_tag="knife" -- carving needs a blade -- is a deliberate deferral.)
    tool_tag = None
    craft_duration = 30                 # small, fiddly assembly; mirrors stone knife
    min_skill = 0                       # E.1 rung 0: survival bootstrap, never floored (AC5.1)

    # consume_policy inherits "raw" -> a hunt is never wasted on a bad roll.

    def _finalize_item(self, obj, outcome):
        # Component G: a superior bone needle (critical craft, quality > 100) gains a
        # "superior bone needle" alias -- same rationale as the stone knife. db.quality
        # is stamped by the base; the +tool_bonus it grants when USED is read live from
        # it by _tool_modifier. No db.condition write (start condition prototype-driven,
        # 30, D.5).
        _apply_tool_quality(obj)


class StoneAxeRecipe(MongooseCraftRecipe):
    """Knap a flint head, seat it in a stick haft, bind it with twine: a stone axe.

    The felling bootstrap (AC2.2). The tree node will not yield wood without an
    axe, so the axe itself must be makeable from what grows and lies about --
    ungated and tool-free, like the stone knife.
    """

    name = "stone axe"
    discipline = "stonework"
    # Flint head + wooden haft + twine lashing, matched by crafting_material
    # tag-key. Twine, not raw fibre: an axe head takes a heavier binding than a
    # knife flake, and twine is one quick craft away.
    consumable_tags = ["flint", "stick", "twine"]
    output_prototypes = ["stone_axe"]
    # tool_tag=None -> _tool_modifier() returns 0 (no improvised penalty): a
    # bootstrap tool is never penalised for lacking itself.
    tool_tag = None
    craft_duration = 30                 # mirrors the stone knife
    min_skill = 0                       # E.1 rung 0: survival bootstrap, never floored (AC5.1)

    # consume_policy inherits "raw" -> every attempt yields an axe.

    def _finalize_item(self, obj, outcome):
        # Superior alias only, as the stone knife; start condition stays
        # prototype-driven (40).
        _apply_tool_quality(obj)


class ClubRecipe(MongooseCraftRecipe):
    """Shape a length of wood into a club: wood's first consumer (AC2.2)."""

    name = "club"
    discipline = "woodwork"
    consumable_tags = ["wood"]          # one length, matched by tag-key
    output_prototypes = ["club"]
    tool_tag = "knife"                  # OPTIONAL: a knife shapes the head (baseline 0); improvised -20
    craft_duration = 30
    min_skill = 20                               # E.1 rung 20 (AC5.1)

class SlingBulletRecipe(MongooseCraftRecipe):
    """Roll a lump of clay into a sling bullet and dry it: clay's first consumer (AC2.3).

    One lump, one bullet. AoL counts bullets in tens, but each bullet is its own
    object here, and nothing consumes bullets in the alpha (the sling exists, but
    there is no combat), so the batch size waits for the mechanic that uses them.
    AC4.0 struck the stone variant (B7); the fired variant is BLOCKED: kiln.
    """

    name = "sling bullet"
    discipline = "stonework"
    consumable_tags = ["clay"]          # one lump, matched by tag-key
    output_prototypes = ["sling_bullet"]
    # tool_tag=None -> _tool_modifier() returns 0 (no improvised penalty): rolled
    # by hand. The registry's knife shapes wood and bone, not clay.
    tool_tag = None
    craft_duration = 20                 # a quick hand-craft; mirrors twine
    min_skill = 0                       # E.1 rung 0 (AC5.1)

    # consume_policy inherits "raw" -> every attempt yields a bullet.

# --- Future garments (one-liners once their materials have a source) ---
# class WoolTunicRecipe(MongooseCraftRecipe):   # needs a "wool" source (shearing)
# class FurCloakRecipe(MongooseCraftRecipe):    # needs "fur" (no fur source yet)
