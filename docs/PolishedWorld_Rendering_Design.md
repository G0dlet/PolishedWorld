# PolishedWorld — Rendering, Tallow, Ash & Lye Design Notes (fat from larger animals, rendering, tallow and what it makes, ash, lye, soap waiting for its consumer)

> **Rev 1 · 2026-11-08** — first version, docs only, with roadmap Rev 56, BACKLOG Rev 81 and README Rev 35. Written from a design chat, the twelfth in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`, `docs/PolishedWorld_Housing_Design.md`, `docs/PolishedWorld_Hunting_Design.md`, `docs/PolishedWorld_Cooking_Design.md`, `docs/PolishedWorld_Temperature_Design.md`, `docs/PolishedWorld_Farming_Design.md`, `docs/PolishedWorld_Textiles_Design.md`, `docs/PolishedWorld_Water_Design.md`, `docs/PolishedWorld_Foraging_Design.md`, `docs/PolishedWorld_Light_Design.md` and `docs/PolishedWorld_Forest_Design.md`. Nothing in this chain exists in the code: no carcass yields fat, no fire burns, and tallow and ash sit in the registry's unratified list. So nothing here changes live behaviour and there is no departures table. **Nothing here is locked.** Every numbered item is a proposal (ZP…), a goal (ZG…) or an open question (ZQ…); the letter is *Z*, the first free letter that reads as nothing else in the series or the engine, as the chat proposed. In the chat Adam approved writing the document from the proposal and asked that the chat's questions go into it with their leanings; they are recorded here as ZQ1–ZQ4 with the leanings recommended in the chat, recorded as *leanings*, not as decisions (the chat's fifth question, the prefix, is answered by this document's use of *Z*). The leanings under the other questions are this document's own. Prior art was read on 2026-11-08; code seams were read against `main` at `50776a7` (Evennia 6.1.0).
> **Canonical:** `docs/PolishedWorld_Rendering_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/roadmap.md`, parallel backlog, *Rendering, tallow, ash & lye* — a new entry (Rev 56), because nothing owned the chain: tallow's consumers are in Light Design (the candle and the torch, LP5), ash's source is in Forest Design (YP10), lye's first reader is a BACKLOG entry, and the fat they all start from has no source at all. `docs/BACKLOG.md` gains two notes (Rev 81): *Light & darkness* — tallow gets a proposed source, fat from larger animals rendered at a fire (ZP1–ZP4); and *Tanning upgrade — bark and water as `LeatherRecipe` inputs* — lye is proposed as a third, optional input (ZP11).
**When to read:** when Hunting Design's slice 3 brings the deer (fat as a harvest part, ZP1, ZP2); when Light Design's candle or torch is decomposed (tallow, LP5; ZP5); when Cooking's fire and the kiln's pot both exist (rendering, ZP3; registry open decision 7); when Cooking's drying rack ships (pemmican, ZP6); when BACKLOG *Tanning upgrade* or registry open decision 6 is picked up (lye, ZP10, ZP11; Water VP2); when Farming's herd is decomposed (fat from livestock, ZP2; potash, ZP13); with *hygiene & bathing* or the roadmap's *Disease system* (soap, ZP12); with *litter, abandoned goods & salvage rights* from the design-series queue (ash piles, ZP9); at the food-professions exclusives decision (ZP16).

---

## 1. The idea in one paragraph

A rabbit is meat, skin and bone; a stag in autumn carries a layer of white fat under its hide, and so does a pig at slaughter time. Fat cut from a carcass goes off as fast as the meat, so whoever has it takes it to a fire the same day and melts it down in a pot: the clear tallow is poured off and keeps for as long as anyone needs it, and the crisp scraps left in the pot are eaten on the spot. Tallow is the winter's light — candles stood in a window through the long nights — and the binder that makes a torch burn an hour instead of a few minutes, and the fat that turns dried meat into food a traveller can carry for a season. Every fire that burns out leaves ash; in the dry it can be swept up, in the rain it washes into the ground. Water run through ash comes out as lye, which strips the hair from a hide and makes better leather, and which one day, boiled with tallow, will make soap — when there is a reason to wash. Autumn's fat is winter's light, and the fire that rendered it leaves the ash for the tanner. Nobody reads a number: fat is *thick* or *thin* on a carcass, tallow is a *cake*, ash is *a grey drift* or *sodden*. Nothing ticks.

---

## 2. Prior art

### 2.1 Dwarf Fortress — the lesson

Sources: the Dwarf Fortress wiki's pages on soap for several game versions (*23a:Soap*, *40d:Soap*, *v0.31:Soap*, *DF2014:Soap*) and on the soap industry (*40d:Soap industry*) (`dwarffortresswiki.org`, read 2026-11-08). Paraphrased:

- Soap is made from lye and tallow. Lye comes from ash run through an ashery, and the ash from wood burnt in a furnace; tallow is fat from a butchered animal, rendered in a kitchen. It is a chain of four or more workshops and as many labours.
- In the early versions soap had no use but as a trade good. The wiki of the next version says plainly that the long chain, the labour, the wood burnt for ash and the scarcity of tallow led most players to ignore soap and sell easier goods instead.
- Later versions tied soap to health: a dwarf washes with it, dirt raises the chance that a wound turns infected, and hospitals use soap to clean wounds. From then on the same wiki calls soap essential to health care, and players asked one another how to make it because their dwarves were dying of infection.

**Worth taking:** the chain itself — fat rendered to tallow, ash leached to lye, the two together making soap — and its two halves, one from the butcher and one from the fire.

**Not for PolishedWorld:** a separate workshop per step; soap as a trade good with no use.

**The lesson (the series' "Achaea lesson" — Achaea has none for this system, so the slot goes to the lineage that has one):** a product at the end of a long chain, with no consumer that matters, is skipped — players do not make it, however complete the chain. The same chain became an industry the day its end product kept people alive. The rule taken: **every link in this chain ships with a consumer that bites, or it does not ship** (ZG1). Tallow ships with the candle; lye ships with the tanner; soap is designed here and waits for a reason to wash (ZP12). This is Forest YP10's rule for ash, applied to the whole chain.

### 2.2 Vintage Story — rendering is preservation

Source: the Vintage Story wiki, *Fat* (`wiki.vintagestory.at`, read 2026-11-08). Paraphrased:

- Fat is cut with a knife from medium and large animals — foxes, wild pigs, sheep, wolves, bears — never from small ones.
- Raw fat has a fresh time and spoils. Heated in a cooking pot it becomes rendered fat, which does not spoil and is the form crafting uses.
- Rendered fat seals a storage crock to keep meals fresh, burns briefly as fuel, and is an input to oiled hide, some machine parts and, optionally, the longbow and the oil lamp.

**Worth taking:** fat from larger animals only (ZP1); raw fat that rots and rendered fat that keeps — rendering as a preservation step (ZG2, ZP3, ZP4); the pot as the rendering vessel (ZQ1).

**Not for PolishedWorld:** fat bought from and sold to NPC traders (pillar 1); fat as a fuel beside wood (Forest YP1's table stays wood's).

### 2.3 Wurm Online — ash and lye

Source: Wurmpedia, *Ash*, *Lye*, *Leather* (`wurmpedia.com`, read 2026-11-08). Paraphrased:

- Ash comes from a burnt-out campfire or a charcoal pile.
- Lye is made by mixing ash into a container of water; the whole of the water in the container becomes lye, and ash is used up at a fixed ratio to the water. Lye's quality is capped by the ash's and moved by a skill check.
- Lye turns hide into leather; a small amount treats a much larger weight of hide.

**Worth taking:** ash from a fire that has burnt out (Forest YP10; ZP8); lye made *in the vessel* — the water becomes lye, a change of kind on Water VP3's field, not a new item (ZP10); lye's first use as the tanner's (ZP11).

**Not for PolishedWorld:** a quality on lye (Water VP3: the kind is the only quality a liquid has); lye made mandatory for leather (no shipped recipe loses its source, ZG6).

### 2.4 History — butchering time and the ash hopper

Sources: a frontier-history blog quoting Laura Ingalls Wilder on candle-making at the end of butchering (`frontierlife.net`); the US National Park Service's teaching page on a fort laundress's soap (`nps.gov`); a homesteading article on leaching lye from hardwood ash (`motherearthnews.com`); a permaculture forum thread on soap-making (`permies.com`) (read 2026-11-08). Paraphrased:

- Candle-making came at the end of the autumn slaughter: the kettles were filled with beef fat, and the tallow melted from it was poured into candle moulds for the winter.
- Lye was leached by running water slowly through hardwood ash in a barrel or hopper; it took hours. Ash had to be kept dry until then, because rain leaches the lye out of it.
- Soap was boiled from lye and grease or tallow, a rule of thumb being a couple of pounds of fat to a gallon of lye water. Rendering and soap-boiling stank, which is why the trades were kept to the downwind edge of a town.

**Worth taking:** autumn's slaughter as the season of rendering and winter as the season of its light (ZG3, ZP2); ash that must stay dry (ZP9); the smell of the trade (§15).

---

## 3. Design goals

- **ZG1 — Every link ships with a consumer that bites.** Fat ships with rendering and the candle; ash with lye; lye with the tanner; soap waits (§2.1).
- **ZG2 — Rendering is preservation.** The step turns a byproduct that rots in a day into stock that keeps, so a hunter's surplus becomes something to sell next month (§2.2).
- **ZG3 — Fat follows the year.** An animal is fat in autumn and lean after winter; the season the fat comes in is the season before the light is needed (§2.4; Light LP2's long nights).
- **ZG4 — Nothing ticks.** Fat spoils on Cooking's index; tallow keeps; an ash pile is read, not watched (Forest YG5).
- **ZG5 — One calibration in one place.** What an animal gives and how many hours of light it makes are set in one table (ZP15).
- **ZG6 — No shipped recipe loses a source.** Where this chain touches a shipped recipe, its input is optional (Farming GQ2's leaning, here for leather).

---

## 4. Legend alignment

**Rules as written:**

- **Craft** — p. 57: the list of crafts includes butcher, candlemaker and cook; it names no renderer or soap-boiler, and Craft (Any) covers the rest. p. 58: a critical makes an item superior in durability, value or utility.
- **Automatic success** — p. 42: the automatic success and failure rules do not apply where the Games Master rules that no test is required.
- **Candle** — p. 112: a small candle that burns for one hour, first used by miners to mark the passage of time underground.
- **Weapon oil** — p. 117: a thin oil made mostly from the rendered fat and oils of fish or whales, which keeps rust off a blade.
- **Monsters of Legend** (book 1): **deer** — p. 109, the stag at SIZ 3D6+12 and does at SIZ 3D6+9; **boar** — p. 106, SIZ 2D6+3; **cattle** — p. 107, SIZ 2D6+9; **brown bear** — p. 104, SIZ 3D6+15. No rabbit or hare is statted.
- **Arms of Legend** (`docs/reference/arms_of_legend.md`): the candlemaking kit, wicks with tallow or wax and the rest for five hundred hours of candles (`:182`); the one-hour torch, cloth dipped in pitch, oil or a similar flammable substance (`:486`); weapon oil, from the rendered fat of fish or whales (`:368`); the pig, which eats rinds, bones and unwanted grease (`:2873`); the chandler, a worker in wax (`:2992`).

**Translation proposals:**

- **ZP-L1 — Fat is a share of SIZ, as the shipped parts are.** The harvest templates already yield meat at SIZ // 2 and hide at SIZ // 3 (`world/harvest_templates.py:30`, `:66–90`); fat joins them as a part with its own divisor, from *Monsters of Legend*'s SIZ (ZP1).
- **ZP-L2 — Rendering needs no test.** Melting fat in a pot over a fire is routine; p. 42 lets the Games Master rule that no test is required. Time, a fire and a pot are its cost, as felling is time with an axe (Forest YP-L1).
- **ZP-L3 — Cutting fat rolls as meat.** AoL puts meat on Survival, remapped to `hunting` in the shipped templates (`world/harvest_templates.py:20–22`); fat is cut with the meat and rolls the same way.
- **ZP-L4 — Candles and pemmican are `craft`.** In Cooking CQ3's leaning `cooking` discipline beside the five shipped ones (`world/recipe_mastery.py:81–87`); Craft (Candlemaker) and (Butcher) arrive with specialised Craft for every craft at once.
- **ZP-L5 — Weapon oil stays fishing's.** Legend makes it from fish or whale fat (p. 117); tallow does not replace it, and Fishing's proposed exclusive is untouched (ZP16).
- **ZP-L6 — Lye harms no one.** Caustic burns are Stage 5's damage model, if ever; nothing here hurts.
- **ZP-L7 — Legend's prices are not used.** Pillar 1.

---

## 5. The loop

Proposed phases; each is something someone can sell.

1. **Kill.** A deer in its range (Hunting slice 3), later a boar, later a herd animal at slaughter (Farming GP12).
2. **Cut.** Fat is cut from the carcass with the meat and hide (ZP1), more in autumn (ZP2).
3. **Hurry.** Raw fat goes off as fast as raw meat (Cooking CP7), so it is sold or rendered the same day.
4. **Render.** At a lit fire, in a pot: tallow to keep, scraps to eat (ZP3, ZP4).
5. **Make.** Candles and torches (Light LP5), pemmican (ZP6), later leather dressing (ZP7).
6. **Sweep.** A fire that burns out leaves ash; gathered while it is dry (ZP8, ZP9).
7. **Leach.** Ash and water become lye in a vessel (ZP10), for the tanner (ZP11); later soap (ZP12).

---

## 6. Fat

**ZP1 — Fat is a part of larger animals.** A harvest template gains a part `fat` (ZP-L1, ZP-L3), proposed divisor SIZ // 6: an average stag (SIZ 22–23, p. 109) or doe (19–20) gives three, a boar (about 10, p. 106) one, cattle (about 16, p. 107) two. **The rabbit gets no `fat` part at all** — not a small one: `compute_yield` floors every part at one (`world/harvest_templates.py:164`), so a rabbit with the part would give fat, and a rabbit is lean. A part absent from the template is simply not offered (`list_parts`, `:128`). Raw fat is food on Cooking's freshness clock with raw meat's shelf life (CP7, CQ2), so it spoils on the global index (CP8) and keeps in a cold store (CP10).

**ZP2 — Fat follows the animal's year.** The yield is scaled once, at the cut, by one factor:

| Source | Factor | Reads |
|---|---|---|
| Wild, killed in autumn (months 8–10) | ×1 | the corpse's death time, by season (`world/gametime_utils.py:56–61`) |
| Wild, summer or winter | ×½, rounded down | the same |
| Wild, spring (months 1–3) | none | the same — the animal is lean after winter |
| A herd animal | *fat* ×1½, *in good flesh* ×1, *lean* ×½, *thin* or *starving* none | Farming GP10's condition ladder |

A carcass with no fat to give says so in words (*there is hardly any fat on it*) when `harvest` lists its parts. This is the rule Farming took from Wurm — condition changes what a slaughter gives (Farming §2.1) — made literal for fat, with one table for wild and herded animals (ZG3). The factors are ZQ5.

---

## 7. Rendering

**ZP3 — `render` at a fire, in a pot.** A timed act on the shared slot (`world/timed_actions.py:107`, `:198`), shaped like Cooking CP5's `cook`: every piece of raw fat the renderer holds, up to the fire's capacity, goes into the pot at once; the act needs a lit fire in the room (Cooking CP1) that burns through its span (CP12's rule for the smoking frame) and a pot among the renderer's tools — a fireproof vessel, which waits for the kiln (registry open decision 7, `world/material_registry.py:505`; Water VP4's clay jug and the fireproof pot Water VP5 needs). No test (ZP-L2). Moving or the fire going out interrupts it and gives the raw fat back, as CP5 does. Each piece of fat gives one cake of **tallow**; each batch also gives one portion of **greaves** — the crisp scraps left in the pot — a small cooked food on Cooking's cooked shelf life (CQ2), so nothing of the animal is wasted. The span is ZQ7.

**ZP4 — Tallow keeps.** Tallow carries no freshness clock: it is the end of the fat's clock, which is the point of the step (ZG2). It is a small item — twenty to one ENC (`world/encumbrance.py:50`) — and one tag, `tallow`, whatever the animal (ZQ2). `tallow` leaves `PROPOSED_UNRATIFIED` (`world/material_registry.py:480`) and gets its registry row with its first consumer, Light's candle (ZP5, ZG1), as every gated recipe needs a source (`tests/test_recipe_sources.py`).

---

## 8. What tallow makes

**ZP5 — Tallow's consumers, in order.**

1. **The candle** (Light LP5): tallow and twine as the wick, a dim light. Tallow's first consumer, as BACKLOG *Light & darkness* says, and the one it is ratified with. How many candles a cake makes is the candle recipe's; this design leans to four one-hour candles a cake (ZP15).
2. **The torch binder** (Light LP5): stick, rags and tallow (or resin) burn an hour where a rough torch burns half that, which is what makes tallow worth carrying out of the house.
3. **Pemmican** (ZP6).
4. **Leather dressing**, later (ZP7).

**ZP6 — Pemmican: meat that keeps without salt.** Dried strips from Cooking's rack (CP11) pounded and mixed with tallow make pemmican, a `craft` recipe in the cooking discipline (ZP-L4). It keeps as long as Cooking's salted food (CQ2's leaning: about a season) — the longest-keeping food in the game that needs no salt, which does not exist in the code (Cooking CP13) and whose only proposed source is a brine spring (Water VP5). It is a traveller's and a winterer's food, a reason to buy tallow that is not light, and a second sink for the drying rack. Whether it ships is ZQ4.

**ZP7 — Leather dressing (later).** Tallow rubbed into a worn leather garment keeps the wet out: for a span of wear ticks the garment wears one step gentler outdoors, read in the one place a garment's wear level is resolved (`world/garment_wear.py:108–126`). A recurring sink for tallow and a reason for the cobbler and the leatherworker to buy it. Not in the first slice (ZQ16).

---

## 9. Ash

**ZP8 — A fire leaves ash by what it burned.** Forest YP10's ash, given a quantity: a fire that burns out leaves an ash pile in the room holding one handful of ash per four game hours of fuel it burned, rounded down — so a fire of sticks leaves nothing and a fire fed through a night (Forest YP1's eight-hour cap) leaves two. Charcoal burns clean and counts half. A clamp that is ruined by early opening leaves two handfuls (Forest YP8, YQ10). `gather ash` takes the handfuls; ash is a small item, twenty to one ENC, under the registry's `plant_ash` (`world/material_registry.py:479`), which it ratifies with lye (ZP10, ZG1). The rate is ZQ9.

**ZP9 — Ash must stay dry.** An ash pile in an outdoor room that is read while it is `raining` or `snowing` is washed into the ground and gone — a one-way change, as rain puts out an outdoor fire (Cooking CP3), so it is monotone and needs no tick. In a room flagged `is_indoor` (`world/thermal.py:68`) — a hearth (Housing BP7) — it keeps. So ash outdoors is gathered soon or lost, and a house's hearth is the ash-maker's steady source. This is also the litter answer for ash: piles in the open do not pile up (*litter, abandoned goods & salvage rights* in the queue). Ash carried in a pack keeps (ZQ10).

---

## 10. Lye

**ZP10 — Lye is water that has run through ash.** `craft lye` with ash in the inventory and a vessel holding fresh water: every draught in the vessel becomes the kind **lye** (Water VP3's kind field, which already names later liquids — Wurm's rule, §2.3), and ash is used at one handful per five draughts, rounded up (ZQ11). The vessel is kept, as Water VP2 keeps it. Lye is a liquid with a kind, not an item, so it needs no registry row: it is carried in a gourd skin, a leather bucket or later a clay jug (Water VP4), poured between vessels of the same kind and emptied like water. **Lye is not drunk:** `drink` refuses it as Water refuses brine (Water N3). Lye does not wear its vessel any faster than water (ZQ3).

**ZP11 — Lye's first consumer is the tanner.** BACKLOG *Tanning upgrade* adds bark and water to `LeatherRecipe` (`world/recipes.py:174`), and its water annotation reads Water VP2. Proposed beside them: lye as an **optional** input. A hide soaked in lye loses its hair cleanly and takes the tan better, which is a roll term on the leather craft — the way a tool's modifier is a roll term, never a trait modifier — and never a requirement (ZG6): today's two-hide recipe still makes leather. The draughts are drawn in `post_craft`, with the consumables, by VP2's rule. Lye is for leather only; a pelt kept fur-on (registry decision 1) is never limed. The size of the term is ZQ12.

---

## 11. What waits

**ZP12 — Soap is designed and does not ship.** Lye and tallow boiled together at a fire in a pot make soap: the end of both halves of the chain. It does not ship until something in the game needs a person or a thing to be clean — *hygiene & bathing* in the design-series queue, the roadmap's *Disease system* (a wound that turns bad, as in Dwarf Fortress), or wool scoured before it takes a dye (not in Textiles Design today) — because a soap that only sells is the soap players ignored (§2.1). Which consumer comes first is ZQ13.

**ZP13 — Ash's later sinks, recorded.** Three further uses, each with its own system: **potash** for fields, a fourth restorer of fertility beside dung, bonemeal and saltpeter (Farming GP5), with Farming's fields; **flux for glass** — the registry already names `soda_ash` beside sand as glass's input (`world/material_registry.py:332`), so the lantern's glass (Light LP5) reads this chain, with the furnace (registry open decision 8); and **an ash glaze** for fired pots, with the kiln. None ships here.

---

## 12. Offline and the world

**ZP14 — Nothing waits on the renderer.** Raw fat on a statue keeps as all food does (Cooking CP9: stone does not rot); tallow keeps anywhere; lye keeps in its vessel. A render is a timed act and is interrupted by logging out, as cooking is, and the raw fat comes back. An outdoor ash pile washes away in the rain whether anyone is online or not, because it belongs to the room: it is read, never watched. A wilderness fire's ash is Stage 6's, as the fire is (Evennia Reference §14.5–§14.6).

---

## 13. Economy

**Sources (all natural or player-made):** fat from larger game in its range (Hunting slice 3) and from herds at slaughter (Farming GP12); tallow from rendering; greaves from rendering; ash from every fire and every ruined clamp; lye from ash and water.

**Sinks:** raw fat's short life (sold or rendered the same day, or lost); candles and torches burned through the night (Light LP4: fuel is time — the largest sink, and larger in winter); pemmican eaten on the road; tallow rubbed into leather, later; ash washed away in the rain; lye drawn by the tanner; the pot's wear and the fire's wood for every batch (Forest YG6).

**Materials this design gives a source or a sink:** **tallow** (a source, and its first consumer with Light's candle — leaving the unratified list); **plant ash** (a source with Forest YP10 and its first sink, lye — leaving the unratified list); **dried meat** (a second sink, pemmican); **leather** (a better tan from lye); **soda ash** (its glass use recorded, not shipped).

**Services:** the renderer with a pot by a fire, to whom hunters sell fat that will not keep; the chandler who sells candles in winter that were made in autumn; the ash-sweeper who sells a hearth's ash to the tanner; the tanner who sells better leather. The renderer and the hunter are tied by the fat's one-day life — the same tie Cooking draws between the hunter and the cook.

**ZP15 — The master constant, on one page (ZG5).** At the leanings: an autumn stag gives three fat (ZP1, ZP2), three fat render to three cakes of tallow (ZP3), and a cake makes four one-hour candles (ZP5) — so **one autumn stag lights twelve candle-hours**, a night and a half of one candle through winter's eight-hour nights (night is 20:00–04:00, `world/gametime_utils.py:46–54`). A night's fire leaves two handfuls of ash (ZP8), which make up to ten draughts of lye (ZP10) — a fire a night keeps a tanner in lye. Every number here is a leaning and moves together; the decomposition tunes this table, not the parts one by one.

**ZP16 — No exclusive.** Fat comes from the hunter's wild game and the herder's animals both, and anyone with a pot may render it. Proposed for the roadmap's food-professions exclusives decision: tallow is on no profession's list, and the livestock list (wool, milk and cheese, eggs, bulk hide, sheepskin) and fishing's (fish oil, salt fish) are untouched (ZP-L5).

**Coin:** none. **Logging:** rendering, making lye and the first candle are ZQ14.

---

## 14. Multiplayer and server load

- **Nothing ticks.** Raw fat reads Cooking's global spoilage index (CP8), one counter on the `WeatherScript` that already wakes every 1800 s (`typeclasses/scripts.py:112`, `:135`); tallow and lye have no clock; an ash pile's fate is decided when it is read.
- **One fire, two renderers.** A fire's capacity is shared, as Cooking CP5's is; each renderer claims their own timed-action slot (`world/timed_actions.py:198`), and the fire's state is checked at the act's end.
- **One ash pile, two sweepers.** `gather ash` reads the pile, checks the weather, moves the handfuls and deletes the pile in one synchronous command; a second sweeper finds it gone.
- **One vessel, one conversion.** `craft lye` changes the kind and the ash in `post_craft`, in one step; a refused or interrupted craft changes nothing (Water VP2's rule).
- **Rooms do not fill with ash.** Outdoor piles wash away in weather; indoor piles are a hearth's, and there are few hearths (ZP9).
- **Wilderness.** No persistent piles or fires there; Stage 6's (Evennia Reference §14.6).

---

## 15. Immersion extras

- **The stink of rendering.** A render in progress gives the room a line (*the reek of hot fat hangs here*) and the rooms beside it one, read from the exits like Cooking CP2's smoke — the reason the trade kept to the edge of town (§2.4).
- **Tallow and beeswax.** A tallow candle smokes and smells of the animal; a beeswax candle burns clean (Light LP5), a reason to pay more for wax once beekeeping exists.
- **Autumn's kettles.** In autumn a settlement's fires burn late for rendering; the season's words can say so.
- **Ash on the ice.** A handful of ash thrown on an icy path gives a grip — a word for *ice & cold* in the queue.
- **The candle as a clock.** Legend's miners marked time with a one-hour candle (p. 112), a thread for *timekeeping & almanacs*.

---

## 16. Layers — a suggested order

1. **Slice 1 — fat, rendering and the candle, together (ZG1):** the `fat` part on the deer (ZP1, ZP2), `render` (ZP3), tallow and greaves (ZP4), and Light's candle and tallow torch (ZP5). Needs: Hunting slice 3 (the deer), Cooking's fire (CP1) and a pot from the kiln (registry open decision 7). If the deer lands first, its template ships without the `fat` part until rendering is ready, so no part ships without a consumer.
2. **Slice 2 — pemmican, with Cooking's drying rack (CP11):** ZP6.
3. **Slice 3 — ash and lye, with BACKLOG *Tanning upgrade* and Water VP2:** ZP8, ZP9, ZP10, ZP11. Needs Cooking's fire; registry open decision 6 is marked resolved by whichever VP2 reader ships first.
4. **Later:** fat from herds with Farming's herd (ZP2's second half); leather dressing (ZP7); soap with its consumer (ZP12); potash with Farming's fields, flux with the furnace, glaze with the kiln (ZP13).

**Prerequisites:** slice 1 needs the deer, the fire and the pot; slice 2 needs the drying rack; slice 3 needs the fire and VP2. **Not prerequisites:** Stage 5, the webclient, the economy milestone.

---

## 17. Seams in today's code (read at `50776a7`)

| Need | Seam | Where |
|---|---|---|
| Harvest parts | rabbit: meat, hide, bone at SIZ // 2, // 3, // 4; meat on `hunting` | `world/harvest_templates.py:66–90`, `:20–22`, `:30` |
| Yield | `compute_yield`, floored at one; `list_parts` | `world/harvest_templates.py:142–164`, `:128` |
| SIZ on the corpse | creature `siz`, carried to the corpse | `typeclasses/creatures.py:48`, `:100` |
| Harvest command | part lookup; yield | `commands/hunting_commands.py:255`, `:304` |
| Spoilage | the corpse's decay; cold storage read, set by nothing | `typeclasses/corpse.py:92–133`, `:104` |
| Registry | unratified list (tallow, plant ash, soda ash); glass from sand and soda ash; pottery BLOCKED on the kiln; raw hide; leather; open decisions 6 and 7 | `world/material_registry.py:478–483`, `:329–334`, `:335–340`, `:197–202`, `:265–274`, `:503–505` |
| Leather | `LeatherRecipe` | `world/recipes.py:174` |
| Vessels | `Drink` with charges; the gourd waterskin recipe | `typeclasses/consumables.py:28–57`; `world/recipes.py:126` |
| Craft | ingredients from inventory; tools from room and inventory; the dry run | `commands/crafting_commands.py:315`, `:324`, `:285` |
| Recipe skill and disciplines | `skill_name`; five disciplines | `world/crafting_base.py:58`; `world/recipe_mastery.py:81–87` |
| Recipe sources | every gated recipe has a source | `tests/test_recipe_sources.py` |
| Indoors | `is_indoor` | `world/thermal.py:68` |
| Garment wear | the effective wear level | `world/garment_wear.py:108–126` |
| Weight | small items twenty to one ENC | `world/encumbrance.py:50` |
| Timed acts | one `ndb.timed_action`; `claim` | `world/timed_actions.py:107`, `:198` |
| Seasons and night | autumn 8–10; night 20–04 | `world/gametime_utils.py:56–61`, `:46–54` |
| Weather script | wakes every 1800 s | `typeclasses/scripts.py:112`, `:135` |
| Statues | logged-out character as stone | `typeclasses/characters.py:472` |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **ZQ1** — Can fat be rendered without a pot — on a hot flat stone by the fire, slowly and with loss — so tallow does not wait for the kiln? *Leaning (chat, 2026-11-08): no — rendering needs a fireproof pot, which waits for the kiln; the hot stone is recorded in §19.*
- **ZQ2** — One tag for all rendered fat, or tallow and lard apart? *Leaning (chat, 2026-11-08): one tag, `tallow`; a pig's is called lard in words only, as species are flavour on generic `wood` (DECISION #10).*
- **ZQ3** — Does lye eat its vessel? *Leaning (chat, 2026-11-08): no — the kind is a liquid's only property (Water VP3), and every vessel holds lye as it holds water.*
- **ZQ4** — Does pemmican ship? *Leaning (chat, 2026-11-08): yes, as tallow's second food-side sink, with the drying rack (ZP6).*
- **ZQ5** — The season factors for wild fat. *Leaning: autumn ×1, summer and winter ×½, spring none (ZP2).*
- **ZQ6** — The fat divisor, and whether stag and doe differ beyond their SIZ. *Leaning: SIZ // 6 for every species, the SIZ alone making the difference (ZP1).*
- **ZQ7** — How long a render takes, and the batch cap. *Leaning: half a game hour per batch, up to the fire's capacity (Cooking CQ11's question for cooking).*
- **ZQ8** — Candles per cake of tallow. *Leaning: four one-hour candles; the number is Light's candle recipe's (LP5), and ZP15 moves with it.*
- **ZQ9** — Ash per fire. *Leaning: a handful per four game hours of fuel burned, rounded down; charcoal at half (ZP8).*
- **ZQ10** — Does ash in a pack get wet in the rain? *Leaning: no — a pack keeps it dry; only piles on the ground wash away (ZP9).*
- **ZQ11** — The lye ratio, and whether leaching takes hours. *Leaning: one handful per five draughts, rounded up, made in an ordinary `craft` act with no long wait; real leaching takes hours, which a later design can add as a stamp if it matters.*
- **ZQ12** — The size of lye's term on the leather craft. *Leaning: the size of a tool's modifier, set in the Tanning upgrade's decomposition with bark and water at the same time.*
- **ZQ13** — Soap's first consumer: hygiene & bathing, the Disease system's wounds, or wool scoured before dyeing (a step Textiles Design does not have today)? *Open.*
- **ZQ14** — Activity-log kinds for rendering and making lye: new kinds or fields on existing ones? The family of Hunting TQ10, Textiles WQ8, Farming GQ6, Fishing FQ6, Water VQ9, Foraging RQ11, Light LQ12 and Forest YQ13. *Open.*
- **ZQ15** — Who may take ash from a fire someone else built, or fat left in a pot by a renderer who walked away? *Leaning: anyone, in the alpha; ownership of what lies about is law & crime's and the litter design's.*
- **ZQ16** — Leather dressing: in slice 1, or later? *Leaning: later, when leather garments are worn enough for it to matter (ZP7).*
- **ZQ17** — Where the candle, pemmican and lye recipes come from: a profession, a scroll or a teacher? `render` is a verb, like `cook`, and needs no recipe; the others do, and every gated recipe needs a source (`tests/test_recipe_sources.py`). *Open.*

---

## 19. Considered and not proposed

- **Soap as a trade good with no use.** Dwarf Fortress's early soap (§2.1; ZG1).
- **A workshop per step.** The ashery, the soap-maker's shop and the kitchen as stations (§2.1); a fire and a pot are enough.
- **The full alkali chain now.** Potash, pearlash and soda ash as separate refined goods; recorded as later sinks only (ZP13).
- **Fat bought from an NPC trader.** Vintage Story's traders (§2.2); pillar 1.
- **Fat from rabbits.** A rabbit is lean (ZP1).
- **Rendered fat as a fuel.** Forest YP1's table stays wood's (§2.2).
- **Rendering on a hot stone without a pot.** ZQ1's leaning.
- **Separate tags for tallow, lard and suet.** ZQ2's leaning.
- **A quality on lye, capped by its ash.** Wurm's rule (§2.3); a liquid's kind is its only property (Water VP3).
- **Lye required for leather.** No shipped recipe loses its source (ZG6).
- **Weapon oil from tallow.** Legend makes it from fish or whales (p. 117; ZP-L5).
- **Burns from lye or hot fat.** Stage 5's (ZP-L6).
- **A rendering minigame or tending.** The series' rule: skill lives in choices, not in watching a pot.
