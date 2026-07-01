# AGENTS.md — PolishedWorld

> **Rev 1 · 2026-07-01** — added §9 (documentation version-header convention).
> **Canonical:** `AGENTS.md` @ G0dlet/PolishedWorld — git wins.

You are a code agent working in **PolishedWorld**, a high-fantasy sandbox-survival
MUD built on the **Evennia** framework (Python 3.11+) using the **Mongoose Legend**
(d100 percentile) ruleset.

Your job in this repo is **content data generation**: producing prototypes,
crafting recipes, harvest tables and material chains that follow the *exact*
existing conventions. You are NOT here to design systems or write game logic.
Read this whole file before writing anything.

---

## 0. SCOPE — read this first

### You MAY edit only these data files:
- `world/prototypes.py` — item / creature / resource-node prototypes (data dicts)
- `world/recipes.py` — one-line `MongooseCraftRecipe` subclasses (data only)
- `world/harvest_templates.py` — the `HARVEST_TEMPLATES` data dict

### You MUST NOT, under any circumstances:
- Create or edit any file under `typeclasses/` (Creature, Corpse, Food, Drink,
  Clothing, ResourceNode, etc. already exist — you only *reference* them).
- Create or edit anything under `commands/`, `server/`, `world/crafting_base.py`,
  `world/skillcheck.py`, `world/gametime_utils.py`, or any Script/hook code.
- Invent Evennia methods, attributes, typeclasses, or settings keys.
- Change game balance with novel numbers (new difficulty bands, regen rates,
  quality thresholds, warmth values) without it being explicitly requested.

### When you hit a wall — STOP and flag, do not improvise
If a requested item needs something that does not yet exist (a new typeclass, a
new attribute on a typeclass, a new crafting skill, a new `clothing_type`, a new
quality rule), **do not invent it**. Stop and write a short note:

```
FLAG: "<item>" needs <X> which does not exist yet (no <typeclass/attr/skill>).
This is a design/code change, not data. Leaving it out — needs Claude/Adam.
```

The human will get the missing piece implemented, then ask you to add the data.

---

## 1. Golden rules (these never bend)

1. **Read before you write.** Always open `world/prototypes.py`,
   `world/recipes.py` and `world/harvest_templates.py` and copy the style of the
   nearest existing entry. Match it exactly — naming, key order, comment style.
2. **Never invent Evennia paths.** Only use a `typeclass` string that already
   appears in an existing prototype (see the table in §3). If you need a new one,
   FLAG it.
3. **Cross-file integrity is mandatory.** Every reference must resolve (see §6).
   A recipe that outputs a prototype that doesn't exist is a broken commit.
   "Resolve" means the target is present in the **actual repo file you can open** —
   verify it by searching that file (e.g. `grep` `world/prototypes.py` for the
   `prototype_key`). A worked example you were handed is a *style* reference only;
   it is NOT proof the thing exists in the repository. If a dependency lives only
   in an example and not in the repo, treat it as missing and FLAG it.
4. **Economy: every item needs a SOURCE and a SINK — tools included.**
   PolishedWorld has a 100% player-driven economy — **no NPC vendors**. The only
   valid source is a gather/harvest or a crafting recipe (never a vendor, never a
   `value`/price field). Every item, *including crafting tools*, must trace back
   to gatherable base materials through a realistic chain (see §1A) and carry a
   one-line comment naming its source and its sink. If you can't name a sink — or
   a realistic chain down to a base material — FLAG it.
5. **Never use the `|` character** in any `desc`, `key`, `alias`, or message
   string. Evennia's parser reads `|` as a colour/markup prefix (`|r`, `|/`,
   `||`, ...). Use a real em-dash (—) or words instead.
6. **English only** in code, keys, comments, descriptions, and commit messages.
7. **Multiplayer mindset.** This is data, but the data feeds a 10+ player server.
   Don't add anything that implies per-object timers or global mutable state —
   that's the typeclass layer's job, not yours.

---

## 1A. Sourcing from the rulebooks & crafting completeness

### Where content comes from
Items, materials and creatures are drawn from **Arms of Legend** (items,
materials, crafting rules, Item Quality) and **Monsters of Legend I & II**
(creatures and what they yield). From those books, take:
- the item / material identities and their realistic real-world makeup;
- the Mongoose Legend **Item Quality** bands (superior / serviceable / poor /
  shoddy) — already encoded by `_finalize_item` (see `WaterskinRecipe`).

Do **NOT** import the books' trade economy: no `value`/price fields, no
"availability by settlement size", no vendor, shop or merchant data. The only
legitimate source of any item is a **gather/harvest** (a `ResourceNode` yield or
a creature part) or a **crafting recipe**. If you're about to write a price, a
`value`, or anything a shopkeeper would use — stop. It does not belong here.

