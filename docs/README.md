# PolishedWorld — docs

> **Rev 8 · 2026-08-12** — **the index listed a directory where it should have listed documents.** One row read `Crafting docs | tactical | docs/crafting/`, which passes any check that asks whether the path exists and fails the only question the table is for: *what is in this repo and at what altitude?* Four documents were invisible behind it — the two crafting decompositions, the 14-system build-order backlog and the content gold-standard — and the Rev 6 check could not have caught it, because `for f in docs/*.md` does not descend. The check is therefore widened to `docs/**/*.md`. The four are listed individually; `PolishedWorld_System_Backlog.md` is marked **strategic**, which is the altitude it actually occupies and not the one its location implies — see `docs/BACKLOG.md` (*Tooling & Process*) for why it is indexed where it lies rather than moved. **The widened check then found a fifth omission on its first run** — `docs/reference/arms_of_legend.md`, the OGL rulebook text the crafting decompositions are built from, unlisted in a second subdirectory nobody had looked in. That is the check earning its widening in the same commit that widened it, and the reason the rule is `docs/**/*.md` and not "remember to check `docs/crafting/` too".

> **Rev 7 · 2026-08-03** — index `PolishedWorld_Skill_Progression_Decomposition.md`. It was added to `main` in the same session that Rev 6 declared the directory-vs-list check to be how this table is verified, and the check was then not run against the new file. One row; the lesson is that the check has to be a step, not a resolution.

> **Rev 6 · 2026-08-03** — **Two documents were missing from the index, and one of them is the first thing anyone should read about the economy.** `PolishedWorld_Economic_Philosophy.md` — the eight principles every other economy document implements — was never listed, and neither was `PolishedWorld_Currency_Decomposition.md`. An index that omits the entry point is worse than no index: it looks complete, so nobody goes looking. Both added — as was **`PolishedWorld_Skill_Improvement_Decomposition.md`**, a third omission the eyeball survey missed and a mechanical check (`for f in docs/*.md; grep -q $f README`) caught immediately. That check is now the way this table gets verified; reading the list and reading the directory are different acts, and only one of them is reliable. The philosophy is marked **read first**. A **reading order for the economy** section is added below the table, because "read first" is a claim a single table row cannot make convincingly and because these five documents are close to useless out of order.

> **Rev 5 · 2026-07-26** — index testing reference, backlog and recipe-knowledge decomp.
> **Rev 4 · 2026-07-19** — indexed the System Map and Source/Sink Ledger (structural / cross-system altitude).
> **Rev 3 · 2026-07-10** — indexed the Stage 2 crafting-progression decomposition (tactical, feature-task altitude).
> **Rev 2 · 2026-07-02** — added GameGold design, GameGold economy, and core-instructions docs to the index (moved out of the project-knowledge-only list).
> **Canonical:** `docs/README.md` @ G0dlet/PolishedWorld — git wins. If this project-knowledge copy's Rev is lower than the repo's, it's stale — re-upload from the repo.

Planning and reference documentation for PolishedWorld, organised by altitude.

## Version headers (read this)

Every Markdown doc here — and every project-knowledge copy of it — carries a version
header directly under its H1 title. The point is a one-glance answer to *"am I on the
latest copy?"*, and quick detection of drift between the repo and the project-knowledge
copies (the exact drift that bit us once: the repo had a section the project-knowledge
copy lacked).

Format:

```markdown
# <Title>

> **Rev N · YYYY-MM-DD** — one-line changelog of this rev
> **Canonical:** `<path>` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.
```

Rules:

- **Rev** — monotonic integer, starts at `1`, `+1` on every content change, never reused.
- **Date** — the date of that rev. **Changelog** — one line, what changed.
- **Bumping the Rev is mandatory in any commit that changes a doc's content.** A content
  diff that doesn't move the Rev line is a review red flag.
- **No commit SHA in the header** — it would be stale the moment the bump commit lands
  (that commit changes the file → new SHA). Rev + date is the human key; `git log` is the
  ground truth.
