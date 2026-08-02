# PolishedWorld — Consolidated Backlog

> **Rev 16 · 2026-08-02** — Stage 4 Component D close-out. Three new entries, none of them defects. **Faucet task-table tuning** (Currency) is the entry the decomposition asked for by name: `TEMPLE_TASKS` is the anchor, and its numbers cannot be judged until crafted goods have prices players actually charge, because the faucet's whole job is to read as obviously a supplement against a market that does not exist yet. **Timed player actions have a pattern but no shared home** (Tooling & Process) records a duplication rather than a bug: `rest` and `work` implement interruptible timed actions independently, and `at_pre_move` in `characters.py` now carries two hand-written branches that will grow one per future action — the *third* is the signal to extract a helper, not the second. **`_format_wait()` truncates** (Currency) is cosmetic: a fresh one-hour cooldown renders as `59 minutes`, which reads as though the clock started early; noted with the reason the naive ceiling fix is wrong in the other direction.

> **Rev 15 · 2026-08-02** — Stage 4 Component C close-out. Four new entries, all small and all found by running the shipped command rather than by reading it. **Ledger `actor` field** (Currency) is the only one with teeth: the entry shape records who *received* a mint but not who *ordered* it, so the ledger alone cannot answer "which admin minted this" — `@economy` writes the actor to the rotating server log as a stopgap, and the trail exists today, but it is in the wrong place. **Audit holder-count vs wallet-sum inconsistency** (Currency) — the count includes the Treasury while the sum excludes it, so a freshly minted economy reads `Wallets: nothing (1 holder)` where the one holder is the Treasury reported on the next line. **`@economy` log-line direction** (Currency) — burns log `-> treasury #N`, which reads as money going in. **Player → Treasury has no command** (Currency): `pay` refuses the Treasury by design and `donate` was deliberately not claimed, so the Stage 4 exchange-back is admin-mediated; Stage 8's `exchange` owns the direction, recorded so nobody fills the gap speculatively.

> **Rev 14 · 2026-07-30** — Stage 4 Component B close-out. Three new entries. **Bank / post office** (Currency) is the deliberate counterpart to a locked *rejection*: `pay` is same-room permanently, because coin is carried on the body and stays with the corpse, so remote payment would cancel the risk that makes carrying a decision — the sanctioned answer to "I don't want to carry this" is a *place* you have to reach. The rejection itself lives in the Currency decomposition, not here; this entry is the feature that replaces it. **`PAY_CONFIRM_THRESHOLD`** (Currency) carries the reasoning for shipping `pay` with no confirmation prompt, and the constraint that any future confirmation must not be a `yield`. ⚠️ **`CoinPile` vs the corpse's atomic delete** (Death & Corpses) is a doc-vs-code conflict found while reading corpse behaviour for B: `PlayerCorpse` destroys all contents at expiry, while Economic Philosophy Rev 2 states currency never weathers and Gold has exactly one permanent exit. Harmless today (no coin objects exist), a silent second burn point the moment `CoinPile` lands.

> **Rev 13 · 2026-07-27** — Stage 4 Component A close-out. Three new entries: **compact amount input** (`50c`, `2g30s` — one feature, one entry), the **`copper` name collision** between the material registry and the currency denomination (harmless in Stage 4, detonates when `CoinPile` materialises), and **`MINT_SOURCES` / `BURN_REASONS` tuning**. The unit-test coverage initiative is marked **DONE** — its "neither is in the repo" note was written honestly and is now simply out of date: `tests/__init__.py` and `tests/test_knowledge.py` are on `main`, `AGENTS.md` Rev 2 carries §0A, and `tests/test_currency.py` is the second suite built to the template.

