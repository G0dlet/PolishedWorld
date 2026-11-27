# PolishedWorld — Healing Decomposition (Stage 5, slice 8b: HL)

> **Rev 1 · 2026-11-27** — first version, docs only, with `docs/PolishedWorld_Combat_Decomposition.md` Rev 28 and README Rev 105. Decomposes Stage 5's slice 8b, HL, from the thirteen locks of Combat Design Rev 17 (§4.4, HL1–HL13), which this document opens none of: the wound clocks counted in the server's runtime; natural healing twelve times faster and nothing credited for time away; `first_aid` for every character and `healing` learned with the healer's kit's recipe; a door in the wound module for one location, and the mark a won treatment leaves; an alarm that asks whether its location is being treated; `treat` and `operate`; and one kind in the activity log. Twelve code tasks, a merge and a close-out (HL-T1–HL-T14) on `feature/healing`. Anchors read at `main` `602c456`; HL11's first risk was run in the sandbox with a real stop, a real crash and a real start before anything was written (§4). **Found while writing, and decided by nobody yet:** `sinew` has no source, so the kit is not built from it; a creature's deadline is stored in wall-clock time as the wound clocks were, and HL11 does not name it (OQ-HL5); the first play that reaches First Aid is a body that has eaten again after starving, since its damage stays (§14, 2).
> **Canonical:** `docs/PolishedWorld_Healing_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Design source:** `docs/PolishedWorld_Combat_Design.md` §4.4 (WO2, WO4, WN3, WN4, WN9, WN10 with their Rev 17 notes; HL1–HL13 and *For the decomposition*), §4.2 (*The statue*), §4.3 (TR2, TR3, TR5), §5 (the rows for WN10 and HL3–HL10), §7 (OQ-WN1, OQ-WN3, OQ-WN4, OQ-HL1–OQ-HL4); `docs/PolishedWorld_Combat_Decomposition.md` §2 (row 8b); `docs/PolishedWorld_Wounds_Decomposition.md` §2, WN-T8–WN-T10, §11, §12; `docs/PolishedWorld_Survival_Loop_Decomposition.md` SL6, SL7; BACKLOG *Two-stage healing — field stabilisation vs. repair*, *Time away heals vs the statue as a snapshot*, *Others cannot tell a body lies senseless*, *First Aid for a body felled by fatigue*, *What a treatment costs is not in the log*, *Free Skill Points*, *Survival loop tuning*; *Legend* core pp. 50–51 and 60, read again for this document.
**Status:** **NOT STARTED** (Rev 1). HL1–HL13 are locked; HL-T1 is next.
**Feature branch:** `feature/healing` — one branch, one merge (ST2). Create it with `git switch -c feature/healing --no-track origin/main`.
**Rough scope:** twelve code tasks, a merge and a close-out; about fourteen to sixteen hours of code — three sessions at 5 h/week, or four. One new module (`world/treatment.py`) and one new command module (`commands/healing_commands.py`); changes in `world/wounds.py`, `world/healing.py`, `world/skill_base.py`, `world/chargen.py`, `world/character_migrations.py`, `world/recipes.py`, `world/prototypes.py`, `world/material_registry.py`, `world/seed_data.py`, `world/activity_log.py`, `world/activity_report.py`, `typeclasses/characters.py` and `commands/character_commands.py`. Two commands, two recipes, one scroll.
**Philosophy:** skynda långsamt — the clock before what leans on it; a number apart from a mechanism; the rule as a function before the command that calls it; a rule no play can reach yet is proven by tests and by `py`, and says so.
**Labels:** HL (locks, in the Combat Design §4.4), HL-T (tasks), HLM (mutations), OQ-HL (open questions: OQ-HL1–OQ-HL4 in the Combat Design §7, OQ-HL5–OQ-HL9 here). `git grep -n -I -E 'HL-T[0-9]|HLM[0-9]'` gave no line at `602c456`, before they were used. The components are HC1–HC7 (`git grep -n -I -E '\bHC[0-9]'` gave no line).

---

## 1. What the slice is

WN built the wound and left two doors with no caller, `wounds.stop_clock` and `wounds.revive`. HL1–HL13 say what a healer does. This slice builds it — before close combat (ML), so that the first blow lands in a world where a friend can do something about it.

**What a player meets after the merge:**

- **Wounds are carried into the next session.** Time away mends nothing (HL10). At the keyboard a body mends twelve times faster than before: a point an hour at Resilience 11–30.
- `treat <who> [<location>]`, with `tend`: one to three minutes and a bandage, or a piece of cloth at −20 %. On a hurt location it gives 1D3 Hit Points, once, until the location is whole again (HL5, HL7, HL8).
- A new skill on every sheet, `first_aid`, and a new recipe anyone can make, `bandage`.
- A scroll in the Old Temple for the healer's kit. Whoever knows that recipe has `healing` and can `operate` (HL3, HL9).
- `status` shows *tended* on a location that has had its treatment (HL12).

**What the slice builds that no play reaches before ML** (§14, 2): a clock stopped by a treatment; a body woken by one; an alarm that waits while its location is treated; surgery, since nothing in play maims.

**What the slice does not build:** disease, poison and impalement (HL1; OQ-HL1); the first aid kit (HL5; Foraging RP7); what a bystander sees of a wound (HL12; ML, with OQ-WN3); First Aid for a collapse (BACKLOG *First Aid for a body felled by fatigue*); a price in the log (BACKLOG *What a treatment costs is not in the log*); treating a creature (OQ-HL4); a cure for *severed* (HL9); a grade of difficulty of the project's own (HL6; OQ-HL2).

---

## 2. The locks, and four choices this document makes

The thirteen locks are the Combat Design's (§4.4, Rev 17), with their reasons, their numbers and what was rejected. One line each here, for the tasks to cite:

| Lock | In a line |
| --- | --- |
| HL1 | First Aid on four rows — unconsciousness, an injured location, a Serious Injury, a Major Injury — and surgery. No disease, poison or impalement. |
| HL2 | `first_aid` (INT + DEX) for every character, at creation and by backfill; `healing` (INT + POW) has no trait until it is learned. |
| HL3 | Knowing the healer's kit's recipe is having `healing`; a scroll in the temple; the trait is made the first time it is needed. |
| HL4 | A treatment under way holds death off: the alarm asks, and waits. Nothing is stored and no time is bought. A second healer on the same location is refused. |
| HL5 | 60, 120 or 180 real seconds; one `bandage`, or one `cloth` at −20 %, used up when the treatment is done, won or lost; −10 % on oneself; `physical_modifier()` whole. |
| HL6 | The test at +0 with no floor; a skill joins `improvable_skills` in the task that builds its test, and only a won test teaches. |
| HL7 | The location's level picks the row; only a won test marks the location; a fumble is 1 point through the writer; the Serious row gives the limb its use back; no Hit Points for a Starving or Dehydrated body. |
| HL8 | `treat <target> [<location>]` with `tend`; the most urgent location when none is named; only the healer is busy and everything is read again at the end; a statue and a creature refused; oneself allowed, a Major Wound too. |
| HL9 | `operate <target> [<location>]` removes *maimed*; not on oneself; nothing permanent; 150, 300 or 450 real seconds; the kit wears per operation. |
| HL10 | `healing.ROWS` divided by twelve; `_credit_time_away` and the stamp removed; a census holds the readers of `away_since` at none. |
| HL11 | Deadlines and a wound's unconsciousness are stored in `gametime.runtime()`. Closes OQ-WN4. |
| HL12 | `treat` says what it does and why it refuses; `status` shows *tended*; what a bystander sees is ML's. |
| HL13 | One activity-log kind, `treat`, once per treatment that reaches its end, with `counterpart`, `skill`, `row`, `result` and `material`. |

**Four choices are this document's, not the design's.** They say how the work is cut, and each can be changed at its task's STOPP 0 without touching a lock.

- **The treatments live in a module of their own, `world/treatment.py`.** `world/healing.py` calls itself *the one writer of health upward by natural healing* and stays that. The new module holds First Aid's and surgery's rules; it imports `wounds`, `skillcheck`, `skill_base` and `healing` (for `BLOCKING`, HL7), and nothing from `commands/` or `typeclasses/`.
- **The clock changes its unit alone, first.** HL-T1 changes what a stored deadline is counted in and nothing else; HL-T8 then gives the alarm its new reader. One commit for the unit and one for the logic, so that a clock that misbehaves after the merge has one commit to be read against.
- **The alarm learns of a treatment from the patient's `ndb`, and asks the timed-action slot whether it is still true.** The treatment's record lives in the *healer's* slot (`char.ndb.timed_action`), and the alarm holds the patient. So the task that starts a treatment writes a note on the patient — location, healer, marker — in `ndb`, through a function of the wound module, and the alarm's reader believes the note only while `timed_actions.is_current(healer, marker)` says so. `world/wounds.py` already imports `timed_actions` (it interrupts the slot at a knock-out), so nothing reaches upward; the note dies with the slot at a reload, which is HL4's *nothing new is stored*; and the same reader refuses the second healer. *Rejected:* a registry in `world/treatment.py` that the wound module asks (the lower module importing the higher, or a hook to register); a flag in `db` (HL4 rejected it: a pause whose treatment died at a reload).
- **The rule before the command.** HL-T9 builds First Aid as a function with the dice patched — the row, the test, what each outcome does — and HL-T10 builds the command around it: the search, the time, the material, the lines. HV's guard was cut the same way. A mutant in the rule is then killed by the rule's test and not by a comparison of strings (lesson 181).

---

## 3. Verified source anchors (read 2026-11-27, `main` at `602c456`; Evennia 6.1.0 from the wheel)

**The wound module, `world/wounds.py`:**

- `time.time()` stands on twelve lines. Seven are code: `knock_out` (`:618`), `unconscious` (`:661`), `_wake_due` (`:682`), `holds_body` (`:719`), `minutes_until` (`:724`), `start_clock` (`:752`) and `_clock_due` (`:773`). Two are comments (`:683`, `:774`) and three are docstrings that say what a stored value is (`:605`, `:723`, `:728`). `_left` (`:223`) and `report` (`:229`) read through `minutes_until`.
- `_clock_due` (`:762`) already sets itself again for what is left when it rings early (`:773–776`), and `_wake_due` (`:670`) does the same.
- `unconscious` (`:642`) wakes the body it is asked about, and answers `True` while any location's clock is due. `holds_body` (`:709`) only reads.
- `stop_clock` (`:783`) and `revive` (`:805`) have no caller in production. `stop_clock` turns a body with no player to stone once nothing holds it (`_stone_if_released`, `:701`).
- `heal` (`:538`) mends every hurt location at once and skips a clocked one; `room_to_heal` (`:524`).
- `start_clock` (`:735`) keeps an earlier deadline. `clock_seconds` (`:834`): 1260 s and 52.5 s at CON + POW 21.
- The states and their words: `DISABLED`, `MAIMED`, `SEVERED` (`:65–67`), `SEVERED_ENABLED = False` (`:72`), `STATE_WORDS` (`:219`).

**Natural healing:** `world/healing.py` — `ROWS` (`:28`), `FASTEST_HOURS` (`:35`), `BLOCKING` (`:42`), `interval_for` (`:45`), `is_blocked` (`:81`), `accrue` (`:86`). Its one caller in the tick is `world/survival_ticker.py:120`. Every row divided by twelve is a whole number of game seconds: 21600, 14400, 10800, 7200, 5400 and 3600.

**The character, `typeclasses/characters.py`:** the stamp `db.away_since` in `turn_to_stone` (`:581`, with its docstring `:570`); the call `self._credit_time_away()` in `at_post_puppet` (`:635`, and the docstring `:622`); `_credit_time_away` (`:666`). Outside `tests/` the word `away_since` stands only in this file. The four combat skills are made in a loop over `skill_base.COMBAT_SKILL_TRAITS` (`:536`). `improvable_skills = frozenset({"craft", "hunting"})` (`:1343`). `physical_modifier` (`:1043`). `knows_recipe` (`:1573`) and `learn_recipe` (`:1588`): a tag in a category and a `bool`, and nothing about skills. `refuse_if_collapsed` (`:2003`).

**Skills:** `world/chargen.py` — `SKILL_BASE_PAIRS` (`:67`), nine keys; `apply_allocation` (`:200`). `world/skill_base.py` — `SKILL_LADDERS` (six words a skill), `COMBAT_SKILL_TRAITS` (`:116`), `value_of` (`:153`), `trait_kwargs` (`:171`), `ensure_style` (`:209`), which takes a key of `combat_styles.STYLES` only. `world/character_migrations.py::backfill_combat_skills` (`:172`) is the form of a backfill: every `Character`, the missing traits only, a trained value never written over, a summary string.

**Timed actions, `world/timed_actions.py`:** one slot per character in `ndb` (`_Record`, `:66`); `start` (`:107`) refuses a busy body and one a wound has knocked out, and calls back as `callback(char, *args, marker)`; `is_current` (`:180`) does not empty the slot, but **does** empty it for a body with no player; `claim` (`:210`); `interrupt` (`:241`). `delay` there is not persistent (D7).

**Knowledge and goods:** `world/knowledge.py::_can_transmit` (`:192`) asks `knows_recipe` and the mastery count. A gated recipe is a class in `world/recipes.py` with `requires_knowledge = True` (*linen cuirass*, `:312–319`, is the form: `consumable_tags`, `output_prototypes`, `tool_tag`, `craft_duration`, `min_skill`). `world/seed_data.py::SCROLLS` (`:238`) is one row a scroll, and `tests/test_recipe_sources.py` fails a gated recipe with neither a grantor nor a row. `typeclasses/durable.py::apply_wear` (`:49`), and the class flag `mendable`. `world/material_registry.py`: `cloth` (`:255`) and `twine` (`:246`) are `EXISTS`; the tools `knife` (`:359`) and `needle` (`:368`) are `EXISTS`; **`sinew` (`:220`) is `DATA`, with the source *creature harvest (tendon) — add as a harvest part*, and no prototype** — nothing in the game yields it. `docs/PolishedWorld_SourceSink_Ledger.md` is rendered from the registry.

**The log:** `world/activity_log.py` — `KINDS` (`:60`), ten kinds; `RESERVED` (`ts`, `gt`, `kind`, `actor`, `room`); `record(kind, actor, **fields)` (`:94`). The pinned copy is `world/activity_report.py:44`.

**The census, `tests/test_client_state.py::TestPushCensus`:** `WOUND_ATTRIBUTES` (`:1094`), `DOOR_WRITES` (`:1095`), `NOT_PANEL` (`:1126`), `DOORS` (`:1180`): `damage`, `heal`, `restore_at_respawn`, `knock_out`, `start_clock`. `stop_clock`'s writes are in `NOT_PANEL` today.

**`status`:** `commands/character_commands.py:45` prints `wounds.report(char)`, a line per badly hurt location.

**Evennia 6.1.0:** `evennia/server/service.py` — `runtime` is read back from `ServerConfig` in the maintenance loop's first pass (`:88–93`), the loop is started with `now=True` (`:458`), saved every pass (`:103`) and last in the shutdown (`:588`); the persistent tasks are loaded after it (`:664`; the Combat Design's HL11 says `:662`, the comment above it). `evennia/scripts/taskhandler.py:626`: a task whose date has passed is set for 0 seconds. §4 has what a real server did.

**The book** (read again 2026-11-27): p. 50, *First Aid (DEX+INT)* — the same sum as HL2's INT + DEX; *Neither person can move*; the five rows of the table. p. 51: a critical halves the time, and on an injured location gives 1D3 + 1; a fumble is 1 point. p. 60: *Use of this skill will always require a healer's kit*; 1D3 × 10 minutes; a critical in surgery gives a Hit Point; a fumble leaves the location *permanently maimed* (HL9 departs). p. 114: the healer's kit, *bandages, mortar and pestle, poultices, barber's tools, basic surgical equipment*.

---

## 4. What was run (sandbox: Python 3.13.18, Evennia 6.1.0; a copy of a fresh clone of `602c456`, started as a real server)

HL11 carries a risk that was read and not run: an alarm restored at a start that read `gametime.runtime()` before the counter was restored would find every clock run out. A probe module outside the repository armed a persistent `delay` from `at_server_start`, with a deadline in `gametime.runtime()`, and its callback did what `_clock_due` does — read the counter, and set itself again for what was left.

| | What was done | What the alarm read |
| --- | --- | --- |
| **P1** | Armed at runtime 0.0 for 90.0. `evennia stop` at runtime 24.0. Down 112 s, so the task's wall-clock date had passed. `evennia start`. | It rang at once, **after** the start hook, at runtime 24.0: 66.0 left. It set itself again and rang at runtime 90.0. |
| **P2** | Armed at runtime 116.4 for 206.4. `pkill -9` on the server and the portal 75 s later, at runtime about 191.5. Down 67 s. `evennia start`. | It rang at runtime 176.5: 29.9 left — the counter's last save, 15 s before the kill. It rang again at runtime 206.4. |
| **P3** | `evennia reload` at runtime 116.4. | The start hook read 116.4 on both sides of the reload. |

- **The order holds:** an alarm restored at a start reads the restored counter. Nothing in HL11 needs a guard for it.
- **A clock stands still while the server is down,** and after a crash up to a minute is given back, in the wounded body's favour (P2: 15 s).
- **`_clock_due` needs no new branch for a start.** The branch that sets an early alarm again (`:773–776`) is the whole of it.
- **Found:** the first start of a new database starts, stops and starts again within three seconds (the initial setup), so a check on a fresh database sees two start hooks.
- **Not shown:** HL11's second risk — an old deadline in wall-clock time, read as runtime, never runs out. That is a question about a database, and HL-T1 carries it.

---

## 5. Dependency graph

```
HL-T1 ───────────────┐
HL-T2 ─> HL-T3       │
HL-T7 ───────────────┴─> HL-T8 ─┐
HL-T4 ──────────────────────────┴─> HL-T9 ─┐
HL-T5 ─────────────────────────────────────┴─> HL-T10 ─> HL-T11 ─┐
HL-T6 ───────────────────────────────────────────────────────────┴─> HL-T12 ─> HL-T13 ─> HL-T14
```

HL-T1 is first because HL-T8 changes the same alarm. HL-T2 and HL-T3 are a number and a mechanism, apart, and touch nothing the rest reads. HL-T4, HL-T5 and HL-T6 are the skill and the goods, each needed by one later task and by nothing else. HL-T7 and HL-T8 are the wound module's own work: what a treatment may do to a body, and what the alarm asks. HL-T9 is the rule, HL-T10 the command, HL-T11 what is shown and written down. `operate` is last in the code: it uses everything `treat` built and changes nothing `treat` reads.

**The order the tasks are taken in is their number.** The mutants are given out here in blocks, one per task, so no number is taken twice (lesson 498): HLM1–HLM4, HLM5–HLM7, HLM8–HLM10, HLM11–HLM13, HLM14–HLM16, HLM17–HLM20, HLM21–HLM25, HLM26–HLM29, HLM30–HLM37, HLM38–HLM43, HLM44–HLM46, HLM47–HLM52.

**Between HL-T2 and HL-T3 the branch heals twelve times faster and still credits time away** — a week away is a body made whole at the login. Nothing is merged between them.

**The names below are proposals** — the functions, the Attributes, the constants, the lines' own wording. Each is taken at its task's STOPP 0, the wording against the Tone Guide. **Each task's *In-game check* says what is done and what is seen; the whole line is written and tried through `CmdPy` in the sandbox at the task** (lessons 502 and 509).

---

## 6. Component HC1 — The clock

### Task HL-T1 — A deadline is counted in the server's runtime
- **Goal:** A wound clock's deadline and the end of a wound's unconsciousness are stored in `gametime.runtime()`, so neither moves while the server is down.
- **Dependencies:** none.
- **Approach:** in `world/wounds.py`, one private reader of *now* — the server's runtime — in place of `time.time()` on the seven lines of code that read it (§3), and the three docstrings and two comments that name the unit. `delay` keeps its seconds: runtime and real time pass together while the server is up. The alarms' early-ring branches stay as they are (§4). **How the tests set the clock is a choice at STOPP 0:** they patch `world.wounds.time` today (Testing Reference §27.2), and they will patch either the module's one reader or `gametime` in it; count the patch sites before the lock — `git grep -c 'world.wounds.time' -- tests` gives five modules at `602c456`: `test_wound_clocks`, `test_wound_unconscious`, `test_wound_report`, `test_glancing_blow` and `test_hero_points` (lesson 183). **Before the code is reloaded on a database, one `py` line lists every body in it with `wound_clocks` or `wound_unconscious`** — every `Character` in the database, not the ones in a room (lesson 507) — and what it finds is removed with `attributes.remove`: a wall-clock deadline is a thousand times a runtime and would never run out (HL11, risk 2). The line is written and tried in this task, run by Adam at home before the reload, and goes into the Alpha Runbook's §7 at HL-T13.
- **Testing:** the existing clock and unconsciousness tests, on the new reader. New: a deadline set at runtime R with the counter then held still — a stop — is not due however far the wall clock moves; the stored value is of the runtime's size and not the wall clock's (a deadline stored now is below 10⁹ on any database younger than thirty years); `holds_body`, `minutes_until` and `report` read the same clock, so a body is not shown *bleeding out, 3 min* and held for another unit's reason. **An old value, both ways** (lesson candidate 13 of the handoff): a wall-clock deadline read by the new code is not due and holds the body — the test says so, as the reason the listing line exists.
- **Red before green:** the stop test, against today's module with only the wall clock moved: the clock is due.
- **Mutations (HLM1–HLM4):** `start_clock` storing wall-clock time; `_clock_due` comparing with wall-clock time; `knock_out` storing wall-clock time; `holds_body` reading wall-clock time.
- **In-game check** *(by `py`, on a character made for it — it dies)*: the listing line first, on the home database. Then a limb's Major Wound by `py` (Testing Reference §27.3), the stored deadline printed beside `gametime.runtime()`; `evennia stop`, two minutes, `evennia start`; the deadline is the same number and the time left in `status` is what it was at the stop; `wounds.stop_clock` by `py` ends it.
- **Commit:** `feat(wounds): deadlines counted in the server's runtime (HL11)`

