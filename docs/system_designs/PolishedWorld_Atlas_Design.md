# PolishedWorld — World Atlas Design Notes (the map the world is cut from: Azgaar's generator as the source, a frozen extraction, one cell to a region, biomes, rivers and climate as data, realms as lore, the frontier as a window)

> **Rev 1 · 2026-11-10** — first version, docs only, with roadmap Rev 69, BACKLOG Rev 96, README Rev 47 and the series handoff `docs/system_designs/HANDOFF.md` Rev 10. Written from a design chat, the nineteenth note in the one-system series and, like Comfort and Homunculi, written off the queue at Adam's request: he asked what Claude thought of using Azgaar's Fantasy Map Generator (`azgaar.github.io/Fantasy-Map-Generator`) to make PolishedWorld's world — a later step he wanted to talk through now. The chat's answer was yes, as an atlas and a canon, not as a room generator; Adam then asked for a BACKLOG entry and this note. The generator was read at version 1.157.0 (commit `4b34afc`, 2026-11-09) from a shallow clone of `github.com/Azgaar/Fantasy-Map-Generator`; PolishedWorld was read at `main` `f157bc0`. Adam answered the proposal with a bare "kör", so its questions are QQ1–QQ4 with the chat's leanings; QQ5–QQ14 were found while writing. Nothing is decided; no proposal changes live behaviour, so there is no departures section and the system's content starts at §6.
> **Canonical:** `docs/system_designs/PolishedWorld_Atlas_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/BACKLOG.md`, World & Rooms, *World atlas — Azgaar's Fantasy Map Generator as the source* — a new entry (Rev 96), because nothing owned the world's macro geography: roadmap Stage 6 owns the rooms (grid and wilderness), BACKLOG *Biome fragment library* owns a room's words, and the queue's *biomes & regional resources\** owns what is found where. The roadmap's Stage 6 gains a dated *Atlas* line and the decision log's *[DEFERRED] Procedural world generation* a note that a fixed atlas does not lift the deferral (Rev 69). *Biome fragment library* gains a note that its keys are the vocabulary the atlas maps onto (QP12), and *⛔ Regional weather* a note that the atlas is a region concept it can hang on (QP17); both keep their Status.
**When to read:** at roadmap Stage 6's design session (scale, QQ2; the frontier, QP22–QP23; the grid/wilderness split, QQ12); when BACKLOG *Biome fragment library* is designed (the biome keys, QP12, QQ13); when the queue's *biomes & regional resources\** is designed (the helper, QP13–QP15); when BACKLOG *⛔ Regional weather (per-area rather than global)* is unblocked (QP16–QP17); when *maps & navigation* is designed (Lore (Regional), QP-L1; cartographers, QP-L4; the website map, QQ7); when the newcomer's economy note places the starter settlement (QP24).

---

## 1. The idea in one paragraph

Before anyone builds a wilderness room, the world already has a shape: a coast that bends north into a cold sea, a river that drains a ring of hills, a dry heath in the rain shadow of a ridge, the overgrown line of a road that once ran from a city no one lives in any more. That shape is drawn once, in Azgaar's Fantasy Map Generator, chosen by hand from as many seeds as it takes, and then frozen: a small file in the repo says, for every patch of land, what grows there, how high it lies, whether water runs through it, how warm its year is and how wet. The game never draws a map; it only looks things up. A player at the edge of the frontier sees the hills the atlas says are there, drinks from the river the atlas says runs there, and cannot yet cross the bog the atlas says lies beyond — until enough people live here that staff open the next stretch of land, which was always there.

---

## 2. Prior art

### 2.1 Daggerfall — the lesson

Sources: the UESP wiki's pages on `WOODS.WLD` (`en.uesp.net`, *Daggerfall Mod:WOODS.WLD format*), the Daggerfall Workshop blog posts on climate processing and the streaming world (`dfworkshop.net`, 2009 and 2014), and a Daggerfall Unity forum thread on custom worlds (`forums.dfworkshop.net`) (read 2026-11-10). No MUD offered a lesson for this system; the slot goes to the best lineage, and Daggerfall is the game the roadmap's Stage 6 names as its scale. Paraphrased:

