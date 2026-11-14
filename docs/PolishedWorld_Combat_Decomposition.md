# PolishedWorld — Combat Decomposition (Stage 5: the slice map, and the first slice — Names)

> **Rev 1 · 2026-11-14** — first version, docs only, with roadmap Rev 81, BACKLOG Rev 113 and README Rev 61. Decomposes Stage 5 from `docs/PolishedWorld_Combat_Design.md` (Rev 1) in the scope Adam chose at session start: **a slice map for the whole stage** (§2, locks ST1–ST5) and **a full task breakdown for the first slice only**, Names — Evennia's `rpg/rpsystem` on the character (§3–§10, locks NM1–NM15, tasks NM-T1–NM-T19), from `docs/system_designs/PolishedWorld_Names_Design.md` (Rev 1). Read against live source the same day: `main` at `33fab93` (tree `ca8bd8d`; only `docs/` differs from `baed99b`), Evennia 6.1.0 from the wheel. Two things were **run** in the sandbox and are recorded in §4: a probe of the class order, the search and per-reader names, and the whole suite with the one-line class change applied (17 of 1635 tests break). No code is written and none is changed by this document.
> **Canonical:** `docs/PolishedWorld_Combat_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Design source:** `docs/PolishedWorld_Combat_Design.md` §4 (every two-letter item there is Adam's decision) and §7; `docs/system_designs/PolishedWorld_Names_Design.md` (UP1–UP26, K1–K9, UQ1–UQ11); `docs/roadmap.md`, *Stage 5 — Combat*.
**Status:** the map is locked (ST1–ST5); NM is decomposed and not started. Slices 2–14 are named and ordered, not decomposed.
**Feature branch (NM):** `feature/names` (one branch, one merge).
**Rough scope (NM):** 17 code tasks and a close-out, about 18 hours of code — four sessions at 5 h/week. Large for a "first slice" because it is not the display overrides: the contrib replaces the search every command goes through, and twenty room messages, the statue, the body, the teach offer, `trade` and `who` give a name away today.
**Philosophy:** skynda långsamt — the contrib's handlers and parser are taken as they are; its commands are taken one at a time; every name the game prints is resolved by one mechanism, and one test keeps it so.
**Labels:** ST (stage locks), NM (Names locks), NM-T (tasks), NMM (mutations), OQ-NM (open questions). All were free across `docs/`, `world/`, `commands/`, `typeclasses/`, `server/` and `tests/` when checked with `grep -rhoE "\b<XX>[0-9]+\b"`, before they were used.

---

## 1. Why this order

Combat's first blow needs six things that do not exist: a way to name a target that is not its key (NM), two forms of skill test (SC), a body with locations and combat skills (BD), a damage path that knows where it lands (WN), something to hit with and something to be hit in (GR), and something to hit that can be hurt and not only felled (CE). None of them is combat, and each can ship, be played and be tested without it. The alternative — one long `feature/combat` — would keep `main` without any of it for months and run the whole suite rarely.

Names goes first because it changes the search. Every later slice adds commands that take a target; each one written before the contrib would be written twice.

---

## 2. The slice map (ST1–ST5)

**ST1 — Fourteen slices, in this order.** A slice's label is also the prefix of its future locks and tasks.

| # | Slice | Carries (Combat Design) | Depends on | Missing before it can be decomposed |
| --- | --- | --- | --- | --- |
| 1 | **NM** — Names (`rpg/rpsystem`) | TR1, TR6; Names UP1–UP8, UP10–UP20, UP22, UP24–UP26, K1–K9, UQ7 | — | nothing; §3–§10 below |
| 2 | **SC** — the skill-check forms | OC1–OC3 | — | — |
| 3 | **BD** — the body: skills and derived values | CS1, CS2, CS4; Combat Actions, Strike Rank, Damage Modifier, Hit Points per location (core pp. 10–14) | — | the list of styles (CS2), which needs the weapon tables' categories read (Combat Design §3.6) |
| 4 | **WN** — wounds and the damage path | WO1–WO7; BACKLOG *`at_character_death()` restore block vs persistent wound tiers*, *Survival loop tuning* | BD, SC | the bleed-out clocks (WO4), the time to death by starvation (WO7) |
| 5 | **HE** — Hero Points | HP1–HP4 | WN | the earning rate (HP4) |
| 6 | **GR** — weapons and armour | IS1–IS5, AR1–AR6, the first recipes (roadmap *Gear*) | BD | the weapon tables row by row; the armour clothing types (AR3); wear per use (IS5) |
| 7 | **CE** — creatures that can be hurt | CR1–CR2, HQ1 | WN, SC | *Monsters of Legend* (Combat Design §3.6) |
| 8 | **HV** — the haven and the attack guard | PV1, PV3, PV5, TR5 | NM | — |
| 9 | **ML** — close combat | CT1–CT7, PV2, TR2–TR4, HB1–HB3, CS3, CM1–CM2, SR3 | 2–8 | the manoeuvre list (CM2), `ROUND_SECONDS` and the opening beat (CT2, CT3), the text volume (§4.1), Evennia's single-threaded execution read in source (§3.6) |
| 10 | **DL** — coin on the body | BACKLOG *`CoinPile` vs the corpse's atomic content delete*, *`copper` is both a material and a denomination* | — | the two entries read whole (only their decisions were read for this map) |
| 11 | **DR** — dangerous rooms | SO2, the statue rule (§4.2), a creature's turn and its initiative | ML, CE, HV | **an open design question:** how a creature takes its turn without the slot, and how it decides to attack and to follow (Combat Design §7) |
| 12 | **PJ** — projectiles | PD1, SR1–SR2, `shoot` (CS3) | ML, GR | the Projectile note's proposals, locked |
| 13 | **CL** — the character panel | BACKLOG *Character panel: Legend combat state* | WN, ML | — |
| 14 | Close-out | calibration pass, the design notes annotated (Combat Design §6), System Map and BACKLOG *Runnable seam checker for the System Map*, BACKLOG *Two-stage healing* and *Bank / post office* unblocked | all | — |

```
NM ──> HV ───────────────┐
SC ─┬─> WN ─┬─> HE       │
BD ─┤       └─> CE ──────┼──> ML ─┬─> DR
    └─> GR ──────────────┘        ├─> PJ
