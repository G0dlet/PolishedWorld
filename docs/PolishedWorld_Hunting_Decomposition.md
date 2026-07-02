# PolishedWorld — Hunting & Harvesting Decomposition
 
**Feature branch (planned):** `feature/hunting`
**Status:** Planning / decomposed
**Philosophy:** skynda långsamt — validera creature+corpse innan harvesting byggs ovanpå.
 
---
 
## 1. Varför den här featuren
 
Hunt → corpse → harvest ligger i skärningen mellan två spår:
 
- **Survival-banan:** `meat` är en ny matkälla (laga → ät → mätta hunger). Ren utökning av överlevnadsloopen.
- **Clothing-materialkedjan:** `hide`/`fur` ger äntligen en *ärlig* källa till läder/päls, så `fur_cloak` / `leather_boots`-prototyperna (Component B) får riktiga recept. Linne-only-begränsningen lyfts.
Det är alltså inte två features — det är ett fundament som matar båda.
 
---
 
## 2. Designbeslut låsta den här sessionen
 
| Beslut | Val | Konsekvens |
|--------|-----|------------|
| Förnyelse | **Respawn-ticker från start** | `GLOBAL_SCRIPTS`-spawner håller population i flaggade rum. Förnybar mat- och materialkälla, inte engångsinjektion. |
| Sink för plagg | **Durability + repair, Legend-baserat** | Plagg slits över tid, repareras via skill-check. Håller päls/läder-efterfrågan vid liv. |
| Hunt-skill | **`hunting`** (ej `survival`) | "survival" är redan trait-gauge-kategorin (hunger/thirst/fatigue) — namnkrock undviks. |
| Creatures | **Passiva, slår inte tillbaka** | Inget combat-beroende. Hunt = skill-check, inte stridsrundor. |
| Harvest-scope | **`meat` + `hide` först** | Ben/special-parts/preservation skjuts upp (finns i Creature_Harvesting_Design.md). |
 
---
 
## 3. Verifierade källankare (source-first)
 
Allt nedan är kontrollerat mot `feature/clothing` / Evennia-source så task-formerna är ärliga:
 
- `world/skillcheck.py` → `skill_check(skill_value, modifier=0)` returnerar dict:
  `{"result", "success", "roll", "target", "margin", "crit_score"}`. Tier = `result`.
- Tickers: `GLOBAL_SCRIPTS`-registrerade `Script(DefaultScript)`-subklasser med `at_repeat()`,
  `interval`/`persistent`/`repeats` (mönster: `WeatherScript` i `typeclasses/scripts.py`).
- `typeclasses/clothing.py` → `ClothingWithBuffs(ContribClothing)` med
  `warmth = AttributeProperty(default=0, autocreate=True)` samt `armor_points`/`encumbrance`/
  `rain_protection` (autocreate=False). `wear()`/`remove()` recomputar thermal stress.
- `world/crafting_base.py` → `MongooseCraftRecipe(CraftingRecipe)`: `skill_name`, valfri `tool_tag`
  (+`tool_bonus`/`improvised_penalty`), `consume_policy="raw"`, tier→quality-mappning.
- `custom_gametime` returnerar **0-indexerade** tuples (offset +1 för år/månad/dag) — relevant för decay.
---
 
## 4. Beroendegraf
 
```
[H1 Creature] ──┬──> [H2 Hunt] ──> [H3 Corpse] ──> [H4 Harvest] ──┬──> meat (survival-loop)
                │                                                  │
                └──> [H1.3 Respawn ticker] (renewability)          └──> hide ──> [H5 Recipes] ──> garments
                                                                                       │
                                                          [H6 Durability + Repair] <────┘  (sink)
```
 
**Minimal hunt-corpse-fundament** = Component H1 + H2 + H3 (Session A nedan).
Resten är "fortsätt i survival-banan".
 
---
 
## 5. Sessionsplan
 
