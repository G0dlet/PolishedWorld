"""
PolishedWorld barter hardening layer.

Thin subclasses over Evennia's barter contrib that fix confirmed upstream
bugs, and swap corrected classes in by reassigning the module globals the
contrib resolves at call time. The contrib's CmdTrade.func was reused
unchanged until Names NM-T13b, which gave CmdPWTrade its own (see below).

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

Names NM-T13: the trade's lines name each party as the reader knows them
    Every command of the trade's cmdset takes `_PerReader`, whose `parse`
    frames the lines to the other party around the caller as that party
    knows them; `end trade` is overridden for it (CmdPWFinish). The
    stale-offer line is per reader (`_stale_offer_reasons`). The activity log
    keeps keys: it is out of character.

Names NM-T13b: the `trade` command that starts a trade
    CmdPWTrade.func is the project's own: each party named as the reader
    knows them, the answer line giving a name the invitee can type in their
    room (`names.name_to_type_here`), and three contrib faults fixed -- the
    crash on `trade X accept` with no proposal, the inviter's `trade X
    decline` that never took an invitation back, and `accept`/`decline`
    found as substrings of a name.
"""

import re

from django.conf import settings
from evennia.contrib.game_systems.barter import barter as barter_module
from evennia.contrib.game_systems.barter.barter import (
    CmdTrade as CmdBaseTrade,
    CmdOffer as CmdBaseOffer,
    CmdAccept as CmdBaseAccept,
    CmdDecline as CmdBaseDecline,
    CmdEvaluate as CmdBaseEvaluate,
    CmdFinish as CmdBaseFinish,
    CmdStatus as CmdBaseStatus,
    TradeHandler as BaseTradeHandler,
    TradeTimeout as BaseTradeTimeout,
)

from evennia.utils import logger
from world import activity_log
from world import client_state
from world import names

from world import encumbrance
from world.currency import format_copper, parse_amount

# The search's own multimatch regex, compiled the way evennia/objects/manager.py
# compiles it (:28): once, at import. `offer` asks it whether a digit-led
# segment is a numbered item (`2-fiber`) before reading it as coin. Reading the
# setting rather than copying the pattern keeps the two from drifting apart.
_MULTIMATCH_REGEX = re.compile(settings.SEARCH_MULTIMATCH_REGEX, re.I + re.U)


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


def _offered_currency_still_held(handler):
    """True if each side can still cover the coin it put on the table.

    The sibling of `_all_offers_in_hand()`, and it exists for the same reason:
    an offer is made at one moment and honoured at another, and the world moves
    in between. An item can be dropped; coin can be spent (S4-R4). The check
    differs only because money has no location -- the only meaningful question
    is whether the promised sum is still covered.

    ⚠️ GROSS, NOT NET, AND DELIBERATELY SO. Each side is measured against what
    it *promised*, not against the difference that will actually change hands.
    Otherwise this passes: A offers 50 while holding 20, B offers 30, net is A
    paying 20 -- affordable, and A never backed the 50 that B accepted on.

    ⚠️ can_afford()'s own docstring forbids using it to decide that a later
    debit will succeed, and names the exception: it is safe when the check and
    the debit are one unbroken synchronous sequence. That is the case here --
    this runs inside finish(), with no yield point between it and the transfer
    (S4-R1). If settlement is ever moved out of finish(), this guard has to move
    with it or it becomes exactly the bug it was written to prevent.

    Sides offering no coin are skipped before can_afford() is reached: it calls
    _require_positive() and raises on 0, which is every ordinary trade.
    """
    for party in (handler.part_a, handler.part_b):
        amount = _offered_currency(handler, party)
        if not amount:
            continue
        wallet = getattr(party, "currency", None)
        if wallet is None or not wallet.can_afford(amount):
            return False
    return True


