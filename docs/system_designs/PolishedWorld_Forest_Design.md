# PolishedWorld — Forest & Fuel Design Notes (fuel and burn time, green and seasoned wood, regrowth, felling, the charcoal clamp)

> **Rev 2 · 2026-11-08** — moved, docs only, with roadmap Rev 60, BACKLOG Rev 85 and README Rev 39: from `docs/` to `docs/system_designs/`, together with the fourteen other one-system design notes and the series handoff, `docs/system_designs/HANDOFF.md`. The *Canonical* line and every path to a design note outside a Rev line now name the new folder; no content changed. Rev lines keep the paths they were written with, since changelog lines are left exactly as written.
> **Rev 1 · 2026-11-08** — first version, docs only, with roadmap Rev 55, BACKLOG Rev 80 and README Rev 34. Written from a design chat, the eleventh in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`, `docs/PolishedWorld_Housing_Design.md`, `docs/PolishedWorld_Hunting_Design.md`, `docs/PolishedWorld_Cooking_Design.md`, `docs/PolishedWorld_Temperature_Design.md`, `docs/PolishedWorld_Farming_Design.md`, `docs/PolishedWorld_Textiles_Design.md`, `docs/PolishedWorld_Water_Design.md`, `docs/PolishedWorld_Foraging_Design.md` and `docs/PolishedWorld_Light_Design.md`. Wood is gathered and crafted today, and the shipped tree regrows the same in every season, so the notes name the places they would change live behaviour (§6). **Nothing here is locked.** Every numbered item is a proposal (YP…), a goal (YG…) or an open question (YQ…); the letter is *Y* for *yew*, because F, W and T are taken by Fishing, Textiles and Hunting, and the departure rows are U1–U2. In the chat Adam approved writing the document from the proposal without answering its four questions; they are recorded here as YQ1–YQ4 with the leanings recommended in the chat, recorded as *leanings*, not as decisions. The leanings under the other questions are this document's own. Prior art was read on 2026-11-08; code seams were read against `main` at `345ffb3` (Evennia 6.1.0).
> **Canonical:** `docs/system_designs/PolishedWorld_Forest_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/roadmap.md`, parallel backlog, *Forest & fuel — wood, fuel, felling, charcoal* — a new entry (Rev 55), because nothing owned the supply side of wood: the tree and the felling chain came with the alpha content epic, and the readers of wood (Cooking's fire, Temperature's warmth, Housing's frames, the torch) are each in their own design. `docs/BACKLOG.md` gains two notes (Rev 80): *Seasonal supply & population memory* — this design proposes that wood is not flat (U1, YP5); and *Metal tools + craft-station / forge* — charcoal needs no kiln (YP8), which leaves registry open decision 7 to pottery.
**When to read:** when Cooking Design's fire is decomposed (CP1, CP3, CQ8 — the fuel table is here, YP1); when Cooking CQ9's weather-history change is decomposed (seasoning reads the drying index, YP3); with *Seasonal supply & population memory* part (1) (YP5); before Housing's timber cottage is decomposed (Housing Design BP8 rung 3 — felling, YP6); at the start of the metallurgy epic (the charcoal clamp, YP8; registry open decision 7); when Farming's dung or rendering's ash is designed (YP10, YP13); with *settlements & commons* from the design-series queue (woodland rights, YQ11); when Stage 6 decomposes wilderness (forest as terrain, §14).
**Departs from shipped behaviour in two places**, listed with their source lines in §6: the shipped tree stops regrowing in winter, and a length of wood says whether it is green or seasoned.

---

## 1. The idea in one paragraph

Every fire in the world eats wood, and wood comes from somewhere. Dead branches lie under the trees for anyone to pick up, and a handful of sticks keeps a small fire going an hour; a proper fire wants lengths of wood cut with an axe, and wood cut today is green — it hisses, smokes and burns half as long as wood that has lain a month. The woods regrow while things grow: the cut stools and lopped trees put out new poles from spring to autumn, and in winter they stand bare, so the fire that warms a house in the cold months was cut and stacked in the summer. A big tree can be felled for a builder's timber; it comes down all at once and lies heavy at the feller's feet, and the stump it leaves sprouts again and is a tree after a year. A collier stacks wood under earth and lets it smoulder for a day, and opens it to find charcoal — light, smokeless, three hours of heat in a lump a pack hardly notices, the fuel that will carry fire into towns and forges far from the trees. Nobody reads a number: a stand is *thick with poles* or *cut back hard*, a log is *green* or *well seasoned*, a fire is *blazing* or *burning low*. Nothing ticks.

---

## 2. Prior art

### 2.1 Achaea — the lesson

Sources: Achaea's help file on commodities and its 2019 announcement of foragers (`achaea.com`), and the forum thread players opened on foraging a month later (`forums.achaea.com`, read 2026-11-08). Paraphrased:

- Wood and fibre used to be bought from NPC commodity shops in villages and cities. In 2019 Achaea moved both to player gathering: a player dispatches a group of foragers to an area, and they bring back what the area holds. Wood is found in wooded areas, in autumn and winter.
- A month later players reported that the wood for a season arrived all at once at its start, that every forest was empty a day or two later, and that later trips brought back little. A player listed what eats wood — a house room at two thousand wood, a ship at ten thousand, furniture at hundreds — and the market price of a unit went from a few dozen gold to several hundred. Fibre, with lower demand and two products made from it, stayed stable.
- Staff replied that their production numbers had been conservative and would be raised now that they had data. Players asked that wood appear across the whole season rather than in a burst, so that it was not the first to send who took it all.

**Worth taking:** seasonality in the supply of wood; the warning that a raw material which is the bulk input of every large sink sets the economy's pace.

**Not for PolishedWorld:** wood gathered by dispatched NPC groups (pillar 1: the labour is a player's); wood released in a seasonal burst.

**The lesson (the series' "Achaea lesson"):** wood is the bulk input of every large sink — houses, ships, furniture, fuel — so **its rate of supply is the economy's master constant**, and a rate that arrives as a burst goes to whoever moves first and leaves everyone else nothing. The rule taken: **wood grows; it is never spawned** — it regrows continuously while things grow, on the node's own anchor, so supply scales with the work of cutting up to what the woods can bear and nobody can corner a season by being early; the stock is visible in words; and the whole calibration — how much the woods give against how much a fire eats — sits in one place (YG1, YG2, YP13).

### 2.2 Wurm Online — trees with an age

Source: Wurmpedia, *Tree*, *Felled Tree*, *Age* (`wurmpedia.com`, read 2026-11-08). Paraphrased:

- A tree has an age stage, from young to overaged and shrivelled. Young trees give a small log when cut; old ones give a felled tree, a heavy trunk that is then chopped into logs.
- Sprouts are picked from a tree with a sickle and planted to make new trees; trees left to sprout seed themselves nearby.
- Woods differ: birch burns better than other wood, cedar decays more slowly, willow suits bows.

**Worth taking:** felling as a bulk yield from a mature tree; a tree that takes long to come back; planting as someone's work; species as properties later (DECISION #10).

**Not for PolishedWorld:** a simulated age per tree on every tile; felling as the main way to train a skill.

### 2.3 Vintage Story — the charcoal pit

Source: the Vintage Story wiki, *Charcoal*, *Firewood*, *Pit kiln* (`wiki.vintagestory.at`, read 2026-11-08). Paraphrased:

- Charcoal is made in a pit: stacks of firewood enclosed in an airtight shell of earth or other solid blocks, lit from a firepit on top and sealed. No built kiln is needed.
- Each full stack of firewood yields a few charcoal on average; a pit that is not sealed in time burns its wood instead.
- Firewood can be aged, and a pit kiln for pottery finishes faster on charcoal than on firewood.

**Worth taking:** charcoal from an earth-covered stack with no station — the answer to the registry's kiln question for charcoal (YP8); a ratio of several wood to one charcoal; failure as wood burnt to ash.

**Not for PolishedWorld:** the block geometry and the race to seal in thirty seconds.

### 2.4 A Tale in the Desert — the collier's art as a minigame

Source: A Wiki in the Desert, *Charcoal Hearth*, *Charcoal Oven*, *Charcoal Brazier* (`atitd.wiki`, read 2026-11-08). Paraphrased:

- The charcoal hearth is run in real time against bars for heat, oxygen, wood, water and danger. Too much heat and oxygen burns the wood up; too little and the fire goes out. Guides say it takes practice and instinct.
- A later building, the brazier, makes charcoal on its own; its bars move only for show.

**Worth taking:** charcoal as a skilled process that can fail.

**Not for PolishedWorld:** a reaction game over bars — the series' rule from Fishing is that skill lives in choices, not reaction speed; the game's own later brazier says the minigame was not the point.

### 2.5 Armageddon — fuel and kindling

Sources: Armageddon's game-discussion boards on fire-making and on pottery in the south (`gdb.armageddon.org`, read 2026-11-08). Paraphrased:

- A campfire is crafted from fuel and kindling; firewood is broken down from branches and logs; dried dung is a second fuel where wood is scarce.
- Players reasoned that where wood and dung are both dear, pottery — which needs fuel to fire — is dear too.

**Worth taking:** kindling and fuel as two things (YP2); dung as a fuel beside wood (Farming); the price of fuel carried into every craft that needs heat (YG6).

### 2.6 History — coppice and standards

Sources: a review of medieval European firewood management (`pmc.ncbi.nlm.nih.gov`), the Conservation Handbooks' history of coppicing (`conservationhandbooks.com`) and a Forestry Commission leaflet on coppice (read 2026-11-08). Paraphrased:

- Firewood in temperate Europe came mostly from coppice: trees cut to the ground regrow many poles from the stump, and the young poles could go straight on the fire. Medieval cycles were often under ten years.
- In coppice-with-standards, some trees were grown on for timber over a much longer cycle while the underwood was cut beneath them. Where animals grazed, trees were pollarded — cut above their reach — instead.
- Charcoal, tanbark and fuel for kilns kept coppice woods in use; they were not cleared for it.

**Worth taking:** two kinds of tree — underwood cut often for fuel and standards felled seldom for timber (YP4); the shipped tree's lopped limbs as a pollard; a wood that is used rather than destroyed.

---

## 3. Design goals

- **YG1 — Wood grows; it is never spawned.** Regrowth is continuous while things grow, on each node's own anchor, never a burst at a season's start (§2.1).
- **YG2 — One calibration, in one place.** What the woods give and what a fire eats are set in one table, so the master constant can be tuned once (YP1, YP13).
- **YG3 — Working ahead pays.** Seasoned wood burns longer than green; winter's fire is cut in summer. The woodpile is stock, and stock is worth money.
- **YG4 — The free fuel never runs out.** Deadfall regrows in every season, so anyone can keep a small fire; the cold is never a wall for the poor (Temperature's rule that every harm has an answer within reach).
- **YG5 — Nothing ticks.** Regrowth, seasoning, a clamp's burn are read from stamps and indexes, never written by a script per object.
- **YG6 — Heat costs fuel.** Every fire, clamp, kiln and forge burns something someone gathered (Light LG1's rule for light, here for heat).

---

## 4. Legend alignment

**Rules as written:**

- **No forestry skill.** The core has no woodcutting or charcoal-burning skill. The **Woodsman** profession (core p. 23) bundles Athletics +10 %, Axe +10 %, Brawn +10 %, Lore (Regional) +5 % and Resilience +5 % among its common skills and opens Survival as its Advanced Skill: cutting wood is a life, not a test.
- **Inanimate objects** — p. 91: objects have Armour and Hit Points, and attacks on them hit automatically — only the damage is worked out. p. 92: a weapon used on an object as hard as itself is damaged too; tools made for the work are not.
- **Hatchet** — p. 103: a cheap cleaving tool that cuts wooden objects with no risk to its edge. **Hand saw** — p. 118: cuts wood at 1D4 Hit Points per round, ignoring the wooden object's Armour Points.
- **Fire** — p. 83, Fire and Heat: a camp or cooking fire is a *small fire*, 1D6 per round to anyone in it; a large bonfire a *large fire*, 2D6.
- **Craft** — p. 57: the listed crafts include carpenter, cooper, joiner and bowyer; none burns charcoal or cuts wood. Craft (Any) covers the rest.
- **Survival** — p. 63: a daily test when an Adventurer lacks food, water or a safe place to sleep; not used in towns.
- **Arms of Legend** (`docs/reference/arms_of_legend.md`): flint and tinder build a fire in a minute without a Survival roll under common conditions, with penalties in high wind, driving rain or *without the best fire-making kindling or wood* (`:262`); the fire seed, a ceramic pot that keeps one coal from last night's fire alive for up to three days and is put out by a wetting (`:244–248`); the hand saw (`:432`); the hatchet (`:1593`); the carpenter (`:2982`); alchemists' furnaces fired by charcoal, coal or wood (`:3669`).

**Translation proposals:**

- **YP-L1 — Cutting wood is time, not a test.** Inanimate objects are hit automatically (p. 91), so a cut always succeeds; the tool decides how long it takes. No roll to lop, cut or fell, as `forage` has none (`commands/foraging_commands.py:54`).
- **YP-L2 — The tool tier is speed.** The stone axe is a hatchet's equal for this (p. 103); a metal axe is faster and the saw (p. 118) faster again, when smithing gives them. Wear stays light: p. 103 says a hatchet's edge takes no harm from wood (YQ7).
- **YP-L3 — No woodcutting skill.** The Woodsman is a profession bundle (p. 23), and the codebase's skills are five (`world/chargen.py:59–65`). Felling waits on no new skill; the clamp is `craft` (YQ3).
- **YP-L4 — Poor wood is AoL's poor kindling.** `:262`'s penalty for poor wood becomes green wood's short burn and harder lighting (YP3); it is Light LP7's `kindle`, unchanged.
- **YP-L5 — Hours are game hours.** As Light LP-L3: burn times are in game hours, a quarter of a real hour each at the 4× clock (`server/conf/settings.py:50–64`).
- **YP-L6 — Fire damage waits for Stage 5.** Standing in a fire or a clamp is p. 83's and combat's; nothing here harms.
- **YP-L7 — Legend's prices are not used.** Pillar 1.

---

## 5. The loop

Proposed phases; each is something someone can sell.

1. **Gather small.** Sticks from deadfall, by hand, in any season (shipped).
2. **Cut.** Lengths of wood from a lopped tree or a coppice stand, with an axe (shipped `forage`; regrowth YP5).
3. **Fell.** A standard comes down all at once for a builder (YP6); its bark goes to the tanner (YP7).
4. **Carry.** Wood is heavy (ENC 1 a length); someone hauls it to where the fire is.
5. **Stack and season.** Green wood lies until it is seasoned (YP3).
6. **Burn.** Kindling, then fuel; a fire fed through a night (YP1, YP2; Cooking CP1, CP3).
7. **Char.** Wood into charcoal in a clamp, for heat far from the trees (YP8, YP9).

---

## 6. Departures from shipped behaviour

Each row is a change to behaviour that `main` has today; each is a proposal.

| # | Shipped today | Proposed | Where shipped |
|---|---|---|---|
| U1 | The tree regrows one length per 7200 game-seconds in every season, up to three | It regrows on Farming's growing index (GP2): full in spring and summer, half in autumn, nothing in winter; the anchor still advances by whole intervals, so `available` stays monotone (YP5). Deadfall is unchanged (YG4) | `world/prototypes.py:396–411`; `typeclasses/resources.py:67–97` |
| U2 | A length of wood looks the same however long ago it was cut | Its look says *green* or *seasoned*, read from a stamp set when it is cut; a length with no stamp reads *seasoned* (YP3) | `world/prototypes.py:384–394`; the spawn in `commands/foraging_commands.py:133` |

Unchanged: `forage`, its tool check and the axe's wear (`commands/foraging_commands.py:54`, `:110–122`, `:151`); deadfall and every other shipped node; every recipe that consumes wood (`world/recipes.py:438`, `:450`, `:462`, `:491`, `:597`); the weight of wood (ENC 1); `thermal_regime()` (`world/thermal.py:46–80`).

---

## 7. Fuel

**YP1 — Fuel is time per piece (Cooking CQ8).** A fire is Cooking CP1's object with `burns_until`; feeding it pushes `burns_until` out by the piece's span, up to a cap. Leanings, in game hours (YP-L5):

| Fuel | Burns | Notes | Status |
|---|---|---|---|
| **stick** | ¼ h | kindling; a small fire of sticks alone is possible | shipped (`world/prototypes.py:203–214`) |
| **wood, green** | 1 h | smokes; hard to light without kindling (YP3) | shipped wood, stamped (U2) |
| **wood, seasoned** | 2 h | the ordinary fuel | shipped wood, aged (YP3) |
| **charcoal** | 3 h | no smoke; light to carry (YP9) | BLOCKED → the clamp (YP8) |
| later: dung cake, peat | 1 h; 2 h | dung from Farming GP12; peat needs bog ground and a spade | Farming §13; digging & earthworks |

**The cap is one night (YQ6).** A fire holds at most eight game hours of fuel, so a sleeper can bank it at dusk and wake to embers (Cooking CP12's banked fire; *rest, sleep & camp* in the queue). The night is 20–04, eight game hours (`world/gametime_utils.py:46–54`).

**YP2 — Kindling, then fuel (YQ4).** `build fire` takes one stick as kindling beside its wood — a refinement of Cooking CP1, which names wood only — and Light LP7's `kindle` lights it with fibre as tinder. A fire of sticks alone needs no wood: the poor man's fire (YG4). Sticks are free and plentiful, so the step costs a walk, not a market.

**YP3 — Green and seasoned (U2).** A length of wood is stamped when it is cut with the value of Cooking's **drying index** (CP11) — the global counter on `WeatherScript` that grows in clear weather and half in fog — and reads *seasoned* once the index has moved on by a span worth about a game month of fair weather (YQ5). Green wood burns half as long (YP1) and gives the fire's smoke line its thick word (Cooking CP2); a fire built of green wood without a stick of kindling will not catch (AoL `:262`; YP-L4). A length with no stamp — every length in the world before this ships — reads seasoned, so nothing is migrated. If the drying index has not shipped when this does, the stamp is absolute game time and the span is a game month; the switch to the index is one function body. Seasoning ignores statues: it is a gain, not a loss, and Cooking's rule is that nothing is *lost* while a player is away (Cooking §9).

---

## 8. Where wood comes from

**YP4 — Three kinds of source.**

- **Deadfall** — the shipped node (`world/prototypes.py:232–245`): sticks, by hand, flat in every season (YG4). Storms bring branches down in winter too.
- **Lopped and coppiced wood** — the shipped tree is already this: its lower limbs are cut and grow again, which is a pollard (`world/prototypes.py:396–411`, *"its lower limbs within reach of an axe"*). New **coppice stands** — stools of hazel or ash cut to the ground — are the same node shape with a different description and yield: lengths of wood, with an axe, regrowing on the growing index (YP5). The fuel source.
- **Standards** — mature trees grown on for timber, felled whole with `fell` (YP6). The builder's source.

**YP5 — Regrowth reads the growing index (U1).** A lopped tree and a coppice stand advance their regeneration by Farming's growing index (GP2), not by raw game-seconds: full in spring and summer, half in autumn, nothing in winter. This is *Seasonal supply & population memory* part (1)'s question answered for wood, and it departs from that entry's leaning that wood is flat; flint and clay stay flat, and so does deadfall. The node keeps its own shape — the anchor advances by whole intervals of index, so a season's change re-prices only time not yet counted and `available` is monotone (`typeclasses/resources.py:67–97`). Regrowth is continuous through the growing season, never a burst (YG1). The calibration this sets is in YP13.

**YP6 — Felling a standard.** `fell <tree>` with an axe is a timed act on the shared slot (`world/timed_actions.py:107`, `claim` `:198`) — a few real minutes with a stone axe, less with a metal one (YP-L2) — with no roll (YP-L1). At its end the standard comes down: a bulk yield of wood (leaning: eight lengths) lands at the feller's feet through `receive_or_set_down` (`typeclasses/characters.py:1624`), because no one carries eight at once without a pack, and the node becomes a **stump**. A stump is a coppice stool: it gives a small trickle of wood on the growing index, and after about a game year of growing it is a standard again (YQ8). The neighbouring rooms hear it fall, read from the exits like Cooking CP2's smoke. The axe wears once for the act, not per length (YQ7).

**YP7 — Bark from a felled oak.** A felled standard that is an oak gives oak bark to a knife as a second yield (`world/material_registry.py:114–118`), Foraging RP14's tree-and-knife source for BACKLOG *Tanning upgrade*. While DECISION #10 keeps one `wood` tag, *oak* is the standard's description and its bark, not a kind of wood.

---

## 9. Charcoal

**YP8 — The clamp, not the kiln.** Charcoal needs no station (§2.3): wood is stacked, covered with turf and earth, and lit, and it smoulders. Proposed: `build clamp` in an outdoor authored room takes a stack of wood (leaning: six lengths, green or seasoned) and makes a **clamp** object; `kindle` lights it like a fire; it then burns for a span (leaning: one game day, six real hours) stored as `done_at`, read on look — *smoke seeps from the mound*, then *the mound has gone cold* — and the neighbouring rooms see its smoke (Cooking CP2). Rain does not reach it under its earth. `open clamp` after `done_at` rolls `craft` (YQ3) and yields charcoal by result — leaning: two lumps on a success, three on a critical, one on a failure, none on a fumble, which leaves ash; opening it early lets the air in and burns it all to ash (YQ10). There is no tending in v1: the collier's skill is in the roll and the choice of when to open, not in watching bars (§2.4; YQ9). Six lengths to two lumps is the System Backlog's three to one; Vintage Story's ratio is higher, and the number is tuning (YQ9).

This answers half of registry open decision 7 (`world/material_registry.py:505`): **charcoal needs no kiln**, so the kiln is pottery's — and lime's and the fire seed's (AoL `:244–248`) — and the registry's `blocked_on` for charcoal (`:281–286`) becomes *a clamp*. The metallurgy epic's decomposition records it (BACKLOG *Metal tools + craft-station / forge*). Light LQ14's leaning — a spent torch leaves no stub — stands; its "charcoal comes from kilns" reads *from a clamp*.

**YP9 — Charcoal is wood made to travel.** A lump burns three game hours with no smoke (YP1) and is light: ENC 0, counted twenty to one by the weight mechanic (`world/encumbrance.py:50`). Three lengths of seasoned wood weigh three and burn six hours; the charcoal made from them weighs nearly nothing and burns six as well. That is why charcoal was made in the woods and carried to towns, and why it matters only where distance does: a forge, a kiln, a town far from the trees, a boat. It ships with the metallurgy epic's first slice, its largest consumer (smelting and smithing fuel, `world/material_registry.py:281–286`; YQ14), not before: in a six-room alpha the trees are next door, and a source is not shipped before its sink (roadmap (D2)).

---

## 10. What a fire leaves

**YP10 — Ash.** A fire that burns out leaves ash, a pile in the room that can be gathered. `plant_ash` is in the registry's unratified list (`world/material_registry.py:479`), and it is not ratified here: it gets its row when its first sink ships — lye for soap and leather in *rendering, tallow, ash & lye*, or a fourth restorer of field fertility beside dung, bonemeal and saltpeter in Farming GP5. Until then a burnt-out fire leaves nothing but a word (*cold ashes*).

---

## 11. Signs and reading the woods

**YP11 — A stand says how it stands.** The shipped availability phrase (`typeclasses/resources.py:129`) already turns a node's stock into words with no number and no write. A coppice stand and a lopped tree add a season word read from the growing index — *bare stools under the snow*, *new poles thick on the stools* — so a player sees why there is nothing to cut in winter. A stump reads as a stump, and *sprouting* once it gives again. Reading regrowth with skill — *this stand was cut hard this season* — is *Seasonal supply*'s part (3) for trees, with Foraging RP2's rule for plants.

---

## 12. Offline and the world

**YP12 — Nothing waits on the cutter.** Regrowth is the node's (read on `forage` or `look`); seasoning is the wood's (read on look or when fed to a fire); a clamp's burn is its `done_at`. A statue carries wood that seasons as everyone's does (YP3). A clamp lit before its collier logs out finishes on time and waits, cold, to be opened — by whom is YQ3's question. A wilderness clamp or fire is Stage 6's: no persistent objects there (Evennia Reference §14.5–§14.6).

---

## 13. Economy

**Sources (all natural or player-made):** sticks from deadfall (shipped); wood from lopped trees, coppice stands and felled standards; oak bark from felled oaks; charcoal from clamps; ash from fires, when ratified.

**Sinks:** every fire (Cooking CP1, CP3 — the largest sink for wood, larger in winter, Temperature KP8); charcoal (three lengths to one lump); building (Housing BP8, by the frame); every wood recipe (shipped); the axe's wear per cut and per felling; a felled standard gone for a year (a sink of the world's stock, not of an item); green wood's lost hours when burnt unseasoned.

**Materials this design gives a source or a sink:** **wood** (its largest sink, and its supply made seasonal); **stick** (kindling at every fire); **oak bark** (a source, Foraging RP14); **charcoal** (a source, unblocking the registry row with metallurgy); **plant ash** (a source, waiting on a sink). The clamp and the standards are added by the decompositions that ship them, with sources and sinks, as the registry requires.

**Services:** cutting and hauling wood — the classic bulk good, cheap where it grows and dear where it is burned, which is what weight was made a prerequisite for (roadmap (E)); keeping a woodpile seasoned and selling it in winter; felling for builders; charcoal-burning for smiths; keeping a hall's fire through the night.

**Exclusives:** none proposed. Wood is not a food product; the food professions' exclusives decision is not touched.

**Coin:** none. **Logging:** felling, a clamp opened and fuel burned are YQ13.

**YP13 — The master constant, on one page (YG2).** At today's numbers: a lopped tree gives twelve lengths per game day in the growing season (`world/prototypes.py:405–410`: three, one per 7200 game-seconds) — half that in autumn, none in winter (YP5); deadfall gives forty-eight sticks per game day in every season (`:241–244`); a fire fed day and night eats twelve seasoned lengths or forty-eight sticks per game day (YP1). So **one tree keeps one fire alive** while it grows, and deadfall alone keeps one at the stick rate. Winter, three game months (21 real days, `world/gametime_utils.py:56–61`), runs on the woodpile and on sticks. Every number here is a leaning and moves together; the decomposition tunes this table, not the nodes one by one.

---

## 14. Multiplayer and server load

- **Nothing ticks.** Regrowth is read on harvest and look (`typeclasses/resources.py:67–97`, `:105–123`); seasoning is a subtraction of two index values; the clamp is a timestamp. The growing and drying indexes are counters on the one `WeatherScript` that already wakes every 1800 s (`typeclasses/scripts.py:135`).
- **Two cutters, one stand.** `harvest()` is a synchronous read-modify-write, serialised by the reactor (`typeclasses/resources.py:105`); unchanged.
- **Two fellers, one tree.** Felling claims each feller's own slot; the tree's state is checked and changed at the act's end in one step, as Housing's shared site stock is (Housing §12): the second feller finds a stump and is told so, and their axe does not wear.
- **One clamp, one opening.** `open clamp` checks `done_at`, rolls, spawns and deletes the clamp in one command; a second opener finds it gone.
- **Wilderness.** Forest is terrain there, not nodes — the same answer as Water VP8, Fishing FQ5 and Foraging RP13 — and Stage 6's (Evennia Reference §14.6).

---

## 15. Immersion extras

- **A tree falls.** *Somewhere to the north a tree comes down with a long crack and a crash*, to the rooms beside it.
- **The collier's smoke.** A thin blue smoke over the woods for a day, seen from the next room.
- **Winter felling.** Woodsmen fell in winter, when the sap is down and there is nothing else to do; a standard's description can say so, and winter is a season with work in it.
- **The woodpile.** A stack of seasoned wood against a house wall, a Housing part (BP7) when parts are decomposed.
- **The fire seed.** A clay pot that carries a coal from last night's fire (AoL `:244–248`), when the kiln makes clay pots: lighting with no kindling and no flame.
- **Woods that burn differently.** Birch burns bright (§2.2), and Cooking §15's woods that taste, once DECISION #10's revisit distinguishes species.

---

## 16. Layers — a suggested order

1. **Slice 1, with Cooking's fire (Cooking slice 1):** the fuel table and the cap (YP1); kindling (YP2); green and seasoned (YP3, U2) on the drying index if Cooking CQ9 has shipped, on game time otherwise.
2. **Slice 2, with *Seasonal supply* part (1):** regrowth on the growing index (YP5, U1); one coppice stand seeded beside the shipped tree; the season words (YP11).
3. **Slice 3, before Housing's timber cottage:** standards, `fell`, the stump that coppices (YP6); oak bark (YP7).
4. **Slice 4, with the metallurgy epic's first slice:** the clamp and charcoal (YP8, YP9); registry open decision 7 left to pottery.
5. **Later:** ash, with its first sink (YP10); dung cakes with Farming's pen; peat with bog ground and a spade (*digging & earthworks*); species (DECISION #10); planting new stands (YQ12); woodland rights (YQ11); forest as wilderness terrain (Stage 6).

**Prerequisites:** slice 1 needs Cooking's fire; slice 2 needs the growing index (Farming GP2); slice 3 needs nothing new beyond the timed-action slot; slice 4 needs a consumer.

---

## 17. Seams in today's code (read at `345ffb3`)

| Need | Seam | Where |
|---|---|---|
| The tree | ash tree node, axe required, 3 lengths, 7200 game-s each | `world/prototypes.py:396–411`; seeded `world/seed_data.py:206–207` |
| Wood | `length of wood`, green timber, tag `wood`, ENC 1 | `world/prototypes.py:384–394` |
| Sticks | deadfall node, 6, 1800 game-s; the stick, ENC 0 | `world/prototypes.py:232–245`, `:203–214` |
| The axe | stone axe, a `Tool`, condition 40, re-hafted with stick and twine | `world/prototypes.py:363–382`; `typeclasses/tools.py:34` |
| Forage | tool check; claim; spawn; set down; wear | `commands/foraging_commands.py:110–122`, `:133`, `:142`, `:151`; `FORAGE_TOOL_WEAR` `:28` |
| Node regrowth | `_update_regen`, anchor by whole intervals; `harvest`; availability phrase | `typeclasses/resources.py:67–97`, `:105–123`, `:129` |
| Wood consumers | quarterstaff, spear, bow, tent, club | `world/recipes.py:438`, `:450`, `:462`, `:491`, `:597` |
| Registry | wood; oak bark; charcoal BLOCKED; axe; saw; kiln; forbidden variants; unratified list; open decisions 7 and 10 | `world/material_registry.py:104–113`, `:114–118`, `:281–286`, `:390–396`, `:397–401`, `:418–423`, `:453–465`, `:478–483`, `:505`, `:509–511` |
| Weight | small items twenty to one ENC | `world/encumbrance.py:50` |
| Set down | `receive_or_set_down` | `typeclasses/characters.py:1624` |
| Timed acts | one `ndb.timed_action`; `claim` | `world/timed_actions.py:107`, `:198` |
| Seasons and periods | winter months 11–13; night 20–04 | `world/gametime_utils.py:56–61`, `:46–54` |
| Weather script | wakes every 1800 s | `typeclasses/scripts.py:112`, `:135` |
| Statues | logged-out character as stone | `typeclasses/characters.py:472` |
| Clock | 4× speed | `server/conf/settings.py:50–64` |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **YQ1** — Does wood regrow at all in winter? *Leaning (chat, 2026-11-08): no — the growing index gives nothing in winter (YP5); deadfall stays flat, so there is always a poor man's fuel (YG4).*
- **YQ2** — Does building timber need a tag of its own beside `wood`? *Leaning (chat, 2026-11-08): no — DECISION #10's generic `wood` holds until carpentry; `timber` and `log` are forbidden variants of `wood` today (`world/material_registry.py:453`).*
- **YQ3** — Which skill rolls the clamp, and who owns it while it burns? *Leaning (chat, 2026-11-08): `craft`, rolled when the clamp is opened; it belongs to whoever lit it (a stamp on the clamp), and taking another's charcoal is law & crime's question, not this design's.*
- **YQ4** — Does `build fire` need a stick as kindling beside its wood? *Leaning (chat, 2026-11-08): yes (YP2).*
- **YQ5** — How long does seasoning take, and does cover matter? *Leaning: about a game month of fair weather on the drying index; cover does not matter in v1 — a woodshed is a later nicety, with Housing's parts.*
- **YQ6** — The fire's cap. *Leaning: one night, eight game hours (YP1).*
- **YQ7** — Felling: how long, how much, how much wear? *Leaning: a few real minutes with a stone axe; eight lengths; the axe wears once for the act by the shipped `FORAGE_TOOL_WEAR` doubled (Legend p. 103: wood spares an edge).*
- **YQ8** — How long until a stump is a standard again? *Leaning: one game year of the growing index — about three real months.*
- **YQ9** — The clamp's ratio, burn and tending. *Leaning: six lengths to two lumps, one game day, no tending in v1; a `tend` that raises the yield is a later thought, and never a timing game (§2.4).*
- **YQ10** — Does opening a clamp early ruin it? *Leaning: yes, to ash (§2.3).*
- **YQ11** — Woodland rights: who may cut a stand or fell a standard on land someone holds? *Open — with *settlements & commons* (Housing BQ2, Farming GQ4). In the alpha, anyone.*
- **YQ12** — Planting new stands: who makes a coppice or a standard where there was none (Wurm's sprouts, §2.2)? *Leaning: later, with settlements; authored rooms only.*
- **YQ13** — Activity-log kinds for felling, opening a clamp and burning fuel: new kinds or fields on existing ones? The family of Hunting TQ10, Textiles WQ8, Farming GQ6, Fishing FQ6, Water VQ9, Foraging RQ11 and Light LQ12. *Open.*
- **YQ14** — Charcoal before metallurgy? *Leaning: no — it ships with its largest consumer (YP9).*
- **YQ15** — Registry open decision 7 once charcoal needs no kiln. *Leaning: the kiln is pottery's (and lime's) alone; the metallurgy decomposition records it.*
- **YQ16** — A profession that grants the clamp (a collier), or a recipe anyone learns from a scroll or a teacher? *Open — as every gated recipe must have a source (`tests/test_recipe_sources.py`).*

---

## 19. Considered and not proposed

- **Wood released in a seasonal burst.** Achaea's foragers (§2.1; YG1).
- **NPC woodcutters or dispatched gatherers.** Pillar 1 (§2.1).
- **A charcoal minigame.** A Tale in the Desert's bars (§2.4).
- **An age per tree on every tile.** Wurm's simulation (§2.2); a stand has stock and a stump has a span, and that is enough.
- **A woodcutting skill.** Legend has none (YP-L3).
- **Wood bought from an NPC.** Pillar 1.
- **Separate tags for log, firewood and timber now.** DECISION #10 (YQ2).
- **A falling tree that hurts the feller.** Harm is Stage 5's (YP-L6).
- **Wildfire.** *Natural hazards* in the queue.
- **A felled forest that never comes back.** Coppice woods were used, not cleared (§2.6); every stump regrows.
