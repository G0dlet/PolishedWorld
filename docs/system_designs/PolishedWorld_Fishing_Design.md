# PolishedWorld — Fishing Design Notes

> **Rev 2 · 2026-11-08** — moved, docs only, with roadmap Rev 60, BACKLOG Rev 85 and README Rev 39: from `docs/` to `docs/system_designs/`, together with the fourteen other one-system design notes and the series handoff, `docs/system_designs/HANDOFF.md`. The *Canonical* line and every path to a design note outside a Rev line now name the new folder; no content changed. Rev lines keep the paths they were written with, since changelog lines are left exactly as written.
> **Rev 1 · 2026-11-07** — first version, docs only, with roadmap Rev 46 and README Rev 24. Written from a design chat: Adam asked how fishing could be made as immersive as possible and which MUDs to learn from, and asked for the result to be kept for the day fishing is taken up. **Nothing here is locked.** Every numbered item is a proposal (FP…) or an open question (FQ…); the fishing decomposition locks or rejects each one, as every decomposition before it has. Prior art was read on 2026-11-07; code seams were read against `main` at `f0c2708` (Evennia 6.1.0).
> **Canonical:** `docs/system_designs/PolishedWorld_Fishing_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** roadmap, *Parallel / opportunistic backlog*, *Food professions — farming · fishing · livestock*. This document is the fishing third of that entry, written early; the entry's rule that exclusive products are decided **once across all three professions** still binds, and §10 does not decide it.
**When to read:** at the start of the food-professions decomposition, or of a fishing-only one if the roadmap splits fishing off ("cheapest of the three … can run in parallel").

---

## 1. The idea in one paragraph

Fishing is a conversation with the water, not a button. The player chooses where to cast, at what depth and with what bait, reads signs the world gives back (the float, the light, the season, the weather), decides when to strike and how to play the fish, and lands one particular fish — a 68 cm pike of about 2 kg, not "1 fish". The skill lives in **reading and choosing**, never in reaction speed. Every piece of tackle is player-made, every catch is food that spoils, and every water holds a finite stock that recovers slowly, so the ecology — not anti-bot code — is what limits how much fish enters the economy.

---

## 2. Prior art

### 2.1 Ansalon MUD (Dragonlance, ROM-derived, fishing since 2005)

Sources: `http://www.ansalon.net/?page_id=858` (how to fish) and `?page_id=1515` (the code's change history, 2005–2026). Ansalon lists 100+ species and treats fishing as a headline feature. Paraphrased:

**Worth taking**

