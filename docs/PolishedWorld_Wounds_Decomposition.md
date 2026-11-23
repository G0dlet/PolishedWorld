# PolishedWorld — Wounds Decomposition (Stage 5, slice 4: WN)

> **Rev 3 · 2026-11-23** — docs only, on `main`, with README Rev 70 and BACKLOG Rev 119: *Shipped* lines for WN-T4, WN-T5, WN-T7 and WN-T6, in that order on `feature/wounds` (`db9420b`, `59369f9`, `32b0c25`, `8e3beb7`; tree `c423520`); the status line; three in-game checks corrected (WN-T5 stored a `None`, WN-T6 used `py` as a player, WN-T7 named the head's margin where the arm's is the worst). What the tasks found is at each task: P2 and P1 failed more tests than §4 counted, and each extra one was read; the pushes stay with the doors' callers, and the census now reads the stored damage's writes; a CON + SIZ 20 body has a head of 4; `is_dead` takes no source yet and WN-T8 must change it. No lock changes.
> **Rev 2 · 2026-11-23** — docs only, on `main`, with README Rev 69: *Shipped* lines for WN-T1, WN-T2 and WN-T3, which are on `feature/wounds` (`cd603c9`, `1442ce9`, `246d36f`; tree `f4a1a92`); the status line. Four things the tasks found are recorded at their tasks: WN-T1's spy is the only test that tells a sum from a call per condition; WN-T2 added WNM7b and WNM8b and made `clock_seconds` refuse a key that is no location; WN-T3's census counts a local named `traits`, does not count `chargen_menu`'s *Feeds health* (a word, not a read), and removed `test_no_descs_reads_empty` (Adam); and a mutation restored at the same size within the same second left its bytecode behind (WN-T3). No lock changes.
> **Rev 1 · 2026-11-23** — first version, docs only, with `docs/PolishedWorld_Combat_Design.md` Rev 6 (the design locks WN1–WN11 and WN2b), `docs/PolishedWorld_Combat_Decomposition.md` Rev 17, roadmap Rev 87, BACKLOG Rev 118 and README Rev 68. Decomposes Stage 5's fourth slice, WN, from Combat Design §4.4 (WO1–WO7 and the locks under them): damage stored per location, `health` as a display, the wound's Resilience test, the two clocks, starvation's rate, healing per location and what respawn keeps. Twelve locks (Adam, 2026-11-23, one at a time, each as recommended; one reworded on his own point — a statue is a snapshot, WN4), eleven code tasks, a merge and a close-out (WN-T1–WN-T13). Read against live source the same day: `main` at `7d920a3`, tree `c52cd82`; Evennia 6.1.0; *Legend* core pp. 11, 82, 86–90 and 144–146. Three things were run before a line was planned (§4), and one of them decides the order of the tasks: **five of 825 tests notice when the one writer of health is given a new required argument**, so the net is woven first (WN-T1). No code is written and none is changed by this document.
> **Canonical:** `docs/PolishedWorld_Wounds_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Design source:** `docs/PolishedWorld_Combat_Design.md` §3.3, §4.2 (the statue), §4.4 (WO1–WO7, WN1–WN11), §4.10 (CS4), §5, §6, §7 (OQ-WN1–OQ-WN4); `docs/PolishedWorld_Combat_Decomposition.md` §2 (ST1, ST2; WN's row); `docs/PolishedWorld_Body_Decomposition.md` BD7–BD9; `docs/PolishedWorld_Survival_Loop_Decomposition.md` SL6, SL7, SL9, SL11; roadmap decision log, *Hit locations & wound permanence* (Rev 20) and *Death-consequence policy* (Rev 26, (iv)); *Legend* core pp. 11, 82, 86–90, 125, 144–146.
**Status:** IN PROGRESS (Rev 3). WN1–WN11 and WN2b are locked. WN-T1–WN-T7 shipped on `feature/wounds` (`8e3beb7`, tree `c423520`); WN-T8 is next, then WN-T9 and WN-T10.
**Feature branch:** `feature/wounds` — one branch, one merge (ST2). Create it with `git switch -c feature/wounds --no-track origin/main`.
**Rough scope:** eleven code tasks, a merge and a close-out; about twelve to fourteen hours of code — three sessions at 5 h/week. One new module (`world/wounds.py`), seven production files changed (`typeclasses/characters.py`, `world/healing.py`, `world/survival_ticker.py`, `world/chargen.py`, `world/chargen_menu.py`, `world/client_state.py`, `commands/character_commands.py`), no migration, no new command, and nothing in the web client.
**Philosophy:** skynda långsamt — weave the net before cutting the rope; move every reader and writer behind one module while nothing changes, and only then change what is behind it; a thing that cannot be shown truthfully is not shown.
**Labels:** WN (locks, in the Combat Design), WN-T (tasks), WNM (mutations; a letter after the number marks one added at the task), OQ-WN (open questions, in the Combat Design §7). All were free across the repository when checked with `git grep -n -w -E 'WN[0-9]+b?|WN-T[0-9]+|WNM[0-9]+|OQ-WN[0-9]+'`, before they were used. WO1–WO7 stay the Combat Design's labels for the decisions the locks fill in.

---

## 1. What the slice is

A character's hurt is one number today: the `health` trait, CON × 2, written by one method and read by three screens. BD gave the body seven locations and the most each can take (`world/body.py`), and stored nothing. WN is what is left of them:

1. **Where the hurt is.** The damage on each location, stored; its Hit Points, its wound level and the one figure `status` shows, worked out when asked (WN1, WN2).
2. **What a wound does.** A Serious Wound is a Resilience test against the blow that made it; a Major Wound maims, and kills at once or by a clock (WO1–WO3, WN4, WN7).
3. **What starvation does now.** One point from every location, at today's pace for the standard body, with no test and no state (WO7, WN5, WN6).
4. **How it mends,** and what death gives back (WN9, WN10).

**The damage path is whole after WN, and only one road leads onto it.** Starvation and thirst are the only sources of damage in the game. They set no state and start no clock (WN5), so the Resilience test, unconsciousness, *maimed* and both clocks are proven by unit tests and by an in-game protocol that puts the damage there with `py`. The first of them a player meets in play comes with ML. Every task's *In-game check* says which kind of proof it is.

**What a tester notices:** `status` reads differently, and names where the hurt is; death by starvation follows CON + SIZ and not CON alone; natural healing is faster for a body hurt all over. Nothing else.

**One roll site is added and no improvement call.** The wound's test calls `opposed_against`, so `ROLL_SITES` goes from eight to nine and W3.1's question is asked and answered (WN7: yes, the whole physical modifier). The call-site census for `attempt_skill_improvement` stays at six, and a new census holds the wound module at none until ML (WN8).

**No migration.** A character with no damage stored is an unhurt body (WN1), and the old `health` trait stays on old characters, unread (WN2b). BACKLOG *Persistent alpha instance* is not touched.

---

## 2. The locks, and three choices this document makes

The twelve locks are the Combat Design's (§4.4, Rev 6), with their reasons, their numbers and what was rejected. One line each here, for the tasks to cite:

| Lock | In a line |
| --- | --- |
| WN1 | The damage is stored per location, the state beside it, in two Attributes; Hit Points are the maximum less the damage. |
| WN2 | `health` shows the worst location's margin to a Major Wound: (2 × max − damage) / (2 × max), the lowest of seven. |
| WN2b | The `health` trait is no longer created and nothing reads it; old characters keep theirs, unread. |
| WN3 | Combat Actions, rounds and minutes are real time, a minute 60 seconds; hours and days are game time. |
| WN4 | Clocks: (CON + POW) × 60 s for a limb, (CON + POW) / 2 × 5 s for head, chest and abdomen, as stored deadlines. A body with a running clock does not turn to stone. |
| WN5 | `all` damage sets no state and calls for no Resilience test, on any location. |
| WN6 | Starvation and thirst: one point from every location per two survival ticks, per condition. |
| WN7 | The wound's Resilience test takes `physical_modifier()` whole (closes OQ-SC1). |
| WN8 | Resilience's improvement call lands with ML; it lives in the wound module's test function. |
| WN9 | Respawn empties the damage, clears *disabled*, stops clocks and unconsciousness, keeps *maimed* and *severed*. |
| WN10 | Natural healing: one point to every hurt location per interval, one counter; a location with a running clock does not heal. |
| WN11 | WN builds the whole path and shows it in text; `status` names the wounded locations, chargen shows Hit Points per location, the short description's wound word waits for ML. |

**Three choices are this document's, not the design's.** They say how the work is cut, and each can be changed at its task's STOPP 0 without touching a lock.

- **The seam comes before the change.** WN-T3 and WN-T4 move every reader and every writer of health behind `world/wounds.py` while the trait is still what is read and written; nothing a player sees changes, and a census holds the door shut. WN-T5 then changes what is behind the module in one place. The other order — storage first — has a commit where the writer fills the new Attributes and the screens still read the old trait, and §4's first prototype says how many tests that touches at once: 111.
- **A clock is a stored deadline with an alarm.** The deadline, in `db`, is the truth. `evennia.utils.delay(..., persistent=True)` is only what wakes the check: when it fires it reads the deadline again and does nothing if the deadline is gone or later. Stopping a clock is removing the deadline, so nothing has to be cancelled and a task left behind is harmless. The project's reason for avoiding persistent tasks (`commands/work_commands.py:79–83`: the marker lives in `ndb` and would not survive with the task) does not apply, since here nothing lives in `ndb`.
- **A wound's unconsciousness is its own Attribute, read by the collapse's refusal.** `db.collapsed` stays fatigue's: `arm_collapse()` starts fatigue's recovery and is called by every refusal (§3), so a wound that set the same flag would be woken on fatigue's terms by the first command typed. `refuse_if_collapsed()` asks for either cause; the wound's waking is a stored time (WN3); a body with both wakes when both are gone.

---

## 3. Verified source anchors (read 2026-11-23, `main` at `7d920a3`)

**The Combat Design's seam lines have not moved since its Rev 5** (dated there at `22fb018`; `7d920a3` is a docs commit on top).

| Seam | At `7d920a3` | What WN does with it |
| --- | --- | --- |
| `Character.physical_modifier()` | `typeclasses/characters.py:1001` | read by the wound's test (WN7) |
| `Character.improvable_skills` | `:1331` | untouched (WN8) |
| `Character.attempt_skill_improvement` | `:1340`; the winner's-dict rule `:1363–1366` | not called (WN8) |
| `Character.apply_health_damage(amount, source=None)` | `:1623` | gains `location`, keyword-only, no default (WO5) |
| `Character.at_character_death` | `:1677`; the restore `health.current = health.max` `:1791` | the restore calls one function of the wound module (WN9) |
| `Character.collapse()`, `arm_collapse()` | `:1915`, `:1933`; `_collapse_tick` `:2331` clears the flag at fatigue 41 | untouched |
| `Character.refuse_if_collapsed` | `:1956` | asks for either cause |
| `Character.at_pre_move` | `:1975` | untouched |
| The `health` trait's creation | `:432–449` (the word table `:440–448`) | removed (WN2b) |
| `Character.update_health_max()`, `health_desc()` | `:1059`, `:1071` | the first removed, the second reads the wound module |
| `Character.at_post_unpuppet`, `at_post_puppet`, `is_statue` | `:554`, `:595`, `:958` | `is_statue` is False while a clock runs (WN4) |
| `Character._credit_time_away` | `:656`; the stamp `:572` | untouched (the statue's known exception, Combat Design §4.2) |

| Module | At `7d920a3` | What WN does with it |
| --- | --- | --- |
| `world/body.py` | `LOCATIONS` `:195`, `hit_points_max(con, siz)` `:209`, `derived(char)` `:246` | read; nothing added |
| `world/skillcheck.py` | `opposed_against(made, skill, modifier=0)` `:246` | the wound's test |
| `world/skill_base.py::value_of`, `world/healing.py::resilience` `:63` | — | how Resilience is read |
| `world/healing.py` | `ROWS` `:30`, `BLOCKING` `:44`, `accrue` `:88`; the writes to `health.current` `:117–132` | `accrue` gives its points to the wound module (WN10) |
| `world/survival_ticker.py` | `STARVE_DAMAGE` `:32`, `deplete_all_survival_traits` `:44` (sessions only), the tick's re-arm `:104`, `_apply_survival_conditions` `:146`, **the one production call of the writer `:177`** | a counter and a policy (WN5, WN6) |
| `world/chargen.py` | `derive_health_max` `:183`, the refusal without a `health` trait `:251–252`, the call `:262` | all three go (WN2b) |
| `world/chargen_menu.py` | `readers.append("health")` `:143`, the line *Health max* `:464` | the line becomes Hit Points per location (WN11) |
| `world/client_state.py` | `_gauge` `:75`, the `char` snapshot's `health` `:130–135` | same shape, other numbers |
| `world/sdesc.py::_wounds` | `:130`, returns `None` | untouched (OQ-WN3) |
| `commands/character_commands.py` | `status` `:60–63`, `sheet` `:354–361` | read the wound module; `status` gains lines |
| `server/conf/at_server_startstop.py`, `settings.py` | `SURVIVAL_TICK_INTERVAL = 600` `:27`, `TIME_FACTOR = 4` `:55` | read |

| Test | At `7d920a3` | What WN does with it |
| --- | --- | --- |
| `tests/test_encumbrance.py` | `ROLL_SITES` `:982` (eight, in five modules), `TestRollCensus` `:1016` | a sixth module, a ninth roll |
| `tests/test_improvement_engine.py` | `TestImprovableSkillsSet` `:778`, `TestImprovementCallSiteCensus` `:867` | untouched; a new census beside them |
| `tests/test_client_state.py` | `TestPushCensus` `:981`, `test_every_gauge_write_pushes_its_domain` `:1137`; the two calls of the writer `:837`, `:885` | the writer's pushes are rows |
| `tests/test_health_desc.py` | `TestHealthDescCallSites` `:86` | the word table moves |

**Read in Evennia 6.1.0:** `evennia/utils/utils.py:1145` (`delay`; `persistent=True` saves the callback and its arguments), `evennia/scripts/taskhandler.py:358–446` (`add`: an argument that cannot be serialised is dropped with a log line and the task still runs), `:571–600` (`do_task`), `:617` (`create_delays`: each task set against its original time, a passed time at once), `evennia/server/service.py:662–665` (both called at start).

**Read in the book** (the reading text's page markers; the hit location table sits on the turn of pp. 144–145): Hit Points per location, p. 11; falling, p. 82; natural healing and its two restrictions, pp. 86–87; fatigue's *All Skill Tests* and starvation, p. 90; overload, p. 86; Minor, Serious and Major Wounds, pp. 145–146.

---

## 4. What was run (sandbox: Python 3.13.18, Evennia 6.1.0, Django 6.0.10; copies of a fresh clone of `7d920a3`)

**The baseline.** The twenty test modules that name health, death, starvation or respawn (`git grep -l -i -E 'health|at_character_death|survival_ticker|starv|respawn' -- tests`): **825 tests, OK**, 689 s on two cores. The other 1 341 `def test_` of the suite's 2 166 were not run; they do not name health, and a fixture can pass through it all the same (lesson 183), so the whole suite is WN-T12's and Adam's machine's.

**P1 — the trait removed at creation** (one line after the trait is added: `self.traits.remove("health")`). 825 tests, **111 fail** (22 failures, 89 errors), 675 s:

| Module | Fail | Why it notices |
| --- | --- | --- |
| `test_chargen_menu`, `test_chargen`, `test_chargen_help` | 32, 11, 8 | chargen refuses a character with no `health` trait and calls `update_health_max()` |
| `test_healing` | 27 | `accrue` writes `health.current` |
| `test_sheet_combat` | 12 | `sheet` reads the trait |
| `test_health_desc` | 10 | the word table is the trait's `descs` |
| `test_client_state`, `test_fatigue`, `test_rest` | 6, 4, 1 | the snapshot, and respawn |

This is WN2b's cost, and the reason the seam comes first: after WN-T3 and WN-T4 the trait is reached from one module, and the same removal is one module's change.

**P2 — the writer requires a location** (`def apply_health_damage(self, amount, *, location, source=None)`, nothing else touched). 825 tests, **5 fail**, all `TypeError`, 869 s:

- `test_client_state`: `TestHookSites.test_death_pushes_all_four_and_both_rooms`, `TestImmediateSites.test_health_max_and_damage_push_char`
- `test_fatigue`: `TestAwakeTick.test_the_tick_that_starves_adds_minus_twenty`, `…_dehydrates_…`
- `test_healing`: `TestTickHeals.test_the_tick_that_dehydrates_does_not_heal`

**What five means.** The writer has one call in production (`world/survival_ticker.py:177`) and two in tests, and no test module follows starvation through the tick to a death: there is no `tests/test_survival_ticker.py`, and the only test file with *death* in its name is the contract's text. The five pass through the writer on the way to something else — a push, a fatigue penalty, a blocked heal. `_apply_survival_conditions`' docstring promises *one fatal tick -> one corpse* for a body both starving and dehydrated, and nothing holds it to that. WN rewrites that chain, so **WN-T1 writes its tests first, against today's code**.

**Not run:** nothing of WN's own. The slice's functions are small enough to be written at their tasks, and the three prototypes above answer the questions the order of work depends on.

---

## 5. Dependency graph

```
WN-T1 ─┐
WN-T2 ─┴─> WN-T3 ──> WN-T4 ──> WN-T5 ─┬─> WN-T6 ──────────────────────┐
                                      ├─> WN-T7 ──────────────────────┤
                                      └─> WN-T8 ──> WN-T9 ──> WN-T10 ─┴─> WN-T11 ──> WN-T12 ──> WN-T13
