# PolishedWorld — Homunculi Design Notes (the made servant: the egg and the jar, the maker's bond, orders and their limits, the attended rule, loss and the shock, the flask in trade)

> **Rev 1 · 2026-11-09** — first version, docs only, with roadmap Rev 66, BACKLOG Rev 93, README Rev 42 and the series handoff `docs/system_designs/HANDOFF.md` Rev 5. Written from a design chat, the seventeenth note in the one-system series and, like Comfort, written off the queue at Adam's request: he brought the idea from the viral egg experiments (an egg injected with human material in the hope of growing a homunculus) and asked whether players could make such a creature, command it to do simple tasks — a sanctioned, limited kind of player-made bot — and trade or sell it. In the chat Claude recommended the idea as a design note now and a build much later, a hard rule that a homunculus produces nothing that enters the economy, the creature as an item in a flask while it rests, a bond paid in the maker's own life-force, and a recipe of egg, blood and mandrake rather than the videos' version, for the tone. Adam agreed with the reasoning and the note on tone, and added that homunculi should be able to do somewhat simpler chores and some gathering too — not to be locked now. That softens the chat's "produces nothing" into JG4 and JP10, and the question stays open as JQ2 with Adam's leaning recorded. Nothing here changes live behaviour, so there is no departures table. **Nothing here is locked.** Every numbered item is a proposal (JP…), a goal (JG…) or an open question (JQ…); the letter is *J*, free across `docs/`, `world/`, `commands/`, `typeclasses/`, `server/` and `tests/` when checked — *H*, the natural letter, is avoided because HP is Legend's hit points, and Temperature's departure rows J1–J7 share the letter, not the shape. Two things were found while writing that the chat did not weigh, and they are recorded rather than decided: the roadmap's Stage 7 says the trait foundation holds POW and Magic Points, and only POW exists in code (JQ14); and the shipped gathering verb, the cooldowns and the timed-action slot are all written for a character that types commands, which a homunculus is not (JQ15). Prior art was read on 2026-11-09; code seams were read against `main` at `1f4ce0c` (Evennia 6.1.0).
> **Canonical:** `docs/system_designs/PolishedWorld_Homunculus_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/roadmap.md`, parallel backlog, *Homunculi — the made servant* — a new entry (Rev 66), because nothing owned a creature a player makes and commands: the only non-player actors in code are the sweeper on his beat (`typeclasses/npcs.py:68`) and the hunted animals (`typeclasses/creatures.py:34`); BACKLOG *Automated test players* is about software driving accounts, not creatures in the world; Stage 7 holds magic and the queue's *alchemy & poisons\** the laboratory. The roadmap's Stage 7 gains a dated note that only POW exists in code (JQ14). `docs/BACKLOG.md` gains one note (Rev 93): *Automated test players* — a homunculus is not an automated player; its lines are kept, and the runbook's offline filter drops them only when its maker is a listed bot (JP21).
**When to read:** when *alchemy & poisons\** from the design-series queue is designed (the alchemist's homunculus, JP4; the discipline, JQ13); when livestock's eggs or *fowling & wild birds\** are decomposed (the egg, JQ12); when Foraging's herb nodes are decomposed (the mandrake, JP1); when Storage's jar and seal ship (JP1, JP7); when Stage 5's design session decides what may be attacked and what a haven guards (JP15, JQ8, JQ9); when Stage 7 reads POW (JP-L1, JQ14); when the economy milestone first reads gathering in the activity log (JP21, JP22); when BACKLOG *Strangers by description — `rpg/rpsystem`* is decided (JQ17).

---

## 1. The idea in one paragraph

A hen's egg, a sliver of mandrake root and a drop of the maker's own blood go into a small clay jar, sealed with tallow, and the jar is set by a fire to keep warm. For forty game days nothing seems to happen; in the last days there is a faint tapping inside. Then the seal cracks and something the size of a hand climbs out — wrinkled, root-coloured, blinking — and from then on it is bound to the one whose blood is in it. It follows its maker, carries a little, keeps the fire fed through the night, fills a waterskin at the spring, and picks what grows where it is set to pick, slowly, never better than its maker would. It works only while its maker is in the world: when they log off it curls up and sleeps. It eats a little, it ages, and one day it is gone — dissolved into a curl of eggshell and a pinch of root dust — and its maker feels the loss, a dull ache for a day, before the part of themselves they put into it slowly returns. It never touches coin, never works the temple's coffer, and never makes more than the world grows. It can be given away in its jar, but it serves no one who has not bound it with their own blood.

---

## 2. Prior art

### 2.1 Ultima Online's shards — the lesson

Sources: the rules of *UO Outlands* (`uooutlands.com`, Code of Conduct & Shard Rules), the about page of *UO Lost Lands* (`uolostlands.com`), and a rules thread on `uoforum.com` (read 2026-11-09). Paraphrased:

- Ultima Online's skills rise by repetition, so players have long let macros play for them. The shards still running draw one line through it: unattended macroing to raise a skill is allowed; unattended gathering of resources — logs, ore, fish — is forbidden, enforced by staff checks and, on some shards, a challenge the gatherer must answer.
- The reason given on the forum is that unattended gathering hurts everyone if it goes unchecked: the goods it makes reach the same market every attended player sells into.

**Worth taking:** the line itself — practice is the player's own business, but anything that adds goods to a shared market has to have a person behind it; and that the line can be drawn by rule of the game rather than by policing.

**Not for PolishedWorld:** policing by staff checks and challenges — a solo developer cannot watch, so the rule has to be the creature's own nature (JG1).

**The lesson (the series' "Achaea lesson"):** the servant that works while its master is away is the bot every sandbox ends up forbidding, because its goods land in everyone's market; so the servant must stop when its master stops. The rules taken: **a homunculus acts only while its maker is in the world** (JG1), and **it never touches coin** (JG2).

### 2.2 Achaea — the homunculus as a rule

Sources: AchaeaWiki, *Homunculus* (`wiki.achaea.com`), and Achaea's own class page for the Alchemist (`achaea.com`) (read 2026-11-09). Paraphrased:

- Achaea's alchemists grow a homunculus in an equipped laboratory from a sample of their own flesh; it is bound to its maker in body and spirit, and serves as their eyes and ears.
- Its powers come one at a time with the alchemist's training: seeing and hearing through it, moving it at a distance, speaking through it, hands that can pick things up, and in combat a body that blocks an enemy's escape.

**Worth taking:** the maker's own body as the material and the bond; powers that come one at a time, as orders do here (§16).

**Not for PolishedWorld:** the homunculus as a combat piece (Stage 5's to decide); a laboratory before the first one (Pottery PG2 — the first of everything needs no station, JP1).

Achaea has a rule here but no story — nothing in what was read says what the homunculus did to the game — so the lesson slot goes to Ultima Online (§2.1).

### 2.3 RuneScape — Summoning's familiars

Source: the RuneScape Wiki, *Beast of Burden* and *Summoning familiars* (`runescape.wiki`) (read 2026-11-09). Paraphrased:

- A familiar is summoned from a pouch the player makes and consumes; only one can be out at a time, and each lasts a fixed span before it leaves, renewed only by spending another pouch.
- A beast of burden carries a few slots of items; the player must take them back into their own pack to use them; it can be attacked, and refuses to carry anything too valuable to trust to it.

**Worth taking:** one at a time; a span that runs out, so every familiar is consumed; carrying as the first and plainest service.

**Not for PolishedWorld:** a familiar summoned from a pouch in a moment (the homunculus is grown, JP2); points that drain while it is out (it eats instead, JP8).

### 2.4 Paracelsus and Goethe — the jar

From the alchemical tradition, paraphrased: the recipe ascribed to Paracelsus has the creature grown in a sealed vessel kept warm in horse dung for forty days and then fed for weeks; in Goethe's *Faust* the homunculus lives in a glass phial and cannot leave it. Both are where the jar, the warmth and the forty days come from (JP1, JP2, JP7). The seed in Paracelsus' recipe, as in the viral videos, is not taken (§19).

---

## 3. Design goals

- **JG1 — It acts only while its maker is in the world.** Every order lapses when the maker is unpuppeted, and nothing is done for them while they are a statue (§2.1). The servant that works while its master is away is the bot this design exists not to build.
- **JG2 — It never touches coin.** No `work` at the temple, no pay, no trade as a party, no sale on its own account. Coin in PolishedWorld is GameGold's 1:1 shadow; a creature that earned it would be a mint with legs.
- **JG3 — One maker, one bond, paid in the maker's own life-force.** Blood Magic's advice to the Games Master who lets players enchant: let them power their creations only with their own life-force (p. 67). The price is what keeps them few.
- **JG4 — It does what its maker's hands do, slower and smaller, never more.** No verb of its own makes value; it uses the shipped verbs' cores on the same nodes, at its maker's skill less twenty, carrying what a hand-sized body carries. It can move who picks a thing up; it cannot raise what the world yields.
- **JG5 — It can be lost, and losing it costs.** It ages, starves and can die; it leaves no corpse to butcher; its maker feels it (JP16).
- **JG6 — Nothing ticks for it.** Its life, hunger and incubation are stamps read on demand; its orders are timed actions that re-arm only while JG1 holds. No timer per homunculus.
- **JG7 — It is a small warm thing in the world, read in words.** It shows in the room, sits by the fire, curls up asleep; its state is a phrase, never a bar (Comfort EG1; Temperature KG1).

---

## 4. Legend alignment

**Rules as written:**

- **Blood Magic, enchanting with one's own life** — p. 67: where magic needs sacrifice, the Games Master who lets players make items is advised to limit them to their own life-force. p. 68: a permanent enchantment's life-force must come from the sorcerer himself; breaking it gives its creator a psychic shock; points lost to it come back at one a week once it is broken; and if the creator is slain, the enchantment goes on working. p. 69: optional limits on making enchantments — one point of a Characteristic per item, or a number of Improvement Rolls. p. 70: the Psychic Shock table, rolled for an effect (from blind to *Incapable*, all skills −20 %) and for a length (from a few combat actions to permanent); and Prince Koura's homunculus, a clay body given a drop of his blood and a year of his life, which flew off at his mental command while he watched through its eyes — when it was killed he was struck down by the shock for minutes.
- **Blood Magic, summoned entities** — p. 76: an entity has all seven Characteristics, bought with Magic Points — one point buys 1D6 — so the least entity costs seven, and the tiny, vaguely humanoid ones are called homunculi.
- **Monsters of Legend II, the alchemical duplicate** — pp. 9–10: an artificial being made from vats of alchemical compounds and blood; tough, but stolid and dull, unable to deviate from its programmed instructions; it has its original's learned skills at about −20 %, none of its special abilities; killed, it dissolves into a pool of slime.
- **Monsters of Legend II, the root guardian** — p. 123: a made guardian is given one of two kinds of orders, to guard a place or to patrol an area seeking enemies its maker named.
- **Arms of Legend** (`docs/reference/arms_of_legend.md`): Lore (Alchemy), INT ×2, the skill of every alchemical experiment (`:3518`); the laboratory — a workbench, storage, a heat source (`:3663`), the athanor, a clay furnace (`:3667`), vessels of glass, clay and earthenware (`:3673`); the warning that alchemy which works makes long life commonplace and devalues gold (`:3753`); the familiar's pack (`:238`); animal training (`:2811`).

**Translation proposals:**

- **JP-L1 — The bond is a reserved point of POW, not a lost one.** While a homunculus lives its maker's POW is one lower — a `mod` on the static POW trait (`typeclasses/characters.py:264`); when the bond ends the point comes back after a game week (p. 68's one a week). Improvement Rolls (p. 69) are not used: PolishedWorld improves skills by use, with no session rolls to spend (roadmap Stage 4.5). POW rather than Magic Points because only POW exists (JQ14); whether POW has a live reader that makes the price bite before Stage 7 is JQ14's too.
- **JP-L2 — The shock is one row, not a roll.** Blood Magic's table runs from seconds to permanent and decades; a permanent maim drawn by lot is not a price anyone can weigh. Proposed: *Incapable* — every skill test −20 % — for one game day (six real hours), after a death that was not a gentle end (JP16).
- **JP-L3 — Seven small Characteristics.** As p. 76's least entity: each 1D6, SIZ fixed at the low end; carrying is STR + SIZ as for anyone (`world/encumbrance.py:284`), so a homunculus carries a handful of ENC, not a pack's worth.
- **JP-L4 — Its skills are its maker's, less twenty, and never rise.** The duplicate's rule (MoL II pp. 9–10): where an order meets a roll, it rolls its maker's skill −20. It does not improve: improvement on use is the character's own (`typeclasses/characters.py:938–959`).
- **JP-L5 — Orders, not thought.** The duplicate cannot deviate from its instructions; the root guardian holds one kind of order (p. 123). A homunculus holds one standing order at a time (JP9).
- **JP-L6 — Lore (Alchemy) waits for alchemy.** It is an advanced skill and not among the five shipped (`world/chargen.py:59–65`). The folk homunculus is a crafted thing (JP1); the alchemist's homunculus waits on the queue's *alchemy & poisons\** (JP4).
- **JP-L7 — No transmutation, and Legend's prices are not used.** AoL's own warning about gold (`:3753`) is a GameGold rule here: nothing alchemical makes coin or metal from nothing. Pillar 1 for prices.

---

## 5. The loop

Proposed phases; each is something someone can sell or give.

1. **Gather the makings.** An egg (livestock's, or a wild one, JQ12); a mandrake root from an herb node (Foraging RP1); a clay jar and a cake of tallow to seal it (Storage DP6, DP7); a drop of the maker's own blood, given at the moment of making.
2. **Keep it warm.** The sealed jar by a lit fire or in a warm dung heap for forty game days (JP2).
3. **The hatching.** The seal cracks; the maker, present, takes the bond (JP3).
4. **Give orders.** Follow, stay, hold, tend the fire, fill a vessel, gather where it stands (§8).
5. **Keep it.** Feed it; read its state in words (JP8).
6. **The end.** It is released, grows old, starves or is killed; its maker's POW comes back (§10).
7. **Pass it on.** The jar with the homunculus asleep inside is given or traded; the new holder binds it with their own blood (§11).

---

## 6. Making a homunculus

**JP1 — The folk recipe needs no station.** Pottery PG2's rule: the first of everything needs no station. One crafted item — a sealed jar holding an egg, a mandrake root and the maker's blood — made by `craft` from an egg, a mandrake root, a storage jar (Storage DP6) and a cake of tallow (Storage DP7), gated by knowledge like other rare recipes (`requires_knowledge`; every gated recipe needs a source, `tests/test_recipe_sources.py`; JQ13). The blood is not an item: making it costs the maker a small, fixed bite of fatigue (Rest's levels, when they ship) and stamps the maker's dbref on the jar. Mandrake is a new herb on Foraging RP1's herb nodes, found unnamed unless the finder can name it (Foraging RP3) — so a careless maker can seal the wrong root and hatch nothing.

**JP2 — Forty game days by a warm thing.** The jar carries `warm_since` and `hatches_at` — state on the thing, not the person (Pottery PG3). It counts only while it is warm: in a room with a lit fire (Cooking CP1, Forest YP1, Temperature KP8) or set in a dung heap (Farming GP12, Paracelsus' horse dung). It is read at events — a look, a move, a fire going out — and a jar left cold for more than a game day is spoiled: *the tapping has stopped*. Forty game days is ten real days (`server/conf/settings.py:50–64`), the length of Paracelsus' forty days and long enough to be a commitment rather than a click.

**JP3 — The bond is taken at the hatching, by the maker in the room.** When the jar is read past `hatches_at`, the homunculus comes out only if its maker is present and awake; otherwise the jar waits (it does not spoil once it is due). The bond stores the maker's dbref on the creature, and JP-L1's POW point is reserved at that moment, not before — a jar that spoils costs its makings, not a piece of the maker.

**JP4 — The alchemist's homunculus, later.** With *alchemy & poisons\** — the laboratory, the athanor, Lore (Alchemy) — and *glassmaking\** for a true flask, a second recipe makes a homunculus with better Characteristics (more than 1D6 each, p. 76's next rows) and a longer life. Its orders are the same list (§8); being better made never adds a kind of work (JG4).

**JP5 — One per maker.** A maker with a living bond cannot make or bind another; the recipe refuses with a line that says why (JG3). An alchemist's homunculus replaces a folk one only after the first is gone.

---

## 7. What a homunculus is

**JP6 — A creature, not a character.** A subclass of the shipped `Creature` (`typeclasses/creatures.py:34`): it cannot be picked up, given or pushed through barter while it is out (`get:false()`, `:59`), it is not puppeted and has no account. It needs its own seven Characteristics as traits (JP-L3) — the encumbrance limit reads `char.stats.str` and `char.stats.siz` (`world/encumbrance.py:284`), and the shipped creature has only `siz` (`typeclasses/creatures.py:48`). Its description is composed from parts drawn at hatching — size, skin, eyes, a habit (*it hums*, *it clicks its tongue*) — in words, as Textiles WG4 composes appearance; no free text.

**JP7 — It rests in its jar.** The hatched jar keeps the creature: `uncork` lets it out into the room beside its maker; `cork` (in the same room) calls it back in, and the jar is an ordinary carried item of ENC 2 (Storage DP6's jar) that can be given or traded (§11). Inside, the homunculus does nothing and is shown as *something asleep in a stoppered jar*. This is how it travels without a follow order and how it changes hands without the creature itself ever being an item.

**JP8 — It eats, ages and shows it.** A homunculus is fed by its maker's hand: `feed <homunculus> <food>` consumes one portion of any food (`typeclasses/consumables.py:19`) and stamps `fed_at`. It needs one portion a game week (seven game days, about a day and three quarters); a week unfed it reads *thin and listless* and its timed orders take twice as long; two weeks unfed it dissolves (JP15). Its life is about six game months from the hatching (about six real weeks), counted in world time (JQ5); in its last game week it reads *grey and slow*. All of it is computed from stamps when read (JG6), shown on `look` in words, and never sent as a message unasked — upkeep shows, it never calls (Comfort EP3).

---

## 8. Orders

**JP9 — One standing order, from its maker, in the same room.** `order <homunculus> <order>` replaces whatever it was doing; only its maker can order it; an order given from another room is not heard (eyes and voice at a distance are JQ18's). The proposed orders, in the order they could ship (§16):

| Order | What it does | Reads |
|---|---|---|
| **follow** | walks behind its maker from room to room | `move_to` (the sweeper's quiet move, `typeclasses/npcs.py:101–112`) |
| **stay** | stays where it is | — |
| **hold** / **give** | takes items from its maker into its own carry, up to its limit, and hands them back | `world/encumbrance.py:180`, `:284` |
| **tend fire** | feeds the room's fire from wood lying in the room when it burns low, through the night | Forest YP1's fuel table, its one-night cap |
| **fill** | fills a vessel it holds at a water source in its room | `CmdRefill` (`commands/foraging_commands.py:178`); Water VP2 |
| **gather** | gathers from one node in its room (JP10) | `ResourceNode.harvest` (`typeclasses/resources.py:105`) |

The watch over a sleeping maker (Rest NP18) and seeing through its eyes (Blood Magic p. 70; Achaea, §2.2) are later and JQ18's.

**JP10 — Gathering, as Adam leaned in the chat: some, and bounded.** A gather order names one node in the homunculus's room. It takes from that node through the same core the player's `forage` uses — same yield, same depletion, same regrowth (`typeclasses/resources.py:67–97`) — at twice forage's cooldown (`commands/foraging_commands.py:23`); where a node rolls (Foraging RP1's herb nodes), it rolls its maker's skill −20 (JP-L4). What it gathers goes into its own small carry and stops when it is full, when the node is empty, or when its maker leaves the world (JG1). It never fells, hunts, butchers, crafts, repairs, scribes or works the temple's coffer: those are a person's (JG2, JG4). Whether it gathers at all, and how much, is JQ2 — Adam's leaning is yes; these bounds are this document's.

**JP11 — Every step is one timed action, re-armed only while its maker is in the world.** A standing order is a chain of short timed actions on the homunculus's own slot (`world/timed_actions.py:107`), each re-arming the next only if its maker is still puppeted. `@reload` drops `ndb` and with it the chain (`persistent=False`); the homunculus then simply waits, *idle*, until it is ordered again — no Script per homunculus, unlike the sweeper's (`typeclasses/npcs.py:50`), whose point is to move on his own.

**JP12 — Its work goes through the same cores as a player's.** Today the forage core lives inside a command's `func` (`commands/foraging_commands.py:77`) and its cooldown on the character's handler (`typeclasses/characters.py:155`), so a homunculus, which types no commands and has no cooldown handler, has nothing to call. The decomposition moves each core it needs into a function both the command and the order call — one path, one log line, one depletion — rather than a second, homunculus-only copy (JQ15).

---

## 9. The attended rule

**JP13 — When its maker leaves the world, it sleeps.** At the maker's unpuppet (`typeclasses/characters.py:472`) every order lapses, and the homunculus curls up asleep where it is — in the room if it was out, in its jar if it was corked. It wakes when its maker logs in again. While its maker is a statue it does nothing at all (JG1). A homunculus left out in the open sleeps where anyone can see it; whether anything may touch it there is JQ8 and JQ9.

**JP14 — It is not company.** Comfort EP4's *company* is another puppeted character in the room; a homunculus is not one, and a lone maker with a homunculus by the fire is still alone. Its warmth is in the words (JG7), not in the comfort read.

---

## 10. Loss

**JP15 — It dissolves; there is no corpse.** A homunculus that starves (JP8), grows old, is released by its maker (`release <homunculus>`) or — once Stage 5 gives anything a way to attack — is killed, dissolves: *it slumps and crumbles to a curl of eggshell and a pinch of root dust*, which blows away. The shipped creature's death spawns a corpse for butchering (`typeclasses/creatures.py:61–108`); a homunculus overrides it, as the duplicate dissolves into slime (MoL II pp. 9–10), so homunculi are never a source of meat or parts.

**JP16 — The shock follows a hard end, not a gentle one.** If it starves or is killed, its maker suffers JP-L2's shock — *Incapable* for one game day — wherever they are, with one line: *something tears inside you, far away*. If it is released or dies of age, there is no shock, only the quiet line. Either way the reserved point of POW comes back a game week later (JP-L1). Care is rewarded; neglect hurts.

**JP17 — The maker's death does not end the bond.** Blood Magic p. 68: the enchantment goes on working when its creator is slain. A maker who dies keeps the bond through the respawn; the homunculus sleeps until they are back in the world. If the jar was carried, it goes to the corpse with everything else that is not soulbound (`world/death_contract.py:122`), and whoever takes it holds a jar they cannot command (JP19).

---

## 11. The jar in trade

**JP18 — The jar trades; the bond does not.** A corked jar is an ordinary item: it can be given, sold through barter for coin or goods, stolen or looted. The creature inside stays bound to its maker and obeys no one else.

**JP19 — Binding again.** The new holder takes the bond with `bind <jar>`: a drop of their own blood, the same fatigue bite as the making (JP1), one point of their POW reserved (JP-L1), and the previous maker's point beginning its week's return — with no shock, because the old bond was let go, not torn. Without binding, the homunculus sleeps in its jar; a maker who already has a bond cannot bind a second (JP5). A maker can sell their homunculus; a jar taken from a corpse binds the same way, and whether taking it was theft is *law/crime/bounties*'.

**JP20 — Making for others is a trade.** A maker who keeps eggs, roots and jars by the fire can hatch a homunculus, cork it and sell the jar; each buyer pays their own point of POW to bind it. The maker's own bond is held while the homunculus is theirs, so a maker sells one at a time.

---

## 12. Offline and the world

A homunculus does nothing while its maker is offline (JP13). Its incubation (JP2) and its life (JP8) run in world time like every other stamp in the game; a jar warming by a fire in a shared room keeps warming while its maker sleeps, and goes cold if the fire does. Whether a statue's sleep should freeze a homunculus's life, as Cooking CP9 freezes food a statue carries, is JQ5.

---

## 13. Economy

**Sources (all player-made or gathered):** eggs (livestock's proposed exclusive, Farming §11, or wild eggs from *fowling & wild birds\**); mandrake (Foraging's herb nodes); the jar and its seal (Storage DP6, DP7, from Pottery's pit and Rendering's tallow); warmth (Forest's wood, or dung from Farming's pen, GP12).

**Sinks:** the egg, the root, the jar and the tallow in every making; a jar that goes cold; a portion of food every game week; the homunculus itself, consumed by its span; one point of the maker's POW while it lives.

**Materials this design gives a source or a sink:** **eggs** (a sink outside the kitchen); **mandrake** (a new herb with one buyer); **storage jars and tallow** (a second use beside Storage's); **food** (a slow, steady sink); **dung** (a warmth use beside Farming's fields).

**Services:** the maker who hatches homunculi for others (JP20); the herb-gatherer who can name a mandrake; the egg-keeper; the fire-keeper whose hearth warms other people's jars — a place by the fire as the incubation's service, as a place in a kiln load is the kiln's (Pottery §13).

**JP21 — Logging: the homunculus is the actor, its maker a field.** Its gathering is logged as the shipped `gather` kind (`world/activity_log.py:60`) with the homunculus as `actor` and a `maker` field holding its maker's `[dbref, key]` pair — the shape the runbook's offline filter for automated test players already matches (BACKLOG *Automated test players*, its annotation), so a homunculus line is dropped only when its maker is a listed bot. `maker` is not a reserved name (`world/activity_log.py:75`). Making, binding, feeding and loss are JQ10.

**JP22 — The master constant, on one page.** At the leanings: forty game days to hatch (ten real days); about six game months of life (about six real weeks); one portion of food a game week (about twenty-four portions over its life); one homunculus per maker; a carry of STR + SIZ at 1D6 each (two to twelve ENC, about seven); gathering at half its maker's pace, in one room, only while its maker is online. A maker who plays two real hours a day and sets a homunculus to gather beside them adds at most what one more slow pair of hands takes from the nodes in that room — and the nodes regrow at the rate they always did (`typeclasses/resources.py:67–97`), so the world's supply is unchanged; what changes is who holds it. Every number moves together; the decomposition tunes this table, not the parts one by one.

**JP23 — No exclusive.** Anyone who has the recipe may hatch a homunculus.

**Coin:** none, ever (JG2).

---

## 14. Multiplayer and server load

- **Bounded by people.** One homunculus per maker, acting only while its maker is online: the number of working homunculi can never exceed the number of players in the world.
- **Nothing ticks.** Incubation, hunger and age are stamps read on demand (JG6); orders are timed actions (JP11); no Script, no ticker per creature.
- **Shared nodes, one path.** A homunculus takes from a node through the same synchronous core as a player (JP12), so a homunculus and a player picking the last herb cannot both get it — the shape the shop's last item needs (Housing BP16).
- **Only the maker orders.** An order checks the bond before anything else; two players cannot fight over one homunculus.
- **Bonds are atomic.** Binding and releasing write the bond and the POW `mod` in one command with no `yield` between them.
- **Wilderness.** No homunculi gathering there in v1: resource nodes there are not persistent objects (Evennia Reference §14.5–§14.6); Stage 6's.

---

## 15. Immersion extras

- **The tapping jar.** In its last days by the fire the jar gives a faint tapping now and then to whoever is in the room.
- **The hatching.** A crack in the tallow, a wet grey hand, a sneeze.
- **By the hearth.** An idle homunculus in a room with a fire sits close to it; one with a sleeping maker sits on the maker's chest or pack.
- **Small habits.** It hums, mimics its maker's gestures a moment late, flinches from rain, hides from strangers behind its maker's leg — drawn at hatching (JP6), one or two, never a stream of messages.
- **The end, gently.** A released homunculus touches its maker's hand before it crumbles.

---

## 16. Layers — a suggested order

1. **Nothing yet.** The makings come from other systems: eggs (livestock or fowling), mandrake (Foraging's herb nodes), the jar and the seal (Storage DP6, DP7, after Pottery's pit and Rendering's tallow), and fire to keep it warm (Cooking and Forest).
2. **Slice 1 — the homunculus that keeps you company in words:** the making and the jar (JP1–JP3, JP7), the bond and its POW point (JP-L1, JP5), feeding and age (JP8), the end and the shock (JP15–JP17), and the first orders: follow, stay, hold (JP9). No gathering.
3. **Slice 2 — chores:** tend fire and fill (JP9), with the fire and the vessels they read.
4. **Slice 3 — gathering (JP10, JP12, JP21):** after the economy milestone can read gathering in the activity log, so its effect is measured, not guessed (roadmap [OPEN] *No milestone measures the economy*).
5. **Slice 4 — the jar in trade (JP18–JP20).**
6. **Later:** the alchemist's homunculus (JP4); the watch over a sleeper (Rest NP18); eyes at a distance (JQ18); what Stage 5 lets a homunculus do or suffer.

**Prerequisites:** eggs, mandrake, the jar and seal, and a fire, each from its own system. **Not prerequisites:** Stage 5 (until a homunculus can be attacked), Stage 7 (the bond is priced in POW, not Magic Points), the webclient.

---

## 17. Seams in today's code (read at `1f4ce0c`)

| Need | Seam | Where |
|---|---|---|
| A creature that cannot be carried | `Creature`, `get:false()`, `siz` only, a corpse on death | `typeclasses/creatures.py:34`, `:59`, `:48`, `:61–108` |
| A non-player actor that moves | the sweeper: a Script per object, quiet `move_to` | `typeclasses/npcs.py:50`, `:68`, `:101–112` |
| POW | static trait with a `mod`; no Magic Points trait | `typeclasses/characters.py:264` |
| Carrying | the limit STR + SIZ reads `stats`; the receiving walk | `world/encumbrance.py:284`, `:180` |
| Cooldowns | a lazy handler on Character only | `typeclasses/characters.py:155` |
| Improvement | gates and the per-skill cooldown, on the character | `typeclasses/characters.py:938–959` |
| Gathering | `CmdForage.func`, the cooldown; node harvest and regrowth | `commands/foraging_commands.py:54`, `:77`, `:23`; `typeclasses/resources.py:105`, `:67–97` |
| Water | `CmdRefill`; the water-source flag | `commands/foraging_commands.py:178`; `typeclasses/resources.py:47` |
| Timed actions | one slot per actor, `start` | `world/timed_actions.py:89`, `:107` |
| The maker leaving | `at_post_unpuppet` (the statue) | `typeclasses/characters.py:472` |
| Food | `Food` | `typeclasses/consumables.py:19` |
| Coin | the temple's paid work in the Treasury's room | `commands/work_commands.py:357`, `:474` |
| Logging | `KINDS`, `RESERVED`, `record` | `world/activity_log.py:60`, `:75`, `:94` |
| Death | what goes to the corpse | `world/death_contract.py:122` |
| Recipe sources | every gated recipe has a source | `tests/test_recipe_sources.py` |
| Skills | the five shipped | `world/chargen.py:59–65` |

Evennia 6.1.0 has no follower, pet or familiar contrib; the nearest readings are EvAdventure's NPC and mob classes (`evennia/contrib/tutorials/evadventure/npcs.py:21`, `:252`) and `rpg/llm`'s NPC, which this design does not use (§19). Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **JQ1** — The letter. *Leaning: J, as used here; H is avoided for HP.*
- **JQ2** — Does a homunculus gather at all, and how much? *Leaning (Adam, chat 2026-11-09): yes — somewhat simpler chores and some gathering, not locked now. This document's leaning for the bounds: JP10's — one node in its own room, the shared core and depletion, twice the cooldown, its maker's skill −20, its own small carry, only while its maker is online — and the slice after the economy milestone (§16).*
- **JQ3** — What happens to the bond when the jar changes hands? *Leaning (chat, 2026-11-09): the new holder binds it with their own blood and POW; the old point returns with no shock (JP19).*
- **JQ4** — Which orders ship first? *Leaning: follow, stay and hold; tend fire and fill next; gathering last (§16).*
- **JQ5** — Its span: about six game months of world time, or counted only while its maker is in the world (the statue freezing it, as Cooking CP9 freezes food)? *Leaning: world time — counted only online, a casual player's homunculus would live for most of a real year.*
- **JQ6** — What it eats and how often. *Leaning: any food, one portion a game week (JP8).*
- **JQ7** — The shock's length, and which ends bring it. *Leaning: one game day of Incapable, after starving or being killed only (JP16).*
- **JQ8** — Where it sleeps when its maker logs off, and whether a haven guards it as a body (Comfort EP10). *Leaning: where it stands; in a haven, yes.*
- **JQ9** — Before Stage 5, can anyone harm, take or move a homunculus asleep in the open? *Leaning: no — it is a creature (`get:false()`) and nothing attacks yet; a corked jar is an item, and taking it is law & crime's.*
- **JQ10** — Activity-log kinds for making, binding, feeding and loss: new kinds or fields on existing ones? The family of Comfort EQ10. *Open.*
- **JQ11** — Its skill: its maker's −20 (JP-L4), or a base of its own from its Characteristics? *Leaning: its maker's −20; it never improves.*
- **JQ12** — The egg: livestock's exclusive only, or wild eggs from *fowling & wild birds\** too? *Leaning: either.*
- **JQ13** — The recipe's discipline and source: a gated recipe in which discipline, granted how? Every gated recipe needs a source (`tests/test_recipe_sources.py`). *Open — with alchemy & poisons\*, or as a seeded scroll before it.*
- **JQ14** — Found while writing: the roadmap's Stage 7 says the trait foundation holds POW and Magic Points; only POW exists (`typeclasses/characters.py:264`). The bond is priced in POW for that reason (JP-L1). If POW has no live reader beyond character creation, the reserved point costs nothing until magic reads it — is that acceptable for slice 1, or does slice 1 wait for a reader? *Open; Stage 7's dependencies line is annotated, not changed.*
- **JQ15** — Found while writing: the forage core lives in a command's `func`, cooldowns are a Character handler, and the timed-action slot is written for a character that is messaged (`commands/foraging_commands.py:77`; `typeclasses/characters.py:155`; `world/timed_actions.py:107`). Which cores are extracted for a homunculus, and does a creature hold the timed-action slot unchanged? *Open — the decomposition's, verified against live source.*
- **JQ16** — More than one homunculus for an alchemist, later? *Leaning: no (JG3).*
- **JQ17** — What others see: *a homunculus*, or *Adam's homunculus*? *Open — with BACKLOG* Strangers by description — `rpg/rpsystem` *, which decides how characters are named to each other.*
- **JQ18** — Eyes and voice at a distance (Blood Magic p. 70; Achaea's eyes and ears). *Leaning: later; it is scouting, and scouting is stealth's and Stage 5's question.*

---

## 19. Considered and not proposed

- **The viral recipe with human seed.** Not proposed, for the tone — agreed in the chat; egg, blood and mandrake keep the uncanny alchemy without it.
- **A homunculus that works while its maker is away.** The bot every sandbox forbids (§2.1; JG1).
- **A homunculus that touches coin.** No temple work, no pay, no trading on its own account (JG2).
- **Many homunculi per maker.** An army of servants is a factory (JG3; JP5).
- **Felling, hunting, butchering, crafting, repairing or scribing by a homunculus.** A person's work (JG4; JP10).
- **A corpse to butcher.** Homunculi would become a meat or parts farm (JP15).
- **A homunculus that thinks or talks for itself.** BACKLOG *An NPC guide driven by a language model — `rpg/llm`* is a separate idea; a homunculus takes orders (JP-L5).
- **Rolling the shock on Blood Magic's table.** Its permanent and decades-long rows are a lottery no one can weigh (JP-L2).
- **Paying in Improvement Rolls.** There are none to spend (JP-L1).
- **Transmutation or gold from alchemy.** AoL's own warning, and GameGold's 1:1 (JP-L7).
- **A homunculus in combat.** Achaea's is a fighter (§2.2); Stage 5's to decide.
- **Homunculi sold by an NPC.** Pillar 1.
