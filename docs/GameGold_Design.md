# GameGold - PolishedWorld Cryptocurrency Design

> **Rev 1 · 2026-07-02** — first versioned copy; platform migrated Komodo Smartchain → blackcoin-more fork (Bitcoin Core 26.x, PoSV3).
> **Canonical:** `docs/GameGold_Design.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

## Overview

GameGold is an experimental cryptocurrency designed to bridge the in-game economy of PolishedWorld with real-world value. It is **not** intended as a speculative investment or get-rich-quick scheme, but rather as an interesting technical experiment that adds a unique dimension to the game.

## Core Philosophy

- **Hobby project first**: This is an indie/experimental project with no guarantees
- **Gameplay over speculation**: The game comes first, crypto is a feature, not the product
- **Transparency**: Clear communication that this may never be completed or successful
- **No official sales**: PolishedWorld will never sell GameGold or in-game gold for real money
- **Community-driven**: Players who want to help test, stake, or participate are welcome

## Technical Specifications

| Parameter | Value |
|-----------|-------|
| Platform | blackcoin-more fork (Bitcoin Core 26.x base, PoSV3) |
| Consensus | 100% Proof of Stake (PoSV3) after 100 PoW bootstrap blocks |
| Block time | 1 minute |
| Block reward | 1 GameGold |
| Daily supply | ~1,440 GameGold |
| Annual supply | ~525,600 GameGold |

### Bootstrap Phase

- **Blocks 1-100**: Proof of Work only
- **Purpose**: Create initial coins required for PoS to function
- **After block 100**: 100% Proof of Stake

### Why a Blackcoin fork (blackcoin-more)?

- **PoSV3 is exactly our consensus model** — pure Proof of Stake after a short PoW bootstrap, which is precisely GameGold's design, rather than bending a general-purpose platform to fit
- **Modern, audited base** — blackcoin-more tracks Bitcoin Core 26.x, so we inherit years of hardening, SegWit, and a familiar `bitcoin.conf` / RPC surface
- **Full sovereignty** — our own `chainparams.cpp` (fair launch, no premine, 1-min blocks, 1 coin/block) instead of depending on another platform's infrastructure or token rules
- **Runs on our hardware** — Bitcoin Core has ARM64 builds, so nodes fit the Orange Pi Zero 2W deployment
- **Simple, strong node security** — a wallet-less public node can be exposed while an isolated staking node holds keys (see `PolishedWorld_GameGold_Economy.md`)

> **Migration note**: GameGold originally targeted a Komodo Smartchain; we moved to a blackcoin-more fork for the reasons above.

## Economic Model

### In-Game Currency Denominations

```
1 Gold = 100 Silver
1 Silver = 100 Copper
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
1 Gold = 10,000 Copper
```

This provides granularity for everyday transactions (buying bread for a few Copper) while Gold remains the "bank level" currency for larger transactions and crypto exchange.

### The 1:1 Exchange Rate

```
1 GameGold (crypto) = 1 Gold (in-game)
```

This is a **hard peg** maintained by the official exchange mechanism.

### Minimum Exchange Amount

**10 Gold minimum** for all exchanges (both directions).

Rationale:
- Reduces administrative burden during manual handling phase
- Prevents micro-optimization and spam transactions
- Makes exchanging a meaningful decision
- New players must actually accomplish something before cashing out
- Makes staking rewards feel significant (1 whole Gold per block = 10,000 Copper)

### Gold Creation

**Critical design decision**: In-game gold can ONLY be created by exchanging GameGold cryptocurrency. There is no other source of gold in the game - no monster drops, no quest rewards, no NPC vendors.

```
GameGold (blockchain)
        â”‚
    Exchange 1:1
        â”‚
    In-game Gold â†â”€â”€ ONLY source
        â”‚
    Circulates between players
        â”‚
    Can be exchanged back to GameGold
```

### Player-Driven Economy Integration

Since PolishedWorld has a 100% player-driven economy:

- **No gold is ever destroyed** - it only changes hands
- Every "gold sink" (food, repairs, fuel) is another player's income
- The crafter who repairs your sword receives your gold
- That gold continues circulating until someone exchanges it back to crypto

### Self-Regulating Balance

The system creates two communicating vessels:

| State | Effect | Player Response |
|-------|--------|-----------------|
| Much gold in-game, little crypto available | Crypto becomes scarce, potentially more valuable | Players exchange gold â†’ crypto |
| Much crypto staked, little gold in-game | Hard to trade, low liquidity | Players exchange crypto â†’ gold |

Players regulate the money supply themselves based on their individual needs and incentives.

### Death and Gold Loss

When a player dies, they leave behind a **corpse containing all gold and items** they were carrying.

```
Player dies in the wilderness
        â”‚
    Corpse with gold + items
        â”‚
    â”Œâ”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚                   â”‚