| Session | Tasks | Resultat |
|---------|-------|----------|
| **A — Fundament** | H1.1, H1.2, H1.3, H2.1, H2.2, H3.1 | Huntbara, respawnande creatures → corpses |
| **B — Harvest-payoff** | H4.1, H4.2, H4.3 | `meat` som mat + `raw_hide` som material |
| **C — Stäng clothing-loopen** ✅ | H5.1, H5.2 | `raw_hide` → `leather` → `leather_boots` |
| **D — Sinken** | H6.1, H6.2, H6.3 | Plagg slits & repareras (Legend wear) |
| **B/C — Spelar-död** | H7.1, H7.2, H7.3 | HP 0 = död → player-corpse + respawn (deferred: H7.4 dying-state) |
 
---
 
## 6. Component H1 — Creature Foundation
 
### Task H1.1 — `Creature` typeclass (passiv)
- **Goal:** En passiv, dödbar varelse med SIZ och referens till en harvest-template.
- **Dependencies:** `DefaultObject`, skillcheck (för hunt senare), gametime.
- **Approach (key shape):**
  ```python
  # typeclasses/creatures.py
  class Creature(DefaultObject):
      siz = AttributeProperty(default=8, autocreate=True)        # Mongoose SIZ, driver yield
      natural_ap = AttributeProperty(default=0, autocreate=True) # för hide-armour senare
      harvest_template = AttributeProperty(default="rabbit", autocreate=True)
      flee_skill = AttributeProperty(default=30, autocreate=True) # opposed mot hunting
      def at_object_creation(self):
          self.locks.add("get:false()")   # kan inte plockas upp
      def at_death(self, hunter):
          # spawnar Corpse (H3.2), kopierar siz/template, river creature
          ...
  ```
- **@py test:** skapa creature, `obj.db.siz`, `obj.db.harvest_template` → väntat default.
- **Commit:** `feat(creatures): add passive Creature typeclass with SIZ and harvest template`
### Task H1.2 — Creature-prototyp (rabbit)
- **Goal:** En spawnbar prototyp `rabbit` (liten SIZ, ger hide + meat).
- **Dependencies:** H1.1, `world/prototypes.py`.
- **Approach:** prototyp i `world/prototypes.py`: `typeclass`=Creature, `siz=4`, `harvest_template="rabbit"`,
  key/aliases/desc. (Päls-creature, t.ex. `fox`, läggs i Session C när fur-receptet finns.)
- **@py test:** `spawn("RABBIT")` → creature i rummet med rätt siz.
- **Commit:** `feat(creatures): add rabbit prototype (hide + meat source)`
### Task H1.3 — Respawn-ticker
- **Goal:** Global script som håller en population av creatures i flaggade rum (renewability).
- **Dependencies:** H1.2, `GLOBAL_SCRIPTS`-mönstret (WeatherScript).
- **Approach (key shape):**
  ```python
  # typeclasses/scripts.py
  class CreatureSpawnScript(Script):
      def at_repeat(self):
          # för varje rum med db.spawn_creatures (t.ex. {"RABBIT": 3}):
          #   räkna nuvarande Creatures, spawna upp till cap
          #   gles spawn (en per tick) för att undvika flockar
  ```
  Registreras i `GLOBAL_SCRIPTS` med interval (t.ex. 300s), `persistent=True`.
  Rum opt-in via `db.spawn_creatures = {"RABBIT": 3}`.
- **Race condition:** spawn räknar `room.contents` — säkert i Evennias single-threaded tick.
- **@py test:** sätt `room.db.spawn_creatures`, kör `script.at_repeat()`, räkna Creatures → cap.
- **Commit:** `feat(creatures): add CreatureSpawnScript to maintain room populations`
---
 
## 7. Component H2 — Hunt Action
 
