# PolishedWorld — Hunting Design Notes (tracks, stalking, wind, herds)

> **Rev 1 · 2026-11-07** — first version, docs only, with roadmap Rev 48, BACKLOG Rev 70 and README Rev 26. Written from a design chat, the third in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md` and `docs/PolishedWorld_Housing_Design.md`. Unlike the first two, this system is **already shipped** (roadmap Stage 0, `docs/PolishedWorld_Hunting_Decomposition.md`), so the notes propose changes to live behaviour and name every one of them (§6). **Nothing here is locked.** Every numbered item is a proposal (TP…) or an open question (TQ…); a hunting decomposition locks or rejects each one. In the chat Adam took the recommended answer to TQ1–TQ4 as the design's working assumption; each is recorded as a *leaning* under its question, not as a decision. Prior art was read on 2026-11-07; code seams were read against `main` at `2d1c951` (Evennia 6.1.0).
> **Canonical:** `docs/PolishedWorld_Hunting_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** roadmap, *Stage 0 — Hunting* (delivered), and its 2026-11-07 note (Rev 48); the forward-looking halves live in `docs/BACKLOG.md` — *Ecology & Supply*, *Seasonal supply & population memory* (its part (2) is TP9 here and its part (3) is TP2; TP10 adds pressure beside them), and *Professions & Chargen*, *A `hunter` profession* (TP11 would fire its trigger). Both gain a 2026-11-07 annotation (Rev 70) and neither is replaced by this document.
**When to read:** at the start of any hunting decomposition; when *Seasonal supply & population memory* is triggered; at the Stage 5 design session (the wounded quarry, TP12); at the Stage 6 design session (passage records and ranges as coordinate data, §7, §9); and when housing's break-in traces are decomposed (Housing Design §9 reads the same passage log, TP4).
**Departs from shipped behaviour in nine places**, listed with their source lines in §6. The largest: quarry is no longer a standing object in the room; it is met at the end of a stalk.

---

## 1. The idea in one paragraph

A hunter does not walk into a meadow and pick a rabbit off a list. They read the ground: droppings still soft, grass bitten short, a line of prints in the clay by the brook, older ones half washed out by last night's rain. They decide which trail is worth it, follow it with the wind in their face, and close the last distance by stealth against an animal whose senses are better than theirs. Then one shot, clean or not. The world answers back: a wood that was hunted hard goes quiet and the deer move to the far side of their range; in winter they come down from the ridge; at dawn and dusk they feed in the open and by day they lie up in the trees. A skilled hunter knows all this from what they see, not from a number, and an unskilled one walks through the same wood and sees nothing but trees.

---

## 2. Prior art

### 2.1 MUME — the model

Source: MUME's in-game help, *TRACK* (`mume.org/help/track`, generated 2026-11-01). Paraphrased:

- `track` alone examines the ground and, after a delay, reports who and what has passed. How visible a set of tracks is depends on what made it, how long ago, the weather and the terrain; rain and snow make them fade faster.
- An unlucky look shows fewer tracks than are there, and looking again may show more. Tracks are graded on a falling five-step scale from obvious to faint. Bleeding prey is easier to find and follow.
- `track <target>` finds that target's newest trail; moving along it (or `pursue`) keeps tracking automatically until the target is found, the trail is lost, or the hunter stops. Some creatures — fish, birds, spirits — leave no tracks. Skill makes covered tracks findable and tracking faster, up to a limit.
- MUME also has `where <target>`, which looks for the target's tracks in the current room only.

**Worth taking:** the reading as a timed act with a delay; the graded scale; weather and terrain as the modifiers; fewer tracks on a bad reading rather than a failure message; blood making a trail easier; following as movement.
**Not for PolishedWorld:** anything that locates a named target at a distance.

### 2.2 Armageddon — the players' wishlist

Sources: Armageddon's player forum (`gdb.armageddon.org`, topic 52834 and message 994276, 2017). Paraphrased:

- `hunt` shows tracks in the current room; following them meant stopping in every room to use the skill again, and players asked for a separate *track* that keeps a chosen trail from room to room until it is lost.
- The same threads ask for covering one's own tracks, and for an unbroken trail across sand on a windless day — weather as the thing that decides whether a trail survives.