- **Tackle as components with trade-offs.** Rod, line, hook, sinker and bait are separate items. Heavier line is stronger but more visible to fish; a broken line leaves the angler with a shorter line; the sinker sets depth; a big hook scares small fish and a small hook will not hold a big one. Every part is a decision — and in PolishedWorld every part is a player-made good.
- **Direction and depth.** You cast in a direction (`fish north`), raise and lower the bait, and reel with or against the fish's run; when the fish runs hard you let it run before reeling.
- **Every catch is unique.** Length is rolled per catch, weight is derived from length, and the depth you fished at shifts the size. Examine shows approximate length, weight and condition.
- **The fish fights.** It pulls line out; rod and line can break, weighed by rod durability and line strength.
- **Species selection without table bias** (their v2.3, 2026): first collect the species *eligible* here (fresh/salt, place, angler's skill), pick one at random, *then* test abundance, peak time, hunger, bait, hook and sinker against that one fish. Simple, predictable for beginners, keeps rarity. This is directly reusable (FP6).
- **Fishing feeds other crafts.** Fish can be butchered into bait (bigger fish, more bait), and bait gets nibbled down — the developers note they did this deliberately so players have something to spend on, i.e. a sink.
- **Visibility.** Others see the angler "here fishing", and the rod shows its line in the water.

**Not for PolishedWorld**

- Fish are sold to NPC shops. That is pillar 1's one hard "no".
- Ansalon withdraws money from a global production figure when fish are created, to offset the faucet. PolishedWorld already has the better form of that idea — every economic event in `server/logs/activity.jsonl` — and needs no counter-faucet because fish never become coin except through another player.

### 2.2 Achaea (IRE) — the warning

The loop is bait the hook → cast in a direction → when a nibble message arrives, tease the line → jerk the pole to set the hook → reel, relaxing when tension builds. Searching for it finds, first, a client script that plays the whole loop from triggers (zuggsoft forum, *Achaea: Auto Fisher*).

**Lesson:** in a MUD, any step that is *react to line X with command Y* becomes a trigger, and then the minigame is played by the client. PolishedWorld cannot and should not ban triggers. It can make sure that a trigger gains nothing a skilled character would not: put the skill into choices and into *how much information the character is given* (FP4), and cap yield with the water's stock (FP8).

---

## 3. Design goals

- **G1 — Skill in choices, not reflexes.** Every timing window is generous (several real seconds). What can be gotten wrong is *which* action, not *how fast*.
- **G2 — The skill gates information.** A low-skill angler is shown ambiguous signs; a high-skill one is shown clear ones. A script reading the text can only be as good as the character whose text it reads.
- **G3 — The world is read, not decorated.** Season, time of day, weather and (later) light change what bites and how. Fishing is the first system on the *supply* side to read them (see BACKLOG *Seasonal supply & population memory*).
- **G4 — Finite water.** Each water holds a stock that regenerates lazily. Two anglers share it. Overfishing is visible.
- **G5 — Every catch is a thing.** Species, length, weight, condition; food that spoils.
- **G6 — Everything is player-made.** Rod, line, hook, float, sinker, bait, net, trap, boat.
- **G7 — Source and sink named together** (Economic Philosophy; the ledger).
- **G8 — Short.** Two to four decisions per catch. A fishing session should be something you can do while talking to someone at the jetty.

---

## 4. Legend alignment

**Rules as written** (Legend core; *Arms of Legend*, `docs/reference/arms_of_legend.md`):

- Catching fish is a **Survival** test (POW+CON).
- **Fish hook:** lets the Adventurer use Survival to catch a fish *without penalty*; needs string, twine or rope. The size of the penalty without one is not given.
- **Fishing kit** (12 hooks, 10 m line, segmented rod, six corks): **+20 %** to the Survival test; handles fish of **SIZ 2 or less**; each extra 10 SP adds 1 ENC and **doubles** the SIZ it handles.
- **Fishing net** (2 × 2 m, weighted): **+25 %** to Survival for catching food; takes **3D10 minutes** to use.
- **Fishing arrow:** **+10 %** to the Survival test.
- **Fisherman** profession: Athletics, Lore (Regional), Resilience, Swim, plus two of Boating, Craft (Any), Shiphandling, Survival.
- Boats: *Arms of Legend* lists hide and dugout canoes and a **fishing boat**; `docs/crafting/PolishedWorld_System_Backlog.md` lists the fishing boat.
- Fumble on Survival (core): immediate harm — Resilience test or 1D3 damage — adjudicated to the situation.

**Translation proposals**

- **FP1 — A `fishing` skill, not `survival`.** The project's precedent is exact: `hunting` is a custom skill named so *"to avoid colliding with the `survival` trait-gauge category (hunger/thirst/fatigue)"* (`typeclasses/characters.py:443–449`), with chargen deriving it from Track's pair. `fishing` would follow it, derived from Survival's pair, **POW+CON**. Note: the roadmap entry names `Craft (Fishing)`; that skill is not in Legend's core — the core Fisherman picks *Craft (Any)* — and the roadmap annotation of Rev 46 records this.
- **FP2 — The SIZ rule is the tackle rule.** Each fish has a Legend SIZ; each rig has a SIZ it can handle (bone hook and twine low; a better line and hook higher, the kit's doubling as the model). A fish above the rig's SIZ can bite but cannot be landed — the line or hook gives. This is Ansalon's "small hook, big fish" in Legend's own terms.
- **FP3 — Modifiers as Legend writes them.** No hook: line fishing is impossible (hands or spear instead, at a penalty the decomposition picks). Hook and line: ±0. Good rig / kit: +20. Net: +25. Fishing arrow: +10. Situational terms (weather, time, bait match) are roll terms in `skill_check(skill_value, modifier)`, never trait mods — lesson candidate (p) from launch-minimum session 4.
- Critical: a better fish (size or condition). Fumble: the core's harm is kept for the *water* (slip on the rocks, a hook in the hand) — open question FQ7.

---

## 5. The loop

Proposed phases (FP4). Each phase is a beat on the existing timed-action slot (§14).

1. **Prepare.** Rig the rod (line, hook, float or sinker, bait). Rigging is done once and persists until something is lost.
2. **Cast.** `fish [<direction>|here] [shallow|deep]` — a water has one or more casting directions (reed bed, the deep, the current); direction and depth decide which species are eligible (FP6).
3. **Wait.** Ambient lines *to the angler only*, built from the world: the light, the weather on the water, birds, the float on the current. One line per beat, not a stream.
4. **Read.** Signs arrive: a nibble (small fish, or a big one testing) or a take. **FP4 / G2: the angler's skill decides how clearly the sign is described.** A novice reads *"the float moves"* for both; a skilled angler reads *"the float trembles twice and lies still"* (nibble — wait) versus *"the float slides sideways and slips under"* (take — strike).
5. **Strike.** `strike`. On a take: hooked. On a nibble: bait lost, fish gone. Too late on a take (after a generous window): the fish spits the bait.
6. **Play.** Two to four rounds of an opposed check, `opposed_check(fishing, fish.fight, …)`. Each round the fish *runs*, *rests* or *turns*, shown as text that is again clearer with skill. The angler answers `reel`, `give` or `hold`: reel on a rest gains ground, give on a run saves the line, reel on a run raises tension and tests the line's strength against the fish (FP2). The fish has stamina; the fight ends when it is spent (landed) or the tackle fails.
7. **Land.** The fish is created as an item with its species, length, weight, SIZ and condition (§7). One line to the room for a notable catch (FP12).

What it reads like (illustrative, not a spec):

```
> fish north deep
You cast toward the deep water past the reeds. The float settles on grey,
foggy water.
...
The float trembles twice, then lies still.
...
The float slides sideways and slips under.
> strike
The line snaps taut. Something heavy bores for the reeds.
> give
You let it run; the line hisses out and slows.
> reel
It tires. You draw it in through the shallows.
You land a pike: 68 cm, about 2 kg.
```

Moving away interrupts fishing (the slot's `at_pre_move` branch already does this for every timed action). `@reload` abandons a cast; nothing is consumed before the beat that consumes it (Epic A's D7 rule).

---

## 6. The water

**FP5 — Water is data on a fixture, not fish objects.** A `FishingWater` fixture in the room (a `ResourceNode` subclass is the obvious start: lazy regen, `get:false()`, number-free availability phrase, a serialised `harvest()` that two anglers cannot double-take). It carries:

- `water`: fresh / salt; `habitat`: still, flowing, reeds, deep, shore, ice-capable;
- `casts`: the directions and depths available here, each a habitat;
- `species`: keys into a species table (FP6), optionally weighted per water;
- `stock` / `max_stock` / regen fields, as `available` / `max_yield` / `regen_interval` already are.

**FP6 — Species selection, Ansalon's v2.3 shape.** Collect eligible species (water type, the habitat of the chosen cast, season, the angler's skill floor), pick one at random, then test it: abundance in this water, its active times (`get_time_of_day()`: night, dawn, morning, day, afternoon, evening, dusk), weather (`get_current_weather()`: clear, raining, snowing, foggy), bait match, rig SIZ. A failed test is a quiet wait, not a message. At 4× game speed a game day is six real hours, so a dawn window is about 30 real minutes — a peak time a player can actually plan for.

**FP7 — Winter.** Some waters freeze (season *winter*, a habitat flag). Fishing then needs a hole cut with an axe (the stone axe exists) and opens winter-only species. A clean way to make the 13-month calendar matter to food supply.

**FP8 — Stock and population memory.** The stock is shared by everyone fishing that water and regenerates lazily. Proposed refinement for *Seasonal supply & population memory*: below a floor, regeneration slows — an overfished pond recovers slowly, and the room's description says so (*"the shallows are empty of fry"*). This is the real anti-farm: a scripted angler empties a water no faster than a skilled human, and then the water is empty for both.

**Wilderness:** `docs/BACKLOG.md` and the gotcha notes are explicit that resource nodes must not be persistent room objects in wilderness (O(n) coordinate scan; room recycling keeps Attributes and Tags). Fixture-per-water works for authored rooms only; wilderness water needs a per-coordinate profile — FQ5, decided with Stage 6.

---

## 7. Fish as items

**FP9 — One typeclass, many species.** A `Fish(Food)` item with `species`, `length_cm`, `weight_kg`, `siz`, `condition` (fresh, bruised, torn — a hard fight or a fumble tears it). Weight from length per species (Ansalon's approach); depth and a critical shift length up. Key reads naturally (*a pike*, *a large pike*); examine gives the numbers in words (*about 68 cm, a good 2 kg*). Only notable sizes are named in the short key.

**Species table** in a data module (`world/fish_data.py`, shape like the seed and prototype tables): key, water, habitats, depth, active times, seasons, weather likes, length range, weight factor, SIZ by length, fight, stamina, bait preferences, rarity, skill floor. Proposed first set (cold-temperate freshwater, fits the setting): perch, roach, bream, tench, pike, trout, eel, burbot (winter nights).

**Spoilage.** Fish without a freshness clock is the case `docs/BACKLOG.md` *Food spoilage* names: *"preservable salt fish" is only an exclusive product if unpreserved fish spoils.* Fishing ships after, or with, that clock (§13).

---

## 8. Tackle — all player-made

What already exists on `main`: `twine` (aliases *cord*, *cordage*), `stick`, `bone` (harvested from corpses; `bone_needle` is the precedent for a ground-bone tool), stone, wood, the `Tool` class with its 0–100 `condition` axis and `apply_wear`. The AoL decomposition already sketches the kit: hooks ← bone/bronze/iron `[hooks: DATA; metal: BLOCKED]`, line ← plant-fibre twine, rod ← wood, corks ← oak bark.

**FP10 — A bootstrap ladder that needs no metal.**

| Rung | Rig | Built from | SIZ handled (proposal) |
|---|---|---|---|
| 0 | hands / sharpened stick (spear) | stick | shallows only, penalty |
| 1 | bone gorge or hook + twine on a stick rod | bone, twine, stick | small |
| 2 | proper rod, twisted line, float, stone sinker | wood, twine, bark, stone | medium |
| 3 | metal hook, better line (after metallurgy, which opens with tools — roadmap Rev 45) | metal, fibre | large |
| — | fishing kit (AoL) as a crafted bundle, +20 | rung 2–3 parts | the kit's doubling rule |

**Rig model — FQ3.** Ansalon makes the rod a container you `put` line, hook, sinker and bait into. PolishedWorld has containers with ENC capacity and no nesting (weight decomposition). The alternative is a `rig` attribute on the rod naming its parts and their condition. Decide in the decomposition; the second is less code and fewer objects.

**Bait.** Worms and grubs from `forage` (a new forage yield), fish offcuts from processing a catch (Ansalon's *make bait*: small fish are bait for pike), later bread or grain from farming. Bait is consumed on a take, often on a nibble.

---

## 9. Passive fishing

**FP11 — Nets, traps and weirs, lazily.** The roadmap's own sketch: passive traps on the lazy-eval trick. A set trap stores `set_at`, the water and the bait; on inspection it derives what was caught from elapsed time and the water's stock, with no ticker. The AoL net's +25 % and 3D10 minutes are the model for an active net. Passive gear draws on the same stock as rods (G4), wears, can be lost to a storm or a thief once Stage 5 exists. Ownership of a set trap in a shared water — FQ4.

---

## 10. Economy

**Sources:** fish (food); offcuts → bait; later fish oil (AoL weapon oil is made from fish or whale fat) and preserved fish.
**Sinks:** bait eaten; hooks lost to snags and fights; line shortened on a break; rods and nets worn through `apply_wear`; fish spoiling (*Food spoilage*); stock limited per water (a cap on the source, not a sink).
**Exclusives:** the roadmap's candidates for fishing are **fish oil** and **preservable salt fish**. They are decided once with farming and livestock, not here.
**Logging:** a catch is an economic event. Whether it is the existing `gather` kind with a field naming the source, or an eleventh kind (the report's copy of `KINDS` is pinned by a test) — FQ6.
**Ledger:** every new item gets its source and sink row in the same commit, as the alpha content epic required.

---

## 11. Multiplayer and server load

- **Per-character slot.** Each angler occupies their own `ndb.timed_action`; nothing global ticks. 20 anglers are 20 short `delay` chains, each a few beats long, dead on `@reload`.
- **Shared stock.** Takes go through the node's serialised read-modify-write (`ResourceNode.harvest()`'s docstring: two near-simultaneous takers cannot lose an update). A fish is taken from the stock **when it is hooked**, not when it is landed, so two anglers cannot both play the last fish; a lost fight returns nothing (the fish escaped — FQ8 whether it returns to stock).
- **Message volume.** Ambient lines go to the angler alone. The room hears casting, a strike, and a notable landing — three lines per catch at most.
- **No persistent fish in water.** Species and stock are numbers on the fixture.

---

## 12. Immersion extras

- **FP12 — Visible anglers.** The room shows *"Adam stands at the water's edge, line out"*; look at the water shows lines in it. A notable catch is one line to the room.
- **FP13 — A personal catch journal.** `fish journal`: species caught, the largest of each, where. Fills in as you go; never lists what you have not caught. Progress you can read without a number.
- **FP14 — Records for the gazette.** The largest pike of the month is a gazette item (BACKLOG *In-world gazette*), with the player anonymous unless they opt in, per that entry.
- Later, once *Light & darkness* exists: night fishing needs a light, and some species only bite then.

---

## 13. Layers — a suggested order

1. **Slice 1 (the smallest real thing):** `FishingWater` on authored rooms; the species table with 6–8 species; `fishing` skill; rungs 0–1 of tackle; worms as bait; the loop with read → strike → one-to-three play rounds; `Fish(Food)` with size and weight; stock and lazy regen; activity logging. Needs the spoilage clock first.
2. **Slice 2:** depth and sinkers, line strength vs visibility, species behaviours in the play rounds, the journal, freezing waters.
3. **Slice 3:** nets, traps and weirs (lazy); processing (gutting, smoking, salting, oil) — with the exclusives decision.
4. **Slice 4:** boats and deep water, after Stage 6 (wilderness water) and with the boat recipes.

**Prerequisites:** *Food spoilage* (BACKLOG, OPEN) for slice 1; the food-professions exclusives decision for slice 3; Stage 6 for wilderness water and boats. Not prerequisites: Stage 5 (fishing has no combat), the webclient (the OOB `room` snapshot can carry "fishing" later).

---

## 14. Seams in today's code (read at `f0c2708`)

| Need | Seam | Where |
|---|---|---|
| Timed, interruptible beats | `start(char, key, seconds, callback, …)`; `is_current()` for repeating beats (the `rest` pattern), `claim()` for the last | `world/timed_actions.py` |
| Interrupt on move | the single `interrupt()` branch in `at_pre_move` | `typeclasses/characters.py` |
| Lazy stock, serialised take | `ResourceNode._update_regen`, `harvest()`, `get:false()` | `typeclasses/resources.py` |
| Season / time of day | `get_season()`, `get_time_of_day()` | `world/gametime_utils.py` |
| Weather | `get_current_weather()` → clear, raining, snowing, foggy | `world/weather.py` |
| d100 tests | `skill_check(skill_value, modifier)` → dict with `result`, `margin`; `opposed_check(...)` | `world/skillcheck.py` |
| Physical penalty | `Character.physical_modifier()` (overload) | `typeclasses/characters.py` |
| Tool wear | `Tool(DurableObject)`, `condition`, `apply_wear()` | `typeclasses/tools.py`, `typeclasses/durable.py` |
| Food | `Food` | `typeclasses/consumables.py` |
| Materials | `twine`, `stick`, `flint`, `bone` (via corpse harvest) | `world/prototypes.py` |
| Skill precedent | `hunting` (custom, named to avoid `survival`) | `typeclasses/characters.py:443–449` |
| Economic events | `activity_log.record(kind, actor, **fields)`, ten `KINDS` | `world/activity_log.py` |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 15. Open questions

- **FQ1** — `fishing` skill (FP1) or Legend's Survival as written? And does chargen's Fisherman-like profession grant it?
- **FQ2** — How many play rounds, and how strict is the strike window in real seconds? (G1 says generous.)
- **FQ3** — Rig as container contents or as a `rig` attribute on the rod?
- **FQ4** — Who owns a set trap or net in a shared water, and can another player empty it?
- **FQ5** — Wilderness water: per-coordinate profile, a biome-level species table, or no fishing outside authored rooms until Stage 6?
- **FQ6** — Activity-log kind for a catch: `gather` with a field, or a new kind?
- **FQ7** — What does a fumble do: core harm (hook in the hand, a slip), lost tackle, or both by situation?
- **FQ8** — Does an escaped fish return to stock?
- **FQ9** — Is fishing one of the food professions' exclusive *producers*, or is fish the shared food and only oil and salt fish exclusive?

---

## 16. Considered and not proposed

- **A reflex minigame** (react within a second to a cue). Becomes a client trigger at once (§2.2), excludes screen-reader players, contradicts G1.
- **NPC fish buyers** or a fish market fed by the server. Pillar 1.
- **Fish as persistent objects swimming in rooms.** Thousands of objects for one number's worth of state.
- **A ticker per water or per trap.** The project's lazy-evaluation rule; 20 waters × a ticker each buys nothing a timestamp does not.
- **A "fishing rod +10" single item.** Loses every decision tackle gives (§2.1).