### Task H2.1 — `hunting`-skill bootstrap
- **Goal:** Karaktärer får `hunting`-skill vid creation (bredvid perception/stealth).
- **Dependencies:** `typeclasses/characters.py` skill-init.
- **Approach:** lägg `self.skills.add("hunting", "Hunting", trait_type="counter", base=25, ...)`
  i `at_object_creation`. Befintliga karaktärer: engångs-`@py`-batch eller migrate-kommando.
- **@py test:** ny karaktär → `char.skills.get("hunting").value` finns.
- **Commit:** `feat(characters): grant base Hunting skill at creation`
### Task H2.2 — `CmdHunt`
- **Goal:** `hunt <creature>` → opposed-ish skill-check → vid framgång `at_death` → corpse.
- **Dependencies:** H1.1, H2.1, skillcheck.
- **Approach (key shape):**
  ```python
  # commands/hunting_commands.py
  class CmdHunt(Command):
      key = "hunt"
      def func(self):
          target = self.caller.search(self.args.strip())   # måste vara Creature
          # lås målet för denna jakt (race): target.ndb.hunted_by
          skill = self.caller.skills.get("hunting").value
          res = skill_check(skill, modifier=-(target.db.flee_skill // 5))
          if res["success"]:
              target.at_death(self.caller)   # river creature, spawnar Corpse
          else:
              # creature "flyr" → despawn eller flytta; meddela margin
  ```
  Trötthet/fatigue-kostnad kan haka i survival-systemet (valfritt, Session B).
- **Race condition:** `ndb.hunted_by`-guard så två spelare inte fäller samma creature dubbelt;
  kontrollera + sätt i samma tick innan `at_death`.
- **@py test:** spawna rabbit, sätt `char.skills.hunting` högt, kör hunt → Corpse finns, creature borta.
- **Commit:** `feat(hunting): add hunt command with Mongoose skill check`
---
 
## 8. Component H3 — Corpse Foundation
 
### Task H3.1 — `Corpse` typeclass (lazy-sim decay)
- **Goal:** Corpse som lagrar `death_time`, beräknar `decay_stage` on-demand, spårar uttagna delar.
- **Dependencies:** gametime, harvest-templates.
- **Approach (key shape):**
  ```python
  # typeclasses/corpse.py
  class Corpse(DefaultObject):
      creature_type = AttributeProperty(default="rabbit", autocreate=True)
      creature_siz  = AttributeProperty(default=4, autocreate=True)
      death_time    = AttributeProperty(default=0.0, autocreate=True)  # gametime.gametime()
      harvested     = AttributeProperty(default=dict, autocreate=True) # {part: True}
      @property
      def decay_stage(self):
          elapsed = gametime.gametime() - self.db.death_time
          # tröskla mot Creature_Harvesting_Design tidslinje (fresh/stale/rotting/skeleton)
          # justera med rum/säsong (cold 0.5x, hot 2.0x) — lazy, ingen ticker
  ```
  Ingen decay-ticker behövs — staten beräknas vid `look`/`harvest`. Matchar resource-node-mönstret.
- **Gotcha:** gametime 0-indexerat; använd rå `gametime.gametime()`-sekunder för diff, inte tuple-fält.
- **@py test:** skapa corpse, sätt `death_time` i dåtid, läs `decay_stage` → väntat steg.
- **Commit:** `feat(corpse): add Corpse typeclass with lazy on-demand decay`
### Task H3.2 — `at_death` → corpse-konvertering
- **Goal:** `Creature.at_death()` spawnar en Corpse med kopierad siz/template på platsen.
- **Dependencies:** H1.1, H3.1.
- **Approach:** i `at_death`: `create_object(Corpse, key=f"{self.key} corpse", location=self.location,
  attributes=[("creature_siz", self.db.siz), ("creature_type", self.db.harvest_template),
  ("death_time", gametime.gametime())])`, sen `self.delete()`.
