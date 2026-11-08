# PolishedWorld — Pottery, Kilns & Stations Design Notes (clay shaped and dried, the pit firing, the kiln, what fired clay makes, and one contract for every station)

> **Rev 2 · 2026-11-08** — moved, docs only, with roadmap Rev 60, BACKLOG Rev 85 and README Rev 39: from `docs/` to `docs/system_designs/`, together with the fourteen other one-system design notes and the series handoff, `docs/system_designs/HANDOFF.md`. The *Canonical* line and every path to a design note outside a Rev line now name the new folder; no content changed. Rev lines keep the paths they were written with, since changelog lines are left exactly as written.
> **Rev 1 · 2026-11-08** — first version, docs only, with roadmap Rev 57, BACKLOG Rev 82 and README Rev 36. Written from a design chat, the thirteenth in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`, `docs/PolishedWorld_Housing_Design.md`, `docs/PolishedWorld_Hunting_Design.md`, `docs/PolishedWorld_Cooking_Design.md`, `docs/PolishedWorld_Temperature_Design.md`, `docs/PolishedWorld_Farming_Design.md`, `docs/PolishedWorld_Textiles_Design.md`, `docs/PolishedWorld_Water_Design.md`, `docs/PolishedWorld_Foraging_Design.md`, `docs/PolishedWorld_Light_Design.md`, `docs/PolishedWorld_Forest_Design.md` and `docs/PolishedWorld_Rendering_Design.md`. Clay exists (a clay bank by the brook, and the sun-dried sling bullet as its one consumer), but nothing is fired: pottery is BLOCKED on a kiln, and no station of any kind exists in the code. Nothing here changes live behaviour, so there is no departures table. **Nothing here is locked.** Every numbered item is a proposal (PP…), a goal (PG…) or an open question (PQ…); the letter is *P*, for pottery, free across `docs/`, `world/`, `commands/`, `typeclasses/` and `server/` when checked. In the chat Adam approved writing the document from the proposal without answering its questions; they are recorded here as PQ1–PQ6 with the leanings recommended in the chat, recorded as *leanings*, not as decisions. The leanings under the other questions are this document's own. Registry open decisions 7–9 (kiln, furnace, forge and anvil) belong to the metallurgy epic's decomposition (roadmap, *[RESOLVED] Metallurgy enters through tools*); this document leans on them and locks none. Prior art was read on 2026-11-08; code seams were read against `main` at `1357ba2` (Evennia 6.1.0).
> **Canonical:** `docs/system_designs/PolishedWorld_Pottery_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/roadmap.md`, parallel backlog, *Pottery, kilns & stations* — a new entry (Rev 57), because nothing owned the chain: the registry blocks pottery on a kiln and the kiln on a station typeclass, and the readers of fired clay are written down in five other designs — Rendering's pot (ZP3), Water's clay jug and fireproof pot (VP4, VP5), Textiles' loom weights and spindle whorl (WP2, WP4), Forest's fire seed (§15) and Cooking's dishes (CP6). `docs/BACKLOG.md` gains two notes (Rev 82): *Metal tools + craft-station / forge* — the station contract this design proposes for registry open decisions 7–9 and Textiles WQ3, leaned and not decided (PP7–PP9); and *Light & darkness* — the pot that tallow is rendered in no longer waits for a kiln, because a pit firing makes it (PP3).
**When to read:** when Cooking's fire (CP1) or Light's `kindle` (LP7) is decomposed (a firing is lit like a fire); when Rendering's slice 1, Water's salt (VP5) or Cooking's stew (CP6) needs its pot (PP10); when Water's clay jug is decomposed (VP4); when Textiles' spinning or loom is decomposed (WP2, WP4; WQ3's station question, PP7); when the metallurgy epic is decomposed (registry open decisions 7–9, PP9; the crucible, PP10); when Housing's parts gain tiles or a hearth (PP12); with *masonry & lime*, *oils & pressing*, *bone, horn & antler* or *chimneys, smoke & indoor fire* from the design-series queue (PP12); with *law/crime/bounties* (another's firing, PQ11).

---

## 1. The idea in one paragraph

A lump of grey clay from the brook bank is wedged and shaped by hand into a jug, a pot or a stack of bricks, and left to dry; wet clay put in a fire bursts. Once it is dry it goes into a pit with wood heaped over and around it, the wood is lit at dusk, and in the morning, when the ashes are cold, the potter digs out jugs that ring when tapped and hold water. A pit fires four pots a night and the rain can put it out; so a potter who fires every week builds a kiln of the pit's own bricks, which holds three times as much on the same wood and has a roof. The kiln wears with every firing and is relined with clay, and a neighbour who has no kiln pays for a place in the next load. The pot the renderer melts fat in, the jug on a household's table, the fire seed a traveller carries and the weights on the weaver's loom all come out of this pit — and the kiln, the loom, the forge and the furnace that come after it are one kind of thing: a fixture someone built, that wears, and that holds its own state while its maker walks away.

---

## 2. Prior art

### 2.1 A Tale in the Desert — the lesson

Source: the A Tale in the Desert wiki, *Kiln Construction* (Tale 11) (`atitd.wiki`, read 2026-11-08). Paraphrased:

- Kilns are buildings a player constructs, and they come in a ladder: a box kiln of plain bricks is used up by one firing; a true kiln, built of firebricks, lasts tens of firings and can be repaired; a reinforced kiln lasts a thousand; the largest fires structural pieces and never wears out.
- Each kiln has a capacity per firing and burns a fixed amount of wood per firing, and the better kilns fire more pieces for less wood each.
- The firebricks that a true kiln is built from are themselves fired in a kiln — the trade makes the station it needs to grow.

**Worth taking:** a station that is built, has a capacity and a fuel cost per use, wears out by use and is repaired; a ladder where the better station is built from the worse one's product.

**Not for PolishedWorld:** the top tiers (thousands of bricks, rare stone, steel sheeting); the cultural scale of a tale.

**The lesson (the series' "Achaea lesson" — Achaea has a rule for stations but no story of one changing, so the slot goes to the lineage that has one):** a station is a product of its own trade. The kiln is built from bricks, the bricks are fired in a pit, the pit is a hole in the ground — so the first potter needs nothing but clay and wood, and every station above that is something a player made, uses up and remakes. The rule taken: **no station is scenery** (PG1).

### 2.2 Vintage Story — the pit kiln

Sources: the Vintage Story wiki, *Pit kiln* and *Clay forming* (`wiki.vintagestory.at`, read 2026-11-08). Paraphrased:

- A pit kiln is a hole one block deep with up to four raw clay items in it, dry grass, sticks and fuel heaped over them, then lit. It needs no built station.
- It burns the same fuel for the same time whether it holds one item or four, so a potter fills it. With firewood it takes about twenty game hours; with charcoal about half that.
- Rain or snow can put it out, and the player must relight it and wait again. Its embers can set fire to flammable things nearby.
- Clay items are shaped first and are raw until fired; one item, the clay oven, works without firing.

**Worth taking:** the pit as the bootstrap — pottery with no station at all; a fixed cost per firing, so batching pays; rain as the pit's risk.

**Not for PolishedWorld:** voxel clay forming; wildfire from embers (*natural hazards* in the queue).

### 2.3 Wurm Online — a kiln of bricks

Source: Wurmpedia, *Kiln* (`wurmpedia.com`, read 2026-11-08). Paraphrased:

- A kiln is a masonry furnace built from bricks, clay and dirt, used to harden pottery; it is improved with clay.
- It is lit with a fire tool and kindling, and fuelled with any fuel item; its quality affects how long it stays lit.
- It holds a set number of pots by size; after use it can be cleaned with a shovel for ash.
- It does not decay on a settlement that is paid up for a month ahead — elsewhere it does.

**Worth taking:** the kiln built of bricks and clay and mended with clay; ash from a kiln; capacity by size.

**Not for PolishedWorld:** a temperature carried by every item; settlement upkeep paid in coin (*absence, upkeep & inheritance* in the queue).

### 2.4 Achaea — forges as scenery

Sources: AchaeaWiki, *Forging* and *Weaponsmithing*, and a 2004 forging script on the Zuggsoft forums (read 2026-11-08). Paraphrased:

- Forges are placed in many places by the game — cities, houses and temples have them — and a smith goes to one.
- A forge is fired with one coal before work begins; the commodities are laid out on it and forged.

**Worth taking:** a firing costs fuel, every time.

**Not for PolishedWorld:** stations the game places; a station no one builds, owns or wears out (pillar 1; PG1).

---

## 3. Design goals

- **PG1 — No station is scenery.** Every kiln, loom, forge and furnace is built by a player, wears by use and is mended or rebuilt (§2.1).
- **PG2 — The first of everything needs no station.** The first pot is fired in a pit, as the first charcoal is made in a clamp (Forest YP8) and the first axe is knapped by hand; a station makes more, better or cheaper, never the first.
- **PG3 — The state lives on the thing, not on the person.** A firing is the pit's or the kiln's, read from a stamp; the potter may walk away, log out or go to bed (Forest YG5's rule).
- **PG4 — Every ware ships with a consumer that bites.** Rendering ZG1's rule, here for pots, jugs and bricks: a ware ships with its reader or waits.
- **PG5 — Nothing ticks.** Drying, firing and wear are read from stamps and indexes.
- **PG6 — No shipped recipe changes.** The sun-dried sling bullet stays as it is (`world/recipes.py:604`).

---

## 4. Legend alignment

**Rules as written:**

- **Craft** — p. 57: Craft is several separate skills; the list names potter, mason, smith and blacksmith. p. 58: a critical makes an item superior in durability, value or utility; a fumble halves its Armour and Hit Points and its value.
- **Craftsman** — p. 20: the profession's skills are Craft (Any) with Evaluate +20%, and an advanced choice of a second Craft, Engineering or Mechanisms.
- **No test** — p. 42: the automatic success and failure rules do not apply where the Games Master rules that no test is required.
- **Fire and Heat** — p. 83: damage by intensity — a flame (a candle), a large flame (a brand), a small fire (a camp or cooking fire), a large fire (a bonfire, a burning room), an inferno (lava, the inside of a blast furnace).
- **Lantern** — p. 114: most lanterns are made of brass or bone. **Oil** — p. 116: oil comes in small pottery containers or glass bottles.
- **Arms of Legend** (`docs/reference/arms_of_legend.md`): the fire seed, a ceramic container that keeps a coal from last night's fire for up to three days, is put out by a soaking and gives +10% to tests to start or keep a fire (`:244–248`); the pottery wheel, a large wooden device kept in a workshop that makes Craft (Pottery) faster and gives +10% (`:386`; 25 ENC, `:607`); the potter, whose wares run from sun-dried water jugs to enamelled urns (`:3088`); tools and resources, which decide whether a task is possible, how long it takes and how good it is — a smith needs iron, an anvil and a forge (`:1034–1044`); the athanor, a clay furnace in sections (`:3667`), and the great furnaces fired with charcoal, coal or wood (`:3669`); the industrial apron, worn against a smith's or glassblower's heat (`:718`).

**Translation proposals:**

- **PP-L1 — Shaping is `craft`.** In a proposed sixth discipline, `pottery` (PQ4), beside the five shipped ones (`world/recipe_mastery.py:81–87`); Craft (Potter) arrives with specialised Craft for every craft at once.
- **PP-L2 — Firing needs no test.** A fire in a pit is routine; p. 42 lets the Games Master rule that no test is required. What a firing gives depends on the ware's state and the weather, not a roll (PP4; PQ2).
- **PP-L3 — Heat by p. 83's rows.** The table's intensities name the steps of heat a station gives: a cooking fire is a small fire, a pit or a kiln a large fire, a furnace an inferno (PP8).
- **PP-L4 — The hand gives the quality.** The shaping roll stamps quality as every shipped craft does (`world/crafting_base.py:229–235`, `consume_policy` "raw" `:36`); the firing keeps it. p. 58's critical and fumble land on the ware through that stamp.
- **PP-L5 — A station decides whether, not how well — except the wheel.** AoL's tools-and-resources rule (`:1034–1044`): a kiln or forge makes a task possible; AoL's pottery wheel is the one station that adds a term, +10 (`:386`), on the shipped tool path.
- **PP-L6 — Heat harms no one.** Burns are Stage 5's damage model, if ever; the industrial apron is recorded with it.
- **PP-L7 — Legend's prices are not used.** Pillar 1.

---

## 5. The loop

Proposed phases; each is something someone can sell.

1. **Dig.** Clay from a bank, by hand (`world/prototypes.py:447–461`).
2. **Shape.** A jug, a pot, a fire seed, bricks — `craft`, the potter's roll (PP1).
3. **Dry.** The ware dries on Cooking's drying index; firing it wet bursts it (PP2).
4. **Fire.** In a pit for a night with wood over it (PP3), or in a kiln (PP5, PP6).
5. **Open.** Cold ware comes out fired; the ash goes to the tanner (PP4; Rendering ZP8).
6. **Use.** Water in the jug, fat in the pot, an ember in the fire seed (PP10); every ware wears (PP11).
7. **Build.** Bricks become a kiln, and the kiln fires for others (PP5; §13).

---

## 6. Clay and shaping

**PP1 — Shaping is one craft, and its output is unfired.** A pottery recipe is a `MongooseCraftRecipe` like the shipped sling bullet (`world/recipes.py:604`): clay in by tag-key, by hand (`tool_tag = None`), rolled on `craft` in the `pottery` discipline (PP-L1). Its output is an **unfired ware** — *an unfired jug*, *an unfired pot* — an object that names what it becomes (`db.fires_to`, the fired prototype) and carries the quality the roll stamped (PP-L4). An unfired ware is good for nothing but firing: it holds no water and goes on no fire (§19, AoL's sun-dried jug). Clay per ware is in PP10's table; a lump of clay is ENC 0 (`world/prototypes.py:444`), and so is every small ware.

**PP2 — Wet, then dry.** An unfired ware is stamped at shaping with the value of Cooking's **drying index** (CP11), as Forest YP3 stamps a length of wood, and reads *dry* once the index has moved on by a span (leaning: about a game day of fair weather, PQ7). It reads *wet* until then, in words. A wet ware put in a firing bursts (PP4). Indoors or out makes no difference to the index in v1; a drying shelf is a later word for Housing.

---

## 7. Firing

**PP3 — The pit firing: the clamp's twin.** `build pit` in an outdoor authored room takes the dry unfired wares the builder holds, up to a capacity counted in lumps of clay (leaning: eight — four pots, four jugs or eight bricks, PQ8), and fuel worth a night — eight game hours on Forest YP1's table: four lengths of seasoned wood, eight of green, three lumps of charcoal — and makes a **pit** object holding them. `kindle` lights it as it lights a fire (Light LP7; Cooking CP1); it then burns for a fixed span (leaning: one night, eight game hours, two real hours) stored as `done_at`, read on look — *a low fire smoulders in a pit*, then *the pit has gone cold* — and the neighbouring outdoor rooms see its smoke (Cooking CP2). The span is the same for one ware or eight, so a potter fills the pit (§2.2). `open pit` after `done_at` gives the fired wares, leaves ash by Rendering ZP8's rate (two handfuls for a night), and deletes the pit. A pit is not a station: it is made and unmade by one firing, as the clamp is.

**PP4 — What a firing gives, without a roll (PP-L2).** Every ware comes out by its state, never by chance:

| Case | Result |
|---|---|
| dry ware, the span burned through | fired: the ware named by `fires_to`, with the quality stamped at shaping |
| wet ware | bursts: gone, its clay lost (PP2) |
| rain or snow read on an outdoor pit before `done_at` | the fire goes out and stays out (Cooking CP3's one-way rule, Light LP8): the fuel is spent and the wares come out unfired but dry, to be fired again |
| opened before `done_at` | the cold air cracks every ware: all lost (Forest YP8's early opening) |

The potter's skill is in the shaping roll, the drying and the choice of a dry night; there is no tending and no second roll (PQ2; §19).

---

## 8. The kiln

**PP5 — A kiln is built of the pit's bricks.** `build kiln` in an authored room takes fired bricks and clay to line and seal them (leaning: sixteen bricks — two pit firings — and four lumps of clay, PQ5) and makes a **kiln**, a fixture (`get:false()`, as a `ResourceNode` is, `typeclasses/resources.py:61`) with `condition` on the shipped durability axis (`typeclasses/durable.py:41`, `apply_wear` `:43`). Building is a timed act with no test, as the clamp's is; the bricks carry their quality, and a kiln of better bricks wears slower (PQ9). A kiln stands outdoors or in a workshop room; indoors it wants a chimney (*chimneys, smoke & indoor fire* in the queue).

**PP6 — A kiln fires more for the same wood, under a roof.** `load kiln` puts dry unfired wares in, up to its capacity (leaning: twenty-four lumps — three pits' worth, PQ8); `fire kiln` takes the same night's fuel as a pit and is lit with `kindle`; `done_at`, the read-on-look lines, the smoke and `open kiln` work as the pit's (PP3, PP4) — except that **rain does not reach it**: the firing is under its own roof. The kiln is not deleted on opening; each firing wears it (leaning: two points, about fifty firings from new, PQ9), and a worn kiln is relined with clay (PQ9's seam). One load at a time: a kiln that is loaded or burning refuses a second load (§14). The kiln is an upgrade, not a gate (PG2): three times the ware for the fuel, no rain, and the heat for what a pit cannot fire (PP12).

---

## 9. Stations

**PP7 — Two kinds of station, one contract.** Textiles WQ3 asks whether the loom is a station; the registry asks the same of the kiln, the furnace, the forge and the anvil (open decisions 7–9, `world/material_registry.py:505–507`). Proposed: one duck-typed contract rather than one class per station (PQ6). Every station is a **fixture** — `get:false()`, placed by whoever built it, on the `condition` axis, mended with its own materials — and comes in one of two kinds:

| Kind | Examples | How a recipe finds it | What it holds | Wear |
|---|---|---|---|---|
| **work station** — used while a craft is made | loom (Textiles WP4), pottery wheel (AoL `:386`), anvil | as a tool: `craft … using wheel` finds tools in the room as well as the inventory (`commands/crafting_commands.py:324`) | nothing | the shipped tool-wear sink, per completed craft (`world/crafting_base.py:335`) |
| **firing station** — holds a load over time | pit (one firing), clamp (Forest YP8, one firing), kiln, furnace, oven | by its own verbs: `load`, `fire`, `open` | the load and a `done_at` stamp, and who loaded it | per firing |

**The work station needs almost nothing new.** A `DurableObject` fixture tagged as a tool already rides the shipped path: craft searches the room for it, `_used_tool()` finds it among the inputs by tag (`world/crafting_base.py:176`), and the wear sink nicks it (`:335`) — both docstrings already name a future station or furnace. What is new is one user at a time (§14; PQ10) and mending a fixture, since `repair` today finds only what the caller carries (`commands/repair_commands.py:95`), though it already reads a target's own `db.repair_materials` (`:121`). **The firing station is the new part:** a load, a stamp and three verbs, written once for the pit and reused by the kiln, the clamp and later the furnace.

**PP8 — Heat is a field, named by p. 83 (PP-L3).** Every fire and firing station carries a `heat` on Legend's rows: Cooking's fire and a hearth are a **small fire** — cooking, rendering, boiling brine; a pit and a kiln are a **large fire** — earthenware, bricks, and in the kiln glaze; a furnace is an **inferno** — smelting and glass. A recipe or a verb asks for at least a step of heat, never for a named class, so a kiln can stand in for a fire where a fire is enough, and a forge is whatever the metallurgy epic says it is. Heat is read; it never moves on its own.

**PP9 — Registry open decisions 7–9, leaned.** **7 — the kiln is pottery's**, with its bricks, tiles and glaze, and later lime (*masonry & lime*); charcoal left it for the clamp (Forest YP8, YQ15), so `charcoal`'s and the kiln's rows lose *charcoal* when either ships. **8 — the furnace: leaning separate**, a bloomery for iron that is broken open for each bloom (a firing station used up like the pit) beside a glass furnace that lasts (a kiln of greater heat); both are the metallurgy epic's to lock, with glass's soda ash from Rendering ZP13. **9 — the forge and the anvil are fixtures in a room**, the forge a fire at inferno heat and the anvil a work station, and the hammer is what the smith carries; the metallurgy epic's decomposition decides. This design locks none of the three.

---
## 10. What the clay makes

**PP10 — The first wares, each with its reader (PG4).** Clay in lumps; every ware below is fired in a pit unless marked:

| Ware | Clay | Reader | Ships with |
|---|---|---|---|
| **clay jug** | 2 | drinking: ten draughts, ENC 2, a `Drink` with charges (Water VP4; `typeclasses/consumables.py:28`) | this design's first slice — thirst is its consumer today |
| **pot** (fireproof) | 2 | rendering (Rendering ZP3), boiling brine for salt (Water VP5), stew (Cooking CP6) | whichever of those three ships first |
| **brick** | 1 | the kiln (PP5); later Housing's walls and hearth | the kiln |
| **fire seed** | 1 | carries an ember for up to three days, out if soaked; +10 to lighting a fire (AoL `:244–248`; Light LP7's `kindle`) | Cooking's fire |
| **bowl** | 1 | dishes by category (Cooking CP6) | Cooking's slice 5 |
| **spindle whorl**, **loom weights** | 1, 2 | spinning and the warp-weighted loom (Textiles WP2, WP4) | Textiles' slices |
| **crucible** (kiln) | 2 | smelting and casting | the metallurgy epic |
| **glazed ware**, **roof tiles** (kiln) | — | glaze from ash (Rendering ZP13); a Housing roof part (BP7) | later (PP12) |

The pot is the ware five readers wait for: Rendering ZP3 and Water VP5 both wrote *after the kiln*, and with the pit firing **the pot needs no kiln**. Fired sling bullets stay in the recipe's note (`world/recipes.py:609`) and wait for something that shoots them (PQ16).

**PP11 — Fired clay wears and breaks.** Every ware is a `DurableObject` on `condition` (`typeclasses/durable.py:41`). A jug wears per refill (Water VG5), a pot per use on a fire, a fire seed per carrying; at zero a ware is broken and gone, with no sherds (§19). A better-shaped ware lasts longer, through the quality stamped at shaping (PP-L4). Breakage is the potter's steady market.

---

## 11. What waits

**PP12 — Recorded, each with its own system:**

- **Glaze** — ash, clay and water on a ware fired in a kiln, so a jug holds water without sweating and keeps longer (Rendering ZP13).
- **Lime** — limestone burnt in a kiln for mortar and plaster; `limestone` is unratified (`world/material_registry.py:481`); with *masonry & lime*.
- **Glass** — sand and soda ash in a furnace (`world/material_registry.py:329–334`), for the lantern's panes (Light LP5) and bottles; with the metallurgy epic's furnace (PP9). A lantern's first panes may be horn, which Legend allows (p. 114), with *bone, horn & antler*.
- **The oil lamp** — a clay lamp burning oil, which has no source yet (Light LP5); with *oils & pressing*.
- **The pottery wheel** — a work station of wood and stone, +10 and faster (AoL `:386`; PP-L5); with *carpentry & cooperage*, once planks exist (`world/material_registry.py:317`).
- **Tiles and bricks for building** — Housing's parts (BP7), and the clay-and-wax box for a locksmith (AoL `:194`) with *stealth, locks & theft*.

---

## 12. Offline and the world

**PP13 — Nothing waits on the potter.** A firing is the pit's or the kiln's (PG3): it burns to its `done_at` whether its potter is online, asleep or a statue (`typeclasses/characters.py:472`), and is read when someone looks or opens it. Rain on an outdoor pit is decided when the pit is read, as Cooking CP3's fire is, so a pit nobody looks at during a shower is decided at the next look by the weather then — the one-way rule's known softness, shared with the fire. Unfired wares dry on the global index wherever they lie, in a pack or on a statue. Shaping is an ordinary craft act and is interrupted by logging out, as every craft is. Wilderness pits are Stage 6's, as fires are (Evennia Reference §14.5–§14.6).

---

## 13. Economy

**Sources (all natural or player-made):** clay from the bank, free and flat (Forest YP5 keeps clay flat); fired wares from pits and kilns; ash from every firing.

**Sinks:** clay into every ware; a night's fuel per firing (Forest YG6); wares that burst wet or crack when opened early; every ware's wear and breakage (PP11); the kiln's wear and its relining clay (PP6); bricks into kilns.

**Materials this design gives a source or a sink:** **clay** (its second sink, the reason a clay bank matters); **pottery** (a source — leaving BLOCKED for a pit); **wood and charcoal** (a sink per firing); **plant ash** (a second source beside the fire, Rendering ZP8).

**Services:** the potter, who sells jugs and pots that break; the brickmaker; the kiln keeper, who fires a neighbour's wares in the next load — a place in a firing is the kiln's natural service, since a kiln fires three pits' worth on one pit's wood; the ash seller.

**PP14 — The master constant, on one page.** At the leanings: a clay bank gives four lumps and one more each game hour (`world/prototypes.py:457–459`), so it refills a pit's eight lumps in about a night; **one night's firing** — four lengths of seasoned wood — fires four pots or four jugs in a pit, or twelve in a kiln, and leaves two handfuls of ash (Rendering ZP8); a kiln costs two pit firings of bricks; a kiln lasts about fifty firings. Every number moves together; the decomposition tunes this table, not the parts one by one.

**PP15 — No exclusive.** Clay is free at the bank and anyone may shape and fire it. Proposed for the roadmap's food-professions exclusives decision: pottery is on no list.

**Coin:** none. **Logging:** shaping, firing and building a kiln are PQ13.

---

## 14. Multiplayer and server load

- **Nothing ticks.** Drying reads Cooking's drying index; a firing reads its `done_at`; wear moves on use.
- **One station, one load.** `load` and `fire` check and set the load in one synchronous command; a second potter finds the kiln loaded. Who loaded it is stamped on it, and anyone may open it — taking another's wares is law & crime's question (PQ11; Forest YQ3, Rendering ZQ15).
- **One work station, one user.** A wheel or loom is claimed for a craft's span with a stamp on the station, because `ndb.timed_action` is per character (`world/timed_actions.py:107`, `:198`); a second user is told it is in use (PQ10).
- **Rooms do not fill with pits.** A pit is deleted when it is opened; a forgotten pit is *litter, abandoned goods & salvage rights*' question. Kilns are few and built.
- **Wilderness.** No pits or kilns there; Stage 6's (Evennia Reference §14.6).

---

## 15. Immersion extras

- **The glow at night.** A burning pit or kiln is a light in the dark room (Light's `light_emitted()`) and warms whoever stands by it (Temperature KP8's `radiant_warmth()`) — PQ14.
- **The ring of fired clay.** Opening a firing gives a line for the sound of cooling pots; a burst ware gives another.
- **The thumbprint.** The shipped clay keeps the print of every finger (`world/prototypes.py:438–439`); a maker's mark pressed into a pot before firing belongs with BACKLOG *Material / maker's-mark aliases beyond "superior"*.
- **Firing night.** A settlement's pits are lit at dusk and opened at dawn; smoke from the potters' end of town reads from the exits (Cooking CP2).

---

## 16. Layers — a suggested order

1. **Slice 1 — shaping, drying, the pit and the jug, together (PG4):** PP1–PP4 and the clay jug (PP10). Needs: Cooking's fire or Light's `kindle` (a pit is lit like a fire), and Cooking's drying index (CP11). The jug's consumer — drinking — ships today.
2. **Slice 2 — the pot, with its first reader:** Rendering's slice 1, Water's salt (VP5) or Cooking's stew, whichever comes first. The fire seed with Cooking's fire; the bowl with Cooking's slice 5; whorl and weights with Textiles.
3. **Slice 3 — bricks and the kiln, with the first ware a pit cannot fire:** the crucible (metallurgy), glaze or tiles (PP5, PP6, PP12). The firing-station verbs are already written for the pit.
4. **The station contract (PP7–PP9)** is written down by whichever ships first — the loom (Textiles' slice 3), the kiln, or the metallurgy epic's forge.

**Prerequisites:** slice 1 needs a way to light a fire and the drying index; slice 2 needs one of the pot's readers; slice 3 needs a ware that needs a kiln. **Not prerequisites:** Stage 5, the webclient, the economy milestone.

---

## 17. Seams in today's code (read at `1357ba2`)

| Need | Seam | Where |
|---|---|---|
| Clay | the lump (ENC 0); the bank (max 4, one per 3600 game-seconds); seeded at the Brook | `world/prototypes.py:432–445`, `:447–461`; `world/seed_data.py:204–205` |
| Clay's one consumer | `SlingBulletRecipe`, discipline `stonework`, by hand; fired variant noted BLOCKED | `world/recipes.py:604–622` |
| Registry | clay, sand; glass; pottery BLOCKED on the kiln; anvil, furnace, kiln, forge; unratified list (limestone, soda ash); open decisions 7–9 | `world/material_registry.py:141–152`, `:329–334`, `:335–340`, `:407–429`, `:478–483`, `:505–507` |
| Craft | ingredients from inventory; tools from room and inventory | `commands/crafting_commands.py:315`, `:324` |
| Recipe base | `skill_name`; consume policy "raw"; `_used_tool()` and its station note; quality by tier; the wear sink and its station note | `world/crafting_base.py:58`, `:36`, `:176`, `:229–235`, `:335` |
| Disciplines | five | `world/recipe_mastery.py:81–87` |
| Durability | `condition`, `apply_wear` | `typeclasses/durable.py:41`, `:43` |
| Fixtures | `get:false()` on a node | `typeclasses/resources.py:61` |
| Repair | the target from the caller's contents only; per-target materials | `commands/repair_commands.py:95`, `:121` |
| Vessels | `Drink` with charges | `typeclasses/consumables.py:28` |
| Timed acts | one `ndb.timed_action`; `claim` | `world/timed_actions.py:107`, `:198` |
| Indoors | `is_indoor` | `world/thermal.py:68` |
| Weight | small items twenty to one ENC | `world/encumbrance.py:50` |
| Statues | logged-out character as stone | `typeclasses/characters.py:472` |
| Recipe sources | every gated recipe has a source | `tests/test_recipe_sources.py` |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **PQ1** — Does a pit firing make pottery with no station, so the pot and the jug do not wait for a kiln? *Leaning (chat, 2026-11-08): yes (PP3, PG2).*
- **PQ2** — Roll at shaping only, and none at firing? *Leaning (chat, 2026-11-08): yes — the hand gives the quality, the firing's outcome follows from the ware's state and the weather (PP4, PP-L2).*
- **PQ3** — Is drying its own step? *Leaning (chat, 2026-11-08): yes, on Cooking's drying index (PP2).*
- **PQ4** — A sixth discipline, `pottery` (Potter)? *Leaning (chat, 2026-11-08): yes; the sling bullet stays `stonework` (PG6).*
- **PQ5** — Is the kiln built of pit-fired bricks? *Leaning (chat, 2026-11-08): yes (PP5, §2.1).*
- **PQ6** — One duck-typed station contract rather than a base class? *Leaning (chat, 2026-11-08): yes — locked in the metallurgy epic's decomposition, or by whichever station ships first (PP7).*
- **PQ7** — The drying span. *Leaning: about a game day of fair weather on the index (PP2).*
- **PQ8** — Capacities in lumps of clay. *Leaning: a pit eight, a kiln twenty-four (PP3, PP6).*
- **PQ9** — The kiln's wear per firing, whether brick quality slows it, and how a fixture is mended. *Leaning: two points a firing; mended with clay through `repair`, its target search widened to the room for fixtures (`commands/repair_commands.py:95`) and its materials read from `db.repair_materials` as today (`:121`).*
- **PQ10** — One user at a time at a work station. *Leaning: a stamp on the station for the craft's span, beside the user's own `ndb.timed_action` (§14).*
- **PQ11** — Who may open a firing someone else loaded? *Leaning: anyone, in the alpha; the loader is stamped on it, and taking another's wares is law & crime's (Forest YQ3, Rendering ZQ15).*
- **PQ12** — Where the pottery recipes come from: a profession, a scroll or a teacher? `build pit`, `fire` and `open` are verbs and need no recipe; the shaping recipes do, and every gated recipe needs a source (`tests/test_recipe_sources.py`). *Open.*
- **PQ13** — Activity-log kinds for shaping, firing and building a kiln: new kinds or fields on existing ones? The family of Hunting TQ10, Textiles WQ8, Farming GQ6, Fishing FQ6, Water VQ9, Foraging RQ11, Light LQ12, Forest YQ13 and Rendering ZQ14. *Open.*
- **PQ14** — Does a burning pit or kiln light and warm its room like a fire? *Leaning: yes, through the same duck-typed readers (§15).*
- **PQ15** — Does green wood fire a pit as well as seasoned? *Leaning: yes, by its hours on Forest YP1's table — twice the lengths, with its thick smoke.*
- **PQ16** — Fired sling bullets. *Leaning: not until something shoots them (Stage 5); the sun-dried bullet is unchanged.*

---

## 19. Considered and not proposed

- **Stations the game places.** Achaea's forges in every city (§2.4; PG1).
- **A kiln before the first pot.** The registry's shape today; the pit comes first (PG2).
- **Sun-dried ware as a lesser jug.** AoL's potter makes them (`:3088`); here an unfired ware is only a stage, so no rule is needed for clay that softens in water.
- **A firing roll, or tending a firing.** The series' rule: skill lives in choices, not in watching a fire (PQ2).
- **Fuel that shortens a firing.** Vintage Story's charcoal halves its pit (§2.2); here fuel is hours on one table (Forest YP1) and a firing is a night.
- **A temperature on every item.** Wurm's model (§2.3).
- **Voxel clay forming.** Vintage Story's (§2.2).
- **Sherds and grog.** A broken ware is gone; crushed sherds as temper are *offcuts, scraps & byproducts*' if anything.
- **Charcoal in the kiln.** The clamp makes it (Forest YP8).
- **A kiln per ware or a brick kiln apart.** One kiln fires everything a large fire can (PP8).
- **The top of A Tale in the Desert's ladder.** Reinforced and vault kilns; one kiln is enough until something needs more (§2.1).
- **Burns at a kiln or forge.** Stage 5's (PP-L6).
- **Pottery bought from an NPC.** Pillar 1.