### Material vocabulary is governed by the registry
`world/material_registry.py` is the **single source of truth for crafting
material tag-keys**. Read it before adding any material. Reuse a registered
tag-key (e.g. a hide part is always `raw_hide`, a bone part is always `bone`) —
do not coin a variant. The registry's `FORBIDDEN_VARIANTS` lists the wrong names
and their canonical replacements (`pelt`/`hide`/`skin` → `raw_hide`, etc.); those
words are fine as prototype *aliases* but never as tag-keys. Introducing a **new
shared material** is a curated decision — FLAG it for Claude/Adam; do not invent
the tag-key yourself. (Per-creature food byproducts like `venison` are not shared
materials and are not registered — but their shared parts must reuse registry
tag-keys.) A generator may reference a material only when its registry status is 
EXISTS. Materials marked DATA, BLOCKED or DECISION are not in the 
repo yet — reference one only if the current batch is the one creating it; 
otherwise FLAG it.

### Everything is crafted, from base material up — tools included
Every finished item, **including crafting tools** (knife, needle, awl, …), must be
craftable from gatherable base materials through as realistic a chain as possible.
No item may have "spawned" or "given" as its only source.

- Model the **full real process; never collapse stages.**
  - Good: `raw_hide → leather (tanning) → leather boots (cut & stitch)`
  - Bad: `raw_hide → leather boots` (skips tanning)
  - Good: `iron ore → iron ingot (smelt) → blade blank (forge) → knife (haft)`
  - Bad: `iron ore → knife`
- The base of every chain is a **gatherable raw material** (a `ResourceNode`
  yield or a creature harvest part). Trace every chain back to one.
- Because all recipe tools are *optional* (+20 with / −20 improvised), no chain is
  ever hard-locked: a primitive item is always hand-makeable at a penalty. That
  is how the tool bootstrap is solved — a bone needle or a stone knife can be made
  by hand, and then eases the crafts that follow.

### When a realistic chain outruns what exists — FLAG the step
A faithful chain may need a step the game can't model yet (a smelting furnace, a
forge station, a heat source, a new process or typeclass). Build the chain in data
**as far as existing typeclasses and materials allow, then FLAG the first missing
step and stop** — do NOT shortcut past it, and do NOT invent a station/typeclass
to bridge it.

```
FLAG: realistic "<item>" chain needs a <smelt/forge/...> step with no support yet
(no furnace/forge station or process). Chain stops at <last buildable step>.
Needs Claude/Adam (design + code), not data.
```

This is expected and useful — it surfaces which subsystems must be built before a
branch can be filled. Soft crafts (fibre/cloth, hide/leather, bone, wood) are
largely buildable now; metal and other heat/station-dependent branches will mostly
FLAG until their systems exist.

---

## 2. Naming conventions (verbatim from the codebase)

| Thing | Convention | Example |
|---|---|---|
| Prototype variable | `UPPER_SNAKE_CASE` module global | `RABBIT_MEAT` |
| `prototype_key` | lowercase, matches the variable | `"rabbit_meat"` |
| `key` (display name) | lowercase noun phrase | `"raw rabbit meat"` |
| Recipe `name` | lowercase, **spaces** not underscores | `"linen shirt"` |
| `output_prototypes` entry | the lowercase `prototype_key` | `"linen_shirt"` |
| Crafting-material tag-key | lowercase, the thing recipes match on | `"raw_hide"` |
| Harvest-template key | lowercase, == creature's `harvest_template` | `"rabbit"` |

`desc` style: in-world, evocative, present tense, describes the object itself (not
"you see..."). Long descs use parenthesised string concatenation, e.g.:

```python
"desc": (
    "A raw animal hide, fur still on and the underside damp. Untreated it "
    "will spoil; tanned, it becomes leather fit for working."
),
```

---

## 3. Prototype schemas (`world/prototypes.py`)

Only these `typeclass` strings exist — never use any other without FLAGging:

| typeclass | Use for | Required / common keys |
|---|---|---|
| `typeclasses.objects.Object` | inert items, materials, tools | `tags` |
| `typeclasses.consumables.Food` | edible | `restore_amount`, `consume_message` |
| `typeclasses.consumables.Drink` | drinkable | `charges`, `max_charges`, `restore_amount`, `refillable` |
| `typeclasses.clothing.ClothingWithBuffs` | wearables | `clothing_type`, `warmth` |
| `typeclasses.creatures.Creature` | huntable fauna | `siz`, `harvest_template`, optional `natural_ap`, `flee_skill` |
| `typeclasses.resources.ResourceNode` | gatherable node | `resource_type`, `max_yield`, `regen_interval`, `available`, `yield_prototype` |

