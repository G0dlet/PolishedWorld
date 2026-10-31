# PolishedWorld — Recipe Mastery Decomposition

> **Rev 2 · 2026-10-31** — **closed out: the feature is merged** (`abe9e6b`, tree `2e71112`, parents `1c00951` and `129618e`; the whole suite, 971 tests in 43 modules, run at home on `129618e` before the merge and again on `abe9e6b` after it, OK). §11 records the seven code tasks and the merge in shipping order, and each task in §5–§9 gains a *Shipped* line with what the build changed from the text above it; those departures were locked task by task and are not reopened here. §4 and §10 disagreed on the order of M6.1 and M6.2; the merge went first (§10). OQ1, OQ2 and OQ5 are closed; OQ3 and OQ4 stay with E.2. §3 gains a re-read at `abe9e6b` and one correction (`world/skill_xp.py:131` was a blank line). M6.1 itself found two of its instructions already done by Rev 1's own commit — the roadmap's *single-purpose* note (MD5) and the struck *111 → ~113* (MD4) — and one of them wrong: *README: no change* was false, because README's index row quotes the lesson range (lesson 193).
> **Rev 1 · 2026-10-30** — first version. Decomposes the roadmap's second alpha prerequisite, *per-recipe mastery* (alpha entry (A); order fixed by (F): after weight, before E.2), into six components and nine tasks, against live source read the same day (`main` at `8aeb91c`, tree `8d33202`; Evennia 6.1.0; `Legend.pdf` core, *Teaching* and *Teachers and Mentors*). The roadmap's backlog entry (Rev 16, 2026-08-11) and the decision-log entry *Craft specialisation model* were read against the code first; of the ten premises checked, four did not survive and are corrected here: the write site is not the `_should_produce` branch, which is always taken under the `"raw"` policy every recipe inherits (MD2); there is no quality ceiling to lift, because P-7 removed the skill cap (MD4); the transmission switch leaves `min_skill` with three readers, not one (MD5); and which commands write the counter had to be decided, because scribe, repair and disassemble also roll Craft (MD2). Locks **MD1–MD9**. **One BACKLOG entry is taken:** *`skill_check` has no automatic success (01–05) or automatic failure (96–00)*, whose trigger names this feature (MD8, M5.1). No code.

**Canonical:** this document, for the feature; `docs/roadmap.md` for its place in the alpha; `docs/PolishedWorld_Recipe_Knowledge_Decomposition.md` for the knowledge layer it gates.
**Status:** DONE. Merged to `main` 2026-10-31 as `abe9e6b` (tree `2e71112`); every task's record is in §11.
**Feature branch:** `feature/recipe-mastery` (one branch, one merge), cut from `f8c8e5b`, merged 2026-10-31 and deleted on origin and at home.
**Rough scope:** 9 tasks, ~2 sessions at 5 h/week (M1 1–1.5 · M2 1.5 · M3 1 · M4 1.5–2 · M5 1 · M6 0.5). *(Actual: three build sessions and a close-out, sessions 2–5.)* Small because the pattern exists: `world/skill_xp.py` is the handler to copy, `do_craft` already has the roll and the improvement call to sit beside, and `_can_transmit` is one function with three callers.
**Philosophy:** skynda långsamt — one counter, one writer, one modifier term, one gate switch. No ticker, no migration, no new command; `recipes` grows two modes.

---

## 1. Why this feature

Two measured gaps, both in the roadmap entry and both confirmed at `8aeb91c`.

**The teaching gate is generic.** `_can_transmit` (`world/knowledge.py:43`) answers *may this character inscribe, scribe or teach this recipe* with *knows it* and *permanent Craft (`.current`) ≥ the recipe's `min_skill`*. Craft is one trait for every recipe, so a crafter at Craft 60 who learned the waterskin from a scroll yesterday may teach it today, having never made one. Legend's own teacher rule is relative, not absolute — *anyone can act as a teacher or mentor as long as they have at least 20% more in the skill being taught* (`Legend.pdf`, *Teachers and Mentors*) — and still generic, because the skill is still Craft. Neither rule can say *this person has made this thing*.

**Specialisation does not exist.** Every recipe rolls the same `craft` trait (`MongooseCraftRecipe.skill_name`), so a weaver and a tanner at the same Craft are the same character. Legend's answer is to split Craft — *like the Lore skill, the Craft skill is actually several separate skills grouped under a single* heading — and the decision log rejected that on 2026-08-11: a DB-stored trait migration, and still no way to tell a waterskin from twine inside one trade.

Per-recipe mastery closes both with one number: a completed-craft count per recipe and character. The count gates transmission (you teach what you have made) and nudges the roll (you make better what you have made often), and it never gates crafting itself.

**One premise this document retires.** The roadmap entry says mastery *lifts the quality ceiling 111 → ~113*. 111 was the ceiling when Craft was capped at 100 (Crafting Progression Rev 8: skill 100 + superior tool 10 → `crit_score` 11). Skill Progression's **P-7** removed the cap (`typeclasses/characters.py:349` *No max*; `world/progression.py:54` *level 150 → 30 628 XP*) and `skill_check` never clamps `target`, so quality on a critical is `100 + target // 10` with no ceiling at all. No document reconciled the figure after P-7; this one does (MD4).

## 2. Decisions locked 2026-10-30 (MD1–MD9)

