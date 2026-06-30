# PolishedWorld — System Backlog (14 Systems Needed)

Prioriterad lista över de 14 system som behöver byggas för att låsa upp hela
crafting-trädet från *Arms of Legend*. Sorterad i byggordning med beroenden.

---

## SYSTEM 1: Wood Gathering `[DATA — bygg först]`

**Vad det gör:**
Spelare kan samla trä från träd (ek, ask, yxe, etc.) via ResourceNodes.

**Implementation:**
- `ResourceNode`-prototyper för olika trädslag (oak_tree, ash_tree, yew_tree)
- `wood`-material i material_registry (olja: `oak_wood`, `ash_wood`, etc.)
- Eventuellt: `log`-prototyp (fäller träd → log → sågas till planks)

**Exempel på items som låses upp:**
- Club, quarterstaff, spear shaft, bow (wooden)
- Raft, canoe (dugout)
- Wooden armour, torch handles
- Tool handles (hammer, axe, etc.)

**Beroenden:** Inga — kan byggas direkt.

**Prioritet:** KRITISK — trä behövs i nästan allt.

---

## SYSTEM 2: Stone/Clay/Sand/Mineral Gathering `[DATA — bygg först]`

**Vad det gör:**
Spelare kan samla sten, lera, sand, flinta, svavel, salpeter, ockra från ytnoder.

**Implementation:**
- `ResourceNode`-prototyper: boulder, clay_deposit, sand_bank, flint_deposit, sulfur_vent, ochre_vein, saltpeter_crust
- Material i registry: `stone`, `clay`, `sand`, `flint`, `sulfur`, `saltpeter`, `ochre`
- Eventuellt: `limestone` för chalk/cement

**Exempel på items som låses upp:**
- Stone tools (hammer head, mace head)
- Sling bullets (stone/clay)
- Milling stones, grindstones
- Chalk, pigment (ochre)
- Pottery (raw clay)
- Black powder ingredients (sulfur + saltpeter)

**Beroenden:** Inga — kan byggas direkt.

**Prioritet:** HÖG — behövs för pottery, black powder, pigment.

---

## SYSTEM 3: Ore Gathering `[DATA — bygg först]`

**Vad det gör:**
Spelare kan samla malm (järn, koppar, tenn) från ytnoder (bog iron, surface deposits).

**Implementation:**
- `ResourceNode`-prototyper: bog_iron, copper_deposit, tin_deposit
- Material i registry: `iron_ore`, `copper_ore`, `tin_ore`
- Eventuellt: `cinnabar` (kvicksilver/sulfid) för alchemy
- Tidigare: mining skill + pickaxe (advanced gathering)

**Exempel på items som låses upp:**
- Alla metallföremål (efter smelting + smithing)
- Bronze (copper + tin)
- Iron/steel weapons, armour, tools
- Lead (sling bullets, weights)

**Beroenden:** Inga — kan byggas direkt.

**Prioritet:** KRITISK — behövs för hela metallgrenen.

---

## SYSTEM 4: Tanning (DECISION #2) `[DATA — ett beslut bort]`

**Vad det gör:**
Omvandlar `raw_hide` → `leather` genom garvning med oak bark + water.

**Implementation:**
- `TanningRecipe` i `world/recipes.py`:
  ```python
  class TanningRecipe(MongooseCraftRecipe):
      name = "leather"
      consumable_tags = ["raw_hide", "oak_bark"]  # + water (DECISION #6)
      output_prototypes = ["leather"]
      tool_tag = None  # hand-craft, optional vessel
      craft_cooldown = 60  # lång process
  ```
- `leather`-material i registry
- `oak_bark`-material + recipe (oak_wood + knife)
- DECISION #6: behövs `water`-material eller räcker det att vara vid vattenkälla?

**Exempel på items som låses upp:**
- Leather armour (soft/hard)
- Boots, shoes, gloves
- Sacks, backpacks, saddlebags
- Saddles, bridles, harnesses
- Leather straps, bindings

**Beroenden:** Wood gathering (oak_bark), raw_hide (från creature harvest).

**Prioritet:** KRITISK — raw_hide har ingen sink utan detta.

