# PolishedWorld — Creature Harvesting Design Notes (what a dead creature gives, and who owns the rest)

> **Rev 1 · 2026-11-25** — first version, docs only, with roadmap Rev 92, BACKLOG Rev 125, README Rev 86 and the series handoff `docs/system_designs/HANDOFF.md` Rev 20. Written from a design chat, the twenty-second in the series of one-system design notes, and the queue's *butchery & offal* under a wider name: it covers every body that comes from a `Creature`, not only game. It **replaces the project-knowledge file of the same name** (v1.0, 2024-12-20, annotated 2026-06-27 as a "reference mine"), which was never in git although two docstrings and the Hunting Decomposition cite it by this file name; §5.2 records what the code took from it and §19 what was left behind. Like Hunting, this system is **already shipped** (roadmap Stage 0), but unlike Hunting the note proposes **no change to live behaviour**, so it has no departures table and the system's content starts at §6. **Nothing here is locked.** Every numbered item is a proposal (HTP…) or an open question (HTQ…); a decomposition locks or rejects each one. In the chat Adam chose the note's scope (what nobody owns, plus a map of who owns the rest), its boundary (the `Creature` class, with a person's body left refused and asked as HTQ9) and its rule for parts (none without a named sink, HTP3). Prior art was read on 2026-11-25; code seams were read against `main` at `500424c` (Evennia 6.1.0).
> **Canonical:** `docs/system_designs/PolishedWorld_Creature_Harvesting_Design.md` @ G0dlet/PolishedWorld — git wins. A project-knowledge file of this name is the retired v1.0 and is not this document.

**Altitude:** design (one feature, before its decomposition).
**Home:** roadmap, *Stage 0 — Hunting* (delivered), and its 2026-11-25 note (Rev 92); `docs/BACKLOG.md` gains one entry, *`harvest_templates.py` credits the book with a rule it does not have* (Rev 125).
**When to read:** before a second species gets a harvest template; at the start of any hunting decomposition (the deer, Hunting Design §16); when Rendering's fat (ZP1) or Cooking's first slice (E3) is decomposed; when an armour batch reaches a piece of 3 Armour Points or more (§11); and before anyone copies from the retired v1.0.
**Departs from shipped behaviour nowhere.** Every proposal adds data or an item; none changes what `harvest` does today.

---

## 1. The idea in one paragraph

A body on the ground is a short list of useful things and a clock. The harvester kneels with a knife and decides what is worth the time before the meat turns: the meat first, then the skin, and the bones can wait until they are all that is left. What the body gives depends on what it was — a rabbit is meat, a skin and a few bones; a stag adds fat in autumn and antlers; a boar has tusks; a wyvern has scales no knife was made for. PolishedWorld already has the body, the clock and the knife. What it lacks is the rule for the second animal: who decides what a new species gives, with which skill each thing is taken, and which of the many things a carcass could give are worth an item at all. This note answers that, and says who already owns everything else.

---

## 2. Prior art

### 2.1 MUME — the lineage

`butcher` takes food, hides or other useful things from a corpse and needs a cutting tool, wielded or on the belt. A corpse that has been butchered or scalped shows it. Orcs and trolls, and only they, may butcher a dead player for food.

- **Take:** one verb on the body, a blade as the tool, and a body that shows what has been taken (HTP7).
- **Take as a question:** butchering a person is tied to who the butcher is, not open to all (HTQ9).
- **Leave:** nothing; it is the shape `harvest` already has.

### 2.2 Wurm Online — every corpse, one knife

Any corpse can be butchered. A butchering knife gives more than another sharp tool. Butchering a human corpse lowers the butcher's alignment and trains nothing.

- **Take:** the dedicated tool is better, not required (§10). A person's body can be made costly instead of forbidden (HTQ9).
- **Leave:** the list of products per creature is long and mostly for its own sake.

### 2.3 UnReal World — the skin is lost in steps

A hide's grade can fall at every step — skinning, cleaning, tanning — and when too much time passes between them. Players report a clean kill and a poor skin, and do not understand why.