```

WN-T1 (the net) and WN-T2 (the pure functions) touch no file in common and may be taken in either order; both come before the seam. WN-T3 before WN-T4, because the readers are the larger and the safer half. WN-T5 is the one task where what a player sees changes for a reason other than a new line of text, and everything after it builds on the stored damage. WN-T6 (the trait goes), WN-T7 (starvation's rate) and the chain WN-T8–WN-T10 (states and the test, unconsciousness, the clocks) are independent of each other after WN-T5.

**Between WN-T5 and WN-T7 the branch starves a body twice as fast as `main`** — a point a tick from every location, ten points to a head of 5 — and that is why it is a branch.

---

## 6. Component W1 — The net and the pure functions

### Task WN-T1 — The net under the writer
- **Goal:** Tests follow starvation and thirst through the survival tick to a death, on today's code.
- **Dependencies:** none.
- **Approach:** new `tests/test_survival_death.py`; tests only, no production line changes. They drive `survival_ticker._deplete_character(char)` on an `EvenniaTest` character, as `tests/test_fatigue.py::TestAwakeTick` does, and assert **what a player could see**: dead or not, how many corpses lie in the room, where the body is, whether the condition buff is on. The body's hurt is read through one helper in the module, `_hurt(char)`, so that WN-T5 changes one function and not every assertion. Cases: a tick at hunger's minimum hurts by `STARVE_DAMAGE` and puts *Starving* on; both gauges at minimum hurt by two in **one** call of `apply_health_damage` (a spy on the method, which is the receipt that the road to death is the writer); a body one point from death under both conditions dies **once** — one corpse, the body at its respawn point, unhurt, both conditions gone; a gauge above its minimum hurts nothing and takes its condition off; a character with no session is not touched by `deplete_all_survival_traits()`.
- **Testing:** the new module with `tests.test_fatigue`, `tests.test_healing` and `tests.test_client_state`.
- **Red before green:** none — these describe code that exists. The mutations are the receipt that they bite, and each is run before the task is called done.
- **Mutations (WNM1–WNM4):** `STARVE_DAMAGE = 0` (the first case must fail); one call of the writer per condition in place of the sum (the spy's count must fail); the writer never calls `at_character_death()` (the death must fail); the `else` that removes a condition dropped (the fed body must fail).
- **In-game check:** none. Nothing a player can see changes; the mutation table is the proof.
- **Commit:** `test(survival): follow starvation through the tick to a death (WN-T1)`
- **Shipped (Rev 2):** `cd603c9` on `feature/wounds`, tree `b8edc4b` (the sandbox commit and a `git am` on a fresh clone gave the same tree, as for every task below). Six tests in `tests/test_survival_death.py`; the tick is driven as `TestAwakeTick` drives it, with the weather patched out and the clock left alone, so the first tick reads 0 game seconds and neither the awake test nor healing takes part. Three choices at STOPP 0 (Adam, each as recommended): the first case asserts **1**, not `STARVE_DAMAGE` — an assertion that reads the constant reads the value WNM1 changes and passes at 0 = 0; the respawn point is set to `room2`, since the fixture's fallback, `home`, is the room the body falls in; the fed body's hunger is 50, because the tick depletes the gauges before it reads them (`world/survival_ticker.py:88–94`). Hunger and thirst have a case each. WNM1–WNM4 killed; **WNM2 by the spy alone**: under a call per condition the loop reads thirst again after the respawn has filled it, so the death test still sees one corpse — the docstring's *by accident*, shown. With `test_fatigue`, `test_healing` and `test_client_state`: 199 tests OK.

### Task WN-T2 — Hit Points, levels, the margin, the table and the clocks' lengths
- **Goal:** `world/wounds.py` answers from numbers alone what a location has left, what its wound is called, what `health` shows, which location a d20 names and how long each clock is.
- **Dependencies:** none.
- **Approach:** new `world/wounds.py`, with no Evennia import in this task. `VITAL = ("head", "chest", "abdomen")`, the other four of `body.LOCATIONS` being limbs. `hit_points(maximum, damage)` is the difference. `level(maximum, damage)` gives `intact` at no damage, `minor` while Hit Points are positive, `serious` at 0 or below, `major` at minus the maximum or below (pp. 145–146). `margin(maximum, damage)` gives the pair (2 × max − damage, floored at 0; 2 × max). `health(maxima, damages)` gives the pair of the location whose fraction is lowest, the first in `LOCATIONS`' order on a tie, with its percentage (WN2). `location_for(roll)` is the book's table — 1–3 right leg, 4–6 left leg, 7–9 abdomen, 10–12 chest, 13–15 right arm, 16–18 left arm, 19–20 head — and raises `ValueError` outside 1–20. `clock_seconds(con, pow_, location)` is (CON + POW) × `MINUTE` for a limb and (CON + POW) / 2 × `VITAL_ROUND_SECONDS` otherwise, with `MINUTE = 60` and `VITAL_ROUND_SECONDS = 5` named beside WN3's and WN4's reasons. `HEALTH_WORDS` is the trait's table copied (0 *dead* … 100 *healthy*, `typeclasses/characters.py:440–448`) and `word_for(percent)` reads it as `health_desc()` does today.
- **Testing:** `tests/test_wounds.py`, plain `unittest`. The maxima at CON + SIZ 21 (5, 7, 6, 4, 5) taken from `body.hit_points_max(10, 11)` and not typed; `level` at damage 0, 1, 4, 5, 9 and 10 for a maximum of 5; WN2's three rows (a head at −5: 0 %; five points everywhere with the arms stopped at 4: 50 %; one arm at 0: 50 %); every one of the twenty rolls, and 0 and 21; the clocks at CON + POW 21 (1260 and 52.5); every boundary of the word table; a test that `HEALTH_WORDS` equals the trait's `descs` for as long as the trait is created (it goes with WN-T6).
- **Red before green:** the import fails first; then, with `level` written with `<` at the Major boundary, the row at damage 10 fails.
- **Mutations (WNM5–WNM9):** Major at less than minus the maximum; the margin over the maximum and not twice it (a location at 0 reads 0 %); `health` taking the highest fraction; the arm and leg rows of the table swapped; the limb's clock halved.
- **In-game check:** `py from world import wounds; self.msg(str((wounds.level(5, 10), wounds.clock_seconds(10, 11, "head"), wounds.location_for(20))))` prints `('major', 52.5, 'head')`.
- **Commit:** `feat(wounds): Hit Points, levels, the margin, the hit location table and the clocks' lengths (WN1–WN4)`
- **Shipped (Rev 2):** `1442ce9`, tree `c43be01`. Nineteen tests in `tests/test_wounds.py`, `SimpleTestCase` (a database query fails it) except the one that holds `HEALTH_WORDS` equal to the trait's `descs`. Read against the book first (pp. 145–146 in the reading text): Major at *a negative score equal or greater than its starting Hit Points*, the table row by row, the clocks in minutes and rounds. Choices at STOPP 0 (Adam, each as recommended): `health` returns `(left, whole, percent)`, the percent an unrounded float, the lowest fraction found with `fractions.Fraction`; `clock_seconds` raises `ValueError` for a key that is not one of `body.LOCATIONS` (added here: a misspelled vital key would get the limb's clock, twenty-four times longer); the levels are the constants `INTACT`, `MINOR`, `SERIOUS`, `MAJOR`. Red: the import, then `level` with `<` at the Major boundary failed the damage-10 row alone. WNM5–WNM9 killed, with **WNM7b** — a tie taken by the last location: in the five-point row the legs end at 5/10, the head's own numbers, so that row cannot see it, and `test_on_a_tie_the_first_location_is_shown` (head 5/10, arm 4/8) was added — and WNM8b, the other half of the arm/leg swap. With `test_body` and `test_health_desc`: 57 OK. The in-game check, run by Adam, printed `('major', 52.5, 'head')`, and `wounds.health(..., {"head": 5, "left_arm": 4})` printed `(5, 10, 50.0)`.

