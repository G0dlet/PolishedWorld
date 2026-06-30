# Deer batch — gold-standard worked example

Reference implementation for PolishedWorld content generation. Every entry below
conforms to `AGENTS.md`. Use this as the style example when generating further
creatures. Integrity checklist is filled in at the bottom — reproduce that habit.

Self-contained loop demonstrated:
**deer (creature) → harvest → venison / raw_hide / bone (parts) → bone needle (recipe) → needle (existing tool).**
No new typeclass, no new attribute, no invented Evennia API. `raw_hide` is reused,
not redefined.

---

## 1. Additions to `world/prototypes.py`

```python
# --- Hunting: deer (large game) ----------------------------------------------
# A bigger-bodied counterpart to the rabbit. Higher SIZ -> more harvest yield.
# SOURCE: spawned by CreatureSpawnScript (same as RABBIT). SINK: hunted (H2).
# SIZ 13 is a roe/red-deer scale design value; tunable against Monsters of Legend.

DEER = {
    "prototype_key": "deer",
    "typeclass": "typeclasses.creatures.Creature",
    "key": "deer",
    "aliases": ["doe", "stag"],
    "desc": (
        "A lean wild deer, coat the colour of dry bracken, muscles bunched to "
        "spring. Its ears swivel toward every sound, and it watches you with "
        "dark, wary eyes."
    ),
    "siz": 13,                      # large prey: meat 6, hide 4, bone 3 (see H4 yields)
    "harvest_template": "deer",     # MUST match a key in HARVEST_TEMPLATES below
    "tags": [("deer", "creature")],
    # flee_skill / natural_ap left at Creature defaults (30 / 0).
}


# --- Hunting: deer harvest products ------------------------------------------
# SOURCE for all three: the deer harvest template (below). NOT spawned freely.

VENISON = {
    "prototype_key": "venison",
    "typeclass": "typeclasses.consumables.Food",
    "key": "raw venison",
    "aliases": ["venison", "deer meat"],
    "desc": (
        "A heavy cut of dark red venison, rich and lean. Edible raw at a pinch, "
        "though it would reward cooking far more than it does the impatient."
    ),
    # Larger restore than rabbit_meat (15): a deer is substantial game. Headroom
    # left for a future cooking step (raw -> cooked) to carry the bigger payoff.
    # SINK: eaten (CmdEat).
    "restore_amount": 25,
    "consume_message": "You eat {key}. Rich and gamey, it sits heavy and filling.",
}

BONE = {
    "prototype_key": "bone",
    "typeclass": "typeclasses.objects.Object",
    "key": "bone",
    "aliases": ["bones"],
    "desc": (
        "A clean length of animal bone, pale and hard. Carved and ground, it "
        "takes a fine point — good for needles, awls and small tools."
    ),
    # crafting_material tag-key "bone" is what the bone needle recipe lists.
    # SINK: consumed by BoneNeedleRecipe (and future bone tools).
    "tags": [("bone", "crafting_material")],
}

# NOTE: the deer also yields a hide, but it reuses the existing RAW_HIDE
# prototype (no new prototype needed) — see the "hide" part in the template.
```

---

## 2. Addition to `world/harvest_templates.py`

Add this entry inside the existing `HARVEST_TEMPLATES` dict (after `"rabbit"`):

```python
    "deer": {
        "meat": {
            "skill": "hunting",
            "difficulty": 20,          # Easy: field-dressing familiar game
            "yield_divisor": 2,        # SIZ 13 -> 6 portions
            "max_stage": STALE,        # soft part: gone once ROTTING
            "prototype": "venison",
        },
        "hide": {
            "skill": "craft",
            "difficulty": 0,           # Normal: skinning for usable hide
            "yield_divisor": 3,        # SIZ 13 -> 4 hides
            "max_stage": STALE,        # soft part: gone once ROTTING
            "prototype": "raw_hide",   # reuse the existing rabbit-hide prototype
        },
        "bone": {
            "skill": "craft",
            "difficulty": 0,           # Normal: breaking out clean bone
            "yield_divisor": 4,        # SIZ 13 -> 3 bones
            "max_stage": SKELETON,     # hard part: survives all the way to bones
            "prototype": "bone",
        },
    },
```

---

## 3. Addition to `world/recipes.py`

Add this class (placement near the other tool/material recipes is fine):

```python
class BoneNeedleRecipe(MongooseCraftRecipe):
    """Carve a length of bone into a sewing needle."""

    name = "bone needle"
    consumable_tags = ["bone"]      # one bone per needle
    output_prototypes = ["needle"]  # the existing NEEDLE prototype (a crafting_tool)
    tool_tag = "knife"              # OPTIONAL: a knife carves it (+20); improvised -20
    craft_cooldown = 30             # fiddly carving; between cloth (25) and shirt (40)
```

This gives `NEEDLE` the crafting source its prototype comment said was "a future
task", closing the tailoring tool loop. The needle is a *tool* (not consumed); its
own durability/wear SINK follows the same deferred pattern as the waterskin.

---

## 4. Integrity checklist (filled — reproduce this every batch)

- [x] `output_prototypes` resolve: `"needle"` exists in `prototypes.py`. ✓
- [x] `consumable_tags` have a source: `"bone"` ← new `BONE` prototype (this batch). ✓
- [x] `tool_tag` resolves: `"knife"` ← existing `KNIFE` (`crafting_tool`). ✓
- [x] Harvest `prototype`s exist: `venison` (new), `raw_hide` (existing), `bone` (new). ✓
- [x] Harvest `skill`s are `"hunting"` / `"craft"` only. ✓
- [x] Creature `harvest_template` `"deer"` has a matching template key. ✓
- [x] No `ResourceNode` added — N/A.
- [x] No `|` characters in any string. ✓
- [x] No new typeclass paths, no invented attributes. ✓
- [x] Difficulty values within established bands (Easy +20 / Normal 0). ✓
- [x] SOURCE + SINK commented for deer, venison, bone (raw_hide already documented). ✓

No FLAGs for this batch — every reference resolves and every part has a sink.
```