- **Take:** time between steps matters, which the corpse's clock already says.
- **Leave, as a warning:** a grade that falls for reasons the player cannot see. If parts ever carry a grade (Cooking CP16, Hunting TP12), the line that tells the harvester must say why.

### 2.4 Stoneshard — the kill decides the pelt

Each pelt has hidden hit points that fall with the damage the animal takes; too low at death and there is no pelt. Piercing and crushing damage spare it most.

- **Take, for later:** how a creature died can reach the hide. CE gives a creature damage it carries (Combat Design CE9), and Hunting TP12 already asks for the clean kill. It is theirs to propose; this note only says the hide is where it would land.
- **Leave:** the hidden number.

### 2.5 Haven & Hearth — the tool caps the result

Butchering gives hide, meat, intestines and entrails. The result's quality comes from the animal's and is capped by the sharp tool's quality and by Survival.

- **Take:** the tool and the skill both bound the result. Today the knife is a flat +10 (§5.1).
- **Leave:** entrails as an item with no use but another recipe's input.

### 2.6 World of Warcraft and Warhammer Online — the warning, and a line worth keeping

In *World of Warcraft* a creature's level sets the skinning skill needed to skin it at all, so the skill is raised by skinning whatever is the right colour. *Warhammer Online* separates sentient creatures from the rest: not everything killed can be butchered.

- **Leave (the series' "Achaea lesson"):** a number that gates the body. Here a poor harvester may try any body and fail; the roll decides, not a threshold.
- **Take as a question:** the line between a beast and a thinking creature (HTQ10).

---

## 3. Design goals

- **HTG1 — The template is the whole answer.** What a body gives is read from its species' template and nowhere else (HTP1).
- **HTG2 — No part without a sink.** A thing is not an item until something consumes it (HTP3; pillar 1; `AGENTS.md` §1A).
- **HTG3 — One owner per subject.** Where another note owns a part's fate, this note points there (§6).
- **HTG4 — The clock makes the choice interesting.** Soft parts first, hard parts later; nothing here adds a second clock (Cooking CP8 owns the one there is).
- **HTG5 — Legend's rules where the book has them, and said plainly where it does not.** The book has one paragraph on taking a hide and one kit; everything else is ours (§4).
- **HTG6 — Lazy and cheap.** No ticker, no per-part object until it is taken.
- **HTG7 — A new species is data.** Adding one is a template and its part prototypes; the command does not change (`world/harvest_templates.py:63–64`).

---

## 4. Legend alignment

**Rules as written:**

- **Taking a hide** — *Arms of Legend*, *Creature Hide Armour* (`docs/reference/arms_of_legend.md:1420`): a hide meant for armour is harvested and prepared within 48 hours of death; that is generally a normal Craft (Leatherworking) test, and the Games Master may give a penalty for odd beasts; Lore (Animal) or Survival may be used instead as a Hard (−40 %) test.
- **Monster Hide Armour** (`:1426–1448`): the table groups creatures by natural Armour Points. Natural AP 1–5 gives armour of AP 1–2 at no craft penalty in 2 days; 6–9 gives 3–4 at −10 % in 5 days; and so on to 24–25. The wearer needs a creature of **no less than double his own SIZ**; a smaller one covers only some Hit Locations. Armour from a hide generally has **half** the creature's AP, and the table assumes it. A creature with natural AP above 25 is generally unsuitable (`:1422`). A magical ability in the skin does not survive.
- **Anatomy Kit** (`:120`; ENC 1, 50 SP, `:533`): knives and sharpened flints of natural materials, ritually cleansed so that materials and body parts can be taken *without contaminating them*; **+10 % to Heal tests made to extract materials from a dead creature**.
- **Butcher** (`:2978`): a labourer who turns livestock, fowl and game into meat, expert at removing bones, hooves and scales to reach the meat or to save what the animal gives.
- **Craft (DEX+INT)** — Legend core p. 57: many separate skills; the list includes butcher, leatherworker, bowyer and fletcher. **Lore (INT×2)** — p. 52. **Survival (POW+CON)** — p. 63. **Healing (INT+POW)** — p. 60: always needs a healer's kit.
- **Natural armour, by species** — *Monsters of Legend*: deer (stag) SIZ 3D6+12, average 23, AP 1 on every location, *Hide* (p. 109); boar SIZ 2D6+3, average 10, AP 2, *Tough Hide*, with a tusk attack (p. 106); wolf SIZ 2D6+3, average 10, AP 2, *Fur, Hide* (p. 122); brown bear SIZ 3D6+15, average 26, AP 3, *Fur* (p. 104); wyvern SIZ 4D6+12, average 26, AP 5 on the hindquarters, *Scales* (p. 100).

**What the book does not have.** No table gives a skill and a difficulty per kind of part. The retired v1.0 printed one under the heading *From Arms of Legend*; a search of the whole book text in git finds no such table, no *sinew*, *tendon* or *tallow*, and Craft (Leatherworking) and Lore (Animal) only in the paragraph above. The table was v1.0's own extension of that paragraph. Two things followed from it and are corrected here: the kit was called *"required for quality extractions"* (the book gives a bonus and requires nothing), and `world/harvest_templates.py:19–20` says *"AoL puts meat on Survival (Easy, +20)"*, which the book does not say (BACKLOG entry, §17).

**Translation proposals:**

- **HTP-L1 — The hide stays on `craft`, at Normal.** This is the book's rule and it is shipped (`world/harvest_templates.py:75–77`). Craft (Leatherworking) arrives when specialised Craft arrives for every craft (Cooking CQ3's leaning); the skill is data per part, so that is a one-line change.
- **HTP-L2 — The book's 48 hours is the corpse's second threshold.** A hide is harvestable through *stale* and gone at *rotting*, and stale ends at 48 game-hours (`typeclasses/corpse.py:43`; `max_stage` `STALE`, `world/harvest_templates.py:79`). The shipped number and the book's agree; nothing to change, and worth knowing before either is tuned.
- **HTP-L3 — Meat on `hunting` is ours, not the book's.** Survival is the core skill for living off the land (p. 63) and `survival` is the gauge category here, so `hunting` stands in for it (Hunting Design TP-L1). The +20 is a calibration choice.
- **HTP-L4 — The kit is for delicate parts, and it is a bonus.** See HTP8.
- **HTP-L5 — Hide armour takes the table as it stands.** See §11.

