# PolishedWorld — Recipe Knowledge & Discovery Decomposition

> **Rev 5 · 2026-07-13** — Component D (profession-grants, the first knowledge *source*) complete & in-game-verified on `feature/recipe-knowledge`, two atomic tasks: **D.1** (`world/professions.py` — pure-data `PROFESSIONS` map of four small, overlapping recipe bundles + `grant_profession(character, key)`, idempotent via `learn_recipe`, unknown key → no-op + `evennia.utils.logger` warning) and **D.2** (`CmdChooseProfession` — `profession`/`professions`, a one-time free choice guarded by a `db.profession` sentinel; grants recipe *knowledge* only). Design locked against Legend RAW: professions are **free choice** (Legend gates on Cultural Background, never a characteristic minimum — a weak character can still be a smith, just lower Craft), and Component D models only the Advanced-Skill-access half; the Common-Skill-bonus half and Cultural-Background gating are deferred (BACKLOG Rev 6, new *Professions & Chargen* section, both BLOCKED on a real chargen). No `at_object_creation` change and no `character_migrations` backfill needed — a *choice* cannot be backfilled; existing characters simply gain the command. Status pointer advanced to Component E.
> **Rev 4 · 2026-07-11** — Component C (`recipes` discovery surface) complete & in-game-verified on `feature/recipe-knowledge`, split into two atomic tasks: **C.1** (`CmdRecipes`, `key="recipes"`/alias `recipe`) renders Common + learned ("Known") recipes with an alphabetised, base-sentinel-skipped listing and a vague "hidden crafts" hint (exact count behind `SHOW_HIDDEN_COUNT`, default off, to preserve mystery); **C.2** (`recipes <name>`) details a *visible* recipe's ingredients (`consumable_tags` duplicate-collapsed to `Nx tag`), optional tool, skill floor and output, reusing B.2's `_resolve_recipe` and gated by the same visibility partition as the list — an advanced recipe the caller has not learned is refused *by name* (a teach/learn nudge) without leaking its ingredients. Wiring added once (C.1) after `CraftingCmdSet`; unique key/alias avoids the `look`/`ExtendedRoomCmdSet` collision (H7.3b lesson). BACKLOG Rev 5 logged the `recipes <name>` output-name prettify deferral. Status pointer advanced to Component D.
> **Rev 3 · 2026-07-11** — Component B (dual knowledge-gate) complete & in-game-verified on `feature/recipe-knowledge`: B.1 (`requires_knowledge` gate in `MongooseCraftRecipe.pre_craft`, placed after input validation and before the skill-gate, defensive `knows_recipe` getattr guard, raises before any consume) and B.2 (`CmdCraftGated(CmdCraft)` in new `commands/crafting_commands.py`, early-rejecting unknown advanced recipes before ingredient search; wired after `CraftingCmdSet` so it overrides the stock `craft`). Verified in-game: unknown `cloth` blocked with materials intact → `learn_recipe("cloth")` → crafts; common `twine` bypasses the gate. BACKLOG Rev 4 logged the `CmdCraftGated` resolver-duplication tech-debt. Status pointer advanced to Component C.
> **Rev 2 · 2026-07-11** — Component A (foundation) complete & in-game-verified on `feature/recipe-knowledge`: A.1 (tag-based known-recipe set on `Character` — module const `KNOWN_RECIPE_CATEGORY` + `knows_recipe`/`learn_recipe`/`known_recipes` helpers) and A.2 (`requires_knowledge` class-attr on `MongooseCraftRecipe`, `True` on the four learnable recipes, common four inherit `False`) shipped. Status pointer advanced to Component B.
> **Rev 1 · 2026-07-11** — first version. Decomposes roadmap Stage 3 (Recipe Knowledge & Discovery) into nine components: the knowledge foundation (per-character known-set + `requires_knowledge` recipe flag), the dual knowledge-gate (`pre_craft` backstop + `CmdCraft` early-reject), a `recipes` discovery surface, and six knowledge *sources* — profession-grants at chargen, reverse-engineering, scroll, perishable book, player-teaching, and a thin world-loot seed. Locks the four roadmap sub-decisions — **(a)** consumable scroll, **(b)** primitive-common baseline via a recipe flag, **(c)** profession-grants + thin world-loot seed, **(d)** know-it + `min_skill` gate (Teaching *skill* is **not** a gate — deferred to BACKLOG as an amplifier) — plus three session additions: a **perishable book** (multi-recipe `DurableObject`, worn per study, no repair), the **`recipes`** discovery command, and **reverse-engineering** (destructive + Craft-roll). Source-verified against `main`: the `pre_craft` gate slot, `_RECIPE_CLASSES` fuzzy match, `DurableObject` API, and — flagged — three discrepancies (stock `craft` lists nothing; `do_craft` does **not** stamp the recipe name; the Legend Craft-teacher gate is p.72–73, not the p.70–71 cited in roadmap/decomp).
> **Canonical:** `docs/PolishedWorld_Recipe_Knowledge_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If this project-knowledge copy's Rev is lower than the repo's, it's stale — re-upload from the repo.

**Feature branch:** `feature/recipe-knowledge` (green from `main` — Stage 2 merged via PR #12).
**Status:** design locked; Components A–D complete & in-game-verified on `feature/recipe-knowledge`. Component E (recipe-stamp + reverse-engineering) next, fresh chat.
**Philosophy:** skynda långsamt — bygg *gaten* först (known-set + gate testbara isolerat med manuell tag-add) och lägg *källorna* därefter i beroende-ordning, så varje kanal verifieras separat: "lär via X → nu craftbart".

---

## 1. Varför den här featuren

Stage 2 gjorde craft-utfallet *kännbart* (kvalitet, verktyg, skill-gate). Stage 3 gör **kunskap** till en resurs. Idag kan varje karaktär craft:a varje recept och kan inte ens *se* vilka som finns — kunskap är varken gätad eller en vara. Stage 3 aktiverar den **tredje ortogonala gaten**:

- **knowledge** (binär — *kan* du receptet alls?) — NY, hela poängen med stagen.
- **skill** (Stage 1-improvement + Stage 2:s E/F) — *hur bra*, och *får du försöka*.
- **capability** (Stage 2:s verktyg/G) — *vilka verktyg skalar utfallet*.

De två senare är byggda och verifierade; knowledge-gaten byggs här. När kunskap är gätad blir den en **ekonomisk vara**: spelare lär sig / köper / säljer / lär ut / plockar-isär recept → specialisering och ömsesidigt beroende (pelare 1). Legend-ankaret: "recept" är en MUD-konvention (Legend har bara Craft-rolls) MEN gätad kunskaps-*överföring via lärare* är rulebook-troget — Craft kan inte själv-läras (Legend p.72–73).

---

## 2. Designbeslut låsta den här sessionen

**De fyra roadmap-delbesluten:**

- **(a) book vs scroll → B, scroll (consumable), + perishable book som bulk-variant.** Scrollen är ett craftbart engångs-föremål (kunnig skriver → elev förbrukar) — source *och* sink native i ett objekt, starkaste pelare-1-sinken. **Bok-tillägg:** efter högre expertis kan en spelare skriva en `Book` som håller *flera* recept och nöts per studie tills den vittrar bort (`DurableObject`); boken är den async, storskaliga spridaren. Skalan: scroll = 1 recept/1 användning; bok = många recept/många användningar.
- **(b) cold-start-baseline → B, primitiv-common via recept-flagga.** `MongooseCraftRecipe.requires_knowledge = False` (default = common/ogated, speglar `min_skill = 0`). Common = survival/verktygs-primitiverna **{twine, waterskin, stone knife, bone needle}**; lärbart (`requires_knowledge = True`) = förädlade material + färdiga varor **{cloth, leather, linen shirt, leather boots}**. Common bypassar gaten helt → known-set:et innehåller bara *avancerade* recept (litet, meningsfullt). `leather boots` blir nu dubbel-gätad (kunskap + `min_skill = 30`) — ren ortogonalitets-demo.
- **(c) bootstrap-källa → C, profession-grants vid chargen + tunn world-loot-scroll-seed.** Professioner seedar kunskap in i *spelarbasen själv* (pelare-1-rent, Legend-format, löser "vem skriver första boken"); den tunna world-loot-seeden är säkerhetsventil så ett recept inte blir ovinnbart om dess profession saknas online. NPC-"master" deferrad (pelare-1-spänning). Endast kunskaps-slicen av professioner byggs nu — inga stat-bonusar (senare epic).
- **(d) teaching-mekanik → C, know-it + `min_skill`.** Lärar-gate = *känner receptet (obligatoriskt)* + *möter receptets `min_skill`* (Legend "professional ≥50%"-smak, utan separat Teaching-beroende). **Teaching-*skill* är INTE en gate** (Legend-troget — den är en amplifier) → BACKLOG som framtida bonus (kortare cooldown / fler elever). Samma rum, samtyckes-handshake, cooldown.

**Tre arkitektur-lås (styr flera komponenter):**

- **Dubbel gate.** (1) `pre_craft` tredje gate = auktoritativ backstop för alla kod-vägar som anropar `craft()` direkt (barter-craft, scripts) — placerad efter `super().pre_craft()`, **före** skill-gaten ("kan du det alls" före "är du skicklig nog"). (2) `CmdCraft`-subklass = UX-avvisning *före* ingrediens-sök, så spelaren inte tvingas samla material för ett recept hen inte kan. Speglar barter-guardens "validering + `finish()`-backstop".
- **Tag-baserad known-set.** `char.tags.add(name, category="known_recipe")` — querybart ("vem kan X?"), idiomatiskt, ingen mutable-default-fälla, billig `tags.has()`. Centraliseras bakom Character-helpers (`knows_recipe`/`learn_recipe`/`known_recipes`) så kategori-strängen bara skrivs en gång.
- **Skrivning är kommando, inte recept.** Scroll-/bok-skrivning kan inte vara en `MongooseCraftRecipe` — outputen är *parametriserad* av vilket recept du inskriberar (valt vid craft-tid), medan recept har fixerade `output_prototypes`. Dedikerade kommandon (`inscribe`, `scribe`), parallellt med varför `CmdRepair` är ett kommando. Gemensam behörighet (`_can_transmit`) delas av `inscribe`, `scribe` och `teach`.

**Delad behörighets-regel (scroll ⋂ book ⋂ teach):** *känner receptet + möter `min_skill`*. En hjälpfunktion `_can_transmit(char, recipe_name)` införs i Component F och återanvänds av G och H.

---

## 3. Verifierade källankare (source-first, mot `main`)

- **`world/crafting_base.py::MongooseCraftRecipe.pre_craft`** — ordning: `self.rolled = False` (+ reset) → `super().pre_craft()` (contrib input-validering) → **skill-gate** (`_skill_value() < min_skill` → `msg` + `raise CraftingError`) → **cooldown-gate**. Varje raise-gate lämnar `rolled = False` → `post_craft` consumar inget. Knowledge-gaten läggs som tredje raise-gate i **samma metod**, direkt före skill-gaten. *(Not: minnet sa `CraftingError(rolled=False)`; källan sätter `self.rolled = False` separat + plain `raise CraftingError(msg)`.)*
- **`world/crafting_base.py::do_craft`** — stämplar `obj.db.quality` och `obj.db.crafted_by = self.crafter.key` på varje spawned output *före* `_finalize_item`. **Stämplar INTE receptnamnet.** → Component E lägger `obj.db.recipe = self.name` i samma loop (förutsättning för reverse-engineering; synergiserar med BACKLOG maker's-mark).
- **`evennia.contrib.game_systems.crafting.crafting`** — `_load_recipes()` fyller global `_RECIPE_CLASSES` en gång från `settings.CRAFT_RECIPE_MODULES`; modul-`craft(crafter, recipe_name, *inputs)` gör fuzzy-match (exact → `startswith` → `in`, unik). **Ingen per-karaktär-filtrering finns.** `RecipeClass.name`/`RecipeClass.requires_knowledge` är klassattribut → läsbara utan instansiering (för command-nivå-gaten).
- **`CmdCraft`** — `parse()` delar `<recipe> [from …] [using …]`; `func()` söker ingredienser i inventory *innan* modul-`craft()` anropas. **Utan argument → skriver bara usage, listar INGA recept.** → hela discovery-ytan (`recipes`) är ny; det finns inget inbyggt att gäta.
- **`typeclasses/durable.py::DurableObject`** — `condition = AttributeProperty(default=100, autocreate=True)`; `apply_wear(amount)` → nytt värde (floor 0, atomiskt under reaktorn); `is_broken` (`condition <= 0`); `condition_line()` + `get_display_desc()` som redan hänger condition-raden på `look`. → `Book(DurableObject, Object)` ärver allt; condition-på-`look` gratis.
- **`typeclasses/characters.py`** — `skills` = `TraitHandler`; AttributeProperty-mönster finns (`login_skill_snapshot = AttributeProperty(default=None, autocreate=False)`, coalesce `None → {}`); `tags`-handler tillgänglig; `attempt_skill_improvement(skill_key, outcome)` + `_improvement_feedback(result)` är den gätade improvement-vägen (reverse-engineering blir en femte check-site).
- **`commands/default_cmdsets.py::CharacterCmdSet`** — `self.add(CraftingCmdSet)` är craft-inhaket; nya `recipes`/`inscribe`/`scribe`/`learn`/`teach`/`disassemble` hakar in här. H7.3b-lärdomen (`CmdContainerLook` clashade med `ExtendedRoomCmdSet::look`) → nya kommandon får unika nycklar, ingen `look`-krock.
- **`world/recipes.py`** — 8 recept: `TwineRecipe`, `WaterskinRecipe`, `ClothRecipe`, `LeatherRecipe`, `LinenShirtRecipe`, `LeatherBootsRecipe`, `StoneKnifeRecipe`, `BoneNeedleRecipe`. Ingen recept-kunskaps-scaffolding — fältet är tomt.
- **`Legend.pdf` p.72–73** — Craft (Advanced) kan **endast** läras via lärare/mentor; lärare måste vara **professional (≥50%)** för en ny advanced skill, annars ≥20% mer än eleven. **Teaching (INT+CHA) är en amplifier, ingen gate** (bonus till improvement, +1 elev per 20%, högre kostnad). *(Roadmap/decomp citerar "p.70–71" — korrigeras i deras nästa Rev.)*

---

## 4. Beroendegraf

```
                 A (known-set + requires_knowledge-flagga)   [FOUNDATION]
                 /              |                 \
                B (dubbel gate) C (recipes-        D (profession-grant
                 |               discovery)          vid chargen)     [POPULATION SEED]
                 |
        +--------+--------+------------------+
        |                 |                  |
   E (recipe-stamp    F (scroll:          H (teach:
    + reverse-eng)     inscribe + learn)    handshake, _can_transmit)
                         |
                   G (book: Book(DurableObject)
                    + scribe + learn-utökning)
                         |
                   I (tunn world-loot-scroll-seed)   [SAFETY VALVE]