**Status:** BLOCKAD på DECISION #2 (soft hand-craft vs vat/station).

---

## SYSTEM 5: Charcoal Burning `[BLOCKED — behöver kiln]`

**Vad det gör:**
Omvandlar `wood` → `charcoal` via en kolningsprocess (pyrolys).

**Implementation:**
- `CharcoalKiln` station typeclass (eller `Kiln` generisk)
- `CharcoalRecipe`:
  ```python
  class CharcoalRecipe(MongooseCraftRecipe):
      name = "charcoal"
      consumable_tags = ["wood", "wood", "wood"]  # 3 wood per charcoal
      output_prototypes = ["charcoal"]
      tool_tag = None
      craft_cooldown = 120  # lång process
      requires_station = "charcoal_kiln"  # eller liknande
  ```
- `charcoal`-material i registry
- `charcoal_kiln`-prototyp (station)

**Exempel på items som låses upp:**
- Bränsle för smelting (krävs för metall)
- Black powder ingredient (charcoal + sulfur + saltpeter)
- Teckning, pigment, filter

**Beroenden:** Wood gathering, kiln station typeclass.

**Prioritet:** HÖG — behövs för smelting.

---

## SYSTEM 6: Smelting `[BLOCKED — behöver furnace + process]`

**Vad det gör:**
Omvandlar `iron_ore` → `iron_ingot` (och copper/tin → bronze) via smältning.

**Implementation:**
- `Furnace` station typeclass (bloomery/furnace)
- `SmeltingRecipe`-subclasses:
  ```python
  class IronSmeltingRecipe(MongooseCraftRecipe):
      name = "iron ingot"
      consumable_tags = ["iron_ore", "charcoal"]  # malm + bränsle
      output_prototypes = ["iron_ingot"]
      tool_tag = None
      craft_cooldown = 90
      requires_station = "furnace"
  ```
- Material: `iron_ingot`, `copper_ingot`, `tin_ingot`, `bronze_ingot`
- Eventuellt: `slag` (biprodukt)
- Eventuellt: `bloom` (opornt järn) som behöver further processing

**Exempel på items som låses upp:**
- Alla metallföremål (efter smithing)
- Ingots kan lagras/handlas
- Bronze (copper + tin smält tillsammans)

**Beroenden:** Ore gathering, charcoal burning, furnace station.

**Prioritet:** KRITISK — hela metallgrenen börjar här.

---

## SYSTEM 7: Smithing `[BLOCKED — behöver forge + anvil + process]`

**Vad det gör:**
Smider `iron_ingot`/`steel_ingot` → verktyg, vapen, rustningar, fittings.

**Implementation:**
- `Forge` station typeclass (esse)
- `Anvil` tool/station (crafting_tool eller station)
- `Hammer` tool (crafting_tool)
- `SmithingRecipe`-subclasses för varje item:
  ```python
  class IronDaggerRecipe(MongooseCraftRecipe):
      name = "iron dagger"
      consumable_tags = ["iron_ingot"]
      output_prototypes = ["iron_dagger"]
      tool_tag = "hammer"  # + anvil som station
      craft_cooldown = 60
      requires_station = "forge"
  ```
- Material: `iron_ingot` → items
- Verktyg: `hammer`, `anvil`, `tongs`, `chisel`
- Eventuellt: `smithing_skill` (advanced skill)

**Exempel på items som låses upp:**
- Alla metallvapen (dagger, sword, axe, mace, spear tip)
- Metallrustningar (ringmail, scalemail, chainmail, plate)
- Verktyg (hammer, saw, chisel, knife blade)
- Fittings (nails, hinges, buckles, horseshoes)
- Metal containers (pot, cauldron)

**Beroenden:** Smelting (ingots), forge + anvil stations, hammer tool.

**Prioritet:** KRITISK — låser upp vapen, rustningar, verktyg.

---

## SYSTEM 8: Steelmaking `[BLOCKED — behöver refining process]`

**Vad det gör:**
Förädlar `iron_ingot` → `steel_ingot` genom att tillsätta kol (carbon) och smida.

