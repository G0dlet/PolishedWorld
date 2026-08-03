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

Stage 4 Component E.1: the currency clause on `offer`
    Coin reaches the trade table as a NUMBER ON THE TRADE HANDLER, never as an
    object (decomposition S4-2: the wallet is a single Copper int and there are
    no coin objects in Stage 4). Registering an offer moves no money at all --
    it is bookkeeping. Settlement happens in finish() (E.2), which is why a
    forced teardown needs no refund path: there was never anything to refund.
"""

from evennia.contrib.game_systems.barter import barter as barter_module
from evennia.contrib.game_systems.barter.barter import (
    CmdTrade as CmdBaseTrade,
    CmdOffer as CmdBaseOffer,
    CmdAccept as CmdBaseAccept,
    CmdDecline as CmdBaseDecline,
    CmdEvaluate as CmdBaseEvaluate,
    CmdStatus as CmdBaseStatus,
    TradeHandler as BaseTradeHandler,
    TradeTimeout as BaseTradeTimeout,
)

from world.currency import format_copper, parse_amount


def _all_offers_in_hand(handler):
    """True if every offered item is still in its offerer's possession AND unworn.

    Two ways an offer goes stale between the offer and the final accept:
      * the item left the offerer's inventory (drop/give/eat) -> location check.
      * the item was *worn* after being offered -> worn check. A worn garment
        keeps location == owner, so the location check alone misses it and
        finish() would teleport a worn item off the body.

    Worn-ness is read as truthy db.worn, matching the clothing contrib's own
    test (db.worn is True or a wearstyle string when worn; None/False otherwise).

    NOTE this covers ITEMS only. Offered currency needs its own sibling guard,
    `_offered_currency_still_held()` (E.2), because money has no location and
    cannot be checked the same way.
    """
    for offers, owner in (
        (handler.part_a_offers, handler.part_a),
        (handler.part_b_offers, handler.part_b),
    ):
        for obj in offers or ():
            if obj.location != owner or obj.db.worn:
                return False
    return True


def _offered_currency(handler, party):
    """The Copper amount `party` currently has on the table, 0 if none.

    Read through getattr with a default so that any code path holding a plain
    upstream TradeHandler (a test that instantiates the contrib class directly,
    or a future Evennia change) degrades to "no coin offered" rather than
    raising. Every read of the two currency fields goes through here for that
    reason.
    """
    if party == handler.part_a:
        return getattr(handler, "part_a_currency", 0) or 0
    if party == handler.part_b:
        return getattr(handler, "part_b_currency", 0) or 0
    return 0


def _describe_offer(objs, coin, verb):
    """Render '<verb> <items>, plus <coin> in coin' for the offer messages.

    Split out because the same sentence is built twice (once for the offerer,
    once for the other party) and a phrasing that drifts between the two copies
    reads to players as the two of them seeing different deals.

    The items half reproduces upstream's "a, b and c" join exactly; the coin
    half is joined with ", plus " rather than a third "and", because
    "sword and shield and 5 Silver in coin" parses as three items on first read.
    """
    parts = []
    if objs:
        if len(objs) > 1:
            parts.append(
                ", ".join("|w%s|n" % obj.key for obj in objs[:-1])
                + " and |w%s|n" % objs[-1].key
            )
        else:
            parts.append("|w%s|n" % objs[0].key)
    if coin:
        parts.append("|y%s|n in coin" % format_copper(coin))
    return "%s %s" % (verb, ", plus ".join(parts))


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


class CmdPWOffer(CmdBaseOffer):
    """
    offer items and/or coin in trade.

    Usage:
      offer <object> [, object2, ...] [, <amount> <denomination>] [:emote]

    Examples:
      offer iron sword
      offer iron sword, 5 silver
      offer 50 copper

    This replaces the currently standing offer in full -- including its coin.
    To take coin off the table, offer the items again without it.

    ------------------------------------------------------------------------
    WHY THIS NO LONGER DELEGATES TO super().func()  [FLAGGED DEVIATION, E.1]
    ------------------------------------------------------------------------
    Every other class in this module reuses the contrib's command logic and
    only patches around it. This one cannot. Upstream `func` returns early when
    no object resolves, which makes a coin-only offer impossible, and it calls
    `tradehandler.offer(caller, *offerobjs)` with no way to pass an amount, so a
    mixed offer would silently drop its money. Pre-washing `self.args` and
    delegating would need a second, separate message about the coin -- two
    messages for one action, which reads as the offer having happened twice.
    So `func` is reimplemented here. It keeps upstream's comma-splitting, its
    search-and-bail loop, its `str_caller`/`str_other` emote plumbing and its
    "a, b and c" item join; the ONLY additions are the currency segments.

    ------------------------------------------------------------------------
    HOW A SEGMENT IS CLASSIFIED (decomposition E.1, option A)
    ------------------------------------------------------------------------
    A comma-separated segment is COIN if its first character is an ASCII digit.
    Otherwise it is an item name and goes to `caller.search()` untouched.

    That rule is total, not heuristic, and it is worth writing down why:
    Evennia's disambiguation syntax is a SUFFIX -- SEARCH_MULTIMATCH_REGEX is
    `^(?P<name>.*?)-(?P<number>[0-9]+)...`, i.e. `copper-2`, never `2 copper`.
    So no valid way of naming an object begins with a digit, and the material
    registry's `copper` ingot (a future smelting product) cannot collide with
    the denomination: `offer copper` is the ingot, `offer 5 copper` is money,
    and no input could reasonably mean the other one.

    A digit-led segment that fails to parse gets the CURRENCY error rather than
    "Could not find '5 silvre'". This is exactly why `parse_amount()` returns
    None instead of raising -- so `offer` and `pay` can each own their wording.

    Multiple coin segments SUM (`offer 3 silver, 20 copper`). It costs one
    `+=`, touches nothing in `parse_amount`, and refusing would be arbitrary.
    Note this is NOT the compact multi-denomination parsing deferred in
    BACKLOG ("2g30s"): that is a change to the parser; this is addition.

    ------------------------------------------------------------------------
    AFFORDABILITY IS UX HERE, NOT THE GUARD
    ------------------------------------------------------------------------
    We check `can_afford` at offer time so a player is told immediately, but it
    decides nothing: money can be spent between the offer and the final accept,
    which is the same staleness `_all_offers_in_hand` guards for items. The
    real guard is at completion (E.2). Per S4-R1 this read is safe *because*
    nothing is committed on the strength of it.

    Worn clothing is still refused: a worn garment keeps location == wearer, so
    neither the contrib nor the location-based completion guard would stop it
    being traded straight off the body.
    """

    _USAGE = (
        "Usage: offer <object> [, object2, ...] [, <amount> <denomination>] [:emote]"
    )

    def func(self):
        """implement the offer"""
        caller = self.caller
        if not self.args:
            caller.msg(self._USAGE)
            return
        if not self.trade_started:
            caller.msg("Wait until the other party has accepted to trade with you.")
            return

        # ---- classify the segments ----
        itemnames = []
        coin_total = 0
        coin_seen = False
        for segment in (part.strip() for part in self.args.split(",")):
            if not segment:
                continue
            first = segment[0]
            if first.isascii() and first.isdigit():
                amount = parse_amount(segment)
                if amount is None:
                    caller.msg(
                        f"'|w{segment}|n' isn't an amount of coin I can read. Name "
                        "the denomination too, like |w5 silver|n or |w30 copper|n."
                    )
                    return
                if amount <= 0:
                    # parse_amount happily returns 0 for "0 copper" -- a fine
                    # parse and not an offerable amount. Leaving the segment out
                    # is how you offer no coin; there is no reason to also
                    # accept a way of saying it that looks like a mistake.
                    caller.msg(
                        "Offering nothing is not an offer. Leave the coin out instead."
                    )
                    return
                coin_total += amount
                coin_seen = True
            else:
                itemnames.append(segment)

        if not itemnames and not coin_seen:
            # Reachable with input that is all separators, e.g. "offer ,,,".
            caller.msg(self._USAGE)
            return

        # ---- resolve the items ----
        # search() emits its own miss and multimatch messages, so a falsy result
        # is already fully reported to the player and we just stop.
        offerobjs = []
        for offername in itemnames:
            obj = caller.search(offername)
            if not obj:
                return
            if obj.db.worn:
                caller.msg(
                    f"You can't offer {obj.get_display_name(caller)} "
                    "while you're wearing it \u2014 remove it first."
                )
                return
            offerobjs.append(obj)

        # ---- coin sanity, as UX only ----
        if coin_total:
            wallet = getattr(caller, "currency", None)
            if wallet is None:
                caller.msg("You have no coin to offer.")
                return
            if not wallet.can_afford(coin_total):
                caller.msg(
                    "You don't have that much on you; your purse holds "
                    f"|y{wallet.format()}|n."
                )
                return

        # One call, one complete standing offer. Routing the amount through
        # handler.offer() rather than writing the field from here is what keeps
        # the contrib's "changing an offer resets both accepts" invariant true
        # for a coin-only change as well.
        self.tradehandler.offer(caller, *offerobjs, currency=coin_total)

        caller.msg(self.str_caller % _describe_offer(offerobjs, coin_total, "You offer"))
        self.msg_other(
            caller, self.str_other % _describe_offer(offerobjs, coin_total, "They offer")
        )


class CmdPWDecline(CmdBaseDecline):
    """
    decline the standing offer, counting coin as an offer.

    Upstream's emptiness gate reads `tradehandler.list()`, which returns the two
    ITEM lists only:

        offer_a, offer_b = self.tradehandler.list()
        if not offer_a or not offer_b:
            caller.msg("No offers have been made yet, ...")

    A coin-only offer leaves that side's item list empty, so from E.1 onward
    upstream would refuse to decline a deal that visibly exists -- and would say
    "no offers have been made yet" while `status` shows the money on the table.
    The rest of the body is reproduced from the contrib unchanged; only the
    emptiness gate differs.
    """

    def func(self):
        """decline the offer"""
        caller = self.caller
        if not self.trade_started:
            caller.msg("Wait until the other party has accepted to trade with you.")
            return

        handler = self.tradehandler
        offer_a, offer_b = handler.list()
        a_has_offer = bool(offer_a) or bool(_offered_currency(handler, handler.part_a))
        b_has_offer = bool(offer_b) or bool(_offered_currency(handler, handler.part_b))
        if not a_has_offer or not b_has_offer:
            caller.msg("No offers have been made yet, so there is nothing to decline.")
            return

        if handler.decline(caller):
            # changed a previous accept
            caller.msg(self.str_caller % "You change your mind, |Rdeclining|n the current offer.")
            self.msg_other(
                caller,
                self.str_other
                % "%s changes their mind, |Rdeclining|n the current offer."
                % caller.key,
            )
        else:
            # no acceptance to change
            caller.msg(self.str_caller % "You |Rdecline|n the current offer.")
            self.msg_other(caller, self.str_other % "%s declines the current offer." % caller.key)


class CmdPWStatus(CmdBaseStatus):
    """
    show a list of the current deal, including coin on each side.

    ⚠️ THE COIN LINE MUST NOT CARRY A NUMBER. The numbers in this table are the
    indices `evaluate <nr>` feeds to `TradeHandler.search(index)`, which indexes
    `part_a_offers + part_b_offers` -- items only. Numbering coin into the list
    would silently shift every index after it, so `eval 2` would show the wrong
    object. The coin line is therefore rendered unnumbered and indented under
    its owner's items.

    When neither side offers coin this produces output byte-identical to the
    contrib's, which is a cheap and load-bearing regression property: it means
    the patch cannot have quietly changed the item table.

    The rest is reproduced from the live contrib rather than reconstructed --
    including the `"".join()` over a plain string in the empty case, which works
    because joining a string's characters with "" returns the string.
    """

    def func(self):
        """Show the current deal"""
        caller = self.caller
        handler = self.tradehandler
        part_a_offers, part_b_offers = handler.list()

        count = 1
        part_a_offerlist = []
        for offer in part_a_offers:
            part_a_offerlist.append("\n |w%i|n %s" % (count, offer.key))
            count += 1
        part_b_offerlist = []
        for offer in part_b_offers:
            part_b_offerlist.append("\n |w%i|n %s" % (count, offer.key))
            count += 1

        part_a_coin = _offered_currency(handler, self.part_a)
        part_b_coin = _offered_currency(handler, self.part_b)
        if part_a_coin:
            part_a_offerlist.append("\n   + |y%s|n in coin" % format_copper(part_a_coin))
        if part_b_coin:
            part_b_offerlist.append("\n   + |y%s|n in coin" % format_copper(part_b_coin))

        if not part_a_offerlist:
            part_a_offerlist = "\n <nothing>"
        if not part_b_offerlist:
            part_b_offerlist = "\n <nothing>"

        string = "|gOffered by %s:|n%s\n|yOffered by %s:|n%s" % (
            self.part_a.key,
            "".join(part_a_offerlist),
            self.part_b.key,
            "".join(part_b_offerlist),
        )
        accept_a = handler.part_a_accepted and "|gYes|n" or "|rNo|n"
        accept_b = handler.part_b_accepted and "|gYes|n" or "|rNo|n"
        string += "\n\n%s agreed: %s, %s agreed: %s" % (
            self.part_a.key,
            accept_a,
            self.part_b.key,
            accept_b,
        )
        string += "\n Use 'offer', 'eval' and 'accept'/'decline' to trade. See also 'trade help'."
        caller.msg(string)


class PWTradeHandler(BaseTradeHandler):
    """
    TradeHandler with an ownership re-validation guard at completion, and with
    each side's offered coin recorded as an integer.

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

    ---- CURRENCY (E.1) ----
    `part_a_currency` / `part_b_currency` hold Copper integers. NO WALLET IS
    TOUCHED when they are set: offering coin is a promise, not a payment, which
    is the whole reason S4-2's handler-level bridge beats materialising coin
    objects. It also answers the forced-teardown question outright -- there is
    nothing to refund on decline, timeout or disconnect, because nothing left
    anyone's purse. The fields are still zeroed in the cleanup path alongside
    `part_a_offers = None`, so a handler someone still holds a reference to
    after teardown reads as empty rather than as a live promise of coin.
    """

    def __init__(self, part_a, part_b):
        super().__init__(part_a, part_b)
        # Declared here rather than left to getattr defaults so that `examine`
        # and a debugger show the fields on every handler, including the ones
        # where no coin is ever offered.
        self.part_a_currency = 0
        self.part_b_currency = 0

    def offer(self, party, *args, currency=0):
        """
        Change the standing offer, items and coin together.

        super() is called FIRST on purpose: it owns the party validation (it
        raises ValueError for a stranger) and the reset of both accepts. If it
        raises, no currency has been written, so a bad call cannot leave the
        handler holding coin for a party that is not in the trade.

        Args:
            party (object): who is making the offer.
            args (Object): the offered items.
            currency (int): amount in Copper, 0 for none. A call with no
                `currency` kwarg clears any coin previously on that side --
                correct, because an offer replaces the standing offer whole.
        """
        if isinstance(currency, bool) or not isinstance(currency, int):
            raise TypeError(
                f"currency must be an int, got {type(currency).__name__}: {currency!r}"
            )
        if currency < 0:
            raise ValueError(f"currency cannot be negative, got {currency}")

        super().offer(party, *args)

        if self.trade_started:
            if party == self.part_a:
                self.part_a_currency = currency
            elif party == self.part_b:
                self.part_b_currency = currency

    def finish(self, force=False):
        if (
            not force
            and self.trade_started
            and self.part_a_accepted
            and self.part_b_accepted
        ):
            if not _all_offers_in_hand(self):
                # An offered item left its owner's hands between the offer and the
                # final accept. Cancel the whole trade: drop the accepts so super()
                # moves nothing, then force a full teardown -- otherwise the stale
                # item stays on offer and every re-accept just re-aborts forever.
                self.part_a_accepted = False
                self.part_b_accepted = False
                msg = "Trade cancelled: an offered item is no longer available."
                self.part_a.msg(msg)
                self.part_b.msg(msg)
                return self._finish_and_clear(force=True)
        return self._finish_and_clear(force=force)

    def _finish_and_clear(self, force=False):
        """super().finish(), plus zeroing the coin fields on a real teardown.

        Kept separate because finish() has two exit paths and the clearing must
        happen on both without being written twice. super() returns True only
        when it actually tore the trade down; a False return means nothing
        happened and the standing offer -- coin included -- must survive intact.
        """
        result = super().finish(force=force)
        if result:
            self.part_a_currency = 0
            self.part_b_currency = 0
        return result


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
            if not _all_offers_in_hand(handler):
                msg = "Trade cancelled: an offered item is no longer available."
                handler.part_a.msg(msg)
                handler.part_b.msg(msg)
                # Reset accepts so the forced teardown moves nothing.
                handler.part_a_accepted = False
                handler.part_b_accepted = False
                handler.finish(force=True)
                return

        return super().func()


class CmdPWEvaluate(CmdBaseEvaluate):
    """
    Evaluate command that shows an offered item's LIVE description.

    Upstream CmdEvaluate.func ends with `caller.msg(offer.db.desc)` -- the
    static desc Attribute -- bypassing get_display_desc. So an item whose real,
    player-facing description is rendered dynamically shows its stale prototype
    desc in a trade instead. It bites hardest on the Stage 3 knowledge carriers:
    a stamped scroll evaluates as "a blank scroll" and a scribed book as "a
    blank book", hiding the very recipes -- and, for the perishable book, the
    CONDITION -- a buyer needs to value the offer. In a player-driven economy the
    trade window must show what `look` shows.

    We reproduce upstream's index/name resolution unchanged and only swap the
    final render to get_display_desc(caller) -- the same dynamic path look and
    inventory use -- with a db.desc fallback for objects that don't override it.
    """

    def func(self):
        caller = self.caller
        if not self.args:
            caller.msg("Usage: evaluate <offered object>")
            return
        # Accept a 1-based index too, exactly as upstream does (the offer list in
        # `status` is 1-based).
        try:
            self.args = int(self.args) - 1
        except Exception:
            pass

        offer = self.tradehandler.search(self.args)
        if not offer:
            caller.msg("No offer matching '%s' was found." % self.args)
            return

        # Live, player-facing description -- the same get_display_desc that look
        # and inventory use -- so a stamped scroll/book shows its real recipes and
        # current condition, not the prototype's "blank" desc. Fallback to the
        # static desc for any object without a meaningful override.
        caller.msg(
            offer.get_display_desc(caller)
            or offer.db.desc
            or "You see nothing special."
        )


# CmdTrade.func does `part_a.scripts.add(TradeTimeout)`, resolving the name
# `TradeTimeout` from this contrib module's globals at call time. Reassigning
# it here transparently makes the unmodified func start OUR corrected script.
# CmdsetTrade.at_cmdset_creation resolves CmdOffer/CmdAccept/CmdDecline/
# CmdEvaluate/CmdStatus the same way at trade-start, so swapping these globals
# injects our corrected commands.
barter_module.TradeTimeout = PWTradeTimeout
barter_module.TradeHandler = PWTradeHandler
barter_module.CmdOffer = CmdPWOffer
barter_module.CmdAccept = CmdPWAccept
barter_module.CmdDecline = CmdPWDecline
barter_module.CmdEvaluate = CmdPWEvaluate
barter_module.CmdStatus = CmdPWStatus
