# Barter (player-to-player trading)

Item-for-item trading that closes the player-driven economy loop:
**forage → craft → consume → trade**. Built on Evennia's barter contrib
(`evennia.contrib.game_systems.barter`) with a thin hardening layer in
`world/barter.py`. No currency: coins, when added, are just tradeable objects,
so nothing here needs to change for them.

## Where things live

- `world/barter.py` — the hardening layer (four thin subclasses + three
  module-global patches). Importing this module is what installs the patches.
- `commands/default_cmdsets.py` — `CharacterCmdSet` adds `CmdPWTrade`, the trade
  entry command. The import is routed through `world.barter` so that loading the
  cmdset also installs the patches at server start.

## In-game commands

Entry: `trade <other> [accept|decline] [:emote]`. Once a trade starts, both
parties gain: `offer <obj>[, obj2 ...][:emote]`, `accept` (alias `agree`),
`decline`, `evaluate <obj>` (alias `eval`), `status` (aliases `offers`/`deal`),
`end trade` (alias `finish trade`), `trade help`.

## Why a custom layer exists

The contrib's command logic is reused unchanged. We subclass the affected
helpers and reassign the contrib's module globals (`TradeTimeout`,
`TradeHandler`, `CmdAccept`), which the unmodified contrib resolves at call
time, so our corrected versions are picked up without forking it.

| Class (`world/barter.py`) | Upstream bug it fixes |
|---|---|
| `PWTradeTimeout` | `TradeTimeout` reads `ndb.tradeevent`, which is never assigned (the handler is stored as `ndb.tradehandler`). A timed-out invite was never cleaned up, leaving the inviter stuck in a phantom trade. Also guards on `not trade_started`, so it only times out a still-pending invite and never force-finishes an in-progress one. |
| `CmdPWTrade` | Typing `trade` with no args while holding a tradehandler hit `None.trade_started` (same `tradeevent` typo) → AttributeError crash. Only the no-args branch is overridden; everything else delegates to the upstream command. |
| `CmdPWAccept` | The real ownership re-validation. `finish()` moves offered items via direct `obj.location =` with no ownership check, and the trade cmdset is *added* (not Replace), so `drop`/`give`/`eat` stay available mid-trade. A party could offer an item, the other accepts, then the offerer disposes of it before the final accept — and upstream would teleport it from its new location to the recipient. We intercept the *completing* accept: if any offered item has left its owner's hands, the trade is cancelled cleanly (one message to both, full teardown, no goods moved). |
| `PWTradeHandler` | `finish()` is reduced to a safety net: it refuses to move a stale item (returns `False` without moving) for any direct/programmatic caller that bypasses the command path. |

### Why the staleness check is at accept-time, not in finish()

`CmdAccept` has only two outcomes — "deal made" or "must also accept" — and they
are chosen purely by `finish()`'s boolean. There is no "cancelled" outcome, so a
finish()-based cancel made `CmdAccept` print "Deal is made and goods changed
hands" even when nothing moved. The check therefore lives in `CmdPWAccept`, which
can cancel without invoking the contrib's messaging. The single-threaded reactor
guarantees the check and the swap happen in one synchronous command, so nothing
can change between validation and the move.

## Known, deliberate MVP debt

The actual item move still uses upstream's direct `obj.location =` (via
`super().finish()`), which bypasses move hooks and `get` locks. This is harmless
for current items (no item relies on move hooks during a trade). The upgrade to
`move_to(quiet=True)` is deferred to pair with the future **no-trade flag**
(quest-bound / worn items), where lock enforcement during a trade actually
matters.

## Maintenance / fragility

The hardening relies on the contrib resolving `TradeTimeout`, `TradeHandler` and
`CmdAccept` from its module globals at call time. If a future Evennia version
renames these or stops referencing them as module globals, the patches silently
become no-ops. Pin Evennia, and keep the two-session integration test as a
regression alarm (it exercises the timeout, the bare-`trade` guard, and the
stale-offer cancel in real play — paths the `@py` unit tests cannot reach).