Every prototype has: `prototype_key`, `typeclass`, `key`, usually `aliases` and
`desc`.

### 3.1 Crafting material (consumed by recipes)
```python
RAW_HIDE = {
    "prototype_key": "raw_hide",
    "typeclass": "typeclasses.objects.Object",
    "key": "raw hide",
    "aliases": ["hide", "pelt"],
    "desc": "A raw animal hide, fur still on...",
    # tag-key "raw_hide" is what recipes list in consumable_tags. SOURCE: H5
    # rabbit harvest. SINK: the tanning recipe consumes it into leather.
    "tags": [("raw_hide", "crafting_material")],
}
```

### 3.2 Crafting tool (matched, NEVER consumed; optional with a penalty)
```python
KNIFE = {
    "prototype_key": "knife",
    "typeclass": "typeclasses.objects.Object",
    "key": "knife",
    "aliases": ["blade"],
    "desc": "A simple bladed knife, handy for shaping and cutting.",
    "tags": [("knife", "crafting_tool")],   # category MUST be crafting_tool
}
```

### 3.3 Food
```python
RABBIT_MEAT = {
    "prototype_key": "rabbit_meat",
    "typeclass": "typeclasses.consumables.Food",
    "key": "raw rabbit meat",
    "aliases": ["meat", "rabbit meat"],
    "desc": "A portion of raw, dark rabbit meat...",
    "restore_amount": 15,   # hunger restored; raw small-game stays modest
    "consume_message": "You eat {key}. Gamey and tough raw, but it helps.",
}
```

### 3.4 Creature
```python
RABBIT = {
    "prototype_key": "rabbit",
    "typeclass": "typeclasses.creatures.Creature",
    "key": "rabbit",
    "aliases": ["bunny", "coney"],
    "desc": "A small wild rabbit...",
    "siz": 4,                       # Mongoose Legend SIZ; drives harvest yield
    "harvest_template": "rabbit",   # MUST be a key in HARVEST_TEMPLATES (§5)
    "tags": [("rabbit", "creature")],
    # Omit flee_skill / natural_ap to take the Creature defaults (30 / 0)
    # unless a specific value is requested.
}
```

### 3.5 ResourceNode
```python
FIBER_PLANT = {
    "prototype_key": "fiber_plant",
    "typeclass": "typeclasses.resources.ResourceNode",
    "key": "fibrous plant",
    "aliases": ["plant"],
    "desc": "A clump of tall, sinewy stalks...",
    "resource_type": "fibres",
    "max_yield": 6,
    "regen_interval": 1800,            # game-seconds per unit
    "available": 6,
    "yield_prototype": "plant_fiber",  # MUST equal an existing prototype_key
}
```

### 3.6 Clothing
`clothing_type` must be one of the existing values:
`fullbody`, `top`, `undershirt`, `shoes`, `hat`. Anything else → FLAG.
`warmth` is a small int (0–3 in current content; novel values → FLAG).
```python
LEATHER_BOOTS = {
    "prototype_key": "leather_boots",
    "typeclass": "typeclasses.clothing.ClothingWithBuffs",
    "key": "leather boots",
    "aliases": ["boots"],
    "desc": "Sturdy boots of oiled leather...",
    "clothing_type": "shoes",
    "warmth": 1,
}
```

---

## 4. Recipe schema (`world/recipes.py`)

Recipes are **one-line-config subclasses** of `MongooseCraftRecipe` (already
imported at the top of the file — do not re-import or redefine it).

```python
class LinenShirtRecipe(MongooseCraftRecipe):
    """Cut and stitch cloth into a linen shirt."""

    name = "linen shirt"                  # lowercase, spaces
    consumable_tags = ["cloth", "cloth"]  # tag-keys; repeat for quantity
    output_prototypes = ["linen_shirt"]   # prototype_keys that MUST exist
    tool_tag = "needle"                   # crafting_tool tag-key, or None
    craft_cooldown = 40                   # seconds; base is 30
```

Rules:
- `consumable_tags` lists **tag-keys** (the first element of a
  `crafting_material` tag). Repeat the same key N times to require N units.
- `tool_tag` is a `crafting_tool` tag-key or `None`. Tools are always
  **optional**: present gives +20, improvised (absent) gives −20. Never required.
- `craft_cooldown` defaults to 30; override only if requested.
- Do **not** add a `_finalize_item` method unless explicitly asked — that is
  quality-scaling balance logic. If asked, copy the existing `WaterskinRecipe`
  pattern exactly and FLAG any new thresholds.

---

