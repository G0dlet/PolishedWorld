"""
Mint/burn ledger for the currency economy (Stage 4, Components A.2 / A.3).

WHY A LEDGER AT ALL
-------------------
Decomposition S4-4: transfers are NOT logged. Money moving between two players
is the normal business of the game and logging it would grow without bound for
no diagnostic gain. Only the two events that change the *total amount of money
in the world* are recorded -- mint and burn -- because those are the only ones
that can be wrong.

Integrity is then carried by an invariant rather than by an audit trail:

    Sum(all wallets) + Treasury  ==  Sum(mints) - Sum(burns)

`audit()` (A.3) recomputes both sides and compares. That catches a wallet
corrupted by a bug or a console mistake, which no transaction log would notice,
and it does so without the log having to be trusted.

WHY A GLOBAL SCRIPT AND NOT AN ATTRIBUTE ON SOMETHING
-----------------------------------------------------
An append-only list in an Attribute deserialises *wholesale* on every access,
so the cost of recording entry N is proportional to N. Two mitigations, both
here:

1. The ledger lives on a global Script registered in `settings.GLOBAL_SCRIPTS`,
   following the `WeatherScript` precedent -- auto-created on first server start
   and re-created if ever deleted. It belongs to the world, not to a character.
2. Running totals are maintained as their own integer Attributes, so
   `total_minted()` / `total_burned()` -- and therefore `audit()`, the frequent
   reader -- never touch the entry list at all. Only `append()` pays the
   deserialisation cost, and mints are rare by design (S4-1: one bootstrap
   tranche plus corrections).

DEVELOPMENT-PHASE NOTE
----------------------
During development the database is reset repeatedly and no ledger contents are
worth preserving. That is fine and requires no special handling: the Script is
recreated empty by GLOBAL_SCRIPTS on the next start, totals begin at zero, and
the invariant holds trivially over an empty economy. Nothing here needs a
migration path. What matters *now* is that the shape is right, so that the
first real mint on a live database is recorded correctly without anyone having
to remember to switch something on.

RACE SAFETY
-----------
Evennia runs the Twisted reactor single-threaded, so `append()` is atomic as
long as it never yields -- it does not. The entry write and the running-total
write happen in one unbroken synchronous sequence, which is what keeps them from
drifting. `recompute_totals()` exists as a repair path in case they ever do
anyway (an exception between the two writes, a hand-edited Attribute in a
console).
"""

import time

from evennia.utils import logger

# Must match the key registered in settings.GLOBAL_SCRIPTS.
LEDGER_SCRIPT_KEY = "economy_ledger"

KIND_MINT = "mint"
KIND_BURN = "burn"
VALID_KINDS = frozenset({KIND_MINT, KIND_BURN})


def get_ledger():
    """
    Return the global ledger Script, creating it if it does not exist.

    GLOBAL_SCRIPTS handles the get-or-create: the container auto-(re)creates
    anything declared in settings, so a deleted or reset ledger comes back by
    itself on next access. Imported inside the function rather than at module
    level because `evennia` is not safely importable during early settings load
    -- the same reason `world/weather.py` does it this way.

    Returns:
        Script: the `EconomyLedgerScript` instance.
    """
    from evennia import GLOBAL_SCRIPTS

    return getattr(GLOBAL_SCRIPTS, LEDGER_SCRIPT_KEY)


