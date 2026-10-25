"""
world/material_registry.py
==========================

Canonical registry of crafting **material tag-keys** for PolishedWorld — the
single source of truth for the vocabulary the player-driven economy is built on.

Why this exists
---------------
When content is generated in many separate passes, the classic failure is
*material fragmentation*: one pass yields ``raw_hide``, another invents
``animal_hide`` or ``pelt`` for the same thing; one makes ``iron`` from an
``iron_ingot``, another from ``wrought_iron``. Each is individually valid, but the
economy splits into near-duplicates that never plug into each other. This module
fixes the vocabulary so every batch draws from one controlled set of tag-keys.

Provenance
----------
The base set (fiber, hide, bone, twine, cloth, ...) is grounded in the live repo.
The expansion (wood, ores, metals, leather, charcoal, ...) is *ratified* from the
Arms of Legend crafting decomposition (PolishedWorld_Crafting_Decomposition_AoL_*
and PolishedWorld_System_Backlog), with names standardised and statuses assigned
here. A decomposition *proposes* materials; this registry *ratifies* them. The
registry — not the decomposition doc — is the source of truth.

Ownership
---------
**Claude/Adam curate this file. Content generators (OpenCode) READ it, never edit
it.** Introducing a *new* shared material is a deliberate economic decision. If a
generator needs a shared material not registered here, it FLAGs for a human.

What a generator may reference
------------------------------
A generator may reference a material only when its status is **EXISTS**, OR when
the current batch is explicitly creating it (e.g. the fur-chain batch creates FUR
then references it). Materials with status DATA / BLOCKED / DECISION are NOT in
the repo yet — referencing one in active data is a dangling reference. FLAG it.

tag-key vs alias vs prototype_key (the crux)
--------------------------------------------
- **tag-key**     : the controlled identifier recipes match on. Governed here.
- **prototype_key**: the spawn identity in world/prototypes.py. May differ from
  the tag-key (tag-key ``fiber`` -> prototype ``plant_fiber``).
- **aliases**     : free-form in-game lookup names. NOT governed.
  IMPORTANT: ``pelt`` is now ambiguous (a fur animal's pelt -> ``fur``; a
  thick-hided animal's -> ``raw_hide``). Never use ``pelt`` as a tag-key; choose
  ``fur`` or ``raw_hide`` explicitly.

Naming rules for tag-keys
-------------------------
- lowercase, underscores, singular. one concept -> exactly one tag-key.
- the workable metal stock is the bare metal name: ``iron`` (not ``iron_ingot``),
  ``bronze``, ``steel``, ``tin``, ``copper``. Ores keep ``_ore``.
- per-creature food byproducts (``venison``) are NOT shared materials and are not
  registered — but a creature's *shared* parts must reuse the registered tag-key.
- to add a new shared material: FLAG it for Claude/Adam.

Pure data + pure helpers. No Evennia imports, no side effects — the validator can
import it standalone.
"""

# ---------------------------------------------------------------------------
# Category & status vocabulary
# ---------------------------------------------------------------------------

RAW = "raw"                    # gathered or harvested directly from the world
INTERMEDIATE = "intermediate"  # crafted from other materials (a chain middle)

EXISTS = "exists"      # committed in the repo and live; generators MAY reference
DATA = "data"          # ratified, pure-data buildable now, NOT yet committed
                       # (awaits its generation batch; not referenceable until then)
BLOCKED = "blocked"    # needs an unbuilt system/station/process (see blocked_on)
DECISION = "decision"  # gated on an open design decision (see blocked_on / note)


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------
# Entry shape:
#   "prototype_key" (str) : the prototype spawned for this material.
#   "category"      (str) : RAW | INTERMEDIATE.
#   "status"        (str) : EXISTS | DATA | BLOCKED | DECISION.
#   "blocked_on"    (str) : the system/decision that gates it ("" if none).
#   "source"        (str) : how it is obtained. For EXISTS entries this is what
#                           the code does today; for every other status, intent.
#   "sinks"        (list) : what consumes it (EXISTS: today; else intent);
#                           [] = orphan to resolve.

