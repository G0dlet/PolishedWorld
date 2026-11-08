# PolishedWorld — Farming & Livestock Design Notes (fields, seed, herds, pasture)

> **Rev 2 · 2026-11-08** — moved, docs only, with roadmap Rev 60, BACKLOG Rev 85 and README Rev 39: from `docs/` to `docs/system_designs/`, together with the fourteen other one-system design notes and the series handoff, `docs/system_designs/HANDOFF.md`. The *Canonical* line and every path to a design note outside a Rev line now name the new folder; no content changed. Rev lines keep the paths they were written with, since changelog lines are left exactly as written.
> **Rev 1 · 2026-11-07** — first version, docs only, with roadmap Rev 51, BACKLOG Rev 73 and README Rev 29. Written from a design chat, the sixth in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`, `docs/PolishedWorld_Housing_Design.md`, `docs/PolishedWorld_Hunting_Design.md`, `docs/PolishedWorld_Cooking_Design.md` and `docs/PolishedWorld_Temperature_Design.md`. Nothing in farming or livestock is shipped, so the notes change no live behaviour; they name the shipped seams they would read and the materials they would give a source or a sink. **Nothing here is locked.** Every numbered item is a proposal (GP…), a goal (GG…) or an open question (GQ…); the letter is for *gård*. In the chat Adam approved writing the document from the proposal; the leanings under GQ1–GQ7 are the ones proposed in the chat, recorded as *leanings*, not as decisions. Prior art was read on 2026-11-07; code seams were read against `main` at `63d9d7d` (Evennia 6.1.0).
> **Canonical:** `docs/system_designs/PolishedWorld_Farming_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/roadmap.md`, parallel backlog, *Food professions — farming · fishing · livestock* — the entry gains a third 2026-11-07 annotation (Rev 51) and is not replaced by this document. The entry's rule stands: the exclusive products of all food sources are decided **once**, in that entry, across fishing, farming and livestock (§11 proposes this design's half). `docs/BACKLOG.md` gains one note (Rev 73) on *Seasonal supply & population memory* part (1): the growing index proposed here (GP2) is a candidate clock for the wild plant nodes' seasonal regeneration.
**When to read:** at the food-professions exclusives decision; at the start of a farming or livestock decomposition; when Cooking Design CQ9's weather-history change is decomposed (the growing index is a third counter on the same script, GP2); when Housing Design §7's parts list is decomposed (barn, granary, larder, §13); with *animal taming* (the founding flock, GP8) and with *disease & herbalism* (GP13) from the design-series queue; with the metallurgy epic (shears and the scythe, GP6, GP11).
**Departs from the roadmap note in two places**, both refinements: growth is read from a global, monotone **growing index** stamped at sowing rather than from a raw `planted_at` timestamp (GP2), and the note's "linen to farming" becomes *fine* linen from farmed flax while foraged fibre keeps today's cloth chain (GP7, GQ2). Everything else the note settled — never tick, one `FarmPlot` owning a slot dict, one `Pen` holding the herd as an aggregate, the skill check at harvest, fertility and fodder as sinks, livestock last — is kept.

---

## 1. The idea in one paragraph

A field is a place in the world that a farmer works and a passer-by can read. In early spring the farmer breaks the ground with a digging stick and sows grain from last year's harvest — grain that could have been bread. The field turns green, then stands in ear, then gold; anyone walking past sees which, and a farmer sees more: how heavy the ears are, whether the soil is tiring. Weeding helps but is never a chore on a clock. When the grain is ripe it stands for days before it starts to fall and go to seed, so a farmer who has a life outside the game loses a little, never everything. The harvest is grain, straw and next year's seed; the grain is ground on milling stones into flour and baked over a fire. Beside the fields a herder keeps sheep on a pasture that feeds them in the green months; in winter they eat the hay that was made on clear summer days, and lambs come in spring. The sheep give milk after lambing, wool once a year, dung for the fields, and in the end meat, hide and a fleece-on skin for a winter cloak. Nothing is bought from an NPC: the first seed is gathered wild and the first sheep are caught.

---

## 2. Prior art

### 2.1 Wurm — the lesson

Sources: Wurmpedia (`wurmpedia.com`, pages *Farming*, *Crop*, *Guides:Farming Tips*, *Animal husbandry*) and the Steam community forum for Wurm Unlimited (discussion 3182216552781275839, *Farming, possible with a limited schedule on a 24/7 server?*, October 2017). Paraphrased:

- Crops take several real days to grow; tending a field with a rake about once a real day removes weeds and adds to the yield, and the farming skill raises quality and yield.
- Soon after a crop is fully grown it turns to weeds, and the guide tells players to check their fields every day.
- In the Steam thread a player describes sowing, sleeping and logging in to find every field gone to weeds; another says that for anyone with a job and a family, getting online often enough to harvest in time is close to impossible. Server owners lengthened the stages to make it bearable.
- A higher farming skill shows more of a field at a distance: at 15 the crop and whether it needs tending, at 20 its growth stage, at 60 the yield to expect.
- Animal husbandry: an *inspect animal* view shows hunger and whether an animal can be bred or groomed, and from skill 50 whether it is ready to be sheared or milked; a starving cow gives no meat when butchered and a fat one gives extra; grooming lowers the risk of disease; the number of animals a character can *care for* grows with the skill.

**Worth taking:** a field and a herd read in words, with more visible as skill grows; tending that improves a yield; condition that changes what a slaughter gives.
**Not for PolishedWorld:** a crop lost to a single absence. **The lesson (the series' "Achaea lesson"):** a field or a herd that punishes the owner for being away overnight is not a farm, it is an attendance check, and it selects for players with no life outside the game. In PolishedWorld no crop and no animal is lost in a moment while its owner is away; loss is a slope measured in real days, and the worst outcome of a missed week is a smaller harvest or a thinner flock (GG2).

### 2.2 Avalon — the meadow

Source: Avalon RPG's help page *Livestock* (`avalon-rpg.com/help/pages/livestock`; Avalon is a MUD running since 1989). Paraphrased:

- Livestock is kept on a lush meadow that feeds it in the background. A meadow that is overpopulated can be eaten down past the point where it regrows in spring.
- When the meadow is bare the animals starve slowly; at a dire stage an animal breaks away and roams in widening circles, trampling any field it finds edible; starvation also slows breeding afterwards.
- A trough (outdoors) or a manger (indoors), filled with straw or hay, stands in for the meadow for small herds and prized animals; it holds far less than a meadow.

**Worth taking:** the pasture as the herd's food in the growing season, so that a herder is not a feeder; overgrazing as the herder's real sink; hay in a trough for winter and small herds; slow starvation (GP9, GP10).
**Not for PolishedWorld:** none of it is ruled out; the trampled field waits for a reason to exist (§17).

### 2.3 A Tale in the Desert — seed or fibre, and the pen

Sources: A Wiki in the Desert (`atitd.wiki`, pages *Flax*, *Growing Flax*, *Flax Seeds*, *Rotten Flax*, *Sheep Pen*, tales 8–11). A Tale in the Desert has a player-run economy, which makes it the closest match to pillar 1. Paraphrased:

- A flax bed that is weeded on time yields flax; one left unweeded *goes wild* and yields seed. The choice between fibre and next year's seed is made by how the bed is tended. Harvested flax is rotted in water, combed and spun. Players breed new flax strains and hand seed out freely in chat.
- The weeding windows are measured in seconds, and the game added hotkeys for weeding and harvesting.
- A sheep pen is a building (boards, bricks, dried flax). Sheep in it breed while there is at least one male and one female, eat sheep food made from onions loaded into the pen, produce dung, die eventually if not fed, and stop breeding at ten or more. Sheep can be sheared in the pen and slaughtered there for leather, mutton, oil and wool. A contagious pox once killed sheep until a cure made in a kitchen was developed.

**Worth taking:** seed versus product as the farmer's choice; the pen as an aggregate with a breeding rule, a feed store, dung and a cap; disease as a sink with a crafted answer.
**Not for PolishedWorld:** tending windows of seconds — a reaction test, the opposite of reading signs (GG4).

### 2.4 Haven & Hearth — seed lines

Source: Ring of Brodgar wiki (`ringofbrodgar.com`, *Farming*, *Legacy:Farming*, *Crops*). Paraphrased: a harvest's quality starts from the quality of the seed planted and moves a few points up or down, softcapped by the farmer's skill and the soil; byproducts such as straw take the seed's quality; because each crop has a chance to give slightly better seed, planting only the best seed raises a line's quality over generations. Wild plants found by foraging give the first seed.

**Worth taking:** seed as the farmer's capital, carrying quality from one year to the next (GP4); the first seed from foraging (GP4).
**Not for PolishedWorld:** quality as an open-ended number chased for years; PolishedWorld's quality is the shipped four-band scale (`world/crafting_quality.py:35–43`).

### 2.5 Vintage Story — fertility and cold

Source: the Vintage Story wiki (`wiki.vintagestory.at`, *Farming*, *Crops*, *Fertilizer*). Paraphrased: farmland holds three nutrients and each crop draws one; fallow land recovers faster than planted land; saltpeter, potash and bonemeal restore nutrients; rotation and a fallow quarter are the standard practice. Crops grow more slowly below 10 °C and stop at 0 °C.

**Worth taking:** fertility as a field's sink, restored by fallow time and by goods (GP5) — two of whose goods, saltpeter and bonemeal, already exist or are registered in PolishedWorld; growth that the season and frost stop (GP2).
**Not for PolishedWorld:** three nutrients — in text, one word for the soil carries the decision (GQ7).

### 2.6 Old School RuneScape — offline disease and paid protection

Source: the Old School RuneScape wiki (`oldschool.runescape.wiki`, *Farming*, *Farming skill*). Paraphrased: crops grow on real-time timers while the player is logged out, and may become diseased while the player is away; disease is answered by compost made from weeds and unwanted produce, or by paying an NPC gardener near the patch, in produce, to watch the crop.

**Worth taking:** growth that does not need the player present (GG3); compost as a sink for waste.
**Not for PolishedWorld:** the NPC gardener (pillar 1) — a neighbour paid in grain to look after a field is the player version, and a service (§11); disease that can strike an absent owner's crop at full loss (GG2).

---

## 3. Design goals

- **GG1 — Read in words.** Fields, pastures and herds show their state in words on `look` — *green*, *in ear*, *ripe*, *going to seed*; *fat*, *lean*, *thin* — never as numbers (the `ResourceNode._availability_phrase` precedent, `typeclasses/resources.py:129`). Skill shows more, never a number (GP14).
- **GG2 — No loss in a moment.** Nothing is lost while its owner is away overnight; every loss is a slope of real days that the owner can read and answer (§2.1).
- **GG3 — The world grows while you are gone.** Fields grow and herds graze without the owner; being away costs only what was not tended.
- **GG4 — Skill in choices, not reflexes.** When to sow, which seed to keep, when to let a field lie fallow, how many sheep a pasture carries, whether hay is made — never a timing window.
- **GG5 — Seed is capital.** What is eaten cannot be sown; the trade-off between food and next year is the farmer's (the roadmap entry's seed-vs-food sink).
- **GG6 — Every source a sink.** Fertility, fodder, seed and condition are spent by use, and nothing is created that is not later consumed (pillar 1; the roadmap entry's "or it is a faucet").
- **GG7 — Lazy and global.** No ticker per field, slot or animal. State is derived on read from anchors and from global indices advanced by the one weather script (KG7's spirit; *Lazy evaluation over tickers*).
- **GG8 — Two professions that need each other.** The farmer's straw, hay and grain feed the herder's animals; the herder's dung feeds the farmer's soil; both need the potter, the woodworker and the miller.

---

## 4. Legend alignment

**Rules as written:**

- **Professions** — Legend core p. 21: the **Farmer** (Barbarian, Civilised, Primitive) takes Athletics, Brawn, Driving, Lore (Regional) and Resilience as common bonuses and *"Craft (Farming)"* as its advanced skill; the **Herdsman** (Barbarian, Nomad, Primitive) takes First Aid, Lore (Regional), Resilience and Sling, and Survival as its advanced skill; the **Animal Trainer** takes Driving, First Aid, Lore (Regional), Persistence, Resilience and Riding.
- **Craft (DEX+INT)** — pp. 57–58: several separate skills under one heading; a critical *"allows the item being crafted to be of superior quality"* in durability, value or utility; a fumble halves the item's armour and hit points and its value.
- **Lore (INT×2)** — p. 52: Lore (Regional) is the common skill for the geography, flora and fauna of the land a character grew up in; p. 40's difficulty table makes recalling which plants are edible in farmland an Easy (+40 %) Lore (Regional) test. Advanced Lore must be trained with a teacher (p. 71).
- **Rolling in secret** — p. 39: the Games Master may roll for a character and reveal the result only through play.
- **Equipment** — the scythe, a grain-harvesting tool usable as a weapon (p. 118; AoL `:444`, ENC 2, 30 SP); milling stones that grind grain to powder (AoL `:348`, ENC 2); yarn spun from goat, lamb or yak wool (AoL `:522`).
- **Animals** — the mounts and beasts of burden table (p. 120): ass, donkey, horses, ox, cow, chickens, ducks, geese, pig, goat, with prices and ENC carried. AoL's animal chapter: an untrained animal is trained like a construction project with Lore (Animal), *"The Task Round is two weeks"*, each 25 % a level (`:2811`); goats for milk, meat and some wool (`:2845`); pigs eat anything, kitchen leftovers included (`:2873`); sheep for wool and meat, kept in large flocks with dogs (`:2885`); the livestock farmer's milk, cheese, wool and meat (`:3026`); the shepherd (`:3108`). *Monsters of Legend* p. 107: cattle (STR 4D6+6, CON 2D6+9, SIZ 2D6+9), applicable to cows and oxen.
- **Bless Crops** — p. 179: a priest's spell that guarantees a harvest for a year whatever the weather.

**Translation proposals:**

- **GP-L1 — `farming` is Craft (Farming), as a custom skill.** DEX+INT like Craft; a custom skill on the precedent of `hunting` (`typeclasses/characters.py:443–455`, chargen `world/chargen.py:59–65`) rather than a recipe discipline of `craft`, because sowing, tending and reaping are acts on a place, not recipes. Improvable on use like the other two (`typeclasses/characters.py:892`). GQ1.
- **GP-L2 — `husbandry` is Lore (Animal).** INT×2, Lore's base; AoL makes Lore (Animal) the skill that trains animals (`:2811`), and the herder's reading of a flock is knowledge (GP14). Named for the work, as `hunting` was. GQ1 asks whether one skill should cover both.
- **GP-L3 — Legend's craft resolution at the reap.** The roll is made when the crop is reaped or the animal shorn, not when it is sown: critical lifts the harvest a quality band, fumble halves it (the roadmap entry's rule, unchanged).
- **GP-L4 — Lore (Regional) stays unmodelled.** The codebase has no Lore (Regional); wild seed and wild grain are found with `forage` as wild food is today.
- **GP-L5 — Training is taming's.** AoL's two-week Task Round belongs to the *animal taming* system in the queue; livestock starts with an animal in a pen (GP8).
- **GP-L6 — Bless Crops is recorded for magic.** It is a reader of the growing index (GP2) — a field that ignores weather — and waits for the magic system's economy half.
- **GP-L7 — Legend's prices are not used.** Nothing is sold by NPCs (pillar 1); the table's ENC carried values are for *mounts, pack animals and caravans* in the queue.

---

## 5. The loop

Proposed phases, fields first.

1. **Find seed.** `forage` in a wild meadow finds ears of wild grain (the registry's planned grain/dry-grass node, `world/material_registry.py:153–158`) — grain to eat or sow, and straw.
2. **Break the ground.** On a field slot the farmer owns or is lent, `till` with a digging stick (a timed act).
3. **Sow.** `sow <grain> in <slot>` consumes seed; the slot stamps the growing index (GP2).
4. **Tend.** `tend <slot>` weeds it; once per growth stage it adds to the yield; skipped, the field is weedy and gives less (GP3).
5. **Reap.** When ripe, `reap <slot>` with a sickle — a timed act and the skill roll (GP-L3) — gives sheaves; `thresh` gives grain and straw.
6. **Keep or spend.** Keep the best grain as seed; grind the rest on milling stones; bake, brew, feed or sell it. Let the slot lie fallow, or spread dung (GP5).

And the herd:

1. **Stock the pen.** Animals caught and tamed elsewhere are put in a pen on a pasture (GP8).
2. **Let them graze.** In the green months the pasture feeds them (GP9). Make hay on clear days and fill the trough before winter.
3. **Read the flock.** `look flock` shows condition in words; skill shows who is in lamb, who is sick (GP14).
4. **Take what it gives.** Lambs in spring; `milk` after lambing; `pluck` (roo) the fleece at the summer moult; `muck out` the pen for dung; `slaughter` the surplus (GP11, GP12).

What it reads like (illustrative, not a spec):

```
> look
East Field
...
The barley stands in ear, bending a little in the wind. Weeds have crept in between the rows.
> tend barley
You work along the rows, pulling weeds...
The barley rows are clean again.
> e
Long Pasture
...
A flock of sheep grazes the short grass. They are in good flesh.
The grass is bitten short near the gate.
> look flock
Eleven sheep: seven ewes, a ram and three lambs. Two of the ewes are heavy with lamb.
The trough is half full of hay.
```

---

## 6. The field — where crops grow

**GP1 — A field is an authored plot holding one `FarmPlot`.** Fields are authored rooms placed by the versioned seed (`world/seed_data.py` `ROOMS`, line 79), the rule Housing Design BP4 gives every plot. Each field room holds one `FarmPlot` object (the roadmap entry's name) owning a slot dict — one attribute to version, one lock, one `at_object_delete` — with `get:false()` like a `ResourceNode` (`typeclasses/resources.py:61`). A slot records its owner (or lessee), crop, seed quality, the growing index at sowing, stages tended, fertility and a stage word last shown. No fields outside authored areas until Stage 6 decides resources-as-data (wilderness rooms are recycled and keep Tags and Attributes, Evennia Reference §14.5). Who owns a slot is GQ4.

**GP2 — A growing index, beside the spoilage and drying indexes.** The global `WeatherScript` already wakes every 1800 s (`typeclasses/scripts.py:112`, `:135`). Proposed: it advances a third monotone counter, the **growing index**, by *season factor × weather factor* for the elapsed interval — in growing days, so a full day of summer growth adds one. Season: spring and summer 1, autumn ½, winter 0 (`world/gametime_utils.py:56–61`); weather: snowing 0, every other state 1 (`world/weather.py:23–33`; droughts wait for *Weather inertia*). A slot stores the index at sowing; its progress is *index now − index at sowing* against the crop's need. Reading is O(1), the clock never runs backwards (Cooking Design CP8's argument), offline time is free, and a winter-sown slot simply waits — autumn sowing that ripens in spring falls out of the same rule. This is a refinement of the roadmap entry's `planted_at`: a timestamp counts winter as growth; the index does not. Cooking Design CQ9 asks for one weather-history change for its indexes and Hunting's history; this counter belongs in that change.

**GP3 — Ripe stands; then it goes to seed; never all at once.** Four stages are shown in words: *sown*, *green*, *in ear*, *ripe*. Past its need the crop stands ripe for a further span on the same index (roughly one real week of summer), then *goes to seed*: each further span moves part of the yield from grain to seed scattered and lost, until the slot reads *gone to seed and weeds* and gives a little seed and straw. Winter pauses this as it pauses growth. **Tending** (`tend <slot>`) is once per stage and adds one to the yield for each stage it was done in, as in Wurm (§2.1); a missed stage only loses that one. Nothing ever empties a slot overnight (GG2). The spans are GQ3.

---

## 7. Seed, soil and tools

**GP4 — Grain is seed; seed carries quality.** The first seed is wild grain from `forage` (§5) — the registry's planned grain/dry-grass node, which also gives straw. A harvest of a grain crop gives grain, and that grain is both food and seed: the trade-off is literal (GG5). Grain carries `db.quality` on the shipped four-band scale; a harvest's quality starts from the seed's and moves by the reap roll (GP-L3), softcapped by the farmer's skill (Haven & Hearth, §2.4). Keeping the best grain as seed is how a line improves; a farmer known for good seed has something to sell. A crop that needs separate seed (flax) gives seed only from a slot left to go wild, the ATITD choice (§2.3).

**GP5 — Fertility: one word for the soil.** Each slot has a fertility 0–100 shown in words (*rich*, *good*, *tired*, *spent*). A harvest draws it down by the crop's draw; it recovers on the growing index, faster while the slot lies fallow; yield scales with it. Goods restore it at once: **dung** from a pen (GP12), **bonemeal** — bone ground on milling stones (`world/prototypes.py:928`, `:857–871`) — and **saltpeter**, whose only registered sink today is blocked black powder (`world/material_registry.py:171–176`). One number, not three nutrients (GQ7).

**GP6 — Tools before metal.** A digging stick (a stick, `world/prototypes.py:203`) to `till`; a flint sickle (flint, stick and twine — flint's only sinks are the stone axe and an intended fire-starting use, `world/material_registry.py:135–140`) to `reap`; reaping by hand works at the shipped improvised-tool penalty (`improvised_penalty`, `_tool_modifier`, `world/crafting_base.py:99`, `:190`). The iron scythe (Legend p. 118, AoL `:444`) and shears wait for metallurgy, whose first epic makes metal tools (roadmap decision of 2026-11-07). Tools wear on use like every other tool (`apply_wear`, `typeclasses/durable.py:43`).

---

## 8. What the field gives

**GP7 — Grain, straw and fine linen.**

- **Grain** (a generic `grain` tag first, species as flavour, the provisional rule wood follows, registry note 10) → **flour** on milling stones, which today have no sink (`world/prototypes.py:857–871`) → **flatbread** over Cooking's fire, **porridge** in a pot (Cooking Design CP6). Grain is also fodder (GP9) and, later, malt for the taverns of *markets & taverns* in the queue. Dry grain keeps for a long time on Cooking's freshness clock; that it stores is part of what makes it farming's own product (§11).
- **Straw** from threshing gives the registry's straw its source (`world/material_registry.py:153–158`, note 4 at `:500`): the straw hat, whose prototype has no recipe (`world/prototypes.py:615`), thatch for Housing's roof repair (Housing Design BP14), bedding and trough fodder (GP9).
- **Flax** (slice 2) → retted in water → combed → **fine linen**. Today's cloth comes from foraged plant fibre (`world/prototypes.py:155–167`; `ClothRecipe`, `world/recipes.py:161`). Proposed: foraged fibre keeps today's chain, and farmed flax makes a better grade of linen rather than replacing it — the roadmap note's "linen to farming", refined so that no shipped recipe loses its source (GQ2).

---

## 9. The herd

**GP8 — The first animals are caught, not bought.** No NPC sells an animal (pillar 1). The founding animals come from a wild flock's range (Hunting Design TP8) by live capture and taming — the *animal taming* system in the queue (GP-L5). Livestock starts at the gate of the pen; how many founding animals exist, and whether staff seed a wild range for them, is GQ5.

**GP9 — The pen holds the herd as one aggregate; the pasture feeds it.** A `Pen` object in an authored pasture room keeps the herd as counts and a state — species, females, males, young, condition, trough fodder, anchors — never one object per animal (the roadmap entry's rule; ATITD's pen, §2.3). The pasture's **grass** is a stock in the room, regrowing on the growing index (GP2) up to a cap, and eaten per head per game day; while grass lasts the herd needs nothing from the herder (Avalon, §2.2). When grass is short the trough is drawn on — hay, straw or grain the herder put in. Hay is grass cut and dried on Cooking's **drying index** (Cooking Design CP11), so it is made in clear weeks and spoiled by rain on the swath: *make hay while the sun shines*. Overstocking eats the grass below its regrowth and the pasture reads *bare* for a season — the herder's sink and the roadmap's density pressure. Both stocks are brought up to date on read, piecewise between anchors, with long gaps summarised (GQ8).

**GP10 — Condition is a ladder in words, at game-week pace.** *Fat*, *in good flesh*, *lean*, *thin*, *starving*. A shortfall of food moves the herd down one step per span of game days; full feeding moves it back up. Each step costs something before any animal dies: *lean* stops milk and slows wool; *thin* stops breeding (Avalon's slowed breeding); *starving* sustained beyond a span longer than a real week kills one animal at a time, the weakest first. Slaughter reads the step: a fat animal gives extra meat, a thin one less (Wurm, §2.1). A herder who misses a winter week finds a thin flock, not an empty pen (GG2).

**GP11 — The flock's year.** With a male and a female and condition at *in good flesh* or better, the pen gains young once, in spring, capped by the pen's capacity (ATITD's cap, §2.3); young are adults by the next spring. **Milk** comes from females in milk after lambing, accrued per game day up to what one milking can take — uncollected milk is milk not made, not a loss — and spoils fast on Cooking's clock, which is why butter and cheese are its preservation (hard cheese needs salt, Cooking Design CQ5). **Wool** is taken once a year at the summer moult by plucking (rooing) by hand — no metal — and a fleece not taken in the moult sheds onto the pasture; shears (metallurgy) later take it at any time in the warm season and take more. Wool → yarn on a spindle (`world/material_registry.py:323–328`, `:378–382`) → the dormant wool tunic (`world/recipes.py:625`, warmth 2, `world/prototypes.py:582–592`). **Slaughter** goes through the shipped corpse and harvest pipeline with new templates per species (`world/harvest_templates.py:66`): meat, bulk hide, bone, and a **fleece-on sheepskin** that counts as `fur` under the registry's rule for soft-furred animals (`world/material_registry.py:203–209`, note 1) — a source for the dormant fur cloak (`world/recipes.py:626`, warmth 3).

**GP12 — Dung closes the loop.** The pen accrues dung per head per game day up to a cap; `muck out` collects it and spreading it on a slot restores fertility (GP5). Straw and hay go from field to pen, dung from pen to field — the two professions' trade (GG8). Later species keep the shape: fowl in a coop lay eggs in the warm seasons; pigs eat kitchen leftovers and food Cooking calls *turning* or *spoiled* (AoL `:2873`), a sink for waste.

---

## 10. Sickness and reading

**GP13 — Disease scales with crowding and condition.** On each read, a herd's chance of falling sick grows with heads against pen capacity and against what its keeper's `husbandry` can watch (Wurm's care-for cap, §2.1), and with poor condition. A sick herd reads so, gives no milk or wool, and loses condition faster; it is answered by thinning the herd and, later, by a cure from *disease & herbalism* (ATITD's pox and kitchen-made cure, §2.3). Crop blight is the same idea for monoculture and waits (§17).

**GP14 — Skill reads more, in words and in secret.** Anyone sees a field's stage and a flock's condition. A `farming` reader also sees the soil's word, the weeds, and a word for the yield to expect; a `husbandry` reader sees who is in lamb, a sickness a stage early, and whether the grass will last the month — the Wurm ladder (§2.1) as words. The extra lines come from a roll made in secret (Legend p. 39): a failure shows nothing extra, a fumble a wrong word. The same pattern Hunting Design TP2 uses for signs.

---

## 11. Economy

**Sources (all player-made or gathered):** wild grain and straw from `forage`; field grain, straw and flax; flour and bread from those; animals by capture (taming's); milk, wool, eggs, dung, young; meat, hide, bone and sheepskin by slaughter.

**Sinks:** seed sown (GG5); fertility drawn by every harvest and restored by dung, bonemeal, saltpeter or fallow time (GP5); grain spent as fodder; grass eaten and pastures overgrazed (GP9); hay spoiled by rain; condition lost in a hungry winter (GP10); animals lost to sickness (GP13); tools worn (GP6); milk that spoils uncured; food fed to pigs.

**Materials this design gives a source or a first sink:** wool and yarn (BLOCKED on shearing today); `fur` (no creature yields it); straw (no node); milling stones (no sink); saltpeter (sink blocked); bone (bonemeal); flint (a real tool sink); spoiled food (pigs).

**Exclusives (for the roadmap entry's single decision):** proposed for farming — grain and what is made from it (flour, bread, malt), straw, fine linen; for livestock — wool, milk and cheese, eggs, bulk hide, sheepskin. Fishing's notes proposed fish oil and salt fish. Hunting keeps game meat, small hides and wild fur; foraging keeps berries, wild greens and coarse fibre.

**Services:** threshing and grinding for others; a neighbour paid in grain to tend a field while its owner travels (the player version of OSRS's gardener, §2.6); sharecropping a slot; selling seed of a good line; hay contracts with herders; lending a ram; shepherding someone else's flock; mucking out.

**Coin:** none proposed. **Logging:** sow, reap, pluck, milk and slaughter are economic events; new activity-log kinds or fields on `gather` is GQ6, as Hunting Design TQ10 asks for kills. **Ledger:** every new item gets its source and sink row in `docs/PolishedWorld_SourceSink_Ledger.md` in the same commit.

---

## 12. Multiplayer and server load

- **One global write per 1800 s.** The growing index is one more number on `WeatherScript`'s existing wake; nothing else ticks.
- **Reads are O(1) per object.** A slot compares two index values; a pen and its pasture bring two stocks up to date from their anchors on read and write back only when something changed. Twenty players with twelve slots each is 240 dict entries in twenty attributes, read when someone looks.
- **Concurrency.** Sow, tend, reap and milk are timed acts on the single `ndb.timed_action` slot (`world/timed_actions.py:107`); at completion each re-reads the slot and checks it is still the actor's and still in the expected state (the `claim` pattern, `:198`). Two reapers on one slot are serialised by Evennia's single reactor thread, as two foragers on one `ResourceNode.harvest()` are (`typeclasses/resources.py:105`).
- **Offline.** Nothing reads a statue (`typeclasses/characters.py:472`); fields and herds advance by the world's clock whoever is online, and their slopes are long enough that a night away costs nothing (GG2).
- **Wilderness.** No fields or pens there until Stage 6 (GP1).

---

## 13. Immersion extras

- **Fields across the year in the room text.** Green in spring, gold in late summer, stubble after harvest, snow over the furrows — the *Biome fragment library* entry's seam, or `$state()` fragments today (`typeclasses/rooms.py:198–252`).
- **Harvest home.** The last sheaf in, a feast — a reader for Cooking's well-fed buff (Cooking Design CP15) and, later, the taverns.
- **Lambing at night.** A ewe in difficulty when the herder is there to help — an optional `husbandry` roll for one more lamb, never a loss when nobody is there.
- **The lead ewe's bell**, heard from the next room.
- **Barn, byre, granary, coop.** House parts for Housing Design §7: a roofed byre spares a flock the worst of winter, a dry granary keeps grain off the damp, a larder or cellar sets `is_cold_storage` for milk and cheese (Cooking Design CP10, `typeclasses/corpse.py:104`).
- **Dung cakes for fuel** where wood is scarce, a second fuel for Cooking's fire.
- **Bait.** Grain and bread for fishing (Fishing Design §8).
- **Bless Crops** for a priest, once magic exists (GP-L6).

---

## 14. Layers — a suggested order

1. **Slice 1 (the smallest real thing):** the wild grain node (straw and wild grain) and its forage yield; the growing index, in the same change as Cooking CQ9; `FarmPlot` with one grain crop — `till`, `sow`, `tend`, `reap`, `thresh`; the digging stick and flint sickle; grinding on milling stones; the straw hat recipe; `farming` (GQ1).
2. **Slice 2:** fertility with dung's placeholder, bonemeal and saltpeter (GP5); flatbread and porridge on Cooking's fire; flax and fine linen if GQ2 stands; seed quality lines (GP4).
3. **Slice 3 (livestock — last, as the roadmap entry orders):** `Pen` with sheep on a pasture; grass, trough and hay on the drying index; the condition ladder; lambs; plucking → yarn → the wool tunic; slaughter templates and sheepskin → the fur cloak; dung for the fields; `husbandry`. Needs the founding flock (GQ5).
4. **Slice 4:** milk, butter and cheese (with Cooking's preservation and salt); fowl and eggs; pigs on scraps; disease (with *disease & herbalism*); shears and the scythe (with metallurgy).

**Prerequisites:** the food-professions exclusives decision and BACKLOG *Food spoilage*, as that entry's trigger requires before food professions; Epic A (done) and the crafting tool slice, as the roadmap entry orders; authored field and pasture rooms in the seed. **Not prerequisites:** Stage 5 (predators and rustling wait for combat and law, §17), Housing's code (a field and a pen work without a house; Housing BQ2 shares the ownership question), the webclient.

---

## 15. Seams in today's code (read at `63d9d7d`)

| Need | Seam | Where |
|---|---|---|
| A world fixture that regenerates lazily | `ResourceNode`, `last_regen` advanced by whole intervals | `typeclasses/resources.py:52–96`; `harvest` `:105`; `_availability_phrase` `:129` |
| Fixture lock | `get:false()` at creation | `typeclasses/resources.py:61` |
| The script that would carry the index | `WeatherScript`, 1800 s, four states, `previous_weather` only | `typeclasses/scripts.py:112`, `:135–146`; `world/weather.py:23–33` |
| Seasons, calendar | `_SEASONS`; one game year = 91 real days | `world/gametime_utils.py:56–61`; `server/conf/settings.py:50–53` |
| Wild food and fibre nodes | berries, fibrous plant, gourd vine | `world/prototypes.py:94–179` |
| Forage | `CmdForage` | `commands/foraging_commands.py:54` |
| Straw, saltpeter, flint, fur, bone, wool, yarn, spindle, grindstone | registry rows and notes 1, 3, 4, 10 | `world/material_registry.py:153–158`, `:171–176`, `:135–140`, `:203–209`, `:210`, `:237–242`, `:323–328`, `:373–382`, `:490–511` |
| Dormant garments | `WoolTunicRecipe`, `FurCloakRecipe` commented out | `world/recipes.py:625–626` |
| Garment prototypes | fur cloak warmth 3, wool tunic warmth 2, straw hat (no recipe) | `world/prototypes.py:571–592`, `:615` |
| Milling stones | prototype with no sink; `MillingStonesRecipe` | `world/prototypes.py:857–871`; `world/recipes.py:469` |
| Tool inputs | stick, flint, wood, bone | `world/prototypes.py:203`, `:328`, `:384`, `:928` |
| Improvised tool | `improvised_penalty` −20, `_tool_modifier` | `world/crafting_base.py:99`, `:190` |
| Tool wear | `apply_wear` | `typeclasses/durable.py:43` |
| Quality bands | `SUPERIOR`…`SHODDY`, `quality_band` | `world/crafting_quality.py:35–46` |
| A custom skill | `hunting` (INT+CON), improvable set | `typeclasses/characters.py:443–455`, `:892`; `world/chargen.py:59–65` |
| Professions | four packages, none farming | `world/professions.py:66–70` |
| Skill rolls | `skill_check`, `opposed_check` | `world/skillcheck.py:58`, `:127` |
| Timed acts | `start`, `claim`, `interrupt`; one `ndb.timed_action` | `world/timed_actions.py:107`, `:198`, `:229` |
| Slaughter and parts | `Creature.at_death`; `HARVEST_TEMPLATES`; `CmdHarvest` | `typeclasses/creatures.py:61`; `world/harvest_templates.py:66`; `commands/hunting_commands.py:175` |
| Cold storage flag | read by the corpse, set by nothing | `typeclasses/corpse.py:104` |
| Food | `Food`, `restore_amount` | `typeclasses/consumables.py:19–23` |
| Authored rooms | `ROOMS`, `NODES` in the seed | `world/seed_data.py:79`, `:193` |
| Statues | `at_post_unpuppet` keeps the character in the room | `typeclasses/characters.py:472` |
| Room text by state | `$state()` fragments | `typeclasses/rooms.py:198–252` |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 16. Open questions

- **GQ1** — Skills: a custom `farming` (DEX+INT) and a custom `husbandry` (INT×2), one skill for both, or farming as a `craft` discipline? *Leaning: two custom skills on the `hunting` precedent — Legend separates Craft (Farming) from Lore (Animal), and a farmer and a herder are different players; a discipline does not fit acts on a place.*
- **GQ2** — Linen: does farmed flax give only *fine* linen while foraged fibre keeps today's cloth chain, or does the roadmap's "linen to farming" move cloth to flax? *Leaning: fine linen only — no shipped recipe loses its source, and the exclusive is a grade.*
- **GQ3** — Spans: a grain crop's need, the ripe-standing span and the going-to-seed span. *Leaning: about one game month of summer growth to ripen (a real week) and about the same again standing ripe; roots and greens shorter.*
- **GQ4** — Who owns a field slot or a pasture: one plot per character or per account, claimed or granted, lapsing when idle (Housing Design BQ2)? Is a pasture a commons whose grass every herd shares — overgrazing as a social problem — or private? *Open.*
- **GQ5** — The founding flock: taming only, from a wild range seeded by staff (the scroll-seed precedent of a staff-placed source), or a one-time stocked pen? *Leaning: a seeded wild range to catch from, never animals placed in a pen.*
- **GQ6** — Taking from someone else's slot or pen: allowed and traced (Hunting Design TP4's passage records, TQ12) or owner-only? And the activity-log kinds for sow, reap, pluck, milk and slaughter. *Leaning: owner-only (and lessee) until Stage 5 and law exist; kinds decided with Hunting TQ10.*
- **GQ7** — Fertility as one number, or three nutrients (Vintage Story)? *Leaning: one number with a word — rotation's decision survives as fallow versus manure.*
- **GQ8** — Pasture and herd accuracy over long unread gaps: exact piecewise integration with the growing index, or a summary that errs towards the herd? *Leaning: a summary that errs towards the herd, consistent with GG2.*
- **GQ9** — Does a ripe crop left over winter stand until spring (the index pauses), or does winter weather it on the spoilage index? Which species come first after sheep, and does a goat replace the sheep for slice 3 (milk, meat and some wool from one animal, AoL `:2845`)?
- **GQ10** — `farmer` and `herder` chargen professions now, or with BACKLOG's professions covering the catalogue (post-alpha)?

---

## 17. Considered and not proposed

- **Crops lost overnight.** Wurm's weeds after a night away (§2.1); GG2.
- **Tending windows in seconds.** ATITD's weeding (§2.3); GG4.
- **An NPC gardener, seed merchant or livestock dealer.** Pillar 1; neighbours and wild sources instead (§2.6, GP8).
- **One object per animal, each with AI.** The roadmap's aggregate rule; per-animal names and pets belong to taming.
- **Tickers per field, slot or pen.** GG7; one global index.
- **Growth in winter, or frost-hardy crops now.** The season factor is 0 in winter; greenhouses and cold-hardy species are later content.
- **Three nutrients.** GQ7.
- **Crop blight in slice 1.** Disease starts with herds, where crowding is a real choice; blight waits for monoculture to be a real choice.
- **Predators, rustling and trampling.** Wolves at the fold need Stage 5; theft of animals needs law; Avalon's roaming starved animal waits for both (§2.2).
- **Fields in the wilderness.** GP1; Stage 6.
