# PolishedWorld — Crafting Decomposition (worked examples)

Two target items broken down **top-down** (item → raw materials) as dependency
trees, each node annotated with status. This is Functional Decomposition applied
to the crafting tree instead of to features.

**The principle these examples demonstrate:** *decompose top-down, generate
bottom-up.* You design by starting at the item you want (which is why this can
never produce orphan materials — every node exists because something above it
needs it). You then generate/commit leaf-to-root (raw → intermediate → finished),
so every reference resolves at every commit. The two directions are different
phases, and the **material registry is the hinge** between them: decomposition
*fills* the registry; generation *draws* from it.

## Status legend

- `[EXISTS]` — prototype/recipe already in the repo, live.
- `[DATA]` — buildable now: pure data (prototype/recipe/node), no new code.
- `[NEW MATERIAL]` — a new shared material; must be registered first.
- `[DECISION #n]` — gated on an open decision in `material_registry.py`.
- `[BLOCKED: <system>]` — needs a typeclass/station/process that does not exist.
- `[SINK BLOCKED]` — the finished item has no *use* yet (its consumer is unbuilt).

Tools are shown as `(tool: …)`. Per AGENTS.md, *required* tools/stations are hard
gates; *convenience* tools are optional (improvised at −20).

---

## Example A — Sword  (the "system backlog" tree)

A sword is the deep case. Its tree is mostly **blocked on whole systems**, so
decomposing it is most valuable as *planning*: it enumerates, in dependency
order, the subsystems you must build before any metal content can be committed.

```
sword  [SINK BLOCKED: needs a combat/wielding system to be used]
└─ assembly recipe  [BLOCKED: parts below don't exist]
   ├─ sword blade   [BLOCKED: smithing system]
   │  └─ steel / refined iron  [BLOCKED: smelting + refining]
   │     ├─ pig iron / bloom   [BLOCKED: smelting system]
   │     │  ├─ iron ore        [DATA: an ore ResourceNode — bog/surface iron,
   │     │  │                   hand-gathered early; mining skill/pickaxe later]
   │     │  └─ fuel (charcoal)  [BLOCKED: charcoal-burning process/kiln]
   │     │     └─ wood          [NEW MATERIAL] ← oak tree node [DATA]
   │     └─ flux (ash, sand)   [DATA: gatherable, only meaningful once smelting exists]
   │     ·  (tool: furnace/bloomery [BLOCKED: station typeclass + heat + smelt process])
   │     ·  (tool: crucible      [BLOCKED: station] — for the steel-refining step)
   ├─ sword guard   [BLOCKED: smithing] ← steel + (anvil, hammer, forge)
   ├─ sword pommel  [BLOCKED: smithing] ← steel + (anvil, hammer, forge)
   ├─ sword handle  [DATA*] ← cleaned oak wood + (tool: knife [EXISTS])
   │  └─ cleaned oak wood  [NEW MATERIAL] ← oak wood + (tool: knife)
   │       (*buildable once the "wood" material + oak node exist)
   └─ grip wrap (leather)  [see Example B — buildable soon]
        (tool: anvil, hammer, forge [BLOCKED: smithing system])
```

### System backlog this reveals (in build order)

1. **Wood gathering** — oak tree `ResourceNode` + a `wood` material (+ `oak_bark`,
   `cleaned_oak_wood` derivatives). `[DATA]` — buildable now.
2. **Ore gathering** — iron ore `ResourceNode` (early = surface/bog iron, hand-
   gathered). `[DATA]` now; a mining skill + pickaxe is a later refinement
   (pickaxe is itself metal → bootstrap, so primitive ore must be hand-gatherable).
3. **Fuel** — charcoal from wood via a burning **process/kiln** `[BLOCKED]`, or a
   coal `ResourceNode` `[DATA]` as a shortcut.
4. **Smelting system** — a furnace/bloomery **station typeclass** + a smelting
   process (heat + time) turning ore + fuel → bloom/pig iron. **This is the first
   real blocker and the keystone of the whole metal branch.**
5. **Smithing system** — forge + anvil + hammer (stations/required tools) + a
   smithing process + heat, turning metal → blade/guard/pommel.
