# PolishedWorld — Arrival Decomposition

> **Rev 2 · 2026-11-14** — **DONE.** `feature/arrival` is merged to `main` as `185a47a` (PR #30, merge commit, tree `b21cfaf`, the tree `git merge-tree` predicted) and tagged **`alpha-20261114-2`** (annotated), which L6.1 now deploys in place of `alpha-20261114`: L6.1 had not run, and that day's tag name was taken, so the second tag of the day carries `-2` (AV-T4's lock A1). *Shipped* lines for AV-T1–AV-T5; §3's AV4 row gains what the re-read found (a hookless move skips the rooms' hooks too, and death pushes both rooms itself), §7's five questions are closed, §8 gets its rows and §9 one consequence. Written with the Newcomer note Rev 3, roadmap Rev 79, runbook Rev 10, Evennia Ref Rev 34, Testing Ref Rev 25, Lessons Rev 8 (333–341), BACKLOG Rev 111, the series handoff Rev 17 and README Rev 59, in one commit.
> **Rev 1 · 2026-11-14** — first version. Decomposes the small slice of `docs/system_designs/PolishedWorld_Newcomer_Design.md` (Rev 2) that can ship now — its two departure rows, **Z1** (a new character's first room is Evennia's Limbo) and **Z2** (the chore `water` names a well no room has) — into three code tasks and a close-out, against live source read the same day (`main` at `c0a8a0a`, tree `a144dcd`; Evennia 6.1.0, read from the wheel). Z1 was confirmed on Adam's dev instance before this was written: `START_LOCATION`, `DEFAULT_HOME` and `DEFAULT_RESPAWN_DBREF` printed `#2 #2 None`, and a fresh account's character finished creation in *Limbo* under Evennia's stock welcome text (§3, the receipt). One thing was found while reading that the design note did not weigh, and Adam decided it the same day (AV3): with `DEFAULT_RESPAWN_DBREF` unset, a dead character respawns at its `home`, which is Limbo too. With roadmap Rev 78, README Rev 58, the Newcomer note Rev 2 and the series handoff Rev 16.
> **Canonical:** `docs/PolishedWorld_Arrival_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Design source:** `docs/system_designs/PolishedWorld_Newcomer_Design.md` §6 (Z1, Z2), NCP3, NCP4, NCQ5; `docs/roadmap.md`, parallel backlog, *The newcomer's economy*.
**Status:** DONE (Rev 2). AV-T1 `10b86bc`, AV-T2 `b8bc0ad`, AV-T3 `652cc27` on `feature/arrival`; merged as `185a47a` (PR #30); tagged `alpha-20261114-2`.
**Feature branch:** `feature/arrival` (one branch, one merge).
**Rough scope:** 3 code tasks and a close-out, one session at 5 h/week (AV-T1 1 h · AV-T2 0.5 h · AV-T3 0.25 h · close-out 1 h). Small because every seam exists: the seeder already finds a room by its seed id, character creation already has one node where every write happens, and death already moves a character without hooks.
**Philosophy:** skynda långsamt — one resolver, one call in one node, two strings. No new setting, no new command, no migration, no backfill.

---

## 1. Why this feature

The alpha measures onboarding (roadmap decision (G1)): that a newcomer gets from character creation to a first craft on what the game itself says. Today the first thing the game says after *"Your character is made"* is Evennia's welcome to developers, in a room called Limbo that the seed data calls admin space (`world/seed_data.py:74–77`). The world is one unexplained exit away. The alpha instance is not up yet (L6), so fixing this now costs no redeploy and no migration: the tag L6.1 checks out simply carries it.

The same reading found that death has the same hole. A character's `home` is Limbo, and `home` is where a body wakes when `DEFAULT_RESPAWN_DBREF` is not set — a per-instance line that lives in no committed file. One forgotten line on the alpha box and every death ends in admin space.

The third task is two strings: a chore that walks to a well the world does not have.

---

## 2. Decisions locked 2026-11-14 (AV1–AV8)

**AV1 — The move happens in character creation's last node, not in `START_LOCATION`.** `node_done` is where every write of a finished character happens (`world/chargen_menu.py:338–385`), and it is the only place that knows the character is made. *Alternative rejected:* `START_LOCATION` pointed at the temple. It would stand every unmade character in the world as a statue and run the creation menu in front of whoever is in the temple; the Character Creation decomposition's CC3.2 keeps the menu closed for exactly that reason — an unmade character is not let into the world (`world/chargen_menu.py:350–353`). It would also need a dbref per instance, which the seeder's design avoids.

**AV2 — The arrival room is found by seed id.** One constant, `ARRIVAL_ROOM = "alpha.room.temple"`, beside the room it names in `world/seed_data.py`, and one resolver that calls `world.seeding.find_seeded` (`world/seeding.py:88–102`). No dbref, no setting. A later building pass that moves the temple changes one line.

**AV3 — `home` is set with the move (Adam, 2026-11-14).** The same step writes `character.home`. `_get_respawn_location` falls back to `home` when no override and no setting answers (`typeclasses/characters.py:1343–1351`), so a made character can never respawn in Limbo, whatever the instance's settings say. `DEFAULT_RESPAWN_DBREF` keeps its place in the order and becomes an override rather than a requirement.

**AV4 — The move runs without hooks, as death's does.** `move_to(room, quiet=True, move_hooks=False)`, the form `at_character_death` already uses (`typeclasses/characters.py:1455`). The project's `at_post_move` looks at the room (`:1681–1691`), and the menu's `cmd_on_exit="look"` looks again when it closes (`world/chargen.py:344–351`): with hooks, the newcomer's first screen would show the temple twice. Without them it shows once, after the closing line.

**AV5 — The move comes before the client push.** `node_done` pushes every webclient domain with the final values (`world/chargen_menu.py:380–381`). The Location panel is one of them, so the move and the `home` write land before that push, and the panel's first real content is the temple.

**AV6 — No room found means no move, a logged line, and a finished character.** On a database without the seed — every unit-test database, a scratch game dir — `find_seeded` returns `None`. The character stays where it is, `home` is untouched, one line goes to the server log, and creation completes exactly as it does today. Arrival never blocks a character from being made.

**AV7 — No backfill.** Characters made before this ships keep their location and their `home` (the Character Creation decomposition's decision 10, the same rule). The alpha database is created fresh at L6; the dev databases' characters are staff's.

**AV8 — No arrival line to the room.** Others in the temple see nothing when a newcomer appears. The Newcomer note's arrival line (§15) names a character to a room, and Names Design resolves every such name per reader (UP10); it ships with Names' slice, not here.

---

## 3. Verified source anchors (read 2026-11-14, `main` at `c0a8a0a`)

| Anchor | Where | What it establishes |
| --- | --- | --- |
| `START_LOCATION = "#2"`, `DEFAULT_HOME = "#2"` | `evennia/settings_default.py:625`, `:623` (6.1.0); neither is set in `server/conf/settings.py` | Where a new character is created and what its `home` is. |
| character created at `START_LOCATION` | `evennia/accounts/accounts.py:962` (6.1.0) | The statue stands in Limbo until first login. |
| Limbo's description | `evennia/server/initial_setup.py:29`, `:115` (6.1.0) | Evennia's stock welcome; the project never rewrites it. |
| the one way out | `world/seed_data.py:160–161` (exit `temple`, one-way; comment `:74–77`) | Limbo is admin space by design. |
| pending stamp | `typeclasses/accounts.py:142–153` → `world/chargen.py:266–286` | Every character made for an account meets the menu. |
| the menu | `world/chargen.py:289–353`; `auto_quit=False`, `cmd_on_exit="look"` at `:344–351` | The closing `look` is the newcomer's first room text. |
| `node_done` | `world/chargen_menu.py:338–385`: guard `:358`, refusals `:360–376`, the flag `:378`, baseline `:379`, push `:380–381`, closing text `:382–385` | The one place a made character is written; AV1, AV5. |
| `find_seeded(seed_id)` | `world/seeding.py:88–102`; `SEED_CATEGORY` `:72` | Returns the object or `None`; on duplicates it warns and uses the first. |
| the temple's seed row | `world/seed_data.py:80–92` (`alpha.room.temple`) | AV2's target. |
| respawn order | `typeclasses/characters.py:1333–1351` | override → setting → `home` → location; AV3. |
| death's move | `typeclasses/characters.py:1455` (`quiet=True, move_hooks=False`) | AV4's precedent. *(Rev 2)* Read whole, the precedent is two steps: the move, and the room pushes after it (`:1495–1503`), because a hookless move also skips `Room.at_object_leave` and `Room.at_object_receive` (`typeclasses/rooms.py:377–429`), which push every other viewer's room list. Found at the re-read before AV-T1; `arrive()` does both. |
| the project's `at_post_move` | `typeclasses/characters.py:1681` (looks; does not call `super()`) | Why hooks would double the look. *(Rev 2)* The method runs to `:1731`, not `:1713`, and ends with a survival push; OQ-AV2's answer does not change. |
| `at_pre_move` | `typeclasses/characters.py:1644` | Interrupts timed actions, refuses a collapsed walk; not run under AV4, and a character in the menu has neither. |
| the chore | `commands/work_commands.py:184–193`; the two lines `:189–190` | Z2. |
| the spring | `world/seed_data.py:202–203`; room text `:121–125` | The world's one water source, at the Brook. |
| the chore's origin | `docs/GameGold_Design.md:376` (*Fetch water from the well*) | A design line older than the seeded world; left as history. |
| tests that exist | `tests/test_chargen_menu.py` (`node_done` paths `:242–296`), `tests/test_seeding.py` (`SeedingBase` `:70–76`, `seed_world(limbo=self.room1)`), `tests/test_work_command.py`, `tests/test_death_contract.py` | Where the new tests sit beside. |

**The receipt (Adam's dev instance, work, 2026-11-14 18:5x).** `@py` printed `#2 #2 None`. A new account `arrivaltest`, made with the runbook's `Account.create` line, logged in, went through the menu as a weaver and read, after the closing line: *Limbo*, Evennia's welcome text, *Exits: north and temple*. The `arrivaltest` account is still on that database.

Re-read every row before the first task; live source wins.

---

## 4. Dependency graph

```
AV-T1 (resolver + constant) ──> AV-T2 (node_done calls it) ──┐
AV-T3 (the chore's two lines) ───────────────────────────────┼──> AV-T5 (merge) ──> AV-T4 (docs, tag)
```

AV-T3 is independent of the other two.

---

## 5. Component 1 — Arrival

### Task AV-T1 — `ARRIVAL_ROOM` and `arrive()`
- **Goal:** One function that puts a character in the arrival room and makes it the character's home, with no caller yet.
- **Dependencies:** None.
- **Approach:** `world/seed_data.py`: `ARRIVAL_ROOM = "alpha.room.temple"` directly under `ROOMS`, with a comment naming AV2 and that the value must be a `seed_id` in `ROOMS`. New module `world/arrival.py`: `arrival_room()` returns `find_seeded(seed_data.ARRIVAL_ROOM)`; `arrive(character)` resolves the room, and if there is one sets `character.home = room` and calls `character.move_to(room, quiet=True, move_hooks=False)`, returning the room; if there is none it logs one line with `logger.log_warn` naming the seed id and the character, and returns `None`. A character already in the room still gets its `home` set and is not moved. Docstrings carry AV3 (why `home`), AV4 (why no hooks) and AV6 (why a miss is quiet). Error handling: `find_seeded` never raises — a duplicated seed tag is warned about and the first match used (`world/seeding.py:96–102`) — but `move_to` can return `False`; `arrive` then logs a line, leaves `home` as it has just set it, and returns `None`. Any exception inside `arrive` is caught, logged with `logger.log_trace` and turned into `None`: a broken seed must not stop a character being made (AV6).
- **Testing** (`tests/test_arrival.py`, on `SeedingBase`'s pattern — `seed_world(limbo=self.room1)`): `ARRIVAL_ROOM` is a `seed_id` in `ROOMS`; `arrival_room()` is the seeded temple, and `None` before seeding; `arrive(char)` leaves `char.location` and `char.home` both the temple and returns it; `arrive` on an unseeded database returns `None` and changes neither; `arrive` when already in the temple sets `home`; `_get_respawn_location()` is the temple after `arrive`, with no setting; with `db.respawn_location` set, the override still wins; `override_settings(DEFAULT_RESPAWN_DBREF=…)` still wins over `home`; no `look` text is sent by `arrive` (the hook did not run); with `move_to` patched to return `False`, `arrive` returns `None` and does not raise; with `find_seeded` patched to raise, the same. `world.arrival` and `world.chargen_menu` import in one test (the cycle check).
- **Mutations (AVM1–AVM4):** skip the `home` write (the respawn test must fail); move with hooks (the no-look test must fail); raise on a miss (the unseeded test must fail); resolve by key `"Old Temple"` instead of the seed id (a test that renames the room's key and still arrives must fail).
- **In-game check:** none; no caller.
- **Commit:** `feat(arrival): ARRIVAL_ROOM and arrive() — the resolver, no caller yet`
- **Shipped (Rev 2):** `10b86bc` on `feature/arrival`, tree `8dd7110` (the tree the sandbox commit and a `git am` on a fresh clone both produced). One change from the approach above, taken at STOPP 1 (Adam: *kör*): after a move, `arrive()` pushes the room left and the room entered with `client_state.push_room_soon`, as `at_character_death` does after its own hookless move (§3, death's move); nothing is pushed when the character already stands in the room. `TestPushCensus.SITES` in `tests/test_client_state.py` gains `("world/arrival.py", "arrive", "push_room_soon"): 2` in the same commit — the census pins every push call in production code (lessons 312, 320). `world/seed_data.py`'s module docstring names `world/arrival.py` among its readers. OQ-AV1: the plain assignment saves; a `refresh_from_db()` reads `db_home` as the temple. Tests: `tests/test_arrival.py` (17), on `seed_world(limbo=self.room1)`. AVM1–AVM4 killed, and **AVM4b** (the two pushes removed) killed by the push test and the census. Sandbox: six neighbour modules 206 OK, the whole suite 1624 OK. Work machine: the six modules 206 OK. No in-game check (no caller).

### Task AV-T2 — `node_done` arrives
- **Goal:** A character that finishes creation stands in the temple, with the temple as its home, and reads the temple once.
- **Dependencies:** AV-T1.
- **Approach:** `world/chargen_menu.py`, in `node_done`: after `caller.snapshot_skill_baseline()` and before the `client_state.push` (AV5), `arrival.arrive(caller)`. Nothing else in the node changes: the guard for an already-made character returns before it, and every refusal returns before the flag. The node's docstring gains the step in its *Order* sentence and one line on AV6. `world/chargen.py`'s docstring above the `EvMenu` call (`:344–351`) gains that `cmd_on_exit` now shows the arrival room.
- **Testing** (`tests/test_chargen_menu.py`, new class on a seeded database): the success path leaves location and `home` the temple and the flag `True`; each refusal path (unknown profession, `apply_allocation` raising, the half-done grant) leaves location and `home` untouched; an already-made character run through `node_done` again is not moved (put it in `room2` first); on an unseeded database the success path still sets the flag and returns the closing text; the push is called after the move — patch `client_state.push` and assert `caller.location` is the temple inside the patched call. The existing `node_done` tests run unseeded and must stay green unchanged.
- **Mutations (AVM5–AVM7):** call `arrive` before the refusals (a refusal test must fail); call it after the push (the ordering test must fail); call it in the already-made guard's branch (the not-moved test must fail).
- **In-game protocol** (dev instance; two clients):
  1. Staff: `@py from typeclasses.accounts import Account; a, e = Account.create(username="arrivaltest2", password="<own password>"); self.msg(str((a, e)))`.
  2. Staff: `@py from evennia import search_object; c = search_object("arrivaltest2")[0]; self.msg(f"{c.location} {c.home} {c.db.chargen_complete}")` → `Limbo Limbo False` (the statue waits in Limbo, AV1).
  3. Second client: log in as `arrivaltest2`, finish the menu. After *"Your character is made…"*: **Old Temple**, its description, once. No Limbo text.
  4. As `arrivaltest2`: `@py` is not available to a Player — staff runs `@py from evennia import search_object; c = search_object("arrivaltest2")[0]; self.msg(f"{c.location} {c.home} {c._get_respawn_location()}")` → three times the temple.
  5. Webclient, same login: the Location panel shows the temple on arrival, not Limbo.
  6. Staff: `@py` step 4's line for an older character (`arrivaltest`) → still Limbo for `home` (AV7, no backfill).
- **Commit:** `feat(arrival): a finished character arrives in the temple, and it is home (Newcomer Z1)`
- **Shipped (Rev 2):** `b8bc0ad` on `feature/arrival`, tree `3fe9c4a`. `world.chargen_menu` imports `arrival` as a module: EvMenu makes every public function in the menu module's namespace a node, imported ones included. `_MenuFixture` takes its `cmd_on_exit` from a class attribute, `None` by default, so the existing tests run as before and one new test runs the shipped `"look"`: the closing line, then *Old Temple* once. Tests: `tests/test_chargen_menu.py` (+9), red first against the base node (3). AVM5–AVM7 killed. Sandbox: ten neighbour modules 281 OK, the whole suite 1633 OK. Work machine: the ten modules 281 OK. **The protocol, as run at work** (Testing Ref §24): with `arrivaltest3` — `arrivaltest2` finished the menu before staff had read step 2, so the run began again; its statue stands in the temple. Step 2 `Limbo Limbo False`; staff in `Old Temple(#120)`; the newcomer's client read the closing line and then the temple once, no Limbo text; staff's room panel listed `arrivaltest3` with no line in staff's text (AV8); step 6 `Old Temple Old Temple Old Temple`; `arrivaltest` `Limbo Limbo Limbo` (AV7); `grep -c "arrival:" server/logs/server.log` → `0`. The newcomer played from a text client, so the Location panel on arrival (AV5) was not seen; Adam ruled that `test_the_push_already_sees_the_temple` carries it.

### Task AV-T3 — The chore names the spring
- **Goal:** `work water` reads as a walk to the spring the world has.
- **Dependencies:** None.
- **Approach:** `commands/work_commands.py:189–190`: `begin_actor` → *"You shoulder the yoke and set off for the spring."*; `begin_room` → *"shoulders a water yoke and heads for the spring."* The two `done_` lines name pails and the basin and stand. Read the four lines against `docs/PolishedWorld_Tone_Guide.md`'s checklist before committing. Grep `docs/` for *the well*: `docs/GameGold_Design.md:376` is the faucet's original design line and is left as history; `docs/PolishedWorld_Testing_Reference.md:1252`'s `bug the well is dry` is a report's sample text, not the chore.
- **Testing** (`tests/test_work_command.py`): one test that no line of any chore in `TEMPLE_TASKS` contains *well* as a word, and that `water`'s two opening lines contain *spring*. No test reads the old strings today.
- **Mutations (AVM8):** restore *well* in `begin_room` only (the test must fail).
- **In-game check:** in the Treasury's room, `work water` — the opening line names the spring.
- **Commit:** `fix(work): the water chore walks to the spring, not a well (Newcomer Z2)`
- **Shipped (Rev 2):** `652cc27` on `feature/arrival`, tree `b21cfaf`. The test is two: no chore line has *well* as a word (a word boundary, because the Brook's own text has the spring *wells up*), and water's two opening lines name the spring. Red first against the old lines; AVM8 killed. Sandbox: `test_work_command` 79 OK, the whole suite 1635 OK. Work machine: 79 OK. In game: `work water` answered *There is no work to be had here.* in the seeded Old Temple, because the dev Treasury `#10` stands in the hand-built `temple` `#4` (Launch Minimum's paid-`work` receipt); in `#4`: *You shoulder the yoke and set off for the spring.*, the closing line, 35 Copper.

---

## 6. Component 2 — Close-out (on `main`)

### Task AV-T5 — Merge
- **Goal:** `feature/arrival` on `main` by merge commit, the whole suite OK.
- **Dependencies:** AV-T1–AV-T3 received, every planned mutation killed, AV-T2's protocol run in game.
- **Approach:** the full suite on the branch tip; `git merge-tree` against `main`; PR; merge commit; branch deleted on origin and locally. Merge before docs (lesson 174). Pushes and the tag through GitHub Desktop (lesson 332).
- **Commit:** the merge commit — `Merge pull request #NN from G0dlet/feature/arrival`.
- **Shipped (Rev 2):** `main` had not moved since the branch's base (`7653a42`), so `git merge-tree --write-tree` gave the branch tip's own tree, `b21cfaf`, with no conflict. `def test_` 1635 under `tests/`. The full suite on the merge result before the PR, at work: a local `--no-ff` merge in a detached HEAD, `"#10"` stashed — `03e6c50`, tree `b21cfaf`, parents `7653a42` `652cc27`; `Ran 1635 tests`, `OK` (`ForkTestRunner --parallel auto`). Node and art suites not run: the branch touches nothing under `web/` or `art/`. PR #30 merged with a merge commit: `185a47a`, tree `b21cfaf`, parents `7653a42` and `652cc27`. The branch is deleted on origin (`git ls-remote` empty) and at work. The chain's return to the branch and its `stash pop` was not run before the next step, so the `"#10"` line stayed in the stash until a separate `stash pop` on `main` (lesson 341). In the sandbox, the suite with `"#10"` appended stopped in a worker on *An Account with the name 'TestAccount' already exists* — BACKLOG's dbref-failures entry, annotated.

### Task AV-T4 — Documentation and the tag
- **Goal:** Every document that describes the Limbo start as shipped behaviour describes the temple, in one commit on `main`, and L6.1 has a tag that carries it.
- **Dependencies:** AV-T5.
- **Approach:** this document: status DONE, a *Shipped* line per task, §8 records. `docs/system_designs/PolishedWorld_Newcomer_Design.md`: Z1 and Z2 marked shipped (a new Rev). Roadmap: the parallel-backlog entry *The newcomer's economy* and *Nuläge* gain a dated *delivered* note. `docs/PolishedWorld_Alpha_Runbook.md`: §1's *stands as a stone statue in Limbo until the first login* gains *and arrives in the Old Temple when creation is done*; §7 names the new annotated tag `alpha-YYYYMMDD` as the one L6.1 deploys; wherever the fresh-instance steps set `DEFAULT_RESPAWN_DBREF`, a note that it is now an override (AV3). `docs/PolishedWorld_Evennia_Reference.md`: where chargen and respawn are described. `docs/PolishedWorld_Testing_Reference.md`: AV-T2's protocol as it was run. `docs/PolishedWorld_Lessons.md`: the session's candidates. README Rev line; the catalogue loop.
- **Commit:** `docs: close out arrival (Newcomer Z1–Z2)`
- **Shipped (Rev 2):** this commit. Locked at STOPP 0 (Adam took every recommendation): **(A1)** the tag is `alpha-20261114-2` on the merge commit `185a47a` — `alpha-20261114` was taken by the survival loop's merge, moving a pushed tag was rejected, and the runbook says a day's second tag carries `-2`; made in GitHub Desktop, annotated, and read back from origin (lessons 262, 332). **(B)** OQ-AV3 is closed as recorded, not built, with no BACKLOG entry. **(C)** no dev board card (OQ-AV4). **(D)** the three `arrivaltest` accounts stay on the dev database as fixtures (OQ-AV5). **(E)** BACKLOG Rev 111: the Z2 annotation is marked shipped, and the dbref-failures entry records the `TestAccount` recurrence. **(F)** Lessons 333–341: the handoff's (a)–(g) and two from this close-out. **(G)** one commit. The Newcomer note's Z1 and Z2 are marked shipped (Rev 3); the roadmap's parallel-backlog entry and *Nuläge* carry a dated note (Rev 79); the runbook's §1 statue line, §7 tag and the respawn setting (Rev 10); Evennia Ref §21 (Rev 34) and Testing Ref §24 (Rev 25) are new; README Rev 59 and the catalogue loop. Beyond the approach's list: the series handoff `docs/system_designs/HANDOFF.md` Rev 17, whose gotcha described the Limbo start as shipped behaviour, and the README's Lessons row, which had read *1–296*.

---

## 7. Open questions (each with the task that closes it)

- **OQ-AV1 — Does `home` accept the assignment as written?** `character.home = room` is Evennia's property setter. → AV-T1's first test. If it needs `.save()` or a dbref, the test says so before anything is built on it. **Closed (Rev 2):** it does; `test_home_survives_a_fresh_read` reads `db_home` after `refresh_from_db()`.
- **OQ-AV2 — Does anything the project's `at_post_move` does matter on arrival?** It looks, charges an overloaded step and checks the survival buckets (`typeclasses/characters.py:1681–1713`). A newcomer carries nothing and the closing `look` follows. *Leaning: nothing is lost.* → AV-T2's protocol step 3 and 5; if the webclient's Location panel does not update without the hook, AV5's push is the fix, not the hook. **Closed (Rev 2):** nothing is lost. The look comes once from `cmd_on_exit`; the room lists the skipped room hooks would have pushed are pushed by `arrive()` (AV-T1's change), and staff's panel showed the newcomer; the newcomer's own panels are `node_done`'s push, pinned by a unit test.
- **OQ-AV3 — A character that dies inside the creation menu.** The survival tick runs on a puppeted character in the menu (a staff character once died of thirst in Limbo, runbook §10). Its `home` is still Limbo, so it respawns there, still in the menu. Eight real hours in a menu is not a newcomer's path. *Leaning: recorded, not built.* → AV-T4 files it in BACKLOG if Adam wants it kept. **Closed (Rev 2):** recorded here, not built, no BACKLOG entry (AV-T4's lock B).
- **OQ-AV4 — The dev board.** A slice this small has had no card before. *Leaning: no card.* → AV-T4. **Closed (Rev 2):** no card (lock C).
- **OQ-AV5 — The `arrivaltest` accounts on the dev database.** → AV-T2's protocol leaves two; staff removes them or keeps them as fixtures. **Closed (Rev 2):** it left three (`arrivaltest`, `arrivaltest2`, `arrivaltest3`, the last as `account#9`); all three stay on the work machine's dev database as fixtures (lock D).

---

## 8. Records

| Task | Commit | Tree | Tests | What the build changed from the text above |
| --- | --- | --- | --- | --- |
| AV-T1 | `10b86bc` | `8dd7110` | `tests/test_arrival.py` 17; `TestPushCensus.SITES` +1 row | `arrive()` pushes both rooms after the move (the re-read of death's move); mutation AVM4b added |
| AV-T2 | `b8bc0ad` | `3fe9c4a` | `tests/test_chargen_menu.py` +9 | `_MenuFixture.on_exit`, so one test reads the shipped closing `look`; the protocol ran with `arrivaltest3` |
| AV-T3 | `652cc27` | `b21cfaf` | `tests/test_work_command.py` +2 | the one planned test is two; in game in `#4`, where the dev Treasury stands |
| AV-T5 | `185a47a` (PR #30) | `b21cfaf` | suite 1635 OK on the merge result | — |
| AV-T4 | this commit | — | — | tag `alpha-20261114-2` (lock A1) |

---

## 9. Consequences worth reading twice

- **The statue still waits in Limbo.** Before first login a new account's character stands in Limbo as a statue (AV1). Staff standing in Limbo see it; no player does. That is the intended reading of *admin space*.
- **`home` now means the temple for every made character.** Evennia's `home` command and anything that sends an object home (`DefaultObject.delete()` clears contents to their home, the series handoff's gotcha) lands a made character in the temple, not Limbo. That is the better answer, and it is a change.
- **`DEFAULT_RESPAWN_DBREF` is no longer load-bearing.** An instance without it now respawns at the temple through `home`. An instance with it set to a different room still obeys the setting.
- **The seed id is now read at runtime by play, not only by the seeder.** Renaming `alpha.room.temple` in `world/seed_data.py` without re-tagging the live room would send newcomers nowhere (AV6 keeps them made, in Limbo, with a log line). The constant's comment says so.
- **A hookless move owes the rooms their pushes.** *(Rev 2)* `arrive()` is the second hookless move of a character, beside death; each pushes the room it left and the room it entered itself. A third one — a future `@tel`-like move without hooks — owes the same two lines and a census row.
- **Nothing here teaches.** The first room is fixed; what the room says to a newcomer is the temple's description, which is the next building pass's (Newcomer NCP4, Comfort EP19).
