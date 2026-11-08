# PolishedWorld — Foraging & Herbalism Design Notes (wild plants, herbs, remedies, healing, sickness)

> **Rev 1 · 2026-11-08** — first version, docs only, with roadmap Rev 54, BACKLOG Rev 78 and README Rev 32. Written from a design chat, the ninth in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`, `docs/PolishedWorld_Housing_Design.md`, `docs/PolishedWorld_Hunting_Design.md`, `docs/PolishedWorld_Cooking_Design.md`, `docs/PolishedWorld_Temperature_Design.md`, `docs/PolishedWorld_Farming_Design.md`, `docs/PolishedWorld_Textiles_Design.md` and `docs/PolishedWorld_Water_Design.md`. Foraging is partly shipped — eight forageable nodes in the alpha's rooms and the `forage` command — so the notes name every place they would change live behaviour (§6). The document takes in two neighbours the queue put beside it: healing on today's single health pool, and a first sickness. **Nothing here is locked.** Every numbered item is a proposal (RP…), a goal (RG…) or an open question (RQ…); the letter is for *root* and *remedy*. In the chat Adam approved writing the document from the proposal and asked for the chat's three questions to be recorded here; the leanings under RQ1–RQ3 are the ones recommended in the chat, recorded as *leanings*, not as decisions, and the leanings under the other questions are this document's own. Prior art was read on 2026-11-08; code seams were read against `main` at `67dca8a` (Evennia 6.1.0).
> **Canonical:** `docs/PolishedWorld_Foraging_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/roadmap.md`, parallel backlog, *Herbalism* and *Disease system* — two one-line entries, each annotated (Rev 54) to point here; neither is replaced. `docs/BACKLOG.md` gains three notes (Rev 78): *Seasonal supply & population memory* (herb nodes are proposed as part (1)'s first new readers, RP2), *Two-stage healing — field stabilisation vs. repair* (First Aid on today's pool, RP9, and what that leaves for Stage 5) and *Food spoilage* (the sickness CQ4's queasy buff was waiting for, RP11). The registry's open decision 4 (straw, `world/material_registry.py:500`) is code and is left as it is; the decomposition that ships the wild grain node marks it resolved.
**When to read:** at the start of a foraging, herbalism, healing or sickness decomposition; when BACKLOG *Seasonal supply & population memory* part (1) is decomposed (RP2); when Textiles Design's dye vat is decomposed (WP8 — the dye plants are here, RP4); when Textiles WP12's rags ship (their first sink is the first aid kit, RP7); when Cooking Design's spoilage, drying rack or fire is decomposed (CP11, CP14, CQ4 — RP6, RP11, RP12); when Water Design's still water is taken up (VP3, VP-L3 — RP11); when Farming's slice 1 ships the wild grain node (GP4 — RP14); when Stage 5 decomposes wounds, H7.4 or *Two-stage healing* (§11); when Stage 6 decomposes wilderness (RP13).
**Departs from shipped behaviour in one place**, listed with its source lines in §6: health lost to hunger or thirst comes back by natural healing instead of only at respawn.

---

## 1. The idea in one paragraph

The shipped bushes and deadfalls stay what they are: free food and sticks for anyone. Beside them grow plants that only some people can name. A yarrow stand in the meadow flowers in summer and is bare in winter; a stranger who picks it walks off with *an unfamiliar feathery herb*, while someone who knows plants walks off with *yarrow* and a label on the bundle that says so, and a careless expert now and then labels the wrong thing. Fresh herbs wilt; dried on a rack they keep. A herbalist binds yarrow and rags into a first aid kit, crushes it into a poultice, chews or brews a root against a sick stomach. A body that has gone hungry or thirsty heals again on its own, slowly, by the Legend table — faster with a poultice, and by a handful of hit points at once when someone with skill and a kit treats it. Bad meat, a still pond or a mislabelled leaf can give a character *the flux* for a few days: no appetite, rolls against it each day, and a herbal remedy that helps the roll. Everything here is something someone can sell: the plant, the name on it, the kit, the treatment, the nursing.

---

## 2. Prior art

### 2.1 Achaea — the lesson

Sources: Achaean News, announce post 2733 (*Changes to harvesting and plants*, 2008) and public posts 11587 (2003) and 12380; Achaea's in-game help as published on its site (*Plants and Herbs*, 18.5). Paraphrased:

- Herbs and plants grow in rooms, are gathered with a harvesting skill whose rank decides which plants a character can take, and are eaten or smoked to cure afflictions or worked into salves and elixirs by those with the Remedies skill.
- In 2008 the `PLANTS` command stopped showing exact counts and showed four words of abundance instead; a plant could be harvested once per Achaean day, giving more the more abundant it was; an abundant plant spread to neighbouring rooms of the same environment; the name of the last harvester was shown until the day ended; fire wore plants down.
- Every plant except one suffers from being harvested down to nothing.
- In 2003 a player organisation (Oakstone) announced and changed the minimum to which herbs could be harvested, and noted that one limit for every herb would make enforcing it easier; players argued in the news about who had over-harvested a room.

**Worth taking:** abundance in words (already shipped, §17); harvest that gives more where the plant is thick; a plant that suffers when picked bare (RP2); skill that decides which plants a character can take at all (RP1).

**Not for PolishedWorld:** cures as a flat lookup — eat this herb, lose that affliction — which client scripts play for the player (§2.2 has the same failure); a staff-run spread of plants across rooms the world cannot see.

**The lesson (the series' "Achaea lesson"):** a plant in a room is a commons, and a commons needs two things to last — everyone can *see* its state in words, and taking the last of it costs everyone, not only the one who took it. Achaea's players went further and policed the floor themselves, which is pillar 1's kind of law. The rule taken: herb stock shows in words, a stand picked bare does not come back until the next growing season, and the world records *that* it was picked, not *by whom* (RG1, RP2, RQ10).

### 2.2 DragonRealms — every herb has a place, a season and a job

Source: Elanthipedia, *Healing herbs*. Paraphrased: each healing herb lists the skill ranks needed to find it, the seasons and times of day it can be foraged, the terrains it grows in, the body part it heals and whether it heals wounds or scars; most can also be bought from NPC herb shops in many towns; the page links a client script that checks a character's wounds and applies the right herbs from its pack.

**Worth taking:** a herb as a row of data — season, terrain, skill threshold, one job (RP4).

**Not for PolishedWorld:** herb shops (pillar 1); dozens of herbs whose only difference is which body part they fix — a table a script matches better than a person (§2.1's failure), and Stage 5's locations do not exist yet. Few herbs, each with a different job (RP4).

### 2.3 Project Zomboid — knowledge, not luck, names the plant

Sources: pzfans.com (*Poisonous Berries Guide*, *Traits*) and Steam community discussions. Paraphrased: without the Herbalist trait or the book that teaches it, foraged berries and mushrooms show only as *unknown* and their poison is hidden, even for kinds that are always safe; with it, a poisonous one is named as such; the trait is also what lets a character find medicinal herbs at all.

**Worth taking:** knowledge as the gate to naming (RP3); a name that is the herbalist's to give — and therefore to sell (RG2).

**Not for PolishedWorld:** a trait bought once that removes the risk for good. Here the name is a roll, and a fumble writes a wrong one (Legend p. 52; RP3).

### 2.4 Haven & Hearth — the eye finds, the hand caps quality

Source: Ring of Brodgar wiki (*Foraging*, *Legacy:Foraging*). Paraphrased: the foraging skill uses Perception and Exploration to see herbs, roots and berries at all; a herb's quality comes from the spot it grows on and is hard-capped by the gatherer's Survival.

**Worth taking:** quality capped by the forager's skill (RP5).

**Not for PolishedWorld:** plants that are invisible until a stat reveals them — in authored rooms the stand is there to look at, and who can *name* it is the gate (RP3). Perception's first call-site is contested already (RQ14).

### 2.5 Lost Souls — forage *for* something

Source: LSWiki (*Foraging*). Paraphrased: `forage for <kind>` — bark, boughs, branches, drink, food, herbs — with success and time depending on the foraging skill, the terrain and the matching fieldcraft skill; some places allow no foraging at all.

**Worth taking:** in the wilderness, foraging names a kind and the terrain answers (RP13).

---

## 3. Design goals

- **RG1 — The commons is visible.** Stock reads in words; a stand picked bare is visibly bare and slow to come back (§2.1).
- **RG2 — Knowledge is the herbalist's capital.** What a character can name is what it can sell; a label is a promise someone made (§2.3; RP3).
- **RG3 — The bootstrap stays free.** Shipped nodes keep working for anyone, without a roll (RP1; BACKLOG *First-steps hints* points a hungry newcomer at `forage`).
- **RG4 — Every harm is warned, has an answer within reach, and arrives slowly.** Temperature Design's rule, here for sickness (RP11).
- **RG5 — Treating another is a service.** Treating oneself is worse than being treated (Legend p. 50: at least −10 % on oneself; RP9).
- **RG6 — Nothing ticks, and a statue is stone.** Plants are read on demand; healing and sickness ride the shipped survival tick, which visits online characters only (`world/survival_ticker.py`; `typeclasses/characters.py:472`).

---

## 4. Legend alignment

**Rules as written:**

- **Survival (POW+CON)** — core p. 63: a daily test when an Adventurer lacks food, water or a safe place to sleep, not used in towns. Difficulty examples, p. 40: finding food and water in a forest is Simple (+20 %); recalling which plants are edible in farmland is Lore (Regional), Easy (+40 %); recalling which are edible in an uncharted jungle is **Lore (Plant)**, Difficult (−20 %).
- **Lore (INT×2)** — p. 52: many separate skills; a fumble is a complete misunderstanding, the book's example being mistaking a poisonous fungus for something else.
- **First Aid (INT+DEX)** — base p. 35, rules pp. 50–51: applied to one location; at least −10 % on oneself; 1D3 minutes; a location once treated cannot be treated again until fully healed; needs bandages or salves, and makeshift bandages torn from a dirty tunic give −20 %. On an injured location (above 0 HP) it heals 1D3 HP; on a Serious Injury, 1 HP and function back; on a Major Injury it only stabilises. A critical halves the time and heals 1D3+1; a fumble does 1 more point of damage.
- **Healing (INT+POW)** — p. 60: surgery, antidotes, curing disease; always needs a healer's kit; 1D3×10 minutes. Against a disease, success adds the skill's critical value to the patient's next Resistance roll.
- **Disease and poison** — pp. 78–80: Potency 10–100 opposed by Resilience or Persistence; each has Application (Ingested, Inhaled, Contact, Injected), Onset time, Duration, Resistance Time, Potency, Resistance, Conditions and Antidote/Cure. Conditions include **Nausea** (cannot eat; a Resilience roll on stressful physical action or be sick for 1D3 rounds and gain a level of Fatigue), **Fever** (all skills halved, plus nausea) and **Contagious**.
- **Resilience (CON×2)** — p. 53: resists poison and disease; a critical ends that dose's further rolls.
- **Natural healing** — pp. 86–87: one Hit Point per 72 / 48 / 36 / 24 / 18 / 12 hours for Resilience 01–10 / 11–30 / 31–50 / 51–70 / 71–90 / 91+; strenuous activity drops the rate one row; a Major Wound does not heal naturally until treated with Healing.
- **Starvation and thirst** — p. 90: while starving or thirsty, healing does not work (Water Design §4).
- **Sample cure** — p. 82: the sap of the foxglove protects against a sleeping draught if taken beforehand.
- **Equipment** — p. 113: the first aid kit, bandages, tourniquets and herbal compresses, lets First Aid be used without penalty and lasts five uses whether the test succeeds or fails; p. 114: the healer's kit, needed for Healing.
- **Task times** — p. 67: foraging for food and setting snares, 2 to 4 hours.
- **Arms of Legend** (`docs/reference/arms_of_legend.md`): the first aid kit, of bandages, tourniquets and herbal compresses, some with leeches, salt sticks or fish oil, five uses (`:252`); the healer's kit with mortar and pestle and poultices (`:294`); the poison antidote kit, +20 % to Healing against poison (`:382`); the sleeping draught, a packet of bitter herbs (`:460`); the apothecary, a healer of minor wounds with salts, minerals and tinctures (`:2958`); the healer, for disease and infection (`:3042`); alchemy's poisons and antidotes (`:3622–3653`).

**Translation proposals:**

- **RP-L1 — Shipped foraging stays unrolled.** Legend's daily Survival test is for the wilderness (Water VP-L2); in authored rooms food is found by looking. The shipped nodes keep their no-roll `forage` (RP1).
- **RP-L2 — Lore (Plant) becomes `herbalism`.** A custom skill on the precedent of `hunting` (`typeclasses/characters.py:443–470`), base INT×2 (two INT in `SKILL_BASE_PAIRS`, `world/chargen.py:59–65`), on `improvable_skills` (`typeclasses/characters.py:892`). It finds and names herbs (RP1, RP3) and is the skill remedy recipes roll (RP7). Lore (Regional) stays unmodelled, as Farming GP-L4 says.
- **RP-L3 — First Aid becomes `first_aid`.** Base INT+DEX, rules as written on today's single pool: 1D3 HP, once until health is full again (RP9). The once-until-healed rule moves to each location when Stage 5 ships them.
- **RP-L4 — Natural healing uses the table, with CON×2 for Resilience.** No Resilience skill exists; CON×2 is its base (p. 53) and the value used until one does (RQ4). Thirst and starvation stop it (p. 90).
- **RP-L5 — Disease follows pp. 78–80 as data rows.** v1 has one disease and one condition, Nausea (RP11). Healing's bonus to the next Resistance roll is stood in for by the remedy's own bonus until a Healing skill exists (RQ6).
- **RP-L6 — Task times are not used.** Two to four hours of foraging would be thirty to sixty real minutes at the 4× clock; the shipped 60 s cooldown stays (`commands/foraging_commands.py:23`). First Aid's 1D3 minutes become a short timed act (15–45 real seconds; RP9).
- **RP-L7 — Legend's prices are not used.** Pillar 1. Kits follow AoL's five uses (`:252`).

---

## 5. The loop

Proposed phases; each is something someone can sell.

1. **Find.** A herb stand in an authored room, in its season (RP2); later a terrain in the wilderness (RP13).
2. **Pick and name.** `forage` it; `herbalism` decides whether you get a herb at all and what it is called (RP1, RP3).
3. **Keep.** Fresh herbs wilt; dried on a rack they last (RP6).
4. **Prepare.** Compress, poultice, settling root, first aid kit — recipes that roll `herbalism` (RP7).
5. **Treat.** First Aid on someone hurt (RP9); a poultice that speeds healing (RP10); a remedy for the flux (RP12).
6. **Recover.** Natural healing does the rest, slowly (RP8).

---

## 6. Departures from shipped behaviour

Each row is a change to behaviour that `main` has today; each is a proposal.

| # | Shipped today | Proposed | Where shipped |
|---|---|---|---|
| R1 | Health lost to starvation or thirst never comes back: `health` has `rate=0`, only the survival tick writes it (down), and only respawn restores it | Natural healing on the survival tick, by the Legend table with CON×2 for Resilience, stopped while starving or dehydrated; whole hit points only (RP8) | `typeclasses/characters.py:334–345`, `:1338–1340`; `world/survival_ticker.py:95–102` |

Unchanged: the eight shipped forageable nodes, their yields, regeneration and tool checks (`world/seed_data.py:194–211`; `typeclasses/resources.py:67–123`); `forage`'s cooldown, tool wear, set-down and activity line (`commands/foraging_commands.py:23`, `:28`, `:142`, `:158`); the availability phrase (`typeclasses/resources.py:129–147`); the survival gauges and their damage (`world/survival_ticker.py`); respawn's full restore (`typeclasses/characters.py:1338–1340`); `eat` for anyone not sick.

---

## 7. Finding plants

**RP1 — Two kinds of node; only the new kind rolls.** The shipped nodes stay free (RG3). A **herb node** is a `ResourceNode` with one more attribute — proposed `lore_skill = "herbalism"` and a difficulty — that makes `forage` roll `skill_check(herbalism, difficulty)` (`world/skillcheck.py:58`) before `harvest()` claims a unit (`commands/foraging_commands.py:126`). A failure takes nothing and costs the cooldown — you searched and found nothing you knew; a success takes one unit; the roll's grade goes on to RP3 and RP5. Below a node's threshold (Achaea's rank gate) a character is told the plant is beyond them and nothing is rolled or spent. `herbalism` improves on use, as `hunting` does.

**RP2 — Herb stands grow in their season and suffer when picked bare.** A herb node regenerates only in its season, on whatever clock BACKLOG *Seasonal supply & population memory* part (1) picks — Farming GP2's growing index or a per-type season table — with the node's own anchor advancing by whole intervals, never Corpse-style multiplication. Proposed for herbs, beyond part (1): a stand picked to nothing (`available == 0`) regrows **nothing until the next growing season begins** — the roots live, this year's growth is gone (§2.1). One rule, no new knob. Out of season a stand reads as *dormant* and gives nothing. The shipped berry bush is not a herb node and is not changed by this proposal; whether it follows part (1) is part (1)'s question.

**RP13 — Wilderness forage names a kind and reads terrain.** Stage 6's recycled rooms must not hold nodes (Evennia Reference §14.5), so `forage herbs`, `forage food`, `forage bark` at a coordinate ask the terrain what grows there in this season, through one helper — nodes in authored rooms, terrain outside — the same answer as Water VP8 and Fishing FQ5. Wilderness foraging is Legend's Survival test (RP-L1); which skill rolls it is Water VQ4's question. Stage 6.

---

## 8. Knowing plants

**RP3 — A herb is found unnamed unless the finder can name it; the name is a label.** The item spawns with its true kind in `db.herb` and a display name chosen by the roll:

- **Success** — the true name (*yarrow*), and the bundle carries a label: `db.label` = the kind, `db.labelled_by` = the finder's key.
- **Failure** at a node the character could roll on — nothing is found (RP1).
- **Critical** — the true name, and RP5's quality bonus.
- **Fumble** — a *wrong* label, drawn from the herbs that look alike (Legend p. 52's poisonous fungus). The finder cannot tell.
- A character who forages a herb node with no `herbalism` worth rolling is refused (RP1); a herb that reaches someone unlabelled (bought from a careless picker, found on a body) shows a generic look name — *an unfamiliar feathery herb* — built from a per-kind description, so look-alikes share it.

The label travels with the bundle, as a maker's mark does (`db.crafted_by`, `world/crafting_base.py:405`; Textiles WP10). **Identifying is a service:** a proposed `identify <herb>` rolls the reader's `herbalism` against the herb's difficulty and, on success, tells the true kind and offers to relabel it in the reader's name. A wrong label is how a mislabelled leaf reaches someone's stomach (RP11); the name of who wrote it is how the market learns whom to trust (RG2). Per-character knowledge — Project Zomboid's model — is RQ7.

**RP5 — Quality is capped by the finder.** A herb carries `db.quality` on the shipped four-band scale (Farming GP4); the node gives a base band and the finder's grade caps it (§2.4): a plain success caps at the second band, a critical lifts the cap one band. A remedy's strength is read from its herbs' quality (RP7). v1 may ship every herb at one band and add this later.

---

## 9. The first plants

**RP4 — Few herbs, each with a different job.** Proposed, as data rows (kind, season, difficulty, look-alike group, use). Names are the ones Textiles WP8 already used where they overlap.

| Kind | Season | Job | Reader |
|---|---|---|---|
| yarrow | summer, autumn | compress and poultice | first aid kit (RP7), poultice (RP10) |
| willow bark | all (knife) | fever, later | Fever condition, after v1 (RQ15) |
| chamomile | summer | settles the stomach | the flux (RP12) |
| woad, weld, madder | summer, autumn | blue, yellow, red dye | Textiles WP8 dye vat |
| lichen | all | purple dye | Textiles WP8 |
| foxglove | summer | none in v1; poisonous look-alike | alchemy & poisons (Legend p. 82's sap) |
| wild mushroom | autumn | food; look-alikes are not | the flux (RP11) |

Yarrow and foxglove share a look-alike group in v1 only if foxglove has a harm to carry — until poisons exist, a mislabelled foxglove eaten is an exposure to the flux (RP11).

**RP14 — Other things foraging gives a source to.** Each is a reader that names foraging already; none is decided here.

- **Wild grain and straw** — Farming GP4's wild grain node, which also gives straw; registry open decision 4 calls it cheap and says it unblocks the straw hat (`world/material_registry.py:500`; straw `:153–158`; hat `world/prototypes.py:615`). A plain node, no roll (RP1).
- **Oak bark** — the registry's source is *oak tree + knife* (`world/material_registry.py:114–118`); a second yield of a tree node, with a knife as `required_tool`, for BACKLOG *Tanning upgrade*.
- **Worms and grubs** — Fishing FP10's bait, a plain forage yield.
- **Wild herbs as spice** — Cooking §15's spices that lengthen *well fed* (CP15): thyme and juniper as RP4 rows when cooking ships it.

---

## 10. Keeping and preparing

**RP6 — Fresh herbs wilt; dried herbs keep.** A fresh herb is perishable on Cooking Design's spoilage clock (the statue rule included: nothing ages on a logged-out character); dried on Cooking's drying rack (CP11) it keeps for real weeks. A wilted herb is weaker (one quality band down), not lost. Until spoilage ships, herbs keep — RP6 ships with it.

**RP7 — Remedies are recipes that roll `herbalism`.** The recipe base already names the skill it rolls (`skill_name = "craft"`, `world/crafting_base.py:58`); remedy recipes set `herbalism`. Proposed v1:

- **Compress** — yarrow, pounded on a stone (no new tool). An ingredient, not a remedy.
- **First aid kit** — compresses plus rags (Textiles WP12) or cloth, bound with twine: five uses (AoL `:252`), worn by `apply_wear` like Cooking's Preserving Kit (CP-L6). A kit's maker is stamped as every craft is.
- **Poultice** — yarrow and water (Water VP2's draughts), applied to oneself or another (RP10).
- **Settling root** — chamomile chewed raw: a small bonus against the flux; brewed as a **tea** over a fire (Cooking CP1–CP4) with draughts, a larger one (RP12).

Remedy recipes are not knowledge-gated in v1: anyone can try, the skill decides (RQ13).

---

## 11. Healing

Today there is one health pool, derived from CON (`derive_health_max`, CON×2, `world/chargen.py:172–186`); only the survival tick damages it (`world/survival_ticker.py:95–102`, `apply_health_damage`, `typeclasses/characters.py:1184`); nothing restores it but respawn. Stage 5 replaces the pool with hit locations and wound tiers. Everything below is shaped so that it maps onto locations without being redesigned: the healing rate becomes per location, First Aid's once-until-healed flag moves to each location, and Stage 5's tiers and *Two-stage healing* add what this cannot do — stabilising a Major Wound, surgery, H7.4's dying state.

**RP8 — Natural healing rides the survival tick (R1).** Each survival tick (every 600 s, `server/conf/at_server_startstop.py:27`) adds the game-seconds since the last tick to a per-character healing counter, and whenever the counter passes the character's interval it grants one whole hit point and carries the remainder — the `ResourceNode` anchor shape (`typeclasses/resources.py:67–97`). The interval is the Legend row for CON×2 (RP-L4): at CON 10–15 a hit point every 48 game hours, twelve real hours at the 4× clock (`server/conf/settings.py:50–64`). It accrues nothing while the character is *starving* or *dehydrated* (`world/survival_buffs.py:21`, `:36`; Legend p. 90), and, once Temperature Design's reserve exists, while it is below its threshold (KP-L4).

*Why not the trait's own rate.* Evennia's gauge trait can change itself lazily at a `rate` per second (`evennia/contrib/rpg/traits/traits.py:1527`, `:1570–1577` at v6.1.0), but it counts wall-clock time — through logouts and server downtime, so a statue would heal (RG6) — and leaves `current` fractional, while the survival tick's integer damage relies on a whole `health` (`world/chargen.py:172–186` says so). The tick-and-counter shape keeps both.

**RP9 — First Aid.** `treat <target>` (oneself allowed, at −10 %) is a short timed act on the actor's `ndb.timed_action` slot (`world/timed_actions.py:107`, `claim` `:198`), 1D3 game minutes; both must still be in the room at completion. It needs a first aid kit (no penalty, one use worn) or rags or cloth (−20 %, one consumed, Legend's torn tunic); with neither it is refused. On success it restores **1D3** (critical **1D3+1**, half the time); a fumble does **1** damage (Legend pp. 50–51) through `apply_health_damage`, so a fumble can never kill outside the one chokepoint. A character treated once cannot be treated again until health is back at its maximum — Legend's once-per-location on one pool. Treating another needs their consent (RQ8), because a fumble harms. `first_aid` improves on use.

**RP10 — A poultice speeds healing.** Applied (to oneself or another, no roll beyond the craft that made it), it moves the character one row up the Legend table for a game day — the mirror of p. 87's strenuous rule moving it one row down. It does not restore hit points itself: Legend keeps instant healing for magic (p. 86).

---

## 12. Sickness

**RP11 — One disease in v1: the flux.** A data row in Legend's shape: **Application** Ingested; **Onset** 1D4 game hours; **Duration** 1D3 game days; **Resistance Time** daily, the first at the end of onset; **Potency** set by the source; **Resistance** CON×2 (RP-L4); **Conditions** Nausea; **Cure** a settling remedy (RP12). Exposure is one opposed check at the moment of eating or drinking (`opposed_check`, `world/skillcheck.py:127`); a character who resists notices nothing. Proposed sources, each a hook another design left open:

- **Off food eaten by force** — Cooking CQ4's queasy buff becomes an exposure.
- **Still water** — Water VP3's `still` kind and VP-L3's hook.
- **A mislabelled plant eaten** — RP3's fumble; a wild mushroom from the wrong look-alike group.

Proposed placeholder Potencies, to calibrate in the decomposition: off food 40, still water 30, a wrong mushroom 50. **Nausea** in v1: `eat` is refused (*you cannot keep anything down*) while drinking is allowed; hunger keeps falling, which is the bite; the condition's Fatigue on stressful action waits for BACKLOG *Fatigue-exhaustion consequence*. The clock rides the survival tick like RP8: onset, the daily roll and the duration count down only while the character is online (RG6). The character is told at onset, at each roll and at the end, in words (RG4). A buff carries the state, as `Starving` does (`world/survival_buffs.py:21`). No contagion in v1 (Legend's Contagious condition is RQ15's later work, with Farming GP13's herds).

**RP12 — Treating the flux.** A remedy taken while sick adds its bonus to the **next** daily Resistance roll — Legend's Healing rule (p. 60) with the remedy standing in for the healer's critical value: the chewed root +10 %, the tea +20 %, one band of herb quality worth +5 % more (placeholders). Remedies taken before exposure do nothing in v1 (foxglove's protective sap, p. 82, is alchemy's). A Healing skill and the healer's kit wait for Stage 5 (RQ6).

---

## 13. Economy

**Sources (all natural or player-made):** herb stands in authored rooms (natural, not NPCs — pillar 1 holds); wilderness terrain (Stage 6); remedies and kits made by players.

**Sinks:** herbs eaten, brewed or bound into kits; kits worn to nothing in five uses; rags or cloth consumed by makeshift First Aid; dyestuff consumed every dyeing (Textiles WP8); fresh herbs wilting (RP6); stands picked bare until next season (RP2).

**Materials this design gives a source or a sink:** **rags** (Textiles WP12 — its first sink, the first aid kit and makeshift First Aid); **cloth** (a new sink); **twine** (the kit's binding); **straw** (its source, registry decision 4); **oak bark** (its source, for tanning); the new herbs of RP4 (sources and sinks together); dye plants (Textiles WP8's source). New registry rows — the herbs, the compress, the kit, the poultice, the settling root — are added by the decomposition that ships them, with sources and sinks, as the registry requires.

**Services:** picking for a dyer or a healer; **naming** — identifying and relabelling herbs (RP3); treating the hurt (RG5); kits sold to travellers and hunters; nursing the sick with tea.

**Exclusives:** none proposed. Herbs are foraging's by nature; whether herb beds on a farm plot ever compete is RQ12. Wild grain is shared with farming as Farming GP4 proposes.

**Coin:** none proposed. **Logging:** a herb taken is the shipped `gather` kind (`commands/foraging_commands.py:158`); treating, identifying and falling sick are RQ11.

---

## 14. Multiplayer and server load

- **Nothing new ticks.** Herb nodes regenerate on read, as every node does; healing and sickness add a few lines to the survival tick, which already visits each online character every 600 s.
- **Two pickers, one stand.** `harvest()` is a synchronous read-modify-write under Evennia's single reactor thread (`typeclasses/resources.py:105–123`); the roll happens before the claim, so a failed roll claims nothing and two successes serialise as two foragers do today.
- **Treating.** One actor slot each; the patient's state is re-read at completion (health, the once-treated flag, presence in the room). Two people treating one patient at once: the second completion finds the flag set and refunds nothing because nothing was spent before completion (RQ8's consent prompt closes the rest).
- **Labels.** A label is two attributes on the item; `identify` writes only after a success, inside one command.
- **Offline.** A statue neither heals nor sickens, and its herbs do not wilt (RG6).

---

## 15. Immersion extras

- **Reading a stand.** A herbalist sees *yarrow, in flower* where others see *a stand of feathery white flowers*; out of season, *dry stalks*.
- **Signs of picking.** A skilled reader sees that a stand was picked lately — *torn stems, still green* — not by whom (RQ10); BACKLOG *Seasonal supply* part (3)'s signs, for plants.
- **The herb bundle.** A label in the labeller's hand: *yarrow — labelled by Adam*.
- **Drying.** Bundles hanging from a rack read as *drying* and then *dry and brittle*.
- **Being sick.** Lines that say what is happening without numbers: *your stomach turns at the thought of food*; *the cramps ease*.
- **Being treated.** The room sees a wound being bound; the patient feels it.

---

## 16. Layers — a suggested order

1. **Slice 1 (no new content):** natural healing on the survival tick (RP8, R1). Small, and it closes the gap §11 opens with.
2. **Slice 2 (herbalism):** the `herbalism` skill and its migration (the `hunting` pattern); one herb node (yarrow) in one alpha room with RP1–RP3, on part (1)'s seasonal clock (RP2); `identify`.
3. **Slice 3 (first aid):** the `first_aid` skill; `treat` with rags or cloth (Textiles WP12); the compress and the first aid kit (RP7, RP9); the poultice (RP10) once Water VP2 has shipped with its first reader.
4. **Slice 4 (sickness):** the flux with its sources as they exist (RP11); the chewed root, and the tea when Cooking's fire exists (RP12).
5. **With their readers:** dye plants with Textiles WP8; wild grain and straw with Farming slice 1 (or alone — registry decision 4); oak bark with *Tanning upgrade*; worms with fishing; drying and wilting with Cooking's spoilage and rack (RP6).
6. **Later:** wilderness foraging (Stage 6, RP13); the Healing skill, surgery and stabilising (Stage 5, *Two-stage healing*, H7.4); Fever, contagion and herd disease (Farming GP13); poisons and antidotes (*alchemy & poisons*).

**Prerequisites:** none for slice 1; a skill migration for slices 2 and 3; part (1)'s clock for RP2 (slice 2 can ship one herb on it, or wait); rags for slice 3's best path (cloth works without them); Cooking CQ4 or Water VP3 for any source of the flux to exist.

---

## 17. Seams in today's code (read at `67dca8a`)

| Need | Seam | Where |
|---|---|---|
| Forage | `CmdForage`; cooldown; tool wear; node filter; claim; set-down; activity line | `commands/foraging_commands.py:54`, `:23`, `:28`, `:87–92`, `:126`, `:142`, `:158` |
| Nodes | `ResourceNode` attributes; lazy regeneration; harvest; availability phrase | `typeclasses/resources.py:39–48`, `:67–97`, `:99–123`, `:129–147` |
| Shipped forage yields | berries, berry bush, plant fibre, fibre plant | `world/prototypes.py:94`, `:104`, `:127`, `:155` |
| Seeded rooms and nodes | alpha rooms; node seeds | `world/seed_data.py:81–155`, `:194–211` |
| Skills | five skills; base pairs; `hunting` as the custom-skill pattern; improvable set | `world/chargen.py:59–65`; `typeclasses/characters.py:443–470`, `:892` |
| Rolls | `skill_check`; `opposed_check`; grades | `world/skillcheck.py:58`, `:127`, `:52–55` |
| Recipe skill | `skill_name`; tool penalty; maker and recipe stamps | `world/crafting_base.py:58`, `:99`, `:405`, `:412` |
| Health | the gauge, `rate=0`; damage chokepoint; death; respawn restore; max from CON | `typeclasses/characters.py:334–345`, `:1184`, `:1235`, `:1338–1340`; `world/chargen.py:172–186` |
| Survival tick | damage sum and single call; interval | `world/survival_ticker.py:95–102`; `server/conf/at_server_startstop.py:27` |
| Conditions | `Starving`, `Dehydrated`, `DeathWeakness` | `world/survival_buffs.py:21`, `:36`, `:91` |
| Trait rate (not used) | `GaugeTrait` lazy rate by wall clock | `evennia/contrib/rpg/traits/traits.py:1527`, `:1570–1577` (v6.1.0) |
| Timed acts | one `ndb.timed_action`; `claim` | `world/timed_actions.py:107`, `:198` |
| Statues | logged-out character as stone | `typeclasses/characters.py:472` |
| Materials | straw; oak bark; registry decision 4; unratified list | `world/material_registry.py:153–158`, `:114–118`, `:500`, `:478–483` |
| Professions | four, none outdoor | `world/professions.py:66–70` |
| Clock | 4× speed, day and month lengths | `server/conf/settings.py:50–64` |
| Wilderness recycling | what recycling does not reset | `docs/PolishedWorld_Evennia_Reference.md` §14.5 |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **RQ1** — Two new skills, `herbalism` and `first_aid`, or one? *Leaning: both — Legend keeps Lore (Plant) and First Aid apart (pp. 50, 52), First Aid is a skill every Adventurer has while plant lore is a specialist's, and RG5's service needs a skill that is not the herbalist's.*
- **RQ2** — Natural healing now (slice 1, R1) or with Stage 5's locations? *Leaning: now — health lost to thirst never comes back today, the rate maps onto locations unchanged, and the tick-and-counter shape keeps health whole.*
- **RQ3** — Does sickness belong in this document, or in its own? *Leaning: here, as the one-disease v1 of §12; a document of its own when contagion, Fever and herd disease come.*
- **RQ4** — Resilience: CON×2 derived, or a real skill that improves? *Leaning: derived, no improvement, until combat or a second resistance reader needs the skill.*
- **RQ5** — Does a statue heal? *Leaning: no — nothing happens to stone (RG6); the gauges already freeze.*
- **RQ6** — A Healing skill (INT+POW) and the healer's kit in v1 for the flux? *Leaning: no — the remedy's bonus stands in (RP12); Healing comes with surgery in Stage 5.*
- **RQ7** — Is a herb's name a label on the item, or knowledge in each character's head (Project Zomboid)? *Leaning: a label — it can be bought, trusted, forged by mistake, and it names who wrote it.*
- **RQ8** — Does treating another need the patient's consent? *Leaning: yes, a yes/no at the start, because a fumble harms.*
- **RQ9** — Does a stand picked bare wait for the next growing season, or recover logistically from what is left? *Leaning: the next season — one rule, no knob, and the commons lesson in plain sight.*
- **RQ10** — Does a stand show who picked it last (Achaea)? *Leaning: when, not who — a sign a skilled reader sees; names are for players to tell each other.*
- **RQ11** — Activity-log kinds for treating, identifying and falling sick: new kinds or fields on existing ones? The family of Hunting TQ10, Textiles WQ8, Farming GQ6, Fishing FQ6 and Water VQ9. *Open.*
- **RQ12** — Herb beds on a farm plot slot, later? *Leaning: later — wild stands stay the seed source, as wild grain is for farming (Farming GP4).*
- **RQ13** — A herbalist or healer profession, and knowledge-gated remedy recipes? *Leaning: not in v1; wait for BACKLOG *Every knowledge-gated recipe has a profession grantor*.*
- **RQ14** — Perception: does spotting herbs (Haven & Hearth) claim its first call-site, beside Cooking CQ13 and *light & darkness*? *Leaning: no — in authored rooms the stand is visible and `herbalism` names it.*
- **RQ15** — What comes after the flux: Fever (skills halved — a modifier on every check), contagion, willow bark's job? *Open; after v1 is played.*
- **RQ16** — Where do the first herb stands grow — the meadow, the woods, the brook? A content decision. *Open.*
- **RQ17** — Legend's strenuous rule (p. 87): does hunting or crafting drop the healing row? *Leaning: not in v1; `rest` as the light-activity mark later.*

---

## 19. Considered and not proposed

- **A roll on every forage.** It would turn a newcomer's first meal into a skill check (RG3; RP-L1).
- **Herbs for sale from NPCs.** Pillar 1 (§2.2).
- **A herb per body part.** A lookup table a client script plays (§2.1, §2.2); Stage 5's locations do not exist.
- **Instant healing from a herb.** Legend keeps it for magic (p. 86); remedies speed or help, they do not refill.
- **Healing on the trait's own rate.** Wall-clock time and fractional health (RP8).
- **Plants that spread to neighbouring rooms.** Achaea's spread needs rooms that share an environment; authored rooms are written by hand. Wilderness terrain answers it differently (RP13).
- **Over-harvest limits enforced by the server.** The commons shows its state; players decide what to do about it (§2.1).
- **Disease that strikes the absent.** A statue does not sicken (RG6; Farming GG2's rule).
- **Poisons, antidotes and the sleeping draught.** *Alchemy & poisons* in the queue (AoL `:460`, `:3622–3653`).
- **Magical healing.** Stage 7.