> **Rev 12 · 2026-07-26** — Stage 3 close-out. **Component I (thin world-loot scroll
> seed) deferred here in full** rather than built — the decomp named it a defer-candidate
> if world-content plumbing wasn't ready, and it isn't (`world/batch_cmds.ev` is untouched
> Evennia boilerplate). The entry carries the profession-coverage analysis, the sharpened
> trigger (risk is highest at LOW player counts, so the trigger is *before the first real
> player cohort*, not "when the world is big"), and the design decisions that would
> otherwise be lost. Also added the *unit-test coverage initiative* under a new
> **Tooling & Process** section: `tests/test_knowledge.py` was drafted in an earlier
> session but is not in the repo on either branch, and `AGENTS.md` §0 never gained the
> `tests/` scope entry — logged honestly rather than left in working memory.
> **Rev 11 · 2026-07-26** — Stage 3 Component H close-out (teaching — synkron
> transfer med samtycke, H.1). Added two *Crafting & Tools* entries: *teach-channel
> tuning* (`TEACH_TIMEOUT` / `TEACH_COOLDOWN` — one axis, and the entry carries the
> `TEACH_COOLDOWN >= TEACH_TIMEOUT` invariant that makes "one student at a time"
> structural), and *Teaching skill as an amplifier* — moved into its canonical home
> here, having lived only as a decomp §15 anchor since Rev 1. The two entries are
> deliberately cross-referenced: any future "more simultaneous students" amplifier
> must be read against the invariant, since raising it silently is what would break
> the one-offer guarantee.
> **Rev 10 · 2026-07-25** — Stage 3 Component G close-out (book — perishable bulk
> transfer, G.1–G.3). Added three *Crafting & Tools* deferrals: *book-channel tuning
> constants* (`SCRIBE_MIN_CRAFT` / `SCRIBE_COOLDOWN` / `SCRIBE_CONDITION_BY_TIER` /
> `BOOK_WEAR_PER_STUDY` — one balance axis, since start-condition ÷ wear IS
> readers-per-book), *scribe's band→condition bypasses `quality_band`* (a deliberate
> consistency divergence, logged rather than refactored), and *book repair
> ("rebind")* — moved into its canonical home here, having lived only as a decomp
> §15 anchor. Extended the existing *parchment* entry with G.2's book-cover case
> instead of duplicating it (same tanning-chain blocker, same design axis).
> **Rev 9 · 2026-07-18** — Stage 3 Component G.1 (perishable `Book` typeclass).
> Added one *UX & Item Identity* deferral: *per-recipe `min_skill`/detail on
> book & scroll `look`/`evaluate`* — the "show buyers craftability, not just
> contents" refinement; MVP Alpha ships names + condition only. No new Crafting
> deferral from G.1 itself; the barter `evaluate`→`get_display_desc` fix that
> surfaced alongside it is a completed hardening (shipped on
> `feature/recipe-knowledge`), not a backlog item.
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
  instead of F.1's MVP reuse of `cloth`. G.2 extends the same question to the
  *book*: the decomposition's first shape was `parchment×N` pages plus a `leather`
  cover bound with `twine`, shipped instead as `SCRIBE_MATERIAL_TAGS = cloth×2 +
  twine`. Both carriers should adopt the hide-derived surface together.
- **Why deferred:** Parchment-from-hide needs a tanning chain that does not exist:
  `leather` is DECISION-status (unbuilt) and `raw_hide` is an orphan until tanning
  lands, so building parchment now drags in half an unbuilt economy chain. F.1
  reuses `cloth` (EXISTS, a plausible woven writing surface) so the scroll channel
  ships without blocking on tanning.
