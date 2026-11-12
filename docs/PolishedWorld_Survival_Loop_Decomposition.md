# PolishedWorld — Survival Loop Decomposition

> **Rev 1 · 2026-11-12** — first version. Decomposes roadmap **Stage 4.6 — Survival loop** (three first slices: Water, Foraging's natural healing, Rest's fatigue levels) into four components and eleven tasks, against live source read the same day (`main` at `0be751e`, tree `14c79e0`; Evennia 6.1.0; *Legend* core pp. 86–90). Four premises of the design notes did not survive the read and are answered by locks here: Rest slice 1 has no way back up without slice 2's `sleep` (SL10); natural healing on the tick alone is one hit point per twelve real hours *online* (SL7); `DeathWeakness` on `fatigue_rate` is near-inert once that rate scales a clock instead of a drain (SL12); and a waterskin on `condition` becomes mendable by `repair` and loses its sink (SL5).
> **Canonical:** `docs/PolishedWorld_Survival_Loop_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Design sources:** `docs/system_designs/PolishedWorld_Water_Design.md` (VP1, VP3, VQ6, VQ8, VQ9; departures N1, N2), `PolishedWorld_Foraging_Design.md` (RP8, RP-L4; departure R1), `PolishedWorld_Rest_Design.md` (NP1–NP3, NP14, NP15, NQ14; departures O1, O2, O5, O6); `docs/roadmap.md` *Stage 4.6*; BACKLOG *Fatigue-exhaustion consequence*, *`DeathWeakness` debuff → `fatigue_rate`*, *Waterskin `durability` → `condition` migration*, *Webclient: players and NPCs apart, and active conditions*. The notes' leanings were inputs; the locks below are the decisions.
**Status:** DECOMPOSED. Code follows on `feature/survival-loop`, cut from `main` with `--no-track`.
**Feature branch:** `feature/survival-loop` (one branch, one merge).
**Rough scope:** 11 tasks, ~4–5 sessions at 5 h/week (S1 1–1.5 · S2 1 · S3 2 · S4 0.5).
**Philosophy:** skynda långsamt — no new item, no new skill, no new ticker. One new command (`empty`), one new module (`world/fatigue.py`), one helper for water (`world/water.py`), and the survival tick doing two more things with the time it already has.

---

## 1. Why this feature

Three holes in the shipped loop, each small, each in the way of something larger (roadmap, *Why here*):

- **Health never comes back.** Only the survival tick writes health, downward (`world/survival_ticker.py:101–102`), and only respawn restores it (`typeclasses/characters.py:1375`). Stage 5 will write wounds on the same pool.
- **Fatigue does nothing.** The gauge drains one point a tick and no roll reads it; at zero nothing happens. Stage 5 reads Legend's levels, so they should exist before its design session.
- **A newcomer cannot drink at the spring.** `drink` accepts only a carried `Drink` (`commands/consumption_commands.py:91`); the alpha measures onboarding (decision (G)).

What the feature must not do is make an evening's play a chore. Rest Design NG1 is the test: fatigue bites the long day and the overloaded road, not the ordinary session.

## 2. Decisions locked 2026-11-12 (SL1–SL13)

**SL1 — One document, one branch.** This file; `feature/survival-loop`; locks `SL…`; tasks `S1.1…` (S1 Water, S2 Healing, S3 Rest, S4 close-out); mutations `SL-M…`. The slices keep the roadmap's order because S3 reads S2's tick helper.

**SL2 — Drink at the source.** `drink` with no argument, or naming a water source in the room, drinks there: thirst +45 (three draughts of the shipped 15 — VQ8), instant, the room told. With no argument and no source the answer stays *Drink from what?*. Logged as the shipped `consume` kind with `verb="drink"`, `item` the source's key and **no** `charges_left` (VQ9) — the report's reader of that field is checked in S1.1. A carried vessel is never chosen implicitly: bare `drink` means the source.

**SL3 — Kinds in one word, only *fresh* in the world.** Sources carry `water_kind` (default `"fresh"`, `autocreate=False`, so the seeded spring needs no migration). A vessel carries the kind of what is in it and loses it with the last draught. A filled vessel with no kind stored reads as fresh (read-time default, no backfill). `refill` refuses a vessel holding another kind — *empty it first*; `empty <vessel>` is new and pours it out. With one kind in the world the refusal is reachable only in unit tests and by `@set` in the protocol; that is accepted — the field is laid before the second kind (brine, Water slice 3), not after.

**SL4 — The vessel wears on `condition`.** `Drink` gains `DurableObject`. Each refill wears 8; a crafted waterskin starts at 96 / 80 / 48 / 24 by band (superior … shoddy), which is exactly today's 12 / 10 / 6 / 3 refills. The behaviour kept is the split on the dip *after* the last refill (`commands/foraging_commands.py:227–235`), now read from `is_broken`. `db.durability` is no longer read or written; waterskins in development databases start at 100 (no backfill — no instance is deployed, runbook §7).

**SL5 — A waterskin is not mended.** `repair` accepts any `DurableObject` and falls back to cloth and twine (`commands/repair_commands.py:103`, `:121`), so SL4 alone would let a gourd be patched to 100 — above a superior one's 96 — and close its sink. A vessel answers *You can't mend …* through one class flag (`mendable = False` on `Drink`, read in `repair` beside the `isinstance`). Pillar 1: the gourd that splits is replaced. Mendable vessels are the leather waterskin's question (Water slice 2).

**SL6 — Natural healing by Legend's table.** One hit point per 72 / 48 / 36 / 24 / 18 / 12 game hours for CON×2 of 01–10 / 11–30 / 31–50 / 51–70 / 71–90 / 91+ (core pp. 86–87; RP-L4). Whole points only; a per-character counter of game seconds carries the remainder (`db.heal_progress`). Nothing accrues while *Starving* or *Dehydrated* (p. 90), and the counter is zero at full health, so an old surplus never heals a new wound at once. One quiet line per point; no activity-log line (healing is not an economic event). At CON 6–15 that is a point per twelve real hours; at 16–18, nine.

**SL7 — Time away heals (B).** On the tick alone a five-hour-a-week player would heal 0.4 points a week — R1's hole left open. So the game time between unpuppet and puppet is credited to the same counter at login, unless the character logged out *Starving* or *Dehydrated* (the gauges are frozen while away, so the state at logout is the state throughout). This pulls forward the healing half of Rest NP20 and departs from Foraging RQ5's leaning (*a statue does not heal*); NP20, the later note, already says *online or away*. The fatigue half of NP19–NP20 (logout is sleep) stays in Rest slice 2. The world's clock stands still while the server is down, so downtime heals nobody.

**SL8 — Six levels, one table.** `world/fatigue.py` holds the bands — Debilitated 0, Exhausted 1–20, Wearied 21–40, Tired 41–60, Winded 61–80, Fresh 81–100 — with their penalties 50 / 40 / 30 / 20 / 10 / 0 (NP1; core p. 90). The word is read through `Character.fatigue_desc()`, the `health_desc()` precedent (`typeclasses/characters.py:687`), by `status`, the client's `survival` snapshot and the tick's warning, so characters made before this feature need no rewrite of their stored `descs`. The penalty is added in `physical_modifier()` beside overload's (NP2): the two sum, −70 at worst. Movement, Strike Rank and Combat Action effects are Stage 5's (NP-L5).

**SL9 — The awake clock replaces the drain.** The tick stops draining fatigue. It adds the tick's game seconds × `fatigue_rate` to `db.awake_seconds`; past (10 + CON) game hours each further whole hour rolls **Athletics** (NP-L1) with `physical_modifier()` and a further −20 while *Starving* or *Dehydrated*; a failure costs one level, twenty points (NP3). `ColdStress` and `HeatStress` keep their meaning: they spend the hours faster. The rolls never call `attempt_skill_improvement` — an involuntary roll that trained Athletics would be training by standing still. The overload step per room is unchanged and is the other way down (NP5).

**SL10 — The way up is the shipped `rest` (A).** Slice 1 has no `sleep`. `rest` stays as shipped — five points every ten seconds, to full, anywhere — and a rest that reaches full resets the awake clock. So in this slice a level is a few minutes' pause, not a night; the document says so rather than pretending otherwise. Rest slice 2 replaces the rows (NP6–NP9) and moves the reset to sleep (NP8); `REST_RESETS_CLOCK`'s one call site is where it does. Rejected: pulling `sleep`, the ceiling and logout-as-sleep in now — it doubles S3 and a stage the roadmap calls small.

**SL11 — Collapse at the bottom.** At Debilitated each survival tick rolls a Difficult (−20) Athletics test at the level's −50. A failure is a forced rest: the shipped recovery, which the character cannot end, until the gauge reaches `COLLAPSE_WAKE_AT = 41` (Tired) — about ninety real seconds, a placeholder that slice 2 replaces with NP14's *out of Debilitated, at the place's row*. Meanwhile moving, eating, drinking and every timed action are refused; looking and speaking are not. The state is `db.collapsed`, not only the `ndb` slot, so a reload or a relog does not wake anyone: the tick and `at_post_puppet` re-arm the recovery. Death clears it. No activity-log kind (NQ16 stays open). A collapsed character is defenceless, which is Stage 5's to design. This closes the open questions of BACKLOG *Fatigue-exhaustion consequence* (2026-10-18): length, eating, thresholds, the harder test, movement refused.

**SL12 — NQ14 ratified: death's chill is tiredness.** Respawn sets fatigue to 40 (Wearied), zeroes the awake clock and clears a collapse; `DeathWeakness` keeps its name, messages and 300 s with one mod, `fatigue_rate` +25 %, in place of the two on hunger and thirst. Read plainly: under SL9 that mod adds about 75 seconds to a clock measured in hours — the level is the consequence, the buff is its name and its timer until Rest slice 2 or Temperature give `fatigue_rate` more to do. The death message's weakness line gains *Rest mends the weariness that comes with it.* — a change to the player contract of death-consequence policy (v), ratified here at Adam's decision and recorded in the roadmap's decision log in the same commit.

**SL13 — The level is readable; the conditions list is not this feature.** BACKLOG *Webclient: players and NPCs apart, and active conditions* part (2) names Rest slice 1 as its trigger. Answered narrowly: `status` prints the level with its penalty, and the client's survival panel receives the word through the snapshot it already shows. A list of active buffs (text home, `conditions` in `char`, pushes) stays in BACKLOG on its other trigger.

## 3. Verified source anchors (read 2026-11-12, `main` at `0be751e`)

| Anchor | Where | What it establishes |
| --- | --- | --- |
| `CmdDrink` | `commands/consumption_commands.py:70`; the Drink-only check `:91`; restore `:103`; `consume` record `:107` | SL2's branch goes before `:91`; the record's shape. |
| `CmdRefill` | `commands/foraging_commands.py:178`; room scan `:198–202`; split on the dip `:227–235`; `refill()` `:239`; fill line `:243` | The scan S1.1 moves into `world/water.py`; the behaviour SL4 keeps. |
| `forage` skips water | `commands/foraging_commands.py:90` | Third reader of `is_water_source`; unchanged. |
| `ResourceNode.is_water_source` | `typeclasses/resources.py:47`; wording `:135–136` | Where `water_kind` goes; the fresh line stays. |
| The spring | `world/prototypes.py:117–125` (aliases `spring`, `water`); seed `world/seed_data.py:202–203` | `drink water` and `drink spring` both resolve; the only source in the world. |
| `Drink` | `typeclasses/consumables.py:28–57` (`refill()` `:44–53`, `is_worn_out()` `:55–57`) | `db.durability`'s only reader and writer besides the recipe. |
| Waterskin recipe | `world/recipes.py:57–62` (band table), `:154` (the write); prototype `world/prototypes.py:259–271` | SL4's table; four values to re-key. |
| `DurableObject` | `typeclasses/durable.py:31` (`apply_wear` `:43`, `is_broken`, `get_display_desc`) | What `Drink` inherits; `look` gains the condition line. |
| `repair`'s gate | `commands/repair_commands.py:103`, default materials `:121` | SL5. |
| The tick | `world/survival_ticker.py:20` (`BASE_RATES`), `:57` (`_deplete_character`), `:65` (the drain), `:73`, `:106`, `:129` | Fatigue leaves `BASE_RATES`; the warning loop needs its own gauge tuple. |
| Tick interval and clock | `server/conf/at_server_startstop.py:27` (600 s); `server/conf/settings.py:55` (`TIME_FACTOR = 4`) | A tick is 40 game minutes. |
| Game time | `world/gametime_utils.py:88` (`get_absolute_gametime`) | The stamp both counters read. |
| Health | gauge `typeclasses/characters.py:336–352`; `apply_health_damage` `:1216`; max `world/chargen.py:172` | Healing writes `health.current` upward; damage stays at the chokepoint. |
| Fatigue gauge | `typeclasses/characters.py:319–333` (keys 0/20/40/60/80/95) | The stored `descs` SL8 stops reading. |
| `physical_modifier()` | `typeclasses/characters.py:634`; `world/encumbrance.py:63`, `:70`; census `tests/test_encumbrance.py:988` | The seam; the six rolls need no edit. |
| Rest | `start_resting` `:1412`, `stop_resting` `:1460`, `_rest_tick` `:1753` (`:1787` the gain); `CmdRest` `commands/consumption_commands.py:121` | SL10's reset site; SL11's recovery reuses the gain. |
| Movement hook | `typeclasses/characters.py:1487`, `:1510` | The first refusal goes before the interrupt (O5). |
| Puppet hooks | `at_post_unpuppet` `:475` (bails while sessions remain), `at_post_puppet` `:500` | SL7's stamp and credit; SL11's re-arm. |
| Respawn | `typeclasses/characters.py:1313`, `:1375`, `:1398` | SL12's three writes. |
| `DeathWeakness` | `world/survival_buffs.py:94`, flavor `:121`, mods `:135–136`; message `world/death_contract.py:132` | SL12. |
| Readers of the word | `commands/character_commands.py:74–76`; `world/client_state.py:144–150`; `world/survival_ticker.py:129` | SL8's three readers. |
| Censuses that will move | `tests/test_client_state.py:895` (`TestPushCensus`), `:957` (the tick's write row) | Every task that adds a push or a write updates the count in the same commit (lesson 183). |
| Activity log | `world/activity_log.py:60` (`KINDS`) | No new kind (SL2, SL6, SL11). |

Line numbers are re-read at each task (live source wins).

## 4. Dependency graph

```
S1.1 world/water.py + drink at the source
  └─ S1.2 water_kind on sources and vessels + empty
