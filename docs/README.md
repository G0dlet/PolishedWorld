# PolishedWorld — docs

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
| Evennia reference | reference (API / contribs) | `docs/PolishedWorld_Evennia_Reference.md` |
| Hunting decomposition | tactical (feature tasks) | `docs/PolishedWorld_Hunting_Decomposition.md` |
| Crafting docs | tactical | `docs/crafting/` |
| GameGold design | design (crypto spec) | `docs/GameGold_Design.md` |
| GameGold economy | design (economy) | `docs/PolishedWorld_GameGold_Economy.md` |
| Agent scope & schemas | governance | `AGENTS.md` |
| Core instructions | governance (project meta) | `docs/PolishedWorld_Core_Instructions.md` |

*(Docs still living only in project knowledge — testing reference, functional-decomposition
methodology, Mongoose Legend notes, code standards, creature-harvesting
design — get a header and move here as they're next touched.)*