- **Trigger:** The tanning chain landing (leather / DECISION #2 resolved), decided
  *together with* the blank-scroll entry below — both answer the same question
  ("what is the physical writing surface, and is it a crafted good?").
- **Origin:** Recipe Knowledge decomp §11, Task F.1 (choice (a), locked to cloth);
  §12, Task G.2 (choice (b), book bound from cloth×2 + twine).
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

### Book-channel tuning (`SCRIBE_*` + `BOOK_WEAR_PER_STUDY`)
- **What:** The four named constants in `commands/crafting_commands.py` governing how
  fast books spread knowledge: `SCRIBE_MIN_CRAFT` (50), `SCRIBE_COOLDOWN` (120),
  `SCRIBE_CONDITION_BY_TIER` (`{critical: 100 + crit_score, success: 80, failure: 50,
  fumble: 25}`) and `BOOK_WEAR_PER_STUDY` (20).
- **Why deferred:** Balance-tuning, not a mechanic gap, and deliberately ONE entry:
  start-condition ÷ wear IS readers-per-book (currently 2 / 3 / 4 / 5+ by binding
  quality), so tuning any one constant in isolation moves the same emergent number.
  All four are conservative dev values — the material cost (cloth×2 + twine) is the
  real economic throttle, and no playtest data exists on how widely a single book
  should seed a recipe.
- **Trigger:** Live data on book production/trade cadence, or recipes spreading
  visibly faster/slower than the scroll and teach channels.
- **Origin:** Recipe Knowledge decomp §12, Tasks G.2 & G.3.
- **Status:** OPEN

### Scribe's band→condition bypasses `quality_band`
- **What:** `SCRIBE_CONDITION_BY_TIER` maps a `skill_check` result tier straight to a
  start-condition, where the house pattern routes tier → `QUALITY_BY_TIER` →
  `crafting_quality.quality_band()` → a band→condition table (E.3's
  `_apply_garment_quality` / `GARMENT_CONDITION_BY_BAND`).
- **Why deferred:** Deliberate, not an oversight. `scribe` is a standalone Command,
  not a `MongooseCraftRecipe`: it never computes a `quality` number and stamps no
  `db.quality`, so routing through `quality_band()` would mean synthesising a quality
  purely to classify it back into a condition. The four values are tuned directly
  against `DurableObject`'s colour bands instead. Cost of the divergence: if the
  quality bands are ever retuned, scribe will not follow, and books cannot gain a
  "superior" alias the way tools and waterskins do.
- **Trigger:** Retuning the quality bands, or wanting a `superior book of <recipes>`
  alias — either makes unification worth its indirection.
- **Origin:** Recipe Knowledge decomp §12, Task G.2 (locked band→condition choice).
- **Status:** OPEN

### Book repair ("rebind")
- **What:** Let a worn book be repaired/rebound rather than crumbling away, the way
  `CmdRepair` restores tools and garments.
- **Why deferred:** Excluded from Component G *on purpose*, to keep the sink clean.
  A book is the bulk knowledge-carrier; if it can be rebound indefinitely, one
  well-scribed book seeds a recipe to the whole server and the channel stops costing
  anything. Complete-then-crumble (G.3) makes the book a genuine consumable. Repair
  would also need its own material + skill story (rebinding ≠ patching leather).
- **Trigger:** Playtest showing books crumble faster than the economy can replace
  them, or a deliberate decision to soften the knowledge sink.
- **Origin:** Recipe Knowledge decomp §12, Task G.3 (and §15 anchor).
- **Status:** OPEN

### Teach-channel tuning (`TEACH_TIMEOUT` / `TEACH_COOLDOWN`)
- **What:** The two named constants in `commands/crafting_commands.py` pacing the live
  knowledge channel: `TEACH_TIMEOUT` (60s, how long a pending offer stays answerable)
  and `TEACH_COOLDOWN` (120s, between teaching *offers*).
- **Why deferred:** Conservative dev values, and deliberately ONE entry because the
  two are not independent. **Invariant: `TEACH_COOLDOWN >= TEACH_TIMEOUT`.** That
  relationship is what makes the MVP "one student at a time" rule structural rather
  than bookkeeping — an old offer has always lapsed before a teacher may send a new
  one, so there is never more than one live offer per teacher and no second copy of
  the state to keep in sync. Tuning either constant in isolation can silently break
  that guarantee. Teaching is otherwise entirely free (no material, no roll), so the
  cooldown is the whole economic and social throttle, and it is spent at OFFER time
  because the unsolicited message is the only thing `teach` can push at an unwilling
  player.
- **Trigger:** Playtest data on how fast recipes should spread person-to-person
  relative to the scroll and book channels, or offer-spam complaints.
- **Origin:** Recipe Knowledge decomp §13, Task H.1.
- **Status:** OPEN

### Teaching skill as an amplifier (never a gate)
- **What:** Use Legend's Teaching skill (INT+CHA) as a *bonus* on the knowledge
  channels — shorter `teach` cooldown, more simultaneous students, or lower book
  wear per study. Never as a permission gate.
- **Why deferred:** Locked at decomp §2 (d): the transmission gate is *know it +
  meet `min_skill`* only. Legend (p.72–73) treats Teaching as something that makes
  instruction better, not something that makes it possible — a competent smith with
  no Teaching skill can still show an apprentice how it is done. Adding it as a gate
  would also mean a second skill to raise before a player can participate in the
  knowledge economy at all, which cuts against the cold-start story professions and
  the world-loot seed exist to solve.
- **Trigger:** A chargen/skill pass that makes Teaching a real, raisable skill, plus
  a reason to differentiate teachers beyond "knows it well enough".
- **Note:** A "more simultaneous students" amplifier interacts directly with the
  *Teach-channel tuning* entry above — one live offer per teacher is currently
  guaranteed by `TEACH_COOLDOWN >= TEACH_TIMEOUT`, not by an explicit check, so
  multi-student teaching needs real per-teacher offer state rather than just a
  shortened cooldown.
- **Origin:** Recipe Knowledge decomp §2 (d) + §15 anchor; Legend p.72–73.
- **Status:** BLOCKED (on a real chargen/skill system — see *Professions & Chargen*)

### World-loot scroll seed (Stage 3 Component I — the knowledge safety valve)

- **What:** A small, deterministic supply of stamped recipe scrolls placed in the world,
  so an advanced recipe cannot become permanently unreachable when no online player holds
  the profession that grants it. Decomp §2 (c) named it the safety valve for the
  profession-grant bootstrap; §14 specified it as Task I.1. **Deferred in full at Stage 3
  close-out — Stage 3 shipped Components A–H, not A–I.**
- **Why deferred:** Three reasons, in order of weight.
  1. **The failure mode requires players, and there are none.** Profession-grant is the
     only bootstrap source (reverse-engineering needs a crafted item, and scroll/book/teach
     all need a sender who already knows the recipe), so a coverage gap is real — but it
     cannot occur with an empty server.
  2. **The valve is already operable manually.** An admin can place a correctly stamped
     scroll in one line
     (`@py ... spawn("scroll")[0] ... .stamp("linen shirt") ... .move_to(...)`, see
     Testing Reference §7). I.1 would add *automation and determinism*, not capability, so
     deferring costs almost nothing today.
  3. **There is no world to seed into.** `world/batch_cmds.ev` is untouched Evennia
     boilerplate — zero build commands. Choosing a seed location, cadence and respawn
     policy against a world that doesn't exist is guesswork that would need redoing.
- **Trigger:** ⚠️ **Before the first cohort of real players logs in** — *not* "when the
  world is large". The risk runs the other way: with few players the profession bundles
  are unlikely to be fully covered, so exposure is **highest** at low player counts and
  falls as the population grows. Treat this as a launch-blocker checklist item, not a
  someday-item.
- **Exposure at time of writing (recompute before implementing):** coverage is uneven
  across the four advanced recipes —

  | Recipe | Granted by | Exposure |
  |---|---|---|
  | `cloth` | weaver, generalist | 2 — robust |
  | `leather` | tanner, generalist | 2 — robust |
  | `linen shirt` | **weaver only** | **1 — exposed** |
  | `leather boots` | **cobbler only** | **1 — exposed** |

  So a seed needs to cover `linen shirt` and `leather boots`, not all four. `leather boots`
  is doubly exposed: single grantor, plus `min_skill = 30`, plus a dependency on
  tanner/generalist leather. ⚠️ **This table is an artefact of the current 4-recipe /
  4-profession vertical slice.** When the recipe catalogue grows the coverage maths changes
  completely — recompute against `world/professions.py` and `world/recipes.py` at
  implementation time rather than trusting this snapshot.
- **Design decisions to preserve (so the future build is short):**
  - Go through `Scroll.stamp(recipe_name)` — it owns identity and sets both `db.recipe` and
    a real stored `key` (barter matches on `obj.key`). Never hand-set `db.recipe`.
  - Only `requires_knowledge = True` recipes can be seeded; `learn` refuses common ones.
  - **Idempotency is required** — re-running the seed must not double the scrolls. Tag the
    seeded objects, or flag the room.
  - **Decide one-shot vs respawn explicitly.** A seeded scroll is *consumed* by `learn`, so
    without replenishment the valve fires exactly once, ever. That has to be a decision, not
    an accident.
  - No loot-table infrastructure — the goal is the valve, not a drop system.
- **Origin:** Recipe Knowledge decomp §14 (Task I.1) + §2 (c).
- **Status:** BLOCKED (on world content existing, and on a real player base)

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

### ⚠️ `CoinPile` vs the corpse's atomic content delete
- **What:** Decide what happens to coin left on an unlooted corpse that expires.
  `typeclasses/corpse.py::PlayerCorpse.return_appearance` deletes **every** item
  inside the body when it passes its recovery window (288 game hours), then
  deletes the body. Once `CoinPile` materialises in Stage 5 and drops on death,
  that path destroys currency.
- **Why deferred:** Harmless today — Stage 4 keeps the wallet on death (S4-3) and
  no coin objects exist, so nothing currency-shaped can be inside a corpse. It
  cannot be *resolved* today either, because the object it concerns is not built.
- **Why it matters, stated plainly:** this is a **doc-vs-code conflict**, not a
  refinement. `PolishedWorld_Economic_Philosophy.md` Rev 2 states that currency
  never weathers and that Gold has exactly **one** permanent exit (exchange back
  to GameGold). An expiring corpse would be a second, unintended and **unlogged**
  exit — and it would be invisible to `@economy audit`, because a deleted
  `CoinPile` simply stops appearing in `get_by_attribute("wallet")`, leaving the
  invariant reporting a discrepancy it cannot explain. Whichever way this is
  decided, one of the two documents has to change.
- **Trigger:** **Stage 5 kickoff**, with `CoinPile`. Three candidate resolutions:
  exempt `CoinPile` from the atomic delete; accept it as an intended sink and
  amend Economic Philosophy accordingly; or move coin to the room when the body
  crumbles.
- **Origin:** Found in Stage 4 B.2 while reading corpse behaviour for the
  same-room payment rationale (2026-07-30).
- **Status:** SCHEDULED (Stage 5, with `CoinPile`)

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

### Per-recipe `min_skill` / detail on book & scroll `look`/`evaluate`
- **What:** Show each held recipe's `min_skill` (and optionally its full detail
  block) when a knowledge carrier is inspected, so a buyer can judge whether they
  could ever craft what a book/scroll teaches — not just its name and condition.