---

## 5. The loop today

### 5.1 What `harvest` does

`harvest <part> from <corpse>` (aliases `skin`, `butcher`, `commands/hunting_commands.py:196`) rolls the part's own skill through `world/skillcheck.py` with the part's difficulty, +10 if a knife is carried (`:28`, `:433`; no penalty without one) and the harvester's physical modifier (`:287–292`). A success takes the **whole part at once**: `max(1, SIZ // divisor)` units (`world/harvest_templates.py:164`), a critical 150 % rounded up (`:49`). A failure can be retried; a fumble ruins the part. A part is taken once per corpse (`commands/hunting_commands.py:274`, `:312`). One attempt per 30 real seconds (`:27`). A clean take or a botch is logged as `gather` (`:378`). A person's body is refused (`:241`; §12).

The one template is the rabbit (`world/harvest_templates.py:66–90`):

| Part | Skill | Difficulty | Yield | Harvestable through | Prototype |
|---|---|---|---|---|---|
| `meat` | `hunting` | +20 | SIZ // 2 | stale | `rabbit_meat` |
| `hide` | `craft` | 0 | SIZ // 3 | stale | `raw_hide` |
| `bone` | `craft` | 0 | SIZ // 4 | skeleton | `bone` |

No part carries a quality or an age. `natural_ap` is copied from the creature to its body (`typeclasses/creatures.py:104`; `typeclasses/corpse.py:73`) and nothing reads it.

### 5.2 The numbers the code credits to this file

`typeclasses/corpse.py:10` and `world/harvest_templates.py:29` name this file as their source. They mean v1.0. What they took, as shipped:

