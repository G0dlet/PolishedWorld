# PolishedWorld — Consolidated Backlog

> **Rev 8 · 2026-07-18** — Stage 3 Component F close-out (scroll — the first *written*
> knowledge channel, F.1–F.4). Added three Crafting & Tools deferrals: *`INSCRIBE_COOLDOWN`
> tuning* (conservative 60s, no playtest data), *parchment writing material* (the
> hide-derived surface deferred from F.1a, BLOCKED on the tanning chain), and *blank
> scroll as a craftable intermediate* (F.4 follow-up, same design axis as parchment).
> Extended *`CmdCraftGated` recipe-resolver duplication* to its full four call sites —
> `_can_transmit` (F.1) and `CmdLearn` (F.2) both read `_RECIPE_CLASSES`, and
> `render_recipe_detail_by_name` (F.3) deliberately keeps that read inside
> `world/knowledge.py` so the `Scroll` typeclass never becomes a fifth consumer.
> Extended the *`recipes <name>` prettify* entry: the renderer is now shared
> (`render_recipe_detail`) by `recipes <name>` and `look <scroll>`, so one fix lands both.
> **Rev 7 · 2026-07-13** — Stage 3 Component E close-out. Added *`DISASSEMBLE_COOLDOWN`
> tuning* under Crafting & Tools (the conservative 300s constant, no playtest data
> yet). Extended *`CmdCraftGated` recipe-resolver duplication*: `CmdDisassemble`
> (E.2) is a second consumer of the contrib's private `_RECIPE_CLASSES` — an exact
> `.get(name)` this time, not the fuzzy matcher — so both live under one entry.
> Noted the E.1 `obj.db.recipe` stamp now provides the recipe half of the
> maker's-mark identity.
> **Rev 6 · 2026-07-12** — Added a new *Professions & Chargen* section two
> Stage 3 Component D deferrals from the Legend profession analysis: *Profession
> Common-Skill bonuses (Legend's other half)* and *Cultural-Background gating of
> professions*. Both BLOCKED on a real chargen / Cultural Background system;
> Component D ships knowledge-only, free-choice professions.
> **Rev 5 · 2026-07-11** — Added *`recipes <name>` output name is a prettified
> prototype key* (polish) under Crafting & Tools — the C.2 detail view (Recipe
> Knowledge decomp §8) shows `output_prototypes` keys with underscores swapped
> for spaces; resolving the prototype's real key/desc and correct
> article/pluralisation ("a pair of leather boots") is deferred.
> **Rev 4 · 2026-07-11** — Added *`CmdCraftGated` recipe-resolver duplication*
> (tech-debt) under Crafting & Tools — a UX-layer duplicate of the crafting
> contrib's private recipe matcher, backstopped by pre_craft (Recipe Knowledge
> decomp §7 / Task B.2).
> **Rev 3 · 2026-07-11** — Added *Duplicate `MongooseCraftRecipe` import in
> recipes.py* (tech-debt) under Crafting & Tools, flagged during Stage 3
> Component A source-verification.
> **Rev 2 · 2026-07-11** — Origin-trim pass. Added the hunt-independent needle
> primitive (a Stage 2 §13 item missed in the Rev 1 seed). Removed *Search /
> disambiguation UX* — it is already richly homed in the always-read `roadmap.md`
> §backlog, so listing it here would only duplicate it (see scope note below).
> Corrected two origins (`look`-injection and GameGold explorer originate from
> working memory, not a written doc line). Migrated items trimmed to pointers in
> their origin decomps (crafting §13 Rev 9, hunting Rev 2, Evennia Ref §8.8 Rev 12).
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
has no stage of its own. **Items already safely homed in the always-read
`roadmap.md` are intentionally excluded** — duplicating them here would recreate
the very drift this file exists to prevent. Only items that would otherwise be
*orphaned* (buried in a closing decomp, or living only in working memory) belong
here.

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

### `DISASSEMBLE_COOLDOWN` tuning
- **What:** Real-time seconds between reverse-engineering attempts, the named
  constant `commands/crafting_commands.py::DISASSEMBLE_COOLDOWN` (currently 300).
- **Why deferred:** Balance-tuning, not a mechanic gap. The disassemble roll is
  already destructive (the item is consumed win or lose), so the cooldown only
  paces *attempts*; 300s is a conservative dev value chosen to keep the item
  channel from undercutting the paid scroll/teach channels, with no playtest data
  to tune against yet.
- - **Trigger:** Live playtest data on how fast players grind bought goods for
  recipes.
- **Origin:** Recipe Knowledge decomp §10, Task E.2.
- **Status:** OPEN

### `INSCRIBE_COOLDOWN` tuning
- **What:** Real-time seconds between `inscribe` attempts, the named constant
  `commands/crafting_commands.py::INSCRIBE_COOLDOWN` (currently 60).