- **Why deferred:** MVP Alpha already gives buyers the two decisive signals —
  *which* recipes (stamped key + `status` list + names in `get_display_desc`) and
  *how worn* the item is (condition) — and craftability stays discoverable by
  attempting to `learn`/craft. Adding skill/detail now would couple the `Book`
  typeclass to recipe internals for a refinement, not a blocker.
- **Trigger:** Playtest signal that buyers misjudge books (pay for recipes above
  their skill), or books routinely carrying recipes far beyond a typical buyer.
- **Origin:** Component G.1 (Rev 9) — the "val C-half" surfaced while deciding
  what `look`/`evaluate` should reveal; deferred by decision.
- **Status:** OPEN — when built, route the lookup through a `world/knowledge.py`
  helper (a names→summary renderer), NOT direct `_RECIPE_CLASSES` access, so
  `Book`/`Scroll` never become registry consumers (mirrors
  `render_recipe_detail_by_name`, keeping the coupling in one module).

> **Not listed here:** *Search / disambiguation UX + item identity* — already a
> written, cross-cutting entry in `roadmap.md` §backlog (rides on Stage 2/3 alias
> work). It has a safe home in an always-read doc, so per the scope note it is not
> duplicated here.

---

## Tooling & Process

### Unit-test coverage initiative (`tests/` + OpenCode replication)