**MD1 — One counter per recipe and character.** `RecipeMasteryHandler` in a new `world/recipe_mastery.py`, wired as `@lazy_property` `recipe_mastery` on `Character` beside `skill_xp` (`typeclasses/characters.py:176`), storing one Attribute `recipe_mastery`: a mapping from canonical recipe name (`MongooseCraftRecipe.name`, the key `knows_recipe` uses) to an integer count. The handler copies `SkillXPHandler`'s shape (`world/skill_xp.py:85`): `_store()` reads through `collections.abc.Mapping`, never `isinstance(..., dict)`, because Evennia hands back a `_SaverDict`; writes go through `attributes.add` with a fresh dict; an invalid amount raises; a recipe name the registry no longer knows is kept, and `all()` unions stored keys with the registry so an orphan stays visible. No backfill: every character starts at 0 in every recipe, including characters who have crafted for months. Mastery is an Attribute on the Character, so it survives death like skills and knowledge (death policy (i), not permadeath).

**MD2 — Exactly one writer, gated on the check, in `do_craft`.** The roadmap entry placed the write *inside the `_should_produce` branch, so successes and criticals count and fumbles do not*. At `8aeb91c` that branch filters nothing: `_should_produce` (`world/crafting_base.py:210`) returns `True` for every tier under `consume_policy == "raw"`, and all 29 recipes inherit `"raw"` (`:60`; no override in `world/recipes.py`), so failures (quality 50) and fumbles (25) spawn there too. The gate that means *the check succeeded* is `outcome["success"]`, the one `attempt_skill_improvement` already uses (`typeclasses/characters.py:884`). The write therefore sits in `do_craft` directly after the improvement call (`:323–324`), guarded by `outcome["success"]`, and before the produce branch. Not in `post_craft` (`:347`): since W5.1 that hook consumes, delivers and messages, and a product set down on the floor at the ceiling is still a product made — the count is a fact about the roll, not about delivery. **Only `do_craft` writes.** Scribe (`commands/crafting_commands.py:828`), disassemble (`:579`) and repair (`commands/repair_commands.py:137`) roll Craft but are not the making of a recipe; they neither read nor write the counter.

**MD3 — A roll modifier, never a gate.** `_mastery_modifier()` on `MongooseCraftRecipe` returns `min(MASTERY_CAP, MASTERY_STEP * (count // MASTERY_STEP_SIZE))` with `MASTERY_STEP = 5`, `MASTERY_STEP_SIZE = 5`, `MASTERY_CAP = 20` — +5 per five completed crafts, +20 from the twentieth — and joins the roll as a third term: `skill_check(self._skill_value(), self._tool_modifier() + self._physical_modifier() + self._mastery_modifier())` (`:291`). Full mastery exactly cancels `improvised_penalty = -20` (`:86`), the stance `_tool_modifier` already takes. `skill_check` does not clamp (`world/skillcheck.py:70`), so the extremes are honest: Craft 22 (the lowest chargen start), no tool, overloaded is a target of −18 without mastery and 2 with it; Craft 100, superior tool, full mastery is 130. Nothing in crafting ever refuses an attempt for lack of mastery.

**MD4 — There is no quality ceiling; mastery adds up to +2 to `crit_score`.** Quality on a critical is `QUALITY_BY_TIER["critical"] + outcome["crit_score"]` (`:202–208`) and `crit_score = max(0, target // 10)` (`world/skillcheck.py:94`), unclamped; with P-7's uncapped skill the ceiling does not exist. Mastery's +20 raises `target // 10` by 2 at every skill level. The roadmap's *111 → ~113* is struck, not corrected — it had no referent after P-7.

