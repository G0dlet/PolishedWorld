# PolishedWorld — Trivial Work Decomposition

> **Rev 1 · 2026-10-31** — first version. Decomposes the second half of the alpha's first prerequisite, **E.2 — the trivial-work gate** (Skill Progression decomp §7, Component E; order fixed by roadmap (F): after per-recipe mastery, last of the four), into five components and seven tasks, against live source read the same day (`main` at `af164d6`, tree `bbf2aac`; Evennia 6.1.0; *Legend* core pp. 68–71). Of §7's premises checked against the code, three did not survive and are corrected here: `attempt_skill_improvement`'s docstring counts *both live call sites* and there are six; disassemble *has* a difficulty datum (it subtracts `min_skill` from its roll), so it leaves E.3; and *routine tasks do not earn an Improvement Roll* is not a rule in *Legend* — Improvement Rolls are awarded by the Games Master at a story's close on how the Adventurers acquitted themselves (p. 68), so the gate is the on-use adaptation's stand-in for that judgement, faithful in spirit and not by citation. Locks TD1–TD9 in §2; the BACKLOG blocker goes BLOCKED → SCHEDULED in the same commit, and two new entries are filed there (disassemble salvage, the scribe leak).
> **Canonical:** `docs/PolishedWorld_Trivial_Work_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Design source:** `docs/PolishedWorld_Skill_Progression_Decomposition.md` §7 (Component E; marked moved-out, points here from Rev 10); `docs/roadmap.md` for its place in the alpha.
**Status:** DECOMPOSED. Code follows on `feature/trivial-work`, cut from `main` with `--no-track`.
**Feature branch:** `feature/trivial-work` (one branch, one merge).
**Rough scope:** 7 tasks, ~2 sessions at 5 h/week (T1 1 · T2 1.5–2.5 · T3 1–1.5 · T4 0.5 · T5 0.5). Small because the seam exists: `attempt_skill_improvement(…, meaningful=True)` has waited since Stage 4.5 B.2 for exactly this caller, and `min_skill` already sits on all 29 recipes (AC5.1).
**Philosophy:** skynda långsamt — one constant, one pure function, two call sites that pass a boolean, two display lines. No new field on recipes, no read of mastery, no migration, no new command.

---

## 1. Why this feature

Stage 4.5 made Craft *slow* (A–D) and per-recipe mastery made specialisation *pay* (M1–M5). Neither objects to the grind: with a flat grain the optimal path to Craft 100 is still the cheapest recipe you know, repeated ~2 900 times. Component E was designed to remove that in 2026-08 and was blocked on content — eight recipes, one floor — until AC5.1 laddered all 29 on rungs 0/20/40/60. The ladder exists; the gate that reads it does not. This is the last piece of alpha prerequisite 1.

The lever is difficulty **relative to the crafter**: a recipe written for a level far below yours is routine work, and routine work does not teach. Nothing about the roll changes (P-3): the improvement roll is simply not attempted. The seam is `meaningful=False` on `attempt_skill_improvement`, built for this in B.2 and never passed by anyone (`typeclasses/characters.py:900`).

What it must not do is build a wall. With a ceiling of 60 and a band of 30, nothing would teach above 91 while Craft is uncapped (P-7) and the next rungs (smithing, FAS 3) are outside the alpha. §7's own ruling — *a dead end is strictly worse than the grind it replaces* — applies to E.2's own output, and TD3 is the answer.

## 2. Decisions locked 2026-10-31 (TD1–TD9)

**TD1 — Accept: `min_skill` is the level a recipe is written for, and the gate is its fourth reader.** Skill Progression decomp §7 offered *accept* or a second field (`teaches_until`); the roadmap's (F) said the choice would be easier once mastery existed, and it is. After MD5 `min_skill` has three readers with one meaning — the craft floor (`.value`, `world/crafting_base.py:307`), disassemble's modifier (`commands/crafting_commands.py:736`) and the displays (`:530`, `world/knowledge.py:155`) — and the gate adds a fourth with the same meaning: a recipe you are barely qualified for is also the one that teaches you most. `teaches_until` would be 29 new data points with no content reason behind any of them. Raising a floor to keep a recipe teaching also locks lower crafters out of it; that coupling is accepted and named, not hidden. Mastery decomp OQ4 is closed by this: neither reading consumes the mastery count.

**TD2 — The expression reads `.current`, and nothing else.** A recipe is *routine* for a crafter when `trait.current − min_skill > SKILL_TRIVIAL_BAND`, with `trait` the recipe's `skill_name` on the crafter (`"craft"` for all 29). Progression reads `.current`, resolution reads `.value` (Evennia Ref §3.5): a tool's ±20 never reaches the gate (it shifts the roll in `do_craft`), a buff never makes a task harder and so more instructive than it is, overload never makes it easier, and mastery's +20 is a roll term (MD3, MD7) and is not read. The band is one constant, `SKILL_TRIVIAL_BAND = 30`, in `server/conf/settings.py` beside `SKILL_XP_BASE`, read per call through `getattr(settings, …)` with a module default (`world/progression.py:148`'s precedent). 30 is the value AC5.1 pinned (`tests/test_min_skill_ladder.py:59`) and the value the ladder was laddered against; 20 is the rung spacing and the smallest band the ladder test allows, and 30 was kept because the overlap means two rungs teach at most levels — a crafter at 45 learns from rung 20 and rung 40 — which leaves the knowledge gate, not the band, as the thing that limits choice. The band is a calibration constant, not a contract: `help craft` says *well above its floor*, not *30*.

**TD3 — The top rung always teaches.** A recipe whose `min_skill` equals the registry's highest `min_skill` is never routine, whatever the crafter's skill. `ladder_top()` is read from the registry at call time, so the exemption moves itself the day a higher rung lands (smithing) and the rung-60 recipes go routine for a Craft-100 crafter on that commit, without anyone editing E.2. Today the exemption makes 91 a soft edge: above it only the seven rung-60 recipes teach, which is the grind as it stands now and never worse. Rejected: *accept the wall* (the alpha's practical Craft ceiling would be 91, reachable by a determined crafter in weeks, and the first player to hit it would find the game's one expensive number frozen); *a mastery-based `teaches_until`* (a second mechanic to calibrate, §7's rejected soft gate in another coat, and it strands a low-skill crafter who knows only rungs 0 and 20).

**TD4 — One pure function, two call sites.** `routine_for(crafter, recipe_cls) -> bool` lives in `world/knowledge.py` beside `recipe_names()`, because `ladder_top()` reads the private registry and BACKLOG *`CmdCraftGated` recipe-resolver duplication* (Rev 24) requires every new reader of it to live inside an existing consumer module (lesson 182); `world/knowledge.py` already reads it. `do_craft` passes `meaningful=not routine_for(self.crafter, type(self))` (`world/crafting_base.py:353–354`); `CmdDisassemble` passes `meaningful=not routine_for(caller, cls)` (`commands/crafting_commands.py:756`). The function is `getattr`-guarded like `_skill_value`: a crafter without `skills` reads 0 and is never routine.

**TD5 — Disassemble joins the gate now; repair, hunt and scribe stay out (E.3).** §7 listed disassemble among the sites with *no difficulty datum comparable to `min_skill`*; it reads `min_skill` as a roll modifier and has since Stage 3 E.2, so the datum is there and the claim is corrected. Today the gate at disassemble is nearly inert — only an *unknown* recipe can be taken apart, so it fires once per recipe — but Adam's standing intention is that disassemble also **salvages parts and raw materials from known items** (filed in BACKLOG this Rev, post-alpha), and the day it does, *craft a rung-0 item (routine, no tick) → take it apart (tick)* is the grind back through a side door. Gating disassemble now closes that loop by construction before the door exists. Repair, hunt-attack, hunt-harvest and scribe keep `meaningful=True`, the generous side (P-5), each with a comment saying so (§7: *say this out loud in the code*). Scribe is the one that matters — a real Craft roll on cheap material at any skill, cooldown-limited only — and gets its own BACKLOG entry rather than a fix nobody designed.

**TD6 — The player can see the rule, and is not told it per craft.** Stage 4.5's `CmdScribe` decision stands on *a rule of the form "some Craft rolls teach and some do not, and you are not told which" is not learnable*. So: `recipes` tags each listed recipe that is routine for the viewer, `recipes <name>` carries a *teaches you* line, and `help craft` and `help recipes` each gain a paragraph. No line is printed by `post_craft` on a routine craft: a non-tick is already silent (`attempt_skill_improvement` returns `None` in the common case), and a crafter making fifty waterskins for the market should not read fifty reminders. The detail line and the help text are passed into `render_recipe_detail` as `extra_lines` (lesson 188: the renderer also draws scrolls, which have no viewer).

**TD7 — Mastery is untouched.** No code in this feature reads `recipe_mastery`, and no mastery constant enters the gate. The counter already has two jobs (the roll term, the transmission gate); a third would tie E.2's calibration to `MASTERY_*`, which is two knobs on one job. Mastery decomp OQ3 (should the dismantler's mastery ease disassemble?) is not E.2's to answer once salvage exists — it is the salvage design's — and is re-homed to that BACKLOG entry.

**TD8 — The ladder test reads the real constant.** `tests/test_min_skill_ladder.py` replaces `TRIVIAL_BAND_PIN = 30` with the constant the gate reads, so a band change that opens a gap in the ladder fails the catalogue test instead of shipping; and it gains a test that `ladder_top()` is the catalogue's ceiling (60 today, by the same `ALPHA_LADDER_CEILING`).

**TD9 — Unnumbered, and an adaptation.** Prerequisite 1's second half by decision (A), unnumbered for Rev 17's reason. *Legend* has no per-task improvement rule — Improvement Rolls are the Games Master's award at a natural close, one to five by how the Adventurers acquitted themselves (p. 68–69) — so the gate is not a citation; it is what an on-use system does instead of a Games Master deciding that fifty waterskins were not an adventure. Skill Progression decomp §7's *Legend-faithful* sentence is annotated, not deleted.

## 3. Verified source anchors (read 2026-10-31, `main` at `af164d6`)

| Anchor | Where | What it establishes |
| --- | --- | --- |
| `attempt_skill_improvement(self, skill_key, outcome, meaningful=True)` | `typeclasses/characters.py:900`; gate 2 at `:934` (`if not meaningful or not outcome.get("success"): return None`) | The seam; nobody passes `meaningful` today. Docstring `:913–916` says *both live call sites (craft, hunt)* — there are six. |
| the six call sites | craft `world/crafting_base.py:353–354`; repair `commands/repair_commands.py:169`; hunt-attack `commands/hunting_commands.py:112`; hunt-harvest `:290`; disassemble `commands/crafting_commands.py:756`; scribe `:1030` | T2.1 gates craft, T2.2 gates disassemble, the other four get the E.3 comment. |
| `_skill_value()` reads `.value` | `world/crafting_base.py:127–131` | Resolution read; the gate must not use it (TD2). |
| the floor | `world/crafting_base.py:295–309` (`.value`, raises `CraftingError`) | `min_skill`'s first reader; unchanged. |
| disassemble's roll | `commands/crafting_commands.py:730–736` (`modifier=-min_skill + physical_modifier()`); the known-recipe refusal `:714–716` | The datum E.3 said disassemble lacked; the refusal that makes the gate inert there until salvage. |
| `min_skill` on all 29 | `world/recipes.py` (6 × 0, 10 × 20, 6 × 40, 7 × 60); the four-reader note in its module docstring `:35–37` | The ladder; the docstring becomes *five ways* in T2.1. |
| the ladder test | `tests/test_min_skill_ladder.py:56–59` (`ALPHA_LADDER_CEILING = 60`, `TRIVIAL_BAND_PIN = 30`) | TD8 replaces the pin. |
| `recipe_names()` and the Rev 24 constraint | `world/knowledge.py:48–60` | Where `ladder_top()` and `routine_for()` go (TD4). |
| `render_recipe_detail(cls, extra_lines=None)` | `world/knowledge.py:111`; called with `_mastery_lines` at `commands/crafting_commands.py:653` | The seam for the *teaches you* line (TD6). |
| the `recipes` list | `commands/crafting_commands.py:516–533` (`_show_list`, the `(needs Craft N%)` note) | Where the routine tag goes. |
| the settings precedent | `world/progression.py:148–149`; `server/conf/settings.py:177–178` | `getattr(settings, NAME, default)` per call; the constant's home. |
| craft test fixtures | `tests/test_craft_command.py:103–140` (`CraftFixtureMixin`, `CraftTestBase`, `randint` pinned) | T2.1's harness. |
| disassemble's existing test | `tests/test_encumbrance.py:838–851` (`TestPenaltyReachesDisassemble`, a piece with `db.recipe = "cloth"`) | T2.2 copies the fixture. |
| improvement reads `.current` | `typeclasses/characters.py` `improve_skill_on_use`; MD7 and its test (mastery M2.2) | The gate's read and the roll's read agree. |
| *Legend* on Improvement Rolls | core pp. 68–71, *Adventurer Advancement* | TD9. |

Imports: `world/crafting_base.py` will import `routine_for` from `world/knowledge.py`; `world/knowledge.py` imports the contrib registry and `world/recipe_mastery.py`, never `world/crafting_base.py`, and `_load_recipes()` is lazy, so there is no cycle. T1.1 proves it by importing both modules in a test, and falls back to an in-function import only if the suite says otherwise.

## 4. Dependency graph

```
T1.1 SKILL_TRIVIAL_BAND + knowledge.ladder_top() + knowledge.routine_for() + pure tests
  ├─ T2.1 do_craft passes meaningful=; docstring six; E.3 comments at repair/hunt/scribe
  ├─ T2.2 CmdDisassemble passes meaningful=; its first gate test
  ├─ T3.1 recipes tag + detail line + help craft / help recipes
  └─ T4.1 ladder test reads the constant; ladder_top() == ceiling
