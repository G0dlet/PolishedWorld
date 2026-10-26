# PolishedWorld — Weight and Encumbrance Decomposition

> **Rev 1 · 2026-10-26** — first version. Decomposes the roadmap's seventh alpha prerequisite, *weight* (alpha entry (E); order fixed by (F): decomposition only, code after character creation), into six components and eleven tasks, against live source read the same day (`main` at `f4f0c32`, tree `153b871`; Evennia 6.1.0 from PyPI; `Legend.pdf` core p.86 and pp.89–90; *Arms of Legend* pp.28–30). Locks **WD1–WD8**: the limit is STR+SIZ as written (WD1); two bands and a ceiling — free to the limit, *Overloaded* to twice it, refused above (WD2); the band's cost is −20 % on physical tests and a fatigue cost per room moved, computed lazily with no buff and no rate multiplier (WD3, **which reverses the direction recorded in BACKLOG Rev 41**); twenty items at `enc` 0 count as 1 ENC wherever they are carried (WD4); containers hold ENC, not items, and never nest (WD5); crafting and foraging honour the ceiling by setting the surplus down (WD6); the wallet weighs nothing and `CoinPile`'s ENC is Stage 5's (WD7); no Source/Sink Ledger row (WD8). **One consequence the BACKLOG entry asked this document to decide:** the ceiling prices distance in trips from the first day, so *Fatigue-exhaustion consequence* is neither inside this feature nor a dependency of it; it stays OPEN and the per-room cost gains teeth when it ships. No code.
> **Canonical:** `docs/PolishedWorld_Weight_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Status:** PLANNED (no code yet). Code waits for character creation (`docs/PolishedWorld_Character_Creation_Decomposition.md`) per alpha decision (F); nothing here depends on it technically, see §13.
**Feature branch:** `feature/weight` (one branch, one merge). Create it with `git switch -c feature/weight --no-track origin/main` (lesson 64).
**Rough scope:** 11 tasks, 2–3 sessions at 5 h/week (W1 0.5–1 · W2 1 · W3 1 · W4 1–1.5 · W5 0.5 · W6 0.5). Small because the data already exists: 47 `enc` fields in `world/prototypes.py` since the alpha content epic (AD8), and `tests/test_material_registry.py` test (g) keeps them complete.
**Philosophy:** skynda långsamt — the mechanic is one lazy reader and three places that consult it; no new state, no ticker, no migration.

---

## 1. Why this feature

Pillar 1 measures emergent prices, and prices need geography: a thing must cost more where it is used than where it is gathered, or carrying is free and no one is paid to carry. Today one character carries any quantity anywhere — `enc` has no reader (grep of `commands/`, `typeclasses/`, `world/`: zero hits outside `world/prototypes.py`). This feature gives `enc` a reader, gives STR and SIZ their first reader in the alpha, and gives the three craftable containers (sack, backpack, saddlebag — AC4.2) a use. It must be on `main` before *Persistent alpha instance* opens: objects spawned there before a reader exists would otherwise be carried without limit until a migration (roadmap (E), BACKLOG *Weight and encumbrance* trigger).

## 2. Decisions locked 2026-10-26 (WD1–WD8)

**WD1 — The limit is STR+SIZ, as written (Legend p.86).** No scaling, no flat cap. With Points Build (CC1) the limit spans 12–36; until character creation ships every character has STR 10, SIZ 10 (`static`, `typeclasses/characters.py:196, 217`) and a limit of 20. The limit reads the stats live, so chargen changes it without a migration. Measured against the catalogue: the heaviest item weighs 2 (`saddlebag`, `bone_armour`, `quarterstaff`, `spear`, `milling_stones`, `tent`), eleven weigh 1, thirty weigh 0 (`world/prototypes.py`, 47 fields), and `wood` and `stone` are one object per unit at `enc` 1 — so the limit bites on bulk, which is exactly pillar 1's case: a weak character is overloaded by the thirteenth log, a strong one carries 36. *Rejected:* **A**, a scaled limit (a second knob, and it makes the Legend and *Arms of Legend* ENC columns wrong in both directions); **B**, a flat limit (removes STR and SIZ's only reader in the alpha).

**WD2 — Two bands and a ceiling: free to the limit, *Overloaded* to twice it, refused above (an adaptation, not RAW).** Legend's rule is a soft limit: *Overloaded* is a penalty, never a refusal. The project adds a ceiling at **2 × (STR+SIZ)**, Legend's own figure for beasts of burden (p.86: *never more than double*; core text line ~6292) borrowed for people. *Why the ceiling:* the band's costs are a skill penalty and a fatigue cost (WD3), and fatigue at zero has no consequence today (*Fatigue-exhaustion consequence* is OPEN), so without a ceiling the alpha's hauler pays nothing until that entry ships. The ceiling prices distance **in trips** from the first day — the OSRS and Tibia model the chargen decomposition already adopts (CC1's framing) — while the band stays Legend-faithful and gains teeth later. The refusal is on *receiving* only: `Character.at_pre_object_receive` returns False above the ceiling, for `get`, `give`, `get … from` and `put`; `drop` and movement are never refused (Epic A D1: a move is always allowed). That is the criterion the BACKLOG entry set — the cost makes haulage a service, it never locks the player. *Rejected:* **A**, Legend's soft limit alone (prices nothing before *Fatigue-exhaustion consequence*, which would make that entry an eighth prerequisite in practice); **B**, a hard limit at STR+SIZ (deletes the *Overloaded* state, and with it Stage 5's −20 % on weapon tests). **Consequence:** *Fatigue-exhaustion consequence* is neither inside this feature nor a dependency of it (the question its BACKLOG entry and this one asked). It stays OPEN; W3.2's per-room cost is wired now and becomes a reason to rest when that entry ships.

**WD3 — The band's cost: −20 % on physical tests, and a fatigue cost per room moved. No buff, no rate multiplier.** *This reverses the direction recorded 2026-10-18 (BACKLOG Rev 41: an `Overloaded` buff with a `fatigue_rate` mult, recomputed each tick).* Two reasons. **(a)** A rate multiplier prices *time*; a cost per room prices *distance*, and distance is pillar 1's quantity — a loaded character standing in a workshop is not working harder than an unloaded one, and Legend's *Movement halved* translates to a room-based world as *every room costs*. The −20 % on Fatigue tests has nothing to attach to: the project has no activity tests (Legend p.89), only a gauge. **(b)** A buff is a cache: dropping an item leaves it stale until the next tick, and a 30-minute tick (`settings.py:91`) is a long time to be wrongly overloaded. Summing `contents` on demand is the lazy, single-writer pattern (P-2): Evennia keeps `contents` in memory (the contents cache), the sum is O(n) over tens of objects, and nothing is stored. The −20 % is Legend's own (p.86, *all tests that require physical actions … most tests that have DEX or STR as a Characteristic*). It needs a seam that does not exist: every caller passes its own `modifier` to `skill_check()` (`world/skillcheck.py:46`; six call sites, no character-level modifier). W3.1 adds `Character.physical_modifier()` → −20 or 0, and the physical callers add it: every Craft test (DEX+INT — `characters.py:387`: craft, disassemble, repair, harvest) and hunting's opposed check. Forage and scribing are excluded: forage is Survival, CON+POW in Legend, scribing is Lore, INT × 2 — the *exceptions* the rule allows. The same seam carries the Fatigue-level penalties when that entry ships. *Rejected:* **A**, the rate-multiplier buff (reasons above); **B**, a movement delay (a timed move is a new mechanism, and Epic A's slot interrupts on move — a delayed move would have to refuse, which D1 forbids); **C**, a forbidding band (locks the player — the criterion).

**WD4 — Twenty items at `enc` 0 count as 1 ENC, wherever they are carried.** `enc` 0 means *too light to score*, never weightless (BACKLOG annotation 2026-10-26): `zero_enc_count // 20` is added to the sum, counted over the whole carried tree, with or without a container. Legend's *so long as the Adventurer has a suitable means of carrying them* is plausibility, not a mechanic; making it one is a second knob and a special case for the character holding nineteen stones in two hands. The test the BACKLOG entry demands — twenty items at `enc` 0 count as 1 ENC — is W1.1's, with nineteen counting as 0.

