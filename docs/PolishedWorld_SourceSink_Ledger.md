# PolishedWorld — Source / Sink Ledger

> **Rev 2 · 2026-08-03** — Stage 4 currency shipped, so the currency row moves off `[BLOCKED]` — and reading it against the code found the row claiming a tighter guarantee than the code provides. **`MINT_SOURCES` has two tags, not one**: `admin_correction` sits beside `crypto_exchange` to repair the exchange path, ledgered and audited identically and never a grant mechanism, with `BURN_REASONS` carrying the matching pair. **The faucet transfers out of the Treasury rather than redistributing** (S4-1) — the distinction matters, because it is why an empty Treasury makes the faucet dry instead of inflationary. **The death-drop was stated in the present tense** and is not shipped: S4-3 keeps the wallet through death, and the drop waits on `CoinPile` in Stage 5 — flagged here rather than only in BACKLOG because it arrives as a *potential second sink*, which is exactly the class of bug this ledger exists to catch. Also added: **barter settlement is a transfer, not a sink** — do not file it as one — and the note that this is why it is deliberately unledgered (S4-4), the invariant `Σ(wallets) + Treasury == Σ(mint) − Σ(burn)` being the proof rather than a transaction history. Status split honestly: wallet, ledger and audit are `[EXISTS]`; the exchange itself remains `[BLOCKED: Stage 8]`.
> **Rev 1 · 2026-07-19** — first version. Whole-economy source/sink roll-up (pillar 1). Materials delegate to `world/material_registry.py`; currency/goods sinks defer to the economy docs. Uses the `docs/crafting/` status vocabulary.
> **Canonical:** `docs/PolishedWorld_SourceSink_Ledger.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

## What this is

One place to answer, for anything that enters the economy: **where is it born,
and where does it die?**

Three gap types (vocabulary shared with `docs/crafting/`):

- **orphan** — a source but **no sink** (inflation / dead-end clutter).
- **`[SINK BLOCKED]`** — a finished good whose *consumer* is unbuilt (it can be
  made but does nothing yet, e.g. a sword with no combat system).
- **fountain** — a sink but **no source** (can never be obtained).

All three are bugs against pillar 1.

## Design: this doc does NOT restate the material registry

`world/material_registry.py` **already is** the source/sink ledger for raw and
intermediate *materials* — each entry carries `source`, `sinks`, `status`,
`blocked_on`. **The code is the source of truth; duplicating it here would just
create drift.** So:

- **Materials** → a *script-generated* snapshot (below). Never hand-listed.
- **Finished goods & abstract resources** → not in the registry. This doc owns them.

### Material snapshot — GENERATED, never hand-edit

Regenerate (from repo root):

```bash
python -m world.material_registry --ledger
```

Snapshot @ Rev 1 (`feature/recipe-knowledge`) — paste of the command's output,
trimmed to the load-bearing groups (the script prints all four + every
`blocked_on`):

```
EXISTS  (7) — committed & live: cloth, feather, fiber, gourd, raw_hide, tusk, twine
DATA    (17) — ratified, buildable now, uncommitted (17 keys; see script)
BLOCKED (12) — needs an unbuilt system:
  bronze/copper/iron/tin  [blocked_on: smelting (furnace + process)]
  charcoal                [blocked_on: kiln/charcoal-burning process]
  glass                   [blocked_on: glassblowing (furnace + process)]
  pottery                 [blocked_on: kiln (station + firing)]
  steel                   [blocked_on: steelmaking (refining process)]
  planks                  [blocked_on: carpentry (saw + tools)]
  silk/wool/yarn          [blocked_on: sericulture / husbandry / spinning]