```

- **A** är foundation för allt (lagring + flagga). **B** läser A (gate:ar avancerade recept). **C** läser A (vad är känt/common). **D** skriver A (seedar known-set).
- **B** placeras direkt efter A: då är premissen live (avancerade recept blockerade) och varje källa verifieras "lär via X → nu craftbart". Fram till D landar bekräftas known-set via manuell tag-add (A:s test).
- **E/F/H** är oberoende kanaler som alla skriver known-set (kräver bara A; B för att kanalens *poäng* ska synas). **F** inför `_can_transmit` som **G** och **H** återanvänder. **G** bygger på F:s `learn`-verb. **I** kräver att Scroll-objektet finns (F).
- **Första speltestbara helhet:** A+B+C+D tillsammans (gate live + du ser vad du kan + professioner seedar kunskap att sprida). Källorna E–I fördjupar ekonomin ovanpå.

---

## 5. Sessionsplan

3–5 tasks/session, en komponent per chatt för ren kontext.

- **Session 1 (foundation + core gate):** A.1–A.2 (known-set-helpers + `requires_knowledge`-flagga med baseline-partition) + B.1 (`pre_craft`-backstop). Låser den ortogonala gaten. B.2 (`CmdCraft`-UX-reject) kan följa här eller i S2 — polish, inte kritisk väg.
- **Session 2 (legibility + population):** C.1 (`recipes`-discovery) + D.1–D.2 (professions-modul + chargen-grant). **Kräver egen source-verify av chargen-flödet live** (menyn/`at_object_creation`) i D:s chatt. Efter S2: A+B+C+D = första speltestbara helhet.
- **Session 3 (item-kanalen):** E.1 (recipe-stamp i `do_craft`) + E.2 (`disassemble` reverse-eng) + F.1–F.2 (`inscribe` + `learn` scroll, inför `_can_transmit`).
- **Session 4 (bulk + social):** G.1–G.3 (`Book`-typeclass + `scribe` + `learn`-utökning) + H.1 (`teach`-handshake).
- **Session 5 (ventil + reconcile):** I.1 (world-loot-seed) + doc-reconcile (roadmap Rev, evref Rev, BACKLOG amplifier/bok-repair).

**Trim-ordning om tid pressar:** I (world-loot-seed) är mest deferrbar → BACKLOG; G (bok) kan bli fast-follow efter F. E/F/H är kärnkanalerna och bör alla in.

---

## 6. Component A — Knowledge foundation

Per-karaktär known-set + recept-flaggan som avgör *vad* gaten bryr sig om. Ingen gate än (den läser detta i B); testas via manuell tag-add.

### Task A.1 — Known-recipe-set på Character
- **Goal:** Karaktären äger en tag-baserad mängd kända recept, bakom tre helpers.
- **Dependencies:** `typeclasses/characters.py` (`tags`-handler).
- **Implementation:** Konstant `KNOWN_RECIPE_CATEGORY = "known_recipe"` (modulnivå i characters.py). Tre metoder på `Character`: `knows_recipe(self, name)` → `self.tags.has(name, category=KNOWN_RECIPE_CATEGORY)`; `learn_recipe(self, name)` → idempotent `self.tags.add(name, category=...)`, returnera `True` om nytt (kolla `knows_recipe` först — så call-sites kan säga "du kunde redan detta" utan att slösa material/scroll); `known_recipes(self)` → `self.tags.get(category=..., return_list=True)` (alltid lista). Namnet som lagras är den kanoniska recept-`name` (registry-nyckeln, ej prototype_key).
- **Testing:** `@py` `me.learn_recipe("cloth")` → `str([me.knows_recipe("cloth"), me.knows_recipe("leather"), me.known_recipes()])` → `[True, False, ['cloth']]`; andra `learn_recipe("cloth")` returnerar `False` (idempotent).
- **Commit:** `feat(knowledge): add tag-based known-recipe set on Character`

### Task A.2 — `requires_knowledge`-flagga + baseline-partition
- **Goal:** Recept deklarerar om de är gätade; survival-primitiverna är ogated (common).
- **Dependencies:** A.1, `world/crafting_base.py`, `world/recipes.py`.
- **Implementation:** Klassattr `requires_knowledge = False` på `MongooseCraftRecipe` (default = common, speglar `min_skill = 0`). Sätt `requires_knowledge = True` på de fyra lärbara: `ClothRecipe`, `LeatherRecipe`, `LinenShirtRecipe`, `LeatherBootsRecipe`. `TwineRecipe`/`WaterskinRecipe`/`StoneKnifeRecipe`/`BoneNeedleRecipe` ärver default `False`. Ingen gate-logik än — bara deklarationen som B/C läser. Dokumentera partitionen i docstring (survival/verktyg = common; förädling/varor = lärbart).
- **Testing:** `@py` `from world.recipes import ClothRecipe, TwineRecipe; me.msg(str([ClothRecipe.requires_knowledge, TwineRecipe.requires_knowledge]))` → `[True, False]` (klassattr, ingen instansiering).
- **Commit:** `feat(recipes): flag advanced recipes as requiring knowledge`

---

## 7. Component B — Dual knowledge-gate

Den ortogonala tredje gaten. `pre_craft` är sanningen; `CmdCraft`-subklassen är artigheten.

### Task B.1 — Knowledge-gate i `pre_craft` (auktoritativ backstop)
- **Goal:** Ett gätat recept avbryts före consume om craftaren inte kan det — oavsett kod-väg.
- **Dependencies:** A.1, A.2, `world/crafting_base.py` (`pre_craft`, `CraftingError`).
- **Implementation:** I `pre_craft`, **efter** `super().pre_craft()` och **före** skill-gaten: `if self.requires_knowledge and not (getattr(self.crafter, "knows_recipe", None) and self.crafter.knows_recipe(self.name)): self.msg("You don't know how to make that."); raise CraftingError(f"{self.name}: recipe unknown to crafter.")`. `getattr`-guard matchar modulens defensiva crafter-access (crafter är normalt Character men world-lagret antar det inte). `rolled` förblir False → `post_craft` consumar inget. Placeringen (före skill) ger prioritet "kan du alls?" före "är du skicklig nog?".
- **Testing:** `@py` (`@reload` efter modul-ändring) — spawna material för `cloth`, craft utan `knows_recipe("cloth")` → meddelande, material kvar (`for o in list(me.contents)` oförändrat); `me.learn_recipe("cloth")` → craft går igenom. Common-recept (`twine`) craftar oberoende av known-set.
- **Commit:** `feat(knowledge): gate advanced recipes on known-recipe set in pre_craft`

### Task B.2 — `CmdCraft`-subklass (tidig UX-reject) *(polish; ej kritisk väg)*
- **Goal:** Ett okänt recept avvisas *innan* ingrediens-sök, med tydligt skäl.
- **Dependencies:** B.1, `commands/default_cmdsets.py`, contribens `CmdCraft`/`_RECIPE_CLASSES`.
- **Implementation:** `commands/crafting_commands.py::CmdCraftGated(CmdCraft)` som override:ar `func()`: en liten `_resolve_recipe(name)` speglar contribens fuzzy-match (exact → `startswith` → `in`, unik; efter `_load_recipes()`) och returnerar klassen eller None; om klassen har `requires_knowledge` och `not caller.knows_recipe(cls.name)` → `caller.msg("You don't know how to make that.")` + `return` (före `super().func()`). Byt `self.add(CraftingCmdSet)` mot att lägga `CraftingCmdSet` **plus** `CmdCraftGated()` (subklassen override:ar `key="craft"`). *Duplicerar ~5 rader fuzzy-logik — accepterat: `pre_craft` är backstop om contribens matchning driftar; logga i BACKLOG att detta ska konsolideras om contriben stabiliserar ett publikt resolver-API.*
- **Testing:** In-game: `craft cloth from fiber` utan kunskap → "You don't know…" *utan* att fiber-sökningen körs; efter `learn` → normal craft. `craft twine …` opåverkat.
- **Commit:** `feat(knowledge): reject unknown recipes at the craft command before ingredient search`

---

## 8. Component C — `recipes` discovery-yta

Legibility: vad du kan, med en hint att mer finns. Löser att stock `craft` inte listar något. C.1 *listar*; C.2 *detaljerar* ett synligt recept.

### Task C.1 — `CmdRecipes` (overview)
- **Goal:** Spelaren ser sina *kända* recept + *common*-recepten, med en vag hint om dolda.
- **Dependencies:** A.1, A.2, `_RECIPE_CLASSES`.
- **Implementation:** `commands/crafting_commands.py::CmdRecipes` (`key="recipes"`, `aliases=["recipe"]`, lås `cmd:all()`). Kör `_load_recipes()`, iterera `_RECIPE_CLASSES.values()` (skip:a defensivt bas-sentinel `"mongoose craft base"`): `not requires_knowledge` → hink "Common"; annars `caller.knows_recipe(cls.name)` → "Known"; annars → räkna som "hidden". Rendera Common + Known alfabetiskt (namn, ev. `min_skill`-not). `hidden > 0` → vag hint `|xWhispers speak of crafts beyond your knowing.|n`; exakt antal bakom klassattr `SHOW_HIDDEN_COUNT` (default `False`). Färgkoder via Evennia-parser, aldrig rå `|`.
- **Testing:** `@reload` en gång efter patch; känt-set läses live per anrop (ingen reload mellan `learn_recipe`/`tags.clear` och nästa `recipes`). Färsk karaktär → fyra common + hint; `learn_recipe("cloth")` → cloth i "Known", hint kvar; `learn_recipe("leather boots")` → `(needs Craft 30%)`-not; alla fyra lärda → hint borta; alias `recipe`; `SHOW_HIDDEN_COUNT=True` → antal (singular/plural); `.replace("|","!")`-eko för råa färgkoder.
- **Commit:** `feat(discovery): add recipes command listing known and common recipes`

### Task C.2 — `recipes <name>` (detail)
- **Goal:** Spelaren ser ett *synligt* recepts ingredienser (med antal), tool, skill-floor och output.
- **Dependencies:** C.1; B.2 (`_resolve_recipe`); A.1 (`knows_recipe`).
- **Implementation:** Utöka `CmdRecipes.func` till dispatch på `self.args` (rå → `.strip().lower()`; tomt → `_show_list`, annars `_show_detail`). `_show_detail` löser via `_resolve_recipe` och **synlighets-gätar** som listan: `cls is None` → `No recipe matches '<name>'.`; avancerat + ej lärt → `You don't know the recipe for '<name>'. Seek someone who does.` (namnger receptet som teach/learn-nudge, läcker *inte* ingredienser). `consumable_tags`-dubletter → `Counter` → `Nx tag`; `tool_tag None` → "none needed", annars "<tool> (optional; …penalty)"; `min_skill` → "Craft N% minimum"/"no minimum"; `output_prototypes` = prototyp-*nycklar*, prettify `_`→mellanslag. En `Tip: 'recipes <name>' …`-rad tillkommer i overview.
- **Testing:** `recipes waterskin` (1x gourd/1x twine, knife optional); `recipes twine` (3x fiber, none needed); `recipes cloth` färsk → refusal utan ingredienser; `recipes leather` (exact, avancerat, ej lärt) → refusal; `learn_recipe("leather boots")` → `recipes leather boots` (2x leather, needle, Craft 30% minimum); fuzzy `recipes water`/`recipes needle`; tvetydigt `recipes le` → No recipe matches; `recipes glesch` → No recipe matches.
- **Commit:** `feat(discovery): detail a recipe's ingredients and tools via 'recipes <name>'`