**WD5 — Containers hold ENC, not items; contents count fully for the carrier; no nesting.** `typeclasses/containers.py::Container(ContribContainer)` overrides `at_pre_put_in` (the documented point, Evennia `contrib/game_systems/containers/containers.py:83`; the shipped check is `len(self.contents) >= self.capacity`, line 99) to compare the container's carried ENC plus the item's against `capacity` in ENC. Capacities from *Arms of Legend*: backpack 20 (p.28), sack 10 (p.29, *Sack, Large*), saddlebag 15 (p.30, *each saddlebag*). A container does not lighten its contents (Legend lists the container's own ENC; nothing says the contents weigh less), so the carrier's sum is recursive. A container refuses another container (one check in `at_pre_put_in`), so the recursion is one level deep in practice — the reader is still written recursively, because a corpse is a container-shaped object and a future one might nest. `CmdPut` (`containers.py:227`) is added alone to the character cmdset, as `CmdContainerGet` already is (`commands/default_cmdsets.py:181`); `ContainerCmdSet` as a whole stays out because `CmdContainerLook` collides with the seasonal `look` (BACKLOG *Full container support*, folded into this feature). *What a container is for, with WD4 counting without one:* it is the haulage unit — `give sack to <hauler>` moves ten ENC in one command and one hook, and a dropped sack is one object on the floor, not twenty. *Rejected:* nesting (recursive capacity checks for no alpha use); `capacity` as items (the contrib's default — a sack of twenty logs would weigh the same as a sack of twenty bullets).

**WD6 — Crafting and foraging honour the ceiling by setting the surplus down.** Forage already moves its yield with `item.move_to(caller, quiet=True)` (`commands/foraging_commands.py:138`), so the W2.1 hook applies; when it refuses, the item is moved to the room with *"… is too much to carry; you set it down."* — no refund, because the node is already taken (lesson 93). Crafting assigns `obj.location = self.crafter` directly (`world/crafting_base.py:324`), **bypassing every hook**, and is changed to the same `move_to` with the same fallback. The corpse case needs no decision: `Corpse` carries `get:false()` (`typeclasses/corpse.py:80`), so a body is never carried — death is a retrieval run, as the death-consequence policy (ii) intends, and looting it item by item goes through the same receive hook.

**WD7 — The wallet weighs nothing; `CoinPile`'s ENC is Stage 5's.** Coin is an integer in copper on the character (S4-2, `world/currency.py`), not objects, and this feature does not change that (no-backfill, Economic Philosophy §4). `CoinPile` does not exist in the code today (grep: no class); when Stage 5 materialises it, it is an item prototype and AD8's rule gives it an `enc` like any other — recorded as an annotation on BACKLOG *`CoinPile` vs the corpse's atomic content delete*.

**WD8 — No Source/Sink Ledger row.** Weight creates nothing and destroys nothing; it is a price on distance. The ledger renders sources and sinks (lesson 103: a rendered field is a claim), and a row for a mechanic that is neither would be a false one. The economic claim lives in this document's §1 and the roadmap's (E).

## 3. Verified source anchors (read 2026-10-26)

Legend core page numbers refer to `Legend.pdf` (UTF-8 text) read through `iconv -f utf-8 -t ascii//TRANSLIT`; the page number sits two lines below each `Order #…` footer. Project lines are `main` at `f4f0c32`; Evennia lines are 6.1.0 from PyPI.

| Anchor | Where | What it says |
|---|---|---|
| Encumbrance | Legend p.86 (text lines 4203–4221) | ENC per item; ~20 items too light to score = 1 ENC with a sack or backpack; carry ≤ STR+SIZ without penalty; *Overloaded* above: −20 % to physical tests (weapon tests, most DEX/STR tests; Sleight and Mechanisms excepted), Movement halved, −20 % to Fatigue tests |
| Beasts of burden | Legend p.86 (line ~6292, *ENC Carried*) | a mount carries its own ENC, never more than double it — the ceiling's source |
| Fatigue | Legend pp.89–90 (lines 4309–4380) | activity tests (light/medium/heavy), Persistence after 10+CON hours awake; levels Winded…Debilitated at −10…−50 %; recovery one level per two hours of rest |
| Container capacities | *Arms of Legend* p.28 Backpack (text 180–183), p.29 Sack, Large (838–840), p.30 Saddlebag (1363–1366) | 20 ENC · 10 ENC · 15 ENC each; the containers' own ENC 1 · 1 · 2 (table rows 87, 100, 1245) |
| `enc` data | `world/prototypes.py` | 47 fields: 30 × 0, 11 × 1, 6 × 2; `sack` :700, `backpack` :715, `saddlebag` :741, `wood` :393, `stone` :189 |
| `enc` readers | `commands/`, `typeclasses/`, `world/` | **none** outside `world/prototypes.py` |
| `enc` completeness | `tests/test_material_registry.py:160` `_enc_problem` | test (g): every item prototype has a non-negative `int` `enc`; non-pickable typeclasses exempt (line 117) |
| Objects without `enc` in tests | `tests/` | 20 `create_object(` calls in 8 files (`test_death_contract` 4); 17 `spawn(` calls through prototypes — the reader must read a missing `enc` as 0 |
| Characteristics | `typeclasses/characters.py:196, 217` | `str`, `siz` static traits, base 10 |
| Fatigue gauge | `characters.py:286–288`; `world/survival_ticker.py:21, 56–65` | base 100, min 0; `BASE_RATES["fatigue"] = 1` per tick, `trait.current -= rate` in `_deplete_character`; tick 1800 s (`settings.py:91`) |
| Rest | `characters.py:1018–1019` | `rest_interval = 10`, `rest_recovery = 5` (dev tuning) |
| `at_pre_move` | `characters.py:1281` | interrupts the timed action, always allows the move (Epic A D1) |
| `skill_check` | `world/skillcheck.py:46` | `skill_check(skill_value, modifier=0)`; callers: `crafting_base.py:272`, `crafting_commands.py:578, 823`, `repair_commands.py:136`, `hunting_commands.py:96` (opposed), `:279` |
| Craft output | `world/crafting_base.py:324` | `obj.location = self.crafter` — no hooks run |
| Forage output | `commands/foraging_commands.py:138` | `item.move_to(caller, quiet=True)` — hooks run |
| Corpse | `typeclasses/corpse.py:80` | `get:false()` on every corpse; `PlayerCorpse` adds `get_from:corpse_grace()` |
| `move_to` | Evennia `objects/objects.py:1173`, hook order 1222–1224, call 1263 | step 1 `at_pre_move`, step 3 `destination.at_pre_object_receive(obj, source_location)` — abort on False |
| Receive hooks | `objects.py:2266, 2443, 2460` | `at_pre_object_receive(arriving_object, source_location, **kwargs) -> bool`; `at_object_leave(moved_obj, target_location, move_type, **kwargs)`; `at_object_receive(moved_obj, source_location, move_type, **kwargs)` |
| `at_post_move` | `objects.py:354` | `at_post_move(source_location, move_type="move", **kwargs)` — always called after a move |
| Default commands | Evennia `commands/default/general.py:422, 485, 545` | `CmdGet` (hook 466, `move_to` 472), `CmdDrop` (532), `CmdGive` (`at_pre_give` 595, `move_to` 601) — every path is a `move_to` into the character |
| Containers contrib | `contrib/game_systems/containers/containers.py:44, 52, 83, 99, 152, 227` | `ContribContainer`, `capacity = AttributeProperty(default=20)`, `at_pre_put_in` (item count at 99), `CmdContainerGet` (`move_to` 209), `CmdPut(CmdDrop)` (`at_pre_put_in` 279, `move_to` 283) |
| Inventory | `contrib/game_systems/clothing/clothing.py:642`; `commands/default_cmdsets.py:48, 166` | the clothing contrib's `CmdInventory` is the one installed — W2.2 subclasses it |
| Character creation | `docs/PolishedWorld_Character_Creation_Decomposition.md` CC1, CC4 | Points Build 6–18 → STR+SIZ 12–36; Damage Modifier and Strike Rank derive at Stage 5 |

## 4. Dependency graph

```
W1.1 world/encumbrance.py (pure: item_enc, carried_enc, enc_limit, state)
  ├─ W1.2 Character properties + @py surface
  │    ├─ W2.1 at_pre_object_receive ceiling + giver/getter message
  │    │    ├─ W2.2 crossing messages + inventory line
  │    │    ├─ W5.1 craft/forage surplus set down        (needs the refusal to exist)
  │    │    └─ W4.2 CmdPut installed                       (put goes through the hook)
  │    ├─ W3.1 physical_modifier() seam + three callers
  │    └─ W3.2 fatigue cost per room (at_post_move)
  └─ W4.1 Container typeclass, ENC capacity, no nesting, three prototypes
W6.1 docs close-out (after all) → W6.2 merge
```

Nothing depends on character creation: the limit reads `stats.str` and `stats.siz` whatever set them. Order (F) puts the code after chargen for the alpha's sake, not for this graph's.

## 5. Component W1 — The reader (Claude)

### Task W1.1 — `world/encumbrance.py`: pure functions over objects
- **Goal:** One module that answers *how much does this carry* and *what state is this character in*, with no state of its own.
- **Dependencies:** None.
- **Approach:** `item_enc(obj) -> int` reads `obj.attributes.get("enc", default=0)` and coerces to `int` (a missing field is 0 — the 20 `create_object` test objects and any builder-made object weigh nothing rather than raising). `carried_enc(holder) -> int` walks `holder.contents` recursively, summing `item_enc` and counting objects at 0, then adds `zero_count // 20` (WD4); the walk ignores objects that are characters or exits (`obj.has_account`, `obj.destination`), and stops at a depth of 4 as a guard — depth is 2 in practice (WD5). `enc_limit(char) -> int` is `stats.str.value + stats.siz.value`. `encumbrance_state(char) -> str` returns `"free"`, `"overloaded"` or `"ceiling"` from `carried_enc` against `limit` and `2 * limit`. Constants `OVERLOAD_FACTOR = 2` and `SMALL_ITEMS_PER_ENC = 20` at module top, each with its Legend line in the comment. Nothing writes.
- **Testing** (`tests/test_encumbrance.py`, `EvenniaTest`): an object with no `enc` weighs 0; `enc` 2 weighs 2; twenty objects at `enc` 0 sum to 1 and nineteen to 0 (the BACKLOG's required test); a container holding `enc` 3 adds 3 to the carrier (recursion); a character's limit is 20 at the defaults and 36 after `stats.str.base = 18; stats.siz.base = 18`; state is `free` at 20/20, `overloaded` at 21/20, `ceiling` at 41/20 (the boundaries, both sides). An `enc` stored as the string `"2"` is coerced, not summed as text (§11k: the negative case prints its type).
- **Mutations:** `SMALL_ITEMS_PER_ENC` → 19 (the twenty/nineteen test must fail); drop the recursion (the container test must fail); `>` → `>=` at the limit (the 20/20 test must fail).
- **Commit:** `feat(encumbrance): pure reader — item_enc, carried_enc, enc_limit, encumbrance_state`

### Task W1.2 — `Character.carried_enc`, `.enc_limit`, `.encumbrance_state` and the `@py` surface
- **Goal:** The three answers are one attribute read away on the character, so every consumer (W2, W3, W4, Stage 5) reads the same thing (P-2).
- **Dependencies:** W1.1.
- **Approach:** Three read-only properties on `Character` delegating to the module; no caching (WD3 b). A `encumbrance` paragraph in the class docstring beside the survival gauges. Testing Reference §11 gains the `@py` idiom: `self.msg(str((me.carried_enc, me.enc_limit, me.encumbrance_state)))` — a tuple, because `@py` discards return values (gotcha).
- **Testing:** the properties agree with the module functions on a loaded character; a spy on `carried_enc` proves `encumbrance_state` reads it rather than a stored value (§11f).
- **Mutations:** return a constant from `encumbrance_state` (the spy test must fail).
- **Commit:** `feat(encumbrance): character properties and the @py surface`

## 6. Component W2 — The ceiling and what the player sees (Claude; in-game protocol by Adam)

### Task W2.1 — `Character.at_pre_object_receive` refuses above the ceiling
- **Goal:** No path puts a character above 2 × (STR+SIZ): `get`, `give`, `get … from <corpse>`, and (after W4.2) `put` into a carried container all end in `move_to(character)`, and `move_to` asks the destination first.
- **Dependencies:** W1.2.
- **Approach:** Override `at_pre_object_receive(self, arriving_object, source_location, **kwargs)` (Evennia `objects.py:2266`): `if carried_enc(self) + item_enc(arriving_object) > OVERLOAD_FACTOR * enc_limit(self): message and return False`. The message goes to `self` (*"You cannot carry any more."*) and, when `source_location` is a character other than `self` (a `give`), to the giver (*"<n> cannot carry any more."*), because `CmdGive` prints nothing on a refused `move_to` beyond its own generic line. `super()` is called first and its False honoured. The hook is the ceiling only — the band is W3's, and movement is never refused (D1).
- **Testing:** at 39/20 a `get` of an `enc` 2 item is refused and the item stays in the room; at 38/20 it succeeds (41 > 40, 40 ≤ 40 — both sides of the boundary); a `give` across the ceiling leaves the item with the giver and messages both; `.call()` runs no locks (gotcha), so the refusal test also asserts the object's `location` — the independent receipt.
- **Mutations:** `>` → `>=` (the 38/20 test must fail); drop the giver message (its assertion must fail).
- **Commit:** `feat(encumbrance): at_pre_object_receive refuses above twice the limit`

### Task W2.2 — Crossing messages and the inventory line
- **Goal:** A player learns they are *Overloaded* the moment it happens, and `inventory` always shows where they stand.
- **Dependencies:** W2.1.
- **Approach:** Override `at_object_receive` and `at_object_leave` (`objects.py:2460, 2443`; both call `super()`): compute the state before and after — `at_object_leave` runs before the object has moved, so *before* is the current sum and *after* subtracts the leaver; `at_object_receive` runs after, so *before* adds nothing and *after* is current — and message only on a change: *"You are overloaded."* / *"You are no longer overloaded."* `commands/inventory_commands.py::CmdInventory(ClothingCmdInventory)` (`clothing.py:642`) appends one line, *"Carrying 7/20 ENC"*, with *" (overloaded)"* when in the band; it replaces the clothing import in `default_cmdsets.py:48`. The number in the line is the Testing Reference's in-game receipt for every protocol in this feature.
- **Testing:** picking up the item that crosses the limit messages once; picking up a second item in the band messages nothing (the *change* condition); dropping back under messages the recovery once; `inventory` output contains `7/20 ENC` for a known load and `(overloaded)` only in the band. Each message test asserts the count of messages, not their presence (the second-item case is the *nothing changed* receipt).
- **Mutations:** message unconditionally (the second-item test must fail); swap before/after in `at_object_leave` (the recovery test must fail).
- **Commit:** `feat(encumbrance): overloaded crossing messages and the inventory ENC line`

## 7. Component W3 — What the band costs (Claude)

### Task W3.1 — `physical_modifier()` and the three physical callers
- **Goal:** One seam returns the character's situational penalty on physical tests, and the callers Legend p.86 names add it.
- **Dependencies:** W1.2.
- **Approach:** `Character.physical_modifier(self) -> int` returns `OVERLOAD_PENALTY` (−20, `world/encumbrance.py`, Legend p.86) when `encumbrance_state != "free"`, else 0; it is the hook the Fatigue levels will add to (BACKLOG *Fatigue-exhaustion consequence*, bands −10…−50). Callers: `world/crafting_base.py:272` (craft) adds it to the tool modifier; `commands/crafting_commands.py:578` (`CmdDisassemble`) and `commands/repair_commands.py:136` (`CmdRepair`) likewise; `commands/hunting_commands.py:96` (`CmdHunt`) passes it as `attacker_mod` to `opposed_check` and `:279` (`CmdHarvest`) adds it. `crafting_commands.py:823` (`CmdScribe`, Lore) and forage (Survival) are left alone, with a one-line comment at each saying why (Legend's DEX/STR rule). The physical set is **locked here** (OQ2), not chosen per call site later.
- **Testing:** with `skill_check` patched to record its `modifier`, a craft at 21/20 passes −20 and at 20/20 passes 0; the same for disassemble, repair, hunt and harvest; a forage and a scribe at 21/20 pass 0 (each exclusion is a test, so a later "fix" trips it).
- **Mutations:** `!= "free"` → `== "ceiling"` (the 21/20 craft test must fail); remove the hunting wiring (its test must fail).
- **Commit:** `feat(encumbrance): physical_modifier() seam, applied by craft, repair and hunting`

### Task W3.2 — A fatigue cost per room moved while overloaded
- **Goal:** Distance costs: every room entered while *Overloaded* drains fatigue by `OVERLOAD_MOVE_FATIGUE`.
- **Dependencies:** W1.2.
- **Approach:** Override `Character.at_post_move(self, source_location, move_type="move", **kwargs)` (Evennia `objects.py:354`): `super()`, then if `move_type == "move"` and the state is not `free`, `fatigue.current -= OVERLOAD_MOVE_FATIGUE` (the ticker's own write, `survival_ticker.py:65`; the trait clamps at its `min`). Teleports and the respawn path (`move_type="teleport"`) cost nothing. `OVERLOAD_MOVE_FATIGUE = 1` to start — one room costs what one survival tick costs (`BASE_RATES["fatigue"] = 1`), calibrated at alpha close-out against the cohort's routes (OQ1); it is one knob, the band's only one. No message: the gauge's `descs` warnings (`_check_survival_warnings`) already fire on a bucket change, and the `inventory` line says why.
- **Testing:** a move at 21/20 lowers fatigue by exactly 1 and at 20/20 by 0; a `move_to(..., move_type="teleport")` at 21/20 by 0; fatigue at 0 stays 0 (the clamp, so the hook never goes negative). The *nothing changed* cases carry the move itself as receipt (`location` changed).
- **Mutations:** drop the `move_type` guard (the teleport test must fail); `-=` → `+=` (the 21/20 test must fail).
- **Commit:** `feat(encumbrance): fatigue cost per room while overloaded`

## 8. Component W4 — Containers (Claude)

### Task W4.1 — `typeclasses/containers.py::Container` with ENC capacity, and the three prototypes
- **Goal:** A sack holds ten ENC, not twenty things, and never holds another container.
- **Dependencies:** W1.1.
- **Approach:** `class Container(ObjectParent, ContribContainer)` (`containers.py:44`): `capacity` keeps the contrib's `AttributeProperty` but is read as ENC; `at_pre_put_in(self, putter, target, **kwargs)` (`:83`) refuses when `carried_enc(self) + item_enc(target) > self.capacity` (*"The sack is full."*) and when `target` is a `Container` (*"You cannot put a container inside another."*), each a separate test. `at_pre_get_from` (`:66`) stays the contrib's. `world/prototypes.py` `SACK` :700, `BACKPACK` :715, `SADDLEBAG` :741 get `"typeclass": "typeclasses.containers.Container"` and `"capacity": 10 / 20 / 15` (AoL pp.28–30); test (g)'s exemption list is **not** extended — a container is pickable and keeps its `enc`. `return_appearance` is the contrib's (contents listed), untouched: `look` stays the extended room's.
- **Testing:** `enc` 3 into a sack at 8/10 refused, at 7/10 accepted (both sides); a sack into a backpack refused; a sack holding 4 ENC adds 4 (plus its own 1) to the carrier; the three prototypes spawn as `Container` with the stated capacities (a loop over the three keys, `search_prototype(no_db=True)` as T1 did).
- **Mutations:** drop the nesting check (its test must fail); `>` → `>=` (the 7/10 test must fail).
- **Commit:** `feat(containers): Container typeclass with ENC capacity; sack, backpack, saddlebag use it`

### Task W4.2 — `CmdPut` installed; `help put`
- **Goal:** `put <item> in <container>` works for carried and floor containers, through the contrib's command and the project's hooks.
- **Dependencies:** W4.1, W2.1.
- **Approach:** `self.add(CmdPut())` beside `CmdContainerGet` in `commands/default_cmdsets.py:181` — the contrib's `CmdPut(CmdDrop)` (`containers.py:227`) already calls `at_pre_put_in` (279) then `move_to(container, move_type="drop")` (283). Putting into a *carried* container does not change the carrier's sum (WD5), so no character hook fires; putting into a floor container is a drop and fires `at_object_leave` (W2.2). `help put` and `help get` prose: one sentence each on capacity in ENC.
- **Testing:** `put` into a carried sack at capacity refused through the command (not only the hook — lesson 73: the protocol step is verified against the command's parse); `put` then `get … from` round-trips the item; `get … from` a sack when the carrier is at the ceiling is refused by W2.1 (the two hooks compose). The in-game protocol starts with `inventory` (lesson 71) and uses `-N` forms.
- **Mutations:** remove the `self.add` (the command tests must fail with *command not found*, printed).
- **Commit:** `feat(containers): CmdPut installed; help text`

## 9. Component W5 — Production paths (Claude)

### Task W5.1 — Crafting and foraging set the surplus down
- **Goal:** No path creates an object inside a character above the ceiling, and no yield is lost.
- **Dependencies:** W2.1.
- **Approach:** `world/crafting_base.py:324` `obj.location = self.crafter` becomes `if not obj.move_to(self.crafter, quiet=True): obj.move_to(self.crafter.location, quiet=True); self.crafter.msg(f"{name} is too much to carry; you set it down.")` — through `move_to` so W2.1 runs (today's assignment runs no hook at all). `commands/foraging_commands.py:138` gains the same fallback after its existing `move_to`; the node stays harvested (lesson 93) and the cooldown stays set. Both fallbacks are the one place a new object may land on the floor, named in the Testing Reference.
- **Testing:** a craft at the ceiling leaves its product in the room, messages, and the recipe's consumption is unchanged (the receipt that the craft ran); a forage at the ceiling leaves the yield in the room with the node decremented and the cooldown set; below the ceiling both land in the inventory as before (the existing craft and forage tests are the regression).
- **Mutations:** restore the direct assignment (the craft-at-ceiling test must fail); drop the fallback (the item ends with `location` None — the test asserts the room).
- **Commit:** `fix(crafting,forage): products go through move_to; surplus is set down at the ceiling`

## 10. Component W6 — Docs close-out and merge (Claude, on `main`)

### Task W6.1 — Documentation
- **Goal:** Every document that describes carrying, containers or fatigue says what the code does.
- **Dependencies:** W1–W5 shipped.
- **Approach:** This document's §§9–11 become records as the alpha content decomposition's did (Rev per shipped component); Testing Reference gains §11's `@py` idiom (W1.2), the fallback sites (W5.1) and an in-game protocol: `inventory` → gather to the band → `inventory` (the number) → one move (fatigue by 1) → `put`/`get … from` → the ceiling refusal → `drop` to recover. Evennia Reference gains the receive-hook order (`move_to` steps 1–3) and the containers contrib's two hooks (candidate list, with the EvMenu section CC4.1 owns). BACKLOG: *Weight and encumbrance* and *Full container support* → DONE; *Fatigue-exhaustion consequence* annotated with W3.1's seam and W3.2's cost. Roadmap: (E) gets its ✅ and the prerequisite line. Prose sites to sweep before code (the pattern in the gotcha file): `crafting_base.py` docstring at the output step; `help get`; the corpse docstring that says `CmdContainerGet` is the only container command (`corpse.py:239`).
- **Testing:** catalogue loop after the files exist in the tree (README Rev 9's rule); `git diff --check`.
- **Commit:** `docs: weight and encumbrance shipped (W1–W5); testing protocol; BACKLOG and roadmap`

### Task W6.2 — Merge
- **Goal:** `feature/weight` on `main` by merge commit, before *Persistent alpha instance* opens.
- **Dependencies:** W6.1.
- **Approach:** As the alpha content epic: PR, merge commit (not rebase), branch deleted, `git ls-remote` per ref (lesson 82), suite figure recorded from Adam's local run (the sandbox cannot run it across a turn).
- **Commit:** merge commit.

## 11. (reserved for records as tasks ship)

## 12. Open questions (each with the task that closes it)

- **OQ1 — `OVERLOAD_MOVE_FATIGUE`.** Pinned at 1 by W3.2 and calibrated at alpha close-out against how far the cohort actually hauls. Not a knob to turn before there is a route to measure.
- **OQ2 — The physical set.** Every Craft test (craft, disassemble, repair, harvest) and the hunt in; scribe and forage out. → W3.1 locks it with a test per exclusion.
- **OQ3 — Worn clothing.** Legend counts worn armour in the total (the armour table lists ENC). The clothing contrib keeps worn items in `contents`, so W1.1 counts them without a special case — decided by not deciding, and tested: a worn `enc` 1 cloak counts 1. → W1.1.
- **OQ4 — Builders.** A builder loading a room with `spawn` or `create` is not a character and is never refused; a builder *character* at the ceiling is. The Testing Reference names `@py me.encumbrance_state` as the first thing to check when `get` refuses. → W6.1.
- **OQ5 — `CoinPile`'s ENC and a corpse's coin.** Stage 5's, by WD7; nothing here closes it.

## 13. Consequences worth reading twice

- **The direction of 2026-10-18 is reversed (WD3).** A reader of BACKLOG Rev 41's annotation expects a buff and a rate multiplier; neither exists. The annotation is corrected in BACKLOG Rev 50 rather than left as history, because it reads as an instruction.
- **Every character carries 20 until chargen ships.** Dev characters, seeded protocols and the Testing Reference's figures assume 20; after CC1 the same protocol on a 12 or a 36 reads differently, so protocols state the limit they were run at.
- **The weight code does not need character creation.** Order (F) is about the alpha, not the graph (§4). If chargen slips, this feature can ship first without a migration — the limit reads whatever STR and SIZ are.
- **A missing `enc` is silent at runtime.** The reader's *missing = 0* (W1.1) keeps eight test files untouched and makes a forgotten field a weightless item in play. Test (g) is the guard, and it covers prototypes only; an object created by hand in the persistent instance is weightless until a builder sets `enc`. Named in the Testing Reference as a builder rule.
- **The ceiling is the first haulage.** With `wood` at `enc` 1, a 20-limit character hauls at most 40 logs in one trip and is overloaded for the last twenty rooms of it. A second character, or a second trip, is the price of distance from the first day — and the sack makes the hand-off one command.
- **Containers do not lighten.** A player who expects a backpack to *add* capacity (as in most MMOs) will find it adds organisation and a hand-off unit, and costs 1 ENC. `help put` says so in one sentence.
- **Prose sites.** Three named in W6.1 before code; expect three-to-four more (the epic pattern in the gotcha file).