- **@py test:** redan täckt av H2.2-testet; här isolerat: `creature.at_death(char)` → Corpse med rätt siz.
- **Commit:** `feat(corpse): convert creature to corpse on death`
---
 
## 9. Component H4 — Harvesting (survival-payoff)   ✅ KLAR & committad

> **Avvikelse mot ursprunglig plan (medveten):** delades data-före-beteende i TRE
> tasks istället för två, och source-verifieringen rättade tre antaganden:
> (1) consumable-typeclassen heter **`Food`** (inte "Consumable"), bär bara data
> (`restore_amount`/`consume_message`); restaureringen ligger i `CmdEat`.
> (2) `consume_policy` är ett *recept*-koncept — irrelevant för ett Food-item.
> (3) `harvest_template` var bara en sträng-nyckel; själva tabellen byggdes här.

**Låsta beslut:** harvest-skill är **per-part i datan** (meat → `hunting` +20 "Easy",
hide → `craft` 0 "Normal" — enda Legend-trogna mappningen med skills som finns; seam
för framtida `craft_leatherworking` är en enradsändring). Yield `meat = max(1, SIZ//2)`,
`hide = max(1, SIZ//3)`; critical = `ceil(1.5×)`, fumble förstör delen, failure = försök
igen. **Quality deferred** (tier→`db.quality` är ~2 rader att lägga till i H5 när leather
behöver den). Decay-gate via `max_stage = STALE` (mjuka delar borta vid ROTTING).

### Task H4.1 — `world/harvest_templates.py` (datamodul)
- **Goal:** Ren data + helpers: `HARVEST_TEMPLATES` (rabbit: meat/hide med
  skill/difficulty/yield_divisor/max_stage/prototype) + `get_template` / `get_part` /
  `list_parts` / `compute_yield`. Stage-konstanter importeras från `typeclasses.corpse`.
- **Dependencies:** `typeclasses.corpse` (FRESH/STALE/ROTTING/SKELETON). Inga side effects.
- **@py/shell test:** `compute_yield(get_part("rabbit","meat"),4)` → 2; `...hide...` → 1;
  `get_part("rabbit","meat")["max_stage"] == STALE` → True. (Ren logik → `evennia shell`.)
- **Commit:** `feat(harvest): add harvest template table with rabbit meat+hide`

### Task H4.2 — Part-prototyper
- **Goal:** `RABBIT_MEAT` (`Food`, `restore_amount=15`, raw-flavour) + `RAW_HIDE`
  (`Object`, `tags=[("raw_hide","crafting_material")]` för H5:s tanning).
- **Dependencies:** H4.1 (prototyp-nycklar matchar templatens `"prototype"`), `Food`.
- **@py test:** `spawn("rabbit_meat")` → `eat` höjer hunger via befintlig CmdEat (noll ny
  kod); `spawn("raw_hide")[0].tags.has("raw_hide","crafting_material")` → True.
- **Commit:** `feat(harvest): add rabbit_meat (Food) and raw_hide part prototypes`

### Task H4.3 — `CmdHarvest`
- **Goal:** `harvest <part> from <corpse>` → decay-gate → atomiskt claim → `skill_check`
  (per-part skill/difficulty) → spawna `compute_yield`-antal. `harvest <corpse>` listar delar.
- **Dependencies:** H4.1, H4.2, H3.1, `skill_check`. Ligger i `commands/hunting_commands.py`,
  registrerad i `default_cmdsets.py` bredvid `CmdHunt`.
- **Outcome-semantik (enkel `skill_check`, ej opposed):** success/critical = delen tas
  (markeras i `corpse.db.harvested`), fumble = förstörs (markeras), failure = orörd (kan
  försökas igen). Valfri knife-bonus +10 (ingen penalty om frånvarande — bootstrap-vänligt).
- **Race condition:** claim-före-spawn + refund-vid-undantag, speglar `CmdForage`; hela
  `func` är atomisk i single-threaded reactorn → samtidiga harvesters serialiseras.
  `is_expired` städar spent corpse lazily. Per-karaktär cooldown 30s, bara på resolverat försök.