## 5. Harvest template schema (`world/harvest_templates.py`)

Add a key to the `HARVEST_TEMPLATES` dict. Decay stages (`FRESH`, `STALE`,
`ROTTING`, `SKELETON`) are already imported at the top — use those names, never
raw ints.

```python
"rabbit": {
    "meat": {
        "skill": "hunting",      # a Character.skills key (e.g. "hunting", "craft")
        "difficulty": 20,        # Legend band: Easy +20, Normal 0, Hard -40
        "yield_divisor": 2,      # units = max(1, SIZ // divisor)
        "max_stage": STALE,      # highest decay stage still harvestable
        "prototype": "rabbit_meat",  # prototype_key that MUST exist in §3
    },
    "hide": {
        "skill": "craft",
        "difficulty": 0,
        "yield_divisor": 3,
        "max_stage": STALE,
        "prototype": "raw_hide",
    },
},
```

Difficulty bands currently in use: **Easy = +20, Normal = 0, Hard = −40.** Use one
of these. A different value is a balance call → FLAG it.

`skill` must be a real character skill. Known-safe values: `"hunting"`, `"craft"`.
Any other skill string → FLAG (it may not be granted at character creation).

---

## 6. Integrity checklist — run this before every commit

After generating, verify each reference resolves and paste the result. For every
"exists" line below, **confirm it by searching the real file in the repo** (open
or `grep` `world/prototypes.py`), not by trusting an example you were shown:

- [ ] Every recipe `output_prototypes` entry exists as a prototype in `prototypes.py`.
- [ ] Every recipe `consumable_tags` entry matches a `("<key>", "crafting_material")`
      tag on some existing prototype (the material's source).
- [ ] Every recipe `tool_tag` (if not None) matches a `("<key>", "crafting_tool")` tag.
- [ ] Every harvest part `prototype` exists in `prototypes.py`.
- [ ] Every harvest part `skill` is `"hunting"` or `"craft"` (else FLAGged).
- [ ] Every creature `harvest_template` has a matching key in `HARVEST_TEMPLATES`.
- [ ] Every `ResourceNode` `yield_prototype` equals an existing `prototype_key`.
- [ ] No `|` characters in any string. No new typeclass paths. No invented attrs.
- [ ] No `value` / price / vendor / "availability" fields anywhere.
- [ ] Every new tool has a crafting source tracing to base materials (or it's FLAGged).
- [ ] Every new item has a SOURCE + SINK comment.

---

## 7. Working style

- **Batch logically.** Generate a whole chain or a whole creature's parts in one
  pass (e.g. *deer → deer corpse parts → venison + raw_hide reuse → recipes*),
  so style stays consistent and references resolve within the batch.
- **Mirror the nearest example.** When unsure, find the most similar existing
  entry and copy its shape.
- **Atomic conventional commits**, English, one logical addition each:
  - `feat(prototypes): add deer creature and venison/hide parts`
  - `feat(recipes): add fur cloak and wool tunic recipes`
  - `feat(harvest): add deer harvest template`
- After a batch, end with the §6 checklist filled in and any `FLAG:` lines.

---

## 8. How this file is maintained

This file is the authoritative schema. **Claude/Adam own it.** When the game gains
a new attribute, typeclass, `clothing_type`, skill, or convention, Claude will
update the relevant schema section here (or hand Adam a patch). Your job is to
generate data that conforms to the schemas *as written above* — if the data you're
asked for doesn't fit, that's a FLAG, not a reason to extend the schema yourself.

---

## 9. Documentation version headers

Every Markdown doc in this project (repo **and** any project-knowledge copy) carries
a version header directly under its H1 title, so anyone can tell at a glance whether
they're looking at the latest copy:

```markdown
# <Title>

> **Rev N · YYYY-MM-DD** — one-line changelog of this rev
> **Canonical:** `<path>` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.
```

Rules:

- **Rev** is a monotonic integer, starting at `1`, **`+1` on every content change**,
  never reused. **Date** is that rev's date. **Changelog** is one line describing
  what changed in this rev.
- **Bumping the Rev is a mandatory part of any commit that changes a doc's content.**
  A content diff that does not move the Rev line is a review red flag.
- **No commit SHA in the header** — it is stale-by-construction (the bump commit
  changes the file, producing a new SHA). Rev + date is the human key; `git log` is
  the ground truth.
- A doc not yet in the repo marks Canonical as *"project-knowledge only — not yet in repo."*

This applies to **docs only**. The data files you generate (`world/prototypes.py`,
`world/recipes.py`, `world/harvest_templates.py`, …) are **not** docs and carry no Rev
header. But if you are ever asked to edit a Markdown doc that has one, bump its Rev in
the same commit.