def append(kind, amount, tag, recipient=None):
    """
    Record one mint or burn and update the matching running total.

    Called by `CurrencyHandler.add()` and `.burn()` **before** they mutate a
    wallet, so a ledger failure aborts the money movement rather than leaving it
    unrecorded. That ordering is the whole reason the invariant can be trusted.

    Args:
        kind (str): `KIND_MINT` or `KIND_BURN`.
        amount (int): a POSITIVE amount in Copper. Burns are recorded as
            positive numbers and subtracted by `total_burned()`; storing them
            negative would make a sign error in one place cancel a sign error in
            another and still balance.
        tag (str): the mint source or burn reason (e.g. "crypto_exchange").
            Vocabulary is validated by the caller, not here -- this function is
            storage, the handler owns policy.
        recipient (Object, optional): whose wallet is affected. Both the key and
            the dbref are stored: the dbref identifies the object exactly, the
            key stays readable after that object is gone.

    Returns:
        dict: the entry as stored.

    Raises:
        ValueError: if `kind` is unknown or `amount` is not a positive int.
    """
    if kind not in VALID_KINDS:
        raise ValueError(f"economy_log.append: unknown kind {kind!r}; expected one of {sorted(VALID_KINDS)}.")
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError(f"economy_log.append: amount must be a positive int, got {amount!r}.")

    entry = {
        # Real-world epoch seconds, not game time: this is an audit record about
        # the server, not an event in the fiction. Stored as a float rather than
        # a datetime to keep the Attribute trivially serialisable, and rendered
        # only on display.
        "timestamp": time.time(),
        "kind": kind,
        "amount": amount,
        "tag": tag,
        "recipient_key": recipient.key if recipient else None,
        "recipient_dbref": recipient.dbref if recipient else None,
    }

    ledger = get_ledger()

    # Entry first, then the total. If the process died between the two, the
    # total would under-count and audit() would flag a mismatch -- visible and
    # repairable. The other order would silently claim money that has no record.
    ledger.db.entries.append(entry)

    if kind == KIND_MINT:
        ledger.db.minted = (ledger.db.minted or 0) + amount
    else:
        ledger.db.burned = (ledger.db.burned or 0) + amount

    return entry


def total_minted():
    """
    Total Copper ever minted.

    Reads the running total, never the entry list -- see the module docstring on
    why that distinction matters.

    Returns:
        int: total minted, in Copper.
    """
    return get_ledger().db.minted or 0


def total_burned():
    """
    Total Copper ever burned.

    Returns:
        int: total burned, in Copper.
    """
    return get_ledger().db.burned or 0


def net_issued():
    """
    Minted minus burned: how much money should exist in the world right now.

    This is the right-hand side of the audit invariant (A.3).

    Returns:
        int: net Copper in circulation according to the ledger.
    """
    return total_minted() - total_burned()


def entries(limit=None, kind=None):
    """
    Return ledger entries, newest last.

    This is the expensive reader (it deserialises the whole list), so it is for
    admin inspection only -- `audit()` deliberately does not use it.

    Args:
        limit (int, optional): return only the most recent `limit` entries.
        kind (str, optional): filter to `KIND_MINT` or `KIND_BURN`.

    Returns:
        list[dict]: matching entries, as plain dicts.
    """
    # dict(entry) copies out of Evennia's _SaverDict, so a caller mutating the
    # result cannot accidentally write back into the ledger.
    result = [dict(entry) for entry in (get_ledger().db.entries or [])]

    if kind is not None:
        result = [entry for entry in result if entry.get("kind") == kind]

    if limit is not None:
        result = result[-limit:]

    return result


def recompute_totals():
    """
    Rebuild the running totals from the entry list.

    Repair path, not a routine operation. The totals and the entries are written
    in one synchronous sequence in `append()`, so they should never disagree --
    but if an exception lands between the two writes, or someone edits an
    Attribute from a console, this is how the ledger is made self-consistent
    again. `audit()` (A.3) is what tells you it is needed.

    Returns:
        str: human-readable summary of what changed, safe to print from `@py`.
    """
    ledger = get_ledger()

    old_minted = ledger.db.minted or 0
    old_burned = ledger.db.burned or 0

    minted = burned = 0
    for entry in ledger.db.entries or []:
        try:
            amount = int(entry.get("amount", 0))
            if entry.get("kind") == KIND_MINT:
                minted += amount
            elif entry.get("kind") == KIND_BURN:
                burned += amount
        except (TypeError, ValueError):
            # One malformed entry must not abort the repair of all the others.
            logger.log_err(f"economy_log.recompute_totals: skipping malformed entry {entry!r}")

    ledger.db.minted = minted
    ledger.db.burned = burned

    return (
        f"recompute_totals: minted {old_minted} -> {minted}, "
        f"burned {old_burned} -> {burned} "
        f"(over {len(ledger.db.entries or [])} entries)."
    )