**Implementation:**
- `SteelmakingRecipe`:
  ```python
  class SteelRecipe(MongooseCraftRecipe):
      name = "steel ingot"
      consumable_tags = ["iron_ingot", "charcoal"]  # iron + carbon
      output_prototypes = ["steel_ingot"]
      tool_tag = "hammer"
      craft_cooldown = 120  # längre än iron
      requires_station = "forge"
  ```
- `steel_ingot`-material i registry
- Eventuellt: `crucible`-station för högre kvalitet
- Eventuellt: quality tiers (wrought iron → steel → Damascus)

**Exempel på items som låses upp:**
- Steel weapons (skarpare, starkare än iron)
- Steel armour (högre AP/HP)
- Steel tools (mer hållbara)
- Advanced items (rapier, longsword, plate armour)

**Beroenden:** Smelting (iron_ingot), smithing (forge + hammer), charcoal.

**Prioritet:** MED — steel är "endgame" för vapen/rustningar.

---

## SYSTEM 9: Glassblowing `[BLOCKED — behöver furnace + process]`

**Vad det gör:**
Smälter `sand` + `soda_ash` → `glass` items via glassblåsning.

**Implementation:**
- `GlassFurnace` station typeclass (högre temp än smelting)
- `GlassblowingRecipe`-subclasses:
  ```python
  class GlassBottleRecipe(MongooseCraftRecipe):
      name = "glass bottle"
      consumable_tags = ["sand", "soda_ash"]
      output_prototypes = ["glass_bottle"]
      tool_tag = "blowpipe"  # special tool
      craft_cooldown = 45
      requires_station = "glass_furnace"
  ```
- Material: `glass`, `soda_ash` (från plant_ash)
- Verktyg: `blowpipe`, `glassblowing_jacks`
- Eventuellt: `glassblowing_skill` (advanced)

**Exempel på items som låses upp:**
- Flaskor, burkar, vials
- Lantern mantles
- Hourglass
- Sighting lens, magnifying glass
- Window glass (byggnader)
- Alchemy apparatus (alembics, retorts)

**Beroenden:** Sand gathering, soda_ash production, glass furnace station.

**Prioritet:** MED — behövs för alchemy, lanterns, bottles.

---

## SYSTEM 10: Pottery/Kiln `[BLOCKED — behöver kiln station]`

**Vad det gör:**
Bränner `clay` → `pottery` items via en keramikugn.

**Implementation:**
- `Kiln` station typeclass (kan vara samma som charcoal kiln med lägre temp?)
- `PotteryRecipe`-subclasses:
  ```python
  class ClayPotRecipe(MongooseCraftRecipe):
      name = "clay pot"
      consumable_tags = ["clay"]
      output_prototypes = ["clay_pot"]
      tool_tag = None  # hand-formed
      craft_cooldown = 30
      requires_station = "kiln"
  ```
- Material: `clay` (raw) → `pottery` (fired)
- Eventuellt: `pottery_wheel` tool (ger +20 bonus)
- Eventuellt: `glaze`-material för waterproofing

**Exempel på items som låses upp:**
- Krukor, skålar, koppar
- Lagringskärl (jars, jugs)
- Crucibles (för alchemy/smelting)
- Tegostenar (byggnad)
- Lera ammunition (sling bullets)

**Beroenden:** Clay gathering, kiln station.

**Prioritet:** HÖG — behövs för lagring, alchemy, smelting (crucibles).

---

## SYSTEM 11: Carpentry `[BLOCKED — behöver saw + tools]`

**Vad det gör:**
Sågning och bearbetning av `wood` → planks, frames, furniture.

**Implementation:**
- `Saw` tool (crafting_tool, kräver smithing för att skapa)
- `CarpentryRecipe`-subclasses:
  ```python
  class WoodenPlankRecipe(MongooseCraftRecipe):
      name = "wooden plank"
      consumable_tags = ["wood"]
      output_prototypes = ["wooden_plank"]
      tool_tag = "saw"
      craft_cooldown = 20
  ```
- Material: `wood` → `wooden_plank`, `wooden_beam`
- Verktyg: `saw`, `chisel`, `plane`, `mallet`
- Eventuellt: `carpentry_skill` (advanced)

