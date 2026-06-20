"""
PolishedWorld barter hardening layer.

Thin subclasses over Evennia's barter contrib that fix confirmed upstream
bugs WITHOUT forking the contrib's ~95-line command logic. We reuse the
contrib's CmdTrade.func unchanged and only swap in corrected helper classes
by reassigning the module globals that func resolves at call time.

CmdTrade is re-exported here so that routing the cmdset import through this
module is what loads it (and runs the monkeypatch) at server start.

Task 2.1: MongooseTradeTimeout
    Upstream TradeTimeout reads ndb.tradeevent, which is never assigned
    anywhere (the handler is stored as ndb.tradehandler). Result: a timed-out
    invite is never cleaned up and the inviter is left in a phantom trade.
"""

from evennia.contrib.game_systems.barter import barter as barter_module
from evennia.contrib.game_systems.barter.barter import (
    CmdTrade as CmdBaseTrade,
    CmdAccept as CmdBaseAccept,
    TradeHandler as BaseTradeHandler,
    TradeTimeout as BaseTradeTimeout,
)


class PWTradeTimeout(BaseTradeTimeout):
    """Times out an unanswered trade *invite* and tears it down correctly."""

    def at_repeat(self):
        # The handler lives on the inviting object as `tradehandler`, not the
        # never-set `tradeevent` upstream looks for. Only time out while the
        # invite is still pending: once the trade has started there is no
        # timeout (parties decline/finish manually), so we must NOT finish it.
        handler = self.obj.ndb.tradehandler
        if handler and not handler.trade_started:
            handler.finish(force=True)
            self.obj.msg("Trade request timed out.")

    def is_valid(self):
        handler = self.obj.ndb.tradehandler
        return bool(handler) and not handler.trade_started


class CmdPWTrade(CmdBaseTrade):
    """
    Trade entry command with the bare-'trade' crash fixed.

    Upstream's no-args branch reads self.caller.ndb.tradeevent.trade_started,
    but ndb.tradeevent is never assigned -> AttributeError whenever you type
    'trade' while already holding a tradehandler. We handle that one branch
    here (reading the real attribute, tradehandler) and delegate every other
    case to the unmodified upstream func.
    """

    def func(self):
        if not self.args:
            handler = self.caller.ndb.tradehandler
            if handler and handler.trade_started:
                self.caller.msg("You are already in a trade. Use 'end trade' to abort it.")
            else:
                self.caller.msg("Usage: trade <other party> [accept|decline] [:emote]")
            return
        return super().func()


class PWTradeHandler(BaseTradeHandler):
    """
    TradeHandler with an ownership re-validation guard at completion.

    Upstream finish() moves every offered object with `obj.location = ...`
    without re-checking that the object is still in the offerer's possession.
    The trade cmdset is *added* (not Replace), so drop/give/eat stay available
    during a trade: a party can offer an item, the other accepts, then the
    offerer disposes of that item before the final accept lands. Upstream would
    then teleport the item from wherever it now is to the recipient -- a
    dupe/loss vector in a player-driven economy.

    We re-validate only on a *voluntary* completion (force=False). A forced
    teardown (timeout, decline, 'end trade') must always be able to clean up,
    so we never block it.
    """

    def finish(self, force=False):
        if (
            not force
            and self.trade_started
            and self.part_a_accepted
            and self.part_b_accepted
        ):
            a_ok = all(obj.location == self.part_a for obj in self.part_a_offers)
            b_ok = all(obj.location == self.part_b for obj in self.part_b_offers)
            if not (a_ok and b_ok):
                # An offered item left its owner's hands between the offer and the
                # final accept. Cancel the whole trade: drop the accepts so super()
                # moves nothing, then force a full teardown -- otherwise the stale
                # item stays on offer and every re-accept just re-aborts forever.
                self.part_a_accepted = False
                self.part_b_accepted = False
                msg = "Trade cancelled: an offered item is no longer available."
                self.part_a.msg(msg)
                self.part_b.msg(msg)
                return super().finish(force=True)
        return super().finish(force=force)


class CmdPWAccept(CmdBaseAccept):
    """
    Accept command with an ownership re-validation guard.

    CmdAccept has only two outcomes ('deal made' / 'must also accept'), driven
    purely by finish()'s boolean, so a stale-item cancel can't be expressed via
    the handler's return value. We intercept the *completing* accept here: if
    an offered item has left its owner's hands, cancel cleanly and emit a single
    'Trade cancelled' instead of letting the contrib print a misleading message.
    """

    def func(self):
        caller = self.caller
        if not self.trade_started:
            caller.msg("Wait until the other party has accepted to trade with you.")
            return

        handler = self.tradehandler
        # Does this accept complete the deal (i.e. has the other party already
        # accepted)? Only then is the swap imminent and worth re-validating.
        other_already_accepted = (
            handler.part_b_accepted
            if caller == handler.part_a
            else handler.part_a_accepted
        )
        if other_already_accepted:
            a_ok = all(o.location == handler.part_a for o in handler.part_a_offers)
            b_ok = all(o.location == handler.part_b for o in handler.part_b_offers)
            if not (a_ok and b_ok):
                msg = "Trade cancelled: an offered item is no longer available."
                handler.part_a.msg(msg)
                handler.part_b.msg(msg)
                # Reset accepts so the forced teardown moves nothing.
                handler.part_a_accepted = False
                handler.part_b_accepted = False
                handler.finish(force=True)
                return

        return super().func()


# CmdTrade.func does `part_a.scripts.add(TradeTimeout)`, resolving the name
# `TradeTimeout` from this contrib module's globals at call time. Reassigning
# it here transparently makes the unmodified func start OUR corrected script.
barter_module.TradeTimeout = PWTradeTimeout
barter_module.TradeHandler = PWTradeHandler
barter_module.CmdAccept = CmdPWAccept