- Daggerfall keeps its whole world in a handful of coarse maps of the same 1000 × 500 size: one for elevation, one for climate, one for politics.
- Inside each map pixel the terrain is generated, not stored: the pixel's height is combined with smooth noise to give the small detail a walker sees.
- The climate value of a pixel decides which ground textures and which plant set appear there — a lookup from a coarse key to a set of assets.
- The Daggerfall Unity developer's own conclusion: the world is far too large to author by hand at walking scale, and it holds together because a few coherent coarse maps drive everything procedural.

**Worth taking:** author coarse, generate fine (QG1); the coarse key decides a whole set of things — here the biome decides the room's words and what grows (QP12–QP13).

**Not for PolishedWorld:** politics as live control of the land (QP19); generated content that rolls fresh each visit (QP7 makes it a function of place).

### 2.2 Azgaar's Fantasy Map Generator — the tool

Sources: the generator's source at 1.157.0 (`src/services/io/export-json.ts`, `src/model/physical/biomes-generator.ts`, `src/model/units.ts`, `LICENSE`) and its wiki pages *Knowledge Base* and *Data import* (read 2026-11-10). Paraphrased:

- A browser application, MIT-licensed (copyright Max Haniyeu, *Azgaar*). The map is a Voronoi mesh of cells over a heightmap, with climate, biomes, rivers, cultures, states, settlements (*burgs*), routes and markers generated in that order.
- It exports JSON in four kinds — Full, Minimal, PackCells and GridCells (`export-json.ts:13–17`). A packed cell carries, among others, `biome`, `h` (height), `r` (river), `fl` (water flux), `haven` and `harbor`, `area`, `burg`, `routes`, `culture` and `state` (`:129–156`); temperature `temp` and precipitation `prec` sit on the finer grid cell (`:222–223`), reached from a packed cell by its `g`. The export's settings carry the distance unit and scale (`:113–114`); temperature defaults to °C (`units.ts:16`).
- Thirteen default biomes, from Marine through Hot desert, Grassland, Temperate deciduous forest and Taiga to Glacier and Wetland (`biomes-generator.ts:25–138`), each editable in the generator.
- The current version also generates and exports an economy of its own — `goods`, `markets` and `deals` (`export-json.ts:68–71`).
- Its wiki warns that a map saved by an old version needs that old version to open it, and that the JSON and GeoJSON exports are for other tools and cannot be loaded back into the generator.

**Worth taking:** the geography, the rivers, the biomes and the climate; routes as candidate roads; name bases for places (QP9, QP11).

**Not for PolishedWorld:** its goods, markets and deals, its armies and its populations (QP10, pillar 1).

### 2.3 The Foundry VTT importer — the atlas as lore

Sources: the *Unofficial Azgaar's Fantasy Map Generator Import* module (`foundryvtt.com/packages/azgaar-foundry`, `ethck.itch.io/azgaar`) (read 2026-11-10). Paraphrased: a tabletop tool takes a generated world into Foundry not as terrain but as journals — one entry per state, culture, settlement and so on, linked to each other — so a game master reads the world rather than walks it.

**Worth taking:** the realms and settlements as linked lore rather than as places that run (QP19–QP20).

**Not for PolishedWorld:** importing everything; most of it is struck (QP10).

### 2.4 mapwright — the generator in Python

Sources: the `mapwright` package on PyPI (read 2026-11-10). Paraphrased: a pure-Python, numpy-only, seed-deterministic world generator, written clean-room from the generator's published techniques and MIT-licensed, producing cells, biomes, rivers and names as plain data — but with terrain capped at 1,500 cells.

**Worth taking:** nothing now. It is the shape a future in-repo generator could take, if the deferral in the roadmap's decision log is ever lifted (§19).