DL (free-standing, before DR)     └─> CL ──> close-out
```

**ST2 — One decomposition, one branch and one merge per slice** (Adam, 2026-11-14), as Arrival was. Each slice's decomposition is its own document, indexed from this table; this document stays the stage's map and is revised as slices ship.

**ST3 — DL lands before DR.** Its trigger is Stage 5's kickoff and it touches no combat code; it is placed so that the death contract is whole before creatures begin to kill.

**ST4 — HE is its own slice.** HP2 reads the wound level and HP4 is a clock; neither belongs in the damage path.

**ST5 — The seam checker waits for the close-out.** It is a development tool with no dependency on combat; its trigger (Stage 5's kickoff) is answered by placing it, not by building it first.

**What the map says about play.** Nothing can be attacked until ML ships, and nothing attacks a player until DR. Six slices come before the first blow; no shorter route keeps PV2 (one exchange for players and creatures) and WO5 (no default location).

**Not in any slice:** theft from a person (PV4), opening PvP (PV6), the statue in the wild, aiming at what one cannot see, reconciling `hunt` (HQ2) — Combat Design §7 names the home of each.

---

## 3. Names — decisions locked 2026-11-14 (NM1–NM15)

Adam took the fifteen as proposed. NM5, NM10 and NM11 are the session's own and not the Names note's; NM3, NM4, NM10, NM12 and NM15 answer what the source reading found (§4).

**NM1 — The scope is the Names note's layer 3.** UP1–UP8, UP10–UP20, UP22, UP24–UP26 and departure rows K1–K9. Outside: masks and disguise (UP9, UP-L2), `rplanguage` (UP21), the letter of introduction (UQ4), fading recognition (UQ5). UP23, the first-steps hint, stays in BACKLOG *First-steps hints*: no hint mechanism exists in code to hang it on.

**NM2 — Only `Character` takes the contrib** (TR1, UP16): `Character(ObjectParent, ClothedCharacter, ContribRPCharacter)`. Rooms, items and creatures do not.

**NM3 — The contrib's commands are added one at a time, and its command set is taken off.** `emote`, `say` and `pose` go into `CharacterCmdSet`. `ContribRPCharacter.at_object_creation` adds `RPSystemCmdSet` to every new character, persistently (`rpsystem.py:1565`), and that set carries `sdesc` and `mask`; the project's `at_object_creation` removes it after `super()`. UP2 and UP9 need the removal, not only the omission.

**NM4 — `recog`, `forget` and `introduce` are the project's commands on the contrib's handler.** The contrib's `recog` takes anything in the room — a creature, an item, oneself (`:1191`) — and lets a `SdescError` from the handler through uncaught (`:810`, `:825` against the `except RecogError` at `:1230`). The project's version names only other characters, and `forget` looks in the recogniser's own list, so it works anywhere (UP7).

**NM5 — `introduce` sets each hearer's recog (UQ2), and does not overwrite one the hearer has set.** What a player has chosen to call someone is theirs (UG3). The hearer still reads the name in the line.

**NM6 — `who` shows players a count and Builders the table** (UQ1, K1).

**NM7 — The short description is composed in character creation from three choices,** at most 40 characters; there is no `sdesc` command for players, and a Builder-only command sets free text (UP1, UP2). The vocabulary is NM-T15's, approved by Adam at that task's STOPP (UQ9).

**NM8 — Characters made before the slice are backfilled:** the two recog Attributes (UQ7), the pose Attributes, and **a placeholder short description**, because without `_sdesc` the handler falls back to the key (`:690`). Development databases only; the alpha database is created fresh.

**NM9 — `N-name` multimatch,** in `server/conf/settings.py`, with the Testing Reference's protocols and the tests that type `fiber-1` changed in the same task (K6, UQ6).

**NM10 — An exact match comes first.** The contrib's search matches the start of any word in a key or alias, so with *leather* and *leather strap* in the pack `get leather` is a multimatch where today the exact key wins (§4, run). `Character.get_search_result` keeps only the exact key or alias matches when there are any.

**NM11 — No colour on a short description or a recog.** The contrib paints them `|b` and `|m` (`:1651`, `:1670`). Dark blue reads badly, and a leading colour code stops `$You()` from capitalising a name at the start of a sentence (`funcparser.py`, the last branch of `funcparser_callable_you`: `name[:1].upper()`).

**NM12 — Every room message that names a character goes through `$You()` or `mapping`, and a census test keeps the rule** (UP10, UP11). There are twenty such sites at `33fab93`, not the note's sixteen. The test is the base TR4 extends when combat lines arrive.

**NM13 — The statue, the body and the teach offer are named per reader** (K2, K3, K5).

**NM14 — One line per character with its pose; the pose is reset on a move** (K8, UP19, UQ10).

**NM15 — `trade` and the account-level commands are inventoried in tasks of their own** and changed where they name a character (UQ8). `world/barter.py` and the barter contrib under it name the other party by key throughout; the Names note's K-rows do not list them.

---

## 4. Verified source anchors (read 2026-11-14, `main` at `33fab93`; Evennia 6.1.0 from the wheel)

| Anchor | Where | What it establishes |
| --- | --- | --- |
| the contrib's character | `evennia/contrib/rpg/rpsystem/rpsystem.py:1500` (`ContribRPCharacter(DefaultCharacter, ContribRPObject)`); creation hook `:1554–1567` | Sets `_sdesc`, the two recog Attributes, adds `RPSystemCmdSet` persistently (`:1565`), and the sdesc *A normal person* (`:1567`). NM3. |
| the command set | `rpsystem.py:1284–1297` | `emote`, `say`, `sdesc`, `pose`, `recog`, `mask` — all six or none. NM3. |
| display | `rpsystem.py:1509–1552`; `get_sdesc` `:1583–1610`; `process_sdesc` `:1612–1651`; `process_recog` `:1653–1670` | Recog, else sdesc, else key; a looker without `get_sdesc` (or `None`) gets the sdesc. The two colours. NM11. |
| the search | `rpsystem.py:1326–1364`; called by `DefaultObject.search` at `evennia/objects/objects.py:870` | The override is on the **searcher**. With candidates it runs the emote parser in search mode and falls back to a key search only for a Builder who matched nothing (`:1339`, `:1346`). A global or dbref search has no candidates (`objects.py:565–614`) and goes to the default (`:1361–1363`). TR6. |
| the parser in search mode | `rpsystem.py:383–395` (candidate map), `:433–445` (the query) | An object without `sdesc` is matched on key and aliases; the query is a word-start regular expression per word. NM10. `N-` is read by the parser itself (`:208`, `:423–428`, `:496`). |
| `me`, `here` | `objects.py:539–563` | Answered before the contrib's override is reached. |
| the handlers | `SdescHandler` `:660–751` (fallback to key `:690`, `:751`); `RecogHandler` `:754–887` (the write `:836–837`, the lock `:809`, `:858`) | UQ7 as the note says: the write goes into `attributes.get(..., default={})`, which is a throwaway when the Attribute is missing. NM8. |
| the contrib's `recog` | `rpsystem.py:1123–1234` | Candidates are the room's whole contents (`:1191`), for `forget` as well (`:1192`); only `RecogError` is caught (`:1230`). NM4. |
| emotes | `send_emote` `rpsystem.py:558–651`; self-reference added first by default (`:609–620`) | `say` is an emote (`at_pre_say`, `:1569–1581`). |
| multimatch | `evennia/settings_default.py:417`, `:425`; `rpsystem/README.md:80–81`; `evennia/objects/manager.py:28`, `:477` | NM9. |
| `msg_contents` | `evennia/objects/objects.py`, `msg_contents`: `mapping` values and `$You()` are resolved with `get_display_name(looker=receiver)` | NM12. `$You()` capitalises a third-person name; a plain `{key}` from `mapping` does not. |
| the project's character | `typeclasses/characters.py:64` (class), `:224` (`at_object_creation`), `:594–601` (`get_display_name`, which wraps `super()`), `:603–614` (the statue's look, by `self.key`), `:616–632` (`get_display_things`) | NM2, NM13. |
| statue messages | `typeclasses/characters.py:503–507`, `:564–568` | K2. |
| the body | `typeclasses/characters.py:1412–1417` (`key=f"corpse of {self.key}"`, `owner`); `world/death_contract.py:142` (the help line types the key); `tests/test_death_contract.py:96`, `:203–239` | K3. |
| room messages by `.key` (8) | `commands/consumption_commands.py:62`; `typeclasses/creatures.py:84`; `typeclasses/characters.py:503`, `:564`, `:1553`, `:1597` (`FALL_ROOM`), `:1965`, `:2001` (`WAKE_ROOM`), `:2018`; templates `world/fatigue.py:243`, `:245` | NM12. (`:503` and `:564` are the statue's two, counted here and converted in NM-T11.) |
| room messages by `get_display_name()` with no looker (12) | `commands/consumption_commands.py:193`, `:240`; `commands/crafting_commands.py:280`; `commands/hunting_commands.py:338`, `:347`; `commands/work_commands.py:468`, `:609`; `commands/foraging_commands.py:171`, `:240`, `:255`; `commands/currency_commands.py:324` (two characters) | NM12. |
| not a character | `commands/hunting_commands.py:163`, `typeclasses/creatures.py:89`, `typeclasses/corpse.py:207` | A creature's or a corpse's key; unchanged (UP26). |
| the teach offer | `commands/crafting_commands.py:1265–1272` (`from {caller.key}` at `:1271`); the student's search `:1456` | K5. |
| `trade` | `world/barter.py:170`, `:436`, `:441`, `:493–503`; contrib `evennia/contrib/game_systems/barter/barter.py:414–421`, `:560–617`, `:708–751`, `:821–896` | NM15. |
| the room's lists | `typeclasses/rooms.py:320–335` (the comma line), `:337–357`; `world/room_text.py:75` (`room_lists`) | K8. |
| the webclient | `world/client_state.py:134` (own name), `:213–241` (`room_snapshot`, per viewer), `push` `:257`, `push_room` `:271` | UP22. |
| the push census | `tests/test_client_state.py::TestPushCensus`, `SITES` | Every new push is a row. |
| character creation | `world/chargen_menu.py:269` (`node_profession`), `:301–337` (`node_confirm_profession`, the final yes), `:339` (`node_done`) | K9. |
| migrations | `world/character_migrations.py:54` (`backfill_hunting`, the pattern) | NM8. |
| the command set | `commands/default_cmdsets.py:51–191` | NM3, NM4. No project `who`, `say` or `give` exists today. |
| Evennia's own commands | `evennia/commands/default/general.py:482`, `:542` (`get`, `drop`: `$You()`), `:607–611` (`give`: per looker); the clothing contrib's wear lines (`clothing.py:286–313`, `:372–418`) | Already per reader; nothing to change. |
| the old multimatch in tests and docs | `tests/test_craft_command.py:116`, `:222–276`; `tests/test_set_down.py:231`, `:246`; `docs/PolishedWorld_Testing_Reference.md:304`, `:319`, `:783`, `:996` | NM9. |

**What was run (sandbox, 2026-11-14, Evennia 6.1.0, Python 3.13).** A scratch test, never committed, on a class `Probe(Character, ContribRPCharacter)`:

- The order is `Character, ObjectParent, ClothedCharacter, ContribRPCharacter, DefaultCharacter, ContribRPObject, DefaultObject`. `get_display_name`, `get_display_things` and `at_object_creation` resolve to the project's; `get_search_result` to the contrib's.
- A new character has the cmdsets `DefaultCharacter` and `rpsystem_cmdset`, and both recog Attributes.
- The statue is already named per reader through `super()`: a stranger reads *stone statue of a weathered woman*, a recogniser *stone statue of Mia*, and a looker of `None` the sdesc.
- With *leather* and *leather strap* carried: today's search returns one, the contrib's two. With two *fiber*: `fiber-1` finds nothing, `1-fiber` one. `weathered` finds the character, her key finds nothing, `me` finds the searcher. A dbref finds nothing for a character without Builder.
- `$You(actor)` with `mapping={"actor": …}` and `$You()` with `from_obj` both give the actor *You* and the other reader the name as that reader knows it.

**The whole suite with only the class line changed:** `Ran 1635 tests`, `failures=16, errors=1`, in eight modules — `test_client_state` (4), `test_craft_command` (2), `test_currency_commands` (4), `test_encumbrance` (2), `test_knowledge` (2), `test_room_look` (2), and one error in `test_report_commands` that passes alone on the unchanged tree and was not explained (OQ-NM1). The sixteen assert a key where a short description now shows, or find a character by key. The tree was restored afterwards.

Re-read every row before the first task; live source wins.

---

## 5. Dependency graph

```
NM-T1 (N-name) ──> NM-T2 (the class) ─┬─> NM-T3 (search) ──┬─> NM-T5 (recog, forget) ──> NM-T6 (introduce) ─┐
                                      ├─> NM-T4 (backfill) │                                              ├─> NM-T17 (pushes)
                                      ├─> NM-T7 (say, emote, pose) ──> NM-T8 (room lines) ────────────────┘
                                      ├─> NM-T9 ──> NM-T10 (census) ──> NM-T11 ──> NM-T12 ──> NM-T13 (trade)
                                      ├─> NM-T14 (who)
                                      └─> NM-T15 (vocabulary) ──> NM-T16 (chargen)
