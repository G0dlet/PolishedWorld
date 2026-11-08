# PolishedWorld — Rest, Sleep & Camp Design Notes (Legend's fatigue levels, the awake clock, sleep and the logout, where one sleeps, the bedroll, the camp)

> **Rev 1 · 2026-11-08** — first version, docs only, with roadmap Rev 58, BACKLOG Rev 83 and README Rev 37. Written from a design chat, the fourteenth in the series of one-system design notes that follows `docs/PolishedWorld_Fishing_Design.md`, `docs/PolishedWorld_Housing_Design.md`, `docs/PolishedWorld_Hunting_Design.md`, `docs/PolishedWorld_Cooking_Design.md`, `docs/PolishedWorld_Temperature_Design.md`, `docs/PolishedWorld_Farming_Design.md`, `docs/PolishedWorld_Textiles_Design.md`, `docs/PolishedWorld_Water_Design.md`, `docs/PolishedWorld_Foraging_Design.md`, `docs/PolishedWorld_Light_Design.md`, `docs/PolishedWorld_Forest_Design.md`, `docs/PolishedWorld_Rendering_Design.md` and `docs/PolishedWorld_Pottery_Design.md`. Fatigue is shipped — a gauge, a drain on the survival tick and a `rest` command — so the notes name the places they would change live behaviour (§6). **Nothing here is locked.** Every numbered item is a proposal (NP…), a goal (NG…) or an open question (NQ…); the letter is *N*, for night, free across `docs/`, `world/`, `commands/`, `typeclasses/` and `server/` when checked (Water's departure rows N1–N3 share the letter, not the shape). The departure rows are O1–O6; *O* was one of the free single letters. In the chat Adam approved writing the document from the proposal without answering its five questions; they are recorded here as NQ1–NQ5 with the leanings recommended in the chat, recorded as *leanings*, not as decisions. The leanings under the other questions are this document's own. Two things were found while writing that the chat did not weigh, and both are recorded rather than decided: the respawn the chat proposed changes the death message's contract (NQ14), and Housing Design gives a tent a rest term that this design gives to bedding (NQ1). The chat's provisional departure numbers are renumbered here in table order. Prior art was read on 2026-11-08; code seams were read against `main` at `8e9c259` (Evennia 6.1.0).
> **Canonical:** `docs/PolishedWorld_Rest_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one feature, before its decomposition).
**Home:** `docs/roadmap.md`, parallel backlog, *Rest, sleep & camp* — a new entry (Rev 58), because nothing owned the system: the gauge and `rest` came with the survival loop, BACKLOG *Fatigue-exhaustion consequence* owns only what happens at the bottom of the gauge, and the readers of sleep are each in their own design — Housing's rest at home (BP10), Forest's fire banked for a night (YP1), Light's dark nights (LP2), Foraging's natural healing (RP8). `docs/BACKLOG.md` gains two notes (Rev 83): *Fatigue-exhaustion consequence* — this design answers the open questions its direction B left (NP1–NP3, NP14); and *`DeathWeakness` debuff → `fatigue_rate`* — the re-point, and a respawn that wakes the body tired (NP15).
**When to read:** when BACKLOG *Fatigue-exhaustion consequence* is decomposed (§7, §10 — this is its design); when Foraging Design's natural healing or First Aid is decomposed (RP8, RP9 — the offline credit and the fatigue level, NP20, NP21); when Housing's shelter ladder, rest at home or furniture is decomposed (BP8–BP10 — bedding and beds, NP10, NP13); when Temperature's reserve and *Exposed* are decomposed (KP3, KP4 — the awake clock reads `fatigue_rate`, NP3); when Cooking's fire or Forest's fuel ships (CP1, YP1 — the fire through the night, NP16); when the weight decomposition's OQ1 calibrates the overload step (NP5); with *lodging & safe logout*, *markets & taverns*, *stealth, locks & theft* and *law/crime/bounties* from the design-series queue (beds rented, a statue robbed, NQ5, NQ13); when Stage 5 decomposes combat (surprise, heavy activity, the watch, NP18).
**Departs from shipped behaviour in six places**, listed with their source lines in §6: the gauge reads in Legend's six levels and the bottom bites; the gauge stops draining by the tick and is spent by an awake clock instead; `rest` slows to Legend's light-activity row; logging out is sleep; a sleeper cannot walk away; and a respawned body wakes tired.

---

## 1. The idea in one paragraph

A body that has been awake all day gets tired, and a body that has slept well wakes fresh. For most of a day nothing happens; past the hours a body can stand — longer for the hardy — it starts to flag, a level at a time, each level a little worse at everything, until at the bottom it falls asleep where it stands. Sleep is where the night goes, and for a player the night is the time away: logging out is lying down, and the statue that stands in the world while its player is gone is a body asleep. What a player chooses is *where* to lie down. On the bare ground a body rests but never fully — it wakes stiff and a little slow; in a bedroll, in a bed, on a straw pallet in the temple, it wakes fresh. So a traveller carries a bedroll, a bedroll wears thin with the nights, a bed can be built and kept and rented to strangers, and a camp is a fire banked for the night, a bedroll beside it and, later, someone awake to watch. Nobody waits through a night in real time, and nothing ticks while anyone sleeps.

---

## 2. Prior art

### 2.1 Ultima Online — the lesson

Sources: UOGuide, *Camping* and *Bedroll* (`uoguide.com`); the Ultima Online site's article on camping (`uo.com`); the UO Outlands wiki, *Camping* (`wiki.uooutlands.com`), read 2026-11-08. Paraphrased:

- Camping was a skill whose one use was to log out safely in the wilderness: kindling made a campfire, the camp became secure after about thirty seconds, and anyone near it could log out at once by unrolling a bedroll from a provisioner.
- It is described as almost never used, because even new players log out at a tavern or an inn, and as having lost what little use it had once players owned houses and could recall home; higher skill did not even shorten the wait.
- A later free shard rescued the skill by bolting unrelated rewards onto it — fast travel between secure campsites and a larger pack.

**Worth taking:** the camp as fire plus bedroll; one fire serving everyone at it.

**Not for PolishedWorld:** a skill whose only reward is a convenience; logout safety bought from an NPC provisioner (pillar 1).

**The lesson (the series' "Achaea lesson"; Achaea has a rule here but no story, §2.2):** UO's camping died because the one thing it gave — a place to log out — was given for free everywhere else, and no player chooses a cost that buys nothing. The rule taken: **where one sleeps must always matter** — not only for the minutes a player waits, but for what the body wakes as, even after a week away. So the place sets a *ceiling*, not just a rate (NP9): bare ground wakes a body Winded however long it slept; bedding wakes it Fresh. The bedroll is worth carrying because the free alternative is measurably worse, and that is Legend's own line (AoL `:146`, §4).

### 2.2 Achaea — a rule, not a story

Source: Achaea help 5.15 *Sleeping* (`achaea.com`), and players' forum threads on the insomnia and kola defences (`forums.achaea.com`), read 2026-11-08. Paraphrased:

- A character grows more tired every Achaean day and must sleep; asleep, it slowly regains health and grows rested, and wakes on its own when fully rested and healed. `WAKE` starts a struggle out of sleep rather than waking at once.
- Sleep can be forced by venoms and a tattoo; a root gives *insomnia*, which a sleep attack strips before it can put the victim under, and a nut lets the sleeper wake at will. Most of the talk about sleep is about this — sleep as a combat affliction.
- Characters past a high attainment no longer need sleep naturally, and may switch tiredness back on if they want it.

**Worth taking:** waking on one's own when rested (NP7); a sleeper who can be woken; sleep as a vulnerability, for Stage 5.

**Not for PolishedWorld:** sleep as a daily chore waited through online — the game's own advanced players are excused from it.

### 2.3 Wurm Online — the bed and the absent player

Sources: Wurmpedia, *Sleep bonus*, *Bed*, *Sleep* (`wurmpedia.com`), read 2026-11-08. Paraphrased:

- A player logs out *in a bed* inside a completed house and accumulates a sleep bonus the longer they are offline — about a minute of bonus for every twenty-four asleep, up to a cap of a few hours. While the bonus runs, skill gain is doubled and stamina returns faster. The wiki states the aim: to help players who cannot play many hours a day without hindering those who can.
- A straw bed gives three-quarters of the gain, and a bedroll used by a tent the same. Sleeping damages a bed whether or not the house is on a deed.
- A bed's owner can rent it for a fixed sum, which makes running an inn a way to earn money.

**Worth taking:** the logout as sleep, and the place of it mattering (NG1, NP19); bedding ranked by quality; beds that wear by being slept in (NP13); renting a bed as a player's service (pillar 1).

**Not for PolishedWorld:** a skill-gain multiplier earned offline (NQ3); a bed usable only inside a finished house.

### 2.4 Valheim — the camp as fire and roof

Sources: the Valheim comfort guides of Mobalytics, Indifferent Broccoli's wiki and game8 (read 2026-11-08). Paraphrased:

- A character becomes *Rested* by resting about twenty seconds by a lit fire, sitting, or standing under shelter in reach of a fire; *Rested* then lasts for a while after leaving.
- Its length grows with *comfort*: a fire in the open counts for little, a roof and a fire for more, and furniture — a bed, chairs, rugs, a hearth — adds to it. Comfort lengthens the effect; it does not make it stronger.

**Worth taking:** fire and roof as the camp's two halves (NP16, Temperature KP6, KP8); better places give *longer* good states, not stronger ones (NP9's ceiling).

**Not for PolishedWorld:** a buff that counts unique furniture items near the sleeper.

### 2.5 The Long Dark — bedding and needs

Source: The Long Dark wiki, *Sleep*, *Bed*, *Bear Skin Bedroll* (`thelongdark.fandom.com` and its archive), read 2026-11-08. Paraphrased:

- Sleep needs a bed or a deployed bedroll; a survivor cannot sleep on the floor or a chair. Sleep restores fatigue and is the main way to recover condition — but only while no need is empty; a sleeper who freezes, starves or thirsts loses condition, and can die asleep.
- A bearskin bedroll is much warmer than a cloth one; a vehicle can be slept in without one.

**Worth taking:** bedding as what makes sleep complete (NP9, NP10); healing only while needs are met — Legend's own rule (p. 90, NP20); a fur bedroll for the hunter's path (NP11).

**Not for PolishedWorld:** dying in one's sleep while logged out — a statue's needs do not run (§12).

### 2.6 The Diku lineage — sit, rest, sleep, wake

Sources: Aardwolf's help on *rest* (`aardwolf.com`) and MUME's help on *sleep* (`mume.org`), read 2026-11-08. Paraphrased:

- Positions — sit, rest, sleep, stand — set how fast a character regenerates; hunger, thirst and some rooms slow it. A character can wake another who went to sleep by choice.
- In MUME, sleeping by a campfire or in a comfortable bed gives a small boost.

**Worth taking:** `wake <name>` (NP7); a fire and a bed as what makes a sleep better.

---

## 3. Design goals

- **NG1 — The night is the logout.** The body's sleep is spent while the player is away; nobody waits through a night in real time (§2.2, §2.3). Online sleep exists for a nap and for a collapse, not for the night.
- **NG2 — Where one sleeps always matters.** The place sets what a body wakes as, however long it slept (§2.1).
- **NG3 — The ramp before the cliff.** Each level is felt before the next; the bottom is the last step, never the first consequence (BACKLOG *Fatigue-exhaustion consequence*, direction B).
- **NG4 — Every harm has an answer within reach.** A collapse always ends by logging out; the temple's pallets give the first night free (Temperature's rule; Pottery PG2's for the first of everything).
- **NG5 — Nothing ticks for sleep.** Sleep is worked out from stamps when it ends or is read; the survival tick already wakes for everyone online and carries the awake clock.
- **NG6 — Rest is a product.** Bedding is made and wears out; a bed is built, kept and rented. Nobody sells sleep but a player.

---

## 4. Legend alignment

**Rules as written:**

- **Fatigue** — core p. 89: physical activity is light, medium or heavy. *Light* — travelling at a reasonable pace, light loads — never risks Fatigue. *Medium* — back-breaking manual labour, running, climbing, swimming — risks it after CON minutes, then a Simple (+20 %) Athletics test every CON minutes; *heavy* — combat, sprinting — after CON Combat Actions, a Normal Athletics test. Each failed test drops one level. *Time and Fatigue:* after 10+CON hours awake, regardless of activity, a Persistence test each hour or drop one level. *Recovering:* one level up for every **two hours of complete rest** or **four hours of light activity**; a successful First Aid or Healing test raises one level once per day but **never above Winded**.
- **Fatigue Levels** — p. 90: Fresh (none); Winded −10 % to all skill tests, including further tests to resist Fatigue; Tired −20 %, movement −1 m; Wearied −30 %, Strike Rank −2; Exhausted −40 %, movement halved, a Persistence test every minute or fall unconscious for 1D3×2 hours; Debilitated −50 %, a Difficult Persistence test every Combat Round or fall unconscious for 1D6×2 hours.
- **Exposure, starvation and thirst** — p. 90: after three days without food, −10 % to Fatigue tests; while exposed, starving or thirsty the Fatigue test penalty doubles to −20 %, and natural healing cannot heal the damage until the need is met. **Overloaded** — p. 86: −20 % to all Fatigue tests.
- **Abstract Fatigue** — pp. 90–91: a GM may call a Simple Athletics test after each *major exertion* instead of counting time, harder with each one; a rest between them may reset the clock.
- **Natural healing** — pp. 86–87: one Hit Point per 72 to 12 hours by Resilience; only light activity is allowed, anything strenuous drops the rate one row.
- **Survival** — p. 63: one test every day an Adventurer lacks food, water or *a safe place to sleep*; not used in towns.
- **Equipment** — p. 112: the bedroll, *a blanket and cushioned pad*, tied with a metre of leather cord, ENC 1. p. 118: the four-person tent keeps four dry but is not comfortable, *which is why so many Adventurers invest in good bedrolls*. p. 99: a winter cloak may serve as a warm blanket and bedroll. p. 111: lodging, poor to superior.
- **Surprise** — p. 138: a character attacked asleep is surprised; a freshly woken one may be at −20 %, groggy.
- **Arms of Legend** (`docs/reference/arms_of_legend.md`): the bedroll — *without a bedroll, sleeping on the open ground does not count as complete rest for the purposes of healing or recovering from Fatigue*; it can serve as a stretcher (`:146`); the tents (`:480–482`); the winter cloak as blanket and bedroll (`:734`); the sleeping draught, a full eight hours' rest despite troubles (`:460`); the everyday tonic, a full night's sleep in six hours (`:224`); the tree net for sleeping off the ground (`:498`); insect netting for camping in swamps (`:314`).

**Translation proposals:**

- **NP-L1 — Persistence is Athletics.** The codebase has five skills and no Persistence (`world/chargen.py:59–65`); BACKLOG *Fatigue-exhaustion consequence* (direction B) already chose Athletics for every Fatigue test.
- **NP-L2 — Hours are game hours.** As Forest YP-L5: two hours of complete rest are thirty real minutes at the 4× clock (`server/conf/settings.py:50–64`); 10+CON hours awake are five to seven real hours online for CON 10 to 18.
- **NP-L3 — `rest` is light activity.** Sitting awake and resting is Legend's light-activity row; walking about, crafting and chores are light activity that neither tires nor restores (p. 89: light activity never risks Fatigue).
- **NP-L4 — Medium and heavy work is abstract Fatigue, later.** Counting CON minutes of labour is replaced by pp. 90–91's test after a major exertion (NP4); heavy activity is combat, Stage 5's.
- **NP-L5 — The levels' movement, Strike Rank and Combat Action effects wait for Stage 5.** A room-based world has no metres; only the skill-test penalty is taken now.
- **NP-L6 — Unconsciousness is the collapse, at the bottom only.** Exhausted's test every minute and the 1D3×2 and 1D6×2 hours are not taken: a collapse comes at Debilitated and lasts until the body is out of that level (NP14). Thirty to ninety real minutes of a forced state is far too long (BACKLOG's own finding).
- **NP-L7 — The bedroll rule is the ceiling.** AoL `:146` and p. 89's *never above Winded* together become NP9: sleep without bedding never lifts a body above Winded.
- **NP-L8 — Survival tests and prices are not used.** There is no Survival skill (`world/chargen.py:59–65`); the place's ceiling stands in for p. 63's safe place to sleep. Lodging prices (p. 111) are not used — pillar 1.

---

## 5. The loop

Proposed phases; each is something someone can sell.

1. **Wake.** Fresh, or Winded off the bare ground; the awake clock starts (NP3).
2. **Work.** Hours of ordinary work tire nothing until the body's hours are spent; hauling overloaded costs a little per room (shipped), heavy work later a test (NP4).
3. **Flag.** Past the hours, a level at a time; each level a penalty a player feels on every roll (NP1, NP2).
4. **Make camp.** A fire fed for the night, a bedroll unrolled, a tent against the rain (NP16, NP11; Housing BP8).
5. **Sleep.** A nap online, or the night away — logged out, the body asleep where it lay (NP7, NP19).
6. **Wake rested.** As far as the place allowed (NP9); a bedroll a little more worn (NP11).

---

## 6. Departures from shipped behaviour

Each row is a change to behaviour that `main` has today; each is a proposal.

| # | Shipped today | Proposed | Where shipped |
|---|---|---|---|
| O1 | The fatigue gauge has six descriptions (*exhausted* … *energetic*) and nothing happens at any value, zero included; no roll reads it | The six descriptions become Legend's six levels on twenty-point bands, each with its penalty read through `physical_modifier()`, and the bottom band can collapse the character (NP1, NP2, NP14) | `typeclasses/characters.py:316–331`, `:603–625`; `world/survival_ticker.py:28–35` |
| O2 | The survival tick drains one point of fatigue from every online character, scaled by `fatigue_rate` | The tick no longer drains the gauge; it advances an awake clock by the same `fatigue_rate`, and past 10+CON game hours rolls Athletics once a game hour, a failure costing one level (NP3). The overload step per room is unchanged | `world/survival_ticker.py:21`, `:58–68` |
| O3 | `rest` restores five points every ten real seconds, to full, anywhere | `rest` is Legend's light activity: one level per four game hours (one real hour), never above Winded; `sleep` is complete rest (NP6) | `typeclasses/characters.py:1180–1182`, `:1369`, `:1693–1736`; `commands/consumption_commands.py:117` |
| O4 | A logged-out character's gauges are frozen; logging out neither rests nor tires | Logging out is sleep: at the next login the time away is credited as sleep at the place's row, up to the place's ceiling (NP19) | `world/survival_ticker.py:45–46`; `typeclasses/characters.py:472`, `:494` |
| O5 | Every timed action ends when the character moves, and the move goes ahead | A sleeper, and a collapsed character, is refused the move until awake (NP7, NP14) — the first timed action that refuses rather than interrupts | `typeclasses/characters.py:1444–1468`; `world/timed_actions.py:229` |
| O6 | Respawn leaves fatigue as it was; `DeathWeakness` raises hunger and thirst rates by a quarter for 300 s | Respawn sets the gauge to Wearied; `DeathWeakness`'s two mods move to `fatigue_rate`, as BACKLOG *`DeathWeakness` debuff → `fatigue_rate`* intends; the death message's line about the weakness changes with it (NP15, NQ14) | `typeclasses/characters.py:1337–1347`, `:1362–1363`; `world/survival_buffs.py:91–135`; `world/death_contract.py:132` |

Unchanged: the overload step of one point per room (`world/encumbrance.py:70`, `typeclasses/characters.py:1505–1509`); `ColdStress` and `HeatStress` and their `fatigue_rate` mods (`world/survival_buffs.py:68`, `:87`), which now scale the awake clock (NP3); the statue (`typeclasses/characters.py:472`); hunger and thirst on the tick; the tent item and its recipe (`world/prototypes.py:872–884`, `world/recipes.py:483–496`).

---

## 7. Fatigue and its levels

**NP1 — Six levels on the shipped gauge.** The gauge stays 0–100 (`typeclasses/characters.py:316–331`). Its six descriptions — the shipped keys are upper bounds, inclusive (`GaugeTrait.desc`, Evennia 6.1.0 `evennia/contrib/rpg/traits/traits.py`) — become Legend's six words on twenty-point bands: **Debilitated** at 0, **Exhausted** 1–20, **Wearied** 21–40, **Tired** 41–60, **Winded** 61–80, **Fresh** 81–100. A level lost is twenty points; a level regained is twenty. `status` already prints the gauge and its word (`commands/character_commands.py:74–76`), and the survival warning already fires when the word gets worse (`world/survival_ticker.py:104`); both read the new words with no change of their own. The words are what a player is told; the number stays in `status` as today.

**NP2 — The penalty is read where overload's is.** Each level's penalty — 0, −10, −20, −30, −40, −50 — is added in `Character.physical_modifier()` (`typeclasses/characters.py:603–625`) beside `OVERLOAD_PENALTY` (`world/encumbrance.py:63`), the seam the weight decomposition left for exactly this (BACKLOG annotation 2026-10-30). Read live at each roll and never stored, so a nap mid-session shows on the next roll. Legend applies the penalty to *all* skill tests; every roll in the codebase today is one of the six physical ones the method's docstring lists, so the two coincide for now, and a later non-physical roll (Lore, Evaluate) is NQ4's question — Light Design's `light_modifier()` (LP10) is the same question from the other side.

**NP3 — The awake clock (O2).** A body is not tired by the clock until it has been awake 10+CON game hours (p. 89). The survival tick, which already wakes every 600 s for every online character (`server/conf/at_server_startstop.py:27`, `world/survival_ticker.py:37`), stops draining the gauge and instead adds the game time since the last tick to a per-character awake clock, multiplied by `fatigue_rate` exactly as the drain is today (`buffs.check(base, "fatigue_rate")`, `world/survival_ticker.py:58–68`). So everything that already raises `fatigue_rate` keeps its meaning — `ColdStress` and `HeatStress` (`world/survival_buffs.py:68`, `:87`) spend the hours faster, Temperature's *Exposed* doubles them (KP4), and a respawn's chill (NP15). Once the clock passes 10+CON hours, each further whole game hour rolls **Athletics** (NP-L1) at the level's own penalty (NP2), at a further −20 while *Starving*, *Dehydrated* or *Exposed* (p. 90); a failure costs one level. The clock is reset by sleep (NP8), not by `rest`. With today's clock the body's day is five to seven real hours online; most sessions end before the first test, which is the point (NG1): fatigue bites the long day and the overloaded road, not the evening's play.

**NP4 — Heavy work, later: one test per major exertion.** Legend's medium activity (manual labour) becomes pp. 90–91's abstract Fatigue: a Simple (+20 %) Athletics test after a major exertion, failure costing one level. Candidates, each with the act that ships it: felling a standard (Forest YP6), a building stage (Housing), opening a charcoal clamp or a firing pit (Forest YP8, Pottery PP3). None in the first slice; each act's own decomposition decides whether it is major.

**NP5 — The other ways down stay as they are.** The overload step — one point for every room entered past the limit (`world/encumbrance.py:70`, `typeclasses/characters.py:1505–1509`) — is unchanged, and now means something: twenty overloaded rooms are a level. Its calibration stays the weight decomposition's OQ1. Foraging Design's *Nausea* gains its level of Fatigue on stressful action (RP11's note that it waits for BACKLOG *Fatigue-exhaustion consequence*): one level, twenty points.

---

## 8. Sleeping and resting

**NP6 — Two rows, two verbs (O3).** Legend has two ways up (p. 89), and each gets a verb:

| Verb | Legend row | Rate | Ceiling | Resets the clock |
|---|---|---|---|---|
| `rest` — sit awake | light activity | one level per 4 game h (1 real h) | Winded | no |
| `sleep` — lie down | complete rest | one level per 2 game h (30 real min) | the place's (NP9) | yes, after a night (NP8) |

Both are measured from elapsed game time when they end or are read, with the remainder carried — the shape of Foraging RP8's healing counter and the `ResourceNode` anchor (`typeclasses/resources.py:67–97`) — rather than by a repeating ten-second tick as `rest` is today (`typeclasses/characters.py:1693–1736`). `rest` keeps its toggle, its slot and its messages (`commands/consumption_commands.py:117`, `typeclasses/characters.py:1369`, `:1417`); only its rate and ceiling change.

**NP7 — `sleep` and `wake`.** `sleep` takes the shared timed-action slot as `rest` does (`world/timed_actions.py:107`), refused while Fresh (*You are not tired*, the shipped line) and refused when the place's ceiling is already reached. A sleeper:

- **cannot walk away** — a move is refused with *You are asleep* (O5), where every timed action today is interrupted and the move allowed (`typeclasses/characters.py:1444–1468`);
- **sees and hears little** — `look` and the room's chatter are not shown; the room shows the sleeper as *asleep* beside the name, as it shows a statue (`typeclasses/characters.py:518`);
- **puts out what it holds** — a held light is snuffed on falling asleep, as Light LP11 does on logging out; a fire in the room burns on;
- **wakes by `wake`**, at once in v1 (Achaea's struggle out of sleep is Stage 5's, with surprise, p. 138); **by another's `wake <name>`** (§2.6) — any character in the room may wake any sleeper, the first social act of a camp; and **on its own** when the ceiling is reached, by one scheduled call (NP19's arithmetic run forward), with a line in the room.

**NP8 — Sleep resets the clock after a night.** A sleep of eight game hours or more — a night, two real hours, the sleeping draught's *full eight hours* (AoL `:460`) — sets the awake clock to zero. A shorter sleep takes its length off the clock, so a nap buys back the hours it lasted and no more. The same rule serves online sleep and the logout (NP19), so logging out for ten minutes is a ten-minute nap and nothing else.

---

## 9. Where one sleeps

**NP9 — The place sets the ceiling (§2.1, NP-L7).** Sleep with no bedding is not complete rest (AoL `:146`), and Legend already has the line it stops at: p. 89's *never above Winded*. So:

| Where | Row | Wakes as |
|---|---|---|
| bare ground, floor, a tent with no bedding | light activity | Winded at best |
| bedding — a bedroll, a winter cloak worn, a bed, a pallet | complete rest | Fresh |

A body asleep on the bare ground, however long, wakes Winded: −10 on every roll until it sleeps properly. The ceiling is what survives a week away — rates stop mattering once a player is gone longer than a night, ceilings do not.

**NP10 — What counts as bedding.** One duck-typed question, asked of the sleeper's inventory and worn things and of the room — proposed `bedding()`, the way Temperature KP8 asks `radiant_warmth()` and Light LP3 asks `light_emitted()` — answered by: a **bedroll** carried (unrolled as the sleeper lies down; NP11); a **winter cloak** worn (AoL `:734`, core p. 99; Textiles Design §13's immersion note, waiting on the cloak); a **bed** in the room the sleeper takes (NP13); a room that is bedded throughout — the temple's **pallets** (NP12). A roof is not bedding and neither is a tent: shelter is warmth and dryness, Temperature KP6's two halves, and a tent is *not exceptionally comfortable* (core p. 118, AoL `:480`). This differs from Housing Design, which gives the tent and lean-to a smaller rest term and the roof a larger one (BP8, BP10); this design proposes that Housing's rest term is the bedding inside, and the roof's gift is Temperature's (NQ1).

**NP11 — The bedroll.** Legend's own shape (p. 112): a blanket, a pad and a cord. Proposed as a recipe in the **weaving** discipline (`world/recipe_mastery.py:81–87`, as the sack is, `world/recipes.py:315–320`): 2 cloth (the blanket), 2 plant fibre for the pad — straw once straw has a source (registry `world/material_registry.py:153–158`, DATA; Foraging RP14) — and 1 leather for the cord (`:265`); a needle as tool, as the tent (`world/recipes.py:494`). ENC 1 (p. 112). It is a `DurableObject` (`typeclasses/durable.py:41`): each night slept on it costs a little `condition` through `apply_wear` (`:43`) — Wurm's bed that wears (§2.3) — and at zero it is a bundle of rags that is no longer bedding. It mends with cloth by the shipped `repair` (`commands/repair_commands.py:121`'s per-target materials). A fur bedroll for the hunter's path, warmer (The Long Dark's bearskin, §2.5), waits on fur's source (Textiles). Rung, wear and the recipe's source are NQ10 and NQ11.

**NP12 — The temple's pallets.** The Old Temple, already the newcomer's lit room (Light LP2's pin) and the respawn point, is bedded throughout: straw pallets along the walls, a room attribute rather than objects, no occupancy and no wear. A newcomer's first nights need no bedroll (Pottery PG2's rule; Forest YG4's free fuel; NG4). The pallets are not sold and cost nothing; they are a floor, like the clay bank and the deadfall, and they are at the temple — a traveller far from it still needs a bedroll. The description gains a line for them (`world/seed_data.py:81–92`). Room-wide or per pallet is NQ12.

**NP13 — Beds.** A bed is furniture — Housing Design's ordinary crafted item, woodwork, set into a room (§*Furniture*, after BP10) — and this design says what it does: it is bedding (NP10) for **one** sleeper. Taking a bed is a claim made at `sleep` or logout in one synchronous step; a second sleeper is told it is taken. A statue in a bed holds it while its player is away — *asleep under a blanket, gone to stone* — and frees it on login. A bed wears a little per night, as the bedroll does (§2.3), and is mended with cloth. Whose bed may be slept in is the owner's to say; renting one for the night is a tavern-keeper's service, and its mechanism — a price, a key, a night — belongs with *markets & taverns* and *workshops & shared stations* (NQ13).

---

## 10. Collapse and death

**NP14 — Collapse at the bottom (O1, O5).** At Debilitated each survival tick rolls a **Difficult** (−20) Athletics test at the level's −50 (p. 90's Debilitated row; NP-L6). A failure puts the character to sleep where it stands: a forced `sleep` it cannot `wake` from, ending on its own when the body is out of Debilitated — one level, so two game hours (thirty real minutes) on bedding, four (an hour) on the bare ground (NP6). It cannot move (O5), eat or drink (NQ9). It **can always log out** — the statue sleeps the rest (NP19), so the answer is within reach (NG4). Collapsing outdoors in a winter night is dangerous, and meant to be: the body is online, Temperature's reserve keeps draining (KP3), and a companion's fire or a cloak laid over it is the help a friend gives. This answers BACKLOG *Fatigue-exhaustion consequence*'s open questions: the forced rest's length (one level), eating during it (no, NQ9), the thresholds (twenty-point bands), a harder test at depth (Difficult at the bottom only), and movement refused.

**NP15 — Death's chill is tiredness (O6).** A respawned body wakes **Wearied** — the gauge set to 40, the awake clock at zero — and `DeathWeakness` keeps its name, its messages and its 300 s, with its two mods moved from `hunger_rate` and `thirst_rate` to `fatigue_rate` (`world/survival_buffs.py:132–133`), the target its own docstring names (`:109–113`). So a body back from death is slow at everything until it sleeps, and tires faster for its first minutes. The death message promises that the weakness *passes on its own* (`world/death_contract.py:132`), which stays true of the buff but not of the level: the line gains *and sleep mends the weariness*. That is a change to the player contract the death-consequence policy (v) put in the message, so it is NQ14's to ratify at roadmap altitude, not this design's.

---

## 11. The camp

**NP16 — The fire through the night.** A fire holds at most eight game hours of fuel — one night — so a sleeper can bank it at dusk and wake to embers (Forest YP1). For a sleeper online it is warmth — Temperature KP8's term against KP5's cold night — and light — Light LP3's, in a night that is dark under cloud (LP2). For a statue it is nothing: nothing the body needs runs while its player is away (§12). The camp's fire is the online sleeper's, the nap and the collapse; the night away needs only bedding.

**NP17 — One camp, many sleepers.** One fire serves everyone in the room, as every light and every warmth does (LP3, KP8); bedding is each sleeper's own (NP10). A pitched tent keeps the rain off everyone in it, Housing BP8's rung 0 and Temperature KP6's *dry* (KQ9's open question of whom it covers stays there).

**NP18 — The watch, later.** Someone sitting up by the fire while others sleep is a camp's oldest job, and Legend has the reason: a sleeper attacked is surprised (p. 138). Today nothing comes in the night — no predators, no thieves — so a `watch` would guard against nothing. It is proposed with Stage 5's surprise and with *law/crime/bounties*: a watcher stays awake (light activity, `rest`'s row), sees who enters, and can `wake` the camp (NP7). Until then, the waking of one sleeper by another is the whole of it.

---

## 12. Offline and the world

**NP19 — Logout is sleep (O4).** When a character is unpuppeted (`typeclasses/characters.py:472`) the time and the place are stamped on it: when it lay down, and whether it had bedding (NP10) — a bed claimed then and there. At the next login (`:494`) the game time away is credited once, as one sleep, at the place's row and up to its ceiling (NP6, NP9), and the clock is reset or reduced by NP8. A line tells the player how they woke: *You wake stiff from the hard ground* or *You wake rested*. Nothing is computed while the player is away, and nothing about the statue changes. Link-dead counts as lying down: a dropped connection is a nap, not a penalty.

Hunger, thirst, temperature and the rest of the body stay frozen while logged out, as shipped (`world/survival_ticker.py:45–46`) and as Cooking Design's rule for carried food: a statue cannot starve, freeze or be woken by the cold, so a camp's fire and a tent matter to the online sleeper, not to the statue (NP16).

**NP20 — Healing rides the same credit.** Foraging Design's natural healing (RP8) adds game time to a counter on the survival tick and grants a hit point each interval of the character's row. The login credit adds the time away to the same counter, so a body heals while its player sleeps — the one way a casual player heals at all at Legend's rates (RP8: one hit point per forty-eight game hours at CON 10–15, p. 86 — twelve real hours). Not while *Starving* or *Dehydrated* at logout (p. 90; RP8 already says so). On the bare ground, one row slower (AoL `:146`; NQ2). Sleep and rest are the light activity p. 87 asks for, which answers Foraging RQ17 for these two acts; whether other work drops the row stays RQ17's.

**NP21 — First Aid raises a level.** A successful First Aid test raises one level once a game day, never above Winded (p. 89). With Foraging RP9's `first_aid` skill and its kit, on the same act. Not before RP9 ships.

---

## 13. Economy

**Sources (all player-made or free floors):** the bedroll (NP11, a weaving recipe); beds (Housing's furniture); the temple's pallets (NP12, a free floor that is neither sold nor carried).

**Sinks:** the bedroll's wear per night slept and its cloth for mending (NP11); a bed's wear per night (NP13); the cloth, plant fibre — straw later — and leather the bedroll takes; and time: a body on the bare ground pays −10 on every roll until it sleeps on bedding (NP9). The fire burnt through a night is Forest's sink (YP1), now with a second reason to burn it.

**Materials this design gives a sink:** **cloth** and **leather** (the bedroll, beside garments); **plant fibre** (padding); **straw** (padding, once it has a source — its registry row already names *bedding* among its intended sinks, `world/material_registry.py:153–158`); the **tent**, a little: a tent pitched over bedding keeps a camp dry, though the tent's own sink is Housing BP8's pitching and striking.

**Services:** making and mending bedrolls; a bed rented for the night — the inn, Wurm's player-run lodging (§2.3), the tavern-keeper's room at *markets & taverns*; keeping a camp's fire through the night for a party (Forest §13); later, standing watch for hire (NP18); hauling, now that twenty overloaded rooms cost a level (NP5).

**Exclusives:** none proposed.

**Coin:** none. **Logging:** a night slept, a collapse and a bedroll worn out are NQ16.

**NP22 — The master constant, on one page.** At today's clock (`server/conf/settings.py:50–64`) and Legend's rows: a body's day is 10+CON game hours, **five to seven real hours online**; a night is eight game hours, **two real hours away**, worth four levels on bedding (NP6) — so a body at the very bottom is Fresh after two and a half real hours away on bedding, and Winded after four on the bare ground, where it stops. A player who logs out once a real day sleeps one night a real day; at a wear of two `condition` a night, a bedroll lasts about **fifty nights** — some seven real weeks, two thirds of a game season (NQ11). Healing rides it at RP8's row: a hit point every twelve real hours at CON 10–15, online or away (NP20). Every number here is a leaning and moves together; the decomposition tunes this table, not the verbs one by one.

---

## 14. Multiplayer and server load

- **Nothing new ticks.** The awake clock rides the survival tick that already runs (`world/survival_ticker.py:37`), and a test is rolled only past 10+CON hours — one comparison per online character otherwise. Sleep and rest are worked out from stamps when they end or are read (NP6); the logout credit is one calculation at login (NP19). The one scheduled call is a sleeper's own wake-up (NP7), `persistent=False` like every timed action (`world/timed_actions.py:107`); after a reload the sleeper simply sleeps on until woken, and the arithmetic is the same.
- **Many sleepers, one room.** Each sleeper's state is its own; a fire and a tent are read, never written, by the people they serve (NP17).
- **Two sleepers, one bed.** The claim is checked and set in one synchronous step at `sleep` or at logout; the reactor is single-threaded, so the second is told the bed is taken (NP13).
- **Waking another.** `wake <name>` checks the target is asleep and in the room in the same command; a collapsed character is not woken by it (NP14).
- **Login storms.** The credit is a handful of arithmetic per login, no queries beyond the character's own attributes.
- **Wilderness.** A bedroll is carried, so it works anywhere; a bed is furniture in an authored or built room; Stage 6's wilderness needs nothing of this design.

---

## 15. Immersion extras

- **How one woke.** The login line says it: *stiff from the hard ground*, *rested*, *the fire is cold ash beside you* if a fire burnt out in the room while the statue slept.
- **The sleeper in the room.** *Mara lies curled in a bedroll, asleep.* A statue in a bed reads *asleep under a blanket, gone to stone* (NP13).
- **Waking a friend.** *You shake Mara awake.* — the camp's first act of company.
- **Dreams, sometimes.** A line on waking from a long night, by season — never information, only colour.
- **The bedroll as a stretcher.** AoL `:146`: unrolled and lashed, a bedroll carries the wounded — with Stage 5's wounds.
- **The everyday tonic and the sleeping draught.** A full night's rest in six hours (AoL `:224`); sleep despite any trouble (`:460`) — with *alchemy & poisons*.

---

## 16. Layers — a suggested order

1. **Slice 1, BACKLOG *Fatigue-exhaustion consequence*:** the six levels and their penalty (NP1, NP2, O1); the awake clock (NP3, O2); the collapse (NP14, O5 for the collapse); Nausea's level when RP11 ships (NP5); the respawn (NP15, O6) once NQ14 is ratified. Needs nothing new.
2. **Slice 2, sleep:** `rest` and `sleep` on their rows (NP6, O3); `sleep` and `wake` (NP7, O5); the clock reset (NP8); the ceiling and the bedding question (NP9, NP10); the temple's pallets (NP12); logout as sleep (NP19, O4).
3. **Slice 3, the bedroll:** the recipe, its wear and mending, and its source (NP11).
4. **With Foraging's healing and First Aid:** healing on the login credit (NP20); First Aid's level (NP21).
5. **Later:** beds, with Housing's furniture (NP13) and renting with *markets & taverns*; heavy work, with felling and building (NP4); the watch, with Stage 5 and *law/crime/bounties* (NP18); the winter cloak with Textiles; the fur bedroll with fur's source.

**Prerequisites:** slice 1 needs nothing; slice 2 needs slice 1; slice 3 needs slice 2 and a recipe source (`tests/test_recipe_sources.py`); slice 4 needs Foraging RP8 and RP9.

---

## 17. Seams in today's code (read at `8e9c259`)

| Need | Seam | Where |
|---|---|---|
| The gauge | `fatigue`, 0–100, six descs as upper bounds | `typeclasses/characters.py:316–331`; `GaugeTrait.desc` (Evennia 6.1.0) |
| The drain | `BASE_RATES`; `buffs.check(base, "<key>_rate")` per tick; offline skipped | `world/survival_ticker.py:21`, `:58–68`, `:45–46` |
| Zero conditions | `HEALTH_CONDITIONS`, fatigue deliberately absent | `world/survival_ticker.py:28–35` |
| Warnings | bucket drop warning, reads the descs | `world/survival_ticker.py:104` |
| The tick | every 600 s | `server/conf/at_server_startstop.py:27` |
| Rate mods | `ColdStress`, `HeatStress` on `fatigue_rate`; `DeathWeakness` on hunger and thirst | `world/survival_buffs.py:68`, `:87`, `:91–135` |
| Penalty seam | `physical_modifier()`; `OVERLOAD_PENALTY` | `typeclasses/characters.py:603–625`; `world/encumbrance.py:63` |
| Overload step | one point per room | `world/encumbrance.py:70`; `typeclasses/characters.py:1505–1509` |
| Rest | knobs; `start_resting`; `stop_resting`; `_rest_tick`; the command | `typeclasses/characters.py:1180–1182`, `:1369`, `:1417`, `:1693–1736`; `commands/consumption_commands.py:117` |
| Timed acts | `is_busy`, `start`, `is_current`, `claim`, `interrupt`; `at_pre_move` interrupts | `world/timed_actions.py:89`, `:107`, `:168`, `:198`, `:229`; `typeclasses/characters.py:1444–1468` |
| Statues | unpuppet keeps the body; puppet wakes it; the statue's name | `typeclasses/characters.py:472`, `:494`, `:518` |
| Respawn | restore block; `DeathWeakness` added | `typeclasses/characters.py:1337–1347`, `:1362–1363` |
| Death message | the weakness line | `world/death_contract.py:98`, `:118`, `:132` |
| Health | one pool, `rate=0` | `typeclasses/characters.py:340` |
| Skills | five, Athletics among them; `skill_check` | `world/chargen.py:59–65`; `world/skillcheck.py:58` |
| The tent | prototype, no sink; recipe, needle | `world/prototypes.py:872–884`; `world/recipes.py:483–496` |
| A bedroll's parts | cloth, leather, plant fibre, straw DATA; weaving discipline | `world/material_registry.py:254`, `:265`, `:93`, `:153–158`; `world/recipe_mastery.py:81–87`; `world/recipes.py:315–320` |
| Wear and mending | `condition`, `apply_wear`; per-target repair materials | `typeclasses/durable.py:41`, `:43`; `commands/repair_commands.py:121` |
| The temple | seeded room; the tent's scroll | `world/seed_data.py:81–92`, `:250–251` |
| Status | gauge and word printed | `commands/character_commands.py:74–76` |
| Clock | 4× speed; night 20–04 | `server/conf/settings.py:50–64`; `world/gametime_utils.py:46–54` |

Re-read every row against live source before the decomposition locks anything (lesson: live source wins).

---

## 18. Open questions

- **NQ1** — Does a roof without bedding count as bedding? *Leaning (chat, 2026-11-08): no — a roof is warmth and dryness (Temperature KP6), bedding sets the ceiling (NP9, NP10). This differs from Housing Design BP8 and BP10, which give the tent, the lean-to and the roof a rest term; the decompositions reconcile it, with this design's proposal that Housing's rest term is the bedding inside the house.*
- **NQ2** — Does sleep on the bare ground heal one row slower? *Leaning (chat, 2026-11-08): yes (AoL `:146`; NP20).*
- **NQ3** — A skill-gain bonus after a night in a bed, as Wurm's sleep bonus (§2.3)? *Leaning (chat, 2026-11-08): not in v1; recorded so it is asked once. The anti-grind throttle (roadmap, *Anti-grind throttle*) is the reason to be careful.*
- **NQ4** — Is the fatigue penalty read in `physical_modifier()`, or in a modifier every roll reads, physical or not? *Leaning (chat, 2026-11-08): `physical_modifier()` now — every roll today is physical — and the question returns with the first non-physical roll, beside Light LP10's `light_modifier()`.*
- **NQ5** — Can a statue be robbed, or a sleeper? *Leaning (chat, 2026-11-08): not this design's — *lodging & safe logout*, *stealth, locks & theft* and *law/crime/bounties* own it; this design only reads where a statue lies.*
- **NQ6** — Does awake `rest` stop at Winded? *Leaning: yes — Fresh takes sleep; `rest` is the light-activity row (NP6).*
- **NQ7** — The awake clock's calibration: Legend's hourly test after 10+CON hours, or a CON-scaled drain? *Leaning: the hourly test (NP3); the decomposition sets whether the tests grow harder with depth beyond Debilitated's Difficult one.*
- **NQ8** — What counts as a night for the clock? *Leaning: eight game hours, two real (NP8); shorter sleeps take their length off.*
- **NQ9** — May a collapsed character eat or drink? *Leaning: no — it is asleep; logging out is the answer (NP14). BACKLOG's entry raised it because the ticker drains hunger and thirst meanwhile; a collapse lasts one level, thirty to sixty real minutes.*
- **NQ10** — The bedroll's rung and the source of its recipe. *Leaning: a low rung, so a newcomer can make one; a scroll in the temple beside the tent's (`world/seed_data.py:250–251`) — every gated recipe needs a source (`tests/test_recipe_sources.py`).*
- **NQ11** — Wear per night, and what counts as a night for wear. *Leaning: two `condition` per sleep of a night or more, nothing for a nap — about fifty nights (NP22).*
- **NQ12** — The temple's pallets: room-wide or one per sleeper? *Leaning: room-wide, no occupancy, no wear (NP12).*
- **NQ13** — How long may a statue hold a bed, and how is one rented? *Leaning: while its player is away; renting with *markets & taverns* and *workshops & shared stations* (NP13).*
- **NQ14** — Respawn at Wearied changes the death message's promise (death-consequence policy (v); `world/death_contract.py:132`). *Leaning: yes, with the line amended; to be ratified at roadmap altitude before slice 1 ships it.*
- **NQ15** — Is `rest` or `sleep` taken only in some rooms — never in water, never while overloaded? *Leaning: anywhere a character can stand; overload does not stop sleep.*
- **NQ16** — Activity-log kinds for a night slept, a collapse and a bedroll worn out: new kinds or fields on existing ones? The family of Forest YQ13, Hunting TQ10, Textiles WQ8, Farming GQ6, Fishing FQ6, Water VQ9, Foraging RQ11 and Light LQ12. *Open.*
- **NQ17** — Is twenty overloaded rooms to a level right? *Open — the weight decomposition's OQ1, at alpha close-out (NP5).*
- **NQ18** — Which design owns lodging — inns, beds for rent, where a statue is safe — this one or *lodging & safe logout*? *Leaning: the body's sleep is this design's; the inn and the statue's safety are *lodging & safe logout*'s, which reads NP13.*

---

## 19. Considered and not proposed

- **Sleep waited through online.** A night is two real hours at today's clock; Achaea's own advanced players are excused from it (§2.2; NG1).
- **A skill whose only reward is a logout.** UO's camping (§2.1; NG2).
- **Furniture counted for a timed buff.** Valheim's comfort (§2.4); a place's quality is its ceiling, not a count.
- **Dying in one's sleep while logged out.** The Long Dark's risk (§2.5); a statue's needs do not run (§12).
- **Legend's unconsciousness lengths and Exhausted's test every minute.** Far too long and too fine-grained for a real-time game (NP-L6).
- **A Survival test for a safe place to sleep.** No Survival skill (NP-L8); the ceiling stands in for it.
- **Skipping the night when everyone sleeps.** One shared clock cannot be skipped for some.
- **A rest that refuses the tired.** Being too tired to sleep is a fiction; being too *rested* is the only refusal (NP7).
- **Lodging bought from an NPC innkeeper.** Pillar 1.
- **The tree net and insect netting** (AoL `:498`, `:314`). With terrain that has predators and swamps — Stage 5 and Stage 6.
