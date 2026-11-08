# PolishedWorld — Water Design Notes (drinking, vessels, wells, brine, rain)

> **Rev 1 · 2026-11-08** — first version, docs only, with roadmap Rev 53, BACKLOG Rev 77 and README Rev 31. Written from a design chat, the eighth in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`, `docs/PolishedWorld_Housing_Design.md`, `docs/PolishedWorld_Hunting_Design.md`, `docs/PolishedWorld_Cooking_Design.md`, `docs/PolishedWorld_Temperature_Design.md`, `docs/PolishedWorld_Farming_Design.md` and `docs/PolishedWorld_Textiles_Design.md`. Water is partly shipped — one spring, the gourd waterskin, `drink` and `refill` — so the notes name every place they would change live behaviour (§6). **Nothing here is locked.** Every numbered item is a proposal (VP…), a goal (VG…) or an open question (VQ…); the letter is for *vatten*. In the chat Adam approved writing the document from the proposal; the leanings under VQ1 and VQ2 are the ones proposed in the chat, recorded as *leanings*, not as decisions, and the leanings under the other questions are this document's own. Prior art was read on 2026-11-08; code seams were read against `main` at `2f2b02f` (Evennia 6.1.0).
> **Canonical:** `docs/PolishedWorld_Water_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/roadmap.md`, parallel backlog, *Water — drinking, vessels, wells, brine* — a new entry (Rev 53) that points here; water had no roadmap entry before. `docs/BACKLOG.md` gains three notes (Rev 77): *Waterskin `durability` → `condition` migration* (VQ6 leans to doing it first, before any new vessel copies the divergent shape), *Tanning upgrade — bark and water as `LeatherRecipe` inputs* (VP2 proposes the shape of registry open decision 6, which that entry names as its trigger) and *Weather inertia, and Legend's four independent axes* (the rain catch reads Cooking's wet index, not inertia; droughts, VQ5, are a consumer of part (1)). The registry's open decision 6 (`world/material_registry.py:503–504`) is code and is left as it is; the decomposition that locks VP2 marks it resolved.
**When to read:** at the start of a water decomposition; when Cooking Design's fire, drying rack or salting is decomposed (CP1–CP3, CP11; CQ5 salt, CQ14 water in a stew); when Textiles Design's retting, felting or dye vat is decomposed (WP1, WP3, WP8); when BACKLOG *Tanning upgrade* is picked up; when the station question (kiln, furnace, forge — registry open decisions 7–9) is decided, since the clay jug waits for the kiln; when Housing Design's plots and parts are decomposed (a well on a plot, BP4, BP7; ownership BQ2); with *Disease system* and *Herbalism* (still water, VP3); with *Weather inertia* (droughts, VQ5); when Stage 6 decomposes wilderness (VP8, with Fishing Design FQ5).
**Departs from shipped behaviour in three places**, listed with their source lines in §6. The largest: a character can drink at a spring without a vessel.

---

## 1. The idea in one paragraph

Water is free, and it is only ever *there*. A traveller kneels at the brook and drinks; to carry water away she needs a vessel, and every vessel was made by someone — a gourd strapped with twine, a sewn leather skin, a leather bucket, a fired jug, a cooper's barrel — and wears out as it is used. Where people live is where water is: a spring, a stream, a pond, and in time a well that someone sank over ground that holds water, with a bucket on a rope that someone else made. A barrel under the eaves catches the rain. A brine spring up on the ridge gives nothing to drink, but brine poured into a stone-lined pan dries in a week of sun to a white crust of salt, the first salt anyone has had. Every craft that needs water — a stew, a felting, a dye vat, a tanning — takes it the same way: free at the water's edge, or poured out of a vessel the crafter carried there. Nobody sells water; people sell the vessel, the well, the salt and the carrying.

---

## 2. Prior art

### 2.1 The Diku lineage — the lesson

The series puts Achaea in this place. A search for how Achaea handles water and thirst turned up nothing usable, so the slot goes to the lineage every MUD's water comes from. Sources: Aardwolf's in-game help as published on its wiki (*Newbie-Thirst*), MUME's command documentation (*Drink*), the WoTMUD wiki (*Liquid container*, *A fountain*) and the Cleft of Dimensions wiki (its drink-container and fountain notes). Paraphrased:

- Aardwolf tells a new player there are two ways to deal with thirst: type `drink` in the room with the academy's fountain, or buy a goblet from a clan hall, which can be filled at any fountain and lasts forever.
- MUME's `drink` with no argument drinks from a source in the room — a stream, a fountain, a well; thirst costs effectiveness in combat and in regeneration.
- WoTMUD lists fountains as stationary liquid containers holding ten thousand sips, and its list of such fixtures includes wells, ponds and creeks — and one well described as repulsive. Liquids have kinds: water, ales, wines, milk, tea.
- In Cleft of Dimensions, containers are filled at fountains, poured into one another and emptied onto the ground; a container holds one kind of liquid and must be emptied before it takes another; drinking straight from a fountain takes three servings at once.

**Worth taking:** drinking at the source (VP1); three servings at a source (VP1); one kind of liquid per vessel, with `pour` and `empty` (VP3, VP4); wells and ponds as fixtures in rooms.

**Not for PolishedWorld:** drink containers and drinks bought from shops (pillar 1); a vessel that lasts forever.

**The lesson (the series' "Achaea lesson"):** a fountain in every town and a cup that never wears out turn thirst into a tax paid once and then forgotten. The rule taken: water itself is free and never sold, but only where it is; what costs is distance — the vessel, the carrying, the well (VG1, VG2). The shipped waterskin already wears out by refills (`typeclasses/consumables.py:44–53`), so the second half is half done.

### 2.2 A Tale in the Desert — the jug, not the water

Sources: A Wiki in the Desert (`atitd.wiki`, Tale 8–11 pages *Jugs*, *Jugs of Water*, *Wet Clay Jugs*, *Clay*). A Tale in the Desert has a player-run economy, the closest match to pillar 1. Paraphrased:

- Empty jugs are filled near any water source in one action.
- Most actions that need water — filling a tub, watering vegetables, gathering clay — empty the jug and leave it; only where water in jugs is itself a building material, a research donation or tuition is the jug used up with the water.
- Jugs are wet clay shaped on a pottery wheel and fired in a kiln, and gathering clay costs a jug of water, so a new player starts with a free jug from a school or trades for one.

**Worth taking:** the shape of registry open decision 6 — the work empties the vessel and keeps the vessel (VP2); the vessel, not the water, as the scarce good (VG2).

**Not for PolishedWorld:** a free starter vessel from the game. The shipped bootstrap is the gourd waterskin at rung 0 with no tool required (`world/recipes.py:126–135`), and VP1 makes the very first drink need no vessel at all.

**The rule taken:** the work empties the vessel, not the world (VP2).

### 2.3 Haven & Hearth — where the water is

Sources: the Ring of Brodgar wiki (*Well*, *Legacy:Well*, *Legacy:Water*, *Legacy:Nodes*, *Finding high quality water, clay, and soil*). Paraphrased:

- Water carries a quality; most water is at a base value, but rivers and lakes hold nodes where it is higher, and players sample along a river to find the centre of one.
- A well is a built structure of stone, wood, rope and a bucket, sited with a dowsing rod, and drawn from with a container; its water's quality comes from the source beneath it.
- High-quality water is traded as a commodity to those without access, and it limits the quality of what is made from it.

**Worth taking:** the well as a built thing that needs a place, a bucket and a rope (VP6); where water is decides where people settle.

**Not for PolishedWorld:** water quality as a number that caps craft quality. Water here has a kind in one word, not a grade (VP3), and adds nothing to a recipe's roll. Dowsing as a magic focus (AoL `:216`) waits for Stage 7.

**The rule taken:** place matters. A well can be sunk only where authored ground holds water (VP6).

### 2.4 Project Zomboid — when free water stops

Sources: player guides on `pzfans.com` (*Rain Collector*, *Boiling Water*, *How to Build a Well*), the PZ wiki (*Water Bottle*) and Steam discussions. Paraphrased:

- Tap water runs clean until a shutoff; after it, players build rain collectors with carpentry, which fill only under open sky.
- River, lake and rain water is tainted and makes a character sick unless boiled on a heat source or treated with tablets; plumbing a sink to a rain barrel moves the water indoors but does not purify it.
- Players plan a water day: collect, boil, store.

**Worth taking:** a rain catch as a built object that fills from the weather (VP7); boiling as the answer to bad water, when bad water means something (VP3).

**Not for PolishedWorld:** a scripted shutoff; tainted water before a disease system exists to give it teeth.

**The rule taken:** when water stops being free *nearby*, players build for it. PolishedWorld's shutoff is geography — the alpha has one spring (`world/seed_data.py:202–203`).

---

## 3. Design goals

- **VG1 — Water is free at the source.** No one sells water; the world gives it where it is (§2.1).
- **VG2 — Distance is the price.** What is sold is the vessel, the carrying, the well, the barrel and what is made from water — salt (§2.1, §2.2).
- **VG3 — One rule for every craft that needs water.** Registry open decision 6 is decided once, and every later reader uses it (§2.2; VP2).
- **VG4 — No one is stranded beside a stream.** A character with nothing can always drink at a source (VP1).
- **VG5 — Every vessel wears.** Refills and draws wear what holds the water, as the shipped waterskin does (`typeclasses/consumables.py:44–53`).
- **VG6 — Nothing ticks.** Sources are endless, rain is read from an index, a salt pan from another; no water object runs a ticker (the project's lazy-evaluation rule, `typeclasses/resources.py:7–11`).

---

## 4. Legend alignment

**Rules as written:**

- **Exposure, Starvation and Thirst** — Legend core p. 90: an Adventurer can go CON × 4 hours before becoming chronically thirsty, and particularly arid places reduce that to CON × 3 or even CON × 2; while thirsty, the Fatigue test penalty doubles to −20 % and every location takes one point of damage a day; only water (or food, or shelter, for their conditions) lets healing work again.
- **Survival (POW+CON)** — p. 63: one test for every day an Adventurer lacks food, water or a safe place to sleep; success means he finds it; not used in a city or town; a critical weathers the conditions for days, a fumble calls for a Resilience test.
- **Poisons and diseases** — p. 78: one application is *Ingested*, through eating or drinking; Potency 10–100 is opposed by Resilience or Persistence.
- **Engineering (INT×2)** — p. 58; Housing Design BP1 makes it the building skill.
- **Swim** and **Asphyxiation/Suffocation/Drowning** — named, not used here (travel/boats in the queue).
- **Rain** — p. 186, a spell that brings rain from a clear sky; Stage 7.
- **Arms of Legend, goods** (`docs/reference/arms_of_legend.md`): the waterskin, a lined bladder or sewn leather pouch with a spout, holding enough to sustain an Adventurer for two days, and as able to hold wine or poison (`:512`; ENC 1, `:617`); the water pack, a tar-and-wax sealed skin on two straps holding 25 litres (`:508`; ENC 6, `:615`); the water trap, a waxed tarp on a frame that gathers 1D4−1 daily rations of dew a night (`:510`; ENC 4, `:616`); the water additive, a vial of alcohol for brackish pools, +10 % to a Resilience test against disease, not poison (`:504`); sea salt, collected from salt water (`:448`); salt tablets (`:430`); dowsing rods, +10 % to casting Detect spells (`:216`); the great font of a temple (`:268`).
- **AoL, trades:** the cooper, who makes and binds barrels, tuns and kegs (`:3004`); the potter, whose wares run from sun-dried water jugs to burial urns (`:3088`).
- **Shipped:** the waterskin prototype cites Legend core p. 119 and AoL for its ENC 1 (`world/prototypes.py:270`).

**Translation proposals:**

- **VP-L1 — Thirst stays the shipped gauge.** Thirst falls 2 a tick (`world/survival_ticker.py:21`) every 600 s (`server/conf/at_server_startstop.py:27`), so a full gauge lasts about 33 game hours at the 4× clock, against Legend's CON × 4 (48 hours at CON 12). Noted, not changed: that is a balance pass. Legend's arid ×3 and ×2 become a room or biome multiplier on `thirst_rate` — the same mod HeatStress already applies (`world/survival_buffs.py:86`) — when Stage 6 has dry country.
- **VP-L2 — Survival's daily test is for the wilderness.** In authored rooms water is visible and found by looking; the test belongs to coordinates with no authored water, and the skill that rolls it is VQ4 (the `survival` name is taken by the gauge category, `typeclasses/characters.py:446`).
- **VP-L3 — Ingested disease is still water's hook.** Nothing harms a drinker until *Disease system* exists; then a draught of still water is an exposure with a Potency, opposed by Resilience, and AoL's water additive is an alchemist's product (*alchemy & poisons* in the queue).
- **VP-L4 — A well is engineering.** Built on Housing Design's site machinery: Engineering, Task Rounds, a site that shows its need (BP1, BP2, BP6).
- **VP-L5 — Legend's prices are not used.** Pillar 1. ENC: the leather waterskin ENC 1 (AoL `:617`); the bucket proposed ENC 2 (AoL has none; the water pack's 25 litres are ENC 6).

---

## 5. The loop

Proposed phases; each is something someone can sell.

1. **Find water.** A spring, a stream, a pond in an authored room, read on `look` (VP3); later a well (VP6), a rain catch (VP7), or a coordinate's terrain in the wilderness (VP8).
2. **Drink there.** `drink` at the source, no vessel needed (VP1).
3. **Draw it.** `refill` a vessel; the vessel takes the source's kind (VP3) and wears (VG5).
4. **Carry it.** In a waterskin to drink on the road; in a bucket to a dye vat, a felting or a cookpot; `pour` from one vessel into another (VP4).
5. **Use it.** Drink a draught, or let a craft draw its draughts — free at a source, or out of the carried vessel (VP2).
6. **Store it.** A barrel in a house; a rain catch outdoors (VP4, VP7).
7. **Make salt.** Brine from a brine spring into a salt pan; a week of dry weather gives salt (VP5).

---

## 6. Departures from shipped behaviour

Each row is a change to behaviour that `main` has today; each is a proposal.

| # | Shipped today | Proposed | Where shipped |
|---|---|---|---|
| N1 | `drink` accepts only a `Drink`; a character with no vessel cannot drink at the spring | `drink` with no target, or naming a source, drinks at a source in the room (VP1) | `commands/consumption_commands.py:67`, `:88` |
| N2 | `refill` fills any refillable `Drink` at any source with *cool, clear water*, and every source reads *clear water flows here* | A source has a kind; the vessel takes it; a vessel holding another kind must be emptied first; the lines name the kind (VP3) | `commands/foraging_commands.py:198–202`, `:243`; `typeclasses/resources.py:135–136` |
| N3 | A draught restores the vessel's `restore_amount` whatever it holds | Brine is refused as a drink; fresh and still restore as today (VP3, VP5) | `commands/consumption_commands.py:100` |

Unchanged: the thirst gauge, its rate and the *dehydrated* condition (`world/survival_ticker.py:21`, `:32–35`); heat stress on `thirst_rate`; respawn's thirst reset (`typeclasses/characters.py:1337–1344`); the waterskin recipe, its band table and its refill wear (`world/recipes.py:57–62`, `:126–156`); the spring's endlessness; `forage`'s skip of water sources (`commands/foraging_commands.py:90`); the `consume` log line for drinking from a vessel.

---

## 7. Drinking

**VP1 — Drink at the source.** `drink` with no target, or `drink spring` (any source's key or alias), drinks at a water source in the room, the same scan `refill` makes (`commands/foraging_commands.py:198–202`). One act restores what three draughts would — Cleft's fountain rule (§2.1), 45 at today's draught of 15 (`world/prototypes.py:268`) — and is instant, as drinking from a vessel is. The room sees it (*kneels at the spring and drinks*). A source of brine refuses (VP5). Logged as the shipped `consume` kind with the source's key as the item and no `charges_left` (VQ9). How much one act gives is VQ8.

Drinking from a vessel is unchanged except for its kind (N3).

---

## 8. Water in crafts — registry open decision 6

**VP2 — Water is draughts, never an item.** The registry asks whether to register a *water* material or have water-using recipes require a nearby source or waterskin charges (`world/material_registry.py:503–504`). Proposed: neither a material nor a mere presence check — one rule that covers both places a crafter can be:

- A recipe declares the draughts it needs, and of what kind (fresh unless it says brine).
- **At a source** of that kind in the room, the need is met and nothing is drawn: you are at the water's edge. The room scan is the one `refill` makes; the craft command's tool lookup already searches the room as well as the inventory (`commands/crafting_commands.py:324`; ingredients are inventory-only, `:315`).
- **Elsewhere,** the draughts come out of vessels the crafter carries holding that kind, fullest first. The check runs in `pre_craft`, so the dry run refuses before the wait (`_inputs_pass`, `commands/crafting_commands.py:285`); the draughts are drawn in `post_craft`, with the consumables, so a refused or interrupted craft spends no water.
- The vessel is kept and only emptied — A Tale in the Desert's rule (§2.2). A vessel's wear comes from refilling it, as today, not from pouring it out.

**Why not a water item.** A carried water material would duplicate everything a `Drink` already holds — an amount, a container, a weight — and would let water sit in a pack without a vessel. Charges already exist (`typeclasses/consumables.py:28–57`), and every reader below wants either *at the water* or *out of a vessel*.

**Readers, none shipped:**

- **Cooking CQ14** — a stew draws its draughts, so a camp cook carries a skin or cooks by the stream.
- **Textiles WP1 — retting** is done at a source: a retting pit stands in a room with water, which is why the retting pond smells outside the village (Textiles §13).
- **Textiles WP3 — felting** wants hot water: draughts plus a lit fire in the room (Cooking CP1).
- **Textiles WP8 — the dye vat** is loaded with draughts when it is filled; a bucket is the dyer's vessel.
- **BACKLOG *Tanning upgrade*** — bark and water as `LeatherRecipe` inputs; its trigger is this decision.
- **VP5 — salt** reads the same rule with the kind *brine*.

Nothing ships with the rule alone. It ships with its first reader, whichever of these is decomposed first, and that decomposition marks registry decision 6 resolved.

---

## 9. Where water is, and what kind

**VP3 — Kinds in one word.** A source carries a kind: `fresh`, `still` or `brine` (proposed attribute `water_kind`, default `fresh`, so the shipped spring is unchanged with no migration). A vessel carries the kind of what is in it, or nothing when empty. Proposed rules:

- `refill` fills an empty vessel with the source's kind; a vessel holding another kind is refused — *empty it first* (N2).
- `empty <vessel>` pours it out on the ground; the kind clears with the last draught.
- `look` at a source names its kind in words: the shipped *clear water flows here* for fresh (`typeclasses/resources.py:135–136`), *still, greenish water* for still, a *sharp, salt smell* for brine.
- **Fresh** — springs, streams, wells, rain. **Still** — ponds and pools. Drinking still water is harmless until *Disease system* gives it a Potency (VP-L3); boiling it to fresh needs a fireproof vessel, so it waits for the kiln's pot and the fire. **Brine** — undrinkable (N3); its use is salt (VP5).
- The kind is the only quality water has. It adds nothing to a recipe's roll (§2.3).
- Later liquids — ale, milk — use the same field, so the vessel rule already covers *brewing* and *livestock* in the queue.

A fishing water is a natural water source too: Fishing Design's `FishingWater` fixture (FP5) is a `ResourceNode`, so the same fixture can carry `is_water_source` and a kind — a still pond fishes and drinks from one object.

**VP8 — Wilderness water is terrain, not objects.** Stage 6's recycled rooms must not hold fixtures (Evennia Reference §14.5), so a coordinate's water is a property of its terrain or biome, read through one helper that answers *what water is here, and what kind* — fixtures in authored rooms, terrain in the wilderness. `drink`, `refill` and VP2 read only the helper. The same answer as Fishing Design FQ5.

---

## 10. Vessels

**VP4 — A ladder of vessels, each from someone's trade.**

| Vessel | Made from | Draughts (serviceable) | Drunk from | ENC | Waits for |
|---|---|---|---|---|---|
| Waterskin (gourd) | gourd, twine | 5 (3–6 by band) | yes | 1 | shipped (`world/recipes.py:126`) |
| Leather waterskin | leather, twine | 8 (AoL's two days) | yes | 1 | nothing: leather ships (`world/recipes.py:174`) |
| Leather bucket | leather, sticks, twine | 20 | no | 2 | nothing |
| Clay jug | fired clay | 10 | yes | 2 | the kiln (registry open decision 7) |
| Barrel | planks, hoops | 100 | no — a room object | — | planks (BLOCKED on a saw, `world/material_registry.py:317`), a cooper |

- A **bucket** is carried but not drunk from: `drink bucket` is refused, and `pour bucket into skin` fills the skin. It is the dyer's, the felter's and the cook's vessel, and the vessel a well needs (VP6). Leather buckets were the old fire bucket; a wooden one follows cooperage.
- **`pour <vessel> into <vessel>`** moves draughts between two vessels of the same kind (or into an empty one); a barrel is filled and emptied this way. One command, synchronous.
- A **barrel** stands in a room (`get:false()`, as a fixture, `typeclasses/resources.py:61`): a household's store, and the cooper's product that brewing, salt fish and Textiles' dye vat also want.
- Every vessel wears on refill (VG5). The shipped waterskin counts refills in `db.durability` and splits on the dip after the last (`typeclasses/consumables.py:44–57`; `commands/foraging_commands.py:227–235`); VQ6 asks to move it onto `condition` before any new vessel copies it.
- Whether a full vessel weighs more than an empty one is VQ1; the name of AoL's leather skin beside today's gourd *waterskin* is VQ2.

---

## 11. Brine and salt

**VP5 — A brine spring gives salt.** Salt has no source today — it is not in the registry at all (saltpeter is, `world/material_registry.py:171`) — and Cooking Design asks where it comes from (CQ5). Proposed, as the first source:

- **A brine spring** is an authored source of kind `brine`: a `ResourceNode` with `is_water_source`, like the shipped spring (`world/prototypes.py:117–125`). Where it stands is a content decision (VQ10).
- **A salt pan** is a shallow, stone-lined pan built beside it from stone and clay — existing materials (`world/material_registry.py:120`, `:141`) — and fixed in its room. Brine is poured in, from a vessel or at the spring (VP2's rule with the kind *brine*).
- **It dries on the drying index.** Cooking Design proposes a global, monotone drying index on `WeatherScript` that grows only in clear weather, half in fog (CP11). The pan stores the index at filling and is done when the index has grown by a set span — about a game week of good weather. Rain or snow over an unfinished pan dilutes it: the start is pushed back (the wet index, compared on read, as CP11's rack is soaked). Read on demand; nothing ticks.
- **Salt** is a new material, one row in the registry and one in `docs/PolishedWorld_SourceSink_Ledger.md` before it ships. Its sinks are Cooking's salting (CP13), Farming's cheese (its slice 4 waits for salt) and AoL's salt tablets as a reader for heat (Cooking §15).
- **Boiling** brine down over a fire is the faster second route, once there is a fireproof pot (the kiln, or metallurgy).

Who owns salt — this design's brine, mining's rock salt or a coast's sea salt (AoL `:448`) — is VQ7, and belongs with the *Food professions* entry's single exclusives decision. Brine at a spring anyone can reach is proposed as not exclusive.

---

## 12. Wells

**VP6 — A well is sunk where the ground holds water.**

- **Where.** A room flagged as holding water underneath (proposed `db.water_table`, its value the kind a well would give). Flags are authored, as plots are (Housing Design BP4): a well cannot be sunk anywhere, and the flags say where a village can grow.
- **How.** A small building site on Housing Design's machinery: Engineering (BP1), Task Rounds (BP2), a site that shows what it still needs (BP6). Stages: dig, line with stone, set the windlass. Materials: stone, wood, twine, and a bucket hung on it. The digging tool is the decomposition's to name; nothing in the registry digs yet.
- **What it is when done.** A water source of the flagged kind, `get:false()` like any fixture, so `drink`, `refill` and VP2 read it with no new code paths.
- **It wears.** The well's parts sit on the condition axis like a house's (BP7) and wear lazily (BP12). The bucket on it wears with each draw (`apply_wear`, `typeclasses/durable.py:43`); a well whose bucket is worn through gives nothing until someone hangs a new one. That is the bucket-maker's repeat business, and the shape of the house roof's repair (BP14).
- **Whose.** A well on a plot is the plot-holder's; a well on common ground is everyone's. Who may draw from someone else's well is VQ3, beside Housing BQ2 and *settlements & commons* in the queue.

---

## 13. Rain

**VP7 — A rain catch fills from the weather, on read.** An outdoor vessel set to catch rain: a barrel (when the cooper exists) or, first, a hide-lined pit (leather and sticks).

- **It reads the wet index.** Cooking Design names a wet index on `WeatherScript`, compared on read (CP11), and CQ9 asks for one weather-history change for all such counters (spoilage, drying, Farming GP2's growing index). The catch stores the index at its last read and adds draughts for the growth since, up to its capacity. Snow counts at half.
- **Indoors catches nothing.** A room with `is_indoor` (`world/thermal.py:68`) gives a catch no rain.
- **Rain is fresh** (VQ11) — Project Zomboid's tainted rain waits for disease, like still water.
- **Weather inertia** is not needed: the index reads today's four states (`world/weather.py:23`). Droughts that empty a catch, a spring or a shallow well are VQ5, a consumer of BACKLOG *Weather inertia* part (1).

AoL's water trap — dew gathered on a tarp (`:510`) — is the same object for dry country; it is not proposed separately (§20).

---

## 14. Economy

**Sources (all natural or player-made):** springs, streams and ponds in authored rooms (natural, not NPCs — pillar 1 holds); brine springs (authored); wells (built); rain catches (built). **No one sells water** (VG1).

**Sinks:** vessel wear on every refill (shipped); bucket wear at a well; the well's parts; salt eaten or used in salting; draughts drawn by crafts (free at a source; carried water costs the vessel's wear).

**Materials this design gives a source or a sink:** leather (new sinks: the leather waterskin and the leather bucket); twine (more sinks); stone and clay (the salt pan and the well's lining — stone's sinks beyond the stone axe); pottery (the jug, once the kiln exists); planks (the barrel, once planks have a source); **salt** (a new material with a source). New rows — salt, the leather waterskin, the bucket, the jug, the barrel, the salt pan, the well, the rain catch — each need their source and sink in `docs/PolishedWorld_SourceSink_Ledger.md` before they ship. Brine and still water are kinds in a vessel, not items, and need no row.

**Services:** carrying water — to a dye works, a felter, a field camp, and in dry country to anyone; sinking a well for a neighbour; hanging a new bucket on a common well; salt-making for cooks and fishers; a cooper's barrels for a household's store.

**Exclusives:** none proposed. Salt's owner is VQ7, for the *Food professions* entry's one decision.

**Coin:** none proposed. **Logging:** drinking at a source is the shipped `consume` kind (VQ9); building a well or a salt pan is the site's and the craft's logging; `pour` and `empty` are not logged.

---

## 15. Multiplayer and server load

- **Nothing ticks.** Sources are endless (`typeclasses/resources.py:20–22`); a salt pan and a rain catch store an index and compare it on read; wells wear lazily. No new script, and two or three counters on the existing `WeatherScript` that Cooking and Farming already propose.
- **No contention for water.** Two characters drinking or refilling at one spring touch only their own vessels and gauges.
- **One writer per vessel and per object.** `pour`, `empty`, `refill` and a draw at a well are single synchronous commands under Evennia's one reactor thread — the serialisation `ResourceNode.harvest()` relies on (`typeclasses/resources.py:105–113`). A rain catch or a salt pan re-reads its index inside the command that takes from it.
- **A craft's draughts** are checked in `pre_craft` and drawn in `post_craft` inside the craft's own completion, on the crafter's single `ndb.timed_action` slot (`world/timed_actions.py:107`); a vessel emptied by its owner during the wait is caught at completion, as an ingredient given away is.
- **Room scans stay small.** `refill` already scans the room's contents for a source (`commands/foraging_commands.py:198–202`); authored rooms hold few objects, and the wilderness reads terrain instead (VP8).
- **Offline.** A statue carries its vessels unchanged; a pan or a catch keeps filling on the world's clock whoever is online.

---

## 16. Immersion extras

- **Kneeling to drink.** The room sees who drinks at the spring, and a wet sleeve or a cupped hand says how.
- **Water you can read.** Clear and cold at the spring, still and green in the pond, a white rime round the brine spring's stones.
- **The windlass.** A well creaks when someone draws, one line to the room; an untended well's rope frays in its look text.
- **Rain in the barrel.** A rain catch says how full it is in words (*a hand's depth*, *brimming*), the shipped availability phrase's shape (`typeclasses/resources.py:129`).
- **The salt pan's crust.** A pan reads *wet*, *crusting*, *white with salt* as it dries, and a wet week shows.
- **Clay and water.** The alpha's clay bank is on the brook's slope (`world/seed_data.py:119–125`); a potter works where the water is.

---

## 17. Layers — a suggested order

1. **Slice 1 (no new content):** drink at a source (VP1, N1); the kind field on sources and vessels with only *fresh* in the world, and `empty` (VP3, N2); the waterskin's move onto `condition` (VQ6).
2. **Slice 2 (leather):** the leather waterskin and the leather bucket, and `pour` (VP4). Nothing to wait for.
3. **With the first water-using craft:** VP2's rule, shipped with whichever reader is decomposed first — Cooking's stew, felting, the dye vat, tanning — and registry decision 6 marked resolved.
4. **Slice 3 (salt):** a brine spring, the salt pan and salt (VP5, N3), with Cooking's drying index (CP11) and a first reader for salt.
5. **Slice 4 (wells):** the well (VP6), with Housing's site machinery and plots.
6. **Slice 5 (rain):** the rain catch (VP7), with the wet index (Cooking CQ9) — a hide-lined pit first, the barrel when there is a cooper.
7. **Later:** the clay jug after the kiln; still water, boiling and the water additive with *Disease system* and alchemy; wilderness water with Stage 6.

**Prerequisites:** none for slices 1 and 2; a water-using recipe for VP2; Cooking's drying index and a salt reader for slice 3; Housing's site machinery and plot rules (BQ2) for slice 4; the wet index for slice 5; registry open decision 7 for the jug; planks (a saw) and a cooper for the barrel.

---

## 18. Seams in today's code (read at `2f2b02f`)

| Need | Seam | Where |
|---|---|---|
| Water source flag and endlessness | `ResourceNode.is_water_source`; `get_available` and `harvest` return early for water | `typeclasses/resources.py:20–22`, `:47`, `:99–103`, `:105–117` |
| Source wording | `_availability_phrase`, `get_display_desc` | `typeclasses/resources.py:129–136`, `:149` |
| Fixture lock | `get:false()` | `typeclasses/resources.py:61` |
| The spring | `SPRING` prototype | `world/prototypes.py:117–125` |
| Where it stands | Brook room, spring seed | `world/seed_data.py:119–125`, `:202–203` |
| Vessel typeclass | `Drink`: charges, `max_charges`, `restore_amount`, `refillable`, `refill()`, `is_worn_out()` | `typeclasses/consumables.py:28–57` |
| Drinking | `CmdDrink`; Drink-only check; restore; `consume` log | `commands/consumption_commands.py:67`, `:88`, `:100–111` |
| Refilling | `CmdRefill`; room scan; split on the dip; fill line | `commands/foraging_commands.py:178`, `:198–202`, `:227–235`, `:243` |
| Forage skips water | water sources excluded | `commands/foraging_commands.py:90` |
| Waterskin | `WaterskinRecipe`, band table; prototype (ENC 1) | `world/recipes.py:57–62`, `:126–156`; `world/prototypes.py:259–271` |
| Gourd | registry row; gourd and vine prototypes | `world/material_registry.py:99–103`; `world/prototypes.py:142`, `:168` |
| Open decision 6 | water as a crafting input | `world/material_registry.py:503–504` |
| Materials for vessels, pan and well | stone, clay, raw hide, twine, leather, planks, pottery, kiln | `world/material_registry.py:120`, `:141`, `:197`, `:245`, `:265`, `:317`, `:335`, `:418–423` |
| Leather | `LeatherRecipe` | `world/recipes.py:174` |
| Craft inputs | ingredients from inventory; tools from room and inventory; dry run | `commands/crafting_commands.py:315`, `:324`, `:285` |
| Thirst | gauge and descs; base rates; damage conditions | `typeclasses/characters.py:299–314`; `world/survival_ticker.py:21`, `:32–35` |
| Tick interval | `SURVIVAL_TICK_INTERVAL` | `server/conf/at_server_startstop.py:27` |
| Thirst modifiers | `Dehydrated`; HeatStress on `thirst_rate` | `world/survival_buffs.py:36`, `:72`, `:86` |
| Respawn | thirst reset to max | `typeclasses/characters.py:1337–1344` |
| Indoors | `is_indoor` | `world/thermal.py:68` |
| Weather | four states; `WeatherScript` interval and repeat | `world/weather.py:23–33`; `typeclasses/scripts.py:112`, `:135` |
| Wear | `apply_wear` | `typeclasses/durable.py:43` |
| Timed acts | one `ndb.timed_action`; `claim` | `world/timed_actions.py:107`, `:198` |
| Skill check | `skill_check(value, modifier)` | `world/skillcheck.py:58` |
| Wilderness recycling | what recycling does not reset | `docs/PolishedWorld_Evennia_Reference.md` §14.5 |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 19. Open questions

- **VQ1** — Does a full vessel weigh more than an empty one? *Leaning: no — ENC is fixed per vessel, as the shipped waterskin's ENC 1 is; full-and-empty weight is a second number on every vessel for little play.*
- **VQ2** — Today's gourd vessel is keyed `waterskin` (`world/prototypes.py:259–271`), while AoL's waterskin is leather (`:512`). What is the leather one called? *Leaning: keep the shipped key; the new one is the *leather waterskin*.*
- **VQ3** — Who may draw from a well on someone's plot, and is a common well possible before *settlements & commons* is designed? Beside Housing BQ2. *Open.*
- **VQ4** — Finding water in the wilderness: Legend's daily Survival test (p. 63) needs a skill, and `survival` is the gauge category's name (`typeclasses/characters.py:446`). A custom skill as `hunting` was (`:443–455`), an existing skill, or terrain alone? *Open; Stage 6.*
- **VQ5** — Droughts: once rain follows cloud (BACKLOG *Weather inertia* (1)), do rain catches, shallow wells and small springs answer a dry spell? *Leaning: catches and shallow wells yes, springs never.*
- **VQ6** — Move the waterskin's refill-count `durability` onto `condition` (BACKLOG *Waterskin `durability` → `condition` migration*) as the ladder's first task? *Leaning: yes — every new vessel would otherwise copy the divergent shape; the split on the dip after the last refill is the behaviour to keep.*
- **VQ7** — Who owns salt: brine (this design), rock salt (*mining & prospecting*), sea salt (a coast, *travel*)? For the *Food professions* entry's single exclusives decision. *Leaning: brine first, and not exclusive.*
- **VQ8** — How much does one drink at a source give, and does it take time? *Leaning: three draughts, instant (§2.1).*
- **VQ9** — Activity log for drinking at a source: the `consume` kind with the source as the item, or a field marking it? The same family as Textiles WQ8 and Hunting TQ10. *Leaning: `consume`, item = the source's key, no `charges_left`.*
- **VQ10** — Where does the first brine spring stand: an existing alpha room (the ridge) or a new one? A content decision. *Open.*
- **VQ11** — Is rain fresh, or still (Project Zomboid's tainted rain)? *Leaning: fresh — rain has nothing to carry until disease exists.*

---

## 20. Considered and not proposed

- **Water as a carried material.** Registry decision 6's first option; §8 says why not.
- **Water for sale, or a fountain in every room.** Pillar 1; the lesson of §2.1.
- **A vessel that never wears out.** §2.1; VG5.
- **Water quality as a number.** Haven & Hearth's model (§2.3); a kind in one word is enough, and it adds nothing to a roll.
- **A change to thirst's rate.** Today's 33 game hours against Legend's CON × 4 is a balance pass, not a design change (VP-L1).
- **Tainted water before disease.** A harm with no system to carry it (§2.4; VP3).
- **Plumbing and aqueducts.** Settlement-scale works; later, with *settlements & commons*.
- **Dowsing as magic.** AoL's dowsing rods focus Detect spells (`:216`); Stage 7. Wells are sited by authored flags instead (VP6).
- **The water trap and the water pack.** AoL's dew collector (`:510`) is the rain catch for dry country; the 25-litre pack (`:508`) is the bucket's volume on the back. Neither adds a rule.
- **Watering crops.** Farming Design GP2's growing index already reads the weather; irrigation waits for droughts (VQ5).
- **Washing and bathing.** *Hygiene & bathing* in the queue reads VP2 when it comes.
- **Swimming and drowning.** *Travel/roads/boats* in the queue.
