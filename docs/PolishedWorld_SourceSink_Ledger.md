# PolishedWorld — Source / Sink Ledger

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
| **Currency (gold/silver/copper)** | mint at **one point only**: crypto_exchange (GameGold→gold 1:1). Faucet redistributes exchange-minted gold (pays copper), never mints | **one true exit only:** exchange back to GameGold. Gold never decays — on death it drops to the room and waits until looted (transfer, not a sink) | `[BLOCKED: Stage 4]` |
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
    (GameGold→gold 1:1). No monster-drop / quest / NPC / admin gold. The faucet
    is **not** a second mint — it redistributes exchange-minted gold (paid in
    copper), so nothing is created from nothing. This is what keeps every gold
    auditable back to a real exchange.
  - **Circulation is not a sink.** Repairs, rent, station fees, food — these
    *move* gold (they're another player's income), they don't destroy it. Do not
    file them as sinks (my earlier draft did — corrected).
  - **One true exit only:** exchanged back to GameGold — the single burn, matching
    the single mint point. **Gold never decays.** Unlike goods, currency does not
    weather away; when a character dies their gold drops to the room with their
    belongings and simply waits there until another player loots it. Carrying
    wealth still holds real risk (you can lose it to whoever finds your remains)
    and there is room for "treasure hunting" — but that gold is *transferred*,
    never destroyed. Total gold in existence changes only at the exchange.
  - The real inflation lever is the chain's emission (1 coin/block), *outside* the
    game by design. There is no in-game knob, and that is correct.