---

## 3. Design goals

- **QG1 — Author coarse, generate fine.** The atlas says what a whole region is; a room's detail is a function of where it is, never authored per room in the wilderness (§2.1).
- **QG2 — The atlas is geography, never economy.** No generated price, good, market, population or army enters the game. Pillar 1: everything is player-made, and the land only says what can be found.
- **QG3 — Frozen and versioned.** The game reads only its own extraction, committed to the repo with its provenance. A new generator version, a new seed or a click in the browser changes nothing until a reviewed re-import.
- **QG4 — Our vocabulary wins.** Biome keys, the calendar and the words a room uses are PolishedWorld's; the generator's values are inputs mapped onto them.
- **QG5 — Nothing ticks and nothing lives on a room.** Per-place data is a read-only lookup by coordinate (Evennia Reference §14.5); one read when a room is shown for a coordinate, none per tick.
- **QG6 — The frontier is small and the atlas is its horizon.** Most of the atlas is not playable at first; it is what lies beyond, and the world grows into it.

---

## 4. Legend alignment

**Rules as written:**

- **Lore (Regional)** — p. 52: a Common Skill measuring a character's knowledge of the geography, flora and fauna of the area they grew up in or spent most time in; using it in unfamiliar surroundings is at a disadvantage — an arctic mountaineer suffers a penalty in an equatorial desert — and a fumble can mean mistaking a poisonous fungus for food or placing a capital a thousand miles from where it is.
- **Strategic Time Travel Table** — p. 68: a travelling day of about ten hours covers some 30 km walking, 60 on horseback at a casual pace, 15 by wagon, and 60 (favourable) or 32 (unfavourable) by coast or river.
- **Arms of Legend** (`docs/reference/arms_of_legend.md`): settlements by type, culture, population and price factor, from the hamlet of 10–30 people to the capital of 20,000 and more (`:842–850`); the cartographer, who writes, reads and translates maps for those about to travel into unknown land (`:2988`); the navigator, who picks directions by sun, moon and stars (`:3074`).
- Legend's core has no rule for world generation, climate zones or biomes.

**Translation proposals:**

- **QP-L1 — Lore (Regional) reads the atlas.** A character's home region is a set of atlas cells or a family of biomes; outside it the skill tests at a disadvantage, as p. 52 says. Which form, and the size of the penalty, are *maps & navigation*'s; the atlas gives the regions it needs.
- **QP-L2 — Legend's travel table is the scale's yardstick.** Thirty kilometres in a walking day (p. 68) against a game day of six real hours (`server/conf/settings.py:50–64`) is the check on any room size chosen in QQ2: a day's walk should feel like a day's walk.
- **QP-L3 — The settlement table names the ruins.** A burg's generated population maps to Arms of Legend's settlement type for lore text only — *the ruin of a small town* — and the table's price factors are not used (pillar 1).
- **QP-L4 — Maps are a trade.** The cartographer and the navigator (`:2988`, `:3074`) are players' work, *maps & navigation*'s; the atlas is the truth their maps are drawn from, never a map handed to players (QQ7).

---

## 5. The loop

Proposed phases; the first three are staff work, the rest are what players meet.

1. **Choose a world.** Adam generates and edits in the browser until a map feels right, and picks where the frontier lies (QQ4).
2. **Freeze it.** The editable source file and a slim extraction go into the repo, with the generator's version and seed (QP1–QP3).
3. **Place what is authored.** The starter settlement and every grid area get a home on the atlas (QP24).
4. **Walk it.** In the wilderness, every coordinate reads its cell: the words of the room, the water, what can be foraged, how cold the year runs (QP12–QP17).
5. **Grow into it.** When the population milestone of roadmap Stage 6 is met, staff open the next cells; the land beyond was always there (QP22–QP23).

---

## 6. The atlas as an artifact