S1.3 Drink on condition; repair refuses a vessel        (independent of S1.1–S1.2)
S2.1 tick time helper + natural healing on the tick
  └─ S2.2 time away credited at login
S3.1 world/fatigue.py: levels, fatigue_desc(), status, snapshot, warning
  ├─ S3.2 the penalty in physical_modifier()
  └─ S3.3 the awake clock (needs S2.1's helper); rest to full resets it
       └─ S3.4 collapse
            └─ S3.5 respawn at Wearied; DeathWeakness; the death message
S4.1 merge → S4.2 docs close-out
```

## 5. Component S1 — Water

### Task S1.1 — Drink at the source
- **Goal:** A character with no vessel can drink at the spring.
- **Dependencies:** None.
- **Approach:** `world/water.py`: `source_in(room)` returns the first `ResourceNode` with `is_water_source` in the room or `None` — the scan `refill` makes today, moved so `drink` and `refill` share it (and so Stage 6's terrain water has one place to answer, VP8). `CmdDrink`: no argument → `source_in`; an argument that resolves to a water source → that source; otherwise today's path unchanged. `SOURCE_DRAUGHTS = 3` × the default `restore_amount`. Record, messages to the drinker and the room, `client_state.push(caller, "survival")`. Help text for `drink` rewritten. Board: the *Healing over time…* card moves to *In progress* in a docs commit on `main` when the branch is cut.
- **Testing** (`tests/test_water.py`, `EvenniaCommandTest`): bare `drink` beside a spring raises thirst by 45 and clamps at max; with no spring, *Drink from what?* and thirst unchanged; `drink spring` and `drink water` both work; a carried full waterskin is untouched by bare `drink` (its charges are the receipt); `drink waterskin` beside the spring still drinks the skin; the log line has the source's key and no `charges_left`; the report reads the line without error; `refill` still finds the spring through the helper. In game: `@py` thirst to 10, `drink`, `status`.
- **Mutations:** SL-M1 bare `drink` picks a carried vessel; SL-M2 restore 15; SL-M3 keep `charges_left`; SL-M4 `source_in` returns any `ResourceNode`.
- **Commit:** `feat(survival-loop): drink at a water source; world/water.py holds the room scan`

### Task S1.2 — The kind, and `empty`
- **Goal:** Water has a kind on sources and in vessels, with one kind in the world.
- **Dependencies:** S1.1.
- **Approach:** `ResourceNode.water_kind = AttributeProperty("fresh", autocreate=False)`; `Drink.water_kind = AttributeProperty(None, autocreate=False)` with `held_kind()` (None when empty, stored kind or `"fresh"` when not). `refill`: refuse when the vessel holds another kind; set the kind on a fill; the fill line names fresh as today. `CmdDrink`: the kind clears when the last draught goes. `CmdEmpty` (`empty <vessel>`): carried refillable `Drink`, charges to 0, kind cleared, no wear, the room told; an empty vessel answers that it is empty.
- **Testing** (`tests/test_water.py`): a fill stamps `fresh`; a vessel filled before this task (charges 3, no kind) reads fresh and refills; a vessel `@set` to `brine` is refused at the spring and accepted after `empty`; the last draught clears the kind; `empty` on a non-vessel and on an empty vessel. In game: `refill`, `@set waterskin/water_kind = brine`, `refill` (refused), `empty waterskin`, `refill`.
- **Mutations:** SL-M5 refill ignores the kind; SL-M6 `empty` leaves the kind; SL-M7 `held_kind()` returns the stored kind on an empty vessel; SL-M8 `empty` wears the vessel.
- **Commit:** `feat(survival-loop): water kinds on sources and vessels (fresh only); empty <vessel>`

### Task S1.3 — The vessel on `condition`
- **Goal:** The waterskin wears on the shared axis, with the refill counts it has today, and is not mended.
- **Dependencies:** None (ordered last in S1 so S1.1–S1.2 touch `refill` first).
- **Approach:** `class Drink(DurableObject, Object)`; `REFILL_WEAR = 8`; `refill()` calls `apply_wear`; `is_worn_out()` goes, `refill`'s split reads `is_broken`. `_WATERSKIN_STATS_BY_BAND` becomes band → (`max_charges`, start condition) 96/80/48/24 and the recipe writes `obj.condition`. `mendable = False` on `Drink`; `repair` refuses before reading materials. A test pins `start // REFILL_WEAR` to 12/10/6/3 so the table and the constant cannot drift apart.
- **Testing** (`tests/test_water.py`, and the recipe's existing tests re-keyed — count the sites that read `durability` first, lesson 183): a serviceable skin survives exactly ten refills and splits on the eleventh dip; `look` shows the condition line; `repair waterskin` is refused with cloth and twine in hand and both kept; a `Drink` with a stale `db.durability = 0` refills (the attribute is not read). In game: craft a waterskin, `look`, refill and drink through its life.
- **Mutations:** SL-M9 wear on drink instead of refill; SL-M10 split before the last fill; SL-M11 drop `mendable`; SL-M12 wear 10.
- **Commit:** `refactor(survival-loop): Drink wears on condition (8 a refill); a vessel is not mended`

## 6. Component S2 — Healing

### Task S2.1 — Natural healing on the tick
- **Goal:** An online character who is neither starving nor dehydrated regains hit points at Legend's rate.
- **Dependencies:** None.
- **Approach:** `world/survival_ticker.py`: `_tick_game_seconds(char)` reads `get_absolute_gametime()` against `char.ndb.survival_tick_at` and returns the difference (0 on the first tick after a puppet or a reload — at most one tick is lost, never gained), then stamps. `world/healing.py`: `interval_for(con)` (the table, in game seconds), `accrue(char, game_seconds)` → adds to `db.heal_progress`, grants whole points, carries the remainder, zeroes at full health, returns the points granted. Called from `_deplete_character` after `_apply_survival_conditions`, so a condition applied this tick already stops it. One line per point, `client_state.push(char, "char")` when a point lands.
- **Testing** (`tests/test_healing.py`): the table's six rows at their edges (CON 5, 6, 15, 16); a counter one second short grants nothing and the next second grants one; two intervals at once grant two and stop at max; *Starving* accrues nothing and keeps what was there; full health zeroes the counter; a float `health.base` (BACKLOG *Dev characters keep a float `health.base`*) still gains whole points; `_tick_game_seconds` is 0 on the first call and the clock's difference on the second. In game: `@py` health down 2, `@py self.db.heal_progress = <interval − 1>`, wait a tick.
- **Mutations:** SL-M13 ignore *Dehydrated*; SL-M14 drop the remainder; SL-M15 no zero at full; SL-M16 first tick credits since server start; SL-M17 heal past max.
- **Commit:** `feat(survival-loop): natural healing on the survival tick (Legend pp. 86-87, CON x2)`

### Task S2.2 — Time away heals
- **Goal:** The game time a character spent as a statue is credited to healing at login.
- **Dependencies:** S2.1.
- **Approach:** `at_post_unpuppet` (after the multisession bail): `db.away_since = get_absolute_gametime()`, or `None` if *Starving* or *Dehydrated*. `at_post_puppet`: if a stamp is there, `healing.accrue(self, now − stamp)`, clear it, and say one line when points were gained. The stamp is cleared on death too. OQ-S1 is read first.
- **Testing** (`tests/test_healing.py`): unpuppet, advance the game clock by two intervals, puppet → two points; logged out *Dehydrated* → none; a second session leaving stamps nothing; no stamp → nothing and no error; the tick after login does not credit the same span again (S2.1's first-tick zero is the receipt). In game: `@py` health down, `@py self.db.heal_progress = <interval − 60>`, quit, wait, log in.
- **Mutations:** SL-M18 stamp before the bail; SL-M19 keep the stamp after crediting; SL-M20 stamp while *Starving*.
- **Commit:** `feat(survival-loop): time away is credited to natural healing at login`

## 7. Component S3 — Rest

### Task S3.1 — The levels and their word
- **Goal:** The fatigue gauge reads as Legend's six levels everywhere a player sees it.
- **Dependencies:** None.
- **Approach:** `world/fatigue.py`: `LEVELS` (upper bound, word, penalty), `level_for(value)`, `penalty_for(value)`, `LEVEL_POINTS = 20`. `Character.fatigue_desc()`. `at_object_creation`'s `descs` re-keyed to the same table (a test pins that the two agree, so new characters' `trait.desc()` cannot contradict the reader). `status` prints the word and, below Fresh, `−N% to physical tests`; `survival_snapshot` and the tick's warning read `fatigue_desc()`; the warning's bucket index for fatigue comes from `level_for`.
- **Testing** (`tests/test_fatigue.py`): both sides of every boundary (0/1, 20/21 … 80/81); a character carrying the old `descs` (keys …/95) reads the new words; `status` at 35 shows *wearied* and *−30%*, at 100 no penalty text; the snapshot carries the word; the warning fires once on 61 → 60 and not on 60 → 59.
- **Mutations:** SL-M21 `<` for `<=` at a bound; SL-M22 snapshot reads `trait.desc()`; SL-M23 penalty text at Fresh.
- **Commit:** `feat(survival-loop): Legend's six fatigue levels on the gauge; status and the client read one table`

### Task S3.2 — The penalty
- **Goal:** Every physical roll is harder by the level's penalty.
- **Dependencies:** S3.1.
- **Approach:** `physical_modifier()` returns overload's term plus `−fatigue.penalty_for(current)`; the docstring's *Later penalties…* sentence becomes a statement of both terms. No call site changes.
- **Testing** (`tests/test_fatigue.py`; `tests/test_encumbrance.py`'s fixtures set fatigue explicitly where they assert an exact modifier — count them first): 0 at Fresh; −30 at 40; −70 overloaded at 0; one command-level test through craft that the roll's modifier moved (the six sites are already pinned by `TestRollCensus`). In game: `@py` fatigue 40, a craft, the roll line.
- **Mutations:** SL-M24 fatigue replaces overload instead of adding; SL-M25 sign flipped.
- **Commit:** `feat(survival-loop): fatigue levels add their penalty in physical_modifier()`

### Task S3.3 — The awake clock
- **Goal:** Time awake, not the tick, tires a body; a full rest starts the day again.
- **Dependencies:** S2.1 (the helper), S3.2.
- **Approach:** `fatigue` leaves `BASE_RATES`; the warning loop gets its own gauge tuple. `world/fatigue.py`: `advance_clock(char, game_seconds)` adds `buffs.check(game_seconds, "fatigue_rate")` to `db.awake_seconds`; `tests_due(char)` counts whole hours past `(10 + CON) × 3600` not yet rolled (`db.awake_tests`); each rolls `skill_check(athletics.value, physical_modifier() + need_penalty)`; a failure subtracts `LEVEL_POINTS` and says so. `_rest_tick`: on reaching max, `fatigue.reset_clock(char)`. The census row for the tick's writes (`tests/test_client_state.py:957`) is updated here.
- **Testing** (`tests/test_fatigue.py`, `randint` pinned): no drain on a tick; no roll one second before the threshold, one roll an hour past it, two after two hours in one call; a failure costs 20 and clamps at 0; *Starving* adds −20 to the roll; `ColdStress` shortens the day; a pinned success leaves the Athletics improvement cooldown ready (no improvement attempted); rest to full zeroes clock and count, a rest stopped at 95 does not. In game: `@py self.db.awake_seconds = <threshold − 60>`, wait ticks, read the gauge; `rest` to full, read the clock.
- **Mutations:** SL-M26 keep the drain; SL-M27 roll every tick past the threshold; SL-M28 reset on any rest tick; SL-M29 ignore `fatigue_rate`; SL-M30 call improvement.
- **Commit:** `feat(survival-loop): the awake clock replaces the fatigue drain; rest to full resets it`

### Task S3.4 — Collapse
- **Goal:** A body at the bottom can fall where it stands, and stays down until it has rested.
- **Dependencies:** S3.3.
- **Approach:** In the tick, after the clock: at `current <= 0` and not collapsed, a Difficult roll; on failure `fatigue.collapse(char)` — interrupt the slot, set `db.collapsed`, start a `collapse` timed action whose tick is the rest gain and which ends at `COLLAPSE_WAKE_AT`, clearing the flag. `at_pre_move` returns False with a line while collapsed, before the interrupt (OQ-S2 decides which `move_type`s are refused; staff teleport is not). `eat`, `drink`, `rest` and `empty` refuse; other timed actions are refused by the slot. The tick and `at_post_puppet` re-arm a collapse whose slot is gone; `at_character_death` clears the flag. Room lines for the fall and the waking; `push_room_soon`.
- **Testing** (`tests/test_fatigue.py`): pinned failure at 0 collapses, pinned success does not, at 1 no roll; a move is refused and the character is still in the room, a teleport is not; `eat`/`drink` refused with the food kept; recovery ends at 41 with the flag cleared and movement allowed; the slot wiped (a reload) → the next tick re-arms; death while collapsed leaves no flag. In game, two characters in the room: `@py` fatigue 0, wait a tick (or call the tick by `@py`), try to walk, wait it out.
- **Mutations:** SL-M31 the refusal after the interrupt; SL-M32 wake at 1; SL-M33 flag only in `ndb`; SL-M34 roll without the −20; SL-M35 death keeps the flag.
- **Commit:** `feat(survival-loop): collapse at Debilitated - a forced rest that refuses movement`

### Task S3.5 — Death's chill is tiredness
- **Goal:** A respawned body is Wearied, and the death message says what mends it.
- **Dependencies:** S3.4.
- **Approach:** `at_character_death`'s restore block: fatigue 40, clock reset, collapse cleared. `DeathWeakness`: one `fatigue_rate` mult 0.25; docstring, comments and `flavor` rewritten (the prose that says *hunger and thirst* — the false-claims loop is run over `survival_buffs.py`, `characters.py` and `death_contract.py`). `death_message()` and `help death` gain the line.
- **Testing** (`tests/test_death_contract.py`, `tests/test_fatigue.py`): respawn from 100 and from 0 both read 40; `buffs.check(100, "fatigue_rate")` is 125 and `hunger_rate` is 100 under the buff; the message and the help entry carry the new line; the clock is 0. In game: the death protocol of Testing Ref, then `status`.
- **Mutations:** SL-M36 leave fatigue; SL-M37 keep the hunger mod; SL-M38 drop the line from help only.
- **Commit:** `feat(survival-loop): respawn at Wearied; DeathWeakness moves to fatigue_rate; the death message says rest mends it`

## 8. Component S4 — Close-out

### Task S4.1 — Merge
- **Goal:** `feature/survival-loop` on `main` by merge commit, the whole suite OK on the merge result.
- **Dependencies:** S1.1–S3.5 received, every mutation killed, every protocol run.
- **Approach:** `git merge-tree` first; the full suite on the merge result (`ForkTestRunner --parallel auto`, `"#10"` stashed, the count predicted from `def test_`); Node and art suites unchanged; PR, merge commit, branch deleted; a new `alpha-YYYYMMDD` tag only if L6.1 has not deployed by then, or as the instance's first live tagged deploy if it has (LM10).
- **Commit:** the merge commit.

### Task S4.2 — Documentation
- **Goal:** Every document that describes these three holes as open describes them as closed.
- **Dependencies:** S4.1.
- **Approach:** this document DONE with records; roadmap (Stage 4.6 ✅, *Next* the newcomer's economy note); BACKLOG (*Fatigue-exhaustion consequence*, *`DeathWeakness` → `fatigue_rate`*, *Waterskin migration* DONE; the three design notes' slice-1 lines marked shipped; calibration entries filed per OQ-S3); Testing Ref (the protocols); Evennia Ref if a hook's behaviour was learned (OQ-S1, OQ-S2); Lessons; the board card to *Done*; the catalogue and prose loops.
- **Commit:** `docs: close out the survival loop (Stage 4.6)`

## 9. Records

| Task | Commit | Tree | Date | Suite after |
| --- | --- | --- | --- | --- |
| (base) | `0be751e` | `14c79e0` | 2026-11-12 | 1447 (`def test_`), catalogue loop 57/0 |

## 10. Open questions (each with the task that closes it)

- **OQ-S1 — Does a cold shutdown run `at_post_unpuppet`?** SL7's stamp is written there. Read in Evennia 6.1.0 before S2.2; if not, the stamp is also written from `at_server_shutdown`.
- **OQ-S2 — Which `move_type`s does a collapse refuse?** Exits and teleports reach `at_pre_move` with different values; read live at S3.4. Staff teleport and `move_hooks=False` paths stay open.
- **OQ-S3 — Calibration.** 45 at the source, wear 8, `COLLAPSE_WAKE_AT = 41`, the healing rows: none is tuned by play. Filed at S4.2 with alpha close-out as the trigger.
- **OQ-S4 — The lines.** The healing line, the collapse and waking lines and the death message's sentence are written against `docs/PolishedWorld_Tone_Guide.md` at their tasks.
- **OQ-S5 — Tests that pass through the drain.** How many tests rely on a tick lowering fatigue, or on `DeathWeakness`'s hunger rate, is counted at S3.3 and S3.5 before the mechanism changes (lesson 183).

## 11. Consequences worth reading twice

- **An idle character no longer tires.** Today a hundred ticks empty the gauge. After S3.3 the gauge moves only by a failed hourly test late in a long day, by walking overloaded, and by death. That is the design (NG1), and it means most players first meet the levels through overload or a respawn.
- **In this slice a level costs minutes.** `rest` is unchanged (SL10), so −30 % is a two-minute pause away. The feature ships the reading of fatigue — the words, the penalty, the bottom — and leaves its price to Rest slice 2.
- **A collapse cannot be escaped by logging out, and cannot kill by itself.** The flag persists and the gauges freeze for a statue; but hunger and thirst keep draining for the ninety seconds a collapsed character is online, and a winter night keeps its cold.
- **Healing is slow on purpose.** Two points a real day is Legend's rate at the 4× clock. It makes First Aid and the poultice (Foraging slice 3) worth making; it does not make thirst damage trivial.
- **The spring is free and the waterskin still matters.** Forty-five at the source against fifteen a draught carried: the vessel is what lets a character leave the brook.