def _over_ceiling_after_trade(handler):
    """The parties this trade would put above their ceiling, A first (W5.1 Q5).

    Upstream's finish() moves the offers by assignment (`obj.location =`,
    barter.py:369, 371), which runs no hook, so the ceiling W2.1 enforces on
    every `move_to` is checked here, before anything moves. Each party's sum
    after the swap comes from the reader (`encumbrance.enc_after_trade`), with
    its own offer leaving and the other's arriving.

    A party is refused only when the sum after is above the ceiling AND above
    the sum before (Q4): a trade that lightens someone already over the
    ceiling -- STR drained, a load from before W2.1 -- is never refused.
    Coin is an integer, not an object, and weighs nothing (OQ5).

    Runs after `_all_offers_in_hand`, so every offered object is still with
    its offerer when this reads.
    """
    over = []
    for party, leaving, arriving in (
        (handler.part_a, handler.part_a_offers or (), handler.part_b_offers or ()),
        (handler.part_b, handler.part_b_offers or (), handler.part_a_offers or ()),
    ):
        before = encumbrance.carried_enc(party)
        after = encumbrance.enc_after_trade(party, leaving, arriving)
        ceiling = encumbrance.OVERLOAD_FACTOR * encumbrance.enc_limit(party)
        if after > ceiling and after > before:
            over.append(party)
    return over


def _stale_offer_reasons(handler):
    """{party: the line to cancel with}, or None if the deal is still honest.

    Both call sites -- PWTradeHandler.finish() and CmdPWAccept.func() -- need
    the same three checks in the same order and the same wording, so the choice
    lives here rather than being written out twice and drifting apart.

    Items are checked first only because an item leaving someone's hands is the
    older and commoner failure; neither takes precedence in any deeper sense.
    The ceiling comes last (W5.1 Q5): it reads the offers where the first
    check has just found them. The line names who cannot carry it, as each
    party knows them (Names NM-T13, NM15; lock 3 A: one's own side by one's
    own name), so each party gets their own line; the other two name nobody
    and read the same to both.
    """
    parties = (handler.part_a, handler.part_b)
    if not _all_offers_in_hand(handler):
        return dict.fromkeys(parties, "Trade cancelled: an offered item is no longer available.")
    if not _offered_currency_still_held(handler):
        return dict.fromkeys(parties, "Trade cancelled: offered coin is no longer available.")
    over = _over_ceiling_after_trade(handler)
    if over:
        return {
            reader: "Trade cancelled: %s cannot carry that much."
            % " and ".join(party.get_display_name(reader) for party in over)
            for reader in parties
        }
    return None


def _tell(reasons):
    """Send each party their own line from `_stale_offer_reasons`."""
    for party, line in reasons.items():
        party.msg(line)


