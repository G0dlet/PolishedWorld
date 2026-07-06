# PolishedWorld — Skill Improvement Decomposition (Stage 1)

> **Rev 1 · 2026-07-06** — first version header. Written after live source-verification of `main` (post-`feature/hunting` merge). Records the greenfield finding (`check_skill_improvement` does **not** exist), the verbatim Legend Improvement-Roll rule, the four locked design decisions, and the A–E component breakdown.
> **Canonical:** `docs/PolishedWorld_Skill_Improvement_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If this project-knowledge copy's Rev is lower than the repo's, it's stale — re-upload from the repo.

**Feature branch:** `feature/skill-improvement`
**Status:** Decomposed & source-verified. Task A.1 next (greenfield primitive).
**Philosophy:** skynda långsamt — bygg en *helt smal men komplett* vertikal skiva (primitiv → trigger → felt-progress) för de skills som faktiskt har check-sites (`craft`, `hunting`), validera in-game, tuna siffrorna sen. Ja till "balansera sen", nej till "validera sen".

---

## 1. Varför den här featuren

Roadmap §Stage 1: idag *växer inga skills*. En skill-check konsumerar `skill_value` men matar aldrig tillbaka. Det gör survival-/craft-/hunt-loparna platta — ingen känsla av att bli bättre. Stage 1 stänger den återkopplingen: **använd en skill → chans att förbättra den → omedelbar synlig progress.**

Legends kanoniska väg (GM delar ut Improvement Rolls vid story-beats) **portar inte** till en persistent multiplayer-värld — det finns ingen GM och "rest" är inte samma sak som ett narrativt beat. Vi ersätter den med **improvement-on-use som resolvar vid själva skill-checken** (RuneScape-/RuneQuest-nära): omedelbar feedback, belönar aktivitet. Detta är en medveten adaption, inte en Legend-avvikelse av slarv.

---

## 2. Designbeslut låsta den här sessionen

| Beslut | Val | Konsekvens |
|--------|-----|------------|
| **Pacing/display** | **Rå % som enda mekanisk sanning, on-use, ingen accumulator, ingen badge än** | Legend-formeln self-throttlar redan (låga skills hoppar, höga kryper) → RS-nära känsla gratis. Badge först om playtesting visar att % läses platt. |
| **Eligibility + rate-limit** | **success/critical-only + mot verklig svårighet + cooldown-gate per skill** | On-use har ingen knapp valuta som i kanon → grinden till *rollen* är strypventilen. Misslyckanden lär inget; triviala auto-pass betalar inte; Cooldowns-contrib kappar spam. |
| **HP-formel** | **Behåll `CON×2` för Stage 1** | Kanonisk General HP = `round((CON+SIZ)/2)`, men med dagens uniforma 10/10-stats vore det en ren nerf (10 vs 20) + migration som halverar allas HP, utan uppsida. SIZ-tillväxt rör inte HP ännu. General HP paras med Legend-chargen. |
| **Characteristic-trigger** | **Stage 1 = skill-loop + HP-recompute-*hook*; characteristic-*höjning* minimal/uppskjuten** | Kanon = spendera-N-rolls (ingen tärning); on-use saknar roll-valuta. HP-hooken (`update_health_max` vid CON-ändring) byggs; själva höjningstriggern hålls till admin/test tills chargen ger stat-variation värd att odla. |

Alla fyra är avsiktligt öppna för omjustering senare — de flyttar skelettet, inte balansen.

---

## 3. Verifierade källankare (source-first) — "live source wins"

Kontrollerat mot `main` @ raw.githubusercontent.com + `/mnt/project/Legend.pdf` innan dekomposition:

- **`check_skill_improvement` finns INTE.** Repo-wide grep (`--include=*.py`) → noll träffar utom en kommentar i `characters.py:252`. Inget improvement-/skills-kommando i `character_commands.py` (bara `status`/`stats`/`skills`/`sheet` display). **Stage 1 är greenfield, inte en patch.** De "tre kända avvikelserna" (saknad INT-bonus, 1D3 istf 1D4+1, ingen garanti-+1) beskrev en tänkt implementation — de blir nu **specen** för A.1, inte fixar.
- **`world/skillcheck.py`** → `skill_check(skill_value, modifier=0)` är den *rena* single-chokepointen. Returnerar `{"result","success","roll","target","margin","crit_score"}`. Tar en `int`, känner varken karaktär eller skill-nyckel → improvement-lagret måste ligga **ovanpå**, inte inuti. Speglar dess renhetsdisciplin i `world/improvement.py`.
- **Call-sites för `skill_check`** (= hook-yta för on-use), exakt fyra, mappar till två skills:
  - `world/crafting_base.py:153` → **craft**
  - `commands/repair_commands.py:108` → **craft**
  - `commands/hunting_commands.py:255` (`skill_check`) + `:96` (`opposed_check`) → **hunting**
  - `perception`/`stealth`/`athletics` har **inga** call-sites → vilande, byggs inte för spekulativt. De hakar på gratis dagen något rullar mot dem.
- **`typeclasses/characters.py`** — tre TraitHandlers: `stats` (static: str/dex/con/siz/int/pow/cha), `traits` (gauge: hunger/thirst/fatigue/health), `skills` (counter, `base`/`current`/`mod`, `max=100`). `update_health_max()` räknar `con.value * 2` (läser bara CON, aldrig SIZ). INT läses via `self.stats.int.value`.
- **Legend Improvement Roll — verbatim** (`Legend.pdf`, "Using Improvement Rolls", ~rad 3480):
  - Rulla 1D100, **addera hela INT-Characteristicen** (inte en tabell-modifier — CHA-tabellen styr *antalet* rolls, inte roll-bonusen).
  - `(1D100 + INT) > current skill` → **+1D4+1**.
  - `(1D100 + INT) ≤ current skill` → **+1** (garanterat golv, aldrig 0).
  - `>100 %`-band (mål 100 + halverad INT per 100%-band) — **intentionally deferred**; MVP kappar vid 100, dead code precis som `opposed_check`:s >100%-not. Dokumenterad TODO-hook i A.1, byggs när caps lyfts.
  - **Self-throttle:** rollen måste *överstiga* current skill → låga skills får ofta 1D4+1, höga skills nästan alltid +1. Detta är pacing-motorn; ingen hidden accumulator behövs.
- **Characteristic-improvement (kanon):** höja 1 poäng kostar `current value` improvement rolls (10→11 = 10), inga tärningar. Relevant för varför on-use-höjning behöver egen adaption (uppskjuten, se beslut 4).

---

## 4. Beroendegraf

```
[A improvement.py]  (ren primitiv, source-first spec)
        │
        ▼
