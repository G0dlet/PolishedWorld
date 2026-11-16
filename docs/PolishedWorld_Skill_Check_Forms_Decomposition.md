# PolishedWorld — Skill-Check Forms Decomposition (Stage 5, slice 2: SC)

> **Rev 2 · 2026-11-16** — **SC is DONE.** `feature/skill-check-forms` is merged to `main` as `d3d7ae1` (PR #32, merge commit, tree `e335913`, the tree `git merge-tree` predicted), not tagged (OQ-SC3, Adam). Docs only, SC-T8, with Combat Decomposition Rev 14, Combat Design Rev 4, BACKLOG Rev 116, Core Instructions Rev 8, Testing Ref Rev 28, Evennia Ref Rev 37, the Skill Progression decomposition Rev 12, the Skill Improvement decomposition Rev 5, roadmap Rev 84, README Rev 65 and Lessons Rev 11 (386–395). *Shipped* lines for SC-T1–SC-T8; OQ-SC3 closed. One line in `tests/test_skillcheck.py` corrected in the same commit: a comment cited p. 149 for Thrace's example, which is on p. 150. No lock changes.
> **Rev 1 · 2026-11-16** — first version, docs only, with `docs/PolishedWorld_Combat_Decomposition.md` Rev 13, Combat Design Rev 3, the Hunting note Rev 3, BACKLOG Rev 115, roadmap Rev 83 and README Rev 64. Decomposes Stage 5's second slice, SC, from Combat Design §4.14 (OC1–OC3): the corrected opposed test, the over-100 % rule, and the two forms combat needs that `world/skillcheck.py` does not have. Six locks (SC1–SC6), six code tasks, a merge and a close-out (SC-T1–SC-T8). Read against live source the same day: `main` at `0c4c1f8` (tree `9cd6492`), *Legend* core from the project's `Legend.pdf`, Evennia 6.1.0 at the tag `v6.1.0`. **Run in the sandbox and recorded in §4:** every fixture the tasks name, against today's code and against a prototype of the locked design; exact outcome tables over all 10 000 pairs of rolls; and the in-game protocol, line by line through the real `py` command. No code is written and none is changed by this document.
> **Canonical:** `docs/PolishedWorld_Skill_Check_Forms_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Design source:** `docs/PolishedWorld_Combat_Design.md` §4.14 (OC1–OC3), §1 point 3, §4.7 (HQ2), §6; `docs/PolishedWorld_Combat_Decomposition.md` §2 (ST1, ST2; SC's row); BACKLOG *`opposed_check` lets an automatic success win on a roll outside the skill range*; *Legend* core pp. 45, 129, 131, 145–146.
**Status:** **DONE (Rev 2).** SC1–SC6 are locked (Adam, 2026-11-16, each as recommended). SC-T1–SC-T6 shipped on `feature/skill-check-forms`; merged to `main` as `d3d7ae1` (PR #32, SC-T7), not tagged; closed in the docs by SC-T8.
**Feature branch:** `feature/skill-check-forms` — one branch, one merge (ST2). Create it with `git switch -c feature/skill-check-forms --no-track origin/main`.
**Rough scope:** six code tasks, a merge and a close-out; about five to six hours of code — one long session or two at 5 h/week. One production file changes in substance (`world/skillcheck.py`), one docstring in another (`world/improvement.py`), and no command.
**Philosophy:** skynda långsamt — the book's order of resolution is kept step for step, one judge owns it, and every form is pinned by a test before anything in combat calls it.
**Labels:** SC (locks), SC-T (tasks), SCM (mutations; a letter after the number marks one added at the task, so the planned numbers stay), OQ-SC (open questions). All were free across `docs/`, `world/`, `commands/`, `typeclasses/`, `server/` and `tests/` when checked with `grep -rhoE "\b<XX>[0-9]+\b"`, before they were used. OC1–OC3 stay the Combat Design's labels for the decisions the locks carry out.

---

## 1. What the slice is

`world/skillcheck.py` has two functions today: `skill_check`, one d100 test, and `opposed_check`, two of them and a winner. Combat needs four things of that module that it does not do:

1. **Break a tie between two successes by the book** (OC1). The tie goes to the higher roll *within his skill range* (p. 45); today it goes to the higher roll, in the range or not.
2. **Apply the over-100 % rule** (OC2, p. 45). The docstring still says skills cap at 100, which P-7 ended in Stage 4.5.
3. **Compare two levels of success with no opposed test** (OC3), for attack against parry (pp. 129, 131).
4. **Run an opposed test against a roll already made** (OC3), for the wound tests (pp. 145–146) and for the manoeuvres that name *the original attack roll* (Bleed, Disarm).

None of it is combat. The slice has no new command and one live caller, `hunt`. WN and CE wait for it (ST1).

**`skill_check` does not change.** It never clamps its target and already has the bands above 100 (only 00 fumbles, a critical band of 12 at 120), with tests (`tests/test_skillcheck.py`, `TestTargetOneTwenty`). Its seven callers and its fourteen band tests are untouched by every task here.

**Skill improvement does not change.** `attempt_skill_improvement` reads only `outcome["success"]` (`typeclasses/characters.py:1354`), and the improvement roll has had its own band above 100 since Stage 4.5 (`world/improvement.py`). What changes there is one warning in a docstring that becomes false (SC-T2).

---

## 2. Decisions locked 2026-11-16 (SC1–SC6)

Adam took the six as recommended, one at a time.

**SC1 — Three public functions over one private judge.**
- `opposed_check(attacker_skill, defender_skill, attacker_mod=0, defender_mod=0)` keeps its signature. It returns `{"winner", "attacker", "defender", "excess"}`; `excess` is new (SC3).
- `opposed_against(made, skill, modifier=0)` takes a finished `skill_check` result, rolls only the resisting side and returns `{"resisted": bool, "made": dict, "resisting": dict, "excess": int}`.
- `compare_levels(attacker_level, defender_level)` takes two levels (`CRITICAL` … `FUMBLE`), rolls nothing and returns `{"winner": ATTACKER | DEFENDER | None, "levels": 0–3}` by the table on p. 131.
- A private `_judge` holds p. 45's order — level, roll within the range, skill, coin — for the first two.
- **`opposed_against` takes only a successful `made`** and raises `ValueError` otherwise, before any die is rolled. The book always opposes *the successful attack roll*, so a stalemate cannot arise; a failed `made` is the caller's programming error and not a state of play.
- *Why these shapes:* each function has one return shape. `resisted` and not `winner`, because in Disarm the roll already made can be the parry, and `ATTACKER`/`DEFENDER` would point the wrong way. `None` and not `STALEMATE` in `compare_levels`, because `STALEMATE` means *roll again later* (p. 45) and the table's "—" only means that nobody gains a manoeuvre; the attack may still have hit. Levels and not results as input, because a defender with no Combat Action is *treated as having automatically rolled a Failure* (p. 131) and has no roll to hand over.
- *Rejected:* parameters on `opposed_check` (the return shape would depend on an argument); the caller rolling and the module only judging (the over-100 % rule has to be applied before the roll, so every caller would have to fetch it and pass it in).

**SC2 — The judge counts a roll outside the skill as 0.** A success is *within the skill* when `roll <= target`. At the same level of success the judge compares the roll if it is within the skill and 0 if it is not; the rest of p. 45's order stands. OC1 then follows without a rule of its own: every success within the skill (a roll of at least 1) beats one outside it, and two outside meet at 0 and go on to the higher skill, then the coin. Outside the skill are 02–05 above the target and the critical 01 at a target of 0 or less.
- `skill_check`'s result is not touched: no new key, and `result`, `success`, `margin` and `crit_score` read as before.
- `compare_levels` is not touched by it: on p. 131 an automatic success is a success.
- *Rejected:* a key `in_range` in every `skill_check` result (seven callers would carry a key only the judge reads); a fifth rank in `_LEVEL_RANK` (it would leak into the manoeuvre table, which has four levels).

**SC3 — The over-100 % rule, and a roll already made keeps its level.**
- `excess = max(0, highest modified target − 100)`, taken off both sides. It is computed on the targets *after* every other modifier, as the book says: a hunter at 120 % with −20 for overload has a target of 100 and gives no excess.
- Both opposed forms report `excess` (0 in the ordinary case), and a side's `target` in the result is the lowered one.
- **In `opposed_against` the roll already made keeps its level and its roll.** A critical stays a critical. Whether it lies within the skill (SC2) is asked against the lowered target, `made["target"] − excess`, and the resisting side rolls against its own lowered target. `made` is returned as it came, not copied and not changed.
- **The book is silent on this,** so it is a project rule, entered in Combat Design §5. *Why this reading:* one blow has one level — re-judging would let the same attack win manoeuvres as a critical and then be weighed as a plain success in the wound test for the same cut; and the rule works in both directions, so a Resilience above 100 % is worth more than one of 100.
- *Rejected:* re-judging the made roll at the lowered target; leaving the made side untouched (a resisting skill above 100 % would then gain nothing over 100).

**SC4 — `hunt` gets the corrected judge and the over-100 % rule in this slice, and `commands/hunting_commands.py` is not edited.** It calls the same function with the same arguments. **This is read against HQ2** (*`hunt` does not change in Stage 5*): HQ2 protects the hunt's model — one roll that abstracts stalking and felling — until a hunting decomposition reconciles it with combat. It does not protect a tie-break that OC1 has decided is wrong. Combat Design HQ2 and the Hunting note's TP7 carry a note saying so (Rev 3 of each).
- The judge is tested in `tests/test_skillcheck.py`, with the die pinned at `world.skillcheck.randint`.
- The hunt gets a test of its own through `CmdHunt`, with the same pin, that reads what became of the quarry (SC-T3). Today the command is run by two tests, both in `tests/test_encumbrance.py`, and both read the modifiers and not the winner.
- *Rejected:* shielding the hunt behind a flag or a copy of the old judge (a rule decided wrong would live on, and the Hunting note's `stalk` and shot, TP6–TP7, would have two judges to choose between); the correction now and the over-100 % rule later (it needs an edit to the command, which is what HQ2 asked not to happen).

**SC5 — The roll census learns the new names in the commits that add them.** `tests/test_encumbrance.py`: `ROLL_NAMES` gains `opposed_against`; `compare_levels` goes into a second, named tuple of forms that roll nothing; and a new test requires every public function defined in `world/skillcheck.py` to stand in exactly one of the two. `ROLL_SITES` keeps its eight: the slice adds no call in production code.
- *Why:* the census exists to stop a skill test nobody decided about (the physical modifier or not, W3.1 OQ2). A name it does not know is a call it does not see.
- *Rejected:* deriving the names by walking the module's calls (the decision *rolls or does not* would be nowhere in plain text); leaving the name to WN (the first call would pass unseen unless someone remembered).

**SC6 — The in-game protocol pins the die where the tests pin it, on the running server, and takes the hunt through the real command.** Three parts: readings that need no die; the judge with the die pinned; `hunt` with the die pinned. Each step's outcome is one only the new code gives.
- **The mechanism changed when it was run** (§4.4), inside the lock: the protocol is single `py` lines, not `py/edit` buffers. In the editor a command sent with `execute_cmd` is appended to the buffer and never runs, and `:q` answered *yes* saves — which for this editor means running the buffer a second time. A `with` statement is legal on a `py` line when it is the line's only statement, which is all the protocol needs.
- *Rejected:* a Builder command that sets the next roll (production code that exists for a protocol); playing `hunt` and accepting any outcome (it shows the server reloaded and nothing else — OC1 moves the hunt's odds by hundredths of a percentage point, §4.2).

---

## 3. Verified source anchors (read 2026-11-16)

**The rulebook** (`Legend.pdf` in the project knowledge; page numbers are the book's own).

| Rule | Where | What it establishes |
| --- | --- | --- |
| Levels of success | p. 38 (*Levels of Success and Failure*) | Four, best to worst: critical, success, failure, fumble. |
| Automatic success and failure | p. 42 | 01–05 always succeeds, 96–00 always fails, *regardless of the level of his skill*. The reason an automatic success can lie outside the skill. |
| Opposed skills | p. 45 | Higher level wins; same level, *the higher dice roll within his skill range*; same roll, the higher skill; then a coin. Both fail: a stalemate, rolled again later. SC2. |
| The book's own examples | p. 45 | Stealth 75 % rolling 71 beats Perception 60 % rolling 59, and 54 loses to it; Athletics 35 % rolling 02 (a critical) beats 95 % rolling 94. SC-T1 uses them as tests. |
| Opposed skills over 100 % | p. 45 | *Whichever participant has the highest mastered skill subtracts 100 % from it and uses the remainder as a penalty to everyone in the contest*; the highest is identified *after any other modifiers*. SC3. |
| Attack and parry | pp. 129, 131 | Both roll; *the difference between them, if a difference in level of success exists*, decides. Not called an opposed test. A defender with no Combat Action *is treated as having automatically rolled a Failure*. |
| The levels table | p. 131 | Sixteen cells. Where neither side succeeded — failure or fumble against failure or fumble — the cell is "—": the winner must have succeeded. Otherwise the steps between the two levels, 1–3. SC-T5 transcribes it. |
| The wound tests | pp. 145–146 | Wounds that require Resilience *must test them in an Opposed Test against the value of the original attack roll*; four cases (Serious and Major, limb and body). In both worked examples (pp. 149, 151) the defender simply fails its own roll: Resilience 45 % rolling 53, and 38 % rolling 69 against an attack roll of 24. |
| Other users of a made roll | pp. 132–133 (Bleed, Disarm) | Bleed: Resilience against *the attacker's original attack roll*. Disarm: Combat Skill against the original attack roll *or the original parry roll*. Why SC1 names the sides `made` and `resisting`. |

**Code** (`main` at `0c4c1f8`).

| Anchor | Where | What it establishes |
| --- | --- | --- |
| `skill_check` | `world/skillcheck.py:58–114` | Target is `int(skill_value) + int(modifier)`, never clamped (`:82`); the band order (`:94–105`); the result's six keys (`:107–114`). Not changed. |
| the level constants and ranks | `:52–55`, `:119–121`, `:124` | `CRITICAL` … `FUMBLE`; `ATTACKER`, `DEFENDER`, `STALEMATE`; `_LEVEL_RANK` 3–0. |
| `opposed_check` | `:127–181` | Rolls both sides afresh (`:159–160`); both fail is a stalemate (`:164`); **the tie on the raw roll** (`:171–173`), which is OC1's defect; the docstring's *caps skills at 100 for the MVP* (`:141–144`). |
| the one caller | `commands/hunting_commands.py:99–101` | `opposed_check(hunting_value, flee, attacker_mod=caller.physical_modifier())`. Reads `result["winner"]` (`:102`), `result["attacker"]` for improvement (`:118`) and `result["attacker"]["result"]` for the fumble line (`:136`). All three keys keep their meaning. |
| the quarry's skill | `typeclasses/creatures.py:51` | `flee_skill`, default 30. No prototype overrides it (`world/prototypes.py:493`). |
| flight | `commands/hunting_commands.py:153–173` | The quarry moves through a random exit, or is deleted where the room has none. A test of *it fled* cannot read `pk` alone. |
| improvement's gate | `typeclasses/characters.py:1354–1390` | Reads `outcome["success"]` only. A lowered `target` in the dict changes nothing there. |
| the stale warning | `world/improvement.py:66–70` | Says `opposed_check` *has its OWN unimplemented >100% rule*. False after SC-T2. |
| the seven `skill_check` callers | `commands/hunting_commands.py:292`; `commands/crafting_commands.py:807`, `:1095`; `commands/repair_commands.py:139`; `world/crafting_base.py:324`; `world/fatigue.py:207`, `:267` | None is touched. |
| the roll census | `tests/test_encumbrance.py:978–1027` | `ROLL_SITES` (eight calls in five modules), `ROLL_NAMES = ("skill_check", "opposed_check")` (`:985`), counted with `ast`. SC5. |
| the hunt's only tests | `tests/test_encumbrance.py:918–951` | Two runs of `CmdHunt`, both spying on `opposed_check` for `attacker_mod` and `defender_mod`. |
| the band tests | `tests/test_skillcheck.py` | Fourteen tests, all of `skill_check`; **none of `opposed_check`**. Its order of resolution is untested today. |

**Evennia** (`v6.1.0`).

| Anchor | Where | What it establishes |
| --- | --- | --- |
| how `py` runs a line | `evennia/commands/default/system.py:227–241` | Compiled in `eval` mode, and in `exec` mode if that fails; run with empty globals and `self`, `me`, `here`, `evennia` as locals (`:289–292`). A `with` statement compiles in `exec` mode when it is the line's only statement. |
| `py/edit` | `system.py:383`, `:396–408` (`savefunc` at `:402`); `:153–164` | The editor's save function *is* the execute function (`savefunc=_py_code`), so saving runs the buffer. |
| the editor's quit | `evennia/utils/eveditor.py:76–79` | `:q` asks to save a changed buffer; `:q!` does not. |

---

## 4. What was run (sandbox: Python 3.13.18, Evennia 6.1.0, Django 6.0.10; a fresh clone of `0c4c1f8`)

A prototype of §2 was written in a throwaway clone to run the fixtures against. It is not delivered and not the implementation; the tasks write the code.

### 4.1 The defect, and how far it reaches

BACKLOG's example — *at target 3 a 05 beats an opponent's 04 at target 60* — is **wrong**: at a target of 60 the critical band is 01–06, so the 04 is a critical and wins on level (run: `defender`). The defect is real and narrower. With the attacker at a target of 3, every pair of rolls was tried against every defender target from 1 to 100: an automatic success beats a success within the skill in 81 combinations, and in none where the defender's target is above 30. Example: target 3 rolling 05 beats target 30 rolling 04 (run today: `attacker`). The entry is corrected in BACKLOG Rev 115.

### 4.2 Exact odds, over all 10 000 pairs of rolls

**OC1 alone** (attacker's chance to win):

| Attacker against defender (targets) | Today | With SC2 |
| --- | --- | --- |
| 3 against 30 | 3.78 % | 3.77 % |
| 3 against 10 | 4.65 % | 4.60 % |
| 3 against 2 | 4.90 % | 4.94 % |
| 50 against 30 | 45.62 % | 45.62 % |

**The over-100 % rule in `opposed_check`** (attacker's chance to win, then the stalemates):

| Attacker against defender | Win today | Win with SC3 | Stalemate today → with SC3 |
| --- | --- | --- | --- |
| 100 against 30 | 90.52 % | 90.52 % | 3.50 % → 3.50 % |
| 101 against 30 | 90.74 % | 90.71 % | 3.50 % → 3.55 % |
| 120 against 30 | 90.95 % | 94.15 % | 3.50 % → 4.50 % |
| 150 against 30 | 91.52 % | 94.15 % | 3.50 % → 4.75 % |
| 120 against 90 | 57.14 % | 71.14 % | 0.50 % → 1.50 % |
| 200 against 150 | 54.95 % | 82.85 % | 0.25 % → 2.50 % |

**A roll already made** (the chance that the resisting side resists, under the three readings SC3 weighed; A is the lock):

| Roll made | Resisting skill | A | B (re-judged) | C (made side untouched) |
| --- | --- | --- | --- | --- |
| target 120, roll 12 (critical) | 60 | 0 % | 32 % | 0 % |
| target 120, roll 50 | 60 | 4 % | 4 % | 4 % |
| target 80, roll 70 | 130 | 95 % | 95 % | 36 % |
| target 80, roll 45 | 130 | 61 % | 61 % | 61 % |

### 4.3 The fixtures the tasks name

Each line was run against today's `world/skillcheck.py` and against the prototype. Dice are in the order the code rolls them: attacker, defender, then the coin if one is tossed.

| Fixture | Today | With the slice |
| --- | --- | --- |
| `opposed_check(3, 30)`, dice 05, 04 | attacker | defender |
| `opposed_check(3, 2)`, dice 04, 05 (both outside) | defender | attacker (higher skill) |
| `opposed_check(30, 60)`, dice 30, 29 (a roll equal to the target) | attacker | attacker |
| `opposed_check(50, 40)`, dice 20, 20 | attacker | attacker |
| `opposed_check(50, 50)`, dice 20, 20, coin 1 / coin 2 | attacker / defender | attacker / defender |
| `opposed_check(50, 40)`, dice 80, 99 (failure, fumble) | stalemate | stalemate |
| `opposed_check(120, 30)` | targets 120, 30 | `excess` 20; targets 100, 10 |
| `opposed_check(120, 30, attacker_mod=-20)` | targets 100, 30 | `excess` 0; targets 100, 30 |
| `opposed_check(60, 130)` | targets 60, 130 | `excess` 30; targets 30, 100 |
| `opposed_check(200, 150)` | targets 200, 150 | `excess` 100; targets 100, 50 |
| `opposed_check(120, 60)`, dice 11, 30 | attacker (a critical at 120) | defender (11 is a plain success at 100; 30 is the higher roll within 40) |
| `opposed_check(120, 60)`, dice 99, 99 | — | attacker failure, defender fumble, stalemate |
| `opposed_against`, made at target 60 rolling 40, skill 50, die 45 / 30 | — | resisted / not |
| made at target 3 rolling 05, skill 30, die 04 | — | resisted (the made roll is outside its skill) |
| made at target 3 rolling 05, skill 30, die 80 | — | not resisted (the resisting side failed) |
| made at target 3 rolling 05, skill 2, die 04, coin unused | — | not resisted (both outside; the made side has the higher skill) |
| made at target 120 rolling 12, skill 60, die 03 | — | `excess` 20; resisting target 40, a critical; not resisted (12 against 03, both criticals); `made` still a critical |
| made at target 80 rolling 70, skill 130, die 20 | — | `excess` 30; resisting target 100; resisted (70 is outside the lowered 50) |
| made at target 80 rolling 45, skill 130, die 20 / 60 | — | not resisted / resisted |
| a failed `made` | — | `ValueError`, and no die rolled |
| every `opposed_against` above | — | one die rolled; `made` equal to a copy taken before |
| `compare_levels`, all sixteen cells | — | the table of p. 131, cell for cell (§7, SC-T5) |
| `compare_levels("hit", SUCCESS)` | — | `ValueError` |

**The hunt through `CmdHunt`** (a `Creature` in the room, the hunter's `hunting` value set through the trait's `mod`, `physical_modifier()` read as 0, both dice consumed inside the patch):

| Hunting, `flee_skill`, dice | Today | With the slice |
| --- | --- | --- |
| 3, 30, dice 05, 04 | killed | fled |
| 120, 30, dice 97, 20 | fled | still in the room (a stalemate) |
| 120, 90, dice 50, 85 | fled | killed |

With the prototype in place `tests.test_skillcheck`, `tests.test_encumbrance`, `tests.test_harvest_guard` and `tests.test_names_room_messages` ran green (14 and 120 tests).

### 4.4 The in-game protocol

Every line of §7 SC-T7's protocol was sent through the real `py` command as a Developer character, in a command test, against the prototype and against today's code.

- The quarry's line gave `('#8', 30)`, and the delete line `[True]` and then `[]`.
- The readings without a die gave `(20, 100, 10)`, `{'winner': 'attacker', 'levels': 3}`, `{'winner': None, 'levels': 0}` and a traceback ending in `ValueError`.
- The judge with the die pinned gave `('defender', 2)` against the prototype and `('attacker', 2)` against today's code.
- The hunt with the die pinned gave *scdeer breaks away and bolts before you can close in.* and `2` against the prototype, and *You fell scdeer.* against today's code.

**Two things the first form of the protocol got wrong,** found by running it:

- **A command sent from inside `py/edit` never runs.** `self.execute_cmd("hunt scdeer")` in an executed buffer was appended to the buffer as a new line, because the editor's command set is on the caller while the editor is open. The patch saw 0 dice.
- **`:q` after `:!` can run the buffer again.** The editor asks whether to save; any answer but *no* saves, and saving this editor executes it (`system.py:402`, `:153`). A hunt in the buffer would be made twice. `:q!` leaves without it.

Both go away with single `py` lines, so the protocol has no editor in it.

---

## 5. Dependency graph

```
SC-T1 (the judge, OC1) ──> SC-T2 (over 100 %) ──> SC-T3 (the hunt's test) ─┐
SC-T4 (the census, complete) ──> SC-T5 (compare_levels) ───────────────────┼──> SC-T7 (protocol, suite, merge) ──> SC-T8 (docs)
SC-T1, SC-T2, SC-T4 ──> SC-T6 (opposed_against) ───────────────────────────┘
```

SC-T4 depends on nothing and can be taken first. SC-T5 needs only SC-T4. SC-T6 needs the judge with both rules in it.

**Test runs** (the policy of 2026-10-30): per task, `tests.test_skillcheck` and the task's own file, with `tests.test_encumbrance` whenever the census or the hunt is touched. The whole suite once, at SC-T7.

---

## 6. Component S1 — The opposed test by the book

### Task SC-T1 — The judge, and an automatic success outside the skill
- **Goal:** Between two successes of the same level, a roll outside the skill loses to any roll within it.
- **Dependencies:** None.
- **Approach:** `world/skillcheck.py`. A private helper returns the roll if `roll <= target` and 0 otherwise (SC2). A private `_judge` takes the two results, and optionally a target for each side to measure *within the skill* against, defaulting to the result's own `target` (SC-T6 uses the option; nothing in this task does). It returns `ATTACKER`, `DEFENDER` or `STALEMATE` in p. 45's order: both failed; the higher level; the higher roll within the skill; the higher target; the coin. `opposed_check` rolls as today and calls it. The function's docstring is rewritten: step 2 says what *within skill range* means here and names SC2; the order is otherwise as it stands. The return shape does not change in this task.
- **Testing:** `tests/test_skillcheck.py` gains the first tests of `opposed_check`, with the die pinned by `side_effect` in rolling order (attacker, defender, coin). **The order** — the book's three examples (§3); the same roll, where the higher skill wins; the dead heat, with the coin showing 1 and then 2; failure against fumble, a stalemate. **Outside the skill** — the first three lines of §4.3, and an automatic success against a failure (target 3 rolling 05 against target 30 rolling 80: the attacker still wins, on level). Each class's docstring says which defect it presses on.
- **Red before green:** the two tests of §4.3's first two lines fail on `main`'s code (run: `attacker` and `defender` there). Every other new test passes on `main` too; they pin the order so that the refactor cannot move it.
- **Mutations (SCM1–SCM4):** the helper returns the roll whatever the target (the two outside-the-skill tests must fail); `<=` becomes `<` (the roll-equal-to-target test must fail); the skill tie-break is reversed (the same-roll test must fail); the both-failed check is removed (the failure-against-fumble test must fail, since failure outranks fumble).
- **In-game check:** in SC-T7, with the die pinned.
- **Commit:** `fix(skillcheck): an automatic success outside the skill ranks lowest in an opposed test (OC1, SC2)`
- **Shipped (Rev 2):** `6c868eb` on `feature/skill-check-forms`, tree `6c69dea` (the sandbox commit and a `git am` on a fresh clone gave the same tree). Ten tests in `TestOpposedOrder` and `TestOutsideTheSkill`, each also asserting that exactly the dice given were rolled. Red on `main`'s code: the two tests of §4.3's first two lines and no others (`attacker` and `defender` there). SCM1–SCM4 each fail the tests named for them; SCM3 also fails the both-outside test, which goes to the higher skill. Targeted run `tests.test_skillcheck tests.test_encumbrance`, 116 OK — the census module too, because the hunt goes through the new judge.

### Task SC-T2 — Opposed skills over 100 %
- **Goal:** The highest modified skill in an opposed test is lowered to 100 and its excess is taken off both sides.
- **Dependencies:** SC-T1.
- **Approach:** `world/skillcheck.py`. A private helper returns `max(0, highest target − 100)`. `opposed_check` computes both modified targets with the same `int()` coercion `skill_check` uses, takes the excess, and passes each side's modifier less the excess to `skill_check`, so the bands follow the lowered target with no change to `skill_check`. The return gains `"excess"`. The docstring's NOTE (`:141–144`) is replaced by the rule, with p. 45 and SC3; the *Returns* block names the new key and says that `target` is the lowered target. `world/improvement.py:66–70`: the warning is replaced by one sentence saying the rule is delivered here, in the manner of that docstring's own *DELIVERED* paragraph above it — replaced and not annotated, for the reason that paragraph gives. The module docstring of `world/skillcheck.py` gains a line that the over-100 % rule belongs to the opposed forms and not to `skill_check`.
- **Testing:** `tests/test_skillcheck.py`. The four target lines of §4.3 (`excess` and both targets); a control below 100 on both sides (50 against 30: `excess` 0, targets 50 and 30); `excess` is present when it is 0; the two dice lines for 120 against 60 — 11 and 30, where today's critical becomes a plain success and the defender wins, and 99 and 99, where the attacker's 99 is a failure at a target of 100 and the defender's a fumble at 40.
- **Red before green:** the target lines and the 11-and-30 line fail on SC-T1's code.
- **Mutations (SCM5–SCM8):** the excess is taken from the skills before their modifiers (the `attacker_mod=-20` test must fail); it is taken off the lesser side only (the 11-and-30 test and the target tests must fail); `max(0, …)` is dropped (the control below 100 must fail, with a negative excess paid out as a bonus); the excess is reported and not taken off (the target tests must fail).
- **In-game check:** `py r = __import__("world.skillcheck").skillcheck.opposed_check(120, 30); self.msg(str((r["excess"], r["attacker"]["target"], r["defender"]["target"])))` prints `(20, 100, 10)`; on `main` it prints `KeyError: 'excess'` (run).
- **Commit:** `feat(skillcheck): opposed skills over 100 % (OC2, SC3)`
- **Shipped (Rev 2):** `053eb39`, tree `0c124e2`. Eight tests in `TestOpposedOverOneHundred`. Red on SC-T1's code: seven of the eight — `KeyError: 'excess'` on the target lines, the control and the zero excess, and `attacker` on the 11-and-30 line. The 99-and-99 line is green on both, as the task's red list implies: a failure and a fumble either way. SCM5–SCM8 each fail the tests named; SCM7 also fails three of SC-T1's tests, because a negative excess is a bonus that moves the bands. Targeted run, 124 OK.

### Task SC-T3 — The hunt, read through its command
- **Goal:** A test runs `hunt` to its outcome with both dice pinned and reads what became of the quarry.
- **Dependencies:** SC-T1, SC-T2.
- **Approach:** No production code (SC4). New `tests/test_hunt_resolution.py`, an `EvenniaCommandTest` with the project's `Character`. A fixture clears the hunt cooldown, creates a `Creature` with a key of its own and a given `flee_skill`, and sets the hunter's `hunting` to a given value through the trait's `mod` (`value` is `current + mod`). The command runs inside `mock.patch("world.skillcheck.randint", side_effect=[…])`. **Receipts in every test, independent of the outcome:** `physical_modifier()` is 0 and the trait's `value` is the number meant, read before the command; the patch's `call_count` is 2 after it. **The three outcomes are read from the world:** a kill leaves a `typeclasses.corpse.Corpse` in the room and no creature; a flight leaves no corpse and no creature in the room (the creature has moved or, in a room without exits, been deleted — `hunting_commands.py:167–173`); a stalemate leaves the creature where it was.
- **Testing:** the three lines of §4.3's hunt table, one test each, named for the rule (an automatic success outside the skill does not fell the quarry; a quarry's success is lost to the hunter's excess; the excess turns a flight into a kill).
- **Red before green:** all three fail against `main`'s `world/skillcheck.py` (run: killed, fled, fled). Take the receipt by running the new file with that one module checked out from `main`, then restore it from a copy.
- **Mutations:** none new. SCM1 and SCM8 are run again against this file alone: the first test must fail on SCM1 and the other two on SCM8. That is the receipt that the hunt is read through its call and not around it. (SCM6 does not serve here: with the excess taken off the quarry alone, both hunts end as they should.)
- **In-game check:** in SC-T7.
- **Commit:** `test(hunt): the hunt's outcome under the corrected opposed test (SC4)`
- **Shipped (Rev 2):** `fd4e3dd`, tree `e907260`. `tests/test_hunt_resolution.py`, three tests, with `ActivityLogMixin` first in the bases: a kill trains `hunting` and writes the improvement line to the activity log. The fixture's room has an exit to `room2`, so a flight moves the quarry there; the assertion accepts a deletion too. Red with `main`'s `world/skillcheck.py` checked out into the clone: killed (a corpse in the room), fled, fled (`pk` 8, alive); the module was restored from a copy and compared with `cmp`. SCM1 fails the first test and SCM8 the other two; SCM6 fails none of the three, as the task says. Targeted run with `tests.test_hunt_resolution`, 127 OK.

---

## 7. Component S2 — The two new forms; S3 — close-out

### Task SC-T4 — The census knows every form
- **Goal:** A function added to `world/skillcheck.py` fails a test until someone has said whether it rolls.
- **Dependencies:** None.
- **Approach:** `tests/test_encumbrance.py`. Beside `ROLL_NAMES`, a second tuple names the public forms that roll nothing; it is empty in this task. A new test in `TestRollCensus` collects the public functions *defined in* `world.skillcheck` (by `__module__`, so the imported `ceil` and `randint` are not counted, and no name with a leading underscore) and requires that set to equal the union of the two tuples, and the two to share no name. The three places that describe the census by its two names are rewritten to say *the names in `ROLL_NAMES`*: the file's header (`:89`), the comment above `ROLL_SITES` (`:976`) and `_roll_census`'s docstring. `ROLL_SITES` is not touched.
- **Testing:** the new test is green with two names in the first tuple and none in the second.
- **Mutations (SCM9):** `opposed_check` is taken out of `ROLL_NAMES` (the new test must fail; the count test fails too, on `commands/hunting_commands.py`, which is the old guard and not this one).
- **In-game check:** none; a test of the tests.
- **Commit:** `test(census): every public form in world/skillcheck.py is a roll or is named as none (SC5)`
- **Shipped (Rev 2):** `a58a59e`, tree `db0e0c2`. `NON_ROLL_NAMES = ()` and `TestRollCensus.test_every_public_form_is_named`. SCM9 fails it and the count test (`commands/hunting_commands.py: 1, expected 2`). One receipt beyond the task: a public function appended to the module with its name in neither tuple fails the new test alone — the case SC-T5 and SC-T6 take as their red. Targeted run, 125 OK.

### Task SC-T5 — `compare_levels`
- **Goal:** Two levels of success give the winner and the number of levels won, by the table on p. 131.
- **Dependencies:** SC-T4.
- **Approach:** `world/skillcheck.py`: `compare_levels(attacker_level, defender_level)`. If neither level is a success, nobody wins: `{"winner": None, "levels": 0}`. Otherwise the difference in `_LEVEL_RANK`: `ATTACKER` or `DEFENDER` with 1–3 levels, or `None` and 0 when the levels are equal. A value that is not one of the four constants raises `ValueError` naming it. No die is rolled and no excess applies: this is not an opposed test (Combat Design §1, point 3; OQ-SC2). The docstring gives the page, says why the result is `None` and not `STALEMATE`, and that a defender with no Combat Action is passed as `FAILURE`. `tests/test_encumbrance.py`: the name goes into the tuple of forms that roll nothing, in this commit.
- **Testing:** `tests/test_skillcheck.py`. The sixteen cells against a literal table in the test, transcribed from the book and not computed (rows are the defender's level, columns the attacker's):

  | Defender ↓ / Attacker → | Critical | Success | Failure | Fumble |
  | --- | --- | --- | --- | --- |
  | Critical | — | defender 1 | defender 2 | defender 3 |
  | Success | attacker 1 | — | defender 1 | defender 2 |
  | Failure | attacker 2 | attacker 1 | — | — |
  | Fumble | attacker 3 | attacker 2 | — | — |

  The die patched to raise, to show that nothing rolls; an unknown level; the defender without an action (`SUCCESS` against `FAILURE`: the attacker, 1).
- **Red before green:** with the function written and the census tuple not yet extended, SC-T4's test fails on `compare_levels`. Take that receipt before adding the name.
- **Mutations (SCM10–SCM12):** the neither-succeeded rule is removed (failure against fumble must fail its cell: the ranks alone would give the attacker 1); the winner is swapped (the ten cells with a winner must fail); the name is taken out of the second tuple (SC-T4's test must fail).
- **In-game check:** `py self.msg(str(__import__("world.skillcheck").skillcheck.compare_levels("critical", "fumble")))` prints `{'winner': 'attacker', 'levels': 3}`, and with `"fumble", "failure"` it prints `{'winner': None, 'levels': 0}`.
- **Commit:** `feat(skillcheck): compare_levels, the attack-against-parry table (OC3, SC1)`
- **Shipped (Rev 2):** `bc35604`, tree `d0942e9`. Four tests in `TestCompareLevels` against the literal `LEVELS_OF_SUCCESS`. Red: the import first; then, with the function written and the tuple not yet extended, SC-T4's test on `'compare_levels'` and the four new tests green. SCM10 fails the two cells where failure meets fumble; SCM11 the ten cells with a winner and the no-action test (11 failures); SCM12 SC-T4's test. The in-game lines, run in plain `python3`, print §7's two dicts. Targeted run, 129 OK.

### Task SC-T6 — `opposed_against`
- **Goal:** A skill is rolled against a successful roll that already exists, and the answer is whether it resisted.
- **Dependencies:** SC-T1, SC-T2, SC-T4.
- **Approach:** `world/skillcheck.py`: `opposed_against(made, skill, modifier=0)`. First, `ValueError` if `made` is not a success — before the die. The excess is taken from `made["target"]` and the resisting side's modified target (SC3). The resisting side rolls `skill_check(skill, modifier − excess)`. `_judge` is called with `made` as the first side and its target given as `made["target"] − excess`; the resisting result carries its own lowered target. `resisted` is true when the judge names the second side. `made` is returned by identity and never written to. The docstring names the three users the book has (the wound tests, Bleed, Disarm), says that the sides are named for what they are because the made roll can be a parry, states SC3's rule and that the book is silent on it, and says that the `modifier` is the caller's to compose, as with `skill_check`. `tests/test_encumbrance.py`: the name goes into `ROLL_NAMES`, in this commit; `ROLL_SITES` stays at eight.
- **Testing:** `tests/test_skillcheck.py`. A helper builds a made roll with `skill_check` at a pinned die, so a test's `made` is a real result and not a hand-written dict. The `opposed_against` lines of §4.3, each asserting `resisted`, `excess` and the resisting `target` where the line gives them; the book's two worked examples (Resilience 45 % rolling 53, and 38 % rolling 69 against an attack roll of 24: not resisted); the dead heat (made at target 50 rolling 20, skill 50, die 20) with the coin both ways; the failed `made`, with `call_count` 0; one die for every other case; `made` equal to a copy taken before the call, and the returned `made` the same object.
- **Red before green:** with the function written and `ROLL_NAMES` not yet extended, SC-T4's test fails on `opposed_against`.
- **Mutations (SCM13–SCM17):** the made roll is re-judged at the lowered target (the critical-at-120 test must fail: it would be resisted); the made side's range is left at its own target (the 70-against-130 test must fail); the `ValueError` is removed (its test must fail); `resisted` is inverted (most must fail); the name is taken out of `ROLL_NAMES` (SC-T4's test must fail).
- **In-game check:** `py __import__("world.skillcheck").skillcheck.opposed_against({"success": False}, 50)` prints a traceback ending in `ValueError`.
- **Commit:** `feat(skillcheck): opposed_against, an opposed test against a roll already made (OC3, SC1, SC3)`
- **Shipped (Rev 2):** `cc70260`, tree `e335913`. Twelve tests in `TestOpposedAgainst`, each `made` built by `skill_check` at a pinned die. The book's worked examples read with the combatants' skills from p. 148 (the goblins' Sword and Shield 50 %, Alaric's Spear and Shield 80 %): Lilina's Resilience 45 % rolling 53 against a goblin's 39 (p. 149) and a goblin's 38 % rolling 69 against Alaric's 24 (p. 151). **One test beyond the task's list:** the scene's third example, Thrace's Spear 58 % scoring 06, a critical, which a Resilience of 38 % cannot resist (*must roll a critical success … and gain a higher roll than 06*; its criticals are 01–04), run over all hundred faces. It is on p. 150; the test's comment and the commit message said p. 149, and the comment is corrected in SC-T8 (lesson 392). Red: SC-T4's test on `'opposed_against'`, with the twelve green. SCM13 fails the critical at 120, SCM14 the 70 against 130, SCM15 the refusal, SCM16 every test that reads `resisted`, SCM17 SC-T4's test. `ROLL_SITES` stays at eight. Targeted run, 141 OK.

### Task SC-T7 — Protocol, suite and merge
- **Goal:** `feature/skill-check-forms` is on `main` by a merge commit, with the whole suite and the in-game protocol green on what was merged.
- **Dependencies:** SC-T1–SC-T6.
- **Approach:** The whole suite on the work machine with `server.test_runner.ForkTestRunner` and `--parallel`, with the settings line stashed or the two treasury tests named as the only failures; in the sandbox in batches. `git merge-tree` against `main` to predict the tree. The mutation runs restore from a backup copy and read stderr (lessons 70, and the AC2.1 loss). The protocol below on the dev server at the branch tip, after `evennia reload`. Then the PR, the merge commit, and the branch deleted. Whether the merge is tagged is OQ-SC3.
- **In-game protocol.** Typed as G0dlet in the game, one `py` line at a time. Every line is as it was run in §4.4.
  1. **Read first.** `inventory`, then `py sk = self.skills.get("hunting"); self.msg(str((sk.current, sk.mod, sk.value, self.physical_modifier(), self.cooldowns.ready("hunt"))))`. Write down `mod`; step 7 restores that number and no other. If it prints an error because `sk` is `None`, the character has no Hunting: stop and use one that has.
  2. **The excess, no die.** The line of SC-T2. Expect `(20, 100, 10)`. *Proves the rule is applied after the modifiers' sum and reported.*
  3. **The table, no die.** The two lines of SC-T5. *Proves the form exists and that neither-succeeded gives nobody a level.*
  4. **The refusal, no die.** The line of SC-T6. Expect `ValueError` as the last line. *Proves a failed roll cannot be opposed.*
  5. **The judge, die pinned.** `py with __import__("unittest.mock").mock.patch("world.skillcheck.randint", side_effect=[5, 4]) as die: r = __import__("world.skillcheck").skillcheck.opposed_check(3, 30); self.msg(str((r["winner"], die.call_count)))`. Expect `('defender', 2)`. *Proves OC1 on the server's own module; the 2 is the receipt that both dice were the pinned ones.* On `main` it prints `('attacker', 2)`.
  6. **The hunt, die pinned.** Make the quarry: `py d = evennia.create_object("typeclasses.creatures.Creature", key="scdeer", location=here); self.msg(str((d.dbref, d.db.flee_skill)))` — expect a dbref and `30`. Set the target to 3: `py sk = self.skills.get("hunting"); sk.mod = 3 - sk.current - self.physical_modifier(); self.msg(str(sk.value + self.physical_modifier()))` — expect `3` (shown as `3.0`). Then `py with __import__("unittest.mock").mock.patch("world.skillcheck.randint", side_effect=[5, 4]) as die: self.execute_cmd("hunt scdeer"); self.msg(str(die.call_count))`. Expect *scdeer breaks away and bolts before you can close in.* and then `2`. *Proves the command reaches the corrected judge: with the same dice `main` prints* You fell scdeer. *and leaves a body.*
  7. **Restore.** `py sk = self.skills.get("hunting"); sk.mod = <the number from step 1>; self.msg(str((sk.mod, sk.value)))`. Then `py self.msg(str([o.delete() for o in evennia.search_object("scdeer")]))` — the quarry fled to a neighbouring room, or was deleted if the room has no exit; expect `[True]` or `[]`. `inventory` reads as in step 1.
  - **What the protocol must not assume.** The hunt has a 30-second cooldown: step 1 reads it, and a second try waits. A staff character's hunger and thirst tick while it is run. No `evennia test` on the same machine while the activity log is being read: a hunt writes to it.
  - **Not in the protocol:** `opposed_against` with a pinned die. No command reaches it until WN, and steps 4 and 5 cover its refusal and its judge; its outcomes are the unit tests'.
- **Commit:** the merge commit of the PR.
- **Shipped (Rev 2):** PR #32 merged with a merge commit, `d3d7ae1`, tree `e335913`, parents `3ca2907` and `cc70260`; the branch deleted on origin and at work. `git merge-tree --write-tree` predicted `e335913`: `main` had not moved since the branch was cut. **The suite:** at work on a local `--no-ff` merge in a detached HEAD (`0cf563b`, tree `e335913`), `"#10"` stashed — `Ran 2050 tests in 925.085s`, `OK` (`ForkTestRunner`, `--parallel auto`). The first read, with `tail -n 5`, showed only test databases being destroyed; `-n 15` showed the result (lesson 247, recurred). The sandbox gave 2050 OK in 974 s with `--parallel 2`. A static count of `def test_` under `tests/` gives 2029; two classes inherit every test of their parents and run them again (`test_names_trade.TestTradeNamesKnown`, 13, and `test_names_trade_start.TestTradeStartKnown`, 8), which is the whole difference (lesson 386). **The protocol,** at work after `evennia reload`, as G0dlet in Limbo: step 1 `(25, 0, 25.0, -30, True)` — G0dlet was *wearied*, and step 6's line absorbs the −30 (`mod` 8); step 2 `(20, 100, 10)`; step 3 `{'winner': 'attacker', 'levels': 3}` and `{'winner': None, 'levels': 0}`; step 4 a traceback ending in `ValueError` (`world/skillcheck.py:297`); step 5 `('defender', 2)`; step 6 `('#279', 30)`, `3.0`, *scdeer breaks away and bolts before you can close in.* and `2`; step 7 `(0, 25.0)` and `[True]`. Step 7's line carried the placeholder for step 1's number into the session's instructions, where it was typed as written and raised `SyntaxError` before the number was entered (lesson 162, recurred). **One finding outside the slice:** after the flight the location panel still listed *a scdeer* — `CmdHunt._flee` moves the quarry with `move_hooks=False`, which skips the rooms' push hooks (lesson 157, recurred); filed as BACKLOG *Webclient: a quarry that flees stays in the location panel*. **OQ-SC3:** not tagged (Adam).

### Task SC-T8 — Documentation
- **Goal:** The docs say what `world/skillcheck.py` now does, and nothing in them says what it used to.
- **Dependencies:** SC-T7.
- **Approach:** One docs commit on `main`.
  - This document: *Shipped* lines and DONE. `docs/PolishedWorld_Combat_Decomposition.md`: SC DONE in §2 and the Status line; the next slice is BD.
  - `docs/BACKLOG.md`: *`opposed_check` lets an automatic success win…* → DONE, with what shipped.
  - `docs/PolishedWorld_Combat_Design.md` §4.14 and §6: the anchors `world/skillcheck.py:58` and `:127` are a snapshot at `baed99b`; say so or move them.
  - `docs/PolishedWorld_Core_Instructions.md:201`: the line describing `opposed_check`'s order gains *within the skill* and the three forms.
  - **Every `world/skillcheck.py:<line>` in a design note is read live** — the Hunting (`:199`, `:271`), Foraging (`:288`), Light (`:288`), Farming (`:279`) and Projectile (`:230`, `:300`) notes and `docs/system_designs/HANDOFF.md:1240` cite `:127`, which moves. `grep -rn "skillcheck.py:" docs` gives the list; a Rev line is left as written, a table of anchors is updated or dated.
  - `docs/PolishedWorld_Testing_Reference.md`: pinning two dice with `side_effect` in rolling order; a `with` statement on a `py` line; why not `py/edit` (§4.4). `docs/PolishedWorld_Evennia_Reference.md`: the editor's command set swallowing `execute_cmd`, and save-is-execute.
  - `docs/PolishedWorld_Skill_Progression_Decomposition.md:932` and `docs/PolishedWorld_Skill_Improvement_Decomposition.md:59`, `:117` describe the over-100 % rule as unimplemented; they are history and get a dated note, not a rewrite.
  - `docs/PolishedWorld_System_Map.md` if it names the module's surface; roadmap, README, the lessons from the slice.
  - A prose loop afterwards for *caps at 100*, *higher roll wins* and *rolls both sides* across `docs/`, `world/`, `commands/` and `typeclasses/`.
- **Commit:** `docs: close out the skill-check forms (Stage 5 slice SC)`
- **Shipped (Rev 2):** this commit, on `main` after `d3d7ae1`. Combat Decomposition Rev 14 (SC DONE; next BD), Combat Design Rev 4 (§4.14 built; §6's seams read before SC), BACKLOG Rev 116 (the entry DONE; the panel entry new; the hunt-tests entry annotated), Core Instructions Rev 8 (`:201`, the three forms), Testing Ref Rev 28 (§26), Evennia Ref Rev 37 (§23: `py` and `py/edit`), the Skill Progression decomposition Rev 12 (`:932`) and the Skill Improvement decomposition Rev 5 (`:59`, `:117`) with dated notes, roadmap Rev 84, README Rev 65 and Lessons Rev 11. The System Map names `skillcheck.py` in one arrow and not its surface, so it is not touched. **Every `world/skillcheck.py:<line>` in the design notes was read live** (`grep -rn "skillcheck.py:" docs`): `skill_check` is now at `:60` and `opposed_check` at `:193`, so `:58` and `:127` both moved — more sites than this task's list, which named `:127` only (lessons 143 and 322, recurred). Each of the eight notes' seam tables is headed *read at* a commit, and the proposals that cite a line (Hunting TP3, TP6; Foraging RP1, RP11; Projectile RWP26; Housing BP2) belong to notes read at that commit, so the notes are left as written; the series handoff's line (`HANDOFF.md:1240`) is a session's gotcha among others of its date (its `physical_modifier()` `:603–625` is at `:1017` today) and is left too. The Weight and Recipe Mastery decompositions' `:46`, `:70` and `:94` were snapshots before this slice. The prose loop (*caps at 100*, *higher roll wins*, *rolls both sides*, *higher successful roll*) over `docs/`, `world/`, `commands/` and `typeclasses/` finds only history, decisions and this slice's own text.

---

## 8. Open questions (each with what closes it)

- **OQ-SC1 — Does a wound's Resilience test take the physical modifier?** `opposed_against` takes whatever modifier it is given. The first call to it in production code changes the census's count, and the census's failure message asks the question (W3.1 OQ2). **Closes at:** WN's decomposition.
- **OQ-SC2 — Does the over-100 % rule touch attack against parry?** As built, no: the book gives the rule for *opposed tests*, attack against parry is not one (Combat Design §1, point 3), and `compare_levels` takes levels and no skills. A fighter at 130 % then gains from it only a wider critical band and a deadlier wound test. **Closes at:** ML's decomposition, with the book's combat chapter open.
- **OQ-SC3 — Is the merge tagged?** Names was, so that a server set up now would carry it. This slice changes nothing a player can see below a skill of 101 %. **Closes at:** SC-T7, Adam's call. *(Rev 2: closed — not tagged, Adam 2026-11-16: the slice changes nothing a player sees below 101 %, and `alpha-20261116` is not deployed yet.)*
- **OQ-SC4 — A `made` roll that came out of `opposed_check`.** Its `target` is already lowered, and `opposed_against` would lower it again if the resisting skill were above 100 %. No caller does this: attack and parry are plain `skill_check` rolls at the full target. **Closes at:** the first slice that wants it, or never.

---

## 9. Consequences worth reading twice

1. **The hunt's outcome changes and its file does not.** `git log commands/hunting_commands.py` will show nothing for this slice. HQ2's note and SC-T3's test are where the change is recorded.
2. **A skill above 100 % finally pays in a contest, and only there.** Today 150 % against a rabbit wins 91.52 % of the time, against 90.52 % at 100 %. With the rule it is 94.15 % — and the same 94.15 % at 120 %, because the quarry's 30 cannot be pushed below the automatic 01–05.
3. **In an opposed test the master's own critical band shrinks.** At 120 % a plain test criticals on 01–12; in an opposed test the target is 100 and the band 01–10. A roll of 11 is a critical when crafting and a plain success when hunting. This is the book's rule, not a side effect to fix.
4. **Stalemates become more common above 100 %:** 3.50 % to 4.50 % for 120 against 30, because the lesser side fails more and the master fails as often as before (96–00).
5. **Two meanings of "nobody won".** `STALEMATE` from `opposed_check` means roll again later. `None` from `compare_levels` means no manoeuvre, and says nothing about whether the blow landed. `opposed_against` has neither: it always answers.
6. **`made["target"]` and `resisting["target"]` are not the same kind of number** in `opposed_against`'s result. The first is the target the roll was made against; the second is already lowered by `excess`. A message that prints both must say so, or read `excess`.
7. **BACKLOG's example had been wrong since the entry was filed** (2026-10-31), through a design session that decided the entry. It was caught by running it (§4.1), not by reading it.
8. **`opposed_check` had no test of its order** before this slice. SC-T1's first tests are the book's own examples.