all ──> NM-T18 (merge) ──> NM-T19 (docs)
```

NM-T9 to NM-T13 are ordered only so that the census (NM-T10) grows one way; any of T5–T8, T14 and T15–T16 can be taken between them.

---

## 6. Component N1 — The contrib on the character

### Task NM-T1 — `N-name` multimatch
- **Goal:** `1-fiber` is the game's form for the first of several, before the contrib arrives.
- **Dependencies:** None.
- **Approach:** `server/conf/settings.py`: `SEARCH_MULTIMATCH_REGEX` and `SEARCH_MULTIMATCH_TEMPLATE` exactly as the contrib's README gives them (`README.md:80–81`), with a comment naming NM9 and that the pair must change together (`settings_default.py:415–425`). `tests/test_craft_command.py` and `tests/test_set_down.py`: every `name-N` becomes `N-name`. `docs/PolishedWorld_Testing_Reference.md:304`, `:319`, `:783`, `:996`. Grep `docs/` and `tests/` for the old form once more before committing; a help text or a hint that prints `rabbit-1` is a miss.
- **Testing:** the changed craft and set-down tests; one new test that `caller.search("2-fiber", quiet=True)` returns the second of two and `"fiber-2"` returns nothing; one that the multimatch error lists `1-fiber`.
- **Mutations (NMM1):** restore the default regex only (the template still prints `1-fiber`, and the search test must fail).
- **In-game protocol:** carry three fiber; `get fiber` lists `1-fiber`, `2-fiber`, `3-fiber`; `craft twine from 1-fiber, 2-fiber, 3-fiber` starts.
- **Commit:** `feat(names): N-name multimatch, with the protocols that type it (Names K6)`

### Task NM-T2 — The character takes the contrib
- **Goal:** A character is shown to others by its short description, with nothing else changed yet.
- **Dependencies:** NM-T1.
- **Approach:** `typeclasses/characters.py`: the import and `Character(ObjectParent, ClothedCharacter, ContribRPCharacter)` (NM2). In `at_object_creation`, after `super()`: `self.cmdset.remove(RPSystemCmdSet)` (NM3), wrapped so that a missing set is not an error. Override `process_sdesc` and `process_recog` to return the text with the case handling the contrib's `ref` argument asks for and no colour (NM11). The class docstring gains the order and why `ContribRPCharacter` is last. **The seventeen tests of §4 are this task's:** each asserts what a viewer reads, so each is changed to the short description it now reads, or finds its character by object and not by key. A small helper in `tests/` gives the fixture characters distinct short descriptions.
- **Testing** (new `tests/test_names_character.py`): the class order (the names of §4, in order); a new character has no `rpsystem_cmdset` and cannot run `sdesc` or `mask`; `get_display_name` for a stranger, a recogniser, oneself and `None`; no `|b` or `|m` in any of them; `$You()` capitalises a short description at the start of a line; the statue wraps the same name; `tests.test_room_look.TestHookMro` still holds.
- **Mutations (NMM2–NMM4):** leave the cmdset on (the `sdesc` test must fail); restore `|b` (the capitalisation test must fail); put `ContribRPCharacter` before `ClothedCharacter` (the order test must fail).
- **In-game check:** none worth a protocol yet — every character reads *A normal person* until NM-T16.
- **Commit:** `feat(names): Character takes ContribRPCharacter — short descriptions shown, the contrib's cmdset off`