**Exempel på items som låses upp:**
- Planks, beams (byggnad)
- Furniture (stolar, bord, sängar)
- Doors, window frames
- Cart/chariot frames
- Ship hulls (med shipbuilding)
- Shields (wooden core)

**Beroenden:** Wood gathering, saw tool (från smithing).

**Prioritet:** MED — behövs för fordon, skepp, möbler.

---

## SYSTEM 12: Sericulture `[BLOCKED — behöver lifecycle + reeling]`

**Vad det gör:**
Odlar silkesmaskar på mullbärsträd, skördar cocoons, reeler silk thread.

**Implementation:**
- `MulberryTree` ResourceNode
- `Silkworm` Creature typeclass (livscykel: egg → larva → cocoon → moth)
- `SilkwormCocoon` harvest product
- `SilkReelingRecipe`:
  ```python
  class SilkReelingRecipe(MongooseCraftRecipe):
      name = "silk thread"
      consumable_tags = ["silkworm_cocoon", "silkworm_cocoon"]
      output_prototypes = ["silk_thread"]
      tool_tag = "reeling_frame"  # station/tool
      craft_cooldown = 60
  ```
- Material: `silk_thread` → `silk_cloth` (via weaving)
- Eventuellt: `reeling_frame` station

**Exempel på items som låses upp:**
- Silk cloth (lyxtyg)
- Silk rope (starkare än hemp)
- Fine clothing (noble garments)
- Intruder's catsuit
- Elven silk armour (alternate material)

**Beroenden:** Mulberry tree, silkworm lifecycle, reeling process.

**Prioritet:** LÅG — lyxmaterial, inte kritiskt för core gameplay.

---

## SYSTEM 13: Alchemy `[BLOCKED — behöver laboratory + system]`

**Vad det gör:**
Kemiska processer: extraktion, destillation, transmutation, gifttillverkning.

**Implementation:**
- `AlchemyLab` station typeclass (eller suite av stations)
- `AlchemySkill` (advanced skill, Lore-baserad)
- `AlchemyRecipe`-subclasses:
  ```python
  class AcidRecipe(MongooseCraftRecipe):
      name = "acid (vitriol)"
      consumable_tags = ["vitriol", "water"]
      output_prototypes = ["acid_vial"]
      tool_tag = "alembic"  # station
      craft_cooldown = 120  # lång process
      requires_station = "alchemy_lab"
  ```
- Material: `vitriol`, `aqua_fortis`, `philosophers_stone` (endgame)
- Stations: `furnace`, `alembic`, `retort`, `crucible` (från pottery/glassblowing)
- Processer: distillation, sublimation, calcination

**Exempel på items som låses upp:**
- Acid vial
- Poisons + antidotes
- Medicines (healing draughts)
- Black powder (om inte separat system)
- Philosopher's Stone (endgame item)
- Alchemical weapons (Greek fire, smoke bombs)

**Beroenden:** Glassblowing (apparatus), pottery (crucibles), många material.

**Prioritet:** LÅG — endgame content, komplext system.

---

## SYSTEM 14: Shipbuilding `[BLOCKED — behöver shipyard + massive resources]`

**Vad det gör:**
Bygger fartyg (raft → canoe → rowboat → ship) via skeppsvarv.

**Implementation:**
- `Shipyard` station typeclass (stor station, kräver yta)
- `ShipwrightSkill` (advanced skill)
- `ShipbuildingRecipe`-subclasses:
  ```python
  class RowboatRecipe(MongooseCraftRecipe):
      name = "rowboat"
      consumable_tags = ["wooden_plank", "wooden_plank", "wooden_plank", ...]  # många
      output_prototypes = ["rowboat"]
      tool_tag = "saw"
      craft_cooldown = 300  # mycket lång process
      requires_station = "shipyard"
  ```
- Material: massiva mängder `wooden_plank`, `nails`, `pitch`, `cloth` (segel), `rope`
- Eventuellt: ship components (hull, mast, rudder, sails) som monteras
- Eventuellt: ship quality/sizing (tonnage, crew capacity)