MATERIALS = {

    # === RAW — plant / gathered ============================================
    "fiber": {
        "prototype_key": "plant_fiber", "category": RAW, "status": EXISTS,
        "blocked_on": "",
        "source": "fiber_plant (ResourceNode)",
        "sinks": ["twine recipe", "cloth recipe"],
    },
    "gourd": {
        "prototype_key": "raw_gourd", "category": RAW, "status": EXISTS,
        "blocked_on": "",
        "source": "gourd_vine (ResourceNode)",
        "sinks": ["waterskin recipe"],
    },
    "wood": {
        "prototype_key": "wood", "category": RAW, "status": EXISTS,
        "blocked_on": "",
        "source": "tree (ResourceNode, required_tool axe). Generic tag — see DECISION #10",
        "sinks": [
            "club recipe", "quarterstaff recipe", "spear recipe", "bow recipe",
            "tent recipe", "handles", "shafts", "planks", "furniture",
            "fuel/charcoal",
        ],
    },
    "oak_bark": {
        "prototype_key": "oak_bark", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "oak tree + knife (tannin)",
        "sinks": ["tanning recipe (-> leather)"],
    },
    "stone": {
        "prototype_key": "stone", "category": RAW, "status": EXISTS,
        "blocked_on": "",
        "source": "stone_outcrop (ResourceNode)",
        "sinks": ["stone knife recipe", "milling stones recipe", "stone tools",
                  "grindstone", "building"],  # no stone sling bullet (B7)
    },
    # stick != wood: a stick is a hand-gathered deadfall piece for hafting, not
    # timber. Keep the two tags apart (wood is DECISION #10's generic tag).
    "stick": {
        "prototype_key": "stick", "category": RAW, "status": EXISTS,
        "blocked_on": "",
        "source": "stick_deadfall (ResourceNode)",
        "sinks": ["stone knife recipe", "stone axe recipe"],
    },
    "flint": {
        "prototype_key": "flint", "category": RAW, "status": EXISTS,
        "blocked_on": "",
        "source": "flint_scatter (ResourceNode)",
        "sinks": ["stone axe recipe", "fire-starting"],
    },
    "clay": {
        "prototype_key": "clay", "category": RAW, "status": EXISTS,
        "blocked_on": "",
        "source": "clay_bank (ResourceNode)",
        "sinks": ["sling bullet recipe", "pottery (blocked: kiln)"],
    },
    "sand": {
        "prototype_key": "sand", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "riverbed/beach ResourceNode",
        "sinks": ["glass (blocked)", "pottery temper", "casting moulds"],
    },
    "straw": {
        "prototype_key": "straw", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "grain/dry-grass ResourceNode",
        "sinks": ["straw hat", "thatch", "bedding"],
    },
    "ochre": {
        "prototype_key": "ochre", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "surface mineral ResourceNode",
        "sinks": ["pigment"],
    },
    "sulfur": {
        "prototype_key": "sulfur", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "volcanic/hot-spring ResourceNode (specialised)",
        "sinks": ["black powder (blocked: alchemy)"],
    },
    "saltpeter": {
        "prototype_key": "saltpeter", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "cave-floor/deposit ResourceNode (specialised)",
        "sinks": ["black powder (blocked: alchemy)"],
    },
    "iron_ore": {
        "prototype_key": "iron_ore", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "bog/surface iron ResourceNode (hand-gathered early)",
        "sinks": ["smelting (-> iron)"],
    },
    "copper_ore": {
        "prototype_key": "copper_ore", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "surface copper ResourceNode",
        "sinks": ["smelting (-> copper)"],
    },
    "tin_ore": {
        "prototype_key": "tin_ore", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "surface tin ResourceNode",
        "sinks": ["smelting (-> tin)"],
    },

    # === RAW — animal parts (from harvest) =================================
    "raw_hide": {
        "prototype_key": "raw_hide", "category": RAW, "status": EXISTS,
        "blocked_on": "",
        "source": "rabbit harvest (HARVEST_TEMPLATES)",
        "sinks": ["leather recipe"],  # the DURABLE chain; distinct from fur (#1)
    },
    "fur": {
        "prototype_key": "fur", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "soft-furred animal harvest (fox...; no creature in the alpha "
                  "yields fur, Q7); pelt kept fur-on",
        "sinks": ["fur cloak", "fur-lined warmth garments"],  # WARMTH chain (#1)
    },
    "bone": {
        "prototype_key": "bone", "category": RAW, "status": EXISTS,
        "blocked_on": "",
        "source": "rabbit harvest (HARVEST_TEMPLATES)",
        "sinks": [
            "bone needle recipe", "scrollcase recipe", "bone armour recipe",
            "spear recipe", "bone tools/weapons",
        ],
    },
    "sinew": {
        "prototype_key": "sinew", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "creature harvest (tendon) — add as a harvest part",
        "sinks": ["bowstring", "strong binding/cordage", "hafting"],
    },
    "tusk": {
        "prototype_key": "boar_tusk", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "boar harvest — no harvest creature yet",
        "sinks": [],  # ORPHAN: needs a carving/ornament recipe
    },
    "feather": {
        "prototype_key": "feather", "category": RAW, "status": DATA,
        "blocked_on": "",
        "source": "bird harvest (pheasant...) — no harvest creature yet",
        "sinks": [],  # ORPHAN today: fletching (arrows) and trim — unlock with ammo
    },
    "wool": {
        "prototype_key": "wool", "category": RAW, "status": BLOCKED,
        "blocked_on": "husbandry/shearing (no shearable animal yet)",
        "source": "shearing a domestic animal",
        "sinks": ["yarn", "wool tunic (dormant)"],
    },

    # === INTERMEDIATE — crafted ============================================
    "twine": {
        "prototype_key": "twine", "category": INTERMEDIATE, "status": EXISTS,
        "blocked_on": "",
        "source": "TwineRecipe (fiber x3)",
        "sinks": [
            "waterskin recipe", "stone axe recipe", "spear recipe", "bow recipe",
            "tent recipe", "lashing/binding",
        ],
    },
    "cloth": {
        "prototype_key": "cloth", "category": INTERMEDIATE, "status": EXISTS,
        "blocked_on": "",
        # NOTE: "canvas"/"sailcloth" map to cloth (a heavy grade) — see DECISION #11
        "source": "ClothRecipe (fiber x3)",
        "sinks": [
            "linen shirt recipe", "breeches recipe", "robe recipe", "hood recipe",
            "reversible clothes recipe", "linen cuirass recipe", "sack recipe",
            "tent recipe", "garments", "sacks/packs", "sails/tents",
        ],
    },
    "leather": {
        "prototype_key": "leather", "category": INTERMEDIATE, "status": EXISTS,
        "blocked_on": "",
        "source": "LeatherRecipe (raw_hide x2, knife optional)",
        "sinks": [
            "leather boots recipe", "shoes recipe", "backpack recipe",
            "saddlebag recipe", "bandolier recipe", "sling recipe",
            "bone armour recipe", "soft armour", "saddles",
        ],
    },
    "pigment": {
        "prototype_key": "pigment", "category": INTERMEDIATE, "status": DATA,
        "blocked_on": "",
        "source": "ochre ground on a grindstone",
        "sinks": ["dyeing", "paint", "decoration"],
    },
    "charcoal": {
        "prototype_key": "charcoal", "category": INTERMEDIATE, "status": BLOCKED,
        "blocked_on": "kiln/charcoal-burning process",
        "source": "wood burned slow in a kiln",
        "sinks": ["smelting fuel", "smithing fuel", "ink (soot)"],
    },
    "iron": {
        "prototype_key": "iron", "category": INTERMEDIATE, "status": BLOCKED,
        "blocked_on": "smelting (furnace + process)",
        "source": "smelt iron_ore + charcoal in a furnace",
        "sinks": ["smithing -> tools/weapons/armour/fittings", "steel"],
    },
    "copper": {
        "prototype_key": "copper", "category": INTERMEDIATE, "status": BLOCKED,
        "blocked_on": "smelting (furnace + process)",
        "source": "smelt copper_ore",
        "sinks": ["bronze", "copper goods"],
    },
    "tin": {
        "prototype_key": "tin", "category": INTERMEDIATE, "status": BLOCKED,
        "blocked_on": "smelting (furnace + process)",
        "source": "smelt tin_ore",
        "sinks": ["bronze"],
    },
    "bronze": {
        "prototype_key": "bronze", "category": INTERMEDIATE, "status": BLOCKED,
        "blocked_on": "smelting (furnace + process)",
        "source": "alloy copper + tin in a furnace",
        "sinks": ["smithing -> early tools/weapons/armour"],
    },
    "steel": {
        "prototype_key": "steel", "category": INTERMEDIATE, "status": BLOCKED,
        "blocked_on": "steelmaking (refining process)",
        "source": "refine iron + carbon",
        "sinks": ["smithing -> superior blades/tools/armour"],
    },
    "planks": {
        "prototype_key": "planks", "category": INTERMEDIATE, "status": BLOCKED,
        "blocked_on": "carpentry (saw + tools)",
        "source": "saw wood into planks",
        "sinks": ["furniture", "vehicles", "shields", "construction"],
    },
    "yarn": {
        "prototype_key": "yarn", "category": INTERMEDIATE, "status": BLOCKED,
        "blocked_on": "spinning (needs wool, which is blocked)",
        "source": "spin wool on a spindle",
        "sinks": ["wool tunic", "knitted goods"],
    },
    "glass": {
        "prototype_key": "glass", "category": INTERMEDIATE, "status": BLOCKED,
        "blocked_on": "glassblowing (furnace + process)",
        "source": "melt sand + soda_ash (staging) in a furnace",
        "sinks": ["bottles", "lenses", "hourglass"],
    },
    "pottery": {
        "prototype_key": "pottery", "category": INTERMEDIATE, "status": BLOCKED,
        "blocked_on": "kiln (station + firing)",
        "source": "fire clay in a kiln",
        "sinks": ["jars/pots", "crucibles", "tableware"],
    },
    "silk": {
        "prototype_key": "silk", "category": INTERMEDIATE, "status": BLOCKED,
        "blocked_on": "sericulture (silkworm lifecycle + reeling)",
        "source": "reel silkworm cocoons (sub-chain deferred to the system)",
        "sinks": ["fine garments"],
    },
}