---

## 7. Component W2 — The seam

### Task WN-T3 — Every reader of health goes through the wound module
- **Goal:** `status`, `sheet`, the `char` snapshot and `health_desc()` read health from `wounds.health_of(char)`, which for now reads the trait.
- **Dependencies:** WN-T2.
- **Approach:** `wounds.health_of(char)` returns the three numbers the screens print — current, max and percentage — or `None` for an object with no body to read, as `client_state._trait` gives `None` today. In this task it takes them from the trait. `health_desc()` (`:1071`) becomes `wounds.word_for(percentage)`; `status` (`commands/character_commands.py:60–63`), `sheet` (`:354–361`) and `client_state.char` (`:130–135`) take the numbers from the function, the snapshot keeping its three keys. A census in `tests/test_wounds.py`, read by AST as `TestImprovableSkillsSet` reads calls, counts the reads of the `health` trait per module and holds them against a table that the next three tasks shrink: after this task `world/wounds.py`, `world/healing.py`, `world/chargen.py`, `world/chargen_menu.py` and `typeclasses/characters.py`, with the count each has.
- **Testing:** `tests.test_health_desc`, `tests.test_sheet_combat` and `tests.test_client_state` **unchanged and green** — that is the proof that nothing moved. The census is new. **Read at STOPP 0:** `TestHealthDescCallSites` (`tests/test_health_desc.py:86`), which may pin how the word is reached.
- **Red before green:** the census is written first with the table as it will be, and fails on today's code with the three command and snapshot sites listed.
- **Mutations (WNM10–WNM12):** `status` reading the trait again (the census must fail); `health_of` returning the maximum as the current value (`status`' tests must fail); `word_for` given the value and not the percentage (`test_health_desc` must fail).
- **In-game check:** `status` and `sheet` before and after the task print the same lines. With the hurt put on by hand — first `py self.msg(str(self.traits.health.current))` to read what to put back, then `py self.traits.health.current = 5` — `status` reads *5/20* and the word it read on `main`; then the first value is restored.
- **Commit:** `refactor(wounds): every reader of health goes through world/wounds.py (WN2b)`
- **Shipped (Rev 2):** `246d36f`, tree `f4a1a92`. `wounds.health_of` returns `(current, max, percent)` — current and max whole, truncated as `status` printed them, the percent unrounded — or `None` without a trait; `status`, `sheet` and the snapshot call it through the module, and a local `_percent` in `commands/character_commands.py` prints `"{:3.1f}%"`, a gauge's default, so every row prints as before. `sheet` prints the Health row before its loop over the other three. **The census** counts three shapes by AST — `X.traits.health`, `X.traits.<method>("health", ...)`, `_trait`/`getattr` with `"health"` — and a local named `traits` as `X.traits`: its first version was blind to `health_of`'s own reach, and so to any reader written that way. A bare `"health"` string is a word, not a read, so `chargen_menu.py:143` (*Feeds health*), named in this task's *Approach*, is **not** in the table; it goes with WN-T6 all the same. After this task: `typeclasses/characters.py` 6 (creation 1, `update_health_max` 3, the writer 1, the restore 1), `world/chargen.py` 1, `world/healing.py` 1, `world/wounds.py` 1 — read WN-T4's, WN-T5's and WN-T6's census numbers against this. `sheet`'s `getattr(char.traits, key)` cannot be read by AST and is held by a stub test instead: `health_of` patched to 7/9, 77.7 %, which `status`, `sheet` and the snapshot must all show. **`test_health_desc` was not left unchanged** (Adam, at STOPP 0): `test_no_descs_reads_empty` was removed, since the word no longer comes from the trait's `descs`; the rest is unchanged and green. WNM10–WNM12 killed, with WNM10b (`sheet`) and WNM10c (the snapshot). The twenty-two modules that name health, death, starvation or respawn: 855 tests OK, the static count. **A first run of those modules tested a mutant:** WNM12 has the original's size and was restored within the same second, and Python's bytecode check is mtime in whole seconds and size, so the stale `.pyc` ran; the mutation harness now runs with `PYTHONDONTWRITEBYTECODE=1`. The in-game check, run by Adam: `status` and `sheet` the same across the reload; 5/20 *(25.0%) critically wounded* in `status` and in the snapshot; restored to 20.

### Task WN-T4 — One door for damage, healing and respawn; the writer names its location
- **Goal:** Damage, natural healing and respawn's restore reach health through three functions of the wound module, and `apply_health_damage` refuses a call that does not say where.
- **Dependencies:** WN-T1, WN-T3.
- **Approach:** `Character.apply_health_damage(amount, *, location, source=None)`: `location` is keyword-only and has no default (WO5). It takes `wounds.ALL`, `wounds.RANDOM` or one of `body.LOCATIONS`' keys; anything else raises `ValueError` before anything is written. The method calls `wounds.damage(char, amount, location)` and then asks `wounds.is_dead(char)`, calling `at_character_death()` as today. `world/healing.py::accrue` asks `wounds.room_to_heal(char)` and gives its points to `wounds.heal(char, points)`, which returns what landed; the restore block (`:1791`) calls `wounds.restore_at_respawn(char)`. All four still read and write the trait, and the policy is checked and not yet used. `world/survival_ticker.py:177` passes `location=wounds.ALL`. Tests that put hurt on a character by writing `health.current` are changed to go through the writer, so that WN-T5 changes their numbers and not their lines. The census of WN-T3 gains the writes. **Read at STOPP 0:** `test_every_gauge_write_pushes_its_domain` (`tests/test_client_state.py:1137`) and `TestPushCensus` (`:981`) — the writes change module, and both are keyed by where a write stands.
- **Testing:** `tests/test_wounds.py`: no `location` is a `TypeError`; an unknown one is a `ValueError` and leaves health as it was; `heal` stops at the maximum and returns what landed; `restore_at_respawn` fills it. WN-T1's net stays green with one line changed (the spy now sees `location=wounds.ALL`).
- **Red before green:** prototype P2 again, on the branch: with the new signature and nothing else, the same five tests of §4 fail, and are green when the three call sites pass a location.
- **Mutations (WNM13–WNM16):** a default `location=ALL` (the `TypeError` test must fail); `accrue` writing the trait itself (the census must fail); the restore block not calling the function (WN-T1's *unhurt after death* must fail); the check of the policy after the write (the unknown location must leave a mark and fail).
- **In-game check:** behaviour as on `main`. `py self.msg(str(self.traits.hunger.current))` to read what to put back; `py self.traits.hunger.current = 0`; `py from world import survival_ticker; survival_ticker._deplete_character(self)`; `status` is one point lower and *Starving* is on; hunger is restored and `py self.traits.health.current = self.traits.health.max` puts the point back.
- **Commit:** `refactor(wounds): one door for damage, healing and respawn; the writer names its location (WO5)`
- **Shipped (Rev 3):** `db9420b`, tree `bdd16fb`. `world/wounds.py` gains `ALL`, `RANDOM`, `check_location`, `damage`, `is_dead`, `heal`, `room_to_heal` and `restore_at_respawn`; the writer is `apply_health_damage(amount, *, location, source=None)`. **P2 failed nine tests, not five:** the five of §4 and four of WN-T1's net, written after §4 and under the writer too. Choices at STOPP 0 (Adam, as recommended): **the pushes stay with the callers** — the writer pushes after its death check, so a fatal blow still sends the refilled value (W4.2) — and `TestPushCensus` gained `DOOR_WRITES` and a test that each door has exactly one caller in production and that the caller pushes its domain; **the place is checked before `amount <= 0`**, so a wrong place fails on the tick's usual 0; one helper, `_health_trait`, is the module's one reach (census: `typeclasses/characters.py` 4, `world/chargen.py` 1, `world/wounds.py` 1). Five of the ten hand-written `health.current` lines in the tests went through the doors; five set premises the writer cannot. WNM13–WNM16 killed, and WNM14b (a second caller of `damage` that does not push) by the door census alone. 865 tests in the twenty-two modules OK. **The in-game check showed what choice A costs:** a door called from `py` pushes nothing, so the panel kept 18/20 while `status` read 20/20; in play a door is reached only through its caller.

---

## 8. Component W3 — The change

### Task WN-T5 — The damage is stored per location
- **Goal:** Behind the seam, damage is stored on each location and `health` is the worst location's margin; the trait is neither read nor written.
- **Dependencies:** WN-T4. **The slice's largest task** — about two hours; if it runs long it is cut at the tests of healing, never between the writer and the screens.
- **Approach:** one Attribute, `db.body_damage`: a plain dict from location to a whole number, holding only hurt locations. Readers take `None` as an unhurt body and test for `collections.abc.Mapping`, never `dict` (a stored dict comes back as `_SaverDict`); writers assign a fresh dict and never change one in place. `wounds.damage`: `ALL` adds the amount to every location, **a limb stopping at its maximum** (Hit Points 0, WO7); a named key adds to that location; `RANDOM` rolls `location_for(randint(1, 20))`. `wounds.is_dead`: for an `ALL` source, a vital location at a Major Wound (WO7, WN5); what a blow's Major Wound does is WN-T8's. `wounds.health_of` reads CON and SIZ through `body.hit_points_max` and the damage (WN2), and gives `None` for an object without both stats. `wounds.heal` takes a point from every hurt location; `room_to_heal` is the largest damage on any (WN10). `restore_at_respawn` removes the Attribute. The trait is still created (WN-T6) and the census's table drops to its creation and chargen's three sites.
- **Testing:** on a character with CON 10 and SIZ 11. Five points of `ALL`: the arms hold 4, the rest 5, `health_of` gives 5 of 10 and 50 %. Ten points of `ALL`, through WN-T1's net: dead, once, and unhurt after. A named leg; `RANDOM` with `world.wounds.randint` patched to 20 hurting the head. A heal mends every hurt location by one and returns one. An unhurt character has no Attribute. A character whose CON is raised keeps its damage and gains Hit Points. **A character with the old trait at 3 of 20 and no damage reads 100 %** — WN2b's promise to every character made before WN. `tests.test_healing`'s expectations are rewritten in locations.
- **Red before green:** the five-point row first: on WN-T4's code it reads 15 of 20, 75 %.
- **Mutations (WNM17–WNM21):** a limb that does not stop at 0 (the arms' row must fail); `is_dead` counting limbs; `health_of` taking the best location; `heal` mending only the first location in order; `restore_at_respawn` leaving the damage (the net's *unhurt after death* must fail).
- **In-game check:** `py self.msg(str(self.db.body_damage))` prints `None`. `py from world import wounds; self.apply_health_damage(5, location=wounds.ALL); self.msg(str(self.db.body_damage))` prints seven keys, the arms at 4. `status` reads *5/10 (50%)* for a character with CON + SIZ 21–25. `py self.attributes.remove("body_damage")` puts back what the first step read, and `status` reads *10/10* (Rev 3: was `py self.db.body_damage = None`, which stores a `None`).
- **Commit:** `feat(wounds): damage stored per location, health as the worst margin (WN1, WN2, WN10)`
- **Shipped (Rev 3):** `59369f9`, tree `40cc17e`. Choices at STOPP 0 (Adam, as recommended): `TestPushCensus` reads an assignment to `db.body_damage` and `attributes.remove("body_damage")` as writes, so the doors stay in it; the new tests run at CON 10 and SIZ 11, the rest at the fixture's CON + SIZ 20, every maximum from `body.hit_points_max`; WN-T1's `_hurt` is the largest damage on any location; premises no writer can make (0 %, a limb past a Major Wound) are written to `db.body_damage` by hand, and the float-base healing test went; `is_dead` takes no source yet — **WN-T8 must change it**, since a won Resilience test at a vital Major Wound is unconsciousness, not death. **A CON + SIZ 20 body — the fixture's, and the dev character `adam` — has a head of 4, not 5:** 8/8 unhurt, and starvation kills at eight points. Three tests outside the plan counted CON × 2 or removed SIZ, which the encumbrance limit reads (`TestWholeNumbers` reads 10/10 at CON 14 + SIZ 8). WNM17–WNM21 killed, with WNM20b (an empty dict kept for an unhurt body); **WNM18 (limbs counted for death) by the premise test alone**, since no `ALL` source can bring a limb to a Major Wound. 877 tests OK. The in-game check's `py self.db.body_damage = None` left a stored `None`; the line now removes the Attribute.

### Task WN-T6 — The trait goes
- **Goal:** A new character has no `health` trait, character creation shows Hit Points per location, and nothing creates, rescales or asks for the trait.
- **Dependencies:** WN-T5.
- **Approach:** removed: the trait's creation (`typeclasses/characters.py:432–449`), `update_health_max()` (`:1059`), `chargen.derive_health_max` (`world/chargen.py:183`), chargen's refusal of a character without the trait (`:251–252`) and its call (`:262`), the menu's reader (`world/chargen_menu.py:143`). The menu's line *Health max* (`:464`) becomes *Hit Points: head 5, chest 7, abdomen 6, arms 4, legs 5*, from `body.hit_points_max` on the draft's CON and SIZ; a test holds that the two arms and the two legs are equal for every legal sum, which is what lets the line name them once. The sentence of `help` that quotes `derive_health_max(10)` (`world/chargen.py:398`) is rewritten. The census's table is now empty, and its failure message names WN2b. Characters made before this task keep their trait; nothing reads it.
- **Testing:** `tests.test_chargen`, `tests.test_chargen_menu` and `tests.test_chargen_help` rewritten where they named the trait or the line; WN-T2's test that the word table equals the trait's `descs` goes with the trait.
- **Red before green:** prototype P1 again, on the branch. In §4 it failed 111 tests in nine modules; here it must fail in the three chargen modules only, and **that number is the receipt that the seam held**.
- **Mutations (WNM22–WNM24):** the refusal put back (a character created without the trait must fail to finish); the line showing the head alone; one reader allowed in the census.
- **In-game check:** a fresh account (`Account.create`, lesson 242) reaches the confirmation and reads the *Hit Points* line; from a Developer character, `py import evennia; self.msg(str(evennia.search_object("<name>")[0].traits.get("health")))` prints `None` for it (Rev 3: a fresh character is a player and has no `py`), `py self.msg(str(self.traits.get("health")))` prints a trait for a character made before, and `status` is right for both.
- **Commit:** `refactor(character): the health trait is no longer created (WN2b)`
- **Shipped (Rev 3):** `8e3beb7`, tree `c423520`, after WN-T7 on the branch. **P1 failed 59 tests in six modules, not three:** fifty-one in the chargen modules, and `TestChargenEnd`, which goes through the refusal; the other seven name the trait or `update_health_max` themselves — three WN-T5 premises for a character made before WN, the census, the word-table test, the snapshot's check of the old trait, the push test — and **no production reader** failed. Choices at STOPP 0 (Adam, as recommended): the allocate screen says CON *and* SIZ feed *Hit Points*, where the *Approach* removed CON's *Feeds health* — both feed the new number; `tests/wounds_fixture.py::made_before_wn` adds the trait as it was created, for the three tests that hold WN2b's promise to an old character; `TestPushCensus` lost `update_health_max`'s write and push; the line has one home, `chargen.hit_points_text(con, siz)`, used by the menu and by `help chargen` (CON 10 and SIZ 10). Gone with the trait: `TestHealthIsInt`, `TestWordsMatchTheTrait`, and the two prose lines WN-T7 left that named `STARVE_DAMAGE`. WNM22–WNM24 killed, WNM24 by the census alone. 879 tests OK. In the in-game check a fresh character is a player and has no `py`; its trait is read from a Developer character.

### Task WN-T7 — Starvation's rate
- **Goal:** Starving or thirsting takes one point from every location per two survival ticks for each condition, and a body that has eaten starts its next hunger from nothing.
- **Dependencies:** WN-T5.
- **Approach:** `STARVE_TICKS_PER_POINT = 2` in `world/survival_ticker.py`, where `STARVE_DAMAGE` stood, with WN6's reason beside it. A counter per character, `db.starve_progress`, as `db.heal_progress` is kept: each tick adds one for each condition that is on, whole pairs become points, the remainder is carried, and **the Attribute is removed on the first tick with no condition on**. The points go in one call of the writer, as today, so the docstring's *one fatal tick, one corpse* still describes the code.
- **Testing:** in WN-T1's module. One tick: nothing. Two: a point everywhere. Both conditions: a point every tick. A meal between two ticks: the counter is gone and the next hunger needs two ticks again. Twenty ticks to a death at head 5 and twelve at head 3. The tick's interval stays pinned where it is (`tests/test_server_startstop.py`).
- **Red before green:** *one tick: nothing* fails on WN-T5's code, which takes a point a tick.
- **Mutations (WNM25–WNM27):** the counter kept when the condition ends (the meal must fail); one tick per point; a counter that adds one a tick whatever the number of conditions (both conditions must fail).
- **In-game check:** read hunger and `db.body_damage` first. `py self.traits.hunger.current = 0`, then `py from world import survival_ticker; survival_ticker._deplete_character(self)` twice: `status` reads *10/10* after the first and *7/8 (87.5%)* after the second — the arm's margin, the worst at one point (Rev 3: was *9/10 (90%)*, the head's). Restore hunger, `py self.attributes.remove("body_damage")`, and one more tick removes `starve_progress`.
- **Commit:** `feat(survival): starvation takes a point from every location per two ticks (WN6)`
- **Shipped (Rev 3):** `32b0c25`, tree `68eb901`. Choices at STOPP 0 (Adam, as recommended): the counter is removed only by a tick with no condition on, not at death — the respawn fills the gauges and the next tick clears it; WN-T1's net rewritten — one tick sets the condition and hurts nothing, the second hurts one; both conditions take one point a tick in one call; a meal between two ticks empties the counter; head 5 lives 19 ticks and dies on the 20th, head 3 on the 12th; healing's dehydrating tick asserts no point yet; the two prose lines that named `STARVE_DAMAGE` went with WN-T6. WNM25–WNM27 killed, WNM25 by the meal test alone. 880 tests OK. **The in-game check's numbers were wrong:** at one point of `ALL` the worst margin is the smallest location's, the arm's — 7/8 (87.5 %) at CON + SIZ 21, 5/6 (83.3 %) at 20 — not the head's; the line is corrected. A missing Attribute reads `[]` from `attributes.has`, not `False`. Adam's question at STOPP 0 — should starvation's death use the whole body's Hit Points? — is filed at BACKLOG *Survival loop tuning*.

---

## 9. Component W4 — What a wound does

### Task WN-T8 — States, and the Resilience test
- **Goal:** A blow's Serious or Major Wound is tested against the roll that made it and leaves its state, and respawn keeps *maimed*.
- **Dependencies:** WN-T5.
- **Approach:** the writer gains `made=None`: the attack roll's `skill_check` dict, when the source has one. After damage from a named or a random source, a location left at 0 or below **by this call** is a wound to answer for (*not repeated unless the location is wounded again*, p. 145). `wounds.resilience_test(char, made)` is `opposed_against(made, value_of(char, "resilience"), char.physical_modifier())` and returns its dict whole, `resisting` included, which is what WN8's call will need. A second Attribute, `db.wound_states`, from location to `disabled`, `maimed` or `severed`, the heavier state replacing the lighter.

  | Wound | With a made roll | State |
  | --- | --- | --- |
  | Serious, limb | lost: the limb is useless | `disabled`, cleared when the location is above 0 again |
  | Serious, head, chest, abdomen | lost: unconscious for the damage in minutes | none |
  | Major, limb | lost: unconscious | `maimed` |
  | Major, head, chest, abdomen | lost: **death at once**; won: unconscious | `maimed` |

  Unconsciousness and the clock are returned in this task as what the wound calls for and are carried out by WN-T9 and WN-T10. With `made=None` there is no test (OQ-WN1) and the state is still set. `severed` is written behind a constant that is off, `SEVERED_ENABLED = False`: on, a limb's Major Wound gives it (roadmap Rev 20 — built, and switched off). An `ALL` source reaches none of this (WN5). **`restore_at_respawn` now removes `disabled` and keeps the rest, in this commit** (BACKLOG *`at_character_death()` restore block vs persistent wound tiers*). `ROLL_SITES` gains `"world/wounds.py": 1`, with W3.1's answer in the comment; a new census holds the calls of `attempt_skill_improvement` in the module at none, and its message names WN8.
- **Testing:** `world.skillcheck.randint` patched, as `tests/test_encumbrance.py` does. Each row of the table, won and lost. The modifier handed to `opposed_against` is `physical_modifier()` for an overloaded, Wearied body (−50). A second blow on a location already below 0 is tested again; damage elsewhere is not. Ten points of `ALL` on a limb leave no state. A healed limb loses `disabled`. **A maimed leg, a death, and the state is still there**; `disabled` is not. `severed` with the constant patched on.
- **Red before green:** the respawn test first: on WN-T5's code nothing writes the state, so it is written by hand, and the restore — which removes the damage — is shown to leave it; then the task's own writer is used.
- **Mutations (WNM28–WNM33):** modifier 0 (WN7); an `ALL` source setting a state; **respawn clearing `maimed`** (the hazard the BACKLOG entry was filed for); the constant ignored; `disabled` kept above 0; the test repeated for a location this call did not touch.
- **In-game check** *(by `py`; no play reaches this before ML)*, on a character made for it: `py from world import wounds; self.apply_health_damage(6, location="left_leg", made={"result": "success", "success": True, "roll": 1, "target": 200}); self.msg(str((self.db.body_damage, self.db.wound_states)))` — a roll Resilience all but never beats, so the leg at −1 is `disabled` (if the states print `None`, the test was won: put the damage back and repeat). The same with 10: `maimed`. Afterwards `py self.db.body_damage = None` and `py self.db.wound_states = None`.
- **Commit:** `feat(wounds): the Resilience test and the stored states; respawn keeps maimed (WO1, WO2, WN7, WN9)`

### Task WN-T9 — Unconsciousness from a wound
- **Goal:** A body a wound has knocked out can do nothing until its time is over, and wakes without help.
- **Dependencies:** WN-T8.
- **Approach:** `db.wound_unconscious`, holding the location and the real time at which it ends (`time.time()` plus the damage × `MINUTE`, WN3). `wounds.knock_out(char, location, minutes)` interrupts the timed action as `collapse()` does (`:1915`), tells the body and the room, and sets an alarm (§2's second choice). `wounds.unconscious(char)` answers from the stored time and clears a time that has passed, so nothing depends on the alarm having fired. `refuse_if_collapsed()` (`:1956`): collapsed, as today; otherwise unconscious from a wound, the same refusal **without** `arm_collapse()`. `restore_at_respawn` clears it. A Major Wound's unconsciousness has no length in the book (*from the agony*, p. 146): a limb's is given the damage in minutes, as a Serious Wound's is, and a vital location's lasts for as long as its clock runs (WN-T10). **A body knocked out is not a statue until it wakes** — WN4's door, opened one step wider; see OQ-WN6. `wounds.revive(char)` is written and called by nothing: it is HL's (*the restoration of a single Hit Point … will revive them*, p. 87).
- **Testing:** `EvenniaCommandTest`, `world.wounds.time` patched. A knocked-out body is refused a command and a step through an exit. **Its first refusal leaves the timed-action slot empty** — the test of §2's third choice. It wakes when the time has passed, on a command and on the alarm. A body both collapsed and knocked out is still down when either ends. A death clears it.
- **Red before green:** the slot test first, against a version that sets `db.collapsed`: the refusal arms fatigue's recovery.
- **Mutations (WNM34–WNM36):** `db.collapsed` set in place of the Attribute; the comparison of times turned round; the refusal asking only for a collapse.
- **In-game check** *(by `py`)*: `py from world import wounds; wounds.knock_out(self, "head", 1)`; `look` and a step are refused; a minute later the waking line comes by itself and `look` answers.
- **Commit:** `feat(wounds): a wound's unconsciousness, with its own cause and its own waking (WO1, WN3)`

### Task WN-T10 — The clocks
- **Goal:** A Major Wound that a body survives kills it when its time is out unless the clock is stopped; the location does not mend while it runs; and the body is not a statue.
- **Dependencies:** WN-T9.
- **Approach:** `db.wound_clocks`, from location to the real time at which it runs out. Started by WN-T8's Major Wound from a named or random source, with `clock_seconds(CON, POW, location)`. The alarm is `delay(seconds, wounds._clock_due, char, location, persistent=True)`; `_clock_due` is a module-level function, reads the deadline again and does nothing unless it has passed; if it has, the body is told and `at_character_death()` is called. `wounds.stop_clock(char, location)` removes the deadline and returns whether there was one — **the function HL calls**. `heal` and `room_to_heal` skip a location with a deadline (WN10), and when only such locations are hurt the healing counter is zeroed as at full health. `is_statue` (`:958`) is False while there is a deadline or WN-T9's unconsciousness; **read at STOPP 0:** `at_post_unpuppet` (`:554`), which says the *turns to weathered stone* line and stamps `db.away_since` when the session ends — both must wait until the body does turn to stone. `restore_at_respawn` removes the deadlines.
- **Testing:** a head's Major Wound survived starts a clock of 52.5 s at CON + POW 21 and an arm's one of 1260 s. `_clock_due` on a passed deadline kills once; on a stopped one does nothing; on one replaced by a later one does nothing. Two clocks: the first death removes both, and the second alarm does nothing — **the body is not killed again at its respawn point** (WN9). The call to `delay` is seen to be persistent and to carry the character and the location, `world.wounds.delay` being patched. A clocked location is not healed and the others are. `is_statue` for a body with no session and a clock is False, and True once the clock is stopped.
- **Red before green:** the stopped clock first, against a `_clock_due` that does not read the deadline: it kills.
- **Mutations (WNM37–WNM41):** `_clock_due` not reading the deadline; respawn leaving the deadlines; `heal` mending a clocked location; `is_statue` ignoring the clock; a limb given the vital length.
- **In-game check** *(by `py`, on a character made for it — it dies, and what it carries goes to a corpse)*: (1) `py self.apply_health_damage(10, location="head")`: `status` reads 0 %, and after (CON + POW) / 2 × 5 seconds the body dies, wakes in the temple unhurt, and `py self.msg(str(self.db.wound_states))` still prints the head as `maimed` (OQ-WN2). (2) `py self.apply_health_damage(8, location="left_arm")`, then `evennia reload` in a shell, then `py self.msg(str(self.db.wound_clocks))`: the deadline is the same; `py from world import wounds; self.msg(str(wounds.stop_clock(self, "left_arm")))` prints `True`, and nothing happens at the deadline. (3) with a second character in the room, the first is hurt as in (2) and its player quits: `look` shows a body and no statue. Afterwards the three Attributes are set to `None`.
- **Commit:** `feat(wounds): the two clocks, stopped by one function; a body with a clock is no statue (WN4, WN9, WN10)`

---

## 10. Component W5 — What is shown, and close-out

### Task WN-T11 — `status` names the wounds
- **Goal:** Under the health line, `status` and `sheet` say where a body is badly hurt and what state each location is in.
- **Dependencies:** WN-T6, WN-T7, WN-T10.
- **Approach:** `wounds.report(char)`: for each location in `LOCATIONS`' order that is at a Serious Wound or worse, or has a state, or has a clock, its name, its level and its state. `status` prints a line for each under the health line — *left leg: serious, maimed* — and nothing more for a body with only Minor Wounds, since a starving body has seven of them and the figure already says so. The `char` snapshot is not touched (the panel is CL's). The words are OQ-WN5.
- **Testing:** `EvenniaCommandTest`: an unhurt body, five points of starvation (head, both arms and both legs at *serious*, in that order), a maimed leg after a respawn (*intact, maimed*), a location with a clock.
- **Red before green:** the maimed leg after a respawn: `status` reads 100 % and says nothing of it.
- **Mutations (WNM42–WNM44):** Minor Wounds listed; the state left out; the order taken from the stored dict.
- **In-game check:** WN-T7's two steps repeated until `status` reads 5/10: five lines appear in the order head, arms, legs. Restore as there.
- **Commit:** `feat(status): the wounded locations, by level and state (WN11)`

### Task WN-T12 — Protocol, suite and merge
- **Goal:** `feature/wounds` is on `main` by a merge commit, with the whole suite green and every in-game check run once in order on the merged tree.
- **Dependencies:** WN-T1–WN-T11.
- **Approach:** the suite whole and parallel on Adam's machine (`server.test_runner.ForkTestRunner`, `--parallel`); the count predicted from `git grep -c 'def test_'` before the run. The in-game checks of WN-T5–WN-T11 as one protocol on a character made for it, each step with what it proves and whether it is play or `py`. `git merge-tree` for the merge's tree before the PR; a merge commit, not a rebase; the branch deleted. Whether a tag is cut is OQ-WN7.
- **Commit:** the merge commit of the PR.

### Task WN-T13 — Documentation
- **Goal:** The slice is closed in the documents in one commit on `main`.
- **Dependencies:** WN-T12.
- **Approach:** *Shipped* lines here; the Combat Decomposition's row and status; the Combat Design's §6 seams dated after the merge; BACKLOG — *`at_character_death()` restore block vs persistent wound tiers* DONE, *Dev characters keep a float `health.base`* closed by WN-T6, and *Character panel: Legend combat state*, *Survival loop tuning*, *Free Skill Points*, *Two-stage healing* annotated with what shipped; the System Map (one writer of hurt, and where); the Testing Reference (the new census, the `py` protocols); the Evennia Reference (`delay` with `persistent=True`, read in §3); the Alpha Runbook (how staff reads and mends a body now that `health.current` is not it; a longer stop of the server is announced, WN4; §7's tag if one was cut); the lessons batch; README; and OQ-SC1 marked closed where it is asked (the Skill-Check Forms and Body decompositions' open questions — WN7 answers it). **Before any of it:** BACKLOG is searched for the names the slice touched (`health`, `apply_health_damage`, `at_character_death`, `wound`, `Resilience`, `starv`, `bleed`, `heal`, `location`, `Hit Points`, `statue`, `collapse`) — lessons 238 and 408. The catalogue loop is run after the files are in the tree.
- **Commit:** `docs: close out wounds (Stage 5 slice WN)`

---

## 11. Open questions (each with what closes it)

OQ-WN1–OQ-WN4 are the design's and stand in the Combat Design §7: what a wound with no attack roll is tested against (the first slice that builds such a source); what a maimed head, chest or abdomen does to the living (ML's design); how the short description tells a blow's wound from starvation's (ML's design); whether a server start pushes the clocks on (ML's decomposition).