**Worth taking:** reading and following as two acts (TP3, TP5); wind and weather as what keeps or erases a trail (§7, §8).
**Not for PolishedWorld:** nothing structural; covering tracks is filed as a question (TQ9).

### 2.3 Aardwolf and Achaea — the warning

Sources: Aardwolf help *Hunt* and *Newbie-Campaign* (`aardwolf.com/wiki`), the Mudlet Aardwolf GUI page (same wiki), and a bashing script posted to the Achaea forums (`forums.achaea.com`). Paraphrased:

- Aardwolf's `hunt <target>` tells the direction the target went, with a certainty. Players use it as a locator: the help itself teaches the *hunt trick* — try `hunt 2.citizen`, `hunt 3.citizen` and so on until one cannot be hunted, which identifies the target among identical names — and client packages bind a short alias to hunt everything.
- Achaea's community bashing scripts keep a priority list of targets per area and attack whatever is in the room, room after room, with one key to start.

**The lesson (the series' "Achaea lesson"):** an answer that is exact becomes a GPS, and a GPS plus a one-command kill becomes a script. PolishedWorld's shipped loop is already that shape: `hunt rabbit` every thirty seconds in the Meadow, which is topped back up to three rabbits every five minutes (§6). **The rule taken:** the skill lives in reading and choosing — where, when, from which side — and every answer the world gives is graded and partial; supply per area is finite, so a script that hunts all day finds the area empty (TG1, TG2, TG4).

### 2.4 theHunter: Call of the Wild — pressure as memory

Sources: player discussions on the game's Steam forum (`steamcommunity.com/app/518790/discussions`, 2017–2023) and a player guide. Paraphrased:

- Animals keep *need zones* — places they feed, drink and rest at set times of day. A hunter discovers a zone by inspecting tracks and droppings, and the map then shows when the animals will be there.
- Each kill leaves *hunting pressure* around the spot, which fades with time; animals avoid it, and enough of it deletes the need zones inside it until it fades. Players learned to spread kills and rotate between zones so pressure never builds.

**Worth taking:** daily rhythms tied to places; signs as how a hunter learns them; pressure that fades, so overhunting is local and recoverable.
**Not for PolishedWorld:** the exact schedule on a map — once it is known it is farmed, which is the Achaea lesson again. Here the rhythm is learned and inferred from signs, never displayed (TP8).

---

## 3. Design goals

- **TG1 — Read, then act.** Skill lives in reading signs and choosing an approach, never in repetition or reaction time (§2.3).
- **TG2 — Graded answers, never a locator.** Every reading is partial and worded (*fresh, a few hours, old*); a poor roll shows less, it does not say "you failed" (Legend's *Rolling in Secret*, §4; MUME, §2.1).
- **TG3 — The world reads the hunt, and the hunt writes back.** Season, time of day, weather, wind and ground decide where game is and how easy it is to read; kills and disturbance change what the next hunter finds.
- **TG4 — Finite game per area.** Supply is capped by a stock that recovers slowly; overhunting shows, then heals (BACKLOG *Seasonal supply & population memory* (2)).
- **TG5 — No standing quarry.** Nothing waits in a room to be clicked on; an animal is met at the end of a stalk (TP1).
- **TG6 — Lazy and cheap.** Timestamps read on demand, no per-creature ticker, no persistent objects in wilderness (Evennia Reference §14.6), state that survives room recycling (§14.5).
- **TG7 — Source and sink named together** (Economic Philosophy; `docs/PolishedWorld_SourceSink_Ledger.md`).
- **TG8 — Legend's own skills where they exist.** Stealth and Perception are core; the custom `hunting` keeps the place Track holds in Legend.

---

## 4. Legend alignment

**Rules as written:**

- **Track (INT+CON)** — Legend core p. 64, an Advanced skill: locate the tracks of a specific creature and follow them; a test to find the trail and another every hour it is followed. Modifiers for terrain (footprints in sand Easy, across hard cobbles Formidable), for the trail's age and for anything that has covered it, deliberately or by weather. A **critical** means no further tests in pursuit of that quarry; a **fumble** loses the trail for good. Picking up and following a trail takes two minutes to two hours (task times, p. 67). The difficulty examples (p. 40) give tracks in snow as Very Easy (+60 %) and on a busy street as Hard (−40 %).
- **Stealth (DEX+INT)** — p. 55: evading detection, typically opposed by Perception and modified by the situation. A critical puts any later attempt to find the stealthy one at a penalty; a fumble causes a commotion that alerts everyone near.
- **Perception (INT+POW)** — p. 52: the senses; a fumble leaves one oblivious.
- **Evade (DEX×2)** — p. 49: getting out of the way; the animal's side of a chase.
- **Survival (POW+CON)** — p. 63: the core skill for living off the land, also called for when hunting or gathering food for others.
- **Difficulty grades** — p. 39: Very Easy +60, Easy +40, Simple +20, Standard 0, Difficult −20, Hard −40, Very Hard −60, Formidable −80. **Rolling in Secret** (same page): the Games Master may roll for the adventurer and reveal the result only through play.
- **Deer** — *Monsters of Legend* p. 109: wary and easily frightened; lives on forest fringes and in brush, following established feeding and migration trails; small herds of does and fawns with a stag or a few bachelor stags. Skills include Perception 95 %, Evade 70 %, Athletics 75 %, Stealth 25 %. (No ordinary rabbit or hare is statted in either *Monsters of Legend* book.)
- **Animal Snare/Trap** — *Arms of Legend* (`docs/reference/arms_of_legend.md:126`): placing it takes a Survival test, whose result is what an animal's Perception must beat; a sprung snare attacks at 75 %, which the animal must Evade or be held. **Animal Call** (`:124`): +10 % to Survival for hunting. **Ashen Powder** (`:132`): spoils scent-tracking — evidence that AoL treats scent as a tracking channel.

**Translation proposals:**

- **TP-L1 — `hunting` stays the Track-and-kill skill.** It already carries Track's INT+CON (`typeclasses/characters.py:443–455`) and is the only improvable outdoor skill, so it reads tracks (TP3), follows them (TP5) and takes the shot (TP7). Renaming it `track` would be a migration of every character for a word; Survival's hunting uses (snares, calls) also land on `hunting`, because `survival` is the gauge category in this codebase (same comment, `:444–446`).
- **TP-L2 — Stealth for the approach, the animal's Perception against it.** Core rule as written. The `stealth` skill exists and has no call-site (`typeclasses/characters.py:881`); the stalk becomes its first (TQ2).
- **TP-L3 — Evade for the escape.** The shipped `flee_skill` is Evade by another name; per-species values come from *Monsters of Legend* where it has the animal and by judgement where it does not (TQ6).
- **TP-L4 — Readings are rolled in secret.** Reading and following report what the roll earns in words; the tier is never printed. A failed reading shows fewer or older-looking signs, as MUME does; a fumble on following loses the trail, as Legend does.
- **TP-L5 — One Track test per room followed.** Legend tests once per hour followed; a wilderness room is distance, not time, so a room entered along the trail is the unit. A critical ends the tests for that trail, as written.

---

## 5. The loop

Proposed phases. Every reading, following step and stalk is a beat on the shared timed-action slot (`world/timed_actions.py:107`, `start()`; moving away interrupts through `at_pre_move`, `typeclasses/characters.py:1444`).

1. **Arrive and look.** An outdoor room with game in its range shows **signs**, not animals: a line in the room text tiered by what is there and how recently (TP2). Everyone sees the coarse line; a better `hunting` sees more of it, for free, on `look`.
2. **Read.** `track` (TP3) is a short timed act: the room's passage log (§7) is read through a secret `hunting` roll with ground, age and weather modifiers. The answer lists sets of tracks — kind, a number word, freshness, which way they went — and a poor roll lists fewer and vaguer ones.
3. **Choose and follow.** `follow <trail>` (TP5) moves along a chosen trail one room at a time, with a Track test per room; the trail ends where the quarry is, goes cold, or is lost.
4. **Stalk.** Where the trail is hot, `stalk` (TP6) is the approach: Stealth against the quarry's Perception, with wind, load, light, weather and ground as roll terms. Success means the animal is there and has not seen you (TP1's encounter); failure means it has, and it bolts — leaving a fresh trail, so the chase can continue.
5. **Shoot.** `hunt <animal>` is today's opposed test (`commands/hunting_commands.py:96–99`), with the stalk's outcome as a modifier (TP7).
6. **After.** A kill makes today's corpse; harvest is unchanged. The kill writes the area's stock down and its pressure up (TP9); the next hunter reads both in the signs.

What it reads like (illustrative, not a spec):

```
> look
Edge of the Woods
Old trees stand close together, their branches meeting overhead. ...
Deer have been feeding here; the bark is stripped low on two saplings.
The breeze comes from the north.
> track
You crouch and study the ground...
You make out the tracks of several deer, made early this morning,
heading north, and older rabbit runs going nowhere in particular.
> follow deer
You follow the deer north, keeping low...
Stony Ridge
... The deer's tracks are fresh here. They cannot be far.
> stalk deer
You work your way upwind through the scrub...
A doe lifts her head, ears turning, and goes back to grazing. She has
not seen you.
> hunt doe
```

---

## 6. Departures from the shipped loop

Each row is a change to behaviour that `main` has today; each is a proposal.

| # | Shipped today | Proposed | Where shipped |
|---|---|---|---|
| D1 | Creatures stand in the room, are listed by `look` and targeted directly by `hunt <name>` | No standing quarry in game areas; the animal is spawned at the end of a successful stalk (TP1, TQ1) | `commands/hunting_commands.py:69–77` |
| D2 | `CreatureSpawnScript` tops each flagged room up to a fixed count every 300 s | A stock that kills write down and that recovers on read; the script stops serving wild game (TP9) | `typeclasses/scripts.py:174–186`; `server/conf/settings.py:113–117`; `world/seed_data.py:116`, `:141` |
| D3 | `stalk` is an alias of `hunt` | `stalk` becomes its own command (TP6) | `commands/hunting_commands.py:46` |
| D4 | One opposed roll decides the hunt from the moment of arrival | Read → follow → stalk → shot; the shot keeps `opposed_check` and gains the stalk's modifier (TP7) | `commands/hunting_commands.py:96–99` |
| D5 | On a clean escape the creature moves silently through a random exit, or is deleted if there is none | The escape writes a fresh passage record in the direction it fled, which can be followed (TP4); under TQ1 the object itself goes | `commands/hunting_commands.py:151–172` |
| D6 | `flee_skill` is a flat placeholder (30, from the typeclass) | Per-species Evade and Perception (TP-L3, TQ6) | `typeclasses/creatures.py:51`; `world/prototypes.py:493` |
| D7 | `stealth` has no call-site; the improvable label set is `{craft, hunting}` | The stalk is a Stealth call-site and the label gains `stealth` with its test (TQ2) | `typeclasses/characters.py:881–892` |
| D8 | A kill writes nothing to the activity log; only harvesting does (`gather`) | A kill is an economic event too (TQ10) | `commands/hunting_commands.py:374`; `world/activity_log.py:60` |
| D9 | There is no wind | A derived, global wind (§8) | — (grep finds the word only in room and item text) |

Unchanged: the corpse and its lazy decay (`typeclasses/corpse.py`), harvest and its templates (`world/harvest_templates.py:66`), the 30 s cooldown on the shot, and the claim that stops two hunters resolving one animal (`commands/hunting_commands.py:84–89`).

---

## 7. Tracks and the passage log

**TP2 — Signs on `look`.** An outdoor room in a range (§9) adds one sign line, worded by species and tier (*rabbit runs criss-cross the grass*, *deer have been feeding here*, *the wood is quiet*), chosen from the stock and the freshest passage record. `hunting` above a threshold sharpens the line on `look` with no roll and no write — looking never writes, as `ResourceNode._availability_phrase()` already holds (`typeclasses/resources.py:129`). This is BACKLOG *Seasonal supply* part (3), with its skill choice answered as `hunting` (TQ7).

**TP3 — `track` reads the room.** A timed act of some tens of real seconds, shorter with skill (MUME: skill tracks faster, to a limit). One secret `skill_check(hunting, modifier)` (`world/skillcheck.py:58`); the modifier sums ground (soft clay or snow easier, rock harder), age, and weather since the record was made. The tier sets how many records are shown and how exactly: a critical shows all, with counts and close ages; a success the main ones with rough ages; a failure one or two, aged wrongly towards "old"; a fumble nothing, and the hunter believes the ground is empty. Freshness is worded on a falling scale (*still warm*, *this morning*, *yesterday*, *days old*), never as hours.

**TP4 — The passage log (the data).** Each outdoor room keeps a short list of passage records — `(what, count, when, exit_out, bleeding)` — capped at a handful and pruned on write. Writers: a herd shifting within its range (§9), a quarry escaping (D5), a wounded animal (TP12), and **characters moving through outdoor rooms**, written from the arrival hook the room already runs (`typeclasses/rooms.py:358`). Characters are recorded by appearance (*boots*, *two people*, *heavily laden*), never by name; whether a skilled reader can match prints to someone they have met is TQ8. Housing Design §9's break-in traces are a second reader of the same log, not a second mechanism (TQ4).
- Records age by **read-time arithmetic on stored timestamps** — `when` plus the weather that fell since — and must **not** copy `Corpse.decay_modifier`'s shape, which multiplies total elapsed time by the *current* weather and can run backwards (`typeclasses/corpse.py:92–133`; BACKLOG *⚠️ Decay time can run backwards when the weather turns*). To know what fell since, the global `WeatherScript` keeps a short history of `(time, state)` changes beside the `previous_weather` it keeps today (`typeclasses/scripts.py:112–143`) — one small write per weather change (every 1800 s at most, `server/conf/settings.py:102–104`), read by every track.
- **Storage that survives recycling.** Each record carries the room's identity (its coordinate once Stage 6 exists, its dbref in authored areas), and a reader ignores records whose identity does not match the room it is read in. Wilderness recycling keeps Attributes (Evennia Reference §14.5), so a recycled shell's old tracks become invisible instead of leaking to a new place (TQ3).

**TP5 — `follow <trail>`.** Chooses a set of tracks from the last reading and moves along its `exit_out`, one room per beat, with one Track test per room (TP-L5). A success shows the trail continuing; a failure stops the follow with the trail unclear, and a new `track` may pick it up again; a fumble loses this trail for good (Legend). A critical at any step ends the tests for this trail (Legend) — the hunter walks it to its end. Following is ordinary movement, so weight's fatigue per room applies (`typeclasses/characters.py:1470`).

---

## 8. Wind

**TP-W1 — A derived, global wind.** No stored state and no ticker: the wind for any moment is a function of the game day, the period of the day (`world/gametime_utils.py:46–54`, seven periods) and the current weather — a deterministic hash picking one of eight compass points or *calm*, with fog always calm and rain or snow never calm. Global, like weather (`world/weather.py:89`). Anyone outdoors reads it on `look` (*the breeze comes from the north*); no roll, because a wet finger is not a skill.

**TP-W2 — One roll term, on the stalk only.** If the hunter closes in from downwind, the stalk gains; from upwind, it loses; across the wind or in calm, nothing. Direction is read from the exit the hunter arrived through, which works wherever exits are compass points (every exit between the alpha's outdoor rooms is, `world/seed_data.py:168–185`) and is neutral elsewhere. Wind does not touch reading or following, and it does not move animals (TQ5) — one knob, one job.

---

## 9. Herds, ranges and seasons

**TP8 — A range per herd, and a rhythm.** A species in an area has an authored **range**: a few rooms, each with a role — feeding ground, cover, water. Where the herd *is* is a function of season and period: in the open at dawn and dusk, in cover by day, at water in the evening, lower ground in winter and higher in summer (deer follow feeding and migration trails, §4). Nothing moves on a timer: when anyone reads a room, the herd's place is computed, and a shift since the last read writes the passage records that shift would have left (TP4). A rabbit's range can be one room; a deer herd's spans several. The rhythm is never displayed; a hunter learns it from signs and memory, which is theHunter's need zone without the map (§2.4).

**Ranges are authored data**, like rooms today (`world/seed_data.py`), and become coordinate data at Stage 6 (BG6's rule in the housing design: nothing built in play that a map module must know about).

---

## 10. Stock and pressure

**TP9 — Stock: BACKLOG part (2), adopted.** Each range keeps the record BACKLOG *Seasonal supply & population memory* already shapes — a stock, a cap, a timestamp — recovered logistically on read, written down by exactly one site, `Creature.at_death()` with a player killer (P-2; `typeclasses/creatures.py:61`). An encounter needs `floor(stock) ≥ 1`. The fixed targets in `spawn_creatures` become the caps. That entry's open choices — one recovery knob, breeding seasons or not, migration of `spawn_creatures` — stay its decomposition's.

**TP10 — Pressure: disturbance that fades.** A second, separate value per range: failed stalks, escapes and kills stamp it; it decays with its own half-life. While it is high, the herd's Perception rises by a grade and the herd keeps to the far rooms of its range, and the sign line says so (*the wood is quiet*, *the deer are skittish*). It is not a second population knob: stock is how many animals there are, pressure is how warily they behave, and each has one constant (lesson: two knobs doing one job make a system uncalibratable — these are two jobs). Whether pressure ships with stock or after it is TQ11.

---

## 11. Encounter, stalk and shot

**TP1 — The encounter.** On a successful stalk with stock available, the quarry is spawned from its prototype into the hunter's room, already claimed for that hunter (the shipped `ndb.hunted_by` claim, `commands/hunting_commands.py:84–89`). Others in the room see it break cover if the hunter misses. Not shot within a short window, it slips away and leaves a fresh record. The `Creature` typeclass, `at_death()`, the corpse and harvest are unchanged — only *when* the object exists changes (TQ1).

**TP6 — `stalk`.** A timed act: `opposed_check(stealth, quarry Perception, attacker_mod=…)` (`world/skillcheck.py:127`). Terms: wind (TP-W2); `physical_modifier()` for load (`typeclasses/characters.py:603`); light (dawn and dusk help, night hinders, `world/gametime_utils.py:46`); rain and snow mask sound; pressure's grade (TP10). Outcomes: a critical — unseen, close, the herd calm; a success — unseen at range; a stalemate — not yet, try again; the animal wins — it bolts, leaving a hot trail; a fumble — the whole herd scatters and pressure jumps (Legend's commotion). An improvement attempt follows a win, as `hunt` does today (`commands/hunting_commands.py:117`).

**TP7 — The shot keeps today's roll.** `hunt <animal>` stays `opposed_check(hunting, Evade, attacker_mod=…)`; the stalk's tier adds a roll term (unseen and close best), so stalking well is how a modest hunter takes a wary animal. A hunt without a stalk is still possible where an animal is met by chance, at the plain roll.

---

## 12. Snares, calls and the clean kill

**TP11 — The snare: hunting's first recipe.** AoL's snare as written, translated: placing it is a `hunting` test whose result is the number the animal's Perception must beat; it is checked lazily — the next time anyone reads that room, the elapsed time decides whether something walked into it, drawing from the range's stock. A sprung snare holds a small animal (SIZ 3 or less, AoL) until someone takes it — possibly not its owner, which is a trust question players settle (TQ12). Snares wear and break. A hunting recipe fires BACKLOG *A `hunter` profession*'s trigger. **The animal call** (+10 % on the stalk for hunting, AoL) is the second recipe.

**TP12 — The wounded quarry and the clean kill.** A shot that wins narrowly (a success against the animal's success, under whatever margin the decomposition picks) wounds rather than kills: the animal bolts and leaves a **bleeding** trail that is easier to read and follow (MUME), ending at its body. A critical shot is a clean kill and could raise the hide's grade — but harvested parts carry no quality today (`world/harvest_templates.py:66–90`), so that half waits for a quality field on parts. The wound needs no Stage 5 damage: it is a state of the encounter, not hit points; whether Stage 5 should own it instead is TQ13.

---

## 13. Economy

**Sources (all player-made or hunted):** meat, hide and bone as today; snares and animal calls (sticks, `twine` or `plant_fiber`, bone or wood — existing materials).

**Sinks:** snares and calls wear and break; meat and hide spoil on the corpse as today; the stock itself is the cap on supply, so price can move with scarcity — the signal pillar 1 needs (BACKLOG *Seasonal supply*, *Why it matters*).

**Services hunting creates:** guiding (a skilled tracker sells knowledge of where a herd ranges this season), hunting to order, setting snare lines for others, and dressing game.

**Coin:** none proposed.

**Logging:** a kill, a snare placed and a snare emptied are economic events (D8). New `KINDS` or fields on existing ones is TQ10; the report keeps a pinned copy of the set.

**Ledger:** every new item gets its source and sink row in the same commit.

---

## 14. Multiplayer and server load

- **Per-character slots.** `track`, `follow` and `stalk` occupy the hunter's own `ndb.timed_action`; nothing ticks per creature or per range.
- **One quarry, one hunter.** The encounter is claimed at spawn (TP1); two hunters stalking the same herd at once compete for the stock, which is read and written in one synchronous step at the kill — the same serialisation `ResourceNode.harvest()` relies on (`typeclasses/resources.py:105`).
- **Passage writes.** One small Attribute update per character step in an outdoor room — the one real cost in this design. The list is capped and pruned on write; if measurement shows it matters, characters can be recorded only on soft ground or every other step (TQ3).
- **Weather history.** One list on a global script, appended at most every 1800 s, read by every track; capped.
- **Wind.** Pure computation; nothing stored.
- **Object count.** Fewer than today: no standing animals in game areas, one object per encounter for the minute it lasts, and no spawn ticker scanning flagged rooms for wild game.
- **Message volume.** Readings and stalks message the hunter; the room hears a bolt, a shot and a kill.

---

## 15. Immersion extras

- **Snow.** Tracks in snow are Very Easy (Legend's own example) — and so are yours.
- **Antlers shed in spring**, found by reading signs in a deer range: a seasonal bone source.
- **Birds fall silent** in a room a stalk is fumbled in, for anyone there: a line in the room for a little while.
- **The dawn hunt.** Players learn that the meadow is worth reading at dawn and dusk, not at noon, without the game ever saying so.
- **Records for the gazette.** The season's largest stag, the first deer taken from the ridge (BACKLOG *In-world gazette*).

---

## 16. Layers — a suggested order

1. **Slice 1 (the smallest real thing):** the passage log with escapes and character steps as writers; weather history; `track` and `follow` with Track tests; sign lines on `look`; derived wind; `stalk` as a Stealth call-site; the encounter (TP1) drawing from today's `spawn_creatures` counts read as caps, with no stock memory yet. Rabbit only; its Perception and Evade set by judgement (TQ6).
2. **Slice 2:** stock (TP9) and pressure (TP10) — when BACKLOG *Seasonal supply & population memory* is triggered, because stock changes what hunting costs the world and that is settled before a cohort, not under one (its own *Trigger*).
3. **Slice 3:** ranges and rhythms (TP8); deer as the second species, with *Monsters of Legend*'s numbers.
4. **Slice 4:** snares and calls (TP11) — the first hunting recipes, and with them the `hunter` profession question.
5. **Slice 5:** the wounded quarry (TP12); the clean-kill hide once parts carry quality.
6. **With housing slice 3:** break-in traces as a reader of the passage log.
7. **At Stage 6:** passage records and ranges keyed by coordinate.

**Prerequisites:** none for slice 1. **Not prerequisites:** Stage 5 (the shot is not combat, as today), the webclient, the economy milestone (except slice 2's own trigger).

---

## 17. Seams in today's code (read at `2d1c951`)

| Need | Seam | Where |
|---|---|---|
| The shot, the claim, the escape | `CmdHunt.func`, `ndb.hunted_by`, `_flee` | `commands/hunting_commands.py:50–149`, `:84–89`, `:151–172` |
| `stalk` alias to move | `aliases = ["stalk"]` | `commands/hunting_commands.py:46` |
| d100 test, tiers | `skill_check(skill_value, modifier)`; `opposed_check(…, attacker_mod, defender_mod)` | `world/skillcheck.py:52–58`, `:127` |
| Improvement on a win | `attempt_skill_improvement`; label set held by a test | `typeclasses/characters.py:901`, `:881–892` |
| `hunting` (INT+CON), `stealth`, `perception` | skill definitions | `typeclasses/characters.py:359–470` |
| Physical penalty | `Character.physical_modifier()` | `typeclasses/characters.py:603` |
| Timed, interruptible acts | `start()`, `claim()`, `interrupt()` | `world/timed_actions.py:107`, `:198`, `:229` |
| Interrupt on move; fatigue per step | `at_pre_move`, `at_post_move` | `typeclasses/characters.py:1444`, `:1470` |
| Arrival hook in rooms | `Room.at_object_receive` (puppets only) | `typeclasses/rooms.py:358` |
| Creature data, death, corpse spawn | `Creature`, `at_death()` | `typeclasses/creatures.py:34`, `:61` |
| Spawn by flagged room | `CreatureSpawnScript.at_repeat` | `typeclasses/scripts.py:149`, `:174–186` |
| Lazy decay, its backwards-running shape | `Corpse.decay_modifier`, `_elapsed_game_hours` | `typeclasses/corpse.py:92–133` |
| Harvest parts (no quality field) | `HARVEST_TEMPLATES` | `world/harvest_templates.py:66–90` |
| Number-free availability text | `ResourceNode._availability_phrase` | `typeclasses/resources.py:129` |
| Global weather, its state | `WeatherScript`, `get_current_weather()`, four states | `typeclasses/scripts.py:112–143`; `world/weather.py:23`, `:89` |
| Periods of the day, season | `TIMES_OF_DAY`, `get_season()` | `world/gametime_utils.py:46–54`, `:132` |
| Room text by season and weather | `room_states` | `typeclasses/rooms.py:198` |
| Authored rooms and exits | `ROOMS`, `EXITS` | `world/seed_data.py:79`, `:159` |
| Economic events | `activity_log.record`, ten `KINDS` | `world/activity_log.py:60` |
| Grid and wilderness rules | recycling keeps Attributes; O(n) object scan | Evennia Reference §14.5, §14.6 |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **TQ1** — Is wild quarry spawned at the end of a stalk (TP1), or kept as standing objects that are hidden until stalked? *Leaning (chat, 2026-11-07): spawned at the end of the stalk — nothing standing to script against, no persistent objects in wilderness, and the stock is the cap. The authored alpha rooms move to it with the rest.*
- **TQ2** — Does the stalk train Stealth? *Leaning: yes — the stalk is Stealth's first call-site, and `stealth` joins the label set at `typeclasses/characters.py:892` in the same commit, with the test that holds the set against the call-sites.*
- **TQ3** — Where does the passage log live? *Leaning: a capped Attribute list on each room, every record stamped with the room's identity and filtered on read, so recycled wilderness shells cannot leak tracks. Open within it: whether characters are recorded on every outdoor step or only on soft ground.*
- **TQ4** — Do character tracks belong to this design or to housing? *Leaning: here — the log and its reading are one mechanism; Housing Design §9's traces are a reader of it.*
- **TQ5** — Does wind move animals (herds drifting downwind of a disturbance), or stay one roll term? Proposed: one roll term only.
- **TQ6** — Per-species Perception and Evade for the rabbit, which *Monsters of Legend* does not stat; and whether `flee_skill` is renamed or read as Evade.
- **TQ7** — Sign lines: `hunting` (proposed here) or `perception` — the choice BACKLOG *Seasonal supply* part (3) left open; and the thresholds.
- **TQ8** — Can a skilled tracker tell whose prints these are, if they have met the person? Privacy against the Haven & Hearth idea that crime leaves evidence.
- **TQ9** — Covering one's own tracks (Armageddon's request; AoL's ashen powder for scent): in slice 1, later, or not at all?
- **TQ10** — Activity-log kinds for a kill and for snares: new kinds or fields on existing ones?
- **TQ11** — Does pressure (TP10) ship with stock or after it?
- **TQ12** — Snares that anyone can empty: allowed theft that leaves tracks, or owner-only?
- **TQ13** — The wounded quarry: a state of the encounter now, or Stage 5's locational damage later?
- **TQ14** — Reading time, follow time and the encounter window in real seconds, at 4× game speed (a game hour is fifteen real minutes).

---

## 19. Considered and not proposed

- **A locator** (`where`, Aardwolf's `hunt` direction to a named target). The Achaea lesson (§2.3).
- **Need zones shown on a map with times.** Farmed as soon as known (§2.4).
- **Per-creature AI tickers** wandering herds through rooms. TG6; the rhythm is computed on read instead.
- **Tracks as objects in rooms.** An object per footprint; the log is a list on the room.
- **Reaction-speed minigames** for the shot. The skill is in reading and choosing (TG1), as fishing decided (Fishing Design).
- **NPC buyers for pelts or bounties for pests.** Pillar 1.
- **Copying `Corpse`'s decay shape for track age.** It runs backwards when the weather turns (§7).