# --------------------------------------------------------------------------
# The audit invariant (A.3)
# --------------------------------------------------------------------------
#
# WHAT IT PROVES, AND WHY IT IS NOT A TRANSACTION LOG
# ---------------------------------------------------
#     Sum(every wallet in the world)  ==  Sum(mints) - Sum(burns)
#
# A transaction log answers "what happened". This answers the harder and more
# useful question: "is the amount of money in the world still the amount we
# created?" It catches things no log could -- a wallet corrupted by a bug, a
# console mistake, a half-applied transfer, a typeclass that started minting by
# accident -- because it recomputes both sides from scratch and compares them
# rather than trusting any record of intent.
#
# It also does not care *how* money moved. That is exactly why transfers can go
# unlogged (S4-4) without weakening anything: a transfer changes two wallets by
# equal and opposite amounts, so it cannot move the left-hand side at all.

# Attribute key for the wallet. Must match CurrencyHandler's default; the audit
# reads storage directly rather than importing the handler (see below).
WALLET_ATTRIBUTE = "wallet"


def _wallet_holders():
    """
    Every object in the world that holds money.

    ENUMERATION BY ATTRIBUTE, NOT BY TYPECLASS -- deliberate, and a deviation
    from the decomposition's suggested
    `ObjectDB.objects.typeclass_search("...Character", include_children=True)`.
    That call is real and works (it is `Character.objects.all_family()` with one
    more layer of indirection -- verified in evennia/typeclasses/managers.py,
    where typeclass_search simply delegates to all_family when
    include_children=True). The problem is not correctness today, it is that it
    enumerates the wrong *concept*.

    Auditing "all Characters" means the audit is complete only for as long as
    Characters are the only wallet holders. The Treasury (C.1) is already not a
    Character, and the moment any future typeclass gets a wallet -- a guild
    bank, a shop, a corpse that keeps its purse in Stage 5 -- the sum silently
    under-counts and audit() reports a failure that is really a bug in audit().
    A false alarm in the one tool that exists to be trusted is worse than no
    tool.

    Enumerating by Attribute makes the audit complete by construction: anything
    with a wallet is included, whatever it is, with no maintenance. It is also
    the cheaper query -- one indexed lookup on the Attribute key rather than a
    full typeclass-family scan -- and because the wallet Attribute is not
    created until the first mutation (D6), objects that have never touched money
    are correctly and automatically absent from a sum they contribute nothing to.

    Returns:
        Queryset: ObjectDB rows carrying a wallet Attribute.
    """
    from evennia.objects.models import ObjectDB

    return ObjectDB.objects.get_by_attribute(key=WALLET_ATTRIBUTE)


def _read_treasury():
    """
    The canonical Treasury object, or None if there is not one yet.

    Guarded import: `typeclasses/treasury.py` does not exist until C.1, and A.3
    must not depend on it. This matters beyond build order -- `get_treasury()`
    is documented to return None whenever the settings key is unset, so every
    consumer has to handle its absence anyway.

    Note what does NOT depend on this: the invariant itself. The Treasury holds
    a wallet Attribute like anything else, so it is already counted by
    `_wallet_holders()`. Identifying it separately only lets audit() *report* it
    on its own line, because "how much is in the Treasury" is the number an
    admin actually wants to see. If the Treasury cannot be identified, the
    invariant is still exact; its balance is simply reported inside `wallet_sum`
    instead of beside it.

    Returns:
        Object | None: the Treasury.
    """
    try:
        from typeclasses.treasury import get_treasury
    except ImportError:
        # Expected until C.1 lands. Not an error worth logging.
        return None

    try:
        return get_treasury()
    except Exception:
        logger.log_trace()
        return None