### Task NM-T3 — The search: exact first, and what still finds what
- **Goal:** Typing an item's exact name finds that item, and every existing command still finds its target.
- **Dependencies:** NM-T2.
- **Approach:** `Character.get_search_result(self, searchdata, candidates=None, **kwargs)`: call `super()`; when there is more than one result and `searchdata` is a string, keep those whose key or an alias equals it, case-insensitively, after any `N-` prefix is set aside; if none is exact, return the results unchanged (NM10). Docstring: what the contrib's parser matches (`rpsystem.py:433–445`) and why the narrowing is done on the result and not in the parser. Error handling: anything unexpected in the narrowing returns the unnarrowed list.
- **Testing** (`tests/test_names_search.py`): *leather* against *leather strap*, both orders; `1-leather` with two *leather* and a *leather strap*; a creature by key and by alias, and `2-rabbit`; a character by a word of its description and by several; a character's key finds nothing for a player and finds it for a Builder who matched nothing else; `me`; a dbref through `evennia.search_object` (TR6, UP18); `hunt`, `craft … from`, `pay … to`, `teach`, `get … from` each reach their target (one test per command, on `caller.search`'s arguments as the command passes them: `commands/hunting_commands.py:76`, `commands/crafting_commands.py:315`, `:324`, `:1222`, `commands/currency_commands.py:249`).
- **Mutations (NMM5–NMM6):** drop the narrowing (the leather test must fail); narrow on key only (the alias test must fail).
- **In-game protocol:** carry *leather* and a *leather strap*: `drop leather` drops the leather. Two rabbits: `hunt rabbit` lists `1-rabbit`, `2-rabbit`.
- **Commit:** `feat(names): an exact name wins the search (NM10), with the commands' targets pinned`

