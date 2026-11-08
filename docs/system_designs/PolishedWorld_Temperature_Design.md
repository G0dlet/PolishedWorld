# PolishedWorld — Temperature & Exposure Design Notes (cold, heat, wet, shelter)

> **Rev 2 · 2026-11-08** — moved, docs only, with roadmap Rev 60, BACKLOG Rev 85 and README Rev 39: from `docs/` to `docs/system_designs/`, together with the fourteen other one-system design notes and the series handoff, `docs/system_designs/HANDOFF.md`. The *Canonical* line and every path to a design note outside a Rev line now name the new folder; no content changed. Rev lines keep the paths they were written with, since changelog lines are left exactly as written.
> **Rev 1 · 2026-11-07** — first version, docs only, with roadmap Rev 50, BACKLOG Rev 72 and README Rev 28. Written from a design chat, the fifth in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`, `docs/PolishedWorld_Housing_Design.md`, `docs/PolishedWorld_Hunting_Design.md` and `docs/PolishedWorld_Cooking_Design.md`. Temperature is half shipped — the thermal model in `world/thermal.py` already turns clothing against climate into stress — so the notes name every place they would change live behaviour (§6). **Nothing here is locked.** Every numbered item is a proposal (KP…), a goal (KG…) or an open question (KQ…); the letter is for *köld*. In the chat Adam approved writing the document from the proposal; the recommended answers to KQ1–KQ6 are recorded as *leanings* under their questions, not as decisions. Prior art was read on 2026-11-07; code seams were read against `main` at `764ac79` (Evennia 6.1.0).
> **Canonical:** `docs/system_designs/PolishedWorld_Temperature_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/roadmap.md`, parallel backlog, *Temperature & exposure* — the entry gains a 2026-11-07 annotation (Rev 50), which also records that its clothing prerequisite is now met, and is not replaced by this document. `docs/BACKLOG.md` gains one note (Rev 72) on *Weather inertia*: this design reads today's weather states and does not fire part (2); wind chill (KP9) is the consumer that part waits for.
**When to read:** at the start of the exposure decomposition; when Cooking's fire is decomposed (Cooking Design CP1–CP4; the fire is a warmth term here, KP8); when Housing's shelter ladder and roof are decomposed (Housing Design BP8–BP9; KP6); when *Weather inertia* part (2) fires (wind chill, KP9); with *Fatigue-exhaustion consequence* (exposure doubles the fatigue rate, KP-L2); with *Light & darkness* (the fire is read by both).
**Departs from shipped behaviour in seven places**, listed with their source lines in §6. The largest: the cold becomes something a character can die of, and something the player is told about.

---

## 1. The idea in one paragraph

Weather in PolishedWorld is felt before it is fatal. A character walking out at dusk in late autumn feels the chill come on and is told so in words — *chilly*, then *cold* — and told which way it is going. Clothing answers most of it, and the warm clothing is what tailors make. A body can stand being underdressed for a while — Legend says for as many hours as its CON — and then it is *exposed*: tiring twice as fast and slowly losing health, as a starving or parched body does. Shelter and fire answer the rest: a tent keeps you dry but not warm, a hut keeps you warm, a fire warms everyone around it and dries their clothes. Rain soaks through what a hat and hood do not keep off, and wet wool is half as warm. In temperate weather nobody is ever in danger, however little they wear; the danger is winter, winter nights, and later the mountains and deserts. Nothing ticks while a player is away: a statue does not freeze. Winter is something a player prepares for, with things other players make.

---

## 2. Prior art

### 2.1 Achaea — the lesson

Sources: the MUD-Dev mailing-list archive (`mud-dev.zer7.com`, October 1999, thread *weather*, Matthew Mihaly's opening post) and Achaea's player forum (`forums.achaea.com`, discussion 6464, *Handling Extreme Cold*, July–August 2018). Paraphrased:

- In 1999 Achaea's founder posted a detailed weather design for review: per-area base temperature, humidity and wind, continental fronts, a daily temperature curve and a precipitation ladder. How the weather would affect players was left explicitly for later.
- In 2018 a player in a region running far below freezing kept getting shivering messages, bought warm clothing, and had a tailor sew a whole outfit with added warmth; nothing changed. Other players concluded the messages were flavour only, and one recalled that the tundra once had real effects but called it an uninteresting mechanic to deal with. The player felt the coin spent on clothing had been wasted.
- After a later rewrite added frozen ground, a player reported slipping up to eight times in a room before getting out of the mountains, and called it very frustrating.
- Secondhand, in Aetolia's forum (`forums.aetolia.com`, comment 73657): a player had been told that Imperian's weather had effects large enough that players scripted automatic dressing and undressing.

**Worth taking:** a weather model that is visible to players (Achaea's FORECAST); clothing with a warmth value made by player tailors.
**Not for PolishedWorld:** a simulation built first with the player's side deferred. **The lesson:** there are two ways to get this wrong, and Achaea did both. Warmth without teeth makes the crafted warmth worthless, which breaks pillar 1 quietly: the tailor's product has no customer. Harm without an answer, or harm that strikes at random, is only annoyance. The rule taken: every harm is warned in words before it lands, has an answer within the player's reach, and is slow enough to answer (KG2); and the answer is an outfit per season, not a swap per weather change, so there is nothing to script (KG5).

### 2.2 The Long Dark — words and a direction

Sources: The Long Dark wiki (`thelongdark.fandom.com`, pages *Hypothermia* and *Warmth*, the latter read through a mirror). Paraphrased:

- Warmth is a meter worded through states from *Warm* to *Freezing*, with arrows beside it that show whether it is rising or falling, and how fast.
- When the meter is empty the character is freezing and loses condition at a fixed rate; after about two hours of that, Hypothermia sets in, doubling the loss and draining fatigue faster. Hypothermia heals only after a long unbroken spell (a day) above freezing.
- The air, the wind and the clothing together give a "feels like" temperature; clothing has separate warmth and windproof values, and wet clothing protects less.

**Worth taking:** a worded state with a direction (KP1); a buffer before harm, and an affliction that outlasts its cause so a player plans rather than steps indoors for a moment (KP4's threshold); wet as a warmth multiplier (KP7).
**Not for PolishedWorld:** death within hours of real time, and per-body-part frostbite that waits for hit locations (Stage 5).

### 2.3 Valheim — two tiers, wet, fire and roof

Sources: the Valheim wiki (`valheim.fandom.com`, page *Wet*), guide pages on status effects, and a Steam community thread (*You are Cold, You are Wet*, March 2021). Paraphrased:

- *Cold* comes at night outside and only slows regeneration; *Freezing*, in the mountains, stops it and deals damage. Rain or water make a character *Wet*, and being wet in the mountains brings on Freezing whatever resistance the character's cloak gives.
- A fire nearby removes cold and dries the character quickly; a roof stops rain from wetting them. Fire, roof and sitting together give *Resting*.
- Players complained early that, with rain so common, they were nearly always wet and cold, a standing debuff with no counter but the fire.

**Worth taking:** two tiers — discomfort everywhere, harm only where the climate is hostile (KP3); wet that strips clothing's protection (KP7); fire and roof as the remedies (KP6, KP8).
**Not for PolishedWorld:** a debuff the player lives under most of the time. Here the temperate seasons never drain anything (KG4), and a character dries out under any roof.

### 2.4 Vintage Story — warmth that holds until half worn

Source: the Vintage Story wiki (`wiki.vintagestory.at`, page *Clothing*). Paraphrased:

- Each worn piece offsets the effective temperature by its warmth. A piece gives its full warmth down to half condition and loses it only below that, reaching nothing at zero; a garment at zero is not destroyed.

**Worth taking:** the question it raises — today's `worn_warmth` scales warmth linearly with condition (`world/thermal.py:123–126`), so every point of wear costs warmth and repair is never a threshold decision (KQ8).
**Not for PolishedWorld:** temperatures in degrees. The comfort band in words (`world/thermal.py:38–43`) does the same job with fewer numbers to tune.

---

## 3. Design goals

- **KG1 — The cold is felt and named.** A state in words with a direction (*cold, getting colder*), never a number (§2.2; `ResourceNode._availability_phrase`, `typeclasses/resources.py:129`).
- **KG2 — Warned, answerable, slow.** Every harm is announced before it lands, has an answer within reach (a garment, a roof, a fire) and takes game hours to arrive (§2.1).
- **KG3 — Warmth has teeth.** A tailor's warm clothing is worth paying for (pillar 1).
- **KG4 — Temperate is never hostile.** A naked newcomer in spring is uncomfortable — hungrier, as today — and never in danger.
- **KG5 — One outfit per season.** Bands stay wide and the buffer is long, so nobody dresses per weather change and nothing invites a script (§2.1).
- **KG6 — No harm while away.** Statues do not tick (`world/survival_ticker.py:46–47`).
- **KG7 — On the existing tick.** Everything runs in the survival ticker's per-character pass; no new ticker, no per-object script.
- **KG8 — The world reads in, one knob per job.** Season, night, weather, roof and fire each enter once, as a term in one place (`world/thermal.py`).

---

## 4. Legend alignment

**Rules as written:**

- **Exposure, Starvation and Thirst** — Legend core p. 90: exposure comes from being insufficiently prepared for a hostile environment, normally a failed Survival test; an Adventurer can normally survive *"a number of hours equal to his CON before suffering from exposure"*, which weather can change. Starvation takes CON days, thirst CON×4 hours. While suffering any of the three, the Fatigue test penalty doubles to −20 %, and each condition deals one point of damage to every location per day. Healing will not mend that damage until there is enough shelter, food or water.
- **Fatigue** — pp. 89–90: Fatigue tests, the levels Winded to Debilitated with −10 % to −50 % on skill tests, recovery by rest.
- **Survival (POW+CON)** — p. 63: one test per day without food, water or a safe place to sleep; a critical lets the Adventurer weather the conditions for days without further Resilience tests; a fumble calls for an immediate Resilience test against 1D3 damage. The codebase has no `survival` skill; the word names the gauge category (`typeclasses/characters.py:446`).
- **Resilience (CON×2)** — the skills list, p. 14. Not a skill in the codebase.
- **Weather** — pp. 231–233: four axes (wind, cloud cover, temperature, precipitation); wind STR from a table with its effect on Perception and ranged attacks; cloud cover from 1D100 with seasonal modifiers, setting the chance of rain in a six-hour period; precipitation read as snow in the cold, doubled. There is no temperature table.
- **Arms of Legend** (`docs/reference/arms_of_legend.md`): **Coat, Winter** (`:732`) and **Cloak, Winter** (`:734`) +10 % to Survival or Resilience against natural cold, the cloak doubling as a bedroll; **Hat, Winter** (`:760`) +5 %; **Tent, 4 Person** (`:480`) keeps four people dry, and AoL adds that it is not comfortable, which is why travellers buy bedrolls and warm clothing; **Bedroll** (`:146`) — sleeping on open ground without one is not complete rest; **Salt Tablets** (`:430`) +10 % to Resilience against heat and forced marches.

**Translation proposals:**

- **KP-L1 — CON hours become a reserve.** The buffer is a gauge sized so that one stack of stress empties it in CON game hours (KP3). Weather and clothing change the rate, as Legend says weather changes the hours.
- **KP-L2 — The Fatigue penalty becomes a fatigue rate.** The codebase has no Fatigue tests; fatigue is a gauge drained per tick. Exposed doubles that drain (KP4). It bites once *Fatigue-exhaustion consequence* (`docs/BACKLOG.md`, *Survival*) gives the gauge Legend's levels; until then it is honest but quiet, as the stress multipliers are today.
- **KP-L3 — Legend's equality, not Legend's clock.** The project already departs from Legend's damage clock: HP is CON×2 (decision CC9, `world/chargen.py:172`) and starvation deals `STARVE_DAMAGE` per survival tick (`world/survival_ticker.py:26`). What Legend fixes is that the three conditions are equal — one point each, summed. Exposed joins the same list with the same damage (KP4).
- **KP-L4 — Healing blocked until sheltered, recorded for later.** There is no natural healing (`health` has `rate=0`, `typeclasses/characters.py:340`), so there is nothing to block. When *Two-stage healing* or a regeneration rate lands, exposure damage heals only once the reserve is back above its threshold (KP4).
- **KP-L5 — No daily Survival test.** The reserve is deterministic: the player reads it and acts. A Survival or Resilience skill is KQ5.
- **KP-L6 — AoL's winter gear is warmth, not a roll term.** The project resists cold with a warmth sum against a band, not with tests; AoL's +10 % and +5 % become warmth values (§10). The winter cloak's second use as a bedroll is Housing Design BP10's rest term.
- **KP-L7 — Wind waits.** Wind STR and cloud cover are *Weather inertia* part (2); wind chill joins this model when that struct exists (KP9).

---

## 5. The loop

Proposed phases.

1. **Read the sky.** Weather and season are on every outdoor `look` already; the character's own state is in `status` and in a line when it changes (KP1).
2. **Dress for the season.** One outfit per season, bought or commissioned from a tailor (§10); a hat and hood against rain (KP7).
3. **Go out.** In temperate weather nothing drains. In the cold, the reserve drains at a rate set by how far the outfit falls short (KP3); the character is told *chilly*, *cold*, *very cold*, *freezing*.
4. **Answer it.** Put on another layer, step under a roof, build a fire and stand by it (KP6, KP8), or turn back. The reserve refills while it is not draining, faster by a fire or indoors.
5. **Or don't.** At empty, the character is *exposed*: tiring twice as fast and losing health each tick until the reserve is a quarter full again (KP4). Death by exposure goes through the one chokepoint every death uses.

What it reads like (illustrative, not a spec):

```
> look
Stony Ridge
...
Snow drifts down from a white sky.
You are cold, and getting colder.
> wear hood
You put on a hood.
> status
  ...
  Warmth: cold, steady