- **@py test:** corpse + skill → `harvest meat from corpse` ger 2 meat; andra försöket nekas;
  aged corpse (effektiv ålder via `/decay_modifier` in i [48,144)) → hide "too decayed".
- **Commit:** `feat(harvest): add harvest command with decay-gated atomic part extraction`
 
## 10. Component H5 — Material → Clothing recipes (stänger loopen)   ✅ KLAR & committad

> **Utfall (source-verifierat mot feature/hunting denna session):** ingen strukturell
> avvikelse mot planen — H5.1 + H5.2 levererades som tänkt. Tre saker låstes/rättades:
> (1) recept-namn följer `LinenShirtRecipe`-konventionen med **mellanslag**:
> `name="leather boots"` (inte `"leather_boots"`), så `craft`-parsern läser naturligt.
> (2) `leather`-prototypen saknades helt i repot — skapad som H5.1-output
> (key "piece of leather", alias "leather", tag `("leather","crafting_material")`).
> (3) Quality **deferred**: basen stämplar `db.quality`, inget `_finalize_item` i någon
> task (H6 durability läser det sen) — speglar `LinenShirtRecipe`.

**Låsta beslut:** ratio 2/2 (2×raw_hide → 1 leather; 2×leather → 1 boots = 4 hides per
boots-par, håller leather värdefullt + matar H6-sinken). Cooldowns: leather 45s, boots 40s.
Tools valfria men crafting **straffar** frånvaro (−20 improviserat, till skillnad mot harvest,
som inte straffar). Identiska ingredienser kräver multimatch-syntax `name-N`
(`craft leather from hide-1, hide-2`) — se Evennia-ref 11.6.

### Task H5.1 — `raw_hide` → `leather`  ✅
- **Goal:** Garva 2×`raw_hide` → ny `leather`-prototyp (Craft-skill, valfri knife).
- **Dependencies:** H4.2, `MongooseCraftRecipe`, `CRAFT_RECIPE_MODULES = ["world.recipes"]`.
- **Implementation:** `LeatherRecipe(MongooseCraftRecipe)` i `world/recipes.py`
  (`name="leather"`, `consumable_tags=["raw_hide","raw_hide"]`, `output_prototypes=["leather"]`,
  `tool_tag="knife"`, `craft_cooldown=45`) + `LEATHER`-prototyp i `world/prototypes.py`. `reload`.
- **Verifierat in-game:** `craft leather from hide-1, hide-2 using knife` → `quality=100 mat=True`,
  båda hides konsumerade.
- **Commit:** `feat(recipes): add hide-to-leather tanning recipe`

### Task H5.2 — `leather` → `leather_boots`  ✅
- **Goal:** Sy 2×`leather` → befintlig `leather_boots`-prototyp (Craft-skill, valfri needle).
- **Dependencies:** H5.1, `LEATHER_BOOTS`-prototyp (finns), `NEEDLE`-tool (finns).
- **Implementation:** `LeatherBootsRecipe(MongooseCraftRecipe)` i `world/recipes.py`
  (`name="leather boots"`, `consumable_tags=["leather","leather"]`,
  `output_prototypes=["leather_boots"]`, `tool_tag="needle"`, `craft_cooldown=40`). `reload`.
- **Verifierat in-game:** `craft leather boots from leather-1, leather-2 using needle` → critical,
  `newest_q=111` (100 + crit_score), leather konsumerat.
- **Commit:** `feat(recipes): add leather boots tailoring recipe`

> **Fur-not:** `fur_cloak` kräver ett pälsdjur (t.ex. `fox`) + `fur`-part + recept. Läggs som
> egen liten task-rad här när Session C körs, så materialkedjan blir lika ärlig som linne/läder.
 
---
 
