# PolishedWorld Evennia Reference

> **Rev 2 · 2026-07-02** — added §11.7–§11.11 (H6 garment durability: TICKER_HANDLER vs GLOBAL_SCRIPTS, command testing via execute_cmd, validate-then-commit ordering, repair-as-command, condition end-rounding).
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
| BuffHandler | `evennia.contrib.rpg.buffs` | Planned (post-survival) |
| TickerHandler | `evennia.scripts.tickerhandler` (built-in) | Planned (survival ticker) |
| CooldownHandler | `evennia.contrib.game_systems.cooldowns` | Planned |
| Barter | `evennia.contrib.game_systems.barter` | Planned (MVP completion) |
| Crafting | `evennia.contrib.game_systems.crafting` | Planned (post-MVP, 320 recipes) |
| Clothing | `evennia.contrib.game_systems.clothing` | Planned (post-MVP) |
| AttributeProperty | `evennia.typeclasses.attributes` (built-in) | Use throughout |
| Search multimatch UX | settings `SEARCH_MULTIMATCH_*` / `SEARCH_AT_RESULT` | Backlog — item-identity + optional reskin (§12) |
 
---
 
**Freshness:** tracked in the Rev header at the top of this file (Evennia baseline: `main`; §12 spot-checked 2026-07-01).
**Maintained alongside:** `PolishedWorld_GDD_v2.md`, `PolishedWorld_Functional_Decomposition.md`, `PolishedWorld_Code_Standards.md`.
