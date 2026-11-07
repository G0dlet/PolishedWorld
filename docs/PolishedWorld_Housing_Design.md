# PolishedWorld — Housing & Building Design Notes

> **Rev 1 · 2026-11-07** — first version, docs only, with roadmap Rev 47 and README Rev 25. Written from a design chat, the second in a series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`: Adam wants players to build their own houses and perhaps open shops in them (roadmap Rev 42), and asked for the most immersive version of that to be kept for the day housing is taken up. **Nothing here is locked.** Every numbered item is a proposal (BP…) or an open question (BQ…); the housing decomposition locks or rejects each one. Prior art was read on 2026-11-07; code seams were read against `main` at `9f3c32f` (Evennia 6.1.0).
> **Canonical:** `docs/PolishedWorld_Housing_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** roadmap, *Parallel / opportunistic backlog*, *Persistent storage / housing / settlements*, and its 2026-11-05 note (Rev 42). The shop half has its own home in `docs/BACKLOG.md` (*Currency*, *Player shops and market stalls*); §10 is written against that entry and does not replace it.
**When to read:** at the start of a housing decomposition, at the Stage 5 design session (break-in, §9), at the Stage 6 design session (where plots stand, §6), and when *Player shops and market stalls* is triggered.
**Departs from the roadmap note in one place:** the note says housing waits on Stage 6 because *"where a house may stand is its question"*. BP4 proposes that a house is the state of an authored plot rather than a room created in play, which would make Stage 6 decide *where plots are* but not *how houses work*. That is a proposal, flagged here so it is not read as a decision.

---

## 1. The idea in one paragraph

A house is not bought; it is raised. Somebody draws up the plan, many hands carry the timber, clay and stone to the site, and the builder works the frame up stage by stage — foundation, frame, walls, roof, door — each stage a run of Engineering rolls that adds to the project the way *Arms of Legend* says building works. When the roof goes on, the room under it changes: the wind stops, the weather falls silent, rest comes easier, and the owner has a place in the world that is theirs. Then the world starts taking it back. Rain wears the roof, frost the walls, time the door; every repair is timber and skill that another player may sell. A neglected house does not vanish at a moment someone can camp — it leaks, then it is cold inside, then its door is weak enough to force. The house is the largest sink the game can have, and every unit of it is a good some player made or carried.

---

## 2. Prior art

### 2.1 Ultima Online — the warning

Sources: the community wikis' *House Decay* pages (`uoforever.com/wiki/index.php/House_Decay`, `uoguide.com/IDOC`), UO's Publish 108 notes (`uo.com`), and Massively OP's report on Publish 122 (2026-02-11). Paraphrased:

- A placed house has to be refreshed by its owner or it walks down a ladder of decay stages — *Like New* through *Greatly Worn* — to **In Danger Of Collapsing** (IDOC), and then falls.
- When it fell, everything inside dropped to the ground and the plot became free to whoever placed a house on it first. Players camped IDOC houses for hours for the loot and, above all, for the plot; some made it their whole game.
- UO spent two decades patching that one moment: hiding the decay stage from everyone but the owner (Publish 108), lengthening and publicising the final stage, and on some shards a lottery for the contents. Publish 122 (February 2026) finally ended first-come plot claims after 28½ years, replacing them with a raffle — partly because players widely believed scripts were winning the placements.

