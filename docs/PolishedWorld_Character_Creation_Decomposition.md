# PolishedWorld — Character Creation Decomposition

> **Rev 1 · 2026-10-26** — first version. Decomposes the roadmap's *Legend character creation* alpha prerequisite (alpha entry (A), order fixed by (F)) into four components and ten tasks, against live source read the same day (`main` at `a60b73f`, tree `a25c1c9`; Evennia 6.1.0 from PyPI; `Legend.pdf` core rules). The framing decision is the one that matters: **no dice.** Legend's chargen was written for a table with a Games Master; this is an always-online world with free characters, so the design borrows from the games that solved the same problem (OSRS, Tibia, Albion) and keeps Legend where Legend still fits. Decisions CC1–CC10 in §2.
> **Canonical:** `docs/PolishedWorld_Character_Creation_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Status:** PLANNED (no code yet).
**Feature branch:** `feature/character-creation` (one branch, one merge, as the alpha content epic). Create it with `git switch -c feature/character-creation --no-track origin/main` (lesson 64).
**Rough scope:** 10 tasks, 3–4 sessions at 5 h/week (CC1 1 · CC2 0.5–1 · CC3 1.5–2 · CC4 0.5). Smaller than the roadmap entry feared, because §2 removes the roller, the reroll policy and the backfill.
**Philosophy:** skynda långsamt — variation comes from two choices the player makes on purpose, and from play; nothing is rolled.

---

## 1. Why this feature

Every character today is the same character: seven characteristics at 10 (`typeclasses/characters.py:195–237`), Craft at DEX+INT = 20 (line 387), health at CON × 2 = 20 (line 304), fixed skill bases (perception 25, stealth 20, athletics 25, hunting 25). The alpha's fourth prerequisite exists so that the stat-derived mechanics vary — and three later prerequisites read what this one sets: E.2 is calibrated against how fast Craft rises (`world/improvement.py:19–25` adds the whole INT to the roll; the Craft base is DEX+INT), weight's limit is STR+SIZ, and the recipe ladder's rung 20 (`cloth`, `leather`) is reachable only from Craft ≥ 20. That is why roadmap (F) puts this feature first among the four that remain.

The roadmap entry describes Legend's process in full: roll *or* allocate, derived attributes, Cultural Background, Profession, free skill points, community, starting gear, starting money. §2 takes a position on each.

## 2. Decisions locked 2026-10-26 (CC1–CC10)

**CC1 — No dice: Points Build only (Legend p.9).** 80 Characteristic Design Points over the seven characteristics, each 6–18, all points spent. Both Random Roll options (p.8–9) are rejected: at a table a roll is made once, under a Games Master's eye; in a free online world it is made until it shows 18s, and a reroll policy is a second system to build and police. Points Build is deterministic, Legend-canonical, and the only method under which the ladder's rung 20 is a *choice* (see CC6). The two optional rules on p.9 (re-roll a 6 or less; the two-point swap) apply to rolled characteristics and are not adopted. *Alternative rejected:* Random Roll Assign with one re-roll — unpredictable against rung 20 and a magnet for alt-spam.

**CC2 — One identity choice: Profession. Cultural Background is out of the alpha.** Legend's culture table (p.15–18) has four columns: Common-skill bonuses, Combat Styles, Advanced Skills, Starting Money. Three are outside the alpha (combat; CC3) and the first has nothing to land on — the culture bonuses go to Culture (Own), Lore (Regional), Survival and weapon styles, none of which exist among the five skills. Profession is therefore the single choice at creation, as Tibia's vocation and WoW's class are: it is what a player picks to *be*. Cultural Background is deferred to `docs/BACKLOG.md` with the trigger *Culture / Lore skills exist* (Rev 49); the existing *Cultural-Background gating of professions* entry stays BLOCKED on it. Community and family (p.25–26) have no mechanic and are struck for the alpha.

**CC3 — No starting money, no starting gear.** Money: gold is minted in one place only, the GameGold exchange (`docs/PolishedWorld_Economic_Philosophy.md` §4 *Gold enters the world at exactly one point*), and the faucet *moves* gold out of the Treasury; a chargen grant would be a second faucet with no sink argument behind it, so Legend's Starting Money (4D6 × 10/20/75 silver, p.18–19) is struck. Gear: pillar 1 — every item is crafted by a player — and the ladder's rung 0 is the bootstrap answer: the stone knife, the waterskin and the rest of rung 0 are makeable from nothing (AC5.1). *Alternative rejected:* a Treasury transfer at creation.

**CC4 — Scope of the derivation.** The seven characteristics are stored (today's traits, re-based). Derived **now:** Hit Points (CC9). Derived **at Stage 5**, when their readers exist: Damage Modifier (STR+SIZ, p.10) and Strike Rank ((INT+DEX)/2, p.13). **Not adopted:** Magic Points (= POW, p.12; no magic in the alpha) and the Improvement Roll Modifier (CHA, p.12): the project's improvement model is XP-per-level with the whole INT in the roll (decision log, *Skill progression → XP-per-level*; `world/improvement.py`), and the CHA table governs the *number* of rolls in a story-based campaign, which has no counterpart here. The roadmap entry's phrase *"Improvement Roll modifier"* is corrected by pointer (Rev 30). **Consequence, stated plainly:** POW and CHA are stored with no reader in the alpha; see §13.

**CC5 — Common-skill bases derive from characteristics (Legend p.13–14).** The fixed bases are a placeholder from the same era as the 10s. With characteristics varying, a chargen that re-derives only Craft would leave four of five skills identical across the cohort and most of the 80 points without a reader. So: Athletics = STR+DEX, Perception = INT+POW, Stealth = DEX+INT, Craft = DEX+INT (unchanged), and Hunting — the project's own skill, not Legend's — gets a base chosen in CC1.1 (§12, OQ1). At 10s this is 20 everywhere, five lower than today's perception and athletics; nothing migrates (CC7), and the XP model needs no write: an absent `skill_xp` entry is derived from `.current` on read (`world/progression.py`; `tests/test_skill_xp.py` docstring), so a chargen that sets `.current` is already consistent with it.

**CC6 — A profession is recipe grants plus a skill bonus; Free Skill Points are out of the alpha.** Legend's own crafter is instructive: *Craftsman* (p.20) gets Craft (Any) as an Advanced skill at its base and bonuses to Evaluate, Influence and Persistence; the Craft score itself comes from Free Skill Points (250, max 30 per skill, p.25). FSP would be a third allocation screen over five skills; deferred to `docs/BACKLOG.md` (Rev 49) with the trigger *more Common skills than the alpha's five*. In its place the profession carries a Craft bonus — a deliberate adaptation, written down as one: with a floor of 6 the lowest Craft base is 12, and a crafting profession's bonus is what makes rung 20 a thing a crafter *chooses* rather than a thing the ladder withholds. The existing BACKLOG entry *Profession Common-Skill bonuses* has the trigger *a real chargen with per-character characteristics*; it fires here and is closed by CC2.1. The numbers are data, locked at task time (lesson 98); the table in CC2.1 is the proposal.

**CC7 — No backfill, no re-spec, and `CmdChooseProfession` is replaced.** The only characters that exist are development characters; the persistent alpha instance opens after this feature ships and is wiped at alpha close-out (roadmap (D3)). A one-time re-spec would be a migration for a population of one, and `world/currency.py`'s rule is the model: derive, never backfill. Existing characters keep their 10s and their `skill_xp`. The profession command (`commands/character_commands.py:353`) goes: the EvMenu calls the same `grant_profession()` (`world/professions.py:62`), and a one-time choice should have one home. *Alternative rejected:* a flag-gated `respec` command.

**CC8 — The menu is launched from the character's first puppet, not from `menu_login`.** Read live in Evennia 6.1.0: `MULTISESSION_MODE` (0) and `AUTO_CREATE_CHARACTER_WITH_ACCOUNT` (True) are at their defaults in `server/conf/settings.py`, so the character is created *inside* `Account.create()` (`evennia/accounts/accounts.py:1117`) with `at_object_creation`'s 10s, before the player sees anything, and `at_post_login` auto-puppets it. The `menu_login` contrib ends at `sessionhandler.login()` (`node_quit_or_login`) and knows nothing about the character. The honest hook is `Character.at_post_puppet` (`typeclasses/characters.py:459`): if `db.chargen_complete` is not set, start the chargen `EvMenu` with `persistent=True` (survives a disconnect mid-creation — a cohort member on a phone will disconnect) and `auto_quit=False` (there is no world to fall back into). The roadmap entry's *"flowing from the existing `menu_login` screen"* is corrected by pointer.

**CC9 — Hit Points stay CON × 2, and the health `descs` are fixed in this epic.** Legend's table (CON+SIZ per location, p.11) belongs to hit locations, which are Stage 5. CON now spans 6–18, so the max spans 12–36 — and the `descs` table, keyed on absolute 0–100 (`docs/BACKLOG.md` *Health `descs` use a 0–100 scale*), goes from misleading to wrong for everyone. The reader change that entry asks for lands as CC1.2; the entry closes with it.

**CC10 — Order among the alpha's remaining work:** this feature first, then weight (decomposition only), per-recipe mastery, E.2 — roadmap (F), recorded 2026-10-26. (F) carries its own caveat: it holds only while characteristics vary at creation; CC1 is what keeps it true.

## 3. Verified source anchors (read 2026-10-26)

| Anchor | Where | What it says |
|---|---|---|
| Points Build | `Legend.pdf` p.9 | 80 points · 1 per point · 6–18 · all spent |
| Common-skill bases | p.13–14 | Athletics STR+DEX · Perception INT+POW · Stealth DEX+INT · Evaluate INT+CHA · Lore INT×2 · Persistence POW×2 |
| Previous Experience | p.15 | culture → profession → free skill points, in that order |
| Culture table columns | p.15–18 | Common-skill bonuses · Combat Styles · Advanced Skills · Starting Money (4D6 × 10/20/75) |
| Craftsman | p.20 | Evaluate +20%, Influence +5%, Persistence +5%; Craft (Any) as Advanced skill |
| Free Skill Points | p.25 | 250 · max 30 per skill · an Advanced skill costs 10 and starts at base |
| Characteristics improve in play | Adventurer Advancement, p.68ff | Improvement Rolls raise skills *and* characteristics |
| Seven `stats.add(base=10)` | `typeclasses/characters.py:195–237` | the placeholder |
| Health base | line 304 | `con.value * 2` · helper at line 534 recalculates on CON change |
| Skill bases | lines ~330–395 | fixed 25/20/25/25; Craft = `dex.value + int.value` (387) |
| `at_post_puppet` | line 459 | C.3 snapshot of each skill's `.current` for `progress` |
| `grant_profession()` | `world/professions.py:62` | idempotent via `learn_recipe()`; unknown key → warning, `[]` |
| `PROFESSIONS` | line 54 | `weaver`, `tanner`, `cobbler`, `generalist` → recipe lists |
| `CmdChooseProfession` | `commands/character_commands.py:353` | one-time, `cmd:all()`, knowledge only; no test names it |
| Login path | `evennia/accounts/accounts.py:1117`, `:1709` | character created in `Account.create()`; auto-puppet in `at_post_login` |
| `EvMenu` | `evennia/utils/evmenu.py` | `persistent`, `auto_quit`, `cmd_on_exit`, `startnode` |
| XP floor on read | `world/progression.py`, `tests/test_skill_xp.py:25–33` | absent entry = `xp_threshold(.current)`, no write |

**Measurement, tests that assume the static character (STOPP 0):** two files read stat defaults directly (`tests/test_rest.py:441` health.max; `tests/test_skill_xp.py:155` craft at 20) and the `test_skill_xp.py` docstring states the old bases. `tests/test_min_skill_ladder.py` pins rungs, not a starting Craft. The other nineteen `20`s in assertions are progress-bar widths. The test migration is small; the prose sites are the larger count (§13).

## 4. Dependency graph

```
CC1.1 world/chargen.py (pure: validate + derive + apply)
  ├─ CC1.2 health descs by percent()          (closes BACKLOG entry)
  ├─ CC2.1 PROFESSIONS gains skill_bonus; grant_profession applies it
  │     └─ CC2.2 registry/ledger check that every bonus key is a real skill
  └─ CC3.1 menu nodes (allocate → confirm → profession → confirm → done)
        ├─ CC3.2 launch from at_post_puppet; persistent; gate until done
        └─ CC3.3 remove CmdChooseProfession; help chargen; prose sweep
              └─ CC4.1 docs close-out (Evennia Ref EvMenu §, Testing Ref, roadmap, BACKLOG closes)
                    └─ CC4.2 merge
