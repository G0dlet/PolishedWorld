# PolishedWorld — Strategic Roadmap

> **Rev 15 · 2026-08-05** — Stage 4.5 corrections from its own sub-decision close-out. **Scope changes from five call-sites to six**: `CmdScribe` was excluded by omission rather than by decision, and a rule of the form *"some Craft rolls teach and some do not, and you are not told which"* is not learnable by a player. **Rough scope grows from ~4–6 to ~6–8 commits** — Components A and B each took one, and a fifth component was added. **Component E (difficulty gate) is opened and immediately BLOCKED on recipe content**, which is the entry worth reading twice: the eight-recipe catalogue tops out at `min_skill = 30`, so a trivial-work gate would stop teaching Craft above 61 and strand every crafter who got there. It is recorded here because a blocked component that lives only in a decomposition gets forgotten at stage-planning time, which is exactly when a content trigger needs to be visible. Also records the measured effect the epic actually has: **38 eligible ticks today vs 2 931 after C.1**, a 77× slowdown, against the 43-craft measurement that opened Stage 4.5 in Rev 14.
> **Rev 14 · 2026-08-03** — **Skill progression (XP) opens as Stage 4.5**, and the Stage 1 pacing decision is superseded — the first RESOLVED entry in this log to overturn another. It is overturned by *measurement*, not by a change of mind: Stage 1 chose its pacing model before the shipped system had been measured, and at INT 12 **43 successful crafts take a skill from 0 to 100** — under two hours including gathering. Legend's Improvement Roll is calibrated for a table that meets weekly; in a world that is online continuously it is not a pacing curve at all. Three of the old entry's four parts survive untouched (raw percentage as the single mechanical truth, no cosmetic 1–99 badge, success-plus-cooldown gating); only "no hidden XP accumulator" reverses. **Numbered 4.5, not 5.** A renumber would have moved 82 `Stage N` references across 11 files — four of them production source — and four `docs/BACKLOG.md` entries carry the literal trigger *"Stage 5 kickoff"*, which would silently have come to mean this epic instead of Combat. Stage numbers stopped being ordinals the moment code comments started citing them as names; the maintenance rules now say so.
> **Rev 13 · 2026-08-03** — one-line correction found while verifying the System Map's seam table: the Stage 1 bullet said improvement-on-use was wired at **four** check-sites. It is **five** — Stage 3's `disassemble` became the fifth (`commands/crafting_commands.py:438`, and the code says so in a comment), which is why the number was true when written and false a stage later. Left deliberately untouched in Rev 12 because the count had not yet been checked against the source; checked now.
> **Rev 12 · 2026-08-03** — **Stage 4 merged to `main`** (PR #14, `02d1807`); the "merge pending" status Rev 11 recorded is now history. Rev 11 fixed the *instance* — Stage 3's heading — but the pattern behind it survived in four more places, so this revision fixes the pattern: **a branch name belongs in a changelog entry (past tense, permanently true), never in a status heading (present tense, it rots at merge).** The Nuläge section's `🔄 Feature-complete on feature/skill-improvement` heading named a branch that merged on 2026-07-10 and had since become a parking spot for two *closed* stages, while Stage 2 and Stage 4 appeared nowhere in Nuläge at all — it is replaced by **✅ Numbered stages — all merged on `main`**, keyed on a criterion that cannot expire. Stage 0 moves into it from the systems list; Stage 1/2/4 headings drop their branch names; the critical-path graph gains the three ✅ it never received. Also corrected: the Stage 3 bullet cited its decomposition at Rev 10 — it is at Rev 11. **Changelog entries are append-only** — same discipline as the economy ledger (**S4-4**): Rev 11's line stands exactly as written, and the *topmost* entry is the status.
> **Rev 11 · 2026-08-03** — **Stage 4 (In-game currency) complete on `feature/currency`, in-game-verified; merge to `main` pending.** Components A–F: currency math + `CurrencyHandler` + ledger + audit (A), `wallet`/`pay` (B), `Treasury` + `@economy` (C), the temple faucet `work` command funded by Treasury transfer (D), the barter currency bridge (E), documentation close-out (F). 316 tests green. Stage 4's two open design questions are answered and the notes rewritten to say so rather than still asking: a single Copper integer (**S4-2**) makes rounding bugs structurally impossible, and wallet-on-character beat coin-as-objects — coin-as-objects returns as `CoinPile` in Stage 5, where it is a death-drop question rather than a wallet question. **Also corrected: Stage 3 never got the ✅ its own Rev 10 changelog announced.** Rev 10's prose said "CLOSED and merged to `main`" while the heading still read like an open epic, so the scan-the-headings view of this document — the one anybody actually uses — had Stage 3 open for two weeks. A changelog entry is not a status marker.

> **Rev 10 · 2026-07-26** — **Stage 3 (Recipe Knowledge & Discovery) CLOSED and merged to `main`.** Shipped Components A–H: the per-character known-recipe set + `requires_knowledge` flag (A), the dual gate — `pre_craft` backstop + `CmdCraft` early-reject (B), the `recipes` discovery surface (C), and **five knowledge channels** — profession-grants at chargen (D), destructive reverse-engineering (E), the one-use scroll (F), the perishable multi-recipe book (G) and live consenting teaching (H). Knowledge is now a gated, tradeable resource with sources, sinks and a discovery surface, exactly as the Rev 2 decision-log entry specified. **Component I (world-loot scroll seed) deferred to `docs/BACKLOG.md`** — its failure mode needs players, the valve is manually operable, and there is no world content to seed into; trigger is *before the first real player cohort*. All four Stage 3 sub-decisions are now RESOLVED (see decision log). Decomp: `PolishedWorld_Recipe_Knowledge_Decomposition.md` (Rev 10). **Next: Stage 4 (In-game Currency).**
> **Rev 9 · 2026-07-11** — Stage 3 (Recipe Knowledge & Discovery) underway on `feature/recipe-knowledge`; the in-progress pointer moves off the now-merged Stage 2. Component A (foundation) complete & in-game-verified: per-character known-recipe set + `requires_knowledge` recipe flag (storage + declaration; the gate is Component B). Decomp: `PolishedWorld_Recipe_Knowledge_Decomposition.md` (Rev 2).
> **Rev 8 · 2026-07-11** — Stage 2 Component **G (superior-tool scaling) complete & in-game-verified → Stage 2 CLOSED**. G.1 (a *superior* crafted tool, `quality > 100`, grants `+10` on the craft check via `_tool_modifier` reading the tool's own `db.quality`; `None`-guarded, broken = absent; tool recipes gain a `superior <key>` alias) and G.2 (`CmdRepair._tool_modifier` generalised per target-type via `db.repair_tool_tag` — unset → needle default, `""` → no tool for stone knife / bone needle; superior repair tool grants +10; the old garment-centric needle bug is fixed). Ceiling reconcile: max craft quality **110 → 111** (a superior tool's +10; `skillcheck` never clamps `target`). The three orthogonal gates — knowledge (Stage 3), skill (F/E), capability (tools/G) — are all live. **Next: Stage 3 (Recipe Knowledge & Discovery)**, its own decomposition. Tactical detail in `PolishedWorld_Crafting_Progression_Decomposition.md` (Rev 8).
> **Rev 7 · 2026-07-11** — Stage 2 Component **F (skill-gate) complete & in-game-verified**: F.1 (`min_skill` floor on `MongooseCraftRecipe`, default 0 = ungated, enforced in `pre_craft` *before* consume — under-skilled crafts abort with `rolled=False`, materials untouched; the gate reads *effective* skill, so a buff/mod can lift you over it) and F.2 (only `leather boots` gated at `min_skill = 30`; every other recipe inherits the ungated default, so the survival bootstrap loop never locks). The three orthogonal gates are now distinct in code: knowledge (Stage 3), skill (this + Stage 1 improvement + E's quality scaling), capability (tools/G). Remaining Stage 2: **G (superior-tool scaling)**. Tactical detail in `PolishedWorld_Crafting_Progression_Decomposition.md` (Rev 7).
> **Rev 6 · 2026-07-11** — Stage 2 Component **E (quality → capability) complete & in-game-verified**: E.1 (`world/crafting_quality.py` band helper, single source of truth), E.2 (waterskin reads the band — superior tier finally reachable, dead `>=125` branch removed), E.3 (garment start-`condition` scaled by craft tier + `superior <key>` alias). Crafted quality is now *felt* — a critical yields a measurably better item. Remaining Stage 2: **F (skill-gate) → G (superior-tool scaling)**. Tactical detail in `PolishedWorld_Crafting_Progression_Decomposition.md` (Rev 6).
> **Rev 5 · 2026-07-10** — Stage 2 Component **D (tool wear sink) complete & in-game-verified**: D.4 (repair convergence — `CmdRepair` broadened to tools *and* garments, data-driven repair materials) and D.5 (bootstrap start-condition 40/30, prototype-override verified) shipped. The full craft loop is closed and repairable: gather/hunt → tool wears → breaks (lingers) → repair. Remaining Stage 2: E (quality → capability) → F (skill-gate) → G (superior-tool scaling). Tactical detail in `PolishedWorld_Crafting_Progression_Decomposition.md` (Rev 5).
> **Rev 4 · 2026-07-10** — Stage 2 Component **D (tool wear sink) underway**: D.1 (per-use tool wear), D.2 (broken tool = absent/improvised, not deleted), D.3 (colour-banded condition shown on `look` for tools & garments) complete & in-game-verified; D.4 (repair convergence — tools become repairable) and D.5 (bootstrap start-condition tuning) remain. The craft source→sink loop now closes (gather/hunt → tool wears → breaks → repair). Tactical detail in `PolishedWorld_Crafting_Progression_Decomposition.md` (Rev 4).
> **Rev 3 · 2026-07-10** — Stage 2 (Crafting progression & tools) **underway** on `feature/crafting-progression`: Components A (tool-modifier flip), B (shared `condition` durability axis), and C (tool bootstrap — `Tool` typeclass, stone/stick primitives + nodes, stone-knife & bone-needle recipes) complete & in-game-verified. The zero-to-tool loop is playtestable both ways (forage→stone knife, hunt→bone→bone needle). Remaining Stage 2: D (tool wear sink) → E (quality→capability) → F (skill-gate) → G (superior-tool scaling). Tactical detail in `PolishedWorld_Crafting_Progression_Decomposition.md` (Rev 3).
> **Rev 2 · 2026-07-10** — Stage 1 (Skill Improvement) **complete & in-game-verified** on `feature/skill-improvement`: primitive → gated trigger → felt-progress (tick-feedback + desc-tier celebration + `progress` command). Resolves the skill-improvement pacing/display open question (raw % is the single mechanical truth, surfaced via on-use ticks + desc-tier-crossing celebration, no 1–99 badge). Hunting (Stage 0) merged to `main`. **Critical-path reorder:** the two crafting-economy epics that cash in Stage 1 are promoted out of the backlog ahead of currency — new order S2 Crafting progression & tools → S3 Recipe knowledge & discovery → S4 In-game currency → S5 Combat → S6 Wilderness → S7 Magic → S8 GameGold (later stages renumbered +2).
> **Rev 1 · 2026-07-01** — initial strategic roadmap: felt-progress + legibility (Stage 1), recipe-knowledge economy epic, search/disambiguation UX item, full decision log.
> **Canonical:** `docs/roadmap.md` @ G0dlet/PolishedWorld — git wins. If this project-knowledge copy's Rev is lower than the repo's, it's stale — re-upload from the repo.

> **Supersedes** `PolishedWorld_Implementation_Plan.md` (retired — its content is fully implemented/merged).
> This document operates at **epic/milestone altitude**: *what we tackle next and why, in which order*.
> It deliberately contains **no tasks, no code, no `@py` tests** — those live in per-feature decomposition docs.

---

## How this document relates to the others

PolishedWorld has three planning altitudes. Keep them distinct to avoid drift:

| Altitude | Document(s) | Answers | Updated when |
|---|---|---|---|
| **Strategic** | *this file* | What's next, why, in what order | An epic starts/finishes or sequencing changes |
| **Tactical** | `*_Decomposition.md` (e.g. hunting, skill improvement) | How to build one feature, task by task | During a feature's design session |
| **Reference** | `*_Evennia_Reference.md`, `*_Mongoose_Legend.md`, `*_Code_Standards.md`, `GameGold_*` | Hard-won facts, gotchas, rules | As learnings accrue |

**Workflow per epic:** when an epic comes off this roadmap, run *one* design/source-verification session → produce a decomposition doc → implement task-by-task. This file then marks the epic Done.

---

## North star (design pillars the roadmap serves)

1. **100% player-driven economy** — no NPC vendors; every item player-crafted from gathered/hunted resources; prices emerge.
2. **Sandbox survival** — hunger/thirst/fatigue as the core loop.
3. **Dynamic environment** — 13-month calendar (4× speed), seasons, weather, day/night.
4. **GameGold (experimental)** — crypto layer, 1:1 with in-game gold, hobby/experiment framing.

Every epic below is justified against at least one pillar. Anything that serves none is a candidate for the cut list.

---

## Nuläge

### ✅ Done & merged on `main`
- **Character foundation** — TraitHandler stats/survival gauges/skills; character commands (stats/status/skills/sheet).
- **Environment** — gametime infrastructure (13-month calendar, 4× speed); `world/gametime_utils.py` central time bridge (single source of truth: `get_current_time`/`get_absolute_gametime`/`get_time_of_day`/`get_season`); weather system; ExtendedRoom-driven time/season descriptions.
- **Survival loop** — hunger/thirst/fatigue ticker, conditions, Food/Drink typeclasses, consumption commands.
- **Foraging** — `ResourceNode` with lazy regeneration, `CmdForage`/`CmdRefill`, `CooldownHandler`.
- **Crafting foundation** — `MongooseCraftRecipe`, `world/skillcheck.py` (d100 utility), starter recipes (twine/waterskin/cloth/linen shirt).
- **Barter** — `PWTradeHandler`, timeout/staleness guards, worn-item no-trade guard.
- **Clothing & thermal** — `ClothingWithBuffs`, `world/thermal.py` (per-regime `COMFORT_BANDS`, replacing the old flat `COMFORT_MARGIN`), Cold/Heat stress buffs, garment prototypes.
- **QoL/infra** — statue logout system, custom menu-login connection screen.

### ✅ Numbered stages — all merged on `main`

- **Stage 0 — Hunting** ✅ — full loop: `Creature` + tag-based `CreatureSpawnScript`, `hunt` skill-check command, corpse system with decay, harvesting (meat/hide → craftable materials, activating the stubbed wool/fur/leather recipes), respawn ticker, and player death (`at_character_death()` hook + `apply_health_damage()` chokepoint — the seams combat will reuse). Canonical doc: `PolishedWorld_Hunting_Decomposition.md` (Rev 2).

- **Stage 1 — Skill Improvement** ✅ — Legend-faithful improvement-on-use (`world/improvement.py` pure primitive → `improve_skill_on_use` chokepoint → `attempt_skill_improvement` gated wrapper, wired at five check-sites: craft, repair, hunt-attack, hunt-harvest, and disassemble — the fifth added by Stage 3 Component E), plus the felt-progress layer: per-tick feedback, desc-tier-crossing celebration, and the `progress` command (deltas since login). In-game-verified. Canonical doc: `PolishedWorld_Skill_Improvement_Decomposition.md` (Rev 3).

- **Stage 2 — Crafting progression & tools** ✅ — Components A–G: tool-modifier flip (A), shared `condition` durability axis (B), tool bootstrap — `Tool` typeclass, stone/stick primitives, stone-knife & bone-needle recipes (C), tool wear sink + `CmdRepair` convergence (D), quality → capability via `world/crafting_quality.py` bands (E), `min_skill` recipe gate (F), superior-tool scaling (G). The three orthogonal gates — knowledge, skill, capability — are all live; max craft quality 111. Canonical doc: `PolishedWorld_Crafting_Progression_Decomposition.md` (Rev 9).

- **Stage 3 — Recipe knowledge & discovery** ✅ **CLOSED & merged** — Components A–H. Known-recipe set + `requires_knowledge` flag (A); dual gate, `pre_craft` backstop + `CmdCraft` early-reject (B); `recipes` discovery surface (C); and five knowledge channels: profession-grants (D), reverse-engineering (E), scroll (F), perishable book (G), live teaching (H). Component I (world-loot seed) deferred → `docs/BACKLOG.md`. Canonical doc: `PolishedWorld_Recipe_Knowledge_Decomposition.md` (Rev 11).

- **Stage 4 — In-game currency** ✅ — Components A–F: currency math + `CurrencyHandler` + append-only ledger + audit invariant (A), `wallet`/`pay` (B), `Treasury` + `@economy` (C), the temple faucet `work` command funded by Treasury transfer (D), the barter currency bridge (E), documentation close-out (F). Wallet is a single Copper integer with no declared Attribute (**S4-2**, **D6**); `Treasury.add()` is the only mint path (**S4-1**). 316 tests green. Canonical doc: `PolishedWorld_Currency_Decomposition.md` (Rev 7).

---

## The roadmap (post-Stage-1)

Ordering principle: **make progression real → make it *matter* (skill-gated recipes, better goods) → turn knowledge into an economy → put money in → add stakes → add space → add depth → the experimental layer last.** Estimates are *very rough*, in commits, at the ~5 h/week, 3–5 tasks/session rhythm.

### Critical path

```mermaid
graph LR
    S1[Stage 1: Skill Improvement ✅] --> S2[Stage 2: Crafting Progression + Tools ✅]
    S2 --> S3[Stage 3: Recipe Knowledge ✅]
    S3 --> S4[Stage 4: In-game Currency ✅]
    S4 --> S45[Stage 4.5: Skill Progression XP]
    S45 --> S5[Stage 5: Combat]
    S5 --> S6[Stage 6: Wilderness + Scaling]
    S6 --> S7[Stage 7: Magic]
    S7 --> S8[Stage 8: GameGold]
    P[Parallel backlog:<br/>character creation, disease,<br/>herbalism, taming, web sheet] -.slot in between.-> S5
```

---

### Stage 0 — Hunting ✅ *(complete, merged to `main`)*
**Delivered:** H2.x–H7 per the hunting decomposition — hunt → corpse → harvest → meat/hide/leather in crafting; HP 0 = death works.
**Pillars:** survival, player-driven economy (source+sink).
**Strategic payoff:** closed the survival→harvest→craft→economy loop with animal-sourced materials (a new *source* feeding existing clothing/food *sinks*), **and** laid the death seams combat reuses.

---

### Stage 1 — Skill Improvement System ✅ *(complete — merged to `main`)*
**Goal (met):** an automated, Legend-faithful progression layer so skills grow through use — no GM, no levels, no XP-as-a-character-stat — **and is *felt*.** Because Legend has no level-up "ding," a mechanically correct system can still ship as an invisible backend that feels dead. The epic is not done when the number quietly grows; it's done when the player *notices* growth. This epic owns the skill-number axis **and its presentation**.
**Why here (before combat):** relatively contained, but it retroactively makes *all* existing skill use — hunting, crafting, foraging — progression-meaningful at once, and combat + magic will both lean on it. Highest leverage per unit effort on the board.
**Legend alignment:** Legend has **no character levels and no XP**. Its two advancement paths port very differently:
- *Improvement Rolls* — GM-awarded at narrative beats (roll 1D100 + INT vs current skill → >current gives +1D4+1, else +1). The real trigger is the **GM's judgment of a story beat**, which has no multiplayer equivalent, so this path **does not port**. Replaced with **improvement-on-use that resolves at the check itself** (RuneScape-style): immediate feedback, rewards activity. ✅ shipped.
- *Training* — downtime + teacher + funds; a week of study, then 1D100 vs current skill; can't train the same skill twice in a row. This **ports cleanly** (classic MUD trainer tradition). The teacher is a *player* with high skill + Teaching charging coin — a progression sink *and* an economic activity (pillar 1). *(Deferred; pairs with Stage 3 recipe-teaching and Stage 4 currency.)*

**Anti-grind throttle (shipped):** the action's own cooldown + Legend's self-throttling curve (high skills rise slowly) — **not** forced rest. Improvement is gated to success-against-real-difficulty under a per-skill real-time cooldown.
**Felt-progress / legibility layer (✅ delivered):** immediate feedback on each meaningful tick, celebration on crossing a skill's **named desc-tier boundaries**, and the `progress` command showing deltas since login. This is what converts "the number grew" into "I made progress." *(Tactical detail — command, message copy, tier logic — lives in the Stage 1 decomposition, Rev 3.)*
**Outcome (see decision log):** raw % is the single mechanical truth; surfaced RuneScape-near via frequent on-use ticks + desc-tier-crossing celebration; no cosmetic 1–99 badge for now.
**Pillars:** progression backbone for every skill-using system; the Training path (deferred) doubles as player-to-player economic activity (pillar 1).

---

### Stage 2 — Crafting progression & tools ✅ *(complete — merged to `main`)*
**Goal:** turn Stage 1's skill numbers into **felt capability** — gate higher recipes behind skill thresholds, scale output quality with skill (crit-craft → superior item) — and make tools a player-crafted quality/efficiency layer with a durability sink.
**Why here (promoted ahead of currency):** it depends only on Stage 1 (now done) and is the cheapest, highest-"makes-progression-matter" payoff on the board. Without it the Stage 1 numbers stay a stat readout; with it they become a growing craft menu and better goods.
**Scope — two threads:**
- *Skill → capability:* recipe skill-gates + quality tiers driven by the craft-check outcome (the fumble/success/critical tiers `skillcheck.py` already resolves). Rides straight on the improvement layer.
- *Tools:* tools must be player-crafted (no implicit NPC source, per pillar 1). Design them as quality/efficiency **modifiers, not hard gates** (fits the existing `consume_policy="raw"` philosophy), to avoid the bootstrap chicken-and-egg where the first tool can't be made. **Tool durability/wear = the sink**, and creates recurring economic demand.
**Bonus:** individuating crafted items by material/quality ("a superior steel dagger") also feeds the search/disambiguation root-cause fix (backlog) for free.
**Dependencies:** Stage 1 (✅), crafting foundation (✅).
**Pillars:** player-driven economy (recurring tool demand = sink), progression (felt capability).
**Rough scope:** small–moderate — a refinement of the existing crafting system, not a from-scratch epic.

---

### Stage 3 — Recipe knowledge & discovery ✅ *(complete — merged to `main`)*
**Goal:** make recipe knowledge a **gated, tradeable resource** rather than a universal capability (decision log: RESOLVED). Today every character can craft every recipe but can't even *see* which exist; knowledge is neither gated nor a resource. Players learn / buy / sell / teach recipes → knowledge becomes an economic good driving specialisation and interdependence (pillar 1).
**Why here (before currency):** pillar-1-core, and it pairs tightly with Stage 1's training loop (teaching) and Stage 2's skill gate. Buy/sell ideally wants coin, but **barter works in the interim** — so it can precede currency without blocking.
**Keep three orthogonal gates distinct:** **knowledge** (binary — do you know it? *this epic*), **skill** (how good — Stage 1 + Stage 2's quality scaling), **capability** (tools/stations — Stage 2 tools / deferred metallurgy).
**Scope:** a per-character known-recipe set; a craft-time knowledge check; a discovery/legibility surface (what you know, with a hint that more exists); and knowledge *sources* — tradeable books/scrolls, player teaching (matches Stage 1's training loop **and** Legend's teacher-gate: Craft can't be self-taught, rulebook p.70–71), and profession grants at chargen.
**Cold-start hybrid (near-certain):** basic survival recipes = common knowledge; only advanced recipes must be learned — else new players can't eat or make twine (the same cold-start shape the GameGold temple-faucet solves).
**Bootstrap concern:** books/teachers need their *own* first source (world-loot seed or a starting master), or no one can write the first book.
**Legend fidelity:** "recipes" are a MUD convention (Legend has only Craft rolls), but gated knowledge *transfer via teacher* is rulebook-faithful.
**Dependencies:** crafting foundation (✅); pairs with **Stage 1** (teaching = the training loop), **Stage 2** (the skill gate), and **Stage 4** (buy/sell wants real coin — barter interim).
**Open sub-decisions (its design session):** book vs scroll (sink strength); exact cold-start baseline; bootstrap source (world-loot seed vs starting master vs profession grants); whether player teaching requires Legend's Teaching skill. See decision log.
**Pillars:** player-driven economy (knowledge as a tradeable good; specialisation + interdependence).
**Rough scope:** moderate–large. **Needs its own design session** before decomposition.

---

### Stage 4 — In-game currency ✅ *(complete — merged to `main`)*
**Goal:** Gold/Silver/Copper as actual money (100:1:1), with a character wallet and basic give/pay/price plumbing — the medium of exchange the economy currently lacks.
**Why here:** the economy is **barter-only** today (no coin system in the repo). Several items assume money: Stage 1's Training-via-teacher, Stage 3's recipe buy/sell (charging coin), and **Stage 8 GameGold, which is defined as 1:1 with in-game gold** — gold must exist as a currency before the crypto layer can bridge to it. Kept small and early so it unblocks all coin-based trade while the economy is still small.
**Pillars:** player-driven economy (the exchange primitive everything else trades through).
**Dependencies:** none hard; pairs with barter (`PWTradeHandler`), Stage 1's training loop, and Stage 3's recipe trade.
**Hard requirement:** must land **before Stage 8 (GameGold)**.
**Rough scope:** small, ~3–5 commits.
**Design notes:** *(both questions now answered — kept for the reasoning.)* Denominations are a single base-unit integer under the hood (stored in Copper, rendered as G/S/C), which is what makes rounding bugs structurally impossible rather than merely guarded against — **S4-2**. Wallet-on-character won over coin-as-objects for Stage 4: an integer Attribute, with no `wallet` Attribute declared on the typeclass so there is no bypass write (**D6**), and no coin objects at all. Coin therefore reaches the barter table as a number on the trade handler rather than as goods. Coin-as-objects returns as `CoinPile` in **Stage 5**, where it is a death-drop question rather than a wallet question.
**Shipped:** `world/currency.py`, `world/economy_log.py`, `typeclasses/treasury.py`, `wallet`/`pay`/`@economy`/`work`, and the barter currency bridge. 316 tests. Components A–F; see `docs/PolishedWorld_Currency_Decomposition.md`.

---

### Stage 4.5 — Skill progression (XP) *(small; blocks nothing, shapes everything)*
**Goal:** give every skill a growth curve that survives a persistent world, by reinterpreting Legend's Improvement Roll rather than replacing it. The roll stays verbatim; its *output* becomes XP banked toward the next whole percentage point instead of points added directly.
**Why here:** Stage 1 shipped a mechanically faithful system that is **43 successful uses wide**. Measured at INT 12: 0 → 100 in about 22 minutes of pure cooldown, under two hours including gathering. Every epic after this one — combat, magic, wilderness — hangs progression off the same primitive, so the curve is far cheaper to fix now than once three more systems ride on it. It also blocks nothing: no other stage depends on it.
**Scope — the shared primitive, so all six improvement call-sites move together:** craft, repair, hunt-attack, hunt-harvest, disassemble, scribe. Crafting-only would leave hunting maxing in 43 kills, and two progression engines in one game. *(Rev 15: five → six. Scribe rolls Craft with a material cost and a real failure mode; it was left out by omission, and the resulting rule — some Craft rolls teach, some do not, and the player is not told which — is not one anybody could infer.)*
**Storage:** lifetime-total XP per skill is the sole persisted truth. Level and progress bar are **derived**, never stored — so recalibrating is a settings change rather than a migration, and the bar cannot drift out of step because there is nothing to drift. `skill.current` becomes a materialised cache with exactly one writer, the same discipline `world/currency.py` holds over the wallet Attribute (**S4-R2**).
**Curve shape (measured, not assumed):** normalised to equal total playtime, Tibia's cubic and a doubling-every-20-points exponential put **68%** and **70%** of playtime in the last quartile of the scale; RuneScape's (×2 per 7 levels) puts **94%** there, which on a 100-point scale erases the lower half entirely. RuneScape's shape is ruled out; the other two are effectively the same design.
**Calibration is deliberately NOT fixed by this epic.** It cannot be known before there is content and players. One documented constant in `settings.py` carries a provisional value plus the procedure to recompute it. **Generous now, tightened never** — lowering the curve later is free, raising it de-levels people.
**Cap:** Legend's >100% band, which `world/improvement.py` deliberately left unimplemented (the formula is already sitting in its docstring), becomes reachable. No hard cap at 100.
**⛔ Component E (difficulty gate) is BLOCKED on recipe content, and will not ship with A–D.** Without it the optimal route to Craft 100 is to repeat the cheapest recipe you know ~2 900 times; the curve taxes that grind but does not object to it. The gate that fixes it — a craft far below your skill teaches nothing, which is Legend-faithful and uses a seam `attempt_skill_improvement` already carries — needs recipes at graduated `min_skill` values. There are eight recipes and the highest is 30, so the gate would stop teaching Craft above 61 and strand every crafter who reached it. **Trigger: a recipe catalogue that ladders across the scale** (`docs/BACKLOG.md`, *Crafting & Tools*, BLOCKED). A–D are unaffected and ship without it.
**Measured effect (2026-08-05, 400 simulated careers, INT 10):** craft 20 → 100 takes **38** eligible ticks on the shipped system and **2 931** after Component C — a 77× slowdown, or ~19 minutes against ~24 hours at the 30 s cooldown. The cooldown is deliberately **frozen** at 30 and reclassified from anti-spam guard to wall-clock floor: the curve is the sole calibration knob, because two levers with the same observable effect cannot be told apart after the fact.
**Dependencies:** Stage 1 (✅). **Pillars:** progression backbone for every skill-using system.
**Rough scope:** small–moderate, ~6–8 commits (A and B took one each; E is blocked and not counted). Decomp: `PolishedWorld_Skill_Progression_Decomposition.md`.

---

### Stage 5 — Combat *(recommended big epic)*
**Goal:** opposed-d100 combat that turns the survival *simulation* into a survival *game* with stakes.
**Why here:**
- Hunting **Stage 0 already provides the seams** (`at_character_death()`, `apply_health_damage()` chokepoint) — combat plugs straight in.
- It gives **existing crafting a purpose**: weapons and armor currently have no use.
- It's the **highest-leverage gameplay addition** for the few early players.

**Mongoose Legend alignment:** opposed d100, combat actions, hit locations, fumble/critical tiers (already in `skillcheck.py`), weapons/armor from *Arms of Legend*. **Key adaptation decision:** real-time-with-cooldowns vs turn-based rounds — project stance is real-time/cooldowns, which needs careful multiplayer-fairness design.
**Dependencies:** Stage 0 (death seams), crafting (gear), thermal/clothing (armor-layering interaction to resolve).
**Pillars:** survival (stakes), player-driven economy (activates weapon/armor sinks).
**Rough scope:** large, ~10–15+ commits. **Needs its own design/source-verification session** (Legend combat + *Arms of Legend*) before decomposition.
**Open questions:** PvE-only first or PvP? Cooldown model for fairness under 10+ concurrent players.

---

### Stage 6 — Wilderness / XYZ grid + dynamic world scaling
**Goal:** give the world Daggerfall-scale room; tie world growth to population milestones (story-justified frontier setting).
**Why here (after combat):** new space populated with *stakes* (encounters, danger) rather than empty rooms; more room for hunting/foraging/combat.
**Implementation note:** `evennia.contrib.grid.xyzgrid` is the likely base (verify at source). **Procedural generation is the long-term vision — initial scope is a hand-built frontier with scaling hooks**, not a generator.
**Dependencies:** creature spawning (done), combat (so wilderness has stakes), gametime bridge.
**Pillars:** dynamic environment, dynamic world scaling.
**Rough scope:** large.
**⚠️ Main sequencing fork:** Stage 5 ↔ Stage 6 order. Recommendation is combat-first (Stage 0 seams + crafting payoff). Flip to world-first only if "more space" feels more compelling to early players than "more danger." Record the decision below when made.

---

### Stage 7 — Magic (Common, Divine, Sorcery, Spirit, Blood)
**Goal:** layer Legend's magic schools onto the game.
**Why here:** several schools are combat-adjacent (Sorcery offensive, Divine/Spirit support) — combat gives them something to plug into. POW/Magic Points already exist in the trait foundation.
**Mongoose Legend alignment:** Legend core (Common/Divine/Sorcery) + Spirit magic book + Blood magic ebook (all in project knowledge). Huge surface area.
**Dependencies:** combat (for offensive magic to matter), POW/MP traits (exist).
**Pillars:** depth, Legend fidelity.
**Rough scope:** very large — **decompose school-by-school, each as its own feature.** Likely Common first (simplest), then expand.

---

### Stage 8 — GameGold integration
**Goal:** the experimental crypto layer (blackcoin-more fork, 1:1 with in-game gold, temple-faucet cold-start, manual exchange initially).
**Why last:** explicitly post-MVP, and its whole point — emergent market value — **needs market participants**, i.e. a living player economy first. Also the highest external/infra risk (node on Orange Pi, upstream Bitcoin Core rebase maintenance).
**Dependencies:** **Stage 4 (in-game currency) — hard prerequisite**, since GameGold bridges 1:1 to in-game gold; plus a functioning player economy (barter ✅) and enough players for exchange to be meaningful.
**Pillars:** experimental economy.
**Design docs already exist:** `GameGold_Design.md`, `GameGold_Blockchain_Platform.md`.
**Framing guardrail:** hobby/experiment, speculation discouraged, value set by free market.

---

## Parallel / opportunistic backlog (off the critical path)

Low-dependency epics to slot in when a week's 5 hours don't suit a heavy epic — palate-cleansers and motivation wins:

- **Legend character creation** — replace the current hardcoded static traits/skills (every player identical) with proper Legend Adventurer Creation: roll *or allocate* the seven Characteristics (STR/CON/SIZ/DEX/INT/POW/CHA) → derive attributes (HP, damage modifier, Magic Points, Strike Rank, Improvement Roll modifier) → layer **Cultural Background** (Barbarian/Civilised/Nomad/Primitive: Common-skill bonuses, Combat Styles, Advanced Skills, starting money) + **Profession** + **free skill points** + community/family + starting gear. Works now with hardcoded values, so off the gameplay critical path — but **heavier than the other backlog items and a soft prerequisite for any wider/public launch**: it's what gives characters identity and replayability, and it's what lets the stat-derived mechanics (STR damage, DEX strike rank, POW magic points, INT skill improvement) actually produce variation worth testing. Pairs naturally with the character/skill layer (same backfill/migration concern — existing hardcoded characters must be grandfathered or offered a one-time re-roll). Build as a guided Evennia `EvMenu` chargen flowing from the existing `menu_login` screen. *(Consider elevating to a numbered stage if a launch milestone gets scheduled.)*
- **Disease system** — seasonal, ties to gametime + survival. Pairs naturally with herbalism.
- **Herbalism** — extends foraging + crafting toward medicine; pairs with disease.
- **Animal taming** — extends creatures/hunting.
- **Web character sheet UI** — Evennia web; independent of game systems, so safe parallel work with low blast radius.
- **Heroic Abilities / Hero Points** — Legend's prestige/perk track (rulebook p.218): abilities bought with Hero Points once an Adventurer *qualifies* (skill thresholds, and often a cult/brotherhood or a specific master to learn from). These are the rare "ding" moments — the punctuation marks above Stage 1's otherwise smooth curve, and the top of the felt-progress ladder. Mostly combat/magic-adjacent, so it slots naturally alongside **Stage 5/7** and a future brotherhood/cult system rather than standing alone. Logged here so it isn't lost; not near-term.
- **Achievements / milestones / firsts** — the legibility/juice layer that complements Stage 1's felt-progress goal: track and celebrate firsts and personal records (first steel ingot, 100th arrow crafted, first successful hunt). Attribute-flag based, low blast radius, independent of game-system internals — safe parallel work like the web-sheet item. Small.
- **Search / disambiguation UX + item identity** — the default multimatch prompt (`dagger-1`, `dagger-2`) is a *symptom* of items sharing an identical key, not a bug to reskin. Evennia exposes this deliberately as tunable (a settings-level regex+template pair, and a fully replaceable result-formatting hook — technical details in `PolishedWorld_Evennia_Reference.md` §12). Two-layer fix, root-cause first: **(1)** individuate crafted items with distinguishing adjectives/aliases (material, quality, maker's mark) so `steel dagger` resolves to a single match — rides *free* on **Stage 2**'s crafting-quality scaling and **Stage 3**'s recipe work (crit-craft → "a superior steel dagger"); **(2)** stack truly-identical consumables (arrows, twine) into one quantity-bearing object rather than N disambiguable ones — also lighter on the DB (fewer objects = perf win with many players). **Residual polish (low priority):** reskin the multimatch prompt to a clean numbered list, or make it interactive (pick by keypress) instead of re-typing `dagger-2`. Low blast radius; pairs with crafting/inventory. Not its own epic — a cross-cutting UX concern to fold in as crafting/consumables mature.

> **Promoted to the critical path (Rev 2):** *Crafting tools & progression chain* → **Stage 2**; *Recipe knowledge & discovery* → **Stage 3**. They were the two backlog items that most directly cash in Stage 1's skill numbers (skill-gated recipes, quality scaling, teaching/knowledge trade), so they moved ahead of currency.

**Noted, not yet scheduled** (raised in review; flesh out when they come into focus):
- **Persistent storage / housing / settlements** — somewhere to keep goods offline and claim space; partly implicit in Stage 6 (wilderness) but not designed. Load-bearing for a survival sandbox with Daggerfall-scale ambition.
- **Launch readiness** — admin/moderation + anti-grief tooling and an economy-health view (faucet-vs-sink audit). PvP + a real economy create exploit surface; needed before any wider opening, not before.

---

## Decision log & open questions

Record outcomes here as they're settled so the roadmap stays a single source of truth.

- **[RESOLVED] Near-term ordering (Rev 2)** — crafting progression & tools (**Stage 2**) and recipe knowledge & discovery (**Stage 3**) promoted ahead of in-game currency (**Stage 4**). Rationale: both depend only on the just-completed Stage 1 and directly convert its skill numbers into felt capability and economic activity; currency is small and can follow (recipe buy/sell runs on barter in the interim). Later stages renumbered +2 (Combat 5, Wilderness 6, Magic 7, GameGold 8).
- **[RESOLVED] Skill-improvement pacing model** — Legend formula (occasional self-throttling jumps) vs RuneScape-style hidden-XP accumulator vs cosmetic 1–99 level badge. Percentage stays the mechanical input in all three. **Decision (Stage 1 build, in-game-verified):** raw percentage is the *single mechanical truth*, surfaced RuneScape-near via frequent small on-use ticks + **desc-tier-crossing** celebration (the skills' own named ranks — the 25/50/75/100 quarters were dropped as decoupled from those ranks). No cosmetic 1–99 badge for now — revisit only if playtesting shows the raw % reads as flat. Ticks fire only on success against real difficulty (the `meaningful` gate) under a per-skill real-time cooldown.
- **[RESOLVED] Skill progression → XP-per-level, superseding the pacing entry above (Stage 4.5).** The entry above was settled *before the shipped system was measured*. Measured: at INT 12, **43 successful crafts move a skill from 0 to 100** — Legend's Improvement Roll is a reward mechanic for a table meeting weekly, not a pacing curve for a world that is online continuously. **Decision:** keep the roll verbatim and reinterpret its output — `1D100 + INT > current` banks **2–5 XP** instead of adding 1D4+1 points; the floor banks 1. An exponential per-skill threshold stands between each whole percentage point. **What does not change:** the raw percentage remains the single mechanical truth that every check, gate, buff and desc-tier reads via `skill.current`, and no second number is shown to the player — the cosmetic 1–99 badge stays rejected. Only "no hidden XP accumulator" reverses. **Storage:** lifetime-total XP is the sole persisted truth; level and progress bar are derived, never stored, so recalibration is a settings change and the bar cannot drift. **Shape:** Tibia-cubic / doubling-every-20 (both ≈70% of playtime in the top quartile); RuneScape's ×2-per-7 ruled out by measurement (94%). **Calibration deferred on purpose** — unknowable before content and players; one settings constant, provisional value, generous now and tightened never. **Scope:** the shared primitive, so all five call-sites move together. **Cap:** Legend's >100% band becomes reachable.
- **[RESOLVED] Recipe-knowledge model → gated + tradeable** *(now elevated to Stage 3, Rev 2)*. Recipe knowledge is a gated, tradeable resource, not a universal capability: players learn / buy / sell / teach recipes (pillar 1 — specialisation + interdependence). Supersedes the current "everyone can craft everything" state. **Sub-decisions still open, for the Stage 3 design session:** (a) *book vs scroll* — reusable permanent unlock vs consumable one-shot (sink strength); (b) *cold-start baseline* — exactly which recipes count as common knowledge; (c) *bootstrap source* — how the first books/knowledge enter the world (world-loot seed vs starting master vs profession grants); (d) *teaching mechanic* — whether player teaching requires Legend's Teaching skill and how it gates. *(e) elevate to a numbered stage → ✅ done: Stage 3.)*
- **[OPEN] Stage 5 vs Stage 6 order** — combat-first recommended (Stage 0 seams + crafting payoff). Revisit if space > danger for early players.
- **[OPEN] Death-consequence policy** — Stage 0 built the *mechanic* (HP 0 → death → player-corpse), but the *consequence* is undecided: permadeath or not, item loss on death, corpse-retrieval runs? It's simultaneously a stake (combat) and a sink (economy), and it interacts with coin-as-objects (Stage 4) — decide it deliberately, not implicitly in a commit.
- **[OPEN] Combat: PvE-only first vs PvP** — affects fairness/design scope.
- **[OPEN] Combat timing model** — real-time-with-cooldowns is the stance; needs explicit multiplayer-fairness design before decomposition.
- **[OPEN] GameGold trigger** — tie launch to a player-count milestone, not a calendar date.
- **[OPEN] Character creation: rolled vs point-buy** — Legend offers both random (3D6 / 2D6+6) and a non-random points method. Pure random rolls invite re-roll abuse in a MUD (recreate until good stats); point-buy or a constrained standard array is the multiplayer-fair choice and stays Legend-faithful. Also: map cultural/professional skill grants onto the *locked skill taxonomy* (hunting/craft/…), not Legend's full skill list.
- **[DEFERRED] Procedural world generation** — hand-built frontier + scaling hooks first.

---

## Document metadata

- **Home:** `docs/roadmap.md` in the `G0dlet/PolishedWorld` repo — this is now the canonical copy; git history is the changelog (no manual "last updated" bookkeeping).
- **Replaces:** `PolishedWorld_Implementation_Plan.md` (retire it from project knowledge)
- **Altitude:** strategic (epics/milestones)
- **Framework:** Evennia · **Ruleset:** Mongoose Legend (d100)
- **Cadence:** ~5 h/week, 3–5 tasks/session, "skynda långsamt"
- **Maintenance rule:** update on epic start/finish or when sequencing changes; keep tasks out of this file.
- **Stage numbers are identifiers, not ordinals.** They are cited by name in `docs/BACKLOG.md` triggers and in production code comments — 82 references across 11 files as of Rev 14 — so renumbering silently repoints them at the wrong epic. An epic inserted between two existing ones takes a **decimal** (Stage 4.5); never renumber.
- **Status vs. history:** branch names belong in changelog entries (past tense, permanently true), never in status headings (present tense — they rot the moment the branch merges). Changelog entries are append-only; the topmost entry is the status, and older entries are left exactly as written.