**Worth taking:** decay as a ladder of visible states the owner can read and act on; upkeep that requires being there.
**Not for PolishedWorld:** the collapse *moment*. **The lesson (the series' "Achaea lesson"):** whatever single instant turns private property into free loot or a free plot becomes the thing players script and camp. PolishedWorld must never have such an instant — §8 makes decay gradual and §9 makes entry a skill act, so there is nothing to wait for and nothing a trigger can win.

### 2.2 Haven & Hearth — crime that leaves evidence

Sources: Ring of Brodgar wiki, *Personal Claim*, *Authority*, *Yeomanry*. Paraphrased:

- Claiming land needs a learned skill; the claim's upkeep grows with its size.
- Anyone may walk onto your claim, but a trespasser leaves a scent the owner can use to track them to their hearth; taking things leaves a theft scent. Crime is possible and costs evidence.
- Breaking a claim takes time that scales with the claim's power level; a village whose upkeep lapses below a threshold loses its protection, and only then can outsiders act there freely without leaving scents.

**Worth taking:** protection proportional to upkeep, not a binary lock; theft as a skill act that leaves a trace the victim can read; time-to-break that grows with investment.
**Not for PolishedWorld:** upkeep paid in experience points — PolishedWorld's upkeep should be goods (pillar 1), and skill is what Stage 4.5 made expensive, so it must not be the rent.

### 2.3 Avalon — shelves in someone else's shop

Source: Avalon's in-game help, *HELP SHELVES* (`avalon-rpg.com/help/pages/shelves`). Paraphrased:

- A shop owner can rent out shelves to other crafters. The owner sets a monthly rent and a percentage taken from each sale; the shelf-holder stocks and prices their own goods, which buyers see alongside the shop's.
- The shelf-holder settles the shelf's takings in person; the help advises doing so promptly, before burglars or highwaymen get to the coin. Owner and holder can both read a log of sales.

**Worth taking:** a shop that many crafters can sell through without the shop owner handing over the stockroom; a till that is coin *at a place* and has to be collected (§10); a sales log both parties read.
**Not for PolishedWorld:** nothing structural — no NPC sells anything in Avalon's shelf model.

### 2.4 Discworld MUD — secondary sources only

The L-Space wiki and TV Tropes describe a limited housing stock let through rental auctions, furnishable by the tenant, and commercial premises players bid for to run shops that trade while the owner is away. Not read from Discworld's own help, so only one point is taken: offline sales by a player who set the goods and the price are long-standing MUD practice — evidence for, not a decision of, *Player shops and market stalls* open question 1.

---

## 3. Design goals

- **BG1 — Raised, not bought.** No NPC sells a house, a plot deed, a plank or a nail. Every part is a good players made or carried.
- **BG2 — Many hands.** Delivery and labour are open to anyone the owner lets in, so a house is a reason for players to work for one another (haulage, carpentry, masonry as services).
- **BG3 — The world reads the house.** A roof is shelter in the systems that already exist — thermal regime, weather messages, rest — not a flag only the house reads.
- **BG4 — The world takes it back, slowly.** Upkeep is goods on the `condition` axis tools and garments already wear. Decay is a ladder the owner can read, never a moment others can camp (§2.1).
- **BG5 — No risk-free storage.** A locked house nobody can enter is the free version of *Bank / post office*. Private storage ships with a way in, not before (§9).
- **BG6 — No migration debt.** Nothing built in play becomes a room Stage 6 must preserve or a map module must know about (§6).
- **BG7 — Source and sink named together** (Economic Philosophy; `docs/PolishedWorld_SourceSink_Ledger.md`).
- **BG8 — Readable progress.** A site shows what stage it is at and what it still needs, in words, so a passer-by can see what to carry there.

---

## 4. Legend alignment

**Rules as written:**

- **Engineering (INT×2)** — Legend core: designing, building, repairing and sabotaging large mechanisms and constructs. A critical makes the project first rate and early; a fumble makes it unusable, costs double time and then it fails or collapses.
- **Mechanisms (DEX+INT)** — small mechanical devices, *"including traps and locks"*; picking a lock takes one minute to an hour by complexity (Legend core). *Arms of Legend* adds lock picks, and a clay-and-wax box that copies a key (+10 % to Mechanisms against that lock).
- **Craft / Engineering / Mechanisms overlap** — *Arms of Legend* (`docs/reference/arms_of_legend.md`, *Skills* under building and repairing): Craft for items with few moving parts, Engineering for large structures, Mechanisms for small items with moving parts; where two fit, use the higher, with −10 % to −60 % by how apt the skill is.
- **Task Rounds** — *Arms of Legend*, *Tasks*: a project is worked in Task Rounds; each roll adds **critical +50 %, success +25 %, failure 0 %, fumble −25 %**, and the work continues until **100 %** or time or budget runs out. A competent worker with no failures finishes in **four** rounds. Building a wooden or stone structure is an Engineering task whose round is *six months to several years* — a table of examples, not a rule.
- **Item quality** — same chapter: the final percentage is the quality. 100 is serviceable; 75 wears out 25 % faster (or loses a quarter of its HP), 50 half, 25 three quarters; 0 or less is unfinished; 125/150/175+ earn one to three Enhancements. A project that passes 100 % in four rounds or fewer may be refined for Enhancements.
- **Circumstance modifiers** — same chapter: no tools, impossible; improvised tools −40 %; poor tools −30 %; lacking a crucial / major / minor resource −30 / −20 / −10 %; good tools +20 %.
- **Inanimate objects** — Legend core: walls and doors have Armour Points and Hit Points; attacks on them hit automatically, and a door is broken with Brawn, Unarmed or a weapon. Wooden door 4 AP / 25 HP; reinforced 6 / 30; iron door 12 / 75; hut wall (2 m) 3 / 15; wooden fence (2 m) 4 / 5.

**Translation proposals:**

- **BP1 — `engineering` as a skill, Legend's own.** Not a custom skill: Engineering is in the core with base INT×2, so there is no `survival`-style collision to name around (contrast `hunting`, `typeclasses/characters.py:443–449`). Chargen's Points Build would price it like any Advanced skill; the core *Craftsman* career already lists Engineering among its choices. Whether the project's single generic `craft` skill (`typeclasses/characters.py:422`, base DEX+INT) may stand in at AoL's −10 to −60 for small structures (a lean-to, a hut) is **BQ1**.
- **BP2 — Task Rounds as written, as the project mechanic.** A building site holds a `progress` per stage; each work pass is one `skill_check(engineering, modifier)` (`world/skillcheck.py:58`, tiers `critical`/`success`/`failure`/`fumble`, lines 52–55) and adds +50/+25/0/−25. A stage completes at 100 %. This is the first use of AoL's Task Round model in the codebase — single-roll crafts stamp quality from one tier (`world/crafting_quality.py`) — and it is the model AoL itself gives for "building a wooden or stone structure".
- **BP3 — Quality from the total, onto the condition axis.** A stage's final percentage sets how fast that part wears (AoL's 75 → 25 % faster, as a wear multiplier on `apply_wear`) and, for a door, its HP (Legend's table as the 100 % value). Enhancements from refining (125+) are the hook for later rewards: a tighter roof that wears slower, a stouter door. Modifiers are roll terms (lesson candidate (p), launch-minimum session 4): the AoL tool modifiers, missing-material penalties, the overload penalty via `Character.physical_modifier()` (`typeclasses/characters.py:603`).
- Fumble: AoL's −25 % to progress, plus the core's *"collapses"* kept for a **stage**, never the house: a fumbled roof pass can bring that stage's progress down to zero and waste the materials of that pass (BQ6).

---

## 5. The loop

Proposed phases (BP5). Every work pass is a beat on the existing timed-action slot (`world/timed_actions.py`, `start()` at line 107; moving away interrupts it through `at_pre_move`, as every timed action does).

1. **Plan.** A house is built from a *plan* — knowledge, not an item bought: a recipe-like entry (`requires_knowledge`, the same partition `world/knowledge.py` already runs, with scrolls and teaching as sources). Plans ladder: lean-to, wattle-and-daub hut, timber cottage, stone house, shop front.
2. **Lay out the site.** On a free plot (§6) the planner `site <plan>`. The plot gains a *building site* fixture (`get:false()`, the `ResourceNode` precedent, `typeclasses/resources.py:61`) that lists the plan's stages and each stage's bill of materials.
3. **Deliver.** Anyone the site admits (BQ4) runs `deliver <n> <material> to site`. Materials move into the site's stock and stop being items — numbers on the fixture, so the room does not fill with logs. Delivery is where weight matters: a stone house is many trips (WD2's ceiling prices distance in trips).
4. **Work.** `build` starts a pass: one Task Round of `craft_duration`-like length, consuming that pass's share of the stage's materials at completion (Epic A's D7: nothing is consumed before the beat that consumes it). The roll adds to the stage's progress. Several builders can work the same site at once, each on their own slot — a crew finishes sooner, as AoL's ship-repair crews do.
5. **Finish a stage.** At 100 % the stage is done and the plot's description changes (§7). The next stage opens. A stage with no materials left cannot be worked; the site says what it lacks.
6. **Raise the roof.** The roof stage is what makes the plot sheltered (BP9). The door stage is what lets the owner close it (§9).

What it reads like (illustrative, not a spec):

```
> look
A cleared plot at the edge of the green. Four corner posts stand in a
trench of packed stone; the frame of a small cottage is half raised.
A building site: frame (about half done). Still wanted for the frame:
6 wood, 4 twine.
> deliver 6 wood to site
You stack six lengths of wood by the frame.
> build
You set to work on the frame...
You notch and peg two more rafters into place. The frame is nearly done.
```

**BP6 — The site shows need, not numbers of progress.** Progress is shown in words (*begun, about half, nearly done*); material shortfalls are shown as counts, because a carrier needs to know how many trips to make (BG8).

---

## 6. The plot — where a house stands

**BP4 — A plot is an authored room, and a house is that room's state.** No room is created in play. Plots are rooms placed the same way every other room in the alpha is: by versioned seed (`world/seed_data.py` `ROOMS`, line 79; `world/seeding.py:149` already writes `is_indoor` per room) now, by a map module once Stage 6 lands. A plot carries a `plot` tag and an empty state; building writes the house's state onto it.

Why: `xyzgrid spawn` deletes every room whose coordinate is no longer on the map and rewrites every attribute its prototype defines, while keeping attributes the prototype does not define (`batch_update_objects_with_prototype(..., exact=False)`; `docs/PolishedWorld_Evennia_Reference.md` §14.2). So a house that is a *new room* is exactly what Stage 6 would delete, and a house written into `desc` is what the next spawn would overwrite. A house kept in its own attributes — `db.structure` (stages, progress, condition per part, quality), never `desc` — survives a respawn of its plot, and the plot's prototype keeps owning the bare ground. The house's text is composed on display from the plot's base description plus the structure's state.

**Consequences:**

- **Plot scarcity is authored.** The starter settlement has as many plots as the seed gives it; more plots are a content decision, not a land rush. Ownership rules — one plot per character, per account, claim by first site, lapse — are **BQ2**.
- **Multi-room houses** are adjoining authored plots (a front room and a back room on a plan that spans two), or a later Stage 6 virtual node; not a `dig` in play.
- **Wilderness:** no houses on recycled wilderness shells. Room recycling keeps Tags and Attributes (Evennia Reference §14.5), so a structure there would leak to the next coordinate. Building outside authored areas waits on Stage 6's coordinate-data answer, as `ResourceNode` does (roadmap Stage 6, open question 2) — **BQ3**.

---

## 7. The house as a thing

**BP7 — Parts, each on the condition axis.** A finished house has parts — foundation, walls, roof, door (and later hearth, shutters, a shop counter) — each with its own `condition` 0–100 and quality, as `DurableObject` gives one item (`typeclasses/durable.py:41`, `apply_wear` at 43). They are values in `db.structure`, not objects, so a house is one room's attributes, not ten objects.

**BP8 — A shelter ladder that starts with what exists.**

| Rung | Shelter | Built from (existing materials) | What it gives |
|---|---|---|---|
| 0 | a pitched **tent** | the `tent` item (`world/prototypes.py:872–884`) | rest bonus; today the tent has *"SINK: none … shelter, unscheduled"* (line 881) — this rung is its use, and pitching and striking wear it |
| 1 | a **lean-to** | stick, wood, plant fibre | rest bonus, no shelter from cold |
| 2 | a **wattle-and-daub hut** | wood posts, stick wattle, clay daub, plant-fibre thatch | roof → sheltered (BP9); a door you can bar from inside |
| 3 | a **timber cottage** | wood (logs, worked with the stone axe), stone footing, thatch | sheltered; a door that takes a lock (§9); a hearth slot |
| 4 | a **stone house** | stone, clay mortar, timber roof | sheltered; slower wear; the stoutest door |
| — | a **shop front** | a cottage or house plus a counter | the shop half (§10) |

Rungs 1–3 need no material the alpha lacks: `stick`, `wood`, `stone`, `clay`, `plant_fiber`, `twine` and the `stone_axe` are all prototypes on `main`. Nails, hinges and locks wait on metallurgy, which opens with tools (roadmap Rev 45); until then doors hang on leather or twine and close with a wooden bar.

**BP9 — A roof is shelter in the systems that already exist.** While the roof part is above a threshold, the plot reads as indoors: `thermal_regime()` returns temperate for `is_indoor` (`world/thermal.py:68`), and weather transitions are not heard indoors (`world/weather.py:84`). Rather than a second flag, the proposal is that a plot's `is_indoor` is *derived* from its roof (BQ5: a property on the plot room over the stored attribute, or the stored attribute written on stage completion and on decay). A leaking roof turns it off again (§8).

**BP10 — Rest at home.** A rest under a sound roof recovers more per tick. The seam exists: `_rest_tick` adds `char.rest_recovery` per `rest_interval` (`typeclasses/characters.py:1693–1736`, the add at 1727); a shelter term read from the room joins it. A tent or lean-to gives a smaller term; one's own bed (furniture, later) the full one.

**BP11 — Logging out at home.** Characters stay in the world as statues when they log out (`at_post_unpuppet`, `typeclasses/characters.py:472`). Logging out inside one's own closed house is the natural "inn": nobody walks past your statue. It is privacy, not safety, until Stage 5 makes the difference matter.

**Furniture** — beds, tables, chests, shelves, racks — is ordinary crafted items (woodwork discipline), set into the room. They give the room's text its life (*a narrow bed under the eaves*) and some give terms (bed → rest; workbench → a craft station once stations exist). Chests are storage, and storage is §9's question.

---

## 8. Upkeep and decay

**BP12 — Lazy weather wear on the parts.** The house stores `checked_at` and wears its parts on read, from elapsed game time and the weather the room has seen — no ticker, the project's lazy-evaluation rule. The roof wears most in rain and snow; walls in frost (winter); the door with use. Quality scales the rate (BP3). Exposure to weather is the world reading the house (BG3) and makes the BACKLOG's weather-dependent wear concrete.

**BP13 — A ladder the owner can read, with no last moment.** Each part shows a state in words (*sound, weathered, leaking, failing*). As the roof fails, the room stops being sheltered (BP9); as the walls fail, the house gets colder and the door's HP falls with them. Nothing drops, nothing is freed, nothing is announced — a neglected house becomes cold, then easy to enter, over game weeks (§2.1's lesson). What finally happens to a house nobody has touched for a long time — reclaimed plot, a ruin, contents — is **BQ7**, and whatever it is must be a slow process with no instant, and coin found in it goes to the Treasury per the death policy (roadmap Rev 26).

