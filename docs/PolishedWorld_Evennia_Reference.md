# PolishedWorld Evennia Reference

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

**`@py`-not (separat gotcha):** `@py` bygger om sitt namespace per rad med tomma globals och
skriver aldrig tillbaka — inga namn överlever mellan rader, och comprehensions/generators
failar (de slår upp i de tomma globals). Spelvärld/DB-state persisterar dock. Använd
`evennia shell` för ren modullogik; självständiga `@py`-rader med `print()` för in-game-checks.

**Settern klampar också (verifierat 2026-07-06):** `current`-*settern* kör `_enforce_boundaries`,
så `skill.current = X` klampas till `[min, max]` vid tilldelning (max via `>=`). En read-modify
-write som `skill.current = skill.current + gained` auto-kappar därför vid traitens max (skills
använder `max=100`) — ingen manuell `min(cap, …)` krävs för säkerhet, men explicit klampning i
Python håller ett returnerat `old/new/delta` exakt. **Progression läser `.current`** (permanent
nivå), **resolution läser `.value`** (`(current + mod) * mult`, situationell) — en tool-`.mod`-buff
ska hjälpa själva checken men inte höja en improvement-rolls target.
**Corollary — `desc()` läser också `.value`:** `CounterTrait.desc()` slår upp descs-etiketten mot `self.value` (buffad), inte `.current`. En aktiv `.mod` (t.ex. +20 tool-buff) kan därför få `desc()` att rapportera fel tier. För tier-lookup på *permanent* nivå (t.ex. desc-tier-celebration som ska spegla verklig rang, inte tillfällig buff): använd en ren `tier_for(value, descs)` som speglar Evennias övre-gräns-inklusive-loop men tar en explicit int (`world/improvement.tier_for`), matad med de råa `old`/`new`-ints från `improve_skill_on_use`. Samma `.current`/`.value`-regel, en gång till.

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
 
**Status in PolishedWorld:** Planned — central to the player-driven economy.
 
### 7.1 Concept
 
A two-party negotiation system. Each party offers items, both must explicitly `accept` for the trade to finalize. Items only swap once both parties accept the **current** offer set — any `offer` modification resets the accept state.
 
### 7.2 Installation
 
```python
# In commands/default_cmdsets.py
from evennia.contrib.game_systems.barter import barter
 
class CharacterCmdSet(default_cmds.CharacterCmdSet):
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(barter.CmdTradeBase())
        self.add(barter.CmdOffer())
        self.add(barter.CmdAccept())
        self.add(barter.CmdDecline())
        self.add(barter.CmdEvaluate())
        self.add(barter.CmdStatus())
        self.add(barter.CmdTradeHelp())
```
 
### 7.3 In-game flow (player-facing)
 
```
A> trade B: I have a sword.
B> trade A: I'm interested.            # accepts the trade session
A> offer sword: rations please
B> offer ration: prime quality
A> accept
B> accept                              # both accepted — items exchange
```
 
### 7.4 Money in barter
 
The contrib doesn't have a special "currency" concept — coin objects are just items. For PolishedWorld:
 
> *"This system is primarily intended for a barter economy, but can easily be used in a monetary economy as well — just let the 'goods' on one side be coin objects."*
 
So **Gold/Silver/Copper coins are typeclassed objects** that get offered like any other item. This aligns naturally with the GameGold design (1:1 exchange — gold is a real, transferable in-game object).
 
### 7.5 ⚠️ Concurrency
 
`TradeHandler` ties two characters together via a `Script` (`TradeTimeout`). If a third party tries to initiate trade with someone already in a trade, `join` will fail. This is desired — but it means handling "the other player won't trade with me" needs UX consideration.
 
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

---
 
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
  the individual commands you need (e.g. just `CmdContainerGet`), not the bundle.

### 11.15 `search_object()` resolves `#dbref` strings

`evennia.utils.search.search_object(searchdata)` accepts a `#dbref` string or int, not just a key
(docstring: "Object key or dbref to search for."). Handy for resolving a configurable dbref from
settings into an object:

```python
matches = search.search_object(getattr(settings, "DEFAULT_RESPAWN_DBREF", None))
dest = matches[0] if matches else (self.home or self.location)
```

## 12. Search multimatch & disambiguation UX

*(Verified against live Evennia `main`, 2026-07-01. §11.6 covers the search-*resolution* mechanic — exact-first, then fuzzy — and the crafting-ingredient angle; this section covers the multimatch *UX*: why `ball-1`/`ball-2` appears and the three ways to tune it.)*

The default multimatch prompt is **intentional and fully tunable**. It's a *symptom* of two objects sharing an identical key, so the best fix is usually to make multimatch rare rather than to prettify the number (see §12.5).

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
| BuffHandler | `evennia.contrib.rpg.buffs` | Planned (post-survival) |
| TickerHandler | `evennia.scripts.tickerhandler` (built-in) | Planned (survival ticker) |
| CooldownHandler | `evennia.contrib.game_systems.cooldowns` | Planned |
| Barter | `evennia.contrib.game_systems.barter` | Planned (MVP completion) |
| Crafting | `evennia.contrib.game_systems.crafting` | Planned (post-MVP, 320 recipes) |
| Clothing | `evennia.contrib.game_systems.clothing` | Planned (post-MVP) |
| AttributeProperty | `evennia.typeclasses.attributes` (built-in) | Use throughout |
| DurableObject mixin (`condition`/`apply_wear`/`is_broken`/`condition_line`) | `typeclasses/durable.py` (project) | Stage 2 Component B, complete |
| Search multimatch UX | settings `SEARCH_MULTIMATCH_*` / `SEARCH_AT_RESULT` | Backlog — item-identity + optional reskin (§12) |
 
---
 
**Freshness:** tracked in the Rev header at the top of this file (Evennia baseline: `main`; §12 spot-checked 2026-07-01).
**Maintained alongside:** `PolishedWorld_GDD_v2.md`, `PolishedWorld_Functional_Decomposition.md`, `PolishedWorld_Code_Standards.md`.