**QP1 — Two files, one source.** The generator's own saved map (`.map`) is the editable source, kept in the repo because only it can be reopened in the generator; a slim JSON extraction made from a Full export is the only thing the game reads. Both live together (QQ6).

**QP2 — The extraction is slim.** For each land cell, only what a reader needs: an id, its point and neighbours, its area, the mapped biome key (QP12), a height band, river id and flux, coast and haven, temperature and precipitation from its grid cell, and the routes that cross it. Beside the cells: named rivers and lakes, routes, and burgs and markers as named lore sites. Everything else is dropped at import (QP10).

**QP3 — Provenance travels with it.** The extraction records the generator's version, the seed, the map's id and export time (`export-json.ts:98–109`) and a hash of the source file. A test pins the extraction's schema and that no struck field (QP10) is present, so a careless re-export fails loudly.

**QP4 — Coordinates are canonical, cell ids are derived.** A cell id is trusted only within one extraction. Anything the game keys on a place — an opened frontier, a named ruin, a player's claim — stores a wilderness coordinate, and the current extraction answers which cell holds it. A re-import is then a review, not a migration of stored ids.

---

## 7. Scale — cell, region and room

**QP5 — One cell is a region, never a room.** A generator cell spans kilometres; a room a few dozen metres. A cell is a block of wilderness coordinates, and every coordinate in it reads the cell. Which cell holds a coordinate is the nearest cell point, which is containment in a Voronoi mesh (QQ5).

**QP6 — Two numbers fix the size.** The atlas's distance scale and a chosen room size give the number of rooms in a cell. As an example only, not a proposal: a cell of 25 km² is about 5 km across, so at 100 m a room it is about 50 × 50 = 2,500 coordinates. The choice is Stage 6's (QQ2), checked against Legend's walking day (QP-L2).

