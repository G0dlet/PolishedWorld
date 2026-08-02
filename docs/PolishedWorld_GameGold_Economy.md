# PolishedWorld - GameGold & Economy Design

> **Rev 5 · 2026-08-02** — **The Temple-Faucet sketch is marked superseded now that the faucet is shipped** (Stage 4 Component D.1, `commands/work_commands.py`). Rev 4 corrected the sketch's *mint rule*; this Rev addresses what Rev 4 left standing — a sketch that a reader could still mistake for the design. Three divergences are named explicitly: the sketch lists **three** chores while the prose table above it lists **five** (the table is canonical, and the discrepancy was found while reading this document as D's task-table source — the same class of half-finished close-out that Rev 4 was itself fixing); there is **no `TempleFaucet` class**, the faucet being a command with a module-level table and payout function; and the chore **takes time**, with the entire `transfer_to` sequence inside the delayed callback because S4-R1 forbids splitting a check from its commit. The sketch is kept for its comments, with a banner saying to read it for *why* and never for *what*. The wider `CurrencyHandler` sketch remains the superseded per-denomination-dict design and its full rewrite is still **Component F's** work.

> **Rev 4 · 2026-08-02** — **The code sketches are brought into line with the shipped mint rule.** Rev 3 corrected this document's *prose* so that "Gold Creation" matched `MINT_SOURCES`, and left three *sketches* saying the opposite. The Temple-Faucet sketch called `currency.add(..., source='faucet')` — which the shipped `add()` rejects with `ValueError`, and which `tests/test_currency.py` asserts raises, because S4-1 makes the faucet a **transfer** path and `@economy mint` the single production caller of the mint primitive. The `CurrencyHandler.add()` docstring listed `"faucet"` as a valid source, and the economic-metrics sketch broke minted Gold down by a `faucet` bucket that cannot exist by construction. All three are corrected here, and the faucet sketch now shows the Treasury transfer it will actually be. Caught while reading this document as the source of Component D's task table — a reader coming for the table would have found the wrong implementation fifty lines below it. The wider `CurrencyHandler` sketch is still the superseded per-denomination-dict design (S4-2 stores one Copper `int`); it now carries a banner saying so, and its full rewrite remains **Component F's** work.

> **Rev 3 · 2026-07-27** — Reconciles "Gold Creation" with Stage 4's implemented `MINT_SOURCES`. Rev 2 removed the "admin gold (except events)" carve-out to match the single-mint-point principle, and that removal stands — but the shipped whitelist contains `admin_correction` alongside `crypto_exchange`, so the absolute wording needed qualifying before someone read the two documents together and concluded one of them had quietly lost. The distinction is not "admins may create gold sometimes": `admin_correction` repairs the exchange path when a settlement goes wrong, is ledgered identically to any other mint, and shows up in `@economy audit` like any other. It is the same door, used to fix the door. It is **not** a grant mechanism, and no event, reward or compensation may use it.

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
**Gold can ONLY be created via cryptocurrency exchange.**
- No NPC gold rewards
- No quest gold
- No admin gold spawning — not for events, not for rewards, not for compensation
- All gold circulates between players

**The one qualification, and its limits.** Stage 4 ships two mint sources:
`crypto_exchange` and `admin_correction` (`world/currency.py::MINT_SOURCES`).
The second is not a second door. It exists to repair the first one — a
settlement that credited the wrong amount, an exchange that half-completed — and
it is ledgered identically, counts identically in the audit invariant, and is
visible in `@economy audit` like every other mint. Anything that is not
*correcting a specific exchange transaction* is out of scope for it, including
every use the removed "except for events" carve-out once covered.

Structurally, `CurrencyHandler.add()` is the only way to create gold at all, it
refuses any source outside that whitelist, and a unit test asserts the refusal.
Everything else in the game — the temple faucet, wages, payments, trade — moves
existing gold via `transfer_to()`, which cannot change how much exists.

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

> ⚠️ **The faucet transfers. It never mints.** This is decomposition **S4-1** and
> it is enforced, not merely intended: `MINT_SOURCES` does not contain
> `"faucet"`, so `currency.add(amount, source="faucet")` raises `ValueError`,
> and `tests/test_currency.py` asserts that it does. Gold enters the world at
> exactly one point — the exchange path, reached in Stage 4 through
> `@economy mint`, which mints a bootstrap tranche into the **Treasury** against
> a recorded GameGold reserve obligation. The temple then pays players out of
> that balance. A minting faucet would be an unbounded money supply whose
> failure stays invisible until the inflation is obvious.

