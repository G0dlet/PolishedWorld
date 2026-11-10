# Handoff — PolishedWorld: immersive design notes, one system per session

> **Rev 8 · 2026-11-10** — an eighteenth note, docs only, with roadmap Rev 68, BACKLOG Rev 95 and README Rev 45: `docs/system_designs/PolishedWorld_Names_Design.md` Rev 1, the queue's *names, recognition & introductions\**, written next as decided in Rev 7, with Evennia's `rpg/rpsystem` read at `v6.1.0` as the tool. Adam answered the proposal with a bare "kör", so its questions are UQ1–UQ5 with the chat's leanings. *Where we are*, *This session* (the next note is the newcomer's economy, after Stage 4.6), the prefixes (U; departure rows K), the queue (the names entry leaves; pointers on four others), the tie-ins and the gotchas are updated.
> **Rev 7 · 2026-11-10** — the next note **changed**, docs only, with roadmap Rev 67, BACKLOG Rev 94 and README Rev 44: Adam decided `rpg/rpsystem`'s timing (BACKLOG *Strangers by description*, now SCHEDULED). Its design note is the queue's *names, recognition & introductions\**, written next — before the newcomer's economy, any time before Stage 4.6 ships — and its queue entry names the contrib. The newcomer's note stays after Stage 4.6 and reads the names note. No document, prefix or tie-in changed.
> **Rev 6 · 2026-11-09** — seven systems **added** to the queue, docs only, with README Rev 43: after the homunculus note Adam asked, as after every design note, for more systems for the queue, and asked for them to be added in the same breath. They are Claude's suggestions, marked *, ahead of the bracket line: sauna, bathhouse & hot springs; sledges, skis & winter travel; tales & storytelling; lending, borrowing & the tool library; flowers & seasonal greenery; carrier birds & messenger animals; constructs, golems & scarecrows. No document, prefix or tie-in changed.
> **Rev 5 · 2026-11-09** — a seventeenth note, docs only, with roadmap Rev 66, BACKLOG Rev 93 and README Rev 42: `docs/system_designs/PolishedWorld_Homunculus_Design.md` Rev 1, written off the queue at Adam's request like Comfort — a player-made creature grown from an egg, commanded to do simple tasks and passed on in its jar. *Where we are*, the prefixes (J), three queue entries (alchemy & poisons\*, fowling & wild birds\*, magic), the tie-ins and the gotchas are updated. The next note is unchanged: the newcomer's economy, after Stage 4.6.
> **Rev 4 · 2026-11-09** — seventeen systems **added** to the queue, docs only, with README Rev 41: Adam approved two lists from the chat after the Comfort note (nine, then eight more), and said he especially likes systems that make the world feel immersive and alive. They are Claude's suggestions, marked *, ahead of the bracket line. No document, prefix or tie-in changed.
> **Rev 3 · 2026-11-09** — a sixteenth note, docs only, with roadmap Rev 62, BACKLOG Rev 89, README Rev 40 and Evennia Reference Rev 30: `docs/system_designs/PolishedWorld_Comfort_Design.md` Rev 1, written off the queue at Adam's request — the tone *hard roads, warm hearths* (now a line under the roadmap's North star), the queue's *comfort, morale & the good evening* taken in, and a defect found on the way (room echoes cannot start at 6.1.0). The next note is unchanged: the newcomer's economy, after Stage 4.6.
> **Rev 2 · 2026-11-09** — the next system is chosen, docs only, with roadmap Rev 61 and BACKLOG Rev 88: the newcomer's economy*, after Stage 4.6 (Survival loop) ships, with Adam's question whether PolishedWorld wants a newbie school. The previous leaning, lodging & safe logout, moves behind it.
> **Rev 1 · 2026-11-08** — first version in the repo, docs only, with roadmap Rev 60, BACKLOG Rev 85 and README Rev 39: the series handoff joins the fifteen one-system design notes in `docs/system_designs/`, so the latest prompt lives beside the documents it continues. It is the prompt the next design chat starts from; each session that writes a design note updates this file in the same patch.
> **Canonical:** `docs/system_designs/HANDOFF.md` @ G0dlet/PolishedWorld — git wins. If a pasted or project-knowledge copy's Rev is lower than the repo's, it's stale.

Continue the design series for PolishedWorld (Evennia 6.1.0, Mongoose Legend d100,
solo dev Adam). Discuss in Swedish; repo text in English. DESIGN ONLY: no code,
nothing locked. One docs patch for `main` per session.

## Where we are (verify — live source wins)
- The series paused after fifteen documents (2026-11-08); a sixteenth, Comfort,
  and a seventeenth, Homunculi, were written off the queue at Adam's request
  (2026-11-09); an eighteenth, Names, was written next by decision
  (2026-11-10). To resume, paste this
  file as the first message of a new design chat.
- Fifteen documents: Fishing, Housing, Hunting, Cooking, Temperature, Farming,
  Textiles, Water, Foraging, Light, Forest, Rendering, Pottery, Rest, Storage, in
  `docs/system_designs/PolishedWorld_*_Design.md` (all Rev 2 — Rev 1 plus the move;
  this handoff beside them as `docs/system_designs/HANDOFF.md`). Storage (storage,
  granary & pests) was delivered with roadmap Rev 59 (new parallel-backlog entry
  *Storage, granary & pests*), BACKLOG Rev 84 (annotations on *Food spoilage* and
  *⚠️ Decay time can run backwards when the weather turns*), README Rev 38, and is
  on origin as `2bcc1c1`, tree `135c6c7`. The move came after it, with roadmap
  Rev 60, BACKLOG Rev 85 and README Rev 39 (`docs: move the one-system design
  notes and the series handoff to docs/system_designs/`). Confirm with a fresh
  clone that Adam pushed the move — `docs/system_designs/` exists and the old flat
  files are gone; the tree is the receipt, the SHA differs after `git am`.
- Sixteenth: Comfort (comfort, haven & the good evening — cross-cutting, the tone
  every note is written in) as `docs/system_designs/PolishedWorld_Comfort_Design.md`
  Rev 1, with roadmap Rev 62 (North star tone line; new parallel-backlog entry
  *Comfort, haven & the good evening*; Stage 5 *Haven* note), BACKLOG Rev 89
  (new *⚠️ Room echoes cannot start*; annotation on *Builder QoL for dynamic
  rooms*), README Rev 40, Evennia Reference Rev 30 (§2.5 corrected) and this file
  Rev 3. Confirm with a fresh clone that Adam pushed it; the tree is the receipt.