- **OQ-WN5 — The words.** The names of the locations as a player reads them, the four level words, the three state words, whether a running clock gets a word of its own in `status`, and the lines for being knocked out, waking, and the clock running out — all against the Tone Guide. **Closes at:** WN-T9's STOPP 0 for the lines, WN-T11's for the rest.
- **OQ-WN6 — Is a body knocked out by a wound a statue when its player logs out?** WN4 says a body with a running clock is not. WN-T9 proposes the same for unconsciousness, so that the time stored is always time in the world and a statue is never woken by an alarm; the other answer freezes the remaining time at logout, as `db.away_since` does for healing. **Closes at:** WN-T9's STOPP 0 (Adam).
- **OQ-WN7 — Is a tag cut at the merge?** L6.1 is still to deploy `alpha-20261122` before the first player makes a character (Body Decomposition OQ-BD4; Alpha Runbook §7), and a merge before that deploy moves the tag the runbook names. **Closes at:** WN-T12.

---

## 12. Consequences worth reading twice

1. **No play starts a test, a state or a clock before ML.** Starvation is the only road onto the path and it reaches none of them (WN5). WN-T8–WN-T10 are proven by unit tests and by `py`. A check run by `py` proves the function, not that a player can get there.
2. **The in-game checks of WN-T8 and WN-T10 maim and kill.** They are run on a character made for the purpose, never on one that carries anything, and never on the alpha server. *Maimed* has no cure until HL: on a development database it is removed by hand, and the checks say how.
3. **`py self.traits.health.current = …` does nothing after WN-T5**, on any character, old or new. Staff who mend or hurt a body by hand do it through `db.body_damage`; the runbook is changed in WN-T13, and until then this line is the note.
4. **Old characters keep a `health` trait that nothing reads.** It will say *20/20* for ever. The census of WN-T3 is what keeps that harmless.
5. **Between WN-T5 and WN-T7 the branch starves a body in half the time `main` does.** Nothing is merged between them.
6. **Death by starvation follows CON + SIZ after WN,** through the head's Hit Points. A small, tough body (CON 16, SIZ 8) had 32 `health` and five hours twenty; it has a head of 5 and three hours twenty.
7. **Natural healing is faster for a body hurt all over** — half the time of `main` for the half-starved body of WN10 — because seven locations mend at once. It is a change in balance that the mechanism brings with it, and BACKLOG *Survival loop tuning* is annotated with it.
8. **The web client is not changed, and what it shows is.** The `char` snapshot keeps `current`, `max` and `desc`; the numbers are the margin, *10/10* where it said *20/20*. `tests/js/test_pw_char.js` is read at WN-T5 for a number that was assumed.
9. **The clocks run while the server is down** (WN4, OQ-WN4). Nothing can start one before ML.
10. **All of BACKLOG *Two-stage healing* comes before ML,** as slice HL (Combat Decomposition Rev 17). `wounds.stop_clock` and `wounds.revive` are its two entry points and are written here with no caller.
11. **The statue is a snapshot** (Combat Design §4.2). One exception stands — time away heals (SL7) — and it is HL's to remove, with a faster table for time at the keyboard and healing as a service.
