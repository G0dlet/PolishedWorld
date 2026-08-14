# PolishedWorld Evennia Reference

> **Rev 22 · 2026-08-14** — new **§14: XYZGrid & Wilderness**, pre-implementation source verification for roadmap Stage 6. No code written and neither contrib is in use, so the section carries an explicit status banner — but the reading answered the "verify at source" note that has sat in the Stage 6 entry since Rev 2, so it is written down while it is fresh rather than re-derived later. Read against Evennia `main` and then **diffed against the `v6.1.0` tag: all five relevant files are byte-identical**, so the findings apply to the pinned version rather than only to upstream. Four have teeth. **§14.2** `spawn_nodes()` deletes any XYZRoom whose coordinate has left the map string, and re-applies the prototype over survivors with `exact=False` — a `desc` edited in-game is lost at the next spawn, so grid areas are authored in map modules, not with `dig`/`desc`. **§14.5** wilderness room recycling resets `contents` and exit locks but **not Tags or Attributes**, which is precisely where ExtendedRoom keeps room states and seasonal descs — state leaks between coordinates on a shared shell. **§14.6** `get_objs_at_coordinates()` is an O(n) scan over the whole wilderness and runs on effectively every step, which rules out resource nodes as objects. **§14.7** the grid side composes with ExtendedRoom for free (the two contribs override different hooks and `XYZRoom.return_appearance` calls `super()`), while the wilderness side inherits the behaviour but cannot use the storage. Also §14.3: a misspelled `taget_map_xyz` on the `TransitionMapNode` base class, harmless via the registered legend class and an `AttributeError` if you subclass the base directly.
> **Rev 21 · 2026-08-05** — **§3.5 contained a statement this repo had already measured to be false.** Its `@py` note said comprehensions and generators both fail in `@py`; Testing Reference Rev 4 established on measurement that **comprehensions work** (PEP 709 gave them their own scope in 3.12) and that generators and lambda bodies are what fail. Two documents contradicting each other is worse than one saying nothing, so §3.5's note is corrected and now points at the Testing Reference rather than restating it. §3.5 also gains the fact that **`CounterTrait.current` returns a float** (20.0, not 20) — harmless until a value is stored or compared, at which point the float propagates somewhere it does not belong. New **§11.28**: Evennia deserialises Attribute containers into `_SaverDict`/`_SaverList`, for which `isinstance(x, dict)` is **False**, and `AttributeHandler.has()` returns a **list**, not a bool. Both verified live against Evennia 6.1.0 during Stage 4.5 Component B (363 tests green, 2026-08-05); the `_SaverDict` trap had bitten this project twice before and was not in this document at all.
> **Rev 20 · 2026-08-03** — **§7 rewritten; it was not merely stale but actively wrong.** The status line said *Planned* while `world/barter.py` has been merged since Stage 2, but the damage was further down: **§7.2** told the reader to add `CmdOffer`/`CmdAccept`/`CmdDecline`/`CmdEvaluate`/`CmdStatus` to `CharacterCmdSet`, which would make `offer` typable outside a trade and turn the §11.20 `status` collision from scoped into permanent — only `CmdPWTrade` is global, the rest arrive with `CmdsetTrade` at trade start. **§7.4** described coins as typeclassed objects offered like any other item, the architecture S4-2 explicitly rejected; it now documents the handler-level bridge shipped in Stage 4 Component E (digit-first segment classification, gross re-validation, net settlement, one-shot flag, unledgered per S4-4). New **§7.3** documents the module-global patch mechanism and its seven swaps; new **§7.5** tabulates the five confirmed upstream bugs, of which the direct `obj.location` assignment in `finish()` is the one with teeth — **no move hook fires in a trade, ever**. **§7.6** records that the trade cmdset is added rather than Replace, which is why the staleness guards must exist. Also: the contrib status table was wrong on five rows (Barter, CooldownHandler, BuffHandler, Crafting, Clothing all read *Planned* while in use) — corrected against a grep of the repo, not from memory. `TickerHandler` is deliberately left untouched: whether the survival ticker goes through it or through a Script has not been verified, and correcting an unchecked row is the same failure this Rev is fixing.

> **Rev 19 · 2026-08-02** — One lesson from Stage 4 Component D, verified live against Evennia 6.1.0 with the suite running in-sandbox (256 tests green, 2026-08-02): **§11.27** the identity-marker pattern for cancelling a `utils.delay` from somewhere that never saw the task. A string or task-key flag is **not** sufficient — start an action, abandon it, start the same action again, and the first callback wakes up, recognises the flag value, and completes against the second attempt. A per-attempt `object()` compared with `is` cannot collide. Carries the four constraints that come with it: `ndb` and the delay must be non-persistent *together*; the callback must re-check the world and not only the marker; `has_account` is the "still playing" guard under statue-logout; and the callback belongs at module level so it is testable without a reactor. Also records that a delayed action moving currency must keep its **whole** check-and-commit sequence inside the callback (S4-R1) — a precondition checked before the delay and committed after it reopens a window `duration` seconds wide.

> **Rev 18 · 2026-08-02** — One lesson from Stage 4 Component C, verified live against Evennia 6.1.0 with the suite running in-sandbox (184 tests green, 2026-08-02): **§11.26** `EvenniaCommandTestMixin.call()` does **not** run command locks — it goes straight from `at_pre_cmd()` to `func()` with no `access()` check anywhere — so a "this command refuses an unprivileged caller" test written with `.call()` passes **vacuously**, having silently asserted the opposite of what it claims. Permission tests must call `Command.access(caller, "cmd")` directly, which is what the real cmdhandler uses.

> **Rev 17 · 2026-07-30** — Two new lessons from Stage 4 Component B, both verified live against Evennia 6.1.0 with the suite running in-sandbox (129 tests green, 2026-07-30): **§11.24** in the stock `EvenniaTest` fixture `char2` cannot be puppeted, because its puppet lock is `puppet:pperm(Developer)` while `create_accounts()` grants Developer to `account` only — and the auto-puppet fails the lock **silently**, so every test that needs a *played* second party quietly becomes a refusal test instead; **§11.25** `Object.search()`'s local candidate set is `self.contents + [location] + location.contents`, which both gives same-room scoping for free (a target inside a container is a clean miss) and includes the room object itself, and a `#dbref` makes the search global *before* the `use_dbref` permission check, so room scoping is not airtight against Builder+.

> **Rev 16 · 2026-07-27** — Three new lessons from Stage 4 Component A, all verified live against a real test database (82 tests green, 2026-07-27): **§11.21** `typeclass_search(cls, include_children=True)` is literally `cls.objects.all_family()`, and `get_by_attribute()` is the better primitive when the question is "everything that has X" rather than "everything that is X"; **§11.22** a `GLOBAL_SCRIPTS` entry with no `interval` is pure persistent world storage, not a ticker, and is auto-recreated after a database reset; **§11.23** an Attribute row does not exist until first write, so a handler reading with `default=` makes backfill unnecessary rather than merely guarded — the structural escape from the §3.5 family of traps.

> **Rev 15 · 2026-07-26** — **§11.20 corrected — the tie-break was inverted.** Rev 14 derived it from `cmdsethandler.update()` (`new_current = cmdset + new_current`, accumulator on the right), whose own docstring disclaims matching runtime. The real runtime merge is `cmdhandler.get_and_merge_cmdsets()`: `tempmergers[prio] = tempmergers[prio] + cmdset` puts the *incoming* set on the right, and `__add__` gives the right operand the tie. `DefaultObject.get_cmdsets()` returns the raw `cmdset_stack`, so a runtime-added set enters as its own entry, after `CharacterCmdSet`. **Correct rule: on a priority tie the LATER-merged cmdset wins**, and hands the key back when removed. Empirically confirmed in game 2026-07-26 — our `CmdStatus` (`status`/`vitals`) and barter's `CmdStatus` (`status`/`offers`/`deal`) coexist, vitals outside a trade, offer table inside. Stage 3 H.1's mechanical premise therefore did not hold (the decision stands on UX grounds; see Recipe-Knowledge Rev 11). §11.14 re-verified independently: its collision is real but goes through `CmdSet.add()`, not `_union` — same direction, different code path, cross-ref corrected.