- **What:** A committed `tests/` package running under
  `evennia test --settings settings.py .`, seeded by a heavily-commented reference suite for
  `world/knowledge.py` intended as a golden template OpenCode replicates across the other
  modules, plus an `AGENTS.md` §0 scope entry permitting OpenCode to write under `tests/`
  **only**, gated on a green run before commit.
- **Why deferred:** Honest status, not a plan: a 21-test reference suite and a
  `tests/__init__.py` marker were drafted in an earlier session, but **neither is in the
  repo** — both return 404 on `main` and on `feature/recipe-knowledge` — and `AGENTS.md` §0
  still scopes OpenCode to `world/prototypes.py`, `world/recipes.py` and
  `world/harvest_templates.py` with no `tests/` entry. The work exists only in a closed
  chat. Logging it here beats leaving it in working memory, which is exactly how the
  original draft got lost.
- **Trigger:** Any of — a regression that in-game `@py` testing would not have caught;
  onboarding a second contributor; or the crafting-catalogue expansion, where bulk
  OpenCode-generated data makes a green-test guard genuinely load-bearing.
- **Note:** The `AGENTS.md` scope entry is a **prerequisite**, not a follow-up — without it
  OpenCode has no permission to write the files it is meant to replicate.
- **Origin:** Unit-test coverage session (pre-Component G); rediscovered at Stage 3 close-out.
- **Status:** **DONE** (2026-07-27). The "neither is in the repo" note above was
  accurate when written and is now stale: `tests/__init__.py` and
  `tests/test_knowledge.py` are on `main`, `AGENTS.md` Rev 2 adds §0A and the
  `tests/` write-scope, and `tests/test_currency.py` (82 tests at Stage 4
  Component A close) is the second suite built to the golden template. The
  OpenCode *replication* half has not been exercised yet — that is a task, not a
  deferral, and lives in the stage plans rather than here. Keep for traceability,
  prune at the next backlog sweep.