| What | Value | Where |
|---|---|---|
| Stage thresholds, game-hours | 12, 48, 96 (fresh → stale → rotting → skeleton) | `typeclasses/corpse.py:43` |
| A carcass crumbles at | 144 (96 + 48) | `:47` |
| A person's body crumbles at | 288 | `:273` |
| Season factor on the clock | winter ×0.5, summer ×2 | `:54` |
| Weather factor | raining ×1.5, snowing ×0.5 | `:55` |
| Cold-storage room flag | ×0.25 | `:109` |
| Meat, hide | SIZ // 2, SIZ // 3 | `world/harvest_templates.py:71`, `:78` |

The clock is game-time read on demand, with no ticker (`typeclasses/corpse.py:4–8`), which is where the code left v1.0. That it can run backwards is Cooking's to mend (E5, CP8).

---

## 6. Who owns what

This note owns **what a `Creature`'s body gives, and with which skill and tool it is taken**. What becomes of a part afterwards belongs to the note in the right-hand column.

| Subject | Owner |
|---|---|
| Meat's age, spoilage stages, the spoilage index | Cooking Design E3, E5, CP7, CP8 |
| Drying and smoking | Cooking Design CP11 and after |
| A quality on a harvested part | Cooking Design CP16, CQ10; Hunting Design TP12 |
| Fat as a part, its season, tallow | Rendering Design ZP1, ZP2, ZQ6 |
| The corpse's clock in a cellar | Storage Design DQ7; Cooking Design CQ9 |
| Fur's use | Textiles Design WP6 |
| Feathers' use; the bow's string | Projectile Design RWP22, RWP21 |
| Bark and water in tanning | BACKLOG *Tanning upgrade* |
| When and how an animal is met and killed; the snare | Hunting Design (TP1, TP11, TP12) |
| A creature's damage, death and `natural_ap` in a fight | Combat Design CE9, OQ-CE5 |
| Expiry that fires only on interaction | BACKLOG *Corpse expiry fires only on direct interaction* |
| What is carved from bone, horn and antler | series queue, *bone, horn & antler* |
| Birds | series queue, *fowling & wild birds* |
| Teeth, tusks and claws as ornament | series queue, *ornament & jewellery*, *predators* |

---

## 7. The rule for parts

**HTP1 — The template is the whole answer, and absence is the way to say no.** `compute_yield` floors every part at one unit (`world/harvest_templates.py:164`), so a part named in a template always gives something. A species that does not give a part therefore **does not name it**: the rabbit has no `fat` (Rendering ZP1 found this for fat; it is the rule for every part). A template belongs to one species, and a species has one SIZ figure in its prototype, so the author knows the yield when writing the entry. The floor stays. `AGENTS.md` §5 gains the sentence when the second template is written.

**HTP2 — A part says what kind it is.** Each entry gains `kind`, one of three, and the kind gives the entry's usual skill, difficulty and last harvestable stage:

| `kind` | Parts | Skill | Difficulty | Through |
|---|---|---|---|---|
| `flesh` | meat, fat | `hunting` | +20 | stale |
| `skin` | hide, fur | `craft` | 0 | stale |
| `hard` | bone, and later horn, antler, tooth, tusk, claw | `craft` | 0 | skeleton |

These are the shipped rabbit's three rows, named. An entry may still set its own `skill`, `difficulty` or `max_stage` — the book lets a hide from an odd beast be harder (§4) — and the checklist that today demands those keys (`AGENTS.md` §5) asks for `kind` instead. A fourth kind, `delicate`, waits for HTP8. Whether the keys are derived or merely checked against the kind is the decomposition's (HTQ2).

**HTP3 — No part enters a template before a sink names it.** The registry already marks a material with no sink as an orphan (`world/material_registry.py:87`, `:575`). The same test applies before the source is written: a part is added to a template in the commit that adds, or after, the recipe or act that consumes it.

**HTP4 — The parts, by what waits for them.**