---

## 7. Component HC2 — Natural healing

### Task HL-T2 — The table, twelve times faster
- **Goal:** Natural healing reads the book's table through one calibration constant, twelve.
- **Dependencies:** none.
- **Approach:** in `world/healing.py`, a constant beside `ROWS` — the table stays as printed (HL10) — and `interval_for` divides by it, the fastest row too. The module's docstring says what the constant is and that it is a guess (BACKLOG *Survival loop tuning*). Nothing else moves: the tick, the counter and `accrue`'s three steps.
- **Testing:** `tests/test_healing.py`: each of the six rows gives 21600, 14400, 10800, 7200, 5400 and 3600 game seconds; the fastest row is longer than one survival tick (2400 game seconds), which a test holds so that nobody turns the constant up past the tick without seeing it; the tests that typed an interval read it from `interval_for` (Testing Reference §27.2: a maximum is read, never typed).
- **Red before green:** the row test, against today's `interval_for`.
- **Mutations (HLM5–HLM7):** the constant 1; multiplied in place of divided; the fastest row not divided.
- **In-game check:** on a hurt body that is neither Starving nor Dehydrated, `py` prints `healing.interval_for(healing.resilience(self))` and `self.db.heal_progress`; after one tick the counter has grown by the tick's game seconds; at Resilience 11–30 a point lands within an hour at the keyboard.
- **Commit:** `feat(healing): the natural healing table read twelve times faster (HL10)`