**MD5 — Transmission gates on mastery alone; `min_skill` keeps three readers.** `_can_transmit(char, recipe_name)` becomes *knows the recipe AND `char.recipe_mastery.count(recipe_name) >= MASTERY_TRANSMIT_THRESHOLD`*, with `MASTERY_TRANSMIT_THRESHOLD = 5` (the first step). The `.current >= min_skill` clause is removed: a crafter who has completed five of a recipe has met its floor five times. The three callers — inscribe (`commands/crafting_commands.py:652`), scribe (`:772`), teach (`:933`) — keep their `requires_knowledge` guard, which is where *common recipes cannot be transmitted* has always lived (`_can_transmit`'s own docstring says so), and that is what makes grinding self-limiting: mastering twine is worth nothing. The decision log's *leaves `min_skill` single-purpose* was true on 2026-08-11 and is not now: `world/recipes.py:35–37` counts four readers, and after the switch three remain — the craft floor (`.value`), disassemble's `-min_skill` modifier, and the recipe displays. What the switch does close is the `.value`/`.current` double semantics on the transmission path, which was Component E's reason for wanting it first.

**MD6 — `discipline` is for display.** Every recipe class carries one `discipline` string, required: a registry test fails on a recipe without one. `recipes` gains a per-discipline summary (bare `recipes` keeps its current list and adds one line per discipline with *known / mastered-to-teach*), `recipes <discipline>` lists that discipline's recipes with the viewer's count and modifier, and `recipes <name>` shows the count, the modifier and the next step. Titles are cosmetic and read from the **highest single-recipe count** in the discipline: 5 *Apprentice*, 10 *Journeyman*, 20 *Master* (the cap). No sum, no average, no mechanical read of `discipline` anywhere: cross-recipe aggregation would reintroduce the generic competence the counter exists to remove. `discipline` is deliberately not `PROFESSIONS` (CC2's four packages are what a character starts knowing; a discipline is what a recipe is). The set is OQ1, closed by M4.1.

**MD7 — Progression isolation.** Mastery enters the roll only as a `skill_check` modifier. `attempt_skill_improvement` reads `outcome["success"]` and nothing else from the outcome, and `improve_skill_on_use` reads the trait's `.current` (Evennia Ref §3.5: progression reads `.current`, resolution reads `.value`), so the improvement roll's target is unchanged by mastery, as it is unchanged by a tool. This is pinned by a test in M2.2, not by this paragraph.

**MD8 — Mastery takes the `skill_check` BACKLOG entry.** Legend: *Any test result of 01 to 05 is an automatic success. Any test result of 96 to 00 is an automatic failure.* At `8aeb91c` a target of 3 fails on 04 and a target of 97 succeeds on 96–97. MD3 makes the low end real (−18 → 2 is the whole difference mastery makes to an overloaded, tool-less beginner), and this feature already writes tests against the roll's modifier, so it adopts the rule rather than recording the departure. Resolution order in `skill_check`: fumble (99–00 below 100 %, 00 at or above) → automatic failure (96–98; 96–99 at or above 100 %) → critical (`roll <= max(1, ceil(target / 10))`) → automatic success (01–05) → `roll <= target` → failure. A roll of 01 stays a critical. Tests at targets 0, 3, 97 and 120. Own task (M5.1), own commit, last code task so the earlier tasks' predicted counts are not disturbed by a change every skill test flows through.

**MD9 — Unnumbered.** Alpha prerequisite 2 by decision (A), kept unnumbered for Rev 17's reason: stage numbers are cited by name in BACKLOG triggers and production comments, and one invented on a guess is expensive to unwind. The catalogue the Rev 16 note waited for exists (AC4, AC5.1); it changes the size estimate, not the reason.

## 3. Verified source anchors (read 2026-10-30, `main` at `8aeb91c`)

| What | Where |
| --- | --- |
| `consume_policy = "raw"` default | `world/crafting_base.py:60` |
| `improvised_penalty = -20` | `world/crafting_base.py:86` |
| `QUALITY_BY_TIER` | `world/crafting_base.py:100` |
| `_physical_modifier` (W3.1) | `world/crafting_base.py:122` |
| `_tool_modifier` | `world/crafting_base.py:163` |
| `_quality_for` (critical adds `crit_score`) | `world/crafting_base.py:202–208` |
| `_should_produce` (`True` for every tier under `"raw"`) | `world/crafting_base.py:210` |
| `do_craft`; the roll; the improvement call; the produce branch | `world/crafting_base.py:285`; `:290–292`; `:323–324`; `:326` |
| `post_craft` (consume, deliver, message; W5.1) | `world/crafting_base.py:347` |
| `skill_check`: `target = skill + modifier`, unclamped; `crit_score = max(0, target // 10)` | `world/skillcheck.py:70`; `:94` |
| `_can_transmit` (knows + `.current >= min_skill`) | `world/knowledge.py:43` |
| `_RECIPE_CLASSES` / `_load_recipes()` registry | `world/knowledge.py:29–39` |
| `min_skill` read four ways | `world/recipes.py:35–37` |
| `SkillXPHandler`; the `_SaverDict` / `Mapping` note; `attributes.add` | `world/skill_xp.py:85`; `_store` `:128`, the note in its docstring `:133–138` (Rev 2: `:131`, as first written, is a blank line); `:242` |
| `Character.skill_xp` `@lazy_property` | `typeclasses/characters.py:176` |
| `attempt_skill_improvement` (reads `outcome["success"]` only) | `typeclasses/characters.py:884` |
| skills have no `max` (P-7) | `typeclasses/characters.py:349` |
| `CmdRecipes` (bare list; `recipes <name>` detail) | `commands/crafting_commands.py:361` |
| disassemble's roll (`-min_skill + physical_modifier()`) | `commands/crafting_commands.py:579` |
| inscribe / scribe / teach call `_can_transmit` | `commands/crafting_commands.py:652`; `:772`; `:933` |
| scribe's own Craft roll | `commands/crafting_commands.py:828` |
| repair's Craft roll | `commands/repair_commands.py:137` |
| one timed-action slot per character (`ndb.timed_action`) | `world/timed_actions.py:8` |
| `test_known_but_below_skill_floor_blocks` and the three siblings | `tests/test_knowledge.py:198–225` |
| the `patch("world.skillcheck.randint")` pattern for forced outcomes | `tests/test_cloth_goods.py:204` |
| Legend *Teaching (INT+CHA)*; *Teachers and Mentors* (20 % more) | `Legend.pdf` text ~3206; ~3579 |
| Legend *Automatic Success and Failure* | `docs/BACKLOG.md`, the `skill_check` entry |

**Re-read at `abe9e6b` (Rev 2).** The table above is the decomposition's snapshot at `8aeb91c` and stays as written; the feature moved most of its `world/crafting_base.py` rows. Where they are now: `consume_policy` `:63`; `discipline = None` `:85`; `improvised_penalty` `:97`; `QUALITY_BY_TIER` `:111`; `_physical_modifier` `:133`; `_mastery_modifier` `:144`; `_tool_modifier` `:188`; `_quality_for` `:227`; `_should_produce` `:235`; `do_craft` `:311`, with the three-term roll `:321`, the improvement call `:353–354`, the mastery writer `:369–374` and the produce branch `:376`; `post_craft` `:397`, the step and cap lines `:441–445`. `world/knowledge.py`: `recipe_names()` `:48`; `_can_transmit` `:67`, its threshold comparison `:108`; `render_recipe_detail(cls, extra_lines=None)` `:111`, the *Skill:* row `:180`. `commands/crafting_commands.py`: `_resolve_recipe` `:150`; `_visible_recipes` `:368`; `_DISCIPLINE_LABELS` `:422`; `CmdRecipes` `:425`; the `_can_transmit` callers — `CmdRecipes._can_teach` `:495`, inscribe `:809`, scribe `:930`, teach `:1091`, and the student's accept path (`_learn_from_teacher`) `:1364`, which this table did not list. `world/skillcheck.py`: `skill_check` `:58`, automatic failure `:96`, automatic success `:100`, `opposed_check` `:127`. `world/recipe_mastery.py`: the four constants `:69–78`, `DISCIPLINES` `:81`, `MASTERY_TITLES` `:90`. `typeclasses/characters.py`: `recipe_mastery` `:202`.

Concurrency: a character runs one timed action at a time (the `ndb.timed_action` slot), and Evennia's reactor is single-threaded, so two `do_craft` completions for one character cannot interleave; the read-modify-write in `add()` needs no lock. Two characters have two Attributes.

## 4. Dependency graph

```
M1.1 world/recipe_mastery.py handler + Character.recipe_mastery + @py surface
  ├─ M2.1 the writer in do_craft (success-gated) + the step line in post_craft
  │    └─ M2.2 _mastery_modifier() third term + MD7 isolation test
  ├─ M3.1 _can_transmit on the mastery threshold; help teach / inscribe / scribe
  └─ M4.2 recipes: discipline summary, discipline list, count in detail, title
M4.1 discipline on all 29 recipes + registry test          (independent)
M5.1 skill_check automatic bands (MD8)                     (independent; last code task)
M6.2 merge → M6.1 docs close-out              (as run; Rev 2 reversed the arrow, §10)
```

Nothing depends on E.2; E.2 depends on this (the gate and the roll are shared, decision log 2026-08-11).

## 5. Component M1 — The counter (Claude)

### Task M1.1 — `world/recipe_mastery.py`: `RecipeMasteryHandler`, `Character.recipe_mastery`, the `@py` surface
- **Goal:** One handler that answers *how many of this recipe has this character completed* and can add one, stored in one Attribute, with no reader in gameplay yet.
- **Dependencies:** None.
- **Approach:** `RecipeMasteryHandler(obj, db_attribute="recipe_mastery")` after `SkillXPHandler` (`world/skill_xp.py:85`): `_store()` returns the Attribute or `None`, tested through `Mapping`; `count(name) -> int` (0 when unset); `add(name, amount=1)` validates `amount` (an `int` ≥ 1, else `ValueError` — a bug in calling code, not a player condition), rebuilds a plain `dict` and writes it with `attributes.add`; `all() -> dict` unions stored keys with `_RECIPE_CLASSES` so an orphaned name stays visible; `modifier(name) -> int` is the MD3 formula over `count(name)` with the three constants defined in this module (the recipe's `_mastery_modifier` in M2.2 calls it, so there is one formula); `step(name) -> int` returns `count // MASTERY_STEP_SIZE`, which M2.1 compares before and after a write to decide whether to speak. `Character.recipe_mastery` as `@lazy_property` under `skill_xp` (`typeclasses/characters.py:176`). Names are canonical recipe names; the handler does not resolve user-typed names (callers already do, via `_resolve_recipe`).
- **Testing** (`tests/test_recipe_mastery.py`, `EvenniaTest`): unset reads 0; `add` once reads 1, twice reads 2; `add("twine", 3)` reads 3; `add` with 0, −1 and `"one"` raise `ValueError` and leave the store unchanged; `modifier` is 0 at 0–4, 5 at 5, 5 at 9, 10 at 10, 20 at 20 and 20 at 57; `step` is 0 at 4 and 1 at 5; the store round-trips through `attributes.get` and is a `Mapping`, and a second handler instance on the same character reads the first's write; `all()` includes a stored name the registry does not know and a registry name with no store; two characters' counts are independent. `@py`: `self.recipe_mastery.count("waterskin")`, `self.recipe_mastery.add("waterskin")`, `self.recipe_mastery.all()`.
- **Mutations (RM1–RM5):** `MASTERY_STEP_SIZE` → 4 (the 5/9 test must fail); drop the cap (the 57 test must fail); `isinstance(store, dict)` instead of `Mapping` (the round-trip test must fail); `add` returns without writing (the once/twice test must fail); drop the `amount` validation (the `ValueError` tests must fail).
- **Commit:** `feat(mastery): RecipeMasteryHandler — per-recipe completed-craft counter on Character`
- **Shipped (Rev 2):** `99b7296`, tree `af8215f`; suite 894 → 914 (`tests/test_recipe_mastery.py`, 20). A non-int `amount` — `"one"`, and `True`, because `bool` subclasses `int` — raises `TypeError`, not `ValueError`; an int below 1 raises `ValueError`. The handler reaches the registry through a new `world.knowledge.recipe_names()`, not by importing `_RECIPE_CLASSES`, which BACKLOG *`CmdCraftGated` recipe-resolver duplication* (Rev 24 constraint) forbids in a new module; two modules still import the registry, `world/knowledge.py` and `commands/crafting_commands.py`.

## 6. Component M2 — The roll (Claude)

### Task M2.1 — The writer in `do_craft`, and what the crafter hears
- **Goal:** A successful craft check adds one to the recipe's counter, from one call site, and the crafter is told when a step is reached.
- **Dependencies:** M1.1.
- **Approach:** In `do_craft` (`world/crafting_base.py`), after the improvement call (`:323–324`) and before `if not self._should_produce(tier)`, when `outcome["success"]`: read `step` before, `add(self.name)`, read `step` after, and set `self.mastery_step = after` if it rose (else `None`), with the same `getattr`-guard on `self.crafter` the module uses for `attempt_skill_improvement` (a crafter without the handler neither counts nor errors). Default `mastery_step = None` beside `tool_broke`. In `post_craft`, after the improvement feedback and before the tool-break notice, if `self.mastery_step`: *"Your hands know this recipe a little better."* at steps 1–3 and *"You could make this in your sleep."* at step 4 (the cap), so the beat reads *you made X / your skill improves / you know this better / your tool breaks*. Failures and fumbles do not write, whatever `_should_produce` says (MD2); a product set down at the ceiling still counts.
- **Testing** (`tests/test_craft_command.py`, `mock.patch("world.skillcheck.randint")` as in `tests/test_cloth_goods.py:204`): a forced success on `craft twine` reads 1; a forced critical (roll 1) reads 2 after a second craft; a forced failure and a forced fumble (100) each leave the count unchanged *and still yield an item* (the `"raw"` fact, pinned); the fifth success emits the step line once and the sixth does not; the twentieth emits the cap line; a crafter at the weight ceiling whose product is set down still gains the count (W5.1 interplay); the write happens for a timed craft at completion, not at the command (one `delay` patch, count 0 before the callback and 1 after); scribing a book does not change any count (MD2's exclusion, pinned on the scribe path).
- **Mutations (RM6–RM10):** gate on `_should_produce(tier)` instead of `outcome["success"]` (the failure-still-yields test must fail); move the write into `post_craft` after `receive_or_set_down` and have it skip set-down products (the ceiling test must fail); write before the roll (the timed-craft test must fail); emit the step line on every success (the sixth-craft test must fail); write on scribe's roll (the scribe test must fail).
- **Commit:** `feat(mastery): do_craft counts a successful check; step and cap lines in post_craft`
- **Shipped (Rev 2):** `74e9376`, tree `12adac8`; suite 914 → 926. The line is gated on the roll *modifier* rising, not on `step`: past the cap the step keeps climbing while nothing the crafter feels changes, so the line stays silent. One extra mutation, RM9b (the commit message calls it RM11, which is M2.2's number). The weight-ceiling test lives in `tests/test_set_down.py::TestCraftSetsDown`. The scribe test is the first command-level test of `scribe`.

### Task M2.2 — `_mastery_modifier()` as the roll's third term, and MD7 pinned
- **Goal:** Mastery helps the craft roll by the MD3 formula and touches nothing else.
- **Dependencies:** M2.1.
- **Approach:** `MongooseCraftRecipe._mastery_modifier()` returns `self.crafter.recipe_mastery.modifier(self.name)` (0 without the handler, `getattr`-guarded like `_physical_modifier`), and the roll (`:290–292`) becomes `self._tool_modifier() + self._physical_modifier() + self._mastery_modifier()`. The comment above the roll gains the third term. Nothing in `world/improvement.py`, `attempt_skill_improvement` or `improve_skill_on_use` changes.
- **Testing** (`tests/test_craft_command.py`): with `mock.patch("world.crafting_base.skill_check")` (the `tests/test_encumbrance.py:829` pattern), a count of 0 passes modifier 0 beyond tool and physical, 5 passes +5, 20 passes +20, 57 passes +20; with tool absent (−20), overloaded (−20) and count 20, the modifier passed is −20 (the −18 → 2 case at Craft 22); on a forced critical at count 20 the stamped quality is 2 higher than at count 0 for the same skill (MD4); **MD7:** with `mock.patch("world.improvement.randint")` and a count of 20, the improvement roll's `target` equals the one at count 0 (read from the improvement result threaded through `improvement_result`), and `.current` moves by the same grain. A census test asserts the three terms appear exactly once in `do_craft`'s source (`inspect.getsource`), the W3.1 census pattern.
- **Mutations (RM11–RM14):** drop the third term (the +5 test must fail); apply mastery to `_skill_value()` instead of the modifier (the MD7 target test must fail); cap at 25 (the 57 test must fail); subtract instead of add (the −18 → 2 test must fail).
- **Commit:** `feat(mastery): _mastery_modifier joins the craft roll; progression isolation pinned`
- **Shipped (Rev 2):** `face6a7`, tree `22bd022`; suite 926 → 933. `improvement_result` carries no `target` (lesson 180), so MD7 is pinned on `improvement_roll`'s inputs, not on the result. RM12 is killed by the modifier tests, not by the MD7 test named above, because improvement reads `.current` (lesson 181); one extra mutation, RM12b.

## 7. Component M3 — Transmission (Claude)

### Task M3.1 — `_can_transmit` reads mastery; the three help texts
- **Goal:** Teach, inscribe and scribe require five completed crafts of the recipe, and say so.
- **Dependencies:** M1.1.
- **Approach:** `world/knowledge.py::_can_transmit`: keep `knows_recipe`, keep the exact-key registry resolve (a removed recipe still cannot be transmitted), replace the `.current >= min_skill` comparison with `char.recipe_mastery.count(recipe_name) >= MASTERY_TRANSMIT_THRESHOLD` (constant in `world/recipe_mastery.py`, 5). Rewrite the docstring's *Returns* and the *Notes* line that names `.current`; the *common recipe* note stands. The three callers' refusal lines change from *haven't mastered* phrasing that meant the floor to *You haven't made enough of these to teach it* (inscribe `:653`, scribe, teach), and `help teach`, `help inscribe`, `help scribe` gain one sentence: *You must have completed a recipe five times before you can pass it on.* The `recipes <name>` detail's *skill floor* line is untouched (M4.2 adds the count beside it).
- **Testing** (`tests/test_knowledge.py`): `test_known_but_below_skill_floor_blocks` and `test_known_at_exact_floor_transmits` are **replaced** by: known at count 4 blocks; known at count 5 transmits; known at count 5 with `.current` *below* `min_skill` transmits (the floor is gone from this path); unknown at count 50 blocks; a buff on `.mod` with count 4 blocks (the old `.value` guard's intent, kept as a test); the module's `.value`-regression test (`:236`) is rewritten to the new premise. Command level: `teach cloth to <other>` at count 4 refuses with the new line; at 5 proceeds; `inscribe` and `scribe` likewise, one assertion each. Predicted count for `tests.test_knowledge`: 24 − 2 + 5.
- **Mutations (RM15–RM18):** keep the `min_skill` clause in addition (the below-floor-transmits test must fail); threshold 4 (the count-4 test must fail); read `.value` of anything (the buff test must fail); drop `knows_recipe` (the unknown-at-50 test must fail).
- **Commit:** `feat(mastery): _can_transmit gates on five completed crafts, not the Craft floor`
- **Shipped (Rev 2):** `ab0579c`, tree `83c6e89`; suite 933 → 938, `tests.test_knowledge` 24 → 29. The prediction above, 27, counted the buff test twice — as new and as the rewrite of the `.value` regression test; a table giving each old test one fate gave 29 (lesson 186). `TestCanTransmit` stays at 6 tests. +5 command-level tests, three of them in `TestTeachGate`, the first tests `CmdTeach` and the accept path have ever had; they patch `has_account` with a `PropertyMock` (Testing Ref §11f). The accept path (`_learn_from_teacher`) is a fourth caller of the gate and keeps its own refusal line; the three in this task's text get *You haven't made enough …* lines. The help sentence *skilled enough to have mastered* was rewritten, not only extended. The tests the switch broke were 12, not *about 20 calls* (lesson 183): 19 grep hits in `test_knowledge` were 7 tests, and 5 more were in four other modules.

## 8. Component M4 — Disciplines (Claude; names by Adam)

### Task M4.1 — `discipline` on every recipe, and the registry test
- **Goal:** Each of the 29 recipes names its discipline, and no recipe can be added without one.
- **Dependencies:** None.
- **Approach:** `discipline = None` on `MongooseCraftRecipe` with a comment stating MD6 (display only; never read mechanically; not `PROFESSIONS`); one string on every recipe class in `world/recipes.py` from the OQ1 set: **weaving** — twine, cloth, sack, linen shirt, breeches, robe, hood, reversible clothes, linen cuirass; **leatherwork** — leather, waterskin, leather boots, shoes, bandolier, saddlebag, backpack, scrollcase, sling; **stonework** — stone knife, stone axe, milling stones, sling bullet; **bonework** — bone needle, bone armour; **woodwork** — quarterstaff, spear, bow, club, tent. `DISCIPLINES` tuple in `world/recipe_mastery.py` with the five names and their display labels (*Weaver*, *Leatherworker*, *Stoneworker*, *Boneworker*, *Woodworker*), the title nouns for M4.2.
- **Testing** (`tests/test_material_registry.py`, beside test (g)): every class in `_RECIPE_CLASSES` has a non-empty `discipline` in `DISCIPLINES`; every discipline in `DISCIPLINES` has at least one recipe; `MongooseCraftRecipe.discipline` itself is `None` (the base is not a recipe).
- **Mutations (RM19–RM20):** remove `discipline` from one recipe (the first test must fail); add a sixth discipline with no recipe (the second must fail).
- **Commit:** `feat(mastery): discipline on all 29 recipes; registry test`
- **Shipped (Rev 2):** `409749f`, tree `9210b16`; suite 938 → 941. The three tests are `tests/test_recipe_mastery.py::TestDisciplines`, not beside test (g) in `test_material_registry`, and the declaration is read from `cls.__dict__`, so a discipline must be declared on the recipe class itself. One extra mutation, RM19b. OQ1 closed 2026-10-31 with the set as listed.

### Task M4.2 — `recipes` grows a discipline summary, a discipline list, and the count in detail
- **Goal:** A crafter can see what they have made, by discipline and by recipe, and what the count buys.
- **Dependencies:** M1.1, M4.1.
- **Approach:** `CmdRecipes` (`commands/crafting_commands.py:361`): bare `recipes` keeps its list and appends one line per discipline — *Weaving: 6 known · 2 you can teach*; `recipes <discipline>` (resolved before a recipe name, exact match on the five names) lists that discipline's recipes the viewer can craft with *made N (+M)*; `recipes <name>` gains *Made: N · roll +M · next step at K* after the skill-floor line, and *you can teach this* when the count meets the threshold. The title: the highest single-recipe count in a discipline at 5 / 10 / 20 gives *Apprentice / Journeyman / Master <label>*, shown once on the summary line, highest tier only; no sum. The `help recipes` text gains the two modes. Nothing reads `discipline` outside this command.
- **Testing** (`tests/test_craft_command.py` or a new `tests/test_recipes_command.py`): the summary line counts known recipes per discipline for a character with two learned leatherwork recipes; `recipes leatherwork` lists the waterskin with *made 0*; after five forced successes on the waterskin the detail says *made 5 · roll +5 · next step at 10* and *you can teach this*, and the summary carries *Apprentice Leatherworker*; at 20 the title is *Master* and the detail says *roll +20* with no next step; a discipline name that is also a prefix of a recipe name resolves to the discipline; an unknown word falls through to the existing *no such recipe* line.
- **Mutations (RM21–RM24):** title from the sum of counts (the two-recipes-at-3 case must not be Apprentice, and that test must fail); show the discipline list without the count; resolve recipe name before discipline (the prefix test must fail); threshold text hard-coded to 4.
- **Commit:** `feat(mastery): recipes shows disciplines, counts, modifiers and titles`
- **Shipped (Rev 2):** `f5358bf`, tree `0adebaa`; suite 941 → 957 (`tests/test_recipes_command.py`, 16). Nine departures, locked: **(A)** `render_recipe_detail(cls, extra_lines=None)` — the viewer's lines come after *Skill:*, and the scroll path passes none (lesson 188). **(B)** `_visible_recipes(caller)` is `_show_list`'s existing loop, extracted and shared, in `commands/crafting_commands.py`: not a new registry reader, so not in `world/knowledge.py` as BACKLOG Rev 24 had placed it. **(C)** *known* counts what the list shows, common plus learned. **(D)** *you can teach* means `requires_knowledge` and `_can_transmit`; the summary leaves that part out at 0. **(E)** `MASTERY_TITLES` lives in `world/recipe_mastery.py`; the title is read from the highest single count, highest tier only. **(F)** Commas separate the parts, not `·`: no player-facing output is non-ASCII. **(G)** RM23 split in two, because no discipline name resolves as a recipe in real data (lesson 187): RM23a (`recipes leather` is the recipe) and RM23b (a `weaving` recipe patched in with `patch.dict`). **(H)** RM24 reworded to its own comparison with 4; new RM21b, RM22b, RM22c, RM24b, RM24c, RM24d. **(I)** One summary line per discipline with at least one visible recipe — implemented, untested, because every discipline has a common recipe. The test text above changes with (C): two learned leatherwork recipes give *4 known*, since the waterskin and the sling are common, and the teach test uses leather. In game the summary reads *Weaving: 2 known, 1 you can teach. Apprentice Weaver* (Testing Ref §16). OQ2 closed with 5 / 10 / 20.

## 9. Component M5 — The rulebook's bands (Claude)

### Task M5.1 — `skill_check`: automatic success 01–05, automatic failure 96–00
- **Goal:** Every skill test in the game honours Legend's automatic bands, in the order MD8 fixes.
- **Dependencies:** None in code; sequenced last (MD8).
- **Approach:** `world/skillcheck.py::skill_check`: after the fumble test, `elif roll >= 96: FAILURE` (above 100 % the fumble test already took only 00, so 96–99 fall here); then the critical test; then `elif roll <= 5: SUCCESS`; then `roll <= target`. Module docstring: the departure note becomes an adoption note, citing *Automatic Success and Failure*. `margin` and `crit_score` are unchanged (an automatic success at target 3 on a roll of 05 has margin −2; callers that scale on margin get a true number).
- **Testing** (`tests/test_skillcheck.py`, new; forced `randint`): target 0 — 01 critical, 02–05 success, 06 failure, 96 failure, 99 fumble; target 3 — 04 success; target 97 — 96 failure, 97 failure, 98 failure, 99 fumble, 95 success; target 120 — 12 critical, 13 success, 96 failure, 99 failure, 100 fumble; target 50 unchanged at 50 success and 51 failure. Predicted whole-suite effect: no existing test forces a roll in 02–05 or 96–98 against a target it would flip (verified by grep before the run; if one does, that test's premise is the departure and is rewritten with a note).
- **Mutations (RM25–RM28):** auto-failure before fumble (99 at target 97 must be fumble, test must fail); auto-success before critical (01 at target 50 must be critical); `roll >= 95`; `roll <= 6`.
- **Commit:** `feat(skillcheck): automatic success 01–05 and automatic failure 96–00 (Legend)`
- **Shipped (Rev 2):** `129618e`, tree `2030acf`; suite 957 → 971 (`tests/test_skillcheck.py`, 14 — the first direct tests `skill_check` has had, lesson 192). **(A)** The docstring had no departure note to turn into an adoption note; the bands were added as rules, and the 01 note gained *no test required or possible*. **(B)** The cases above plus two: 01 at target 50 (RM26) and `margin`/`crit_score` at target 3. **(C)** Extra boundary mutations RM27b (`> 96`) and RM28b (`< 5`). **(D)** No existing test changed. Greps found 8 modules; a counting wrapper over the run found 13 candidates and 80 calls from 44 tests in 8 modules, and no pinned roll flips (lesson 191). One unpinned test rolls against target 0 and stays green because `"raw"` produces at every tier. In game, 10 000 rolls at targets 0 and 120 matched the band frequencies (Testing Ref §16).

## 10. Component M6 — Docs close-out and merge (Claude, on `main`)

### Task M6.1 — Documentation
- **Goal:** Every document this feature made false is true again, in one commit after the merge.
- **Approach:** This document: each task's record in §11, status DONE, the close-out. Roadmap: the backlog entry becomes a record; the alpha entry notes prerequisite 2 met; the decision log's *Craft specialisation model* gains a dated note correcting *single-purpose* (MD5); the *111 → ~113* sentence is struck with a note (MD4). BACKLOG: the `skill_check` entry goes DONE (M5.1); *Repair, disassemble and hunt have no command tests of their own* gains a note if M2.1 or M3.1 added any. Recipe Knowledge Decomposition: a dated note on `_can_transmit`'s new premise. Testing Ref: an in-game protocol for mastery (craft five, read `recipes`, teach). README: no change (the index row lands with Rev 1). Evennia Ref: only if a new gotcha appeared.

### Task M6.2 — Merge
- Whole suite once, on the branch tip, counted per module before the run; merge by merge commit; delete the branch on origin and at home; `ls-remote` after the push.

**As run (Rev 2): M6.2 first, then M6.1.** §4's arrow put the docs first and M6.1's goal put them after the merge. The merge went first, so the docs could record the suite as run, the merge SHA, and DONE against code already on `main` (lesson 174). M6.1's list above was also two items too long and one item wrong: the roadmap's *single-purpose* note and the struck *111 → ~113* were already made in Rev 1's commit (roadmap Rev 34), and README did change (Rev 15), because its index row quotes the lesson range.

## 11. Records

All nine tasks DONE. Each code task was received with a targeted run of its own module and the neighbours a probe and the greps named, every planned mutation killed, and its protocol run in game; the whole suite ran at home on the branch tip before the merge, and once more on the merge, whose verdict is the one recorded. What each task changed from its text is in its *Shipped* line (§5–§9).

| Task | Commit | Tree | Date | Suite after |
| --- | --- | --- | --- | --- |
| (base) | `f8c8e5b` | `82bafb1` | 2026-10-30 | 894 in 40 modules |
| M1.1 | `99b7296` | `af8215f` | 2026-10-30 | 914 |
| M2.1 | `74e9376` | `12adac8` | 2026-10-30 | 926 |
| M2.2 | `face6a7` | `22bd022` | 2026-10-30 | 933 |
| M3.1 | `ab0579c` | `83c6e89` | 2026-10-30 | 938 |
| M4.1 | `409749f` | `9210b16` | 2026-10-31 | 941 |
| M4.2 | `f5358bf` | `0adebaa` | 2026-10-31 | 957 in 42 |
| M5.1 | `129618e` | `2030acf` | 2026-10-31 | 971 in 43 |
| M6.2 | `abe9e6b` (merge) | `2e71112` | 2026-10-31 | 971 OK: run at home on `129618e` before the merge, and on `abe9e6b` after it (same code; `Ran 971 tests in 110.872s`) |
| M6.1 | the docs commit after it | — | 2026-10-31 | docs only |

`main` moved once during the feature, from `f8c8e5b` to `1c00951` (the lessons register), touching only docs; the merge was checked in advance with `git merge-tree` and gave the same tree.

## 12. Open questions (each with the task that closes it)

- **OQ1 — The discipline set.** Five disciplines over 29 recipes as listed in M4.1; the only judgement calls are the sack (weaving, it is cloth), the sling (leatherwork, its strap), the sling bullet (stonework) and the tent (woodwork, its poles). Closed by M4.1 at its confirmation step. *(Closed 2026-10-31: the set as listed.)*
- **OQ2 — Title thresholds.** 5 / 10 / 20 for Apprentice / Journeyman / Master, read from the highest single count. Closed by M4.2. *(Closed 2026-10-31: 5 / 10 / 20, locked.)*
- **OQ3 — Disassemble and mastery.** Disassemble's roll subtracts `min_skill`; should the dismantler's mastery of the recipe ease it? Recommendation no: disassemble is E.2's seam (reverse-engineering), and E.2 decides what mastery buys there. Recorded here, decided in E.2. *(Open at the merge; E.2's.)*
- **OQ4 — What E.2 spends.** Mastery gives E.2 a count to read; whether `teaches_until` or `accept` consumes it is E.2's. Recorded, not this feature's. *(Open at the merge; E.2's.)*
- **OQ5 — The first-step line's wording** (M2.1) and whether the cap line should name the modifier. Closed by M2.1. *(Closed: the wording above, and the cap line does not name the modifier.)*

## 13. Consequences worth reading twice

- **The first five crafts are the apprenticeship.** A crafter who learns a recipe from a scroll can make it at once and cannot pass it on until the fifth success. That is the feature, and the alpha cohort will meet it as a refusal: *You haven't made enough of these to teach it.*
- **A master smith who never made a waterskin can no longer teach it.** At `8aeb91c` Craft 90 teaches everything known. After M3.1, Craft 90 teaches what it has made five times. Someone will call that a regression; it is the gap this feature was filed to close.
- **Failure yields and never counts.** Under `"raw"` a failed craft still hands over a quality-50 item (D.1's stance: an attempt consumes and produces). It adds nothing to mastery. The two are deliberately decoupled, and M2.1 pins the decoupling.
- **No backfill, and development characters know it.** Every character — including the ones that have crafted for months in the dev database — starts at 0. Testing the teach gate in the dev database means crafting five of something first; the Testing Ref protocol in M6.1 says so.
- **There is no quality ceiling and there has not been one since P-7.** Any document that cites 110 or 111 as a maximum is describing the game before Skill Progression. This decomposition is the first to say so; M6.1 marks the roadmap sentence.
