# PolishedWorld — Hero Points Decomposition (Stage 5, slice 5: HE)

> **Rev 2 · 2026-11-24** — docs only, on `main`, with README Rev 74: *Shipped* lines for HE-T1–HE-T4 on `feature/hero-points` (`06b99ba`, `f748265`, `2f684e1`, `d914a8c`; tree `de25fb6`), components H1 and H2; the status line; OQ-HE2 closed. The choices taken at each task's STOPP 0 (Adam, each as recommended) are at their tasks. **Two departures from Rev 1:** mutations are run in the sandbox, not on Adam's machine (Adam, 2026-11-24), by `tools/mutate.py`, which HE-T1 committed with a TOML spec per task (§4); and the module's census is `TestHeroCensus` in `tests/test_hero_points.py`, not a block in `TestPushCensus`, whose door rule requires a push that no hero door makes (HE-T2). Mutants named as the code reads them or added at their tasks: HEM7, HEM8, HEM11b, HEM13a, HEM13b, HEM14b. HE-T8 gains what a parallel run does with a missing `tblib` or a failing `subTest`. The roadmap is not touched mid-slice, as under WN. No lock changes.
> **Rev 1 · 2026-11-24** — first version, docs only, with `docs/PolishedWorld_Combat_Design.md` Rev 9 (the slice's locks HE1–HE8 under HP1–HP4, a line for the heroic last action under HP3, OQ-HE1), `docs/PolishedWorld_Combat_Decomposition.md` Rev 19, roadmap Rev 89, BACKLOG Rev 122 and README Rev 73. Decomposes Stage 5's fifth slice, HE, from Combat Design §4.13 (HP1–HP4): the points stored on the character behind one module, earned from the survival tick's own span of game time with a cap of 4, *Glancing Blow* as a trim of the blow's damage inside `wounds.damage`, the command `hero` with its switch, a row in `sheet`, and a death that touches none of it. Eight locks (Adam, 2026-11-24, one at a time, each as recommended), seven code tasks, a merge and a close-out. Code read at `main` `f73db6a`; *Legend* core pp. 87–88, 145–146 and 218–219 read line by line. Two sandbox runs (§4): 257 tests in the nine modules that drive a wound, green; **35 notice the simplest *Glancing Blow***, which is why the wound tests switch it off before it is built (HE-T5).
> **Canonical:** `docs/PolishedWorld_Hero_Points_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Design source:** `docs/PolishedWorld_Combat_Design.md` §3.5, §4.4 (WO2, WO5, WO7, WN1, WN5, WN9, WN11), §4.13 (HP1–HP4, HE1–HE8), §5, §7 (OQ-HE1, OQ-WN1); `docs/PolishedWorld_Combat_Decomposition.md` §2 (ST1, ST2; HE's row); `docs/PolishedWorld_Wounds_Decomposition.md` WN-T4, WN-T8–WN-T10; roadmap decision log, *Death-consequence policy* (Rev 26); BACKLOG *Hero Points in a persistent world*; `docs/PolishedWorld_Webclient_Decomposition.md` WC12; `docs/PolishedWorld_Art_Style_Guide.md` §6.
**Status:** **In progress** (Rev 2). HE1–HE8 are locked; HE-T1–HE-T4 shipped on `feature/hero-points` (tree `de25fb6`), and HE-T5 is next.
**Feature branch:** `feature/hero-points` — one branch, one merge (ST2). Create it with `git switch -c feature/hero-points --no-track origin/main`.
**Rough scope:** seven code tasks, a merge and a close-out; about seven to nine hours of code — two sessions at 5 h/week. One new module (`world/hero_points.py`), four production files changed (`world/wounds.py`, `world/survival_ticker.py`, `commands/character_commands.py`, `commands/default_cmdsets.py`), one new command (`hero`, the first since Names), no migration, and nothing in the web client.
**Philosophy:** skynda långsamt — the store and its readers before any writer; the net under the wound tests before the rule that would change what they see; a rule no play can reach yet is proven by tests and by `py`, and says so.
**Labels:** HE (locks, in the Combat Design §4.13), HE-T (tasks), HEM (mutations), OQ-HE (open questions, in the Combat Design §7). All were free across the repository when checked with `git grep -n -w -E 'HE[0-9]+[a-z]?|HE-T[0-9]+|HEM[0-9]+|OQ-HE[0-9]+'`, before they were used. HP1–HP4 stay the Combat Design's labels for the decisions the locks fill in; HP is not used for anything new, since it also reads as Hit Points.

---

## 1. What the slice is

HP1–HP4 say *what*: two Hero Points at creation, one use in Stage 5 (*Glancing Blow*, automatic unless switched off), the other uses waiting, and points earned slowly by time played with a cap of 4. This slice says *how*, and builds it.

**What a player meets after the merge:**

- `hero` shows how many Hero Points the character has, out of 4, and whether *Glancing Blow* is on; `hero glancing off` and `hero glancing on` switch it.
- `sheet` has a row *Hero Points* in its *Combat* block.
- A line when a point is earned: one for each game day played, which is six hours at the keyboard.
- **Nothing else.** No play spends a point before ML: the only source of damage in the game is starvation and thirst, and *Glancing Blow* does not answer them (HE2). The rule is built, tested and shown by `py`, as WN-T8–WN-T10's were.

**What the slice does not build:** the re-roll and the extra Combat Action (HP3: they need a way to choose beforehand, and `hero <use> on|off` is now that way's shape); the heroic last action (p. 146: it needs a Games Master; Combat Design Rev 9 says so under HP3); Heroic Abilities (OQ-HE1); the line a player reads when a point is spent (ML writes the blow's text and reads `glancing` from the outcome); the panel (CL, WC12).

---

## 2. The locks

Each was taken on 2026-11-24 on the recommendation given, one at a time; the Combat Design §4.13 carries them. In short, with what was rejected:

- **HE1 — *Glancing Blow* trims the blow's damage before it is written.** The location is left one point short of a Major Wound (damage 2 × max − 1), which is the book's own mechanism (p. 88), and the level is derived as always (WO2, WN1). The trim comes **before** the Resilience test, so only the Serious Wound's test is made: no *maimed*, no clock, no death at once. *(b)* A vital Serious Wound's minutes of unconsciousness are counted on the damage written, not on the blow's whole. *(c)* A location already at a Major Wound is not downgraded and costs no point; a location already one short that is hit again costs a point, takes no damage, and is tested again (*not repeated unless the location is wounded again*, p. 145) — with nothing sustained, a lost test knocks no one out. *Rejected:* the whole damage stored and the wound flagged Serious (two truths about one location; healing, `health`, `status` and the clocks would each have to know the flag — BD7's argument).
- **HE2 — It answers a blow to a location, with or without an attack roll, and never `ALL`.** Everything that goes through `_wound` can be downgraded; starvation and thirst cannot. A Hero Point would buy one more point of starvation, 1200 seconds, and the automatic spend would burn a starving player's points while they looked for food; `ALL` already sets no state and calls for no test (WN5). *Rejected:* every source; only a source with `made` (a fall would maim with no rescue, and the lock would wait on OQ-WN1).
- **HE3 — The switch is a new command, `hero`.** `hero` shows the points and the switch; `hero glancing off` and `hero glancing on` set it. The use is named, so that HP3's uses fit the same syntax. On is the default and a missing Attribute means on. The switch is a choice and not an act: it costs nothing and is not refused to a collapsed or senseless body. *Rejected:* a switch inside `status` (a reader made a writer); Evennia's account options (the choice belongs to the character, as the points do).
- **HE4 — A point is earned for every game day the survival tick gives the character.** *(a)* Every tick counts — resting, asleep, collapsed or senseless; a statue has no session and earns nothing. *(b)* The tick's own span of game seconds goes into a counter through one door, as natural healing's does. *(c)* The starting rate is one point per 24 game hours, 6 real hours at `TIME_FACTOR` 4: the book's two points per story, a story taken as three evenings of four hours — **the length of a story is this project's assumption, not the book's**. *(d)* At the cap the counter does not run and its Attribute is removed. *Rejected:* counting ticks (a whole tick to whoever logged in a second before it); stamps at login and logout (a crash leaves a stamp open); a counter that fills and waits at the cap (a cap of 5 by another name).
- **HE5 — Death touches neither the points nor the counter.** The restore block gains no line. *Rejected:* a respawn at 2 (a body with none would starve itself for two — the death-consequence policy's (iv) again); a death that costs points (a new term in the death contract, falling on those who saved their points or starved); a counter zeroed (played time is not unplayed by a death).
- **HE6 — One module writes, and `wounds.damage` takes the point itself.** `world/hero_points.py` is the only writer of three Attributes and has three doors, each with one caller in production. *(a)* `wounds.damage` asks the module's door, which answers and takes the point in the same call, so a point taken and a blow trimmed cannot come apart; `wounds` imports `hero_points` and never the other way round. *(b)* A missing Attribute reads as 2 and nothing is written at creation (WN1's answer; no backfill, no migration). **Zero is stored as 0 and never removed.** *Rejected:* the writer `apply_health_damage` deciding and taking the point afterwards (two steps in two modules); 2 written at creation with a backfill command (a step in the first deploy).
- **HE7 — `sheet` shows them; `status` does not; no meter.** *(a)* A row *Hero Points n/4* in `sheet`'s *Combat* block. `status` keeps its four vitals. *(b)* The way to the next point is not shown; a line is sent when a point lands. *Rejected:* a row in `status` (a figure that moves every six hours among four that move by the minute); a meter in `hero` (something to stand and watch — and the one that can be added later, where one taken away is a loss).
- **HE8 — The merge is tagged, and HE is not a condition of the first deploy.** The tag follows the pattern (`alpha-YYYYMMDD`, annotated) and the runbook's §7 moves to it (lesson 418). A character made before HE loses nothing (HE6), no rule a player meets changes (HE2), and the snapshot keeps its shape (HE7). If L6.1 has run by then, HE is the second deploy onto a running instance — the receipt LM10 check (3) waits for. *Rejected:* L6.1 waiting for HE; no tag.

---

## 3. Verified source anchors (read 2026-11-24, `main` at `f73db6a`)

**The book** (*Legend* core, read line by line in the project copy):

| Page | What it says | Used by |
| --- | --- | --- |
| 87 | Two Hero Points at the start; two at the close of a story, zero to four by how the Adventurer did; at most one ad-hoc award per story. No cap. | HP1, HP4, HE4 |
| 88 | Each use costs one point, spent for good. *Glancing Blow*: an Adventurer who suffers a Major Wound may spend a point to make it a Serious one; the damage taken becomes one Hit Point less than a Major Wound would need. | HE1 |
| 88 | The other uses: a last Combat Action, a re-roll, a hint from the Games Master, a Heroic Ability. | HP3 |
| 145 | A Serious Wound's test: a limb is useless on a lost test; head, chest and abdomen are unconscious for the damage sustained in the attack, in minutes. The test is not repeated unless the location is wounded again. | HE1 |
| 146 | A Major Wound: *maimed*; a limb's clock of CON + POW minutes; a vital location's death at once on a lost test, else a clock of half CON + POW rounds. The heading says *lost twice its starting Hit Points*; the text says a negative score equal to the starting Hit Points. | HE1 |
| 146 | Heroic last actions: one act for a Hero Point after a Major Wound, at the Games Master's word. | HP3 (Rev 9) |
| 218–219 | Heroic Abilities are bought with Hero Points. The twenty described cost 8, 10 or 12 each. | OQ-HE1 |

**The book does not say** whether the minutes are counted on the blow before or after the trim, nor what a blow to a location already at a Major Wound does. HE1 (b) and (c) answer both.

**The code:**

| Anchor | What is there |
| --- | --- |
| `world/wounds.py:60` | `MAJOR`; `:133` `level(maximum, damage)` — `MAJOR` at `left <= -maximum`, so at damage ≥ 2 × max. One short is 2 × max − 1. |
| `world/wounds.py:376` | `_wound(char, key, maximum, damage_now, amount, made)` — the Serious rows read `amount` for the minutes. |
| `world/wounds.py:426` | `damage(char, amount, location, made=None)`. The order: `check_location`, the two `ValueError`s for `made`, `amount <= 0` returns `None`, no body or `ndb._dying` returns `None`, the `ALL` branch returns with an empty `wounds` list and never calls `_wound`, then the named or random location is written and `_wound` answers. |
| `world/wounds.py:708` | `start_clock` — a location whose clock runs keeps its earlier deadline. |
| `typeclasses/characters.py:1605` | `apply_health_damage` — carries out what the outcome calls for; `if wound["unconscious"] and minutes:` already skips a length of 0. Pushes `char`. |
| `typeclasses/characters.py:1685` | `at_character_death`; the restore block is `:1796–1832` and calls `wounds.restore_at_respawn` at `:1798`. |
| `world/survival_ticker.py:71` | `_deplete_character`; `elapsed = _tick_game_seconds(char)`; `:116–117` `if healing.accrue(char, elapsed): char.msg(healing.HEALED)`. |
| `world/survival_ticker.py:130` | `_tick_game_seconds` — game seconds since the character's previous tick, 0 for the first tick after a puppet or a reload: time is lost, never gained. |
| `world/survival_ticker.py:195` | The one production call of the writer: `location=wounds.ALL`. |
| `world/healing.py:86` | `accrue(char, game_seconds)` — the counter-through-a-door pattern HE4 follows. |
| `world/fatigue.py:163` | `db.awake_seconds` — a counter in game seconds fed by the tick, zeroed by sleep; not reusable. |
| `typeclasses/characters.py:569–580` | `db.away_since` — game time at logout, `None` while healing is blocked; not reusable. |
| `commands/character_commands.py:61` | `CmdStatus`: four vitals. `:342` `CmdSheet`; its *Combat* block begins at `:399`. |
| `commands/default_cmdsets.py:80–84` | The character commands are added here. |
| `tests/test_client_state.py:1094` | `WOUND_ATTRIBUTES`; `:1095` `DOOR_WRITES`; `:1180` `DOORS`; the AST test that holds the tuple to what `world/wounds.py` writes. |

**No production code names Hero Points:** `grep -rn -i hero world typeclasses commands web` finds nothing of the kind. There is no preference mechanism in the game — no settings command and no Attribute that carries a player's choice — so `hero glancing off` is the first, and its shape is the precedent.

**BACKLOG was searched** for `hero`, `Glancing`, `Major Wound`, `respawn`, `played`, `away_since` and `cap` before the locks (lessons 238 and 408). Five entries name *Glancing Blow* or a Major Wound; none says how a downgrade is done.

---

## 4. What was run (sandbox: Python 3.13, Evennia 6.1.0, Django 6.0; two copies of a fresh clone of `f73db6a`)

**The baseline.** The nine modules that drive a wound or show one — `test_wounds`, `test_wound_states`, `test_wound_clocks`, `test_wound_report`, `test_wound_unconscious`, `test_client_state`, `test_survival_death`, `test_names_statue_body`, `test_sheet_combat`: **257 tests, OK**, 174 s on one core. The rest of the suite's 2327 was not run; the whole suite is HE-T8's and Adam's machine's.

**P1 — the simplest *Glancing Blow*** (seven lines in `wounds.damage` before the write: a blow that would take a location from below a Major Wound to one is trimmed to 2 × max − 1 when `db.hero_points`, read as 2 when missing, is above 0 and `db.hero_glancing_off` is unset; the point is taken in place). 257 tests, **35 fail** (34 failures, 1 error), 170 s:

| Module | Fail | Why it notices |
| --- | --- | --- |
| `test_wound_clocks` | 17 | no Major Wound, so no clock starts |
| `test_wound_states` | 11 | no *maimed*, no death at once; the Serious rows are read instead |
| `test_wound_report` | 5 | the lines name a Serious Wound |
| `test_wound_unconscious` | 1 | the length is the trimmed damage's |
| `test_client_state` | 1 | `TestPushCensus.test_every_attribute_the_wound_module_writes_is_named`: the prototype wrote `hero_points` from `world/wounds.py` |

`test_wounds` does not notice: it holds the pure functions and `ALL`.

**What thirty-four means.** The test body has two Hero Points and the switch on, because a missing Attribute is both (HE3, HE6). Every test that drives a Major Wound through a named location would have it downgraded. So the four base classes — `_Clock`, `_Body`, `_Report`, `_Out` — switch *Glancing Blow* off in `setUp` **before the rule exists** (HE-T5), through the door HE-T3 builds, and HE-T6 then lands on a suite that stays green except for its own new tests.

**What the thirty-fifth means.** The census already refuses the shortcut: an Attribute written from `world/wounds.py` that is not a wound Attribute fails a test today. HE6 (a) keeps the write in `world/hero_points.py`, behind a door.

**Not run:** nothing of HE's own beyond P1. **Mutations are run in the sandbox** *(Rev 2; Rev 1 said Adam's machine, decided 2026-11-23)*: `tools/mutate.py`, committed at HE-T1, reads a TOML spec per task (`tools/mutants/he_t<n>.toml`), runs the unmutated tree first, mutates, runs the task's test modules in parallel with `ForkTestRunner` and prints a summary in which each kill is checked against the test the spec expects. On Adam's machine every mutant of HE-T1 reported no tests, since his venv has no `tblib` (HE-T1's *Shipped*), and Adam moved the runs to the sandbox until the project moves to Claude Code. Test counts are predicted with the runner's own collection, not with `grep` (Testing Reference §27.1, lesson 442).

---

## 5. Dependency graph

```
        ┌─> HE-T2 ───────────────────────┐
HE-T1 ──┼─> HE-T3 ──> HE-T5 ──> HE-T6 ───┴─> HE-T7 ─┐
        └─> HE-T4 ──────────────────────────────────┴─> HE-T8 ──> HE-T9
```

HE-T1 is the store and its readers, and everything reads it. HE-T2 (earning), HE-T3 (the command) and HE-T4 (the row) are independent of each other after it. HE-T5 needs HE-T3's door to switch the wound tests off; HE-T6 needs HE-T5's net. HE-T7 holds death to HE5 and needs both a counter (HE-T2) and a spend (HE-T6) to be worth writing.

**Nothing on the branch between HE-T1 and HE-T8 changes what `main` does to a body.** Earning (HE-T2) is the only task whose effect a player would meet, and it gives and never takes.

---

## 6. Component H1 — The store

### Task HE-T1 — The module and its readers
- **Goal:** `world/hero_points.py` exists, and two readers answer how many points a character has and whether *Glancing Blow* is on.
- **Dependencies:** none.
- **Approach:** *(Rev 2: the script was meant for Adam's machine and runs in the sandbox, §4.)* three constants — `START = 2` (HP1), `CAP = 4` (HP4) and `GAME_SECONDS_PER_POINT = 24 * 3600` (HE4), each with its lock and the book's page in a comment. Three Attribute names, written nowhere yet: `hero_points` (a whole number), `hero_progress` (game seconds towards the next point) and `hero_glancing_off` (present only while the switch is off). `points(char)` returns the stored number, or `START` when the Attribute **is `None`** — never `or START`, which would give a spent-out character two. `glancing_on(char)` is `not char.db.hero_glancing_off`. The module imports nothing from `world.wounds` or `world.body` and knows nothing of a body (HE6). The mutation script for Adam's machine is written here, from Testing Reference §27.1's harness.
- **Testing:** a new `tests/test_hero_points.py`. A fresh character reads 2 with nothing stored; a stored 0 reads 0; a stored 3 reads 3; the switch reads on with nothing stored and off with the Attribute set. The constants are pinned against HP1 and HP4. An import census holds `world/hero_points.py` free of `world.wounds`.
- **Red before green:** the stored 0 first, against a reader written with `or START` on purpose in the working tree — it reads 2 — then the reader as it should be.
- **Mutations (HEM1–HEM3):** `or START` for the `is None` test; `START` 3; the switch read as on when the Attribute is set.
- **In-game check:** `py from world import hero_points; self.msg(str((hero_points.points(self), hero_points.glancing_on(self), self.db.hero_points)))` on `adam` gives `(2, True, None)`: two points, nothing stored.
- **Commit:** `feat(hero): the module, its constants and its readers (HP1, HP4, HE6)`
- **Shipped (Rev 2):** `06b99ba` on `feature/hero-points`, tree `a9ed203` (the sandbox commit and a `git am` on a fresh clone gave the same tree, as for every task below). Choices at STOPP 0 (Adam, each as recommended): the names as above; the harness committed as `tools/mutate.py`, a new top-level directory outside every census's `PRODUCTION` tuple (`server/` is in three), after `art/tools/assetpipe.py`; a TOML spec per task under `tools/mutants/`, read with `tomllib` and never executed, each mutant naming the test expected to kill it (lesson 181); the import census in `tests/test_hero_points.py`, holding the module free of every game package in every spelling — the repository writes `from world import x`, which a census of `world.wounds` alone would miss — and tried on the spellings it must catch. Eleven tests. Red: the stored-0 test against an `or START` reader, *2 != 0*. HEM1–HEM3 killed. The harness was also seen to report SURVIVED, SKIPPED (0 and 2 matches), NO-RUN (a syntax error) and a red baseline. **On Adam's machine every mutant was NO-RUN:** without `tblib` a parallel worker cannot send a failure back (*cannot pickle 'traceback' object*); reproduced in the sandbox by uninstalling it. In-game: `(2, True, None)`.

---

## 7. Component H2 — Earning, and what is shown

### Task HE-T2 — A point for a game day played
- **Goal:** The survival tick feeds a counter, and a full game day becomes a Hero Point, up to four.
- **Dependencies:** HE-T1.
- **Approach:** `hero_points.accrue(char, game_seconds)`, the module's first door, called once from `_deplete_character` beside `healing.accrue` with the same `elapsed`. In order: at `CAP` the counter's Attribute is removed if it is there and nothing is added (HE4 d); a span of 0 or less adds nothing; otherwise the span is added, whole multiples of `GAME_SECONDS_PER_POINT` become points up to `CAP`, and the remainder is carried — unless the cap was reached, when the Attribute is removed. It returns the points that landed, and the tick sends one line when that is above 0, as it does for `healing.HEALED`. No buff is read: `fatigue_rate` is fatigue's. Resting, asleep, collapsed and senseless bodies are fed like any other (HE4 a). The line's wording is chosen at the task's STOPP 0 against the Tone Guide. **The census** *(Rev 2: built as `TestHeroCensus`, see* Shipped*)* (`TestPushCensus`) gains the module's block: the tuple of its Attributes, held to what `world/hero_points.py` writes by an AST test of the same shape as the wound module's; its doors; and one caller per door. Nothing of it is in the `char` snapshot (WC12), so the tick's push is unchanged; a comment there names CL, which will have to push `char` when a point lands.
- **Testing:** a counter one second short of a day earns nothing; the second after earns one and carries nothing; two days and an hour in one span earn two and carry the hour; a body at 3 with two days earns one and has no counter; a body at 4 has no counter after a span, and a counter stored by hand at 4 is removed; a span of 0 writes nothing; a missing `hero_points` and a day gives a stored 3. Through the tick: a collapsed body earns; the line is sent once for a span that earns two.
- **Red before green:** the test at the cap first, against an `accrue` that only adds and divides: the body reads 5.
- **Mutations (HEM4–HEM9):** no cap; the remainder dropped below the cap; the remainder kept at the cap; the counter left to run at the cap; `>=` read as `>` at the day's edge; the tick calling with a constant instead of `elapsed`.
- **In-game check:** `py self.db.hero_progress = 86000`, then wait for the next survival tick (at most ten minutes; a tick adds 2400 game seconds, and the first tick after a reload adds none). The line arrives, `hero` — once HE-T3 is in; until then the `py` of HE-T1 — shows 3, and `py self.msg(str(self.db.hero_progress))` shows the remainder. Afterwards `py self.attributes.remove("hero_points")` and `py self.attributes.remove("hero_progress")`.
- **Commit:** `feat(hero): a Hero Point for a game day played, capped at four (HP4, HE4)`
- **Shipped (Rev 2):** `f748265`, tree `5ee4cbc`. Choices at STOPP 0: the line, `hero_points.EARNED` — *The hard days behind you have left you steadier. Your Hero Points have grown.* — with no number (Tone Guide §7) and no count, since a span can land two, and the book's term, since nothing else shows the points unasked (OQ-HE2 closed); the census as **`TestHeroCensus`** in `tests/test_hero_points.py` — `HERO_ATTRIBUTES` are exactly what `world/hero_points.py` writes, no other production file writes an Attribute named `hero_*` (P-2), and `DOORS` maps each door to its one caller in either spelling — and not a block in `TestPushCensus`, whose door rule requires the caller to push, which no hero door does (HE7); the snapshot's exact keys in `TestCharSnapshot.test_keys_and_types` are where CL's change will be seen; the call directly after healing's, before the warnings, so W4.2's order is untouched. The span is read as a whole number, as healing reads it. Sixteen tests; the tick is tried at 3000 game seconds, so a constant 2400 is seen. Red: the cap test against an `accrue` that only adds and divides returned *2* where 1 was due (the assertion on the body was not reached). HEM4–HEM9 killed. **HEM7** is a stored counter left standing at the cap: one left to run is removed again by step 3. **HEM8** moves the day's edge inside the division: the code divides and does not compare. Neighbours (§27.1's set and every module that drives the tick or scans the packages): 29 modules, 1013 tests OK. In-game: the line came on the second tick after a reload, `(3, True, 3)`, remainder 2000.

### Task HE-T3 — The command `hero`
- **Goal:** A player reads their Hero Points and switches *Glancing Blow* off and on.
- **Dependencies:** HE-T1.
- **Approach:** `CmdHero` in `commands/character_commands.py`, key `hero`, category *Character*, added in `default_cmdsets.py` beside `CmdSheet`. With no argument: the points out of `CAP`, and whether *Glancing Blow* is on. `hero glancing off` and `hero glancing on` call `hero_points.set_glancing(char, on)`, the module's second door, which removes the Attribute for on and sets it for off, and answers with what the switch now is; setting it to what it already is says so and writes nothing. Anything else gets the usage line. The command does not go through `refuse_if_collapsed` (HE3). The help text says what a Hero Point is, that one is earned slowly by time played and four is the most a character holds, what *Glancing Blow* does, and that it works by itself unless switched off; it uses the book's words (*Hero Points*, *Glancing Blow*; Art Style Guide §6). The census names `set_glancing` and its one caller.
- **Testing:** `EvenniaCommandTest`. The bare command at 2, 0 and 4; off, then the bare command; off twice; on; a wrong word; a collapsed body is answered. The help entry exists and names the cap by reading `CAP`, not by a literal 4.
- **Red before green:** *off twice writes nothing*, against a door that always writes.
- **Mutations (HEM10–HEM13):** on and off swapped; the door setting `False` instead of removing; the collapse refusal added; the cap printed as a literal.
- **In-game check:** `hero` → two of four, *Glancing Blow* on. `hero glancing off` → off; `hero` shows it; `py self.msg(str(self.db.hero_glancing_off))` → `True`. `hero glancing on`; the same `py` → `None`. `help hero` reads as written.
- **Commit:** `feat(hero): the hero command and the Glancing Blow switch (HP2, HE3)`
- **Shipped (Rev 2):** `2f684e1`, tree `f62c180`. Choices at STOPP 0: the screen in `sheet`'s row format — *Hero Points 2/4*, *Glancing Blow on* and a line that names the switch — and answers that say what the choice costs (*A Major Wound will stand, and your Hero Points are kept* / *will cost a Hero Point and be a Serious Wound instead*), *already* when nothing changes, the usage for anything else, the words in any case; the cap in the help formatted from `CAP` in `get_help` when asked (Evennia's `Command.get_help` returns `__doc__`, `command.py:576`), since only a test with `CAP` patched to 7 can tell a read cap from a typed 4 — the search index keeps the unformatted docstring (`command.py:111–118`); **`set_glancing(char, on) -> bool`**, True when the switch changed, deciding on `glancing_on` in the same call as the write. The hint reads *hero glancing off or hero glancing on*: a pipe is Evennia markup. Fifteen tests; the help is read through Evennia's `help` on `CharacterCmdSet`, which also proves the command is there. Red: off twice against a door that always writes, *True* where False was due. HEM10–HEM13b killed; **HEM11b**, a needless write behind the right answer, is seen only by the spies on the handler and is their receipt; HEM13 is two, HEM13a (the help) and HEM13b (the screen). **A failing `subTest` cannot be reported by Django's parallel runner** (`MaybeEncodingError`, the subtest is not picklable): HEM1 reported no tests, and `tools/mutate.py` now runs such a mutant once more serially, marked *(serial)*. Neighbours: 26 modules, 807 tests OK. In-game as written.

### Task HE-T4 — The row in `sheet`
- **Goal:** `sheet` shows the Hero Points in its *Combat* block.
- **Dependencies:** HE-T1.
- **Approach:** one row after *Damage Modifier*, in the block's own format: *Hero Points*, then `points(char)` and `CAP` as *n/4*. Read on every call, never stored (BD7). `status` is not touched (HE7), and a test says so.
- **Testing:** in `tests/test_sheet_combat.py`: the row at 2, 0 and 4; it comes after *Damage Modifier*; `status` prints no line that names a Hero Point.
- **Red before green:** the row's test, against today's `sheet`.
- **Mutations (HEM14–HEM15):** the stored Attribute read directly (a fresh character shows *None/4*); the row added to `status`.
- **In-game check:** `sheet` on `adam` → *Hero Points 2/4* under *Damage Modifier*. `status` → four vitals, as before.
- **Commit:** `feat(sheet): the Hero Points row (HE7)`
- **Shipped (Rev 2):** `d914a8c`, tree `de25fb6`. Choice at STOPP 0: **the row follows the Combat block** — a body without characteristics has no block and no row (`body.derived` returns `None`, `body.py:266–273`), and `hero` still shows its points; `test_no_block_without_a_body_to_read` now holds it. Five tests, the values looped without `subTest` (HE-T3). Red: the four row tests against today's `sheet`; the `status` and no-block tests were green before and after. HEM14, HEM14b (the cap typed) and HEM15 killed. HE-T3's HEM13b then matched the sheet row too and was SKIPPED as a double match; its string spans two lines since. Neighbours: 26 modules, 812 tests OK. The runner collects **2374** for the whole suite. In-game: *Hero Points 2/4* under *Damage Modifier*; `status` as before.

---

## 8. Component H3 — *Glancing Blow*

### Task HE-T5 — The net: the wound tests switch it off
- **Goal:** The four wound test modules say that *Glancing Blow* is off for their bodies, and nothing else changes.
- **Dependencies:** HE-T3.
- **Approach:** `hero_points.set_glancing(body, False)` in `setUp` of `_Clock` (`tests/test_wound_clocks.py`), `_Body` (`test_wound_states.py`), `_Report` (`test_wound_report.py`) and `_Out` (`test_wound_unconscious.py`), for every body the class wounds, each with a comment that names HE1 and §4's P1. No production file is touched. The suite is green before and after, which is the task's weakness: the proof that the net holds is P1's patch, applied by hand in the working tree and reverted.
- **Testing:** the nine modules of §4, green. With P1's seven lines applied on top: **the thirty-four are green and the census still fails**; the lines are then removed and the tree is clean (`git status --short` shows the four test files only).
- **Red before green:** P1 on the untouched tests first — the thirty-four fail as §4 lists them — then the `setUp` lines.
- **Mutations:** none of the production code is changed; the P1 run is the task's mutation and is recorded in the commit message with its counts.
- **In-game check:** none; no player-facing behaviour changes.
- **Commit:** `test(wounds): the wound tests switch Glancing Blow off (HE1, HE-T5)`

### Task HE-T6 — The trim in `wounds.damage`
- **Goal:** A blow that would give a location a Major Wound gives it a Serious one instead, for one Hero Point, when the character has one and has not switched it off.
- **Dependencies:** HE-T5.
- **Approach:** `hero_points.take_for_glancing(char)`, the module's third door: when `points(char)` is above 0 and `glancing_on(char)`, it stores one fewer and returns True; otherwise it writes nothing and returns False. Its one caller is `wounds.damage`, in the named-or-random branch only, **after every refusal** — the location, the two `ValueError`s, the amount, the missing body and `ndb._dying` — and before the write:

  | The location before the blow | The blow would leave it | What happens |
  | --- | --- | --- |
  | below a Major Wound | below a Major Wound | nothing; the door is not asked |
  | below a Major Wound | at a Major Wound | the door is asked; on True the amount becomes 2 × max − 1 − the damage before |
  | at a Major Wound | — | nothing; the door is not asked (HE1 c) |

  The trimmed amount is what is written and what `_wound` is given, so a vital Serious Wound's minutes are the trimmed damage's (HE1 b). **A trimmed amount of 0** — a location already one short, hit again — writes no damage and is still answered by `_wound` (HE1 c): the outcome is not `None`, the test is made, a limb may be *disabled*, and for a vital location `unconscious` is False in the outcome when the minutes are 0, not merely skipped by the writer. Every wound's dict gains `glancing`, True or False, for ML to read. The `ALL` branch is not touched (HE2). The census *(Rev 2: `TestHeroCensus.DOORS`, HE-T2)* names the door and `world/wounds.py::damage` as its caller; the writer above still pushes `char`.
- **Testing:** a new `tests/test_glancing_blow.py`, on the decomposition's body where it helps (head 4: Major at 8, one short at 7) and with `ROLL`, `MADE`, `WIN` and `LOSE` from `tests.test_wound_states`. An unhurt head and a blow of 10: 7 stored, one point gone, Serious, no state, no clock, `glancing` True; with a lost test, senseless for 7 minutes and not dead. A leg the same way: *disabled* on a lost test, never *maimed*. A head at 5 and a blow of 10: 2 written, 2 minutes. A head at 7 and a blow of 1: a point gone, 7 stored, tested, `unconscious` False. A head at 8 already: nothing taken, the damage added. No points: the Major Wound as today. Switched off: the same, and the points untouched. `made=None`: trimmed all the same (HE2). Ten points of `ALL`: no point taken, and the head's Major Wound kills as it does today. A blow that stays below a Major Wound: the door is not called (a spy). A failed `made`: `ValueError`, and no point taken. Two blows on a body with two points, then a third: the third maims.
- **Red before green:** *an unhurt head and a blow of 10*, against today's `damage`: 10 stored, *maimed*, a clock.
- **Mutations (HEM16–HEM24):** the trim to 2 × max (still a Major Wound); the trim to 2 × max − 2; the door asked before the refusals (a point lost to a `ValueError`); the door asked for a location already at a Major Wound; the door asked in the `ALL` branch; `_wound` given the blow's whole amount (10 minutes for 7); a trimmed 0 returned as `None`; `glancing` always False; the door ignoring the switch.
- **In-game check** *(by `py`; no play reaches this before ML — HE2)*, on a character made for it and never on the alpha server (Testing Reference §27.3): `hero` → 2. `py self.apply_health_damage(10, location="head"); self.msg(str((self.db.body_damage, self.db.wound_states, self.db.wound_clocks)))` on a head of 4 → `{'head': 7}`, no state, no clock; `hero` → 1; `status` names a Serious Wound to the head. Then `hero glancing off` and `py self.apply_health_damage(1, location="head")` → the head at 8, *maimed*, a clock, senseless until it is due (WN-T10); `hero` answers a senseless body (HE3) → still 1. **The clock kills when it runs out** — 50 seconds at CON + POW 20 — unless `wounds.stop_clock` is called first; left to run, the body comes back in the temple with a maimed head and `hero` → 1, which is HE5 seen in play. Afterwards the wound's own clean-up from Wounds WN-T10, and `py self.attributes.remove("hero_points")`, `py self.attributes.remove("hero_glancing_off")`.
- **Commit:** `feat(wounds): Glancing Blow trims a Major Wound to a Serious one for a Hero Point (HP2, HE1, HE2, HE6)`

### Task HE-T7 — Death leaves them
- **Goal:** A death and its respawn change neither the Hero Points nor the counter towards the next.
- **Dependencies:** HE-T2, HE-T6.
- **Approach:** no production change (HE5). A test kills a body that holds 3 points, a half-full counter and the switch off, by starvation through the tick and by a Major Wound's clock, and reads all three afterwards. The census holds `Character.at_character_death` out of the callers of the module's doors, with a message that names HE5 and the death-consequence policy's (iv). **This test is green on its first run and has no red before green;** its worth is the mutations, and the task says so in its commit.
- **Testing:** the two deaths; a death with nothing stored leaves nothing stored (so the body still reads 2).
- **Red before green:** none, as said. In its place, HEM25 is applied by hand before the commit and the test is seen to fail.
- **Mutations (HEM25–HEM27):** the restore block removing `hero_points`; removing `hero_progress`; setting the points to `START`.
- **In-game check:** `py self.db.hero_points = 3`, then a death by `py self.at_character_death()` on a development database; in the temple, `hero` → 3. Afterwards `py self.attributes.remove("hero_points")`.
- **Commit:** `test(hero): death leaves the Hero Points and the counter (HE5)`

---

## 9. Component H4 — Close-out

### Task HE-T8 — Protocol, suite and merge
- **Goal:** The branch is proven whole and is on `main`, tagged.
- **Dependencies:** HE-T4, HE-T7.
- **Approach:** the in-game checks of HE-T1–HE-T7 run in order on the home database, on `adam` and on a body made for HE-T6; the whole suite once with `ForkTestRunner` and `--parallel auto`, the count predicted by the runner's collection first; `node --test tests/js/*.js`, which nothing here should move; `git merge-tree` for the tree the merge will have. *(Rev 2)* **Before the suite on Adam's machine:** `pip install tblib` in the venv — without it a parallel run with a failure crashes with *cannot pickle 'traceback' object* and names nothing (HE-T1); and a failing `subTest` crashes it the same way even with `tblib` (HE-T3), so a parallel run that reports no tests is run again serially. The count to predict is the runner's: 2374 at HE-T4, plus what HE-T5–HE-T7 add. Push, PR, merge commit and the annotated tag `alpha-YYYYMMDD` in GitHub Desktop and on GitHub (lesson 332); the receipt is a reading of `origin` in a fresh clone.
- **Testing:** the suite, green; the count as predicted.
- **Commit:** the merge commit.

### Task HE-T9 — Documentation
- **Goal:** The documents say what was built and where it stands.
- **Dependencies:** HE-T8.
- **Approach:** this document's *Shipped* lines and Status; Combat Decomposition's row and Status; Combat Design §4.13 and §6 dated after the merge; the Alpha Runbook's §7 — the tag, and a paragraph for a database made before it: nothing is needed (HE6, HE8; lesson 418); Art Style Guide §6, line 192: the limit is decided, four, shown as *n/4*; Testing Reference, a section for the slice with the `py` protocols; System Map, the module and its three doors; BACKLOG, searched first for the names the slice touched; Lessons; roadmap; README. If L6.1 had run before the merge, the deploy's receipt goes into the runbook's LM10 line.
- **Commit:** `docs: close out Hero Points (Stage 5 slice HE)`

---

## 10. Open questions (each with what closes it)

- **OQ-HE1 — The cap of 4 and the price of a Heroic Ability** (Combat Design §7). The book's twenty Heroic Abilities cost 8, 10 or 12 Hero Points (pp. 218–219), and HP4 lets a character hold four. Nothing in HE decides it: the cap is a constant and the points a whole number. **Closes at:** the design of Heroic Abilities (roadmap, *Heroic Abilities / Hero Points*) — a higher cap, other prices, or a currency of their own.
- **OQ-HE2 — The line a point is earned with.** Its wording is chosen at HE-T2's STOPP 0 against the Tone Guide. **Closes at:** HE-T2. **Closed (Rev 2):** *The hard days behind you have left you steadier. Your Hero Points have grown.* — see HE-T2's *Shipped*.
- **OQ-HE3 — Is a game day the right rate?** A calibration constant (HP4, HE4 c), resting on an assumed length for a story. **Closes at:** the alpha's data, with the other rates (Combat Design §5).

---

## 11. Consequences worth reading twice

1. **No player can spend a Hero Point before ML,** and everyone who has played twelve hours by then holds four. HE4's rate is read with that in mind.
2. **A missing Attribute is two points, and zero is a stored 0.** `or START` is the plausible wrong reader, and HEM1 is there for it. Any later code that removes `hero_points` gives the character two.
3. **The wound tests run with *Glancing Blow* off.** A new test of a Major Wound written on another base class meets a body with two points and the switch on, and gets a Serious Wound.
4. **A trimmed blow may write no damage and still be a wound to answer for.** "Nothing was written" and "nothing happened" are different answers from `wounds.damage` after HE-T6.
5. **`wounds` now imports `hero_points`.** The other direction would be a cycle and is held out by a census.
6. **The switch does not save points for a Heroic Ability,** which the cap puts out of reach (OQ-HE1). It is there so that the spend is the player's choice.
7. **Death is not a way to Hero Points and not a cost in them** (HE5); the death contract's text is unchanged.
8. **When CL puts Hero Points in the panel, the tick must push `char` when a point lands** and `set_glancing`'s caller must push too; today nothing of the module is in a snapshot.
9. **HE's merge moves the runbook's §7** and is not a reason to hold L6.1 (HE8).