**QP7 — Fine detail is a function of place.** Variation inside a cell — a clearing in the forest, a stony patch on the heath — is derived from the coordinate and the atlas seed, the same answer every time, never rolled per visit and never stored (§2.1's noise). The leaning for the first slice is a cell that reads the same throughout.

**QP8 — Borders blend in words.** A coordinate near a neighbouring cell of another biome may borrow a line from it — *the trees thin toward open heath* — so walking across a border is a change you see coming, not a wall.

---

## 8. What is kept and what is struck

**QP9 — Kept:** the coastline, lakes and islands; heights, read as bands (lowland, upland, mountain); biomes; temperature and precipitation; rivers with their flux; routes, as candidate roads and old tracks; markers, as candidate landmarks and ruins; the name bases, for naming places.

**QP10 — Struck at import:** goods, markets and deals; military and regiments; populations, development and prosperity; provinces and diplomacy as anything that acts. Pillar 1 forbids the first; a frontier empty of NPC realms (QP19) needs none of the rest.

**QP11 — Place names may come from the atlas.** Rivers, hills and ruins can keep the generator's names or be renamed by hand; character names are never drawn from it (Names Design is about people, and players name their own).

---

## 9. Biomes, rivers and the "what is here" helper

**QP12 — One mapping table, our keys.** The generator's thirteen biomes map onto the biome keys BACKLOG *Biome fragment library* owns (`forest`, `meadow`, `mountain`, `swamp`, …), many to one where needed — Temperate deciduous forest and Temperate rainforest may both read as forest. The table lives with the importer, and a test checks that every generator biome present in the extraction has a key. Whether height overrides biome (a mountain from height, not climate) is QQ13.

**QP13 — The helper starts from the atlas.** Water VP8, Foraging RP13, Fishing FQ5 and Forest §14 each name one helper that answers *what is here* — fixtures in authored rooms, terrain in the wilderness. In the wilderness that terrain is the atlas's cell: biome, height band, river, coast. The helper itself is the queue's *biomes & regional resources\**; this note gives it its ground.

**QP14 — Rivers, lakes and coast are water.** A coordinate on a river's course reads river water, graded by flux into brook, stream and river for fishing; a lake feature reads still fresh water; a coast or haven cell reads the sea, which is brine (Water). Water VP8's *what water is here, and what kind* gets its answer from these three.

**QP15 — What grows where is ours.** The resources of a biome come from PolishedWorld's tables keyed by biome key, never from the generator's goods (QG2). Regions differ because biomes differ, and that difference — clay by the river, flint on the chalk, furs in the taiga — is what travel and markets trade on.

---

## 10. Climate

**QP16 — Temperature is an offset, not a thermometer.** The generator gives each cell a yearly mean. The home cell of the starter settlement is the baseline; another cell's difference from it shifts how the season reads there — a cold upland might read autumn as winter for `thermal_regime()` (`world/thermal.py:46–80`), which today reads season and weather from room states. Temperature KP3's reserve drains only where the climate is hostile; the atlas says where that is. Bands or a continuous shift is QQ14.

**QP17 — Precipitation weights the weather.** Weather today is one global state, rolled from the season's allowed set (`world/weather.py:23`, `:28`, `:44`; read by `:89`). When BACKLOG *⛔ Regional weather (per-area rather than global)* is unblocked — it is BLOCKED because rooms have no region and no biome key to hang it on — a region's precipitation weights the roll and its temperature decides rain against snow. The atlas gives that entry its regions and its inputs; the split itself is that entry's.

**QP18 — The calendar stays ours.** Thirteen months and four seasons (`world/gametime_utils.py:56–61`) hold everywhere; the generator has no seasons and the atlas adds none. A map that crosses the equator does not flip the seasons (QQ9).

---

## 11. Realms, burgs and the lore

**QP19 — A world that has drawn back.** The generator's states and burgs become the old world: realms that withdrew, fell or forgot this coast. Inside the frontier a burg is a ruin with a name and a route is an overgrown road — places to find, not places that trade. This is the roadmap's story-justified frontier (Stage 6's goal) and it keeps pillar 1 whole: no NPC realm sells anything.

**QP20 — Beyond the frontier, words only.** Distant realms may live on in tales, a traveller's line or the gazette (BACKLOG *In-world gazette — a paper per game-month, read in game and posted outside*), but never as trading partners, quest givers or armies. Whether they still stand or are gone is QQ3.

**QP21 — Ruins carry their old size.** A ruin's text reads the burg's former size through Arms of Legend's settlement types (QP-L3) — *the grassed-over walls of what was a large town*. Nothing else of the burg is kept.

---

## 12. The frontier as a window

**QP22 — The playable land is a set of open cells.** The rest of the atlas is horizon. A coordinate at the frontier's edge refuses the step with a reason found in the land — a bog without a path, a ridge too steep, an old road lost under scrub — never an invisible wall. Which cells are open is staff data, keyed by coordinate (QP4).

**QP23 — Opening land is a staff act at a milestone.** Roadmap Stage 6 ties the world's growth to population; when a milestone is met, staff open neighbouring cells. Nothing opens by itself in the first slice. An opening is announced in the world, and is the gazette's natural headline.

**QP24 — Authored places sit on the atlas.** The starter settlement and every grid area are placed at a chosen cell, so their weather, climate offset and what grows around them agree with the land outside. The six seeded rooms (`world/seed_data.py`, from `:81`) get a home cell; the Old Temple's cell is the climate baseline (QP16). The interim rule that nodes are placed only in bounded authored areas (roadmap decision log, Rev 27) is unchanged by the atlas.

---

## 13. Economy

**Sources:** none. **Sinks:** none. The atlas creates nothing and removes nothing; it decides *where* things can be found.

**Materials this design gives a source or a sink:** none directly. It is the map every gathering design reads: where clay banks, flint, fish, timber and furs lie (QP15), so that regions differ and goods move between them — the reason travel, carts and markets exist.

**Services:** none of its own. It is the ground for the cartographer's and the navigator's trades (QP-L4) and for guides who know a region (QP-L1).

**Coin:** none. **Logging:** an opened frontier is a staff event; whether it gets an activity-log line is QQ11.

---

## 14. Multiplayer and server load

**QP25 — Loaded once, read-only, looked up cheaply.** The extraction is read into memory once at server start and never written at runtime. The importer also writes a coarse bucket index over the map, so finding the cell for a coordinate is one bucket and a few distance checks, not a search of every cell.

- **When it is read.** Once when the wilderness shows a room for a coordinate it was not already showing — the moment Evennia Reference §14.6 already identifies as a step's cost — and never per tick.
- **No per-room state.** Nothing from the atlas is written as a Tag or an Attribute on a recycled wilderness room (Evennia Reference §14.5); no object is created per cell (§14.6).
- **No races.** Read-only data has no concurrent writers. The open-cell set (QP22) is the only mutable atlas data; it changes by staff command, rarely, and a step reads it as it stands.
- **Swaps need a reload.** A new extraction is taken in by a server reload after review (QG3), never hot-swapped while players walk.
- **Size.** A slim extraction of a few thousand land cells should be small; the spike measures it (§16 step 1).

---

## 15. Immersion extras

- **The horizon.** From a hilltop, a line names what lies beyond in the direction of the next high cell — *far to the north the land rises into blue hills* — read from neighbouring height bands.
- **Named water.** A river keeps its name along its course, so *the Ashwater* is the same river at the ford and at the mouth.
- **The old road.** A route through open land reads as a track half lost in grass, easier to follow than open country; whether it is faster is *travel/roads/boats*'.
- **Feeling the climate change.** Walking north for a game day, the season's words turn colder before the calendar does (QP16).
- **The ruin at dusk.** A named ruin is a place to rest, shelter and wonder about — never a dungeon with loot spawned in it.

---

## 16. Layers — a suggested order

0. **Now — no code.** Adam chooses a world in the browser and keeps its `.map` file, with notes on where the frontier lies (QQ4).
1. **Spike, at Stage 6's design session.** Read a Full export in Python: confirm the fields and units named in §2.2, the area and distance scale, the containment rule (QQ5) and the extraction's size. Decide QQ2.
2. **Importer and extraction, with the biome keys.** QP1–QP3, QP12 and the struck-field test, once BACKLOG *Biome fragment library* has fixed its keys.
3. **The lookup, read by the "what is here" helper.** QP5, QP13–QP15, QP25, with the first wilderness.
4. **The frontier window.** QP22–QP24, with Stage 6's first open land.
5. **Climate.** QP16–QP17, with BACKLOG *⛔ Regional weather*.
6. **The lore pass.** QP19–QP21 and the immersion lines of §15, when the land has rooms to put them in.

**Prerequisites:** roadmap Stage 6's design session; the biome keys of *Biome fragment library*. **Not prerequisites:** the alpha, the webclient, Stage 4.6, Stage 5's combat code (Stage 6 itself waits for combat in the roadmap; step 0 waits for nothing).

---

## 17. Seams in today's code (read at `f157bc0`)

| Need | Seam | Where |
|---|---|---|
| Room base | `Room(ObjectParent, ExtendedRoom, DefaultRoom)` | `typeclasses/rooms.py:54` |
| Season and time of day on a room | `get_time_of_day`, `get_season` | `typeclasses/rooms.py:174`, `:186` |
| Seasons | four seasons over thirteen months | `world/gametime_utils.py:56–61` |
| Weather | `WEATHER_STATES`, season sets, `roll_weather`, `get_current_weather` — one global state | `world/weather.py:23`, `:28`, `:44`, `:89` |
| Weather clock | `WeatherScript.at_repeat` | `typeclasses/scripts.py:112`, `:135` |
| Thermal regime | season and weather from room states | `world/thermal.py:46–80` |
| Resource nodes | `ResourceNode`, objects in rooms | `typeclasses/resources.py:39` |
| Seeded rooms | six rooms by `seed_id`, the Old Temple first | `world/seed_data.py:81` |
| Wilderness behaviour | recycled shells; state leaks; O(n) step | Evennia Reference §14.4–§14.6 |
| Biomes | none — no `biome` anywhere in `world/`, `typeclasses/` or `commands/` | — |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **QQ1** — Its own note, or does it absorb the queue's *biomes & regional resources\**? *Leaning (chat, 2026-11-10): its own note; the biomes entry stays in the queue and reads this one for its ground (QP13).*
- **QQ2** — How many rooms make a cell (QP6)? *Leaning (chat, 2026-11-10): decided at Stage 6's design session after the spike, checked against Legend's walking day (QP-L2).*
- **QQ3** — Do the realms beyond the frontier still stand, or is the old world gone? *Leaning (chat, 2026-11-10): drawn back and fallen quiet — it suits a frontier and keeps every realm out of trade (QP19–QP20).*
- **QQ4** — Map size, cell count and where the frontier lies. *Leaning (chat, 2026-11-10): open until Adam has chosen a map.*
- **QQ5** — Found while writing: is nearest-cell-point the generator's packed-cell containment in every case, or do coast and lake cells need the polygons? *Open — the spike checks it against the exported vertices.*
- **QQ6** — Found while writing: where the two files live. *Leaning: `world/atlas/` for the extraction the game reads, with the `.map` source beside it; the importer as `world/atlas_import.py`. OpenCode may edit only the files `AGENTS.md` §0 names, none of them these, so the atlas is Claude's and Adam's work.*
- **QQ7** — Found while writing: may the website show a drawn map of the frontier? *Leaning: yes, as a stylised picture for visitors — the cozy front page — while in the game every map is player-made (QP-L4).*
- **QQ8** — Found while writing: Lore (Regional)'s home region — a set of cells, a biome family, or the settlement a character starts in (QP-L1)? *Open — maps & navigation's.*
- **QQ9** — Found while writing: if the chosen map crosses the equator, do seasons flip south of it? *Leaning: no; the calendar is one for the world (QP18), and the frontier lies in one hemisphere.*
- **QQ10** — Found while writing: credit for the generator. *Leaning: a line in the extraction's provenance and on the website's about page; MIT's notice travels with copies of the software itself, which the extraction is not, but the credit is owed all the same.*
- **QQ11** — Found while writing: does opening the frontier write an activity-log line? *Open — the family of Pottery PQ13; it is a staff act, not an economic event.*
- **QQ12** — Found while writing: does the atlas change roadmap Stage 6's open grid/wilderness split? *Leaning: no — it works with either; grid areas are placed on it (QP24), wilderness reads it (QP5).*
- **QQ13** — Found while writing: does height override biome — a mountain from height, whatever the climate? *Leaning: yes for the top band; the fragment library decides how a snowy taiga mountain reads.*
- **QQ14** — Found while writing: the climate offset as bands (a cell reads one season colder) or as a continuous shift on the thermal thresholds? *Leaning: bands first — words change in steps, and Temperature's regimes are already steps.*

---

## 19. Considered and not proposed

- **The generator at runtime.** Generating the world while the server runs, or on every wipe; QG3, and the roadmap's deferral of procedural generation.
- **One cell, one room.** A world of a few thousand rooms each kilometres wide; QP5.
- **The generator's economy.** Its goods, markets and deals as a starting economy; pillar 1, QG2.
- **Living NPC realms.** States that tax, trade or march; QP19.
- **Populations as spawns.** Peopling the land from the generator's population numbers; pillar 1, and a frontier is empty by design.
- **A Python generator in the repo now.** `mapwright` (§2.4) — capped at 1,500 cells, and a generator is the deferred thing; reconsider only if the deferral is lifted.
- **Hand-authoring every wilderness room.** The Daggerfall developer's point (§2.1): it does not survive the scale.
- **A full world map given to every player.** It would erase *maps & navigation* and the cartographer's trade before they exist (QP-L4).