---

## Currency

### `_format_wait()` truncates, so a fresh cooldown reads one unit short
- **What:** `commands/work_commands.py::_format_wait()` floors on division, so a
  cooldown set to 3600s renders as `59 minutes` from the first second onwards.
  Correct arithmetic, wrong impression: it reads as though the clock was already
  running before the chore finished.
- **Why deferred:** Purely cosmetic, and the naive fix (ceiling) is wrong in the
  other direction — it would render a fresh 3600s cooldown as `1 hour` for a
  whole minute and then jump. The right answer is probably to round to the
  nearest unit and accept a one-unit fuzz at both ends, which is a five-minute
  change nobody should make while a component is open.
- **Trigger:** Next time anyone touches faucet output, or the first player who
  mentions it.
- **Origin:** Stage 4 D.1, found in the in-game walkthrough.
- **Status:** OPEN

---

### Faucet task-table tuning (`TEMPLE_TASKS`)
- **What:** Rewards, cooldowns and now `duration` for the five temple chores, in
  `commands/work_commands.py::TEMPLE_TASKS`. The named constant is the anchor,
  per the decomposition; the numbers themselves are first-pass.
- **Why deferred:** They cannot be tuned against anything real until crafted
  goods have prices players actually charge each other. The faucet's job is to
  read as *obviously* a supplement — 170 Copper for the full chain, against a
  crafted item's eventual worth — and that ratio is unknowable before a market
  exists.
- **Trigger:** First playtest with real player-to-player pricing, or Stage 8
  when Gold acquires an external exchange rate.
- **Origin:** Stage 4 D.1 (decomposition §6/D asks for the constant explicitly).
- **Status:** OPEN

---

### Timed player actions have a pattern but no shared home
- **What:** `rest` (Stage 2) and `work` (Stage 4) both implement "this takes
  time and can be interrupted" independently: an `ndb` flag, a `delay`, an
  `at_pre_move` interrupt, a `has_account` guard in the callback. `at_pre_move`
  in `typeclasses/characters.py` now has two hand-written branches and will grow
  one per future timed action.
- **Why deferred:** Two instances is not yet a pattern worth extracting, and the
  third will teach more about the right shape than guessing now would. But the
  duplication is real and `at_pre_move` is where it will become visible first —
  a third branch is the signal to build a small `TimedAction` helper rather than
  a fourth.
- **Trigger:** The third timed action. Likely candidates: gathering with a
  cast time, or anything in Stage 6 combat.
- **Origin:** Stage 4 D.1 (Evennia Reference §11.27 documents the mechanism).
- **Status:** OPEN

---

### Ledger `actor` field — record who ordered a mint, not only who received it
- **What:** Add an `actor_key` / `actor_dbref` pair to the ledger entry shape in
  `world/economy_log.py::append()`, populated by `@economy mint` / `burn`.
