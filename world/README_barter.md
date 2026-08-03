# Barter (player-to-player trading)

Trading that closes the player-driven economy loop:
**forage → craft → consume → trade**. Built on Evennia's barter contrib
(`evennia.contrib.game_systems.barter`) with a thin hardening layer in
`world/barter.py`.

**Currency is included, and it is not an object.** A wallet is a single Copper
`int` (S4-2) and Stage 4 ships no coin objects at all, so coin reaches the trade
table as a number recorded on the trade handler — never as goods. See
*Currency on the table* below.

## Where things live

- `world/barter.py` — the hardening layer (seven thin subclasses + seven
  module-global patches). Importing this module is what installs the patches.
- `commands/default_cmdsets.py` — `CharacterCmdSet` adds `CmdPWTrade`, the trade
  entry command, and **nothing else**. Every other trade command belongs to
  `CmdsetTrade`, which the contrib attaches at trade start and deletes at
  teardown. The import is routed through `world.barter` so that loading the
  cmdset also installs the patches at server start.

## In-game commands

Entry: `trade <other> [accept|decline] [:emote]`. Once a trade starts, both
parties gain: `offer <obj>[, obj2 ...][, <amount> <denomination>][:emote]`,
`accept` (alias `agree`), `decline`, `evaluate <obj>` (alias `eval`), `status`
(aliases `offers`/`deal`), `end trade` (alias `finish trade`), `trade help`.

## Currency on the table

- **Syntax.** A comma-segment whose first character is an ASCII digit is coin;
  everything else is an item name. The rule is total rather than heuristic
  because Evennia's disambiguation syntax is a *suffix* (`copper-2`), so no
  valid way of naming an object begins with a digit — which is also why the
  material registry's future `copper` ingot cannot collide with the
  denomination. Multiple coin segments sum. A digit-led segment that fails to
  parse gets the currency error, not "Could not find".
- **Offering moves no money.** The amount lives on the handler as
  `part_a_currency` / `part_b_currency`. An offer is a promise, which is why a
  forced teardown (decline, timeout, disconnect) needs no refund path.
- **Settlement is in `finish()`**, and it has to be: `finish()` assigns
  `obj.location` directly, so no move hook fires and there is nothing to hang
  off. Guarded by a one-shot flag (S4-R3).
- **Gross check, net transfer.** Each side is re-validated against what it
  *promised*; the money moves as a single netted `transfer_to`. Two transfers
  could half-settle; one cannot. The messages are built from the promised
  amounts, because the players agreed in gross and netting is an implementation
  detail that must not leak into the language.
- **Not ledgered** (S4-4): a settlement is a transfer, not a mint or a burn.

## Why a custom layer exists

The contrib's command logic is reused unchanged wherever possible. We subclass
the affected helpers and reassign the contrib's module globals, which the
unmodified contrib resolves at call time, so our corrected versions are picked
up without forking it.

| Class (`world/barter.py`) | What it fixes or adds |
|---|---|
| `PWTradeTimeout` | `TradeTimeout` reads `ndb.tradeevent`, which is never assigned (the handler is stored as `ndb.tradehandler`). A timed-out invite was never cleaned up, leaving the inviter stuck in a phantom trade. Also guards on `not trade_started`, so it only times out a still-pending invite and never force-finishes an in-progress one. |
| `CmdPWTrade` | Typing `trade` with no args while holding a tradehandler hit `None.trade_started` (same `tradeevent` typo) → AttributeError crash. Only the no-args branch is overridden. |
| `CmdPWOffer` | Adds the currency clause, and refuses to offer worn clothing (a worn garment keeps `location == wearer`, so no location-based guard would catch it). ⚠️ The one class that does **not** delegate to upstream's `func`: upstream returns early when no object resolves, making a coin-only offer impossible, and has no way to pass an amount. Reason recorded in the class docstring. |
| `CmdPWAccept` | Ownership and solvency re-validation on the *completing* accept, for the wording's sake — see below. |
| `CmdPWDecline` | Upstream's emptiness gate reads `list()`, which returns the two **item** lists only, so a coin-only offer reads as "no offers have been made yet" while `status` shows the money. The gate is widened, not removed. |
| `CmdPWEvaluate` | Upstream renders `offer.db.desc`, the static Attribute, bypassing `get_display_desc`. A dynamically-described item shows its stale prototype desc — a scribed book evaluates as "a blank book", hiding the recipes and the condition a buyer needs to value the offer. |
| `CmdPWStatus` | Renders each side's coin as an **unnumbered** line under its owner. Unnumbered is load-bearing: the numbers feed `TradeHandler.search(index)`, which indexes items only, so a numbered coin line would shift every index after it. With no coin offered the output is byte-identical to the contrib's. |
| `PWTradeHandler` | Staleness re-validation and currency settlement in `finish()`; `offer(party, *args, currency=0)` so that a coin-only change still resets both accepts. |

### Why the staleness check is in BOTH `CmdPWAccept` and `finish()`

They are not redundant; they do different jobs.

`CmdAccept` has only two outcomes — "deal made" or "must also accept" — chosen
purely by `finish()`'s boolean. There is no "cancelled" outcome, so a
finish()-only cancel makes the contrib print *"You accept the offer, X must now
also accept"* immediately before the trade dies. The command-layer guard exists
for the **wording**.

The handler-layer guard exists for **correctness**: it catches every caller that
is not a command — the timeout script, programmatic callers, `@py`.

Running both on the happy path is harmless: they are pure reads with no yield
point between them, so the answer cannot have changed.

### Why coin moves exactly when goods move

`_finish_and_clear()` computes `completing` from the *same expression* upstream
uses to decide whether to move items:

```python
self.trade_started and self.part_a_accepted and self.part_b_accepted
```

Note it does not include `force` — upstream moves goods on a forced teardown
too, if both parties are still accepted. That is why the stale-offer path resets
both accepts before forcing: the one reset stops goods *and* coin. The invariant
is structural rather than maintained by hand.

## Known, deliberate MVP debt

The item move still uses upstream's direct `obj.location =` (via
`super().finish()`), which bypasses move hooks and `get` locks. Harmless for
current items. The upgrade to `move_to(quiet=True)` is deferred to pair with the
future **no-trade flag** (quest-bound items), where lock enforcement during a
trade actually matters.

## Maintenance / fragility

The hardening relies on the contrib resolving `TradeTimeout`, `TradeHandler`,
`CmdOffer`, `CmdAccept`, `CmdDecline`, `CmdEvaluate` and `CmdStatus` from its
module globals at call time. If a future Evennia version renames these or stops
referencing them as module globals, the patches silently become **no-ops** — the
contrib keeps working, just with its own bugs. Pin Evennia.

`tests/test_barter_currency.py` asserts all seven swaps and asserts that
`CmdsetTrade()` is actually built from our classes, which is the alarm for
exactly that failure. Keep the two-session in-game protocol as well: it
exercises the timeout, the bare-`trade` guard, `pay` mid-trade and the stale
cancel in real play — paths the unit tests reach only by simulation.
