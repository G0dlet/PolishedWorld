# PolishedWorld — Consolidated Backlog

> **Rev 1 · 2026-07-11** — Initial consolidated backlog. Seeded from the Stage 2
> crafting decomposition §13, the hunting/H7 decomposition backlog, the Evennia
> Reference §8.8 note, and the Component G "not in scope" deferrals.
>
> Canonical: docs/BACKLOG.md

## Purpose & scope

Tactical deferrals **smaller than a stage** — refinements, tech-debt, and
cross-cutting or orphaned tasks that would otherwise die inside a feature
decomposition's §Backlog once that decomposition closes and stops being read.

**This is not the roadmap.** Strategic epics and future stages live in
`roadmap.md` (its backlog + decision log). This file is for the small stuff that
has no stage of its own.

**One item, one home.** When an item lands here it is trimmed from its origin
doc to a one-line pointer (`→ see BACKLOG.md`). A feature-internal deferral that
already has a *scheduled* home ("fixed in Component X") stays in its decomp; only
the homeless items migrate here.

**Workflow hook:** whenever a task is deferred, log it here in the same pass —
so this document doesn't become the next thing that's forgotten.

## Status legend

- **OPEN** — actionable whenever picked up; no blocker.
- **BLOCKED** — waiting on a named prerequisite (stated in *Trigger*).
- **SCHEDULED** — has a concrete future home (stage/component named).
- **DONE** — completed; kept briefly for traceability, then pruned.

Each entry: **What · Why deferred · Trigger · Origin · Status**

---

## Crafting & Tools

### Metal tools + craft-station / forge
- **What:** Metal-tier tools (metal knife/needle already exist as spawn-only
  prototypes) made craftable via a forge/craft-station.
- **Why deferred:** Out of Stage 2 scope; needs a station concept + metallurgy
  materials that don't exist yet.
- **Trigger:** A future crafting/metallurgy epic.
- **Origin:** Crafting Progression decomp §13.
- **Status:** OPEN

### Superior-tool longevity / condition bonus
- **What:** Let a *superior* crafted tool (quality > 100) start with better
  condition or wear slower, on top of the +10 craft bonus it already grants.
- **Why deferred:** Would collide with the prototype-driven start-condition
  (40/30, D.5) that `_apply_tool_quality` deliberately does **not** touch.
- **Trigger:** Metal tools + forge (when start-condition becomes tier-driven
  rather than a flat prototype value).
- **Origin:** Component G design (Rev 8), deferred by decision.
- **Status:** BLOCKED (metal tools + forge)

### `tool_wear_on_fumble` tuning
- **What:** Extra wear on a fumbled craft, tunable via a `tool_wear_on_fumble`
  knob.
- **Why deferred:** Balance-tuning, not a mechanic gap; no data to tune against
  yet.
- **Trigger:** Live playtest data on wear pacing.
- **Origin:** Crafting Progression decomp §13.
- **Status:** OPEN