### Task NM-T4 — The backfill
- **Goal:** A character made before the contrib keeps its recogs across a reload and shows no key.
- **Dependencies:** NM-T2.
- **Approach:** `world/character_migrations.py`: `backfill_names()` on `backfill_hunting`'s pattern (`:54`) — for every character in `Character.objects.all_family()`: create `_recog_ref2recog` and `_recog_obj2recog` when missing, `pose` and `pose_default` when missing, set the placeholder short description *a quiet traveller* when `_sdesc` is missing or empty, and remove a persistent `rpsystem_cmdset`. Idempotent; one broken character does not stop the batch; returns a summary string for `@py`.
- **Testing** (`tests/test_names_migration.py`): a character stripped of the four Attributes gets them and the placeholder; a recog added after the backfill is in `attributes.get("_recog_obj2recog")` and survives a fresh `RecogHandler`; **the same add before the backfill is lost** (the bug, pinned red first); a character with a description keeps it; a second run changes nothing.
- **Mutations (NMM7):** skip `_recog_obj2recog` (the survives test must fail).
- **In-game protocol** (staff, a development database): `@py from world.character_migrations import backfill_names; self.msg(backfill_names())`, twice; the second run reports nothing changed.
- **Commit:** `feat(names): backfill_names — recog storage and a placeholder description for older characters (Names UQ7)`

---

## 7. Component N2 — Knowing people

### Task NM-T5 — `recog` and `forget`
- **Goal:** A player can attach a name to a person in the room, list the names they hold, and drop one from anywhere.
- **Dependencies:** NM-T3.
- **Approach:** new `commands/names_commands.py`. `CmdRecog`: `recog` lists (label and current description, as the contrib does, `rpsystem.py:1170`); `recog <description> as <name>` searches the room's **characters** other than the caller, through `caller.search(..., candidates=…)`, and calls `caller.recog.add`. Both `SdescError` and `RecogError` are caught and shown as one line. `CmdForget`: `forget <name>` looks the label up in `caller.recog.all()`, case-insensitively, and removes it; an unknown label and a label held for two people are each a plain line. Added to `CharacterCmdSet`. Text read against the Tone Guide.
- **Testing** (`tests/test_names_commands.py`): recog by one word and by `2-lanky`; the label then shows in `get_display_name` and finds the person by `search`; a creature, an item and oneself are refused; an empty label and one over 60 characters are refused without a traceback; `forget` in another room; `forget` of an unknown label; the list. Two viewers hold different labels for one person and each sees their own.
- **Mutations (NMM8–NMM9):** let candidates be the room's contents (the creature test must fail); resolve `forget` against the room (the other-room test must fail).
- **In-game protocol** (two players, A and B, in one room): B `recog <a word of A's description> as Tess` → the room lists *Tess*; A still sees B by description; B walks out, `forget Tess`, walks back → the description again.
- **Commit:** `feat(names): recog and forget — a name is the knower's, and can be dropped anywhere (Names UP5, UP7, UP8)`

### Task NM-T6 — `introduce`
- **Goal:** A player can give their true name to the room or to one person.
- **Dependencies:** NM-T5.
- **Approach:** `CmdIntroduce` in `commands/names_commands.py`. `introduce` — every puppeted character in the room reads one line that names the speaker through `$You()` and gives the key — *… introduces themselves as Maren* in shape, the wording read against the Tone Guide (the project already writes singular *they*, `typeclasses/characters.py:505`) — resolved **before** any recog is written, so a stranger reads the description and the name in one line. Then, for each hearer without a recog for the speaker, `hearer.recog.add(speaker, speaker.key)` (NM5); a failure for one hearer is logged and does not stop the others. `introduce to <description>` — the target reads the name and gets the recog; the room reads that an introduction was made, without the name (OQ-NM3). A statue hears nothing.
- **Testing:** a hearer without a recog gains the key; a hearer with their own label keeps it; the line reaches each reader with the name they had before the command; the speaker gains nothing; `introduce to` writes one recog and the bystander's line has no key; a statue in the room is unchanged; a hearer whose recog Attributes are missing (no backfill) does not raise.
- **Mutations (NMM10–NMM11):** overwrite an existing recog (the keeps test must fail); write the recog before the line (the line test must fail).
- **In-game protocol** (A, B, C in one room; C has `recog`ed A as *Liar*): A `introduce` → B's room list shows A's key, C's still *Liar*; both read the name in the line.
- **Commit:** `feat(names): introduce — a true name given to the room, never over a hearer's own (Names UP6; NM5)`