## 11. Component H6 — Garment Durability + Repair (sinken)   ✅ KLAR & committad
 
> **Legend-adaption:** Arms of Legend slitageregler är AP/strids-centrerade (wear-nivåer
> Protected/Basic/Common/Rigorous, veckor mellan reparation, reparationskostnad). Vi adapterar
> *modellen* till warmth-axeln: ett `condition` 0–100 som skalar effektiv `warmth`; degraderas per
> wear-nivå över speltid + exponering; återställs av en Tailoring-reparation. Samma andemening,
> rätt axel för ett survival-spel. Exakta veckor/kostnad lyfts från AoL-tabellen vid implementation.

> **Som byggt (avviker medvetet från skissen nedan — verifierat mot källan; commit-
> meddelandena nedan är de faktiska i git):**
> - **H6.1** byggd som skissat. `worn_warmth` summerar `warmth*condition/100` fraktionellt
>   och **rundar totalen EN gång** (två warmth-1 @49% → 1, inte 0+0); `g.db.condition or 100`
>   håller legacy/plain-plagg opåverkade.
>   Commit: `feat(clothing): scale effective warmth by garment condition`
> - **H6.2** byggd som **TICKER_HANDLER-callback** i `world/garment_wear.py`
>   (`idstring="garment_wear"`, registrerad i `server/conf/at_server_startstop.py`), INTE ett
>   GLOBAL_SCRIPTS-`GarmentWearScript`. Skäl: speglar survival-tickern (enda som redan
>   itererar online burna-plagg-karaktärer) + heltals-condition utan fraktionsfälla.
>   Exponering (`thermal_regime`+`is_indoor`) → Protected/Basic/Common/Rigorous, **samplad vid
>   tick-tid**; rater 0/1/2/4 ur AoL 1–2 AP-raden (AP=2); prod-intervall 10800 s (12 speltimmar).
>   Commit: `feat(clothing): add garment wear ticker degrading worn garments over time`
> - **H6.3** byggd som **`CmdRepair`** (`commands/repair_commands.py`, alias `mend`), INTE ett
>   recept — repair muterar ett befintligt plagg in-place; recept spawnar ny output. Craft-
>   skillcheck, needle +20/−20, tier→condition (crit→100 / success +30 / failure slösar
>   material / fumble −10), konsumerar cloth + twine.
>   Commit: `feat(commands): add CmdRepair restoring garment condition via Tailoring`
 
### Task H6.1 — `condition` på plagg + skalad warmth
- **Goal:** `condition` AttributeProperty (0–100) på `ClothingWithBuffs`; effektiv warmth skalas av den.
- **Dependencies:** `typeclasses/clothing.py`, `world/thermal.py` (`worn_warmth`).
- **Approach:** `condition = AttributeProperty(default=100, autocreate=True)`.
  `worn_warmth` läser idag `db.warmth`; ändra till `warmth * condition/100` (en plats, verifiera mot thermal).
- **@py test:** sätt `garment.db.condition=50`, kontrollera att `worn_warmth` halveras.
- **Commit:** `feat(clothing): scale effective warmth by garment condition`
### Task H6.2 — Wear-ticker
- **Goal:** Global script som degraderar buret plagg per wear-nivå (exponeringsviktat).
- **Dependencies:** H6.1, `GLOBAL_SCRIPTS`-mönstret.
- **Approach (key shape):**
  ```python
  class GarmentWearScript(Script):
      def at_repeat(self):
          # för varje buret plagg: condition -= rate(wear_level)
          # exponering: utomhus/extrem thermal_regime ökar rate (Common→Rigorous)
          # floor på 0; meddela bäraren vid trösklar (t.ex. <25%)
  ```
  `db.wear_level` per plagg (default "common"). Långsam takt — Legend räknar i veckor speltid.
