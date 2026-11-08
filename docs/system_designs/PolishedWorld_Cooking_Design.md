# PolishedWorld — Cooking & Preservation Design Notes (fire, freshness, the larder)

> **Rev 2 · 2026-11-08** — moved, docs only, with roadmap Rev 60, BACKLOG Rev 85 and README Rev 39: from `docs/` to `docs/system_designs/`, together with the fourteen other one-system design notes and the series handoff, `docs/system_designs/HANDOFF.md`. The *Canonical* line and every path to a design note outside a Rev line now name the new folder; no content changed. Rev lines keep the paths they were written with, since changelog lines are left exactly as written.
> **Rev 1 · 2026-11-07** — first version, docs only, with roadmap Rev 49, BACKLOG Rev 71 and README Rev 27. Written from a design chat, the fourth in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`, `docs/PolishedWorld_Housing_Design.md` and `docs/PolishedWorld_Hunting_Design.md`. Cooking is not shipped, but eating is, so the notes name every place they would change live behaviour (§6). **Nothing here is locked.** Every numbered item is a proposal (CP…) or an open question (CQ…); a decomposition locks or rejects each one. In the chat Adam took the recommended answer to CQ1–CQ6 as the design's working assumption; each is recorded as a *leaning* under its question, not as a decision. Prior art was read on 2026-11-07; code seams were read against `main` at `6c07785` (Evennia 6.1.0).
> **Canonical:** `docs/system_designs/PolishedWorld_Cooking_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/BACKLOG.md`, *Survival*, *Food spoilage* — its parts (1)–(3) are this document's clock and stages (§9) and its part (4) is preservation (§10). The entry gains a 2026-11-07 annotation (Rev 71), which also corrects its claim about salt (§13), and is not replaced by this document. The roadmap's *Food professions* entry gains a note (Rev 49): the exclusives decision it owns ("preservable salt fish") stays there.
**When to read:** at the start of the *Food spoilage* decomposition; with fishing slice 1 (fish needs the clock, Fishing Design §7); when housing decomposes its parts (a hearth and a larder, §7, §10); when *Temperature & exposure* or *Light & darkness* is decomposed (the fire is a reader for both, §7); when *Weather inertia* part (2) fires (§9's index is a first mechanical reader of weather); at the Stage 5 design session (burns, §4).
**Departs from shipped behaviour in eight places**, listed with their source lines in §6. The largest: food stops keeping forever, and a character who has logged out stops being a place where food rots.

---

## 1. The idea in one paragraph

Food in PolishedWorld is a clock and a craft. A rabbit is warm when it falls and starts to turn within the day; meat cut from it carries the hour of the kill, not the hour of the knife. Somebody gathers wood, builds a fire and keeps it fed; the cook roasts a whole catch on it at once, slowly for a better result or quickly when it is getting dark, and what comes off the fire fills you more than what went on. What will not be eaten soon is hung on a rack in the wind, smoked over a banked fire or packed in salt, and it keeps for weeks — in a larder, in a pack, in a ship's hold. Nobody reads a number: food *smells fine*, *is turning*, *has gone off*. A character who logs out turns to stone, and the stone keeps what it carries. Winter stores are worth something because summer meat will not wait, and the people who know how to make it wait are people others pay.

---

## 2. Prior art

### 2.1 Armageddon — the lesson

Source: Armageddon's player forum (`gdb.armageddon.org`, topic 52030, *Spoilage and crafting*, December 2016 – January 2017), a discussion after the game added spoilage. Paraphrased:

- Players reported that, by the release notes, raw food in a cool room in a food container lasted about two real days and preserved food about three.
- The complaint that recurs is not stockpiling. It is gifts and orders: food made or bought for another character spoiled because the two players' log-in times did not overlap for a few days, although in the characters' own time they would have met. Several players said the change produced *less* interaction around food — hunters left meat to rot, and others gave food away free rather than let it spoil, which is the opposite of trade.
- Supporters liked that fresh cooked food became special and that ingredients had to be gathered or hired again. Suggestions in the thread: much longer timers for crafted and preserved food, cool rooms and better containers that multiply the timer, and food-type-specific ageing messages — which staff confirmed the code already supports.

**Worth taking:** ageing messages per kind of food; cool rooms and containers as multipliers; preservation as the thing that makes food tradeable.
**Not for PolishedWorld:** short timers that run while a player is away. **The lesson (the series' "Achaea lesson" for this system):** a spoilage clock that runs during a player's absence punishes exactly the asynchronous trade it was meant to create. The rule taken: what a character carries does not age while they are logged out (CP9), and preserved food is measured in real weeks, not real days (CQ2).

### 2.2 Haven & Hearth — processes on objects

Sources: the Ring of Brodgar wiki (`ringofbrodgar.com`), pages *Smoke Shed* and *Hunger*. Paraphrased:

- A smoke shed is a built structure that is loaded with raw meat or fish fillets and fuelled with blocks of wood; after about a real day the batch becomes its smoked variant. Smoked food changes what it gives the eater, and the kind of wood burned changes the result.
- Product quality is a weighted average of the inputs and the shed; food quality is a separate axis from how filling a food is.
- A drying frame outdoors dries hides and plants over many real hours; it cannot be built inside and decays if neglected.

**Worth taking:** slow processes that belong to an object, not to a waiting player; fuel as an input; the fuel and the inputs shaping the output; outdoor drying as a distinct, weather-exposed thing.
**Not for PolishedWorld:** food as the engine of character statistics (FEP) — Legend's characteristics are not grown by eating.

### 2.3 Don't Starve — categories, not item ids

Source: the Don't Starve wiki (`dontstarve.wiki.gg`), pages *Cooking* and *Food Value*. Paraphrased:

- The Crock Pot reads ingredients by *food value* — how much meat, vegetable, fruit, egg and so on each contributes — so many different combinations make the same dish; a dish has requirements and exclusions, and filler completes the pot.
- Some food is dried on a rack in the open rather than cooked; cooked food does not always keep better than raw.

**Worth taking:** dishes defined by categories, which answers Armageddon's other complaint in the same thread (recipes keyed to one exact item with no substitutes). PolishedWorld already matches ingredients by tag-key (`world/recipes.py:119` lists `["fiber", "fiber", "fiber"]`), which is the same idea.
**Not for PolishedWorld:** a guaranteed result whatever the cook's skill — here the dish is a Legend Craft test (§4).

### 2.4 Achaea — the cook as author

Sources: Achaea's tradeskills overview (`achaea.com`) and forum threads on the tradeskill split and a later rework (`forums.achaea.com`). Paraphrased:

- Cooking is one of Achaea's *design* tradeskills: players submit their own dishes — names and descriptions — which are approved and then made from commodities; food is largely social, for feasts and festivals.
- Staff described a later recipe rework as partly meant to reduce players' need for client scripts — the repetition of crafting commands is what players automate.

**Worth taking:** the cook names what they make (§15); food as something served at gatherings.
**Not for PolishedWorld:** licences, approval queues and NPC chefs. **The automation half of the lesson:** repetition is what gets scripted, so one `cook` handles a whole batch (CP5) and the long processes run on objects (§10) — there is nothing to repeat.

---

## 3. Design goals

- **CG1 — Food is a clock you can read in words.** Freshness is shown as a state (*fresh*, *turning*, *off*), never as hours (§2.1; `ResourceNode._availability_phrase`, `typeclasses/resources.py:129`).
- **CG2 — No rot while you are away.** A logged-out character's belongings do not age (§2.1, CP9). Food left in the world does.
- **CG3 — Cooked beats raw.** Cooking is worth doing, so a cook is worth paying (pillar 1).
- **CG4 — Preservation is a craft and a trade.** Long life is made, not given: a new item from a recipe, as BACKLOG *Food spoilage* (4) requires.
- **CG5 — Slow processes live on objects.** Smoking and drying run on a rack or a frame, lazily, while the player does something else (§2.2).
- **CG6 — The world reads in.** Season, weather and shelter change how fast food turns and whether a rack dries; fire needs fuel and fears rain.
- **CG7 — Monotone and lazy.** No tickers per item; no clock that runs backwards (`Corpse.decay_modifier`'s shape is not copied, §9).
- **CG8 — Source and sink named together** (Economic Philosophy; `docs/PolishedWorld_SourceSink_Ledger.md`).

---

## 4. Legend alignment

**Rules as written:**

- **Craft (DEX+INT)** — Legend core p. 57: several separate skills under one heading; the list includes *baker, brewer, butcher, cook*. A **critical** makes the item superior in **durability, value or utility** (choose one).
- **Task times** — p. 67 (Local Time): *prepare and cook a carcass for eating* takes 1 to 12 hours, depending on the SIZ of the carcass; *forage for food, set snares* 2 to 4 hours.
- **Difficulty and Haste** — p. 39: taking double the normal time is Simple (+20 %), five times Easy (+40 %), ten times Very Easy (+60 %); rushing in half the time is Hard (−40 %). **Rolling in Secret** (same page): the result may be revealed only through play.
- **Fire and Heat** — p. 83: a *small fire* (camp fire, cooking fire) does 1D6 per round to anyone in it.
- **Exposure, Starvation and Thirst** — p. 90: survival for CON days without food, −10 % to Fatigue tests after three days. Unchanged by this design.
- **Survival (POW+CON)** — p. 63: tests for living outside civilisation, including gathering food for others. The codebase has no `survival` skill; the word names the gauge category (`typeclasses/characters.py:442–446`).
- **Arms of Legend** (`docs/reference/arms_of_legend.md`): **Preserving Kit** (`:390`) — salt, wrappings, a sawdust tool, jars; it provides the tools for *any* test to preserve and store food, and is good for ten uses. **Spices** (`:472–476`) — one packet flavours thirty meals. **Salt Tablets** (`:430`) — +10 % to Resilience against heat and forced marches. **Pepper** (`:378`) — hides tastes. Two weeks of **trail rations** are ENC 1 in the essential kit (`:85`).

**Translation proposals:**

- **CP-L1 — Cooking is `craft` in a new `cooking` discipline.** The codebase has one generic Craft (`typeclasses/characters.py:416–424`) and recipe disciplines for mastery (`world/crafting_base.py:81–87`; five today: bonework, leatherwork, stonework, weaving, woodwork). Craft (Cook) and (Butcher) arrive with specialised Craft, when that arrives for every craft at once (CQ3).
- **CP-L2 — Haste is a roll term and a duration.** `cook slowly` doubles the timed action and adds +20; `cook quickly` halves it at −40; the default is Routine. Smoking and drying are already "ten times normal time", so they carry no haste choice (§10).
- **CP-L3 — Legend's critical, as written.** A critical cook chooses: **utility** (the dish fills more), **durability** (it keeps longer) or **value** (it is *fine* — a name and a band a buyer can see). Fumble: *charred* — edible, fills little. Failure: *underdone* — fills less and turns sooner.
- **CP-L4 — Task time compressed, not copied.** Legend's 1–12 hours for a carcass becomes real seconds on the shared timed-action slot, scaled by portions; the number is the decomposition's (CQ11).
- **CP-L5 — Fire burns, later.** A fumble while tending a fire is a scorch message and a lost portion now; Legend's 1D6 to a location waits for Stage 5's hit locations.
- **CP-L6 — The Preserving Kit is the preservation tool.** Salting needs it (ten uses, `apply_wear` as other tools); spices and salt tablets are later items with their own readers (§15).

---

## 5. The loop

Proposed phases.

1. **Gather.** Meat from a corpse (it already carries its age, CP8), fish, berries; wood and sticks for the fire.
2. **Build and light.** `build fire` lays a fire from wood; `light fire` with flint is a short timed act and a test (CQ7). The fire shows in the room and its smoke in the rooms beside it (CP2).
3. **Cook.** `cook meat` (optionally `slowly` / `quickly`) is one timed act for every raw portion of that kind the cook holds, up to what the fire takes (CP5). One test; the result names the batch.
4. **Keep the fire.** `feed fire` adds wood; an untended fire burns down; rain puts out a fire in the open (CP3).
5. **Store or preserve.** Hang strips on a drying rack, set a smoking frame over a banked fire, or salt with a kit (§10). Each finishes on its own; anyone passing sees how far along it is.
6. **Eat.** `eat` reads the state; off food is refused unless the eater insists (CP14). A cooked, varied meal leaves the eater *well fed* (CP15).

What it reads like (illustrative, not a spec):

```
> look
Edge of the Woods
...
A small fire burns here, crackling over a ring of stones.
> cook rabbit slowly
You set three portions of raw rabbit over the fire and turn them patiently...
The meat is browned through, the fat spitting. You have three portions of
roasted rabbit.
> look roasted rabbit
A portion of roasted rabbit, still warm. It smells good.
> hang rabbit on rack
You hang a strip of rabbit on the drying rack. The wind takes the smoke away.
... (a game day later)
> look rack
A rough drying rack of lashed sticks. Strips of rabbit hang from it, dark
and nearly dry.
```

---

## 6. Departures from shipped behaviour

Each row is a change to behaviour that `main` has today; each is a proposal.

| # | Shipped today | Proposed | Where shipped |
|---|---|---|---|
| E1 | `Food` has `restore_amount` and `consume_message` and keeps forever | A freshness clock and three worded stages (CP7) | `typeclasses/consumables.py:19–25` |
| E2 | `eat` accepts any `Food`, adds `restore_amount`, deletes it | `eat` reads the stage; off food is refused unless forced (CP14); a quality factor scales the restore (CP16) | `commands/consumption_commands.py:29–53` |
| E3 | Harvested meat is spawned as new — fresh whatever the corpse's stage | Meat inherits the corpse's `death_time` (BACKLOG *Food spoilage* (2); CP8) | `commands/hunting_commands.py:275–277`, `:306–313` |
| E4 | `is_cold_storage` is read by the corpse and set by nothing | A larder or cellar part sets it (housing), and food reads it too (CP10) | `typeclasses/corpse.py:104` |
| E5 | The corpse's age is the whole span × the modifier *now*, which can run backwards | Corpse and food read one shared, monotone spoilage index (CP8, CQ9) | `typeclasses/corpse.py:92–133` |
| E6 | A logged-out character is a statue in the room; nothing about it pauses | A statue's carried food does not age (CP9) | `typeclasses/characters.py:472–491` |
| E7 | The room sweep crumbles expired corpses only | The sweep crumbles anything with `crumble()` — spoiled food, a burnt-out fire (BACKLOG *Food spoilage* (3)) | `typeclasses/rooms.py:358`, `:391` |
| E8 | Raw rabbit restores 15, berries 10, with a comment leaving headroom for cooking | Raw stays low; cooked and preserved foods carry the larger restores (CP16) | `world/prototypes.py:893–909`, `:94–101` |

Unchanged: the hunger gauge and its ticker, `drink` and water containers, harvest templates and their decay gates, the activity-log kinds (cooking logs as `craft`, eating as `consume`, spoiling as `crumble`).

---

## 7. Fire

**CP1 — A fire is an object in the room.** `build fire` consumes wood (`world/prototypes.py:385`) and makes a `Fire` object; it is not a room flag (CQ1). It is lit or cold, and it has `burns_until` (absolute game-seconds) — no ticker: the state is computed on read. In an authored room a cold fire-ring can stay; in wilderness (no persistent objects, Evennia Reference §14.6) a fire is a short-lived object that crumbles once it is cold, through the same expiry pattern as corpses (E7).

**CP2 — A fire is seen and smelt.** The room shows it in words by how much it has left (*blazing*, *burning low*, *embers*); neighbouring outdoor rooms get one line (*smoke rises to the north*), read on `look` from the exits — no writes. A housing hearth is the same object in a house's part slot (Housing Design §7, BP7).

**CP3 — A fire needs fuel and fears rain.** `feed fire` adds wood and pushes `burns_until` out by a fixed span per piece, up to a cap. An outdoor fire that is read while the weather is `raining` or `snowing` goes out and stays out (a one-way change, so monotone); an indoor fire (`is_indoor`, `world/thermal.py:68`) is untouched by weather. The fire is the first sink for wood beyond crafting and the first consumer of flint as a fire-starter (`world/material_registry.py:139`, today an intent only).

**CP4 — A fire is a reader for other systems, later.** Warmth for *Temperature & exposure* (a lit fire in the room as a thermal term) and light for *Light & darkness* (a light source in the room). Neither is in this design's first slice; the object is shaped so they can read it.

---

## 8. Cooking

**CP5 — `cook` is one timed act per batch.** The cook names a kind (`cook rabbit`); every raw portion of that kind they hold, up to the fire's capacity, goes on at once. One `craft` test with the haste term (CP-L2) and a freshness term (turning meat is harder to cook well); one timed action on `ndb.timed_action` (`world/timed_actions.py:107`); moving or the fire going out interrupts it and returns the raw portions unchanged. The recipe is a `MongooseCraftRecipe` in the `cooking` discipline whose `pre_craft` (`world/crafting_base.py:260`) also requires a lit fire in the room.

**CP6 — Dishes by category.** Simple cooking turns one raw thing into its cooked form (roast rabbit, baked fish). Dishes that combine ingredients match by tag-key category — `meat`, `fish`, `root`, `green`, `berry` — as recipes already match `fiber` or `cloth` (§2.3), so any meat makes a meat stew. A pot is a tool; pottery waits on the kiln (`world/material_registry.py:337`), so stews are a later layer (§16).

The cooked item's clock starts from what was left of its ingredients' freshness, not from fresh: cooking does not launder turning meat (§9).

---

## 9. Freshness and the clock

**CP7 — Three stages, in words.** Every food has a shelf life in effective game-hours. It reads *fresh* for the first part, *turning* for the next and *off* after that; past a final limit it crumbles (E7). Words are per kind of food (§2.1): meat *smells fine / is turning / has gone off and stinks*; berries *are plump / are soft and bruised / have gone to mould*. Proposed shelf lives at today's 4× speed (a game day is six real hours, a game month seven real days, `server/conf/settings.py:55–63`) — CQ2:

| Food | Fresh for about | Real time |
|---|---|---|
| raw meat, raw fish | 1 game day | 6 h |
| berries | 2 game days | 12 h |
| cooked meat or fish | 3 game days | 18 h |
| dried or smoked | 1–2 game months | 1–2 weeks |
| salted | a season (about 3 game months) | about 3 weeks |

Multipliers on how fast effective time runs, carried over from the corpse table (`typeclasses/corpse.py:49–50`, `:104`): summer ×2, winter ×0.5, rain ×1.5, snow ×0.5, cold storage ×0.25. They move into one shared module (`world/decay.py`) read by corpse and food, as BACKLOG *Food spoilage* (1) asks.

**CP8 — A global spoilage index, so the clock never runs backwards.** The corpse multiplies the whole elapsed span by the modifier as it is *now* (`typeclasses/corpse.py:116–133`), so a cold snap makes old meat look fresher. Proposed instead: the global `WeatherScript`, which already wakes every 1800 s (`typeclasses/scripts.py:135`), adds the current *season × weather* factor for the elapsed interval to one monotone counter, the **spoilage index**. An item stores the index at its anchor and the effective hours it had already used; its age is *used + (index now − index at anchor) × place factor*. Place factors (cold storage, a statue) change only when the item moves or its holder logs in or out — events — and at each event the item advances its anchor. Reading is O(1), nothing ticks per item, and the clock is monotone. Meat cut from a corpse starts with the corpse's used hours (E3). This is also the first mechanical reader of weather that *Weather inertia* part (2) names as its trigger; Hunting Design §7 proposes a weather history on the same script, and the two should land as one change (CQ9).

**CP9 — The statue keeps what it carries.** A logged-out character stays in the room as stone (`typeclasses/characters.py:472–491`). Proposed: at unpuppet, every `Food` in the character's inventory and its containers advances its anchor and takes place factor 0; at puppet (`:494`), it re-anchors at the current index with its normal factor. In the world's own terms: stone does not rot. This is the rule taken from Armageddon (§2.1). Food on the ground, in a house or on a rack keeps ageing.

---

## 10. Preservation

Preservation turns a short-lived food into a **new item** with a long shelf life (BACKLOG *Food spoilage* (4)): the recipe is a craft and a trade, not a flag on the old item.

**CP10 — Cold storage.** A room flagged `is_cold_storage` slows every clock in it ×0.25. Nothing sets the flag today (E4); a house's larder or cellar part would (a proposal for Housing Design §7's parts list), and staff can set it on an authored cellar.

**CP11 — The drying rack (the first preservation, CQ6).** A rack is made from sticks and twine — existing materials (`stick`, `twine`) — and stands outdoors in an authored room. Raw meat or fish cut into strips, or berries, are hung on it. Drying advances on a second global counter on the same script, the **drying index**, which grows only in clear weather (half in fog), so a rack in a wet week makes no progress. Rain or snow while a batch hangs undone soaks it: the batch's spoilage clock jumps ahead (a wet index, compared on read). A finished batch becomes *dried* items with a long shelf life and a lower restore than cooked. No salt is needed, which is why it is first.

**CP12 — The smoking frame.** A frame set over a lit fire; loaded with strips, it smokes them over a span of game-hours, but only while the fire's `burns_until` covers the span, so the smoker must keep the fire fed or bank it with enough wood. Smoked food keeps as long as dried, and later the wood burned can flavour it (§2.2, §15).

**CP13 — Salting.** Salt plus the Preserving Kit (CP-L6) on raw meat or fish makes salted food, the longest-keeping kind; soaking it before cooking is the price. **Salt does not exist in the code** (§13): no prototype, no registry entry. Its source is CQ5.

---

## 11. Eating

**CP14 — `eat` reads the stage.** Fresh food eats as today. Turning food eats with a line that says so and a smaller restore. Off food is refused (*it stinks; you would be sick*) unless the eater insists (`eat <food> anyway`): then it restores a little and gives a short **queasy** buff — the hook for the roadmap's *Disease system* (CQ4). Buffs are added through the contrib as `world/survival_buffs.py` already does.

**CP15 — Well fed.** A cooked meal gives a short **well-fed** buff — slower hunger for a few game-hours — and two *different* cooked dishes within a game day lengthen it (variety, without Haven & Hearth's statistics, §2.2). It is the reason a traveller buys a meal from a cook rather than eating raw meat: demand without an NPC (CG3).

---

## 12. Quality

**CP16 — Quality, from the same bands.** A cooked or preserved item carries `db.quality` from the craft roll (`world/crafting_base.py:229`) and reads its band from `world/crafting_quality.py` (*superior, serviceable, poor, shoddy*). The band scales the restore; a critical's Legend choice (CP-L3) adds restore, shelf life or the *fine* band. Raw inputs carry the freshness of their source; Hunting Design TP12 asks for a quality field on harvested parts, and the decomposition decides whether that field and this one are the same (CQ10).

---

## 13. Economy

**Sources (all player-made):** cooked, dried, smoked and salted foods; fires, drying racks and smoking frames (sticks, wood, twine — existing materials); later pots (pottery) and the Preserving Kit.

**Sinks:** wood burned as fuel (the largest new sink for wood); food that spoils; batches soaked on a rack; kit uses; racks and frames worn by `apply_wear`; hunger itself, as today.

**Services cooking creates:** the camp cook; provisioning a journey with dried food; smoking a hunter's catch for a share; a winter larder kept for others; meals at a gathering.

**Correction to BACKLOG *Food spoilage* (4).** It says salt would get "its first consumer (one of the seven FAS 1 materials Rev 27 found no sink for)". Roadmap Rev 27's seven are iron, copper and tin ore, sand, ochre, sulfur and **saltpeter**; salt is not among them, and salt has no source either — the AoL decomposition lists it as a new material (`docs/crafting/PolishedWorld_Crafting_Decomposition_AoL_Complete.md:307`). Salt needs a source before it can have a consumer (CQ5).

**Exclusives** ("preservable salt fish" to fishing, and so on) stay with the roadmap's *Food professions* entry, decided once across the set.

**Coin:** none proposed. **Logging:** cooking and preserving are `craft`, eating is `consume`, spoiling is `crumble` — no new kinds (`world/activity_log.py:60`). **Ledger:** every new item gets its source and sink row in the same commit.

---

## 14. Multiplayer and server load

- **No per-item tickers.** Food, fires, racks and frames are all read on demand. The only scheduled work is two or three additions on the existing `WeatherScript` every 1800 s.
- **Statue cost.** Login and logout touch the character's carried food once: O(inventory), on events that already run hooks.
- **One fire, several cooks.** Each cook's batch is on their own timed-action slot; the fire's capacity is checked and claimed at the start of each batch in one synchronous step, as `ResourceNode.harvest()` does (`typeclasses/resources.py:105`). `feed fire` writes `burns_until` in one step; two feeds both count.
- **Racks in public rooms.** Anyone can see a rack; whether anyone can take from it is CQ12.
- **Interrupts.** A batch whose fire goes out mid-cook is interrupted through `world/timed_actions.py`'s `interrupt` (`:229`); the raw portions are untouched until the batch completes.
- **Object count.** Fewer stray objects over time, not more: spoiled food and cold wilderness fires crumble and are swept (E7).

---

## 15. Immersion extras

- **The smell of food.** A cooking fire adds a line to the rooms beside it; a fishing camp smells of smoke.
- **Naming the dish.** A cook with a high band may name a batch (Achaea's design tradeskills, §2.4) within a short word list.
- **Woods that taste.** Smoking over different woods gives the product a word in its name (Haven & Hearth, §2.2) once woods are distinguished.
- **Spices and salt tablets** (AoL): spices lengthen *well fed*; salt tablets are a reader for *Temperature & exposure*.
- **Judging food in secret.** A Perception test, rolled in secret, lets a sharp nose tell *turning* a stage early — `perception`'s first call-site if the light-and-darkness work has not taken that place first (Legend p. 39; CQ13).
- **Feasts for the gazette.** The first winter larder, the largest smoked catch (BACKLOG *In-world gazette*).

---

## 16. Layers — a suggested order

1. **Slice 1 (the smallest real thing, and what BACKLOG *Food spoilage* requires together):** `world/decay.py` with the spoilage index (CP8); the clock and stages on `Food` (CP7); meat inheriting the corpse's time (E3); `eat` reading the stage (CP14, without the queasy buff if the decomposition prefers); the generalised sweep (E7); the fire (CP1–CP3); `cook` for roast rabbit (CP5); the drying rack and dried rabbit (CP11). Rabbit and berries only.
2. **Slice 2:** the statue pause (CP9); cold storage (CP10) with housing's larder or a staff-flagged cellar; quality in the restore (CP16); well fed (CP15).
3. **Slice 3, with fishing slice 1:** fish on the same clock; the smoking frame (CP12).
4. **Slice 4:** salt, once its source is decided (CQ5); the Preserving Kit; salting (CP13).
5. **Slice 5, after the kiln:** pots and dishes by category (CP6); named dishes.

**Prerequisites:** none for slice 1. **Not prerequisites:** Stage 5 (burns wait, CP-L5), the webclient, the exclusives decision (except salt fish, which slice 4 waits on).

---

## 17. Seams in today's code (read at `6c07785`)

| Need | Seam | Where |
|---|---|---|
| Food data | `Food(Object)`: `restore_amount`, `consume_message` | `typeclasses/consumables.py:19–25` |
| Eating | `CmdEat.func`: restore, message, delete, log | `commands/consumption_commands.py:18`, `:29–53` |
| Food prototypes | `berries`, `rabbit_meat` (comment: cooking holds the payoff) | `world/prototypes.py:94–101`, `:893–909` |
| Fuel, fire-starter | `wood`, `stick`, `flint` prototypes; flint's "fire-starting" sink is intent | `world/prototypes.py:385`, `:329–339`; `world/material_registry.py:135–139` |
| Salt | absent; saltpeter is a different material; salt is `[NEW MATERIAL]` in the AoL decomposition | `world/material_registry.py:171`; `docs/crafting/PolishedWorld_Crafting_Decomposition_AoL_Complete.md:307` |
| Kiln (pots) | blocked on a station and firing | `world/material_registry.py:337` |
| Corpse decay, its backwards shape, cold storage read | `decay_modifier`, `_elapsed_game_hours`, `crumble` | `typeclasses/corpse.py:49–50`, `:92–133`, `:166` |
| Harvest decay gate and spawn | step 8, `spawn(part["prototype"])` | `commands/hunting_commands.py:275–277`, `:306–327` |
| Generic Craft skill | `craft` (DEX+INT) | `typeclasses/characters.py:416–424` |
| Recipe discipline, duration, quality, gate | `discipline`, `craft_duration`, `_quality_for`, `pre_craft` | `world/crafting_base.py:59`, `:81–87`, `:229`, `:260` |
| Quality bands | `SUPERIOR`, `SERVICEABLE`, `POOR`, `SHODDY` | `world/crafting_quality.py` |
| Timed, interruptible acts | `start()`, `claim()`, `interrupt()` | `world/timed_actions.py:107`, `:198`, `:229` |
| Statue on logout; login hook | `at_post_unpuppet`, `at_post_puppet` | `typeclasses/characters.py:472–491`, `:494` |
| Room arrival hook, the sweep | `at_object_receive`, `sweep_expired_corpses` | `typeclasses/rooms.py:358`, `:391` |
| Shelter | `is_indoor` read by thermal and weather | `world/thermal.py:68`; `world/weather.py:84` |
| Global weather tick | `WeatherScript.at_repeat`, every 1800 s, keeps only `previous_weather` | `typeclasses/scripts.py:112–143` |
| Game clock, season | `get_absolute_gametime()`, `get_season()`; `TIME_FACTOR`, `TIME_UNITS` | `world/gametime_utils.py:88`, `:132`; `server/conf/settings.py:55–64` |
| Lazy anchor done right | `ResourceNode.last_regen`, advanced by whole intervals | `typeclasses/resources.py:52–59`, `:85–96` |
| Number-free state text | `_availability_phrase` | `typeclasses/resources.py:129` |
| Buffs | `Starving`, `ColdStress`, `DeathWeakness` … | `world/survival_buffs.py:21–116` |
| Economic events | `activity_log.record`, ten `KINDS` | `world/activity_log.py:60` |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **CQ1** — Is a fire an object or a room flag? *Leaning (chat, 2026-11-07): an object — it has fuel and a state, it can be fed, seen and smelt, it is the hearth in a house, and it is the thing temperature and light will read.*
- **CQ2** — Shelf lives against real time. *Leaning: raw about 1 game day, cooked 3, dried and smoked 1–2 game months (1–2 real weeks), salted a season (about 3 real weeks), with the multipliers of CP7; tuned against the cohort's real log-in rhythm, never shortened below what a trade between two players who log in on different days needs.*
- **CQ3** — A cooking skill of its own, or `craft`? *Leaning: `craft` in a new `cooking` discipline; Craft (Cook) and (Butcher) arrive when specialised Craft arrives for every craft.*
- **CQ4** — What does eating off food do? *Leaning: refused unless forced; forced, it restores a little and gives a short queasy buff, the hook for the Disease system.*
- **CQ5** — Where does salt come from? *Leaning: a salt lick or brine spring as an authored `ResourceNode`, or brine boiled down over a fire; the choice is outside this document (it touches the world's geography and the exclusives).*
- **CQ6** — Which preservation recipe ships first? *Leaning: drying, because it needs no salt and reads weather — slice 1 meets the sink and its answer in the same week, as the BACKLOG entry requires.*
- **CQ7** — Lighting a fire: which skill? Legend puts it under Survival, which this codebase does not have as a skill. `craft`, `hunting` (as Survival's hunting uses went), or an automatic success in dry weather with a test only in wind and rain?
- **CQ8** — Fire capacity and how much wood buys how long.
- **CQ9** — One weather-history change for both designs: this document's indexes (CP8, CP11) and Hunting Design §7's history list on `WeatherScript`. Does the corpse move onto the spoilage index in the same change (E5), or keep its shape for display?
- **CQ10** — Is the quality on a cooked item the same field Hunting Design TP12 wants on harvested parts?
- **CQ11** — Real seconds for a batch, per portion, at 4× speed.
- **CQ12** — Racks and frames in public rooms: can anyone take from them (theft that leaves tracks, Hunting Design TQ12), or owner-only?
- **CQ13** — Judging freshness with Perception: does it ship with slice 1, or wait for *Light & darkness*, which also wants Perception's first call-site?
- **CQ14** — Water: does cooking a stew use the waterskin's charges? Ties to BACKLOG *Weather inertia*'s wet axis and the alpha's water decision (#6).

---

## 19. Considered and not proposed

- **Short real-time spoilage that runs while a player is away.** Armageddon's lesson (§2.1).
- **Food that never spoils once cooked.** Then nothing needs preserving and nobody needs a cook.
- **A flag "preserved" on the original item.** BACKLOG *Food spoilage* (4): preservation is a new item from a recipe.
- **Per-item or per-fire tickers.** CG7; everything is read on demand.
- **Copying `Corpse.decay_modifier`'s shape.** It runs backwards when the weather turns (§9).
- **Food as the engine of character statistics** (Haven & Hearth's FEP). Legend's characteristics are not grown by eating.
- **NPC cooks, grocers or innkeepers selling meals.** Pillar 1.
- **Reaction-timing minigames at the fire.** The skill is in choices — what to cook, how patiently, how to keep it — and in the roll.