[B improve_skill_on_use]  (Character-chokepoint) ──> [B.2 eligibility-gate: success + real-diff + cooldown]
        │                                                     │
        │                                                     └──> hookas i [B.3] craft (craft skill) + hunt (hunting skill)
        ▼
[C felt-progress]  C.1 tick-feedback → C.2 tröskel-celebration (25/50/75/100) → C.3 `progress`-kommando (delta sedan login)
        │
        ▼
[D characteristic + HP]  D.1 minimal char-höjning (admin/test) → D.2 CON-höjning → update_health_max
        │
        ▼
[E migration]  engångs-backfill av per-char state (login-baseline), guardat get(...) is None
```

**Minimal vertikal skiva** = A + B + C.1 (använd craft/hunting → skill växer synligt). Resten är påbyggnad.

---

## 5. Sessionsplan

| Session | Tasks | Resultat |
|---------|-------|----------|
| **A — Primitiv + on-use-spine** | A.1, B.1, B.2, B.3 | Craft/hunt-checks kan förbättra respektive skill, gated & rate-limitat |
| **B — Felt-progress** | C.1, C.2, C.3 | Tick-feedback, tröskel-celebration, `progress`-kommando (delta sedan login) |
| **C — Characteristic + HP** | D.1, D.2 | HP-recompute-hook vid CON-höjning; minimal char-höjning (admin/test) |
| **D — Migration** | E.1 | Befintliga hårdkodade chars grandfathrade för ny per-char state |

---

## 6. Component A — Improvement-primitiv (ren, testbar)

### Task A.1 — `world/improvement.py`
- **Goal:** En *ren* funktion `improvement_roll(skill_value, int_char)` som implementerar Legends ≤100 %-Improvement-Roll (1D100 + INT vs current → +1D4+1, annars garanterat +1).
- **Dependencies:** inga (spegling av `world/skillcheck.py`:s renhet; ingen Evennia-import).
- **Approach (key shape):**
  ```python
  # world/improvement.py
  from random import randint

  def improvement_roll(skill_value, int_char):
      roll = randint(1, 100)
      total = roll + int(int_char)
      beat = total > int(skill_value)          # rollen måste ÖVERSTIGA current skill
      gained = (randint(1, 4) + 1) if beat else 1   # +1D4+1 vid beat, annars garanterat +1
      return {"gained": gained, "roll": roll,
              "int_bonus": int(int_char), "total": total, "beat": beat}
  ```
  `>100 %`-bandet (mål 100 + halverad INT) lämnas som dokumenterad TODO — MVP kappar vid 100, oåtkomlig kod idag (samma linje som `opposed_check`).
- **@py test (smoke):** `@py from world.improvement import improvement_roll; print(improvement_roll(25, 10))`
- **evennia shell (self-throttle):** loop 1000× på skill=20 vs skill=90, samma INT=10 → låg skill ~90 % beat, hög skill ~20 % beat; `gained ∈ {1,2,3,4,5}` vid beat, alltid `≥1`.
- **Commit:** `feat(improvement): add pure Legend improvement-roll primitive`

---

## 7. Component B — On-use-trigger

### Task B.1 — `Character.improve_skill_on_use(skill_key)`
- **Goal:** Chokepoint på `Character` som läser INT + current skill, anropar A.1, applicerar gain på `skills.<key>.current` (guardat, kappat vid `max=100`), returnerar delta + ev. korsad tröskel.
- **Dependencies:** A.1; `typeclasses/characters.py` TraitHandlers.
- **Approach:** läs `self.stats.int.value` + `self.skills.get(skill_key)`; `res = improvement_roll(skill.value, int_val)`; `skill.current = min(skill.max or 100, skill.current + res["gained"])`. Returnera `{"delta", "old", "new", "crossed"}`. Analog med `apply_health_damage` (single HP-loss chokepoint).
- **Multiplayer:** read-modify-write på `.current` — enkeltrådad Twisted-reactor serialiserar, men notera antagandet.
- **@py test:** sätt `char.skills.craft.current = 20`, kör metoden, verifiera `current` växte med `delta`.
- **Commit:** `feat(characters): add improve_skill_on_use chokepoint`

### Task B.2 — Eligibility-gate
- **Goal:** Ett test som avgör om en given check får trigga improvement: **success/critical** + **verklig svårighet** + **cooldown** per skill.
- **Dependencies:** B.1; Cooldowns-contrib (redan i bruk, `self.cooldowns`).
- **Approach:** gate-funktion tar `(outcome_dict, skill_key)` → bool. Success-only: `outcome["success"]`. Real-diff: hoppa om effektiv target ≥ tak *eller* call-site flaggat trivialt. Cooldown: `self.cooldowns.ready(f"improve_{skill_key}")`, sätt `self.cooldowns.add(...)` vid tick. Cooldown-längd = ratt (game-minuter), tunas senare.
- **@py test:** kör gate två gånger i rad → andra blockad av cooldown; kör med `success=False` → blockad.
- **Commit:** `feat(improvement): gate on-use ticks by success + cooldown`

### Task B.3 — Hooka call-sites
- **Goal:** Craft (crafting_base + repair) och hunt anropar B.1 via B.2 efter `skill_check`.
- **Dependencies:** B.1, B.2; `world/crafting_base.py`, `commands/repair_commands.py`, `commands/hunting_commands.py`.
- **Approach:** efter varje `outcome = skill_check(...)`: `if gate(outcome, skill_key): caller.improve_skill_on_use(skill_key)`. `crafting_base.py` är world-lager (recept-spawn) → hämta craftaren korrekt; hunt/repair är commands (`caller`).
- **@py test:** kraft-check med hög success-sannolikhet → craft-skill växer (efter cooldown-reset); hunt likaså.
- **Commit:** `feat(improvement): trigger on-use improvement at craft and hunt checks`

---

## 8. Component C — Felt-progress / legibility

### Task C.1 — Tick-feedback
- **Goal:** Omedelbart meddelande vid meningsfull tick: `"Your Crafting improves! (+3, now 41%)"`.
- **Dependencies:** B.1 (returnerar delta).
- **Commit:** `feat(improvement): message the player on each skill tick`

### Task C.2 — Tröskel-celebration
- **Goal:** Extra markering vid 25/50/75/100 (desc-tier-korsning är naturlig hook: `"You are now a |ytracker|n."`).
- **Dependencies:** B.1 (`crossed`), skill-`descs`.
- **Commit:** `feat(improvement): celebrate skill milestone thresholds`

### Task C.3 — `progress`-kommando (delta sedan login)
- **Goal:** Legibility-yta: visa hur mycket varje skill växt sedan senaste login.
- **Dependencies:** per-login-snapshot: baseline fångas i `at_post_puppet`, diffas on-demand (`AttributeProperty`).
- **Multiplayer:** snapshot per karaktär, inget delat state.
- **@py test:** sätt baseline, tick:a en skill, kör `progress` → visar +delta.
- **Commit:** `feat(commands): add progress command showing skill deltas since login`

---

## 9. Component D — Characteristic + HP (gated på beslut 3 & 4)

### Task D.1 — Minimal characteristic-höjning
- **Goal:** Admin/test-väg att höja en Characteristic (ingen on-use-trigger än — uppskjuten tills chargen ger variation).
- **Commit:** `feat(characters): add admin path to raise a characteristic`

### Task D.2 — HP-recompute-hook
- **Goal:** CON-höjning → `update_health_max()` körs så HP-taket följer med (bevarar HP-%).
- **Dependencies:** D.1; befintlig `update_health_max` (CON×2 per beslut 3; SIZ rör ej HP än).
- **@py test:** höj CON, verifiera `health.base` ökade och `current` skalades proportionellt.
- **Commit:** `feat(characters): recompute max HP on characteristic increase`

---

## 10. Component E — Migration / backfill

### Task E.1 — Grandfather befintliga chars
- **Goal:** Engångs-batch ger existerande hårdkodade karaktärer ev. ny per-char state (login-baseline etc.), identiskt med nyskapade.
- **Dependencies:** vilken state B/C inför; `world/character_migrations.py` (finns, utöka).
- **Approach:** guarda med `get(...) is None` — `TraitHandler.add()` defaultar `force=True` och skulle annars förstöra befintlig `.current` (samma fälla som hunting-backfillen H2.1).
- **@py test:** kör migrate på gammal char → ny state finns, gamla skill-`current` orörda.
- **Commit:** `feat(migrations): backfill skill-improvement state for existing characters`

---

## 11. Öppna trådar / backlog (Stage-1-adjacent)

- **`>100 %`-improvement-band** — implementeras när skill-caps lyfts (target 100 + halverad INT per 100%-band). Hook finns i A.1.
- **General HP `round((CON+SIZ)/2)`** — byts in tillsammans med Legend-chargen (då SIZ-variation gör det meningsfullt), med grandfathering av befintliga HP.
- **Characteristic on-use-trigger** — hur STR/CON/etc. växer av användning i en on-use-värld (kanon = spendera-rolls, portar inte). Designas när chargen landat.
- **Vilande skills** (`perception`/`stealth`/`athletics`) — får improvement gratis så snart de får riktiga check-sites; bygg inte i förväg.