def audit():
    """
    Recompute the economy invariant and report the result.

    READS RAW STORAGE, NOT THE HANDLER. `CurrencyHandler.value` is part of what
    is being audited -- if it ever developed a bug (a stray `or 0`, a wrong
    default, a coercion), an audit routed through it would inherit that bug and
    certify the corruption as healthy. Reading the Attribute directly means the
    two sides of the comparison share as little code as possible.

    Full enumeration is acceptable because auditing is an infrequent admin
    action (`@economy audit`, C.2), not something on a hot path.

    Returns:
        dict: with keys

            wallet_sum (int): total held by every wallet EXCEPT the Treasury.
            treasury (int | None): the Treasury's balance, or None if there is
                no Treasury yet (C.1). None means "not reportable separately",
                never "zero" -- an actual empty Treasury reports 0.
            held (int): everything, Treasury included. The left-hand side.
            minted (int), burned (int): ledger totals.
            expected (int): minted - burned. The right-hand side.
            delta (int): held - expected. Positive means money exists that was
                never minted; negative means minted money has vanished.
            wallet_count (int): how many objects hold a wallet.
            corrupt (list[str]): dbrefs of objects whose wallet Attribute is not
                an int. Excluded from the sums, because including them would
                either crash the audit or silently coerce the damage away.
            ok (bool): True only if delta is 0 AND nothing is corrupt.
    """
    treasury_obj = _read_treasury()
    treasury_dbref = treasury_obj.dbref if treasury_obj else None

    wallet_sum = 0
    treasury_balance = None
    wallet_count = 0
    corrupt = []

    for obj in _wallet_holders():
        wallet_count += 1
        balance = obj.attributes.get(WALLET_ATTRIBUTE)

        # bool is checked first because it subclasses int -- a wallet holding
        # True would otherwise pass as 1 and quietly skew the sum by one Copper,
        # which is precisely the kind of tiny persistent drift that is hardest
        # to trace later.
        if isinstance(balance, bool) or not isinstance(balance, int):
            corrupt.append(obj.dbref)
            continue

        if treasury_dbref and obj.dbref == treasury_dbref:
            treasury_balance = balance
        else:
            wallet_sum += balance

    # A Treasury that exists but has never been minted into has no wallet
    # Attribute at all, so the loop never sees it. It holds 0, and reporting
    # None there would wrongly read as "no Treasury".
    if treasury_obj is not None and treasury_balance is None:
        treasury_balance = 0

    held = wallet_sum + (treasury_balance or 0)
    minted = total_minted()
    burned = total_burned()
    expected = minted - burned

    return {
        "wallet_sum": wallet_sum,
        "treasury": treasury_balance,
        "held": held,
        "minted": minted,
        "burned": burned,
        "expected": expected,
        "delta": held - expected,
        "wallet_count": wallet_count,
        "corrupt": corrupt,
        "ok": held == expected and not corrupt,
    }


def audit_report():
    """
    `audit()` rendered as plain text.

    Lives here rather than in the command (C.2) so it is usable from `@py` and
    `evennia shell` during development, before any admin surface exists. C.2
    adds the colour; this stays uncoloured for the same reason format_copper
    does (D2) -- it goes into logs as readily as onto a screen.

    Returns:
        str: multi-line report, safe to pass straight to `msg()`.
    """
    # Imported here rather than at module level: world.currency imports this
    # module, so a top-level import back into it would be circular.
    from world.currency import format_copper

    result = audit()

    treasury_line = (
        "  Treasury:       (none configured)"
        if result["treasury"] is None
        else f"  Treasury:       {format_copper(result['treasury'])}"
    )

    lines = [
        "Economy audit",
        # Fixed-width labels: the holder count goes after the value rather than
        # inside the label, so a three-digit count cannot shift the column.
        f"  Wallets:        {format_copper(result['wallet_sum'])}"
        f"  ({result['wallet_count']} holder{'' if result['wallet_count'] == 1 else 's'})",
        treasury_line,
        f"  Total held:     {format_copper(result['held'])}",
        f"  Minted:         {format_copper(result['minted'])}",
        f"  Burned:         {format_copper(result['burned'])}",
        f"  Expected:       {format_copper(result['expected'])}",
    ]

    if result["ok"]:
        lines.append("  Result:         OK (delta 0)")
    else:
        # Loud and specific. An audit failure means money was created or
        # destroyed outside the mint path, which is the most serious class of
        # bug this project can have -- it must not read like a rounding notice.
        lines.append(f"  Result:         *** MISMATCH *** delta {result['delta']} copper")
        if result["delta"] > 0:
            lines.append("                  More money exists than was ever minted.")
        elif result["delta"] < 0:
            lines.append("                  Minted money has gone missing.")
        if result["corrupt"]:
            lines.append(f"                  Non-integer wallets: {', '.join(result['corrupt'])}")

    return "\n".join(lines)
