# PolishedWorld — Crafting Progression & Tools Decomposition

> **Rev 5 · 2026-07-10** — Component D **complete & in-game-verified**. D.4 (repair convergence): `CmdRepair` gate broadened `ClothingWithBuffs` → `DurableObject` (tools + garments); materials data-driven via `target.db.repair_materials or REPAIR_MATERIALS` (`stone_knife` → stick+fibre, `bone_needle` → bone; garments keep cloth+twine); copy neutralised to mend/restore. D.5: `STONE_KNIFE` condition 40, `BONE_NEEDLE` 30 — and the §10.1 prototype-key-vs-autocreate override is now **verified** (spawn → 40/30, prototype value wins). The source→sink→repair loop is closed end-to-end. Next: Component E (quality → capability).
> **Rev 4 · 2026-07-10** — Component D (tool wear sink) underway: §9 reconciled and split D.1→D.5. D.1 (per-use wear read from `self.inputs`, not `validated_tools`), D.2 (broken tool = absent/improvised, **not** deleted — supersedes Rev 3's `delete()`), and D.3 (colour-banded `condition_line` shown on `look` for tools *and* garments) complete & in-game-verified. D.4 (repair convergence — `CmdRepair` broadened to `DurableObject`, data-driven `db.repair_materials`) and D.5 (bootstrap start-condition tuning + prototype-override verify) remain. Tool-repair promoted from §13 backlog into D.4.
> **Rev 3 · 2026-07-10** — Component C (Tool bootstrap) complete & in-game-verified: `typeclasses/tools.py::Tool(DurableObject, Object)` (condition=100 free via MRO-walk); `stone`/`stick` primitives + `stone_outcrop`/`stick_deadfall` nodes; `StoneKnifeRecipe` (`["stone","stick","fiber"]` → distinct `stone_knife`, `tool_tag=None`); `bone` part in the rabbit harvest-template (`skill=craft`, `difficulty=0`, `yield_divisor=4`, `max_stage=SKELETON`) + `BONE` primitive; `BoneNeedleRecipe` (`["bone"]` → distinct `bone_needle`, `tool_tag=None`). Zero-to-tool loop playtested both ways (forage→stone knife, hunt→bone→bone needle). Locked distinct bootstrap-tool prototypes (not reused `knife`/`needle`) + raw-fibre binding. Verified live: `_tool_modifier` returns 0 for `tool_tag=None` before the penalty path; base has no `min_skill` (Component F adds it); `CmdHarvest` iterates template parts dynamically. Next: Component D (tool wear sink), fresh chat.
> **Rev 2 · 2026-07-10** — Component A (tool-modifier flip) and Component B (shared durability) complete: `typeclasses/durable.py::DurableObject` (condition/apply_wear/is_broken/condition_line) landed; `ClothingWithBuffs(DurableObject, ContribClothing)` inherits it. Alt A locked — `condition_line()` is helper/examine-only, no player-`look` injection until wear is live (Component D). Corrected the B.1 test hint (below). Next: Component C (Tool bootstrap), fresh chat.
> **Rev 1 · 2026-07-10** — first version header. Decomposes roadmap Stage 2 (Crafting progression & tools) into two threads (skill→capability, tools) plus a bootstrap chain. Locks D1–D4 this session: shared quality-band helper (superior = crit-tier), hybrid skill-gate, shared `condition` durability axis across clothing+tools, and corrected tool-modifier semantics (present=baseline / absent=penalty) with primitive stone/stick tools as bootstrap. Flags two source discrepancies: waterskin's dead `>=125` branch and the `condition` vs `durability` naming split.
> **Canonical:** `docs/PolishedWorld_Crafting_Progression_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If this project-knowledge copy's Rev is lower than the repo's, it's stale — re-upload from the repo.

**Feature branch:** `feature/crafting-progression`
**Status:** Components A, B, C, D complete & in-game-verified on `feature/crafting-progression`; E (quality → capability) is next.
**Philosophy:** skynda långsamt — korrigera verktygssemantiken och lägg den gemensamma `condition`-axeln innan primitiva verktyg och kvalitet byggs ovanpå.

---

## 1. Varför den här featuren

Stage 1 gjorde skill-siffrorna *läsbara* (tick-feedback, desc-tier, `progress`). Stage 2 gör dem **kännbara**. Roadmap §"Stage 2" delar detta i två trådar:

- **Skill → capability:** skill-gate:a högre recept + skala output-kvalitet med craft-utfallet (fumble/success/critical-tiern som `world/skillcheck.py` redan resolvar). Rider rakt på improvement-lagret.
- **Tools:** verktyg måste vara spelar-craftade (ingen implicit NPC-källa, pillar 1). De designas som kvalitets-/effektivitets-**modifierare, inte hårda grindar**, och får en **durability/wear-sink** som skapar återkommande ekonomisk efterfrågan.

Plus en tredje, praktisk tråd som de två ovan förutsätter men roadmapen bara antyder:

- **Bootstrap:** för att undvika chicken-and-egg (första verktyget kan inte kräva ett verktyg) craftas **primitiva verktyg av gatherade primitiver (sten, pinne, ev. ben) helt utan verktyg** (`tool_tag=None`). Detta lägger den nedersta pinnen i verktygsstegen.

De tre ortogonala gate:sen hålls åtskilda (roadmap-konvention): **knowledge** = Stage 3, **skill** = Stage 1 + denna stages quality-skalning/skill-gate, **capability** = denna stages verktyg.

---

## 2. Designbeslut låsta den här sessionen

**D1 — Kvalitet → capability via en delad band-helper.**
Kvalitets-*stämplingen* finns redan (`MongooseCraftRecipe.QUALITY_BY_TIER`, `_quality_for`, `obj.db.quality`, den tomma `_finalize_item`-hooken). Det som saknas är att band-logiken är en sanningskälla i stället för magiska tal per recept. En ny modul `world/crafting_quality.py` äger `quality_band(quality) -> "shoddy"|"poor"|"serviceable"|"superior"`, där **superior = quality > 100** (dvs. critical-tiern; `crit_score` skalar *inom* superior-bandet). Recept läser band, aldrig råa tal. `_finalize_item` sätter concrete stats per band och, vid superior, ett distinguerande alias `a superior <key>` (matar disambiguation-fixen gratis).

**D2 — Hybrid skill-gate.**
`min_skill` (default 0 = ogated) på `MongooseCraftRecipe`. Endast **avancerade** recept sätter en tröskel; triviala survival-recept (twine, cloth) förblir ogated så bootstrap-loopen aldrig låses. Gaten enforce:as i `pre_craft` (raise `CraftingError` **före** consume) med tydligt meddelande. Håll ortogonal mot Stage 3:s knowledge-gate: skill-gaten säger "du *kan* men är för dålig", knowledge-gaten säger "du känner inte till receptet".

**D3 — Gemensam durability-sink på en `condition`-axel.**
Standardisera på **`condition` (0–100)** som den enda wear-axeln, via en delad `DurableObject`-mixin (`condition`, `apply_wear(amount)`, `is_broken`, enhetlig examine-rad). Både `ClothingWithBuffs` (refaktoreras) och en ny `Tool`-typeclass ärver den. Verktyg nöts **per-use** i receptet; brutet verktyg (condition 0) raderas. Wear-*triggern* skiljer per typ (garment: tid/bärande via framtida script; tool: per craft), men axeln, vokabulären och reparationen delas.
*Utanför scope (backlog):* waterskinens `durability` är en refill-livslängd, inte en reparerbar 0–100-condition — migreras inte nu. `repair` generaliseras till verktyg (andra reparationsmaterial) som separat task, inte bakat i första wear-tasken.

**D4 — Korrigerad verktygsmodifierare + primitiv bootstrap.**
Nuvarande `+20 med / −20 utan` ger *bonus* för att ha exakt det receptet förutsätter, och avviker från Legend RAW (improviserade verktyg = penalty, korrekta = normalt). Ny semantik för recept med `tool_tag` satt: **verktyg present → 0 (baseline), frånvarande/brutet → `improvised_penalty`** (default −20, RAW −40). Enda vägen *över* baseline blir ett **superior** verktyg (G), vilket gör craftade superior-verktyg eftertraktade. Ändringen rör **två call-sites** (recept-basen + `CmdRepair`) som flippas ihop. Bootstrap: primitiva `Tool`-recept med `tool_tag=None`, matade av nya gatherbara primitiver.

---

## 3. Verifierade källankare (source-first)

Hämtade och lästa mot `main` denna session (raw.githubusercontent.com/G0dlet/PolishedWorld/main/…):

- `world/crafting_base.py` — `MongooseCraftRecipe`: `_tool_modifier` (`tool_bonus=20`/`improvised_penalty=-20`, itererar `self.inputs`), `_quality_for` (critical → `+crit_score`), `_finalize_item` (tom hook, avsedd för quality→stats), `do_craft` stämplar `obj.db.quality`/`crafted_by`, livscykel `pre_craft`(cooldown-gate)→`do_craft`→`post_craft`(consume). `QUALITY_BY_TIER = {critical:100, success:100, failure:50, fumble:25}`.
- `world/skillcheck.py` — `skill_check(skill, mod)` returnerar `result`/`success`/`roll`/`target`/`margin`/`crit_score` (`crit_score = max(0, target//10)`). Tiers: critical/success/failure/fumble.
- `world/recipes.py` — sju recept subklassar basen. `WaterskinRecipe._finalize_item` mappar quality→`max_charges`/`durability`. `LinenShirtRecipe`/`LeatherBootsRecipe` har medvetet *inget* `_finalize_item` (quality inert). Registreras via `CRAFT_RECIPE_MODULES = ["world.recipes"]` (singular).
- `world/prototypes.py` — `KNIFE`/`NEEDLE` (`objects.Object`, taggar `knife`/`needle` i `crafting_tool`); garment-prototyper på `ClothingWithBuffs` (`warmth`, `clothing_type`). Inga sten/pinne/ben-prototyper finns idag.
- `typeclasses/clothing.py` — `ClothingWithBuffs`: `condition = AttributeProperty(default=100, autocreate=True)`; `wear`/`remove` recompute:ar thermal.
- `commands/repair_commands.py` — `CmdRepair` är `isinstance(ClothingWithBuffs)`-låst, läser/skriver `db.condition`, egen `_tool_modifier` med **samma** `+20/−20` (`NEEDLE_BONUS`/`IMPROVISED_PENALTY`).
- `world/thermal.py` — `worn_warmth` skalar `warmth * condition/100`; garment utan condition defaultar 100.
- `evennia/contrib/game_systems/crafting/crafting.py` (Evennia `main`) — kontrakt bekräftat: `tool_tag_category="crafting_tool"`, `consumable_tag_category="crafting_material"`, `exact_tools=True` (vår bas → `False`), `validated_tools`/`validated_consumables` populeras i `pre_craft`, verktyg identifieras före consumables.

**Diskrepanser att fixa i denna stage:**

1. **Waterskinens `>=125`-gren är död kod.** Med MVP:s skill-cap 100 är max `target` = 100 + tool 20 = 120 → `crit_score = 12` → max quality = **112**. Tröskeln 125 nås aldrig. Fixas i E via band-helpern (superior = quality > 100).
2. **Namn-gaffel `condition` vs `durability`.** Clothing/repair/thermal använder `condition` (0–100, lastbärande på tre ställen); waterskin använder `durability` (refill-count). D3 standardiserar på `condition`; waterskins `durability` lämnas som backlog-avvikare.

---

## 4. Beroendegraf

```
A (tool-modifier flip)      B (DurableObject-mixin)
        \                        /
         \                      /
          C (Tool + primitiva verktyg + gatherbara primitiver)   [BOOTSTRAP — speltestbar loop]
                     |
          D (per-use wear-sink; brutet verktyg = frånvarande)
                     |
   E (quality→garments via band-helper; fixar waterskin)
                     |
          F (skill-gate på avancerade recept)
                     |
          G (superior-tool skalar modifieraren — knyter ihop trådarna)
```

- **A** och **B** är oberoende av varandra; båda krävs före **C**.
- **A** före **C** så primitiva verktyg byggs på slutgiltig modifier-semantik (ingen churn).
- **B** före **C** så `Tool` föds med `condition` (ingen re-refaktor).
- **E/F** (skill→capability-tråden) kräver bara att recept-basen är stabil (efter A); de är oberoende av wear-sinken (D) men läggs efter bootstrap per ordningsvalet.
- **G** kräver både en `Tool` med kvalitet (C/E) och den flippade modifieraren (A).

---

## 5. Sessionsplan

3–5 tasks/session, en komponent per chatt för ren kontext. Föreslagen indelning:

- **Session 1:** A.1–A.2 (flip, båda call-sites) + B.1–B.2 (mixin + clothing-refaktor). Låg risk, låser foundations.
- **Session 2:** C.1–C.4 (Tool-typeclass, gatherbara primitiver + nodes, stenkniv, benål) → **speltesta hela noll-till-verktyg-loopen**.
- **Session 3:** D.1 (wear-sink) + E.1–E.3 (band-helper, waterskin-fix, garment-quality).
- **Session 4:** F.1–F.2 (skill-gate) + G.1 (superior-tool-skalning).

Ordningsval (delegerat denna session): bootstrap (C) ligger så tidigt som beroendegrafen tillåter — direkt efter de två foundations den kräver — så att verktygsloopen kan valideras från noll innan wear/kvalitet-djup läggs på.

---

## 6. Component A — Tool-modifier correction (D4)

Flippa verktygsmodifieraren till RAW-nära semantik på båda call-sites. Måste landa ihop så de inte divergerar.

### Task A.1 — Flip `MongooseCraftRecipe._tool_modifier`
- **Goal:** Verktyg som receptet förutsätter ger baseline (0), inte bonus; frånvaro ger penalty.
- **Dependencies:** `world/crafting_base.py` (`_tool_modifier`, `tool_bonus`, `improvised_penalty`).
- **Implementation:** I `_tool_modifier`: om `not self.tool_tag` → `0`; om verktyg finns bland `self.inputs` (befintlig tag-check) → `0`; annars → `self.improvised_penalty`. Retirera den flata `tool_bonus`-returen (bonusen återinförs superior-only i G; behåll attributet men oanvänt eller flytta kommentaren dit). Uppdatera basens docstring/kommentarer så "+20 om verktyg" inte längre står.
- **Testing:** `@py` spawna knife + material, kör ett waterskin-craft med och utan kniv; verifiera att `skill_outcome["target"]` = skill+0 med kniv och skill−20 utan (via `self.crafter.msg`-flöde eller en direkt `MongooseCraftRecipe(...)`-instansiering i `evennia shell`).
- **Commit:** `refactor(crafting): tool present is baseline (0), absence is the penalty`

### Task A.2 — Mirror the flip in `CmdRepair`
- **Goal:** Reparation använder samma verktygssemantik som recept.
- **Dependencies:** A.1, `commands/repair_commands.py` (`_tool_modifier`, `NEEDLE_BONUS`, `IMPROVISED_PENALTY`).
- **Implementation:** `_tool_modifier` returnerar `0` när needle bärs (istf `NEEDLE_BONUS`), annars `IMPROVISED_PENALTY`. Byt `NEEDLE_BONUS`-konstanten mot en kommentar om att baseline är 0 (eller sätt `NEEDLE_BONUS = 0` med förklarande kommentar; behåll namnet för G).
- **Testing:** `@py` slit en garment till condition 50, `repair` med och utan needle; jämför utfallsfrekvens/`target` i två körningar (needle → högre target).
- **Commit:** `refactor(repair): align tool modifier with crafting (needle = baseline, not bonus)`

---

## 7. Component B — Shared durability foundation (D3)

En sanningskälla för wear-axeln, som både clothing och tools ärver.

### Task B.1 — `DurableObject`-mixin
- **Goal:** En mixin som äger `condition` (0–100), `apply_wear`, `is_broken` och en enhetlig examine-rad.
- **Dependencies:** `evennia.AttributeProperty`; ny modul `typeclasses/durable.py`.
- **Implementation:** `class DurableObject:` med `condition = AttributeProperty(default=100, autocreate=True)`; `apply_wear(self, amount)` → `self.condition = max(0, self.condition - amount)`, returnera nya värdet, logga vid brott; `is_broken` property (`self.condition <= 0`); en `get_display_name`/`return_appearance`-hook eller hjälpmetod `condition_line()` som ger t.ex. `Condition: 72%`. Ingen wear-*trigger* här (den bor i clothing-scriptet resp. receptet).
- **Testing:** en *importerbar* host krävs — en shell/`exec`-definierad subklass faller tyst till `DefaultObject` (§11.17), så `create_object(cls)` misslyckas dolt. Scratch-modul `typeclasses/_scratch.py` (`class DurableScratch(DurableObject, DefaultObject): pass`; radera efteråt, committa aldrig), sedan `evennia shell`: `from evennia import create_object; o = create_object("typeclasses._scratch.DurableScratch", key="t"); print(o.condition, o.apply_wear(30), o.is_broken, o.apply_wear(80), o.is_broken, o.condition_line()); o.delete()` → `100 70 False 0 True Condition: 0%`. (apply_wear/is_broken landar även funktionellt i B.2 via en spawnad garment-host.)
- **Commit:** `feat(durability): add DurableObject mixin (condition, apply_wear, is_broken)`

### Task B.2 — Refaktorera `ClothingWithBuffs` onto the mixin
- **Goal:** Clothing använder den delade `condition` utan att bryta thermal eller repair.
- **Dependencies:** B.1, `typeclasses/clothing.py`, `world/thermal.py`, `commands/repair_commands.py`.
- **Implementation:** `class ClothingWithBuffs(DurableObject, ContribClothing):` — ta bort den lokala `condition`-AttributeProperty (ärvs nu). Verifiera att `thermal.worn_warmth` (`warmth * condition/100`) och `CmdRepair` (läser/skriver `db.condition`) fungerar oförändrat; MRO ska ge `DurableObject.condition` företräde. Behåll `wear`/`remove` thermal-recompute.
- **Testing:** `@py` spawna en `fur_cloak`, `examine` visar condition-raden; `apply_thermal_stress` efter `apply_wear(50)` → halverad effektiv warmth; `repair` fungerar som förr (regressionskoll mot befintligt beteende).
- **Commit:** `refactor(clothing): inherit condition from DurableObject mixin`

---

## 8. Component C — Tool bootstrap (D4) ✅   ← BOOTSTRAP  *(complete & in-game-verified)*

Ny `Tool`-typeclass född med condition, nya gatherbara primitiver, och primitiva verktygsrecept utan verktygskrav. Efter denna komponent är hela noll-till-verktyg-loopen speltestbar.

### Task C.1 — `Tool(DurableObject)`-typeclass + retagga KNIFE/NEEDLE
- **Goal:** Verktyg är durable objekt (föds med condition) istället för nakna `objects.Object`.
- **Dependencies:** B.1; `world/prototypes.py`; ny modul `typeclasses/tools.py`.
- **Implementation:** `class Tool(DurableObject, Object):` (tunn; ärver `condition`/`apply_wear`/`is_broken`). Peka `KNIFE`/`NEEDLE`-prototypernas `typeclass` på `typeclasses.tools.Tool`. Befintliga redan-spawnade verktyg behåller sin gamla typeclass tills omspawnade — notera i dev-världen.
- **Testing:** `@py` `spawn("KNIFE")` → `examine` visar condition; `obj.is_broken` False.
- **Commit:** `feat(tools): add Tool typeclass and retag knife/needle prototypes`

### Task C.2 — Gatherbara primitiver (sten, pinne) + resource-nodes
- **Goal:** Råmaterial för primitiva verktyg finns att samla i världen (noll beroende på jakt).
- **Dependencies:** `world/prototypes.py` (`ResourceNode`-mönstret, jfr `FIBER_PLANT`).
- **Implementation:** Prototyper `STONE` (tag `stone`/`crafting_material`) och `STICK` (tag `stick`/`crafting_material`); resource-nodes `STONE_SCREE`/`STICK_THICKET` (eller motsvarande) med `yield_prototype` pekande på dem. Följ regen-interval-mönstret från befintliga noder.
- **Testing:** `@py` spawna noden, `forage` (eller motsvarande gather-kommando) → få sten/pinne med rätt tagg.
- **Commit:** `feat(resources): add stone and stick gatherable primitives with nodes`

### Task C.3 — `StoneKnifeRecipe` (zero-dep bootstrap)
- **Goal:** Crafta en stenkniv av sten + pinne (+ ev. fiber-bindning) **utan verktyg**.
- **Dependencies:** C.1, C.2, `MongooseCraftRecipe`, `CRAFT_RECIPE_MODULES`.
- **Implementation:** `class StoneKnifeRecipe(MongooseCraftRecipe)` i `world/recipes.py`: `consumable_tags=["stone","stick"]` (ev. `+["fiber"]`), `output_prototypes=["knife"]` (eller en distinkt `stone_knife`-prototyp med lägre start-`condition`), `tool_tag=None` (inget verktyg → ingen penalty), lämplig `craft_cooldown`. Ingen `min_skill` (ogated bootstrap).
- **Testing:** Ny karaktär (låg craft), gather sten+pinne, `craft stone knife` → får en `Tool` med condition; verifiera att den fungerar som `knife`-verktyg i ett waterskin-craft (baseline 0, inte penalty).
- **Shipped:** distinct `stone_knife` prototype (`typeclasses.tools.Tool`, tag `("knife","crafting_tool")`, start `condition`=100 — start-tuning deferred to D.5); `consumable_tags=["stone","stick","fiber"]` (raw-fibre binding, not twine); `craft_cooldown=30`. `consume_policy="raw"` → a bad roll still yields a knife.
- **Commit:** `feat(recipes): add stone knife bootstrap recipe (no tool required)`

### Task C.4 — `BoneNeedleRecipe` (harvest-länkad primitiv)
- **Goal:** Crafta en benål av ben (från corpse-harvest) utan verktyg.
- **Dependencies:** C.1, C.3-mönstret; `world/harvest_templates.py` (lägg `bone` i rabbit-templaten) + `BONE`-prototyp.
- **Implementation:** Lägg en `bone`-del i rabbit harvest-templaten + `BONE`-prototyp (tag `bone`/`crafting_material`). `class BoneNeedleRecipe(MongooseCraftRecipe)`: `consumable_tags=["bone"]`, `output_prototypes=["needle"]`, `tool_tag=None`. Notera i doccen att needle-bootstrap därmed förutsätter en jakt (medveten koppling hunting→tools); en jakt-oberoende variant (t.ex. `thorn`/`stick`-nål) är en möjlig framtida additiv källa.
- **Testing:** Jaga → harvest `bone` → `craft bone needle` → verifiera needle-verktyg fungerar i ett garment-craft.
- **Shipped:** distinct `bone_needle` prototype (`typeclasses.tools.Tool`, tag `("needle","crafting_tool")`) — **not** reused `needle` (parity with `stone_knife`; plain `needle` kept as a future bronze/metal target). Rabbit `bone` part: `skill="craft"`, `difficulty=0`, `yield_divisor=4` (SIZ 4 → 1 bone), `max_stage=SKELETON` (harvestable to bare skeleton). `BoneNeedleRecipe`: `consumable_tags=["bone"]`, `tool_tag=None`, `craft_cooldown=30`.
- **Commit:** `feat(recipes): add bone needle recipe (harvest-linked bootstrap)`

---

## 9. Component D — Tool wear sink (D3)

Verktyg nöts per genomförd craft; ett brutet verktyg räknas som frånvarande (improviserad penalty) och **ligger kvar** (aldrig auto-deletat) så det kan repareras. Wear läses från `self.inputs` via `_used_tool()`, inte `validated_tools` (tomt för våra optional-tool-recept — se Evennia_Reference §8.8).

> **Rev-4-reconcile mot Rev 3:** den monolitiska D.1 (wear + break-delete i ett, läsande `validated_tools`) är splittad i D.1–D.5. Tre ändringar: (1) verktyget nås via `self.inputs`/`_used_tool()`, inte `validated_tools`; (2) trasigt verktyg **raderas inte** — behålls för D.4-reparation; (3) tool-repair lyfts från §13 backlog till D.4.

### Task D.1 — Per-use wear i receptet ✅
- **Goal:** Varje genomförd craft nöter det använda verktyget med `tool_wear`.
- **Dependencies:** B.1 (`apply_wear`), C.1 (`Tool`), `world/crafting_base.py` (`do_craft`, `self.inputs`).
- **Implementation:** Klassattr `tool_wear = 5` (överridbar). `_used_tool()`-helper (enda sanningskälla; skannar `self.inputs` för `tool_tag`/`tool_tag_category`) — `_tool_modifier` refaktorerad att läsa den. Wear-anrop i `do_craft` efter `rolled=True` + `cooldowns.add` (bara genomförd craft, aldrig cooldown-abort), hasattr-guardat (`apply_wear`). Fumble-skalning (`tool_wear_on_fumble`) deferrad till balans (§13).
- **Commit:** `feat(crafting): wear the used tool on each completed craft` ✅

### Task D.2 — Broken tool = absent (improvised penalty) ✅
- **Goal:** Ett verktyg nött till `condition 0` går sönder, räknas som frånvarande (→ `improvised_penalty`), meddelar spelaren, och raderas **inte**.
- **Dependencies:** D.1, B.1 (`is_broken`).
- **Implementation:** `_used_tool()` exkluderar `is_broken`-verktyg (`and not getattr(obj, "is_broken", False)`) → `_tool_modifier` faller till penalty *och* wear-sinken hittar inget. Break captureras i `do_craft` (`self.tool_broke`, init i `pre_craft`-reset), emittas i `post_craft` efter improvement-feedback: `"Your {tool} finally gives out and breaks apart."` Ingen `delete()` (reconcile av Rev 3).
- **Commit:** `feat(crafting): broken tools count as absent (improvised penalty)` ✅

### Task D.3 — Condition på `look` (verktyg + plagg) ✅
- **Goal:** `look <tool/garment>` visar en färgbandad condition-rad (vanliga spelare saknar `examine`).
- **Dependencies:** B.1 (`condition_line`), C.1 (`Tool`), ResourceNode-mönstret.
- **Implementation:** `DurableObject.get_display_desc` appendar `condition_line()` via `super()`-MRO (bevarar base: `DefaultObject` för Tool, `ContribClothing` för plagg). Färgband i `condition_line()`: `|g`>66 / `|y`33–66 / `|r`<33 (`_COND_GOOD=66`/`_COND_WORN=33`). Delad på mixin → verktyg **och** plagg ansluter i ett svep (Tool förblir tunn; revokerar B.2:s Alt-A-deferral).
- **Commit:** `feat(durable): show condition on look for tools and garments` ✅

### Task D.4 — Repair-konvergens ✅
- **Goal:** `CmdRepair` reparerar durable-verktyg, inte bara plagg.
- **Dependencies:** D.2 (trasiga verktyg ligger kvar), `commands/repair_commands.py`, `typeclasses/clothing.py` (`ClothingWithBuffs(DurableObject, …)` — bekräftat: `isinstance(target, DurableObject)` fångar båda).
- **Implementation (låst):** grinden `isinstance(garment, ClothingWithBuffs)` → `isinstance(target, DurableObject)`. Material data-drivet: `_collect_materials` läser `target.db.repair_materials or REPAIR_MATERIALS` (plagg default cloth/twine; `stone_knife` → stick+fiber). Generalisera crit/success/fumble-copy bort från "stitching/patch" till neutralt ("mend/restore"). `apply_thermal_stress` bara vid `garment.db.worn` (verktyg saknar → hoppar naturligt). **Split om >90 min:** D.4a (gate + condition-read + neutral copy, interim cloth/twine) / D.4b (data-driven per-tool material).
- **Shipped:** gate `isinstance(target, DurableObject)` (garments + tools); `func` reads `required = target.db.repair_materials or REPAIR_MATERIALS` once and passes to `_collect_materials(caller, required)`; neutral copy (mend/restore/"botch the work"); `apply_thermal_stress` still guarded on `target.db.worn` (tools skip naturally). Prototypes: `STONE_KNIFE.repair_materials=("stick","fiber")`, `BONE_NEEDLE.repair_materials=("bone",)`. `_tool_modifier` left garment-centric (needle) — see §13 backlog. Verified: T1 tier-maths (100/80/50/40), T2 tool-repair stick+fibre 50→80, T3 missing-material bailout (nothing consumed), T4 garment cloth/twine fallback, T5 non-durable refused.
- **Commit:** `feat(repair): allow repairing durable tools, not just garments`

### Task D.5 — Bootstrap start-condition + prototyp-override-verify ✅
- **Goal:** Crude bootstrap-verktyg får kortare livslängd så wear känns; verifiera att prototyp-`condition` overridar autocreate-100.
- **Dependencies:** D.1 (wear live), `world/prototypes.py`.
- **Implementation (låst):** `STONE_KNIFE: condition 40`, `BONE_NEEDLE: 30` (metall `KNIFE`/`NEEDLE` stannar 100). VERIFIERA: spawn → `db.condition == 40` (§8.7/§10.1-corollary, prototyp-vs-autocreate OVERIFIERAD).
- **Shipped & verified:** `STONE_KNIFE: "condition": 40`, `BONE_NEEDLE: "condition": 30` (metal `KNIFE`/`NEEDLE` untouched → autocreate-100). Prototype-key-vs-autocreate ordering **confirmed**: `@reload` + spawn → `db.condition == 40 / 30`, so the prototype top-level key wins over the AttributeProperty default (resolves the §10.1-corollary flag; no `at_object_creation` stamping needed).
- **Commit:** `feat(prototypes): lower bootstrap tool start condition`

---

## 10. Component E — Quality → capability (D1)

En sanningskälla för kvalitetsband; gör Stage 1:s siffror kännbara på output.

### Task E.1 — `world/crafting_quality.py` band-helper
- **Goal:** En pure `quality_band(quality)` som all `_finalize_item`-logik läser.
- **Dependencies:** ingen (ren funktion); används av recepten.
- **Implementation:** `QUALITY_BANDS`-tabell + `quality_band(quality) -> str` med gränser: `superior` (> 100), `serviceable` (100), `poor` (50–99), `shoddy` (< 50). Ev. `band_label`/`band_alias(key, band)` för `a superior <key>`. Ren, unit-testbar.
- **Testing:** `evennia shell`: `quality_band(112)=="superior"`, `quality_band(100)=="serviceable"`, `quality_band(50)=="poor"`, `quality_band(25)=="shoddy"`.
- **Commit:** `feat(crafting): add quality_band helper as single source of quality tiers`

### Task E.2 — Fixa `WaterskinRecipe._finalize_item`
- **Goal:** Waterskinens superior-tier blir nåbar (dödar `>=125`-buggen).
- **Dependencies:** E.1, `world/recipes.py`.
- **Implementation:** Ersätt de råa trösklarna med `quality_band(obj.db.quality)` → sätt `max_charges`/`durability` per band. Superior-bandet (crit) ger nu topp-tiern, som faktiskt nås.
- **Testing:** `@py` tvinga ett critical-utfall (hög skill + `evennia shell`) och verifiera superior-charges; ett vanligt success ger serviceable.
- **Commit:** `fix(recipes): waterskin quality tiers via band helper (superior now reachable)`

### Task E.3 — Garment-quality (`_finalize_item` på plagg)
- **Goal:** Craftade plagg får kännbar quality: bättre band → högre start-`condition`/effektiv warmth; superior → distinguerande alias.
- **Dependencies:** E.1, B.1 (condition), `world/recipes.py` (`LinenShirtRecipe`, `LeatherBootsRecipe`, m.fl.).
- **Implementation:** `_finalize_item` på garment-recepten: mappa `quality_band` → start-`condition` (t.ex. superior 100 / serviceable 90 / poor 70 / shoddy 50) och ev. en liten warmth-justering; vid `superior` sätt `obj.aliases.add("superior <key>")` och/eller prefixa `key`. Läs band, aldrig råa tal.
- **Testing:** `@py` crafta shirt på olika utfall; `examine` visar olika start-condition; superior → `look superior shirt` matchar unikt (disambiguation-vinst).
- **Commit:** `feat(recipes): scale garment quality (condition + superior alias) by craft tier`

---

## 11. Component F — Skill-gate (D2)

Hård tröskel enbart på avancerade recept; ortogonal mot Stage 3:s knowledge-gate.

### Task F.1 — `min_skill`-gate i `pre_craft`
- **Goal:** Recept kan kräva en craft-tröskel; under den avbryts före consume med tydligt meddelande.
- **Dependencies:** `world/crafting_base.py` (`pre_craft`, `_skill_value`, `CraftingError`).
- **Implementation:** Klassattr `min_skill = 0`. I `pre_craft`, efter contrib-validering men **före** cooldown-gaten och consume: om `self._skill_value() < self.min_skill` → `self.msg("Your Craft is too unskilled (need {min_skill}%).")` + `raise CraftingError(...)`. `rolled` förblir False → inget consume.
- **Testing:** `@py` sätt `min_skill` högt på ett testrecept; craft under tröskel → meddelande, inga material förbrukade; höj skill → craft går igenom.
- **Commit:** `feat(crafting): add min_skill gate enforced before consume`

### Task F.2 — Sätt `min_skill` på avancerade recept
- **Goal:** Trösklar på tröskelrecepten (t.ex. leather boots); triviala förblir ogated.
- **Dependencies:** F.1, `world/recipes.py`.
- **Implementation:** Sätt `min_skill` på utvalda recept (boots, framtida armor); twine/cloth/stone knife = 0. Balans-tuning deferras ("yes to balance later"); välj konservativa startvärden.
- **Testing:** In-game: låg-skill-karaktär ser meddelandet på boots men kan fortfarande crafta twine.
- **Commit:** `feat(recipes): gate advanced recipes behind min_skill thresholds`

---

## 12. Component G — Superior-tool scaling (D3 + D4 tie-together)

Ett superior verktyg är enda vägen över baseline — knyter ihop verktygs- och kvalitetstrådarna.

### Task G.1 — Superior verktyg ger `+tool_bonus`
- **Goal:** Ett superior-craftat verktyg skalar modifieraren positivt; normalt = 0, trasigt/frånvarande = penalty.
- **Dependencies:** A.1 (flippen), C.1 (`Tool`), E.1/E.3-mönstret (quality på verktyg — verktygsrecepten får `_finalize_item` som stämplar band/quality på `Tool`).
- **Implementation:** Ge verktygsrecepten ett `_finalize_item` som stämplar band (som garments). I `_tool_modifier`: om verktyget finns och är `superior` (läs `quality_band` på verktyget) → `self.tool_bonus` (återinförd, superior-only, t.ex. +10); annars normalt verktyg → 0; frånvarande/brutet → penalty. Uppdatera `CmdRepair` motsvarande om superior needle ska räknas där också (kan deferras).
- **Testing:** `@py` crafta en superior kniv (tvinga critical), använd i ett recept → `target` = skill + bonus; vanlig kniv → skill + 0.
- **Commit:** `feat(crafting): superior tools grant a positive modifier (ties quality to tools)`

---

## 13. Backlog (utanför denna stages scope)

- **Waterskin-`durability` → `condition`:** migrera refill-livslängden till den delade axeln (semantik-ändring; inte nu).
- **`repair` för verktyg:** promoted to **Task D.4** (Rev 4) — `CmdRepair` broadened to `DurableObject` with data-driven `db.repair_materials` (metal knife ≠ cloth patch). No longer backlog.
- **Jakt-oberoende needle-primitiv:** t.ex. `thorn`/`stick`-nål, så needle-bootstrap inte kräver en jakt.
- **Metallverktyg + station/forge:** bättre condition/quality-verktyg som kräver en craft-station (capability-gate) — bortom denna stage.
- **Fumble-extra-wear tuning:** om `tool_wear_on_fumble` ska divergera från per-use.
- **`CmdRepair._tool_modifier` är plagg-centrerad:** letar alltid efter en `needle`, så att bära en synål gör det (felaktigt) lättare att laga en *stenkniv*. Generalisera per target-typ när superior-verktyg landar (Component G) — låg blast radius, osynlig utan inspektion.
- **Individuering bortom "superior":** material-/maker's-mark-alias för full disambiguation-root-cause-fix (pairar med Stage 3).
