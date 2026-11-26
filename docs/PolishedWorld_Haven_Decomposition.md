# PolishedWorld — Haven Decomposition (Stage 5, slice 8: HV)

> **Rev 1 · 2026-11-26** — first version, docs only, with `docs/PolishedWorld_Combat_Design.md` Rev 15 (the slice's locks HV1–HV8 under PV1–PV6, a note at HQ2 and at TR5, two rows in §5 and OQ-HV1–OQ-HV3 in §7), `docs/PolishedWorld_Combat_Decomposition.md` Rev 25 and README Rev 95. Decomposes Stage 5's eighth slice, HV, from Combat Design §4.2 (PV1, PV3, PV5) and §4.3 (TR5), and from the Comfort note's EP9–EP13 and X1: a room flag read through one function, set by the seed on the Old Temple; a player's body that stays its owner's for as long as it lies in a haven; one guard that answers whether an attack may begin, with player against player switched off behind a constant; and `hunt` as the guard's first caller. Eight locks (Adam, 2026-11-26, each on the recommendation given, one at a time). Five code tasks, a merge and a close-out (HV-T1–HV-T7) on `feature/haven`. Anchors read at `main` `464ac28`; five probes run in the sandbox (§4), two of which corrected what the design chat had said.
> **Canonical:** `docs/PolishedWorld_Haven_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Design source:** `docs/PolishedWorld_Combat_Design.md` §4.2 (PV1–PV6, the statue, HV1–HV8), §4.3 (TR3, TR5, TR6), §4.4 (WN4), §4.7 (HQ2), §4.8 (HB2), §5, §7 (OQ-GR3, OQ-HV1–OQ-HV3); `docs/PolishedWorld_Combat_Decomposition.md` §2 (HV's row, and HL's, ML's, DR's and PJ's); `docs/system_designs/PolishedWorld_Comfort_Design.md` §2.1, EP4, EP9–EP13, EP19, X1, EQ7, EQ12, §16; roadmap, *Haven (2026-11-09)* and the decision log's *[RESOLVED] Combat: PvE first, PvP built and switched off*; BACKLOG *Corpse expiry fires only on direct interaction* (DONE) and *Death contract surfaces* (read whole before HV4).
**Status:** decomposed (Rev 1). HV1–HV8 are locked; no task is started.
**Feature branch:** `feature/haven` — one branch, one merge (ST2). Create it with `git switch -c feature/haven --no-track origin/main`.
**Rough scope:** five code tasks, a merge and a close-out; about five to six hours of code — one session at 5 h/week, or two short ones. One new module (`world/haven.py`), one field in the seed's room table, one property changed on `PlayerCorpse`, three texts of the death contract, a few lines in `hunt`. No new command.
**Philosophy:** skynda långsamt — the flag before its readers; the reader that has a caller today before the one that waits; a rule no play can reach yet is proven by tests and by `py`, and says so; what can be read where it lies is not stored a second time.
**Labels:** HV (locks, in the Combat Design §4.2), HV-T (tasks), HVM (mutations), OQ-HV (open questions, in the Combat Design §7). All were free across the repository at `464ac28`: `git grep -n -I -E '\bHV[0-9]|HV-T[0-9]|HVM[0-9]|OQ-HV[0-9]'` gave no line, before they were used. The components are H1–H4. PV1, PV3, PV5 and TR5 stay the Combat Design's labels for the decisions the locks fill in.

---

## 1. What the slice is

PV3 says *what*: `is_haven` is built in Stage 5 with two readers, no attack can begin in a haven by anyone and against anyone, and a player's body there stays its owner's until it crumbles. PV1 says a player character cannot attack another, behind a setting. This slice says *how*, and builds it — before close combat (ML), so the guard has no blow to guard yet.

**What a player meets after the merge:**

- In the Old Temple, `hunt` is refused. A rabbit that has fled in there is left alone (HV6).
- A body that lies in the Old Temple stays its owner's to take from for as long as it lies there, not for three game days. The death line, `look` at the body and `help death` say so (HV4).
- Nothing else. Nothing tells a player who walks in that the room is a haven (OQ-HV1).

**What the slice builds, for ML, PJ and DR to call:**

- `is_haven(room)`, the one reader of the flag.
- The guard: asked with an attacker and a target, it answers `None` or the line that refuses. It reads both their rooms, asks the haven first and player against player second, and names a player target as the attacker sees it (TR5).
- `PVP_ENABLED = False`, read only by the guard.

**What the slice does not build:** the blow, `attack` and its text (ML); a shot (PJ); a creature that attacks, and what a creature does to a statue (DR; Combat Design §4.2, *The statue*); `wake`, First Aid and rescue, which are TR5's first sentence and HL's (§2, HV7); theft from a person, which stays impossible (PV4); the comfort read and any sign that a room is a haven (HV8); a command that sets the flag (HV3); a haven that is a player's house (Comfort EQ3).

---

## 2. The locks

Each was taken on 2026-11-26 on the recommendation given, one at a time; the Combat Design §4.2 carries them. In short, with what was rejected:

- **HV1 — The guard is built as a function before ML, and the body's rule is built whole.** One question — may this attacker take this target here — with its answer and its refusal line, tested and shown by `py`, for ML to call where an attack takes its target (PV1). *Why:* PV1 says gate, do not defer; ML is the largest slice and should find the question ready; DR waits on HV. *Rejected:* the flag and the body only, with the guard left to ML; a Builder's command that attacks (ML replaces it, CE1's reason). *HV6 then gave the guard a caller in play.*
- **HV2 — The flag is a plain Attribute, `room.db.is_haven`, read through one function.** It is `is_indoor`'s form — five readers of `room.db.is_indoor` (`commands/world_commands.py:47`, `world/client_state.py:245`, `world/garment_wear.py:106`, `world/thermal.py:68`, `world/weather.py:91`), and `Room` has no `AttributeProperty` — and PV3's and Comfort EP9's name. *(The design chat said eight; the list gives five, lesson 494.)* A room without the Attribute is no haven, so no room that exists is touched. The function answers False for no room at all. A census holds that no other code reads the Attribute. *Why:* every reader already holds the room it asks about; none has to find the havens. *Rejected:* an `AttributeProperty` on `Room` (its first, adding nothing the function lacks, and CE3's question of what the first read writes); a tag in the `room_flag` category, as the spawn rooms have (`world/seeding.py:77`) — that form is for a script that must find rooms, and staff would have two ways to flag a room.
- **HV3 — The seed sets the flag when it makes the room; staff use `@set`; an older database gets a line in the runbook.** `seed_data.ROOMS` gains `is_haven`, true for the Old Temple alone. Staff write `@set here/is_haven = True`, whose lock is `cmd:perm(set) or perm(Builder)` (`evennia/commands/default/building.py:1780`, v6.1.0). A database made before the merge finds the temple by its seed tag, `alpha.room.temple`, in the Alpha Runbook's §7. *Why:* the alpha database is made fresh; Comfort EQ12 leans to staff only, and the lock that gives it exists. *Rejected:* a seed that mends rooms it finds (`_seed_rooms` skips them, `world/seeding.py:146–148`; mending would also put back a flag staff had taken away); a staff command of its own (a command, a lock, a help text and tests for something done a handful of times — it can come with *settlements & commons*).
- **HV4 — The body reads the room it lies in, each time it is asked.** `PlayerCorpse.grace_active` is true for as long as the body's room is a haven, and as today otherwise; the lock and `look` read it. The death line, `help death` and the refusal follow. *Why:* the lock already reads everything when it is asked, so that nothing has to fire (`typeclasses/corpse.py:336–339`, the comment and the lock); HV2's one reader is enough; a room staff flag covers the bodies already in it. *Rejected:* a stamp written at the death (a second kind of read of the flag, a copy that can go stale, and one more thing `at_character_death` writes); both.
- **HV5 — `PVP_ENABLED = False`, a constant in `world/haven.py`, read only by the guard.** The pattern PV1 names: `SEVERED_ENABLED` is a constant in `world/wounds.py:72`, read where the choice is made (`:427`), and tests patch the module's attribute. No other module imports the constant; whoever wants to know asks the guard. The constant never opens a haven: with it True the guard still refuses there (PV3). *Why:* opening player against player is then a commit, a tag and a deploy, which is what PV6's *a decision of its own* asks for. *Rejected:* a Django setting (an instance could switch it on in `secret_settings.py`, outside git, without the decision); a value in the database switched in the game.
- **HV6 — `hunt` asks the guard, and is refused in a haven.** A quarry that wins `hunt`'s test bolts through a random exit (`commands/hunting_commands.py:167–171`), the Temple Clearing's exits include the Old Temple, and `hunt` works wherever a creature stands (`:69–72`) — so a player can kill in the haven today (§4, P3). PV3 says *by anyone and against anyone*. **This departs from the letter of HQ2,** which has `hunt` unchanged in Stage 5: the file gains a few lines and the hunt's model — the opposed test, the flight, the kill — is not touched. The Combat Design says so at HQ2. *Why:* PV3 is true as it stands from the day the flag is set; the guard has a caller in play, so a command shows it. *Rejected:* no reader in play (a haven one can kill in, with PV3 locked); a quarry that never flees into a haven (it changes the hunt's own flight, nearer the model than a refusal is).
- **HV7 — HV takes TR5's second sentence; the guard is one question with one answer.** It answers `None`, or the line for the attacker, and sends nothing itself: a creature that attacks has nobody to tell. It reads the attacker's room and the target's, so a shot between rooms is refused into a haven and out of one (SR, PJ). The haven is asked first, player against player second. A player character is the class `Character`; a statue is one. The line that refuses under PV1 names the target with `get_display_name(attacker)`; the haven's line names nobody. *Why:* three callers are coming — `hunt` now, ML and PJ — and none needs the reason to refuse. *Rejected:* building `wake` (there is nothing to wake anyone from: sleep is Rest slice 2, and unconsciousness has HL's `wounds.revive`); a guard that sends the line and answers True or False, as `refuse_if_collapsed` does. **TR5's first sentence** — help aimed at a player uses the same search — is met by NM's search (`Character.get_search_result`, `typeclasses/characters.py:812`), which every `caller.search()` goes through, and is owed a command by HL.
- **HV8 — The comfort read is not built.** Comfort EP4's `comfort()` waits for the first good state it can lengthen (Comfort §16, layer 4), and its ladder and multiplier are open there (EQ8). HV ships the source it names *safe*: `is_haven`. *Rejected:* the read with four of six sources; a line in `look` or `status` that says a room is a haven — how a haven shows itself is the Comfort note's (EP19), and OQ-HV1 holds the question.

---

## 3. Verified source anchors (read 2026-11-26, `main` at `464ac28`; Evennia 6.1.0 from the wheel)

**The book.** No page of *Legend* is read for this slice: PV1 and PV3 are the game's own rules and stand in the Combat Design's §5 as rows without a page.

| Where | What it says | Used by |
| --- | --- | --- |
| `world/seed_data.py:54–55`, `:81–93` | The room fields' description; the Old Temple's row, with `"is_indoor": True` at `:90`. | HV3 |
| `world/seeding.py:144–161` | `_seed_rooms`: a room that exists is skipped (`:146–148`); the Attributes are written at creation (`:149`), and one that is not set is not written (`thermal_regime`, `:151–152`). | HV3 |
| `world/seeding.py:77` | `SPAWN_TAG = ("creature_spawn", "room_flag")`, the flag a script searches by. | HV2 |
| `tests/test_seeding.py:207` | Every seeded room is held to its `is_indoor`. | HV-T1 |
| `typeclasses/corpse.py:86` | `get:false()`: no player moves a body. | HV4 |
| `typeclasses/corpse.py:273`, `:284` | `_PLAYER_EXPIRY_HOURS = 288`, scaled by the weather; `_PLAYER_GRACE_HOURS = 72`, unscaled. | HV4 |
| `typeclasses/corpse.py:339–346` | The lock `get_from:corpse_grace()` and the refusal line, stored on each body as it is made (`db.get_from_err_msg`). | HV4, HV-T3 |
| `typeclasses/corpse.py:348–351` | `grace_active`, the one source of the grace. | HV4, HV-T2 |
| `typeclasses/corpse.py:384–393` | `look` at the body: the claim line, which counts the time left itself (`:389`). | HV-T2 |
| `server/conf/lockfuncs.py:35–64` | `corpse_grace`: the owner first, then `not grace_active` (`:61`); any exception fails closed. | HV4 |
| `world/death_contract.py:60`, `:90–117`, `:120–143` | `grace_game_hours`; the death line, given the body's room; `help death`. | HV-T3 |
| `typeclasses/characters.py:1857` | `death_message(corpse.location if corpse else None)`. | HV-T3 |
| `typeclasses/objects.py:40–65` | `ObjectParent.at_pre_put_in` refuses a put into anything that is not a container. | §4 P2 |
| `world/wounds.py:72`, `:427` | `SEVERED_ENABLED`, and its one read. | HV5 |
| `commands/hunting_commands.py:50–151` | `hunt`: the cooldown read, the name, the creatures in the room (`:69–72`), the search (`:76`), the claim, the roll. | HV6, HV-T5 |
| `commands/hunting_commands.py:153–173` | `_flee`: a random exit the creature may traverse, with no hooks. | HV6 |
| `commands/hunting_commands.py:87` | A name through a looker: `target.get_display_name(caller)`. | HV7 |
| `typeclasses/characters.py:997–1006` | `is_statue`: no account, and no wound holding the body. | HV7 |
| `typeclasses/npcs.py:68` | `Sweeper` is a `DefaultObject`, not a `Character`. | HV7 |
| `typeclasses/scripts.py:158–192` | The spawn script tops a spawn room up to its count; nothing takes a creature away or moves it but `hunt`. | §11, 4 |

**What is not in the code** (`git grep`, 2026-11-26, outside `tests/`): `is_haven`; a command `attack`, `wake` or one for First Aid; `comfort(`; any name with `PVP`, but for a comment at `typeclasses/characters.py:1739`.

---

## 4. What was run (sandbox: Python 3.13.18, Evennia 6.1.0, Django 6.0.10; a fresh clone of `464ac28`)

**The baseline.** `COLLECTED 2700`, by the runner's own collection (Testing Reference §27.1) — the count CE-T7's run gave. Twenty-one test modules name what the slice touches (`git grep -l -i -E 'PlayerCorpse|corpse_grace|grace_active|death_message|CmdHunt|seed_world|is_indoor' -- 'tests/test_*.py'`) and hold 622 tests; they are the neighbour set for every task, with each task's changed symbols searched on top (lesson 440).

**P1 — the flag by `@set`.** A room without the Attribute reads `None`. `@set here/is_haven = True` stores the `bool` True and `= False` the `bool` False; `= yes` stores the string `'yes'`, which is true; `@set here/is_haven =` removes the Attribute. With the account at `Player` the command's lock refuses, and with `Builder` it passes. *(The probe's first form asked the lock with the test account's `Developer` still on, and passed for the wrong reason.)*

**P2 — a put into a body.** Owner and stranger, with the grace running and with it over: all four are refused with *You can't put things in that.*, and nothing goes in. The refusal is `ObjectParent.at_pre_put_in`'s, since a body is not a container; the lock is not reached. **This corrects the design chat,** which said at HV4 that an owner could store things in a body lying in a haven. Nobody can: a body only empties.

**P3 — a rabbit in the temple.** After `seed_world()`, the Temple Clearing's exits a rabbit may traverse lead to the Brook, the Edge of the Woods, the Meadow and the Old Temple. `_flee`, with its choice held to the temple's exit, puts the rabbit in the Old Temple; `hunt rabbit` there reaches the roll.

**P4 — a statue's name.** A character nobody puppets reads *stone statue of a quiet traveller* to another, never its key. So the guard's line names a statue as a statue.

**P5 — the sweeper.** `seed_world()` makes none; where a sweeper stands is the database's. **This corrects the design chat,** which said at HV7 that the sweeper stands in the temple.

The probes were `tests/test_zz_probe_hv.py`, written, run and removed in one command each time; `git status` was clean afterwards.

**Mutations** are run in the sandbox by `tools/mutate.py` with a TOML spec per task under `tools/mutants/` (Testing Reference §28.1), as CE's were.

---

## 5. Dependency graph

```
HV-T1 ──┬─> HV-T2 ──> HV-T3 ──┐
        └─> HV-T4 ──> HV-T5 ──┴─> HV-T6 ──> HV-T7
```

HV-T1 is the flag and its reader, and both branches read it. The body comes before the guard: it has readers today and is the smaller change, so the slice's first behaviour can be seen in play early. HV-T2 changes a rule and HV-T3 three texts, apart, so that a mutant in the rule is killed by the rule's test and not by a comparison of strings (lesson 181). `hunt` is last in the code, so the only lines in a file HQ2 guards are a commit that can be read and reverted alone.

**The order the tasks are taken in is their number.** The mutants are given out here in blocks, one per task, so no number is taken twice (lesson 498): HVM1–HVM3, HVM4–HVM6, HVM7–HVM9, HVM10–HVM15, HVM16–HVM18.

**The names below are proposals** — the functions, the constants for the lines, the lines' own wording. Each is taken at its task's STOPP 0, the wording against the Tone Guide. **Each task's *In-game check* says what is done and what is seen; the whole line is written and tried through `CmdPy` in the sandbox at the task** (lessons 502 and 509: a line written before the code exists is a line that names what was not built).

---

## 6. Component H1 — The flag

### Task HV-T1 — `is_haven`, and the seed
- **Goal:** one function answers whether a room is a haven, and a world seeded from nothing has one: the Old Temple.
- **Dependencies:** none.
- **Approach:** a new module, `world/haven.py`, with `is_haven(room)`: False for `None`, else the truth of `room.db.is_haven`. It imports nothing of the game's. `seed_data.ROOMS` gains the field `is_haven` on all six rows, true on the Old Temple, with a line in the module's *ROOM FIELDS*. `_seed_rooms` writes the Attribute; whether it writes False on the five others or nothing, as `thermal_regime` does, is a choice at STOPP 0 — nothing reads the difference (HV2), so the question is which a later `@set` or a staff member's read finds less surprising.
- **Testing:** a new `tests/test_haven.py`: no room; a room without the Attribute; True; False; the string `'yes'`, which is a haven and is in the test so that nobody tightens the read without seeing it (P1). In `tests/test_seeding.py`, each seeded room is held to its row's `is_haven` through the function, and a second `seed_world()` changes nothing. **A census:** across `world/`, `typeclasses/`, `commands/` and `server/`, the word `is_haven` as an Attribute — `db.is_haven`, or the string in an `attributes` call — stands only in `world/haven.py`, `world/seeding.py` and `world/seed_data.py`; its message names HV2.
- **Red before green:** the seeding test, against the seed as it is.
- **Mutations (HVM1–HVM3):** the read is `is not None`, so a stored False is a haven; the seed writes the flag true on every room; the seed writes it on none.
- **In-game check:** in a room that is no haven, the function is asked through `py` and says False; `@set here/is_haven = True`, and it says True; `@set here/is_haven =`, and it says False again. The home database's Old Temple is not flagged by this task (HV-T6).
- **Commit:** `feat(haven): the haven flag, its reader and the seed (PV3, HV2, HV3)`

---

## 7. Component H2 — The body

### Task HV-T2 — The grace reads the room
- **Goal:** a player's body that lies in a haven is its owner's to take from for as long as it lies there.
- **Dependencies:** HV-T1.
- **Approach:** `PlayerCorpse.grace_active` is true when `haven.is_haven(self.location)`, and otherwise what it is today. The lock function and the class's comments that say the grace *never re-locks* are rewritten to say what holds now (§11, 2). `return_appearance` no longer counts hours for a body in a haven (`:389` would print a span that has run out): the claim line there says the claim lasts while the body lies here. `corpse.py` imports `world.haven`, which imports nothing back.
- **Testing:** in `tests/test_death_contract.py`, beside `TestGraceBoundary`, with the clock pinned as that class pins it: in a haven the stranger is refused at 71, 73 and 287 hours and the owner never; outside, 71 and 73 as today. In two cases the owner and the stranger stand in a room other than the body's — a haven while the body lies outside one, and the reverse — so that the room read is the body's (HVM5; lesson 497: each mutant below was worked through these cases before they were written down). The flag taken off a room opens a body past its 72 hours at once; the flag set on a room closes a body that had opened (the departure, held by a test so that it is a decision and not an accident). `get <item> from corpse` through the command, in a haven at 73 hours: refused, and the item stays. `look` at a body in a haven: the claim line without a number, *Your* for the owner and *Its owner's* for another; outside, as today.
- **Red before green:** the stranger at 73 hours in a haven.
- **Mutations (HVM4–HVM6):** `and` for `or`; the owner's room read in place of the body's; `look` counting hours in a haven.
- **In-game check:** a `PlayerCorpse` made by `py` in a room flagged for the check, owned by one test character, its death set 100 game hours back: the lock is asked for the owner and for a second test character who is not a superuser — a superuser passes every lock (`tests/test_death_contract.py`'s guard) — and answers True and False; the flag is taken off and it answers True and True; the body and the flag are removed.
- **Commit:** `feat(haven): a body in a haven stays its owner's (PV3, HV4, Comfort X1)`

### Task HV-T3 — The death contract's texts
- **Goal:** what a player is told about a body in a haven is what the lock does.
- **Dependencies:** HV-T2.
- **Approach:** `death_message(body_room)` asks `is_haven(body_room)` and, in a haven, says the belongings are the owner's alone for as long as the body lies there, in place of the 72 hours. `help_text()` gains a sentence under *Your claim*. **The refusal line needs a choice at STOPP 0:** it is stored on each body when the body is made (`typeclasses/corpse.py:343–346`) and ends *You can't take from it yet*, which in a haven promises a day that does not come. Either the stored line is reworded so that it holds in both places — bodies made before keep the old one until they crumble — or the body answers the line when asked; the first is smaller, and what `CmdContainerGet` reads decides whether the second is possible at all.
- **Testing:** in `tests/test_death_contract.py`, beside `TestDeathMessage` and `TestHelpDeath`: the death line for a haven carries no span of the grace and says the claim; for another room it is today's, word for word; with no body, today's. `help death` names the haven's rule once. The refusal as chosen.
- **Red before green:** the death line for a room that is a haven.
- **Mutations (HVM7–HVM9):** the death line asks nothing and gives the 72 hours everywhere; it gives the haven's sentence everywhere; `help death` loses its sentence.
- **In-game check:** `help death` read; the death line for the Old Temple and for another room, each asked through `py` from `death_message` with the room found by its seed tag.
- **Commit:** `feat(haven): the death line and help death say what a haven keeps (HV4)`

---

## 8. Component H3 — The guard

### Task HV-T4 — The guard
- **Goal:** one function answers whether an attack may begin, for every caller that is coming.
- **Dependencies:** HV-T1.
- **Approach:** in `world/haven.py`, `PVP_ENABLED = False` with PV1 and PV6 in the comment above it, and a function (proposed `refuse_attack(attacker, target)`) that answers `None` or a line. In order: if the attacker's room or the target's is a haven, the haven's line, which names nobody; else, if `PVP_ENABLED` is False and both are player characters, PV1's line, with the target as `target.get_display_name(attacker)`; else `None`. It sends nothing and writes nothing. **How it knows a player character is a choice at STOPP 0:** the class by its path, as `hunt` finds a creature (`commands/hunting_commands.py:71`), or an import inside the function — `world/haven.py` must not import `typeclasses.characters` at its head, since `typeclasses/corpse.py` imports the module (HV-T2) and the character module is where a body is made. Read the import graph before the lock.
- **Testing:** in `tests/test_haven.py`. **The rooms:** attacker and target in one haven; the attacker in a haven and the target outside; the reverse; neither. **Who:** a character against a creature, a creature against a character, a creature against a creature, a character against a character, a character against a statue, a character against a `Sweeper`, each with the constant False and patched True. In a haven every pair is refused with the haven's line, whatever the constant. Outside, only character against character and character against statue are refused, and only while the constant is False. **The name:** PV1's line for a stranger does not hold the target's key and holds its short description; after `recog`, the recog; for a statue, the statue's name (P4). **Two censuses:** `PVP_ENABLED` is read in no module but `world/haven.py`; and the constant is False on `main`, a test whose message names PV6 and its three conditions, so that the commit that opens player against player changes a test that says what it is doing.
- **Red before green:** character against character outside a haven.
- **Mutations (HVM10–HVM15):** only the attacker's room is read; only the target's; player against player is asked before the haven, so two characters in a haven get PV1's line; `or` for `and` between the two classes, so a creature is refused as a player is; the constant True; the key in the line.
- **In-game check:** by `py`, with a rabbit made for it: the guard is asked for the caller against the rabbit in a room that is no haven and says `None`; the room is flagged and it gives the haven's line; for the caller against a second test character outside a haven it gives PV1's line, with that character named as the caller sees it. Until HV-T5 no play reaches the guard.
- **Commit:** `feat(haven): the attack guard, with player against player switched off (PV1, PV3, TR5, HV1, HV5, HV7)`

### Task HV-T5 — `hunt` asks the guard
- **Goal:** nobody hunts in a haven.
- **Dependencies:** HV-T4.
- **Approach:** in `CmdHunt.func`, after the target is found (`:76–78`) and before it is claimed (`:84–90`), the guard is asked for the caller and the target; a line is sent and the command ends. A refusal costs nothing: no cooldown is started (it is set at `:107`, after the roll), no claim is left on the creature (`:90`), no roll is made. Whether the collapse's refusal (HB2, when it reaches `hunt`) or the haven's speaks first is not decided here: `hunt` has no collapse check today (BACKLOG *A collapsed body's instant commands*). `stalk` is the same command. The file's other lines, and `_flee`, are not touched (HV6).
- **Testing:** in `tests/test_hunt_resolution.py`, or a class beside it: in a haven, `hunt rabbit` gives the haven's line; the rabbit lives and stands where it stood; `ndb.hunted_by` is unset; the cooldown is ready; the opposed test is not called. Outside a haven the module's tests are green as they stand, unedited. A rabbit that flees into a haven is there, and the next `hunt` at it is refused — the whole road of P3.
- **Red before green:** `hunt rabbit` in a haven.
- **Mutations (HVM16–HVM18):** the call removed; the call after the claim, so the refused hunter leaves `hunted_by` set; the guard's answer sent and the hunt run on.
- **In-game check:** a room flagged for the check, a rabbit made in it: `hunt rabbit` is refused, and `hunt rabbit` at once again is refused with the same line and no word of a cooldown; the flag taken off, and `hunt rabbit` runs.
- **Commit:** `feat(haven): hunt is refused in a haven (PV3, HV6)`

---

## 9. Component H4 — Close-out

### Task HV-T6 — Protocol, suite and merge
- **Goal:** the branch is proven whole and is on `main`, tagged, and the home database's Old Temple is a haven.
- **Dependencies:** HV-T3, HV-T5.
- **Approach:** the whole suite in the sandbox first, since it will not have run on the branch (lesson 510), then at home with `ForkTestRunner` and `--parallel auto`, the count predicted by the runner's collection; `node --test tests/js/*.js`; `git merge-tree` for the tree the merge will have. Then the home database, read before anything is predicted (lesson 507): every room that carries the seed tag `alpha.room.temple`, and every room that has `is_haven` at all; the flag set on the seeded Old Temple by a line written and tried in the sandbox at this task; the read again. Then the in-game checks of HV-T1–HV-T5, written from their *Shipped* lines (lesson 509). The same lines go into the Alpha Runbook's §7 as *The haven on a database made before* the tag, and the tag L6.1 deploys moves there (lesson 418). The work database gets the lines when Adam is next at it; it has a hand-built temple beside the seeded one, and the line flags the seeded one.
- **Testing:** the suite, green; the count as predicted.
- **Commit:** the merge commit.

### Task HV-T7 — Documentation
- **Goal:** the documents say what was built and where it stands.
- **Dependencies:** HV-T6.
- **Approach:** this document's *Shipped* lines and Status; Combat Decomposition's row; Combat Design §4.2 and §4.7 dated after the merge, with a *built* paragraph under the locks; **Comfort Design Rev 2** — EP11's *since nothing else kills there* (§11, 3), the table's row *safe*, EP13's two readers, X1's row and EQ7; the roadmap's row *Haven (2026-11-09)*, read against what was built and not only against what was locked (lesson 489); the System Map — the module, `hunt`'s edge to the guard, the body's lock reading the flag, and under *Known gaps* that the guard's half about player against player has no caller before ML; Testing Reference, a section for the slice; BACKLOG as the slice moved it, searched by the names of the task's data and not only by *haven* (lessons 238, 408); Lessons. How the commits are bounded is read from CE-T8 first (lesson 457).
- **Commit:** `docs: close out the Haven (Stage 5 slice HV)`

---

## 10. Open questions (each with what closes it)

- **OQ-HV1 — How a haven shows itself to whoever walks in.** After HV a player learns that the Old Temple is a haven from a refused hunt, from a death line or from `help death`. Nothing in the room says it (HV8). **Closes at:** the Comfort note's layer 2 — the Old Temple written warm (EP19) — or ML, when a refused blow makes the line matter more.
- **OQ-HV2 — The quarry that stays.** A creature that flees into a haven cannot be hunted there, does not leave by itself and does not die of age; the spawn script fills its old room again. Over weeks the Old Temple gathers rabbits (§11, 4). **Closes at:** DR, with a creature's turn and whether it wanders; or the hunting decomposition that reconciles `hunt` (HQ2); or a staff line in the runbook, if it shows in the alpha before either.
- **OQ-HV3 — What a refused attacker has already spent.** The guard answers before anything is written, and `hunt` asks it before its claim. Where ML asks it — before the opening beat, before the slot is taken — is ML's. **Closes at:** ML's decomposition.
- **OQ-GR3 — The fall** stays where it is, with ML: nothing is dropped by a wounded arm before then, so the haven has nothing to say about who may take it up yet.

---

## 11. Consequences worth reading twice

1. **Before ML, the guard's half about players is reached by no play.** There is no `attack`. PV1 is proven by tests and by `py`; the haven's half is reached by `hunt`.
2. **A flag can close a body that had opened.** The grace's clock is unscaled so that a cold snap can never lock an opened body again (`typeclasses/corpse.py:278–279`). Under HV4 a staff member who flags a room does lock the bodies in it, and one who takes the flag off opens those past 72 hours at once. That is a hand and not the weather, and it is the only thing that moves the answer, since no player moves a body. The class's comments that say *never re-locks* change with HV-T2.
3. **More can die in a haven than the Comfort note counted.** EP11 says a body dies in a haven *of hunger, thirst or cold, since nothing else kills there*. Since WN a bleed-out clock started outside runs on inside, and from ML a wounded player will run for the temple. X1 then keeps the belongings of whoever reaches the door — which reads as the design working, and is worth knowing before DR decides what a creature does at that door.
4. **The temple becomes the quarry's refuge.** A rabbit that bolts into the Old Temple is safe there for good (HV6, OQ-HV2). It is the Comfort note's sleeping cat (§2.1), and it is also a slow leak of rabbits out of the hunt: of the quarry that bolts from the Temple Clearing, one in four goes that way, the clearing having four exits (P3).
5. **A body in a haven only empties.** Nobody can put anything into a body, owner or not (P2). It is not storage, and Comfort EQ7's bound — the body's own decay — is the only one needed.
6. **The body that crumbles takes everything with it, in a haven too.** X1 lengthens the claim and not the body: at 288 game hours, as the weather scales them, what the owner has not taken is destroyed (`Corpse.crumble()`). A player who dies in the temple and does not come back loses the same things at the same hour as one who dies in the woods: 288 game hours are three real days at four to one.
7. **`@set` writes whatever it is given.** `= yes` is a haven and `= no` is one too, being a string that is not empty (P1). The runbook writes `True`, and removes the flag with `@set here/is_haven =`.
8. **A database made before the merge has no haven until its line is run.** The seed does not mend the Old Temple (HV3). Until HV-T6's line, `hunt` works in the temple and a body there opens at 72 hours, as today.
9. **A haven guards a room, not a person in it.** An attacker outside and a target inside are refused because the guard reads both rooms; nothing follows a player out of the door (Comfort EP12). What a creature in the next room does about a player in the temple is DR's.
10. **The alpha may wait for Stage 5.** Not decided (BACKLOG *When the closed alpha opens — now, or after Stage 5*), and nothing here assumes it. If it does not wait, the Old Temple is a haven from the first day, since the alpha database is seeded from nothing (HV3).
