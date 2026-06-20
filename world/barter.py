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
    TradeTimeout as BaseTradeTimeout,
)


class MongooseTradeTimeout(BaseTradeTimeout):
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


# CmdTrade.func does `part_a.scripts.add(TradeTimeout)`, resolving the name
# `TradeTimeout` from this contrib module's globals at call time. Reassigning
# it here transparently makes the unmodified func start OUR corrected script.
barter_module.TradeTimeout = MongooseTradeTimeout