- **Why deferred:** Changing the entry shape is a Component A change, and it was
  found mid-Component-C; making it then would have edited the storage primitive
  after three components had been built and tested against it. The trail is not
  missing in the meantime — every mint and burn writes a line naming the caller
  to Evennia's rotating log — it is simply in a file rather than in the record
  that `@economy audit` reads.
- **Trigger:** Component F, or the first time anyone asks the ledger a question
  it cannot answer. Note the ledger is effectively empty before Stage 8 (one
  bootstrap tranche), so a migration is cheap for exactly as long as that holds.
- **Origin:** Stage 4 C.2 (noted in the `currency_commands.py` module docstring).
- **Status:** SCHEDULED (Component F)

---

### `@economy audit` counts the Treasury as a holder but excludes its balance
- **What:** `audit()` returns `wallet_count` over every wallet holder while
  `wallet_sum` deliberately excludes the Treasury, so `audit_report()` renders
  `Wallets: nothing (1 holder)` on a freshly minted economy — the one holder
  being the Treasury, whose balance is on the line below.
- **Why deferred:** Cosmetic. The invariant is exact either way and `delta`
  is unaffected; only the parenthetical is misleading. Fixing it means choosing
  whether the count follows the sum (excluding the Treasury) or the enumeration
  (including it), which is a display decision worth making deliberately rather
  than in passing.
- **Trigger:** Component F's documentation pass, or the first time it confuses
  someone reading an audit.
- **Origin:** Stage 4 C.2 in-game walkthrough, 2026-08-02.
- **Status:** OPEN

---

### `@economy burn` log line reads as an inbound transfer
- **What:** Both mint and burn log `-> treasury #N`, which is right for a mint
  and backwards for a burn.
- **Why deferred:** One f-string. Bundled here rather than patched alone so the
  log line is fixed in the same pass as the `actor` field above, which rewrites
  it anyway.
- **Trigger:** Whenever the `actor` field lands.
- **Origin:** Stage 4 C.2 in-game walkthrough, 2026-08-02.
- **Status:** SCHEDULED (with the `actor` field)

---

### No command moves money from a player INTO the Treasury
- **What:** There is no `donate`, and `pay` refuses the Treasury (its
  `has_account` guard, whose comment anticipates exactly this). The Stage 4
  exchange-back therefore needs an admin to move the coin manually before
  `@economy burn` destroys it.
- **Why deferred:** Not an oversight — `donate` was deliberately not claimed
  (decomposition §5) and `pay`'s refusal is the same guard that stops players
  paying logged-out bodies. The direction belongs to Stage 8's `exchange`
  command, which needs the crypto side to exist before it can settle anything.
  Recorded so that a future session reads "owned by Stage 8" rather than
  "missing" and builds a stopgap that Stage 8 then has to unpick.
- **Trigger:** Stage 8 (GameGold exchange).
- **Origin:** Stage 4 C.2.
- **Status:** SCHEDULED (Stage 8)

---

### Compact amount input (`50c`, `2g30s`)
- **What:** Let `parse_amount()` accept the attached single-denomination form
  (`50c`) and the multi-denomination compact form (`2g30s`), in addition to the
  two-token form (`50 copper`) it accepts today.
- **Why deferred:** Both are the same feature and neither is needed for a
  playable currency. The shipped rule is one sentence — *exactly two
  whitespace-separated tokens, a non-negative integer and a denomination* —
  which rejects both for the same reason and is explainable to a player in a
  single error message. A compact parser needs its own grammar, its own
  ambiguity rules (is `2g30` 30 what?), and its own test surface.
- **Trigger:** Playtest evidence that typing the denomination is friction —
  most likely from `pay` in the middle of a live trade.
- **Origin:** Stage 4 A.1 (`world/currency.py::parse_amount` docstring names the
  deferral).
- **Status:** OPEN

### `copper` is both a material and a denomination
- **What:** `world/material_registry.py` registers `copper` as an INTERMEDIATE
  material (smelted from `copper_ore`, with `copper_ingot → copper` aliased),
  and Stage 4 introduces Copper as the base currency denomination.
