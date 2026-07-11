# PolishedWorld - GameGold & Economy Design

> **Rev 2 · 2026-07-11** — added reading-order pointer to the Economic Philosophy doc; corrected Temple-Faucet rewards from Gold to Copper (were 200–400× too high) and aligned the implementation sketch; removed the "admin gold (except events)" carve-out so Gold Creation matches the single-mint-point principle; clarified CurrencyHandler.add() as a mint-only primitive.
> **Rev 1 · 2026-07-02** — first versioned copy; platform migrated to blackcoin-more fork (PoSV3); added Node Security & Staking Infrastructure section (node-role separation + cold-staking deferred).
> **Canonical:** `docs/PolishedWorld_GameGold_Economy.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.
>
> **Read first:** this document assumes the principles in `PolishedWorld_Economic_Philosophy.md`. Reading order: Philosophy → GameGold_Economy → GameGold_Design.

## GameGold Cryptocurrency

### Core Philosophy
- **Hobby/Experiment** - NOT an investment opportunity
- **Discourage Speculation** - Value determined by player supply/demand
- **Never Official Sales** - Adam will never sell crypto/gold officially
- **Fair Launch** - No premine, community distribution

### Blockchain Specifications
| Property | Value |
|----------|-------|
| Platform | blackcoin-more fork (Bitcoin Core 26.x, PoSV3) |
| Consensus | 100% Proof of Stake (after 100 PoW-block bootstrap) |
| Block Time | 1 minute |
| Block Reward | 1 coin per block |
| Launch | Fair launch, no premine |

### Currency System

**Three Denominations**
```
1 Gold = 100 Silver = 10,000 Copper
```

| Denomination | Use Case |
|--------------|----------|
| Copper | Daily transactions, small purchases |
| Silver | Medium transactions, common items |
| Gold | "Bank-level" transactions, crypto exchange |

**Minimum Exchange**: 10 Gold (prevents micro-transaction spam)

### Key Principle: Gold Creation
**Gold can ONLY be created via cryptocurrency exchange. No exceptions.**
- No NPC gold rewards
- No quest gold
- No admin gold spawning — not even for events
- All gold circulates between players

---

### Node Security & Staking Infrastructure

**Decision (2026-07-02): node-role separation.** The staking wallet is never exposed to the network directly.

- **Public node** — wallet-less (`disablewallet=1`); the only internet-facing node (seed / block explorer). No keys, so nothing to steal if compromised.
- **Staking node** — holds the wallet, `listen=0` (accepts no inbound), RPC bound to localhost, connects outbound to the public node via `addnode`. Isolated behind the firewall.
- **Hot-balance minimization** — split into an offline cold *treasury* (bulk of coins) and a minimal hot *faucet/staking* wallet, topped up periodically. Only the small hot balance is ever at risk.
- If the fork supports it, unlock the staking wallet for staking only (`walletpassphrase <pass> <timeout> true` — verify with `help walletpassphrase`).

This gives most of the protection of a masternode-style setup at a fraction of the complexity, and is proportionate for a fair-launch hobby chain with low coin value.

**Deferred — Cold staking.** True cold staking (P2CS delegation: a staker key that can *only* stake, an owner key that alone can spend) is **not** native to blackcoin-more / PoSV3 — it belongs to the PIVX lineage (`delegatestake`) and would require consensus-level changes plus a soft fork on our own chain.
**Trigger to revisit:** only if GameGold begins to carry real economic value on a secondary market (people buying/selling the fork for fiat at non-trivial amounts). Until then, node-role separation is sufficient and cold staking would be over-engineering.

---

## Temple-Faucet System

Addresses the cold-start problem for new players without requiring crypto purchase.

### Concept
- Temple stakes donated GameGold
- Provides small payments for simple services
- Gateway for new players to earn initial currency

### Tasks & Rewards
| Task | Copper Reward | Cooldown |
|------|---------------|----------|
| Sweep floors | 25 | 1 hour |
| Fetch water | 35 | 1 hour |
| Organize books | 50 | 2 hours |
| Light candles | 25 | 1 hour |
| Clean altar | 35 | 2 hours |

### Design Goals
- **Low rewards** - Supplement, not primary income
- **Cooldowns** - Prevent abuse/farming
- **RP integration** - Tasks fit world lore
- **Progression** - Encourage moving to crafting/trading

### Implementation Sketch
```python
class TempleFaucet:
    """Provides small copper amounts for simple tasks."""

    TASKS = {
        'sweep_floor': {'copper': 25, 'cooldown': 3600},
        'fetch_water': {'copper': 35, 'cooldown': 3600},
        'organize_books': {'copper': 50, 'cooldown': 7200},
    }

    def complete_task(self, character, task_name):
        """Award copper for completing a temple task."""
        task = self.TASKS.get(task_name)
        if not task:
            return False

        # Check cooldown
        cooldown_key = f"faucet_{task_name}"
        if character.cooldowns.get(cooldown_key):
            return False

        # Award copper
        character.currency.add('copper', task['copper'], source='faucet')

        # Set cooldown
        character.cooldowns.add(cooldown_key, task['cooldown'])

        return True
