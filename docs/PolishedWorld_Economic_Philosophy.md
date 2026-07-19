# PolishedWorld - Economic Philosophy

> **Rev 2 · 2026-07-19** — corrected Principle 5: Gold has exactly ONE permanent exit (exchange back to GameGold), matching Principle 4's single burn point. Removed the erroneous "unlooted corpse decay destroys Gold" claim — currency never weathers; on death it drops to the room and persists until looted or exchanged. Dropped the in-world "deflationary pressure" line that depended on that false sink.
> **Rev 1 · 2026-07-11** — first version; defines the long-term economic philosophy and the principles the economy must never compromise. Sits above the two economy design docs and gives them their *why*.
>
> **Canonical:** `docs/PolishedWorld_Economic_Philosophy.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

## Purpose

PolishedWorld is designed around one principle:

> **Players create the world's value.**

The economy does not exist to generate currency. It exists to turn player effort, knowledge and cooperation into goods and services that other players want. Currency is only there to make that exchange convenient.

This document states the principles. It does not describe implementation — that lives in the two design documents below.

## Where this fits

Read in this order. Philosophy first, then the economy, then the blockchain that plugs into it:

1. `PolishedWorld_Economic_Philosophy.md` — *why* the economy is shaped this way (this document)
2. `PolishedWorld_GameGold_Economy.md` — the economy's design: currency, sources/sinks, faucet, monitoring
3. `GameGold_Design.md` — the external cryptocurrency and bootstrap camp in detail

The order mirrors the architecture: **the economy comes first, the integration second.**

---

## Core Principles

### 1. Players produce everything

Every finished good in the world originates from player activity.

The world provides only raw natural resources — wood, ore, plants, water, animals. Everything past that point (tools, clothing, weapons, food, repairs, transport) is produced by players through gathering, refining, crafting, repairing and trading.

NPC vendors are deliberately excluded from the *production* economy. Where the starting camp offers baseline goods, it does so as a bounded fallback (~10% worse or more expensive than player-crafted), never as a competitor — see `GameGold_Design.md`.

### 2. Value is work

Value is created by useful activity, not by holding currency. The economy is meant to reward:

gathering · refining · crafting · repairing · transport · trade · specialisation.

Passive wealth earns nothing on its own. Time, skill, knowledge and cooperation are the real sources of value; currency only represents that value after the fact.

### 3. Wear is the economic engine

Items are not permanent. Every crafted object follows a lifecycle:

```
resources → craft → use → wear → repair → (eventually) destroyed
```

Wear is not a punishment; it is what keeps the economy alive. It creates continuous demand, a continuous need for crafters, and continuous consumption. Repair extends an item's life but never removes the need for new production. An economy without sinks saturates and dies — wear is the primary sink for goods.

### 4. Gold enters the world at exactly one point

In-game Gold is minted in **one place only: the GameGold exchange.** There is no monster-drop gold, no quest gold, no NPC-vendor gold, no admin-spawned gold.

The temple faucet is **not** a second mint. The temple donates GameGold, stakes it, exchanges the staking rewards to Gold, and redistributes *that* Gold to new players for small tasks. Faucet Gold is therefore ordinary exchange-minted Gold that has simply changed hands — no Gold is created from nothing.

```
GameGold (blockchain)
        │  exchange 1:1  ← the ONLY mint point for Gold
        ↓
   in-game Gold
        ↓
   circulates between players
        ↓
   exchanged back to GameGold  ← the ONLY intentional burn