### Task NM-T7 — `say`, `emote`, `pose`, and the pose that stays behind
- **Goal:** Speech and emotes name people as each reader knows them, and a pose does not travel.
- **Dependencies:** NM-T2.
- **Approach:** `commands/default_cmdsets.py`: add the contrib's `CmdEmote`, `CmdSay` and `CmdPose` (`rpsystem.py:903`, `:946`, `:1022`) — they replace Evennia's `say` and `pose` by key (K7). `Character.at_post_move`: `self.db.pose = ""` before the look (UP19). `whisper` is Evennia's and goes through `at_pre_say` (`rpsystem.py:1579`); read `evennia/commands/default/general.py`'s `CmdWhisper` and pin what the receiver reads.
- **Testing:** `say` reaches a stranger with the description and a recogniser with the label; `emote /lanky` names the third person per reader; a failed reference tells only the emoter; `pose` shows in `get_display_name(looker, pose=True)`; after a move the pose is the default; `whisper`'s receiver line has no key.
- **Mutations (NMM12):** drop the reset (the move test must fail).
- **In-game protocol:** A `pose is warming her hands by the fire`; B `look` → the line; A walks out and back → *is here.*
- **Commit:** `feat(names): the contrib's say, emote and pose; a pose is left at the door (Names K7, UP19, UP20)`

### Task NM-T8 — One line per character
- **Goal:** The room lists each awake character on a line of its own, with its pose.
- **Dependencies:** NM-T7.
- **Approach:** `typeclasses/rooms.py::get_display_characters` (`:320–335`): one line per character from `room_text.room_lists(...)["characters"]`, each `c.get_display_name(looker, pose=True, **kwargs)`, first letter capitalised; the *Characters:* heading goes. Statues stay under *You see:* (`:337–357`). `world/client_state.py::room_snapshot` (`:235`) keeps names without poses (the panel is a list of names); say so in its docstring. `world/room_text.py`'s docstring if it describes the comma line.
- **Testing** (`tests/test_room_look.py`): two awake characters give two lines, each with a pose; the viewer is not listed; a statue is under *You see:* and not on a line; `room_lists=False` still gives `""`; the webclient snapshot's `characters` has no pose text.
- **Mutations (NMM13):** join with commas (the two-lines test must fail).
- **In-game check:** `look` in a room with two others.
- **Commit:** `feat(names): the room lists a character per line, with its pose (Names K8)`

---

## 8. Component N3 — Every name through a looker

### Task NM-T9 — The commands' room messages
- **Goal:** No command tells a room an actor's key.
- **Dependencies:** NM-T2.
- **Approach:** the thirteen sites in `commands/` (§4: one by `.key`, twelve by `get_display_name()` with no looker). Each becomes `msg_contents("$You() $conj(verb) …", from_obj=caller, exclude=caller)`; `exclude` stays, because the actor's own line is sent separately and often says more. `commands/foraging_commands.py:240` is a possessive: `$Your()` (`funcparser.py`, `funcparser_callable_your_capitalize`). `commands/currency_commands.py:324` names two characters: `$You()` and `$you(target)` with `mapping={"target": target}`. `commands/work_commands.py:468`, `:609` prefix a task's `done_room`/`begin_room` text, which is written in the third person — keep the text, change the prefix. Item and node names in the same lines keep `get_display_name(looker)`-free forms only where they are not characters.
- **Testing:** per site, one test with a stranger and a recogniser in the room: each reads their own name for the actor, and the actor's key appears in neither line unless it is the recogniser's label. Existing tests that assert the old lines change to the new readers' text.
- **Mutations (NMM14):** restore one site to `get_display_name()` with no looker (its test must fail).
- **In-game protocol:** B has `recog`ed A; C has not. A `eat bread`, `forage`, `work water` → B reads the label, C the description.
- **Commit:** `fix(names): commands tell the room who acted as each reader knows them (Names K4)`

### Task NM-T10 — The typeclasses' room messages, and the census
- **Goal:** No typeclass tells a room a character's key, and a test fails when a new message does.
- **Dependencies:** NM-T9.
- **Approach:** `typeclasses/characters.py:1553`, `:1597`, `:1965`, `:2001`, `:2018` and `typeclasses/creatures.py:84` (the killer). `world/fatigue.py:243`, `:245`: `FALL_ROOM` and `WAKE_ROOM` become `$You()` templates and lose `{name}`. **The census,** `tests/test_names_census.py`, on `TestPushCensus`'s pattern: walk the AST of every module in `commands/`, `typeclasses/` and `world/`; for each call to `msg_contents`, fail when the message expression contains an attribute `.key` or `.name` of a name bound to a character in a small allow-nothing list of receivers (`caller`, `char`, `self` in `Character`, `killer`, `target`, `student`, `teacher`), or a call to `get_display_name` with no argument. Sites that name a creature or a corpse are listed by file and function with their reason (§4, *not a character*). The statue's two sites are listed as NM-T11's and removed there.
- **Testing:** the five sites as in NM-T9; the census passes; the census **fails** on a fixture module with each of the two faults.
- **Mutations (NMM15–NMM16):** restore `f"{char.key} gets up."` (the census and its site test must fail); delete the no-looker rule from the census (the fixture test must fail).
- **In-game protocol:** A `rest`, then stands; B (recogniser) and C (stranger) read their own names for A.
- **Commit:** `fix(names): typeclasses name the actor per reader; a census keeps every room message so (Names UP10, UP11)`

