# PolishedWorld — Combat Design (Stage 5: the source verification, the first reading, and the decisions the decomposition is built on)

> **Rev 5 · 2026-11-22** — notes and two rows, docs only, in the commit that closes slice BD (`docs/PolishedWorld_Body_Decomposition.md` Rev 2; merged as `22fb018`, PR #33, tagged `alpha-20261122`): §3.1 gains fatigue's Strike Rank penalty (p. 90), which the table had only half of; §3.6 says what the weapon tables' categories turned out to be; §4.10 says where CS1, CS2 and CS4 landed; §5 gains BD4's departure (players do not invent styles); §6's seam lines are dated with where they stand after BD; §7 loses the styles' starting list. No decision changes.
> **Rev 4 · 2026-11-16** — two notes, docs only, in the commit that closes slice SC (`docs/PolishedWorld_Skill_Check_Forms_Decomposition.md` Rev 2; merged as `d3d7ae1`, PR #32): §4.14 says OC1–OC3 are built and where they stand in `world/skillcheck.py`; §6's seam line for that module says it was read before SC. No decision changes.
> **Rev 3 · 2026-11-16** — three notes and one row, docs only, with `docs/PolishedWorld_Skill_Check_Forms_Decomposition.md` Rev 1 (slice SC decomposed, locks SC1–SC6): HQ2 says what SC does to the hunt's outcome; §4.14 points to the decomposition and to what its reading found; §5 gains the one place where SC rules beyond the book (SC3). No decision changes.
> **Rev 2 · 2026-11-16** — two notes in §6, docs only, with `docs/PolishedWorld_Combat_Decomposition.md` Rev 12 (Names DONE; merged as `c4ac47a`, PR #31, tagged `alpha-20261116`): the Names note is annotated (Rev 2), so the list of notes not annotated loses it; and the short description's state slot, which Names left for the wound slice (WO2), with `health` given no word. No decision changes.
> **Rev 1 · 2026-11-14** — first version, docs only, with roadmap Rev 80, BACKLOG Rev 112, README Rev 60 and the series handoff `docs/system_designs/HANDOFF.md` Rev 18. Written from Stage 5's design and source-verification session (roadmap decision log, *Order after the webclient*, step (4)): EvAdventure's combat read at the pinned `v6.1.0`, *Legend*'s combat chapter and *Arms of Legend* read in source, and the open questions put to Adam one group at a time. **Unlike the one-system series' notes, the numbered items here are decisions**: Adam took each group on 2026-11-14, with one change of his own (AR1: Armour Points add up across layers) and one rider (AR3: three layers now, open to change). Where an item is a calibration value and not a lock, it says so. No code is written and none is changed by this document.
> **Canonical:** `docs/PolishedWorld_Combat_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Altitude:** design (one stage, before its decomposition).
**Home:** `docs/roadmap.md`, *Stage 5 — Combat* and the decision log's three combat entries, resolved by this document (Rev 80).
**When to read:** when Stage 5 is decomposed — every section; when `rpg/rpsystem` is decomposed as Stage 5's first slice (§4.3); when a weapon or armour recipe is written (§4.5, §4.9); when the series note *lodging & safe logout* is written (§4.2, the statue); when hunting's shot or its wounded quarry is decomposed (§4.7, §4.10); when Rest slice 2 is decomposed (§4.8).
**Labels:** two letters and a number, one pair per question group. The session's chat called the targeting items TG and the wound items WD; `TG1`–`TG5` and `WD1`–`WD5` were already taken in `docs/` (the Hunting design note and the Weight decomposition), so they are **TR** and **WO** here. The other pairs were free across `docs/`, `world/`, `commands/`, `typeclasses/`, `server/` and `tests/` when checked.
**Page references:** *Legend* core is cited by page (p.), *Arms of Legend* by line in `docs/reference/arms_of_legend.md` (AoL l.). The core text used for reading has no page marker for pp. 77, 97 and 142, so a reference beside one of those may sit a page off; the drowning rule starts on p. 76 and continues under the marker for p. 78.

---

## 1. What the session found, in short

1. **EvAdventure's twitch combat is worth reading for its shape and not for its code.** It makes the opposite choice to `world/timed_actions.py` on almost every point — persistent state, a pooled persistent ticker, no identity, no reaction to movement or logout — and its cleanup has holes that the statue logout would make serious (§2).
2. **Three things the session's brief assumed are not in the source:**
   - *Legend* does not add Armour Points across layers: with several pieces on one location only the highest counts (core p. 95). *Arms of Legend* has no layering rule of its own. Adam decided to add them up anyway (AR1), so this is a recorded departure.
   - *Legend* has no wear per hit. A weapon loses Hit Points only through named events, and armour wears by the week (AoL l. 1450–1481). Wear per use on weapons is a project rule (IS5).
   - *Legend* already has two patterns for damage outside combat — named locations and every location — and a third for falls (§3.3).
3. **Attack against parry is not an opposed test** in the book's sense, and a wound's Resilience test is rolled against an attack roll that already exists. `world/skillcheck.py::opposed_check` does neither today (OC3).

---

## 2. The first reading: EvAdventure's combat at `v6.1.0`

BACKLOG *Read EvAdventure's twitch combat before Stage 5's design*. Read from the wheel `evennia-6.1.0` (`VERSION.txt` 6.1.0): `combat_twitch.py` and `combat_base.py` in full, `combat_turnbased.py` in its handler (lines 1–398) with the EvMenu nodes (399–848) in outline. Paths are under `evennia/contrib/tutorials/evadventure/`. Nothing was run.

### 2.1 How actions are queued and repeated

- Twitch has no queue. One handler Script per combatant (`combat_twitch.py:33–36`) holds a single `action_dict`, and a new action overwrites it (`:187`).
- `queue_action` stops the old ticker and starts a new one at the action's `dt` (`:190–199`). `attack` is `dt: 3, repeat: True` (`:338`).
- Every tick builds the action again and runs `can_use()`, `execute()`, `post_execute()` (`:201–212`). A non-repeating action falls back to `hold` with `dt: 0` (`:56`, `:214–217`).
- `stunt`, `use` and `wield` carry no `repeat` key, and twitch reads it with a default of `True` (`:214`), so they repeat as well. The turn-based handler reads the same key with a default of `False` (`combat_turnbased.py:311`).
- Turn-based: one Script on the room, `combatants: {combatant: action_dict}` (`:101`, `:269`), and `at_repeat` runs everyone's action in shuffled order every 30 seconds (`:374–381`).

### 2.2 How cooldowns are held

- There is no cooldown and no `CooldownHandler` in the parts read. The pace is the ticker's interval.
- `repeat()` goes to the TickerHandler, which pools by interval (`evennia/scripts/tickerhandler.py:266–268`) and starts the loop only when it is not running (`:182–186`). Everyone with `dt=3` therefore strikes on one global pulse, in subscription order (`:123`).
- So the first blow lands 0–3 seconds after the command, depending on where the pulse stands, and typing `attack` again moves the attacker to the end of the order without changing the wait.

### 2.3 Where combat state lives

- In `db`. The handler is created `persistent=True` (`combat_base.py:288–295`); `action_dict`, advantages and the ticker reference are `AttributeProperty` (`combat_twitch.py:52–59`). `ndb.combathandler` is only a cache (`combat_base.py:283–297`).
- The ticker is persistent too (`evennia/utils/utils.py:1187`), so a fight survives `@reload`. The call passes `id_string="combat"` (`combat_twitch.py:199`), but the parameter is `idstring` and `**kwargs` is not forwarded (`utils.py:1232–1234`), so the id string stays empty.

### 2.4 How it is cleaned up

- `stop_combat` stops the ticker, removes the cache and the cmdset and deletes the script (`combat_twitch.py:250–257`). It is called only from `check_stop_combat`, which runs only at the end of the combatant's own tick (`:219`).
- The target's handler is created at the attack (`:310–312`) and gets no ticker, so a passive target keeps the script and `TwitchLookCmdSet` until it acts.
- `hold` sets `dt: 0`, which stops the combatant's own ticker and with it the only check that could clean up.
- `at_defeat()` is never called on the twitch path, only in turn-based (`combat_turnbased.py:328`); twitch filters out `hp <= 0` (`combat_twitch.py:231–232`).
- Movement is free: there is no `at_pre_move`, and the weapon refuses only when the target has left the room (`objects.py:211–214`). Logout is not handled.
- The mob side does not work as written: `self.nbd.combathandler` (`npcs.py:283`), `case "combat"` against the probability key `"attack"` (`:261`, `:291`), and `"item"` is not in `action_classes`.

Sides and PvP are room flags: `allow_combat` in `at_pre_command` (`combat_twitch.py:271`) and `allow_pvp` in `get_sides` (`:107`) — the haven's shape with the default turned round.

### 2.5 Against `ndb.timed_action`

| | EvAdventure twitch | `world/timed_actions.py` |
|---|---|---|
| Storage | `db`, a persistent Script | `ndb`, one `_Record` (`:157`) |
| Timer | pooled, persistent ticker | `delay`, non-persistent, its own phase (`:164`) |
| Reload | the fight goes on | the action dies, on purpose (D7) |
| Identity | none; the script's existence | `marker`, compared with `is` (`:190`, `:219`) |
| Movement | changes nothing | `at_pre_move` interrupts (`typeclasses/characters.py:1678`) |
| Unpuppeted body | not handled | the slot is emptied (`:192–194`, `:224`) |

**What fits.** A blow as a timed action gets three things for nothing: combat excludes `rest`, `work` and `craft`; walking interrupts the attack; a statue logout empties the slot. `rest` already shows the pattern for a repeating action with `is_current()`.

**What does not fit, and the decomposition must answer:**

1. **A creature cannot use the slot.** `is_current()` and `claim()` refuse every body without `has_account`, so an NPC or an animal needs another route or a changed rule.
2. **Defence must not need the slot.** `start()` refuses with *You are already resting.* when the slot is taken; someone attacked during a chore must be able to defend without starting anything (CT6).
3. **The attacked side's state lives nowhere.** The slot knows what a character does, not who is fighting it. EvAdventure answers with a handler on the target, which is where its cleanup fails.
4. **Changing target resets the wait** if it is done as `interrupt()` and `start()`.
5. **A persistent ticker is already a known risk here** (BACKLOG *⚠️ `at_server_start` ticker re-adds wipe every other persistent ticker*, as the session's handoff names it; not read live in the session).

---

## 3. Source verification

### 3.1 Time and actions

| Rule | Source |
|---|---|
| A round is 5 seconds; everyone spends Combat Actions in Strike Rank order, cycle after cycle | p. 125 |
| Combat Actions from the average of DEX and INT: 6 or less → 1, 7–12 → 2, 13–18 → 3, +1 per 6 | p. 10 |
| A shield or two weapons give +1 CA | p. 124 |
| Strike Rank is the average of INT and DEX less the armour penalty; initiative is 1D10 + SR | pp. 13, 125 |
| The armour penalty is the total Armour Points worn, divided by five, rounded up | pp. 13, 95, 125 |
| Parry, Evade and Cast Spell are reactions; each costs a CA | p. 127 |
| A parry is declared before the attack roll; if the attack misses the CA may be kept | p. 129 |
| An Evade costs the next attack | pp. 127, 136 |
| With no CA left, or no parry, the defender counts as having failed | p. 131 |
| Combat is Heavy Activity: an Athletics test after CON Combat Actions, then every CON again | p. 89 |
| Exhausted and Debilitated lower DEX by 5 and 10 for Combat Actions | p. 90 |
| Wearied, Exhausted and Debilitated lower Strike Rank by 2, 4 and 6 *(Rev 5: the same row of the book, missing here until BD read it whole; built in `world/body.py`, `STRIKE_RANK_PENALTY`)* | p. 90 |

### 3.2 Attack, defence and damage

| Rule | Source |
|---|---|
| Both roll their Combat Style; a difference in level of success gives 1–3 Combat Manoeuvres | pp. 129, 131 |
| A manoeuvre is chosen before damage and location are rolled | p. 132 |
| Parry by weapon size: equal or larger stops all, one size smaller half, two smaller none | p. 129 |
| Damage is weapon dice plus Damage Modifier, less the parry, less the location's Armour Points | p. 144 |
| Damage Modifier from STR + SIZ; it may be negative | pp. 10–11 |
| Hit location on 1D20: legs 1–6, abdomen 7–9, chest 10–12, arms 13–18, head 19–20 | p. 145 |
| Hit Points per location from CON + SIZ | p. 11 |
| Serious Wound at 0 or below: no attack for 1D3 CA, and Resilience opposed against the attack roll; a failure makes a limb useless, or knocks out for head, chest or abdomen | p. 145 |
| Major Wound at minus the starting Hit Points: a limb severed or shattered, death by blood loss within CON + POW minutes; head, chest or abdomen may kill at once, and otherwise within half CON + POW rounds | p. 146 |
| A helpless target: an automatic critical in close combat, +10 % at range, and no Evade | pp. 135, 136, 141 |
| Surprised — asleep or absorbed in another activity: −10 initiative and defence only for the round | p. 138 |
| A Pulled Blow halves the damage if declared before the attack | p. 138 |
| Reach, Closing and Disengaging are optional rules; leaving gives the opponent a free attack or an Evade contest | pp. 139–140 |
| At range: full skill within Range, halved to double Range, impossible beyond; only shields parry | pp. 140, 143 |
| Unarmed attacks do 1D3 | p. 138 |
| Opposed tests: the higher level of success wins; at the same level the higher roll *within his skill range*; over 100 % the highest skill's excess is taken off everyone | p. 45 |
| Skill bases: close combat styles STR + DEX, ranged styles DEX × 2, Unarmed STR + DEX, Evade DEX × 2, Brawn STR + SIZ, Resilience CON × 2, Persistence POW × 2 | p. 14 |

**Creatures and NPCs** (*Optional Combat Rules For Non-Player Characters*, pp. 146–147): General Hit Points are the average of CON and SIZ, the Critical Wound rating half of that rounded up. At 0 Hit Points a Resilience test every round, death at minus the Critical Wound rating, and a single blow above the rating rolls 1D20 less armour on the Critical Wound table.

### 3.3 Damage outside combat

| Source of damage | Where it lands | Source |
|---|---|---|
| Suffocation and drowning | Chest on a success, Chest and Head on a failure (1D3) or a fumble (1D6) | pp. 76/78 |
| Exposure, starvation and thirst | one point to every location, per day and per condition; it does not heal until the cause is remedied | p. 90 |
| A fall | 1D6 to a random location per band of height, up to four locations; Armour Points do not reduce it | p. 82 |
| Fire and heat | a specific location, or every location when immersed | p. 83 |
| Acid | through the location's Armour Points first | p. 76 |

### 3.4 Armour and weapons

- **Layers:** with several pieces on a location only the highest Armour Point score is used (core p. 95). *Arms of Legend* was searched whole and has no general layering rule. Two pieces add in their own text: the duellist's half-cape adds its Armour Points to the covered arm (AoL l. 1290), and *Reinforced* adds one Armour Point for half again the ENC (AoL l. 1339).
- **All armour is considered lined or padded** (core p. 94).
- **Coverage** is by piece, in the Armour Pieces table (core p. 96; AoL l. 1237–1256) and the specialised armour table (AoL l. 1271–1285): a hauberk covers chest and abdomen, a coat chest, arms and abdomen, pants abdomen and legs.
- **Weapon characteristics:** Category, Damage Dice, STR/DEX minimum (−5 % per point below), Size, Reach, Combat Manoeuvres, ENC, AP/HP, Cost (AoL l. 1499–1517). Ranged weapons add Range and Load, and their Size is the force of the ammunition against a shield (AoL l. 1861–1875).
- **What wears:** a weapon's Hit Points fall through *Damage Weapon* (p. 133), a fumble (pp. 130–131) and striking an object with at least its Armour Points (p. 92). Armour falls through *Sunder* (p. 134) and by the week, by level of wear (AoL l. 1450–1481). A product below a quality score of 100 wears out 25–75 % faster or has fewer Hit Points (AoL l. 1016–1024).

### 3.5 Hero Points

Two at creation; two at the close of a story (zero to four), and at most one more per story (p. 87). Each is spent once: a Combat Action when all are used, a re-roll, a Major Wound downgraded to Serious, a hint, a Heroic Ability (p. 88); and a heroic last action (p. 146). No cap is stated.

### 3.6 Not read

- The weapon tables row by row (core pp. 101–109, and *Arms of Legend*'s). *(Rev 5: BD read them for their categories and found none to use. Core defines a weapon's category (pp. 101, 105) but its tables print no such column (pp. 106–107, 109), and *Arms of Legend*'s column of that name is the hand, 1H or 2H (l. 1499, 1736–1768). So the twelve weapon types are the project's own list (Body Decomposition BD1–BD2, `world/combat_styles.py::WEAPON_TYPES`). The rows themselves — damage, AP/HP, reach per weapon — are still unread, and GR's.)*
- *Monsters of Legend*, for creatures' own hit-location tables and statistics.
- Evennia's single-threaded execution of commands and delayed calls, which the claim *every exchange resolves in one call* rests on; `typeclasses/durable.py:49` states the same property for wear.

---

## 4. Decisions

### 4.1 The timing model (CT)

*Resolves **[OPEN] Combat timing model**.* Legend's round becomes **a beat of one's own per character and one Combat Action pool for attack and defence**, with no global ticker and no command per blow.

- **CT1 — One command starts, the beat repeats.** `attack <target>` sets the intent; the blows go on until the target is gone, the attacker walks or stops. Commands change intent, never single blows.
- **CT2 — The beat is the round divided by Combat Actions.** One blow per `ROUND_SECONDS / CA`: 2.5, 1.67 and 1.25 seconds at 2, 3 and 4 CA with the book's round. **`ROUND_SECONDS` is a calibration constant that starts at 5** (p. 125) and is set by playtest; the shape is the lock.
- **CT3 — Wait first, then strike.** The first blow falls one beat after the command, as `timed_actions.start()` already works. The target learns of the attack when it begins, not when it lands. **Strike Rank sets the length of that opening beat**, so the armour penalty still costs something.
- **CT4 — Combat Actions are a pool refilled in real time.** It holds the character's CA and refills one per beat. An attack and a parry both draw on it; an empty pool is an undefended target, an automatic failure (p. 131). That is the book's rule for several opponents (p. 137) without a round boundary.
- **CT5 — Defence is automatic.** Whoever has a Combat Action parries, or Evades when no weapon will serve (p. 136), with no command. A setting says whether the pool goes to defence or attack first; the book leaves that choice to the player (p. 127).
- **CT6 — The attack lives in the slot, the defence does not.** The attack loop takes `ndb.timed_action`, so it excludes `rest`, `work` and `craft` and `at_pre_move` interrupts it. Defence only reads the pool. A hit interrupts whatever the slot holds (Projectile RWP18 already assumes it).
- **CT7 — Everything in `ndb`, no persistent ticker.** A `@reload` ends every fight at once, in line with Timed Actions D7.

**Fairness with ten or more players:**

| Risk | What the model does |
|---|---|
| A fast typist, a trigger or a low ping wins | At most one beat's head start (CT3); the number of actions comes from CA, not from input (CT1, CT4) |
| Command spam | The pool is the ceiling: at most CA in a burst and CA per round over time |
| Many against one | The book's own mechanic: the defender's pool runs out and the rest land undefended (p. 137) |
| Simultaneous events | Every exchange resolves in one call, in the order the calls arrive (§3.6) |
| Server load | One pending `delay` per combatant |

**Not solved by the model: the amount of text.** Ten combatants at 3 CA in one room are about six exchanges a second. `ROUND_SECONDS` is the first dial.

**Rejected.** *A global round tick in Strike Rank order* — closest to the book and blind to input, but it needs a shared or persistent ticker and combat state outside the character, which is EvAdventure's shape and where its cleanup fails. *Act at once, then wait* — what `hunt` does today (`commands/hunting_commands.py:54–107`): whoever types first hits first, with no warning, and defence has no natural place.

**What it costs.** Combat Manoeuvres cannot be chosen in the moment (§4.11). Creatures cannot use the slot as it stands (§2.5). `hunt` has to be reconciled with the model later (§4.7).

### 4.2 PvE first, the haven, and theft from a person (PV)

*Resolves **[OPEN] Combat: PvE-only first vs PvP**; decides Comfort EP9–EP13 and X1.* Today nothing attacks a character: `Creature` is *stationary and non-aggressive* (`typeclasses/creatures.py:38`) and the only caller of `apply_health_damage` outside the tests is the survival ticker (`world/survival_ticker.py:177`). Stage 5 adds the first thing that can kill a player on someone else's initiative.

- **PV1 — PvE first, with PvP built and switched off.** A player character cannot attack another player character anywhere. The guard is one check where an attack takes its target, behind a setting — the pattern the *severed* tier was given: gate, do not defer, so no migration is owed.
- **PV2 — The exchange is symmetric in code.** Attack, defence and the pool do not tell a player from a creature. The asymmetry is in who receives the damage (locational Hit Points against General Hit Points), which is already locked.
- **PV3 — The haven flag is built in Stage 5.** `is_haven` has two readers from the start: no attack can begin in a haven, by anyone and against anyone, and a player corpse there stays its owner's until it crumbles (Comfort X1, EQ7). Under PvE that means creatures do not attack in the Old Temple.
- **PV4 — Theft from a person does not come in Stage 5.** It stays impossible everywhere — awake, asleep or a statue — and is taken up with the series note *law/crime/bounties*. Goods set down stay as open as today (Comfort EP10).
- **PV5 — The two standing protections are untouched:** *severed* is PvE-only (hit-location entry, (d)) and the corpse's owner-first grace stands (death policy, (iii)).
- **PV6 — Opening PvP is a decision of its own, later.** It needs the haven in service, *law/crime/bounties* written, and the statue question below answered.
- **The statue.** A creature does not attack a statue in Stage 5's first slice; whether a logged-out body in the wild can be attacked is decided in the series note *lodging & safe logout*. A sleeping or collapsed body, whose player is logged in, can be attacked (§4.8).

**Why PvE first:** a statue outside a haven would be free prey with full looting (the statue logout and death policy (ii); a helpless target is an automatic critical, p. 135); a dead crafter is one supplier fewer in a market with no NPC vendor (death policy (i)); a small cohort does not survive one griefer; there is no law, bounty or reputation to answer with; and Stage 5 is already large. **Against it:** a player-driven economy gets its sharpest stake from other players, and loss is harder to add than to start with — which is why PV1 gates and does not omit.

### 4.3 Targeting (TR)

*Decides the Names note's UP16–UP18 for combat.* Checked in the wheel: the contrib's search lets only a Builder fall back to the key (`evennia/contrib/rpg/rpsystem/rpsystem.py:1339`); `ContribRPCharacter` inherits `DefaultCharacter` before `ContribRPObject` (`:1500`); the README gives the `N-name` settings (`README.md:80–81`); and `$You(key)` looks the object up in `mapping` and calls `get_display_name(looker=receiver)` for every receiver (`evennia/utils/funcparser.py:1243–1261`, `evennia/objects/objects.py:1163`).

- **TR1 — Combat takes UP16–UP18 as written.** Only `Character` takes the contrib. Creatures and items keep key and aliases: `attack wolf`, and `attack 2-wolf` for the second (Names K6).
- **TR2 — The target is kept as an object.** It is searched once, when the command is given, and never again by string. Every beat re-checks that it is alive and still in the room, as Projectile RWP18 does for a shot.
- **TR3 — Every combat line goes through `$You()` with role keys** — `mapping={"attacker": …, "defender": …}`, Evennia's own example (`objects.py:1127`), not the character's key as the mapping key as EvAdventure does (`combat_base.py:334`). No combat message formats a character's `.key`.
- **TR4 — A census test guards TR3,** as `TestPushCensus` guards the pushes.
- **TR5 — Help aimed at a player uses the same search:** First Aid, `wake` and later rescue find a player by description or recog. An attack on a player is refused by PV1 in a line that names the target as the viewer sees it.
- **TR6 — Tests and `@py` target by dbref,** never by name (UP18).

`rpg/rpsystem` stays Stage 5's first slice of code, before combat code. *Left to the Light note:* whether one can aim at what one cannot see — the book gives −40 % in darkness and −60 % in pitch black (p. 135), but whether the search finds the target at all is that note's.

### 4.4 Wounds, death and damage outside combat (WO)

*Answers the hit-location entry's sub-question (b) and the rule check carried by BACKLOG* Character panel: Legend combat state*.* The three tiers stay as locked on 2026-09-09.

- **WO1 — *Disabled* follows p. 145.** At 0 Hit Points or below a location always costs 1D3 Combat Actions without an attack. A limb is useless only on a lost Resilience test against the attack roll; for head, chest and abdomen the same test is against unconsciousness. The roadmap's *location unusable until back to positive HP* described the lost test, not the wound.
- **WO2 — Level and state are two things.** The wound *level* (Minor, Serious, Major) is derived on read from the location's Hit Points (pp. 145–146), as `health` is. The *state* (disabled, maimed, severed) is stored, and set by a lost test or a Major Wound. While *severed* is switched off, a Major Wound gives *maimed* on any location.
- **WO3 — What kills is the book's, and `health` is a display.** A Major Wound to head, chest or abdomen with a lost Resilience test kills at once; an untreated Major Wound kills when its clock runs out (p. 146). `health` is computed from the locations for the panel and `status` and is never a writer of its own (P-2).
- **WO4 — The clocks run in real time and are calibration values,** starting at the book's: CON + POW minutes for a limb, half CON + POW rounds for head, chest and abdomen. The short one is death without company; the rescue is BACKLOG *Two-stage healing*'s.
- **WO5 — Every source of damage names its location policy, and there is no default.** Three policies, each from the book (§3.3): `all`, `named` and `random`. `apply_health_damage` gains a location argument that must be given.
- **WO6 — Armour is taken off only where the book says so:** not for a fall (p. 82), first for acid (p. 76), always for a blow (p. 144).
- **WO7 — `all` damage sets no wound state on a limb.** For an `all` source a limb stops at 0, and death comes when a vital location reaches a Major Wound. Without this a starving character would be maimed in four places before dying, since arms have the fewest Hit Points (p. 11). *This is the project's construction;* the book says only *one point of damage to all locations* (p. 90).

**For the decomposition:** the time to death by starvation changes — today it is one `health` per 600 seconds out of CON × 2 (`world/survival_ticker.py:32`, `server/conf/at_server_startstop.py:27`), and under WO7 the head's Hit Points govern (BACKLOG *Survival loop tuning*). Healing is already right: `world/healing.py` adds nothing while starving or dehydrated, which is p. 90.

### 4.5 Armour (AR)

*Answers sub-question (c).* In code today: one garment per body region (`CLOTHING_TYPE_LIMIT`, `server/conf/settings.py:210–213`); warmth adds up over every worn layer, covered ones included (`world/thermal.py:104–118`); the contrib limits only the types listed in `CLOTHING_TYPE_LIMIT` (`evennia/contrib/game_systems/clothing/clothing.py:502–504`), so new types can be added.

- **AR1 — Armour Points add up per location across layers. *A departure from the book*** (core p. 95: only the highest counts), decided by Adam: it is fairest to the player that layers count, as they do for warmth, and layered armour is otherwise pointless.
- **AR2 — Coverage is data on the item, not a consequence of its slot.** An armour item carries `ap` and the Hit Locations it covers (§3.4). The mapping *ContribClothing slot ↔ Hit Location* that sub-question (c) asked for therefore falls away: ordinary garments have no Armour Points, and armour states its own coverage.
- **AR3 — Three armour layers per location, one item per layer:** padding (linen, soft leather), flexible (leather, ring, scale, mail) and rigid (plate, lamellar). Armour gets its own clothing types so that mail does not push the wool tunic out of `top` — the book counts all armour as lined (p. 94). **Three is the choice for now and may change** if play shows the need (Adam). The exact type list is the decomposition's.
- **AR4 — The armour penalty counts every Armour Point worn** (*the total amount of Armour Points the Adventurer is carrying*, p. 13), divided by five and rounded up. It goes into the opening beat (CT3).
- **AR5 — Weight is the second brake.** Each layer's ENC counts against the carrying limit of STR + SIZ, and past it `physical_modifier()` takes 20 % (core p. 86; `typeclasses/characters.py:679`). Linen 2, mail 5 and plate 6 are 13 Armour Points on one location; on all seven that is 91, a penalty of 19 and an ENC of 49.
- **AR6 — The two *Arms of Legend* exceptions are item properties:** *Reinforced* changes the item's `ap` (AoL l. 1339); the half-cape (AoL l. 1290) waits until it is built. **A creature's natural armour** comes off every hit and carries no penalty (p. 13); `natural_ap` exists (`typeclasses/creatures.py:49`).

**A known risk, left to playtest:** 13 Armour Points stop nearly every blow of a 1D8 weapon, so such a target falls only to a critical with *Bypass Armour* (p. 133).

### 4.6 A shot's damage, and creatures' Hit Points (PD, CR)

*Decides Projectile RWP24.* A creature holds `siz`, `natural_ap` and `flee_skill` today, and neither CON nor Hit Points (`typeclasses/creatures.py:48–51`).

- **PD1 — A shot goes through the same damage path as a blow:** weapon dice, the Damage Modifier only where the weapon's table row says so (p. 141), a parry only by a shield (p. 140), then Armour Points. Under PvE every target is a creature.
- **CR1 — A creature gains CON, and with it General Hit Points and a Critical Wound rating** (p. 146). Values per species come from *Monsters of Legend* (§3.6).
- **CR2 — The book's rules at 0 Hit Points and its Critical Wound table are taken as written** (pp. 146–147), the table as data.

### 4.7 The wounded quarry (HQ)

*Decides Hunting TQ13.* `hunt` kills on a won opposed test and deals no damage (`commands/hunting_commands.py:99–121`).

- **HQ1 — Stage 5 owns the damage, Hunting owns the trail.** An animal with General Hit Points that survives a hit is the wounded quarry; the bleeding trail and the flight (Hunting TP12) stay the hunt's.
- **HQ2 — `hunt` does not change in Stage 5.** It abstracts stalking and felling passive prey. Reconciling it with combat belongs to a hunting decomposition afterwards. Until then there are two ways to kill a rabbit, `hunt` and `attack`. *(Rev 3: slice SC corrects the opposed test `hunt` calls — OC1 and the over-100 % rule — and `commands/hunting_commands.py` is not edited. HQ2 protects the hunt's model, not a tie-break OC1 decided was wrong: the slice's lock SC4. Measured, the correction moves the hunt's odds by hundredths of a percentage point, and the over-100 % rule by about three points for a hunter above 100 %.)*

### 4.8 The helpless body (HB)

- **HB1 — Helpless means no automatic defence, an automatic critical in close combat and no Evade** (pp. 135, 136): a collapsed body today, an unconscious one from WO1, a sleeping one when Rest slice 2 exists.
- **HB2 — A collapsed body cannot attack or hunt.** `attack` and `hunt` are refused by `refuse_if_collapsed`. This is the first combat consequence of a collapse, the trigger of BACKLOG *A collapsed body's instant commands*; the rest of that entry's list is left to Rest slice 2.
- **HB3 — Whoever is attacked in the middle of a chore is surprised** (p. 138, *absorbed with another activity*): defence only for one round, and the hit interrupts the slot (CT6).

### 4.9 The item schema (IS)

*The schema the roadmap's* Gear *line and* Metallurgy enters through tools *wait for.*

- **IS1 — A weapon's fields are the book's:** damage dice for one and two hands, STR/DEX minimum, Size, Reach, allowed Combat Manoeuvres, ENC, AP/HP; ranged weapons add Range and Load (§3.4). A shield is a weapon with its own damage and Size (p. 148).
- **IS2 — Armour's fields:** `ap`, covered locations, layer, ENC per location, material.
- **IS3 — One wear axis, the one that exists.** Weapons and armour are `DurableObject`s with `condition` 0–100 (`typeclasses/durable.py:31–60`), mended with `repair`. The book's AP/HP says what a damage event costs: damage above a weapon's Armour Points takes `condition` in proportion to its Hit Points.
- **IS4 — Armour wears as garments already do.** `world/garment_wear.py` is built on *Arms of Legend*'s Armour Wear Values. Combat raises the wear level, the book's *Rigorous Wear*, and *Sunder* (p. 134) takes directly.
- **IS5 — A weapon wears per use, as a tool does. *The project's rule, not the book's*,** and what *Metallurgy enters through tools* meant by *wear per hit*: without it a weapon has no sink but a rare fumble (pillar 1).

### 4.10 Skills (CS)

*Decides Projectile RWQ1.* A character has `perception`, `stealth`, `athletics`, `craft` and `hunting` today.

- **CS1 — Stage 5 introduces combat's skills once, at the book's bases** (p. 14, §3.2). Resilience replaces the stand-in `world/healing.py:63`.
- **CS2 — Styles are data that name weapon categories.** The book lets players invent them (p. 124); the starting list is the decomposition's.
- **CS3 — `attack` and `shoot` roll the weapon's style; `hunt` keeps `hunting`** (HQ2).
- **CS4 — Combat skills improve on use,** by joining `improvable_skills` (`typeclasses/characters.py:1007`). The existing 30-second gate per skill keeps a blow a second from being an improvement roll a second.

### 4.11 Combat Manoeuvres (CM)

- **CM1 — The choice is a standing preference.** The player orders one list for attack and one for defence, and the server takes the first that the weapon and the situation allow (CT1's principle). The book wants the choice before the damage roll (p. 132), which real time cannot ask for.
- **CM2 — The first slice ships a short list; the rest come as data.** Which ones is the decomposition's. *Bash* and *Change Range* wait, since they count metres; *Change Range* belongs with the Projectile note's distance per encounter (RWP7).

### 4.12 Shots between rooms, distance and flight (SR)

*Decides Projectile RWP10 and RWQ13.*

- **SR1 — No shots between rooms in Stage 5.** Under PvE it is creatures that would be kited, and today they cannot follow anyone. The question returns with Stage 6, when the wilderness has sightlines and creatures that come after.
- **SR2 — Distance inside the room comes with the projectile slice,** not with the first close combat. Moving it costs a Combat Action, as the book's *Change Distance* does (p. 127).
- **SR3 — Leaving the room while under attack costs one free attack** from every attacker with a Combat Action left: the book's *Disengaging* (p. 140), simplified. Without it flight is free, as in EvAdventure, and hit-and-run is the best tactic.

### 4.13 Hero Points (HP)

*Decides BACKLOG* Hero Points in a persistent world*.* A persistent world has no stories to close and no Games Master, and no one can be asked in the middle of an exchange.

- **HP1 — Two at creation,** as the book.
- **HP2 — One use in Stage 5: *Glancing Blow*.** A Major Wound is downgraded to Serious (p. 88) automatically when the character has a point and has not switched it off.
- **HP3 — The other uses wait.** A re-roll and an extra Combat Action need a way to choose beforehand; *Heroic Insight* needs a Games Master and is dropped; Heroic Abilities are a system of their own.
- **HP4 — Points are earned slowly by time played, with a cap of 4,** the most the book awards for one story. The rate is a calibration constant. *The project's construction:* the book has no cap and no earning rule a MUD can cite. Tying points to deeds was the alternative and needs a deeds system that does not exist.

### 4.14 `opposed_check` (OC)

*Decides BACKLOG* `opposed_check` lets an automatic success win on a roll outside the skill range*.*

- **OC1 — An automatic success outside the skill value ranks lowest in the comparison.** It loses to every success within the value; between two such, the higher skill wins, the book's next step (p. 45).
- **OC2 — The over-100 % rule is built with Stage 5** (p. 45). The function's docstring still says skills cap at 100.
- **OC3 — Two new forms are needed:** a comparison of level of success alone, for attack against parry (pp. 129, 131), and an opposed test against a roll already made, for the wound tests (p. 145). `opposed_check` rolls both sides afresh (`world/skillcheck.py:127`).

*(Rev 5: BD, `docs/PolishedWorld_Body_Decomposition.md`, merged as `22fb018`.)*
- *CS1 is built:* Resilience, Evade, Unarmed and Brawn are traits from creation at the book's bases (p. 14), backfilled from each character's own characteristics on an older database (BD5, BD6). Persistence waits for magic. Every reader asks `world/skill_base.py::value_of`, which falls back to the base when a character lacks the trait; natural healing reads Resilience through it (`world/healing.py:80`), so *stand-in* is gone. A character has nine skills.
- *CS2 is built as data:* six styles over twelve weapon types, in `world/combat_styles.py` (BD1–BD4). A style names types, never weapons, and becomes a trait the first time it is used (BD3); keys carry the prefix `style_` (OQ-BD3). The slice that adds the first weapon of a type adds its style. Nothing calls a style until ML.
- *CS4 moved:* to WN for Resilience and to ML for the other three and the styles (BD8). `improvable_skills` is unchanged (`typeclasses/characters.py:1331`); `progress` captions the four *(not yet trainable)*.

*(Rev 3: decomposed as slice SC, `docs/PolishedWorld_Skill_Check_Forms_Decomposition.md`. Its reading found that the second form has more users than the wound tests — Bleed and Disarm oppose the original attack or parry roll (pp. 132–133) — that the levels table gives nobody a level when neither side succeeded (p. 131), and that `skill_check` needs no change for OC2: the rule is a modifier on the targets of an opposed test.)*

*(Rev 4: built and merged as `d3d7ae1`, PR #32. OC1 and OC2 in `opposed_check` (`world/skillcheck.py:193`), OC3 as `opposed_against` (`:246`) and `compare_levels` (`:314`), with one private `_judge` (`:147`) under the two opposed forms; `skill_check` is now at `:60`. The docstring no longer says skills cap at 100, and the result reports `excess`.)*

### 4.15 Stage 5 before Stage 6 (SO)

*Resolves **[OPEN] Stage 5 vs Stage 6 order**.*

- **SO1 — Combat first.** Stage 6 names combat as a dependency, so that the wilderness has stakes.
- **SO2 — Stage 5 needs a small dangerous place:** a few hand-built rooms with creatures that take the initiative, outside the haven. They become Stage 6's first neighbour.

---

## 5. Departures from the book, in one place

| Decision | The book | PolishedWorld |
|---|---|---|
| CT1–CT4 | Five-second rounds in Strike Rank order | A beat per character and a pool refilled in real time; Strike Rank sets the opening beat |
| CT5 | The player declares each parry | Defence is automatic, by a standing choice of priority |
| CM1 | A manoeuvre is chosen at each success | A standing preference |
| AR1 | Only the highest Armour Points on a location count (p. 95) | They add up across three layers |
| IS5 | No wear from use | A weapon wears per use |
| WO7 | One point to all locations (p. 90) | The same, but a limb stops at 0 and sets no wound state |
| SR3 | Disengaging: a free attack or an Evade contest (p. 140) | A free attack from every attacker with a Combat Action |
| HP2–HP4 | Awards per story, several uses, no cap (pp. 87–88) | Earned by time played, cap 4, *Glancing Blow* only at first |
| PV1 | — | Player against player is built and switched off |
| BD4 | Players create their own combinations of weapons as styles (p. 124) | The list is the server's: six to start, and the slice that adds the first weapon of a type adds its style *(Rev 5)* |
| OC3 (SC3) | The over-100 % rule is given for opposed tests (p. 45); nothing on an opposed test against a roll already made (p. 145) | The made roll keeps its level and its roll; whether it lies within the skill is measured against the lowered target, and the resisting side rolls against its own lowered target *(Rev 3)* |

---

## 6. For the decomposition

**Order of slices.** `rpg/rpsystem` first (§4.3). Close combat in the room before the projectile slice (SR2).

**Seams in code** (read at `baed99b`):
- `Character.apply_health_damage(amount, source=None)` (`typeclasses/characters.py:1299`) — the one writer of health; it gains the location argument (WO5).
- `Character.at_character_death(killer=None)` (`:1353`), and its restore block against the wound tiers (BACKLOG *`at_character_death()` restore block vs persistent wound tiers*).
- `Character.physical_modifier()` (`:679`) — overload and the fatigue level, already summed.
- `Character.refuse_if_collapsed()` and `at_pre_move` (`:1644`) — HB2, CT6, SR3.
- `world/skillcheck.py`: `skill_check` (`:58`), `opposed_check` (`:127`) — OC1–OC3. *(Rev 4: read before SC; after it `:60` and `:193`, with `opposed_against` `:246` and `compare_levels` `:314`.)*
- `world/timed_actions.py` — one slot per character; `is_current()` and `claim()` refuse a body without an account (§2.5, point 1).
- *(Rev 5: dated. After BD, at `22fb018`: `improvable_skills` `typeclasses/characters.py:1331` (CS4 above), `physical_modifier()` `:1001`, `apply_health_damage` `:1623`, `at_character_death` `:1677`, `refuse_if_collapsed` `:1956` and `at_pre_move` `:1975`; `world/skillcheck.py` unchanged since Rev 4. The lines above are left as read at `baed99b`.)*
- `tests/test_client_state.py::TestPushCensus` and the other census tests — every new push, every write to `.current` and every `.location =` is a row; TR4 adds one for names.

**Calibration constants named here:** `ROUND_SECONDS` (CT2), the opening beat from Strike Rank (CT3), the bleed-out clocks (WO4), wear per use (IS5), the Hero Point rate (HP4), the time to death by starvation (WO7).

**BACKLOG entries whose trigger is Stage 5's kickoff,** to name in the decomposition: *`CoinPile` vs the corpse's atomic content delete* (decided 2026-10-17; the code waits), *`copper` is both a material and a denomination*, *Runnable seam checker for the System Map*. **Blocked on Stage 5's code:** *`at_character_death()` restore block vs persistent wound tiers*, *Two-stage healing*, *Character panel: Legend combat state*, *Bank / post office*.

**Design notes with lines that name Stage 5** — pointers, not decisions; read each live (lines counted at `baed99b`): Projectile 23, Foraging 10, Comfort 9, Rest 9, Homunculus 8, Housing 8, Names 6, Light 5, Hunting 4, Pottery 4, and one to three each in Cooking, Farming, Rendering, Fishing, Forest, Newcomer, Temperature, Atlas and Storage. `grep -n "Stage 5" docs/system_designs/*_Design.md` gives the list. This document answers Projectile RWP10, RWP24, RWQ1 and RWQ13, Hunting TQ13, Comfort EP9–EP13 with X1 and EQ7, and Names UP16–UP18; the notes themselves are not annotated in this revision. *(Rev 2: Names is — its Rev 2, with the slice's close-out; the others are still not.)*

**The short description's state slot** *(Rev 2, from the Names slice's OQ-NM9 (2))*. Since Names a stranger is read from a composed text with one slot for a visible state, the worst first — wounds, wet, fatigue, load (`world/sdesc.py`, `state_word`). The wound slice fills the first from the wound levels (WO2): a Serious or Major Wound that shows, *limping* for one in a leg. `health` gets no word there: it falls only by starving today, and WO3 makes it a display. The reader `_wounds` returns nothing until then.

---

## 7. Open after this session

- **The statue in the wild** — attacked by creatures or not: the series note *lodging & safe logout* (§4.2).
- **Opening PvP** — its own decision, on PV6's conditions.
- **Aiming at what one cannot see** — the Light note (§4.3).
- **The starting lists:** manoeuvres (CM2), armour clothing types (AR3). *(Rev 5: combat styles (CS2) settled by BD4 — six, and a rule that fills the list.)*
- **How a creature takes its turn** without the slot (§2.5), and how a creature decides to attack and to follow (SO2, SR1).
- **Reconciling `hunt`** with the model (HQ2, CT).
- **The rates:** Hero Points (HP4), wear per use (IS5), the clocks (WO4).
- **The text volume** of a crowded fight (§4.1).
- **A project-knowledge file outside the repo,** `PolishedWorld_Mongoose_Legend.md`, gives the round as 6 seconds against the book's 5 (p. 125) and the turn order as *first-come-first-served with cooldowns*, which CT3–CT4 replace. It is Adam's to correct; it is not in git.