- Seventeenth: Homunculi (the made servant — Adam's idea from the viral egg
  experiments: a creature players make, command to do simple tasks and trade) as
  `docs/system_designs/PolishedWorld_Homunculus_Design.md` Rev 1, with roadmap
  Rev 66 (new parallel-backlog entry *Homunculi — the made servant*; a dated note
  under Stage 7's dependencies: only POW exists, no Magic Points), BACKLOG Rev 93
  (annotation on *Automated test players*), README Rev 42 and this file Rev 5.
  Adam's leaning — simpler chores and some gathering — is JQ2, not locked.
  Confirm with a fresh clone that Adam pushed it; the tree is the receipt.
- Eighteenth: Names (names, recognition & introductions — strangers seen by a
  short description until named; Evennia's `rpg/rpsystem` at `v6.1.0` as the
  tool) as `docs/system_designs/PolishedWorld_Names_Design.md` Rev 1, with
  roadmap Rev 68 (Stage 5's *Strangers* line and *Nuläge* annotated), BACKLOG
  Rev 95 (annotations on *Strangers by description* and *A screen-reader
  pass*), README Rev 45 and this file Rev 8. Code read at `main` `4422b65`.
  Confirm with a fresh clone that Adam pushed it; the tree is the receipt.
- Catalogue loop 53/0: bash -c 'shopt -s globstar; n=0; m=0; for f in docs/**/*.md;
  do n=$((n+1)); b=${f#docs/}; grep -q "$b" docs/README.md || { m=$((m+1)); echo
  MISSING $f; }; done; echo "checked $n, missing $m"'
- Prefixes taken: FP/FQ, BP/BQ/BG, TP/TQ/TG, CP/CQ/CG, KP/KQ/KG, GP/GQ/GG, WP/WQ/WG,
  VP/VQ/VG, RP/RQ/RG, LP/LQ/LG, YP/YQ/YG, ZP/ZQ/ZG, PP/PQ/PG, NP/NQ/NG, DP/DQ/DG,
  EP/EQ/EG, JP/JQ/JG, UP/UQ/UG (+ WP-L, VP-L, GP-L, RP-L1–L7, LP-L1–L7, YP-L1–L7, ZP-L1–L7, PP-L1–L7,
  NP-L1–L8, DP-L1–L5, EP-L1–L4, JP-L1–L7, UP-L1–L3…; departure rows D1–D9 hunting, E1–E8 cooking, J1–J7
  temperature, N1–N3 water, R1 foraging, I1–I2 light, U1–U2 forest, O1–O6 rest,
  X1–X2 comfort, K1–K9 names; Rendering, Pottery, Storage and Homunculi have none). OQ is taken. HP
  avoided; AP/SP/XP/MP are Legend/engine words; L1–L7 are launch-minimum tasks;
  webclient tasks are W1.1-style. Free single letters for departure rows: V (reads
  as Water) — K went to Names; regrep a new one. Checked free before Names:
  QP/QQ/QG (0 hits); IP is taken by the runbook's IP-ban — regrep before use. For a new prefix, grep `\b<XX>[0-9-]` across docs/ world/ commands/
  typeclasses/ server/.

## This session: Adam picks from the queue
Names is done (Rev 8): `docs/system_designs/PolishedWorld_Names_Design.md`. Its
code is Stage 5's first slice, after that stage's design session — not beside
the webclient, not in the alpha.

**Next, decided 2026-11-09 (roadmap Rev 61, decision log *Order after the
webclient*): the newcomer's economy\*** — written after roadmap Stage 4.6 (Survival loop) ships, so
its first steps can read drinking at the spring and natural healing as live code.
Adam's question goes with it: should PolishedWorld have a newbie school, as many
MUDs have had? Claude's leaning from that chat, nothing decided: keep the school's
function, not its classic form — no separate zone and no handouts (chargen gives no
money or gear, pillar 1; a separate zone keeps newcomers from the few players
there are; its script rots with every system change), but the starter settlement
as the school: a short path of real rooms with the free nodes, one verb learned by
doing it for real, hints that fire once (BACKLOG *First-steps hints*). Read the
prior art on mud schools and tutorial areas before weighing that leaning. Read
Comfort Design first: the temple is the first haven and its threshold the first a
newcomer crosses (EP9, EP14), and EP2's three questions apply to a first hour too.
Read Names Design too: a newcomer sees everyone as a description and is seen as
one; one first-steps hint teaches `introduce` and `recog` (UP23); the description
is composed at character creation (UP1), a step the first hour passes through.

After it, the previous leaning: lodging & safe logout — best beside Stage 5's
design session, since the statue's safety becomes a combat question. Rest NQ18 leans
that it owns inns, beds for rent and the statue's safety (Rest NP13/NP19); Storage
DP16/DQ2 adds the statue as a stasis larder (Cooking CP9), bounded by one body's load
— decide there whether it merges into markets & taverns. Runner-up: carpentry &
cooperage (planks BLOCKED on a saw; barrels for Water, brewing and salt fish; crates
as Storage's bin of planks, DP15; furniture and beds; the pottery wheel).

Queue:
- travel/roads/boats (+ mounts, pack animals, caravans; swimming/drowning, Water §20)
- markets & taverns (+ dice and tavern games*; beds rented, Rest NP13/NQ13; a
  common room as a haven, Comfort EP9/EQ14; bar keep and busker as trades, EP-L3)
- mining & prospecting (ore, quarries, the underground — pitch-black rooms, Light
  LP2's pin; rock salt, Water VQ7)
- maps & navigation (getting lost, Lore (Regional))
- animal taming (+ the cat, read by Storage DP12 — where cats come from, feeding,
  no free breeding, Storage DQ13; a cat asleep by the hearth, Comfort EP22)
- temples & faith (+ burial and graves*, beside the shipped death contract; AoL
  great font :268; the temple's candles as real objects, Light LQ13 — tallow from
  Rendering ZP5; the temple's straw pallets, Rest NP12; the temple as the first
  haven, Comfort EP9)
- guilds
- law/crime/bounties (player justice, no NPC guards; Foraging §2.1; charcoal taken
  from another's clamp, Forest YQ3; ash or fat taken from another's fire, Rendering
  ZQ15; wares taken from another's pit or kiln, Pottery PQ11; a sleeper or statue
  robbed, Rest NQ5; taking from another's bin or jar, Storage DQ4; a haven guards
  bodies, never goods set down, Comfort EP10; a witness names a thief by a
  short description, stable by design, Names UG4; `recog` as the witness's
  memory, masks and hoods that defeat it, Names UP9)

From the suggestion files:
- brewing, fermentation & beekeeping (Craft (Brewer), core p. 57; ale, mead,
  vinegar; honey, wax for candles, Light LP5, AoL :514 — the clean-burning
  alternative to tallow, Rendering §15; wax seals for jars, Storage DP7;
  pollination for Farming GP2; barrels; fermenting jars, Pottery PP10)
- letters, couriers & notice boards (BACKLOG *Player mail*; `books.py`, `scribe`;
  + paper, ink, parchment and literacy* — PROPOSED_UNRATIFIED,
  `world/material_registry.py:478–483`; ink from soot/charcoal; a letter of
  introduction, after Haven & Hearth's parchment, Names UQ4)
- contracts, seals & reputation (overlaps law; herb labels as a trust signal,
  Foraging RP3)
- settlements & commons (land ownership: Farming GQ4, Housing BQ2; common wells,
  Water VQ3; herb stands as commons, Foraging RG1; woodland rights and planting
  new stands, Forest YQ11/YQ12; a shared kiln as a commons or a service, Pottery §13;
  a public cellar, Storage DQ14; who sets the haven flag, Comfort EQ12)
- calendar, festivals & culture (market days, harvest feast, Perform; Cooking CP15;
  autumn's rendering kettles, Rendering §15; firing night, Pottery §15; autumn
  stores, Storage §15)
- apprenticeship & skill teaching (core pp. 71–72; Craft only from a teacher, p. 73;
  a collier profession or scroll for the clamp, Forest YQ16; candle, pemmican and
  lye recipe sources, Rendering ZQ17; pottery recipe sources, Pottery PQ12; the
  bedroll's recipe source, Rest NQ10; bin and trap recipe sources, Storage DQ15)
- predators (the reverse hunt; Stage 5 for teeth; bear SIZ 3D6+15, MoL p. 104, as a
  big fat and hide source — the deer is fat's first, Rendering ZP1; what a night
  watch guards against, Rest NP18)

Claude's additions*:
- ornament & jewellery* (tusk `material_registry.py:225`, feather `:231`;
  jewelry slot unlimited, `server/conf/settings.py:209`)
- carpentry & cooperage* (planks BLOCKED on a saw, `material_registry.py:317`;
  barrels — Water's (§10), brewing, salt fish; crates as Storage's bin of planks,
  DP15; furniture for Housing BP15/BQ9 — beds, Rest NP13; DECISION #10's timber
  tag, Forest YQ2; hewn beams before the saw; the pottery wheel, Pottery PP12,
  AoL :386)
- alchemy & poisons* (AoL `:3508–3745`, antidotes `:3622–3653`, sleeping draught
  `:460` — a full night's rest, Rest §15; everyday tonic `:224`; foxglove is
  Foraging RP4's look-alike, Legend p. 82; sulfur/saltpeter's only sink is blocked
  black powder; water additive; the athanor, a clay furnace, AoL :3667; vessels of
  glass and earthenware; AoL preservative fluid `:388`; the alchemist's homunculus
  and the folk recipe's discipline and source, Homunculus JP4/JQ13)
- hygiene & bathing* (soap from tallow and lye is designed and held back for a
  consumer, Rendering ZP12/ZQ13 — this system is a candidate; washing reads Water VP2)
- barbers, tattoos & appearance* (Textiles WG4's rule applied to characters;
  the only way a short description changes, Names UP2; masks, hoods and
  disguise as worn items that apply the contrib's `enable_recog` lock, Legend
  Disguise p. 58 against Insight or Perception, Names UP9/UP-L2)
- smithing & metalwork* (forge + anvil, registry decision 9 — leaned by Pottery PP9:
  fixtures in a room, the hammer carried; shears, scythe, cloak pin, spade,
  fireproof pan, fish hooks, needles; flint and steel, Light LQ5; the lantern,
  Light LP5; the metal axe and saw, Forest YP-L2; charcoal from the clamp, Forest
  YP8/YP9; the crucible from the kiln, Pottery PP10; decisions 7–9 stay the
  metallurgy epic's decomposition's)
- leatherwork & tanning* (BACKLOG *Tanning upgrade*; oak bark from Foraging RP14
  and a felled oak, Forest YP7; lye as an optional third input, Rendering ZP11;
  leather dressing with tallow, Rendering ZP7; `LeatherRecipe` `world/recipes.py:174`;
  leather cord for the bedroll, Rest NP11)
- digging & earthworks* (no verb digs; retting pit, salt pan, rain pit, well,
  graves, a cellar that sets `is_cold_storage` — Storage DP4 — pitch black, Light
  LP2; peat cutting, Forest YP1; the firing pit, Pottery PP3, is built, not dug)
- resin, pitch & glue* (resin and gum PROPOSED_UNRATIFIED `:480`; tar for boats;
  the torch binder beside tallow, Light LP5/LP8, Rendering ZP5; glue for fletching)
- ice & cold* (ice from frozen ponds; an ice house that sets `is_cold_storage`,
  Storage DP4/DP15, read at `typeclasses/corpse.py:104`; snow as winter water;
  winter as a working season — winter felling, Forest §15; ash on icy paths,
  Rendering §15)
- climbing, swimming & falls* (no reader for `athletics` or `stealth` outside
  chargen and the character typeclass — verify; Rest NP3/NP14 propose athletics'
  first reader, the fatigue tests; Legend falls p. 82, asphyxiation and drowning
  p. 78; overlaps travel's swimming — decide which doc owns it)
- stealth, locks & theft* (stealth's first reader; Legend p. 39 darkness helps
  hiding, Light LQ3/LQ16; locks and keys for Housing and store rooms, Storage DP15;
  the clay-and-wax box for copying keys, AoL :194; a sleeper or statue robbed,
  Rest NQ5; feeds law/crime/bounties)
- bowyery & fletching* (BACKLOG DECISION #10's wood revisit, Stage 5 and bows;
  arrows as a sink; the feather orphan `:231`; sling bullets `world/prototypes.py:463`,
  fired bullets wait, Pottery PQ16)
- rope & cordage* (twine exists — now also the bow drill and wick, Light LP5/LP7;
  bins and traps, Storage DP8/DP13; rope for Water VP6's well bucket, climbing,
  nets, rigging, tethering)
- sericulture & silk* (mulberry, silk_thread PROPOSED_UNRATIFIED `:481`)
- masonry & lime* (stone has few sinks; limestone `:481`; lime burnt in the kiln,
  which Pottery PP9 leans to pottery's and lime's, PP12; lime mortar; stone parts
  for Housing; a stone granary against vermin, Storage DP13; quarrying shared with
  mining)
- music & instruments* (Perform; bone flutes, gut strings, drums, clay whistles;
  playing for coin — the busker, Comfort EP-L3; a song as a good state, EP5)
- natural hazards* (wildfire — Achaea's fire wears plants, Foraging §2.1, Cooking
  CP3's fire fears rain, Forest §19 left wildfire here; a pit's embers, Pottery
  §2.2; floods, storms, blizzards; BACKLOG *Weather inertia*)
- coin, minting & money supply* (who issues coin in a player-driven economy;
  `world/currency.py`; the GameGold 1:1 layer; the roadmap's [OPEN] *No milestone
  measures the economy*)
- milling & mills* (the milling stones recipe has no sink — `world/material_registry.py:124`,
  grindstone `used_by` milling `:376`, AoL `:348`; quern, water and wind mills; flour
  from Farming's grain — kept in Storage's bin, DP10; a mill as a shared station
  and a service — a work station on Pottery PP7's contract)
- oils & pressing* (lamp oil is the lantern's missing source, Light LP5; the clay
  oil lamp waits on it, Pottery PP12; linseed from flax, Textiles; a binder for
  pigment and for waterproofing; fish oil stays fishing's proposed exclusive and
  weapon oil with it, Rendering ZP-L5 — decide where pressed oil sits beside it)
- painting, carving & sculpture* (Art p. 56; Craft (Painter), (Sculptor) p. 57;
  pigment DATA `world/material_registry.py:275` and ochre DATA `:159` get their first
  sinks; shop signs, murals and carvings for Housing; a maker's mark on art; painted
  pottery)
- basketry & wickerwork* (Craft (Basketweaver) p. 57; fibre and withies — coppice
  poles, Forest YP4; baskets and creels as containers, fish traps for Fishing, skeps
  for beekeeping, wattle for Housing's daub walls and Storage's bin, DP8)
- footwear & cobbling* (Craft (Cobbler) p. 57; shoes wear on the garment-wear model,
  `world/garment_wear.py`, faster on the road; a leather sink; tallow dressing,
  Rendering ZP7; ties travel)
- armour & padding* (Stage 5's economy half; AoL's armour wear values already drive
  garments, `world/garment_wear.py`; quilted cloth, hide, leather as sinks; the
  combat half stays Stage 5's)
- bone, horn & antler* (the bonework discipline exists, `world/recipe_mastery.py:81–87`;
  horn panes for a lantern, Legend p. 114 "brass or bone" — before glass, Pottery
  PP12; cups, combs, glue; antler from larger game, predators)
- appraisal, weights & measures* (Evaluate p. 50, Commerce p. 57; scales and standard
  measures, short weight as fraud; crafting quality words read by an appraiser;
  ties markets, contracts, coin)
- banking, credit & debt* (BACKLOG *Bank / post office* is BLOCKED on Stage 5
  `CoinPile`; player bankers, IOUs, loans and default; the GameGold layer; overlaps
  coin, minting & money supply — decide which doc owns it)
- absence, upkeep & inheritance* (what becomes of a long-absent player's statue, house,
  herds, fields, kiln and stores — statues `typeclasses/characters.py:472`, Farming
  GG2; Wurm's kiln decays and its bins lose goods off a paid-up settlement, Pottery
  §2.3, Storage §2.2; a statue holding a bed, Rest NP13/NQ13; wills and heirs; ties
  settlements & commons and law)
- signals, bells & beacons* (reaching past the room: shouting range, horns, temple
  bells, signal fires read from exits like Cooking CP2's smoke, Light §15's glow and
  Forest §15's falling tree; raising the alarm for law/crime; waking a camp, Rest NP18)
- timekeeping & almanacs* (sundials, candle clocks — AoL `:176`, Legend p. 112's
  miners' candle, Rendering §15 — water clocks; Lore (Astronomy); reading tomorrow's
  weather once BACKLOG *Weather inertia* gives it a memory — a dry night for a pit
  firing, Pottery PP4; sowing dates for Farming; ties calendar & festivals)
- dung, manure & compost* (livestock make it, Farming; fertiliser for fields, dung
  cakes as fuel — 1 h in Forest YP1's table; bating hides for tanning, daub for
  Housing; latrines tie hygiene & bathing; potash from ash is a fourth restorer,
  Rendering ZP13)
- sport & contests* (athletics' first reader outside fatigue — no call-site today,
  `typeclasses/characters.py:880–881`, Rest NP3 proposes the fatigue tests; races,
  wrestling, stone lifting, archery at festivals; wagers tie taverns and dice)
- litter, abandoned goods & salvage rights* (things left in rooms never leave:
  felled wood at the feet, Forest YP6 via `receive_or_set_down`
  `typeclasses/characters.py:1624`; ash piles — outdoors they wash away in rain or
  snow, a hearth's keep, Rendering ZP9; spent clamps; a forgotten pit, Pottery §14;
  a dropped pack past the weight ceiling; a broken jar's spilled contents, Storage
  DP6; who may take what lies about, when it decays, and the server cost of rooms
  that fill up — the shipped corpse sweep, `Room.sweep_expired_corpses()`, BACKLOG
  *Ambient sweeper NPC*, is the precedent; ties law/crime and absence, upkeep &
  inheritance)
- work orders, commissions & the wanted board* (the demand side of pillar 1:
  a player posts what they want and what they pay, another fills it; BACKLOG
  *Wanted board*, moved to the economy milestone, roadmap (G5); commissions for
  a named maker, ties the maker's mark, Textiles; hauling contracts now that
  weight makes distance cost, roadmap (E); a place in the next kiln load, Pottery
  §13, or a neighbour's cellar, Storage §13; overlaps contracts, seals &
  reputation — decide which doc owns it)
- the newcomer's economy* (what a character with nothing can make and sell on
  day one, and to whom; the alpha measures onboarding, roadmap (G1); BACKLOG
  *First-steps hints*; the free nodes as the floor — deadfall, Forest YG4,
  Foraging RG3, clay, Pottery PP14, the temple's pallets, Rest NP12; the
  trivial-work band so a veteran does not undercut the newcomer's first goods;
  ties apprenticeship & skill teaching)
- orchards, nut trees & grafting* (perennial standards that bear fruit rather
  than wood, after Forest YP4's stands; years to first crop on Farming GP2's
  growing index; grafting as a skill and a service; fruit dried on Cooking
  CP11's rack, cider and perry for brewing; nuts as winter food and pig mast,
  kept in Storage's bin; Wurm's fruit and nut trees, Forest §2.2)
- fences, hedges & enclosures* (keeping animals in and out: Farming's pen and
  pasture; wattle hurdles from coppice poles, Forest YP4; hedges from planted
  stands, Forest YQ12; a boundary that says whose field it is, ties settlements
  & commons; fences wear on the condition axis like Housing BP7's parts)
- tool care: sharpening, whetstones & grinding* (tools wear by `apply_wear`,
  `typeclasses/durable.py:43`, and are repaired by `commands/repair_commands.py`;
  a whetstone or grindstone that restores an edge between repairs — stone's
  missing sink, grindstone `used_by` milling `world/material_registry.py:376`;
  sharpening as a service at a fixed stone — a work station, Pottery PP7; the axe
  re-hafted with stick and twine is the shipped precedent)
- fungi & cellar growing* (wild mushroom is Foraging RP4's; mushrooms grown on
  felled logs, Forest YP6, and in pitch-black cellars, Light LP2 — Storage DP4's
  cellar; compost from dung; a poisonous look-alike for alchemy & poisons)
- chimneys, smoke & indoor fire* (Cooking CP2's smoke indoors; a hearth part
  in Housing BP7 that needs a chimney or a smoke hole; an indoor kiln wants one,
  Pottery PP5; green wood's thick smoke, Forest YP3; charcoal burns without
  smoke, Forest YP9; soot for ink, letters & notice boards; a house fire as
  natural hazards' indoor case; the hearth as the steady ash source, Rendering ZP9)
- carts, wheelbarrows & hauling* (weight makes haulage a service, roadmap (E);
  a wheelbarrow or handcart that carries more ENC than a back, but only on a
  road, ties travel/roads; wheelwright and cartwright crafts; planks BLOCKED on
  a saw, `world/material_registry.py:317`; pack animals stay animal taming's;
  tallow as axle grease is a later sink; twenty overloaded rooms now cost a
  fatigue level, Rest NP5; whether sacks wear, Storage DQ3)
- heraldry, banners & signs* (who is who at a distance: a mark on a shield, a
  shop sign, a banner over a hall; composed from parts like Textiles WG4, never
  free text; dye and pigment as sinks; ties contracts, seals & reputation,
  guilds and painting, carving & sculpture; names at a distance, Names §15)
- crop pests* (what is left of *vermin & crop pests* after Storage DQ6: birds and
  mice in a growing field; scarecrows; Farming's rule that nothing is lost in a
  moment, GG2 — probably Farming's own, decide whether it needs a doc at all)
- aging & generations* (a game year is 91 real days; does a character age at
  all, and if so what changes — Legend has no aging table in the core; statues
  do not age, `typeclasses/characters.py:472`; ties absence, upkeep &
  inheritance; possibly "never", recorded so the question is asked once)
- butchery & offal* (Craft (Butcher) p. 57, AoL butcher `:2978`; sinew is DATA with
  "add as a harvest part" as its source, `world/material_registry.py:219` — the
  bowstring's missing input; gut for strings and sausage casings, blood, offal as
  food on Cooking's clock; the carcass beyond meat, hide, bone and Rendering ZP1's
  fat; Cooking CQ3's Craft (Butcher))
- fowling & wild birds* (the feather orphan `world/material_registry.py:231` has no
  source; AoL fowl `:2843`; nets, snares and slings for birds, Hunting TP11's snare
  holds SIZ 3 or less; wild eggs from nests in spring; feathers for fletching and
  for bedding — a feather bed or pillow, Rest NP10/NP13; ties bowyery & fletching;
  wild eggs for the homunculus's jar, Homunculus JQ12)
- knapping & stone tools* (flint EXISTS with only two sinks,
  `world/material_registry.py:135–140`; `StoneKnifeRecipe` `world/recipes.py:499`
  and the stone axe `world/prototypes.py:363–382` are the shipped bootstrap;
  knapping as a skilled act — Vintage Story's and Wurm's — arrowheads for bowyery,
  scrapers for the tanner; flint is a toolmaking stone, not a fire-starter, Cooking
  CQ7 / Light LQ5)
- crates & packaging* (what is left of *containers, packaging & sealing* after
  Storage DQ6: crates after the saw — carpentry & cooperage; wrapping and packing
  for hauling; jars and seals are Storage DP6/DP7, carried containers the weight
  decomposition's — probably folds into carpentry or carts)
- hounds & working dogs* (AoL dog `:2837`, war dog `:2839`, hunting dog in the
  price table `:2912`; hounds tracking by scent, AoL ashen powder `:132`, Hunting
  TQ9; guard dogs for Housing's break-ins and a camp's night, Rest NP18; herding
  dogs for Farming's flock; overlaps animal taming — decide which doc owns it)
- offcuts, scraps & byproducts* (the rule that every craft's waste either feeds
  another chain or vanishes: fish offcuts as bait, Fishing §2's sources; greaves,
  Rendering ZP3; ash, Forest YP10; sherds and grog, recorded and not proposed in
  Pottery §19; wood shavings as tinder, PROPOSED_UNRATIFIED
  `world/material_registry.py:481`; sawdust and hoof shavings in jellied oil, AoL
  `:366`; ties litter, abandoned goods & salvage rights)
- biomes & regional resources* (the one "what is here" helper that Water VP8,
  Fishing FQ5, Foraging RP13 and Forest §14 all name as terrain; what grows, swims
  and lies where — clay banks and limestone too — so regions trade; ties travel,
  markets and maps; regional weather is blocked on the biome layer; Stage 6's)
- lodging & safe logout* (a logged-out character stays as a statue,
  `typeclasses/characters.py:472`, wherever it logs out — in the open, in a house,
  in an inn; Rest NP19 makes the logout sleep and NP13 gives a bed one sleeper,
  held by a statue; Rest NQ18 leans that this system owns inns, beds for rent and
  the statue's safety; the statue as a stasis larder, Storage DP16/DQ2; whether a
  statue can be robbed, ties stealth, locks & theft; Cooking CP9's stone that does
  not rot)
- teas, infusions & hot drinks* (herbs from Foraging steeped in hot water; boiling
  needs Water's fireproof pot, VP5 — now pit-fired, Pottery PP10 — and a fire; a
  hot drink as a short warmth term beside the fire's, Temperature KP8; a drink as
  a kind on Water VP3's field; remedies taken as infusions, Foraging; The Long
  Dark's herbal tea before sleep, Rest §2.5)
- herb & kitchen gardens* (wild herbs moved into a small plot by a house; a Housing
  part beside the field; Foraging RG1's herb stands as commons versus a garden that
  is someone's; overlaps Farming's field — decide which doc owns it)
- scent & smell* (one way for a smell to reach the next room: Cooking CP2's smoke,
  Rendering §15's reek of hot fat, Cooking CP7's food that stinks, a tannery or a
  latrine; scent for hounds and for covering tracks, Hunting TQ9, AoL `:132`;
  overlaps signals, bells & beacons — decide which doc owns it)
- bricks & building materials* (mudbrick and pit-fired brick, Pottery PP10; roof
  tiles from the kiln, PP12; thatch — straw DATA lists thatch and bedding among its
  sinks, `world/material_registry.py:153–158`; wattle and daub, Housing; lime
  mortar, masonry & lime; Housing BP7's parts as the readers; overlaps masonry &
  lime — decide which doc owns it)
- workshops & shared stations* (who owns a station built in a shared room;
  renting a place in a kiln load, a cellar or time at a loom, Pottery §13 and PP7,
  Storage §13; a bed rented for a night, Rest NQ13; one user at a time, Pottery
  PQ10; station fees are circulation, not a sink,
  `docs/PolishedWorld_SourceSink_Ledger.md:198`; overlaps settlements & commons —
  decide which doc owns it)
- baking & ovens* (Craft (Baker), core p. 57; bread from Farming's grain through
  milling & mills; a clay oven as a firing station at small-fire heat, Pottery
  PP8 — Vintage Story's clay oven works unfired, Pottery §2.2; Cooking CP6's
  dishes; ties brewing for yeast and leaven)
- glassmaking* (sand DATA `world/material_registry.py:147–152`, glass
  `:329–334`; soda ash from ash, Rendering ZP13; the glass furnace, registry
  decision 8, leaned apart from the bloomery by Pottery PP9; the lantern's
  panes, Light LP5; AoL glass bottle `:164`, hourglass `:302`, magnifying lens
  `:340`, sighting lens `:450`; glass beads passed off as gems `:142`, ties
  appraisal)
- smelting & the bloomery* (the design half of the metallurgy epic before its
  decomposition — roadmap *[RESOLVED] Metallurgy enters through tools*; bog
  iron DATA `world/material_registry.py:177–182`; charcoal from the clamp,
  Forest YP8/YP9; the bloomery as a firing station used up by each bloom,
  Pottery PP9; the crucible, Pottery PP10; slag as waste, ties offcuts;
  overlaps mining & prospecting and smithing — decide which doc owns what)
- tolls, fees & levies* (a player settlement charging for a bridge, a well, a
  market pitch or a place in the kiln, collected by players, never by an NPC;
  circulation, not a sink, `docs/PolishedWorld_SourceSink_Ledger.md:198`; ties
  settlements & commons, travel/roads, law/crime; a GameGold question for the
  economy milestone; Achaea's city warehouse leases are the NPC-run version to
  avoid, Storage §2.1)
- public works & shared building* (a bridge, a road, a well or a wall built by
  many hands: material and labour recorded on the site as they are given;
  Housing BP1's engineering; who may use it and who must mend it; Water's
  wells, VP6; ties settlements & commons, travel/roads, tolls)
- market prices & the trade record* (what a player can know about prices
  without an NPC: price lists kept and posted by players on notice boards,
  a crier's service; the roadmap's [OPEN] *No milestone measures the economy*
  and the activity report's trade views (`world/activity_report`) as the
  staff-side mirror; ties markets & taverns, appraisal, letters & notice boards)
- salvage & taking apart* (the home is BACKLOG *Disassemble yields parts and raw
  materials — decide the salvage economy before code*: a second `disassemble`
  mode for known items, never returning all the material, and a bad roll can
  destroy it — Adam's two fixed constraints; deferred until the economy
  milestone has a ledger; ties offcuts, scraps & byproducts and litter,
  abandoned goods & salvage rights)
- wind* (the fifth weather axis nobody owns: Hunting TP-W1 derives a direction
  only, Temperature KP9 waits on BACKLOG *Weather inertia* part (2) for wind
  STR, Legend Weather pp. 231–233; readers waiting — wind chill, sails for
  travel/roads/boats, windmills for milling & mills, smoke and scent carried
  to the next room, Cooking CP2, fire spread for natural hazards, scent for
  hounds, Hunting TQ9; decide whether it is its own doc or Weather inertia's)
- moon, stars & tides* (no moon in code; Light LP2 makes a clear night dim
  "because starlight is light" — a full moon could make it brighter, a new
  moon darker; Lore (Astronomy) beside timekeeping & almanacs; night
  navigation for maps; tides for a coast if one is ever authored; festival
  dates for calendar & festivals)
- nutrition & a varied diet* (one hunger gauge today; Wurm's nutrition bars,
  where a high fat bar even slows sleep-bonus drain, Rest §2.3; Cooking CP6's
  dishes as more than calories; whether Legend has any nutrition rule —
  verify; starvation p. 90 is the only floor; ties fat from Rendering ZP1 and
  Farming's milk, eggs and grain)
- disease & contagion* (Foraging RP11 ships one disease, the flux, and names
  Legend's *Contagious* condition, pp. 78–80, without using it; sickness
  spreading between characters in a room or a house; herd sickness on
  Farming's pen; quarantine and the healer's service; ties hygiene &
  bathing, latrines, water kinds, Water VP3's still water; vermin-fouled
  stores, Storage DP14)
- languages & tongues* (Legend's Language skills — verify page and how
  chargen stores them; regional speech as a reason to trade through a
  go-between; written scripts tie letters & notice boards; Armageddon's
  languages as prior art to read; Language pp. 60–61, 50 % fluent, Language
  (Native) +50 % at creation p. 19 — no Language skill in code; the contrib's
  `rplanguage` garbles by a level 0.0–1.0, Names UP21/UP-L3)
- cultures & homelands* (Legend's Cultural Background column in the
  profession table and the Cultures column on every equipment row — Barbarian,
  Civilised, Nomad, Primitive; verify what chargen records; regional goods and
  customs for biomes & regional resources; languages; festivals)
- famine, scarcity & hard winters* (what happens when a season fails: winter
  already runs on stores — Forest YP13's woodpile, Farming's growing index,
  Storage DP17's winter bin; a bad year from BACKLOG *Weather inertia* once it has
  memory; prices rising with no NPC to cap them; Forest §2.1's Achaea lesson on a
  burst of supply; ties market prices & the trade record, predators driven closer)
- intoxication & drunkenness* (brewing makes ale and mead but nothing says what
  drinking does; a short penalty read beside `physical_modifier()`, the
  family Rest NQ4 and Light LP10 point at — verify any Legend rule; sleep
  after drinking, Rest NP7; the sleeping draught, AoL `:460`; ties markets &
  taverns, law/crime)
- fashion, status & display* (what clothes say about their wearer: dye
  colours, superior quality words, the maker's mark, Textiles WG4's composed
  descriptions; a status that someone pays a tailor for; ties heraldry,
  barbers, ornament & jewellery)
- rainwear & waterproofing* (Temperature KP7's wet state reads a reserved
  `rain_protection` on garments that nothing sets; oilcloth from cloth and
  tallow or wax, Rendering ZP7, or pressed oil; a hooded cloak, a waxed tent
  awning, AoL `:482`; ties oils & pressing, Textiles; the tent keeps a camp
  dry, Rest NP17; AoL's waterproof sea chest `:446`)
- news, rumours & the crier* (Achaea started an in-character newspaper in
  November 2026, sold by an NPC — pillar 1 makes it a player's paper; a
  crier's service, news carried by travellers, rumours that are sometimes
  wrong; overlaps letters & notice boards and market prices & the trade
  record — decide which doc owns it)
- insects, swarms & smoke* (biting insects in summer and swamps: AoL insect
  netting `:314` and insect repellent `:316`; Monsters of Legend book 1's insect
  swarm pp. 37–38 — swarms will not enter heavy smoke, so Cooking CP2's smoke is
  the answer; roused beehives tie beekeeping; a summer night outdoors as a cost
  for Rest's camp)
- hired hands & day labour* (Legend's Odd Job Table p. 85 — farmhand, manual
  labourer, bodyguard, rat catcher; the shipped `work` is a temple faucet paid
  from the Treasury, `commands/work_commands.py:2–21` — wages paid player to
  player with `pay` are the pillar-1 version; overlaps work orders & the wanted
  board and apprenticeship — decide which doc owns it)
- dairy, cheese & curing* (milk spoils on Cooking's clock — milk & cheese is
  livestock's proposed exclusive; rennet from butchery & offal; cheese ripened
  in a cellar, Storage DP4 — Vintage Story's ripening cellar; waxed or tallowed
  rinds, Rendering ZP4; salt from Water VP5)
- saddlery, harness & tack* (Legend saddles p. 122 — riding, pack, war; the
  saddlebag is shipped, `world/prototypes.py:742`; AoL horse blanket and hood
  `:666`, feed/mount rations `:680`, wintered tarp `:708`; a leather sink; ties
  animal taming, travel and carts)
- furs & furriery* (fur is DATA with no source, `world/material_registry.py:203`;
  AoL furrier `:3034`; pelts from Hunting; fur-lined winter garments for
  Temperature; overlaps leatherwork & tanning — decide which doc owns it)
- books, libraries & lore keeping* (`typeclasses/books.py` — the recipe book as
  the perishable bulk sibling of the scroll; Lore p. 52; Librarian/Research
  Assistant on the Odd Job Table p. 85; player-kept libraries of recipe books as
  a service; ties letters, paper & ink, apprenticeship)
- weathering of goods left outdoors* (durability moves only by use today,
  `typeclasses/durable.py:43`; tools, wood and cloth left in the rain could wear
  as Housing BP12's parts do; rust after metallurgy; a reason to keep things
  indoors, Storage DP8; ties litter, abandoned goods & salvage rights and
  rainwear)
- caches & hidden stores* (goods buried in the wild — digging & earthworks —
  found by searching, a first reader for Perception, `typeclasses/characters.py:360`;
  safe only while unfound, Storage DG4 and Housing BG5; the wilderness keeps no
  persistent objects, Evennia Reference §14.6 — decide whether a cache is data;
  ties stealth, locks & theft and law)
- ruins, relics & found treasure* (exploration rewards in a sandbox are a
  faucet; AoL true relic `:410`; what a ruin may hold without NPC loot breaking
  pillar 1 — old stone and timber to salvage, lore, maps; ties salvage, temples
  and masonry)
- surveying, boundaries & land measure* (whose field ends where: Housing BQ2,
  Farming GQ4; boundary stones, a surveyor's service, measured plots posted on
  a notice board; ties maps & navigation, fences, settlements & commons, law)
- spices, salt & the far trade* (AoL spices `:472–476`, one packet flavours
  thirty meals, Cooking CP-L6/§15; goods that come only from another region as
  the reason caravans exist; salt as a near-currency; ties travel, markets,
  biomes & regional resources)
- oaths, weddings & ceremonies* (public promises witnessed by players; a
  wedding feast for calendar & festivals; oaths as contracts — contracts,
  seals & reputation; the temple's part; no mechanical benefit unless
  something reads it — record the rule once)
- day length & the working day* (BACKLOG *Season-dependent day length*;
  winter's short day leaves less light for felling and fieldwork, Light LP2;
  candle demand rises in winter, Rendering ZP15; decide whether it needs a doc
  or ships as the BACKLOG entry)
- pickling & fermented foods* (vinegar from brewing, brine from Water VP5,
  jars from Storage DP6; keeping vegetables through winter; Vintage Story's
  pickling; overlaps brewing and Cooking's preservation — decide which doc
  owns it)
- postures, sitting & socials* (sit, stand and lie — by the fire, on a bench, in
  a bed; furniture's first use, Housing BP15, carpentry; `pose` is Evennia's default,
  `general.py:724` at 6.1.0; a small set of warm socials; Comfort EP20–EP21; Rest
  NP6/NP7's sleep as a posture)
- hospitality & guest-right* (host and guest, bread and salt, an invitation
  through a house's door, Housing §9; breaking guest-right is law/crime/bounties';
  gifts and whether they are logged, Comfort EP20/EQ10; havens, EP9)
- rescue, carrying & tending the fallen* (carrying a collapsed character, Rest
  NP14, later a wounded one, Stage 5, to shelter; characters cannot be picked up —
  `get:false()` in DefaultCharacter's lock setup at 6.1.0 — so a carry is its own
  verb with a body's weight, `world/encumbrance.py:180`; First Aid, Foraging RP9;
  tend-and-befriend, Comfort §2.1)
- cooperative work & helping hands* (two players on one craft or one building
  stage, Housing BG2; Legend's Assistance p. 44 and augmenting one skill with
  another p. 42; one timed action per character, `world/timed_actions.py:89` —
  decide whether a helper holds their own slot)
- keepsakes & provenance* (things that remember who made, gave or inherited them:
  `obj.db.crafted_by` is stamped today, `world/crafting_base.py:405`; BACKLOG
  *Material / maker's-mark aliases beyond "superior"*; gifts, Comfort EP20; absence,
  upkeep & inheritance; cozy items loaded with meaning, Comfort §2.1)
- weather lore & reading the sky* (forecasting from Lore or Survival — verify the
  Legend skill and page; makes the road's danger readable, Comfort EG1; needs
  weather with a memory — `roll_weather` ignores `current`, `world/weather.py` — so
  BACKLOG *Weather inertia* first; wind*, moon, stars & tides*)
- seasonal ground: mud, snow cover & ice* (ground by season and weather: fatigue on
  the road beside the overload step, Rest NP5; ground in the Track test, Hunting
  TP3, Legend p. 64; frozen water, Water and ice & cold*; ties travel/roads/boats)
- ambient wildlife & birdsong* (animals with no economic role as ambience by
  season and period — the dawn chorus, geese passing over — the first real content
  for room echoes, Comfort EP17/EP18, after BACKLOG *⚠️ Room echoes cannot start*;
  ties fowling & wild birds*, predators, biomes & regional resources*)
- journals & personal notes* (a player's own notebook on `typeclasses/books.py`
  and `scribe`, `commands/crafting_commands.py:968`; recipes noted, private memory;
  ties books, libraries & lore keeping* and paper, ink and literacy)
- phenology: the year's natural signs* (the 13-month calendar's signs — blossom,
  leaf fall, first frost, migrating birds, spawning fish, the rut — read by rooms in
  words; seasons `world/gametime_utils.py:56–61`; BACKLOG *Biome fragment library*;
  ties fishing, hunting's rhythm, Hunting TP8, ambient wildlife*)
- sunrise, sunset & the turning of the day* (one line when the day period changes,
  as the weather change is told, `world/weather.py:60`; seven periods,
  `world/gametime_utils.py:46–54`; dawn and dusk as moments, Light LP2; indoors
  muted, Comfort EP15's rule)
- life at a distance: work heard, windows lit* (the passive half of reaching past
  the room — an axe or a hammer heard next door, a lit house seen at night; Cooking
  CP2's smoke, Housing §13's chimney, Light LP3; signals, bells & beacons* is the
  deliberate half; scent & smell*)
- visible condition: what others see of you* (looking at a character shows soaked,
  shivering, exhausted, warm and fed — Temperature KP1's worded state, Rest's
  levels, Comfort EP4; `get_display_name` `typeclasses/characters.py:518`; cold as a
  social signal that invites hospitality*)
- trails & desire paths* (paths worn where many feet go, and old camps' ash —
  Rendering ZP8; footprints themselves are Hunting TP4's passage log, which already
  records characters by appearance, so this is the slow, cumulative half; ties
  seasonal ground*, maps & navigation)
- marks, cairns & messages left in the wild* (a blaze on a tree, a cairn at a
  fork, a scratched warning — players leaving signs for each other; the wilderness
  keeps no persistent objects, Evennia Reference §14.6, so decide whether a mark
  is data; ties maps, signals, caches & hidden stores*)
- player-named places & landmarks* (players name a spring, a pass or a clearing and
  the name lives on in descriptions and maps; ties maps & navigation, surveying*,
  heraldry*, Stage 6's XYZGrid for where names can attach)
- omens, folklore & superstition* (a red sky, a ring round the moon, signs people
  read and argue over; culture on top of weather lore* and moon, stars & tides*;
  no mechanical benefit unless something reads it — the rule oaths, weddings &
  ceremonies* records)
- sauna, bathhouse & hot springs* (heat as a place rather than a fire: stones heated by a
  fire, water thrown on them, a sweat and a cold plunge after; a strong warmth term
  read beside the fire's, Temperature KP8, Legend Fire and Heat p. 83; fuel per
  heating on Forest YP1's table; water from a well or a vessel, Water VP6; a Housing
  part, BP7; company and warmth both count, Comfort EP4 — a social room; overlaps
  hygiene & bathing* — decide which doc owns washing; no AoL entry)
- sledges, skis & winter travel* (winter as a season that changes how goods move: AoL
  skis `:458`, snowshoes `:466`, sleds `:2194–2198`; snow cover from seasonal ground*
  slows the foot and speeds the runner; a sledge hauls more ENC than a back on snow
  only, the winter twin of carts, wheelbarrows & hauling*; Rest NP5's overload
  fatigue per room; dogs to pull it, hounds & working dogs*; ties ice & cold* and
  Forest §15's winter felling — logs dragged out on snow)
- tales & storytelling* (stories players tell by the fire and retell: a tale composed
  by its teller, kept in memory or written down, told for company or coin; Legend has
  no storytelling skill — Sing p. 54, Art p. 56 and Influence are the nearest, verify;
  a told tale as a good state's company, Comfort EP4/EP5; ties music & instruments*,
  books, libraries & lore keeping*, news, rumours & the crier* — a rumour is a tale
  that travels; player-written text needs the moderation BACKLOG *Per-account
  cooldown on reports* and `ingame_reports` already give)
- lending, borrowing & the tool library* (an axe lent to a neighbour for a day and
  given back worn: who pays the wear, `apply_wear` `typeclasses/durable.py:43`; a
  lent thing remembers its owner — `obj.db.crafted_by` `world/crafting_base.py:405`
  is the maker, not the owner; `give` both ways, `general.py:545`, with nothing to
  enforce the return but trust and law; a shared tool shelf as a commons; ties
  keepsakes & provenance*, contracts, seals & reputation, banking, credit & debt*
  (coin credit stays there), apprenticeship, law/crime/bounties)
- flowers & seasonal greenery* (small, living, perishable things given and set out:
  wildflowers by season from phenology*, a stand read *in flower*, Foraging §15;
  cut flowers wilt on Cooking CP8's clock, dried ones keep on CP11's rack, pressed
  ones in a journal, journals & personal notes*; a sprig at a grave, temples & faith;
  a midwinter wreath, calendar, festivals & culture; a gift, Comfort EP20; never a
  status ladder — Comfort §19's decoration ladder stays not proposed)
- carrier birds & messenger animals* (a homing pigeon flies to its roost and nowhere
  else, carrying a small scroll, AoL `:2875`; the falconer's kit `:678`, hawk
  `:2851`; a dovecote as a Housing part; one-way and small, never a teleport for
  goods; ties letters, couriers & notice boards, fowling & wild birds*, animal
  taming)
- constructs, golems & scarecrows* (the homunculus's larger kin: MoL II root
  guardian p. 123 — given orders to guard a place or patrol — and the golems it is
  compared with there; a scarecrow that only stands is crop pests*'; anything that
  moves inherits Homunculus JG1–JG4 — acts only while its maker is in the world,
  never touches coin, one per maker, never more than hands; decide whether any is
  needed beyond the homunculus — possibly never, recorded so it is asked once)
- [Adam approved the seventeen above on 2026-11-09 and likes systems that make the
  world feel immersive and alive; the seven before this line were added after the
  homunculus note the same day, at his request (Rev 6); ask again "more systems for
  the queue?" at the end of the next session]

Last:
- magic (economy half only until Stage 5; Rain p. 186, dowsing AoL :216; magical
  healing is instant, Legend p. 86 — Foraging §19; magical light must still burn
  something, Light LG1/LQ15; magical heat too, Forest YG6; Magic Points regained in
  six hours of sleep, Legend p. 154 — Rest's offline credit could carry it; no
  stasis by magic either, Storage DG1; only POW exists in code, no Magic Points —
  the homunculus's bond is priced in POW, Homunculus JP-L1/JQ14)

After the doc, ask whether there are more systems to add to the queue.

Tie-ins already written. Names (UP…): lesson slot = Armageddon's *Remember Me*
thread (2013) — a screen-reader player shut out by long short descriptions and
client-side triggers; veterans wanted strangeness, the thread converged on
limits (masks defeat it, same room only, keyed to the person): strangeness is
the point, illegibility is not (UG2). Sindome (names shown, an honour rule —
left; `@shortdesc` menus — taken), Genesis and MUD-Dev 2001 (introduction vs
naming; the bluff), Haven & Hearth (memorize, per-viewer name, kin as claim
permissions, the parchment). Contrib facts: sdesc falls back to the key
(`rpsystem.py:690`); recog is a free label on the viewer (`:836–837`), a naming
system; `forget` finds only the room (`:1191`); `mask` is a free command
(`:1236`); Builders fall back to key search (`:1339`). UG3 the game tells no
name its owner did not give; UG4 a description is evidence. UP1 description
composed in chargen (build, feature, noun; ≤40 chars); UP2 no player `sdesc`;
UP5 `recog`; UP6 truthful `introduce` sets hearers' recog; UP7 `forget`
anywhere; UP9 masks later as items; UP10 every name via `$You()`/`mapping` or
`get_display_name(looker)`; UP11 grep test; UP12 statue, UP13 body (owner id at
`typeclasses/characters.py:1294–1296`), UP14 `who` a count, UP15 teach offer;
UP16 only Character takes the contrib; UP17 `N-name`; UP19 pose resets on move;
UP22 recog pushes `room` to the recogniser, description/pose to the room;
UP23 newcomer hint. Departures K1–K9 (who, statue, corpse, sixteen room
messages, teach, multimatch, say/emote/pose, room listing, chargen step).
Found while writing: UQ6 `craft` searches the same way; UQ7 recog lost on
characters created before the contrib (backfill); UQ8 account-level commands.
Homunculi (JP…): lesson slot = Ultima Online's shards
(unattended skill macroing allowed, unattended gathering forbidden — its goods reach
everyone's market); Achaea has a rule but no story (alchemist's homunculus from own
flesh, powers learned one at a time); RuneScape familiars (one at a time, a span,
beast of burden); Paracelsus/Goethe (sealed vessel, warmth, forty days; the seed not
taken, for the tone). Rules JG1 acts only while its maker is in the world; JG2 never
touches coin; JG4 its maker's hands, slower and smaller, never more. JP-L1 bond =
one reserved POW point (Blood Magic pp. 67–69), returns a game week after; JP-L2
shock = Incapable −20 % one game day, after a hard end only (JP16); JP-L3 seven 1D6
Characteristics, carry STR+SIZ; JP-L4 maker's skill −20, never improves (MoL II
pp. 9–10). JP1 folk recipe: egg + mandrake (new herb on RP1, named per RP3) + jar
(DP6) + tallow seal (DP7), gated, maker's blood = fatigue bite + dbref; JP2 forty
game days (10 real) while warm — fire or dung (GP12) — cold a game day = spoiled;
JP3 bond at hatching, maker present; JP5 one per maker; JP6 `Creature` subclass,
needs its own stats; JP7 rests in its jar (`uncork`/`cork`), the jar is the item;
JP8 fed by hand one portion a game week, six game months of life; JP9 one standing
order from its maker in the room — follow, stay, hold, tend fire, fill, gather;
JP10 gather: one node in its room, shared core, 2× forage cooldown, maker −20 where
a node rolls, own carry; JP11 timed-action chain, no Script; JP12 cores extracted,
no homunculus copy; JP13 sleeps at maker's logout; JP14 not company (EP4); JP15
dissolves, no corpse; JP17 maker's death keeps the bond; JP18–JP20 jar trades, bond
does not, `bind` with own blood; JP21 `gather` with homunculus as actor + `maker`
pair; JP22 master constant; JP23 no exclusive. No departures.
Comfort (EP…): lesson slot = The Sims Online inside the
Project Horseshoe 2017 coziness report (cozy houses on zero-sum resources → gang
rackets; coziness must be in the systems); report: safety, abundance, softness;
contrast helps only from outside the window; the cozy sandwich (Dark Souls
bonfire); responsibility/notifications/opulence negate it; Diku PEACEFUL/SAFE and
heal-rate rooms. Rule EG1 hard roads, warm hearths (tone line under the roadmap's
North star, EP1 — a lens, not a fifth pillar); EG3 comfort lengthens, never
strengthens. EP2 three questions per decomposition (danger, refuge, threshold);
EP3 upkeep shows, never calls. EP4 `comfort()` = six yes/no sources: warm (no
Cold/HeatStress), dry (indoors or not raining/snowing; KP7 later), fed (hunger and
thirst above lowest desc, or CP15), bedded (Rest NP10), company (another puppeted
char), safe (haven) → uneasy/settled/comfortable/content; EP5 a good state's
duration × (1 + comfort/6) as it begins, nothing stronger; EP6 one term for every
system, Rest's ceiling stays Rest's; EP7 a word in `status`. EP9 `is_haven` room
flag, staff-set, Old Temple first; EP10 guards bodies (no attack, no taking from a
person, sleeper, statue), never goods set down (BG5/DG4 hold); EP11/X1 a corpse in
a haven is its owner's until it crumbles; EP12 no havens in the wild, a camp is
comfort only; EP13 Stage 5 decides. EP14 a line on coming in from rain/snow
(`at_post_move`); EP15/X2 indoor characters hear a muted weather line (shipped
broadcast skips them); EP16 `$state(raining, …)` works indoors today. EP17 echo
defect (BACKLOG); EP18 echoes quiet and of the place; EP19 havens written warm.
EP20 `give` is the gift; EP21 nothing moves anyone on; EP22 the sweeper as the
relaxed guardian. EQ6 (found while writing): comfort does not join Stage 4.6
(no new content). No exclusive.
Storage (DP…): lesson slot = Achaea's 2018 leases and
warehousing (rift too small → commodities on ships and in stockrooms, losses on
link-drop, item DB slowed the game; warehouses leased by cities, decay outside
rift/warehouse, stasis bags stopped working); rules DG1 storage slows the clock,
never stops it (statue the one exception, bounded by a back); DG3 bulk goods are
counts, not objects. Prior art also Wurm FSB/BSB (counts by type, averaged
quality, ~5 %/month loss, pick up only empty), Dwarf Fortress (vermin, barrels,
cats, catsplosion), Vintage Story (cellar × container, crock sealed with fat).
DP1 place factor = room × container × holder (open 1, cellar 0.25; sack/bin 1, jar
0.5, sealed jar 0.25; statue 0) in `world/decay.py`; DP2 every factor change is an
event that advances the anchor first (move, seal/unseal, cellar flag change);
DP4 writers of `is_cold_storage`: staff on an authored cellar, Housing larder/cellar
part, later dug cellar and ice house; DP6 storage jar, a new PP10 ware: 3 clay,
Container 4 ENC, ENC 2, wears per opening, cannot nest in a pack; DP7 `seal jar` =
1 cake of tallow, any take breaks it; DP8 bin of wattle and daub (6 sticks, 4 clay,
2 twine, woodwork, ~40 ENC), indoors only, fixed while not empty; DP9 slots keyed
by (kind, quality band) with count, used hours, anchor — put deletes the object,
take spawns one; DP10 plain goods only, marked/named goods refused; DP11 vermin
~5 % per game month on bins and unsealed jars, deterministic debt, food only, runs
while away; DP12 cat ×0.5 (`keeps_vermin()`), DP13 trap ×0.5; DP14 words; DP16
statue larder accepted; DP17 master constant: 200 measures through a winter lose
~29 / ~15 with a cat / ~7 with cat and trap; seed corn in sealed jars. DQ6 scope:
stored pests and storage vessels here, crop pests Farming's, carried containers
Weight's. DQ7 (found while writing): a cellar flag that comes and goes is a second
trigger for the corpse's backward clock. No exclusive.
Rest (NP…): lesson slot = Ultima Online's camping (a fire
and a bedroll to log out in the wild, dead because inns and houses gave the same
free); Achaea has a rule but no story (sleep heals, auto-wakes; advanced
characters excused). Rule NG2: where one sleeps always matters; NG1: the night is
the logout. NP1: gauge 0–100 read as Legend's six levels on 20-point bands
(Debilitated 0, Exhausted 1–20, Wearied 21–40, Tired 41–60, Winded 61–80, Fresh
81–100; descs keys are upper bounds inclusive). NP2: −10…−50 in
`physical_modifier()`. NP3 (O2): tick stops draining; it advances an awake clock
×`fatigue_rate` (ColdStress/HeatStress/Exposed keep meaning); past 10+CON game h
(5–7 real h online) an Athletics test each game hour, −20 extra while
Starving/Dehydrated/Exposed, failure −1 level. NP4: heavy work = abstract fatigue
(one Simple Athletics per major exertion — felling, building stage, clamp/pit),
later. NP5: overload 1/room unchanged (20 rooms = a level); Nausea (RP11) = one
level. NP6 (O3): `rest` = light activity, 1 level / 4 game h (1 real h), ceiling
Winded; `sleep` = complete rest, 1 level / 2 game h (30 real min), place's ceiling;
lazy from elapsed time. NP7 (O5): sleeper refused movement, sees little, held
light snuffed, `wake`, `wake <name>`, auto-wake at ceiling. NP8: a night (8 game h)
resets the clock, shorter sleeps subtract. NP9: bare ground → Winded at best;
bedding → Fresh (AoL :146 + p. 89 "never above Winded"). NP10: duck-typed
`bedding()` — bedroll carried, winter cloak worn, bed taken, bedded room; roof and
tent are NOT bedding (differs from Housing BP8/BP10 — NQ1). NP11: bedroll =
weaving, 2 cloth + 2 plant fibre (straw later) + 1 leather, needle, ENC 1,
DurableObject, wears per night (~2 → ~50 nights), mended with cloth. NP12: the Old
Temple's straw pallets, room-wide, free, no wear. NP13: bed = one sleeper, statue
holds it, wears per night; renting with taverns. NP14: collapse at Debilitated —
Difficult Athletics per tick, forced sleep until out of the band, no eat/drink,
always ends by logout. NP15 (O6): respawn at Wearied + DeathWeakness mods →
fatigue_rate; changes death contract line (`world/death_contract.py:132`) — NQ14,
roadmap altitude. NP16–NP18: fire through the night (YP1, KP8, LP3) for online
sleepers only; one camp many sleepers; watch later (Stage 5, law). NP19 (O4):
logout is sleep — stamp at unpuppet, credit once at login at the place's
row/ceiling; statue's needs frozen. NP20: RP8 healing gets the same credit; bare
ground one row slower (NQ2). NP21: First Aid +1 level/day, not above Winded, with
RP9. NP22 master constant: day 5–7 real h online, night 2 real h = 4 levels on
bedding; bedroll ~50 nights; healing ~1 HP / 12 real h at CON 10–15. Slices:
(1) levels + clock + collapse (+ respawn once ratified) = BACKLOG entry; (2) sleep,
ceilings, pallets, logout credit; (3) bedroll. No exclusive.
Pottery (PP…): lesson slot (Achaea has a rule — forges game-placed in cities,
houses, temples, fired with one coal — but no story) = A Tale in the Desert's kiln
ladder; rule PG1: no station is scenery. PG2: the first of everything needs no
station. PG3: state on the thing, not the person. PP1: shaping = `craft` in a
proposed sixth discipline `pottery` (PQ4), output an unfired ware with
`db.fires_to`. PP2: wet → dry on Cooking's drying index. PP3: `build pit` —
clamp's twin — 8 lumps' worth, a night's fuel, `kindle`, `done_at`, `open pit`
gives wares + 2 ash. PP4: no firing roll; rain → out; early → cracked. PP5: kiln =
16 pit-fired bricks + 4 clay. PP6: `load`/`fire`/`open kiln`, 24 lumps, −2
condition per firing (~50). PP7: station contract — work stations as tools on
craft's room search; firing stations hold a load + `done_at` + loader stamp; one
user at a time; `repair` reaching a fixture. PP8: heat by Legend p. 83. PP9:
decision 7 kiln = pottery's; 8 bloomery apart from glass furnace; 9 forge + anvil
fixtures. PP10 wares: jug, pot (no kiln), brick, fire seed, bowl, whorl, loom
weights, crucible (kiln), glaze and tiles later — NO storage jar (Storage DP6 adds
it). PP11 wares wear on `condition`. PP14 clay bank refills a pit's 8 lumps in ~a
night. PP15 no exclusive.
Rendering (ZP…): lesson slot = Dwarf Fortress soap; rule ZG1: every link ships with
a consumer that bites. ZP1 `fat` at SIZ // 6 on larger animals (none on rabbit).
ZP3 `render` at a lit fire, pot as tool, no test. ZP4 tallow keeps, a small item
(20 per ENC), sold in cakes. ZP5 order: candle, torch binder, pemmican, dressing.
ZP8 ash per 4 game h of fuel. ZP10 lye. ZP12 soap designed, not shipped. ZP15
master constant: autumn stag = 3 cakes of tallow = 12 one-hour candles.
Forest (YP…): Achaea lesson — wood moved from NPC shops to dispatched foragers in
2019; rule: wood grows, never spawned. YP1 fuel table (stick ¼ h, green 1, seasoned
2, charcoal 3), fire cap one night (8 h). YP2 `build fire`. YP3 green/seasoned.
YP6 `fell`. YP8 charcoal clamp. YP13 one tree = one fire.
Light (LP…): four levels on Legend's darkness rows; `light_level(room)`;
`light_emitted()`; fuel = time; `kindle`; rain puts outdoor flames out; LP2's pin
makes a cellar pitch black; LP10 `light_modifier()` beside `physical_modifier()`;
LP11 logout snuffs held lights.
Earlier: Foraging RP8 natural healing on the tick (Rest NP20 adds the login
credit), RP9 First Aid, RP11 the flux and Nausea; Water VP2–VP8 (barrel in §10,
BLOCKED on planks); Temperature KP3 reserve, KP4 Exposed doubles `fatigue_rate`,
KP6 dry/warm shelter, KP8 fire's warmth; Housing BG5 no risk-free storage, BP8
shelter ladder (tent rung 0), BP9 roof, BP10 rest at home, BQ9 chests open;
Farming GG2 no loss in a moment, GG5 seed is capital, GP2 growing index, §13
granary and larder as Housing parts; Cooking CP8 spoilage index, CP9 statue stops
the clock, CP10 cold storage ×0.25 set by nothing, CP11 drying rack, CQ12 who may
take from a rack. Proposed exclusives: farming = grain/flour/straw/fine linen;
livestock = wool, milk & cheese, eggs, bulk hide, sheepskin; fishing = fish oil,
salt fish; textiles, water, foraging, light, forest, rendering, pottery, rest and
storage own no raw material.

## Method per system (unchanged)
1. Ask which machine (work or home). 2. Read the live repo; cite file:line.
3. Legend: `/mnt/project/Legend.pdf` and both Monsters of Legend PDFs are text
   (grep -a / sed). Page = last bare 2+-digit number line before a match
   (awk 'NR<=n && /^[0-9][0-9]+$/'); a 1-digit filter can catch stray "1" lines;
   a page number can sit two lines after the match's own page break, so read the
   context. Curly apostrophes are 3 bytes. Profession table columns: Cultural
   Background | Common Skill Bonuses | Advanced Skills | Magic. AoL is
   `docs/reference/arms_of_legend.md` (cite by line; entries can break across a
   page-number line, e.g. fire seed :244–248) — read it in Python. Quote, then
   translate.
4. Prior art: search MUDs and other games, fetch pages, take/leave per source
   (pillar 1: no NPC vendors), find the series' "Achaea lesson" (if none, say so
   and give the slot to the best lineage). Paraphrase; at most one short quote
   per source. Elanthipedia pages are huge — fetch with a token limit. Achaea's
   forum threads fetch fine at ~5000 tokens; achaea.com/game/helpview?id=N help
   files fetch fine at ~3000; atitd.wiki and wurmpedia.com pages fetch fine at
   ~3000 (wurmpedia search hits are often MobileDiff pages — readable but
   garbled; the search snippets were enough for Storage). web_fetch refuses URLs
   not seen in a prior result — web_search first.
5. STOPP 1 — findings + proposal in chat (~two mobile screens); wait for "kör".
   A bare "kör" without answers → questions go in the doc as XQ with the chat's
   leanings, recorded as leanings.
6. STOPP 2 — write `docs/system_designs/PolishedWorld_<System>_Design.md` Rev 1 on the series
   skeleton (§1 idea … §19 considered; §6 departures only when live behaviour
   changes — with none, the system's content starts at §6, as Textiles,
   Rendering, Pottery and Storage do); dated annotation on the system's
   roadmap/BACKLOG entry (or a new roadmap parallel-backlog entry if none);
   README row; bump Revs; rerun the catalogue loop after the file exists;
   cross-reference check on §/ID refs (`**XPn —`, `**XGn —`, `- **XQn**`,
   `**XP-Ln —`; also other docs' IDs exist in the doc they are attributed to — a
   regex pass over all foreign prefixes works). Keep proposal numbers in document
   order. BACKLOG annotations go before **Status**. Don't cite BACKLOG line
   numbers inside the design doc. Verify every claim attributed to another doc by
   grepping it. If writing finds something the chat did not weigh, record it as
   an XQ and say so in the Rev line (Rest: the death contract, NQ14; Housing's
   tent rest term, NQ1; Storage: the corpse's clock and the cellar flag, DQ7).
   Update this file (`docs/system_designs/HANDOFF.md`) in the same patch: bump its
   Rev, *Where we are*, the prefixes, the queue, the tie-ins and the gotchas, and
   add a README Rev line for it.
7. Commit as G0dlet <71128449+G0dlet@users.noreply.github.com>, format-patch -1,
   diff --check (and `diff --cached --check` after adding the new file), verify
   with `git am` on a fresh clone, report the tree hash.
8. Apply chains: work = `~/muddev/PolishedWorld`, `~/Hämtningar`; `git stash`
   then read `git --no-pager stash list` (old `WIP on feature/alpha-content` entry
   sits under the new one); doc patches go on `main` (switch + pull --ff-only);
   switch back, `stash pop` + `git --no-pager diff server/conf/settings.py` last.
   Home = same path, `~/Downloads`, nothing to stash. `git --no-pager`;
   `-c user.name/-c user.email` on `am` and `am --abort`; pushes via GitHub
   Desktop. Glob on a word only the new patch name has.
9. End by presenting the updated `docs/system_designs/HANDOFF.md` from the patch;
   it is the next chat's prompt.

## Gotchas (all eighteen sessions)
- Blood Magic (`/mnt/project/blood_magic_ebook.pdf`) is encoded, not a readable
  PDF — pdftotext, pypdf and pdfplumber all fail; read it through
  `project_knowledge_search`, where page numbers appear as bare lines before the
  page's text (enchanting pp. 67–70, homunculi p. 76). Monsters of Legend II is
  text: alchemical duplicate pp. 9–10, root guardian p. 123.
- `rpg/rpsystem` at 6.1.0: its `get_search_result` sends `name-N` to its own
  parser as one word, so `fiber-1` finds nothing for a non-Builder while the
  error template still offers it; the README's `N-name` settings fix it
  (`README.md:80–81`). Builders fall back to key search only when no
  description matched (`rpsystem.py:1339`). A recog is written into an
  Attribute's stored dict (`:836–837`) that only the contrib's creation hook
  creates (`:1562–1563`). Evennia's `who` lists account names, and with the
  default `AUTO_CREATE_CHARACTER_WITH_ACCOUNT` those are character names.
  `msg_contents` with `$You()`/`mapping` resolves names per receiver
  (`objects.py:1051`); moves already do (`:2293`, `:2349`).
- No Magic Points trait in code — POW is a static trait (`typeclasses/characters.py:264`);
  the roadmap's Stage 7 said otherwise until Rev 66.
- Cooldowns are a Character handler (`typeclasses/characters.py:155`); the forage
  core is inside `CmdForage.func` (`commands/foraging_commands.py:77`); `Creature`
  has only `siz` (`typeclasses/creatures.py:48`) and `get:false()` (`:59`) — a
  non-character actor has none of the character's seams. Evennia 6.1.0 has no
  follower, pet or familiar contrib (EvAdventure's NPC/mob classes are the nearest).
- Paths: the design notes live in `docs/system_designs/`. Rev lines are changelog
  and are never edited, so older Rev lines in the roadmap, BACKLOG, README and the
  notes themselves still name the old flat paths (`docs/PolishedWorld_*_Design.md`)
  — true when written. Every other path names the new folder. Cross-reference
  scripts read `docs/system_designs/PolishedWorld_<System>_Design.md`. Other docs'
  paths (`docs/roadmap.md`, `docs/BACKLOG.md`, `docs/reference/…`,
  `docs/PolishedWorld_SourceSink_Ledger.md`) are unchanged; `GameGold_Design.md`
  is not a series note and stays in `docs/`.
- A BACKLOG entry's **Status** line is read before calling it open (maker's mark
  still says SCHEDULED (Stage 3) though Stage 3 closed — recorded, not changed;
  its entry is *Material / maker's-mark aliases beyond "superior"*).
  *Food spoilage* has annotations on both sides of its Status now (Foraging's and
  Storage's before it, Cooking's after it) and is still OPEN for (1)–(3) — food
  does not age in the code.
- BACKLOG anchors are not unique: *Season-dependent day length* and *Weather
  inertia* share the Origin line "Session 2026-09-04 …". Entries inside a
  category are NOT separated by `---`: slice from the entry's `###` to the next
  `\n### ` (or `\n## ` for the last entry of a category, e.g. *`DeathWeakness`
  debuff → `fatigue_rate`*), assert one `- **Status:**` in the slice, then insert.
- Never `cut -c` multibyte docs; slice in Python.
- Count things before stating them in chat. Check a handoff's claims about other
  docs too: the Rest handoff said "jars from the pit (Pottery PP10)", and PP10 has
  no storage jar.
- No stacking anywhere in the code: every unit of a good is its own object
  (Storage DG3/DP9 proposes counts in a bin; coin is already a number, Evennia
  Reference §7.4).
- Evennia source is checkable: `pip download evennia==6.1.0 --no-deps` works in
  the sandbox; read files out of the wheel with zipfile. At 6.1.0 ExtendedRoom
  overrides `get_display_desc` (:462), not `return_appearance`. `GaugeTrait.desc`
  keys are upper bounds, inclusive (contrib/rpg/traits/traits.py).
- The character status command's key is `status`, not `stats`
  (`commands/character_commands.py:39`; fatigue printed `:74–76`).
- Weather: `WEATHER_STATES = clear, raining, snowing, foggy` with season sets
  (`world/weather.py:23–33`), rolled every 1800 s in `WeatherScript.at_repeat`
  (`typeclasses/scripts.py:112`, `:135`); only `previous_weather` kept. Seven day
  periods (`world/gametime_utils.py:46–54`, reader `:121`), copied on the Room
  (`typeclasses/rooms.py:153–161`); seasons `:56–61` (spring 1–3, summer 4–7,
  autumn 8–10, winter 11–13); 4× speed; game day = 6 real h (night 20–04 = 2 real
  h), game month = 7 real days, game year = 91 real days
  (`server/conf/settings.py:50–64`). No wind (Hunting TP-W1 proposes one), no
  moon. Survival tick 600 s (`server/conf/at_server_startstop.py:27`).
- Fatigue (shipped): gauge 0–100, descs 0/20/40/60/80/95 (`typeclasses/characters.py:316–331`);
  drain 1 per tick for online characters (`world/survival_ticker.py:21`, `:58–68`),
  fatigue absent from `HEALTH_CONDITIONS` (`:28–35`); `ColdStress`/`HeatStress` mod
  `fatigue_rate` (`world/survival_buffs.py:68`, `:87`); `DeathWeakness` on hunger/thirst,
  300 s (`:91–135`); death message reads it (`world/death_contract.py:98`, `:118`,
  `:132`). `rest` +5 per 10 s (`typeclasses/characters.py:1180–1182`, `start_resting`
  `:1369`, `stop_resting` `:1417`, `_rest_tick` `:1693–1736`; `CmdRest`
  `commands/consumption_commands.py:117`). `at_pre_move` interrupts every timed
  action and allows the move (`typeclasses/characters.py:1444–1468`); overload
  step `:1505–1509`, `OVERLOAD_MOVE_FATIGUE = 1` (`world/encumbrance.py:70`),
  `OVERLOAD_PENALTY = -20` (`:63`). Respawn restore block `:1337–1347` (fatigue
  untouched), `DeathWeakness` added `:1362–1363`. `at_post_puppet` `:494`,
  `get_display_name` `:518`. Tent: prototype `world/prototypes.py:872–884` (no
  sink), `TentRecipe` woodwork rung 60, needle (`world/recipes.py:483–496`), scroll
  in the temple (`world/seed_data.py:250–251`). No bedroll anywhere.
- Garment wear every 3 real hours (`WEAR_TICK_INTERVAL = 10800`,
  `server/conf/at_server_startstop.py:35`); `_effective_tier`
  `world/garment_wear.py:108–126` (indoor −2, cold/hot +1).
- Health: one pool, CON×2 (`world/chargen.py:172–186`); `rate=0`
  (`typeclasses/characters.py:340`); damaged only by the survival tick
  (`world/survival_ticker.py:95–102` → `apply_health_damage` `:1184`); restored
  only at respawn (`:1338–1340`).
- Skills: five — perception, stealth, athletics, craft, hunting
  (`world/chargen.py:59–65`); perception has no reader (`characters.py:360`,
  `:880–881`); custom-skill pattern `hunting` (`:443–470`); `improvable_skills` =
  craft, hunting (`:892`). Rolls `skill_check`/`opposed_check` (`world/skillcheck.py:58`,
  `:127`). `physical_modifier()` `:603–625`; `hunt` `commands/hunting_commands.py:98–99`;
  butchering `:287`; part lookup `:255`, yield `:304`.
- Harvest: `HARVEST_TEMPLATES` rabbit only (`world/harvest_templates.py:66–90`);
  `compute_yield` floors at 1 (`:142–164`); `list_parts` `:128`. Creature `siz`
  default 8 (`typeclasses/creatures.py:48`), carried to the corpse (`:100`).
- `forage` (`commands/foraging_commands.py:54`): no roll; cooldown 60 s `:23`;
  tool check `:110–122`, spawn `:133`, set down `:142`, `FORAGE_TOOL_WEAR = 5`
  `:28`, applied `:151`. `ResourceNode` `typeclasses/resources.py:39–51`,
  `get:false()` `:61`, regen `_update_regen` `:67–97`, harvest `:105–123`,
  availability phrase `:129–147`.
- Clay chain: CLAY `world/prototypes.py:432–445` (ENC 0 `:444`), CLAY_BANK
  `:447–461` (max 4, regen 3600 game-s, seeded `world/seed_data.py:204–205` at the
  Brook), SLING_BULLET `:463–472`; `SlingBulletRecipe` `world/recipes.py:604–622`.
- Wood chain: TREE `world/prototypes.py:396–411`, WOOD `:384–394` (ENC 1), STICK
  `:203–214` (ENC 0), STICK_DEADFALL `:232–245`, STONE_AXE `:363–382`; seeded tree
  `world/seed_data.py:206–207`. Wood recipes `world/recipes.py:438`, `:450`,
  `:462`, `:491`, `:597`.
- Containers: `Container(ContribContainer)` `typeclasses/containers.py:32`,
  capacity in ENC, refuses containers (no nesting) `:44`; `put` only into
  containers (`typeclasses/objects.py:25`); `CmdGet` from containers
  `commands/inventory_commands.py:68`, `CmdPut` `:104`; SACK 10 / BACKPACK 20 /
  SADDLEBAG 15 (`world/prototypes.py:699–711`, `:715`, `:742`), all "SINK: none"
  (`:708`); `SackRecipe` `world/recipes.py:315`; `enc_after_receiving`
  `world/encumbrance.py:180` walks objects.
- Corpse decay: `_SEASON_MODIFIERS`/`_WEATHER_MODIFIERS` `typeclasses/corpse.py:49–50`,
  `decay_modifier` `:92–106` (cold storage ×0.25 at `:104`), whole-span rescale
  `:116–133`, `crumble` `:166`; lazy sweep `typeclasses/rooms.py:358`, `:391`.
  `Food` `typeclasses/consumables.py:19–25` has no age.
- Registry (`world/material_registry.py`, 650 lines): plant_fiber `:93`, wood
  `:104–113`, oak bark `:114–118`, clay `:141–146`, sand `:147–152` (DATA), straw
  `:153–158` (DATA; sinks straw hat, thatch, bedding), iron_ore `:177–182`,
  raw_hide `:197–202`, fur `:203` (DATA), twine `:245`, cloth `:254`, leather
  `:265–274`, pigment `:275–280`, charcoal BLOCKED `:281–286`, metals `:287–316`,
  planks `:317–322`, glass `:329–334`, pottery BLOCKED on kiln `:335–340`,
  grindstone `:376`, axe `:390–396`, saw `:397–401`, anvil `:407–411`, furnace
  `:412–417`, kiln `:418–423`, forge `:424–429`, forbidden variants from `:440`,
  unratified `:478–483`, open decisions 6 `:503–504`, 7–9 `:505–507`, 10
  `:508–511`. `receive_or_set_down` `typeclasses/characters.py:1624`.
  `SMALL_ITEMS_PER_ENC = 20` (`world/encumbrance.py:50`).
- Crafting seams: `craft` ingredients from inventory (`commands/crafting_commands.py:315`),
  tools from room + inventory (`:324`), dry run (`:285`); `skill_name`
  (`world/crafting_base.py:58`), consume policy "raw" (`:36`), `_used_tool()`
  (`:176`), quality by tier (`:229–235`), `pre_craft` (`:260`), wear sink (`:335`);
  `repair` targets the caller's contents only (`commands/repair_commands.py:95`),
  per-target `db.repair_materials` (`:121`). Five disciplines (`world/recipe_mastery.py:81–87`;
  sack is weaving, `world/recipes.py:315–320`). Every gated recipe needs a source
  (`tests/test_recipe_sources.py`). `DurableObject` is a mixin
  (`typeclasses/durable.py:31`), `condition` `:41`, `apply_wear` `:43`. No station
  typeclass and no `requires_station` in code.
- Timed actions: `is_busy` `world/timed_actions.py:89`, `start` `:107`,
  `is_current` `:168`, `claim` `:198`, `interrupt` `:229`; one `ndb.timed_action`.
- Thermal (shipped): `thermal_regime()` (`world/thermal.py:46–80`, indoor `:68`).
- Water (shipped): `ResourceNode.is_water_source`; one spring; `drink` takes only
  a `Drink` (`typeclasses/consumables.py:28–48`, charges); `WaterskinRecipe`
  `world/recipes.py:126`; `LeatherRecipe` `:174`.
- Room echoes cannot start at 6.1.0: ExtendedRoom passes
  `repeat_broadcast_msg_to_room` (`extended_room.py:198–202`) but defines
  `repeat_broadcast_message_to_room` (`:216`); the rate is a class attribute
  (`:186`), so the project's `db.room_message_rate` (`typeclasses/rooms.py:355–356`)
  is never read (BACKLOG *⚠️ Room echoes cannot start*). Weather changes are told
  only to characters outdoors (`world/weather.py:84–86`), but `room_states` injects
  the global weather into every room, indoors too (`typeclasses/rooms.py:242–250`).
  `give` and `pose` are Evennia's defaults (`general.py:545`, `:724` at 6.1.0). The
  player corpse's owner-first grace is 72 game hours anywhere
  (`typeclasses/corpse.py:279`, lock `:293`). Sweeper `typeclasses/npcs.py:68`.
  Legend p. 63: no Survival tests in a city or town; Cost of Living and Standard of
  Living pp. 84–85; Bar Keep and Bard/Busker odd jobs p. 85.
- Seeded rooms: six — Old Temple (indoor, `world/seed_data.py:81–92`), Temple
  Clearing, Meadow, Brook, Edge of the Woods, Stony Ridge.
- Statues: `typeclasses/characters.py:472` (`at_post_unpuppet`); the ticker skips
  offline characters (`world/survival_ticker.py:45–46`).
- `is_cold_storage` read (`typeclasses/corpse.py:104`), set by nothing. Salt not
  in the registry. No fire, heat source, light or station typeclass. Temple
  `candles` chore is text only (`commands/work_commands.py:204–213`).
- Unsourced/unsunk: wool, yarn, fur, straw, spindle and pigment DATA, ochre DATA,
  sand DATA, tusk and feather orphans, planks BLOCKED, oak bark DATA, milling
  stones; no fat source in code; the tent and the shipped containers have no sink.
- Flint is a toolmaking stone: flint on flint does not make fire (bow drill or
  steel/pyrite) — Cooking CQ7 and Light LQ5 share one answer.
- No persistent resource nodes in wilderness (Evennia Ref §14.5–§14.6). Prefer
  lazy timestamps; every timed action shares `ndb.timed_action`.
- Legend refs used: Craftsman profession p. 20, Woodsman p. 23, starting goods
  (a week's food) p. 35, skill bases p. 35, Difficulty and Haste p. 39, difficulty
  examples p. 40, automatic success/failure and "no test required" p. 42,
  Athletics p. 46, Brawn p. 47, First Aid pp. 50–51, Perception and Lore p. 52,
  Resilience p. 53, Stealth p. 55, Craft list p. 57, Craft critical and fumble
  p. 58, Survival (safe place to sleep) p. 63, task times p. 67, training
  pp. 71–73, disease/poison pp. 78–80, foxglove p. 82, Fire and Heat table p. 83,
  Odd Job Table (Rat Catcher/Pest Control 2D4 CP, free net) p. 85, encumbrance and
  overloaded (−20 % to Fatigue tests) p. 86, natural healing pp. 86–87, Fatigue
  pp. 89–90 (activity, Time and Fatigue 10+CON hours, recovery 2 h complete rest /
  4 h light activity, First Aid not above Winded; levels table p. 90),
  Exposure/Starvation/Thirst p. 90, Abstract Fatigue pp. 90–91, inanimate objects
  pp. 91–92, winter cloak as bedroll p. 99, hatchet p. 103, lodging and food and
  trail rations p. 111, bedroll and candle p. 112, first aid kit p. 113, lanterns
  and healer's kit p. 114, hanging lantern p. 115, oil p. 116, weapon oil p. 117,
  tent (4 person) p. 118, tent (8 person) p. 119, hand saw and scythe p. 118,
  torch p. 119, mounts p. 120, close-combat darkness p. 135, surprise (asleep,
  groggy −20) p. 138, ranged visibility p. 141, Magic Points regained sleeping
  p. 154, Bless Crops p. 179, Rain p. 186, Weather pp. 231–233. No rule for
  spoilage, storage or vermin in the core. Monsters of Legend (book 1): insect
  swarm, brown bear p. 104, boar p. 106, cattle p. 107, deer p. 109; no ordinary
  rats or house cats in either book. AoL: bedroll `:146`, candles `:172–182`, clay
  and wax box `:194`, fire seed `:244–248`, everyday tonic `:224`, flint and tinder
  `:262`, hand-striker `:288`, insect netting `:314`, lanterns `:330–334`, handled
  net (rats) `:356`, oil `:362–366`, weapon oil `:368`, pottery wheel `:386`,
  preservative fluid `:388`, Preserving Kit `:390`, hand saw `:432`, sea chest
  `:446`, sleeping draught `:460`, tents `:480–482`, torches `:486–494`, tree net
  `:498`, wax `:514`, industrial apron `:718`, winter coat `:732`, winter cloak
  `:734`, hat `:760`, crafting quality table `:1000–1025`, tools and resources
  `:1034–1044`, task rounds `:1046–1059`, hatchet `:1593`, blacksmith `:2968`,
  carpenter `:2982`, chandler `:2992`, cooper `:3004`, metalsmith `:3066`, potter
  `:3088`, athanor `:3667`, furnaces and fuel `:3669`, first aid kit `:252`,
  healer's kit `:294`, poison antidote kit `:382`, apothecary `:2958`, healer
  `:3042`, alchemy `:3508–3745`, milling stones `:348`, scythe `:444`, yarn `:522`,
  dye `:218`, dowsing `:216`, great font `:268`, sea salt `:448`, salt tablets
  `:430`, water additive `:504`, water pack `:508`, water trap `:510`, waterskin
  `:512`, animal training `:2811`, cat `:2831`, goat `:2845`, pig `:2873`, sheep
  `:2885`, dyer `:3018`, livestock farmer `:3026`, furrier `:3034`, seamstress
  `:3106`, tailor `:3116`, Craft (Sewing) `:1056`.