---

## 9. Component D — Profession-grants vid chargen  *(population seed)*

Seedar avancerad kunskap in i spelarbasen så teach/scroll-ekonomin lever från de första spelarna. Endast kunskaps-slicen — inga stat-bonusar.

> **D-chatt måste source-verifiera chargen-flödet live** (custom menu-login / character-creation / `at_object_creation`) för att hitta exakt inhak. Nedan är inriktningen, inte den låsta koden.

### Task D.1 — `world/professions.py` (recept-buntar)
- **Goal:** En datadriven karta profession → avancerade recept.
- **Dependencies:** A.2 (recept-namnen).
- **Implementation:** `PROFESSIONS = {"weaver": ["cloth", "linen shirt"], "tanner": ["leather"], "cobbler": ["leather boots"], "generalist": [...]}` (ren Python, inga Evennia-beroenden — som `crafting_quality.py`). En hjälp `grant_profession(character, key)` → för varje namn `character.learn_recipe(name)`; okänd nyckel → no-op + log-warning. Håll buntarna små och överlappande så två professioner behöver varandra (interdependens).
- **Testing:** `@py` `from world.professions import grant_profession; grant_profession(me, "weaver"); me.msg(str(sorted(me.known_recipes())))` → `['cloth', 'linen shirt']`; okänd nyckel → oförändrad known-set.
- **Commit:** `feat(professions): add profession→recipe bundles and grant helper`