Someone loots       No one finds corpse
    â”‚                   â”‚
Gold circulates     Gold lost permanently
    â”‚                   â”‚
Normal economy      Actual gold sink (!)
```

**Economic effects:**
- Creates real risk to carrying large amounts of gold
- Incentivizes staking (gold outside game is safe)
- Potential "treasure hunting" for old corpses
- Natural deflation mechanism if corpses go unlooted

### Permanent Loss Mechanisms

There are only two ways gold/GameGold can permanently leave circulation:

**In-game (gold):**
- Unlooted corpses in the wilderness

**On-chain (GameGold):**
- Lost wallet passwords
- Lost private keys
- Abandoned wallets ("not worth the effort to cash out")
- Destroyed hardware with keys

```
Player quits the game
        â”‚
    â”Œâ”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚                   â”‚                â”‚
Forgets wallet      Loses keys       "Not worth it"
password                                 â”‚
    â”‚                   â”‚            5 GameGold left
    â”‚                   â”‚            "I'll just leave it"
    â”‚                   â”‚                â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                        â”‚
            GameGold lost permanently
                        â”‚
            Total supply decreases forever
```

| Sink | Location | Cause |
|------|----------|-------|
| Unlooted corpse | In-game | Player death + no one finds it |
| Lost wallet | Blockchain | Forgotten password/keys |
| Abandoned wallet | Blockchain | Player decision |
| Destroyed keys | Blockchain | Hardware failure/accident |

**Design note:** Both the game world and the blockchain have the same dynamic - carelessness or abandonment leads to permanent loss. This creates natural, uncontrollable deflation that mirrors real-world economics. All other "sinks" (rent, purchases, fees) simply transfer gold between players or back to the temple for recirculation.

## Why This Isn't Pay-to-Win

Traditional games:
```
Player pays $100 â†’ Gets 10,000 gold instantly â†’ Buys best items from NPCs
```

PolishedWorld:
```
Player buys crypto â†’ Exchanges to gold â†’ Must find a player willing to sell
                                              â”‚
                                        That item must:
                                        - Exist (someone crafted it)
                                        - Be for sale (owner wants to sell)
                                        - Price agreed upon (seller's market)
```

Money gives you **purchasing power**, not **guaranteed access**. Rare items remain rare regardless of how much gold exists.

## Staking Incentive

Players face a meaningful choice:

| Gold in-game | GameGold staked |
|--------------|-----------------|
| Ready to spend | Generates passive rewards |
| Risk of impulse purchases | "Locked" outside game |
| Immediate liquidity | Earning staking rewards |

This creates natural pressure to not hoard excessive gold in-game, as staked crypto earns rewards while idle gold does not.

### Hypothetical Future Scenario: Professional Stakers

**Note:** This is a theoretical scenario far in the future, not something we aim for or encourage now. It's documented here for completeness.

If GameGold were to achieve a stable market value, it could attract non-player stakers - people interested only in staking income, not in playing the game.

**Three types of GameGold holders:**

| Type | Behavior | Effect on economy |
|------|----------|-------------------|
| Players | Exchange to gold, play the game | Gold circulates in-game |
| Professional stakers | Stake only, sell rewards | Liquidity on exchanges |
| Hybrids | Play + stake | Both |

**Potential effects:**

```
Professional staker
        â”‚
    Buys GameGold on exchange
        â”‚
    Stakes (never exchanges to in-game gold)
        â”‚
    Earns staking rewards
        â”‚
    Sells rewards on exchange
        â”‚
    â”Œâ”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚                   â”‚
Players buy         Other stakers buy
    â”‚                   â”‚
Exchange to gold    Stake more
    â”‚                   â”‚
Economy gets        Cycle continues
more liquidity
```

| Effect | Assessment | Comment |
|--------|------------|---------|
| Reduces available supply | Neutral/Positive | Less on market = potentially higher value |
| Takes rewards from players | Neutral | But players get more gold liquidity |
| Sells rewards constantly | Neutral | Creates sell pressure but also liquidity |
| Secures the network | Positive | More stakers = more stable chain |

**Important:** This scenario only becomes relevant if:
1. GameGold achieves meaningful, stable value
2. The game has enough players to create demand
3. Exchanges list GameGold with sufficient volume

None of these are guaranteed or expected. This is a hobby project first.

## Distribution Plan

### Fair Launch

- No premine (beyond the ~100 coins from PoW bootstrap)
- Everyone starts from zero
- Initial coins go to whoever participates in bootstrap mining

### Ongoing Distribution

| Method | Description |
|--------|-------------|
| Staking rewards | 1 GameGold per block, distributed to stakers |
| Temple faucet | In-game work for small payments (see below) |
| Bug bounties | Rewards for finding and reporting bugs |
| Playtesting | Rewards for testing and providing feedback |
| Community help | Small rewards for helping new players |

## Temple Faucet System

### Concept

A self-financing in-game faucet that allows new players to earn starting capital without buying cryptocurrency, while maintaining the principle that all gold originates from the blockchain.

### How It Works

```
Adam donates 1000 GameGold to temple wallet
        â”‚
    Temple wallet stakes continuously
        â”‚
    Generates staking rewards
        â”‚
    Rewards exchanged to in-game gold
        â”‚
    Temple offers small payments for services
        â”‚
    New players earn starting capital
        â”‚
    No gold created from nothing âœ“
```

### Temple Services

New players can perform simple tasks for the temple in exchange for a small payment (e.g., 25-50 Copper). This provides dignity - it's work, not begging.

**Fetch quests:**
- Fetch water from the well
- Gather wood for the sacrificial fire
- Pick wildflowers for the altar
- Retrieve incense from the trader

**On-site work:**
- Sweep the temple floor
- Light candles and torches
- Refill oil lamps
- Keep vigil at the altar

**Delivery tasks:**
- Carry a message to a priest in the next village
- Deliver blessed water to a sick farmer
- Bring food to a hermit

**Symbolic offerings:**
- "Donate" something gathered (wood, berries, water)
- Temple "buys" it for a few Copper

### Anti-Abuse Mechanics

| Mechanic | Effect |
|----------|--------|
| Cooldown | Max 1-2 tasks per day |
| Progression | After X tasks: "You no longer need our help, blessings upon you" |
| Low reward | 25-50 Copper (enough for a meal, not more) |
| Requires action | Must actually perform task, not just click |

### Purpose

This solves the "cold start" problem: new players begin with 0 gold and need to sell to someone who already has gold. The temple provides an entry point into the economy without requiring cryptocurrency purchase.

> *"The temple welcomes all travelers. For those willing to help, there is always a small gift."*

### Temple as Producer

Beyond the faucet, the temple also serves as an early-game producer of essential goods:

**Products:**
- Parchment/Pergament
- Ink
- Empty books (recipe books, spellbooks, journals)

**Economic role:**
```
Early game (few players)
   â”‚
   Temple is the only source
   â”‚
   â†“

Growth phase (crafters emerge)
   â”‚
   Players: 10 Silver    Temple: 11 Silver (+10%)
   â”‚
   Buyers choose players
   â”‚
   â†“

Mature game (active economy)
   â”‚
   Players dominate the market
   â”‚
   Temple â†’ Newspaper supplier + backup only
```

**Design principles:**
- Temple prices are ~10% higher than player crafters
- This incentivizes players to buy from each other
- Temple never competes out players, just fills gaps
- As economy matures, temple becomes less relevant for trade

**Books as gameplay:**

| Book type | Use |
|-----------|-----|
| Empty recipe book | Players record discovered recipes |
| Empty spellbook | Mages collect spells |
| Journal | Personal log (RP value) |

This creates demand that grows with the player base - more crafters = more recipe books needed.

## Newspaper Faucet

A second faucet tied to the in-game newspaper that posts daily updates on X.com (Twitter).

### Concept

The newspaper is run by temple monks as a spiritual service - documenting the world's events. Since the temple owns both production and the newspaper, materials (parchment, ink) are provided internally. Players are paid to help with transport and practical tasks.

**Note:** Editorial content (actual news) is handled by the monk editors, not players. This avoids content moderation issues.

### Newspaper Jobs (paid by temple)

**Transport/delivery:**
- Carry parchment from the production room to the editorial office
- Deliver ink to the printing press
- Post notices on the village board
- Deliver newspapers to the tavern
- Carry messages between monks in different locations

**Material gathering:**
- Collect feathers (for quills)
- Fetch wax (for seals)

**Maintenance:**
- Light the lanterns outside the editorial office
- Clean the printing press

### Economic Loop

```
Temple produces parchment/ink
        â”‚
    Newspaper (same organization) receives materials
        â”‚
    Temple pays players for transport jobs
        â”‚
    Players spend earnings in the economy
        â”‚
    Eventually: players craft and sell to temple instead
```

### Two Faucets, Different Character

| Temple | Newspaper |
|--------|-----------|
| Water, wood, sweeping | Transport, delivery, maintenance |
| Spiritual service | Practical logistics |
| Timeless, calm | Busy, daily rhythm |

Both provide the same economic function (entry point for new players) but with different flavor. Both are financed by the same source: temple staking rewards.

## Bootstrap Economy Summary

The temple creates a minimal functioning economy while waiting for the player-driven economy to mature:

```
Staking rewards
      â”‚
  Temple receives gold
      â”‚
  â”Œâ”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
  â”‚                    â”‚
Pays players      Produces goods
for faucet jobs   (parchment, ink, books)
  â”‚                    â”‚
  â”‚               Supplies newspaper (internal)
  â”‚               Sells to players (+10%)
  â”‚                    â”‚
  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
                       â”‚
               Gold circulates
                       â”‚
               Players start crafting
                       â”‚
               Undercut temple prices
                       â”‚
               Player economy takes over
               (temple buys from players instead)
```

This is a self-regulating system that gracefully fades into the background as the real economy emerges.

## Start Camp - Safe Zone

The starting area is a small, protected settlement with the temple as its heart. This provides new players a safe environment to learn the game and enter the economy.

### Structure

```
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚   TEMPLE    â”‚
                    â”‚  (staking)  â”‚
                    â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
                           â”‚
                     Finances everything
                           â”‚
     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
     â”‚          â”‚          â”‚          â”‚          â”‚          â”‚
     â–¼          â–¼          â–¼          â–¼          â–¼          â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”â”Œâ”€â”€â”€â”€â”€â”€â”â”Œâ”€â”€â”€â”€â”€â”€â”€â”â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ GUARDS â”‚â”‚NEWSPAPERâ”‚â”‚FAUCETâ”‚â”‚PRODUCEâ”‚â”‚  SHOP   â”‚â”‚  BANK  â”‚
â”‚(2 NPCs)â”‚â”‚ (monks) â”‚â”‚(jobs)â”‚â”‚(goods)â”‚â”‚(backup) â”‚â”‚(vault) â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜â””â”€â”€â”€â”€â”€â”€â”˜â””â”€â”€â”€â”€â”€â”€â”€â”˜â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Temple Organization

The temple is staffed by monks who live simply and serve the community:

```
TEMPLE
   â”‚
   â”œâ”€â”€ Monks/Priests (no salary, temple provides for them)
   â”‚      â”‚
   â”‚      â”œâ”€â”€ Editor (1 monk) â”€â”€â”€â”€â”€â”
   â”‚      â”œâ”€â”€ Reporters (2-3 monks)â”œâ”€â”€ Run the newspaper
   â”‚      â””â”€â”€ Others â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€ Faucet jobs, production, services
   â”‚
   â”œâ”€â”€ Operations
   â”‚      â”œâ”€â”€ Newspaper (staffed by monks, no labor cost)
   â”‚      â”œâ”€â”€ Production (parchment, ink, books, porridge)
   â”‚      â”œâ”€â”€ Bank vault (secure storage, weekly rent)
   â”‚      â””â”€â”€ Faucet jobs (paid to players)
   â”‚
   â””â”€â”€ Finances
          â”œâ”€â”€ Guard salaries + basic supplies
          â”œâ”€â”€ Player jobs (deliveries, fetch water, etc.)
          â””â”€â”€ Bank rent income (gold sink)
```

**Narrative logic:**
- Monks live simply (no salary, temple provides)
- Spreading knowledge (newspaper) is spiritual service
- Helping travelers (faucet) is their calling
- Production (books, parchment) supports learning
- Safeguarding valuables (bank) is a sacred trust

> *"The temple sees all, the temple tells all."*

### Guard System

Two NPC guards protect the starting camp from wild animals, creating a safe zone for new players.

**Employment:**
- Guards are employed by the temple
- Temple provides basic supplies (porridge, water, torches)
- Guards receive a weekly salary (in Silver)
- Guards can spend their salary buying from players

**Guard needs (daily):**
- Food (2 portions/day)
- Drink (water, ale)
- Torches/oil (night shift)

**Occasional needs:**
- Weapon repair
- Armor maintenance
- Medicine (if injured)

**Faucet jobs related to guards:**
- "Bring lunch to the guard at the north gate"
- "Fetch water for the night shift"
- "Deliver new torches"

### Guard Food Economy

The guards create a stable customer base for food producers, but they're frugal:

**The 80% rule:**
Guards only offer 80% of what other players have paid recently. They're a "buyer of last resort" - reliable but cheap.

| Phase | Guards eat | Economic effect |
|-------|------------|-----------------|
| Day 1 | Temple porridge | No player activity |
| First hunter | Buys meat (80% of asking price) | Gold flows to player |
| Multiple hunters | Competition drives prices down | Guards get better deals |
| Mature economy | Contract with lowest bidder | Stable business |

**Economic role:**
- Guaranteed buyer (always has temple salary to spend)
- Price floor (80% of market rate)
- Fallback for players who can't find better buyers
- Consistent demand creates predictable income opportunity

### Temple as Universal Backup

The temple serves as fallback supplier for all basic needs:

| Need | Temple offers | Players can sell |
|------|---------------|------------------|
| Food | Porridge | Meat, bread, fish, stew |
| Drink | Water | Ale, wine, mead |
| Light | Tallow candles | Wax candles, torches |
| Writing | Basic parchment | Quality parchment |
| Books | Simple bindings | Decorated books |

**Design principle:** Temple goods are always available but ~10% more expensive and/or lower quality than player-crafted alternatives. This ensures:
- Economy never stalls (baseline always exists)
- Players are incentivized to craft and sell
- No player can monopolize essential goods

### Bank Vault System

The temple provides secure storage for players who want to protect valuables from death loss.

**Implementation:** Uses Evennia's containers contrib (`evennia.contrib.game_systems.containers`)

**How it works:**
```
Player rents a bank locker
        â”‚
    Stores gold and items
        â”‚
    Pays weekly rent
        â”‚
    Contents are safe from death
```

**Rental terms:**
- Minimum rental period: 1 week
- Payment: Weekly in advance
- Size: One standard locker per player (upgrades planned for future)

**Non-payment consequences:**
```
Rent due
   â”‚
   â”œâ”€â”€ Paid â†’ Locker remains accessible
   â”‚
   â””â”€â”€ Not paid â†’ Locker locked
                      â”‚
                  Player has 1 year to pay
                      â”‚
                  â”Œâ”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                  â”‚                   â”‚
              Pays debt           Doesn't pay
                  â”‚                   â”‚
              Unlocked           Contents confiscated
                                      â”‚
                                 Sold at auction
```

**Economic effects:**
- Weekly rent recirculates through the temple (pays for faucet jobs)
- Rent is NOT a gold sink - it stays in the economy
- Auctions create interesting economic events
- Players must balance rent cost vs death risk

**Strategic choice for players:**

| Storage option | Safe? | Cost | Availability | Returns |
|----------------|-------|------|--------------|---------|
| Carry on person | No (death risk) | Free | Immediate | None |
| Bank locker | Yes | Rent/week | Must visit temple | None |
| Staked as crypto | Yes | Free | 10 Gold min + exchange time | Staking rewards |

This creates meaningful decisions:
- Keep some gold on hand for daily needs (risky but convenient)
- Store valuables in locker (safe but costs rent)
- Stake larger amounts (safe + profitable but less liquid)

### Start Camp Summary

The starting camp provides:

1. **Safety** - Guards keep wildlife away
2. **Economy entry** - Faucet jobs for starting capital  
3. **Customers** - Guards buy food and supplies from players
4. **Baseline supply** - Temple sells essentials
5. **Secure storage** - Bank vault protects valuables
6. **Learning space** - New players can explore systems without danger

As players grow stronger and the economy matures, they venture out from the camp into the wider (dangerous) world, while the camp remains a safe hub for new arrivals and trade.

### Transparency Requirements

Since trust is essential, all temple finances must be publicly verifiable:

**On-chain (automatic):**
- Temple wallet address (public)
- Exact balance
- All incoming staking rewards
- All outgoing transactions

**Off-chain (requires effort):**
- Public dashboard/log linking rewards to in-game distribution
- In-game "temple wall" showing faucet balance and recent payments
- Monthly reconciliation: "Temple received X rewards, distributed Y gold to Z players"

**What requires trust:**
The manual exchange step (crypto â†’ in-game gold) cannot be fully trustless without complex smart contracts. However, with a public wallet + public log, anyone can verify consistency.

### Legal Note

The tax and legal implications of this structure (donation to own project, staking rewards, in-game distribution) should be clarified with Swedish tax authorities (Skatteverket) or a tax advisor before implementation. This is a hobby project with low amounts, but proper compliance is important.

## Exchange Mechanism

### Phase 1: Manual Handling

Initially, exchanges will be handled manually:

1. Player requests exchange (Discord, in-game, etc.)
2. Verify gold/crypto balance
3. Perform exchange manually
4. Confirm completion

**Rationale**: Low initial volume doesn't justify automation complexity.

### Phase 2: Automation (Future)

When volume justifies it:
- REST API integration with GameGold node
- In-game exchange interface
- Automated verification and transfer

### Exchange Limits (To Be Determined)

Considerations for preventing micro-optimization abuse:
- Minimum/maximum exchange amounts
- Daily exchange limits
- Possible exchange fee that recirculates into game world (treasure chests, events)

### Peer-to-Peer Exchange

Players can freely exchange gold for GameGold directly with each other outside the official system. This is expected and healthy - it creates a natural market that finds its own price around the official 1:1 anchor.

## Player Trading System

### Barter System

Player-to-player trading uses **Evennia's barter contrib** (`evennia.contrib.game_systems.barter`).

This provides:
- Direct trading between two players
- Offer/counteroffer negotiation
- Both parties must accept before trade completes
- No centralized marketplace (organic interaction)

### Trading Locations

Players meet organically in the world to trade. The starting camp naturally becomes a trading hub due to:
- Safety (guards keep wildlife away)
- Foot traffic (new players arriving)
- Central services (temple, newspaper)

## Example Player Journey

```
New player (no money, no crypto)
        â”‚
    Does temple faucet jobs for starting Copper
        â”‚
    Buys first meal, starts gathering wood
        â”‚
    Sells wood to other players
        â”‚
    Earns gold over time, saves up
        â”‚
    Reaches 10 Gold (minimum exchange)
        â”‚
    Exchanges 10 Gold â†’ 10 GameGold
        â”‚
    Stakes overnight
        â”‚
    Earns small staking reward
        â”‚
    Now has 10+ GameGold generating passive income
```

The "rich" player who initially exchanged crypto into gold **funded** the new player's ability to start staking through normal economic activity.

## Value Proposition

The value of GameGold is determined entirely by the **free market** - not set by PolishedWorld.

For illustration, if 1 GameGold were to trade at 1 Ã¶re (0.01 SEK):
- A day of gameplay earning 25 gold = 25 Ã¶re
- Nobody gets rich
- But effort is **not worthless**
- There's a tangible (if tiny) connection to reality

The actual market price may be higher, lower, or zero - and that's fine. The value emerges from player activity and demand, not from any official pricing.

## Risks and Disclaimers

To be communicated clearly to all participants:

1. **This is an experiment** - may never be completed
2. **No guarantees** - neither game nor cryptocurrency
3. **Don't invest more than you can lose** - treat it as entertainment cost
4. **Speculation is discouraged** - this is not designed for trading profits
5. **Development timeline is uncertain** - hobby project with ~5 hours/week

## Inspiration

- **Eve Online**: Demonstrated that player-driven economies can work at scale
- **Web3 game failures**: Learned what NOT to do (speculation-first, ponzi dynamics)
- **Original reasoning**: Developed through iterative thinking about fair economic systems

## Timeline

| Phase | Status |
|-------|--------|
| Blockchain setup | Tested, ready to deploy |
| Initial distribution | Planned (fair launch + faucet) |
| Manual exchange | Will implement when needed |
| Game integration | After core gameplay is solid |
| Automated exchange | When volume justifies it |

## Summary

GameGold is not trying to revolutionize anything. It's a simple experiment: what happens when you connect a game's economy to a real (if tiny) value through cryptocurrency, while keeping the game itself as a pure player-driven sandbox?

The answer might be "nothing interesting" - and that's fine. The journey of building it is the reward.

---

*Last updated: November 27, 2025*
*Status: Design phase*