class _PerReader:
    """
    The trade's lines name a party as the reader knows them (Names NM-T13,
    NM15). Mixed in first on every command of the trade's cmdset.

    The contrib's `parse` (barter.py:414-421) builds `str_other`, the frame of
    every line sent to the other party, around `caller.key`. Here it is built
    around the caller as the other party knows them, with `$You()`'s capital
    (`names.line_start`), since it starts the line. The contrib paints a
    connected speaker's name `|c`; a name carries no colour (NM11; NM-T13
    lock 2 A). The speech goes into a %-format string, so a `%` in it is
    doubled: the contrib's own frame raised TypeError on `offer 5 silver :
    100% fair`.

    `self.named` is the caller's name for the other party to read where it
    starts a sentence inside the frame (*... declines the current offer.*).
    """

    def parse(self):
        super().parse()
        caller, other = self.caller, self.other
        if other is None:
            self.named = caller.key
            return
        self.named = names.line_start(caller, other)
        frame_name = self.named.replace("%", "%%")
        if self.emote:
            said = self.emote.replace("%", "%%")
            self.str_caller = 'You say, "' + said + '"\n  [%s]'
            self.str_other = f'{frame_name} says, "{said}"\n  [%s]'
        else:
            self.str_other = f"{frame_name}:s trade action: %s"


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
    Initiate trade with another party

    Usage:
      trade <other party> [:say]
      trade <other party> accept [:say]
      trade <other party> decline [:say]

    Initiate trade with another party. The other party needs to repeat
    this command with trade accept/decline within a minute in order to
    properly initiate the trade action. You can use the decline option
    yourself if you want to retract an already suggested trade. The
    optional say part works like the say command and allows you to add
    info to your choice.
    """

    # The project's own func (Names NM-T13b; NM15). The contrib's
    # (barter.py:803-899) named both parties by key in all thirteen of its
    # lines and told the invitee to type `trade <inviter's key> accept`. Here
    # each party is named as the reader knows them, with a capital where the
    # name starts a sentence and no |c on a speaker (NM-T13 lock 2 A; NM11),
    # and the answer line gives a name the invitee can type in their room
    # (`names.name_to_type_here`, lock 1 C). Fixed on the way (locks 2-4 A):
    # `trade X accept` with no proposal from X raised AttributeError
    # (`None.join`); the inviter's `trade X decline` never took an invitation
    # back, as this help says it does (the branch tested `part_b == caller`);
    # and `accept`/`decline` were found as substrings, so a name holding
    # either was read as the keyword -- only the last word counts now. The
    # bare `trade` reads the real attribute, `tradehandler` (upstream's
    # `ndb.tradeevent` is never assigned).

    def func(self):
        caller = self.caller
        if not self.args:
            handler = caller.ndb.tradehandler
            if handler and handler.trade_started:
                caller.msg("You are already in a trade. Use 'end trade' to abort it.")
            else:
                caller.msg("Usage: trade <other party> [accept|decline] [:emote]")
            return

        args, emote = self.args.strip(), None
        if ":" in args:
            args, emote = [part.strip() for part in args.rsplit(":", 1)]
        words = args.split()
        keyword = words[-1].lower() if len(words) > 1 else None
        if keyword in ("accept", "decline"):
            args = " ".join(words[:-1])
        else:
            keyword = None

        part_a = caller
        part_b = caller.search(args)
        if not part_b:
            return
        if part_a == part_b:
            part_a.msg("You play trader with yourself.")
            return

        # The caller as part_b reads them, and part_b as the caller does.
        a_named = names.line_start(part_a, part_b)
        b_seen = part_b.get_display_name(part_a)
        selfemote = theiremote = ""
        if emote is not None:
            selfemote = f'You say, "{emote}"\n  '
            theiremote = f'{a_named} says, "{emote}"\n  '

        def to_a(text):
            part_a.msg(selfemote + text)

        def to_b(text):
            part_b.msg(theiremote + text)

        timeout = barter_module.TRADE_TIMEOUT
        mine = part_a.ndb.tradehandler
        theirs = part_b.ndb.tradehandler

        if keyword is None:
            if mine:
                # Name the party the caller is actually trading or
                # negotiating with, not the one just typed.
                other = mine.get_other(part_a).get_display_name(part_a)
                if mine.trade_started:
                    part_a.msg(
                        f"You are already in trade with {other}. You need to end trade first."
                    )
                else:
                    part_a.msg(
                        f"You are already trying to initiate trade with {other}. "
                        "You need to decline that trade first."
                    )
            elif theirs and theirs.part_b == part_a:
                # part_b has invited the caller: the same as accepting.
                theirs.join(part_a)
                to_b(f"{a_named} starts to trade with you. See |wtrade help|n for aid.")
                to_a(f"You start to trade with {b_seen}. See |wtrade help|n for aid.")
            else:
                PWTradeHandler(part_a, part_b)
                answer = names.name_to_type_here(part_b, part_a)
                to_a(f"You ask to trade with {b_seen}. They need to accept within {timeout} secs.")
                to_b(
                    f"{a_named} wants to trade with you. Use |wtrade {answer} "
                    f"accept/decline [:emote]|n to answer (within {timeout} secs)."
                )
                part_a.scripts.add(PWTradeTimeout)
            return

        if keyword == "accept":
            if mine:
                other = mine.get_other(part_a).get_display_name(part_a)
                part_a.msg(f"You are already in trade with {other}. You need to end that first.")
            elif theirs and theirs.join(part_a):
                to_b(f"{a_named} starts to trade with you. See |wtrade help|n for aid.")
                to_a(f"You start to trade with {b_seen}. See |wtrade help|n for aid.")
            else:
                part_a.msg("No trade proposal to accept.")
            return

        # decline
        if (
            mine
            and mine.part_a == part_a
            and mine.part_b == part_b
            and not mine.trade_started
        ):
            # the inviter takes the invitation back
            mine.finish(force=True)
            to_b(f"{a_named} aborted trade attempt with you.")
            to_a(f"You aborted the trade attempt with {b_seen}.")
        elif theirs and theirs.unjoin(part_a):
            to_b(f"{a_named} declines the trade")
            to_a(f"You decline trade with {b_seen}.")
        else:
            part_a.msg("No trade proposal to decline.")


class CmdPWOffer(_PerReader, CmdBaseOffer):
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
    A comma-separated segment is COIN if its first character is an ASCII digit
    AND it is not a numbered item -- that is, SEARCH_MULTIMATCH_REGEX does not
    match it. Otherwise it is an item name and goes to `caller.search()`
    untouched.

    That rule is total, not heuristic, and it is worth writing down why. The
    game's disambiguation form is a PREFIX, `2-copper` (Names NM9; settings.py,
    MULTIMATCH FORM), and the multimatch error prints it, so a player is told
    to type a digit-led name. Coin is a number, whitespace, a denomination
    (`2 copper`); a numbered item is a number, a hyphen, a name. The search's
    own regex tells the two apart, and asking it rather than copying its
    pattern keeps `offer` reading what the search reads. The material
    registry's `copper` ingot (a future smelting product) still cannot collide
    with the denomination: `offer copper` is the ingot, `offer 2-copper` the
    second ingot, `offer 5 copper` money.

    Until Names NM-T1 the form was Evennia's suffix, `copper-2`, and the rule
    was the first character alone. That rule would read `2-copper` as a
    malformed amount, which is why the regex is consulted.

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
            if (
                first.isascii()
                and first.isdigit()
                and not _MULTIMATCH_REGEX.match(segment)
            ):
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


class CmdPWDecline(_PerReader, CmdBaseDecline):
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
                % f"{self.named} changes their mind, |Rdeclining|n the current offer.",
            )
        else:
            # no acceptance to change
            caller.msg(self.str_caller % "You |Rdecline|n the current offer.")
            self.msg_other(caller, self.str_other % f"{self.named} declines the current offer.")


class CmdPWStatus(_PerReader, CmdBaseStatus):
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

        # Names NM-T13 (NM15; lock 3 A): each side as the reader knows them,
        # their own by their own name; a capital where the name starts a line.
        string = "|gOffered by %s:|n%s\n|yOffered by %s:|n%s" % (
            self.part_a.get_display_name(caller),
            "".join(part_a_offerlist),
            self.part_b.get_display_name(caller),
            "".join(part_b_offerlist),
        )
        accept_a = handler.part_a_accepted and "|gYes|n" or "|rNo|n"
        accept_b = handler.part_b_accepted and "|gYes|n" or "|rNo|n"
        string += "\n\n%s agreed: %s, %s agreed: %s" % (
            names.line_start(self.part_a, caller),
            accept_a,
            self.part_b.get_display_name(caller),
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
        # S4-R3. Declared here so it exists before any path can reach
        # settlement, including a teardown that happens before a single offer.
        self._currency_settled = False

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
            reasons = _stale_offer_reasons(self)
            if reasons:
                # An offered item left its owner's hands, or the promised coin
                # was spent, between the offer and the final accept. Cancel the
                # whole trade: drop the accepts so super() moves nothing -- and
                # note that the same reset is what makes `completing` false in
                # _finish_and_clear, so it stops the settlement too -- then
                # force a full teardown. Otherwise the stale offer stays on the
                # table and every re-accept just re-aborts forever.
                self.part_a_accepted = False
                self.part_b_accepted = False
                _tell(reasons)
                return self._finish_and_clear(force=True)
        return self._finish_and_clear(force=force)

    def _settle_currency(self, a_amount, b_amount):
        """Move the promised coin and tell both parties, exactly once.

        ⚠️ S4-R3, THE ONE-SHOT FLAG. The check lives here rather than at the
        call site so that every path into settlement is covered, however it got
        here. Note what upstream's cleanup does NOT do: it nulls part_a_offers
        but leaves `part_a_accepted` and `trade_started` True, so a second
        finish() re-enters the completion branch and only fails because
        `for obj in None` raises. Today a double settlement is prevented by that
        crash -- by accident, in someone else's code. This flag makes the
        guarantee ours.

        ⚠️ NET SETTLEMENT, GROSS MESSAGING. One transfer_to cannot half-settle
        the way two can; that is the whole reason for netting. But the players
        agreed in gross ("I pay 50, I get 30"), and that is what `status` showed
        them, so the messages are built from the promised amounts. A player told
        "you receive 20" after agreeing to 30 would rightly believe the game had
        miscounted. Netting is an implementation detail and must not leak into
        the language.

        S4-4: transfers are not ledgered. With no transaction log these two
        messages are the only evidence the payment happened, which is why they
        exist at all rather than letting "Deal is made" cover it.

        Args:
            a_amount (int): Copper part_a promised.
            b_amount (int): Copper part_b promised.
        """
        if self._currency_settled:
            return
        self._currency_settled = True

        if not a_amount and not b_amount:
            return

        delta = a_amount - b_amount
        if delta:
            payer, payee = (
                (self.part_a, self.part_b) if delta > 0 else (self.part_b, self.part_a)
            )
            if not payer.currency.transfer_to(payee, abs(delta), reason="barter"):
                # Not reachable while the staleness guard is intact:
                # _offered_currency_still_held() has just passed and
                # |delta| <= what the payer promised. But "unreachable" is a
                # claim about the code as it stands today, and mutation testing
                # during E.2 showed it firing the moment that guard was
                # weakened -- at which point this branch was the only thing
                # standing between a broken check and money moving on a
                # promise nobody could keep. Loud in the log, honest to the
                # players, and second in line rather than decorative.
                logger.log_err(
                    "barter settlement failed after the staleness guard passed: "
                    f"{payer} -> {payee}, {abs(delta)} Copper "
                    f"(promised {a_amount}/{b_amount})"
                )
                stalled = "The coin could not be moved; no money changed hands."
                self.part_a.msg(stalled)
                self.part_b.msg(stalled)
                return

        self._tell_settlement(self.part_a, a_amount, b_amount)
        self._tell_settlement(self.part_b, b_amount, a_amount)

    @staticmethod
    def _tell_settlement(party, paid, received):
        """One party's half of the settlement, in the terms they agreed to."""
        clauses = []
        if paid:
            clauses.append("pay |y%s|n" % format_copper(paid))
        if received:
            clauses.append("receive |y%s|n" % format_copper(received))
        if clauses:
            party.msg("You %s." % " and ".join(clauses))

    def _finish_and_clear(self, force=False):
        """super().finish(), plus currency settlement and cleanup.

        Kept separate because finish() has two exit paths and both need the same
        treatment without it being written twice.

        ⚠️ `completing` MIRRORS UPSTREAM'S OWN `fin` EXPRESSION EXACTLY. That is
        the point: coin moves if and only if items move, structurally, rather
        than by two pieces of code agreeing to. Note it does NOT include
        `force` -- upstream moves goods on a forced teardown too, if both
        parties are still accepted, and the stale-offer path resets the accepts
        precisely so that neither goods nor coin move there.

        Both `completing` and the amounts are read BEFORE super(), which nulls
        the offer lists, and before the clearing below.

        The fallible operation goes first: the item moves are direct
        `obj.location` assignments that could in principle raise, while
        settlement cannot fail once the staleness guard has passed. Ordering
        them this way means a failure leaves no money stranded. There is no
        yield point between them, so nothing can observe the intermediate state
        (S4-R1).
        """
        completing = (
            self.trade_started and self.part_a_accepted and self.part_b_accepted
        )
        a_amount = self.part_a_currency
        b_amount = self.part_b_currency

        # Launch Minimum L2.2: what each side gave, read before super() nulls
        # the offer lists (upstream barter.py:377-378).
        a_items = [obj.key for obj in (self.part_a_offers or [])]
        b_items = [obj.key for obj in (self.part_b_offers or [])]
        result = super().finish(force=force)
        if not result:
            # Nothing happened. The standing offer, coin included, survives.
            return False

        if completing:
            self._settle_currency(a_amount, b_amount)
            # Launch Minimum L2.2: the trade line, after the swap and the
            # settlement -- the alpha's only price datum. Barter moves goods by
            # assignment, so no move hook could have written it. A stale offer
            # never reaches here: finish() resets the accepts, so `completing`
            # is False. Amounts are the agreed (gross) ones, as the players saw
            # them; the netted transfer is an implementation detail.
            activity_log.record(
                "trade",
                self.part_a,
                part_a=[self.part_a.dbref, self.part_a.key],
                part_b=[self.part_b.dbref, self.part_b.key],
                a_items=a_items,
                b_items=b_items,
                a_copper=a_amount,
                b_copper=b_amount,
            )
            # W4.2b: the same assignment ran no hook, so no `char` push
            # either; both parties' `carried` changed with the swap.
            client_state.push(self.part_a, "char")
            client_state.push(self.part_b, "char")

        self.part_a_currency = 0
        self.part_b_currency = 0
        return True


