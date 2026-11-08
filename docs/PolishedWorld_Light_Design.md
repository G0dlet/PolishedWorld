# PolishedWorld — Light & Darkness Design Notes (light levels, torches and candles, kindling, seeing in the dark)

> **Rev 1 · 2026-11-08** — first version, docs only, with BACKLOG Rev 79 and README Rev 33. Written from a design chat, the tenth in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`, `docs/PolishedWorld_Housing_Design.md`, `docs/PolishedWorld_Hunting_Design.md`, `docs/PolishedWorld_Cooking_Design.md`, `docs/PolishedWorld_Temperature_Design.md`, `docs/PolishedWorld_Farming_Design.md`, `docs/PolishedWorld_Textiles_Design.md`, `docs/PolishedWorld_Water_Design.md` and `docs/PolishedWorld_Foraging_Design.md`. Nothing in the game gives light today and nothing is harder in the dark, so the notes name every place they would change live behaviour (§6). **Nothing here is locked.** Every numbered item is a proposal (LP…), a goal (LG…) or an open question (LQ…); the letter is for *light*, and the departure rows are I1–I2 (*illumination*), because L1–L7 are the launch-minimum tasks. In the chat Adam approved writing the document from the proposal without answering its four questions; three of them are recorded here as LQ1–LQ3 with the leanings recommended in the chat, recorded as *leanings*, not as decisions, and the fourth (the prefix) is this document's letters. The leanings under the other questions are this document's own. Prior art was read on 2026-11-08; code seams were read against `main` at `acbc37c` (Evennia 6.1.0).
> **Canonical:** `docs/PolishedWorld_Light_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/BACKLOG.md`, *Environment & Weather*, *Light & darkness* — annotated (Rev 79) to point here and not replaced; *Season-dependent day length* gains a note (Rev 79) because this design leans on it (LQ2). The roadmap has no entry for light and gains none.
**When to read:** at the start of the *Light & darkness* decomposition; with *Season-dependent day length*; when Cooking Design's fire is decomposed (CP1–CP4 — the fire is a light source here, LP3, LP6); when Textiles WP12's rags ship (the rag torch, LP5); when rendering, tallow or beekeeping is designed (the candle, LP5); when Hunting Design's `stalk` is decomposed (TP6 — LQ3); when the first Perception call-site is built (Cooking CQ13, Foraging RQ14 — LP10); when Foraging's herb nodes ship (their roll reads LP10); when Stage 5 decomposes stealth or combat (§4); when Stage 6 decomposes wilderness (§14).
**Departs from shipped behaviour in two places**, listed with their source lines in §6: `look` in a room that is dark shows less, and `hunt` takes a penalty when the light is poor.

---

## 1. The idea in one paragraph

The day is bright and the night is not, and how dark the night is depends on the sky. Under a clear sky a character sees by starlight — everything is there, a little harder to make out; under cloud, rain or snow the night is dark, a room is a few shapes and its exits, and the people in it are *someone*; in a cellar or a cave it is pitch black. Light is something someone makes and carries. A rough torch is a stick and a bundle of fibre; a better one is wrapped in rags and dipped in fat or resin; a candle is tallow or wax on a wick. Each burns for its hours and is gone, and each lights the whole room for everyone in it, so the person who brings a torch into a dark room is doing everyone a favour. Flame comes from a bow drill and a pinch of tinder, from a fire, or from another torch; rain puts a torch out. Nothing about it ticks: the light in a room is worked out when someone looks.

---

## 2. Prior art

### 2.1 Achaea — the lesson

Sources: Achaea's public forums, a discussion of what nightsight does and a thread of class-concept suggestions (`forums.achaea.com`, read 2026-11-08). Paraphrased:

- Two classes have a spell that makes a room dark, and players report that it is rarely used, because it is easy to dispel and nightsight is common.
- A suggestion thread proposes that a certain staff should act as a lantern: held or dropped, it would spare everyone in the room the need for nightsight.

**Worth taking:** light that belongs to the room, not to the looker — whoever brings it, everyone sees (LP3).

**Not for PolishedWorld:** a permanent, near-universal way to see in the dark.

**The lesson (the series' "Achaea lesson"):** when the answer to darkness is permanent and everyone has it, darkness stops being part of the game — even a spell built to make it is not worth casting. MUME's cheap, ever-lit ruby (§2.2), Vintage Story's torch holder (§2.4) and Genesis's debate over torchstones (§2.5) are the same lesson from three other directions. The rule taken: **every light burns something** — no permanent light, no holder that stops the clock, no darkvision for sale (LG1).

### 2.2 MUME — three kinds of room, and a world that goes dark

Source: the MUME wiki, *Newbie Guide Light Sources and Seeing* (`docs.mume.org`). Paraphrased:

- A room is OUTSIDE (lit by the sun, so dark at night), LIT (always lit — buildings assumed to have lamps) or DARK (caves, mines, ruins, dense forest — dark unless someone brings light). Summer days are long and winter nights are long. The moon does nothing for sight.
- Weather does not hurt sight, except fog; heavy fog blinds almost everyone.
- A campfire lights its room and keeps it lit when you walk away; a lit lantern dropped on the floor lights the room; burning a pile of corpses lights it too.
- Torches are held, last a night, and are useless weight once burnt out; a *crude torch* can be taken from a campfire but does not last long; lanterns burn oil, can be refilled, and snuffing one saves its oil.
- In the dark, others show as *Someone is here*, and most commands that target a person or creature fail.
- A thief or scout can cover a light to hide.

**Worth taking:** the three kinds of room as a base level and a pin (LP2); fog as the weather that matters (LP2); a fire that lights a room (LP3); the crude brand from a fire (LP6); *someone* for unseen people (LP9); snuffing to save fuel (LP4).

**Not for PolishedWorld:** torches and oil bought in shops (pillar 1); the cheap permanent light gem (§2.1).

### 2.3 Aardwolf — a number nobody used

Source: Aardwolf's in-game help *Brightness*, as published on its wiki (`aardwolf.com/wiki`). Paraphrased:

- Version 3 replaced *dark or not* with a light value per room: zero is enough to see, a flagged-dark room starts at −1, an outdoor room loses one at night, and every light in the room — an object, a campfire, a player's light — adds one.
- The help file says itself that the variable framework is barely used: almost every room is 0 or −1.

**Worth taking:** lights add to the room for everyone, including lights other players carry (LP3); indoor and outdoor as different bases (LP2).

**Not for PolishedWorld:** a sum of sources — stacking candles until a cave is bright. A scale the builders never used is the warning: four levels with names, each with a job (LP1).

### 2.4 Vintage Story — a torch that does not burn in the hand

Source: the Vintage Story wiki, *Torch* and *Light sources*, and its forums (`wiki.vintagestory.at`, `vintagestory.at/forums`). Paraphrased:

- A torch is a stick and a dry material; it burns only once placed (48 in-game hours) and lasts indefinitely carried; rain puts out a placed torch, which can be relit from a lit torch for free, from a firepit or with a firestarter.
- A torch holder keeps a torch lit indefinitely, through rain and burn time.
- Players have asked that a torch in the hand burn down too, and that grass or resin refresh it.

**Worth taking:** rain puts a torch out and it can be relit (LP8); lighting one flame from another is free (LP6); grass and resin as torch materials (LP5).

**Not for PolishedWorld:** light that burns only when placed, and a holder that stops it burning — the counter-example to LG1.

### 2.5 Genesis and Armageddon — how much darkness, for whom

Sources: Genesis MUD forums, a 2023 thread on darkness levels and *torchstones*; Armageddon MUD's forums, a thread on sneaking and light. Paraphrased:

- Genesis players argued over permanent light items and how many levels of darkness a game needs; one put it plainly: if too many characters can see in the dark, seeing in the dark is worth nothing.
- Armageddon players noted that light there is all-or-nothing and asked for levels between, so that a faint light could let a sneaking character see their feet without being seen from afar.

**Worth taking:** a handful of levels, not a scale (LP1); faint light as its own level (the candle, LP3); stealth as a reader of the same levels, later (§4, LQ3).

---

## 3. Design goals

- **LG1 — Every light burns something.** No permanent light, no holder that stops the clock, no darkvision for sale (§2.1).
- **LG2 — The answer ships before the harm.** A player can make and light a torch before any room is dark (§16); darkness is never a wall — exits always show, and the shipped free nodes work in any light (Foraging RG3).
- **LG3 — One number, read in one place.** `light_level(room)` is to sight what `thermal_regime(room)` is to warmth (`world/thermal.py:46–80`; Temperature KG8): season, weather, time, place and lit things enter once, as terms in one function.
- **LG4 — Legend's steps, not invented numbers.** The levels are the rulebook's darkness rows (§4).
- **LG5 — Nothing ticks, and a statue burns nothing.** Light is worked out on read; a lit thing knows when it burns out; logging out snuffs what you hold (LP4, LP11).
- **LG6 — Light is shared.** A light lights the room for everyone in it (§2.1–§2.3): bringing light is a service.

---

## 4. Legend alignment

**Rules as written:**

- **Darkness in combat** — core p. 135, close combat situational modifiers: fighting in partial darkness −20 %, in darkness −40 %, blind or in pitch black −60 %. p. 141, ranged target visibility: target obscured by smoke or mist or in partial darkness −20 %, by thick smoke or fog or in darkness −40 %.
- **Difficulty and Haste** — p. 39: the grades Difficult −20 %, Hard −40 %, Very Hard −60 %; the darkness rows are the same steps. The page's own example: hiding in a dark wood as night falls is a Stealth test that the darkness makes *easier*.
- **Perception (INT+POW)** — p. 52: the senses, for finding things and people; no darkness table of its own. p. 40, difficulty examples: spotting a gold coin on the floor of a well-lit, uncluttered room is Simple (+20 %).
- **Stealth (DEX+INT)** — p. 55: opposed by Perception and modified by the situation.
- **Candle** — p. 112: one, two or six hours; lights a one-metre radius; any wind stronger than a slight breeze puts it out. **Weather** — p. 232: in a light air candles gutter; in a breeze they go out.
- **Lanterns** — p. 114: a basic lantern of brass or bone shields an oiled or waxen mantle, lights a three-metre radius clearly and burns two hours on a flask of oil; the cowled lantern throws a ten-metre beam. p. 115: the paper hanging lantern, a hazy four-metre glow. **Oil** — p. 116: a flask fuels a lantern two hours; jellied oil is smeared on torches.
- **Torch** — p. 119: one end wrapped in cloth and dipped in pitch; lit with flint and tinder in one round; burns one hour; lights a three-metre radius; as a weapon, a club at −10 % that does 1D4 fire damage and goes out on a fumble or a critical. A six-hour torch, and a waterproof torch that lights even when wet.
- **Craft** — p. 57: Craft (Candlemaker) is one of the listed crafts.
- **Arms of Legend** (`docs/reference/arms_of_legend.md`): candles from the stubby hour-candle to temple votives, used by miners to mark time (`:172–176`); the candle snuff (`:180`); the candlemaking kit, wicks with tallow or wax, 500 hours of candles (`:182`); flint and tinder lights a fire in a minute without a Survival roll under common conditions, with penalties in high wind, driving rain or poor kindling (`:262`); the hand-striker (`:288–290`); lanterns (`:330–334`); oil (`:362–366`); the torch, cloth dipped in pitch, oil or the like (`:486–490`); the six-hour torch, a metal-capped pole holding two flasks of oil (`:492`); the waterproof torch, sealed with pitch and wax (`:494`); beeswax (`:514`); the chandler, who works wax into candles and lamp mantles (`:2992`).

**Translation proposals:**

- **LP-L1 — The darkness rows are the levels.** Partial darkness, darkness and pitch black become *dim* (−20), *dark* (−40) and *pitch black* (−60), beside *bright* (0) (LP1). The +20 % of a well-lit room (p. 40) is not used: bright is the normal case, not a bonus.
- **LP-L2 — Radius becomes a level.** A room is the unit of sight. A one-metre light (the candle) lights a room to *dim*; a three-metre light (torch, lantern, fire) lights it to *bright* (LP3).
- **LP-L3 — Hours are game hours.** A one-hour torch burns one game hour, fifteen real minutes at the 4× clock (`server/conf/settings.py:50–64`; LQ1).
- **LP-L4 — Lighting is a short act, not a test, when it is dry.** Legend lights a torch in a round and AoL a fire in a minute without a roll; here kindling is a short timed act with no roll in dry weather, and nothing kindles outdoors in rain or snow (LP7). The skill question is Cooking CQ7's and is answered once for both (LQ5).
- **LP-L5 — Stealth's darkness bonus and the torch as a weapon wait for Stage 5.** p. 39's mirror — darkness helps whoever hides — is stealth's, and the torch as a club is combat's. This design supplies the level they will read (LQ3).
- **LP-L6 — Craft (Candlemaker) is the shipped `craft` skill.** One generic craft skill and five disciplines (`world/recipe_mastery.py:81–87`); which discipline a torch or a candle belongs to is LQ11.
- **LP-L7 — Legend's prices are not used.** Pillar 1.

---

## 5. The loop

Proposed phases; each is something someone can sell.

1. **Gather.** Sticks and fibre from the free nodes; later rags, fat, resin, wax (LP5).
2. **Make.** A torch or a candle is a recipe (LP5); a bow drill is a tool (LP7).
3. **Kindle.** Flame from the bow drill and tinder, from a fire, or from another lit thing (LP7).
4. **Carry or set down.** A light lights the room it is in, for everyone (LP3).
5. **Burn.** Fuel is time; snuffing keeps what is left; rain puts it out (LP4, LP8).
6. **Do what the dark made hard.** See the room; hunt without the penalty (LP9, LP10).

---

## 6. Departures from shipped behaviour

Each row is a change to behaviour that `main` has today; each is a proposal.

| # | Shipped today | Proposed | Where shipped |
|---|---|---|---|
| I1 | `look` shows a room the same at every hour; only the description's text changes with time and weather | By the room's level: *dim* shows everything; *dark* replaces the description with one line, shows exits, lit things and people carrying light, and anyone else as *someone*; *pitch black* shows exits and lit things only (LP9) | `typeclasses/rooms.py:301–339`; ExtendedRoom's `get_display_desc` (`evennia/contrib/grid/extended_room/extended_room.py:462`, v6.1.0), not overridden by the project's Room |
| I2 | `hunt` rolls `opposed_check(hunting, …, attacker_mod=physical_modifier())` at any hour | `attacker_mod` adds `light_modifier()`: −20 at dusk, dawn and on a clear night, −40 on a dark one (LP10) | `commands/hunting_commands.py:98–99` |

Unchanged: `forage` on the shipped nodes, in any light (Foraging RG3; `commands/foraging_commands.py:54`); the time-of-day and weather texts (`typeclasses/rooms.py:79–100`); `thermal_regime()` (`world/thermal.py:46–80`); the weather roll (`world/weather.py:23–33`); the temple's `candles` chore (`commands/work_commands.py:204–213`); every other roll.

---

## 7. Light levels

**LP1 — Four levels, on Legend's steps.** *bright* (0), *dim* (−20), *dark* (−40), *pitch black* (−60) (LP-L1). The level is derived on read and never stored, in one function — proposed `light_level(room)` in a new `world/light.py`, the shape of `thermal_regime()` (`world/thermal.py:46–80`), and the room's state comes from `room.room_states`, which already merges time, season and weather with any manual pins (`typeclasses/rooms.py:198–252`).

**LP2 — The base level comes from time, sky and place.** Read through the seven periods (`world/gametime_utils.py:46–54`, `:121`) and the four weather states (`world/weather.py:23`):

| Place | morning, day, afternoon, evening | dawn, dusk | night |
|---|---|---|---|
| Outdoors, clear | bright | dim | dim |
| Outdoors, raining or snowing | bright | dim | dark |
| Outdoors, foggy | dim | dim | dark |
| Indoors (`is_indoor`, `world/thermal.py:68`) | bright | dim | dark |

A pin overrides the table, the same shape as `room.db.thermal_regime`: `room.db.light_level = "pitch_black"` for a cave or a cellar, `"bright"` for a hall that is always lit. The **Old Temple** is pinned *bright* — the newcomer's lit room, MUME's LIT kind, its light the candles of the shipped chore — and its description, which speaks of daylight through the doorway (`world/seed_data.py:81–92`), gains a night state. Fog dims the day because it is the one weather that hides things (§2.2; Legend p. 141 puts fog beside darkness); clear night is *dim* because starlight is light. With today's clock night is eight game hours — two real hours of every six — and dawn and dusk one more real hour between them (`server/conf/settings.py:50–64`).

**LP3 — A light lights the room, for everyone, up to its own level.** A lit thing — a torch in a hand or on the floor, a fire (Cooking CP1, CP4), later a hearth (Housing BP7) — offers a level through one duck-typed method, proposed `light_emitted()`, the way Temperature KP8 reads `radiant_warmth()`. A candle offers *dim*; a torch, a lantern or a fire offers *bright* (LP-L2). The room's level is the brightest of its base and every lit thing in it, including what the characters in it carry; sources do not add, so a ring of candles in a cave is *dim*, not daylight (§2.3). *The chat said one and two steps; written here as ceilings, which gives the same result from dark and keeps a candle useful in a cave, where one step would leave it dark.*

---

## 8. Light sources and fuel

**LP4 — Fuel is time, one model with Cooking's fire.** A lit thing carries `burns_until` (absolute game-seconds), as Cooking CP1's fire does; a snuffed one carries `fuel_left` (game-seconds). Lighting sets `burns_until = now + fuel_left`; snuffing sets `fuel_left = burns_until − now`; a lit thing read past `burns_until` is spent — it says so and is deleted (MUME: a burnt-out torch is useless weight). No ticker. A non-persistent `utils.delay` (`evennia/utils/utils.py:1145`, `persistent=False` by default) gives the holder the line *your torch gutters and goes out* at the moment it happens, with the identity-marker guard of Evennia Reference §11.27; if a reload loses the delay, the next read still finds the torch spent, so nothing depends on it. This is neither of the two models BACKLOG's entry offers — `condition` (`typeclasses/durable.py:31`) or `charges` (`typeclasses/consumables.py:28–48`) — because a torch burns whether or not it is used: it counts time, not uses, and garment wear's tick runs every three real hours (`server/conf/at_server_startstop.py:35`), where a torch lasts fifteen minutes.

**LP5 — The first light is made of what already exists.** Burn times are leanings, in game hours (LP-L3):

| Light | Inputs | Burns | Offers | Status |
|---|---|---|---|---|
| **rough torch** | stick + plant fibre — a bundle of dry grass bound to a stick | ½ h | bright | every input shipped (`world/prototypes.py:204`, `:128`) |
| **torch** | stick + rags + a binder (tallow or resin) | 1 h (p. 119) | bright | rags wait for Textiles WP12; tallow and resin are `PROPOSED_UNRATIFIED` (`world/material_registry.py:480`) |
| **candle** | tallow or beeswax + twine as the wick | 1 h, longer as better craft (p. 112) | dim | tallow needs fat: the only carcass yields meat, hide and bone (`world/harvest_templates.py:66–90`), and a rabbit is lean; beeswax needs bees |
| **brand** | a stick, taken from a lit fire | ¼ h | bright | waits for Cooking's fire (LP6) |
| later: six-hour torch, lantern, oil | metal, glass, oil | 6 h; 2 h per flask (AoL `:492`; p. 114) | bright | wait for smithing and a source of oil |

The rough torch is the bootstrap: everything in it comes from the free nodes, so a newcomer can make light before darkness bites (LG2). Tallow's first consumer is the candle, as BACKLOG's entry says, once a larger animal gives fat; a torch dipped in fat or resin outlasts a rough one, which is what makes rags, tallow and resin worth having.

**LP6 — A brand from a fire.** With Cooking's fire, `take brand from fire` lights a stick in the fire: a short torch with no recipe (MUME's crude torch, §2.2). It costs a stick and gives a reason to keep a fire going.

---

## 9. Making flame

**LP7 — One way to make flame, shared with Cooking.** Cooking CQ7 asks which skill lights a fire; this design needs the same act for a torch, so there is one step, proposed `kindle`, used by both. Two notes the chat did not settle:

- **Flint alone does not spark against flint.** A stone-age fire is made by friction — a bow drill — or by striking flint against pyrite or steel. The shipped flint (`world/prototypes.py:329–331`) is a toolmaking stone. The leaning is a **bow drill** as the first fire tool: a crafted `Tool` of sticks and twine (`typeclasses/tools.py:34`; twine `world/material_registry.py:243–250`) that wears with use, with a pinch of plant fibre spent as tinder each time (`tinder`, `world/material_registry.py:481`, stays unratified: fibre is the tinder). Flint and steel come with smithing and make it faster (LQ5).
- **Lighting from a flame is free.** A torch or candle held to a lit fire or another lit thing in the room lights at once and spends nothing (§2.4).

Kindling is a short timed act on the shared slot (`world/timed_actions.py:107`, `claim` `:198`), with no roll in dry weather (AoL `:262`); outdoors while raining or snowing nothing kindles. Indoors is always dry.

**LP8 — Weather puts flames out, one way.** An outdoor torch or candle that is read while it is raining or snowing goes out and keeps its fuel — Cooking CP3's one-way rule for the fire, so the state is monotone — and can be relit when it is dry or under a roof. A candle also goes out outdoors in wind once wind exists (Hunting TP-W1; Legend pp. 112, 232). The waterproof torch (p. 119; AoL `:494`), sealed with pitch and wax, ignores rain later.

---

## 10. Seeing in the dark

**LP9 — `look` by level.** Through the Room's display hooks: `get_display_characters` and `get_display_things`, which the project already overrides for statues (`typeclasses/rooms.py:301–339`), and `get_display_desc`, which ExtendedRoom overrides to build the stateful description (`evennia/contrib/grid/extended_room/extended_room.py:462`) and which the Room would override in turn, calling it when it is light enough. `DefaultObject.return_appearance` (`evennia/objects/objects.py:1878`, v6.1.0) composes all of them, so `return_appearance` itself is not touched.

| Level | Description | Exits | Things | People |
|---|---|---|---|---|
| bright, dim | as today | shown | shown | shown |
| dark | one line — the room's `db.dark_desc` if set, else a generic *dark shapes, too dark to make out much* | shown | lit things only | named if carrying light, else *someone* |
| pitch black | *it is pitch black* | shown | lit things only | named if carrying light, else nothing |

Exits always show (LG2; LQ4). Statues are things and follow the things column. Commands that name a thing in the room still resolve: darkness changes what is shown, and the rolls that read LP10, not what can be targeted (LQ7).

---

## 11. Checks

**LP10 — `light_modifier()` beside `physical_modifier()`.** A method on the character, proposed `light_modifier()`, next to `physical_modifier()` (`typeclasses/characters.py:603`) and the same shape: read live at the roll, never stored, and returning the penalty of the character's room level (0, −20, −40, −60). Rolls that need sight add it. In v1 that is `hunt` (I2) and the roll of Foraging's herb nodes when they ship (Foraging RP1); butchering is LQ8. **Light does not take Perception's first call-site.** `perception` has no reader today (`typeclasses/characters.py:880–881`); whichever call-site comes first — Cooking CQ13's freshness judge or another — adds `light_modifier()` like any other sight-dependent roll, so CQ13 and Foraging RQ14 need not wait for this design.

---

## 12. Offline and the world

**LP11 — Logging out snuffs what you hold.** In the statue hook (`typeclasses/characters.py:472`), every lit thing a character carries is snuffed and keeps its fuel; a statue burns nothing (LG5). A lit torch set down in a room burns on by its timestamp whoever is online.

**LP12 — Light reads the world; nothing writes to it.** The level is computed from `room_states`, the lit things in the room and the pin. Rain does not visit torches; a torch reads the rain when it is next read (LP8). The weather's own echo already tells everyone outdoors that it has started to rain.

---

## 13. Economy

**Sources (all natural or player-made):** sticks and fibre from the free nodes; rags from worn garments (Textiles WP12); fat and resin once they have sources; torches, candles and bow drills made by players.

**Sinks:** every light burns away (LP4); a pinch of fibre spent as tinder at each kindling; the bow drill's wear; a stick for every brand.

**Materials this design gives a source or a sink:** **stick** and **fibre** (a steady new sink); **twine** (the bow drill; the candle's wick); **rags** (a second sink after Foraging's first aid kit); **tallow** (its first consumer, when it has a source); **resin** (a torch binder); **beeswax** (candles, with beekeeping). New registry rows — the torches, the candle, the bow drill — are added by the decomposition that ships them, with sources and sinks, as the registry requires.

**Services:** making torches and candles; lighting a room for others (LG6) — the one who keeps a hall lit at night; guiding through the dark; a light sold at a cave mouth.

**Exclusives:** none proposed. **Coin:** none. **Logging:** a torch crafted is the shipped `craft` kind; lighting and burning out are LQ12.

---

## 14. Multiplayer and server load

- **Nothing ticks.** `light_level(room)` reads `room_states` (already computed on every `look`) and the lit things in the room and in what its characters carry — a scan of the room's contents, no queries beyond it and no writes. A lit thing can carry a tag so the scan skips everything else.
- **One write on read.** A torch read past `burns_until` deletes itself; Evennia runs commands on one reactor thread, so two readers cannot both delete it, and the second finds it gone.
- **Two hands, one torch.** Picking up a lit torch moves it; its `burns_until` moves with it. Lighting claims the shared timed-action slot, so one character kindles one thing at a time.
- **The message delay.** Non-persistent, with the identity marker of Evennia Reference §11.27, so a reload or a second lighting never fires a stale line.
- **Offline.** Snuffed at logout (LP11).
- **Wilderness.** A dropped torch in a recycled wilderness room is as short-lived as Cooking's wilderness fire (Evennia Reference §14.5–§14.6); Stage 6.

---

## 15. Immersion extras

- **Arriving with light.** The room sees *Adam arrives, carrying a torch* — and in a dark room that is all it sees of him.
- **A glow next door.** A neighbouring room in the dark shows *a light flickers to the north*, read on `look` from the exits, as Cooking CP2's smoke is — no writes.
- **The torch tells its fuel.** *burning bright*, *burning low*, *guttering* — words, not minutes.
- **Night descriptions.** Authored rooms gain `db.dark_desc` lines: what a meadow sounds like in the dark.
- **Snuffing.** A candle snuff for those who would rather not use their breath (AoL `:180`).
- **The temple's candles.** The chore's candles become real candles when *temples & faith* is designed — a sink a temple keeps (AoL `:182`).

---

## 16. Layers — a suggested order

1. **Slice 1 (light before dark):** the fuel model (LP4); the rough torch and the bow drill as recipes; `kindle`, `light`, `snuff`; the snuff at logout (LP11). Lights light rooms, but no room is dark yet — players have the answer first (LG2).
2. **Slice 2 (darkness):** `light_level()` and the pin (LP1–LP3); the Old Temple pinned bright with its night description; `look` by level (LP9, I1); `light_modifier()` and `hunt` (LP10, I2); rain on flames (LP8). With *Season-dependent day length* if LQ2 holds.
3. **With their neighbours:** the fire as a source and the brand (Cooking CP1, CP4; LP6); the rag torch with Textiles WP12; the candle with tallow or wax; herb nodes reading LP10 (Foraging RP1); the first Perception call-site reading LP10.
4. **Later:** the lantern, oil and the six-hour torch (smithing, glass, an oil source); the waterproof torch; stealth's bonus and covering a light (Stage 5); the torch as a weapon (Stage 5); light in wilderness (Stage 6); magical light, which also burns something (Stage 7, LG1).

**Prerequisites:** none for slice 1; slice 2 needs slice 1 live first; *Season-dependent day length* beside slice 2 (LQ2).

---

## 17. Seams in today's code (read at `acbc37c`)

| Need | Seam | Where |
|---|---|---|
| Time of day | seven periods; the reader; the Room's copy for ExtendedRoom | `world/gametime_utils.py:46–54`, `:121`; `typeclasses/rooms.py:153–161` |
| Room state | `room_states` merges time, season, weather and pins | `typeclasses/rooms.py:198–252` |
| Weather | four states, season sets; the roll | `world/weather.py:23–33`; `typeclasses/scripts.py:112`, `:135` |
| Thermal (the shape to copy) | `thermal_regime()`; the indoor guard | `world/thermal.py:46–80`, `:68` |
| Display | statue overrides; ExtendedRoom's desc hook; `return_appearance` | `typeclasses/rooms.py:301–339`; `evennia/contrib/grid/extended_room/extended_room.py:462`; `evennia/objects/objects.py:1878` (v6.1.0) |
| Seeded rooms | the Old Temple, indoor | `world/seed_data.py:81–92` |
| Modifiers | `physical_modifier()` | `typeclasses/characters.py:603` |
| Hunt | the roll's `attacker_mod`; butchering's difficulty | `commands/hunting_commands.py:98–99`, `:287` |
| Forage | no roll | `commands/foraging_commands.py:54` |
| Skills | `perception`, no reader; improvable set | `typeclasses/characters.py:360`, `:880–892` |
| Rolls | `skill_check`; `opposed_check` | `world/skillcheck.py:58`, `:127` |
| Wear models (not used) | `condition`; `charges`; the wear tick interval | `typeclasses/durable.py:31`; `typeclasses/consumables.py:28–48`; `server/conf/at_server_startstop.py:35` |
| Tools | `Tool` | `typeclasses/tools.py:34` |
| Materials | stick; plant fibre; flint; twine; unratified list | `world/prototypes.py:204`, `:128`, `:329`; `world/material_registry.py:243–250`, `:478–483` |
| Carcass yields | rabbit: meat, hide, bone | `world/harvest_templates.py:66–90` |
| Craft disciplines | five | `world/recipe_mastery.py:81–87` |
| Timed acts | one `ndb.timed_action`; `claim` | `world/timed_actions.py:107`, `:198` |
| One-shot delay | `utils.delay`, non-persistent by default | `evennia/utils/utils.py:1145`; Evennia Reference §11.27 |
| Statues | logged-out character as stone | `typeclasses/characters.py:472` |
| Temple chore | the `candles` task | `commands/work_commands.py:204–213` |
| Clock | 4× speed, day length | `server/conf/settings.py:50–64` |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **LQ1** — How dear is darkness? A one-hour torch is fifteen real minutes; a dark night is two real hours and eight torches. *Leaning (chat, 2026-11-08): game hours, as Legend's hours everywhere else; a clear night is only dim (LP2), so torches are mostly for cloud, rain, snow and caves. Burn times are tuning, set after play.*
- **LQ2** — *Season-dependent day length* with slice 2, or before it? *Leaning (chat, 2026-11-08): with it or before it, as BACKLOG's entry says — a midsummer night as long as a midwinter one undercuts the point; it touches `world/gametime_utils.py` and the Room's copy of the periods (`typeclasses/rooms.py:153–161`).*
- **LQ3** — Stealth's darkness bonus (Legend p. 39) against Hunting TP6's "night hinders" the stalk. *Leaning (chat, 2026-11-08): the hunter takes `light_modifier()` on their side, the stalker's darkness bonus is Stealth's and comes with Stage 5; TP6's light term becomes this design's level when both are decomposed.*
- **LQ4** — Does a pitch-black room hide its exits? *Leaning: no — hidden exits are hostile to newcomers, and the dark is already hard (LG2).*
- **LQ5** — The first fire tool: a bow drill, flint and pyrite, or flint as Cooking's text has it? One answer for both designs (Cooking CQ7). *Leaning: the bow drill now; flint and steel with smithing.*
- **LQ6** — Fog by day *dim*, fog by night *dark*? *Leaning: yes (MUME, Legend p. 141).*
- **LQ7** — Does darkness stop targeting — `get`, `look <thing>`, `forage` on a node not shown? *Leaning: no in v1; display and rolls only. Fumbling for a thing you know is there works.*
- **LQ8** — Do butchering (`commands/hunting_commands.py:287`) and crafting read `light_modifier()`? *Leaning: butchering yes, with `hunt`; crafting not in v1.*
- **LQ9** — The moon? *Leaning: no — MUME's moon does nothing for sight, and the code has none.*
- **LQ10** — When rain puts a held torch out, is the holder told at once, or on their next look? *Leaning: on read (LP12); a weather-echo line for torch-holders is a later nicety.*
- **LQ11** — Which craft discipline makes torches and candles (`world/recipe_mastery.py:81–87`; Craft (Candlemaker), p. 57)? *Open.*
- **LQ12** — Activity-log kinds for lighting and burning out: new kinds or fields on existing ones? The family of Hunting TQ10, Textiles WQ8, Farming GQ6, Fishing FQ6, Water VQ9 and Foraging RQ11. *Open.*
- **LQ13** — The temple's candles as real objects, a sink the temple keeps? *Leaning: with temples & faith.*
- **LQ14** — Does a spent torch leave a charred stub? *Leaning: no — it is deleted; charcoal comes from kilns.*
- **LQ15** — Night sight for anyone — a race, a herb, a spell? *Leaning: none until magic, and then it burns something (LG1).*
- **LQ16** — Covering a light to hide (MUME's `cover`)? *Leaning: with Stage 5's stealth.*

---

## 19. Considered and not proposed

- **A permanent light.** A gem, a torchstone, a holder that stops the clock (§2.1, §2.4; LG1).
- **Light as a sum.** Aardwolf's additive value lets candles stack into daylight and became a scale nobody used (§2.3).
- **Torches that burn only when set down.** Vintage Story's (§2.4).
- **Per-looker light radius.** A room is the unit of sight; Legend's metres become levels (LP-L2).
- **A ticker that writes light to rooms.** Light is read, not written (LG5).
- **Torches and oil from NPC shops.** Pillar 1 (§2.2).
- **Darkvision for some characters.** There are no races yet, and §2.5 says what it does to darkness when common.
- **Darkness that harms.** Darkness makes things harder, never hurts on its own; harm is cold's and hunger's.