# ---------------------------------------------------------------------------
# Crafting tools (matched, never consumed). Same discipline; tracked so the
# "everything is crafted, tools included" gaps stay visible.
# ---------------------------------------------------------------------------

TOOLS = {
    "knife": {
        "prototype_key": "stone_knife", "status": EXISTS, "blocked_on": "",
        "source": "StoneKnifeRecipe (stone + stick + fiber -> stone_knife)",
        "used_by": [
            "waterskin (optional)", "harvesting",
            "shaping wood/bone (club, quarterstaff, spear, bow)",
            "scrollcase", "cutting leather (sling, bone armour)",
        ],
    },
    "needle": {
        "prototype_key": "bone_needle", "status": EXISTS, "blocked_on": "",
        "source": "BoneNeedleRecipe (bone -> bone_needle)",
        "used_by": [
            "garment recipes (optional)", "backpack, saddlebag (optional)",
            "tent (optional)",
        ],
    },
    "grindstone": {
        "prototype_key": "grindstone", "status": DATA, "blocked_on": "",
        "source": "shaped stone (hand)",
        "used_by": ["pigment", "sharpening", "milling"],
    },
    "spindle": {
        "prototype_key": "spindle", "status": DATA, "blocked_on": "",
        "source": "carved wood (hand)",
        "used_by": ["yarn (spinning)"],
    },
    "hammer": {
        "prototype_key": "hammer", "status": DATA, "blocked_on": "smithing (metal head)",
        # TIERED: a stone maul/hammer is DATA (stone + wood, hand-made); a metal
        # smithing hammer is BLOCKED on smithing.
        "source": "stone head + wood haft (primitive); metal head needs smithing",
        "used_by": ["smithing", "construction", "driving"],
    },
    "axe": {
        # TIERED: the stone axe (flint head + stick haft) EXISTS and is what this
        # entry points at; a metal-headed axe is BLOCKED on smithing (metal head).
        "prototype_key": "stone_axe", "status": EXISTS, "blocked_on": "",
        "source": "StoneAxeRecipe (flint + stick + twine -> stone_axe)",
        "used_by": ["felling wood (tree node, required)", "carpentry"],
    },
    "saw": {
        "prototype_key": "saw", "status": BLOCKED, "blocked_on": "smithing",
        "source": "toothed metal blade + handle",
        "used_by": ["carpentry (wood -> planks)"],
    },
    "chisel": {
        "prototype_key": "chisel", "status": BLOCKED, "blocked_on": "smithing",
        "source": "metal + handle",
        "used_by": ["carving", "stonework", "joinery"],
    },
    "anvil": {
        "prototype_key": "anvil", "status": BLOCKED, "blocked_on": "smithing",
        "source": "cast/forged metal block (required station for smithing)",
        "used_by": ["smithing"],
    },
    "furnace": {
        "prototype_key": "furnace", "status": BLOCKED,
        "blocked_on": "station typeclass + heat/process",
        "source": "built station (smelting/glass)",
        "used_by": ["smelting", "glassblowing"],  # DECISION #8: shared or separate
    },
    "kiln": {
        "prototype_key": "kiln", "status": BLOCKED,
        "blocked_on": "station typeclass + firing process",
        "source": "built station (charcoal/pottery)",
        "used_by": ["charcoal", "pottery"],  # DECISION #7: shared or separate
    },
    "forge": {
        "prototype_key": "forge", "status": BLOCKED,
        "blocked_on": "station typeclass + heat",
        "source": "built station (smithing)",
        "used_by": ["smithing"],  # DECISION #9: forge/anvil as stations or tools
    },
}