- **Race condition:** ingen — enkel per-objekt-mutation i single-threaded tick.
- **@py test:** kör `at_repeat()` N gånger på ett buret plagg → condition sjunker väntat.
- **Commit:** `feat(clothing): add GarmentWearScript degrading worn garments over time`
### Task H6.3 — Repair-recept
- **Goal:** Tailoring-reparation som återställer `condition` (skill-check, konsumerar cloth/thread).
- **Dependencies:** H6.1, `MongooseCraftRecipe`, cloth/twine-material.
- **Approach:** recipe `name="repair_garment"` (eller `CmdRepair` om vi vill rikta ett specifikt buret
  plagg) — Craft-skill, input cloth + målplagg, output = samma plagg med höjt `condition`
  (tier → hur mycket återställs; fumble kan sänka ytterligare per Legend).
- **@py test:** slitet plagg + cloth → `repair` höjer condition; låg skill ger mindre.
- **Commit:** `feat(recipes): add garment repair restoring condition via Tailoring`
---
 
## 12. Component H7 — Player Death & Corpse
 
> **Scope-beslut:** Vi börjar med **HP ≤ 0 = död direkt** (inget First Aid-fönster). Designen byggs
> dock kring två fogar så dying-state (H7.4) kan läggas till senare utan omskrivning:
> (1) en enda konsekvens-hook `at_character_death()`, (2) en enda HP-0-chokepoint. "Direct death"
> är en ren delmängd av "dying-state" — bara triggern skiljer. **Inte permadeath:** respawn med
> konsekvens, inte radering. Player-corpse = den organiska ekonomi-sinken (droppat arbete kan
> förfalla bort om det inte hämtas).
 
### Task H7.1 — `PlayerCorpse` + `at_character_death()`-hook
- **Goal:** En metod `Character.at_character_death(killer=None)` som spawnar en `PlayerCorpse`,
  flyttar buret/buret inventory dit, respawnar karaktären och sätter en död-debuff.
- **Dependencies:** H3.1 (`Corpse` lazy-decay), staty-logout-systemet (`at_post_unpuppet`).
- **Approach (key shape):**
  ```python
  # typeclasses/corpse.py
  class PlayerCorpse(Corpse):
      # ärver lazy decay; håller RIKTIGA droppade objekt (inte harvest-parts)
      # längre recovery-timer än creature-corpse = hämtningsfönstret
      def at_object_creation(self):
          self.locks.add("get:false()")          # corpsen själv kan inte plockas
          # innehåll lootas individuellt (vanliga get-locks)
 
  # typeclasses/characters.py
  def at_character_death(self, killer=None):
      corpse = create_object(PlayerCorpse, key=f"{self.key}s kvarlevor",
                             location=self.location,
                             attributes=[("death_time", gametime.gametime()),
                                         ("owner", self.id)])
      for obj in self.contents:               # droppa inventory (ej soulbound)
          if not obj.tags.has("soulbound"):
              obj.move_to(corpse, quiet=True, move_hooks=False)
      self._clear_statue_state()              # försoning: dö-staty får inte krocka
      self.move_to(self.db.respawn_location or <temple>, quiet=True)
      self.skills  # applicera död-debuff (svaghet/fatigue) via buffs.add(...)
  ```
- **Edge case (måste lösas här):** dö-och-logga-ut, eller logout medan tickern tar dig till 0.
  Död-staten tar prioritet över statysystemet; vid login i död-state → route till respawn.
- **Race condition:** loot av corpse-innehåll = vanliga Evennia get-locks + atomic `move_to`.
- **@py test:** ge char items, anropa `char.at_character_death()` → PlayerCorpse med items finns,
  char på respawn-platsen, debuff aktiv.