### Task HL-T3 — Time away is credited to nothing
- **Goal:** A statue heals nothing: no stamp is written, and nothing is credited at the login.
- **Dependencies:** HL-T2.
- **Approach:** removed from `typeclasses/characters.py`: `_credit_time_away` (`:666`), its call in `at_post_puppet` (`:635`), the stamp in `turn_to_stone` (`:581`), and the passages of the two docstrings that describe them (`:570`, `:622`). `turn_to_stone` keeps its line and the room's push. Stamps already stored are left where they are, unread; `db.heal_progress` is not touched, so it is frozen with the body. **A census** (WN2b's form, walking the AST of the five production directories as HV-T1's does): `away_since` is named nowhere outside `tests/`. **Read at STOPP 0:** `world/help_entries.py` and the death contract's texts for a sentence that promises healing while away; `healing.is_blocked`'s other callers, since the stamp was one.
- **Testing:** a body hurt, logged out and logged in after ten game days has the damage and the `heal_progress` it left with, and is told nothing; a body that logs out writes no `away_since`; a stamp already stored is still there after a login and nothing was credited for it. The S2.2 tests in `tests/test_healing.py` and the nine lines in `tests/test_wound_clocks.py` that name the stamp are rewritten or removed, each read first for what else it held.
- **Red before green:** the ten-days test, against today's code.
- **Mutations (HLM8–HLM10):** the credit left in; the stamp still written; the login zeroing `heal_progress`.
- **In-game check:** a hurt character, `status` read, `quit`, an hour later a login: `status` is the same and no healing line came. `py self.msg(str(self.db.away_since))` on a character made after the merge prints `None`.
- **Commit:** `feat(healing): time away heals nothing; the statue is a snapshot (HL10)`