> ⚠️ **This sketch is superseded by the shipped implementation** (Stage 4
> Component D.1, `commands/work_commands.py`). It is kept because its comments
> carry the reasoning; read it for *why*, never for *what*. Three differences
> that matter, all recorded when D closed:
>
> * **The table above is the source of truth, not the sketch below.** The sketch
>   lists three chores; the table lists five. The shipped `TEMPLE_TASKS` has all
>   five, and each entry also carries a `duration` and four flavour strings
>   (actor and room, at start and at finish) — the house keeps flavour with the
>   data, as `eat` does with `consume_message`.
> * **There is no `TempleFaucet` class.** The faucet is a command, `work`, with
>   a module-level task table and a module-level payout function. No object
>   holds faucet state; the Treasury holds the money and the character holds
>   the cooldowns.
> * **The chore takes time.** `work` messages, waits `duration` real seconds via
>   `utils.delay`, and only then pays. The whole `transfer_to` sequence runs
>   *inside* the delayed callback — S4-R1 forbids splitting a check from its
>   commit, and a split here would be seconds wide. See Evennia Reference §11.27
>   for the cancellation pattern that makes this safe.

```python
class TempleFaucet:
    """Pays small Copper amounts for simple tasks, out of the Treasury."""

    # ⚠️ THREE OF FIVE. The prose table above is canonical; the shipped
    # TEMPLE_TASKS in commands/work_commands.py carries all five chores plus
    # a duration and flavour text for each.
    TASKS = {
        'sweep_floor': {'copper': 25, 'cooldown': 3600},
        'fetch_water': {'copper': 35, 'cooldown': 3600},
        'organize_books': {'copper': 50, 'cooldown': 7200},
    }

    def complete_task(self, character, task_name):
        """Pay a character for completing a temple task."""
        task = self.TASKS.get(task_name)
        if not task:
            return False

        # Check cooldown. Real wall-clock seconds: this throttles player
        # action spam, which is a real-time phenomenon, not a game-time one.
        cooldown_key = f"faucet_{task_name}"
        if character.cooldowns.get(cooldown_key):
            return False

        # typeclasses/treasury.py::get_treasury(). Returns None whenever
        # TREASURY_DBREF is unset or unresolvable, and every consumer must
        # handle that rather than assume — an un-endowed temple is a
        # supported state, not an error.
        treasury = get_treasury()
        if treasury is None:
            return False

        # THE PAYOUT: a transfer, not a mint. The amount is a plain int in
        # Copper (S4-2) — there is no denomination argument, because
        # denominations are a rendering concern. transfer_to() performs the
        # read, the check, the debit and the credit as one unbroken
        # synchronous block (S4-R1) and returns False, having moved nothing,
        # when the Treasury cannot cover the payout.
        if not treasury.currency.transfer_to(
            character, task['copper'], reason="faucet"
        ):
            # The coffers are dry. Note what is NOT done here: the cooldown is
            # deliberately left unset, so an attempt that paid nothing does not
            # cost the player their next attempt. A finite Treasury that can run
            # dry is a feature (it is diegetic, and it bounds faucet farming) —
            # but it must fail without taking something from the player.
            return False

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

> ⚠️ **Superseded sketch — do not implement from this.** It stores currency as a
> per-denomination dict; the shipped design (**S4-2**) stores a single `int`
> denominated in Copper, with denominations applied only at display and input
> time. The live implementation is `world/currency.py`, and `world/economy_log.py`
> holds the ledger and the audit invariant. This section is kept for its
> *intent* until **Component F** rewrites it against the shipped API. Where the
> two disagree, the code wins.

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
            source: must be a member of MINT_SOURCES, which ships as
                {"crypto_exchange", "admin_correction"}. Anything else
                raises ValueError.
                ⚠️ "faucet" is NOT a mint source and never was one in the
                shipped code. The temple pays by transferring out of the
                Treasury (S4-1), so a faucet payout never reaches this
                method at all.
                "admin_correction" repairs the exchange path when a
                settlement goes wrong. It is ledgered identically to any
                other mint and appears in `@economy audit` like any other:
                the same door, used to fix the door. It is not a grant
                mechanism, and no event, reward or compensation may use it.
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
        # Mint sources ONLY. The faucet is absent by construction, not by
        # omission: it transfers Treasury-held Copper and creates nothing, so
        # it can never appear in a breakdown of where money came from. The
        # shipped equivalents are economy_log.total_minted() /
        # total_burned() / net_issued(), with audit() proving the sum.
        'gold_by_source': {
            'crypto_exchange': sum_minted(source='crypto_exchange'),
            'admin_correction': sum_minted(source='admin_correction'),
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