```

## 5. Component CC1 — Characteristics and derivation (Claude)

### Task CC1.1 — `world/chargen.py`: validate a Points Build, derive skill bases, apply to a character
- **Goal:** A pure, tested module that turns a seven-key allocation into a character's characteristics, health and skill bases, refusing anything Legend p.9 forbids.
- **Dependencies:** None.
- **Approach:** Three functions. `validate_allocation(alloc: Mapping) -> list[str]` returns every violation (missing key, non-integer, outside 6–18, sum ≠ 80) so the menu can print all of them at once. `derive_skill_bases(stats: Mapping) -> dict` implements CC5 (`athletics`, `perception`, `stealth`, `craft`, `hunting`; OQ1 fixes hunting's pair). `apply_allocation(character, alloc)` sets each stat's `.base` **and** `.current` (CounterTrait: `.add(base=N)` pins current at creation, but a later `.base = N` does not move `.current` — gotcha file), calls the existing health-recalculation helper (line 534), rewrites every skill's `.base` and `.current` from `derive_skill_bases()`, and returns the derived dict for the confirmation screen. It writes nothing to `skill_xp` (CC5). Constants `DESIGN_POINTS = 80`, `CHAR_MIN = 6`, `CHAR_MAX = 18` live in the module, not in settings — they are rules, not knobs.
- **Testing** (`tests/test_chargen.py`, `EvenniaTestCase` for the pure functions, `EvenniaTest` for `apply_allocation`): sum 79 and 81 refused; 5 and 19 refused; a missing key refused; the all-10s-plus-10 allocation (10×6 + 20 = 80 — the "one 20" trap) refused on the 20, not the sum; a valid allocation applied reads back on every stat's `.base` and `.current`; health max = CON × 2 after apply; each skill's `.current` equals the derived base; `skill_xp` store untouched (TestReadDoesNotWrite's shape). Negative cases print their own type first (Testing Ref §11k).
- **Mutations:** `CHAR_MIN` → 5 (the 5 case must fail); drop the `.current` write (the read-back test must fail); drop the health recalculation (the health test must fail).
- **Commit:** `feat(chargen): points-build validation, derived skill bases and apply_allocation`

### Task CC1.2 — Health `descs` read `percent()`, not the absolute value
- **Goal:** The health label is right for a max of 12 and a max of 36.
- **Dependencies:** CC1.1 (the reason the fix is now).
- **Approach:** The BACKLOG entry's own prescription: the reader follows the gauge's `percent()`. Re-key the table in `at_object_creation` (line ~256) on percent bands and make the reader compare against percent; the table is read as lower bounds, which is the open question in the neighbouring entry *`descs` tables are read as upper bounds but shaped like lower bounds* — this task takes the lower-bound reading for health only and says so in the entry.
- **Testing:** 20/20 reads `healthy`; 36/36 reads `healthy`; 6/12 and 18/36 read the same band; 0 reads the bottom band. A spy on the reader proves the percent path ran (§11f).
- **Commit:** `fix(health): descs follow percent(), not the absolute value (BACKLOG closed)`

## 6. Component CC2 — The profession package (Claude)

### Task CC2.1 — `PROFESSIONS` carries a skill bonus; `grant_profession()` applies it
- **Goal:** A profession is one package: recipes known and a skill bonus applied, idempotently.
- **Dependencies:** CC1.1 (bonuses sit on derived bases).
- **Approach:** `PROFESSIONS` becomes `{"weaver": {"recipes": [...], "skill_bonus": {"craft": 10}}, ...}`. `grant_profession()` keeps its contract (returns newly learned recipe names) and additionally applies the bonus to each named skill's `.base` and `.current` — guarded by `db.profession` so a re-grant at `@reload` adds nothing (the same idempotence `learn_recipe()` already has for knowledge). Proposed values, locked at task time: weaver / tanner / cobbler `craft +10`; generalist `craft +5` (broader knowledge, smaller bonus). A `hunter` profession (`hunting +10`, no recipes) is tempting and **out of scope**: no recipe-knowledge channel needs it and it would be the first profession with no grant — filed as OQ3.
- **Testing:** grant applies +10 once; a second call applies nothing and returns `[]`; unknown key still warns and changes nothing; the bonus lands on `.current` (so the XP floor reads it). The existing knowledge tests keep passing unchanged — the recipe half of the contract is untouched.
- **Mutations:** drop the `db.profession` guard (second-call test fails); apply to `.base` only (XP-floor test fails).
- **Commit:** `feat(professions): skill_bonus in the profession package, applied once by grant_profession`

### Task CC2.2 — Consistency test: every `skill_bonus` key is a skill the character has
- **Goal:** A typo in the data (`"crafting"` for `"craft"`) fails a test, not a player.
- **Dependencies:** CC2.1.
- **Approach:** One test in `tests/test_material_registry.py`'s shape: a guard (≥ 4 professions loaded), then a `subTest` per profession asserting each bonus key is in `derive_skill_bases()`'s key set.
- **Testing:** the test itself; mutate a key to `"crafting"` and watch it name the profession.
- **Commit:** `test(professions): skill_bonus keys resolve to real skills`

## 7. Component CC3 — The EvMenu (Claude; in-game protocol by Adam)

### Task CC3.1 — Menu nodes: allocate → confirm → profession → confirm → done
- **Goal:** A player can build a legal character in under five minutes on a phone, see every number before committing, and change nothing afterwards.
- **Dependencies:** CC1.1, CC2.1.
- **Approach:** `world/chargen_menu.py`, nodes as plain functions (Evennia Ref gains an EvMenu section in CC4.1). *Allocate:* one line per characteristic with the Legend one-sentence description (p.5–7, paraphrased), the running total out of 80, and input as `str 12` style pairs or a single line of seven; `validate_allocation()` prints every violation at once. *Confirm:* the derived sheet — health max, the five skill bases — so the player sees that INT 6 means Craft 12 before saying yes. *Profession:* the four packages with recipes and bonus named. *Confirm, done:* `apply_allocation()`, `grant_profession()`, `db.chargen_complete = True`, re-snapshot the C.3 baseline (the `at_post_puppet` snapshot was taken on the 10s, so without this the first `progress` would report chargen as growth), then `look`. Every write happens in the final node, in one place, so a disconnect anywhere before it changes nothing.
- **Testing** (`EvenniaCommandTest` with the menu driven by `execute_cmd`): the happy path ends with the flag set and the stats applied; an illegal line stays on the allocate node and lists the violation; a disconnect-shaped exit before the last node leaves the character at 10s and the flag unset.
- **Commit:** `feat(chargen): EvMenu nodes for points build and profession`

### Task CC3.2 — Launch from `at_post_puppet`; persistent; nothing else until done
- **Goal:** A new character meets the menu on first puppet and cannot act in the world before finishing it; a disconnect resumes it.
- **Dependencies:** CC3.1.
- **Approach:** CC8. In `Character.at_post_puppet`, after `super()`: if not `db.chargen_complete`, `EvMenu(self, "world.chargen_menu", startnode="node_allocate", persistent=True, auto_quit=False, cmd_on_exit="look")`. The EvMenu cmdset shadows the character cmdset while active, which is the gate. Admin escape: `@py` is not shadowed for builders, and a `chargen/reset <char>` builder command clears the flag for testing. Multiplayer: menu state is per object (persistent mode stores it on the character), so ten first logins at once share nothing.
- **Testing:** unit — a character without the flag gets a menu on puppet, one with the flag does not; in-game protocol (Adam): create a fresh account, see the menu, disconnect mid-allocation, reconnect, confirm the menu resumes with the same running total, finish, `sheet` shows the chosen numbers, `skills` shows the derived bases plus bonus, `progress` shows no growth.
- **Commit:** `feat(chargen): launch the menu on first puppet, persistent until complete`

### Task CC3.3 — Remove `CmdChooseProfession`; `help chargen`; prose sweep
- **Goal:** One home for the profession choice, one help topic for the process, and no sentence left that says every character is identical.
- **Dependencies:** CC3.2.
- **Approach:** Delete the command class and its cmdset line (`commands/default_cmdsets.py`); `help profession` becomes a pointer to `help chargen`, which states the contract in the player's terms (80 points, 6–18, one profession, no do-overs, characteristics improve by play — Legend p.68ff). Count the prose sites before touching any (Testing Ref §11c): the `at_object_creation` comments (`# DEX + INT based`), `world/improvement.py`'s *"at INT 10"* calibration note (stays true as a measurement, re-worded as one), `tests/test_skill_xp.py`'s docstring (the bases it lists), the roadmap entry, and `docs/PolishedWorld_System_Map.md` if it describes chargen.
- **Testing:** `help profession` and `help chargen` render; `profession` is an unknown command; the full suite (Adam, locally, both with and without `TREASURY_DBREF`) — expected: all green but the two known dbref failures.
- **Commit:** `refactor(chargen): retire the profession command; help chargen; prose sweep`