DECISION (1): leather     [blocked_on: DECISION #2 (tanning model)]
ORPHANS  (3): feather, raw_hide, tusk   ← EXISTS but no sink
```

Every `blocked_on` maps to a system in **`docs/crafting/PolishedWorld_System_Backlog.md`**
(the 14-system build order). That doc is the "what's missing, in what order" for
the material layer; this snapshot is its live status readout.

---

## Finished-goods ledger

Items spawned as end products. The registry does not track these — this does.

| Item / class | Source (creation site) | Sink | Status |
|---|---|---|---|
| Crafted items (garments, tools, waterskin…) | `crafting_base.py::do_craft` → `spawn(*output_prototypes)` | disassemble → `target.delete()`; repair total-fail → `obj.delete()`; wear→break (lingers) | `[EXISTS]` |
| Food | forage / craft | eat → `consumption_commands.py::delete()` | `[EXISTS]` |
| Drink (charge-based) | craft (waterskin) | drink decrements charges → delete at 0 | `[EXISTS]` |
| Scroll | `inscribe` → `spawn("scroll")`, consumes 1 cloth | `learn` → `delete()` (one-shot read) | `[EXISTS]` |
| Book | scribe (Component G) | reusable — no delete sink *by design* (multi-read) | `[DATA]` |
| Corpse | death → `create_object` | harvest-then-delete + tickerless decay → `delete()` | `[EXISTS]` |

*The **goods** sink is wear, not any coin cost — `resources → craft → use → wear →
repair → destroyed` is the canonical lifecycle and the primary sink for goods
(Economic Philosophy, principle 3). Repair extends an item's life but never
removes the need for new production; that continuous demand is the point.*

### `[SINK BLOCKED]` — makeable (eventually) but no consumer yet

From `docs/crafting/PolishedWorld_Crafting_Decomposition.md` (Example A). These
aren't orphans (materials); they're *finished goods* whose use-system is unbuilt:

| Finished good | Needs (to have a use) |
|---|---|
| Sword / weapons | combat/wielding system (Stage 5) |
| Armour (mail, plate) | combat + armour-layering resolve |
| Lantern, glass bottle | light system + glassblowing |

*Don't build these until their consumer exists — the decomposition surfaces the
block so effort isn't spent making dead items.*

---

## Abstract-resource ledger

Non-item flows — where long-term balance actually lives.

| Resource | Source | Sink | Status |
|---|---|---|---|
| Recipe knowledge | learn (scroll/book/teach); profession grants at chargen | none — permanent, nothing un-learns | `[EXISTS]` (sink intentionally absent) |
| Survival gauges (hunger/thirst/fatigue) | restore: eat / drink / rest | deplete: `survival_ticker` (global) | `[EXISTS]` |
| Buffs (Starving, Dehydrated, thermal, tool bonus) | condition onset / tool use | condition clear / duration | `[EXISTS]` |
| Skill (`craft` etc.) | `improve_skill_on_use` (on use) | none — permanent | `[EXISTS]` |
| **Currency (gold/silver/copper)** | `MINT_SOURCES` = `crypto_exchange` (GameGold→gold 1:1) + `admin_correction` (repairs the exchange path; ledgered and audited identically, never a grant). Faucet **transfers out of the Treasury**, never mints | `BURN_REASONS`, the same pair. Gold never decays. **Death-drop is Stage 5** — Stage 4 keeps the wallet through death (S4-3) | `[EXISTS]` — wallet, ledger, audit shipped Stage 4; the exchange itself is `[BLOCKED: Stage 8]` |
| GameGold | PoS block reward (blackcoin-more fork) | exchange → in-game gold | `[BLOCKED: Stage 8]` |

---

## Pillar-1 audit (the payoff)

The per-batch version of this already exists — the integrity checklist in
`docs/crafting/deer_batch_gold_standard.md` ("every part has a sink; every
`consumable_tags` has a source"). This section is the *whole-economy* roll-up.

- **Orphans (source, no sink):** `feather`, `raw_hide`, `tusk` (from
  `orphan_materials()`). `raw_hide` is flagged **KRITISK** in the backlog — it
  clears when tanning lands (DECISION #2). `feather`/`tusk` need a consuming
  recipe or a cut.
- **`[SINK BLOCKED]` finished goods:** swords/armour/lanterns — gated on Stage 5
  combat + glassblowing. Tracked, not built.
- **Fountains (sink, no source):** none in built systems.
- **Currency is a pegged, single-mint currency board — its source/sink is owned
  by the economy docs, not this ledger** (delegated the same way materials are
  delegated to the registry). The canonical treatment lives in
  `docs/PolishedWorld_Economic_Philosophy.md` (principles 4–5) and
  `docs/PolishedWorld_GameGold_Economy.md` (`CurrencyHandler.add`, faucet).
  The operative facts this row defers to:
  - **One mint point:** gold is created *only* at the crypto_exchange
    (GameGold→gold 1:1). No monster-drop / quest / NPC gold. The faucet is
    **not** a second mint — it *transfers out of the Treasury* (S4-1), which is
    why an empty Treasury makes the faucet dry rather than inflationary. This is
    what keeps every gold auditable back to a real exchange.
    ⚠️ `MINT_SOURCES` also contains **`admin_correction`**, which repairs the
    exchange path when a settlement goes wrong: the same door used to fix the
    door, ledgered and audited identically, and never a grant mechanism.
    `BURN_REASONS` carries the same pair. Recording it here so this ledger does
    not claim a tighter guarantee than the code provides.
  - **Circulation is not a sink.** Repairs, rent, station fees, food — these
    *move* gold (they're another player's income), they don't destroy it. Do not
    file them as sinks (my earlier draft did — corrected). **Barter settlement
    belongs in this category too**: a trade that swaps a sword for five silver
    is a transfer, which is exactly why it is deliberately *not* ledgered
    (S4-4). The ledger holds mint and burn only; what proves nothing was created
    is the invariant `Σ(wallets) + Treasury == Σ(mint) − Σ(burn)`, not a
    transaction history.
  - **One true exit only:** exchanged back to GameGold — the single intentional
    burn, matching the single mint point. **Gold never decays.** Unlike goods,
    currency does not weather away.
    ⚠️ **The death-drop is intent, not current behaviour.** Stage 4 keeps the
    wallet through death (**S4-3**); gold dropping to the room needs `CoinPile`,
    which is Stage 5. When it lands it arrives as a **potential second sink that
    must not become one** — `PlayerCorpse` deletes all contents at expiry, so a
    `CoinPile` inside a rotting corpse would be an unlogged burn and would break
    the invariant above. Tracked in `docs/BACKLOG.md`; flagged here because a
    silent second sink is precisely the class of bug this ledger exists to catch.
  - The real inflation lever is the chain's emission (1 coin/block), *outside* the
    game by design. There is no in-game knob, and that is correct.
