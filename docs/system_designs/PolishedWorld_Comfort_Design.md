# PolishedWorld — Comfort, Haven & the Good Evening Design Notes (the tone, one comfort read, havens, the threshold, softness in text, company and gifts)

> **Rev 1 · 2026-11-09** — first version, docs only, with roadmap Rev 62, BACKLOG Rev 89, README Rev 40, Evennia Reference Rev 30 and the series handoff `docs/system_designs/HANDOFF.md` Rev 3. Written from a design chat, the sixteenth note in the one-system series, and the first that is not one system: it names the tone the other fifteen are written in — *hard survival, but cozy*, put as **hard roads, warm hearths** — and takes in the queue's entry *comfort, morale & the good evening*, whose question was whether one term gathers comfort or each system invents its own buff. It was written off the queue at Adam's request; the next note is still the newcomer's economy (roadmap Rev 61). **Nothing here is locked**, with one exception: the tone line itself, which Adam asked for and which this patch adds under the roadmap's *North star* as a lens, not a fifth pillar (EP1, EQ2). Every numbered item is a proposal (EP…), a goal (EG…) or an open question (EQ…); the letter is *E*, for ease and hearth, free across `docs/`, `world/`, `commands/`, `typeclasses/` and `server/` when checked (Cooking's departure rows E1–E8 share the letter, not the shape); this document's own departure rows are X1–X2. Adam took the chat's recommendations as given; they are recorded as leanings (EQ2–EQ4). Three things were found while writing that the chat did not weigh, and they are recorded rather than decided: a haven that stopped all taking would be the risk-free storage Housing BG5 and Storage DG4 forbid, so the proposal guards bodies, never goods set down (EP10, EQ5); the first chat's suggestion that comfort join the rest slice of roadmap Stage 4.6 meets that stage's rule of no new content (EQ6); and the shipped weather broadcast skips indoor characters, which is the opposite of the contrast this design wants (X2). One defect was found in the chat and is filed rather than designed: room echoes cannot start at Evennia 6.1.0 (§11, BACKLOG *⚠️ Room echoes cannot start*). Prior art was read on 2026-11-09; code seams were read against `main` at `3bb964e` (Evennia 6.1.0).
> **Canonical:** `docs/system_designs/PolishedWorld_Comfort_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (a cross-cutting tone and one feature, before any decomposition).
**Home:** `docs/roadmap.md`, *North star* (the tone line, EP1) and the parallel backlog, *Comfort, haven & the good evening* — a new entry (Rev 62), because nothing owned comfort as a whole: Rest Design owns where one sleeps and the ceiling a place sets (NP9) and took Valheim's comfort only for that (Rest §2.4); Cooking Design proposes a well-fed buff (CP15); Temperature Design makes fire and roof the remedies (KP6, KP8); Housing Design gives a house a hearth slot (BP7) and smoke from the chimney (§13); and the death contract's open looting runs the same in the temple as in the woods. Stage 5 gains a dated note: the haven is its decision (EP9–EP13, X1). `docs/BACKLOG.md` gains one entry and one note (Rev 89): **⚠️ Room echoes cannot start** (*World & Rooms*), OPEN, and an annotation on *Builder QoL for dynamic rooms*, whose `roommsg` command would wrap a setup that does not run. `docs/PolishedWorld_Evennia_Reference.md` §2.5 is corrected (Rev 30).
**When to read:** at the start of every decomposition, for the three questions of EP2; when Stage 5's design session decides PvP, theft from a person and the corpse (EP9–EP13, X1); when Cooking's well-fed buff (CP15) or Rest's sleep (NP6–NP13) is decomposed — whichever ships first carries the comfort read (EP4); when Housing's parts are decomposed (the hearth, EQ3); when the echo defect is taken (§11); before the next building pass (EP17–EP19); with *markets & taverns*, *temples & faith*, *settlements & commons*, *law/crime/bounties*, *music & instruments* and *animal taming* from the design-series queue.

---

## 1. The idea in one paragraph

The road out of the settlement is hard and stays hard: the rain soaks through, the night is cold, the pack is heavy, and nobody is coming to help. The point of that road is the door at the end of it. You come in out of the snow and stamp it from your boots; the rain you were walking in a moment ago is now a sound on the roof; someone has the fire going, someone else is mending a sleeve by it, and a third is cooking something that smells better than trail food. Nobody here can hurt you or reach into your pack. You sit down, eat, warm through, and for a while nothing presses — and when you leave in the morning the good meal and the dry clothes last longer than they would have if you had eaten them alone in a wet camp. None of this is free and none of it is sold by the game: the fire is someone's wood, the meal someone's cooking, the bed someone's work. The world gives the contrast; the players make the comfort.

---

## 2. Prior art

### 2.1 Project Horseshoe — the definition, and The Sims Online as the lesson

Sources: Daniel Cook, *Cozy Games* (`lostgarden.com`, 2018), the published text of the Project Horseshoe 2017 workgroup report *Coziness in Games: An Exploration of Safety, Softness, and Satisfied Needs* (Short, Ordon, Hurd, Howe, Forbes, Eiserloh, Diaz, Cook), read 2026-11-09. Paraphrased:

- Coziness is how strongly a game evokes three things together: **safety** (no impending loss or threat), **abundance** (basic needs met, so higher ones — company, beauty, mastery — get attention) and **softness** (gentle, low-stress signals). It is an ingredient that can be added to hard genres, not a genre.
- **Contrast enhances it only from outside.** Cold rain on a window makes a reading nook warmer; the same rain through a broken window ends it. Thresholds between the cozy and the dangerous are best when they are distinct to see and to cross — in from a snowstorm to a log cabin.
- **The cozy sandwich.** Dark Souls' bonfires are the report's example of coziness inside a hard game: no danger in reach, the currency spent and so safe, storage reached, the fire's sound and light — a loop of desire, adventure into danger, and respite.
- **What negates it:** extrinsic rewards that turn a pleasure into a transaction; any threat; *responsibility* — mandatory upkeep, needy things that demand constant care; intrusive notifications; non-consensual social presence; opulence and status display. A *home* is listed as cozy-adjacent, not cozy, because homes carry responsibility. A quaint bazaar loses its charm once players optimise it.
- **The lesson — The Sims Online.** It looked cozy (pleasant houses, friendly neighbourhoods), but its housing and other resources were zero-sum, and gangs ran protection rackets on top of them. The report's conclusion: coziness has to exist at the level of the systems, or the skin does not hold.
- Also: safety in numbers (EverQuest players resting together at a camp, trusting each other to defend it); let conversation ramble — low-intensity group crafting that leaves attention free to talk; gifting as a signal of abundance; a relaxed guardian or a sleeping cat as a sign that a place is safe; seasons and ritual.

**Worth taking:** the three ingredients as a lens (EP2); contrast kept outside the window (EG2, X2, EP14–EP16); respite as one half of the loop, never the whole game (EG1); no nagging upkeep (EP3); systems, not skins — a haven must be safe in its rules (EG5, EP9–EP13); small rewards for comfort, so it is not optimised into a queue (EG3); company, gifts, lingering and the relaxed guardian (EP20–EP22).

**Not for PolishedWorld:** a game that is cozy all over (EG1); the removal of scarcity — scarcity outside is what makes the inside worth reaching.

### 2.2 The Diku lineage — peaceful rooms and places that heal

Sources: *Manual for Using OLC on ROM 2.4* (mirrored on `blinkenshell.org`), LuminariMUD's *Room Flags Reference*, MUME's documentation on rooms (`docs.mume.org`), and the Cleft of Dimensions wiki, *Statistics* (read 2026-11-09). Paraphrased:

- ROM's builders set a heal and mana rate per room as a percentage of normal, and a SAFE flag that forbids killing and stealing there.
- LuminariMUD's PEACEFUL flag blocks every attack and offensive ability and is used for towns and newbie areas; a REGEN flag doubles natural recovery in sanctuaries and rest areas.
- MUME lists peaceful rooms, where combat is impossible, among its special room flags.
- In Cleft of Dimensions (a ROM game), recovery is faster when a character sits, rests or sleeps on furniture or in certain rooms.

**Worth taking:** that text MUDs have marked their refuges in the rules for thirty years — a room flag set by builders (EP9); that the place, not a potion, is what restores (EP5).

**Not for PolishedWorld:** a heal rate per room as a builder's number — comfort here is read from what the room holds (EP4); peace everywhere in town, including the streets (EP12).

### 2.3 Valheim — read for Rest

Rest Design §2.4 read Valheim's *Rested* and its comfort level (fire, roof, furniture lengthen the effect, not strengthen it) on 2026-11-08 and took fire and roof as the camp's two halves. This document takes the same rule for every good state, not only sleep (EG3), and keeps Rest §19's refusal to count furniture.

---

## 3. Design goals

- **EG1 — Hard roads, warm hearths.** Danger and scarcity live outside; comfort is a place one reaches and keeps, never a difficulty setting. Nothing here softens the road: Temperature's, Rest's and the death contract's consequences stand as designed outside a haven (Temperature KG4 already keeps temperate weather harmless).
- **EG2 — Contrast stays outside the window.** The world's harshness is seen and heard from inside a haven and never reaches in (§2.1).
- **EG3 — Comfort lengthens, never strengthens.** Better places make good states last longer; no comfort raises a skill, a roll or a rate (Rest NP9, §2.3). Small enough that nobody queues for it.
- **EG4 — Comfort is read, never kept.** It is worked out from what the room and the character hold at the moment a good state begins; nothing ticks for it.
- **EG5 — Systems, not skins.** A place that is called safe is safe in its rules, and no cozy place rests on a zero-sum claim one player can hold against the rest (§2.1, The Sims Online).
- **EG6 — Every comfort is a player's work.** The fire is someone's wood, the bed someone's carpentry, the meal someone's cooking (pillar 1). The game authors only the floor: the temple's shelter and pallets (Rest NP12, NG4).

---

## 4. Legend alignment

**Rules as written:**

- **Survival** — p. 63: a Survival test is required each day an Adventurer lacks food, water or a safe place to sleep, and Survival tests are not used in a city or town. The rulebook draws this design's line itself: hardship belongs outside civilisation.
- **Cost of Living** — pp. 84–85: Adventurers between adventures spend on food, rent and socialising, and the Standard of Living table runs from *Subsistence* through *Within Means*, *Comfortable* and *Luxurious* to *Ostentatious*, as a share of personal wealth; the text notes that luxury is relative to what one has.
- **Odd Job Table** — p. 85: *Bar Keep* (5 CP a day, free lodging) and *Bard/Busker* (1D8 CP) among the odd jobs.
- **Equipment** — p. 112: the bedroll; p. 118: the four-person tent keeps its occupants dry but is not comfortable, which is why Adventurers buy good bedrolls and warm clothing (both already cited by Rest Design §4).

**Translation proposals:**

- **EP-L1 — The settlement line is p. 63's.** A haven is where the road's tests stop; in this game that is a room flag, and the tests it stops are the ones a haven guards against (EP10), not the survival gauges, which keep running everywhere (EG1).
- **EP-L2 — Standard of living is not tracked.** It is what players buy from one another — a bed, a meal, a fire — and the comfort read (EP4) is its only mechanical trace. No wealth share is deducted.
- **EP-L3 — The bar keep and the busker are players' trades.** p. 85's odd jobs become services: keeping a fire and a room, playing for coin (*music & instruments*, *markets & taverns*).
- **EP-L4 — Legend's prices are not used.** Pillar 1.

---

## 5. The loop

1. **Go out.** Gather, hunt, haul — on the road, where nothing is safe (EG1).
2. **Come back over a threshold.** The weather is shaken off at the door and heard from inside (EP14–EP16).
3. **Be warm, dry, fed, bedded and in company.** Each is something a player made or keeps (EP4, EG6).
4. **Linger.** Mend, cook and talk by a shared fire; give and receive (EP20–EP22).
5. **Leave better.** The good states begun in comfort last longer on the next road (EP5).

---

## 6. Departures from shipped behaviour

Each row is a change to behaviour that `main` has today; each is a proposal.

| # | Shipped today | Proposed | Where shipped |
|---|---|---|---|
| X1 | A player corpse is its owner's to loot for 72 game hours anywhere; after that anyone may take from it | In a haven, a player corpse stays its owner's until it crumbles (EP11) — Stage 5's decision, with the haven | `typeclasses/corpse.py:279`, `:293`; `server/conf/lockfuncs.py:35` |
| X2 | A weather change is told to every online character outdoors; characters indoors hear nothing | Characters indoors hear a muted line for the change (*rain begins to drum on the roof*) (EP15) | `world/weather.py:36–41`, `:60–87` (the skip at `:84–86`) |

Unchanged: the survival tick and every gauge, everywhere (EG1); `is_indoor` and the thermal regime (`world/thermal.py:68`); the death contract outside havens; `rest` (Rest Design's O3 is its own).

---

## 7. The tone

**EP1 — One line under the roadmap's North star.** *Hard roads, warm hearths: the world is hard outside and comfortable inside, and players make the inside.* An unnumbered line under the four pillars — a lens every epic is read through, not a fifth pillar an epic can be justified by (EQ2). Added in this patch.

**EP2 — Three questions for every decomposition.** Where is the danger? Where is the refuge? What does the threshold between them say? A decomposition that cannot answer the first has made the road soft; one that cannot answer the second has made the game a chore. Recorded here and pointed to by the roadmap line; no process document changes.

**EP3 — Upkeep shows; it never calls.** Everything that wears — a hearth's fuel, a roof, bedding — shows its state in words when someone is there to read it (Housing BG4, Farming GG2). No message reaches a player who is elsewhere, and nothing cozy demands attention on a timer: one comes home to a cold hearth and a thin roof, never to a ruin that fell in a moment. Neglect is a slope (§2.1, *responsibility*).

---

## 8. One comfort read

**EP4 — One read, six yes-or-no sources.** A proposed duck-typed `comfort(character)` counts what holds at the moment it is read:

| Source | Yes when | Today |
|---|---|---|
| **warm** | neither `ColdStress` nor `HeatStress` is on the character | `world/survival_buffs.py:51`, `:72` |
| **dry** | the room is indoors, or the weather is not `raining` or `snowing` (Temperature KP7's wetting replaces this when it ships) | `world/thermal.py:68`; `world/weather.py:23` |
| **fed** | hunger and thirst are both above their lowest descriptions, or a well-fed buff holds (Cooking CP15) | `typeclasses/characters.py:282`, `:300` |
| **bedded** | the room or the character offers bedding (Rest NP10's `bedding()`; the temple's pallets, NP12) | not shipped |
| **company** | another puppeted character is in the room | — |
| **safe** | the room is a haven (EP9) | not shipped |

The count, 0–6, is read as a word: *uneasy* (0–1), *settled* (2–3), *comfortable* (4–5), *content* (6) (EQ8). Fire counts through *warm* (Temperature KP8) and light through nothing — a dark warm room is comfortable; Light owns darkness's own effects.

**EP5 — Comfort lengthens a good state as it begins.** When a good state starts — the first is Cooking CP15's well fed; later a warm drink, a song, a bath — its duration is multiplied by 1 + comfort/6: unchanged with nothing, doubled with everything (EG3, EQ8). Nothing is made stronger, and nothing already running is changed by walking in or out. A bad state is not shortened by comfort; its own remedy does that (Temperature KP6, KP8).

**EP6 — One term, not one per system.** Every system that adds a good state reads `comfort()` rather than inventing its own place bonus. Rest's ceiling stays Rest's: bedding sets how rested one can become (NP9); comfort sets nothing there (EQ4).

**EP7 — Comfort is shown.** `status` (`commands/character_commands.py:39`) gains one line, the word; the webclient's survival panel can carry the same word (EQ13).

**EP8 — Company counts once.** One other puppeted character in the room is company; ten are no more. A statue is not company (`typeclasses/characters.py:472`) (EQ9).

---

## 9. Havens

**EP9 — A haven is a room flag set by staff.** A proposed `is_haven` room attribute on authored settlement interiors: the Old Temple first — already indoors, the respawn point and the newcomer's lit room (`world/seed_data.py:81–92`; Light LP2, Rest NP12) — then a tavern's common room or a hall when settlements exist. Staff set it; no player command sets it (EQ12).

**EP10 — A haven guards bodies, never goods set down.** In a haven no one may attack, no one may take from another character's person — awake, asleep or a statue — and a player corpse stays its owner's (EP11). Anything set on the floor, on a shelf or in a container in the room is as open as it is today: a haven is not a bank, and Housing BG5 and Storage DG4 stand (EQ5).

**EP11 — The corpse in a haven (X1).** A body that dies in a haven — of hunger, thirst or cold, since nothing else kills there — stays its owner's until it crumbles, rather than for the 72 game hours of the grace (`typeclasses/corpse.py:279`). It is bounded by the corpse's own decay, so it does not become storage (EQ7).

**EP12 — Havens are few, and the wild has none.** The streets, the yard and the fields are not havens; a camp is comfort, never a haven (Rest NP17–NP18). Danger begins at the door (EG1).

**EP13 — Enforcement is Stage 5's.** Today nothing attacks and nothing takes from a person, so the flag has only two readers before combat: the comfort read (EP4) and X1. Stage 5's design session decides PvP, theft from a person and the corpse together, and reads this section.

---

## 10. The threshold

**EP14 — Coming in from weather gets one line.** A character who moves from an outdoor room into an indoor one while it is raining or snowing reads one line — *you shake the rain from your cloak*, *you stamp the snow from your boots* — from `at_post_move` (`typeclasses/characters.py:1470`), reading the source room's `is_indoor` and the current weather (`world/weather.py:89`). No state is stored; the line is the mover's alone.

**EP15 — The weather is heard from inside (X2).** The shipped broadcast skips indoor characters (`world/weather.py:84–86`). Indoors, a muted line per state is proposed instead: *rain begins to drum on the roof*, *the wind drops and snow settles against the shutters*, *the rain on the roof eases*. The contrast is the point (EG2).

**EP16 — Indoor descriptions carry the outside.** The project's `room_states` already adds the global weather to every room's states, indoors included (`typeclasses/rooms.py:242–250`), so an indoor description can say `$state(raining, Rain drums on the roof.)` today. An authoring convention, no code — for BACKLOG *Builder QoL for dynamic rooms* (3).

---

## 11. Softness in text

**EP17 — Echoes are the MUD's music, and they are broken.** ExtendedRoom's random room messages are the text game's ambient sound — the fire settling, a cart passing outside. At 6.1.0 they cannot start: `_start_broadcast_repeat_task` hands `repeat()` the method `repeat_broadcast_msg_to_room` (`evennia/contrib/grid/extended_room/extended_room.py:198–202`), but the method is named `repeat_broadcast_message_to_room` (`:216`), so any room with a rate and messages raises `AttributeError` when it starts (still so on Evennia's `main`, 2026-11-09). The project also writes `db.room_message_rate` (`typeclasses/rooms.py:355–356`) where the contrib reads a class attribute (`:186`), and the room docstring's `@py` recipe (`typeclasses/rooms.py:109–111`) sets a Python attribute that a reload loses. Filed as BACKLOG **⚠️ Room echoes cannot start**; Evennia Reference §2.5 is corrected.

**EP18 — Echoes are quiet and of the place.** Minutes apart, not seconds; each with a source in the room or just outside it; danger only far off (*wolves, somewhere beyond the ridge*); chosen by the room's states — season, time, weather — once the *Biome fragment library* exists. A haven's echoes are its fire, its people and its weather on the roof.

**EP19 — A haven is written warm.** Light of a clear source, natural materials, mundane objects at human scale, signs of plenty (a pot on the hook, wood stacked by the door); never opulence (§2.1). A writing convention for BACKLOG *Builder QoL for dynamic rooms* (3), applied first to the Old Temple's description.

---

## 12. Company, gifts and lingering

**EP20 — `give` is the gift.** Evennia's `give` is in the game unchanged (`evennia/commands/default/general.py:545`), and `pose` beside it (`:724`). A gift needs no new code; whether gifts are logged is EQ10.

**EP21 — Nothing in a haven moves anyone on.** No loitering timer, no idle kick in a haven; the shared fire's low-intensity work — crafting today, cooking and mending later, each a timed action on the one shared slot (`world/timed_actions.py:107`) — leaves the hands busy and talk free (§2.1, *let conversation ramble*).

**EP22 — The relaxed guardian.** The sweeper (`typeclasses/npcs.py:68`, BACKLOG *Ambient sweeper NPC*, DONE) is the report's sign that a place is safe: someone at ease in it. More such figures are welcome on the sweeper's terms — they sell nothing and decide nothing (pillar 1); a cat asleep by the hearth is *animal taming*'s.

---

## 13. Economy

**Sources:** none. Comfort makes no goods.

**Sinks:** comfort is demand for what wears and burns — fuel for fires and hearths (Forest YP1), bedding (Rest NP11), cooked meals (Cooking CP15), mended clothes against the road (Textiles).

**EP23 — Comfort is demand without an NPC.** The traveller comes in cold and pays the woodcutter's wood, the cook's stew and the bedmaker's work, or a player who keeps all three; the comfort read is the reason the stew beats raw meat in a cold camp. **Services:** the fire-keeper and the bar keep (EP-L3), the cook, the busker, the bedmaker, the woodseller.

**EP24 — No exclusive, and nothing for sale by the game.** Anyone may keep a fire or a room. No NPC sells a meal, a bed or a night (pillar 1, EG6).

**Coin:** none. **Logging:** EQ10.

---

## 14. Multiplayer and server load

- **Nothing ticks.** `comfort()` is computed when a good state begins and when `status` is read (EG4); six cheap reads.
- **Company is one scan.** One pass over the room's contents for another puppeted character, stopped at the first.
- **The threshold is one message per move**, only on outdoor-to-indoor moves in rain or snow (EP14).
- **The indoor weather line** reuses the shipped broadcast's one pass over sessions (`world/weather.py:77–87`); a weather change happens at most every 1800 s.
- **Echoes** run on Evennia's non-persistent `repeat()` per room with messages; a few dozen rooms at minutes apart is negligible. Whether a room echoes to nobody is EQ11.
- **Havens are a lock check.** A room attribute read where Stage 5 attacks or steals, and in the corpse's grace lock (X1).

---

## 15. Immersion extras

- **The good evening.** In a haven at evening with a lit fire and company, `look` adds one line — *the room is warm and full of low talk* — read, never pushed.
- **Smoke from the chimney** (Housing §13) and *smoke rises to the north* (Cooking CP2): the outside sees who is home.
- **Seasons as ritual.** Autumn's stores, the first snow heard on the roof, the first warm evening of spring — Storage §15, Rendering §15 and Pottery §15's seasonal work, gathered in *calendar, festivals & culture*.
- **Music later.** Playing by the fire is a good state (EP5) once *music & instruments* exists.

---

## 16. Layers — a suggested order

1. **Now — the tone line** (EP1) in the roadmap, with this document. Docs only.
2. **Any small session — the echo defect** (BACKLOG *⚠️ Room echoes cannot start*), then the Old Temple rewritten warm with two or three echoes (EP17–EP19). Independent of everything else.
3. **With or after Stage 4.6 — the threshold and the indoor weather line** (EP14, EP15, X2). Small; no new content.
4. **With the first good state — the comfort read** (EP4–EP8), with Cooking CP15's well fed or a later good state, whichever is decomposed first.
5. **With Stage 5's design session — havens** (EP9–EP13, X1).

**Prerequisites:** none for 1–3; a good state to lengthen for 4; Stage 5 for 5. **Not prerequisites:** the webclient, Housing, the economy milestone.

---

## 17. Seams in today's code (read at `3bb964e`)

| Need | Seam | Where |
|---|---|---|
| Warm | `ColdStress`, `HeatStress`; `thermal_regime`; comfort bands | `world/survival_buffs.py:51`, `:72`; `world/thermal.py:46`, `:38–43` |
| Indoors | `is_indoor` makes a room temperate | `world/thermal.py:68` |
| Weather | `WEATHER_STATES`; messages; broadcast skipping indoors; current weather | `world/weather.py:23`, `:36–41`, `:60–87`, `:89` |
| Room states | global weather injected into every room's states | `typeclasses/rooms.py:198`, `:242–250` |
| Echoes | rate and messages; the start and its misnamed callback; the broadcast method | `evennia/contrib/grid/extended_room/extended_room.py:186–187`, `:198–202`, `:216–222` (6.1.0) |
| Echoes, project side | `db.room_message_rate`; the docstring's `@py` recipe | `typeclasses/rooms.py:355–356`, `:109–111` |
| Fed | hunger and thirst gauges | `typeclasses/characters.py:282`, `:300` |
| Moves | `at_post_move` | `typeclasses/characters.py:1470` |
| Statues | `at_post_unpuppet` | `typeclasses/characters.py:472` |
| Corpse grace | `_PLAYER_GRACE_HOURS`; the lock; the lockfunc | `typeclasses/corpse.py:279`, `:293`; `server/conf/lockfuncs.py:35` |
| Status | `status` | `commands/character_commands.py:39` |
| Gifts, poses | `give`, `pose` (Evennia default cmdset) | `evennia/commands/default/general.py:545`, `:724` (6.1.0) |
| The temple | Old Temple seed | `world/seed_data.py:81–92` |
| The guardian | `Sweeper`, its script | `typeclasses/npcs.py:68`, `:50` |
| Activity log | `KINDS` | `world/activity_log.py:60` |

Re-read every row against live source before a decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **EQ1** — The letter. *Leaning: E, for ease and hearth, as used here; Cooking's departure rows E1–E8 share the letter, not the shape.*
- **EQ2** — Is the tone a fifth pillar or a line under the four? *Taken (chat, 2026-11-09): an unnumbered line under the North star, a lens and not a justification — applied in roadmap Rev 62 (EP1).*
- **EQ3** — Is a player's own house a haven? *Leaning (this document's; the chat asked without one): later, for its owner and guests, with Housing's door and Stage 5, and on EP10's terms — bodies guarded, goods not — so Housing BG5 holds.*
- **EQ4** — One comfort term, or one per system? *Leaning (chat, 2026-11-09): one term (EP6).*
- **EQ5** — Found while writing: a haven that forbade all taking would be risk-free storage (Housing BG5, Storage DG4). *Leaning: a haven guards bodies, never goods set down (EP10).*
- **EQ6** — Found while writing: the first chat suggested comfort join Stage 4.6's rest slice, but the roadmap gives that stage no new content (Rev 61). *Leaning: no — 4.6's decomposition reads this document and leaves room (one place where a good state's duration is set), and the comfort read ships with the first good state (§16 step 4).*
- **EQ7** — Does a corpse in a haven stay its owner's until it crumbles (X1)? *Leaning: yes; Stage 5 decides it with the haven.*
- **EQ8** — The word ladder and the multiplier. *Leaning: four words on 0–6, and 1 + comfort/6 (EP4, EP5).*
- **EQ9** — Must company be awake and active, or is a puppeted character enough? *Leaning: puppeted is enough; idleness is not tracked.*
- **EQ10** — Is `give` logged? The activity log's ten kinds have no gift (`world/activity_log.py:60`). *Leaning: a `gift` kind later, with the economy milestone — gifts are part of an economy's health, and roadmap decision (G) moved that measurement there.*
- **EQ11** — Do echoes run in empty rooms? *Leaning: the callback returns at once when no puppeted character is present; the rate is the builder's, minutes apart.*
- **EQ12** — Who sets the haven flag? *Leaning: staff only, until settlements & commons and law/crime/bounties say otherwise.*
- **EQ13** — Does comfort show in the webclient? *Leaning: as the word in the survival panel; the webclient decomposition's to place.*
- **EQ14** — Which design owns the tavern — this one, *markets & taverns*, or *lodging & safe logout*? *Leaning: this one owns comfort and havens; the tavern as a business is markets & taverns', beds for rent Rest's and lodging's (Rest NQ18).*

---

## 19. Considered and not proposed

- **Comfort as a bonus to skills or recovery rates.** EG3; it would be optimised into a queue (§2.1).
- **Counting furniture.** Rest §19, after Valheim; a place's quality is what it offers, not a tally.
- **A morale or sanity meter that falls.** A new need that nags is the report's *responsibility*; discomfort already has its gauges (Temperature, Rest).
- **Peace everywhere in a settlement.** Streets and fields stay part of the road (EP12).
- **An NPC innkeeper, cook or seller of beds.** Pillar 1 (EG6).
- **Notices of decay sent to an absent owner.** EP3.
- **A decoration ladder for status.** Opulence negates coziness (§2.1); furniture is Housing's, for use.
