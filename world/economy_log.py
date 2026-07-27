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
