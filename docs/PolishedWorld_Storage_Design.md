# PolishedWorld — Storage, Granary & Pests Design Notes (where goods are kept, the place factor, cold rooms, the storage jar and its seal, the bulk bin, vermin and their answers)

> **Rev 1 · 2026-11-08** — first version, docs only, with roadmap Rev 59, BACKLOG Rev 84 and README Rev 38. Written from a design chat, the fifteenth in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`, `docs/PolishedWorld_Housing_Design.md`, `docs/PolishedWorld_Hunting_Design.md`, `docs/PolishedWorld_Cooking_Design.md`, `docs/PolishedWorld_Temperature_Design.md`, `docs/PolishedWorld_Farming_Design.md`, `docs/PolishedWorld_Textiles_Design.md`, `docs/PolishedWorld_Water_Design.md`, `docs/PolishedWorld_Foraging_Design.md`, `docs/PolishedWorld_Light_Design.md`, `docs/PolishedWorld_Forest_Design.md`, `docs/PolishedWorld_Rendering_Design.md`, `docs/PolishedWorld_Pottery_Design.md` and `docs/PolishedWorld_Rest_Design.md`. Food does not age in the code yet — BACKLOG *Food spoilage* is open and Cooking Design §9–§10 is its design — so storage has nothing to protect against until that clock ships, and this document is written on top of it. Nothing here changes live behaviour, so there is no departures table. **Nothing here is locked.** Every numbered item is a proposal (DP…), a goal (DG…) or an open question (DQ…); the letter is *D*, for depot, free across `docs/`, `world/`, `commands/`, `typeclasses/` and `server/` when checked (Hunting's departure rows D1–D9 share the letter, not the shape). In the chat Adam approved writing the document from the proposal without answering its five questions; they are recorded here as DQ1–DQ5 with the leanings recommended in the chat, recorded as *leanings*, not as decisions, and the chat's leaning on scope as DQ6. The leanings under the other questions are this document's own. One thing was found while writing that the chat did not weigh, and it is recorded rather than decided: a cellar that sets `is_cold_storage` gives the corpse's clock, which already runs backwards when the weather turns, a second way to do so (DQ7). The chat's correction to the series handoff stands here too: Pottery Design PP10 lists no storage jar, so the jar is proposed in this document (DP6). Prior art was read on 2026-11-08; code seams were read against `main` at `9248c11` (Evennia 6.1.0).
> **Canonical:** `docs/PolishedWorld_Storage_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/roadmap.md`, parallel backlog, *Storage, granary & pests* — a new entry (Rev 59), because nothing owned where goods are kept: BACKLOG *Food spoilage* owns the clock and leaves open whether cold storage is a room flag or a container property; Cooking Design proposes the spoilage index and the statue rule (CP8, CP9) and a cold-storage factor that nothing sets (CP10); Housing Design forbids risk-free storage (BG5) and leaves chests open (BQ9); Farming Design names a granary and a larder among Housing's future parts (§13); Forest Design's woodpile and Water Design's barrel wait on parts and planks. `docs/BACKLOG.md` gains two notes (Rev 84): *Food spoilage* — the design answers the entry's room-flag-or-container question with *both*, as factors that multiply (DP1); and *⚠️ Decay time can run backwards when the weather turns* — a cellar flag that comes and goes is a second trigger for the corpse's backward clock (DQ7).
**When to read:** when BACKLOG *Food spoilage* is decomposed (§6 — the place factor is part of its clock; DP1–DP3); when Housing's parts or furniture are decomposed (a larder or cellar part, chests and bins, BP7, BQ9; DP4, DP8); when Pottery's first wares are decomposed (the storage jar, DP6); when Rendering's tallow ships (the seal, DP7); when Farming's grain ships (the bin and seed in sealed jars, §13); when Forest's woodpile becomes a part (DQ17); with *animal taming* (the cat, DP12), *digging & earthworks* and *ice & cold* (cellars and ice houses, DP15), *carpentry & cooperage* (crates and barrels), *litter, abandoned goods & salvage rights* and *law/crime/bounties* (who may take from a store, DQ4) from the design-series queue.

---

## 1. The idea in one paragraph

Grain from the autumn field goes into a bin of wattle and daub in the back room, and the bin holds it as a heap, not as two hundred separate things. Through the winter the mice find it: a little goes every week, and the owner reads it in the bin's own words — *droppings among the grain* — long before it matters. A cat by the bin halves the loss; a trap set beside it halves it again; the seed corn for spring sits apart in clay jars sealed with a skin of tallow, where nothing gets in, and each time a jar is opened the seal is broken and costs another cake of tallow. Meat does not go in the bin: it is eaten, dried, or carried down to a cellar, where every clock runs at a quarter of its pace. None of this stops time — a jar in a cellar still ages, slowly — and none of it is safe from other people; it is only as safe as the door in front of it. What the store gives is a slope instead of a cliff: the household that keeps its stores well loses less, the potter sells jars, the renderer sells seals, the trapper and the cat's owner sell an answer to the mice, and nobody loses a winter's grain in a night.

---

## 2. Prior art

### 2.1 Achaea — the lesson

Sources: the Achaea forums, *Leases and Warehousing* (`forums.achaea.com`, discussion 6369), an Achaea news page on commodity decay (`achaea.com`), and AchaeaWiki, *Rift* (read 2026-11-08). Paraphrased:

- Achaea gives each player a rift — invisible personal storage for herbs, minerals, commodities and other goods. Its capacity did not cover what busy producers made, so they stored commodities on ships and in shop stockrooms, and lost large amounts when they dropped link while carrying them.
- In 2018 the administrators moved commodity storage into warehouses leased out by each city's trade ministry, for a tax, and made storing large amounts anywhere else impractical. The benefit their announcement called most important for players was speed: moving those items out of the general item database made the game run faster.
- From then on, commodities outside a rift or a warehouse decay; stockrooms and preservation bags no longer protect them, and goods taken out of the rift decay half a day later.

**Worth taking:** that storage is designed or it is invented — in the worst place available; that a bulk good kept as thousands of separate objects is a server cost before it is a gameplay question; that a container which stops time outright has to be taken away later, at a price in goodwill.

**Not for PolishedWorld:** the rift itself (weightless, invisible, safe anywhere); a city government that sets the lease and collects the tax (pillar 1; Economic Philosophy).

**The lesson (the series' "Achaea lesson"):** storage that the game does not give a shape will take one, and the shape it takes — goods heaped in stockrooms and ships, preserved by whatever stops their clock — is the one the game then spends years undoing. The rules taken: **storage slows the clock, it never stops it** (DG1), and **bulk goods are counts, not objects** (DG3).

### 2.2 Wurm Online — bins of counts

Source: Wurmpedia, *Food storage bin* and *Bulk storage bin* (`wurmpedia.com`, read 2026-11-08). Paraphrased:

- A storage bin is built of planks and iron ribbons. Items put in it are grouped by type and their quality averaged, so a bin holds a large volume as a few entries rather than as individual items.
- Decay of stored items is almost stopped, but about five percent of the stored goods is lost each month, unless the bin stands on a settlement paid up a month ahead.
- A bin can be picked up only when it is empty; renames, enchantments and other special properties are lost on the way in.

**Worth taking:** a bin as counts by kind, with averaged quality and freshness; a slow, steady loss as the bin's price; a bin that can be carried only empty; special items refused rather than flattened.

**Not for PolishedWorld:** decay almost stopped (DG1); a loss waived for paid upkeep (*absence, upkeep & inheritance* in the queue).

### 2.3 Dwarf Fortress — vermin and the barrel

Source: the Dwarf Fortress wiki, *Vermin* (older versions' pages), *Eat* and *Starting build* (`dwarffortresswiki.org`, read 2026-11-08). Paraphrased:

- Vermin eat food in stockpiles that they can reach, wearing it down until it is gone; food in barrels is protected, and metal barrels protect far better than weak ones.
- Cats hunt vermin and keep their numbers down.
- Cats that breed unchecked overrun a fortress — the well-known *catsplosion*.

**Worth taking:** the container decides exposure to vermin; the cat as the household's answer.

**Not for PolishedWorld:** cats that breed for free (animal taming owns where cats come from, DP12); vermin as creatures in the room.

### 2.4 Vintage Story — the cellar and the sealed crock

Source: the Vintage Story wiki, *Food preservation*, *Room* and *Cellar* (`wiki.vintagestory.at`, read 2026-11-08). Paraphrased:

- A cellar is a small, enclosed room with no sunlight; food stored in it spoils more slowly, and the slowing stacks with the container the food is in.
- A crock of cooked food sealed with fat or beeswax keeps much longer; taking a portion out breaks the seal, which is not restored until it is sealed again.
- The game shows the stored food's perish speed on the container, as a number.

**Worth taking:** a room factor and a container factor that multiply; the seal as a consumable that the act of taking undoes.

**Not for PolishedWorld:** a room recognised by its geometry (a room here is authored or a house's part, DP4); the perish speed as a number (Cooking CG1 reads freshness in words).

---

## 3. Design goals

- **DG1 — Storage slows the clock, it never stops it.** Every place and container is a factor greater than zero. The one exception is the statue, which is Cooking's (CP9) and is bounded by what a body carries (DP16).
- **DG2 — Every loss is a slope you can read and answer.** Farming GG2's rule for the store: nothing is lost in a moment, everything shows in words first, and every loss has a service that answers it.
- **DG3 — Bulk goods are counts, not objects.** A heap of grain in a bin is one object holding numbers, not a row per measure (§2.1, §2.2).
- **DG4 — No risk-free storage.** Housing BG5 as written: a store is as safe as the door in front of it, and no store is a bank.
- **DG5 — Nothing ticks.** Freshness reads Cooking's spoilage index; vermin read elapsed time from a stamp; every change is computed on read or at an event.
- **DG6 — Every store ships with a loss that bites.** Rendering ZG1's rule, here for stores: a bin ships with vermin, a jar with the clock it slows; nothing ships as a pure convenience.

---

## 4. Legend alignment

**Rules as written:**

- **No test** — p. 42: the automatic success and failure rules do not apply where the Games Master rules that no test is required.
- **Odd jobs** — p. 85: the Odd Job Table lists *Rat Catcher/Pest Control* at 2D4 CP a day, with a free net, beside the farmhand and the grave digger.
- **Starting goods** — p. 35: an Adventurer begins with a week's worth of food, fresh or preserved.
- Legend's core has no rule for spoilage, storage or vermin. Monsters of Legend has insect swarms (book 1) and no ordinary rats or house cats.
- **Arms of Legend** (`docs/reference/arms_of_legend.md`): the Preserving Kit — salt, wrappings, a sawdust tool, jars — gives the tools for any test to preserve and store food, ten uses (`:390`); the handled net, for catching small creatures such as rats (`:356`); the cat, which rids a house or farm of small vermin and scares off small predators (`:2831`); the sea chest, built to keep its contents dry even submerged (`:446`); wax, a block used in many trades (`:514`).

**Translation proposals:**

- **DP-L1 — Storing needs no test.** Putting goods away is routine; p. 42 lets the Games Master rule that no test is required. Skill shows in the choices — where, in what, with what answer to the mice — not in a roll.
- **DP-L2 — The rat catcher is a trade.** Legend's odd job (p. 85) is a player's service here: the trapper who sets and tends traps in other people's stores, or the cat's owner (DP12, DP13).
- **DP-L3 — The cat is read, not sold.** AoL's cat (`:2831`) is the reader DP12 names; where a cat comes from is *animal taming*'s.
- **DP-L4 — The Preserving Kit stays Cooking's.** It is the salting tool (Cooking CP-L6); the storage jar is a separate ware a potter makes (DP6).
- **DP-L5 — Legend's prices are not used.** Pillar 1.

---

## 5. The loop

Proposed phases; each is something someone can sell.

1. **Make the store.** A potter fires jars (DP6); a builder raises a bin of wattle and daub (DP8); a house gains a larder or cellar (DP4).
2. **Fill it.** Dry goods into the bin, as counts (DP9); what must keep longest into jars (DP6).
3. **Seal it.** A jar sealed with tallow keeps longer and shuts the mice out (DP7).
4. **Guard it.** A cat by the bin, a trap set beside it (DP12, DP13).
5. **Read it.** The bin says how full it is and whether the mice are at it (DP14).
6. **Take from it.** A measure out of the bin; a jar opened, its seal broken (DP7, DP9).

---

## 6. The place factor

**DP1 — One factor: room × container × holder.** Cooking CP8 gives every food an anchor on a global spoilage index and a *place factor*; this document names its parts. The factor is the product of the room's (open 1, cellar 0.25 — the cold-storage multiplier the corpse already uses, `typeclasses/corpse.py:104`), the container's (none, a sack or a bin 1; a jar 0.5; a sealed jar 0.25) and the holder's (a statue 0, Cooking CP9). It is BACKLOG *Food spoilage*'s room-flag-or-container question answered with *both*, in the shared module that entry asks for (`world/decay.py`). Season and weather stay on the index, not on the place, so a jar in a summer cellar still feels the summer.

**DP2 — Every change of factor is an event, and every event advances the anchor first.** Cooking CP8 makes moves and log-ins events; storage adds three. A food's anchor is advanced at the old factor before the new one applies when it is put in or taken out of a container (a move), when its jar is sealed or unsealed (DP7), and when its room's cold-storage flag changes (DP4) — the last walks the room's contents and their containers once. The clock stays monotone, and reading stays O(1).

**DP3 — The factors, on one table** (DQ11):

| Where | Factor | Vermin (DP11) |
|---|---|---|
| loose in an open room, or in a sack | 1 | not read in v1 |
| in a bulk bin | 1 | yes |
| in a storage jar | 0.5 | yes, as a bin |
| in a sealed storage jar | 0.25 | none |
| in a cellar (`is_cold_storage`) | × 0.25 on any of the above | as above |
| carried by a statue | 0 (Cooking CP9) | none |

A sealed jar in a cellar runs at a sixteenth of the open-room pace; nothing reaches zero but the statue (DG1).

---

## 7. Cold rooms

**DP4 — Who sets `is_cold_storage`.** Nothing does today; the corpse reads it (`typeclasses/corpse.py:104`) and Cooking CP10 waits on it. Proposed, in order: staff on an authored cellar room; a house's larder or cellar part when Housing's parts are decomposed (Housing BP7; Farming §13 names the larder); later, a cellar dug under a house (*digging & earthworks*) and an ice house (*ice & cold*). A cellar is pitch black by Light Design LP2's pin, so finding the jar needs a light. The flag changes only at those writers, and each change is an event (DP2).

**DP5 — The corpse keeps reading the flag.** A body carried down to a cellar slows as it does today; whether the corpse moves onto the spoilage index with food is Cooking CQ9's, and the new way its clock runs backwards is DQ7.

---

## 8. Jars and the seal

**DP6 — The storage jar, a new ware for Pottery PP10.** Three lumps of clay, shaped in Pottery's proposed `pottery` discipline and fired in a pit (Pottery PP1, PP3). A `Container` (`typeclasses/containers.py:32`) of capacity 4 ENC, ENC 2 itself, holding food and dry goods; factor 0.5 for what is inside (DP3). It wears on `condition` per opening, as Pottery PP11's wares wear per use, and breaks at zero with its contents spilled into the room, never destroyed with them. It is a container, so it cannot go into a sack or a pack (`:44`, no nesting): a jar is carried in the hand, which is its weight's point.

**DP7 — Sealing with tallow.** `seal <jar>` consumes one cake of tallow — a small item, twenty to one ENC (`world/encumbrance.py:50`; Rendering ZP4) — and sets the jar sealed: factor 0.25 and no vermin. Any `get … from` the jar breaks the seal (`commands/inventory_commands.py:68`), as Vintage Story's crock does (§2.4); putting more in does too. Sealing and unsealing are events (DP2). Wax seals the same way once beekeeping gives it a source (AoL `:514`). A recurring sink for tallow and the reason a household buys it in autumn.

---

## 9. The bulk bin

**DP8 — A bin of wattle and daub.** Sticks, clay and twine — existing materials, as Housing BP8's hut is — made by `craft` (woodwork, DQ9). It stands indoors only (`is_indoor`, `world/thermal.py:68`): grain in the rain is grain lost, and an outdoor bin is Housing's granary part, later. It can be picked up only while empty (§2.2), and is fixed (`get:false()`, `typeclasses/resources.py:61`) while it holds anything, which is Housing BQ9's question answered for this one object. Its builder is stamped on it. Capacity about 40 ENC (DQ9).

**DP9 — Counts, not objects.** A bin holds slots keyed by kind and quality band (`world/crafting_quality.py`): `{(kind, band): count, used hours, index anchor}`. Putting an item in deletes the object and adds one to its slot, its used hours averaged into the slot's (Wurm's averaging, §2.2) after the slot is advanced to now; taking one out creates a fresh object carrying the slot's used hours, anchored now. Bands are kept apart so that a poor measure never launders into a superior heap. The bin's ENC is its counts' (twenty small items to one ENC, `world/encumbrance.py:50`), checked in the bin's own put hook, since the shipped walk (`enc_after_receiving`, `:180`) counts objects. Two hundred measures of grain are one object and one attribute (DG3), as coin is a number in a wallet (Evennia Reference §7.4). A consequence: a slot ages as one, and a heap that turns, turns together — read in words beforehand (DQ10).

**DP10 — What goes in a bin.** Plain goods only: things with no `condition`, no charges, no maker's mark and no name of their own — grain, flour, dried food, salt, nuts, clay lumps, sticks. Anything else is refused with a line that says why, rather than flattened as Wurm flattens it (§2.2; DQ8, DQ18). Fresh meat goes in a jar or a cellar, not a bin: it is not refused, but it rots at the bin's factor of 1.

---

## 10. Vermin

**DP11 — Vermin as a slope.** A bin, and an unsealed jar, lose part of their food to mice and rats over game time: about five percent of each slot per game month (DQ12) — a game month is seven real days (`server/conf/settings.py:50–64`). It is computed on read from a stamp: the elapsed span times the rate, times the room's answers (DP12, DP13), accumulates as a fractional debt on the slot, and whole units leave the slot when the debt passes one. No dice, no ticker, nothing lost in a moment; a small bin loses its first measure later than a large one, never sooner. Vermin eat food only: clay, salt and sticks in a bin are untouched. It runs whether the owner is online or not (DQ5) — the world's mice do not wait — at a slope a week away barely shows (DG2).

**DP12 — The cat.** A cat in the room halves the rate (AoL `:2831`). Duck-typed: anything in the room whose `keeps_vermin()` is true. Where a cat comes from, whether it must be fed and whether it may wander are *animal taming*'s (DQ13); a cat that breeds for free is not proposed (§2.3).

**DP13 — The trap.** A small trap of sticks and twine (`craft`, woodwork), set in the room, halves the rate again and wears in service, lasting about a game season (DQ15) — a steady sink and the trapper's trade (DP-L2). Cat and trap multiply: a quarter of the rate with both. A raised or stone granary, later, is Housing's part and a third answer.

**DP14 — Read in words.** The bin shows how full it is (*a few handfuls*, *half full*, *heaped*) in the shipped availability phrase's shape (`typeclasses/resources.py:129–147`) and whether vermin are at it (*clean*, *droppings in the corners*, *gnawed and fouled*) from the debt's recent pace, so a careless store is visible to its owner and to a visiting rat catcher alike.

---

## 11. What waits

**DP15 — Recorded, each with its own system:**

- **Barrels, tuns and crates** — planks are BLOCKED on a saw (`world/material_registry.py:317`); Water Design's barrel (§10) stays Water's; a crate is a bin of planks with *carpentry & cooperage*.
- **The woodpile** — Forest Design's later Housing part (§15); whether it holds wood on this document's counts is DQ17.
- **The granary and the larder as house parts** — raised on stones against vermin, dry under a roof, cold below ground; Housing BP7 and Farming §13.
- **Cellars dug and ice houses** — *digging & earthworks*, *ice & cold*; both set `is_cold_storage` (DP4).
- **Wax seals** — with beekeeping (*brewing, fermentation & beekeeping*).
- **Moths in wool and cloth, weevils in flour** — a second vermin kind on the same debt, once Textiles' wool and Farming's flour exist (DQ20).
- **Crop pests in the field** — birds and mice in a growing field stay Farming's (DQ6).
- **Locks on chests and store rooms** — Housing BP15 and *stealth, locks & theft*.

---

## 12. Offline and the world

**DP16 — The statue is a larder, bounded by a back.** Cooking CP9 stops the clock on what a logged-out character carries, for the reason Armageddon taught (Cooking §2.1): goods given between players who are never online together must not rot between them. It also makes a second character, left logged out, a stasis store — Achaea's preservation bag in another coat (§2.1). Proposed: accept it, because it is bounded by what one body can carry — and whether a statue can be robbed is Rest NQ5's question, left to *stealth, locks & theft* and *law/crime/bounties* — and watch it through the activity report at the economy milestone (DQ2). Bins and jars keep ageing and losing to vermin while their owner is away, on the slopes above (DG2).

---

## 13. Economy

**Sources (all player-made):** jars from the pit, bins from sticks and clay, traps, seals of tallow.

**Sinks:** food lost to vermin (the store's ongoing sink, DG6); tallow spent on every seal (DP7); jars worn by opening and broken (DP6); traps worn in service (DP13); the clay, sticks and twine in every bin.

**Materials this design gives a source or a sink:** **clay** (a third ware); **tallow** (a recurring sink beside Light's candle, Rendering ZP5); **sticks and twine** (bins and traps); **food** (a slow sink in every store — the sink BACKLOG *Food spoilage* says the economy lacks, here on what is kept rather than what is carried).

**Services:** the potter's jars; the renderer's seals; the trapper and rat catcher, setting and tending traps in other people's stores (DP-L2); the cat's keeper; the builder of bins; a cellar's owner who keeps a neighbour's jars cool — a place in a cellar is the store's natural service, as a place in a kiln load is the kiln's (Pottery §13).

**DP17 — The master constant, on one page.** At the leanings: a winter is three game months, three real weeks (`world/gametime_utils.py:56–61`, `server/conf/settings.py:50–64`). A bin of two hundred measures of grain left alone through a winter loses about twenty-nine (one minus 0.95³ — about fourteen percent); with a cat about fifteen; with a cat and a trap about seven. Four sealed jars hold eighty measures (twenty small items to one ENC) and lose none to vermin — so the seed corn goes in jars and the eating grain in the bin, which is Farming GG5's seed-is-capital choice made physical. A sealed jar costs one cake of tallow per opening; one autumn stag gives three cakes (Rendering ZP15). Every number moves together; the decomposition tunes this table, not the parts one by one.

**DP18 — No exclusive.** Anyone may make a jar, a bin or a trap. Proposed for the roadmap's food-professions exclusives decision: storage is on no list.

**Coin:** none. **Logging:** filling a bin, sealing and vermin losses are DQ16.

---

## 14. Multiplayer and server load

- **One object for a heap.** A bin of two hundred measures is one row and one attribute, not two hundred objects (DG3) — the reason Achaea moved its commodities (§2.1).
- **Atomic counts.** Putting into and taking from a bin is one synchronous read-modify-write on the slot inside one command, with no `yield` between the read and the write, so two players taking the last measure cannot both get it — the shape the shop's last item needs (Housing BP16).
- **Nothing ticks.** Freshness reads the spoilage index; vermin read a stamp; seals and flags are events (DP2, DP11).
- **Events stay bounded.** A cellar flag change walks one room's contents once (DP2); it happens when a house part is finished or decays, not per read.
- **Who may take.** Anyone, in a room anyone can enter, as with racks, snares, clamps, fires and kilns (DQ4; Cooking CQ12, Hunting TQ12, Forest YQ3, Rendering ZQ15, Pottery PQ11). The bin's builder is stamped on it; theft is law & crime's.
- **Wilderness.** No bins or jars set down there; Stage 6's (Evennia Reference §14.6).

---

## 15. Immersion extras

- **The sound in the wall.** A store with vermin at it gives a line now and then to whoever stands in the room — a scratching, a squeak — from the same debt (DP14).
- **The cat by the bin.** A cat in a store room shows in the room's text, curled on the bin's lid.
- **The tallow skin.** A sealed jar reads *sealed with a pale skin of tallow*; a broken seal shows the crack.
- **Autumn stores.** The harvest goes in, the jars are sealed, the trapper makes rounds — the season's work beside Rendering's kettles and Forest's woodpile.

---

## 16. Layers — a suggested order

1. **Slice 0 — the place factor ships inside BACKLOG *Food spoilage*:** DP1–DP3 as part of the clock, with the room and statue factors only. No new objects.
2. **Slice 1 — the jar, with Pottery's first slice or right after it:** DP6, unsealed; its reader is the clock it slows.
3. **Slice 2 — the seal, with Rendering's tallow:** DP7.
4. **Slice 3 — the bin and vermin, together (DG6), with Farming's grain:** DP8–DP14 — the bin never ships without the mice, and the trap ships with them as their first answer; the cat with *animal taming*.
5. **Cellars (DP4)** whenever staff author one or Housing's parts are decomposed.

**Prerequisites:** BACKLOG *Food spoilage* (1)–(3) for everything; Pottery's pit for the jar; Rendering's tallow for the seal; a bulk good worth storing — grain, or dried food in quantity — for the bin. **Not prerequisites:** Stage 5, the webclient, the economy milestone.

---

## 17. Seams in today's code (read at `9248c11`)

| Need | Seam | Where |
|---|---|---|
| Food | `Food`, `restore_amount`, no age | `typeclasses/consumables.py:19–25` |
| Cold-storage flag | read by the corpse, set by nothing; season and weather tables | `typeclasses/corpse.py:104`, `:49–50`, `:92–106` |
| Expiry | `crumble()`; the room-entry sweep | `typeclasses/corpse.py:166`; `typeclasses/rooms.py:358`, `:391` |
| Containers | `Container`, capacity in ENC, no nesting | `typeclasses/containers.py:32`, `:44` |
| Put only into containers | `ObjectParent.at_pre_put_in` | `typeclasses/objects.py:25` |
| Put and get | `CmdGet` (from containers), `CmdPut` | `commands/inventory_commands.py:68`, `:104` |
| Shipped containers | sack 10, backpack 20, saddlebag 15; no sink | `world/prototypes.py:699–711`, `:715`, `:742`; `world/recipes.py:315` |
| Weight | small items twenty to one ENC; the receiving walk | `world/encumbrance.py:50`, `:180` |
| Durability | `DurableObject`, `condition`, `apply_wear` | `typeclasses/durable.py:31`, `:41`, `:43` |
| Fixtures | `get:false()` on a node; the availability phrase | `typeclasses/resources.py:61`, `:129–147` |
| Indoors | `is_indoor` | `world/thermal.py:68` |
| The weather clock | `WeatherScript.at_repeat` | `typeclasses/scripts.py:112`, `:135` |
| Statues | `at_post_unpuppet`, `at_post_puppet` | `typeclasses/characters.py:472`, `:494` |
| Calendar | seasons; speed | `world/gametime_utils.py:56–61`; `server/conf/settings.py:50–64` |
| Recipe sources | every gated recipe has a source | `tests/test_recipe_sources.py` |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **DQ1** — The letter. *Leaning (chat, 2026-11-08): D, for depot, as used here; Hunting's departure rows D1–D9 share the letter, not the shape.*
- **DQ2** — The statue as a larder (DP16). *Leaning (chat, 2026-11-08): accept it — bounded by what a body carries — and record it, to be watched through the activity report at the economy milestone.*
- **DQ3** — Do sacks wear, so that the shipped containers get a sink (`world/prototypes.py:708`)? *Open — asked in the chat without a leaning; carts & hauling or Textiles' mending may answer it.*
- **DQ4** — Who may take from a bin or jar in a room anyone can enter? *Leaning (chat, 2026-11-08): the same answer as Cooking CQ12 — anyone, in the alpha; the builder stamped; theft is law & crime's.*
- **DQ5** — Do vermin eat while the owner is away? *Leaning (chat, 2026-11-08): yes, as the slow slope of DP11 (DG2).*
- **DQ6** — Which design owns what. *Leaning (chat, 2026-11-08): this one owns pests in stored goods and storage vessels with their seals; pests in a growing field stay Farming's; carried containers stay the weight decomposition's; the queue's* vermin & crop pests *and* containers, packaging & sealing *entries fold into this document for their storage halves.*
- **DQ7** — Found while writing: the corpse multiplies its whole elapsed span by today's modifier (`typeclasses/corpse.py:116–133`), so a cellar flag that is set when a larder is finished and cleared when it decays would make a body in it look fresher or older at once — BACKLOG *⚠️ Decay time can run backwards*'s fault with a second trigger. Does the corpse move onto the spoilage index before any writer of the flag ships (Cooking CQ9), or does the flag stay staff-only until it does? *Open.*
- **DQ8** — What counts as a plain good for a bin: a prototype flag, or the absence of `condition`, charges, mark and own name? *Leaning: a flag on the prototype, checked by a test like `tests/test_recipe_sources.py`, so a new good is opted in, not discovered.*
- **DQ9** — The bin's recipe, discipline and capacity. *Leaning: six sticks, four clay, two twine, woodwork, about 40 ENC.*
- **DQ10** — A slot that averages freshness turns all at once. Is that acceptable, or does a bin keep a few age cohorts per slot? *Leaning: acceptable for goods that keep for months; the words show it turning first.*
- **DQ11** — The factors of DP3. *Leaning: as tabled; tuned with Cooking CQ2's shelf lives.*
- **DQ12** — The vermin rate, and whether it varies with season (mice come indoors in autumn). *Leaning: five percent per game month, flat in v1.*
- **DQ13** — The cat: from *animal taming*, and does it need feeding? *Open — animal taming's.*
- **DQ14** — An authored public cellar in the alpha — under the Old Temple, say — so cold storage exists before Housing's parts? *Open; it is free storage in a room anyone can enter, which DG4 allows and law & crime will test.*
- **DQ15** — The trap's recipe, its wear and its source. *Leaning: two sticks and a twine, woodwork, about a game season of service; its recipe source with the bin's (`tests/test_recipe_sources.py`).*
- **DQ16** — Activity-log kinds for filling and emptying a bin, sealing, and vermin losses: new kinds or fields on existing ones? The family of Pottery PQ13 and its siblings. *Open.*
- **DQ17** — Does Forest's woodpile hold wood on this document's counts, with the seasoning stamp averaged per slot (Forest YP3)? *Leaning: yes, when the woodpile becomes a part; Forest's to decide.*
- **DQ18** — Goods with a maker's mark or a name: refused by a bin, or stored as their own slot? *Leaning: refused (DP10).*
- **DQ19** — How long dry grain and flour keep on the clock. *Open — Farming's and Cooking CQ2's; this design assumes months.*
- **DQ20** — Moths in wool and weevils in flour as a second vermin kind. *Leaning: later, on the same debt, once wool and flour exist.*

---

## 19. Considered and not proposed

- **A rift or any weightless store.** Achaea's (§2.1); DG1, DG4.
- **A bin that stops decay.** Wurm's (§2.2); DG1.
- **Loss waived for paid upkeep.** Wurm's settlement rule (§2.2); *absence, upkeep & inheritance*.
- **Vermin as creatures in the room.** Dwarf Fortress's (§2.3); a debt on the slot is enough, and costs nothing per mouse.
- **Cats that breed for free.** The catsplosion (§2.3).
- **A random raid on a store.** A roll that empties a bin is a loss in a moment (DG2).
- **A cellar recognised by its shape.** Vintage Story's (§2.4); rooms here are authored or built.
- **Freshness shown as a number.** Cooking CG1.
- **NPC warehouses, granaries or rat catchers.** Pillar 1.
- **A statue that ages its goods.** It would rot gifts between players who are never online together (Cooking CP9; DP16).