### Task NM-T11 — The statue and the body
- **Goal:** A statue and a player's body are named as the looker knows the person.
- **Dependencies:** NM-T10.
- **Approach:** *Statue* (K2): `return_appearance` (`:603–614`) names the sleeper with `super().get_display_name(looker)`; the two messages (`:503`, `:564`) through `$You()`/`$Your()`. `get_display_name` already resolves per reader (§4, run). *Body* (K3): `at_character_death` creates the corpse with `key="corpse"` and the alias `body` (`:1412–1417`). `PlayerCorpse.get_display_name(looker, **kwargs)`: *the body of <owner as the looker knows them>*, from the stored `owner` id; an owner that no longer exists gives *a body*. `world/death_contract.py:142`'s help line becomes `get <item> from corpse`. Read `typeclasses/corpse.py::PlayerCorpse` (`:237`) for every place the key is formatted, and `world/room_text.numbered_names` for how two bodies in one room are listed.
- **Testing:** the statue's look and both messages for a stranger and a recogniser; a body listed in the room and looked at, for a stranger, a recogniser and the owner; two bodies in a room are told apart by `1-corpse`; the owner's `get … from corpse` during grace; a deleted owner; `tests/test_death_contract.py`'s keys follow.
- **Mutations (NMM17–NMM18):** key the corpse by the owner's key again (the stranger's test must fail); resolve the body's name with no looker (the recogniser's test must fail).
- **In-game protocol:** A logs out → B (recogniser) sees *stone statue of <label>*, C the description; staff kills A's character on a test database (`@py … at_character_death()`), B and C `look` → the body by label and by description.
- **Commit:** `fix(names): the statue and the body are named per reader (Names K2, K3)`

### Task NM-T12 — The teach offer, and the arrival line
- **Goal:** A lesson's offer names the teacher as the student knows them, and a newcomer's arrival is seen.
- **Dependencies:** NM-T10.
- **Approach:** `commands/crafting_commands.py:1271`: `learn {recipe} from {word}`, where the word is the student's recog for the teacher when there is one and otherwise the first distinguishing word of the description (a helper in `world/`, tested alone; UP15). The student's search at `:1456` already takes either (NM-T3 pins it). *The arrival line* — Arrival's AV8 left it to this slice (`docs/PolishedWorld_Arrival_Decomposition.md` §2): `world/arrival.py::arrive` tells the room it enters, through `$You()`, after the move; the wording is the Newcomer note's §15, read then.
- **Testing:** the offer for a recogniser and a stranger; `learn … from <that word>` succeeds for both; the arrival line reaches a bystander with the description and not the newcomer; no line when the character already stands in the room (Arrival's rule for the push).
- **Mutations (NMM19):** print the key in the offer (the stranger's test must fail).
- **In-game protocol:** B (stranger to A) is offered a recipe by A and types the line as printed.
- **Commit:** `fix(names): the teach offer names the teacher as the student knows them; a newcomer's arrival is seen (Names K5; Arrival AV8)`

### Task NM-T13 — `trade`
- **Goal:** A trade names the other party as each side knows them.
- **Dependencies:** NM-T10.
- **Approach:** first an inventory, written into this document's *Shipped* line: every site in `world/barter.py` and in the barter contrib's commands and handler that formats a party's `.key` (§4), with who reads it. Then: the project's own sites (`world/barter.py:170`, `:436`, `:441`, `:493–503`) take `get_display_name(reader)`; the inherited ones are overridden where the project already overrides the command (`CmdPWTrade`, `CmdPWOffer`, `CmdPWDecline`, `CmdPWStatus`, `CmdPWAccept`, `CmdPWEvaluate`) and otherwise by one override of the base's `parse` that builds `str_other` per reader (`barter.py:414–421`). Log and ledger lines keep the key (`world/barter.py:726–727`): they are out of character. **If the inventory finds more than a task's worth, the task stops at the inventory and splits** (OQ-NM4).
- **Testing:** start, offer, accept, decline, status and finish, each read by a stranger and by a recogniser on either side; the ledger still carries keys.
- **Mutations (NMM20):** restore `caller.key` in the decline line.
- **In-game protocol:** A and B, strangers, trade one item; neither reads the other's key at any step.
- **Commit:** `fix(names): trade names the other party per reader (NM15)`

### Task NM-T14 — `who`, and the account's commands
- **Goal:** `who` tells a player how many are abroad, not who.
- **Dependencies:** NM-T2.
- **Approach:** new `CmdWho` in `commands/` on Evennia's (`evennia/commands/default/account.py:439`), added to `AccountCmdSet`: an account with Builder gets `super().func()`; anyone else one line with the count from `evennia.SESSION_HANDLER.account_count()` (`evennia/server/sessionhandler.py:687`). Then the inventory UQ8 asks for: list every command in `AccountCmdSet` and `SessionCmdSet` at 6.1.0 that prints an account name (`page`, the channel commands, `ooc`/`ic`, `charcreate`'s listing), with one line each on what a player reads, into this document; they are out of character and stay, unless one lists other accounts to a player unasked — that one is brought to Adam (OQ-NM5).
- **Testing:** a player's `who` has a number and no account name; a Builder's has the table; zero, one and several connected read as sentences.
- **Mutations (NMM21):** give players the table (the no-name test must fail).
- **In-game check:** `who` as a player and as staff.
- **Commit:** `feat(names): who counts for players and lists for Builders (Names K1)`

---

## 9. Component N4 — The short description in character creation; N5 — the webclient; N6 — close-out

### Task NM-T15 — The vocabulary, the composer and the Builder's command
- **Goal:** A short description can be built from three choices and set by staff.
- **Dependencies:** NM-T2.
- **Approach:** new `world/sdesc.py`: three tuples — builds (about ten), features (about twenty), nouns (*man, woman, youth, old man, old woman, figure*) — and `compose(build, feature, noun)` returning *a lanky, red-bearded man* with the right article; `MAX_LENGTH = 40`; `validate(text)` for free text. **The lists are put to Adam at this task's STOPP before the commit** (NM7, UQ9), read against the Tone Guide. `@sdesc <character> = <text>` in `commands/admin_commands.py`, `perm(Builder)`, target by dbref or global search, through `validate` and `target.sdesc.add`; it pushes the room (NM-T17 adds the push's census row if this task lands first).
- **Testing:** every combination of the three lists is at most 40 characters and passes the contrib's own `add` (`rpsystem.py:692–736`); the article; `validate` refuses an empty text, one over 40 and one with an emote marker; the command sets, refuses a player, and refuses a non-character.
- **Mutations (NMM22):** raise `MAX_LENGTH` to 60 and add one long build (the every-combination test must fail).
- **In-game check:** staff `@sdesc #<dbref> = a weathered woman in a wool cloak`.
- **Commit:** `feat(names): the short description's vocabulary and composer, and @sdesc for Builders (Names UP1, UP2)`