```

A single mint point is what makes the whole economy auditable and keeps it honest: every Gold in the world can be traced back to a real exchange.

### 5. Circulation is not a sink

Most things people call "gold sinks" — food, repairs, rent, fuel — do **not** destroy Gold. They move it. The crafter who repairs your sword receives your Gold; the temple that collects your rent pays it back out as faucet work. Every apparent sink is another player's income, and the Gold keeps circulating.

Gold leaves the game permanently in only **one** way:

- **Exchanged back to GameGold** — it returns to being crypto (intentional, reversible). This is the single true burn, matching the single mint point in Principle 4.

Gold never decays. When a character dies, their Gold drops to the room with the rest of their belongings — but unlike goods, currency does **not** weather away. It simply waits there until another player picks it up. So carrying wealth still holds real risk (you can lose it to whoever finds your remains) and there is still room for "treasure hunting" — but that Gold is *transferred*, never destroyed. The total Gold in existence changes only at the exchange.

### 6. The cold start is solved without buying crypto

A new player begins with nothing, and the economy is player-to-player — so there must be a way in that does not require buying cryptocurrency. That is the temple faucet's entire reason to exist: a dignified entry point (small paid tasks, not begging), financed by temple staking and routed through the single exchange mint point.

It is deliberately bounded — low reward, cooldowns, and a natural progression that nudges players out of the faucet and into real production and trade. The faucet seeds the economy; it is not meant to sustain anyone.

### 7. Barter is a first-class trading system

Barter is not a fallback for players without money. It is a full trading system, as legitimate as currency, because direct exchange often reflects real economic value better than a price does.

Players must always be free to negotiate:

item-for-item · item-for-currency · currency-for-currency · any mix of items and currency.

The economy must remain fully functional even for players who never touch currency at all.

### 8. Ownership is the thread that ties it together

Underneath the surface, almost every economic system is doing the same thing: moving or creating **ownership**.

Crafting creates ownership. Trade and barter transfer it. Repair preserves it. The exchange converts between in-game ownership (Gold) and external ownership (GameGold). Currency is just one instrument for transferring ownership — not the point of the economy.

*(This is a conceptual lens for reasoning about the design, not a mandate for a single unifying class. The systems are mechanically distinct and should stay that way until a real, demonstrated need argues otherwise.)*

---

## GameGold: an integration, not the economy

GameGold is an **external** cryptocurrency with its own independent blockchain. It can be exchanged 1:1 with in-game Gold, and that is the *only* relationship between them.

PolishedWorld's role is narrow and deliberate:

- It **never sells** GameGold or Gold for real money.
- It **never sets** the price — value is whatever the free market decides, including zero.
- It **never acts as a central bank** — it does not mint, burn, or defend GameGold; the blockchain mints GameGold through staking on its own.
- It only operates the Gold ⇄ GameGold exchange.

The point of GameGold is to let value created *inside* the world move to and from the outside world. It is a bridge, not a foundation.

---

## Separation of Concerns

The project is built as four independent domains, in dependency order:

```
Simulation        (time, weather, thermal, survival)
    ↓
Production         (gathering, refining, crafting, repair)
    ↓
Economy            (ownership, trade, barter, currency)
    ↓
External Integrations   (the GameGold blockchain)
```

Dependencies point **downward only**. The blockchain lives exclusively in the External Integrations layer, and no gameplay system may depend directly on blockchain functionality. Simulation does not know Production exists in order to run; Production does not need the Economy to function; the Economy does not need the blockchain to be online.

---

## Gameplay First

Gameplay always outranks external economics.

The GameGold market must never dictate crafting, survival, weather, progression or balance. Those systems are designed to be enjoyable on their own terms. If the crypto market swings, gameplay does not move with it.

> **Design Rule: PolishedWorld must remain a complete, enjoyable sandbox even if GameGold is removed entirely.**

GameGold is an integration. PolishedWorld is the game.

---

## Long-Term Goal

A living economy in which:

- players produce all goods,
- raw resources and finished items both hold value,
- wear creates continuous, honest demand,
- specialists have real professions,
- trade emerges naturally rather than being scripted,
- currency and barter coexist as equals,
- and external value can flow in and out of the world without ever becoming the foundation the game rests on.

The world should be worth living in before a single coin changes hands.