---

## 8. Component HC3 — The skills and the goods

### Task HL-T4 — `first_aid`
- **Goal:** Every character has `first_aid` at INT + DEX: a new one from creation, an old one by a backfill.
- **Dependencies:** none.
- **Approach:** `chargen.SKILL_BASE_PAIRS` gains `"first_aid": ("int", "dex")`, `skill_base.SKILL_LADDERS` its six words, the creation loop its trait (`typeclasses/characters.py:536`), and `world/character_migrations.py` a backfill in `backfill_combat_skills`' form — **in one commit**, since `apply_allocation` refuses a character with a base pair and no trait (HL2). Whether `first_aid` joins `COMBAT_SKILL_TRAITS` under a wider name or stands in a table of its own is a choice at STOPP 0; so are the six words (Tone Guide §5). It is **not** added to `improvable_skills` here: the label and the call move together (HL6), in HL-T9. **Read at STOPP 0:** which keys of `SKILL_BASE_PAIRS` character creation lets points be spent on, and what a profession's bonus reads (BD9 kept the four combat skills out of the player's hands); `sheet` and the `progress` command, for a list of skills typed by hand.
- **Testing:** a new character has the trait at INT + DEX; the backfill gives it to a character without it, leaves a trained value as it is, and changes nothing on a second run; `apply_allocation` passes for a character made before and backfilled; `skill_base.value_of(char, "first_aid")` answers the base for a character the backfill missed. The censuses that count skills (the ladder table, `TestImprovableSkillsSet`) are read first for a number that was typed.
- **Red before green:** `apply_allocation` on a new character, against the pair added alone: it refuses.
- **Mutations (HLM11–HLM13):** the pair INT + POW; the backfill writing over a trained value; creation skipping the trait.
- **In-game check:** `sheet` on a new character shows the skill; on the home database, `py from world.character_migrations import backfill_first_aid; self.msg(backfill_first_aid())` names the characters it changed, and a second run changes none.
- **Commit:** `feat(skills): first_aid, a Common skill every character has (HL2)`

### Task HL-T5 — The bandage
- **Goal:** Anyone can make bandages from cloth.
- **Dependencies:** none.
- **Approach:** an ungated recipe, `bandage`, on `cloth` (HL5), with its prototype, its row in `world/material_registry.py` — source: the recipe; sink: `treat`, and the healer's kit — and whatever census holds a recipe to its registry row. **How many bandages one cloth gives is a choice at STOPP 0** (OQ-HL8): one makes the bandage a tax of craft time on the −20 %; two or more make a crafter's cloth go further than a torn tunic's, which is the reason to make them. So are the tool (none, or the knife as an optional tool, as the waterskin has it), the time and the floor of skill. The Source/Sink ledger is rendered from the registry and follows at HL-T14.
- **Testing:** the recipe's tests in the form of its neighbours' (found with `git grep -l '"cloth"' -- tests`, and read first); `tests/test_recipe_sources.py` passes with the recipe ungated; the registry's census.
- **Red before green:** the registry's census, against the recipe alone.
- **Mutations (HLM14–HLM16):** the recipe gated; the wrong count out; no cloth used up.
- **In-game check:** `craft bandage` with a cloth carried: the cloth is gone and the bandages are in `inventory`.
- **Commit:** `feat(crafting): the bandage, from cloth (HL5)`

### Task HL-T6 — The healer's kit, its scroll, and `healing`
- **Goal:** A character who has learned the healer's kit's recipe has `healing`; the kit is a thing that wears.
- **Dependencies:** HL-T5.
- **Approach:** a gated recipe for the healer's kit in *linen cuirass*'s form, its prototype a durable item, a row in `seed_data.SCROLLS` for the temple (GR24's pattern), and its registry row. **The recipe is a choice at STOPP 0** (OQ-HL8): from `bandage`, `needle` and `twine`, with the knife as the tool — **not `sinew`, which nothing yields** (§3) — and the book's kit as the guide (p. 114). So are how much one operation wears it (HL-T12 does the wearing) and whether it is `mendable`: a kit that can be repaired has no sink. **Read at STOPP 0:** how a recipe's name is typed and stored — *healer's kit* has an apostrophe, and the name is a tag key and what `craft`, `learn` and `teach` parse; and the scroll's placement ledger (`seed.scrolls_placed`), for what a database made before the merge needs to get the new scroll. **`healing`:** its pair, INT + POW, stands in `world/skill_base.py` and **not** in `chargen.SKILL_BASE_PAIRS` (HL2), with its ladder; one reader answers whether a character has the skill — it knows the recipe — and one function makes the trait at its base if it is missing, in `ensure_style`'s form, refusing a character who does not know the recipe. **Where that function is called is a choice at STOPP 0** (OQ-HL7): `learn_recipe` only adds a tag and knows nothing of skills, so the leaning is the first time the skill is needed — HL-T12's test, and whatever shows a sheet.
- **Testing:** the recipe is gated and `tests/test_recipe_sources.py` finds its scroll; the seed places the scroll once; a character who knows the recipe gets the trait at INT + POW, and a second call returns the same trait with a trained value untouched; one who does not know it gets none, and nothing is written; `apply_allocation` still passes (the pair is not in `SKILL_BASE_PAIRS`).
- **Red before green:** `tests/test_recipe_sources.py`, against the recipe with no scroll row.
- **Mutations (HLM17–HLM20):** the trait made for a character who does not know the recipe; the pair INT + DEX; the recipe ungated; the pair added to `SKILL_BASE_PAIRS`.
- **In-game check:** in the Old Temple after a `seed_world()`, the scroll lies there; `learn` it; `craft` the kit; `py` shows the recipe known and the trait made at INT + POW.
- **Commit:** `feat(healing): the healer's kit, its scroll, and the healing skill learned with it (HL3)`

---

## 9. Component HC4 — What a treatment may do to a body

### Task HL-T7 — A door for one location, and the mark
- **Goal:** The wound module can mend one location, give a limb its use back, and remember that a location has had its First Aid.
- **Dependencies:** none.
- **Approach:** in `world/wounds.py`. **A door for one location** (HL7): so many points to one named location, never past unhurt, returning what landed; a location whose clock runs is refused, as `heal` skips it. *disabled* goes when the location is above 0, as in `heal` — and a second door, or an argument, takes *disabled* from a limb whatever its Hit Points, which is the Serious row (HL7, 4; the two rules meet here, and the door says so). **The mark:** a third Attribute beside WN1's two, a set of locations, with a writer and a reader; emptied for a location when it is whole — in `heal`, in the new door — and for all at `restore_at_respawn`. `tests/test_client_state.py::TestPushCensus` learns all of it: the Attribute in `WOUND_ATTRIBUTES`, the new doors in `DOORS`. **Read at STOPP 0:** how the census holds a door that has no production caller until HL-T9 — `stop_clock`'s writes stand in `NOT_PANEL` today because nothing in the snapshot moves when a clock stops, and the new door moves `body_damage`, which the panel shows.
- **Testing:** three points to an arm with two of damage land two; another location's damage is untouched; a clocked location is refused and nothing is written; a limb at 0 with *disabled* loses the state through the Serious door and keeps its damage; *maimed* is never taken by either door; a marked location that natural healing makes whole loses its mark, and one still hurt keeps it; a death empties the marks and keeps *maimed* (WN9); the census's own test that `WOUND_ATTRIBUTES` is what the module writes.
- **Red before green:** the census's test, against the new Attribute unlisted.
- **Mutations (HLM21–HLM25):** the door mending every location; a location mended past unhurt; the mark kept on a whole location; the mark kept through a death; the Serious door taking *maimed*.
- **In-game check** *(by `py`)*: two locations hurt through the writer, the door called on one, `self.db.body_damage` printed before and after; the mark set and read; `status` unchanged until HL-T11.
- **Commit:** `feat(wounds): a door for one location, and the mark a treatment leaves (HL7)`

### Task HL-T8 — The alarm asks whether its location is being treated
- **Goal:** A clock that falls due while its location is being treated waits and asks again; a second healer on that location is refused.
- **Dependencies:** HL-T1, HL-T7.
- **Approach:** §2's third choice. In `world/wounds.py`: a function that notes a treatment on the patient's `ndb` — location, healer, marker — and answers `False` when a live one is already noted for that location; a reader that answers whether a location is being treated now, believing a note only while `timed_actions.is_current(healer, marker)` is true; and `_clock_due`, which, when the deadline has passed and the reader says yes, sets itself again a short while on — a constant, a few seconds — and returns. Nothing is stored in `db`. A treatment that ends without stopping the clock leaves a note that is no longer true, and the next ring kills (HL4: *lets the body die then*). `unconscious` already keeps a body out while a clock is due (`:642`), so nothing wakes in between. **`is_current` empties the slot of a healer with no player** (§3): the reader may be the first to notice that the healer has gone, which is right, and the docstring says it writes that much.
- **Testing:** `world.wounds.delay` patched, the alarm fired by hand (Testing Reference §27.2). A due clock with its location treated does not kill and sets one new alarm; fired again with the treatment over, it kills once. **Treating the arm does not hold the head's clock.** A note whose marker is stale is not believed. A note lost — `ndb` emptied, a reload — leaves an alarm that kills as it would have. A second note for a location with a live one is refused, and accepted once the first is over. A healer who logs out mid-treatment protects no longer.
- **Red before green:** the due clock with its location treated, against today's `_clock_due`: it kills.
- **Mutations (HLM26–HLM29):** a treatment of any location holding every clock; a stale marker believed; the alarm not set again, so the body never dies; the second healer accepted.
- **In-game check** *(by `py`, on a character made for it — it dies)*: a head's Major Wound survived, and within its 50 seconds a second character's timed action noted as its treatment, by `py`; the deadline passes and the body lives; the action is interrupted, and within the constant the body dies.
- **Commit:** `feat(wounds): a treatment under way holds the clock's death off (HL4)`

---

## 10. Component HC5 — `treat`

### Task HL-T9 — First Aid's rule
- **Goal:** One function carries out a First Aid test on a location and does what its row says.
- **Dependencies:** HL-T4, HL-T7, HL-T8.
- **Approach:** a new module, `world/treatment.py`. **The row** is read from the location (HL7, 1): a Major Wound with a clock running; a Serious Wound; an injured location above 0; and, for a body with nothing else to treat, the unconsciousness. **What refuses,** each with a reason the caller turns into a line (HL12): unhurt; marked; *maimed* with no clock, which is surgery's; the Hit Point rows for a Starving or Dehydrated body, read from `healing.BLOCKING` (HL7, 5). **The test:** `skillcheck.skill_check(skill_base.value_of(healer, "first_aid"), modifier)`, the modifier being `physical_modifier()` whole, −10 on oneself and −20 for cloth (HL5, HL6). **What it does:** won on an injured location, 1D3 points through HL-T7's door, 1D3 + 1 on a critical; on a Serious Wound, one point, the limb's use, and `wounds.revive`; on a Major Wound, `wounds.stop_clock` and no points; on the unconsciousness, `wounds.revive`. Only a won test marks the location. A fumble is one point to the treated location through `Character.apply_health_damage`, with no `made` (HL7, 3; OQ-WN1). A won test calls `attempt_skill_improvement("first_aid", …)`, and `improvable_skills` gains the key in this commit (HL6). The function pushes `char` for the patient, as each door's one caller must, and `DOOR_WRITES` names it for `stop_clock`, `revive` and the new doors. **The most urgent location** (HL8, 1) is a function here too: the clock with the least time left, then a Serious Wound, then the most damage. **Two questions the lock leaves, for STOPP 0:** whether the Serious row gives a limb its use back on a Starving body, where it gives no point (the leaning: yes — HL7 withholds Hit Points and nothing else); and what a won Major row does to a vital location's unconsciousness, which WN-T10 tied to the clock that has now stopped. The roll census (`ROLL_SITES`) gains the module.
- **Testing:** `world.skillcheck.randint` and the module's own die patched. Each row, at each of the four outcomes. The modifier: on oneself, with cloth, with both, on an overloaded and Wearied healer. A lost test marks nothing and may be made again; a won one marks, and the next is refused. The fumble's point lands on the treated location and nowhere else, and a fumble that brings a location to a Serious or Major Wound does what the writer does for a source with no roll (Wounds WN-T8, choice B). A Starving body: no points on either Hit Point row, the clock still stopped, the body still woken. The urgency: two clocks, a clock and a Serious Wound, two injured locations. `improvable_skills` and its census; a lost test teaches nothing.
- **Red before green:** the Major row, against a function that mends: the location must have the damage it had, and no clock.
- **Mutations (HLM30–HLM37):** a lost test marking the location; the critical giving 1D3; the Major row giving points; the modifier 0; −10 given to every patient; a Starving body mended; the fumble's point on another location; a lost test teaching.
- **In-game check** *(by `py`)*: on a body with an arm hurt, the function called with a bandage's modifier until it wins; `self.db.body_damage` before and after, and the mark.
- **Commit:** `feat(treatment): First Aid's test and its four rows (HL1, HL5, HL6, HL7)`

### Task HL-T10 — `treat`
- **Goal:** A player treats another, or herself, with one command that takes the book's time and a bandage.
- **Dependencies:** HL-T5, HL-T9.
- **Approach:** `commands/healing_commands.py`, `CmdTreat`: key `treat`, alias `tend`, in the character's cmdset, with its help. The target is found by `caller.search` — NM's search, TR5's first sentence, which HV7 said HL owed a command. The location is the player's word for it (WN-T11's names) or the most urgent (HL-T9). **Refused, a line apiece** (HL12): a statue; a creature; a body with nothing to treat; and each of HL-T9's reasons. **The material** is found before the time starts — a `bandage` first, else a `cloth`, else the command is refused — and looked for again when it ends. **The time:** 60, 120 or 180 seconds (HL5), rolled at the start, through `timed_actions.start`, with HL-T8's note set on the patient; only the healer is busy (HL8, 2). The healer, the patient and the room each get a line when it begins, through `$You()` with role keys (TR3); the healer's names the location and its condition in words, with no figure (HL12). **When the time is out** everything is read again: both in the room, the patient alive, the location's level — and the row is the row that applies then (TR2). A patient who has gone ends it with the time lost and nothing used. Otherwise the material is used up, the rule is called, and each outcome has its lines. **The book's critical halves the time** (p. 51), and the test is made when the time is out: whether that is built, and how, is OQ-HL6, for this task's STOPP 0 — the leaning is that it is not built and gets a row in the Combat Design §5, since rolling at the start would fix the row before TR2's second read.
- **Testing:** `EvenniaCommandTest`, the second character with a real session (`SecondSessionMixin`, as HV-T4 needed), `world.timed_actions.delay` patched and the callback fired by hand. Each refusal and its line. With a bandage and a cloth carried the bandage is used; with a cloth alone, the cloth, and the modifier is −20; with neither, refused and nothing started. A step by the healer ends it and nothing is used; a patient who walks out ends it and nothing is used; a patient who dies in between ends it. A location that has become a Serious Wound when the time is out gets the Serious row. Oneself. `tend`. The begin lines hold no figure and no key of a stranger (NM). A second healer on the same location is refused, and on another location is not.
- **Red before green:** the walked-out patient, against a callback that does not read the room again: the bandage is used.
- **Mutations (HLM38–HLM43):** the material used up at the start; the cloth taken before the bandage; the row read at the start and kept; the patient's slot occupied; a statue treated; the material not looked for again at the end.
- **In-game check:** two characters at home, one with an arm hurt by `py`: `treat <the other>` begins with its three lines, ends after its time, and `status` and `inventory` show the result; a second `treat` on the same arm is refused with its reason; `treat me` at −10.
- **Commit:** `feat(treatment): treat, with tend (HL5, HL8, HL12)`

### Task HL-T11 — *tended* in `status`, and the log
- **Goal:** The patient sees which locations have had their treatment, and every treatment that reaches its end is one line in the activity log.
- **Dependencies:** HL-T10.
- **Approach:** `wounds.report` (`:229`) shows *tended* on a marked location's line — and **a marked location with only a Minor Wound has no line today**, so whether it gets one is a choice at STOPP 0 (without it, the injured row's refusal has nothing in `status` to explain it). `activity_log.KINDS` and its pinned copy in `world/activity_report.py` gain `treat`; `treat` writes one line when the time is out, with `counterpart` as a pair (the healer's own for oneself), `skill`, `row`, `result` and `material` (HL13). A treatment broken off writes nothing. The field names are held against `RESERVED`. **Read at STOPP 0:** every view of the report a new kind appears in — by kind, by month, the census — so that the line's effect is predicted in each.
- **Testing:** `status` for a marked location, and for one whose mark has gone; a won, a lost, a critical and a fumbled treatment each write one line with the five fields; a treatment the healer walked away from writes none; `tests/test_activity_report.py` holds the two `KINDS` together.
- **Red before green:** the report's test of the two `KINDS`, against the kind added to one.
- **Mutations (HLM44–HLM46):** a line written for a treatment broken off; `row` taken from the start and not from the end; `counterpart` the healer when another was treated.
- **In-game check:** after HL-T10's check, `status` on the patient shows the word, and `python -m world.activity_report server/logs/activity.jsonl` counts the `treat` lines — read before and after, never as an absolute count.
- **Commit:** `feat(treatment): tended in status, and treat in the activity log (HL12, HL13)`

---

## 11. Component HC6 — `operate`

### Task HL-T12 — Surgery
- **Goal:** A character who knows the healer's kit's recipe and carries a kit takes *maimed* from another's location.
- **Dependencies:** HL-T6, HL-T11.
- **Approach:** in `world/treatment.py`, surgery's rule, and in `commands/healing_commands.py`, `CmdOperate`, key `operate`. **It asks** (HL9, 2 and 3): a location that is *maimed* with no clock running; a healer who knows the recipe; a kit carried that is not broken; and that the patient is not the healer. **The time** is 150, 300 or 450 real seconds (HL9, 5), through the same slot. **When it is out,** everything is read again as `treat` does; the kit is worn once, won or lost (`apply_wear`, by HL-T6's amount); the test is `healing` at +0 with `physical_modifier()`, the trait made here if it is missing (OQ-HL7). Won, *maimed* is removed — a door of the wound module, which the census learns — and a critical gives one point through HL-T7's door if the location is hurt. Lost, nothing more. A fumble is one point through the writer, and nothing is permanent (HL9, 4). A won test teaches, and `improvable_skills` gains `healing`. The log's line is `treat`'s, with `skill` `healing` (HL13). `SEVERED_ENABLED` is not touched, and a *severed* location is refused. **This task may be two** — the rule, then the command — and its STOPP 0 says which.
- **Testing:** the rule with the dice patched: each of the four outcomes; *maimed* gone and the damage as it was; the critical's point; the kit's condition after a won and after a lost operation, and a broken kit refused. The command: each refusal and its line — not *maimed*, a clock running, the recipe not known, no kit, oneself, a statue, a creature, *severed*; the time; the read at the end. After a won operation the hand holds again (`world/gear.py`'s reader of the state, GR22). A character who knows the recipe and has never operated has the trait afterwards, at INT + POW.
- **Red before green:** the fumble, against the book's rule written out — *maimed* for good — which the test refuses: the state is as it was and one point has landed.
- **Mutations (HLM47–HLM52):** oneself allowed; a lost test removing *maimed*; the kit not worn on a lost test; a running clock allowed; the recipe not asked for; the time in real minutes.
- **In-game check** *(by `py` for the wound — nothing in play maims before ML)*: a character's arm maimed by `py` and its clock stopped; a second, who has learned the recipe and made a kit, types `operate`; the lines, the time, and afterwards `status`, the kit's condition, and `wield` in that hand.
- **Commit:** `feat(treatment): operate — surgery takes maimed away (HL9)`

---

## 12. Component HC7 — Close-out

### Task HL-T13 — Protocol, suite and merge
- **Goal:** The slice is run whole in play, the whole suite is green, and `feature/healing` is merged.
- **Dependencies:** HL-T12.
- **Approach:** one protocol in play with two characters, from a hurt arm to a bandage to *tended*, and by `py` from a Major Wound to a stopped clock to an operation; the whole suite at home with `ForkTestRunner` and `--parallel auto`, the count taken from the runner (Testing Reference §27.1); `node --test tests/js/*.js`. **The Alpha Runbook's §7 gains, in the order they are run on a database made before the merge:** the listing of bodies with a clock or a wound's unconsciousness, **before** the reload (HL-T1); `backfill_first_aid()` (HL-T4); what places the new scroll (HL-T6). §4, *Scrolls*, gains the line for a healer's kit scroll whose reader has left before five kits (HL3). The merge is a merge commit by PR, its tree predicted with `git merge-tree`. Whether it is tagged is OQ-HL9.
- **Commit:** the merge, and `docs: the runbook's lines for healing` on `main`.

### Task HL-T14 — Documentation
- **Goal:** The documents say what was built.
- **Approach:** two commits, as HV-T7 and CE-T8 were. **(a) The designs:** this document's text follows what was built, each departure beside the words it changes; the Combat Design (the locks' notes, §5's rows — the critical's time if OQ-HL6 falls that way — and §7); the slice map. **(b) The references and registers:** the System Map (*Damage chokepoint*: the doors that have their callers; *Known gaps* loses `stop_clock` and `revive`; the diagram, parsed with Mermaid 11 under jsdom if it changes, lesson 487); the Testing Reference (a section for healing); the Evennia Reference (`runtime`, when it is saved, and the order at a start, with §4's three runs); the Source/Sink ledger, rendered; BACKLOG (the entries this closes and annotates, and the Foraging note's `first_aid` and `treat` on one pool, RP9 and RP-L3); the roadmap; the lessons, from 522, with the thirteen candidates the handoffs carry.

---

## 13. Open questions (each with what closes it)

OQ-HL1–OQ-HL4 are the design's and stand in the Combat Design §7: cures for disease and poison (the Foraging decomposition); whether +0 is too hard without the book's points (the alpha's data, or *Free Skill Points*); what a Major Wound forbids its bearer (ML's design); treating an animal (the first slice with an animal worth saving).

- **OQ-HL5 — A creature's deadline is stored in wall-clock time.** `world/creature_wounds.py` stores a hurt creature's `due` as a `time.time()` (`:361`, read at `:458`; CE6 took the wound clocks' pattern), and HL11 names the character's clocks alone. After HL-T1 a stop of the server still runs a creature's clock on, and no longer a character's. No play starts either before ML. **Closes at:** HL-T1's STOPP 0 (Adam): the same change there in the same task, a task of its own, or ML's — with a BACKLOG entry if it waits.
- **OQ-HL6 — Does a critical success halve First Aid's time (p. 51)?** The test is made when the time is out (HL5), and the row is read then (HL8). **Closes at:** HL-T10's STOPP 0 (Adam). If it is not built, the Combat Design §5 gains a row.
- **OQ-HL7 — Where the `healing` trait is made:** at the learning, or the first time the skill is needed (HL3 says the second and leaves *where*). **Closes at:** HL-T6's STOPP 0.
- **OQ-HL8 — The goods' numbers:** how many bandages a cloth gives; the kit's recipe, with no `sinew`; how many operations a kit lasts; whether a kit can be repaired. **Closes at:** HL-T5's and HL-T6's STOPP 0, each against the Source/Sink ledger.
- **OQ-HL9 — Is a tag cut at the merge?** As OQ-WN7 was asked. BACKLOG *When the closed alpha opens* is not decided. **Closes at:** HL-T13.

---

## 14. Consequences worth reading twice

1. **The first thing a tester meets is a wound that is still there next week** (HL10). Nothing has to have gone wrong for them to meet it: a body that starved on Tuesday is as hurt on Saturday. At home, `adam` was critically hurt and thirsty when this was written, and after the merge stays so until he drinks and is treated or plays the hours.
2. **One row of First Aid is reached in play from the day of the merge; the rest wait for ML.** Starvation's damage stays when the body has eaten, so an injured location above 0 is real, and `treat` on it is the first healing between players. A Serious Wound from starvation is a location at 0 and can be reached too. A clock, a wound's unconsciousness and *maimed* are not started by any play before ML: HL-T1, HL-T8, the Major row and all of `operate` are proven by tests and by `py`, and a check run by `py` proves the function, not that a player can get there (Wounds §12, 1).
3. **A stored deadline from before HL-T1 never runs out** (HL11, risk 2). The listing line is run on every database before the code is reloaded on it — the home database in HL-T1, the work database and the alpha's by the runbook.
4. **The checks of HL-T1, HL-T8 and HL-T12 maim and kill.** They are run on a character made for it and never on the alpha server. From HL-T12 *maimed* has a cure in play, and the Wounds decomposition's note that it is removed by hand (§12, 2) is retired at HL-T14.
5. **Typing `treat` at a stranger tells what hurts them** (HL12). It is read as an examination until ML shows a wound to those who look.
6. **A fumble is the one way a player's act hurts another under PvE** (HL8): about two in a hundred a bandage, on a patient who chose to stand still. The guard is not asked.
7. **At 21 % the price of a treatment is bandages and minutes.** A lost test uses its bandage and may be made again (HL7): on average nearly five bandages and ten minutes for one won treatment, and at 11 % on oneself, nine. OQ-HL2 is answered from the log's lost tests, which is why HL13 writes them. The figures are for the skill a new character has, not an average that assumes success (lesson candidate 7 of the handoff).
8. **The healer's kit's scroll is used up by its first reader.** Until she has made five kits nobody else can learn it, and if she leaves, staff place another (HL3; the runbook's §4).
9. **After a crash the clocks give back up to a minute** (§4, P2). After a clean stop they give back nothing.
10. **Between HL-T2 and HL-T3 the branch is wrong in the player's favour** (§5), and between HL-T4 and HL-T9 a character has a skill nothing rolls. Nothing is merged before HL-T13.
11. **A creature's clock still runs while the server is down** (OQ-HL5), unless HL-T1's STOPP 0 takes it.