# ---------------------------------------------------------------------------
# Forbidden variants -> canonical tag-key (anti-fragmentation map)
# ---------------------------------------------------------------------------
# A KEY here is a wrong tag-key; use the VALUE. (Same words are fine as prototype
# ALIASES.) "pelt" is intentionally absent — it is ambiguous (fur vs raw_hide);
# generators must pick one explicitly.

FORBIDDEN_VARIANTS = {
    # existing
    "fibre": "fiber", "fibres": "fiber", "plant_fibre": "fiber", "plant_fiber": "fiber",
    "hide": "raw_hide", "skin": "raw_hide", "animal_hide": "raw_hide", "rawhide": "raw_hide",
    "bones": "bone", "animal_bone": "bone",
    "tusks": "tusk", "ivory": "tusk",
    "feathers": "feather", "plume": "feather", "plumage": "feather",
    "tanned_hide": "leather", "leathers": "leather",
    "furs": "fur",
    "cord": "twine", "cordage": "twine",
    "fabric": "cloth", "textile": "cloth", "cloths": "cloth",
    "wools": "wool", "straws": "straw",
    # ratified from the AoL decomposition
    "timber": "wood", "lumber": "wood", "log": "wood", "logs": "wood",
    "firewood": "wood", "oak_wood": "wood", "ash_wood": "wood", "yew_wood": "wood",
    "plank": "planks", "board": "planks", "boards": "planks",
    "wooden_plank": "planks", "wooden_beam": "planks",
    "iron_ingot": "iron", "iron_bar": "iron", "pig_iron": "iron", "wrought_iron": "iron",
    "bloom": "iron",
    "steel_ingot": "steel", "crucible_steel": "steel", "tool_steel": "steel",
    "copper_ingot": "copper", "tin_ingot": "tin",
    "bronze_ingot": "bronze", "tin_bronze": "bronze",
    "tendon": "sinew",
    "rock": "stone", "stones": "stone", "boulder": "stone",
    "sticks": "stick",
    "raw_clay": "clay", "char": "charcoal",
    "canvas": "cloth", "sailcloth": "cloth",
    "bark": "oak_bark",
    "glasses": "glass",
}


