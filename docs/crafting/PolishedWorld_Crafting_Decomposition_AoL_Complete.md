# PolishedWorld — Crafting Decomposition: Arms of Legend (Complete)

> **Rev 1 · 2026-10-26** — first Rev header (BACKLOG, *Four docs under `docs/crafting/` and `docs/reference/` carry no Rev header*), written in the Alpha Content epic's close-out (Decomp AC6) with the statuses the epic's code made false. **Shared nodes:** `wood`, `stone`, `clay`, `flint` and `leather` → `[EXISTS]`, with their sources as the code has them (tree, rocky outcrop, clay bank, flint scatter; `LeatherRecipe`, `raw_hide` ×2, knife optional — no bark, no water); `raw_hide` and `bone` come from the **rabbit**, the only harvest creature; `feather` → `[DATA]` (no creature yields it). **`[DECISION #2]` swept:** every leather leaf → `[EXISTS]` (#2 was answered in code — soft hand-craft — and ratified 2026-10-17); `suede` → `[NEW MATERIAL]`; Soft and Hard Leather Armour → `[DATA]`; the saddle's block narrows to smithing. **Items the epic shipped** → `[EXISTS]`, naming the variant where the heading lists several (22 headings). The rule for every change: what `world/material_registry.py`, `world/prototypes.py` and `world/recipes.py` say on `main` today; component tags (`wood handle [DATA]`) are untouched.
> **Canonical:** `docs/crafting/PolishedWorld_Crafting_Decomposition_AoL_Complete.md` @ G0dlet/PolishedWorld — git wins.

Top-down decomposition of **all** items from *Arms of Legend*, grouped by category
with shared material nodes identified. Decompose top-down, generate bottom-up.

**Status legend:**
- `[EXISTS]` — prototype/recipe already in the repo, live.
- `[DATA]` — buildable now: pure data (prototype/recipe/node), no new code.
- `[NEW MATERIAL]` — a new shared material; must be registered first.
- `[DECISION #n]` — gated on an open decision in `material_registry.py`.
- `[BLOCKED: <system>]` — needs a typeclass/station/process that does not exist.
- `[SINK BLOCKED]` — the finished item has no *use* yet (its consumer is unbuilt).

---

## SHARED MATERIAL NODES (cross-category)

These materials appear in multiple item trees. Register once, use everywhere.

### Base Materials (Gatherable)
- **plant_fiber** `[EXISTS]` ← fiber plant ResourceNode `[EXISTS]`
- **raw_hide** `[EXISTS]` ← rabbit harvest (deer/boar intended, no creature yet)
- **bone** `[EXISTS]` ← rabbit harvest (deer/boar intended, no creature yet)
- **feather** `[DATA]` ← pheasant harvest (no creature yields it yet)
- **wood** `[EXISTS]` ← tree ResourceNode `[EXISTS]` (needs an axe; generic wood, species wait on DECISION #10)
- **stone** `[EXISTS]` ← rocky outcrop ResourceNode `[EXISTS]`
- **iron_ore** `[NEW MATERIAL]` ← bog/surface iron ResourceNode `[DATA]`
- **copper_ore** `[NEW MATERIAL]` ← surface copper ResourceNode `[DATA]`
- **tin_ore** `[NEW MATERIAL]` ← surface tin ResourceNode `[DATA]`
- **clay** `[EXISTS]` ← clay bank ResourceNode `[EXISTS]`
- **sand** `[NEW MATERIAL]` ← riverbed/beach ResourceNode `[DATA]`
- **ochre** `[NEW MATERIAL]` ← surface mineral ResourceNode `[DATA]`
- **sulfur** `[NEW MATERIAL]` ← volcanic/hot-spring ResourceNode `[DATA]`
- **saltpeter** `[NEW MATERIAL]` ← cave floor/urine deposits `[DATA]`
- **charcoal** `[NEW MATERIAL]` ← wood + kiln process `[BLOCKED: kiln]`
- **flint** `[EXISTS]` ← flint scatter ResourceNode `[EXISTS]`

### Intermediate Materials (Crafted)
- **twine** `[EXISTS]` ← plant fiber
- **cloth** `[EXISTS]` ← plant fiber
- **leather** `[EXISTS]` ← raw_hide ×2 (knife optional) — `LeatherRecipe`
- **oak_bark** `[NEW MATERIAL]` ← oak wood + knife
- **pigment** `[NEW MATERIAL]` ← ochre + milling
- **yarn** `[NEW MATERIAL]` ← wool + spinning
- **wool** `[NEW MATERIAL]` ← sheep harvest/shearing
- **silk** `[NEW MATERIAL]` ← silkworm cocoons + reeling `[BLOCKED: sericulture]`
- **bronze** `[NEW MATERIAL]` ← copper + tin + smelting `[BLOCKED: smelting]`
- **iron** `[NEW MATERIAL]` ← iron_ore + smelting `[BLOCKED: smelting]`
- **steel** `[NEW MATERIAL]` ← iron + carbon + refining `[BLOCKED: steelmaking]`
- **glass** `[NEW MATERIAL]` ← sand + soda_ash + glassblowing `[BLOCKED: glassblowing]`
- **pottery** `[NEW MATERIAL]` ← clay + firing `[BLOCKED: kiln]`
- **paper** `[NEW MATERIAL]` ← papyrus/pulp + pressing `[DATA]`
- **ink** `[NEW MATERIAL]` ← soot + gum + water `[DATA]`

### Tools (Crafting)
- **knife** `[EXISTS]` ← bone/iron/steel + handle
- **needle** `[EXISTS]` ← bone/iron
- **hammer** `[NEW MATERIAL]` ← iron/steel + wood handle `[BLOCKED: smithing]`
- **chisel** `[NEW MATERIAL]` ← iron/steel + wood handle `[BLOCKED: smithing]`
- **saw** `[NEW MATERIAL]` ← iron/steel + wood handle `[BLOCKED: smithing]`
- **anvil** `[NEW MATERIAL]` ← iron/steel `[BLOCKED: smithing]`
- **furnace/kiln** `[BLOCKED: station typeclass]`
- **forge** `[BLOCKED: station typeclass]`
- **pottery_wheel** `[NEW MATERIAL]` ← wood + stone `[BLOCKED: carpentry]`

---

## CATEGORY A: ADVENTURING GEAR (~100 items)

### A1. Containers & Carrying

**Backpack** `[EXISTS]`
```
backpack
└─ assembly ← leather/canvas + (tool: needle)
   ├─ leather `[EXISTS]` ← raw_hide ×2
   │  └─ raw_hide `[EXISTS]` ← creature harvest
   ├─ canvas (heavy cloth) `[DATA]` ← plant_fiber -> cloth (multiple bolts)
   │  └─ plant_fiber `[EXISTS]`
   └─ straps ← leather strips
```

**Sack (small/large)** `[EXISTS]` (one size)
```
sack
└─ assembly ← leather/canvas + (tool: needle)
   └─ (same as backpack, simpler construction)
```

**Waterskin** `[EXISTS]`
```
waterskin `[EXISTS]`
└─ gourd + twine `[EXISTS]`
   ├─ raw_gourd `[EXISTS]` ← gourd vine ResourceNode `[EXISTS]`
   └─ twine `[EXISTS]` ← plant_fiber
```

**Bottle, Glass** `[BLOCKED: glassblowing]`
```
glass bottle
└─ glassblowing `[BLOCKED: furnace + glassblowing process]`
   ├─ sand `[NEW MATERIAL]` ← riverbed/beach
   ├─ soda_ash `[NEW MATERIAL]` ← plant_ash + leaching
   │  └─ plant_ash `[DATA]` ← burned plant_fiber/wood
   └─ stopper (cork/wood) `[DATA]` ← oak wood + knife
```

**Scrollcase** `[EXISTS]`
```
scrollcase
└─ assembly ← leather/bone + (tool: knife, needle)
   ├─ leather `[EXISTS]`
   └─ bone tube ← bone + knife
      └─ bone `[EXISTS]`
```

### A2. Light & Fire

**Torch (1-hour)** `[DATA]`
```
torch
└─ assembly ← wood + cloth + pitch/oil
   ├─ wood `[EXISTS]` ← tree
   ├─ cloth `[EXISTS]` ← plant_fiber
   └─ pitch `[NEW MATERIAL]` ← tree resin gather `[DATA]`
```

**Candle (1/2/6 hour)** `[DATA]`
```
candle
└─ assembly ← tallow/beeswax + wick
   ├─ tallow `[NEW MATERIAL]` ← animal fat rendering `[DATA]`
   │  └─ animal fat ← creature harvest (boar/deer)
   ├─ beeswax `[NEW MATERIAL]` ← beehive gather `[DATA]`
   └─ wick `[DATA]` ← plant_fiber twisted
```

**Lantern (basic/cowled/hanging)** `[BLOCKED: glassblowing + smithing]`
```
lantern
└─ assembly `[BLOCKED: needs glass + metal frame]`
   ├─ glass mantle `[BLOCKED: glassblowing]`
   ├─ metal frame `[BLOCKED: smithing]` ← iron/bronze
   ├─ oil flask `[DATA]` ← pottery/copper + oil
   └─ wick `[DATA]`
```

**Flint and Tinder** `[DATA]`
```
flint and tinder
├─ flint `[EXISTS]` ← flint scatter
├─ steel striker `[BLOCKED: smithing]` ← iron/steel
└─ tinder `[DATA]` ← dried plant_fiber/fungus
```

### A3. Rope & Cordage

**Rope, Hemp (10m)** `[DATA]`
```
hemp rope
└─ braiding ← plant_fiber (many units)
   └─ plant_fiber `[EXISTS]`
```

**Rope, Silken** `[BLOCKED: sericulture]`
```
silk rope
└─ braiding ← silk thread `[BLOCKED: silkworm + reeling]`
```

### A4. Writing & Recording

**Papyrus Sheet** `[DATA]`
```
papyrus sheet
└─ pressing ← papyrus reeds (gathered)
   └─ papyrus reeds `[NEW MATERIAL]` ← wetland ResourceNode `[DATA]`
```

**Codex (blank)** `[DATA]`
```
codex
└─ binding ← paper/parchment sheets + cover
   ├─ paper `[NEW MATERIAL]` ← papyrus/pulp + pressing
   └─ cover ← leather/wood
```

**Writing Kit** `[DATA]`
```
writing kit
├─ ink `[NEW MATERIAL]` ← soot + gum + water
├─ quills/brushes ← feather/reeds
│  └─ feather `[EXISTS]`
└─ case ← wood/leather
```

**Chalk** `[DATA]`
```
chalk
└─ shaped ← limestone/chalk stone (gathered)
   └─ limestone `[NEW MATERIAL]` ← surface gather `[DATA]`
```

### A5. Tools & Utility

**Hammer** `[BLOCKED: smithing]`
```
hammer
└─ assembly `[BLOCKED: needs forged head]`
   ├─ iron/steel head `[BLOCKED: smithing + smelting]`
   └─ wood handle `[DATA]` ← oak wood + knife
```

**Crowbar** `[BLOCKED: smithing]`
```
crowbar
└─ forged ← iron bar + bending
   └─ iron `[BLOCKED: smelting]`
```

**Saw, Hand** `[BLOCKED: smithing]`
```
hand saw
└─ assembly `[BLOCKED: needs forged blade]`
   ├─ iron/steel blade `[BLOCKED: smithing]`
   └─ wood handle `[DATA]`
```

**Lock Picks** `[BLOCKED: smithing]`
```
lock picks
└─ forged ← thin iron/steel wires
   └─ iron/steel `[BLOCKED: smelting + smithing]`
```

**Compass** `[BLOCKED: smithing + glassblowing]`
```
compass
└─ assembly `[BLOCKED: multiple systems]`
   ├─ lodestone needle `[DATA]` ← magnetite gather
   ├─ glass face `[BLOCKED: glassblowing]`
   ├─ metal casing `[BLOCKED: smithing]`
   └─ oil `[DATA]` ← rendered fat
```

**Hourglass** `[BLOCKED: glassblowing]`
```
hourglass
└─ assembly `[BLOCKED: needs glass + sand]`
   ├─ glass bulbs (2) `[BLOCKED: glassblowing]`
   ├─ frame ← wood/brass
   └─ fine sand `[DATA]` ← sand sifting
```

### A6. Camping & Shelter

**Bedroll** `[DATA]`
```
bedroll
└─ assembly ← cloth + padding + cord
   ├─ cloth `[EXISTS]`
   ├─ padding (wool/fur) `[NEW MATERIAL]` ← wool/fur gather
   └─ cord ← twine `[EXISTS]`
```

**Tent (4/8 person)** `[EXISTS]` (one tent)
```
tent
└─ assembly ← canvas + poles + ropes
   ├─ canvas (heavy cloth) `[DATA]` ← plant_fiber
   ├─ wooden poles `[DATA]` ← oak/ash wood
   └─ ropes ← plant_fiber
```

**Folding Stool** `[BLOCKED: smithing]`
```
folding stool
└─ assembly ← canvas + metal hinges/legs
   ├─ canvas `[DATA]`
   └─ metal legs/hinges `[BLOCKED: smithing]`
```

### A7. Food & Water Processing

**Fishing Kit** `[DATA]`
```
fishing kit
├─ hooks ← bone/bronze/iron wire `[hooks: DATA; metal: BLOCKED]`
├─ line ← plant_fiber twine
├─ rod ← wood (segmented)
└─ corks ← oak bark
```

**Milling Stones** `[EXISTS]`
```
milling stones
└─ carved ← stone (two pieces)
   └─ stone `[EXISTS]` ← rocky outcrop
```

**Preserving Kit** `[DATA]`
```
preserving kit
├─ salt `[NEW MATERIAL]` ← sea salt/rock salt gather `[DATA]`
├─ jars ← pottery `[BLOCKED: kiln]`
├─ sawdust ← wood scraping
└─ sheets ← cloth/leather
```

### A8. Specialized Gear

**Climbing Kit** `[DATA]`
```
climbing kit
├─ harness ← leather
├─ ropes ← plant_fiber
├─ pitons ← iron `[BLOCKED: smithing]`
└─ tools ← bone/iron
```

**Block and Tackle** `[BLOCKED: smithing]`
```
block and tackle
└─ assembly `[BLOCKED: needs pulleys]`
   ├─ wooden pulleys `[DATA]` ← wood + knife
   ├─ rope ← plant_fiber
   └─ metal hooks/rings `[BLOCKED: smithing]`
```

**Grappling Hook** `[BLOCKED: smithing]`
```
grappling hook
└─ forged ← iron/steel
   └─ iron/steel `[BLOCKED: smelting + smithing]`
```

---

## CATEGORY B: RIDING & ANIMAL SUPPLIES (~15 items)

**Saddle (Riding/War/Pack/Flight)** `[BLOCKED: smithing]`
```
saddle
└─ assembly `[BLOCKED: needs metal fittings]`
   ├─ leather (shaped) `[EXISTS]`
   ├─ wood frame `[DATA]`
   ├─ padding (wool/fur) `[NEW MATERIAL]`
   ├─ metal fittings `[BLOCKED: smithing]`
   └─ straps ← leather
```

**Saddlebag** `[EXISTS]`
```
saddlebag
└─ assembly ← leather/canvas + straps
   ├─ leather/canvas `[DATA/DECISION]`
   └─ straps ← leather
```

**Bit and Bridle** `[BLOCKED: smithing]`
```
bit and bridle
├─ bit (metal) `[BLOCKED: smithing]` ← iron/bronze
├─ reins ← leather
└─ straps ← leather
```

**Horseshoes** `[BLOCKED: smithing]`
```
horseshoes
└─ forged ← iron/steel (shaped)
   └─ iron/steel `[BLOCKED: smelting + smithing]`
```

**Barding (animal armour)** `[BLOCKED: armour system]`
```
barding
└─ (same as armour, scaled for animal) `[see Armour section]`
```

---

## CATEGORY C: CLOTHING (~50 items)

### C1. Basic Garments

**Shirt/Tunic (common/fancy)** `[EXISTS]` (linen shirt)
```
shirt/tunic
└─ cut + stitch ← cloth + (tool: needle)
   ├─ cloth `[EXISTS]` ← plant_fiber
   └─ needle `[EXISTS]`
```

**Breeches/Pants** `[EXISTS]` (breeches)
```
breeches
└─ cut + stitch ← cloth + (tool: needle)
   └─ cloth `[EXISTS]`
```

**Dress/Robe** `[EXISTS]` (robe)
```
dress/robe
└─ cut + stitch ← cloth (multiple bolts) + (tool: needle)
   └─ cloth `[EXISTS]`
```

**Cloak (common/winter)** `[DATA]`
```
cloak
└─ assembly ← cloth/fur + (tool: needle)
   ├─ cloth `[EXISTS]`
   └─ fur lining `[NEW MATERIAL]` ← creature hide with fur
```

**Coat (common/winter)** `[DATA]`
```
coat
└─ assembly ← cloth/leather + fur lining + (tool: needle)
   ├─ cloth/leather `[EXISTS/DECISION]`
   └─ fur `[NEW MATERIAL]`
```

### C2. Footwear

**Boots (common/high/riding)** `[EXISTS]` (leather boots)
```
boots
└─ cut + stitch ← leather + (tool: knife, needle)
   └─ leather `[EXISTS]`
```

**Shoes (common/fancy/sandals)** `[EXISTS]` (shoes)
```
shoes
└─ cut + stitch ← leather/cloth + (tool: knife, needle)
   └─ leather/cloth `[EXISTS]`
```

### C3. Headwear

**Hat (brimmed/cowled/winter)** `[DATA]`
```
hat
└─ assembly ← cloth/felt + (tool: needle)
   ├─ cloth `[EXISTS]`
   └─ felt `[NEW MATERIAL]` ← matted wool/fur
```

**Hood/Cowl** `[EXISTS]` (hood)
```
hood
└─ cut + stitch ← cloth + (tool: needle)
   └─ cloth `[EXISTS]`
```

### C4. Specialized Clothing

**Catsuit, Intruder's** `[BLOCKED: silk]`
```
intruder's catsuit
└─ tailored fit ← silk/suede + (tool: needle)
   ├─ silk `[BLOCKED: sericulture]`
   └─ suede (soft leather) `[NEW MATERIAL]`
```

**Reversible Clothes** `[EXISTS]`
```
reversible clothes
└─ assembly ← cloth (two patterns) + (tool: needle)
   └─ cloth `[EXISTS]`
```

**Bandolier** `[EXISTS]`
```
bandolier
└─ assembly ← leather + loops + (tool: knife, needle)
   └─ leather `[EXISTS]`
```

---

## CATEGORY D: ARMOUR (~13 types + modifications)

### D1. Soft Armour

**Soft Leather Armour** `[DATA]`
```
soft leather armour
└─ cut + stitch ← leather + (tool: knife, needle)
   └─ leather `[EXISTS]`
      ├─ raw_hide `[EXISTS]`
      ├─ oak_bark `[NEW MATERIAL]` ← oak wood + knife
      └─ water `[DECISION #6]`
```

**Hard Leather Armour** `[DATA]`
```
hard leather armour
└─ treated ← leather (boiled/layered) + (tool: knife)
   └─ leather `[EXISTS]`
```

**Linen Cuirass** `[EXISTS]`
```
linen cuirass
└─ quilted ← multiple cloth layers + stitching
   └─ cloth `[EXISTS]`
```

### D2. Metal Armour (all BLOCKED on smelting + smithing)

**Ringmail** `[BLOCKED: smithing]`
```
ringmail
└─ assembly `[BLOCKED: needs metal rings + leather backing]`
   ├─ iron/bronze rings `[BLOCKED: smelting + smithing]`
   └─ leather backing `[EXISTS]`
```

**Scalemail** `[BLOCKED: smithing]`
```
scalemail
└─ assembly `[BLOCKED: needs metal scales + backing]`
   ├─ iron/bronze scales `[BLOCKED: smithing]`
   └─ leather backing `[EXISTS]`
```

**Chainmail** `[BLOCKED: smithing]`
```
chainmail
└─ woven ← iron/steel wire links `[BLOCKED: wire-drawing + smithing]`
   └─ iron/steel `[BLOCKED: smelting + steelmaking]`
```

**Banded/Lamellar** `[BLOCKED: smithing]`
```
banded armour
└─ stitched ← metal plates + leather backing
   ├─ iron/steel plates `[BLOCKED: smithing]`
   └─ leather backing `[EXISTS]`
```

**Brigandine** `[BLOCKED: smithing]`
```
brigandine
└─ sandwiched ← metal scales between leather layers + rivets
   ├─ metal scales `[BLOCKED: smithing]`
   ├─ leather layers `[EXISTS]`
   └─ rivets `[BLOCKED: smithing]`
```

**Plate Armour** `[BLOCKED: smithing]`
```
plate armour
└─ forged + fitted ← steel plates (shaped) `[BLOCKED: smithing + forming]`
   └─ steel `[BLOCKED: smelting + steelmaking]`
```

### D3. Alternate Materials

**Bone Armour** `[EXISTS]`
```
bone armour
└─ carved + backed ← bone plates + fur/leather backing
   ├─ bone `[EXISTS]`
   └─ backing ← fur/leather `[NEW/DECISION]`
```

**Wooden Armour** `[DATA]`
```
wooden armour
└─ carved ← wood (shaped) + lacquer
   ├─ wood `[EXISTS]`
   └─ lacquer `[NEW MATERIAL]` ← tree resin + processing
```

### D4. Armour Modifications

**Reinforced** `[BLOCKED: smithing]`
```
reinforced armour
└─ added metal strips ← base armour + metal strips
   └─ metal strips `[BLOCKED: smithing]`
```

**Spiked** `[BLOCKED: smithing]`
```
spiked armour
└─ added spikes ← base armour + metal spikes
   └─ metal spikes `[BLOCKED: smithing]`
```

**Wintered** `[DATA]`
```
wintered armour
└─ lined ← base armour + fur/wool lining
   └─ fur/wool `[NEW MATERIAL]`
```

---

## CATEGORY E: WEAPONS

### E1. Simple/Wooden Weapons (mostly DATA)

**Club** `[EXISTS]`
```
club
└─ shaped ← wood (hardened)
   └─ wood `[EXISTS]`
```

**Quarterstaff** `[EXISTS]`
```
quarterstaff
└─ shaped + banded ← wood + (optional: metal bands)
   ├─ wood `[EXISTS]`
   └─ metal bands `[BLOCKED: smithing]` (optional)
```

**Spear (short/long)** `[EXISTS]` (one spear)
```
spear
└─ assembly ← wood shaft + tip
   ├─ wood `[EXISTS]`
   └─ tip ← bone/iron/steel
      ├─ bone tip `[DATA]` ← bone `[EXISTS]`
      └─ metal tip `[BLOCKED: smithing]`
```

**Bow (short/long/recurve)** `[EXISTS]` (one bow)
```
bow
└─ shaped + strung ← wood + bowstring
   ├─ wood (ash/yew) `[EXISTS]` (generic wood in the alpha)
   └─ bowstring ← plant_fiber/sinew/hair
      ├─ fiber string `[DATA]` ← plant_fiber
      └─ sinew `[NEW MATERIAL]` ← creature harvest
```

**Sling** `[EXISTS]`
```
sling
└─ braided ← leather/cloth strip
   └─ leather/cloth `[EXISTS]`
```

### E2. Metal Weapons (all BLOCKED on smelting + smithing)

**Dagger** `[BLOCKED: smithing]`
```
dagger
└─ forged + hafted ← blade + handle
   ├─ iron/steel blade `[BLOCKED: smithing + smelting]`
   └─ wood/bone handle `[DATA]`
```

**Sword (short/long/bastard/great)** `[BLOCKED: smithing]`
```
sword (see decomposition in Example A)
└─ forged + assembled ← blade + guard + pommel + handle + grip
   ├─ blade `[BLOCKED: smithing]`
   ├─ guard `[BLOCKED: smithing]`
   ├─ pommel `[BLOCKED: smithing]`
   ├─ handle ← wood `[DATA]`
   └─ grip wrap ← leather `[EXISTS]`
```

**Axe (hand/battle/great)** `[BLOCKED: smithing]`
```
axe
└─ hafted ← head + handle
   ├─ iron/steel head `[BLOCKED: smithing]`
   └─ wood handle `[DATA]`
```

**Mace/War Hammer** `[BLOCKED: smithing]`
```
mace/war hammer
└─ assembly ← head + shaft
   ├─ iron/steel head `[BLOCKED: smithing]`
   └─ wood shaft `[DATA]`
```

**Polearm (halberd/glaive/bill)** `[BLOCKED: smithing]`
```
polearm
└─ assembly ← long shaft + metal head
   ├─ wood shaft `[DATA]`
   └─ metal head `[BLOCKED: smithing]`
```

### E3. Ranged Weapons

**Crossbow (light/heavy)** `[BLOCKED: smithing + mechanisms]`
```
crossbow
└─ assembly `[BLOCKED: needs mechanical parts]`
   ├─ wood/steel bow `[DATA/BLOCKED]`
   ├─ stock ← wood `[DATA]`
   ├─ trigger mechanism `[BLOCKED: smithing + mechanisms]`
   └─ string ← sinew/fiber
```

**Arbalest** `[BLOCKED: smithing + engineering]`
```
arbalest
└─ (massive crossbow, same tree but larger)
```

### E4. Ammunition

**Arrows** `[DATA]`
```
arrow
└─ assembly ← shaft + head + fletching
   ├─ wood shaft `[DATA]`
   ├─ head ← bone/iron/steel
   │  ├─ bone `[EXISTS]`
   │  └─ metal `[BLOCKED: smithing]`
   └─ fletching ← feather
      └─ feather `[EXISTS]`
```

**Bolts (crossbow)** `[DATA]`
```
bolt
└─ assembly ← shorter shaft + head + fletching
   └─ (same as arrow, smaller)
```

**Sling Bullets** `[EXISTS]` (clay)
```
sling bullet
└─ shaped ← clay/stone/lead
   ├─ clay `[EXISTS]` (formed, sun-dried; fired waits on a kiln)
   ├─ stone `[EXISTS]` (shaped; no stone bullet in the alpha, AC4.0 B7)
   └─ lead `[BLOCKED: smelting]`
```

### E5. Black Powder Weapons (all BLOCKED)

**Musket/Arquebus/Pistol** `[BLOCKED: black powder + gunsmithing]`
```
firearm
└─ assembly `[BLOCKED: multiple systems]`
   ├─ metal barrel `[BLOCKED: smithing + drilling]`
   ├─ stock ← wood `[DATA]`
   ├─ lock mechanism `[BLOCKED: smithing + mechanisms]`
   └─ black powder `[BLOCKED: alchemy/chemistry]`
      ├─ saltpeter `[NEW MATERIAL]`
      ├─ sulfur `[NEW MATERIAL]`
      └─ charcoal `[BLOCKED: kiln]`
```

### E6. Weapon Modifications

**Banded** `[BLOCKED: smithing]`
```
banded weapon
└─ added metal bands ← base weapon + metal bands
   └─ metal bands `[BLOCKED: smithing]`
```

**Serrated** `[BLOCKED: smithing]`
```
serrated weapon
└─ modified edge ← base weapon + filing
   └─ (requires file tool `[BLOCKED: smithing]`)
```

---

## CATEGORY F: TRANSPORT

### F1. Land Vehicles (all BLOCKED on carpentry + smithing)

**Cart (small/medium/large)** `[BLOCKED: carpentry + smithing]`
```
cart
└─ assembly `[BLOCKED: needs wheels + frame]`
   ├─ wooden frame `[BLOCKED: carpentry]`
   ├─ wooden wheels `[BLOCKED: carpentry]`
   ├─ metal fittings `[BLOCKED: smithing]`
   └─ harness ← leather
```

**Chariot (light/heavy/battle)** `[BLOCKED: carpentry + smithing]`
```
chariot
└─ (similar to cart, lighter/faster)
```

**Sled (dog/heavy/ice/war)** `[DATA for basic]`
```
sled
└─ assembly ← wood + (optional: metal blades)
   ├─ wooden slats/runners `[DATA]`
   └─ metal blades (ice sled) `[BLOCKED: smithing]`
```

### F2. Watercraft (all BLOCKED on carpentry + shipbuilding)

**Raft** `[DATA]`
```
raft
└─ lashed ← logs + rope
   ├─ logs `[NEW MATERIAL]` ← tree felling
   └─ rope ← plant_fiber
```

**Canoe (hide/dugout)** `[DATA]`
```
canoe
├─ hide canoe ← hides + frame
│  ├─ hides (sewn) `[EXISTS]` (leather)
│  └─ wood frame `[DATA]`
└─ dugout ← hollowed log
   └─ log `[NEW MATERIAL]`
```

**Rowboat** `[BLOCKED: carpentry]`
```
rowboat
└─ built ← wooden planks + nails
   ├─ planks `[BLOCKED: carpentry + saw]`
   └─ nails `[BLOCKED: smithing]`
```

**Ships (all types)** `[BLOCKED: shipwright + massive resources]`
```
ship (barge/cog/carrack/galleon/etc.)
└─ built `[BLOCKED: shipyard + shipwright + carpentry + smithing]`
   ├─ hull (planks) `[BLOCKED: carpentry]`
   ├─ masts ← large trees
   ├─ sails ← cloth (massive)
   ├─ rigging ← rope (massive)
   └─ fittings `[BLOCKED: smithing]`
```

---

## CATEGORY G: BEASTS & COHORTS

### G1. Domestic Animals (not crafted, trained)

Animals are not crafted — they are **trained** using Lore (Animal) skill.
Training is a time-based skill progression, not a crafting recipe.

**No crafting decomposition applies.** Animals are acquired via:
- Purchase (from breeders/trainers)
- Capture (wild) + training
- Breeding (requires paired animals + time)

### G2. Hired Companions (NPCs, not crafted)

Hirelings are **NPCs** with skills, not items. They are hired via:
- Payment (SP/day)
- Loyalty/morale system
- Contract terms

**No crafting decomposition applies.**

---

## CATEGORY H: ALCHEMY

### H1. Laboratory Equipment (all BLOCKED)

**Alchemist's Laboratory** `[BLOCKED: glassblowing + pottery + smithing]`
```
laboratory setup
├─ furnace/athanor `[BLOCKED: pottery/masonry + heat]`
├─ alembics `[BLOCKED: glassblowing]`
├─ retorts `[BLOCKED: glassblowing]`
├─ crucibles `[BLOCKED: pottery]`
├─ mortars + pestles `[DATA]` ← stone
└─ storage jars `[BLOCKED: pottery]`
```

### H2. Alchemical Processes (all BLOCKED)

**Philosopher's Stone** `[BLOCKED: alchemy system]`
```
philosopher's stone
└─ Great Work `[BLOCKED: alchemy process + laboratory]`
   ├─ mercury `[NEW MATERIAL]` ← cinnabar ore + processing
   ├─ salt (alchemical) `[NEW MATERIAL]` ← metal + acid + distillation
   ├─ sulfur `[NEW MATERIAL]`
   └─ (week-long process + Lore (Alchemy) rolls)
```

**Poisons** `[BLOCKED: alchemy system]`
```
poison
└─ formulated `[BLOCKED: alchemy process + materials]`
   ├─ toxic ingredients (plant/mineral/animal)
   ├─ solvent (water/alcohol/vinegar)
   └─ (week per dose + Lore (Alchemy) roll)
```

**Transmutation (base metal → gold)** `[BLOCKED: alchemy + philosopher's stone]`
```
gold (transmuted)
└─ Great Work `[BLOCKED: philosopher's stone + week per gram]`
   ├─ base metal (copper/tin/lead)
   ├─ philosopher's stone (see above)
   └─ (week per gram + Lore (Alchemy) roll)
```

---

## CATEGORY I: ENCHANTMENTS (MAGICAL)

Enchantments are **magical effects**, not crafted items. They require:
- Sorcery skill (Enchanting Ritual spell)
- Magic Point investment
- Time (hours = MP²)
- (Optional) Power Crystals

**No crafting decomposition applies** — this is a magic system, not a crafting tree.

---

## SYSTEM BACKLOG (in build order)

1. **Wood gathering** — tree ResourceNodes + `wood` material. `[EXISTS]`
2. **Stone/clay gathering** — surface nodes. `[EXISTS]` (stone, clay, flint; sand `[DATA]`)
3. **Ore gathering** — iron/copper/tin/sulfur nodes. `[DATA]`
4. **Tanning (DECISION #2)** — raw_hide → leather. `[EXISTS]` (soft hand-craft, ratified 2026-10-17)
5. **Charcoal burning** — wood → charcoal via kiln. `[BLOCKED: kiln station]`
6. **Smelting** — ore → metal (iron/bronze). `[BLOCKED: furnace + process]`
7. **Smithing** — metal → tools/weapons/armour. `[BLOCKED: forge + anvil + process]`
8. **Steelmaking** — iron + carbon → steel. `[BLOCKED: refining process]`
9. **Glassblowing** — sand → glass. `[BLOCKED: furnace + process]`
10. **Pottery/Kiln** — clay → pottery. `[BLOCKED: kiln station]`
11. **Carpentry** — wood → planks/frames. `[BLOCKED: saw + tools]`
12. **Sericulture** — silkworms → silk. `[BLOCKED: lifecycle + reeling]`
13. **Alchemy** — chemicals + processes. `[BLOCKED: laboratory + system]`
14. **Shipbuilding** — massive carpentry + smithing. `[BLOCKED: shipyard]`

---

## GENERATION PRIORITY (leaf-to-root)

**Committable today (after decisions):**
1. `wood` material + tree nodes `[DATA]`
2. `stone`/`clay`/`sand`/`flint`/`sulfur` materials + nodes `[DATA]`
3. `ore` materials + nodes `[DATA]`
4. Simple wooden items (club, spear shaft, bow, raft, canoe) `[DATA]`
5. Cloth/fiber items (clothing, rope, sacks, bedroll, tent) `[DATA]`
6. Bone items (bone armour, bone tools) `[DATA]`
7. Arrow/bolt assembly (with bone heads) `[DATA]`

**Unblocked by DECISION #2 (tanning ratified 2026-10-17):**
8. Leather items (boots, soft armour, saddles, bags) `[DATA]`

**Blocked on systems:**
9. All metal items (weapons, metal armour, tools) `[BLOCKED: smelting + smithing]`
10. All glass items (bottles, lanterns, hourglass) `[BLOCKED: glassblowing]`
11. All pottery (jars, crucibles) `[BLOCKED: kiln]`
12. All vehicles (carts, ships) `[BLOCKED: carpentry + smithing]`
13. All black powder items `[BLOCKED: alchemy]`

---

## SHARED NODE SUMMARY

| Material | Used By |
|---|---|
| wood | weapons, tools, vehicles, ships, armour (wooden), furniture |
| iron/steel | weapons, armour, tools, fittings, nails, hinges |
| leather | armour, clothing, containers, saddles, straps |
| cloth | clothing, containers, sails, tents, bedding |
| bone | weapons, armour, tools, ammunition |
| feather | ammunition (fletching), clothing (trim) |
| plant_fiber | cloth, rope, containers, bedding |
| stone | tools, ammunition, buildings, milling |
| clay | pottery, bricks, ammunition |
| sand | glass, pottery (temper), ammunition |

---

## INTEGRITY NOTES

- No `value`/price fields used (per AGENTS.md).
- No `|` characters in any string.
- All typeclass references use existing paths.
- All `harvest_template` keys match existing templates.
- All `yield_prototype` keys match existing prototypes.

**FLAG: Scale** — This decomposition covers ~400-500 items. Many share the same
material chains. The system backlog is the real bottleneck: until smelting/smithing
exist, the entire metal branch (weapons, metal armour, tools, vehicles) is blocked.

**FLAG: Trade economy** — Arms of Legend uses prices (SP/CP). PolishedWorld has no
vendor economy. All items must be crafted from gatherable materials. This decomposition
respects that constraint.