**Exempel på items som låses upp:**
- Raft (basic, redan DATA)
- Canoe (hide/dugout)
- Rowboat
- Fishing boat
- Trading ships (cog, carrack)
- Warships (longship, galleon)

**Beroenden:** Carpentry (planks), smithing (nails, fittings), cloth (sails), rope.

**Prioritet:** LÅG — endgame content, massive resource investment.

---

## BYGGORDNING (rekommenderad)

```
FAS 1: GRUNDERNA (kan byggas parallellt, inga beroenden)
├─ 1. Wood gathering
├─ 2. Stone/clay/sand/mineral gathering
└─ 3. Ore gathering

FAS 2: MJUKA HANTVERKEN (beroende på FAS 1)
├─ 4. Tanning (DECISION #2) ← raw_hide sink
├─ 5. Charcoal burning ← wood + kiln station
└─ 10. Pottery/Kiln ← clay + kiln station

FAS 3: METALL (beroende på FAS 2)
├─ 6. Smelting ← ore + charcoal + furnace
├─ 7. Smithing ← ingots + forge + anvil
└─ 8. Steelmaking ← iron + charcoal + forge

FAS 4: AVANCERAT (beroende på FAS 3)
├─ 9. Glassblowing ← sand + furnace
├─ 11. Carpentry ← wood + saw (från smithing)
└─ 13. Alchemy ← glass apparatus + pottery crucibles

FAS 5: SPECIALISERAT (beroende på FAS 4)
├─ 12. Sericulture ← mulberry + silkworm lifecycle
└─ 14. Shipbuilding ← carpentry + smithing + massive resources
```

---

## IMPLEMENTATIONSPRIORITERING

**Omedelbart (data-only, inga nya typeclasses):**
1. Wood/stone/ore gathering (ResourceNodes + materials)
2. Tanning (DECISION #2 → recipe)
3. Charcoal/pottery (kräver kiln station typeclass)

**Kort sikt (nya typeclasses, men enkla):**
4. Smelting (furnace station + recipes)
5. Smithing (forge + anvil + recipes)

**Medellång sikt (komplexa system):**
6. Steelmaking (refining process)
7. Glassblowing (furnace + tools)
8. Carpentry (tools + recipes)

**Lång sikt (stora system):**
9. Alchemy (lab + många processer)
10. Sericulture (creature lifecycle)
11. Shipbuilding (massivt resource system)

---

## ESTIMERAD ARBETSMÄNGD

| System | Typclasses | Recipes | Materials | Svårighet |
|---|---|---|---|---|
| 1. Wood | 3 nodes | 0 | 1 | LÄTT |
| 2. Stone/mineral | 7 nodes | 0 | 7 | LÄTT |
| 3. Ore | 3 nodes | 0 | 3 | LÄTT |
| 4. Tanning | 0 | 2 | 2 | LÄTT (efter DECISION) |
| 5. Charcoal | 1 station | 1 | 1 | MED |
| 6. Smelting | 1 station | 3 | 4 | MED |
| 7. Smithing | 2 stations | 20+ | 2 | SVÅR |
| 8. Steelmaking | 0 | 1 | 1 | MED |
| 9. Glassblowing | 1 station | 5 | 3 | SVÅR |
| 10. Pottery | 1 station | 5 | 2 | MED |
| 11. Carpentry | 0 | 5 | 2 | MED |
| 12. Sericulture | 2 typeclasses | 2 | 3 | SVÅR |
| 13. Alchemy | 1 station | 10+ | 10+ | MYCKET SVÅR |
| 14. Shipbuilding | 1 station | 5 | 5 | MYCKET SVÅR |

**Totalt:** ~20 nya typeclasses, ~60 recipes, ~45 materials

---

## FLAG: Design decisions needed

**DECISION #2:** Tanning — soft hand-craft (cold soak) eller vat/station?
**DECISION #6:** Water — material eller "near water source" requirement?
**DECISION #7:** Kiln — shared station (charcoal + pottery) eller separate?
**DECISION #8:** Furnace — shared station (smelting + glass) eller separate?
**DECISION #9:** Smithing — forge + anvil som stations eller tools?