# ---------------------------------------------------------------------------
# Staging: proposed-but-NOT-ratified materials
# ---------------------------------------------------------------------------
# Surfaced by the decomposition but deferred — each needs its own mini-decomposition
# (clear source + sink + chain) before entering MATERIALS. Do NOT reference these.

PROPOSED_UNRATIFIED = [
    "paper", "ink", "soda_ash", "plant_ash", "soot", "pulp",   # writing/glass sub-chain
    "resin", "gum", "tallow", "beeswax",                       # binders/waterproofing/light
    "limestone", "tinder", "mulberry", "silk_thread",          # flux / fire / sericulture
    # plus the broad alchemy reagent set (acids, salts) -> their own pass.
]


# ---------------------------------------------------------------------------
# Open design decisions (Claude/Adam to resolve; several gate the metal phase)
# ---------------------------------------------------------------------------
OPEN_DECISIONS = """
1.  [RESOLVED] fur vs raw_hide — kept DISTINCT. fur = warmth chain (pelt kept
    fur-on -> fur garments). raw_hide = durable chain (tan -> leather -> goods).
    Soft-furred animals yield fur; thick-hided yield raw_hide; large may yield both.
    Q7 (AC4.0, Decomp Rev 3 B3): the alpha rabbit yields raw_hide -- the code
    wins; the soft-furred rule waits for a creature that yields fur.
2.  [RESOLVED] Tanning (raw_hide -> leather) — soft hand-craft, no station:
    LeatherRecipe (raw_hide x2, knife optional), commit 896ce33; ratified as
    shipped in roadmap Rev 27 (D2). Bark and water as inputs are deferred to
    BACKLOG "Tanning upgrade".
3.  wool source: needs a shearable animal + husbandry/taming. Likely post-MVP.
4.  straw source: one grain/dry-grass ResourceNode unblocks straw_hat. Cheap.
5.  [RESOLVED] knife source — StoneKnifeRecipe (stone + stick + fiber ->
    stone_knife, no tool required), commit 643815d. The bootstrap root.
6.  water as a crafting input: register a "water" material (from the spring node)
    or have water-using recipes require a nearby water source / waterskin charges?
7.  [NEW] kiln: one shared station for charcoal AND pottery, or separate stations?
8.  [NEW] furnace: one shared station for smelting AND glassblowing, or separate?
9.  [NEW] smithing: are forge + anvil STATIONS (room-bound, like Evennia tools) or
    portable required tools? Affects how blacksmithing recipes gate their tools.
10. [PROVISIONAL] wood: a single generic "wood" tag for the alpha, with species
    as flavour/quality. The revisit (do bows need a distinct springy wood
    mechanically?) moves to Stage 5 — Alpha Content Decomposition AD2.
11. [PROVISIONAL] canvas: folded into "cloth" as a heavy grade (decided). Split
    into its own tag only if sail/tent durability needs to differ mechanically.
"""


