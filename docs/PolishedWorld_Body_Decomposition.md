# PolishedWorld — Body Decomposition (Stage 5, slice 3: BD)

> **Rev 2 · 2026-11-22** — **BD is DONE.** `feature/body` is merged to `main` as `22fb018` (PR #33, merge commit, tree `e030305`, the tree `git merge-tree` predicted) and tagged `alpha-20261122`, annotated (OQ-BD4, Adam). Docs only, BD-T9, with Combat Decomposition Rev 16, Combat Design Rev 5, BACKLOG Rev 117, the Alpha Runbook Rev 12, the Survival Loop decomposition Rev 16, roadmap Rev 86, README Rev 67 and Lessons Rev 12 (396–414). *Shipped* lines for BD-T1–BD-T9, and **one task the slice added, BD-T5b** (§7): every skill's ladder keyed by the top of its band, with a migration. OQ-BD2, OQ-BD3, OQ-BD4 and OQ-BD6 closed (§9). **Departures recorded where they landed:** OQ-BD6 went as two tables for one task, not one table with a guard (BD-T3); `ensure_style` lives in `world/skill_base.py`, not beside the data (BD-T6); the Combat block on `sheet` stands between *Vital Status* and *Skills*, not between the characteristics and the skills (BD-T7); the suite ran at home, not at work (BD-T8). No lock changes.
> **Rev 1 · 2026-11-16** — first version, docs only, with `docs/PolishedWorld_Combat_Decomposition.md` Rev 15, roadmap Rev 85 and README Rev 66. Decomposes Stage 5's third slice, BD, from Combat Design §4.10 (CS1, CS2, CS4) and the book's derived values (core pp. 10–14): four Common skills, six Combat Styles over twelve weapon types, and Combat Actions, Strike Rank, Damage Modifier and Hit Points per location read on demand. Nine locks (BD1–BD9, Adam, one at a time, each as recommended), seven code tasks, a merge and a close-out (BD-T1–BD-T9). Read against live source the same day: `main` at `618351f` (tree `201c3f7`), *Legend* core from the project's `Legend.pdf` with page numbers taken from the text's page markers, *Arms of Legend* from `docs/reference/arms_of_legend.md`. **Run in the sandbox and recorded in §4:** a prototype of the four tables against the book's own examples and every column of the Hit Points table, and the four skills added to a scratch clone to count the existing tests that notice. **One lock moves a decision between slices:** CS4 leaves BD for WN and ML (BD8). No code is written by this document.
> **Canonical:** `docs/PolishedWorld_Body_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Design source:** `docs/PolishedWorld_Combat_Design.md` §3.1, §3.2, §3.6, §4.10 (CS1–CS4), §6, §7; `docs/PolishedWorld_Combat_Decomposition.md` §2 (ST1, ST2; BD's row); `docs/PolishedWorld_Survival_Loop_Decomposition.md` SL8 (*Movement, Strike Rank and Combat Action effects are Stage 5's*); *Legend* core pp. 10–14, 53, 90, 101, 105–107, 109, 124, 133–134, 138; *Arms of Legend* l. 356, 1499, 1736–1768.
**Status:** **DONE (Rev 2).** BD1–BD9 are locked (Adam, 2026-11-16, each as recommended). BD-T1–BD-T7 and BD-T5b shipped on `feature/body`; merged to `main` as `22fb018` (PR #33, BD-T8), tagged `alpha-20261122`; closed in the docs by BD-T9.
**Feature branch:** `feature/body` — one branch, one merge (ST2). Create it with `git switch -c feature/body --no-track origin/main`.
**Rough scope:** seven code tasks, a merge and a close-out; about six to seven hours of code — two sessions at 5 h/week. Three new modules (`world/body.py`, `world/skill_base.py`, `world/combat_styles.py`), four production files changed (`world/chargen.py`, `world/chargen_menu.py`, `world/healing.py`, `typeclasses/characters.py`), one migration, one command's output (`sheet`), and no new command.
**Philosophy:** skynda långsamt — the book's tables are transcribed and pinned by its own examples; nothing derived is stored; a skill nobody has trained is a number that can be worked out.
**Labels:** BD (locks), BD-T (tasks), BDM (mutations; a letter after the number marks one added at the task, so the planned numbers stay), OQ-BD (open questions). All were free across the repository when checked with `git grep -n -w -E 'BD[0-9]+|BD-T[0-9]+|OQ-BD[0-9]+'`, before they were used. CS1–CS4 stay the Combat Design's labels for the decisions the locks carry out.

---

## 1. What the slice is

A character has five skills today (`perception`, `stealth`, `athletics`, `craft`, `hunting`) and one number for its body, `health` at CON × 2. Combat's first blow needs a body that can be asked five things it cannot answer:

1. **How often does it act, and how soon?** Combat Actions and Strike Rank (pp. 10, 12–13), both lowered by fatigue (p. 90).
2. **How hard does it hit?** The Damage Modifier (pp. 10–11).
3. **How much can each part of it take?** Hit Points per location (p. 11) — the maximum only; what is left of them is WN's.
4. **What does it resist, dodge, wrestle and punch with?** Resilience, Evade, Brawn and Unarmed (p. 14).
5. **What does it fight with?** A Combat Style, which is a skill over a kind of weapon (pp. 13–14, 124).

None of it is combat. The slice has no new command; a player sees four more skills, and three derived values in character creation and on `sheet`. WN (wounds) waits for it and for SC; GR (weapons and armour) waits for it (ST1).

**`health` does not change.** It stays the one written measure of hurt until WN builds the damage path, and WO3 then makes it a display (BD7).

**Nothing rolls.** BD adds no call to `skill_check`, `opposed_check` or `opposed_against`, so `ROLL_SITES` stays at eight and W3.1's question is not asked here. It adds no call to `attempt_skill_improvement`, so the call-site census stays at six (BD8).

---

## 2. Decisions locked 2026-11-16 (BD1–BD9)

Adam took the nine as recommended, one at a time.

**BD1 — A style names weapon types from a project list; the hand is a field of its own on the weapon.** A style names one type, or two for a second hand.
- **The types are the project's construction, not the book's.** Core defines *Category* as *the type of weapon* (p. 101) and, for ranged weapons, as *a basis for Combat Styles* (p. 105), and prints no such column in either table (pp. 106–107, 109). *Arms of Legend* has the column, and there it means the hand: `1H`, `2H` or `1H & 2H` (l. 1499, tables from l. 1736). All the book says of type is the substitution rule (p. 124): a short sword may stand in for a long sword and a mace may not, *as the mace is used as a bludgeon, not a cutting edge*.
- *Why:* it is CS2 as written, and p. 124's own example — *Sword and Shield (any one-handed sword and any shield type)*. A new weapon fits without any style changing.
- *Rejected:* a style that lists weapons by name (every recipe would edit styles, and p. 124's substitution penalties would have to be built); one style per type with no combinations (weapon-and-shield stops being something one trains for, and with it the extra Combat Action of p. 124).

**BD2 — Twelve weapon types.**

| Type | Core's weapons (pp. 106–107, 109) | In the game today |
| --- | --- | --- |
| `sword` | short sword, war sword, longsword, great sword, falchion, rapier, sabre, scimitar | — |
| `knife` | knife, dagger, dirk, poniard, main gauche | *stone knife* |
| `axe` | hatchet, battleaxe, great axe | *stone axe* |
| `bludgeon` | club, mace, morning star, military pick, great club, great hammer, quarter staff | *club* |
| `flail` | ball & chain, chain, military flail | — |
| `spear` | short spear, longspear, trident, lance | *short spear* |
| `polearm` | halberd, poleaxe | — |
| `shield` | buckler, target, heater, hoplite, kite | — |
| `bow` | short bow, long bow, recurve bow | *short bow* |
| `crossbow` | light crossbow, heavy crossbow, arbalest | — |
| `sling` | sling, staff sling | *sling* |
| `thrown` | javelin, dart, discus, bolas; and a thrown dagger, hatchet or trident | — |

- The list covers 52 of core's 56 table rows (39 close, 17 ranged). **Left out until built:** net (in both tables), garrotte and blowgun; a handled net *counts as its own Combat Style* (AoL l. 356). **Unarmed is a Common skill** (p. 14) and no weapon type.
- **The quarter staff is a `bludgeon`.** The book's criterion is how the weapon is used (p. 124), and the staff has only *Stun Location*.
- **`polearm` is apart from `spear`.** Halberd and poleaxe carry *Sunder* and cut; the spears only *Impale*.
- **A weapon may have a second type, `thrown`.** Dagger, hatchet and trident are in both tables, and footnote 2 on p. 107 says they are thrown without penalty. A javelin is `thrown` only.
- **BD ships the vocabulary, not the tagging.** Setting the type and the hand on each item is GR's (IS1; OQ-BD1), which also types *Arms of Legend*'s own rows when a recipe wants one. The field is to be called `weapon_type`: *category* already means the hand in *Arms of Legend*.

**BD3 — A style becomes a trait at first use; until then its base is read from the characteristics.** *Every* style starts at its base (p. 14), so a style nobody has trained is a number that can be worked out: STR + DEX in close combat, DEX × 2 at range.
- *Why:* it is the rule banked XP already follows — *derive, never backfill* (CC5/CC7). `skill_check` takes a number, not a trait (`world/skillcheck.py:60`). `skills`, `progress` and `sheet` list `char.skills.all()`, so a style without a trait is not shown and disturbs nothing. Characteristics are set once and do not improve in play (`world/chargen.py:363`), so the base read later is the one creation would have written.
- **An assumption, stated:** if characteristics ever improve (the book allows it, p. 68), an untrained style follows the new value and a trained one stays. That is the book's behaviour for a base, and it differs from storing every style at creation.
- *Rejected:* every style on every character from creation — a backfill per new style, and a row per style in `progress`, most of them *(not yet trainable)*.

**BD4 — Six styles to start, and a rule that fills the list.**

| Style | Main type | Hand | Second hand | Base |
| --- | --- | --- | --- | --- |
| *Knife* | `knife` | 1H | — | STR + DEX |
| *Mace and Shield* | `bludgeon` | 1H | `shield` | STR + DEX |
| *Axe and Shield* | `axe` | 1H | `shield` | STR + DEX |
| *Spear and Shield* | `spear` | 1H | `shield` | STR + DEX |
| *Bow* | `bow` | 2H | — | DEX × 2 |
| *Sling* | `sling` | 1H | — | DEX × 2 |

- **Only types with an item today.** Club, hatchet, knife and shortspear are all `1H` in *Arms of Legend*'s table (l. 1736–1768), so nothing that can be held today needs a two-handed style.
- **The rule:** *the slice that adds the first weapon of a type adds its style in the same commit.* Under BD3 that is one row of data.
- **A style is named for the combination before the shield exists.** Whoever fights with a club trains *Mace and Shield*; the book's rule for a missing weapon (p. 124) leaves the skill unchanged and takes only the shield's protection and its Combat Action. When GR builds a shield, the club fighter has already trained for it.
- **Players do not invent styles. *A departure from the book*** (p. 124: *Adventurers can create their own combinations*): the list is the server's. BD-T9 enters it in Combat Design §5.
- ***Bow* and *Sling* have no use until PJ.** `hunt` keeps `hunting` (CS3, HQ2) and `shoot` is slice 12. They are listed because the items exist, by the rule above.
- *Not listed, with reasons:* *Thrown* (no thrown weapon exists; a short spear is no javelin) and any two-handed style.
- *Rejected:* the book's sword examples now (nine styles, three with nothing to hold); the whole system now (fifteen, nine with nothing to hold).

**BD5 — Four Common skills: Resilience, Evade, Unarmed, Brawn.** Persistence comes with magic (Adam).

| Skill | Base (p. 14) | Reader in Stage 5 |
| --- | --- | --- |
| Resilience | CON × 2 | `world/healing.py:63` today; the wound test in WN (p. 145); a creature at 0 Hit Points in CE (p. 146) |
| Evade | DEX × 2 | the automatic defence when no weapon will serve (CT5, p. 136), in ML |
| Unarmed | STR + DEX | an attack with no weapon, 1D3 (p. 138), and breaking a grip (p. 133), in ML |
| Brawn | STR + SIZ | pulling an impaled weapon free (p. 133); in place of the style when a weapon is pinned (p. 134) and in a grapple (p. 138) |

- *Why Brawn now:* it hangs on *Impale*, which is on spears, knives and arrows (pp. 106–107, 109) — the weapons the game has. A backfill is run by hand per database, which is what CS1's *once* is worth.
- **Against it, kept:** if CM2's list lands without *Impale* and *Pin Weapon*, Brawn arrived a stage early; the cost is one row reading *(not yet trainable)*, as Athletics, Perception and Stealth already read.
- **Persistence has no reader in the combat chapter** (pp. 123–150). **The book does read it elsewhere:** an Exhausted or Debilitated body rolls Persistence or falls unconscious (p. 90). The survival loop put Athletics there (SL9, SL11, NP-L1), so that reader is taken.

**BD6 — The four are traits from creation, existing characters are backfilled from their own characteristics, and every reader goes through one function with a safety net.** The function returns the trait's value if the character has the trait, and the base if not — the function BD3 needs anyway.
- `world/healing.py:63` reads Resilience through it. For a new character the number is today's. When Resilience improves (WN gives it a call site), the character heals faster, because the healing table is read by Resilience: the book's intent, and what the stand-in's comment waits for.
- *Why the net:* without it `healing.accrue` returns 0 for a character the backfill missed, with no message. With it the backfill decides what is shown, not whether healing works.
- *Rejected:* the readers reading the trait directly, as `world/fatigue.py:204` reads Athletics; the four created at first use like styles (a new character would not see Evade or Resilience until its first fight, and character creation could not show what CON and DEX feed).

**BD7 — Combat Actions, Strike Rank, the Damage Modifier and the maximum Hit Points per location are computed on every read. Nothing is stored.**

| Value | BD delivers | Left to |
| --- | --- | --- |
| Combat Actions | the table (p. 10), with fatigue's lowered DEX (p. 90) | +1 for a shield or two weapons (p. 124): ML |
| Strike Rank | the average of INT and DEX rounded up, less fatigue's penalty (p. 90), less an armour penalty taken as an argument | the sum of Armour Points worn: GR. Until then it is 0. |
| Damage Modifier | the table (pp. 10–11) as data: sign, dice, sides | rolling it: ML |
| Hit Points per location | the **maximum** for each of seven locations (p. 11) | the **current** value, the wound level and the wound state: WN (WO2) |

- *Why:* three of the four depend on things that move in play — fatigue, armour worn, what is in the second hand — and under storage each of those is a place that must remember to write. It is the pattern of `enc_limit` and `encumbrance_state` (*Nothing is stored*) and of P-2.
- **BD stores no Hit Points per location.** Two healths side by side, with nothing writing to the new one, would say two things about one body. `world/healing.py:67–69` foresees the change: Hit Points and Resilience share a number *by coincidence*.
- **Above the Damage Modifier table the function refuses.** The table ends at STR + SIZ 100 (p. 10); a player character reaches 36. Creatures may go over (CE); the function raises and does not guess a row.

**BD8 — BD adds nothing to `improvable_skills`. CS4 moves to WN and ML.** The set is a label for `progress`, not a gate (`typeclasses/characters.py:1331–1345`): which skills improve is decided by which call sites exist. BD has none for a combat skill — Resilience is first rolled in WN, the others and the styles in ML.
- *Why:* with the four in the set now, `progress` would draw four bars that cannot move for several slices, which the comment at `:1335` calls *reads as broken*. (The test would pass: it asks only that the set's skills exist on a character.)
- **Styles need their own rule, in ML.** A style is a trait only once used (BD3), so it cannot stand in a fixed set: `test_every_declared_skill_actually_exists_on_a_character` would fail for every style a character has not touched. `progress` should count every key of the style table as trainable — a style that shows is one that has been used.
- **What goes with CS4 to WN and ML:** each new call site changes `TestImprovementCallSiteCensus` (six today) and decides `meaningful`; the 30-second gate per skill stands, as CS4 says.

**BD9 — The three derived values are shown in character creation and on `sheet`. Locations and the webclient panel are not touched.**
- *Why, and why it is not the Persistence argument:* characteristics are set once and cannot be redone (CC7). Whoever spends 80 points today chooses without knowing that the average of DEX and INT sets the number of Combat Actions, with the step at 13 (p. 10). The screen shows the consequence of a choice that cannot be taken back, and says the values belong to combat, which is not built.
- **The allocate screen's *Feeds* line** (`world/chargen_menu.py:119`) gains the four skills by itself, and SIZ its first reader there (Brawn). The derived values are added to it by hand: DEX and INT feed Combat Actions and Strike Rank, STR and SIZ the Damage Modifier.
- *Not shown:* the seven maxima, beside a `health` gauge that is the only one that moves (WN shows them); `char_snapshot` (`world/client_state.py:119`) is CL's, so the push census does not change.

---

## 3. Verified source anchors (read 2026-11-16, `main` at `618351f`)

**Combat Design's seam lines have moved.** Its §6 was read at `baed99b`.

| Seam | Combat Design says | At `618351f` |
| --- | --- | --- |
| `Character.improvable_skills` | `typeclasses/characters.py:1007` | `:1345` |
| `Character.physical_modifier()` | `:679` | `:1017` |
| `Character.apply_health_damage` | `:1299` | `:1637` |
| `Character.at_character_death` | `:1353` | `:1691` |
| `world/healing.py::resilience` | `:63` | `:63` |

**What the tasks touch:**

| File | Line | What is there |
| --- | --- | --- |
| `world/chargen.py` | `:59` | `SKILL_BASE_PAIRS`, five pairs; the one table of bases |
| | `:152` | `derive_skill_bases(stats)` — sums each pair |
| | `:194` | `apply_allocation` — refuses when a derived skill's trait is missing; writes `.base` and `.current` |
| | `:357`, `:368` | `help_text()` prints `Skill (A+B)` from each pair |
| | `:363` | *characteristics do NOT improve in play here* |
| `world/chargen_menu.py` | `:119` | `_feeds(stat)` — the skills whose pair holds the characteristic, plus `health` for CON |
| | `:405`, `:418`, `:424` | `node_confirm_allocation` — *the five skill bases*; `Health max:`; `Skill bases:` |
| | `:474`, `:488` | `node_confirm_profession` derives the bases again |
| `typeclasses/characters.py` | `:304` | `at_object_creation`; characteristics at a placeholder 10 (`:330–376`) |
| | `:457–570` | the five `skills.add` calls; `craft` reads its placeholder from the characteristics, the others are flat |
| | `:1072` | the login snapshot reads every key of `skills.all()` |
| `world/healing.py` | `:30–37` | `ROWS`, the healing table by Resilience (core p. 86) |
| | `:63`, `:117` | `resilience(char)`: `int(con.value * 2)`, `None` without CON; `accrue` returns 0 on `None` |
| `world/fatigue.py` | `:68–75` | `LEVELS`: `debilitated`, `exhausted`, `wearied`, `tired`, `winded`, `fresh` |
| | `:86`, `:108` | `level_for(value)`, `penalty_for(value)` |
| | `:204`, `:264` | Athletics read as `skills.get("athletics")`, `.value` |
| `commands/character_commands.py` | `:158`, `:260`, `:368` | `skills`, `progress` and `sheet` list `char.skills.all()` |
| | `:268` | `progress` reads `improvable_skills` |
| | `:376` | `sheet` prints `skill.desc()` — a trait needs `descs` |
| `world/character_migrations.py` | `:41`, `:58` | `HUNTING_SKILL_DEFAULTS` (a flat 25) and `backfill_hunting()`; run by hand with `@py` |
| `world/skill_xp.py` | `:217` | the XP handler lists `skills.all()` and any stored key |
| `tests/test_improvement_engine.py` | `:764`, `:853` | `TestImprovableSkillsSet` (three subset tests), `TestImprovementCallSiteCensus` (six sites) |
| `tests/test_encumbrance.py` | `:982–993`, `:1016` | `ROLL_SITES`, `ROLL_NAMES`, `NON_ROLL_NAMES`, `TestRollCensus` |

**The book** (page numbers from the page markers in the text of `Legend.pdf`):

| Rule | Page |
| --- | --- |
| Combat Actions: the average of DEX and INT, rounded up; 6 or less 1, 7–12 2, 13–18 3, +1 per further 6 | 10 |
| Damage Modifier from STR + SIZ, fifteen rows, 1–5 to 91–100; it may be negative | 10–11 |
| Hit Points per location from CON + SIZ, eight columns to 36–40 and *+5 → +1*; an arm has 1 in both of the first two columns | 11 |
| Strike Rank: the average of INT and DEX rounded up, less the Armour Points carried divided by 5, rounded up | 12–13 |
| Bases: close styles STR + DEX, ranged DEX × 2, Brawn STR + SIZ, Evade DEX × 2, Resilience CON × 2, Unarmed STR + DEX | 14 |
| Resilience (CON × 2), the skill's description | 53 |
| Fatigue: Strike Rank −2 Wearied, −4 Exhausted, −6 Debilitated; DEX counted 5 and 10 lower for Combat Actions at Exhausted and Debilitated; a Persistence test or unconsciousness at both | 90 |
| *Category: the type of weapon*; for ranged weapons *a basis for Combat Styles* | 101, 105 |
| The close combat table, with no category column; footnote 2, *no penalty when thrown* | 106–107 |
| The ranged table, with no category column | 109 |
| Styles: examples, missing weapons, substituting weapons, players' own combinations | 124 |
| Brawn: an impaled weapon; a pinned weapon; a grapple | 133, 134, 138 |

**Not in Combat Design §3.1, and found here:** fatigue's Strike Rank penalty (p. 90). The design's table gives only the lowered DEX. SL8 handed both effects to Stage 5, so BD-T1 carries both, and BD-T9 adds the row.

---

## 4. What was run (sandbox: Python 3.13.18, Evennia 6.1.0; fresh clones of `618351f`)

**The tables, in plain Python** (a prototype of BD-T1 and BD-T2, no Evennia):

| Asked | Printed | The book |
| --- | --- | --- |
| Combat Actions, DEX 13 INT 16 | 3 | Alaric, p. 10 |
| Combat Actions at an average of 6, 7, 12, 13, 18, 19, 24, 25 | 1, 2, 2, 3, 3, 4, 4, 5 | the table's steps, p. 10 |
| The same Alaric, Exhausted; Debilitated | 2; 2 | p. 90 (an average of 12, then 10) |
| Strike Rank, DEX 13 INT 16; with 4 Armour Points | 15; 14 | Alaric, p. 13 |
| The same, Wearied; with 91 Armour Points | 13; −4 | p. 90; AR5's worst case |
| Damage Modifier, STR 12 SIZ 14 | +1D2 | Alaric, p. 11 |
| Damage Modifier at 5, 6, 20, 21, 25, 26, 36, 50, 51, 100 | −1D8, −1D6, −1D2, +0, +0, +1D2, +1D6, +1D10, +1D12, +2D12 | the table's edges, p. 10 |
| Damage Modifier at 101 | `ValueError` | BD7 |
| Hit Points, CON 7 SIZ 14 | legs 5, abdomen 6, chest 7, arms 4, head 5 | Alaric, p. 11 |
| Every column of the Hit Points table, at both ends of each band, 1–40 | all 80 cells equal a table typed from the book | p. 11 |
| Hit Points at 41–45 | head 9, chest 11, abdomen 10, arms 8, legs 9 | *+5 → +1* |

**Strike Rank can be negative.** The book sets no floor, and BD does not add one; what a negative opening beat means is ML's (CT3; OQ-BD5).

**Who notices four more skills.** In a scratch clone the four were added to `SKILL_BASE_PAIRS` and to `at_object_creation` and nothing else was changed. Eleven test modules were run (333 tests):

- `tests.test_chargen`, `test_chargen_help`, `test_chargen_launch`, `test_chargen_menu`, `test_professions`: 126 run, **4 fail** —
  - `test_chargen.TestDeriveSkillBases.test_each_skill_reads_its_own_pair` and `TestApplyAllocation.test_returns_the_derived_bases`: a literal dict of five bases;
  - `test_chargen_menu.TestAllocateNode.test_start_screen_shows_total_and_descriptions`: the literal *Feeds hunting, health.* for CON;
  - `test_chargen_menu.TestHappyPath.test_progress_baseline_is_retaken`: a literal dict of five skills.
- `tests.test_progress_command`, `test_skill_xp`, `test_improvement_engine`, `test_healing`, `test_client_state`, `test_names_migration`: 207 run, all pass.

So BD-T4 rewrites four tests on purpose and no more are known. **Not run, and predicted:** once `healing.resilience` reads the trait (BD-T3) *and* the trait exists on fixtures (BD-T4), `tests/test_healing.py:66` — which moves CON and expects the interval to follow — will fail, because a trait does not follow its characteristic. It is rewritten in BD-T4 to set the skill. `test_chargen_help` passes with the four added because nothing pins the pair's text; the help then reads *Resilience (CON+CON)* and *Evade (DEX+DEX)*, which BD-T4 corrects.

---

## 5. Dependency graph

```
BD-T1 ──> BD-T2 ───────────────────┐
BD-T3 ──> BD-T4 ──> BD-T5          ├──> BD-T7 ──> BD-T8 ──> BD-T9
              └───> BD-T6 ─────────┘
```

*(Rev 2: BD-T5b, added at BD-T4, came after BD-T5 and before BD-T6 — §7.)*

BD-T1–T2 and BD-T3–T6 do not touch each other's files and may be taken in either order. BD-T3 comes before BD-T4 so that the safety net is tested against a character with no Resilience trait, which after BD-T4 only a test can make.

---

## 6. Component B1 — The derived values

### Task BD-T1 — Combat Actions and Strike Rank
- **Goal:** Two pure functions give a body's Combat Actions and Strike Rank by the book's tables, fatigue included.
- **Dependencies:** none.
- **Approach:** new `world/body.py`. `combat_actions(dex, int_, fatigue_word="fresh")`: DEX less 5 at `exhausted` and 10 at `debilitated`, the average with INT rounded up, then 1 at 6 or less and `2 + (average − 7) // 6` above. `strike_rank(dex, int_, armour_points=0, fatigue_word="fresh")`: the average rounded up, less `ceil(armour_points / 5)`, less 2, 4 or 6 at `wearied`, `exhausted`, `debilitated`. The fatigue words are `world.fatigue.LEVELS`' own; an unknown word raises `ValueError`. Integers in, an integer out; no Evennia import, so the tests are `EvenniaTestCase` or plain `unittest`. The docstrings give the pages and say what is left out and to whom: the +1 for a second hand (ML), the sum of Armour Points (GR).
- **Testing:** `tests/test_body.py`. Alaric's 3 and 15; the eight steps of §4; both fatigue rows for each function; Alaric's jerkin (4 points → 14); 5 and 6 Armour Points on either side of the rounding; a table test that every word in `fatigue.LEVELS` is accepted, so a renamed level fails here.
- **Red before green:** the import fails first; then, with `combat_actions` written as a plain `average // 6 + 1`, the steps at 6, 12 and 18 fail.
- **Mutations (BDM1–BDM3):** round the average down (Alaric's Strike Rank reads 14 and must fail); drop fatigue's DEX (the Exhausted row must fail); divide the armour by 5 with a floor (the 4-point jerkin must fail).
- **In-game check:** `py from world import body; self.msg(str((body.combat_actions(13, 16), body.strike_rank(13, 16, 4), body.combat_actions(13, 16, "exhausted"))))` prints `(3, 14, 2)`.
- **Commit:** `feat(body): Combat Actions and Strike Rank from the book's tables (BD7)`
- **Shipped (Rev 2):** `b6b4a71` on `feature/body`, tree `791d423` (the sandbox commit and a `git am` on a fresh clone gave the same tree, as for every task below). Thirteen tests in `TestCombatActions`, `TestStrikeRank` and `TestFatigueWords`; the last also asserts that every key of the two penalty tables is a word of `fatigue.LEVELS`, since a renamed `wearied` would pass the first test and lose its penalty without a sound. Red: the import first; then, with `average // 6 + 1`, the steps at 6, 12, 18 and 24 and Alaric at Exhausted. BDM1 (16 failures), BDM2 (4), BDM3 (4) and BDM2a, added at the task — the two DEX losses swapped (2) — each red, the file restored from a copy and compared with `cmp`. `test_body` and `test_fatigue`, 87 tests, green.

### Task BD-T2 — The Damage Modifier, the maxima, and a body's reader
- **Goal:** The Damage Modifier and the maximum Hit Points per location come from the book's tables, and one function reads all four values for a character.
- **Dependencies:** BD-T1.
- **Approach:** `world/body.py`. `LOCATIONS`, seven keys: `head`, `chest`, `abdomen`, `right_arm`, `left_arm`, `right_leg`, `left_leg`. `damage_modifier(str_, siz)` returns `(sign, dice, sides)` from a fifteen-row table typed from p. 10, `(0, 0, 0)` at 21–25, and raises `ValueError` below 1 and above 100. `damage_modifier_text` gives `+1D2`, `-1D4`, `+0` for display. `hit_points_max(con, siz)` returns a dict by location: the first column's value plus one per band of five, with the arm's flat first step (1, 1, 2, 3 …). `derived(char)` reads the characteristics as `int(stat.value)` and the fatigue word from the gauge, and returns the four in one dict; `None` for a body without the characteristics. **Why `.value` here and `.base` for a skill's base (BD-T3):** these are read live (BD7) and should follow a modifier on a characteristic if one ever exists; a base is what creation would have written. Nothing writes a characteristic's `mod` today, so the two agree.
- **Testing:** `tests/test_body.py`. Alaric's +1D2 and his five locations; the ten edges of §4; the refusal at 0 and at 101; all 80 cells of the Hit Points table against a literal typed from the book, not computed; 41–45; `derived(self.char1)` on the placeholder 10s (2 Combat Actions, Strike Rank 10, −1D2, locations 4/5/6/3/4), and the same character with its fatigue gauge at 10.
- **Red before green:** with the arm written like the other rows, the cells of the second column fail (an arm would read 2 at 6–10).
- **Mutations (BDM4–BDM6):** shift the Damage Modifier's bands by one (the edges at 20/21 and 25/26 must fail); remove the upper refusal (101 must fail); give the arm the leg's row.
- **In-game check:** `py from world import body; self.msg(str((body.damage_modifier_text(12, 14), body.hit_points_max(7, 14)["head"], body.derived(self)["combat_actions"])))` prints `('+1D2', 5, <n>)`, where `<n>` is the character's own.
- **Commit:** `feat(body): the Damage Modifier and Hit Points per location, read on demand (BD7)`
- **Shipped (Rev 2):** `1bb0a10`, tree `47e4be8`. Fifteen tests, 28 in `test_body`: `TestDamageModifier` at both ends of all fifteen rows — thirty edges, not the ten §4 named, so a mistyped row (*+2D6*) cannot pass — `TestHitPointsMax` on all 80 cells typed from the book, Alaric, 41–45 and the refusals, and `TestDerived` on the placeholder body (2, 10, −1D2, 4/5/6/3/4) with fatigue, DEX and DEX's `mod` moved between two reads. **One addition beyond the task:** `hit_points_max` refuses CON + SIZ below 1, where the table has no column. Red against BD-T1's module: 47 failures; with the arm written as the leg, 32, all in the arm's cells (BDM6). BDM4 run both ways (down: 20 and 25 fail; up: 21 and 26), BDM5 (101), and BDM6a (`derived` reads `.base`; 1) and BDM6b (`derived` fixes the word at *fresh*; 2), added at the task. `test_body`, `test_fatigue`, `test_healing` and `test_encumbrance`, 222 tests, green.

---

## 7. Component B2 — The four skills

### Task BD-T3 — A skill's value with a safety net, and healing reads Resilience
- **Goal:** One function answers what a character's skill is, with or without the trait, and natural healing asks it for Resilience.
- **Dependencies:** none.
- **Approach:** new `world/skill_base.py`. `base_for(char, key)` reads `chargen.SKILL_BASE_PAIRS` and sums the two characteristics' `.base` as integers; `None` when the key has no pair or the character lacks a characteristic. `value_of(char, key)` returns the trait's `.value` when `char.skills.get(key)` is not `None`, and `base_for` otherwise. `world/healing.py`: `resilience(char)` becomes `value_of(char, "resilience")`; its docstring loses *stand-in* and names BD6; the module docstring's lines 4–6 follow. **The pair for Resilience goes into `SKILL_BASE_PAIRS` in this task** — `("con", "con")` — so that the net has something to read; the trait comes in BD-T4. `apply_allocation` refuses a character with a pair and no trait (`world/chargen.py:242`), so the pair is added together with a guard there, or the table is split in two; choose at the task and say which (OQ-BD6). OQ-BD2 (`.value` or `.current`) closes here.
- **Testing:** `tests/test_skill_base.py` and `tests/test_healing.py`. A character with no Resilience trait and CON 10 reads 20 and heals at the 30-row's interval, as today; with a Resilience trait at 45 it reads 45 and the interval is the 50-row's; a character with no CON reads `None` and `accrue` grants nothing. The existing healing tests pass unchanged — the receipt that the swap moved no number.
- **Red before green:** the test with the trait at 45 fails on `main` (today's function reads CON and says 20).
- **Mutations (BDM7–BDM8):** `value_of` ignores the trait (the 45 test must fail); `value_of` returns `None` without the trait (the no-trait healing test must fail — this is BD6's rejected alternative, kept out by a test).
- **In-game check:** `py from world import healing, skill_base; self.msg(str((healing.resilience(self), skill_base.base_for(self, "resilience"), self.stats.get("con").base)))` prints three numbers, the first two twice the third.
- **Commit:** `feat(skills): a skill's value with or without its trait; healing reads Resilience (BD3, BD6, CS1)`
- **Shipped (Rev 2):** `b787fd0`, tree `2ba4c15`. Fourteen tests in `test_skill_base` and `test_healing`. **OQ-BD6 went the other way from this task's text (Adam, B):** two tables for one task — Resilience's pair sat in `skill_base.PENDING_PAIRS`, chargen untouched, and moved into `chargen.SKILL_BASE_PAIRS` with its trait in BD-T4; `TestPendingPairs` failed if a key stood in both. A guard in `apply_allocation` would have weakened a refusal that exists so nothing is written when something is missing, and four chargen tests would have changed twice. **OQ-BD2:** `.value`, as every roll site reads a skill. Red against `main`'s healing: the trait-at-45 test. BDM7 (3 failures), BDM8 (26 errors and 1 failure: `TypeError` in `interval_for` — healing stops, the alternative BD6 rejected) and BDM8a, added (the base reads `.value`; 1). The existing healing tests green unchanged; neighbours 172 and 138 tests green.

### Task BD-T4 — Resilience, Evade, Unarmed and Brawn
- **Goal:** A new character has the four skills at the book's bases, and character creation says so.
- **Dependencies:** BD-T3.
- **Approach:** `world/chargen.py`: `SKILL_BASE_PAIRS` gains `brawn` (STR, SIZ), `evade` (DEX, DEX), `unarmed` (STR, DEX), beside BD-T3's `resilience`; the module docstring's *Derived skill bases* names them and p. 14; `help_text()` prints *CON x2* for a pair of one characteristic. `typeclasses/characters.py`: four `skills.add` calls **built from one table** that the backfill also reads (BD-T5), with the placeholder taken from the placeholder characteristics, as `craft` does (`:520`), so that a fixture's Resilience is CON × 2 and healing's numbers do not move. Each needs `descs`, six words by the Tone Guide; proposed at the task for Adam to take or change. The comments at `:1335–1336` (*three of five skills*) and `world/chargen_menu.py:406` (*the five skill bases*) are corrected. `improvable_skills` is not touched (BD8).
- **Testing:** the four tests §4 names are rewritten against Alaric's bases (Brawn 26, Evade 26, Resilience 14, Unarmed 25; p. 14) and the new *Feeds* lines; `tests/test_healing.py:66` sets the skill and not CON. New: a fresh character has nine skills; `progress` captions the four *(not yet trainable)*; the help text contains *CON x2* and not *CON+CON*; `TestImprovableSkillsSet` is green unchanged.
- **Red before green:** the four rewritten tests fail before the pairs are added; take that receipt per test.
- **Mutations (BDM9–BDM11):** Brawn's pair becomes STR + DEX (Alaric's 26 must fail against 25); the help prints the pair as before; one of the four is added to `improvable_skills` (the caption test must fail).
- **In-game check:** on a fresh account's character after the menu, `skills` lists nine; `py self.msg(str({k: self.skills.get(k).base for k in ("brawn", "evade", "resilience", "unarmed")}))` matches the allocation by hand.
- **Commit:** `feat(chargen): Resilience, Evade, Unarmed and Brawn at the book's bases (BD5, BD6, CS1)`
- **Shipped (Rev 2):** `6000d2a`, tree `00187b1`. Fourteen tests added and two removed (`TestPendingPairs`) over six modules. The four ladders' words were Adam's to take at the task; **they are keyed by each band's top (19/39/59/79/94/100)**, because the traits contrib reads a key as an inclusive upper bound — a first patch keyed by bottoms was replaced before push. Nine existing tests rewritten, not four: the two literal dicts, the *Feeds* line, the `progress` baseline, the CON-edges test (which now sets the skill), and the four tests of the net, which remove the trait first. `PENDING_PAIRS`, `_pair_for` and `TestPendingPairs` are gone. Red: 16 failures and 45 errors in the six task modules (168 tests), most errors from the shared `EXPECTED_BASES` gaining four keys the code did not yet know. BDM9, BDM9b (Resilience as CON + POW), BDM10, BDM11 (killed only by the new caption test — `TestImprovableSkillsSet` lets it through, as §4 said), BDM11b (a flat 25), BDM11c (no ladder), BDM11d (the bottoms' keys) and BDM11e (an edge moved from 94 to 95), all killed. **The commit message is wrong in one sentence:** its *Found on the way* says the five older ladders read one rung early, but BACKLOG had recorded the reading since Rev 35 (2026-10-09, *`descs` tables are read as upper bounds but shaped like lower bounds*). A pushed message is not corrected; this line is the correction.

### Task BD-T5 — The backfill
- **Goal:** A character made before this slice gets the four skills from its own characteristics, and running the migration twice changes nothing.
- **Dependencies:** BD-T4.
- **Approach:** `world/character_migrations.py`: `backfill_combat_skills()`, in the shape of `backfill_hunting` (`:58`) — `Character.objects.all_family()`, one character's error does not stop the batch, a summary string for `self.msg`. For each of the four that is missing, `skills.add` from BD-T4's table with `base` and `current` set to `skill_base.base_for(char, key)`. A skill that is present is left as it is, whatever its value. A character without the characteristics is skipped and named. **Not `backfill_hunting`'s flat 25:** that was right before character creation existed.
- **Testing:** `tests/test_combat_skill_migration.py`. A character stripped of the four gets them at its own sums; a second run reports four skipped and writes nothing; a Resilience already at 60 stays 60; a character with no CON is skipped by name and the next one is still served; banked XP under another key is untouched.
- **Red before green:** with the flat default copied from `HUNTING_SKILL_DEFAULTS`, the own-sums test fails.
- **Mutations (BDM12–BDM13):** the *present* check is removed (the 60 must fail); the `try` is narrowed to exclude the missing-CON case (the batch test must fail).
- **In-game check:** `py from world.character_migrations import backfill_combat_skills; self.msg(backfill_combat_skills())`, twice; the second answer grants nothing. Read `skills` on G0dlet before and after.
- **Commit:** `feat(migrations): backfill the four combat skills from each character's own characteristics (BD6)`
- **Shipped (Rev 2):** `01a8bbc`, tree `ff4ea5c`. Eleven tests in `tests/test_combat_skill_migration.py`. **`skill_base.trait_kwargs(char, key)`** is the one place the four traits' shape is written; `Character.at_object_creation` and the backfill both add through it, so a backfilled character cannot differ from a new one. Every base is computed before the first write, so no character gets three of four. Red: with a flat 25 in `trait_kwargs`, nine of the eleven fail. BDM12, BDM13, and BDM13b (three of four to a character without CON) and BDM13c (a ceiling on the trait), added: four of four killed. Run in the game at home: `changed 5`, then `changed 0; unchanged 5`.

### Task BD-T5b — Every skill's ladder keyed by the top of its band *(added at BD-T4, Rev 2)*
- **Goal:** All nine skills read their six words by the same bands, 0–19, 20–39, 40–59, 60–79, 80–94 and 95 upward, on every character.
- **Why a task of its own:** BD-T4 keyed the four new ladders by each band's top, because the contrib reads a key as an inclusive upper bound. The five older skills were keyed by band bottoms (0/20/40/60/80/95), so they read one rung early: Athletics 25 read *capable*, and 81 read the last word. A trait keeps the ladder it was created with, so the correction is a migration. **Adam decided the reading for the skills on 2026-11-22** — the decision BACKLOG *`descs` tables are read as upper bounds but shaped like lower bounds* asked for before the next change to a table: the tables are re-keyed, the readers (`desc()`, `tier_for`, `_bucket_index`) stay as they are. Hunger and thirst are not touched; they decide when the ticker warns and get a task of their own.
- **Shipped (Rev 2):** `8d70669`, tree `637bdbc`. `world/skill_base.py`: `SKILL_LADDERS` (the words of all nine), `LADDER_TOPS` and `ladder(key)`, which gives each trait its own copy. `typeclasses/characters.py`'s five literal tables and `world/character_migrations.py::HUNTING_SKILL_DEFAULTS` read the same ladder, so it stands in one place, not three. `backfill_skill_ladders()` writes only the table onto every skill whose stored one differs: base, current, mod and `skill_xp` untouched, no skill invented. Nineteen tests in `tests/test_skill_ladders.py` and `tests/test_improvement_engine.py` (all nine skills at both ends of every band; the tier line at 39 → 40 and not at 40 → 41). Red: the five older skills at 20, 40, 60, 80 and 95. Seven mutations (L1–L7), all killed. What a player sees: the word beside a skill between two bands, and the *reaches a new tier* line, now at 20, 40, 60, 80 and 95. Run in the game at home: `changed 5`, then `changed 0; unchanged 5`; Athletics 25 reads *weak*.

---

## 8. Component B3 — Styles; B4 — what is shown, and close-out

### Task BD-T6 — Weapon types and styles
- **Goal:** The twelve types and the six styles exist as data, a style's value can be read for any character, and its trait can be made.
- **Dependencies:** BD-T3.
- **Approach:** new `world/combat_styles.py`. `WEAPON_TYPES`, the twelve of BD2. `STYLES`, the six of BD4, each with its name, main type, hand, second-hand type or `None`, and whether it is ranged. `skill_base.base_for` learns a style's pair from it (STR + DEX, or DEX + DEX when ranged), so `value_of(char, style_key)` works with no trait. `ensure_style(char, style_key)` adds the trait at the base if it is missing and returns it; an unknown key raises. The trait keys are chosen at the task so that none can meet a Common skill's (OQ-BD3). **No production code calls any of it** until ML, as `compare_levels` shipped in SC; the module docstring says who will. The docstring carries BD4's rule for adding a style, and that the types are the project's (BD1).
- **Testing:** `tests/test_combat_styles.py`. Every style's types are in `WEAPON_TYPES`; names and keys are unique; no style key is a key of `SKILL_BASE_PAIRS`; a close style's value on the placeholder character is 20 and a ranged one's 20 by its own pair (then with DEX moved, so the two differ); `ensure_style` twice makes one trait and keeps a trained value; a character with a style trait lists it in `skills.all()` and the XP handler derives its entry; `TestImprovableSkillsSet` and both censuses are green unchanged.
- **Red before green:** `value_of(char, "bow")` returns `None` before `base_for` knows styles.
- **Mutations (BDM14–BDM16):** a ranged style reads STR + DEX; `ensure_style` overwrites an existing trait; a style names a type outside the list.
- **In-game check:** `py from world import combat_styles, skill_base; self.msg(str((len(combat_styles.WEAPON_TYPES), sorted(combat_styles.STYLES), skill_base.value_of(self, "<the key for Spear and Shield>"))))` prints 12, six keys and STR + DEX; `skills` afterwards shows no style.
- **Commit:** `feat(styles): twelve weapon types and six Combat Styles as data (BD1–BD4, CS2)`
- **Shipped (Rev 2):** `f0d01bf`, tree `b1019a6`. Thirty-six tests in `tests/test_combat_styles.py`; one test in `test_skill_ladders` now counts nine rows plus six. **OQ-BD3:** every style's key starts with `STYLE_PREFIX = "style_"` — `style_knife`, `style_mace_shield`, `style_axe_shield`, `style_spear_shield`, `style_bow`, `style_sling` — and no Common skill's key does, which a test holds. The styles' pairs stay out of `chargen.SKILL_BASE_PAIRS`, where `apply_allocation` would refuse every character that has not used a style. **Departure:** `ensure_style` lives in `world/skill_base.py`, not in `world/combat_styles.py`. `base_for` must read the styles' pairs, and with `ensure_style` beside the data the two modules would import each other; `combat_styles.py` is pure data with no project imports (caught at the task's lock, not in code). **One ladder for every style,** `combat_styles.STYLE_LADDER` (*untried, green, drilled, steady, seasoned, deadly*); each style has a row in `SKILL_LADDERS`, so `ladder()` and `backfill_skill_ladders` cover a style's trait. `ensure_style` on a key with no base returns `None` and writes nothing, as `trait_kwargs` does. Red: 21 failures and 26 errors, all `None != 20` or `NoneType` — the function was written with the gap in it, so no test was red on an `ImportError`. BDM14–BDM16 and four more, all killed. Neighbours: 73 and 199 tests green, `TestImprovableSkillsSet` and both censuses unchanged.

### Task BD-T7 — What the player is shown
- **Goal:** Character creation and `sheet` show Combat Actions, Strike Rank and the Damage Modifier.
- **Dependencies:** BD-T2, BD-T4.
- **Approach:** `world/chargen_menu.py`: `node_confirm_allocation` adds one line under *Health max* from `body`'s pure functions on the draft, and a short sentence that these are read in combat, which is not built yet (Tone Guide §5 for the wording; proposed at the task). `_feeds` adds *Combat Actions* and *Strike Rank* for DEX and INT and *Damage Modifier* for STR and SIZ. `commands/character_commands.py`: `sheet` gains the same three from `body.derived(char)`, between the characteristics and the skills; a character without characteristics gets no block. `stats`, `status` and `char_snapshot` are not touched (BD9).
- **Testing:** `tests/test_chargen_menu.py` and a `sheet` test with `EvenniaCommandTest`. Alaric's allocation shows 3, 15 and +1D2 on the confirmation; the allocate screen's DEX row names Combat Actions; `sheet` on a character at fatigue 10 shows the lowered Combat Actions, which proves it is read live; `TestPushCensus` is green unchanged.
- **Red before green:** the confirmation test fails on the missing line.
- **Mutations (BDM17–BDM18):** `sheet` reads the values with the fatigue word fixed at `fresh` (the fatigue test must fail); the confirmation shows Strike Rank from DEX alone.
- **In-game check:** part of BD-T8's protocol.
- **Commit:** `feat(chargen): character creation and sheet show Combat Actions, Strike Rank and Damage Modifier (BD9)`
- **Shipped (Rev 2):** `d1d0a9b`, tree `e030305`. Seventeen tests: the new `tests/test_sheet_combat.py` and five in `tests/test_chargen_menu.py`. The sentence on the confirmation is *These three are read in combat, which is not in the game yet.* (Adam, A1). **The block on `sheet` stands between *Vital Status* and *Skills*** (Adam, B1), not between the characteristics and the skills as the task said: the Fatigue row above it explains a lowered Strike Rank. **One addition beyond the task:** `body.format_damage_modifier(tuple)` is the one spelling of the modifier, and `damage_modifier_text` goes through it; the first version had `sheet` format it a second time. Red: 15 failures and 1 error, all on missing lines. 170 tests in the task's files with chargen, body and `health_desc`, and 162 in `test_client_state` and `test_fatigue`, green; `TestPushCensus` unchanged. BDM17, BDM18 and five more, all killed.

### Task BD-T8 — Protocol, suite and merge
- **Goal:** `feature/body` is on `main` by a merge commit, with the whole suite and the in-game protocol green on what was merged.
- **Dependencies:** BD-T1–BD-T7.
- **Approach:** as SC-T7: the whole suite on the work machine with `ForkTestRunner` and `--parallel auto`, read with `grep -E "^(Ran|OK|FAILED)"` (lesson 247), with the settings line stashed; in the sandbox in batches under 300 s. Predict the count from the last run (2050) plus this branch's new tests, not from a static count (lesson 386). `git merge-tree` to predict the tree. Then the protocol on the dev server at the branch tip after `evennia reload`, the PR, the merge commit, the branch deleted. Whether the merge is tagged, and whether it must be out before the alpha opens, is OQ-BD4.
- **In-game protocol** (to be run line by line in the sandbox at the task before it is given, as §4.4 of the SC decomposition was):
  1. **Read first.** `inventory`; `skills`; `py self.msg(str((sorted(self.skills.all()), {k: self.stats.get(k).base for k in ("str","dex","con","siz","int")}, self.traits.get("fatigue").value)))`. Write the three down.
  2. **The tables, no character.** The in-game lines of BD-T1 and BD-T2. *Proves the server's module holds the book's tables.*
  3. **Healing before the backfill.** BD-T3's line. *Proves the net: Resilience is read with no trait.*
  4. **The backfill.** BD-T5's line, twice. Then `skills`: nine rows, the four new at the sums step 1 gives. *Proves own characteristics, and that a second run is idle.*
  5. **`progress`.** The four read *(not yet trainable)*. *Proves BD8.*
  6. **A style with no trait.** BD-T6's line; `skills` still nine rows. *Proves BD3.*
  7. **`sheet`.** The three derived values, equal to step 2's functions on step 1's characteristics by hand.
  8. **A new character.** With a fresh `Account.create` account, not a played character reset, go through the menu: the allocate screen's *Feeds* lines, the confirmation's three values and nine bases.
  9. **Restore.** Nothing was written but the four traits, which stay. Delete the test account and its character, reading dbrefs before `delete()`.
  - **What the protocol must not assume:** an empty inventory, a Fresh character (G0dlet was *wearied* at the last protocol; step 1 reads it, and step 7's Strike Rank is 2 lower then), or that the dev database was never backfilled.
- **Commit:** the merge commit of the PR.
- **Shipped (Rev 2):** PR #33 merged with a merge commit, `22fb018`, tree `e030305`, parents `3a45e72` and `d1d0a9b`; the branch deleted on origin and at home. `git merge-tree` predicted `e030305`: `main` had not moved since the branch was cut. **The suite ran at home, not at work** (no `"#10"` line there to stash): on the branch tip with `ForkTestRunner` and `--parallel auto`, `Ran 2187 tests`, `OK`, 242.6 s — 2050 + 137 as predicted (BD-T1–BD-T5b +84, BD-T6 +36, BD-T7 +17). **The protocol, at the branch tip after `evennia reload`, with three departures:** step 3 tried the net on a character created and deleted on the same line (`bdt8net`), because the home database was already backfilled; step 8's `py` line could not run as the new account's character, since a Player account has no `py` — `skills` showed the same four numbers (26, 26, 14, 25), and the line should have been written for the staff account with `search_object`; **step 9 was skipped on Adam's decision:** `bdt8` (`#234`) stays in the home database, so a backfill there now counts six characters. **OQ-BD4 closed (Adam, A1):** the merge is tagged `alpha-20261122`, and it must be deployed before the first player creates a character (BD9's reason). The alpha database is created fresh (runbook `:419`); if it is not, both backfills run once, in order (runbook Rev 12).

### Task BD-T9 — Documentation
- **Goal:** The docs say what a character's body now is, and nothing in them says what it used to be.
- **Dependencies:** BD-T8.
- **Approach:** one docs commit on `main`.
  - This document: *Shipped* lines and DONE. `docs/PolishedWorld_Combat_Decomposition.md`: BD DONE in §2 and the Status line; the next slice.
  - `docs/PolishedWorld_Combat_Design.md`: §3.1 gains fatigue's Strike Rank penalty (p. 90); §3.6 loses the weapon tables' categories, with what was found; §4.10 says where CS1, CS2 and CS4 landed; §5 gains BD4's departure (players do not invent styles); §6's seam lines are dated or moved (§3 above); §7 loses the styles' starting list.
  - `docs/PolishedWorld_Alpha_Runbook.md`: the backfill line beside the Names one (`:419`) — the alpha database is created fresh, so it is needed only on a database made before the merge.
  - `docs/PolishedWorld_Core_Instructions.md` if it lists a character's skills; `docs/PolishedWorld_System_Map.md` if it names `world/healing.py`'s reader of CON; the Survival Loop decomposition's SL8 gets a dated note that the Strike Rank and Combat Action effects are built.
  - **`PolishedWorld_Mongoose_Legend.md` (outside git)** is Adam's: say what in it the slice makes stale.
  - **Every line anchor into the changed files is read live:** `git grep -n -E "chargen\.py:|healing\.py:|characters\.py:1[0-9]{3}" docs` gives the list. A Rev line is left as written; a table of anchors is updated or dated (lessons 143, 322).
  - A prose loop afterwards for *five skills*, *stand-in*, *CON x 2* and *CON × 2* across `docs/`, `world/`, `commands/` and `typeclasses/`.
  - roadmap, README, BACKLOG where an entry is touched, and the lessons from the slice.
- **Commit:** `docs: close out the body (Stage 5 slice BD)`
- **Shipped (Rev 2):** this commit, on `main` after `22fb018`. See the Rev 2 line at the top for every document it touches.

---

## 9. Open questions (each with what closes it)

- **OQ-BD1 — Where a weapon's type and hand are stored on the item.** BD ships the vocabulary only. **Closes at:** GR's decomposition (IS1).
- **OQ-BD2 — Does healing read Resilience's `.value` or `.current`?** `.value` is `current + mod`; `world/fatigue.py:207` reads `.value` for Athletics, and nothing writes a skill's `mod` in play except protocols. **Closes at:** BD-T3; `.value` unless the reading there finds a reason. **Closed (Rev 2):** `.value` (BD-T3).
- **OQ-BD3 — The styles' trait keys,** so that none can meet a Common skill's key or a future one's (a style named *Knife* against a skill). **Closes at:** BD-T6. **Closed (Rev 2):** the prefix `style_` (`combat_styles.STYLE_PREFIX`), which no Common skill's key carries, pressed by a test (BD-T6).
- **OQ-BD4 — Is the merge tagged, and must it be out before the alpha opens?** BD9's reason — a permanent choice made blind — applies to every character created between the alpha's start and this merge. L6.1 deploys `alpha-20261116` today, without SC and without this. **Closes at:** BD-T8, Adam's call. **Closed (Rev 2, Adam, A1):** tagged `alpha-20261122`, and deployed before the first player creates a character (BD-T8).
- **OQ-BD5 — A negative Strike Rank.** 91 Armour Points give −4 (§4). BD returns it as computed. **Closes at:** ML's decomposition, with the opening beat (CT3).
- **OQ-BD6 — One table of bases, or two.** `apply_allocation` refuses a character with a pair and no trait, and BD-T3 adds Resilience's pair a task before its trait. **Closes at:** BD-T3. **Closed (Rev 2, Adam, B):** two tables for one task — `skill_base.PENDING_PAIRS` in BD-T3, moved into `chargen.SKILL_BASE_PAIRS` with the trait in BD-T4 (BD-T3, BD-T4).
- **OQ-SC1, inherited — Does a wound's Resilience test take the physical modifier?** Unchanged by this slice, which rolls nothing. **Closes at:** WN's decomposition.

---

## 10. Consequences worth reading twice

1. **A style nobody has used does not exist on the character.** `skills` shows no style until ML rolls one. That is BD3 working, not a missing feature, and BD-T8's step 6 shows it on purpose.
2. **Healing speeds up when Resilience improves — but not in this slice.** BD gives Resilience no call site (BD8), so the number healing reads cannot move until WN.
3. **The club fighter trains *Mace and Shield*.** The name is the book's and the shield is not built. A player will ask; the help for combat, when ML writes it, should answer.
4. **Four rows that read *(not yet trainable)* for several slices.** Honest, and it makes seven of nine. The caption is the set's whole purpose (BD8).
5. **A backfilled Resilience is a snapshot.** The safety net follows CON; the trait, once written, does not. Nothing changes CON today (`world/chargen.py:363`); the day something does, a rule is owed.
6. **Strike Rank and Combat Actions fall with fatigue from the first blow.** A wearied attacker opens two points later, an exhausted one may lose a Combat Action (Alaric: 3 → 2). `physical_modifier()` already takes 30–50 % off the same body's rolls; ML should read the two together before calibrating `ROUND_SECONDS`.
7. **Character creation now names things the game does not do yet.** That is BD9's choice, for a choice that cannot be undone; the sentence on the screen is what keeps it from being a promise.
8. **BD5's reason for Brawn leaned on a hand-run backfill.** The alpha database is created fresh (runbook `:419`), so that cost falls on the two development databases, and on the alpha only if it opens before this merges. The other reason, *Impale* on today's weapons, stands by itself.