```

---

## Player-Driven Economy

### Core Principle: No NPC Vendors
Every item must be:
- âœ… Crafted by a player from gathered resources
- âœ… Traded between players
- âœ… Found as placed item (admin/events only)
- âŒ Never bought from NPCs
- âŒ Never generated automatically

### Resource Flow Design

For every new item/resource, define:

**1. SOURCE - How does it enter the world?**
- Gathering from environment (nodes, foraging)
- Byproduct of crafting (sawdust from woodworking)
- Creature drops (if using creatures)
- Regenerating resource nodes (rate-limited)

**2. SINK - How does it leave the world?**
- Consumed (food, potions)
- Degraded (tool/weapon durability)
- Transformed (crafting material â†’ finished item)
- Lost on death (if using that mechanic)

**3. CIRCULATION - How does it move between players?**
- Barter system (`evennia.contrib.grid.barter`)
- Player shops (future)
- Trade agreements
- Gifts

### Resource Scarcity Levels

| Level | Examples | Availability |
|-------|----------|--------------|
| Abundant | Wood, stone, water | Everywhere, fast respawn |
| Common | Iron ore, basic food | Most areas, moderate respawn |
| Uncommon | Gems, rare herbs | Specific areas, slow respawn |
| Rare | Special metals, components | Few locations, very slow respawn |
| Very Rare | Magical materials | Events, unique locations |

### Economic Balance Checklist
For each new item/resource:
- [ ] Clear gathering method defined
- [ ] Time cost to gather documented
- [ ] Uses in crafting identified
- [ ] Consumption/degradation rate set
- [ ] Trade value relative to other items
- [ ] No infinite loops (Aâ†’Bâ†’A)

### Anti-Stagnation Design

âŒ **Don't create:**
- Items that last forever with no sink
- Resources with no purpose
- Infinite resource spawns

âœ… **Do create:**
- Degradation and wear systems
- Multiple uses for each resource
- Regenerating but rate-limited resources
- Consumables as primary goods

---

## Currency Handler Design

Prepared for future crypto integration:

```python
class CurrencyHandler:
    """Handles in-game currency operations."""
    
    DENOMINATIONS = {
        'gold': 10000,    # 1 gold = 10000 copper
        'silver': 100,    # 1 silver = 100 copper
        'copper': 1       # Base unit
    }
    
    def add(self, character, denomination, amount, source="crypto_exchange"):
        """
        Mint currency onto a character. This is a CREATION primitive and must
        only be called for legitimate mint sources. Player-to-player movement
        (trade, barter, rent) is a transfer with a matching decrement and does
        NOT go through add() — it belongs in a separate transfer path.

        Args:
            character: Character receiving currency
            denomination: 'gold', 'silver', or 'copper'
            amount: Amount to add
            source: "crypto_exchange" (the sole mint point) or "faucet"
                (temple redistribution of exchange-minted gold). "admin" is
                permitted only as an audited, exceptional bug-correction tag —
                never as a normal economic source.
        """
        if amount < 0:
            return False
        
        # Log all currency creation (critical for crypto auditing)
        self._log_transaction(character, denomination, amount, source)
        
        # Add to character
        current = character.db.currency.get(denomination, 0)
        character.db.currency[denomination] = current + amount
        return True
    
    def _log_transaction(self, character, denomination, amount, source):
        """Log for future crypto auditing."""
        import time
        log_entry = {
            'timestamp': time.time(),
            'character': character.key,
            'denomination': denomination,
            'amount': amount,
            'source': source
        }
        # Store in persistent transaction log
```

---

## Development Phases

### Phase 1 - MVP (No Crypto)
- Full economy with currency system
- Temple-faucet for initial funding
- Test economic balance
- Prove player-driven economy works

### Phase 2 - GameGold Launch (1-2 months before game)
- Launch blockchain independently
- Community mining/staking
- Establish initial distribution
- Test exchange mechanics privately

### Phase 3 - Integration
- Connect exchange system to game
- Crypto â†’ gold conversion
- Gold â†’ crypto withdrawal
- Monitor economic impact

---

## Economic Monitoring

### Metrics to Track
```python
def get_economy_stats():
    """Calculate economic health metrics."""
    return {
        'total_gold_supply': calculate_total_gold(),
        'gold_by_source': {
            'crypto_exchange': 0,  # Future
            'faucet': sum_faucet_gold(),
            'admin': sum_admin_gold(),
        },
        'active_trades_24h': count_recent_trades(),
        'average_item_prices': calculate_price_averages(),
        'gold_velocity': calculate_velocity(),  # How fast gold moves
    }
```

### Warning Signs
- ðŸš¨ Gold accumulating (not circulating)
- ðŸš¨ Essential items unavailable
- ðŸš¨ Price deflation (gold too valuable)
- ðŸš¨ Price inflation (gold worthless)
- ðŸš¨ Monopolies forming

---

## Legal Considerations

### Swedish AB Formation
- **Purpose**: Liability protection, tax optimization
- **Scope**: GameGold operations only
- **Timeline**: Before GameGold launch
- **Note**: Game itself remains hobby project

### Security Requirements (Future)
- Secure exchange API
- Transaction verification
- Rate limiting
- Fraud detection
- Audit logging
- Rollback capability