**BP14 — Repair is goods plus skill.** Repairing a part is a short Task Round pass that consumes that part's materials (thatch for a roof, clay for daub) and restores condition by tier, the shape `CmdRepair` already uses for garments (`commands/repair_commands.py:149`, `_resolved_condition` at 200) — which today repairs garments only. **No coin rent.** A coin fee would be a transfer to the Treasury (coin's only permanent exit is exchange, Economic Philosophy Rev 2), which funds the faucet and adds nothing for crafters; materials are what pillar 1 needs a sink for.

---

## 9. Security and storage

The rule is BG5: a place to keep goods that nobody can enter is the risk-free storage `docs/BACKLOG.md` *Bank / post office* exists to refuse, and the same rule binds the shop's till (*Player shops*, open question 4).

**BP15 — Storage arrives with a way in, in layers.**

1. **Slice 1 — shelter, rest, workshop; no private storage.** A hut or cottage with no lock. Things left in it are left in a room anyone can walk into, which is the honest state of an unlocked house. A door that can be **barred from inside** gives privacy while the owner is there.
2. **Lock and key — when entry without the key exists.** A lock is a Mechanisms-made item (metal, after metallurgy's tools); its key is an item, and the door's traverse lock is `holds(<key>)` — Evennia's lockfunc exists at `v6.1.0` (`evennia/locks/lockfuncs.py:577`). Keys can be copied (AoL's clay-and-wax box), lent and lost: trust between players stays part of the economy, as on the *Wanted board*.
3. **Ways in.** *Picking* the lock: Mechanisms against the lock's quality, one minute to an hour (Legend), with picks. *Forcing* the door: Brawn or a weapon against the door's AP and HP (Legend's table, scaled by quality and condition — BP13 makes a neglected door weaker). Forcing needs Stage 5's damage rules; picking does not obviously need combat — **BQ8** asks whether picking can come first.
4. **Every way in leaves a trace.** A forced door shows it; a picked lock is scratched; the owner reads who passed if their tracking is good enough (Haven & Hearth's scents, §2.2; a natural tie to the hunting immersion design's tracks and signs).

**Containers in a house** follow the weight rules: ENC capacity, no nesting (`typeclasses/containers.py`, WD5). A chest is a container that stays put (`get:false()` once placed, BQ9) and is as safe as the door in front of it.

---

## 10. Shops

Written against *Player shops and market stalls* in `docs/BACKLOG.md`, whose five open questions stay that entry's to decide.

- **BP16 — Avalon's shelves.** A shop front is a house stage with a counter. The owner may rent shelves to other crafters at a rent and a share of sales they set (§2.3). A shelf is a container whose items carry the holder's price; a buyer present in the room buys with `pay`-style atomicity (the entry's question 3: one call, no `yield`, so two buyers of the last item cannot both succeed).
- **The till is coin at a place** and so waits for Stage 5's `CoinPile` (the entry's question 2); the shelf-holder settles it in person, which is exactly the risk Avalon's help warns about and the reason it cannot exist before break-in does (§9).
- **The rented market stall** stays the smallest form, needing no house and no plot; this document adds only that a shop front is the stall's grown-up form on the same item and till model.

---

## 11. Economy

**Sources (all player-made):** building materials (`wood`, `stick`, `stone`, `clay`, `plant_fiber` as thatch, `twine`; later worked timber, planks, shingles, mortar), doors, locks and keys, furniture, plans (knowledge, sourced by scroll, teaching and profession grants, as every gated recipe now must have — `tests/test_recipe_sources.py`).

**Sinks:**
- materials delivered into a site are consumed by work passes — the largest single sink in the game;
- upkeep consumes materials for the life of the house (BP14);
- tents, doors and locks wear on use;
- fumbles waste a pass's materials (BP2, BQ6);
- furniture wears slowly.

**Services the house creates (BG2):** haulage (weight makes it real), labour on someone else's site, repairs, lockmaking, shelf rent.

**Coin:** no coin sink is proposed. Coin found in an abandoned house goes to the Treasury, never deleted (roadmap Rev 26).

**Logging:** delivery and building are economic events. Whether a delivery is a `consume`, a building pass a `craft` with a field, or both are new kinds — the report keeps a pinned copy of `KINDS` (`world/activity_log.py:60`) — is **BQ10**.

**Ledger:** every new item gets its source and sink row in the same commit.

---

## 12. Multiplayer and server load

- **Per-character slots.** Each builder occupies their own `ndb.timed_action`; nothing ticks globally. Five builders on one site are five short `delay` chains, dead on `@reload` (Epic A).
- **Shared site stock.** Delivery and a pass's consumption are read-modify-writes on the site fixture's attributes and need the serialised pattern `ResourceNode.harvest()` documents (`typeclasses/resources.py:105`): two builders finishing passes in the same instant must not both consume the last 2 wood. A pass checks and takes its materials at completion in one step, and a pass that finds them gone ends with a message and no roll.
- **Progress writes** are additive per pass; the same serialised write covers them.
- **Lazy decay.** One timestamp per house, worn on read. 50 houses cost nothing until someone looks at one.
- **Message volume.** Pass lines go to the builder; the room hears a stage completing — one line per stage.
- **Object count.** A house is attributes on its plot room, materials are numbers on the site, parts are values: a finished house adds no objects beyond its furniture and its key.

---

## 13. Immersion extras

- **BP17 — The house changes the room's text as it rises.** Each finished stage adds its sentence to the plot's description (*corner posts in a trench of packed stone* → *a frame of pegged rafters* → *daubed walls under new thatch*), and each part's wear changes its sentence again (*the thatch has thinned over the door*). The room states machinery of `ExtendedRoom` (`typeclasses/rooms.py:198`) already varies text by season and weather; a roof in snow can read differently from a roof in rain.
- **Raising day.** A stage finished with three or more builders working it within the same game hour could give each a small mood or rest bonus — the barn-raising. A detail for the decomposition, not a system.
- **A sign.** The owner names the house; the name shows in the room title (*Adam's cottage, by the green*).
- **Smoke from the chimney** once hearths exist: the room *outside* a house with a lit hearth says so — the world shows who is home without a list.
- **Records for the gazette.** The first stone house, the longest-kept roof (BACKLOG *In-world gazette*).

---

## 14. Layers — a suggested order

1. **Slice 1 (the smallest real thing):** `engineering` skill; plots as authored rooms in the starter settlement; the site fixture with stages and bills of materials; `deliver` and `build` on Task Rounds; rungs 0–2 (tent pitched, lean-to, hut) from existing materials; derived shelter (BP9); rest at home (BP10); text that changes with stages. **No locks and no private storage.** No new raw materials.
2. **Slice 2:** lazy weather wear and repair (BP12–BP14); the cottage; furniture; plans as scrolls; ownership lapse (BQ2, BQ7).
3. **Slice 3, after metallurgy's tools:** locks and keys, barred and locked doors, chests; picking (if BQ8 allows it before Stage 5); traces.
4. **Slice 4, after Stage 5:** forcing doors; the shop front, shelves and till with `CoinPile`.
5. **Slice 5, after Stage 6:** plots outside the starter settlement; houses in grid areas as map nodes with structure attributes.

**Prerequisites:** none for slice 1 beyond the settlement having authored plots. Metallurgy's tools for slice 3. Stage 5 for forcing doors and for `CoinPile` (slice 4). Stage 6 for plots outside authored areas. **Not prerequisites:** the webclient (the OOB `room` snapshot can carry a house's state later), food professions, the economy milestone (housing is a sink; the shop half's trigger stays its own).

---

## 15. Seams in today's code (read at `9f3c32f`)

| Need | Seam | Where |
|---|---|---|
| Timed, interruptible work passes | `start(char, key, seconds, callback, …)`; `claim()` on completion | `world/timed_actions.py:107`, `:198` |
| Interrupt on move | the single `interrupt()` branch in `at_pre_move` | `typeclasses/characters.py` |
| d100 test, tiers | `skill_check(skill_value, modifier)` → `critical`/`success`/`failure`/`fumble` | `world/skillcheck.py:52–58` |
| Physical penalty | `Character.physical_modifier()` (overload) | `typeclasses/characters.py:603` |
| Fixture, serialised shared stock | `get:false()`; `harvest()`'s read-modify-write | `typeclasses/resources.py:61`, `:105` |
| Condition axis | `DurableObject.condition`, `apply_wear`, `condition_line` | `typeclasses/durable.py:41–96` |
| Repair by tier (garments today) | `CmdRepair._resolved_condition` | `commands/repair_commands.py:200` |
| Shelter in thermal | `thermal_regime()` → temperate for `is_indoor` | `world/thermal.py:68` |
| Weather silent indoors | `is_indoor` check in the weather broadcast | `world/weather.py:84` |
| Rest recovery | `_rest_tick`, `rest_recovery`, `rest_interval` | `typeclasses/characters.py:1181`, `:1693–1736` |
| Statue logout | `at_post_unpuppet` | `typeclasses/characters.py:472` |
| Authored rooms | `seed_data.ROOMS`, `is_indoor` written per room | `world/seed_data.py:79`, `world/seeding.py:149` |
| Room text by season/weather | `room_states` | `typeclasses/rooms.py:198` |
| Containers by ENC, no nesting | `Container.at_pre_put_in` | `typeclasses/containers.py:44` |
| Key-locked door | `holds()` lockfunc | Evennia `v6.1.0`, `evennia/locks/lockfuncs.py:577` |
| Grid respawn rules | `spawn_nodes()` deletes off-map rooms; `exact=False` keeps undefined attributes | Evennia Reference §14.2 |
| Existing materials | `wood`, `stick`, `stone`, `clay`, `plant_fiber`, `twine`, `stone_axe`, `tent` | `world/prototypes.py` |
| Knowledge-gated plans | `requires_knowledge`; every gated recipe has a source (test) | `world/knowledge.py`, `tests/test_recipe_sources.py` |
| Economic events | `activity_log.record(kind, actor, **fields)`, ten `KINDS` | `world/activity_log.py:60` |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 16. Open questions

- **BQ1** — `engineering` only, or may `craft` stand in for small structures at AoL's −10 to −60? And does chargen's craftsman-like profession grant Engineering?
- **BQ2** — Plot ownership: one per character or per account; claimed by laying out a site or granted by staff; does an unworked site lapse, and when?
- **BQ3** — Building outside authored areas: none until Stage 6, or a per-coordinate structure record once Stage 6 decides resources-as-data?
- **BQ4** — Who may deliver to and work on a site: anyone, or only people the owner names? (Open sites invite griefing by bad passes; closed ones need a permission list.)
- **BQ5** — `is_indoor` derived on read from the roof, or written on stage completion and on decay? The first is single-source; the second keeps today's readers untouched.
- **BQ6** — What a fumble costs: progress only (AoL's −25 %), the pass's materials, or the stage (Legend's *collapses*)?
- **BQ7** — The end of an abandoned house: the plot returns to the pool after how long untouched; the structure becomes a ruin others may salvage (Adam's salvage intent, BACKLOG *Disassemble yields parts and raw materials*); and what happens to the goods inside — always without an instant (§2.1).
- **BQ8** — Can lock-picking (Mechanisms, no combat) ship before Stage 5, opening locked storage earlier?
- **BQ9** — Furniture and chests: fixed once placed, or carryable (and so stealable) objects?
- **BQ10** — Activity-log kinds for a delivery and a building pass: existing kinds with fields, or new ones?
- **BQ11** — Shared houses: co-owners, a household, a guild hall (Discworld's clubs own houses together)?

---

## 17. Considered and not proposed

- **NPC-sold houses, deeds or materials.** Pillar 1.
- **Coin rent to the Treasury as upkeep.** A transfer that funds the faucet, not a sink for goods; it makes a house a coin cost instead of a crafting demand (§8, BP14).
- **Instant houses from a single craft.** Loses every decision a site gives — what to carry, who to hire, when to work — and the many-hands goal (BG2).
- **Houses as rooms created in play (`dig`).** Migration debt against Stage 6's map modules, which delete off-map rooms (§6).
- **A collapse timer that drops contents.** UO's IDOC: the one moment players script and camp for twenty-eight years (§2.1).
- **Instanced or private-copy houses.** Takes the house out of the shared world it is meant to change.
- **A ticker per house.** The project's lazy-evaluation rule; a timestamp does the same work.