### Task NM-T16 — The appearance step
- **Goal:** A new character chooses how strangers see them, once, before the final yes.
- **Dependencies:** NM-T15.
- **Approach:** `world/chargen_menu.py`: `node_confirm_profession`'s *yes* goes to a new `node_appearance` (three numbered lists, one line of input parsed like `node_allocate`'s, the draft carrying the three choices) and `node_confirm_appearance` (the composed line, *This cannot be changed here. Create this character?*, *yes* → `node_done`, *back*). The *cannot be changed* sentence moves from the profession's confirmation to this one. `node_done` writes `caller.sdesc.add(...)` with the other writes, before `arrival.arrive` and the push (Arrival AV5); a draft without the three choices — a menu saved before this task — goes back to `node_appearance` and is not written (the pattern of `_half_done`, `:184`). EvMenu makes every public function in the module a node (Arrival's *Shipped* note for AV-T2): helpers are underscored.
- **Testing** (`tests/test_chargen_menu.py`): the full path writes the composed description; each choice out of range is refused with the list again; *back* returns with the draft intact; a resumed draft without choices lands on the appearance node; `node_done` reached without choices writes nothing and does not set the flag; the existing paths stay green.
- **Mutations (NMM23–NMM24):** write the description after the push (an ordering test must fail); let `node_done` fall back to *A normal person* (the no-choices test must fail).
- **In-game protocol:** a new account through the menu; a second player in the temple sees the newcomer arrive (NM-T12) by the description just composed.
- **Commit:** `feat(chargen): a new character composes how strangers see them (Names K9)`

### Task NM-T17 — The pushes
- **Goal:** The webclient's room panel follows a recog, a forget, an introduction, a pose and a changed description.
- **Dependencies:** NM-T6, NM-T8.
- **Approach:** `recog`, `forget`: `client_state.push(caller, "room")`. `introduce`: one push per hearer whose recog was written. `pose` and `@sdesc`: `client_state.push_room(room)` — the contrib's `CmdPose` is subclassed for the one line. `TestPushCensus.SITES` gains each row in the same commit (lessons 312, 320).
- **Testing:** each command's push reaches the right reader and no other; the census.
- **Mutations (NMM25):** push the room on `recog` (the no-other test must fail).
- **In-game protocol** (webclient): B `recog`s A → B's panel changes, C's does not.
- **Commit:** `feat(webclient): the room panel follows recog, introduce, pose and @sdesc (Names UP22)`

### Task NM-T18 — Merge
- **Goal:** `feature/names` is on `main`.
- **Approach:** the whole suite, parallel, with `"#10"` stashed; `git merge-tree` for the predicted tree; PR, merge commit; the tree compared.

### Task NM-T19 — Documentation
- **Goal:** Every document that describes names says what shipped.
- **Approach:** this document's *Shipped* lines and DONE; the Names note annotated (which UP and UQ items shipped, and NM3, NM4, NM10, NM11, NM15 as findings); Combat Design §6's *not annotated* list shortened by Names UP16–UP18; Testing Reference (UP18's gotcha: target by dbref, never by name; the two-player protocol's setup); Evennia Reference (the contrib's cmdset at creation, the search's word-start match, `$You()` and a leading colour code); BACKLOG *Strangers by description* DONE, *First-steps hints* annotated with UP23, *A screen-reader pass* annotated; roadmap, README, the System Map's seam table; the tag if L6 is up by then.

---

## 10. Open questions (each with the task that closes it)

- **OQ-NM1** — Why does `tests.test_report_commands.TestExport.test_one_line_per_report_with_its_fields` error under the class change, when it passes alone on `main`? *NM-T2, before anything else is fixed.*
- **OQ-NM2** — Does the persistent `RPSystemCmdSet` come back on a reload after `cmdset.remove`? The set is stored by path on the object. *NM-T2: a test that reloads the cmdset handler; NM-T4's backfill is the fallback.*
- **OQ-NM3** — `introduce to <one person>`: does the room read that an introduction was made? *Leaning: yes, without the name. NM-T6's STOPP.*
- **OQ-NM4** — Is `trade` one task? *NM-T13's inventory.*
- **OQ-NM5** — Does any account-level command list other accounts to a player unasked? *NM-T14's inventory.*
- **OQ-NM6** — The placeholder for older characters, *a quiet traveller*: one text for all, so several staff characters share it until `@sdesc`. *NM-T4; identical descriptions are allowed (UP4).*
- **OQ-NM7** — A name with a digit and a hyphen in it (*2-handed sword*) against `N-name`. No such key exists in the recipe data today; unchecked for seeded objects. *NM-T1.*

---

## 11. Consequences worth reading twice

- **A player can no longer type another player's key.** Every protocol in the Testing Reference that has one player name another changes in this slice, and every later one targets by description, recog or dbref (TR6).
- **The search matches the start of any word.** `get strap` finds a *leather strap*. That is more forgiving than today, and NM10 keeps it from being less exact.
- **Sixteen tests break on one line.** The number is the measure of how much of the suite reads a name — and why the class change is its own task.
- **Until NM-T16, everyone is *A normal person*.** The branch is not playable between NM-T2 and NM-T16, which is why it is one branch and one merge.
- **Combat's TR4 is this slice's census, extended.** When ML writes its first line, the census already fails a `.key` in a room message; TR3's role keys are the form NM-T9 uses for two characters.
- **Nothing ticks, and nothing races.** A recog is written on its owner, by its owner's command or by one `introduce` call that runs to its end; recognition is a dictionary read when text is drawn (Names UG6).
