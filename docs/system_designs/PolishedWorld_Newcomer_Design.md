# PolishedWorld — The Newcomer's Economy Design Notes (no school, the settlement as the school, first-steps hints, the first hour's ledger, first goods, knowledge and the guide)

> **Rev 2 · 2026-11-14** — one open question **answered** and one slice **decomposed**, docs only, with `docs/PolishedWorld_Arrival_Decomposition.md` Rev 1, roadmap Rev 78, README Rev 58 and the series handoff Rev 16. NCQ5: the Limbo start (Z1) was confirmed on Adam's dev instance the same evening — `START_LOCATION`, `DEFAULT_HOME` and `DEFAULT_RESPAWN_DBREF` printed `#2 #2 None`, and a fresh account's character finished creation in Limbo under Evennia's welcome text — and Adam decided it is fixed before the alpha's invitations. Z1 and Z2 are decomposed as the Arrival decomposition's AV-T1–AV-T3; the move happens in character creation's last node, not in `START_LOCATION` (AV1), and the same step makes the temple the character's `home`, because an unset `DEFAULT_RESPAWN_DBREF` sends the dead to Limbo too (AV3 — found while reading for the decomposition). The row Z1, NCP3 and NCQ5 gain dated notes; nothing else changes.
> **Rev 1 · 2026-11-14** — first version, docs only, with roadmap Rev 77, BACKLOG Rev 110, README Rev 56 and the series handoff `docs/system_designs/HANDOFF.md` Rev 14. Written from a design chat, the twenty-first note in the one-system series and the one the roadmap ordered after Stage 4.6 (Rev 61, decision log *Order after the webclient*), so that it could read drinking at the spring, natural healing and the fatigue levels as live code. It takes up Adam's question whether PolishedWorld should have a newbie school, as many MUDs have had. **Nothing here is locked.** Every numbered item is a proposal (NCP…), a goal (NCG…) or an open question (NCQ…); the stem is *NC*, for newcomer, free across `docs/`, `world/`, `commands/`, `typeclasses/` and `server/` when checked (no single letter is left; Projectiles took RW the same way); this document's departure rows are Z1–Z2 (Rendering's ZP… shares the letter, not the shape). Adam answered the proposal with a bare "kör", so the chat's four questions are NCQ1–NCQ4 with the chat's leanings, recorded as leanings. Two things were found while writing that the chat did not weigh, and they are recorded rather than decided: a new character's first room is not the temple but Evennia's own Limbo, with Evennia's stock welcome text, because `START_LOCATION` is not overridden (Z1, NCQ5) — read in source, not seen on a running instance; and a first-steps hint is the game speaking, so hints shipped during the alpha would change what the alpha's fifth close-out criterion measures (NCQ6). Prior art was read on 2026-11-14; code seams were read against `main` at `c4f8d0b` (Evennia 6.1.0).
> **Canonical:** `docs/system_designs/PolishedWorld_Newcomer_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one cross-cutting question and a small feature, before any decomposition).
**Home:** `docs/roadmap.md`, the parallel backlog, *The newcomer's economy* — a new entry (Rev 77), because nothing owned a character's first hour as a whole: roadmap decision (G) makes onboarding what the alpha measures; the Character Creation decomposition gives a new character no money and no gear (CC3); the faucet is Stage 4's; the free nodes are the alpha content's; and the only onboarding text is `help alpha`. `docs/BACKLOG.md` gains three annotations (Rev 110): on *First-steps hints*, on *An NPC guide driven by a language model — `rpg/llm`*, whose trigger this note was, and on *Faucet task-table tuning (`TEMPLE_TASKS`)*.
**When to read:** when the alpha's reports are read at close-out (the hints, NCP5–NCP11, NCQ6); before any change to character creation's last step or to `START_LOCATION` (Z1); when Names' first slice is decomposed (the `introduce` hint, Names UP23); when the economy milestone is defined (roadmap *[OPEN] No milestone measures the economy*; §10); when the LLM guide's BACKLOG entry is taken (§12); with *apprenticeship & skill teaching*, *temples & faith*, *markets & taverns* and *lodging & safe logout* from the design-series queue.

---

## 1. The idea in one paragraph

You wake in an old temple with nothing in your hands and nothing in your purse, and nobody takes you aside to explain the world. There is no school behind a door that locks after you, no practice sword, no purse of play money. There is a doorway with daylight in it, and outside it a clearing where the paths are plain to read: grass to the north, running water to the east, trees to the west. The first hour is the game itself at its smallest — pick fibre, twist it into twine, drink at the spring, find out that the gourd on the vine can carry water — and the game says one short thing, once, at the moment you first need it. What you have to spend is time and attention, not coin; what you can sell first is what your hands made and what you were willing to carry. The people you meet are the players who are already here, because you started where they are.

---

## 2. Prior art

Read 2026-11-14. Paraphrased throughout.

### 2.1 The Diku lineage — mud school, and what Aardwolf did with it

Sources: Raph Koster, *What is a Diku?* (`raphkoster.com`); Aardwolf's wiki, *Help/Academy* and *Newbie Mistakes* (`aardwolf.com`).

- Koster's account of the Diku family has the stock town of Midgaard gain a stock tutorial, the mud school, which walks a new character through a first fight. It shipped with the codebase, so hundreds of games had the same one.
- Aardwolf replaced its Mud School in 2008 with the Aylorian Academy: lessons from named trainers, most ending in a quiz, every lesson optional, a command to skip straight to the quiz, and rewards that are forfeited by skipping. The academy stands just above the game's recall point, inside the world rather than before it, and it leans on a newbie channel and volunteer helpers.

**Worth taking:** that the lesson is optional and can be left and returned to; that the school stands in the world, next to where everyone passes (NCP1).

**Not for PolishedWorld:** rewards for lessons — an item or coin handed out is a second faucet and a second source of goods (pillar 1; Character Creation CC3); a quiz, which tests reading rather than doing (NCG2).

### 2.2 Discworld and Achaea — the introduction as a place apart

Sources: MobyGames and two trope wikis on Discworld MUD's Pumpkin Town; Achaea's announcement of its third introduction (`achaea.com/news`), HELP 1.15 *New Adventurer Introduction* and HELP 2.2 *Newbies*.

- Discworld MUD starts every character in Pumpkin Town, a separate area with a limited inventory and play money, where a character cannot die and to which nobody returns after leaving.
- Achaea has rebuilt its introduction twice — Loom Island, then the Trial of Rebirth, now a two-part story — and its own help file says the introduction is linear and that the game after it is neither linear nor simple. It also keeps three areas that only characters under level 21 may enter.

**Worth taking:** the frankness of Achaea's help file — a tutorial that is unlike the game teaches the tutorial (NCG1).

**Not for PolishedWorld:** play money and practice goods; a zone veterans are ejected from; an introduction that must be rewritten each time the game changes — three versions at a commercial studio is the cost in plain numbers, and this project has five hours a week (NCG5).

### 2.3 Wurm Online — the starter place, and the problem of leaving it

Sources: Wurmpedia, *Golden Valley (server)* and *Server types*; the developers' *State of Wurm* post of March 2024 (read through a Steam news mirror).

- Golden Valley was first a tutorial server players could stay on for good; that was ended, and it became a one-way passage to the real servers. In 2020 the tutorial was split onto its own server.
- The 2024 post plans a starter island with gentler rules, open to everyone so that veterans can be part of its community, with a quest system giving small rewards for tasks that show the mechanics. The developers say themselves that quests may sit oddly in a sandbox, and name as unsolved how to move players on to the real servers without their feeling that they lose what they built. What was shipped after the post was not read.

**Worth taking:** letting veterans into the place where newcomers start — the reason is the community, not the lessons (NCG3).

**Not for PolishedWorld:** any place a newcomer's work must be left behind in. In a game where everything is made by hand, the first twine and the first waterskin are the newcomer's whole estate (NCP1).

### 2.4 A Tale in the Desert — the lesson: the Welcoming Island debate

Source: the archived developer chat on the Bastet shard, Tale 4 (`atitd.wiki`, *Amnesty/Tale 4/Bastet*), in which the developer Teppy weighs with players whether to open a separate Welcoming Island for new characters.

- For the island: the same citizenship tasks with everything closer together, nowhere to get lost, mentors who know where to look, newcomers' first clumsy buildings kept out of established players' land.
- Against it, from players: an island isolates newcomers from the community that keeps them, and real community starts only after leaving it. From Teppy: newcomers build there first and must then tear it all down, and a griefer on the island reaches only the new.
- Teppy's numbers: about one new player an hour — too few for a mentor to wait on an island for, enough to travel to one newcomer when they appear.
- Where it ended in that chat: no decision on the island, a leaning against it, and the tutorial for the next Tale delivered as popups during citizenship on the mainland.

This is the series' lesson for this note, as Achaea's forum threads were for earlier ones: a developer with real retention figures, arguing it out with players, moved the teaching from a place to a moment. PolishedWorld's realistic cohort is one to three humans (roadmap decision (G)); a school zone would hold one person, alone.

**Worth taking:** teaching at the moment of need, in the real world (NCP5); the citizenship idea that the first tasks are the real game's first tasks (NCP2).

**Not for PolishedWorld:** a citizenship level that gates the rest of the game — nothing here is locked behind having been taught.

### 2.5 Armageddon — no school at all

Sources: Armageddon's General Discussion Board, the threads *Newbie Perks* (2010) and *Do we need a n00b school?* (`gdb.armageddon.org`).

- The game has no school and no newbie channel; it has documents to read before playing and volunteer helpers reached outside the game.
- Its players argue both ways. Against a school: tutorials and channels would change the first impression of a serious world. For one: the command syntax is not a barrier worth keeping. One poster reports from the game's own survey that the players most likely to stay had been invited by a friend; another that the hard part of being new was not the code but things like telling players from NPCs.

**Worth taking:** that the first impression is part of the design, and a hint must not break it (NCP8); that the people already playing matter more than any lesson (NCG3).

**Not for PolishedWorld:** required reading before play; help that lives outside the game — the alpha measures what the game itself says (roadmap (G1)).

### 2.6 Ultima Online — the flag instead of the place

Sources: `uo.com`'s new-player FAQ and a Stratics new-player guide.

- Besides a starter town, UO marks new accounts *Young* for their first forty hours or until skills pass a threshold: a Young character is kept out of the most dangerous facet and the advanced shards, and can renounce the status with a spoken sentence.

**Not for PolishedWorld:** a status that changes the rules for one class of player. The temple as a haven (Comfort EP9) protects whoever stands in it, new or old; nothing else is softened (Comfort EG1).

---

## 3. Design goals

- **NCG1 — The first hour is the game.** Whatever a newcomer does in it, they do with the real verbs, on the real nodes, under the real gauges. Nothing is practised that is not kept.
- **NCG2 — Taught by doing, told once.** A verb is learned by using it for a purpose; the game speaks at the first moment of need and does not repeat itself.
- **NCG3 — A newcomer starts among the players there are.** No zone, level or flag separates the new from the old (§2.3, §2.4).
- **NCG4 — Nothing is handed out.** No starting coin, no starting gear, no reward for a lesson (pillar 1; Character Creation CC3).
- **NCG5 — Nothing here rots.** No script walks a newcomer through steps that a later system change would break; a hint hangs on an event the system itself raises, and dies with it (§2.2).
- **NCG6 — A newcomer's time is worth something to someone.** The first goods have a buyer for reasons the rules already give, not for charity (§10).

---

## 4. Legend alignment

**Rules as written:**

- **Equipment** — p. 35: every Adventurer is assumed to begin with the clothes they wear and a spare set, some personal mementoes, a week's worth of food and one weapon suited to their skills and culture.
- **Starting money** — by cultural background; struck by the Character Creation decomposition (CC3), which cites it.
- **Survival** — p. 63: Survival tests are not used when the Adventurer is in a city or town.
- **Teachers and Mentors** — p. 72: anyone may teach who has at least 20% more in the skill than the student.
- **Odd Jobs** — pp. 84–85: paid part-time work, generally non-hazardous and poorly paid, with a table of jobs and daily pay.

**Translation proposals:**

- **NCP-L1 — The week's food is the full gauges.** A new character starts with hunger and thirst at 100 (`typeclasses/characters.py:288–320`); at the shipped rates that is about sixteen real hours of play before the hunger gauge is empty and eight before thirst's is (§9). The rulebook's week of food is that grace, held in the body rather than the pack. No food item is granted (NCG4).
- **NCP-L2 — The mementoes are the description.** What Legend gives as personal effects, Names gives as how a character looks (Names UP1). No object.
- **NCP-L3 — The clothes and the weapon stay struck.** CC3 stands: a stone knife and a club are rung-0 and rung-20 work from free nodes. What a newcomer wears, and whether nakedness matters before Temperature's clothing ships, is NCQ7.
- **NCP-L4 — Odd jobs are the temple's chores.** p. 84's description — non-hazardous, poorly paid — is the faucet's (`commands/work_commands.py:173`). The other odd jobs become players' trades (Comfort EP-L3).
- **NCP-L5 — Legend's 20% is not used for lessons.** `teach` passes on a recipe, not skill points, and has no skill floor for the teacher beyond knowing it; *apprenticeship & skill teaching* owns p. 72.

---

## 5. The loop — a first hour

1. **Arrive.** Character creation ends; the newcomer stands in the temple (Z1).
2. **Read the room.** The temple's description and the clearing's name the ways out and what grows there (§7).
3. **Gather.** `forage` at the free nodes — eight of the nine seeded nodes need no tool.
4. **Make.** `recipes`, then `craft twine`: three fibres, no tool, no knowledge gate. The alpha's fifth criterion is this moment (roadmap (G2)).
5. **Drink.** `drink` at the spring, with nothing in hand (Stage 4.6).
6. **Carry and meet.** A gourd and the twine make a waterskin; another player is a description until introduced (Names).
7. **Come back.** The temple is where the scrolls, the chores and — when Stage 5 decides it — safety are (Comfort EP9).

---

## 6. Departures from shipped behaviour

Each row is a change to behaviour that `main` has today; each is a proposal.

| # | Shipped today | Proposed | Where shipped |
|---|---|---|---|
| Z1 | A new character is created in Limbo — `START_LOCATION` is not set in `server/conf/settings.py`, so Evennia's default `"#2"` holds — stands there as a statue until first login, runs character creation there, and then stands in Evennia's own room with Evennia's stock welcome text, one one-way exit `temple` away from the world | Character creation's last step places the character in the Old Temple; Limbo stays admin space (NCP3, NCQ5). *(Rev 2: confirmed live; decomposed as Arrival AV-T1–AV-T2.)* | `evennia/settings_default.py:623`, `:625`; `evennia/server/initial_setup.py:29`, `:115` (6.1.0); `world/seed_data.py:160–161`; `docs/PolishedWorld_Alpha_Runbook.md:46` |
| Z2 | The chore `water` sends the worker to *the well*, which no room has; the world's one source is the spring at the Brook | The chore's two opening lines name the spring (NCP4) | `commands/work_commands.py:189–190`; `world/seed_data.py:202–203` |

Unchanged: character creation's steps and what it grants (CC3); the faucet's rewards and cooldowns (BACKLOG *Faucet task-table tuning*); the gauges, the awake clock and healing; the scroll seed (NCQ3); `help alpha`.

---

## 7. No school: the settlement is the school

**NCP1 — No school zone.** PolishedWorld has no newbie school, tutorial area, starter island or practice ground, and no status that marks a character as new. The six seeded rooms are where a newcomer learns, because they are where the first materials are (`world/seed_data.py:79–157`, `:193–212`). The reasons, in the order the prior art gave them: a zone apart keeps the newcomer from the few players there are (§2.4); whatever is made there must be left or carried out (§2.3); a scripted path is rewritten with every system change (§2.2); and handouts are a second faucet (§2.1).

**NCP2 — The first tasks are the real first tasks.** The stone axe's three inputs sit in three rooms and the tree it fells two steps from the temple (`world/seed_data.py:189–192`, the alpha content's AD8). That layout is already a curriculum: a newcomer who makes the axe has walked the whole settlement and used `forage`, `craft` and `recipes`. Nothing is added to it; the next building pass keeps the property that rung 0 is complete within sight of the first haven.

**NCP3 — The first room is the temple (Z1).** The newcomer's first screen after character creation is the Old Temple's description, not Evennia's welcome to developers. Where the move happens — a `START_LOCATION` resolved from the seed tag at startup, or character creation's own last step — is the decomposition's; the temple is found by its seed id, never by a dbref in settings (the seeder's rule, `world/seed_data.py`). *(Rev 2: character creation's last node, Arrival AV1; `home` is set with it, AV3.)*

**NCP4 — The room says where things are; the hint says what a verb does.** Place knowledge belongs in descriptions: the clearing already names grass to the north, water to the east and trees to the west, the berry bush and the fallen branches (`world/seed_data.py:96–101`). The temple's description names the doorway and nothing a newcomer can do there (`:83–88`); Comfort EP19 already asks for it to be rewritten warm, and that rewrite also shows the scroll rack, the broom and the basin — the things `learn` and `work` act on. The chore `water` names the spring (Z2). No hint ever gives directions.

---

## 8. First-steps hints

**NCP5 — A hint is one line, fired by a first occurrence.** The mechanism BACKLOG *First-steps hints* describes: each hint has a key and an event; the first time the event happens to a character who has not seen that hint, one line is shown and the key is stored on the character. Nothing repeats. Nothing ticks — a hint is raised from the seam where its event already happens.

**NCP6 — Hints point at verbs and at `help`.** *Thirst is told in words on `status`; `drink` at running water needs nothing in your hands.* A hint names a command and what it is for; it never states a number, a recipe or a location (NCP4), so a change to a system changes at most one line (NCG5).

**NCP7 — A player can read them again and turn them off.** `hints` lists the hints already seen; `hints off` and `hints on` are a per-character switch. A veteran's second character turns them off in one command.

**NCP8 — A hint is marked as the game speaking.** One style, used for nothing else, so it is never mistaken for the world's own text and the world's text is never mistaken for a tip (§2.5; the Tone Guide's review checklist applies to the wording).

**NCP9 — One at a time.** A hint is not shown while a timed action's own lines are running or inside the character-creation menu, and two hints never arrive in the same breath; how the second waits is NCQ8.

**NCP10 — Candidates, not a list.** Which hints exist is the alpha's answer (BACKLOG *First-steps hints*, BLOCKED on alpha reports). The candidates this note can name, each with the seam that would raise it:

| Event | Points at | Seam today |
|---|---|---|
| first arrival in the temple | `look`, exits, `help` | Z1's placement |
| first worse thirst word | `drink` | the tick's warning, `world/survival_ticker.py:25–27` |
| first worse hunger word | `forage` | the same |
| first successful `forage` | `recipes`, `craft` | `commands/foraging_commands.py:73` |
| first failed craft | `recipes` | `commands/crafting_commands.py` |
| first time in the Treasury's room | `work` | `commands/work_commands.py:505` |
| first other player in the room | `introduce`, `recog` | Names UP23, with Names' slice |
| first nightfall outdoors | shelter | the day-period change |
| first failed awake test | `rest` | `world/fatigue.py:133` |

**NCP11 — Hints are logged as shown.** Onboarding is what the alpha measures (roadmap (G1)); a line per hint shown, with the hint's key, lets a close-out read where newcomers were when the game spoke. Whether that is an eleventh activity-log kind or a field is the decomposition's (`world/activity_log.py:60`; Comfort EQ10 asks the same of gifts).

---

## 9. What a newcomer has — the first hour's ledger

**NCP12 — Four things, and coin is the least of them.** Read from `main`:

| | What a newcomer holds | Where |
|---|---|---|
| **Body** | hunger and thirst at 100; thirst falls 2 and hunger 1 each 600 s tick while online, so a first real hour costs 12 and 6; thirst reaches zero after 8 h 20 min of play and hunger after 16 h 40 min; time offline costs nothing | `typeclasses/characters.py:288–320`; `world/survival_ticker.py:23`; `server/conf/at_server_startstop.py:27` |
| **Wakefulness** | no awake test before (10 + CON) game hours — five real hours at CON 10 | `world/fatigue.py:123` |
| **Knowledge** | twelve recipes need no teaching, six of them at floor 0 (twine, waterskin, stone knife, bone needle, stone axe, sling bullet); seventeen are gated behind a scroll, a profession or a teacher | `world/recipes.py` |
| **Coin** | none; then up to 170 copper for the five chores, about two minutes' work, each on a cooldown of one or two real hours; paid out of a Treasury that was minted once | `commands/work_commands.py:173–225`, `:19` |

**NCP13 — The first hour has no clock on it, and that is right.** Nothing in the table can kill a newcomer in a first session. The road is hard (Comfort EG1), but the first hour is spent within sight of the first haven, and Legend draws the same line (p. 63). The hardness arrives as the gauges' words, in the second and third hour — which is when the hints about them fire (NCP10).

**NCP14 — Coin teaches that coin exists; nothing else.** No one sells anything to a newcomer but another player (pillar 1), and the realistic cohort is one to three (roadmap (G)). The faucet stays what its BACKLOG entry calls it, a supplement, and this note proposes no change to it. What a newcomer's 170 copper can buy on day one is a player's time: a lesson is free by code (`commands/crafting_commands.py:1167`), so a teacher may charge for it with `pay`.

---

## 10. First goods, and to whom

**NCP15 — What a character with nothing can make on day one.** From the eight free nodes, with no tool and no teacher: twine (three fibres); a waterskin (a gourd and twine); a stone knife (stone, stick, fibre); a stone axe (flint, stick, twine); sling bullets (clay); and, at floor 20, milling stones (two stones). With the axe, wood — and from wood a club and a quarterstaff. A bone needle and a spear wait on a first rabbit, and the sling on leather, which is gated (`world/recipes.py`).

**NCP16 — The veteran is the newcomer's first customer, by a rule that already ships.** A recipe is routine for a crafter whose Craft is more than `SKILL_TRIVIAL_BAND` above its floor, and routine work is not rolled for improvement (Trivial Work TD2; `server/conf/settings.py:190`, band 30). An hour of twine teaches a newcomer and teaches a veteran nothing, while the veteran still needs twine for everything above it. The gate was built against grinding; it also prices the newcomer's hour. No protected price, no reserved recipe and no rule against a veteran making twine is proposed — only that the gate's band is not tuned without reading this effect.

**NCP17 — Carrying is the other first trade.** Every unit of a good is its own object and weight makes distance cost (the alpha content's AD8). A newcomer with empty hands and full gauges can fetch — fibre, clay, deadfall — for someone whose time is better spent at the craft. Evennia's `give`, the project's `pay` (`commands/currency_commands.py:173`) and the barter trade (`world/barter.py`) are the whole machinery.

**NCP18 — The temple buys nothing.** An NPC that buys twine is an NPC vendor run backwards: it sets a price and mints demand (pillar 1). The faucet pays for chores, which make no goods.

**NCP19 — None of this can be measured in the alpha.** Prices from one to three players are habits, not a market (roadmap (G)). §10 is written for the session that defines the economy milestone (roadmap *[OPEN] No milestone measures the economy*), which should ask of its data: did any newcomer sell anything in their first three sessions, and to whom?

---

## 11. Knowledge: the scrolls and the teacher

**NCP20 — A newcomer learns recipes from people.** `teach` costs the teacher a 120-second cooldown and nothing else (`commands/crafting_commands.py:133`, `:147`, `:1177`). It is the cheapest thing an established player can give and the first reason for a newcomer to speak to one; Names makes it a reason to exchange names (Names UP15).

**NCP21 — The seeded scrolls are the first settlers', not every newcomer's.** Fifteen scrolls lie in the temple; each is consumed by `learn`, and the seeder never places one twice (`world/seed_data.py:67–71`, `:221–252`). The first players to arrive can take them all, and a later newcomer finds the rack bare. That is consistent with knowledge as something players hold and pass on — and it is a wall when the one knower of a recipe is offline or gone. Staff can replace a scroll, one recipe at a time (`reseed_scroll`, the same docstring). Whether anything more is wanted is NCQ3.

---

## 12. The guide

**NCP22 — No guide that states rules from a language model.** The BACKLOG entry's own second constraint is the reason: a guide that invents a recipe breaks the alpha's first-craft criterion, and a right one blurs it. Hints say what the game says, from text a human wrote (NCP6).

**NCP23 — The sweeper stays a figure at ease.** The relaxed guardian (Comfort EP22; `typeclasses/npcs.py:68`) sells nothing and decides nothing. If alpha reports show questions the hints cannot answer, the cheaper first guide is the entry's `talking_npc` with fixed answers — a later decision, with those reports (NCQ4).

**NCP24 — People are the guide.** The Public channel and `page` already reach staff and the cohort (`help alpha`). With one to three players, the most useful thing the game can do for a newcomer is put them in the same six rooms as the others (NCG3).

---

## 13. Economy

**Sources:** none. This note adds no item and no coin.

**Sinks:** none of its own. A newcomer's first purchases are other players' goods and lessons.

**NCP25 — No newcomer subsidy.** No starting kit, no first-day bonus, no reduced price, no protected node. The free nodes are the floor for everyone (Foraging RG3, Forest YG4), and the gauges' grace is the only allowance (NCP-L1).

**Services:** teaching for coin (NCP14); gathering and carrying (NCP17); rung-0 goods made for those above the band (NCP16).

**Coin:** the faucet only, unchanged. **Logging:** hints shown (NCP11); everything else a newcomer does is already an activity-log kind (`world/activity_log.py:60`).

---

## 14. Multiplayer and server load

- **Nothing ticks.** A hint is raised from an event that already happens; the check is one membership test against a small set stored on the character.
- **No shared state.** Hints seen are per character; two newcomers in one room each get their own lines, and neither sees the other's.
- **The first room.** Z1 moves each new character once. Several characters created at the same moment all arrive in the temple; nothing there is claimed by arriving.
- **The scrolls are the one contested thing** a newcomer meets in the first minute: `learn` deletes the scroll, so two characters reaching for the same one resolve in command order, as any `get` does (NCP21).
- **The faucet's cooldowns are per character** (`commands/work_commands.py:268–270`), so newcomers do not queue for chores; they draw on one Treasury.

---

## 15. Immersion extras

- **The newcomer is seen arriving.** A line to the temple when someone steps out of character creation — a stranger blinking in the doorway — resolved per reader once Names ships (Names UP10).
- **The temple shows its use.** A swept floor, a filled basin, lit candles for a while after the chores are done — text read from the chores' own cooldowns, so a newcomer sees that someone was here (Light LQ13 asks for the candles as real objects).
- **The first craft is said plainly.** No fanfare line; the twine in the hand is the reward (Comfort §2.1: an extrinsic reward turns a pleasure into a transaction).

---

## 16. Layers — a suggested order

1. **Now — this document.** Docs only.
2. **Any small session — the first room and the well** (Z1, Z2). Small, no new content; a tagged deploy carries it to the alpha instance, whose close-out asks for one such deploy anyway (roadmap (G2)). Whether to do it before invitations go out is NCQ5.
3. **With the next building pass — the temple's description** (NCP4, Comfort EP19).
4. **After the alpha's reports — the hint mechanism and the first hints** (NCP5–NCP11), chosen from where testers stalled.
5. **With Names' first slice — the introduction hint** (Names UP23) and the arrival line.
6. **With the economy milestone — the first-goods questions** (NCP19).

**Prerequisites:** none for 1–3; alpha reports for 4; Names for 5. **Not prerequisites:** Stage 5, the webclient, Housing.

---

## 17. Seams in today's code (read at `c4f8d0b`)

| Need | Seam | Where |
|---|---|---|
| First room | `START_LOCATION`, `DEFAULT_HOME` defaults; Limbo's description; the one-way exit | `evennia/settings_default.py:623`, `:625`; `evennia/server/initial_setup.py:29`, `:115` (6.1.0); `world/seed_data.py:160–161` |
| Character creation | the menu; what it applies; its help entry | `world/chargen_menu.py`; `world/chargen.py:194`, `:289`, `:391` |
| The settlement | rooms, exits, nodes, scrolls | `world/seed_data.py:79`, `:159`, `:193`, `:221` |
| Gauges | hunger and thirst at 100; base rates; warned gauges; the tick | `typeclasses/characters.py:288–320`; `world/survival_ticker.py:23`, `:25–27`; `server/conf/at_server_startstop.py:27` |
| Drinking | a draught and the source's three | `world/water.py:16–21`; `commands/consumption_commands.py:96` |
| Awake clock | the waking day; the failed-test line | `world/fatigue.py:123`, `:133` |
| Healing | Legend's rows | `world/healing.py:30–37` |
| Faucet | the chores; the Treasury; cooldown keys; the command | `commands/work_commands.py:173–225`, `:19`, `:268–270`, `:505` |
| Recipes | gated and ungated; `recipes` | `world/recipes.py`; `commands/crafting_commands.py:468` |
| Teaching | timeout, cooldown, `teach`, `learn` | `commands/crafting_commands.py:133`, `:147`, `:1177`, `:1295` |
| Routine work | the band | `server/conf/settings.py:190`; `world/knowledge.py:55`, `:77` |
| Foraging | `forage` | `commands/foraging_commands.py:73` |
| Status | `status` | `commands/character_commands.py:40` |
| The guardian | `Sweeper` | `typeclasses/npcs.py:68` |
| Onboarding text | `help alpha`; the connection line | `world/alpha_contract.py:36–70`, `:34` |
| Activity log | `KINDS` | `world/activity_log.py:60` |

No hint mechanism exists in `commands/`, `world/` or `typeclasses/`. Re-read every row against live source before a decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **NCQ1** — The file's name. *Leaning (chat, 2026-11-14; a bare "kör"): `Newcomer`, as used here.*
- **NCQ2** — The prefix. *Leaning (chat): NC — NCP/NCQ/NCG, 0 hits when checked; departure rows Z.*
- **NCQ3** — The seeded scrolls run out (NCP21). *Leaning (chat): leave the seed as it is — knowledge moves through `teach` — and let staff reseed a recipe during the alpha when its only knower is gone. Found while writing: with one to three players, "ask someone" is often "wait until tomorrow"; the alpha's reports will say whether that is a wall.*
- **NCQ4** — The guide. *Leaning (chat): no language-model guide for rules (NCP22); whether a flavour NPC is wanted stays the BACKLOG entry's open question; `talking_npc` only if reports ask for it.*
- **NCQ5** — Found while writing: the first room is Limbo (Z1). Fix before the alpha's invitations, or let the alpha show it? *Leaning: before — it is small, it is not what the alpha is meant to find, and a first screen that greets a developer is a poor first measure of onboarding. Not seen on a running instance; confirm with a fresh test account first.* **Answered (2026-11-14, Rev 2):** confirmed on the dev instance, and fixed before the invitations — `docs/PolishedWorld_Arrival_Decomposition.md`.
- **NCQ6** — Found while writing: the alpha's fifth criterion is a first craft *with no staff help beyond what `help` says* (roadmap (G2)). Is a hint "what the game itself says" (G1), or help beyond `help`? *Leaning: a hint is the game speaking, but hints wait for the alpha's reports anyway (NCP10), so the alpha runs without them and is the baseline they are judged against.*
- **NCQ7** — What a newcomer wears (NCP-L3). Legend gives clothes; CC3 gives none; the seventeen gated recipes hold every garment. *Leaning: nothing granted; Temperature's clothing slice decides whether a first garment must be reachable without a teacher.*
- **NCQ8** — How a second hint waits when two events fall together (NCP9). *Leaning: it is skipped unshown and fires on the event's next occurrence — no queue to keep.*
- **NCQ9** — Does a second character on an account start with hints off? *Leaning: no — per character, one command to silence; accounts hold one character in the alpha.*
- **NCQ10** — Should `help` gain an entry on first steps, beside the hints? *Leaning: `hints` lists what was shown (NCP7); a static entry repeats it and goes stale. The alpha's reports decide.*
- **NCQ11** — Does the temple's work need the newcomer to be told the Treasury can run dry? *Leaning: `work` already says when it cannot pay; no hint.*

---

## 19. Considered and not proposed

- **A newbie school as a zone.** §2.2–§2.4, NCP1.
- **A starter kit, or a first coin.** CC3; a second faucet (NCG4).
- **A reward for a first craft or a finished lesson.** Aardwolf's forfeited rewards show what it teaches: finishing the school (§2.1). Comfort §2.1 on extrinsic rewards.
- **A *Young* flag or any newcomer protection.** §2.6; the haven protects places, not classes of player.
- **Newbie-only nodes or areas.** Achaea's Minia (§2.2); NCG3.
- **A newbie channel.** *channels, tells & the out-of-character line* is the queue's; Public serves a cohort of three.
- **The temple buying first goods.** NCP18.
- **A quest log of first tasks.** Wurm's own doubt about quests in a sandbox (§2.3); the stone axe is the quest, unwritten (NCP2).
- **A rules guide driven by a language model.** NCP22.
- **Hints that give directions or numbers.** NCP4, NCP6.