| Part | Would come from | Sink | State |
|---|---|---|---|
| meat, hide, bone | the rabbit | food; leather (`world/recipes.py:192`); six recipes | **built** |
| fat | larger game | tallow | **owned** — Rendering ZP1 |
| fur | soft-furred animals | lining a garment | **owned** — Textiles WP6; registry `DATA` (`world/material_registry.py:203`) |
| feather | birds | fletching | **owned** — Projectile RWP22; waits for a bird |
| sinew | any animal | none open | **waits** — HTQ4 |
| tusk | boar | none | **waits** — registry orphan (`:226`) |
| horn, antler | deer and others | none written | **waits** — queue *bone, horn & antler* |
| tooth, claw | predators | none written | **waits** — queue *ornament & jewellery* |
| gut, blood, offal | any animal | none written | **waits** — HTQ5 |
| venom, chitin, scales | monsters | none; no alchemy | **waits** — §11 for scales as armour |

Sinew is the instructive row. The registry gives it the sink *bowstring* (`:224`), but the bow's recipe takes twine and says so — *"AD4: a fibre string, never sinew"* (`world/recipes.py:585`; Alpha Content Decomposition AD4) — and Projectile RWP21 restrings with twine. Its named sink is closed by a lock and filled by another material.

**HTP5 — What the next three species would give, under the rule.** An illustration, not a proposal for species — which animals exist is Hunting's and *predators*'.

| Species | Built kinds | Owned elsewhere | Waiting |
|---|---|---|---|
| Deer | meat, hide, bone | fat | antler |
| Boar | meat, hide, bone | fat | tusk |
| Wolf | meat, bone | fur (*Fur, Hide*, p. 122) — HTQ3 | tooth |

---

## 8. Skill and difficulty

**HTP6 — Two skills, by kind, until Craft is specialised.** `flesh` on `hunting`, `skin` and `hard` on `craft` (HTP2). Both are given at character creation, so no harvest is impossible by default (`world/harvest_templates.py:22–23`), and `AGENTS.md` §5 already flags any other skill (`:507`). The book's alternative — Lore (Animal) or Survival at Hard for a hide — is not proposed as a second route: there is no Lore skill, and `hunting` at −40 for a hide would make `craft` the better choice for almost everyone. It is recorded as HTQ6.

**Difficulty is the part's, and the species may shift it.** The grades are ours (§4). Larger or stranger bodies get a harder hide through the entry's own `difficulty`, which is what the book's *penalty for particularly odd beasts* is.

---

## 9. What the body shows

**HTP7 — A body shows what has been taken.** Today only `harvest <corpse>` lists a part as *already taken* (`commands/hunting_commands.py:420`); `look` adds the decay stage and nothing else (`typeclasses/corpse.py:236–239`). Proposed: one derived line on `look` — *it has been skinned*, *little is left but bone* — built from `db.harvested` and the template, with no write. MUME's butchered corpse is identifiable at a glance (§2.1).

---

## 10. Tools

**The knife, as shipped:** carried, +10, never required (`commands/hunting_commands.py:28`, `:433–436`). Whether a blade should be required for `skin` and `flesh` is HTQ7; it would be this note's only departure and is not proposed.

**HTP8 — The Anatomy Kit, when there is something delicate to take.** The book's kit exists to take parts *without contaminating them* and helps Heal tests (§4). Translated: an item tagged as the kit gives +10 on parts of kind `delicate` — organs, glands, anything whose sink is alchemy or magic — and on nothing else. It is a bonus, never a requirement. It has no price (`AGENTS.md` §1A). It waits for the first delicate part, which waits for a sink (HTP3), which waits for alchemy. Whether it stacks with the knife's +10, and which skill a delicate part uses when no healing skill exists, are HTQ8.

---

## 11. Hide armour and `natural_ap`

**HTP9 — The creature owns `natural_ap`; the body keeps the figure it died with.** After CE, the damage writer is the one reader of a creature's armour in a fight (Combat Design CE9). The copy on the body (`typeclasses/corpse.py:73`) is not a second owner: it is the hide's record, taken once at death, and the only reader it will have is the hide. Nothing changes; this is said so that no one adds a third place.