> e
...
You are freezing. Your fingers have stopped answering you.
> build fire
...
You hold your hands to the flames. You are warming up.
```

---

## 6. Departures from shipped behaviour

Each row is a change to behaviour that `main` has today; each is a proposal.

| # | Shipped today | Proposed | Where shipped |
|---|---|---|---|
| J1 | ColdStress and HeatStress are silent buffs; no message and no command names them, and `status` has no line for them | A worded state with a direction, a line when it changes, a `status` line, a visible shiver (KP1, KP2) | `world/survival_buffs.py:51–89`; `commands/character_commands.py:27–76` |
| J2 | Stress only multiplies rates: cold +8 % hunger and fatigue per stack, heat +10 % thirst and +4 % fatigue | Those stay; stress in a hostile regime also drains a new reserve gauge (KP3) | `world/survival_buffs.py:66–68`, `:86–87`; `world/survival_ticker.py:58–68` |
| J3 | The elements cannot harm; only starvation and dehydration damage health | *Exposed* joins the health conditions with the same damage, and doubles the fatigue rate (KP4) | `world/survival_ticker.py:26`, `:32–35` |
| J4 | The regime ignores the time of day: a winter night needs what a winter noon needs, and summer is hot at midnight | Night and dawn shift the band up by one outdoors; summer is hot only by day and under a clear sky (KP5) | `world/thermal.py:71–80`; `world/gametime_utils.py:46–54` |
| J5 | Rain and snow do not touch the body; `rain_protection` is reserved on garments and read by nothing, so the straw hat does nothing | A wet state that scales worn warmth; rain protection slows it (KP7) | `typeclasses/clothing.py:49`, `:56`; `world/prototypes.py:616–626` |
| J6 | Garment wear samples `thermal_regime()`, so it follows the regime as it is | J4's regime changes garment wear too: more wear on winter nights, less on summer nights | `world/garment_wear.py:34`, `:96` |
| J7 | Respawn restores health, hunger and thirst and clears *starving* and *dehydrated* | It also refills the reserve and clears *exposed* | `typeclasses/characters.py:1336–1349` |

Unchanged: the comfort bands (`world/thermal.py:38–43`), the warmth sum and its slot caps (`server/conf/settings.py:206–213`), the stress multipliers, offline characters (no tick), indoor rooms (always temperate), the weather states and their broadcast.

---

## 7. Feeling it

**KP1 — A worded state with a direction.** The character's state is a word chosen from the reserve and the side the stress is on. Cold side: *comfortable*, *chilly*, *cold*, *very cold*, *freezing*, *exposed*. Warm side: *comfortable*, *warm*, *hot*, *sweltering*, *heat-sick*, *exposed*. The direction is *getting colder* / *getting warmer* while the reserve drains, *steady* while stress holds without draining (temperate), *warming up* / *cooling down* while it refills. `status` shows the word and the direction and no number (KQ6). A line is sent only when the word gets worse — the bucket pattern the ticker already uses for hunger (`world/survival_ticker.py:104–130`, baseline in `ndb`), plus one onset line when stress first appears (*the cold bites through your clothes*). The line is sent from the tick and from `wear`/`remove` (which already call `apply_thermal_stress`, `typeclasses/clothing.py:68`, `:78`), never from a move hook: an exception in `at_post_move` reports a completed move as failed.

**KP2 — Others can see it.** `look <character>` adds one short line from *very cold* down (*shivering, lips blue*) or from *sweltering* up (*flushed, sweating*). A cloak handed over is the obvious answer, and a social one (§14); `give` already takes a worn garment off its wearer first (§10).

---

## 8. The reserve

**KP3 — A reserve, Legend's CON hours, that drains only where the climate is hostile.** A new gauge in the survival category beside hunger, thirst and fatigue, `trait_type="gauge"`, base **3 × CON**, with descs on percent as `health` already has (CON×2 base, descs 0–100, `typeclasses/characters.py:333–350`). Each survival tick (600 s real, 40 game minutes, `server/conf/at_server_startstop.py:25`):

- In a **hostile regime** (cold or hot), the reserve loses **2 per stack** of stress. One stack therefore empties it in exactly CON game hours (1.5 × CON ticks); four stacks — naked in winter — in a quarter of that, about 45 real minutes at CON 12.
- Otherwise — **temperate**, or comfortable inside the band — it gains **2**, or **6** indoors or beside a lit fire (KP8).
- Temperate stress never drains it (KG4): a naked newcomer in spring keeps today's hunger multiplier and nothing more. The temperate band's lower bound of 1 (`world/thermal.py:41`) stays.

The numbers are tunables named once in `world/thermal.py`. The trait needs a backfill on every existing character, in the idempotent pattern of `world/character_migrations.py:54`.

**KP4 — *Exposed* at empty.** At 0 the character gains an *Exposed* condition: a buff with an onset message, as *Starving* has (`world/survival_buffs.py:21`), that doubles `fatigue_rate` (KP-L2) and joins `HEALTH_CONDITIONS` (`world/survival_ticker.py:32–35`), so it deals `STARVE_DAMAGE` each tick and is summed into the single `apply_health_damage(..., source=…)` call with starvation and thirst (KP-L3). It clears only when the reserve is back above **a quarter** — one step indoors does not end it, so a player plans a real rest. Death goes through `at_character_death` like every other death; respawn refills the reserve and clears *Exposed* (J7).

---

## 9. What the body reads

**KP5 — Night and the summer day.** Two terms in `thermal_regime()` / the band, outdoors only:

- **Night and dawn** (`world/gametime_utils.py:46–54`) raise both ends of the band by one: a winter night asks warmth 5 instead of 4, a spring night 2 instead of 1.
- **Summer is hot only by day under a clear sky** — the periods from morning to evening while the weather is `clear`; a summer night, or rain or fog in summer, is temperate. This is the refinement `world/thermal.py:76–77` already names.

Both change garment wear through the shared regime (J6), which is intended: a garment worn through winter nights wears out by spring.

**KP6 — Shelter has two halves: dry and warm.** *Warm* is `is_indoor`, which already makes a room temperate (`world/thermal.py:68`) — a hut and up on Housing Design BP8's ladder, through BP9's roof. *Dry* stops wetting (KP7) and gives nothing against cold: a pitched tent (AoL `:480`: dry, not comfortable) or a lean-to — rungs 0 and 1. Whether *dry* is a room state or belongs to whoever is inside the tent is KQ9. No shelter object exists yet (`world/prototypes.py:873–884`: the tent has no sink); this design only names what thermal reads.

**KP7 — Wet.** A small state on the character, `db.wet`, 0–3: *dry*, *damp*, *wet*, *soaked*. Each tick outdoors while it is `raining` raises it by one; `snowing`, by one every other tick; `foggy` and `clear` do not. The summed `rain_protection` of worn garments (the reserved attribute, `typeclasses/clothing.py:56`) slows it: 1 halves the rate, 2 stops rain from wetting at all. Each step cuts worn warmth by a quarter (soaked keeps a quarter), applied to the sum before rounding. It falls by one a tick under any dry or warm shelter, by two beside a fire, and by one every other tick outdoors in clear weather. Written only when it changes. The straw hat (warmth 0, `world/prototypes.py:616–626`) gets the use its comment reserves for it.

**KP8 — A fire is a warmth term.** Cooking Design CP4 shapes the fire to be read here. Thermal sums the radiant warmth of lit things in the room — a duck-typed `radiant_warmth()` on the fire object, so a hearth in a house part (Housing Design BP7) is the same reader — and adds it to the worn warmth: a proposed **+3**, enough to carry an underdressed character into the winter band. Beside a fire the reserve refills at the indoor rate and wet falls by two. An outdoor fire goes out in rain or snow (Cooking CP3), so on the worst nights the answer is a roof, then a fire under it.

**KP9 — Wind waits for its struct.** Wind chill is the natural fifth term, but wind has no strength in code; Hunting Design TP-W1 derives a direction only. When *Weather inertia* part (2) splits weather into Legend's four axes, wind STR becomes a band term here (one step per Legend wind band above *Breeze*, outdoors) and windproof garments a later attribute. Not before: a guessed wind would be a second knob on the job night already does.

---

## 10. Clothing

**KP10 — Warmth stays the shipped sum, measured against what players can make.** `worn_warmth()` (`world/thermal.py:104–127`) sums every worn piece times its condition, capped one piece per body region (`server/conf/settings.py:206–213`). Today the craftable wardrobe is six pieces of warmth 1 each — hood, reversible clothes, linen shirt, robe, breeches, leather boots (`world/recipes.py:187–279`, prototypes `world/prototypes.py:616–682`) — **6** at full condition. The wool tunic and the fur cloak have prototypes but no recipe, because wool and fur have no source (`world/recipes.py:625–626`; `world/material_registry.py:203–208`: no creature in the alpha yields fur). So a full cloth wardrobe in good repair meets a winter day (4) and, with KP5, a winter night (5) with one to spare; a worn wardrobe or a wet one does not, and the fire and the roof answer the rest. The decomposition rechecks this sum against the bands before it locks a number (KQ7).

**AoL's winter gear** maps onto the warmth chain as higher values on fur and wool pieces once their sources exist: winter coat and cloak around 3 (the fur cloak's 3 already, `world/prototypes.py:572–580`), winter hat 2. **Rain protection** belongs on hats, hoods and a later oiled or waxed cloak.

**Moving a worn garment already takes it off.** BACKLOG *Worn clothing leaves without `remove()`* is DONE (launch minimum L3.1, `2c56c07`): `ClothingWithBuffs.at_post_move` runs `remove()` when a worn garment leaves its wearer by `put`, `drop` or `give` (`typeclasses/clothing.py:80–129`), and barter refuses worn items. So a garment handed over cannot count for two people, and the warmth sum cannot be gamed by passing clothes around — which matters more once warmth is survival. Re-read it in the decomposition (a chat claim that the bug was still open was corrected against this entry before writing).

---

## 11. Heat

**KP11 — The same reserve, on the hot side.** Hot is a hostile regime (Legend's crippling deserts), so heat stress drains the reserve like cold. With KP5, hot means a summer day under a clear sky, and the hot band is 0–1 (`world/thermal.py:42`): a character in a tunic in the summer sun takes one stack; undressing answers it. The heat side is deliberately light until regions exist (*Regional weather* is BLOCKED in `docs/BACKLOG.md`), and the shipped thirst multiplier stays its main cost. Salt tablets (AoL `:430`) are a later reader on this side.

---

## 12. Economy

**Sources (all player-made):** garments from the existing tailoring recipes; rain gear (the straw hat's protection, later hoods and an oiled cloak); fires (Cooking); tents, lean-tos and houses (Housing). The warmth chain's top — wool and fur — still has no source; a fur-bearing creature or shearing is what gives it one, and that is the *Food professions* entry's and the hunting design's to place.

**Sinks:** garments worn faster on winter nights (J6) and repaired (`commands/repair_commands.py`); wood burned to keep warm (Cooking's fuel sink, larger in winter); tents worn by pitching (Housing).

**Demand and services:** a season to prepare for — three months of thirteen are winter (`world/gametime_utils.py:56–61`) — so warm clothing sells before it and repair through it; a tailor's winter trade; the keeper of a warm hearth who lets travellers in; a fire kept for a hunting party. This is the prepare-for-winter loop *Seasonal supply & population memory* names as supplied by this entry.

**Coin:** none proposed. **Logging:** no new activity-log kinds; a death by exposure is a death like the others. **Ledger:** every new item gets its source and sink row in the same commit.

---

## 13. Multiplayer and server load

- **No new ticker.** Everything is in `_deplete_character` (`world/survival_ticker.py:58–68`), once per online character per 600 s. With 10+ players that is 10+ short passes every ten minutes.
- **Writes only on change.** The reserve is a gauge write each tick only while it moves; `db.wet` is written only when its step changes; messages go only on worse buckets.
- **Fire lookups.** Summing radiant warmth scans the room's contents; the tick loop can cache it per room for the pass, so ten people round one fire cost one scan.
- **Concurrency.** The reserve and wet belong to one character and are written only by the ticker and by that character's own `wear`/`remove`, all in Evennia's single reactor thread; no cross-character writes. A fire's `burns_until` is the fire's own (Cooking).
- **Offline.** Statues do not tick (KG6), so a character who logs out in the snow is safe; the place they log out has no effect on their reserve, which waits as it is.

---

## 14. Immersion extras

- **The visible shiver** (KP2) and handing someone a cloak.
- **Warming food.** A hot cooked dish could add a short *warmed* term, The Long Dark's warming-up; a reader for Cooking's dishes (KQ10).
- **Breath in the air.** A cold-morning line on `look` from the regime and the period — text only, through the existing `$state()` fragments (`typeclasses/rooms.py:198–252`).
- **Snow on the shoulders.** A soaked character's look line says so; a damp one leaves wet prints (Hunting Design TP4's passage records could note it).
- **The forecast.** A weather-wise character could read tomorrow's sky — a reader for *Weather inertia* part (1)'s Markov table, and a candidate first use of a Survival skill (KQ5).

---

## 15. Layers — a suggested order

1. **Slice 1 (the smallest real thing):** the worded state and its lines (KP1, KP2); the reserve and its backfill (KP3); *Exposed* (KP4); night and the summer day (KP5); respawn (J7). Nothing here waits on another system.
2. **Slice 2:** wet and rain protection (KP7); dry shelter as soon as Housing's tent rung exists (KP6).
3. **Slice 3, with Cooking slice 1:** the fire as a warmth term (KP8).
4. **Slice 4, with *Weather inertia* part (2):** wind chill (KP9).

**Prerequisites:** none for slice 1. **Not prerequisites:** Stage 5 (frostbite and location damage wait for hit locations), the webclient (its `survival` panel can show the state when both exist), *Fatigue-exhaustion consequence* (KP-L2 is honest without it, only quieter).

---

## 16. Seams in today's code (read at `764ac79`)

| Need | Seam | Where |
|---|---|---|
| Regime | `thermal_regime(room)`: pin, `is_indoor`, season and snow | `world/thermal.py:46–80` (indoor `:68`, summer `:76–79`) |
| Band and stress | `COMFORT_BANDS`, `thermal_stress()` | `world/thermal.py:38–43`, `:83–101` |
| Warmth sum | `worn_warmth()`, warmth × condition/100, rounded once | `world/thermal.py:104–127` |
| Apply stress | `apply_thermal_stress()`, `_set_stress()` (remove then add) | `world/thermal.py:129–159` |
| Stress buffs | `ColdStress`, `HeatStress`, silent, perstack mult mods | `world/survival_buffs.py:51–89` |
| A condition with onset message | `Starving`, `Dehydrated` | `world/survival_buffs.py:21–49` |
| The tick | `deplete_all_survival_traits`, `_deplete_character`; offline untouched | `world/survival_ticker.py:37–68` (`:46–47`) |
| Health conditions, damage | `HEALTH_CONDITIONS`, `STARVE_DAMAGE`, one summed call | `world/survival_ticker.py:26`, `:32–35`, `:71–102` |
| Worse-bucket warnings | `_check_survival_warnings`, `ndb.survival_buckets` | `world/survival_ticker.py:104–130` |
| Tick interval | `SURVIVAL_TICK_INTERVAL = 600` | `server/conf/at_server_startstop.py:25` |
| Gauges | `fatigue`, `health` (CON×2, descs on percent, `rate=0`) | `typeclasses/characters.py:317`, `:333–350` |
| Death and respawn | `at_character_death`, vitals restored, conditions cleared | `typeclasses/characters.py:1235`, `:1336–1349` |
| Physical roll modifier | `physical_modifier()` (not used here; KP-L2 is a rate) | `typeclasses/characters.py:603–624` |
| Status display | `CmdStatus` | `commands/character_commands.py:27–76` |
| Garments | `warmth`, reserved `rain_protection`; `wear`/`remove` recompute | `typeclasses/clothing.py:49–56`, `:60–78` |
| A worn garment that leaves its wearer | `at_post_move` → `remove()` (L3.1) | `typeclasses/clothing.py:80–129` |
| Slot caps | `CLOTHING_TYPE_LIMIT` | `server/conf/settings.py:206–213` |
| Garment prototypes, recipes | straw hat, hood, robe…; wool tunic and fur cloak without recipe | `world/prototypes.py:563–682`; `world/recipes.py:187–279`, `:625–626` |
| Fur source | none in the alpha | `world/material_registry.py:203–208` |
| Garment wear reads the regime | `thermal_regime(room)` | `world/garment_wear.py:34`, `:96` |
| Weather states, seasons, broadcast | `WEATHER_STATES`, `SEASON_ALLOWED_WEATHER`, indoor silence | `world/weather.py:23`, `:28–33`, `:84` |
| Day periods, seasons | `TIMES_OF_DAY`, `_SEASONS` | `world/gametime_utils.py:46–61` |
| Room states | `room_states` injects period, season, weather | `typeclasses/rooms.py:198–252` |
| Microclimate pin, indoor per room | `thermal_regime`, `is_indoor` in seed data | `world/seed_data.py:53–56`; `world/seeding.py:149–152` |
| Tent | prototype, no sink | `world/prototypes.py:873–884` |
| Backfill pattern | idempotent migration | `world/character_migrations.py:54` |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 17. Open questions

- **KQ1** — A new stored gauge, or a reserve derived from a timestamp? *Leaning (chat, 2026-11-07): a gauge — it fits the survival category, the warnings pattern and `status`, and it drains at a rate that changes every tick, which a single anchor does not model without a history.*
- **KQ2** — Does *Exposed* deal the same damage as starvation? *Leaning: yes — one row in `HEALTH_CONDITIONS`, one knob, Legend's equality (KP-L3).*
- **KQ3** — The heat side in the same slice? *Leaning: yes, symmetric, since it is the same reserve and the same code path; it is light by design (§11).*
- **KQ4** — Wet in slice 1 or slice 2? *Leaning: slice 2 — it adds a state and a garment attribute's first reader, and slice 1 is already a new trait, a condition and a migration.*
- **KQ5** — A Survival (POW+CON) or Resilience (CON×2) skill now? *Leaning: no — CON already sizes the reserve; a skill arrives when something needs a roll (lighting a fire, Cooking CQ7; reading the weather, §14), and is named to avoid the `survival` gauge category, as `hunting` was.*
- **KQ6** — Does `status` show the reserve as a number like the other gauges, or as words? *Leaning: words and a direction — the side (cold or hot) is part of the meaning, and a percentage invites the minute-by-minute management KG5 avoids.*
- **KQ7** — With night (+1) and wet (−25 % a step), does the craftable wardrobe still answer a winter night without a fire? It reaches 6 against 5 at full condition and dry; does slice 1 need a seventh piece (gloves or socks have slots and no garment), or is the fire the intended answer?
- **KQ8** — Keep warmth linear in condition, or full warmth down to half condition (Vintage Story, §2.4)? The second makes repair a threshold decision and is kinder to a worn wardrobe; it also changes every shipped warmth sum below full condition.
- **KQ9** — *Dry* shelter: a state of the room (a pitched tent shelters everyone there) or of the people inside it (`enter tent`)? The first is simpler and wrong for a crowd; the second needs a container the character is in.
- **KQ10** — Warming food: does a hot dish give a timed warmth term, and is it Cooking's or this design's to own?
- **KQ11** — Exposed's threshold: a quarter of the reserve, or Legend-shaped hours of rest (The Long Dark's day above freezing)?

---

## 18. Considered and not proposed

- **Weather as flavour only.** Achaea's 2018 thread (§2.1): the crafted warmth becomes worthless.
- **Random harm from weather** — slipping, falling ice. Harm must be answerable (KG2).
- **Degrees.** Words and bands do the job with fewer numbers (§2.4).
- **Exposure in temperate weather.** KG4; a naked newcomer is hungry, not dying.
- **A thermal ticker, or a per-character script.** KG7; the survival tick already visits every online character.
- **Exposure while logged out.** KG6; the statue waits.
- **A −20 on every physical roll while exposed.** Legend doubles the *Fatigue test* penalty, not skill tests in general; the project's equivalent is the fatigue rate (KP-L2). `physical_modifier()` stays for overload and, later, fatigue levels.
- **Per-region climates now.** *Regional weather* is BLOCKED on the biome layer; a cold region built on today's global weather is the migration debt that entry exists to prevent. A staff pin (`room.db.thermal_regime`) already covers an authored cold cave or a heated hall.
- **NPC tailors or innkeepers selling warmth.** Pillar 1.