- A doc not yet in the repo marks Canonical as *"project-knowledge only — not yet in repo."*
- **To check freshness:** compare the Rev line of your project-knowledge copy against the
  repo's. Lower here = re-upload from the repo.

The same convention is restated for content agents in `AGENTS.md` §9.

## Index

| Doc | Altitude | Canonical path |
|---|---|---|
| Strategic roadmap | strategic (epics / milestones) | `docs/roadmap.md` |
| System map | structural (how built systems connect) | `docs/PolishedWorld_System_Map.md` |
| Source/sink ledger | structural (economy pillar-1 audit) | `docs/PolishedWorld_SourceSink_Ledger.md` |
| Evennia reference | reference (API / contribs) | `docs/PolishedWorld_Evennia_Reference.md` |
| Testing reference | reference (`@py` idioms & gotchas) | `docs/PolishedWorld_Testing_Reference.md` |
| Consolidated backlog | tactical (deferrals — canonical home) | `docs/BACKLOG.md` |
| Recipe knowledge decomposition | tactical (feature tasks) | `docs/PolishedWorld_Recipe_Knowledge_Decomposition.md` |
| Hunting decomposition | tactical (feature tasks) | `docs/PolishedWorld_Hunting_Decomposition.md` |
| Crafting progression decomposition | tactical (feature tasks) | `docs/PolishedWorld_Crafting_Progression_Decomposition.md` |
| Currency decomposition | tactical (feature tasks) | `docs/PolishedWorld_Currency_Decomposition.md` |
| Skill improvement decomposition | tactical (feature tasks) | `docs/PolishedWorld_Skill_Improvement_Decomposition.md` |
| Skill progression (XP) decomposition | tactical (feature tasks) | `docs/PolishedWorld_Skill_Progression_Decomposition.md` |
| Crafting decomposition (worked examples) | tactical (crafting-tree tasks) | `docs/crafting/PolishedWorld_Crafting_Decomposition.md` |
| Crafting decomposition — Arms of Legend (complete) | tactical (crafting-tree tasks) | `docs/crafting/PolishedWorld_Crafting_Decomposition_AoL_Complete.md` |
| System backlog (14 systems, build order) | strategic (unlocks the crafting tree) | `docs/crafting/PolishedWorld_System_Backlog.md` |
| Deer batch — content gold standard | reference (generation style example) | `docs/crafting/deer_batch_gold_standard.md` |
| Arms of Legend (rulebook text, OGL) | reference (source material) | `docs/reference/arms_of_legend.md` |
| **Economic philosophy** | design (economy — **read first**) | `docs/PolishedWorld_Economic_Philosophy.md` |
| GameGold design | design (crypto spec) | `docs/GameGold_Design.md` |
| GameGold economy | design (economy) | `docs/PolishedWorld_GameGold_Economy.md` |
| Agent scope & schemas | governance | `AGENTS.md` |
| Core instructions | governance (project meta) | `docs/PolishedWorld_Core_Instructions.md` |

### Reading order for the economy

The economy documents build on one another and are close to useless out of
order. Read them this way:

1. **`PolishedWorld_Economic_Philosophy.md`** — the *why*. Eight principles;
   everything below is an implementation of one of them.
2. **`PolishedWorld_SourceSink_Ledger.md`** — the pillar-1 audit. Where does
   each thing enter the economy, and where does it leave?
3. **`PolishedWorld_GameGold_Economy.md`** — the shipped currency design and the
   crypto bridge.
4. **`GameGold_Design.md`** — the chain itself.
5. **`PolishedWorld_Currency_Decomposition.md`** — the task-level record of how
   Stage 4 was actually built, including every deviation and why.

*(Docs still living only in project knowledge — functional-decomposition methodology,
Mongoose Legend notes, code standards, creature-harvesting design — get a header and
move here as they're next touched.)*