class CmdPWAccept(_PerReader, CmdBaseAccept):
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
            reasons = _stale_offer_reasons(handler)
            if reasons:
                _tell(reasons)
                # Reset accepts so the forced teardown moves neither goods nor
                # coin -- see _finish_and_clear's `completing`.
                handler.part_a_accepted = False
                handler.part_b_accepted = False
                handler.finish(force=True)
                return

        # The contrib's body (barter.py:555-572), with each party named as the
        # reader knows them (Names NM-T13, NM15).
        if handler.accept(caller):
            # deal finished. Trade ended and cleaned.
            caller.msg(
                self.str_caller
                % "You |gaccept|n the deal. |gDeal is made and goods changed hands.|n"
            )
            self.msg_other(
                caller,
                self.str_other
                % f"{self.named} |gaccepts|n the deal. |gDeal is made and goods changed hands.|n",
            )
        else:
            # a one-sided accept.
            caller.msg(
                self.str_caller
                % f"You |Gaccept|n the offer. {names.line_start(self.other, caller)} "
                "must now also accept."
            )
            self.msg_other(
                caller,
                self.str_other
                % f"{self.named} |Gaccepts|n the offer. You must now also accept.",
            )


class CmdPWEvaluate(_PerReader, CmdBaseEvaluate):
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


class CmdPWFinish(_PerReader, CmdBaseFinish):
    """
    end the trade prematurely

    Usage:
      end trade [:say]
      finish trade [:say]

    This ends the trade prematurely. No trade will take place.

    The contrib's command (barter.py:745-752), with the caller named as the
    other party knows them (Names NM-T13, NM15).
    """

    def func(self):
        """end trade"""
        caller = self.caller
        self.tradehandler.finish(force=True)
        caller.msg(self.str_caller % "You |raborted|n trade. No deal was made.")
        self.msg_other(
            caller, self.str_other % f"{self.named} |raborted|n trade. No deal was made."
        )


# The contrib's CmdTrade.func does `part_a.scripts.add(TradeTimeout)`,
# resolving the name `TradeTimeout` from this contrib module's globals at call
# time; CmdPWTrade.func (NM-T13b) names PWTradeTimeout and PWTradeHandler
# itself, and the swaps stay for anything else that resolves them.
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
barter_module.CmdFinish = CmdPWFinish