### Task D.2 — Grant vid chargen
- **Goal:** En ny karaktär får sin professions-bunt seedad in i known-set vid skapande.
- **Dependencies:** D.1, **verifierat chargen-inhak** (D-chattens source-verify).
- **Implementation:** Beroende på vad live-flödet visar: ett menysteg som väljer profession, ELLER (MVP-fallback) ett `db.profession`-default + grant i chargen-hooken, ELLER ett engångs-`CmdChooseProfession` tillgängligt tidigt. Idempotent (kör grant en gång; guarda mot re-grant vid `@reload`/re-puppet). Håll det till kunskaps-grant — ingen stat-påverkan. Synka ev. med `world/character_migrations.py`-mönstret så backfill av befintliga karaktärer är möjlig (parallellt med `HUNTING_SKILL_DEFAULTS`-noten).
- **Testing:** Skapa en ny testkaraktär via det verkliga flödet → `known_recipes()` innehåller buntens recept; befintlig karaktär opåverkad tills backfill körs.
- **Commit:** `feat(chargen): grant a starting profession's recipes at character creation`

**Status pointer:** Component D complete (D.1 + D.2). **Component E next.**

---

## 10. Component E — Recipe-stamp + reverse-engineering  *(item-kanal)*

Kunskap läcker genom *handlade* varor: köp en rivals plagg, plocka isär, lär dig receptet. Destruktiv + Craft-gätad så den inte underminerar de betalda kanalerna.