> **Rev 14 · 2026-07-26** — New §11.20 (verified live against Evennia `main` — `commands/cmdset.py`, `cmdsethandler.py`, `commands/command.py`): a duplicate command key across two cmdsets at **equal priority** is *silently deleted*, not shadowed, and the survivor is the **already-merged (lower) set**, not the one added last — the opposite of the natural intuition. `Command.__eq__` matches on key+alias **intersection** and `__hash__` on key alone, so an alias overlap is enough. Worked example: a global `accept` in `CharacterCmdSet` would erase barter's `CmdAccept` (and our `CmdPWAccept` ownership backstop) for the whole trade session. §11.14's `look`/`ExtendedRoomCmdSet` collision is the same lesson's first instance; cross-referenced. Drove Stage 3 H.1's decision to extend `learn` rather than key a new `accept`.
> **Rev 13 · 2026-07-11** — New §11.19 (verified live): `TagHandler` key normalisation (`add`/`get`/`has` lower-case + strip; internal spaces kept), `add()` DB-level idempotency, and `get(category=…, return_list=True)` → list-of-key-strings (`[]` when empty) / `has(single_key)` → `bool`. Underpins the Stage 3 Component A known-recipe set (`Character.knows_recipe`/`learn_recipe`/`known_recipes`).
> **Rev 12 · 2026-07-11** — Doc hygiene: §8.8's "is wearing nothing" backlog candidate trimmed to a pointer at `docs/BACKLOG.md` (the technical finding stays; only the backlog note moved). No other change.
> **Rev 11 · 2026-07-11** — Crafting Progression Component G (superior-tool scaling), verified live: §8.7 updated — `_tool_modifier` now has a **superior branch** reading the tool's OWN `db.quality` (stamped by `do_craft` on every output, tools included, *before* `_finalize_item`), banded via `quality_band`: `superior` (>100) → `+tool_bonus` (10), plain present → 0, absent/broken → penalty; **`db.quality` is `None`-guarded** (an uncrafted/admin tool like the metal `KNIFE` has no quality stamp → short-circuits to baseline 0 before banding, else `quality_band(None)` raises). §8.7 `CmdRepair` gap CLOSED — `_tool_modifier(caller, target)` is generalised per target via `target.db.repair_tool_tag` (unset → needle default; `""` → no tool; verified the spawner stores an empty-string top-level prototype key faithfully, so the `""` sentinel is reliable), target excluded from the search, broken tools skipped. §8.9 max-quality note **110 → 111** (a superior tool's +10 with `skillcheck` never clamping `target`). **Stage 2 closed.**
> **Rev 10 · 2026-07-11** — Crafting Progression Component E (quality → capability): new §8.9 (verified live) — a shared `_finalize_item` body must be a **plain module-level function**, not a `CraftingRecipe` subclass, or `_load_recipes()` registers it as a phantom recipe; `_finalize_item` runs in `do_craft` after `obj.db.quality`/`crafted_by` are stamped and before `obj.location = crafter`, so writing `obj.db.condition` there overrides the `DurableObject` autocreate default; the craft quality scale is discrete (`{25, 50, 100, 100+crit_score}`, max **110** post-A-flip) with `superior = quality > 100`; and to force a tier in tests, monkeypatch **`world.crafting_base.skill_check`** (the bound name), not `world.skillcheck.skill_check`.
> **Rev 9 · 2026-07-10** — Component D repair/tuning verified: §8.7 updated — `CmdRepair` gate is now `isinstance(target, DurableObject)` (tools + garments repairable), materials data-driven via `target.db.repair_materials or REPAIR_MATERIALS`; and the §10.1 prototype-key-vs-autocreate override is **confirmed** (spawn `stone_knife`/`bone_needle` with `"condition": 40/30` → `db.condition` 40/30; prototype top-level key wins over the mixin's AttributeProperty default). Clears the "unverified" flags in §8.7 and the §10.1 corollary.
> **Rev 8 · 2026-07-10** — Crafting Progression Component D (wear/repair): new §8.8 (verified live) — `self.validated_tools` is ALWAYS empty for `MongooseCraftRecipe` (tools live only in `self.inputs`, read via `_used_tool()`); `craft()` lifecycle (side-effects in `do_craft`, emit in `post_craft`); broken tools linger (no delete); `ContribClothing.get_display_desc` describes a *wearer* so a looked-at garment says "is wearing nothing"; `condition_line()` colour bands (|g>66 |y33–66 |r<33). Corrects §9's `validated_tools` wording (Decomposition Rev 4).
> **Rev 7 · 2026-07-10** — Crafting Progression Component C (tool bootstrap): new §8.7 (verified live) — `MongooseCraftRecipe._tool_modifier` returns 0 for `tool_tag=None` *before* the penalty path (bootstrap-safe, no −20); the base has **no** `min_skill`/skill-floor (ungated by default — Component F adds gating); `CmdHarvest` iterates template parts dynamically, so adding a part is pure data and existing corpses gain it live after reload; `CmdRepair` is gated to `ClothingWithBuffs` only (tools not yet repairable — Component D convergence). §10.1 corollary — a crafted/spawned `Tool` autocreates `condition=100` free (confirmed end-to-end); prototype-key-vs-autocreate override still unverified (flag for Component D.5).
> **Rev 6 · 2026-07-10** — Crafting Progression Component B (shared durability): §10.1 AttributeProperty-on-a-mixin (init_evennia_properties walks full __mro__ → autocreate fires on the host; MRO gives the mixin's descriptor precedence, no migration), §11.17 exec/shell-defined throwaway typeclasses fall silently to DefaultObject, §11.18 ContribClothing.wear stores wearstyle *as* db.worn (pass True for style-less wear).
> **Rev 5 · 2026-07-10** — Skill-improvement Session C: §3.5 `desc()`-reads-`.value` corollary — tier-lookup på permanent nivå måste ske på råa `.current`-ints via `tier_for`, inte `skill.desc()`.
> **Rev 4 · 2026-07-06** — Stage-1 skill-improvement session: §3.5 CounterTrait setter-clamps addendum, §6.2 cooldown real-time-seconds note, §11.16 `evennia shell` interactive-console paste gotcha.
> **Canonical:** `docs/PolishedWorld_Evennia_Reference.md` @ G0dlet/PolishedWorld — git wins. If this project-knowledge copy's Rev is lower than the repo's, it's stale — re-upload from the repo.
 
**Purpose:** Curated reference of Evennia modules and contribs used (or planned) in PolishedWorld. This is a working document — extend as new systems are integrated. Verified against Evennia `main`; per-copy freshness is tracked in the Rev header above.
 
**How to use:** Treat this as the primary lookup for Evennia API in this project. When something is missing or unclear, fall back to:
1. `web_fetch` against `https://raw.githubusercontent.com/evennia/evennia/main/...` for ad-hoc deep dives
2. Per-session zip upload for navigating the full source tree
---
 
## 1. GameTime — Standard vs Custom
 
PolishedWorld uses a **13-month, 364-day fantasy calendar at 4× real-time speed**. Two related modules handle time, and the distinction matters.
 
### 1.1 `evennia.utils.gametime` (built-in, real-world calendar)
 
**Path:** `evennia/utils/gametime.py`
 
**Use for:** Server uptime, runtime, raw timestamps. **Not** for in-game date display in PolishedWorld — its date math assumes a 12-month real-world Gregorian calendar.
 
Key functions:
 
```python
from evennia.utils import gametime
 
gametime.runtime()              # Total server runtime in seconds (excluding downtimes)
gametime.uptime()               # Time since last reload
gametime.gametime(absolute=False)   # Float seconds; if absolute=True, includes TIME_GAME_EPOCH
gametime.server_epoch()         # Real-world unix epoch when the server first started
gametime.game_epoch()           # In-game epoch (settings.TIME_GAME_EPOCH or server_epoch)
```
 
**Critical:** `gametime.gametime()` returns a flat seconds count. To convert to a date, the docstring suggests `datetime.fromtimestamp(...)` — but that assumes a real-world calendar and **will break for a 13-month year**. Use `custom_gametime` instead.
 
Settings used:
- `TIME_FACTOR` (default 1.0) — speedup multiplier. PolishedWorld uses 4.0
- `TIME_IGNORE_DOWNTIMES` — if True, in-game time keeps advancing during server downtime
- `TIME_GAME_EPOCH` — the absolute in-game start datetime (unix timestamp)
### 1.2 `evennia.contrib.base_systems.custom_gametime` (custom calendar)
 
**Path:** `evennia/contrib/base_systems/custom_gametime/custom_gametime.py`
 
**Use for:** All in-game date arithmetic in PolishedWorld.
 
Configured via the `TIME_UNITS` settings dict, where each unit is expressed in seconds. Default:
 
```python
TIME_UNITS = {
    "sec": 1,
    "min": 60,
    "hr": 60 * 60,
    "hour": 60 * 60,
    "day": 60 * 60 * 24,
    "week": 60 * 60 * 24 * 7,
    "month": 60 * 60 * 24 * 7 * 4,    # 28 days
    "yr": 60 * 60 * 24 * 7 * 4 * 12,
    "year": 60 * 60 * 24 * 7 * 4 * 12,
}
```
 
Adapt for the 13-month / 364-day calendar (28 days × 13 months = 364):
 
```python
# In settings.py
TIME_UNITS = {
    "sec": 1,
    "min": 60,
    "hr": 3600,
    "hour": 3600,
    "day": 86400,
    "week": 86400 * 7,           # 7-day weeks
    "month": 86400 * 28,         # 28-day months (4 weeks)
    "yr": 86400 * 28 * 13,       # 13-month year = 364 days
    "year": 86400 * 28 * 13,
}
```
 
Public API:
 
```python
from evennia.contrib.base_systems import custom_gametime
 
# Get current in-game time as a tuple (year, month, week, day, hour, min, sec)
custom_gametime.custom_gametime(absolute=False)
# absolute=True returns time since TIME_GAME_EPOCH; otherwise since server start
 
# Convert in-game time to real seconds
custom_gametime.gametime_to_realtime(days=2)            # → real seconds for 2 in-game days
custom_gametime.gametime_to_realtime(days=2, format=True)  # → (yr, month, week, day, hr, min, sec)
 
# Convert real time to in-game time
custom_gametime.realtime_to_gametime(days=3, mins=34)
custom_gametime.realtime_to_gametime(days=3, mins=34, format=True)
 
# Schedule a callback at an absolute in-game time
custom_gametime.schedule(callback, repeat=True, hour=10)         # next 10:00 in-game
custom_gametime.real_seconds_until(hour=5, min=10, sec=0)        # seconds until that time
```
 
### 1.3 ⚠️ Critical indexing gotcha
 
**`custom_gametime()` returns 0-indexed values.** This is easy to miss because the source comment around `real_seconds_until` says *"day/week/month start from 1, not from 0"* — but that comment refers only to the **kwargs you pass in** when scheduling (calendar-style: "schedule for day 5"), not to what `custom_gametime()` **returns**.
 
The math is just integer division on elapsed seconds:
 
```python
# In time_to_tuple():
results.append(seconds // divisor)
seconds %= divisor
```
 
So at exactly server start, `custom_gametime()` returns `(0, 0, 0, 0, 0, 0, 0)` — year 0, month 0, day 0.
 
**Implication for `gametime_utils.py`:**
 
| Use case | Indexing |
|---|---|
| Reading current time → tuple | 0-indexed (add +1 for "Month 1, Day 1" UI display) |
| `schedule(month=3, day=5)` | 1-indexed (calendar-style input) |
| `real_seconds_until(month=3, day=5)` | 1-indexed |
 
**Verification command** to run in-game:
 
```python
@py from evennia.contrib.base_systems import custom_gametime; print(custom_gametime.custom_gametime())
```
 
Run this immediately after a fresh server start — if the first values are zeros, indexing is confirmed 0-based.
 
---
 
## 2. ExtendedRoom
 
**Path:** `evennia/contrib/grid/extended_room/extended_room.py`
 
**Status in PolishedWorld:** Currently being integrated; `typeclasses/rooms.py` overrides `get_time_of_day()` and `get_season()` to delegate to `gametime_utils`.
 
### 2.1 Class structure
 
```python
from evennia.contrib.grid.extended_room import ExtendedRoom
 
class Room(ExtendedRoom):
    pass
```
 
`ExtendedRoom` extends `DefaultRoom` and adds:
 
- **Seasonal descriptions** via `desc_spring`, `desc_summer`, `desc_autumn`, `desc_winter` Attributes
- **Time-of-day embedded text** via `$state(roomstate, txt)` and `$timeofday(morning, txt)` funcparser tags
- **Room states** as Tags with category `"room_state"` (e.g., `on_fire`, `flooded`)
- **Details** — look-targets without database objects (e.g., `look mural`)
- **Random room broadcast messages** at a configurable rate
### 2.2 ⚠️ Default time/season methods do NOT use custom_gametime
 
Built-in implementation (lines 224–260 of source):
 
```python
def get_time_of_day(self):
    timestamp = gametime.gametime(absolute=True)
    datestamp = datetime.datetime.fromtimestamp(timestamp)   # ← real-world calendar!
    timeslot = float(datestamp.hour) / self.hours_per_day
    # ...
 
def get_season(self):
    timestamp = gametime.gametime(absolute=True)
    datestamp = datetime.datetime.fromtimestamp(timestamp)   # ← real-world calendar!
    timeslot = float(datestamp.month) / self.months_per_year
    # ...
```
 
`datetime.fromtimestamp()` cannot represent month 13, so for PolishedWorld you **must override** both methods. The contrib's docstring confirms this: *"Override to customize."*
 
Override pattern (already what's planned in `typeclasses/rooms.py`):
 
```python
from evennia.contrib.grid.extended_room import ExtendedRoom
from world import gametime_utils
 
class Room(ExtendedRoom):
    # Match PolishedWorld's 7-period day
    times_of_day = {
        "night":     (0,           4 / 24),    # 00:00 - 04:00
        "dawn":      (4 / 24,      6 / 24),    # 04:00 - 06:00
        "morning":   (6 / 24,     11 / 24),    # 06:00 - 11:00
        "day":       (11 / 24,    14 / 24),    # 11:00 - 14:00
        "afternoon": (14 / 24,    18 / 24),    # 14:00 - 18:00
        "evening":   (18 / 24,    20 / 24),    # 18:00 - 20:00
        "dusk":      (20 / 24,     0),         # 20:00 - 00:00 (wrap)
    }
    # Override months_per_year on the class for season math
    months_per_year = 13
 
    def get_time_of_day(self):
        return gametime_utils.get_time_of_day()
 
    def get_season(self):
        return gametime_utils.get_season()
```
 
The exact period boundaries above are illustrative — adjust to PolishedWorld's finalized 7-period spec.
 
### 2.3 Room state API
 
```python
room.add_room_state("on_fire", "smoky")
room.remove_room_state("on_fire")
room.clear_room_state()
room.room_states                     # → sorted list of active states
```
 
Add a description that only shows when a state is active:
 
```python
room.add_desc("Flames lick the walls.", room_state="on_fire")
```
 
### 2.4 Embedded conditional text
 
Within any `desc` you can use funcparser tags:
 
```
The marketplace is bustling. $state(on_fire, Smoke chokes the air.) $timeofday(night, Lanterns flicker overhead.)
```
 
These resolve at look-time per viewer — no extra plumbing needed.
 
### 2.5 Random room broadcast
 
```python
class TavernRoom(Room):
    room_message_rate = 60  # seconds (real time)
    room_messages = [
        "A drunk laugh erupts from a corner.",
        "The fire crackles softly.",
    ]
```
 
⚠️ Rate is in **real seconds**, not in-game time. Started in `at_init()`, so it survives server reload.
 
### 2.6 Built-in commands (added via `ExtendedRoomCmdSet`)
 
- `look` — extended (handles details + room state desc)
- `desc` — interactive desc editor with seasonal support
- `detail` — add/remove look-targets
- `roomstate` — toggle room states
- `gametime` — show in-game time/season
---
 
## 3. TraitHandler (already in use)
 
**Path:** `evennia/contrib/rpg/traits/traits.py`
 
**Status in PolishedWorld:** Implemented in Phase 1 — Mongoose Legend stats, survival gauges, percentile skills.
 
### 3.1 Installation pattern
 
```python
from evennia.utils.utils import lazy_property
from evennia.contrib.rpg.traits import TraitHandler
 
class Character(DefaultCharacter):
    @lazy_property
    def traits(self):
        return TraitHandler(self)
 
    def at_object_creation(self):
        # Mongoose Legend characteristics
        self.traits.add("str", "Strength",     trait_type="static", base=10)
        self.traits.add("dex", "Dexterity",    trait_type="static", base=10)
        self.traits.add("con", "Constitution", trait_type="static", base=10)
        # Survival gauges
        self.traits.add("hunger",  "Hunger",  trait_type="gauge", min=0, max=100, base=100)
        self.traits.add("thirst",  "Thirst",  trait_type="gauge", min=0, max=100, base=100)
        self.traits.add("fatigue", "Fatigue", trait_type="gauge", min=0, max=100, base=100)
        # Percentile skill
        self.traits.add("athletics", "Athletics", trait_type="counter", min=0, max=100, base=20)
```
 
### 3.2 Built-in trait types
 
| `trait_type` | Class | Use case |
|---|---|---|
| `"static"` | `StaticTrait` | Fixed value with bonuses (e.g., STR, DEX) |
| `"counter"` | `CounterTrait` | Bounded value that increments (e.g., XP, percentile skill) |
| `"gauge"` | `GaugeTrait` | Counter where `current` defaults to `max` (e.g., HP, hunger) |
| `"trait"` | `Trait` | Base trait — has `value` only |
 
### 3.3 Common operations
 
```python
char.traits.str.value       # → current effective value (base + mod) * mult
char.traits.str.base        # → base value only
char.traits.str.mod         # → modifier only
char.traits.str += 2        # works on most trait types
char.traits.hunger.current  # gauge: current value (drinking/eating modifies this)
char.traits.hunger.max      # gauge: cap
 
char.traits.all             # → list of all trait keys
char.traits.get("str")      # → trait or None
char.traits.remove("str")
char.traits.clear()
```
 
### 3.4 Custom trait classes
 
For something Mongoose-Legend-specific (e.g., a wound trait that handles serious/major wounds), subclass and register:
 
```python
from evennia.contrib.rpg.traits import StaticTrait
 
class WoundTrait(StaticTrait):
    trait_type = "wound"   # registers it; use this string in .add()
 
    @property
    def is_serious(self):
        return self.value >= self.serious_threshold
```
 
In `settings.py`:
 
```python
TRAIT_CLASS_PATHS = ["world.traits.WoundTrait"]
```
 
Then: `char.traits.add("left_arm", "Left Arm", trait_type="wound", base=0)`.
 
### 3.5 ⚠️ Counter/gauge `.value` läser `.current`, inte `.base`

`CounterTrait`/`GaugeTrait`: `value = (current + mod) * mult`. Gettern för `current` är
`self._data.get("current", self.base)` — den faller tillbaka på `base` **bara om `current`
är osatt**. Men `traits.add(..., base=N)` pinnar `current=N` redan vid skapandet, så att
sätta `.base` i efterhand lagras men flyttar **inte** `.value`.

```python
skill = char.skills.get("hunting")   # added with base=25 -> current pinned to 25
skill.base = 100                      # stored, but ignored by .value
skill.value                           # -> 25.0   (reads current, not base)
skill.current = 100                   # THIS moves it
skill.value                           # -> 100.0
```

**Regel:** för att ändra en counter/gauge-traits effektiva värde, sätt `.current` (eller
`.mod`), aldrig `.base`. Gäller skills, survival-gauges och allt counter-baserat. (Static
traits skiljer sig: där *är* `value = (base + mod) * mult`, jfr 3.3.)

**`@py`-not (separat gotcha) — RÄTTAD i Rev 21:** `@py` bygger om sitt namespace per rad och
skriver aldrig tillbaka — inga namn överlever mellan rader. Spelvärld/DB-state persisterar dock.
⚠️ Rev 1–20 påstod här att *"comprehensions/generators failar"*. Halva påståendet var fel, och
det mättes: `py` kör `eval(code, {}, available_vars)`, alltså **tom globals-dict**, men PEP 709
gav comprehensions egen scope i 3.12, så de **fungerar**. Det som failar är generator-uttryck och
lambda-*kroppar*, som slår upp fria namn i de tomma globals. Bärande regel: *varje namn som
används inuti en lambda eller generator måste komma in som argument.* Fullständig tabell och de
diskriminerande testformerna: **Testing Reference Rev 4 §3** — den är källan, det här är en
pekare.

**Settern klampar också (verifierat 2026-07-06):** `current`-*settern* kör `_enforce_boundaries`,
så `skill.current = X` klampas till `[min, max]` vid tilldelning (max via `>=`). En read-modify
-write som `skill.current = skill.current + gained` auto-kappar därför vid traitens max (skills
använder `max=100`) — ingen manuell `min(cap, …)` krävs för säkerhet, men explicit klampning i
Python håller ett returnerat `old/new/delta` exakt. **Progression läser `.current`** (permanent
nivå), **resolution läser `.value`** (`(current + mod) * mult`, situationell) — en tool-`.mod`-buff
ska hjälpa själva checken men inte höja en improvement-rolls target.
**Corollary — `desc()` läser också `.value`:** `CounterTrait.desc()` slår upp descs-etiketten mot `self.value` (buffad), inte `.current`. En aktiv `.mod` (t.ex. +20 tool-buff) kan därför få `desc()` att rapportera fel tier. För tier-lookup på *permanent* nivå (t.ex. desc-tier-celebration som ska spegla verklig rang, inte tillfällig buff): använd en ren `tier_for(value, descs)` som speglar Evennias övre-gräns-inklusive-loop men tar en explicit int (`world/improvement.tier_for`), matad med de råa `old`/`new`-ints från `improve_skill_on_use`. Samma `.current`/`.value`-regel, en gång till.

**`.current` är en `float` (verifierat 2026-08-05):** `CounterTrait` lagrar 20.0, inte 20 — synligt
redan i exemplet ovan (`skill.value  # -> 25.0`), men lätt att läsa förbi. Ofarligt så länge värdet
bara jämförs, men så fort det *lagras* eller matas in i en ren funktion propagerar floaten dit den
inte hör hemma. Coerca explicit vid anropsstället, inte inuti mottagaren, så trunkeringen syns där
den sker: `improve_skill_on_use` skriver `int(skill.current)`, och `world/skill_xp.py` gör samma sak
innan nivån går in i `xp_threshold()`. Riktningen spelar roll där: `int()` trunkerar nedåt, vilket är
rätt för ett golv som ska vara det *minsta* värde som är förenligt med nivån.

---
 
## 4. BuffHandler (planned)
 
**Path:** `evennia/contrib/rpg/buffs/buff.py`
 
**Status in PolishedWorld:** Planned for environmental effects (cold, exhaustion buffs from weather/state).
 
### 4.1 Installation
 
```python
from evennia.utils.utils import lazy_property
from evennia.contrib.rpg.buffs import BuffHandler
 
class Character(DefaultCharacter):
    @lazy_property
    def buffs(self) -> BuffHandler:
        return BuffHandler(self)
```
 
### 4.2 Defining a buff
 
`BaseBuff` is the parent class. Class-level attributes are immutable; cache values are mutable per-instance.
 
```python
from evennia.contrib.rpg.buffs import BaseBuff
 
class Frostbite(BaseBuff):
    key = "frostbite"
    name = "Frostbite"
    flavor = "Your fingers ache from the cold."
 
    duration = -1            # -1 = permanent until removed; 0 = instant; >0 = seconds
    refresh = True           # Reapplying refreshes timer
    unique = True            # Replace existing buff with same key
    maxstacks = 3            # Up to 3 stacks
    tickrate = 30            # Tick every 30 seconds (0 = no tick)
 
    triggers = ["take_damage"]   # Will respond to handler.trigger("take_damage")
    mods = []                    # Stat modifications (see samplebuffs.py)
 
    def at_apply(self, *args, **kwargs):
        self.owner.msg("|cYour skin tightens against the cold.|n")
 
    def at_tick(self, initial=True, *args, **kwargs):
        if not initial:
            self.owner.traits.hp.current -= 1 * self.stacks
 
    def at_trigger(self, trigger, *args, **kwargs):
        # Called when handler.trigger(trigger) is invoked
        pass
 
    def at_remove(self, *args, **kwargs):
        self.owner.msg("|cThe cold subsides.|n")
```
 
### 4.3 Handler operations
 
```python
char.buffs.add(Frostbite)
char.buffs.add(Frostbite, stacks=2, duration=300)
char.buffs.add(Frostbite, to_cache={"intensity": 0.7})  # extra runtime data
 
# Modify a value through buffs
modified_damage = char.buffs.check(damage, "incoming_damage")
 
# Trigger event
char.buffs.trigger("take_damage")
 
# Inspection / removal
char.buffs.get("frostbite")
char.buffs.remove("frostbite")
char.buffs.clear()
```
 
### 4.4 `playtime` flag for offline players
 
```python
class StarvationBuff(BaseBuff):
    playtime = True   # Pauses while character is unpuppeted
```
 
Useful so logged-out players don't starve to death.
 
---
 
## 5. TickerHandler (for global survival ticker)
 
**Path:** `evennia/scripts/tickerhandler.py`
 
**Status in PolishedWorld:** Planned for the global survival depletion ticker. **Memory-flagged decision: one global ticker, not per-character** — more efficient and aligns with Evennia best practice.
 
### 5.1 Access pattern
 
```python
from evennia import TICKER_HANDLER as ticker
```
 
### 5.2 Adding a ticker
 
```python
ticker.add(
    interval=60,                          # seconds between calls
    callback=world.survival.tick_all,     # global function
    idstring="survival_global",           # disambiguator
    persistent=True,                      # survives server reload
)
```
 
The callback can be a top-level function **or** a method on a typeclassed entity. For "global" tickers, use a top-level function — it doesn't tie the ticker to a specific object's lifetime.
 
### 5.3 Removing
 
```python
ticker.remove(
    interval=60,
    callback=world.survival.tick_all,
    idstring="survival_global",
    persistent=True,
)
# Or: ticker.remove(store_key=stored_key)   # store_key returned by .add()
```
 
### 5.4 Implementation sketch for global survival ticker
 
```python
# world/survival.py
from evennia import search_object
from evennia.objects.objects import DefaultCharacter
 
def tick_all():
    """Called every N seconds by TickerHandler. Decrements survival gauges
    on all puppeted characters."""
    for char in DefaultCharacter.objects.filter(db_account__isnull=False):
        if not char.has_account:   # not currently puppeted
            continue
        char.traits.hunger.current -= 1
        char.traits.thirst.current -= 1
        char.traits.fatigue.current -= 1
        # Trigger buffs based on thresholds
        if char.traits.hunger.current <= 20:
            char.buffs.add(StarvingBuff)
```
 
Register once at server start (e.g., in a server-start hook or a one-shot `@py` command):
 
```python
@py from evennia import TICKER_HANDLER; from world.survival import tick_all; \
    TICKER_HANDLER.add(interval=60, callback=tick_all, idstring="survival_global", persistent=True)
```
 
⚠️ **Multiplayer note:** Don't iterate over *all* characters — only **puppeted** ones. Otherwise an idle DB with thousands of unused characters drags every tick. The `playtime` flag on buffs (section 4.4) can complement this for offline pause behavior.
 
⚠️ **Don't double-register.** TickerHandler doesn't deduplicate by callback identity alone; the same `(interval, callback, idstring, persistent)` tuple is the unique key. Use a unique `idstring` so re-running the registration doesn't silently spawn a second ticker.
 
### 5.5 Tickers vs Cooldowns vs delay()
 
| Use case | Tool |
|---|---|
| Recurring server-wide event (every N seconds) | `TickerHandler` |
| One-shot delayed callback | `evennia.utils.delay()` |
| Rate-limit player actions (no callback needed) | `CooldownHandler` (section 6) |
| Buff with periodic effect on one character | `BaseBuff.tickrate` (handled by buffs internally) |
 
---
 
## 6. CooldownHandler
 
**Path:** `evennia/contrib/game_systems/cooldowns/cooldowns.py`
 
**Status in PolishedWorld:** Planned for skill use rate-limiting and Mongoose-Legend-style real-time-with-cooldowns combat.
 
### 6.1 Installation
 
```python
from evennia.utils.utils import lazy_property
from evennia.contrib.game_systems.cooldowns import CooldownHandler
 
class Character(DefaultCharacter):
    @lazy_property
    def cooldowns(self):
        return CooldownHandler(self, db_attribute="cooldowns")
```
 
### 6.2 API
 
```python
char.cooldowns.ready("power_attack")          # → bool
char.cooldowns.time_left("power_attack")      # → float (seconds)
char.cooldowns.time_left("power_attack", use_int=True)  # → int
 
char.cooldowns.add("power_attack", 10)        # 10s cooldown
char.cooldowns.extend("power_attack", 5)      # add 5s
char.cooldowns.reset("power_attack")          # clear specific
char.cooldowns.clear()                        # clear all
char.cooldowns.cleanup()                      # purge expired entries
 
char.cooldowns.all                            # → dict of all cooldowns
```

**Enhet = realtidssekunder** (`time.time()`), inte speltid. En saknad cooldown räknas som ready.
Rätt enhet för att strypa spelarens wall-clock-action-spam (t.ex. Stage-1:s on-use-improvement-gate).

### 6.3 ⚠️ No callbacks
 
> *"This module does not register or provide callback functionality for when a cooldown becomes ready again. Users of cooldowns are expected to query the state of any cooldowns they are interested in."*
 
So cooldowns are pull-based. If you need "when ready, do X", combine with `delay()` or `TickerHandler`. For typical use (gating commands), polling at command time is exactly the right pattern.
 
### 6.4 Pattern for commands
 
```python
class CmdPowerAttack(Command):
    key = "power attack"
    cooldown_seconds = 10
 
    def func(self):
        if not self.caller.cooldowns.ready("power_attack"):
            remaining = self.caller.cooldowns.time_left("power_attack", use_int=True)
            self.caller.msg(f"Not ready! ({remaining}s left)")
            return
        self.do_power_attack()
        self.caller.cooldowns.add("power_attack", self.cooldown_seconds)
```
 
---
 
## 7. Barter contrib

**Path:** `evennia/contrib/game_systems/barter/barter.py`
**Hardening layer:** `world/barter.py` (project)

**Status in PolishedWorld:** **In use.** The contrib ships as-is; every fix we
needed lives in a thin subclass layer, never a fork.

### 7.1 Concept

A two-party negotiation. Each side offers, both must `accept`, and goods swap
only when both have accepted the **current** offer set — any change to an offer
resets both accepts. PolishedWorld extends "offer" to include coin (§7.4).

### 7.2 Installation — ⚠️ ONLY THE ENTRY COMMAND IS GLOBAL

```python
# commands/default_cmdsets.py
from world.barter import CmdPWTrade      # NOT from the contrib directly

class CharacterCmdSet(default_cmds.CharacterCmdSet):
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CmdPWTrade())
```

That is the whole installation. Do **not** add `CmdOffer`, `CmdAccept`,
`CmdDecline`, `CmdEvaluate` or `CmdStatus` to `CharacterCmdSet`: they belong to
`CmdsetTrade`, which the contrib attaches to both parties when a trade starts
and deletes when it ends. Adding them globally would make `offer` typable
outside a trade and would turn the `status` key collision (§11.20) from
scoped-to-a-trade into permanent.

The import path is load-bearing. `world/barter.py` installs its fixes by
reassigning the contrib's own module globals, and **importing the module is what
runs those assignments** — routing the cmdset's import through it is what
guarantees they are in place at server start.

### 7.3 The module-global patch mechanism

The contrib resolves helper names from its own module namespace *at call time*:
`CmdTrade.func` does `part_a.scripts.add(TradeTimeout)`, and
`CmdsetTrade.at_cmdset_creation` does `self.add(CmdOffer())`. Reassigning those
names makes the unmodified contrib pick up our subclasses:

```python
barter_module.TradeTimeout = PWTradeTimeout
barter_module.TradeHandler = PWTradeHandler
barter_module.CmdOffer    = CmdPWOffer
barter_module.CmdAccept   = CmdPWAccept
barter_module.CmdDecline  = CmdPWDecline
barter_module.CmdEvaluate = CmdPWEvaluate
barter_module.CmdStatus   = CmdPWStatus
```

Seven swaps. A dropped assignment is a **silent** no-op — the contrib keeps
working, just with its own buggy class — so `tests/test_barter_currency.py`
asserts all seven and asserts that `CmdsetTrade()` is built from them.

### 7.4 Money in barter — ⚠️ NOT COIN OBJECTS

The contrib's own documentation suggests letting the goods on one side be coin
objects. **PolishedWorld does not do this**, and the reason is S4-2: a wallet is
a single `int` in Copper, and Stage 4 ships no coin objects at all. There is
nothing to put on the table.

Coin reaches a trade through a **handler-level bridge** instead
(Stage 4 Component E):

- `offer` takes currency segments alongside item names —
  `offer iron sword, 5 silver`. A comma-segment whose first character is an
  ASCII digit is coin; everything else is an item. The rule is total rather
  than heuristic because `SEARCH_MULTIMATCH_REGEX` is a *suffix* form
  (`copper-2`), so no valid way of naming an object begins with a digit.
- The amount is recorded as `part_a_currency` / `part_b_currency` on the trade
  handler. **No wallet is touched at offer time** — an offer is a promise.
- Settlement happens inside `finish()`, alongside the item moves (§7.5), gated
  by a one-shot flag (S4-R3) and by a re-validation that each side still holds
  what it promised (S4-R4). The check is **gross** per side; the transfer is
  **net**, because one `transfer_to` cannot half-settle the way two can.
- Settlement is a transfer, so it is **not ledgered** (S4-4).

### 7.5 ⚠️ Upstream bugs, all confirmed against 6.1.0

| Bug | Effect | Our fix |
|---|---|---|
| `TradeTimeout` reads `ndb.tradeevent`, never assigned (it is `ndb.tradehandler`) | a timed-out invite is never cleaned up; the inviter is stuck in a phantom trade | `PWTradeTimeout` |
| `CmdTrade`'s no-args branch reads the same missing attribute | `AttributeError` on bare `trade` while already trading | `CmdPWTrade` |
| `finish()` assigns `obj.location` directly | **no move hooks fire at all**, and ownership is never re-checked — offer an item, have it accepted, dispose of it, then complete the accept, and the contrib teleports it from wherever it now is | `PWTradeHandler.finish()` + `CmdPWAccept` re-validate |
| `CmdEvaluate` renders `offer.db.desc` | a dynamically-described item shows its stale prototype desc — a scribed book evaluates as "a blank book", hiding the recipes and condition a buyer needs | `CmdPWEvaluate` uses `get_display_desc()` |
| `CmdDecline`'s emptiness gate reads `list()`, which returns item lists only | a coin-only offer reads as "no offers have been made yet" while `status` shows the money | `CmdPWDecline` |

The direct-assignment bug is the one to remember: **any behaviour that must
happen when goods change hands in a trade has to live in `finish()` itself.** A
move hook will never fire.

### 7.6 ⚠️ Concurrency

`TradeHandler` ties two characters together and `join` fails if either is
already trading — desired, but it means "the other player won't trade with me"
needs UX consideration.

The trade cmdset is **added, not Replace**, so `drop`, `give`, `pay` and the
rest stay available mid-trade. That is deliberate (it would be worse to trap
players), and it is exactly why the staleness guards in §7.5 exist.

Settlement and the item moves happen in one unbroken synchronous block with no
yield point, which is what makes them atomic — Evennia's reactor is
single-threaded, so nothing can interleave (S4-R1). Introducing a `yield` or a
`utils.delay` anywhere inside `finish()` would reopen the window for the whole
economy.

---
 
## 8. Crafting contrib
 
**Path:** `evennia/contrib/game_systems/crafting/crafting.py`
 
**Status in PolishedWorld:** Planned — base for the 320+ recipe system.
 
### 8.1 Installation
 
In `settings.py`:
 
```python
CRAFT_RECIPE_MODULES = [
    "world.recipes.smithing",
    "world.recipes.cooking",
    "world.recipes.tailoring",
    # ...
]
```
 
In `commands/default_cmdsets.py`:
 
```python
from evennia.contrib.game_systems.crafting import CraftingCmdSet
 
class CharacterCmdSet(default_cmds.CharacterCmdSet):
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(CraftingCmdSet)
```
 
### 8.2 Defining a recipe
 
```python
from evennia.contrib.game_systems.crafting.crafting import CraftingRecipe
 
class IronSwordRecipe(CraftingRecipe):
    name = "iron sword"
    tool_tags = ["forge", "hammer"]              # not consumed; in inventory OR location
    consumable_tags = ["iron ingot", "wood"]     # consumed on success
    output_prototypes = [{
        "key": "iron sword",
        "typeclass": "typeclasses.weapons.Sword",
        "desc": "A serviceable iron sword.",
        "tags": [("weapon", "item_type")],
        "attrs": [("damage", "1d8"), ("weight", 1.5)],
    }]
```
 
Materials/tools are identified by **tags with categories `"crafting_material"` and `"crafting_tool"`** — name doesn't matter, the tag does. So multiple "iron ingot"-named objects from different sources all qualify if they carry the right tag.
 
### 8.3 Calling from code
 
```python
from evennia.contrib.game_systems.crafting import crafting
 
results = crafting.craft(crafter, "iron sword", iron_ingot, wood, hammer, forge)
# results is a list — empty on failure
```
 
### 8.4 In-game
 
```
> craft iron sword from iron ingot, wood with hammer
```
 
The `with` keyword separates tools from consumables in the command syntax.
 
### 8.5 Override hooks
 
`CraftingRecipe` has three lifecycle methods to override:
 
| Method | Purpose |
|---|---|
| `pre_craft(**kwargs)` | Validate inputs before crafting; raise `CraftingValidationError` to fail |
| `do_craft(**kwargs)` | Build the output objects (override for custom logic) |
| `post_craft(craft_result, **kwargs)` | Post-process; e.g., apply quality based on skill |
 
Mongoose-Legend skill check integration goes in `pre_craft` (gate on success) or `post_craft` (modify quality based on roll margin).
 
### 8.6 ⚠️ Recipe loading is module-level
 
Recipes are discovered at startup by walking `CRAFT_RECIPE_MODULES`. Adding a new recipe requires either a server reload or a manual `_load_recipes()` call. For a 320+ recipe system, organize recipes into focused submodules to keep load times reasonable and merge conflicts manageable.

### 8.7 ⚠️ MongooseCraftRecipe bootstrap findings (Component C, verified live)

- **`tool_tag=None` skips the penalty path.** `_tool_modifier()` opens with `if not self.tool_tag: return 0` — *before* the has-tool loop — so a recipe with `tool_tag=None` gets modifier 0, **not** `improvised_penalty`. This is what makes tool-free bootstrap recipes (stone knife, bone needle) craftable without a −20. A plain present tool is likewise baseline 0 (Component A flip). **Superior branch (Component G, Rev 11, verified):** a present tool crafted at the critical tier (`quality > 100`) grants `+tool_bonus` (10) — read live from the tool's OWN `db.quality` (which `do_craft` stamps on every output, tools included, *before* `_finalize_item`), banded via `quality_band`. **`db.quality` is `None`-guarded**: an uncrafted/admin-spawned tool (the metal `KNIFE` prototype has no craft recipe) carries `db.quality = None`, which short-circuits to baseline 0 before banding (a plain tool *is* baseline, and `quality_band(None)` would raise). A broken tool never reaches this branch — `_used_tool()` skips `is_broken` tools, so a broken *superior* tool returns `None` → penalty (broken = absent, by design).
- **No `min_skill` in the base.** `MongooseCraftRecipe` has no skill-floor mechanism at all — recipes are ungated by default. "Ungated bootstrap" means simply *not adding one*. A `min_skill` gate is Component F's job (it adds it to `pre_craft`).
- **A crafted/spawned `Tool` gets `condition=100` for free** unless a prototype overrides it. Spawning `stone_knife`/`bone_needle` (both `Tool(DurableObject, Object)`) with no `condition` key yields `db.condition=100` (no `at_object_creation`), confirming §10.1 end-to-end. **Prototype override confirmed (D.5):** with `"condition": 40`/`30` set as a top-level prototype key, a fresh spawn reads `db.condition == 40`/`30` — the prototype value wins over the AttributeProperty autocreate default, no `at_object_creation` stamping needed.
- **`CmdHarvest` iterates template parts dynamically.** It validates `get_part(creature_type, part_name)` and lists `get_template(...)` keys — no hardcoded meat/hide. Adding a part to `world/harvest_templates.py` is pure data; the command picks it up, and **existing corpses gain the part live after reload** (parts are read at harvest-time from the corpse's `creature_type`, not baked in at spawn).
- **`CmdRepair` is gated to `DurableObject`** (`isinstance(target, DurableObject)`, ~line 88), so tools *and* garments are repairable — the Component D wear→repair convergence (D.4). Materials are data-driven: `func` reads `target.db.repair_materials or REPAIR_MATERIALS` (garments fall through to the cloth/twine default; `stone_knife` → stick+fibre, `bone_needle` → bone). **Tool modifier generalised (Component G.2, Rev 11, verified):** `_tool_modifier(caller, target)` now reads `target.db.repair_tool_tag` (parallel to `repair_materials`) instead of always looking for a needle — unset (`None`) → `DEFAULT_REPAIR_TOOL = "needle"` (garments keep the old behaviour with no prototype change), `""` → no tool needed (flat 0; `STONE_KNIFE`/`BONE_NEEDLE` set `repair_tool_tag=""`, so a carried needle no longer wrongly shifts a stone-knife repair), `"<tag>"` → that `crafting_tool` tag-key. A *superior* repair tool grants `+SUPERIOR_TOOL_BONUS` (10, matching the craft side); the target is excluded from the tool search (`obj is not target`) and broken tools are skipped, consistent with `_used_tool()`. Verified the spawner stores a `""` top-level prototype value faithfully (no truthiness filter), so the sentinel is reliable.
- **Known limitation (backlog):** distinct crafted tools keep the tool-word in their `key` (`stone knife` / `bone needle`), so `get knife` / `get needle` can multimatch the metal versions. Crafting is unaffected (tool match is tag-based, consumables are named explicitly in `from …`). See §12.5 — fix identity, not the number.
 
### 8.8 ⚠️ MongooseCraftRecipe wear/repair findings (Component D, verified live)

- **🔴 `self.validated_tools` is ALWAYS empty for `MongooseCraftRecipe`.** Concrete recipes set only `consumable_tags` plus our own `tool_tag` (singular) — never the contrib's required `tool_tags`. During validation `_check_completeness([], …)` returns `[]`, and `exact_tools=False` skips the excess check, so `validated_tools == []` even when a matching tool was supplied via `using`. The tool lives **only in `self.inputs`**. Every tool-side operation — the check modifier, the D.1 wear sink, and Component G's superior-tool scaling — must read `self.inputs`, done once via the shared `_used_tool()` helper (scans `self.inputs` for `tool_tag`/`tool_tag_category`, and excludes `is_broken` tools). This contradicts the original §9 D.1 wording (`validated_tools`); reconciled in Decomposition Rev 4.
- **`craft()` lifecycle** (contrib `CraftingRecipeBase.craft`, ~line 320): `pre_craft` (runs validation → fills `validated_consumables`/`validated_tools`) → `do_craft` → `finally: post_craft` (always, even on abort). Both `self.inputs` and the `validated_*` lists are live in `do_craft` and `post_craft`. Pattern: mutate/capture side-effects (wear, improvement, break-flag) in `do_craft` after `rolled=True`; emit player messages in `post_craft` after the craft-result line, so "you make X / skill improves / tool breaks" reads in order. A broken tool is **not** deleted — it lingers at `condition 0`, counts as absent next craft (improvised penalty), and stays repairable (D.4).
- **`ContribClothing.get_display_desc` (contrib ~line 348) describes a *wearer*.** It lists `get_worn_clothes(self)`, so `look`ing at a *garment* (which wears nothing) already emits "X is wearing nothing." — a pre-existing contrib quirk, now visible above the D.3 condition line. `DurableObject.get_display_desc` uses `super()` to preserve that base and append the condition line; for a `Tool` the same `super()` resolves to `DefaultObject.get_display_desc` (plain desc). The mixin sits before the real base in every host's MRO, so its override wins while still deferring via `super()`. → backlog: bare-garment "is wearing nothing" suppression, tracked in `docs/BACKLOG.md`.
- **`condition_line()` colour bands (D.3):** `|g` > 66, `|y` 33–66, `|r` < 33, via class attrs `_COND_GOOD=66`/`_COND_WORN=33` on `DurableObject`. No prior code consumed `condition_line()`, so colouring it was safe. Player-facing wear now shows on `look` for both tools and garments (ordinary players lack `examine`).

### 8.9 ⚠️ MongooseCraftRecipe quality→capability findings (Component E, verified live)

- **🔴 A shared `_finalize_item` body must be a plain module-level function, not a subclass.** `LinenShirtRecipe` and `LeatherBootsRecipe` share one quality→condition mapping. Factoring it into a `GarmentRecipe(MongooseCraftRecipe)` base *defined in* `world/recipes.py` would make `_load_recipes()` register that base as a phantom recipe — `callables_from_module()` returns it and it passes the `inspect.isclass` + `issubclass(CraftingRecipeBase)` guard (unlike the *imported* `MongooseCraftRecipe`, whose `__module__` differs — see §8.6). The fix is a plain function, `_apply_garment_quality(obj)`, which fails the `isclass` guard and is never registered. Same trap, same escape as the base-import exclusion.
- **`_finalize_item` write-point.** It runs inside `do_craft` **after** `obj.db.quality`/`obj.db.crafted_by` are stamped and **before** `obj.location = crafter`. Writing `obj.db.condition = N` there overrides the `DurableObject` autocreate default (100) — the write lands on the very Attribute `apply_wear`/`is_broken`/`condition_line` read back, so a shoddy garment is born already worn-in. Capability values (waterskin `max_charges`/`durability`, garment start-`condition`) live in the **recipe layer** (`_WATERSKIN_STATS_BY_BAND`, `GARMENT_CONDITION_BY_BAND`); `world/crafting_quality.py` owns only classification (`quality_band`) and the superior alias (`band_alias`).
- **The craft quality scale is discrete; max is 111 (with a superior tool).** `_quality_for` yields only `{25 fumble, 50 failure, 100 success, 100+crit_score critical}`. With a plain tool no positive modifier survives (present = 0 baseline), so max `target` = skill-cap 100 → `crit_score = 10` → **quality 110**. **Component G (Rev 11)** reintroduces the positive modifier: a *superior* tool (`quality > 100`) grants `+tool_bonus` (10), and `skillcheck` never clamps `target` (see `world/skillcheck.py` docstring), so max `target` = 110 → `crit_score = 11` → **max quality = 111**. (The Decomposition's earlier "112" assumed a +20 tool; the locked +10 lands the real ceiling at 111.) Hence `superior = quality > 100` *is* the critical tier — with one deliberate edge: a critical at modified skill 0–9 has `crit_score = 0` → quality exactly 100 → bands `serviceable`. That is capability-banding (the item's capability equals a success), not a bug.
- **Forcing a tier in tests: patch the bound name.** `do_craft` calls `skill_check` resolved from `crafting_base`'s module globals (bound by `from world.skillcheck import skill_check`). Monkeypatch **`world.crafting_base.skill_check`**, not `world.skillcheck.skill_check` — the latter cannot touch the already-bound reference. Restore by re-pointing to the real function (`cb.skill_check = skill_check`), not `importlib.reload(cb)` (reload redefines the class while the registered recipe keeps referencing the old one).

---

## 9. Clothing contrib
 
**Path:** `evennia/contrib/game_systems/clothing/clothing.py`
 
**Status in PolishedWorld:** Planned — 11-slot clothing system with material-determines-function approach.
 
### 9.1 Installation
 
```python
from evennia.contrib.game_systems.clothing import ClothedCharacter, ClothedCharacterCmdSet
 
class Character(ClothedCharacter):
    pass
 
class CharacterCmdSet(default_cmds.CharacterCmdSet):
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(ClothedCharacterCmdSet)
```
 
### 9.2 Default settings (override in `settings.py`)
 
```python
CLOTHING_TYPE_ORDER = [
    "hat", "jewelry", "top", "undershirt", "gloves",
    "fullbody", "bottom", "underpants", "socks", "shoes", "accessory",
]
CLOTHING_TYPE_LIMIT = {"hat": 1, "gloves": 1, "socks": 1, "shoes": 1}  # max per type
CLOTHING_OVERALL_LIMIT = 20
```
 
For PolishedWorld's planned 11 slots, override `CLOTHING_TYPE_ORDER` with the project-specific list. Limits per slot go in `CLOTHING_TYPE_LIMIT` (e.g., `{"head": 1, "torso": 1, ...}`).
 
### 9.3 Creating clothing items
 
```
@create a leather tunic : evennia.contrib.game_systems.clothing.ContribClothing
@set tunic/clothing_type = top
```
 
### 9.4 Style-of-wear
 
Adds free-form descriptive text:
 
```
wear scarf draped loosely around the neck
```
 
Renders as: *"...wearing a scarf draped loosely around the neck"* in descriptions. Useful for the customization layer without needing per-slot description code.
 
### 9.5 Coverage / layering
 
`CLOTHING_TYPE_AUTOCOVER` (defined further down in source) controls auto-coverage rules — e.g., putting on pants automatically covers underpants. ⚠️ Note from the source: *"clothing only gets auto-covered if it's already worn when you put something on that auto-covers it"*. Order of dressing matters in display.
 
### 9.6 Material-determines-function
 
The contrib doesn't natively know about materials. The PolishedWorld design plan adds a `material` Attribute on each clothing item, which downstream systems (cold protection, water protection, abrasion) read for environmental buff modification. This is layered logic on top of the contrib, not a contrib feature.
 
---
 
## 10. AttributeProperty pattern
 
**Path:** `evennia/typeclasses/attributes.py` (line 165+)
 
Modern Evennia pattern that replaces the old `self.db.foo` access for typeclass attributes. Used heavily in `ExtendedRoom` and recommended for all new typeclasses.
 
```python
from evennia.typeclasses.attributes import AttributeProperty
 
class Character(DefaultCharacter):
    desc = AttributeProperty("", autocreate=False)
    custom_field = AttributeProperty(default=None, category="game_data")
    inventory_slots = AttributeProperty(default=lambda: {})  # use callable for mutables!
```
 
Constructor signature:
 
```python
AttributeProperty(default=None, category=None, strattr=False, lockstring="", autocreate=True)
```
 
Key parameters:
 
- `default` — value if attribute is unset. Use a **callable** for mutable defaults (`lambda: []`, `dict`, `list`) to avoid the standard Python mutable-default trap
- `autocreate=False` — don't write to DB until first explicit set; the default is read-only until then. Recommended for descriptions and other "may stay empty" fields
- `category` — optional Attribute category (use to namespace groups)
Access pattern is plain attribute syntax — no `.db.` prefix:
 
```python
char.desc                     # read
char.desc = "A new desc."     # write — auto-persists
```
 
Compared to `self.db.desc`: identical persistence, cleaner syntax, IDE-friendly (typecheckers can see it), and supports defaults declaratively.

### 10.1 AttributeProperty on a *mixin* (shared durability foundation)

An `AttributeProperty` can live on a plain, non-typeclass mixin and still autocreate on the host at object-creation. `evennia/typeclasses/models.py::init_evennia_properties()` walks the **entire `type(self).__mro__`** and collects every `AttributeProperty` in `vars(base)` for *each* base — including a bare `class Mixin:` that never touched the typeclass metaclass — then `getattr`s each once so `autocreate=True` fires. The descriptor becomes db-backed only through a real host (one whose instances have an `.attributes` handler); a bare `Mixin()` has none, so test the mixin through a host, never a bare instance (§11.17).

This is the mechanism behind `typeclasses/durable.py::DurableObject` (`condition`, `apply_wear`, `is_broken`, `condition_line`), inherited by `ClothingWithBuffs(DurableObject, ContribClothing)` and, later, `Tool(DurableObject, Object)`. MRO order `(Mixin, ContribBase)` puts the mixin **first**, so its descriptor takes precedence while the base's methods (clothing's `wear`/`remove`) resolve unchanged. A default identical to a previously-local `AttributeProperty` (here `condition=100`) means **no migration** of already-spawned objects. Django/Evennia allow a non-model mixin ahead of a model base; the most-derived metaclass (`TypeclassBase`) is selected automatically.

**Corollary (Component C confirmed; D.5 verified):** `Tool(DurableObject, Object)` shipped exactly this way — spawning `stone_knife`/`bone_needle` with no `condition` key yields `db.condition=100`, no `at_object_creation` on `Tool` (it stays a thin, empty typeclass; the wear *trigger* lives in the recipe, Component D). **Prototype override now verified (D.5):** setting `"condition": 40`/`30` as a top-level prototype key makes a fresh spawn read `db.condition == 40`/`30` — the prototype value wins over the AttributeProperty autocreate default, so lowering a bootstrap tool's start condition is pure prototype data (no `at_object_creation` stamping required).
 
---
 
## 11. Useful patterns and gotchas
 
### 11.1 `lazy_property` for handlers
 
All handler installations use `@lazy_property` from `evennia.utils.utils`:
 
```python
from evennia.utils.utils import lazy_property
 
@lazy_property
def traits(self):
    return TraitHandler(self)
```
 
This caches the handler instance per object, instantiating only on first access. **Don't** use `@property` here — it would re-instantiate every access, breaking handler state caching.
 
### 11.2 Server reload vs restart
 
| Action | Effect on tickers/scripts |
|---|---|
| `@reload` | In-memory state preserved; persistent tickers continue |
| `@reset` (server only) | Server process restarts; non-persistent tickers gone |
| `@shutdown` | Full stop |
 
When testing tickers and scripts, use `@reload` to verify state survives — but verify `@reset` for full server-restart behavior before relying on persistence.
 
### 11.3 `at_init` vs `at_object_creation`
 
| Hook | When called |
|---|---|
| `at_object_creation` | Once, when object first created |
| `at_init` | Every time object loads into memory (creation + every reload) |
 
Use `at_object_creation` for one-time setup (initial trait values). Use `at_init` for things that need re-establishing on reload (like `ExtendedRoom`'s broadcast task). Don't put DB-modifying code in `at_init` — it runs on every reload.
 
### 11.4 Picklable callback args
 
Both `TickerHandler` and `BuffHandler` store callback args via Python pickling. Anything passed as `*args` or `**kwargs` to these handlers must be picklable. Typeclassed objects (Characters, Rooms, etc.) are fine — they serialize as DB references. Lambdas, open file handles, and database cursors are not.
 
### 11.5 Querying puppeted characters
 
The pattern from section 5.4 — `DefaultCharacter.objects.filter(db_account__isnull=False)` — gets characters that have an Account set. To find currently *puppeted* (i.e., a player is connected to and playing as) characters, check `.has_account` on the result. Just having an account doesn't mean the player is online.
 
For online sessions specifically:
 
```python
from evennia.server.sessionhandler import SESSIONS
for session in SESSIONS.get_sessions():
    char = session.puppet
    if char:
        # char is currently being puppeted
```
 
This is more correct for "every active player" queries on a global ticker.
 
### 11.6 `object_search` is exact-first, then fuzzy — and what it means for `craft`

`DefaultObject.search(name)` (and the manager's `object_search`) runs an **exact**
key/alias pass first, and only falls back to **partial/fuzzy** word-start matching if the
exact pass returns zero hits (`evennia/objects/manager.py` — "always run first check
exact - we don't want partial matches").

Consequences, both seen live:

- **An exact alias beats a partial key.** Searching `"leather"` while carrying *piece of
  leather* (alias `leather`) **and** wearing *leather boots* returns only the material —
  the boots is just a partial match, and a non-empty exact pass excludes it.
- **The same query resolves differently as inventory changes.** Once the leather is
  consumed, `search("leather")` finds no exact hit, so the fuzzy fallback now returns
  *leather boots*. A post-consume "is it gone?" check via the material's name can therefore
  return the boots instead of `[]`. Check by **tag** or **dbref** if you need certainty.

**Crafting impact (`CmdCraft`):** the command does one `caller.search(token)` **per
ingredient token**. Two objects sharing a key/alias multimatch → the search aborts and the
craft fails. Supply identical ingredients with Evennia's numbered disambiguation, which is
`name-number` (regex `(?P<name>.*?)-(?P<number>[0-9]+)`, default separator `-`):

    craft leather from hide-1, hide-2 using knife
    craft leather boots from leather-1, leather-2 using needle

dbrefs (`craft X from #140, #141`) are the bulletproof alternative — exact and unambiguous.

### 11.7 TICKER_HANDLER vs GLOBAL_SCRIPTS — which for a global periodic system
Both the survival ticker (`world/survival_ticker.py`) and the garment-wear ticker
(`world/garment_wear.py`) are **module-level callables registered with
`TICKER_HANDLER.add(...)` in `server/conf/at_server_startstop.py`**, NOT
`settings.GLOBAL_SCRIPTS` scripts. Use TICKER_HANDLER when the job is "run this
function every N seconds over the online population" — the callback must be a
picklable module-level function (no closures/lambdas) for `persistent=True`.
Reserve GLOBAL_SCRIPTS for systems needing their own persistent Attribute state and
lifecycle hooks (e.g. `WeatherScript` holding `db.current_weather`). Re-adding with
the same `idstring` is idempotent, so calling `.add` on every `at_server_start` is safe.

### 11.8 Driving commands from `@py`, and cooldown cleanup in tests
`caller.execute_cmd("repair linen shirt")` runs a full command (parse + func + its
own messaging) inside a `@py` one-liner — the way to integration-test a Command
without a live client. Reset a cooldown between runs with
`caller.cooldowns.reset("<key>")`; without it the cooldown gate fires first and masks
the branch you meant to test. Keep RNG out of unit tests by extracting the pure
decision (e.g. `CmdRepair._resolved_condition(current, outcome)`) so tier maths can be
asserted deterministically, separate from the random `skill_check`.

### 11.9 Command structure: validate-then-commit ordering
Order a command so every *free bailout* (missing/ambiguous target, wrong type,
nothing to do, missing materials, on cooldown) returns BEFORE anything is consumed.
Only once the attempt is irrevocably resolved do you consume materials and set the
cooldown — on success, failure AND fumble alike. The single-threaded reactor makes
the collect→roll→consume sequence atomic against concurrent runs, so no locking is
needed. (See `CmdRepair`, `CmdHarvest`.)

### 11.10 Repair mutates in place → command, not recipe
`MongooseCraftRecipe`/`CraftingRecipe` are strictly input→**new** output (`do_craft`
spawns from `output_prototypes`). A task that must target an existing object and
mutate one of its Attributes (garment repair raising `db.condition`) has no clean
recipe path — write a dedicated Command instead. Bonus: resolving one named object
also sidesteps the `craft` ingredient multimatch problem (§11.6).

### 11.11 Condition-scaled sums: round the total, not the parts
When several worn items each contribute a small fractional value, scale each
fractionally, sum, and round **once** at the end. Rounding per item first makes two
worn-1 garments at 49% both round to 0 → total 0, when the true stacked value is
round(0.98)=1. `world/thermal.py::worn_warmth` follows this. Distinct from
"sum-then-scale", which is wrong because the scale (condition) is per item.
 
### 11.12 Typeclass compile failure → silent `DefaultObject` fallback

A `SyntaxError`/`ImportError` in a typeclass module means Evennia can't import the class, and
objects using it fall back to base `DefaultObject`. The symptom surfaces *far from the cause*:
a broken `characters.py` shows up as `'DefaultObject' object has no attribute 'buffs'` fired by
the survival ticker every tick — not as an error in `characters.py`. First diagnostic for any
`'DefaultObject' object has no attribute '<your-custom-attr>'`: `python -m py_compile <file>`.
A clean compile rules the module out. Don't debug the code that happens to crash; find the
module that won't load.

### 11.13 `return_appearance` lists contents via the `{things}` slot

`DefaultObject.return_appearance` fills its `appearance_template` with
`things=self.get_display_things(looker)`, so looking at *any* object already lists its contents.
Consequence for containers: `look <container>` shows what's inside for free — you do **not** need
`CmdContainerLook` to display contents. (PlayerCorpse relies on this for loot display, skipping
`CmdContainerLook` to avoid the collision in §11.14.)

### 11.14 Containers contrib — locks, backward-compat, and the `look` collision

`evennia.contrib.game_systems.containers`:

- `CmdContainerGet(CmdGet)` (key `get`) is backward-compatible: no `from` clause → `location =
  caller.location`, i.e. plain `get <obj>` behaves exactly like stock. With `from`, it searches
  the container and checks `location.access(caller, "get_from")`.
- Two **orthogonal** locks: `get` governs picking up the object itself; `get_from` governs taking
  items *out* of it. `get:false()` + `get_from:true()` = can't be pocketed, but freely looted.
- Import commands from the submodule (`...containers.containers import CmdContainerGet`) — they
  are **not** re-exported from the package `__init__.py` (same pattern as `CraftingCmdSet`).
- ⚠️ `ContainerCmdSet` bundles `CmdContainerLook`, which replaces `look` and **collides** with
  extended_room's `CmdExtendedRoomLook` (seasonal descriptions). With extended_room in use, add
  the individual commands you need (e.g. just `CmdContainerGet`), not the bundle. Both classes
  inherit `key = "look"` from `default_cmds.CmdLook`, so they compare equal (§11.20).
- ⚠️ The *mechanism* here is **not** §11.20's merge operator. `self.add(SomeCmdSet)` inside
  `at_cmdset_creation` is not a merge at all: `CmdSet.add()` copies the other set's *commands*
  into ours, removing any equal command already present before appending ("later added commands
  will simply replace existing ones" — its own docstring). Verified live 2026-07-26 against
  `evennia/commands/cmdset.py::CmdSet.add`. In `commands/default_cmdsets.py`
  `ExtendedRoomCmdSet` is added early and `ContainerCmdSet` would be added last, so the seasonal
  `look` would lose. Same *direction* as §11.20 (later wins), different code path — and a
  different lifetime: this deletion is permanent for the life of the cmdset, whereas a merge-time
  loss lasts only while the winning set is present.

### 11.15 `search_object()` resolves `#dbref` strings

`evennia.utils.search.search_object(searchdata)` accepts a `#dbref` string or int, not just a key
(docstring: "Object key or dbref to search for."). Handy for resolving a configurable dbref from
settings into an object:

```python
matches = search.search_object(getattr(settings, "DEFAULT_RESPAWN_DBREF", None))
dest = matches[0] if matches else (self.home or self.location)
```

### 11.16 `evennia shell` interactive-console paste-fälla

`evennia shell` är en vanlig Python `InteractiveConsole` (`code`/`codeop`). Att klistra in ett
flerradigt compound statement — en `for`/`if` vars kropp spänner över flera rader, *särskilt* med
en implicit radbrytning inuti parenteser — följt av ett dedenterat top-level-statement utan tom rad
emellan, får den inkrementella kompilatorn att ackumulera allt till ETT block och kasta
`SyntaxError` (Python 3.14 fel-hintar till och med "Did you mean 'not'?"). Det är en paste-artefakt,
inte ett kodfel.

**Fix — två paste-säkra former:**
- En fysisk rad per statement: `for x in seq: a = f(x); print(a)` (hela kroppen på raden).
- Eller wrappa flerradig kod i `exec("""…""")` så konsolen ser en enda sträng, aldrig indraget.

Skild från §3.5:s `@py`-not (rad-isolerat namespace). Tumregel för stat-/loop-tester: en fysisk
rad per statement, eller `exec` en sträng.

### 11.17 `exec`/shell-defined throwaway typeclasses fall silently to `DefaultObject`

Evennia resolves a typeclass by **importable dotted path**, not by class identity. A class defined inside `exec("""...""")` or the `evennia shell` `InteractiveConsole` has `__module__` = `builtins`/`__console__` — no importable path — so `create_object(ThatClass, ...)` cannot re-import it and falls back **silently** to `settings.BASE_OBJECT_TYPECLASS` (`DefaultObject`) per §11.12. The object then lacks any `AttributeProperty` the throwaway declared, surfacing later as `AttributeError: 'DefaultObject' object has no attribute '<field>'`.

Fix: to functionally test a mixin/typeclass in the shell, put a real host in an **importable scratch module** (`typeclasses/_scratch.py`, delete after, never commit) and `create_object("typeclasses._scratch.HostClass", ...)` by path. (Also: the flat API exposes `create_object`, not a `create` module — `from evennia import create_object`, not `from evennia import create`.)

### 11.18 `ContribClothing.wear` stores `wearstyle` *as* `db.worn`

`wear(self, wearer, wearstyle, quiet=False)` does `self.db.worn = wearstyle` verbatim, and `get_worn_clothes` (hence `world/thermal.worn_warmth`) filters on truthy `db.worn`. So `wear(wearer, "")` sets `db.worn = ""` (falsy) and the garment reads as **un-worn** — contributes 0 warmth, absent from worn listings. For style-less wearing pass `True` (the contrib's documented sentinel: "just the name will be shown"); reserve a non-empty string for an actual wear-style suffix. Bites any code that calls `wear` programmatically (tests, scripts, NPC dressing).

### 11.19 `TagHandler` normalises keys and category-queries (known-recipe set, Component A)

*(Verified live against Evennia `main`, 2026-07-11 — `evennia/typeclasses/tags.py`.)* The Stage 3 known-recipe set stores recipe names as Tags on the `Character` under a category. Three non-obvious behaviours:

- **Keys are normalised on write AND read** — `add()` does `str(key).strip().lower()` (and `_getcache`/`has`/`get` lower-case identically). Leading/trailing space is stripped but **internal** space is kept, so `"linen shirt"` survives. Net: storage is case-insensitive and round-trips cleanly, but the *stored* form is always lower-case. Store the canonical recipe-registry name (`MongooseCraftRecipe.name`), never a `prototype_key`.
- **`add()` is idempotent at the DB level** — a matching key+category re-uses the existing Tag, never duplicates. A `learn_recipe` guard (`if knows_recipe(): return False`) is therefore only for the *return signal* ("already knew it"), not to prevent duplicate rows.
- **`get(category=X, return_list=True)` returns a list of key strings** — with `key=None` it takes the category branch (`_getcache`: `key = … if key else None`) and returns every tag key in that category as `to_str(tag.db_key)`, or `[]` when empty. `has(single_key, category=X)` returns a plain `bool` (a single match unwraps). Exactly what `known_recipes()`/`knows_recipe()` rely on.

Multiplayer: a `learn` is a read-then-write on the tag set, but Evennia's single-threaded reactor serialises commands, so concurrent learns can't race — worst case the second sees the tag present and returns `False`.

### 11.20 ⚠️ Duplicate command keys are *deleted*, not shadowed — and the LATER-merged set wins ties

*(Verified live against Evennia `main`, 2026-07-26 — `evennia/commands/cmdset.py`, `cmdhandler.py`, `cmdsethandler.py`, `commands/command.py`, `objects/objects.py`. **This section corrects Rev 14**, which had the tie-break backwards; see the meta-lesson at the end.)* Two cmdsets carrying the same command key do **not** produce a multimatch or a polite override. One command disappears — that much Rev 14 got right. *Which* one survives is the opposite of what it said.

- **Equality is by key+alias intersection.** `Command.__eq__` returns `self._matchset.intersection(cmd._matchset)` where `_matchset = {key} | set(aliases)`, and `__hash__` is `hash(self.key)`. Two commands that share *only an alias* compare equal. So collisions are wider than the key alone suggests.
- **Union merge drops the incoming duplicate.** `CmdSet._union` does `existing_commands = set(cmdset_a.commands)` then extends with `[cmd for cmd in cmdset_b if cmd not in existing_commands]` — anything already present is never added.
- **The tie goes to the right-hand operand.** `_union`'s own docstring names `cmdset_a` as "Cmdset given higher priority in the case of a tie", and `__add__(self, cmdset_a)` — i.e. `C = B + A` — takes the `self.priority <= cmdset_a.priority` branch on a tie and calls `_union(cmdset_a, self)`. So in `B + A`, **A wins**.
- **The runtime merge puts the *later* set on the right.** `cmdhandler.get_and_merge_cmdsets()` groups same-priority sets with `tempmergers[prio] = tempmergers[prio] + cmdset` — accumulator left, incoming right. And `DefaultObject.get_cmdsets()` returns `self.cmdset.current, list(self.cmdset.cmdset_stack)`, i.e. the **raw stack**, so every set on the object arrives as its own entry in stack order; `CmdSetHandler.add()` does `cmdset_stack.append(...)`. A cmdset added at runtime therefore merges last and **does** override a same-keyed command at equal priority — for its lifetime, handing the key back when deleted. The function's docstring says as much: "Object's cmdset is merged last (and will thus take precedence over same-named and same-prio commands on Account and Session)." (`.current` is used here only for the `no_objs`/`no_exits` flags, never for the command merge.)
- **Where Rev 14 went wrong.** It derived the rule from `cmdsethandler.update()`, which folds the stack the *other* way (`new_current = cmdset + new_current`, accumulator on the right) — true for that function, and irrelevant. `update()` disclaims itself: its result "will likely not match the true current cmdset as determined at run-time by `cmdhandler.get_and_merge_cmdsets()`". `.current` is bookkeeping; `cmdhandler` decides what runs.
- Both `default_cmds.CharacterCmdSet` and contrib cmdsets such as barter's `CmdsetTrade` are `priority = 0`, so this tie is the default case, not an edge case.

**Empirical confirmation (in game, 2026-07-26):** `commands/character_commands.py::CmdStatus` (key `status`, alias `vitals`) and barter's `CmdStatus` (key `status`, aliases `offers`/`deal`) coexist correctly. Outside a trade, `status` prints vitals; inside a trade it prints the offer table; when the trade ends, vitals come back. Both sets are `priority = 0`, so this is the tie case, and the runtime-added set wins it non-destructively. Under the Rev 14 rule this pairing should have been broken since Stage 2 — it never was.

**Consequence for Stage 3 H.1:** the mechanical premise was wrong. A global `accept` in `CharacterCmdSet` would **not** have erased barter's `CmdAccept` (nor our `CmdPWAccept` stale-offer backstop, §7.5) — it would have *lost* to it inside a trade and worked outside one. An inversion, not a silent erasure. The decision to extend `learn` instead stands, but on UX grounds only: `learn` is the student's verb for every knowledge carrier, so a second verb would have split one concept across two keys. Corrected in `PolishedWorld_Recipe_Knowledge_Decomposition.md` Rev 11. Note barter itself still avoids owning a global `accept` for its *invite* handshake, using `trade <person> accept`: same verb, accept as an argument.

**Rule for this project:** every new command gets a key and aliases verified unique against the default `CharacterCmdSet` *and* every contrib cmdset we merge, including ones added at runtime — a collision still *deletes* a command, it just deletes the other one now. Deliberate temporary override by a runtime cmdset is a supported technique (that is exactly how barter's trade verbs work), but it is not a substitute for owning a key: when a second command genuinely needs to answer an existing verb *permanently*, extend the command that already owns it (H.1 extended `learn` to a third carrier). Raising `priority` to "win" only moves the casualty.

**Related:** §11.14 (`ContainerCmdSet`'s `CmdContainerLook` vs `extended_room`'s `look`) is a **different mechanism** with the same direction — `CmdSet.add()`, not `_union`. Read both before assuming either explains the other.

**Meta-lesson (why this section needed correcting):** Rev 14 was written after source verification against Evennia's actual code, and was still wrong — right code, wrong function. Source verification is necessary but not sufficient. For any claim about *runtime* behaviour, prove it in a running game before writing it down as a lesson; here a two-minute `status`-inside-a-trade check would have caught it.

---

### 11.21 Enumerating objects: `typeclass_search` is `all_family`, and often the wrong question

*(Verified against Evennia `main` 2026-07-27 — `evennia/typeclasses/managers.py`.)*

`ObjectDB.objects.typeclass_search(cls, include_children=True)` does exactly one
thing in that branch: `return typeclass.objects.all_family()`. It is not a
different or better query than the `Character.objects.all_family()` already used
in `world/character_migrations.py` — just one more layer. Pick either; do not
imagine the longer one is doing more.

The more useful point is **which question you are asking.** Typeclass
enumeration answers *"everything that IS an X"*. When what you actually need is
*"everything that HAS an X"*, use the Attribute query instead:

```python
from evennia.objects.models import ObjectDB
ObjectDB.objects.get_by_attribute(key="wallet")   # one indexed filter on db_key
```

**Why it matters (Stage 4 A.3).** The currency audit sums every wallet in the
world. Written as "all Characters" it would have been complete only while
Characters were the only wallet holders — and the Treasury already is not one.
The first future wallet-holder (guild bank, shop, Stage 5's purse-keeping
corpse) would have made the audit under-count and report an invariant failure
that was really a bug in the audit. A false alarm in the one tool that exists to
be trusted is worse than no tool. The Attribute query is complete by
construction, needs no maintenance, and is the cheaper query besides.

**Rule:** when a query exists to be exhaustive over a *capability*, enumerate the
capability, not the class that currently happens to have it.

---

### 11.22 A `GLOBAL_SCRIPTS` entry with no `interval` is persistent storage, not a ticker

*(Verified live 2026-07-27 — `evennia/utils/containers.py::GlobalScriptContainer`.)*

`interval` is optional. A global Script registered in `settings.GLOBAL_SCRIPTS`
without one never fires `at_repeat` and simply exists — which makes it the right
home for world-level state that belongs to no object. The container
auto-(re)creates anything declared in settings on access, so the Script comes
back by itself after deletion **or after a full development-database reset**,
with no migration path to write and nothing to remember to switch on.

```python
# settings.py
"economy_ledger": {
    "typeclass": "typeclasses.scripts.EconomyLedgerScript",
    "persistent": True,
    "desc": "Mint/burn ledger for the currency economy",
},
```

Server log confirms it: `GLOBAL_SCRIPTS: (Re)creating economy_ledger (...)`.

⚠️ **`at_script_creation` must still be idempotent.** Seed state behind a
`if self.db.x is None:` guard, exactly like every backfill in this project — an
unguarded seed would zero a live ledger the first time the Script is recreated
for any reason.

**Design note:** an append-only list in an Attribute deserialises wholesale on
every access, so keep any running totals as their own integer Attributes. The
frequent reader then never touches the list, and only the rare writer pays.

---

### 11.23 An Attribute row does not exist until first write — so design the backfill away

*(Verified live 2026-07-27 — asserted directly in `tests/test_currency.py`.)*

`obj.attributes.get("wallet")` on an object that never wrote one returns `None`,
and **no Attribute row exists in the database**. Combined with a handler that
reads through a default:

```python
return self.obj.attributes.get(self._db_attribute, default=0) or 0
```

…an object that has never touched the value behaves identically to one holding
the default, without anything ever having been written for it.

**The consequence is structural, not cosmetic.** §3.5 and
`world/character_migrations.py` document the recurring trap: state added in
`at_object_creation` must be backfilled onto existing objects, and the backfill
must be guarded because `TraitHandler.add()` defaults to `force=True` and will
happily wipe live progress. Stage 4's wallet has **no** `at_object_creation`
entry and **no** `AttributeProperty` declaration, so there is no backfill to
guard and nothing that could clobber a live balance. The trap is not avoided by
care; it is absent.

A second benefit falls out: with no `AttributeProperty`, there is no
`char.wallet = 500` shortcut for code outside the owning module to reach for.
"Only this module writes this state" stops being a review convention and becomes
a property of the code. Both effects are worth the trade wherever a value has a
meaningful default and a single owner.

**Trade-off, stated honestly:** you lose the self-documenting declaration on the
typeclass and the tab-completion that comes with it. For a value with one owner
and one writer that is a good trade; for ordinary descriptive state it is not.

---

### 11.24 `EvenniaTest`'s `char2` cannot be puppeted — and it fails silently

*(Verified live 2026-07-30 against Evennia 6.1.0, `evennia/utils/test_resources.py`
and `evennia/accounts/accounts.py::puppet_object`. Cost one debugging cycle in
Stage 4 Component B.)*

`EvenniaTestMixin.setup_session()` logs in **only `self.account`**, on sessid 1,
and `create_accounts()` grants `Developer` to **`self.account` only**. `char2`
does get `account2` and an `_last_puppet` pointer, so the auto-puppet on login
*attempts* to run — and then fails, because a Character's puppet lock is
`puppet:pperm(Developer)`.

The failure mode is the problem. `puppet_object()` does not raise on a lock
refusal; it calls `self.msg("You don't have permission to puppet …")` and
`return`s. In a test there is no session to read that message, so nothing
surfaces. `char2` is simply still a body afterwards.

**Why this bites specifically.** `Object.has_account` is `self.sessions.count()`
— sessions puppeting *that object*, not sessions logged into its account. So any
command that requires a played target (`pay`, `teach`, any consent handshake)
refuses `char2`, and the test that was meant to exercise the happy path passes
while asserting the refusal branch. Under our statue-logout the symptom is
legible if you read it: the expected-vs-returned diff says
`stone statue of Char2 …`, because `get_display_name` is telling the truth about
an unpuppeted character.

**The fix, and the assertion that keeps it honest:**

```python
self.account2.permissions.add("Developer")   # mirrors create_accounts() for account1
# ... portal_connect + login on sessid 2 ...
if not self.char2.sessions.count():          # do not depend on AUTO_PUPPET_ON_LOGIN
    self.account2.puppet_object(session2, self.char2)
self.assertTrue(self.char2.has_account, "...")
```

The final assert is the load-bearing line. A fixture mixin whose entire job is
establishing a precondition must fail loudly when it stops establishing it,
because the alternative is a suite that stays green while testing the wrong
branch. Tear the session down in `tearDown` — `SESSION_HANDLER` is global, and a
leaked session makes `char2`'s connected-ness depend on test execution order
(the same bug class as ledger and cooldown bleed).

Reference implementation: `tests/test_currency_commands.py::SecondSessionMixin`.

---

### 11.25 `Object.search()`'s candidate set — room scoping for free, with two edges

*(Verified live 2026-07-30 against Evennia `main`,
`evennia/objects/objects.py::get_search_candidates`.)*

With no `location`/`global_search` override, the local candidate set is exactly:

```python
candidates = self.contents
if location:
    candidates = candidates + [location] + location.contents
```

Three consequences worth knowing before writing a targeted command:

1. **Same-room scoping is free — don't build it.** A target in another room is
   not a candidate, and `search()` emits its own miss and multimatch messages, so
   a falsy return is already fully reported to the player. Just `return`.
2. **A target inside a container in the room is also not a candidate**, because
   `container.contents` is not included. That resolves as a clean miss rather
   than a surprise hit — the right answer for vehicles and enterable containers,
   ahead of having either.
3. **The room object itself is a candidate.** So `pay 1 copper to <room name>`
   reaches your command body. Any guard that assumes a Character target
   (`hasattr(target, "currency")`, `target.has_account`) is load-bearing, not
   decorative — without it the call falls through to a handler that raises.

**The edge that is not tight:** the dbref branch runs *before* the permission
check —

```python
if kwargs.get("global_search") or dbref(searchdata):
    return None            # None == search everything
```

— while `use_dbref` is resolved separately from a `perm(Builder)` lockstring. A
plain player typing `#42` gets a global candidate set but cannot match it as a
dbref; a Builder+ can, and so can reach across the world. For staff-reachable
holes this is usually acceptable (they have `@py` already), but state it in a
comment rather than assuming the scoping is airtight.

---

### 11.26 ⚠️ `.call()` does not run command locks — permission tests written with it pass vacuously

*(Verified live 2026-08-02 against `evennia/utils/test_resources.py`; asserted in `tests/test_economy_command.py`.)*

`EvenniaCommandTestMixin.call()` assigns the command's properties and then runs:

```python
if not cmdobj.at_pre_cmd():
    ...
    ret = cmdobj.func()
```

There is **no `access()` call anywhere in the sequence.** Lock checking lives in
the cmdhandler, which `.call()` bypasses entirely by constructing and invoking
the command directly.

The consequence is a test that fails in the most expensive way available — by
passing:

```python
# WRONG. This does not test the lock. It never touched the lock.
def test_plain_character_is_refused(self):
    self.char2.permissions.remove("Developer")
    output = self.call(CmdEconomy(), "", caller=self.char2)
    self.assertIn("refuse", output)      # <- asserts against the command
                                         #    having RUN, not been refused
```

`.call()` happily executes the command as `char2`, the command body does not
consult permissions (that is the lock's job), and the assertion then measures
whatever the command printed. Written the other way round — `assertNotIn`, or
asserting an empty return — it passes for the same wrong reason.

The correct form checks the lock the way the cmdhandler does:

```python
def test_plain_character_is_refused(self):
    self.char2.permissions.remove("Developer")
    self.assertFalse(CmdEconomy().access(self.char2, "cmd"))

def test_developer_is_allowed(self):
    self.assertTrue(CmdEconomy().access(self.char1, "cmd"))
```

`Command.access(srcobj, access_type="cmd")` delegates to
`self.lockhandler.check(...)` — the same call the cmdhandler makes — so this
tests the real thing and needs no fixture beyond a caller.

**Two corollaries worth holding onto.**

First, this is the same shape of trap as §11.24 (`char2` cannot be puppeted): a
test-harness convenience quietly diverges from the runtime, and the divergence
surfaces as green. Whenever a test needs to assert that something is *refused*,
check whether the refusal is enforced by a layer the harness skips.

Second, the inverse is a *feature* and is what makes `.call()` usable at all: a
Developer-locked command can be exercised from a test without granting
permissions to the fixture. Just never mistake that convenience for coverage of
the lock.

⚠️ In-game, remember that a **superuser bypasses every lock**, command locks and
object locks alike. Verifying `cmd:perm(Developer)` or `get:false()` while logged
in as the superuser proves nothing; it needs a second, unprivileged character
(Testing Reference §10 — two *sessions*).

---

### 11.27 Cancelling a `utils.delay` you have already scheduled — the identity-marker pattern

*(Verified live 2026-08-02 against Evennia 6.1.0; shipped in
`commands/work_commands.py`, asserted in `tests/test_work_command.py`.)*

`utils.delay(seconds, callback, *args)` returns a task, but in practice a timed
*player action* is not cancelled by holding the task object — the cancellation
usually has to happen somewhere that never saw it (`at_pre_move`, a death hook,
a second invocation of the same command). The workable pattern is to let the
callback fire on schedule and **decide for itself whether it is still wanted**.

The naive version stores a flag:

```python
caller.ndb.working = "sweep"          # start
...
if caller.ndb.working != "sweep":     # in the callback
    return
```

⚠️ **This is broken, and it is broken in a way that pays out twice.** Start a
task, abandon it, start the *same* task again: the first callback is still in
flight, wakes up, finds a flag whose value it recognises, and completes against
the second attempt. A string cannot distinguish two attempts that share a name.

The fix is an identity token that cannot collide, compared with `is`:

```python
marker = object()                      # fresh per attempt
caller.ndb.working = marker
delay(duration, _finish, caller, task_key, marker)

def _finish(caller, task_key, marker):
    if not caller.pk or caller.ndb.working is not marker:
        return                         # cancelled, superseded, or reloaded away
    caller.ndb.working = None
    ...
```

Cancelling from anywhere is then a single assignment — `self.ndb.working = None`
— with no reference to the task and no import of the command module. The
`rest`/`at_pre_move` interrupt in `typeclasses/characters.py` uses exactly this.

**Four properties of this arrangement worth knowing before reusing it:**

1. **`ndb` holds arbitrary Python objects by reference.** NAttributes are an
   in-memory dict on the typeclass instance with no serialisation, so `object()`
   round-trips by identity. This is precisely why it must not be combined with
   `delay(..., persistent=True)`: a persistent task is serialised to the
   database, and it would wake in a process where the marker no longer exists.
   Keep `ndb` and the delay non-persistent **together**, so a `@reload` kills
   both and the action is cleanly abandoned rather than half-alive.
2. **The callback must re-check the world, not just the marker.** A move hook
   catches walking out; it does not catch teleport, death, or the target object
   being moved. The marker proves the *attempt* is current; it proves nothing
   about whether the preconditions still hold.
3. **`has_account` is the guard for "still actually playing".** Under a
   statue-logout scheme the body stays in the room, so a callback firing after
   logout finds a perfectly valid character. `_rest_tick` in `characters.py` has
   guarded itself this way since Stage 2.
4. **Make the callback a module-level function, not a closure or a bound
   method.** It is then directly callable from a test, which is the difference
   between testing the action and testing the reactor. Read the marker off the
   object under test rather than fabricating one — a fabricated marker passes
   even with the identity check deleted.

⚠️ **The race rule interacts with this.** If the delayed action moves currency
(or anything else with a check-then-commit shape), the *entire* check-and-commit
sequence must sit **inside** the callback. Checking a precondition before the
delay and committing after it reopens exactly the window that a single
synchronous block closes — and the window is `duration` seconds wide. See the
Currency decomposition's S4-R1.

---

### 11.28 ⚠️ Attribute containers are `_SaverDict`/`_SaverList`, and `has()` returns a list

Two type surprises in the same API, both verified live against Evennia 6.1.0.

**A stored dict does not come back as a `dict`.** Evennia deserialises Attribute
containers into `_SaverDict` / `_SaverList` — proxies that write through to the
database on mutation. They implement the full mapping/sequence protocol, so
`.get()`, `in`, iteration and `dict(x)` all behave, but:

```python
char.attributes.add("skill_xp", {"craft": 170})
got = char.attributes.get("skill_xp")

type(got).__name__                      # -> '_SaverDict'
isinstance(got, dict)                   # -> False        ⚠️
isinstance(got, collections.abc.Mapping)  # -> True       ✅
got.get("craft")                        # -> 170
dict(got)                               # -> {'craft': 170}   (detached copy)
```

`isinstance(x, dict)` is the natural thing to write and it silently takes the
**wrong branch**. The failure is quiet by nature: a handler that guards its reads
with `isinstance(..., dict)` behaves as though the store were permanently empty,
re-deriving or re-initialising after every write and losing everything the
previous write put there. Nothing raises.

**Rule:** test containers with `collections.abc.Mapping` / `Sequence`, never with
`dict` / `list`. Return `dict(x)` from any accessor whose caller should get
something detached from the database.

This has now bitten the project twice — the survival layer and Stage 4.5's XP
store — and was not in this document until Rev 21.

**`AttributeHandler.has()` returns a list, not a bool.**

```python
char.attributes.has("skill_xp")   # -> []   when absent, not False
```

Falsy, so `if char.attributes.has(...)` reads correctly and `assertFalse` passes.
But `assertIs(..., False)`, `is True`, and `== False` all fail on a value that is
semantically correct. In tests use `assertTrue`/`assertFalse`; in `@py` wrap it as
`bool(self.attributes.has("skill_xp"))` so the output is legible.

**Related:** §11.23 — an Attribute row does not exist until first write, which is
what lets a handler reading with `default=` design the backfill away rather than
merely guard it. §11.28 is the trap you hit *after* taking §11.23's advice: the
row now exists, and the type it comes back as is not the type you put in.

---

## 12. Search multimatch & disambiguation UX

*(Verified against live Evennia `main`, 2026-07-01. §11.6 covers the search-*resolution* mechanic — exact-first, then fuzzy — and the crafting-ingredient angle; this section covers the multimatch *UX*: why `ball-1`/`ball-2` appears and the three ways to tune it.)*

The default multimatch prompt is **intentional and fully tunable**. It's a *symptom* of two objects sharing an identical key, so the best fix is usually to make multimatch rare rather than to prettify the number (see §12.5).

### 12.1 What produces `ball-1` / `ball-2`

When a search returns >1 match, Evennia routes the result through the pluggable hook named by `SEARCH_AT_RESULT` (default `evennia.utils.utils.at_search_result`). For a multimatch it prints a `More than one match...` header, then one line per match rendered by `SEARCH_MULTIMATCH_TEMPLATE`. The *input* syntax the player types to disambiguate is defined by `SEARCH_MULTIMATCH_REGEX` (§11.6 shows this regex from the crafting side — here is the full trio):

```python
# evennia/settings_default.py
SEARCH_MULTIMATCH_REGEX = r"^(?P<name>.*?)-(?P<number>[0-9]+)(?P<args>(?:\s.*)?)$"
SEARCH_MULTIMATCH_TEMPLATE = " {name}-{number}{aliases}{info}\n"
SEARCH_AT_RESULT = "evennia.utils.utils.at_search_result"
```

Internally `at_search_result` groups matches by `get_display_name(caller)` (case-insensitively), strips pluralization aliases, and fills the template per match. Fields: `{number}` (ordinal from 1), `{name}` (display key), `{aliases}` (`[a;b]`), `{info}` (e.g. `#dbref`, staff only).

### 12.2 Lever 1 — reskin via settings (cheapest, global)

Change `SEARCH_MULTIMATCH_TEMPLATE` **and** `SEARCH_MULTIMATCH_REGEX` together. ⚠️ **They must stay in sync** — Evennia warns about this explicitly: the regex must keep the `(?P<name>...)` and `(?P<number>...)` capture groups (and may keep the optional `(?P<args>...)`), and the template must render a form the regex can parse back. This only *reskins* the number; the player still types a numeric disambiguator, and it's global (affects every search in the game).

```python
# settings.py — ILLUSTRATIVE ONLY: numbered-list style ("  1. a steel dagger").
# Verify the round-trip (template output -> regex parse) in a test before shipping.
SEARCH_MULTIMATCH_REGEX = r"^(?P<number>[0-9]+)[.\s-]+(?P<name>.*?)(?P<args>(?:\s.*)?)$"
SEARCH_MULTIMATCH_TEMPLATE = "  {number}. {name}{aliases}{info}\n"
```

### 12.3 Lever 2 — replace `SEARCH_AT_RESULT` (full message control)

Point the setting at your own function for total control over *both* nomatch and multimatch output (it serves command- **and** object-searches). Signature and contract:

```python
# world/search.py
def at_search_result(matches, caller, query="", quiet=False, **kwargs):
    # matches: list of 0 / 1 / >1 entities (or Commands).
    # Must MSG appropriate errors (unless quiet) and RETURN a single match or None.
    # Respect kwargs["nofound_string"] / kwargs["multimatch_string"] if callers pass them.
    ...
```
```python
# settings.py
SEARCH_AT_RESULT = "world.search.at_search_result"
```

Easiest path: copy `evennia.utils.utils.at_search_result` verbatim and edit only the `len(matches) > 1` branch. The single-match (`return matches[0]`) and nomatch branches must be preserved or every search in the game breaks.

### 12.4 Lever 3 — `quiet=True` + your own resolver (best UX, most work)

`caller.search(query, quiet=True)` suppresses the default error and **returns the raw list**, letting a specific command resolve ambiguity interactively instead of forcing the player to re-type `dagger-2`. Evennia commands support generator `yield` for input:

```python
def func(self):
    matches = self.caller.search(self.args, quiet=True)
    if not matches:
        self.caller.msg(f"You see no '{self.args}'.")
        return
    if len(matches) > 1:
        for i, m in enumerate(matches, 1):
            self.caller.msg(f"  {i}. {m.get_display_name(self.caller)}")
        resp = yield ("Which one? (number)")      # command-level input
        try:
            target = matches[int(resp.strip()) - 1]
        except (ValueError, IndexError):
            self.caller.msg("Cancelled.")
            return
    else:
        target = matches[0]
    # ... use target
```

⚠️ `yield`-based input needs a session-backed command context (the default cmdhandler provides it; batch/unit-test contexts may not). Scope it to the few commands that need pretty disambiguation, not globally.

### 12.5 Design stance for PolishedWorld — fix identity, not the number

The prompt is ugly because the game can't tell two objects apart. Preferred order:

1. **Individuate crafted items** — give them distinguishing adjectives/aliases (material, quality tier, maker's mark) so an exact search (`steel dagger`, `bjorn's dagger`) returns a single hit and no prompt appears. Per §11.6, `object_search` runs the **exact key/alias pass first**, so a unique alias short-circuits multimatch entirely. Rides free on the crafting-quality progression hook (crit-craft → superior/named items) and recipe work.
2. **Stack truly-identical consumables** (arrows, twine) into one quantity-bearing object rather than N disambiguable ones — fewer objects also means lighter DB load with many players. Evennia has no built-in stacking; it's a custom `quantity`-attr + merge-on-same-key pattern (verify the contrib landscape at design time).
3. **Reskin / interactive resolver** (§12.2–12.4) is then only *residual polish* for the few remaining collisions, not the primary fix.

Roadmap cross-ref: backlog item *"Search / disambiguation UX + item identity"*.

---

## 13. Quick-reference table
 
| System | Module path | Status |
|---|---|---|
| GameTime (custom calendar) | `evennia.contrib.base_systems.custom_gametime` | Phase 2, indexing verified pending |
| ExtendedRoom | `evennia.contrib.grid.extended_room` | Phase 2, in progress |
| TraitHandler | `evennia.contrib.rpg.traits` | Phase 1, complete |
| BuffHandler | `evennia.contrib.rpg.buffs` | In use (`world/survival_buffs.py`) |
| TickerHandler | `evennia.scripts.tickerhandler` (built-in) | Planned (survival ticker) |
| CooldownHandler | `evennia.contrib.game_systems.cooldowns` | In use (`typeclasses/characters.py`) |
| Barter | `evennia.contrib.game_systems.barter` | In use, hardened (`world/barter.py`, §7) |
| Crafting | `evennia.contrib.game_systems.crafting` | In use (Stage 3; `world/crafting_base.py`) |
| Clothing | `evennia.contrib.game_systems.clothing` | In use (`typeclasses/clothing.py`, `world/garment_wear.py`) |
| AttributeProperty | `evennia.typeclasses.attributes` (built-in) | Use throughout |
| DurableObject mixin (`condition`/`apply_wear`/`is_broken`/`condition_line`) | `typeclasses/durable.py` (project) | Stage 2 Component B, complete |
| Search multimatch UX | settings `SEARCH_MULTIMATCH_*` / `SEARCH_AT_RESULT` | Backlog — item-identity + optional reskin (§12) |
| XYZGrid | `evennia.contrib.grid.xyzgrid` | Not in use — source-verified for Stage 6 (§14) |
| Wilderness | `evennia.contrib.grid.wilderness` | Not in use — source-verified for Stage 6 (§14) |
 
---
 
## 14. XYZGrid & Wilderness

> **Status: neither contrib is in use.** This section is pre-implementation source verification for
> roadmap Stage 6, done 2026-08-14. Every claim below was read out of
> `evennia/contrib/grid/xyzgrid/{xyzroom,xymap,xymap_legend}.py` and
> `evennia/contrib/grid/wilderness/wilderness.py`. All five files involved (those four plus
> `extended_room.py`) are **byte-identical between Evennia `main` and the `v6.1.0` tag** as of that
> date, so these findings hold for the pinned version this project runs. Nothing here has been
> exercised against a running server — it is source reading, not measurement, and the distinction
> matters until Stage 6 actually starts.

The working shape is the two contribs side by side: **XYZGrid for authored, persistent structure**
(roads, villages, anything a player should be able to return to and find unchanged) and
**wilderness for large homogeneous resource areas** (forest, mountain, anywhere the rooms are
interchangeable). They are independent systems with independent coordinate spaces and no built-in
bridge between them.

### 14.1 XYZGrid — coordinates are Tags

`XYZRoom` (a `DefaultRoom` subclass) stores its position as three Tags, categories
`room_x_coordinate` / `room_y_coordinate` / `room_z_coordinate`; `XYZExit` additionally carries
`exit_dest_x_coordinate` and siblings for its destination.

**Z is not height — it is the map's name** (a string, matched `__iexact`). Each Z is a separate 2D
map string living in a Python module. X and Y are ints.

The custom manager gives coordinate queries directly:

```python
XYZRoom.objects.get_xyz(xyz=(3, 7, "byvagen"))          # exactly one, no wildcards allowed
XYZRoom.objects.filter_xyz(xyz=("*", "*", "byvagen"))   # a whole map in one query
```

Both find subclasses of `XYZRoom`, not only exact matches. `'*'` is the wildcard and is accepted by
`filter_xyz` only.

`XYZRoom.xyz` caches into `self._xyz`, but **deliberately skips caching when any of the three tags
reads back `None`** — tags may not have finished saving on a freshly created room. Don't
reintroduce an unconditional cache.

For a future web atlas this is the cheap half: one tag query returns every room on a map with its
coordinates.

### 14.2 The map module is the source of truth, not the database

This is the fact with the largest operational consequence, and it inverts how this project has
built rooms so far.

`XYMap.spawn_nodes()` (`xymap.py`) begins by **deleting** rooms:

```python
for existing_room in _XYZROOMCLASS.objects.filter_xyz(xyz=(x, y, self.Z)):
    roomX, roomY, _ = existing_room.xyz
    if (roomX, roomY) not in map_coords:
        self.log(f"  deleting room at {existing_room.xyz} (not found on map).")
        existing_room.delete()
```

Any XYZRoom whose coordinate is no longer present in the map string is destroyed. Then, per node,
`MapNode.spawn()` (`xymap_legend.py`) either creates the room or — if one already exists — runs:

```python
spawner.batch_update_objects_with_prototype(self.prototype, objects=[nodeobj], exact=False)
```

`exact=False` means attributes *absent* from the prototype survive, but **everything the prototype
does define is rewritten**. A `desc` edited in-game with the `desc` command is therefore lost at the
next `xyzgrid spawn` if the prototype defines `desc`.

Practical rule: **grid areas are authored in map modules and prototypes under version control, not
with `dig` / `desc` in-game.** That suits this project's commit discipline, but it is a habit
change, and `spawn` is destructive rather than additive.

A node whose prototype is falsy is a *virtual* node — `spawn()` returns early and no room is built.

### 14.3 Map-to-map transitions, and the `taget_map_xyz` typo

Grid-to-grid transitions are solved in-contrib. `MapTransitionNode` (legend symbol `T`) is never
spawned as a room; its `get_spawn_xyz()` returns `target_map_xyz`, so the exit built toward it lands
on another Z-map instead. At most one link may connect to a `T` node; a two-way crossing needs a `T`
on each map, each pointing at the *real* `#` node on the other map — not at the other `T`.

⚠️ The base class `TransitionMapNode` (`xymap_legend.py:485`) misspells its own class attribute as
`taget_map_xyz`, while `get_spawn_xyz()` reads `self.target_map_xyz`. The class actually registered
in the default legend, `MapTransitionNode` (`:1184`), defines the name correctly, so ordinary use of
`T` is fine. **Subclass `MapTransitionNode`, never `TransitionMapNode` directly** — via the base
class the intended `MapParserError` never fires and you get a bare `AttributeError` instead.

Grid-to-wilderness has **no** contrib support: the wilderness is not a Z-map. That transition is
project code at designated trailhead rooms, in both directions.

### 14.4 Wilderness — rooms are recycled shells

`WildernessScript` holds the whole system on three Attributes: `db.rooms` (`(x, y)` → room),
`db.itemcoordinates` (object → `(x, y)`), and `db.unused_rooms`. Coordinates are 2D `(x, y)`, a
separate namespace from XYZGrid's `(x, y, z)`; several named wildernesses may coexist.

Movement does not move the character between rooms — it re-points a room at new coordinates.
`WildernessScript.move_obj()` assigns `obj.location` directly (`= None`, then `= room`), so **no
move hooks fire from the assignment itself** — the same failure family as the Barter `finish()` bug
in §7.5. The saving grace is that `WildernessExit.at_traverse()` calls `at_pre_move(None)` and
`at_post_move(None)` explicitly, so guards on those hooks do run — but with `None` as the
destination, so any guard that inspects where the mover is going gets nothing.

`_destroy_room()` returns a room to `unused_rooms` once no account remains in it. With the default
`preserve_items=False`, leftover objects get `location = None` but **keep their `itemcoordinates`
entry**, so they reappear when someone next stands on that coordinate. `preserve_items=True`
instead blocks recycling while any object is present. Dropped items and corpses therefore do
persist by coordinate — that part works.

### 14.5 ⚠️ What recycling does *not* reset

`WildernessRoom.set_active_coordinates()` reassigns the room's `contents` and rewrites the exits'
traverse/view locks. It does **not** touch Tags or Attributes on the room object.

Everything ExtendedRoom stores lives in exactly those two places: `room_states` are Tags
(`tags.batch_add`, category `room_state`), and `desc_*` seasonal descriptions and details are
Attributes. On a recycled shell they leak across coordinates. Set `on_fire` at `(5, 5)`, walk away,
let the room recycle — and the next occupant of that same shell at `(99, 99)` is still on fire.

**Rule for the wilderness: per-place state is coordinate-keyed data held by the map provider or the
script. Never a Tag or an Attribute on the room.** The same rule is what rules out scattering
resource nodes as objects (§14.6).

### 14.6 Wilderness performance is O(n) per step

`WildernessScript.get_objs_at_coordinates()` iterates the entire `itemcoordinates` dict — its own
docstring calls this a *"naive iteration through every object inside the wilderness"* — and it is called
from `set_active_coordinates()`, i.e. whenever a room is activated for a coordinate it was not
already showing.

For a lone traveller that is **every step**: the room behind them is recycled, the coordinate ahead
has no room, so a room is claimed and re-pointed. The cost of one step therefore scales with the
total object count of the whole wilderness, multiplied by concurrent movers. `itemcoordinates` is
also a single pickled Attribute on a single Script — one write hotspot for every object entering or
leaving.

Consequence for Stage 6: **resources in the wilderness should be coordinate-keyed data in the map
provider, materialised into an object only when a player actually harvests.** Objects-per-node does
not scale to the resource density this project wants.

### 14.7 Composing both with ExtendedRoom

Both `XYZRoom` and `WildernessRoom` inherit `DefaultRoom`, not `ExtendedRoom`, so neither brings
this project's weather, seasonal descriptions or room states along. The two sides cost very
different amounts to fix.

**Grid side — composes cleanly.** The hooks do not collide: `XYZRoom` overrides `return_appearance`
and `get_display_name`; `ExtendedRoom` overrides `get_display_desc` and does **not** touch
`return_appearance`. `XYZRoom.return_appearance()` opens with
`room_desc = super().return_appearance(looker, **kwargs)`, so under MRO
`PWGridRoom → XYZRoom → Room(ExtendedRoom) → DefaultRoom` the call reaches `DefaultRoom`'s version,
which calls `self.get_display_desc()` — resolving to ExtendedRoom's. Seasonal descriptions and the
minimap both work. Lock the MRO with a test rather than trusting it to stay accidental.

**Wilderness side — behaviour composes, storage does not.** `WildernessRoom.get_display_desc()` is
the *same* hook as ExtendedRoom's; it returns `ndb.active_desc` when set and otherwise falls through
to `super()`. So simply never setting `active_desc` lets ExtendedRoom answer. But per §14.5 the
underlying storage is unusable on a shared shell, so the behaviour has to be re-implemented in
memory — biome from the map provider by coordinate, season from `world/gametime_utils.py` — rather
than via `desc_*` Attributes. Writing Attributes per step would also defeat the contrib's entire
`ndb`-based no-DB-write-on-move design.

### 14.8 Two things XYZGrid gives away free

`XYZRoom.return_appearance()` renders an in-game ASCII minimap: `map_display`, `map_mode`
(`'nodes'` or `'scan'`), `map_visual_range` (default 2), `map_character_symbol`. Each is a class
attribute overridable per room and further overridable per-call via kwargs and per-map via
`xymap.options`. The map is emitted as a **separate `msg()` tagged `type='xymap'`**, which makes it
straightforward to route into its own client pane later.

Pathfinding across a map is also built in — `InterruptMapNode` (`I`) marks a node the auto-stepper
stops at, `InterruptMapLink` (`i`) the same for a link.

---

**Freshness:** tracked in the Rev header at the top of this file (Evennia baseline: `main`; §12 spot-checked 2026-07-01; §14 verified against `main` **and** the `v6.1.0` tag, 2026-08-14).
**Maintained alongside:** `PolishedWorld_GDD_v2.md`, `PolishedWorld_Functional_Decomposition.md`, `PolishedWorld_Code_Standards.md`.