**HTP10 — Hide armour belongs to a later armour batch, and the book says when.** By the table, a creature of natural AP 1–5 gives armour of AP 1–2 (§4). The shipped leather and bone pieces already give 2 (`world/gear.py:217–225`). Deer (1), boar and wolf (2) and brown bear (3) are all in that first row, so hide armour made from any ordinary animal would equal what `leather` already makes. It starts to matter with the first creature of **natural AP 6 or more**, whose hide gives 3–4 — which is also where Gear's open question on wear rows for 3 AP and up closes (Gear Decomposition OQ-GR2). Until then the hide of a bear is `raw_hide`, more of it.

When that batch comes, the book gives it four numbers this note asks it to keep: **half** the creature's AP; taken within **48 hours** (the stale threshold, HTP-L2); a creature of **double the wearer's SIZ** for a full suit — a brown bear or a wyvern, average 26, for a wearer of SIZ 13, and a stag at 23 not quite; and nothing above natural AP 25. Three things it must decide are HTQ11–HTQ13: whether such a hide is its own item carrying species, AP and SIZ, against the one-`leather` rule (Gear GR11); what a creature with uneven armour gives (Combat Design OQ-CE5); and whether SIZ is read from the body or from the count of hides.

---

## 12. A person's body

`harvest` refuses a person's body: *"That is no quarry, but what remains of someone"* (`commands/hunting_commands.py:241–249`). That was built to stop the body reading the rabbit's template (BACKLOG *`harvest` treats a player's body as a rabbit*, done 2026-10-20), not as an answer to whether a person may be harvested. **This note proposes no change** and asks the question once, as HTQ9, with what stands against opening it now: the body holds the dead character's belongings for 288 game-hours, so making it a resource as well gives a reason to kill; the rules for when a character may be attacked are designed and not yet built (Combat Design PV1–PV3); and the book's one use for a large hide needs a creature of double the wearer's SIZ, which a person is not.

---

## 13. Economy

**Yields under today's divisors** (fat at Rendering's proposed SIZ // 6):

| Body | SIZ | meat | hide | bone | fat |
|---|---|---|---|---|---|
| Rabbit, as shipped | 4 | 2 | 1 | 1 | — |
| Rabbit at the book's scale (Combat Design OQ-CE1) | 2 | 1 | 1 | 1 | — |
| Boar, wolf | 10 | 5 | 3 | 2 | 1 |
| Stag | 23 | 11 | 7 | 5 | 3 |
| Brown bear | 26 | 13 | 8 | 6 | 4 |

Two things the table shows:

- **OQ-CE1 costs one portion of meat.** Moving the rabbit from SIZ 4 to 2 halves its meat and changes nothing else, because hide and bone are already at the floor. The harvest is not a reason to keep SIZ 4; whether one portion per rabbit is enough to live on is Cooking's and the survival loop's to say (HTQ1).
- **The first large animal multiplies hide.** One stag gives seven `raw_hide`; leather takes two (`world/recipes.py:192`). A stag is three leathers where three leathers today are six rabbits. That may be right — a hide is an area, and the book counts hide by SIZ — but it should be chosen, not found (HTQ1).

**Sources:** parts, as §7. **Sinks:** each part's own (HTP3); the clock on the body; the fumble. **Services:** dressing game for a hunter who cannot carry it or lacks the craft; skinning to order. **Coin:** none proposed. **Logging:** `gather`, as shipped; a kill is Hunting's (D8, TQ10). **Ledger:** every new part gets its source and sink row in the commit that adds it.

---

## 14. Multiplayer and server load

- **One taker per part.** The slot is claimed before anything is spawned (`commands/hunting_commands.py:312`), on a single-threaded reactor, so two harvesters cannot both take the meat. With large game this becomes a social fact: eleven portions go to whoever cuts first. Sharing a carcass is a matter between players today; taking part of a part is HTQ14.
- **A large take is a burst of objects.** A bear's meat is thirteen spawns in one command, twenty on a critical. They stack on the harvester or are set down at the feet past the carrying limit (`:330`). No ticker, no per-part object before the take.
- **Nothing ticks.** The body's stage is read on demand (§5.2). A body nobody touches lingers (BACKLOG *Corpse expiry fires only on direct interaction*).
- **Ten harvesters, ten bodies** cost ten skill checks and their spawns; the 30-second cooldown is per character.

---

## 15. Immersion extras

- The room line for a harvest names the part (`commands/hunting_commands.py:340`); a large take could say how the harvester is laden.
- A body's `look` line by kind and stage (HTP7): *skinned and stripped*, *picked to the bone*.
- A fumble on a `skin` part could leave a torn hide rather than nothing — a lesser item, which HTP3 forbids until something wants one.

---

## 16. Layers — a suggested order

1. **With the next code commit that touches the file:** correct the docstring in `world/harvest_templates.py` (BACKLOG entry). No behaviour.
2. **With the second species** (Hunting's deer): its template under HTP1; `kind` (HTP2) and the `AGENTS.md` sentences in the same change; fat if Rendering's ZP1 is ready. Settle HTQ1 first.
3. **Any small session:** the body's `look` line (HTP7).
4. **As sinks arrive:** each waiting part of HTP4, in the commit of its sink.
5. **With alchemy:** `delicate` parts and the Anatomy Kit (HTP8).
6. **With an armour batch that has a creature of natural AP 6+:** hide armour (HTP10).

---

## 17. Seams in today's code (read at `500424c`)

- **Template:** `world/harvest_templates.py:66–90` (rabbit); part keys `:55–61`; `compute_yield` `:142–167`, floor `:164`; critical multiplier `:49`; stage constants imported from the corpse `:47`.
- **Command:** `commands/hunting_commands.py` — `CmdHarvest` `:176`; aliases `:196`; refusal of a person's body `:241–249`; taken-once `:274`; decay gate `:280`; the roll `:287–292`; yield `:307`; claim `:312`; set down `:330`; `gather` `:378`; listing `:410–431`; knife `:433`; constants `:27–28`.
- **Corpse:** `typeclasses/corpse.py` — thresholds `:43`; expiry `:47`; factors `:54–55`; cold-storage flag `:109`; `creature_siz` and `creature_natural_ap` `:72–73`; `decay_stage` `:141`; `crumble` `:171`; `return_appearance` `:236–239`; `PlayerCorpse` expiry `:273`.
- **Creature:** `typeclasses/creatures.py` — `siz`, `natural_ap`, `harvest_template` `:48–50`; `natural_ap` "reserved" `:13`; `at_death` `:61`; the copy to the body `:104`.
- **Registry:** `world/material_registry.py` — `raw_hide` `:197`, `fur` `:203`, `bone` `:210`, `sinew` `:220`, `tusk` `:226`, `feather` `:232`; `tallow` unratified `:481–483`; orphans `:575`.
- **Recipes and gear:** `LeatherRecipe` inputs `world/recipes.py:192`; the bow's string `:585`; armour rows `world/gear.py:217–225`.
- **Agent rules:** `AGENTS.md` §1A (no prices), §3.4 (creature prototype, `:354–366`), §5 (template schema `:463`, checklist `:506–508`).
- **One false sentence, in code:** `world/harvest_templates.py:19–20` credits *Arms of Legend* with meat on Survival at Easy (§4).
- **Four citations of this file's name** that now resolve: `typeclasses/corpse.py:10`, `world/harvest_templates.py:29`, `docs/PolishedWorld_Hunting_Decomposition.md:31`, `:175`. Lesson 493 records the time they did not.

---

## 18. Open questions

- **HTQ1** — The divisors for large game, and the rabbit's SIZ. Does a stag give seven hides and eleven portions, or do the divisors grow with SIZ? And does the rabbit's meat fall to one if Combat Design OQ-CE1 moves its SIZ to 2? *Leaning: keep the divisors linear, since the book counts a hide by SIZ; decide with the deer's template and Cooking's restore figures on the table, not before.*
- **HTQ2** — Is `kind` the source of `skill`, `difficulty` and `max_stage`, or a label the checklist tests them against? *Leaning: a label that is checked; the three keys stay explicit, as the command reads them today.*
- **HTQ3** — Does a wolf give `fur` or `raw_hide`? The registry keeps them apart and says a large animal may give both (`world/material_registry.py:493–495`); the book says *Fur, Hide*. *Open; Textiles' to answer with WP6.*
- **HTQ4** — Sinew. What does it do that twine does not, and is AD4 lifted for it? *Leaning: nothing until a bow note proposes a string that differs in play (queue, bowyery & fletching); the registry's `DATA` entry stays as it is.*
- **HTQ5** — Gut, blood and offal. Food on Cooking's clock, casings, strings? *Open; no sink is written anywhere. Offal as food is the nearest, and is Cooking's.*
- **HTQ6** — The book's second route for a hide (Lore (Animal) or Survival, Hard). *Leaning: not built; one skill per part.*
- **HTQ7** — Should `skin` and `flesh` parts need a blade? *Leaning: not before the newcomer's first hour is checked with a character who has no knife (Newcomer Design); it would be a departure.*
- **HTQ8** — The Anatomy Kit: does its +10 stack with the knife's, and which skill takes a delicate part? *Open; waits for alchemy.*
- **HTQ9** — May a person's body be harvested? Asked because the note's boundary is the `Creature` class and Adam raised it (2026-11-25). What must be answered first: when a character may be attacked at all (Combat Design PV1–PV3); what the body's belongings and the 288-hour window become; whether it is open to all, tied to who the harvester is (MUME) or costly (Wurm); and what it would give that has a sink. *Leaning: stay refused, as built.*
- **HTQ10** — A thinking creature that is not a character — the minotaur is a `Creature` with a template like any other. *Leaning: the template decides; a species the world should not see skinned is given no template.*
- **HTQ11** — Is a hide meant for armour its own item, carrying species, natural AP and SIZ, or `raw_hide` × n? It pulls against one `leather` (Gear GR11) and the registry's rule against fragmentation. *Open; the armour batch's.*
- **HTQ12** — A creature whose armour differs by location (Combat Design OQ-CE5): which figure does its hide carry? *Open.*
- **HTQ13** — "Double the wearer's SIZ": read from the body, or expressed as a number of hides? *Open.*
- **HTQ14** — May a part be taken in portions, so that two harvesters share a stag? *Leaning: no; players share what is taken.*

---

## 19. Considered and not proposed

- **v1.0's own d100 roll, its decay ticker and its `world/harvesting/` package.** The shipped code uses `world/skillcheck.py`, reads the clock on demand and keeps templates in one module. v1.0's status note already said so.
- **v1.0's skills** (`survival`, `craft_butchery`, `lore_animal`, `heal`, `lore_alchemy`). None exists; §8.
- **Five quality tiers** (poor to masterwork, by skill value). The project has four bands from the craft roll (`world/crafting_quality.py`), and a part's quality is Cooking's and Hunting's question (§6).
- **The *Harvest Difficulty by Part Type* table as a book rule.** It is not in the book (§4).
- **Prices.** `AGENTS.md` §1A.
- **The full catalogue** — eyes, hearts, livers, essence, spirit residue, silk glands. Twenty parts and no sinks (HTP3).
- **Per-part preservation times.** One clock, on the body and then on the food (Cooking CP7–CP8).
- **Combat kills as the source.** A creature that dies of damage and one felled by `hunt` leave the same body, through `Creature.at_death` (Combat Design HQ2; `typeclasses/creatures.py:61`).
- **v1.0's figures for the wolf and the giant spider** (SIZ 8; SIZ 12, AP 4). The book's wolf is SIZ 2D6+3 (p. 122).
- **A skill gate per creature.** §2.6.
- **A dedicated `butchery` or `skinning` skill.** Two skills cover three kinds until Craft is specialised for every craft (§8).
- **Template inheritance for variants.** One species, one template (HTP1); a shared template is what makes the floor of one unit a problem.
- **A torn hide, a cracked bone.** Lesser items with nothing to consume them (§15).