6. **Steel refinement** (optional depth) — crucible + flux (ash/sand).
7. **Tanning** — the leather sub-chain for the grip (see Example B; soft craft).
8. **Assembly recipe** — sword from its parts (trivial once parts exist).
9. **The sword's own SINK** — a combat/wielding system. Until that exists, even a
   finished sword has no use. *The decomposition surfaces that the item is blocked
   at both ends.*

**Generation order (once the systems exist):** wood/ore/fuel materials → smelting
→ pig iron → steel → blade/guard/pommel → handle/grip → assembly. Nothing here is
committable today beyond the `[DATA]` leaves (wood, ore, flux nodes).

---

## Example B — Leather boots  (the "almost all buildable" tree)

The contrast case. Leather boots need **no new systems** — only a couple of new
data nodes and **one design decision** (how tanning works). Decomposition pins
the exact unblock point.

```
leather boots  [recipe DORMANT; LEATHER_BOOTS prototype EXISTS]
└─ leather boots recipe  ← leather + (tool: knife [EXISTS] cut; needle [EXISTS] stitch, optional)
   └─ leather  [NEW MATERIAL — registered, status PLANNED]
      └─ tanning recipe  [DATA, pending DECISION #2: soft hand-craft vs vat/station]
         ├─ raw_hide   [EXISTS] ← boar / deer harvest
         ├─ oak bark (tannin)  [NEW MATERIAL] ← oak wood + (tool: knife)
         │  └─ oak wood  [NEW MATERIAL] ← oak tree [NEW ResourceNode, DATA]
         └─ water  [DECISION #6: a "water" material, or draw from a water source?]
              (tool: vessel/cauldron — optional, so tanning stays a soft craft now)
```

This structure matches Evennia's own example (`example_recipes.py`): leather =
rawhide + oak bark + water + a vessel; oak bark = oak wood + knife. The only thing
we change is making the vessel *optional* so tanning is hand-doable now, rather
than a hard station gate.

### What it takes to unblock (all near-term, mostly data)

- **DECISION #2** — accept tanning as a soft hand-craft (cold bark-soak, optional
  vessel). *Recommended.* This is the single gate; resolving it turns the whole
  chain green.
- **DECISION #6** — does tanning consume a `water` material, or just require being
  near a water source? (Affects whether `water` is registered.)
- New data: `wood` material + oak tree `ResourceNode`; `oak_bark` material; the
  `leather` prototype; the tanning recipe; then flip `LeatherBootsRecipe` from
  dormant to active. All pure prototypes/recipes — opencode territory.

### Generation order (leaf-to-root, committable today after the decisions)

1. oak tree `ResourceNode` + `wood` material  `[DATA]`
2. `oak_bark` material (oak wood + knife)  `[DATA]`
3. `leather` prototype + tanning recipe (raw_hide + oak_bark + water)  `[DATA]`
4. activate the leather boots recipe (leather → leather_boots)  `[DATA]`

Each step references only things committed in an earlier step — no dangling refs.
And **this also clears the `raw_hide` orphan**, because step 3 finally gives
`raw_hide` a sink.

---

## Shared nodes — why decompose a *set*, not one item

`oak wood` appears in **both** trees (sword handle *and* the bark for boot
leather). `leather` appears in both (grip wrap *and* boots). Had we decomposed the
sword alone, we'd have modelled oak wood as a sword-only node; decomposing a small
*set* of targets (sword + boots + a bag + an axe) surfaces the shared intermediates
and stations up front, so the registry reserves them once instead of fragmenting
them per item. That is the argument for taking a handful of target items into the
next decomposition pass together.

## How this feeds the pipeline

1. Decompositions like these **populate the registry** with the materials and
   intermediates each target needs, and reserve their canonical names.
2. The `[BLOCKED: …]` nodes become the **system roadmap** (smelting, smithing,
   kiln) — Claude/Adam build those.
3. The `[DATA]` leaves and chains become **generation batches** for OpenCode, run
   leaf-to-root in the order above.

**Immediate path:** leather boots is one decision (#2) away from being a fully
generable chain — and generating it clears the `raw_hide` orphan. The sword stays
a planning artifact until the smelting/smithing systems are built.