T5.2 merge → T5.1 docs close-out (merge first, lesson 174)
```

Nothing depends on this feature. It depends on mastery only historically (the `.value`/`.current` double semantics it needed closed, MD5).

## 5. Component T1 — The rule (Claude)

### Task T1.1 — `SKILL_TRIVIAL_BAND`, `ladder_top()`, `routine_for()`
- **Goal:** One place that answers *is this recipe routine for this crafter*, with no caller yet.
- **Dependencies:** None.
- **Approach:** `server/conf/settings.py`: `SKILL_TRIVIAL_BAND = 30` under the `SKILL_XP_*` block with a four-line comment (what it is, that 20 is the floor the ladder test enforces, that it is read per call). `world/knowledge.py`: `_DEFAULT_TRIVIAL_BAND = 30`; `trivial_band()` → `max(0, int(getattr(settings, "SKILL_TRIVIAL_BAND", _DEFAULT_TRIVIAL_BAND)))`; `ladder_top()` → `_load_recipes()` then `max((getattr(cls, "min_skill", 0) or 0) for cls in _RECIPE_CLASSES.values())`, 0 on an empty registry, no caching (29 classes; tests patch the registry); `routine_for(crafter, recipe_cls)` as in TD2–TD4: floor at the top → `False`; no `skills` → `current = 0`; `current - floor > trivial_band()`. Docstrings carry TD2 (why `.current`) and TD3 (why the top rung) in full, since the function is the whole policy.
- **Testing** (`tests/test_trivial_work.py`, `EvenniaTest`): `ladder_top()` is 60 on the live registry and 0 with `patch.dict(_RECIPE_CLASSES, {}, clear=True)`; `routine_for` on twine (floor 0) is `False` at `current` 30 and `True` at 31 (the boundary, both sides); on cloth (floor 20) `False` at 50, `True` at 51; `trait.mod += 40` at `current` 25 leaves twine not routine, and `mod -= 40` at `current` 40 leaves it routine (`.value` moved, the answer did not); `recipe_mastery.add("twine", 20)` changes nothing; a rung-60 recipe is not routine at `current` 150; with `ladder_top` patched to 0, twine is not routine at 150; a crafter object with no `skills` is not routine; `override_settings(SKILL_TRIVIAL_BAND=10)` makes twine routine at 11. Both modules import in one test (the cycle check).
- **Mutations (TW1–TW5):** read `.value` (the `mod` tests must fail); `>=` for `>` (the 30/31 boundary must fail); drop the top-rung exemption (the 150 test must fail); cache `ladder_top()` at import (the patched-registry test must fail); read `settings.SKILL_TRIVIAL_BAND` directly (the `override_settings` test must still pass, so this mutation is instead: ignore the setting — the 10/11 test must fail).
- **Commit:** `feat(trivial-work): SKILL_TRIVIAL_BAND, ladder_top() and routine_for() — the rule, no caller yet`

## 6. Component T2 — The two call sites (Claude)

### Task T2.1 — `do_craft` passes `meaningful`; the other sites say why they do not
- **Goal:** A routine craft completes, yields, wears the tool, counts for mastery — and does not attempt the improvement roll.
- **Dependencies:** T1.1.
- **Approach:** `world/crafting_base.py:353–354` becomes `improve(self.skill_name, outcome, meaningful=not routine_for(self.crafter, type(self)))` with a comment: read on `.current` through `routine_for`, never `_skill_value()`; evaluated at the roll (a timed craft reads the skill at completion, like the three modifiers). Everything after it is unchanged: the mastery write (M2.1) still counts a routine success — mastery is *practice*, and practice of routine work still makes you faster at it (MD3), it just does not make you better at Craft. `typeclasses/characters.py:913–916`: *both live call sites* → *six call sites; craft and disassemble pass `meaningful=` from `world.knowledge.routine_for`; repair, hunt-attack, hunt-harvest and scribe pass the default — see each site*. `commands/repair_commands.py:169`, `commands/hunting_commands.py:112` and `:290`, `commands/crafting_commands.py:1030` each gain the E.3 sentence: *no difficulty datum here; `meaningful=True` is deliberate (Skill Progression decomp §7 E.3, Trivial Work TD5), not an omission*. `world/recipes.py:35–37`: *four ways* → *five ways*, adding the gate (`world/knowledge.py`, `.current`).
- **Testing** (`tests/test_craft_command.py`, `CraftTestBase`, `randint` pinned to a success): at `current` 30 a `craft twine` completion sets the `improve_craft` cooldown and returns a non-`None` `improvement_result` (the tick fired); at 31 the same craft yields twine, nicks the tool if one is supplied, adds 1 to mastery, and leaves `improve_craft` **not** on cooldown with `improvement_result is None` — three positive receipts that the craft ran, per Testing Ref §11 and lesson 185; with `ladder_top` patched to 0, twine ticks at 150; `mod += 40` at 25 still ticks. A grep count of `attempt_skill_improvement(` outside `def` is pinned at six (`tests/test_improvement_engine.py` or this file: lesson 191's *count the calls*).
- **Mutations (TW6–TW9):** pass `meaningful=True` (the 31 test must fail); gate on `self._skill_value()` (the `mod` test must fail); gate the mastery write too (the mastery-at-31 test must fail); drop the top-rung patch in the call (the 150 test must fail).
- **Commit:** `feat(trivial-work): do_craft passes meaningful= from routine_for; E.3 sites say why they do not`

### Task T2.2 — `CmdDisassemble` passes `meaningful`
- **Goal:** Taking apart an item whose recipe is routine for you teaches you the recipe (as now) and not the skill.
- **Dependencies:** T1.1.
- **Approach:** `commands/crafting_commands.py:756` becomes `caller.attempt_skill_improvement("craft", outcome, meaningful=not routine_for(caller, cls))`, `cls` being the registry class resolved at `:707`. Comment: the gate is nearly inert today (only unknown recipes reach this line) and is here for the salvage mode BACKLOG *Disassemble yields parts and raw materials* describes, so that craft-then-dismantle never becomes the grind (TD5). The improvement line (`_improvement_feedback`) is unchanged; `None` prints nothing, as it already does on cooldown.
- **Testing** (`tests/test_craft_command.py`, new class, fixture copied from `tests/test_encumbrance.py:838`: a piece with `db.recipe = "cloth"`, `char1` not knowing cloth, `randint` pinned to a success): at `current` 50 the dismantle learns cloth **and** sets `improve_craft`; at 51 it learns cloth, destroys the piece, sets the `disassemble` cooldown, and does not set `improve_craft` (the learn and the two cooldowns are the receipts). This is disassemble's first command test of the gate; BACKLOG *Repair, disassemble and hunt have no command tests of their own* is annotated at T5.1, not closed (repair and hunt still have none).
- **Mutations (TW10–TW11):** pass the default (the 51 test must fail); gate on `skill_value` (`.value`) instead (a `mod` variant of the 51 test must fail).
- **Commit:** `feat(trivial-work): disassemble passes meaningful= from routine_for (salvage-proof before salvage exists)`

## 7. Component T3 — What the player sees (Claude)

### Task T3.1 — The `recipes` tag, the detail line, the two help paragraphs
- **Goal:** A crafter can see, before crafting, which recipes still teach — the rule is learnable (TD6).
- **Dependencies:** T1.1.
- **Approach:** `_show_list` (`commands/crafting_commands.py:516–533`): after the `(needs Craft N%)` note, ` |x(routine)|n` when `routine_for(caller, cls)`. `_show_detail` (`:653`): one more `extra_lines` entry built beside `_mastery_lines`: `Teaches you: yes` or `Teaches you: no — this is routine work for you`. `CmdCraft.__doc__` and `CmdRecipes.__doc__`: a paragraph each — *a recipe well above its floor is routine for you: you still make it, your tools still wear, it still counts towards mastery, but it no longer improves your Craft; the hardest recipes known to the world always do. `recipes` marks routine recipes; `recipes <name>` says whether one still teaches you.* No number in the help (TD2: the band is a constant, not a contract).
- **Testing** (`tests/test_recipes_command.py`; a help test after `tests/test_craft_command.py:383`'s `TestHelpStatesTheRule`): twine listed without the tag at `current` 30 and with it at 31; `recipes twine` carries *Teaches you: yes* at 30 and *no* at 31; a scroll's `look` (the other `render_recipe_detail` caller) carries neither line; `help craft` and `help recipes` contain *routine* and do not contain *30*. The viewer-dependence test is lesson 188's.
- **Mutations (TW12–TW14):** tag on `.value` (a `mod` variant must fail); put the line inside `render_recipe_detail` (the scroll test must fail); write *30* into the help (the help test must fail).
- **Commit:** `feat(trivial-work): recipes marks routine recipes; detail says whether a recipe teaches; help craft / help recipes`

## 8. Component T4 — The ladder test (Claude)

### Task T4.1 — The ladder test reads the band the gate reads
- **Goal:** A band change that opens a gap in the ladder fails the catalogue test.
- **Dependencies:** T1.1.
- **Approach:** `tests/test_min_skill_ladder.py:56–59`: remove `TRIVIAL_BAND_PIN`, import `trivial_band` from `world/knowledge.py`, use it in the three `ladder_violations` calls that took the pin; add a test that `ladder_top()` equals `ALPHA_LADDER_CEILING` (the two agree today; when smithing lands both lines change in the same commit, and this test is what says so). The module docstring's *E.2's `SKILL_TRIVIAL_BAND` does not exist yet* goes with the pin.
- **Testing:** the file's own tests, run after `override_settings(SKILL_TRIVIAL_BAND=10)` in one new test must report a gap (the rungs are 20 apart): the honest receipt that the test now reads the setting.
- **Mutations (TW15):** keep a local 30 (the `override_settings` test must fail).
- **Commit:** `test(trivial-work): ladder test reads SKILL_TRIVIAL_BAND; ladder_top() is the ceiling`

## 9. Component T5 — Close-out (Claude, on `main`)

### Task T5.2 — Merge
- **Goal:** `feature/trivial-work` on `main` by merge commit, the whole suite OK before and after.
- **Dependencies:** T1.1–T4.1 received, every planned mutation killed, the protocol below run in game.
- **Approach:** the full suite at home on the branch tip (`ForkTestRunner --parallel`), `git merge-tree` against `main` first (mastery's precedent), PR, merge commit, branch deleted on origin and at home. Merge before docs (lesson 174).
- **Commit:** the merge commit — `Merge branch 'feature/trivial-work' (E.2 trivial-work gate, alpha prerequisite 1)`.

### Task T5.1 — Documentation
- **Goal:** Every document that describes the gate as future describes it as shipped, in one commit on `main`.
- **Dependencies:** T5.2.
- **Approach:** this document: §10 records, status DONE, each task's *Shipped* line. Roadmap: prerequisite 1 **met** in the alpha entry, the status line reading *1 met · 2 met · 4 met · 5 settled · 6 not started · 7 met*, and (F) exhausted — the next decision is the launch minimum (prerequisite 6). BACKLOG: *⛔ The recipe catalogue does not span the skill scale* SCHEDULED → DONE and the ⛔ dropped from its title; *Repair, disassemble and hunt have no command tests of their own* annotated (T2.2); *A craft driven as `char2`…* unchanged unless a test needed it. Skill Progression decomp §7: a dated *shipped* note (Rev 11). Testing Ref: §17 *Trivial work* with the protocol below and the three-receipt pattern from T2.1 (Rev 17); Evennia Ref unchanged unless a task found something. Lessons register: the feature's lessons appended, README's range row updated in the same commit (lesson 193). Catalogue loop against the tree as it will be; `git diff --check`.
- **Commit:** `docs: close out the trivial-work gate (E.2) — alpha prerequisite 1 met`

### In-game protocol (the shape; Testing Ref §17 carries it in full at T5.1)
1. `inventory` first (lesson 71); `@py self.skills.get("craft").current = 30`, `@py self.msg(str(self.skills.get("craft").current))`.
2. `recipes` — twine listed, no *(routine)* tag; `recipes twine` — *Teaches you: yes*.
3. `craft twine` with its material; on completion, the improvement line may appear (success + cooldown); `@py self.msg(str(self.cooldowns.ready("improve_craft")))` → `False` is the receipt the roll was attempted.
4. Wait out the cooldown (30 s); `@py self.skills.get("craft").current = 31`; `recipes` — twine *(routine)*; `recipes twine` — *Teaches you: no*.
5. `craft twine` again: the item arrives, `@py self.msg(str(self.recipe_mastery.count("twine")))` has risen by one, and `@py self.msg(str(self.cooldowns.ready("improve_craft")))` → `True`: the craft ran and the roll was not attempted. Three receipts, no absence.
6. `@py self.skills.get("craft").current = 150`; `recipes` — every rung-60 recipe you know is untagged (TD3), everything below is *(routine)*.
7. Restore: `@py self.skills.get("craft").current = <the value from step 1>`.

## 10. Records

| Task | Commit | Tree | Date | Suite after |
| --- | --- | --- | --- | --- |
| (base) | `af164d6` | `bbf2aac` | 2026-10-31 | 971 in 43 modules |

## 11. Open questions (each with the task that closes it)

- **OQ-T1 — The tag's wording.** `(routine)` in the list, *routine work for you* in the detail. Closed by T3.1.
- **OQ-T2 — Where the six-call-site count is pinned.** `tests/test_improvement_engine.py` does not grep call sites today (checked: zero occurrences of `attempt_skill_improvement(`), so T2.1's file carries the count. Closed here.
- **OQ-T3 — Whether `ladder_top()` should exclude rungs no player can reach.** Not today: every rung is a recipe someone can know. Revisit if a rung is ever authored as admin-only. Closed by T1.1, by not doing it.

## 12. Consequences worth reading twice

- **The knowledge gate becomes the limit, by design.** A crafter at 52 who knows no rung-40 recipe learns nothing from crafting until they buy, find or are taught one. The band does not cause that — a band of 20 would do it at 41 — the ladder does, and it is pillar 1 doing its job at the moment it should: recipe knowledge is worth money at exactly the skill where the player wants it.
- **Mastery still rises on routine work.** Fifty routine waterskins make a Waterskin Master (MD6) and teach no Craft. That is two different things being measured, and it is why the mastery write stays ungated (T2.1).
- **91 is a soft edge, not a wall, and it moves without a code change.** Above 91 the seven rung-60 recipes teach and nothing else does; the day a rung-80 recipe exists they stop at 111 and the rung-80 ones take over. `ladder_top()` reads the registry, and `tests/test_min_skill_ladder.py` ties it to the ceiling constant so the two never silently disagree.
- **Scribe is the known open door.** It is not fixed here because nothing in its roll measures difficulty; it is filed with a trigger. If the alpha ledger shows Craft rising on books, that trigger is met.
- **Disassemble is gated for a feature that does not exist.** Today the gate there fires once per unknown recipe; the test proves it reads `.current`. It is there so that salvage, when designed, cannot reopen the grind.