### Task E.1 — Stämpla receptet på craftad output
- **Goal:** Craftade föremål bär sitt recept-namn så reverse-eng vet vad de lär ut.
- **Dependencies:** `world/crafting_base.py::do_craft`.
- **Implementation:** I `do_craft`:s spawn-loop, direkt efter `obj.db.crafted_by = self.crafter.key`: `obj.db.recipe = self.name`. En rad; generellt användbar (matar BACKLOG maker's-mark/individuering). Spawnade/loot/admin-items saknar stämpeln (`db.recipe` = None) → reverse-eng biter bara på spelartillverkade varor (önskvärt).
- **Testing:** `@py` craft ett `cloth` (efter `learn`), inspektera outputen → `obj.db.recipe == "cloth"`; en `spawn`-ad prototyp utan craft → `db.recipe` None.
- **Commit:** `feat(crafting): stamp the recipe name on crafted output`

### Task E.2 — `disassemble`-kommando (Craft-roll, destruktivt)
- **Goal:** Offra ett craftat föremål för en chans att lära dess recept; föremålet förstörs oavsett.
- **Dependencies:** E.1, A.1, `world/skillcheck.py`, `attempt_skill_improvement`, `cooldowns`.
- **Implementation:** `commands/crafting_commands.py::CmdDisassemble` (`key="disassemble"`, alias `["salvage"]`). Sök target i inventory; läs `name = target.db.recipe`. Guards: None → "You can't learn anything by taking this apart."; recept ej gätat (common) eller redan känt → "You already know how these are made." (förstör **inte** — ingen anledning). Annars: cooldown-check (`cooldowns.ready("disassemble")`); `skill_check(craft_value, modifier=-min_skill)` (svårare för mer avancerade recept — läs målреceptets `min_skill` via `_RECIPE_CLASSES[name].min_skill`); **förstör target oavsett utfall** (`target.delete()`) och sätt cooldown. Success → `caller.learn_recipe(name)` + rutta outcome genom `attempt_skill_improvement("craft", outcome)` (femte check-site) + `_improvement_feedback`. Fail → "The piece falls apart before you grasp how it was made." Multiplayer: läs-modifiera-radera är atomiskt under reaktorn; cooldown mot spam.
- **Testing:** `@py` craft ett `cloth`, ge bort known-set:et (ny karaktär utan cloth), `me.cooldowns.clear()`; `disassemble cloth` upprepat (deterministiskt via hög/låg `craft`-`mod`) → success lär + förstör, fail förstör utan att lära; redan-känt → ingen förstörelse.
- **Commit:** `feat(knowledge): add disassemble command to reverse-engineer crafted items`

---

## 11. Component F — Scroll  *(skriven engångs-transfer)*

Consumable enkelrecept-scroll. Inför den delade `_can_transmit`-behörigheten.

### Task F.1 — `inscribe`-kommando (skriv en scroll)
- **Goal:** En kunnig craftare skriver en scroll för ett recept hen kan; förbrukar skrivmaterial.
- **Dependencies:** A.1, A.2, `world/skillcheck.py`, prototyp för scroll + skrivmaterial.
- **Implementation:** Delad `world/knowledge.py::_can_transmit(char, recipe_name)` → `char.knows_recipe(name) and char._skill_value...`— läs craft-skill via `char.skills.get("craft")` och jämför mot `_RECIPE_CLASSES[name].min_skill` (Legend "professional"-smak). `CmdInscribe` (`key="inscribe"`): parsa målrecept; `_can_transmit`-guard ("You can't inscribe a recipe you haven't mastered."); common-recept → "Everyone already knows this."; förbruka skrivmaterial (**tuning-flagga:** ny primitiv `parchment` (hide-härledd, knyter hunting-ekonomin) ELLER MVP-återbruk av `fiber`/`cloth` — låses i F-chatten); spawna `scroll`-prototyp, stämpla `obj.db.recipe = name`; cooldown. Scrollen är ett vanligt `Object` (ej DurableObject — den är engångs, förbrukas vid `learn`).
- **Testing:** `@py` `me.learn_recipe("cloth")` + tillräcklig craft; `inscribe cloth` → scroll i inventory med `db.recipe == "cloth"`, material förbrukat; utan kunskap → guard-meddelande.
- **Commit:** `feat(knowledge): add inscribe command to write single-recipe scrolls`

### Task F.2 — `learn`-kommando (läs en scroll)
- **Goal:** Läs en scroll → lär receptet permanent; scrollen förbrukas.
- **Dependencies:** F.1, A.1.
- **Implementation:** `CmdLearn` (`key="learn"`): sök scroll (`learn <scroll>` / `learn from <scroll>`); läs `name = scroll.db.recipe`; None → "There's nothing to learn from that."; `learn_recipe(name)` returnerar `False` (redan känt) → "You already know this recipe." och **förbruka inte** (var snäll); annars success-meddelande + `scroll.delete()`. (`learn` utökas i G.3 att även ta böcker.)
- **Testing:** `@py` skriv en scroll (F.1), ny karaktär, `learn <scroll>` → known-set får receptet, scroll borta; upprepa → "already know", ingen scroll att förbruka.
- **Commit:** `feat(knowledge): add learn command to study recipe scrolls`

---

## 12. Component G — Book  *(förgänglig bulk-transfer)*

Multi-recept `DurableObject` som nöts per studie tills den vittrar. Bygger på F:s `learn`.

### Task G.1 — `Book(DurableObject, Object)`-typeclass
- **Goal:** Ett förgängligt föremål som håller flera recept och visar sitt slitage.
- **Dependencies:** `typeclasses/durable.py`, F (scroll-mönstret).
- **Implementation:** `typeclasses/books.py::Book(DurableObject, Object)` — ärver `condition`/`apply_wear`/`is_broken`/`get_display_desc` (condition-rad på `look` gratis). `db.recipes` = lista recept-namn. `get_display_desc` utökas: condition-rad + "The pages hold N recipes." (lista ej namnen på `look` — kräv studie). Ingen repair (MVP — bevarar sinken; bok-repair → BACKLOG). Start-condition sätts av `scribe` (G.2), ej hårdkodat här.
- **Testing:** `@py` (importerbar host krävs — scratch om nödvändigt) spawna en `Book`, sätt `db.recipes=["cloth","leather"]`, `look` visar condition + "2 recipes"; `apply_wear(120)` → `is_broken` True.
- **Commit:** `feat(books): add perishable Book typeclass holding multiple recipes`

### Task G.2 — `scribe`-kommando (skriv en bok)
- **Goal:** Efter högre expertis: samla flera recept i en bok med start-condition efter skicklighet.
- **Dependencies:** G.1, F.1 (`_can_transmit`), skrivmaterial.
- **Implementation:** `CmdScribe` (`key="scribe"`, t.ex. `scribe book of cloth, leather`): parsa recept-lista; **kräv `_can_transmit` för VARJE listat recept** (du kan bara skriva ned det du bemästrat) + en högre bok-tröskel än scroll (**tuning:** flat Craft ≥ 50 "professional", eller `max(min_skill)+N` — låses i G-chatten); förbruka mer material än scroll (bokbindning: parchment×N + `leather` omslag + `twine`); spawna `Book`, sätt `db.recipes`; start-`condition` skalad av craft-utfall (`skill_check` → band → t.ex. superior 100 / success 80 / … via ett litet band→condition-table, speglar E.3-mönstret). Cooldown.
- **Testing:** `@py` känn cloth+leather över tröskel; `scribe book of cloth, leather` → Book med `db.recipes==["cloth","leather"]`, condition satt, material förbrukat; ett okänt recept i listan → guard.
- **Commit:** `feat(knowledge): add scribe command to compile perishable recipe books`

### Task G.3 — `learn` från bok (nöt per studie)
- **Goal:** Studera ett recept ur en bok → lär det; boken nöts; en tömd bok vittrar bort.
- **Dependencies:** G.1, F.2 (`CmdLearn`), A.1.
- **Implementation:** Utöka `CmdLearn` att ta böcker: `learn <recipe> from <book>` — validera att receptet finns i `book.db.recipes`; `learn_recipe(name)` (`False` = redan känt → meddelande, **nöt inte** boken); annars success + `book.apply_wear(BOOK_WEAR_PER_STUDY)`. **Mikro-val (lås i G-chatten):** studien som skulle ta condition ≤0 *slutförs* (du får receptet) och boken vittrar bort (`book.delete()`) — sista lektionen — kontra "bruten bok = kan ej studeras, lingrar" (parallellt med brutet verktyg). Rekommendation: slutför-då-vittra (`delete`), håller sinken ren och undviker husk-skräp.
- **Testing:** `@py` skriv en bok med låg condition; `learn cloth from book` upprepat → known-set får receptet, condition sjunker; studien som når 0 lär + raderar boken; redan-känt receptet nöter inte.
- **Commit:** `feat(knowledge): learn recipes from books, wearing them down per study`

---

## 13. Component H — Teaching  *(synk personlig transfer)*

Gratis men kräver närvaro + samtycke. Legend-troget: Teaching-*skill* är ingen gate.

### Task H.1 — `teach`-handshake
- **Goal:** En kunnig lär ut ett recept till en samtyckande spelare i samma rum.
- **Dependencies:** A.1, F.1 (`_can_transmit`), barter-handshake-mönstret (`PWTradeHandler` timeout/staleness), `cooldowns`.
- **Implementation:** `CmdTeach` (`key="teach"`, `teach <recipe> to <player>`): guards — samma location, target är en spelad Character, `_can_transmit(caller, name)` (känner + `min_skill`; Teaching-skill EJ krävd). Skicka target ett pending-offer (som barter: en handler eller ett `db.pending_teach`-tuple med timeout + lärare-ref + recept-namn), meddela båda. Target accepterar via `accept` (återanvänd/parallellt barter-accept) eller ett dedikerat svar → **backstop-validering vid accept** (lärare fortfarande närvarande + kan fortfarande receptet — barter-`finish()`-lärdomen) → `student.learn_recipe(name)` + meddela båda + cooldown på läraren. Stale/timeout/olika-rum vid accept → avbryt tyst. Gratis (inget material). Multiplayer: handshake hindrar icke-samtyckande kunskaps-injektion; cooldown mot spam.
- **Testing:** Tvåspelar-test (eller två puppets): `teach cloth to Bob` utan kunskap → guard; med kunskap → Bob får offer, `accept` → Bob:s known-set får cloth; lärare lämnar rummet före accept → avbrutet.
- **Commit:** `feat(knowledge): add teach command with consent handshake`

---

## 14. Component I — Tunn world-loot-scroll-seed  *(säkerhetsventil)*

Så ett recept inte blir ovinnbart om dess profession saknas online.

### Task I.1 — Seeda scrolls i världen
- **Goal:** Ett litet, deterministiskt utbud av recept-scrolls finns att hitta i världen.
- **Dependencies:** F.1 (scroll-prototyp/-stämpel), världs-content-inhak (I-chattens source-verify).
- **Implementation:** Tunn: en seeding-mekanism som placerar N scrolls (stämplade med utvalda avancerade recept) i utpekade rum — t.ex. ett `@batchcommand`/seed-script eller en enkel `Script` som spawnar in dem en gång i ett "ruined library"-rum. Ingen loot-table-infra byggs här (deferrbart); målet är säkerhetsventilen, inte ett drop-system. **Deferr-kandidat till BACKLOG om världs-content-plumbing inte är redo** — logga i så fall och lämna profession-grant + reverse-eng som de aktiva kanalerna tills vidare.
- **Testing:** Kör seeden → utpekat rum innehåller scrolls med korrekt `db.recipe`; `learn` fungerar på en seedad scroll.
- **Commit:** `feat(knowledge): seed a thin world supply of recipe scrolls`

---

## 15. Backlog (utanför denna stages scope)

Konsolideras i `docs/BACKLOG.md` samma pass (en sanningskälla; trimma origin till pekare):

- **Teaching-skill som amplifier** — Legends Teaching (INT+CHA) som *bonus* (kortare `teach`-cooldown / fler samtidiga elever / lägre studie-slitage), aldrig en gate. Ankare: Legend p.72–73; denna decomp §2 (d).
- **Bok-repair ("återbind")** — låt en vittrad bok repareras i stället för att raderas. Avsiktligt uteslutet i G för att hålla sinken. Ankare: §12 G.3.
- **`CmdCraftGated` fuzzy-duplicering** — konsolidera mot ett publikt contrib-resolver-API om ett sådant stabiliseras. Ankare: §7 B.2.
- **Maker's-mark/individuering** — `obj.db.recipe`-stämpeln (E.1) + `crafted_by` matar "a steel dagger of <smith>"-alias och search/disambiguation-fixen. Ankare: BACKLOG Rev 2 + roadmap §backlog.
- **Parchment som hide-härledd primitiv** — om F/G väljer den nya primitiven framför material-återbruk, knyt den till harvest-ekonomin. Ankare: §11 F.1.