### Material / maker's-mark aliases beyond "superior"
- **What:** Individuating aliases from material and maker ("a steel dagger of
  <smith>") on top of the quality alias.
- **Why deferred:** Pairs with recipe knowledge (who knows/made what).
- **Trigger:** Stage 3 (Recipe Knowledge & Discovery).
- **Origin:** Crafting Progression decomp §13; also feeds the disambiguation fix.
- **Status:** SCHEDULED (Stage 3)

### Waterskin `durability` → `condition` migration
- **What:** Migrate the waterskin's refill-count `durability` onto the shared
  `condition` axis used by everything else.
- **Why deferred:** D3 standardised on `condition` but left the waterskin as a
  known divergent; migrating it is a self-contained refactor.
- **Trigger:** None hard; do when touching waterskin next.
- **Origin:** Crafting Progression decomp §3 (name-fork note) + §13.
- **Status:** OPEN

---

## Death & Corpses

### Per-item corpse decay
- **What:** Independent decay timers per loot item, so loot lingers after the
  corpse rots (leather before steel) instead of the current atomic delete.
- **Why deferred:** Current `PlayerCorpse` deletes all loot at expiry; the
  centralised deletion in H7.3 makes per-item decay a clean later addition.
- **Trigger:** None hard; a refinement on the closed H7 loop.
- **Origin:** Hunting / H7 decomposition backlog.
- **Status:** OPEN

### `DeathWeakness` debuff → `fatigue_rate`
- **What:** Point the death-weakness debuff at `fatigue_rate` (its intended
  target) instead of the current `hunger_rate`/`thirst_rate` stand-in (+25%).
- **Why deferred:** Fatigue-exhaustion has no real consequence yet, so a
  fatigue-rate debuff would be toothless.
- **Trigger:** Fatigue-exhaustion consequence (below).
- **Origin:** Hunting / H7 decomposition backlog.
- **Status:** BLOCKED (fatigue-exhaustion consequence)

---

## Survival

### Fatigue-exhaustion consequence
- **What:** A real consequence for hitting fatigue exhaustion (unconsciousness,
  skill penalties, etc.), so fatigue matters like hunger/thirst do.
- **Why deferred:** Not yet needed for the core loop; unblocks `DeathWeakness`.
- **Trigger:** None hard; also the prerequisite for the death-weakness re-point.
- **Origin:** Survival mechanics (core loop).
- **Status:** OPEN

---

## Containers

### Full container support
- **What:** Generic `CmdPut` + a reusable `ContribContainer` typeclass (bags,
  chests). Possibly a `CmdContainerLook` (likely skipped — contents shown via
  `return_appearance`).
- **Why deferred:** H7.3b added only `CmdContainerGet` for corpse looting, and
  deliberately excluded `ContainerCmdSet` to avoid a `look` collision with
  `ExtendedRoomCmdSet`. Full support needs bags/chests to exist first.
- **Trigger:** Bags/chests as craftable items.
- **Origin:** Hunting / H7.3b decomposition backlog.
- **Status:** BLOCKED (no container items yet)

---

## UX & Item Identity

### `look`-injected condition for non-admin players
- **What:** Surface the condition line in `look` output for regular players
  (who lack `examine`).
- **Why deferred:** D.3 shows condition on `look` for tools/garments via
  `return_appearance`, but a general `look`-injection for arbitrary items was
  scoped out.
- **Trigger:** None hard.
- **Origin:** Crafting Progression decomp (D.3) backlog.
- **Status:** OPEN

### Suppress "is wearing nothing" on a bare garment
- **What:** Stop `look`ing at a garment from emitting "X is wearing nothing."
- **Why deferred:** Pre-existing `ContribClothing.get_display_desc` quirk (a
  garment "wears" nothing); cosmetic, low priority.
- **Trigger:** None hard.
- **Origin:** Evennia Reference §8.8.
- **Status:** OPEN

### Search / disambiguation UX + item identity
- **What:** Two-layer fix for identical-key multimatch — (1) individuate crafted
  items with adjectives/aliases so `steel dagger` resolves singly (rides on
  quality/recipe work), (2) stack truly-identical consumables into one
  quantity-bearing object. Residual: reskin/interactive multimatch prompt.
- **Why deferred:** Not its own epic — a cross-cutting concern to fold in as
  crafting/consumables mature.
- **Trigger:** Crafting/consumables maturity (Stage 3 alias work helps).
- **Origin:** roadmap.md backlog + Evennia Reference §12.
- **Status:** OPEN

---

## GameGold

### GameGold block explorer
- **What:** A Django-based, staking-focused block explorer for the GameGold
  chain.
- **Why deferred:** Part of the much-later GameGold epic; no chain deployment to
  explore yet.
- **Trigger:** GameGold epic (post-mainnet).
- **Origin:** GameGold design doc + roadmap.md (Stage 8).
- **Status:** BLOCKED (GameGold not yet deployed)