## 8. Component CC4 — Docs close-out and merge (Claude, on `main`)

### Task CC4.1 — Documentation
- **Goal:** Every document that described the static character describes the built one.
- **Dependencies:** CC3.3 on the branch.
- **Approach:** Evennia Ref gains an EvMenu section (persistent mode, the cmdset shadow, the first-puppet hook) — Rev 25; Testing Ref takes the epic's candidates (the one-write-node pattern, the C.3 re-snapshot) — Rev 14; roadmap: the alpha prerequisite marked met, the chargen entry turned to a record — Rev 31; BACKLOG: *Health `descs`* and *Profession Common-Skill bonuses* closed, *Cultural-Background gating* and the two Rev 49 deferrals re-pointed — Rev 50; this decomposition to DONE. Catalogue loop against the tree as it will be (README Rev 9's lesson).
- **Commit:** `docs: close out character creation (CC4)`

### Task CC4.2 — Merge
- **Goal:** `feature/character-creation` on `main` via merge commit; branch deleted on origin; `git ls-remote` per ref.
- **Commit:** the merge commit (PR).

## 9–11. (reserved for records as tasks ship, as the alpha content decomposition did)

## 12. Open questions (each with the task that closes it)

- **OQ1 — Hunting's base pair.** Hunting is the project's skill, not Legend's; Legend's nearest are Track (Advanced) and Survival (culture bonus). Proposal: `INT+POW` (reading sign, the same pair as Perception, which `hunt` already leans on); alternative `DEX+INT` (the stalk). → CC1.1.
- **OQ2 — Bonus values** (CC6's table). → CC2.1, locked on the scratch branch before code (lesson 98).
- **OQ3 — A `hunter` profession.** The first profession with no recipe grant; decide whether a package may be bonus-only. → CC2.1 decides for the alpha; if no, a BACKLOG entry.
- **OQ4 — Builder escape.** `chargen/reset` as a builder command or an `@py` idiom in the Testing Ref. → CC3.2.
- **OQ5 — The dump-stat shape of the cohort.** Nothing closes this in the epic; it is measured at alpha close-out (§13).

## 13. Consequences worth reading twice

- **POW and CHA have no reader in the alpha (CC4).** A Points Build with a floor of 6 invites 6/6 there, which is 68 points over five characteristics. This is accepted *because the instance is wiped at close-out* (D3): the cohort's allocations are data about what players value when nothing is hidden, and Stage 5 and magic get their readers before any character carries a 6 into a world that keeps it. The alternative — fix POW and CHA at 10 and build on 60 — hides the question instead of measuring it.
- **The order (F) depends on CC1.** A future decision to start everyone identical reopens the order of the remaining prerequisites; it does not merely simplify this feature.
- **Default characters get weaker in two skills.** Perception and athletics at 10s go 25 → 20 (CC5). Only dev characters exist, and they do not migrate (CC7).
- **Rung 20 is now a choice, not a rule.** A character who takes INT 6 for STR 18 will buy `cloth` and `leather` from a crafter. That is the economy pillar doing what it is for; it is also the first time a new character cannot make something on the ladder, and the cohort contract should say so (*help chargen*, CC3.3).
- **Prose sites.** Four named in CC3.3 before code; expect three-to-four more (the epic pattern in the gotcha file).