- **Commit:** `feat(death): add PlayerCorpse and at_character_death consequence hook`
### Task H7.2 — HP-0 chokepoint (`apply_health_damage`)
- **Goal:** En enda helper som all HP-skada går genom; eldar `at_character_death()` vid HP ≤ 0.
- **Dependencies:** H7.1, survival-tickern (thermal/svält-skada), HP-gauge-traiten.
- **Approach (key shape):**
  ```python
  def apply_health_damage(self, amount, source=None):
      hp = self.traits.health          # gauge; min-callback finns inte → checka explicit
      hp.current -= amount
      if hp.current <= hp.min:          # tröskel
          self.at_character_death(killer=source)
  ```
  Koppla in: köld/värme-stress i survival-tickern, framtida svält→HP-blödning, senare combat —
  **alla** via denna metod. **Detta är fogen** där dying-state-grenen (H7.4) sen läggs in på ETT ställe.
- **@py test:** sätt HP lågt, `char.apply_health_damage(99)` → död-loopen körs en gång (inte dubbelt).
- **Commit:** `feat(death): funnel HP loss through apply_health_damage with death threshold`
### Task H7.3 — Respawn + död-debuff
- **Goal:** Definiera respawn-plats (temple/hem) och en tillfällig, läkande debuff efter död.
- **Dependencies:** H7.1, buffs-systemet.
- **Approach:** `db.respawn_location` (default temple — knyter an till GameGold-templet). Debuff =
  tidsbegränsad fatigue/svaghets-buff som tickar av. Recovery-timer på PlayerCorpse = hämtningsfönster;
  förfaller corpsen innan loot → items borta (sinken realiseras).
- **@py test:** död → char på respawn-plats, debuff finns och löper ut efter N ticks.
- **Commit:** `feat(death): add respawn location and temporary post-death debuff`
### Task H7.4 — *(DEFERRED)* Dying-state + First Aid-räddning
- **Goal:** HP ≤ 0 → `dying`-state + bleed-ticker; annan spelare kan stabilisera via First Aid-skillcheck.
- **Dependencies:** H7.2 (grenen läggs in i chokepointen), First Aid-skill.
- **Approach:** i `apply_health_damage`: vid tröskel, sätt `db.dying=True` + starta bleed-ticker i
  stället för direkt `at_character_death()`; ticker eldar döden vid timeout om ingen First Aid-success.
  Legend-aligned (major wound → bleed-out). **Ingen ändring av H7.1-konsekvensen behövs.**
- **Status:** Medvetet uppskjuten. Tas in när vi vill ha den sociala räddnings-loopen / inför combat.
---
 
## 13. Öppna frågor / risker
 
- **Respawn-balans:** cap per rum + interval måste tunas så population inte exploderar eller töms.
- **Hunt-svårighet:** opposed mot `flee_skill` vs flat modifier — bestäm vid H2.2.
- **Hide-skill:** ~~hunting eller Craft?~~ **LÖST:** per-part i template-datan — meat→`hunting` (+20), hide→`craft` (0). Seam för framtida `craft_leatherworking` är en enradsändring.
- **Befintliga karaktärer** saknar `hunting` — engångs-batch vid H2.1.
- **Reload-krav:** nya recept laddas modul-level → `reload` efter H5/H6.3 (känt mönster).
- **Wear-takt:** Legend räknar veckor; vid 4× speltid måste tickerns rate kännas rättvis, inte tjatig.
- **Staty vs död (H7.1):** dö-och-logga-ut / logout-medan-tickern-dödar — död-state måste ta prioritet över `at_post_unpuppet`-statysystemet.
- **Soulbound (H7.1):** ska något (t.ex. mest basala plagg/verktyg) överleva döden, eller droppar allt? Påverkar loss-frustration för nya spelare.
- **PvP-policy:** behöver beslutas innan combat introduceras, men inte nu — död-loopen byggs under survival-only-död först.
---
 
**Skapad:** denna session · **Stil:** Functional Decomposition (Goal/Deps/Approach/@py/Commit)
**Nästa steg:** "Let's implement Task H1.1" → full runnable kod + tester (efter slutlig source-check).