# ---------------------------------------------------------------------------
# Lookup helpers (return None / [] rather than raising)
# ---------------------------------------------------------------------------

def material(tag_key):
    """Return a material entry by tag-key, or None."""
    return MATERIALS.get(tag_key)


def tool(tag_key):
    """Return a tool entry by tag-key, or None."""
    return TOOLS.get(tag_key)


def is_registered_material(tag_key):
    """True if tag_key is a canonical crafting-material tag-key."""
    return tag_key in MATERIALS


def is_registered_tool(tag_key):
    """True if tag_key is a canonical crafting-tool tag-key."""
    return tag_key in TOOLS


def canonical_for(name):
    """Map a known forbidden variant to its canonical tag-key, else None."""
    return FORBIDDEN_VARIANTS.get(name)


def prototype_for(tag_key):
    """Return the prototype_key a material/tool tag-key spawns, or None."""
    entry = MATERIALS.get(tag_key) or TOOLS.get(tag_key)
    return entry.get("prototype_key") if entry else None


def all_material_tag_keys():
    """Set of every canonical material tag-key."""
    return set(MATERIALS)


def by_status(status):
    """List material tag-keys with the given status (EXISTS/DATA/BLOCKED/DECISION)."""
    return [k for k, d in MATERIALS.items() if d["status"] == status]


def referenceable_materials():
    """Materials a generator may reference today (status EXISTS only)."""
    return by_status(EXISTS)


def orphan_materials():
    """EXISTS materials with no sink yet (consumable dead-ends to resolve)."""
    return [k for k, d in MATERIALS.items() if d["status"] == EXISTS and not d["sinks"]]


def render_ledger():
    """
    Render the material source/sink ledger as plain text, grouped by status.

    Pure string builder -- no I/O, no Evennia import -- so the module stays
    standalone-importable and this stays unit-testable. The CLI (__main__)
    prints it; the ledger doc pastes that output as a clearly-generated
    snapshot, so the snapshot can never drift from the registry (it IS the
    registry, rendered).
    """
    lines = []
    order = [
        (EXISTS, "committed & live -- generators may reference"),
        (DATA, "ratified, buildable now, not yet committed"),
        (BLOCKED, "needs an unbuilt system/station (see blocked_on)"),
        (DECISION, "gated on an open design decision"),
    ]
    for status, gloss in order:
        keys = sorted(by_status(status))
        lines.append(f"{status.upper()} ({len(keys)}) -- {gloss}")
        for k in keys:
            blocked = MATERIALS[k].get("blocked_on") or ""
            suffix = f"   [blocked_on: {blocked}]" if blocked else ""
            lines.append(f"  {k}{suffix}")
        lines.append("")
    orphans = sorted(orphan_materials())
    lines.append(f"ORPHANS ({len(orphans)}) -- EXISTS but no sink (economic dead-ends):")
    lines.append("  " + (", ".join(orphans) if orphans else "(none)"))
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m world.material_registry",
        description="Inspect the crafting-material registry.",
    )
    parser.add_argument(
        "--ledger",
        action="store_true",
        help="print the source/sink ledger snapshot (status groups + orphans)",
    )
    args = parser.parse_args()
    if args.ledger:
        print(render_ledger())
    else:
        parser.print_help()