- **Why deferred:** Balance-tuning, not a mechanic gap. `inscribe` already costs a
  bolt of cloth per scroll, so the material is the real economic throttle and the
  cooldown only stops scroll-spam; 60s is a conservative dev value (lighter than
  disassemble's 300, since inscribe is the *intended* paid channel), no playtest
  data yet.
- **Trigger:** Live playtest data on scroll production/trade cadence.
- **Origin:** Recipe Knowledge decomp §11, Task F.1.
- **Status:** OPEN

### Parchment writing material (hide-derived writing surface)
- **What:** A dedicated `parchment` primitive as the scroll's writing surface,
  tanned/derived from hide (tying the hunting economy into the knowledge economy),
  instead of F.1's MVP reuse of `cloth`.
- **Why deferred:** Parchment-from-hide needs a tanning chain that does not exist:
  `leather` is DECISION-status (unbuilt) and `raw_hide` is an orphan until tanning
  lands, so building parchment now drags in half an unbuilt economy chain. F.1
  reuses `cloth` (EXISTS, a plausible woven writing surface) so the scroll channel
  ships without blocking on tanning.
- **Trigger:** The tanning chain landing (leather / DECISION #2 resolved), decided
  *together with* the blank-scroll entry below — both answer the same question
  ("what is the physical writing surface, and is it a crafted good?").
- **Origin:** Recipe Knowledge decomp §11, Task F.1 (choice (a), locked to cloth).
- **Status:** BLOCKED (tanning chain)

### Blank scroll as a craftable intermediate
- **What:** Make the writing surface its own craftable good:
  `cloth → blank scroll (craft) → inscribe → scroll of <recipe>`. `inscribe` would
  then simply `stamp()` a held blank scroll (F.4 already provides `stamp()`) — no
  prototype spawn, no material search inside the command.
- **Why deferred:** An economy-depth refinement, not a correctness gap: the scroll
  loop works today (inscribe spawns + consumes cloth directly). Adding a tradeable
  intermediate before players want to *trade* blank scrolls builds depth ahead of
  demand. Low-risk to defer — inserting a craft step later needs no migration of
  existing "scroll of <recipe>" items.
- **Trigger:** Player demand to trade blank writing surfaces, or the parchment
  decision above — same design axis, decide the two together.
- **Origin:** Working memory — Component F.4 follow-up (deferred by decision).
- **Status:** OPEN

### Material / maker's-mark aliases beyond "superior"
- **What:** Individuating aliases from material and maker ("a steel dagger of
  <smith>") on top of the quality alias.
- **Why deferred:** Pairs with recipe knowledge (who knows/made what). The data
  primitives are now in place: `crafted_by` (the maker) plus the `obj.db.recipe`
  stamp from E.1 (the recipe) — this entry is the display/alias layer on top.
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

### Hunt-independent needle primitive
- **What:** A gatherable needle primitive (e.g. a `thorn`/`stick` needle) so the
  needle bootstrap doesn't require a hunt (bone needle → bone → a kill).
- **Why deferred:** The bone needle covers the bootstrap today; a forage-only
  path is a convenience/robustness refinement, not a gap.
- **Trigger:** None hard; do if the hunt-gated needle proves a friction point for
  new players.
- **Origin:** Crafting Progression decomp §13.
- **Status:** OPEN

### Duplicate `MongooseCraftRecipe` import in `recipes.py`
- **What:** `world/recipes.py` imports `MongooseCraftRecipe` twice on adjacent
  lines at the top of the file. Remove the redundant second import.
- **Why deferred:** Pure hygiene; harmless (a re-import is a no-op) and outside
  the scope of the Stage 3 Component A commits it was spotted during.
- **Trigger:** None hard; fold into the next `recipes.py` touch, or a standalone
  `chore(recipes): remove duplicate import`.
- **Origin:** Stage 3 Component A source-verification (2026-07-11).
- **Status:** OPEN

### `CmdCraftGated` recipe-resolver duplication
- - **What:** `commands/crafting_commands.py::_resolve_recipe` re-implements the
  contrib's fuzzy match (exact → `startswith` → `in`, unique) and reads the
  private `_RECIPE_CLASSES` / `_load_recipes` from the crafting contrib. There are
  now four call sites reading that private registry: `_resolve_recipe` (B.2, fuzzy)
  and `CmdDisassemble` (E.2, exact `.get` on the E.1 stamp) in
  `crafting_commands.py`, plus `_can_transmit` (F.1) and `CmdLearn` (F.2, exact
  `.get` on a scroll stamp) in `world/knowledge.py` / `crafting_commands.py`. F.3's
  `render_recipe_detail_by_name` deliberately keeps its resolve *inside*
  `world/knowledge.py` (already a consumer via `_can_transmit`) so the `Scroll`
  typeclass renders `look` detail without touching the registry — the count stays at
  these four modules, not five.
- **Why deferred:** The contrib exposes no public recipe-resolver API; `pre_craft`
  (B.1) is the authoritative backstop if this duplicate drifts, so the ~5 lines
  are an accepted UX-only convenience, not a correctness dependency. E.2's
  exact-get degrades gracefully (a removed recipe → None → unlearnable, no
  destroy), so it too tolerates the private matcher changing under us.
- **Trigger:** The crafting contrib stabilising a public resolver API (or its
  private matcher changing under us).
- **Origin:** Recipe Knowledge decomp §7 (Task B.2); §10 (Task E.2).
- **Status:** OPEN

### `recipes <name>` output name is a prettified prototype key
- - **What:** `world/knowledge.py::render_recipe_detail` renders each
  `output_prototypes` entry by swapping `_`→space (e.g. `leather_boots` →
  "leather boots"). It does not resolve the prototype's real `key`/`desc`, nor
  apply a correct article/pluralisation ("a pair of leather boots"). As of F.3 this
  renderer is shared by `recipes <name>` (C.2) and `look <scroll>` (the `Scroll`
  typeclass), so one fix corrects both surfaces.
- **Why deferred:** Resolving prototypes is a separate verification surface
  (`evennia.prototypes`) and article/plural rules are per-item; the prettified
  key is legible and correct enough for discovery. Cosmetic only.
- **Trigger:** Any pass that adds prototype display-name resolution, or the first
  recipe whose prototype key reads badly when prettified.
- **Origin:** Recipe Knowledge decomp §8, Task C.2.
- **Status:** OPEN

---

## Professions & Chargen

### Profession Common-Skill bonuses (Legend's other half)
- **What:** A Legend profession grants two things -- access to Advanced Skills
  (modelled today as recipe knowledge, Component D) *and* Common-Skill bonuses
  (e.g. Blacksmith: Brawn +15%, Hammer +10%). Only the knowledge half is built;
  the skill-bonus half is deferred.
- **Why deferred:** Stat territory, which Component D deliberately excludes
  ("knowledge only, no stat bonuses"). Also meaningless while every character
  has placeholder characteristics -- the bonuses need a real chargen (rolled or
  allocated characteristics) to sit on.
- **Trigger:** A real chargen with per-character characteristics.
- **Origin:** Stage 3 Component D -- Legend profession analysis (Legend.pdf
  Professions section, verified 2026-07-12).
- **Status:** BLOCKED (real chargen / characteristic variation)

### Cultural-Background gating of professions
- **What:** In Legend RAW the only gate on which profession a character may take
  is Cultural Background (e.g. Alchemist = Civilised only), NOT a characteristic
  minimum. Component D ships free choice (any character, any profession); a
  culture-based availability gate is the Legend-authentic future refinement.
- **Why deferred:** No Cultural Background / chargen system exists yet to gate
  against, and free choice is both Legend-faithful and the only meaningful option
  while characteristics are identical placeholders. Explicitly NOT a
  characteristic-minimum gate -- that would diverge from Legend RAW.
- **Trigger:** A Cultural Background / chargen system.
- **Origin:** Stage 3 Component D.2 -- Legend profession analysis (verified
  2026-07-12).
- **Status:** BLOCKED (Cultural Background / chargen system)

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
- **Origin:** Working memory (Component D.3 era) — never had a written doc entry;
  this is now its first written home.
- **Status:** OPEN

### Suppress "is wearing nothing" on a bare garment
- **What:** Stop `look`ing at a garment from emitting "X is wearing nothing."
- **Why deferred:** Pre-existing `ContribClothing.get_display_desc` quirk (a
  garment "wears" nothing); cosmetic, low priority.
- **Trigger:** None hard.
- **Origin:** Evennia Reference §8.8.
- **Status:** OPEN

> **Not listed here:** *Search / disambiguation UX + item identity* — already a
> written, cross-cutting entry in `roadmap.md` §backlog (rides on Stage 2/3 alias
> work). It has a safe home in an always-read doc, so per the scope note it is not
> duplicated here.

---

## GameGold

### GameGold block explorer
- **What:** A Django-based, staking-focused block explorer for the GameGold
  chain.
- **Why deferred:** Part of the much-later GameGold epic; no chain deployment to
  explore yet.
- **Trigger:** GameGold epic (post-mainnet).
- **Origin:** Working memory / GameGold design context — not written in any doc
  (roadmap Stage 8 names GameGold but not the explorer); this is its only home.
- **Status:** BLOCKED (GameGold not yet deployed)