- **Why deferred:** Harmless in Stage 4 and cheap to leave alone. The wallet is
  an `int`, there are no coin objects, and the verbs do not overlap —
  `pay 5 copper to Bob` never reaches `caller.search()`, while
  `give copper to Bob` never reaches the currency parser. Renaming either side
  now would churn the material registry and the recipe data for a collision that
  does not yet exist.
- **Trigger:** **Stage 5 kickoff** — the same trigger as the `CoinPile` deferral
  (S4-3), and for the same reason: the moment coins are real objects, two
  different things in a room answer to `copper` and `caller.search()` has to
  disambiguate them. Decide then whether to rename the metal, name the coin
  distinctly (`copper coin`), or lean on search-multimatch UX (§12 of the
  Evennia Reference).
- **Origin:** Stage 4 A.1 review; flagged in session before A.2.
- **Status:** SCHEDULED (Stage 5, with `CoinPile`)

### `MINT_SOURCES` / `BURN_REASONS` vocabulary
- **What:** The two whitelists in `world/currency.py`, currently
  `{"crypto_exchange", "admin_correction"}` each.
- **Why deferred:** Deliberately minimal. Every entry is a door money can walk
  through, so the list should grow only against a demonstrated need, never
  pre-emptively. The symmetry between the two is intentional: an unvalidated
  free-text burn reason would let the ledger fill with unrecognised tags while
  the invariant still balanced perfectly.
- **Trigger:** A real settlement scenario that neither tag describes honestly.
- **Origin:** Stage 4 A.2 (decision D8).
- **Status:** OPEN

### Bank / post office (coin and gear storage at a place)
- **What:** A location where a player can deposit coin and equipment and
  withdraw it later, plus — optionally, and separately — a way to send coin or
  goods to a player who is elsewhere.
- **Why deferred:** It is the *replacement* for a mechanic that was deliberately
  rejected, not a missing convenience. `pay` is same-room permanently (Currency
  decomposition §6/B.2 and the module docstring of
  `commands/currency_commands.py` both state the rule and its reasoning): coin is
  carried on the body and, from Stage 5, stays with the corpse to be looted, so
  carrying a large sum is a risk the player chooses. A global `pay` would cancel
  that risk for free — empty your pockets remotely from inside the dungeon and
  the decision costs nothing. A bank restores the *option* while keeping the
  cost, because reaching it is a journey that can go wrong. Building it before
  `CoinPile` exists would mean designing storage against a risk that is not yet
  implemented.
- **Trigger:** After Stage 5 (`CoinPile` / death-drop), which is what makes
  carrying risky in the first place. Player demand for remote settlement is a
  *secondary* signal and must be answered with this, never by widening `pay`.
- **Origin:** Stage 4 B.2 design session (2026-07-30); the rejection of remote
  payment is recorded in the Currency decomposition Rev 4.
- **Status:** BLOCKED (Stage 5 `CoinPile`)

### `PAY_CONFIRM_THRESHOLD` — confirmation for large payments
- **What:** An optional threshold above which `pay` asks for confirmation before
  transferring.
- **Why deferred:** `pay` ships with **no** confirmation, deliberately. Most of
  the protection is already structural: D1 requires an explicit denomination, so
  the dangerous mistake — meaning Silver and typing a bare number — is a syntax
  error rather than a silent transfer of a hundredth of the intended sum. What
  remains is socially recoverable, since there are no NPC vendors and a
  misdirected payment sits in another player's hands rather than being destroyed.
  Both parties see the amount echoed back through `format_copper`, which is the
  cheap version of a confirmation. Adding a prompt before anyone has been hurt by
  its absence is speculative UX.
- **Trigger:** Playtest evidence of players fat-fingering the *denomination*
  (`gold` for `silver`), not merely the digits.
- **Constraint on the fix:** an `ndb` two-step or an explicit `confirm` argument
  — **never a `yield`**. There is no `yield` anywhere in the codebase, and `pay`
  is the one command where S4-R1's atomicity rule applies, so it is the worst
  possible place to introduce the first one.
- **Origin:** Stage 4 B.2 (considered and rejected in the design session).
- **Status:** OPEN

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
