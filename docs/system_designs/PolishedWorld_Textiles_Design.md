# PolishedWorld — Textiles Design Notes (fibre, spinning, weaving, dyeing, tailoring)

> **Rev 2 · 2026-11-08** — moved, docs only, with roadmap Rev 60, BACKLOG Rev 85 and README Rev 39: from `docs/` to `docs/system_designs/`, together with the fourteen other one-system design notes and the series handoff, `docs/system_designs/HANDOFF.md`. The *Canonical* line and every path to a design note outside a Rev line now name the new folder; no content changed. Rev lines keep the paths they were written with, since changelog lines are left exactly as written.
> **Rev 1 · 2026-11-07** — first version, docs only, with roadmap Rev 52, BACKLOG Rev 74 and README Rev 30. Written from a design chat, the seventh in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`, `docs/PolishedWorld_Housing_Design.md`, `docs/PolishedWorld_Hunting_Design.md`, `docs/PolishedWorld_Cooking_Design.md`, `docs/PolishedWorld_Temperature_Design.md` and `docs/PolishedWorld_Farming_Design.md`. Textiles are partly shipped — plant fibre, twine, cloth, six garments, a sack, a tent, garment wear and repair — and this document proposes no change to any of it; it names the shipped seams it would read and the materials it would give a source or a sink. **Nothing here is locked.** Every numbered item is a proposal (WP…), a goal (WG…) or an open question (WQ…); the letter is for *weaving*. In the chat Adam approved writing the document from the proposal; the leanings under WQ1–WQ6 are the ones proposed in the chat, recorded as *leanings*, not as decisions, and WQ7–WQ9 are raised by this document and open. Prior art was read on 2026-11-07; code seams were read against `main` at `a8d505c` (Evennia 6.1.0).
> **Canonical:** `docs/system_designs/PolishedWorld_Textiles_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/roadmap.md`, parallel backlog, *Textiles — fibre, spinning, weaving, dyeing, tailoring* — a new entry (Rev 52) that points here; textiles had no roadmap entry before. `docs/BACKLOG.md` gains two notes (Rev 74): *Material / maker's-mark aliases beyond "superior"* (WP10 proposes the display) and *Disassemble yields parts and raw materials* (WP12 proposes rags as a lossy salvage product).
**When to read:** at the start of a textiles decomposition; when Farming Design's slice 2 (flax, GQ2) or slice 3 (wool and sheepskin, GP11) is decomposed; when hunting gains its first fur-bearing creature; when Temperature Design KP10 calibrates its comfort bands against what players can make (§8 is that input, and KQ7's seventh piece); when the station question (kiln, furnace, forge — `world/material_registry.py` open decisions 7–9) is decided, since the loom is a station (WP4); when Housing Design BP7's parts list or BP8's tent and lean-to rungs are decomposed (cloth is building material, WP13); with *maps & navigation* and *travel/roads/boats* in the queue (sails).
**Departs from live behaviour:** nowhere. No shipped recipe, prototype or command changes; WQ2 (splitting the `weaving` discipline) would, and is a question, not a proposal.

---

## 1. The idea in one paragraph

Every piece of cloth in the world went through hands, and the hands are players'. A shepherd plucks the fleece at the summer moult; a spinner turns it to yarn on a stone-weighted spindle; a weaver with a loom in her house turns yarn into a length of woollen cloth, or a farmer's retted flax into fine linen; a dyer steeps it red with madder or blue with woad; a tailor cuts and sews it, and the finished tunic carries the tailor's name. Worn through a winter it thins and is mended — patched, and the patches show — and when it is past mending it is cut into rags that become a bandage or a torch's wick. Warmth climbs with the fibre: plant cloth for summer, wool for autumn, fur and fur linings for the deep winter. Cloth is also what tents, sacks and sails are made of, and those take it by the bolt. Nobody sells any of it but players, every stage is someone's trade, and every garment wears out.

---

## 2. Prior art

### 2.1 Achaea — the lesson

Sources: Achaea's in-game help as published on `achaea.com` (*HELP DESIGN*, *HELP CRAFTING GUIDELINES*, the designs index), and the Achaea forums (threads on tailoring design practice and on approval fees). Paraphrased:

- A tailor writes a garment's appearance, its dropped and examined descriptions, as a *sketch*, and submits it for approval by a Crafting Council; the cost of resubmitting grows with each rejection, and an urgent queue costs more.
- Once approved, the tailor pays an approval fee that depends on the garment and on the materials named (fancy fabrics and gems raise it), and can then make it repeatedly.
- A crafted item shows its crafter's mark when probed; the crafter may pay to hide it.
- Players spoke of visiting a skilled tailor's shop just to look at the designs: the appearance is the product.

**Worth taking:** the appearance and the maker's name as the lasting value of a garment (WP9, WP10).
**Not for PolishedWorld:** free-text designs behind a human review queue. **The lesson (the series' "Achaea lesson"):** Achaea answers the question every clothing system must answer — why would anyone buy a second shirt? — with authored appearance, and pays for it with a standing staff of reviewers. A solo developer has no council. In PolishedWorld appearance is **composed** from parts players make — fibre, colour, cut, lining, the maker's mark — never written in free text, so no queue is needed and nothing can be written that a reviewer would have caught (WG4).

### 2.2 Ultima Online — cloth from a shop

Sources: the official UO wiki (`uo.com`, *Tailoring*), UOGuide (*Tailoring*), and a crafting-forum post describing the process. Paraphrased:

- Wool from sheared sheep, cotton picked from fields or flax are spun on a spinning wheel into yarn or thread and woven on a loom into bolts of cloth, which scissors cut into cloth.
- The same bolts could be bought from NPC tailors and weavers, and players did buy them, because the shop's cloth was cheap and making one's own was slow.
- UOGuide notes that dressing up was neglected in practice: many players simply wore a robe over their armour.

**Worth taking:** the chain itself — fibre, spinning, loom, cloth, cutting — and the spinning wheel and loom as fixtures in a house or a shop.
**Not for PolishedWorld:** NPC cloth (pillar 1). **The rule taken:** without NPCs the same failure has another form — a step that anyone can do quickly, with no grade, no tool and nothing the step before cannot give, is never a trade. Each stage must sell something the stage before it cannot (WG1).

### 2.3 Star Wars Galaxies — clothing that never wore out

Sources: SWGEmu's archive of the SOE *Tailor* forum (2004–2007: a clothing-repair experiment; a list of tailor issues), and an `swgr.org` suggestion thread (2023). Paraphrased:

- Tailors reported that clothing at zero condition could still be worn and its bonuses still worked, so nobody ever had to replace clothing; and that armour-smiths' belts and bandoliers, which did not decay, had taken the belt market from tailors.
- Years later, players on a revival server still observed that tailors lack the built-in repeat business that item decay gives other professions.

**Worth taking:** decay as the tailor's repeat business; repair as a skill of the trade.
**Not for PolishedWorld:** anything worn that keeps working at zero condition. **Already avoided:** shipped thermal multiplies each garment's warmth by its condition (`world/thermal.py:108`), so a worn-out garment warms nothing, and garment wear runs on a ticker (`world/garment_wear.py:43`). The rule is to keep it so for every new piece, including linings (WG2).

### 2.4 A Tale in the Desert — canvas by the hundred

Sources: A Wiki in the Desert (`atitd.wiki`, Tale 9–11 pages *Flax*, *Tow*, *Lint*, *Canvas*, *Clothwork*, *Weaver*). A Tale in the Desert has a player-run economy, the closest match to pillar 1. Paraphrased:

- Harvested flax is left to rot, then combed into straw, tow and lint; tow is spun into twine, lint into thread; twine woven on a loom gives canvas, thread gives linen, and twine also gives rope.
- One canvas takes sixty twine on a loom; canvas is consumed by a long list of buildings, an airship alone taking a hundred and sixty.
- A weaver's specialisation shortens loom timers and lowers material costs; a student's loom breaks strings.

**Worth taking:** retting and combing as the steps that turn a crop into fibre (WP1); coarse and fine products from the same plant; the loom as a building.
**The rule taken:** the largest buyer of cloth is building, not clothing — canvas for tents, sails and walls is consumed by the bolt and never comes back (WG3, WP13).

---

## 3. Design goals

- **WG1 — Every stage is a trade.** Fibre, yarn, cloth, colour and garment each sell something the stage before cannot: a grade, a tool, a station, a slow process or a skill (§2.2).
- **WG2 — Function wears out.** Every piece that warms, carries or shelters loses it with condition and gives nothing at zero (§2.3; shipped).
- **WG3 — Cloth is building material.** Tents, sacks, sails and walls are the bulk sink; clothing is the steady one (§2.4).
- **WG4 — Appearance is composed, never written.** Colour, fibre, cut, lining, patches and the maker's mark are data players make; no free text and no review queue (§2.1).
- **WG5 — No shipped recipe loses its source.** New fibres add grades beside today's cloth chain; they do not replace it (Farming GQ2's rule).
- **WG6 — Slow processes run on objects.** Retting and dyeing take real hours on a pit or a vat, with timestamps read on demand, never on a waiting player and never on a ticker (Cooking Design's rule, CP11, CP12).
- **WG7 — Warmth has teeth.** Wool and fur are the top of the warmth chain, and they are scarce (Temperature Design KG3).

---

## 4. Legend alignment

**Rules as written:**

- **Craft (DEX+INT)** — Legend core p. 57: several separate skills under one heading; the list includes basketweaver, *tailor* and *weaver*. P. 58: a critical success makes the item superior — *"choose one area of excellence"*, durability, value or utility; in utility it gives a bonus equal to the maker's critical score to whichever skill the item is used for. A fumble halves the item's armour, hit points and value.
- **Craftsman** — p. 20: *Craft (Any)* as the advanced skill.
- **Arms of Legend, goods** (`docs/reference/arms_of_legend.md`): yarn, fifty metres, spun from goat, lamb or yak wool, the primary component in knitting and many tailoring trades, weaker than twine (`:522`; ENC 1, 7 CP, `:622`); coloured dye, a paste diluted in water and vinegar, an object soaked in it and left to dry for about twelve hours takes the colour (`:218`; ENC 1, 13 SP, `:531`).
- **AoL, clothing:** the winter coat, wool lined with rabbit or beaver fur, +10 % to Survival or Resilience against natural cold (`:732`); the winter cloak, fur and leather, the same +10 %, also usable as a blanket (`:734`); the winter hat, wool with fur or fleece flaps, +5 % (`:760`); a catsuit that a tailor must fit to its wearer with Craft (Tailor) at −10 % (`:730`); the *Wintered* armour modification, leather or fur fixed into an armour's gaps against cold (`:1343`).
- **AoL, tasks:** repairing torn clothing is Craft (Sewing), with a Task Round of five minutes to an hour (`:1056`).
- **AoL, trades:** the dyer, who dyes cloth, clothing and wool for others (`:3018`); the furrier, who cleans a pelt so the fur stays intact (`:3034`); the seamstress, who mends and hems quickly (`:3106`); the tailor, who makes everything of cloth or canvas (`:3116`).

**Translation proposals:**

- **WP14 — No new skill.** Legend's Craft (Weaver), Craft (Tailor) and Craft (Sewing) are recipe disciplines of the one `craft` skill, as every shipped textile recipe already is (`discipline = "weaving"`, `world/recipes.py:118`; disciplines `world/recipe_mastery.py:81–87`). Specialisation is per-recipe mastery, the roadmap's [RESOLVED] *Craft specialisation model* (2026-08-11). Unlike fishing, hunting and farming, textiles is a workshop craft; there is no field skill to add. Whether tailoring becomes a discipline of its own is WQ2.
- **WP-L1 — The critical's three areas.** Durability is shipped: a garment's quality sets its start condition (`_apply_garment_quality`, `world/recipes.py:73`). Utility is the shipped superior-tool pattern (Stage 2 Component G, `_apply_tool_quality`, `:93`) and applies to the spindle and the loom. Value has no reader — nothing is priced by NPCs — so the maker's mark and the superior alias carry it socially (WP10).
- **WP-L2 — AoL's winter percentages become warmth points.** The codebase has no Survival or Resilience test against cold; Temperature Design maps AoL's winter gear onto the warmth sum (its KP10 note: coat and cloak about 3, hat 2). This document follows that mapping (§8).
- **WP-L3 — Craft (Sewing) is the shipped `repair`.** A Task Round of minutes to an hour is the shipped repair's timed act (`commands/repair_commands.py:61`); mending stays one act per garment (WP11).
- **WP-L4 — Legend's prices are not used.** Pillar 1. The ENC values are: yarn ENC 1 per fifty metres, dye ENC 1.
- **WP-L5 — AoL's trades are candidate professions.** Dyer, furrier, seamstress and tailor beside the shipped `weaver` (`world/professions.py:67`); when is WQ9.

---

## 5. The loop

Proposed phases; each is a stage someone can sell.

1. **Get fibre.** `forage` a fibrous plant for coarse plant fibre (shipped); take retted flax from a farmer (Farming GP7); buy wool from a shepherd (Farming GP11's plucking); buy fur from a hunter or sheepskin from a herder.
2. **Prepare it.** Flax is retted in water — a pit or a pool holds it for a span of game days and gives it back ready to comb (WP1). Wool needs no preparation in this design.
3. **Spin.** Wool on a spindle gives yarn; combed flax gives linen thread (WP2).
4. **Make cloth.** On a loom, yarn becomes woollen cloth and linen thread becomes fine linen (WP4). Plant fibre still becomes coarse cloth by hand, as today. Wool can skip spinning entirely and be felted with water (WP3).
5. **Colour it.** Yarn, cloth or a finished garment steeps in a dye vat for a span of real hours (WP8).
6. **Make the garment.** Cut and sew cloth with a needle (shipped); knot socks, mittens and caps from yarn with a bone needle (WP5); line a garment with fur (WP6). The garment carries its maker's mark (WP10).
7. **Wear it.** It warms by fibre and lining, and wears by exposure (shipped ticker).
8. **Mend it.** With cloth and twine, or yarn for wool; mended garments show their patches (WP11).
9. **Cut it to rags.** Past mending, a garment gives rags for bandages and wicks (WP12).

---

## 6. Fibre and yarn

**WP1 — Three fibre lines; today's cloth stays.** Proposed grades, each a material of its own beside the shipped `cloth` (`world/material_registry.py:254–264`):

- **Plant fibre** (`fiber`, `world/material_registry.py:92–97`; the fibrous plant node, `world/prototypes.py:156–167`) keeps both shipped recipes unchanged: three fibres make twine (`world/recipes.py:114`) or a bolt of coarse cloth (`:161`). Its spinning is implicit in those recipes (WQ1).
- **Flax** from a farmed field (Farming GP7) is retted in water and combed, giving *tow* and *line*: tow goes the way of plant fibre (twine, coarse cloth), line is spun to linen thread and woven to **fine linen** on a loom. This is the ATITD chain (§2.4) cut to its two products that matter here. Fine linen is the *exclusive grade* Farming GQ2 leans to — a better undershirt and a finer robe, not a replacement for coarse cloth.
- **Wool** from livestock (Farming GP11; registry row `:237–242`, today BLOCKED) is spun to **yarn** (WP2), woven to **woollen cloth**, knotted into small pieces (WP5) or felted (WP3).
- **Fur** — the registry's warmth-chain material, a pelt kept fur-on (`:203–209`; no creature yields it in the alpha) — is not spun: it is cut and sewn into fur garments and linings (WP6). Hunting's soft-furred creatures and livestock's fleece-on sheepskin (Farming §11) are its sources.

*Retting* is a slow process on an object (WG6): a retting pit in a room with water takes flax and gives it back combed-ready after a span of game days, stamped on the pit; left far past the span it loses grade slowly, never all at once. Whether water is a room property or a carried material is the registry's open decision 6 (`world/material_registry.py:489–516`), shared with Cooking CQ14.

**WP2 — The drop spindle, and spinning as the slow step.** The registry already plans a spindle as a hand-made tool (`:378–382`, DATA). Proposed: a stick and a whorl — stone now, fired clay once a kiln exists, which would give clay its second sink beside sling bullets (`:141–146`). Spinning recipes take wool to yarn and line to linen thread with `tool_tag = "spindle"`, so the shipped improvised-tool penalty applies to finger-twisting (`improvised_penalty` −20, `world/crafting_base.py:99`; `_tool_modifier` `:190`). Historically spinning, not weaving, was the bulk of a textile's labour; here that weight is carried by counts (several yarns to a cloth, two wool to a yarn), not by long timers — the skill is in choices, not in waiting. A superior spindle gives the shipped tool bonus (WP-L1).

**WP3 — Felt first.** Wool beaten in hot water mats into felt, the oldest wool textile, with no spindle and no loom. Proposed as wool's **first sink**, the cheapest textile that livestock's first fleece can become: a felt hat (hat slot), felt liners for boots, a saddle blanket for *mounts & pack animals*, and felt walls for a nomad's tent in Housing's later rungs. Felt is one of the materials the roadmap's Rev 27 finding (D)(2) counted among those the alpha catalogue needs and nothing provides. It needs water (WP1's open decision).

---

## 7. Cloth and the loom

**WP4 — The loom is a station in a room.** A warp-weighted loom — a wooden frame, warp threads hung from it, kept taut by loom weights of stone (or fired clay, after the kiln) — is a fixture object placed in a room, `get:false()` like a `ResourceNode` (`typeclasses/resources.py:61`), and recipes for woollen cloth and fine linen require one in the room. Today's coarse cloth does not: it is narrow hand-weaving, as the shipped recipe says (`world/recipes.py:169`, *handwoven*), so no shipped recipe changes (WG5). The loom wears on use (`apply_wear`, `typeclasses/durable.py:43`) and is mended with wood and twine. No station typeclass exists today; the loom is the first station that needs no heat, and whether stations share one typeclass is decided once with the kiln, furnace and forge (registry open decisions 7–9; WQ3). Placement: a house part (Housing Design BP7) or a workshop room in an authored settlement; who may use a loom in someone else's house is Housing Design BQ2's and BQ4's question.

**WP13 — Canvas stays cloth; building takes it by the bolt.** The registry folds canvas and sailcloth into `cloth` as a heavy grade (`world/material_registry.py:466`, open decision 11, PROVISIONAL), and this design keeps that: a split earns its keep only when a sail or a tent must wear differently. What changes is the *quantity* later systems ask for. The shipped tent takes four cloth (`world/recipes.py:483–496`) and the sack two (`:315–325`); Housing Design's tent and lean-to rungs (BP8), sails for *travel/roads/boats*, market awnings for *markets & taverns* and felt walls (WP3) should price their builds in cloth counts large enough that cloth is construction material, as ATITD's canvas is (§2.4). That demand is bounded by fibre supply — the fibrous plant node's regeneration and the farmers' flax — which is the point: weavers have a market that is never saturated by clothing alone.

---

## 8. Garments and warmth

**WP5 — Knotted socks, mittens and caps fill the empty slots.** `gloves` and `socks` are clothing types with a limit of one (`server/conf/settings.py:210–213`) that no garment fills. Proposed: socks, mittens and a cap from yarn, made with the shipped bone needle (`BoneNeedleRecipe`, `world/recipes.py:534`; registry `needle`, `:365–372`) by **nålbindning**, the single-needle looping that predates knitting in the north — so no new tool is needed. Socks and mittens give warmth 1 each, which lifts Temperature Design KP10's craftable wardrobe from 6 to 8 at full condition and answers its KQ7 (*does slice 1 need a seventh piece?*). AoL's yarn line (*the primary component in knitting*, `:522`) is the source for using yarn this way.

**WP6 — Fur lining is a change to a garment, not a new garment.** AoL's winter coat is wool lined with fur (`:732`) and *Wintered* fixes fur into armour (`:1343`). Proposed: `line <garment> with fur` consumes fur and sets `db.lined` on an existing garment, adding **+1 warmth** to it. Because the shipped cap counts one garment per body region (`server/conf/settings.py:206–213`), a lining raises a region's ceiling by one without letting anyone stack garments. The lining shares the garment's condition — it wears with it and warms nothing at zero (WG2) — and is lost when the garment is cut to rags. Lining modifies an existing object, which the crafting contrib does not do (it spawns outputs); the shipped `repair` command is the precedent for a command that works on an existing item (`commands/repair_commands.py:61`). Which garments may be lined (outer layers only, or any) is WQ4's companion question.

**WP7 — A warmth ladder by fibre.** Plant cloth 1 (the linen shirt, breeches, robe, hood, reversible clothes and linen cuirass, `world/prototypes.py:596–697`; leather boots and shoes are leather, also 1), wool 2 (the dormant wool tunic, `:585–590`), fur 3 (the dormant fur cloak, `:574–579`), felt 2 (the felt hat), and +1 for a lining. The dormant `WoolTunicRecipe` and `FurCloakRecipe` (`world/recipes.py:625–626`) become the first wool and fur recipes. One fully dressed character at full condition could then reach about **16** — a felt hat 2, a lined wool tunic 3, a linen shirt 1, lined mittens 2, a fur cloak 3, woollen breeches 2, socks 1, lined boots 2 — against 6 today. Temperature Design KP10 calibrates its comfort bands against what players can make; this ladder is that input, and the bands should be set so that the deep winter needs wool *and* fur, not one or the other (WG7).

---

## 9. Colour and the maker

**WP8 — The dye vat.** A vat is an object in a room (a wooden tub; a clay pot after the kiln) that takes water, a dyestuff and yarn, cloth or a garment, and gives the piece back coloured after a span (AoL's twelve hours of drying, `:218`, is three real hours at the 4× clock, `server/conf/settings.py:50–64`). The span is stamped on the vat at loading and read on demand (WG6), the shape of Cooking Design's drying rack (CP11). Dyestuffs: ground ochre — the registry's planned `pigment`, whose sinks already include dyeing (`world/material_registry.py:275–280`, DATA; ochre `:159–164`) — and dye plants from foraging (woad for blue, weld for yellow, madder for red, lichens for purple), which *foraging & herbalism* in the queue would place. A colour is one word from a closed palette, stored on the piece as `db.colour`; dyed yarn makes coloured cloth and coloured cloth a coloured garment, so a dyer sells to weavers and tailors as AoL's dyer does (`:3018`). Dyestuff is consumed every time: colour is a purely cosmetic sink, and the first thing in the game anyone buys only because they want it.

**WP9 — Appearance is composed.** A garment's look line is built from its parts — colour, fibre grade, cut (the recipe), lining, condition word, patches, maker: *a madder-red woollen tunic, fur-lined, patched at the elbows, stitched by Adam*. No free text, no review (WG4). Colour as a display adjective and an alias rather than a change of `key`, so searching for *tunic* still finds it — the shipped superior alias is the precedent (`_apply_garment_quality`, `world/recipes.py:73`). Achaea's authored designs are §17.

**WP10 — The maker's mark is shown.** Every crafted object is already stamped with its maker's key (`obj.db.crafted_by`, `world/crafting_base.py:405`) and recipe (`:412`), and BACKLOG *Material / maker's-mark aliases beyond "superior"* (`docs/BACKLOG.md:294`) is the display layer's home. Proposed for garments first: a line in the look text, *stitched by <maker>* (*woven by* for cloth and felt, *dyed by* for a dyer's colour). A tailor known for good work becomes findable by what people wear — reputation as pillar 1's advertising. Whether a maker may leave a piece unmarked, as Achaea sells, is WQ7.

---

## 10. Mending and rags

**WP11 — Mending follows the fibre, and patches show.** Repair is shipped with cloth and twine as the garment default (`REPAIR_MATERIALS`, `commands/repair_commands.py:35`) and a per-item override in `db.repair_materials` (`:121`). Proposed: wool garments darn with yarn, felt with felt, fur with fur — data on the prototype, no code. Each successful repair adds to a count on the garment, and above a threshold the look line says *patched* (WP9). Mending is the seamstress's trade (AoL `:3106`): quick, cheap and steady, as garment wear (`world/garment_wear.py:43–51`) guarantees.

**WP12 — Rags.** A garment worn past mending can be cut with a knife into rags — fewer than the cloth it took, never cloth itself — and rags are a new material: a bandage for First Aid once BACKLOG's two-stage healing exists, the wick of a torch for *light & darkness*, pulp for paper once the writing chain is ratified (`pulp`, `world/material_registry.py:478–483`, PROPOSED_UNRATIFIED). This is a narrow case of BACKLOG *Disassemble yields parts and raw materials* (`docs/BACKLOG.md:561`) that keeps its two fixed constraints — never all the material, and a bad cut can spoil it — and because rags are not cloth, it does not weaken cloth's sink, the concern that entry names. It waits for that entry's decision, not ahead of it.

---

## 11. Economy

**Sources (all player-made or gathered):** coarse plant fibre from `forage` (shipped); flax from fields (Farming); wool and sheepskin from flocks (Farming, livestock; the founding flock is *animal taming*'s, Farming GQ5); wild fur from hunting; dye plants from foraging; ochre ground on a grindstone; wood, stone and bone for spindles, looms and needles.

**Sinks:** garment wear on every worn piece (shipped); mending materials (shipped); cloth by the bolt in tents, sacks, sails and walls (WP13); dyestuff consumed by every dyeing (WP8); fur consumed by linings; rags consumed as bandages, wicks and pulp (WP12); spindle, loom and needle wear (`apply_wear`).

**Materials this design gives a source or a first sink:** wool (first sinks felt and yarn); yarn (a source — spinning); fur (sinks: fur garments and linings); the spindle (from DATA to a recipe); pigment (its dyeing sink); felt (a source, for the items Rev 27 (D)(2) counted); and new rows — linen thread, fine linen, woollen cloth, dyestuffs, rags — each needing a row in `docs/PolishedWorld_SourceSink_Ledger.md` before it ships.

**Exclusives:** textiles owns no raw material. It is the buyer of farming's fine linen, livestock's wool and sheepskin, hunting's wild fur and foraging's coarse fibre and dye plants; nothing is proposed for the *Food professions* entry's single exclusives decision, which is unchanged.

**Services:** mending for travellers (the seamstress); lining a customer's own garment before winter; dyeing a customer's clothes in a house or guild colour; renting time on a loom; a weaver's standing order from a tent-maker or shipwright; the winter trade Temperature Design §11 names.

**Coin:** none proposed. **Logging:** spinning, weaving, knitting and sewing are crafts and log as the shipped `craft` kind; dyeing and lining modify an existing item and need a decision (WQ8).

---

## 12. Multiplayer and server load

- **Nothing ticks that does not tick today.** Retting pits and dye vats store a timestamp at loading and compare it on read; garment wear stays the shipped ticker over puppeted characters only (`world/garment_wear.py:60`).
- **One writer per object.** A vat or a pit is written only by the load and take commands in Evennia's single reactor thread; at completion a take re-reads the object and checks it still holds the caller's piece (the `claim` pattern, `world/timed_actions.py:198`). Shared vats in public rooms raise Cooking CQ12's question — can anyone take from a rack — which this design shares.
- **One weaver at a loom.** A loom holds who is weaving on it (`ndb`, cleared on completion or interruption) so two crafters cannot weave on one warp at once; the weave itself is the crafter's timed act on the single `ndb.timed_action` slot (`world/timed_actions.py:107`).
- **Offline.** A statue's clothes do not wear (the ticker skips characters without a session); a vat or a pit finishes on the world's clock whoever is online.
- **Reads are cheap.** The composed look line (WP9) is a handful of attribute reads per `look`; linings and colour are one attribute each on the garment.

---

## 13. Immersion extras

- **A loom in the room text.** A house with a loom shows the work on it — *a half-finished length of blue wool hangs from the loom* — a state fragment of the room (`typeclasses/rooms.py:198–252`).
- **The retting pond smells.** A room with a retting pit says so on `look`, and the smell is a reason to put it outside the village.
- **The dyer's hands.** After dyeing, the dyer's hands are stained the colour for a game day — AoL notes dye on skin lasting weeks (`:218`); here, cosmetic and short.
- **Colours that mean something.** House and guild colours for *guilds* and *temples & faith*; a sail's colour visible from the shore, for *travel/roads/boats*.
- **Nålbindning** is named on its recipes, and a sock made by it says so.
- **The winter cloak as a blanket.** AoL lets a winter cloak serve as a bedroll (`:734`): resting wrapped in a fur cloak counts as a bedroll for Housing Design BP10's rest, once a bedroll means something.

---

## 14. Layers — a suggested order

1. **Slice 0 (no new source):** the maker's mark on garments (WP10), the patched line (WP11). Both read data every crafted garment already carries.
2. **Slice 1 (fur, when hunting adds a fur-bearer):** the fur cloak recipe (dormant), fur lining (WP6), fur mending.
3. **Slice 2 (wool, when livestock or taming gives it):** felt and the felt hat (WP3); the spindle and yarn (WP2); nålbound socks, mittens and cap (WP5); the wool tunic (dormant); darning.
4. **Slice 3 (the loom and flax):** the loom as a station, with the station decision (WP4); woollen cloth; retting and fine linen with Farming's slice 2.
5. **Slice 4:** the dye vat and colour (WP8, WP9); rags with the salvage decision (WP12).

**Prerequisites:** a fur-bearing creature (hunting) for slice 1; wool (Farming slice 3, *animal taming*'s founding flock) for slice 2; registry open decision 6 (water) for felting, retting and dyeing; open decisions 7–9 (stations) for the loom; Temperature Design's band calibration reading WP7 before the warmth ladder ships; Housing's parts for a loom inside a house. A kiln is optional throughout (fired whorls, loom weights, clay vats).

---

## 15. Seams in today's code (read at `a8d505c`)

| Need | Seam | Where |
|---|---|---|
| Plant fibre and its node | `fiber` row; fibrous plant `ResourceNode` | `world/material_registry.py:92–97`; `world/prototypes.py:128`, `:156–167` |
| Twine, cloth | `TwineRecipe`, `ClothRecipe` (fibre ×3; cloth gated, rung 20) | `world/recipes.py:114`, `:161` |
| Garment recipes | linen shirt, breeches, robe, hood, reversible clothes, linen cuirass | `world/recipes.py:187–312` |
| Bulk cloth sinks | `SackRecipe`, `TentRecipe` | `world/recipes.py:315`, `:483` |
| Dormant garments | `WoolTunicRecipe`, `FurCloakRecipe` commented out | `world/recipes.py:625–626` |
| Garment prototypes | warmth and clothing type per piece; fur cloak 3, wool tunic 2 | `world/prototypes.py:563–697` |
| Wool, fur, yarn, spindle, needle, pigment, clay | registry rows | `world/material_registry.py:237–242`, `:203–209`, `:323–328`, `:378–382`, `:365–372`, `:275–280`, `:141–146` |
| Canvas, water, stations | aliases; open decisions 6, 7–9, 11 | `world/material_registry.py:466`, `:489–516` |
| Unratified materials | `PROPOSED_UNRATIFIED` (pulp, tallow, mulberry, silk thread) | `world/material_registry.py:478–483` |
| Slots and the per-region cap | `CLOTHING_TYPE_ORDERED`, `CLOTHING_TYPE_LIMIT` | `server/conf/settings.py:201–213` |
| Warmth by condition | `worn_warmth` | `world/thermal.py:104–127` (`:108`) |
| Garment wear | `WEAR_RATES`, `wear_all_garments` | `world/garment_wear.py:43–51`, `:60` |
| Repair | `REPAIR_MATERIALS`, `db.repair_materials`, `CmdRepair` | `commands/repair_commands.py:35`, `:121`, `:61` |
| Rain protection | reserved, read by nothing | `typeclasses/clothing.py:56` |
| Garment type | `ClothingWithBuffs` | `typeclasses/clothing.py:30` |
| Garment quality | `_apply_garment_quality`; tool quality `_apply_tool_quality` | `world/recipes.py:73`, `:93` |
| Maker and recipe stamps | `crafted_by`, `db.recipe` | `world/crafting_base.py:405`, `:412` |
| Improvised tool | `improvised_penalty` −20, `_tool_modifier` | `world/crafting_base.py:99`, `:190` |
| Disciplines and titles | `DISCIPLINES`, `MASTERY_TITLES` | `world/recipe_mastery.py:81–87`, `:90–94` |
| Professions | `weaver` grants cloth and linen shirt | `world/professions.py:66–70` |
| Fixture lock | `get:false()` | `typeclasses/resources.py:61` |
| Tool wear | `apply_wear` | `typeclasses/durable.py:43` |
| Timed acts | one `ndb.timed_action`; `claim` | `world/timed_actions.py:107`, `:198` |
| Room text by state | `$state()` fragments | `typeclasses/rooms.py:198–252` |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 16. Open questions

- **WQ1** — Does today's coarse cloth gain a spinning step (fibre → thread → cloth), or does it stay three fibres by hand with spinning implicit? *Leaning: stays — no shipped recipe changes, and spinning enters where it adds a grade (wool, fine linen).*
- **WQ2** — Split the shipped `weaving` discipline into *weaving* (cloth, yarn, felt) and *tailoring* (garments)? It would change shipped display and titles ("Journeyman Weaver" for a shirt-maker), the one place this design would depart from live behaviour. *Leaning: yes, but at the textiles decomposition, with a departures row.*
- **WQ3** — The loom: a station in a room, or a carried tool? *Leaning: a station, decided once with the kiln, furnace and forge (registry open decisions 7–9).*
- **WQ4** — Which slice first: fur (needs one fur-bearer in hunting), wool (needs livestock or taming) or fine linen (needs Farming's slice 2)? *Leaning: fur — one creature is the cheapest source, and it revives the fur cloak and makes linings.* Companion: may any garment be lined, or outer layers only? *Open.*
- **WQ5** — Do colours fade with wear or sun? *Leaning: not in Rev 1 — another clock for a cosmetic.*
- **WQ6** — The home: textiles had no roadmap entry. *Leaning (taken in this Rev): a new parallel-backlog entry, plus dated notes on BACKLOG's maker's-mark and salvage entries.*
- **WQ7** — May a maker leave a piece unmarked (Achaea sells the option)? And does the mark name the maker's key at crafting time, which a later rename would not follow? *Open.*
- **WQ8** — Activity-log kinds for dyeing and lining: fields on `craft`, a `repair`-like kind, or new kinds — the same question Hunting TQ10, Farming GQ6 and Fishing FQ6 ask. *Open.*
- **WQ9** — Dyer, furrier, seamstress and tailor as chargen professions now, or with BACKLOG's professions covering the catalogue (post-alpha), as Farming GQ10 asks for its own? *Open.*

---

## 17. Considered and not proposed

- **Free-text designs behind a review queue.** Achaea's model (§2.1); WG4.
- **NPC cloth, or an NPC tailor, dyer or weaver.** Pillar 1 (§2.2).
- **Clothing that works at zero condition.** §2.3; WG2.
- **Split Craft skills** — Craft (Weaver), Craft (Tailor). The roadmap's [RESOLVED] per-recipe mastery; WP14.
- **Spinning while walking.** A distaff in the hand while travelling or herding is how much historical spinning was done, but the shipped rule is one timed act per character (`ndb.timed_action`); a second, background slot is a larger change than textiles should carry.
- **Garment sizes and fitting.** AoL's catsuit is fitted to its wearer (`:730`); fit would make every garment a commission and every resale a refit — later, if ever.
- **Cotton and silk.** No climate for cotton and no mulberry (`PROPOSED_UNRATIFIED`); silk waits for its own source.
- **Mordants as a separate material.** Alum and the like would make colour fast; one dyestuff per dyeing is enough until colour has a reader beyond the eye.
- **Renaming the linen shirt.** It is made of coarse cloth and keeps its name; fine linen's shirt can be a better version, not a rename.
- **A wardrobe of unlimited layers.** The per-region cap stays; linings raise a region's value, not its count (WP6).
