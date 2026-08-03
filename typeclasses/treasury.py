"""
The Treasury -- the temple's coffer and the faucet's funding source
(Stage 4, Component C.1).

WHY THIS OBJECT EXISTS AT ALL
----------------------------
Decomposition S4-1. `PolishedWorld_Economic_Philosophy.md` Principle 4 says Gold
is minted at exactly one point (the GameGold exchange) and that the temple faucet
merely *redistributes* exchange-minted Gold. But there is no exchange until Stage
8, so a faucet that pays players in Stage 4 would have to create the money it
pays -- a second mint point, and Principle 4 quietly false for four stages.

The Treasury is what keeps Principle 4 literally true instead:

    bootstrap tranche  ->  Treasury wallet  ->  transfer_to(player)
    (one mint, C.2)         (this object)       (the faucet, D.1)

The faucet **transfers**. It never mints. `CurrencyHandler.add()` therefore has
exactly one production caller in the codebase -- `@economy mint` (C.2) -- which
is what makes S4-1 a testable invariant rather than a review convention.

A secondary property that is a feature, not a defect: a Treasury holds a finite
balance and **can run dry**. That is diegetic (temple donations are finite), it
bounds faucet farming alongside the existing low-reward-plus-cooldown design, and
it gives one readable number for how much Gold the temple can still hand out.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
-----------------------------------------
* It does not create a Treasury. There is exactly one canonical Treasury per
  game and it is built in-world by an admin (`@create`), then pointed at by
  `settings.TREASURY_DBREF`. Auto-creating one would mean a fresh database
  silently acquires a money-holding object nobody placed.
* It does not initialise a balance. See `Treasury.currency` below -- the wallet
  Attribute does not exist until the first mint, by design (D6).
* It does not cache the lookup. See `get_treasury()`.

RELATIONSHIP TO THE AUDIT (D9)
------------------------------
`economy_log.audit()` enumerates wallet holders with
`ObjectDB.objects.get_by_attribute(key="wallet")`, not by typeclass, so the
Treasury is counted **automatically** the moment it holds anything. Nothing in
this module registers it anywhere. `audit()` only resolves it separately in order
to *report* it on its own line, because "how much is in the Treasury" is the
number an admin actually wants to read; the invariant is exact either way.
"""

from django.conf import settings

from evennia.objects.objects import DefaultObject
from evennia.utils import lazy_property, logger, search

from world.currency import CurrencyHandler

from .objects import ObjectParent

# The settings key that names the canonical Treasury by dbref. Read through
# getattr(settings, ..., None) rather than being required, exactly like
# DEFAULT_RESPAWN_DBREF in characters.py::_get_respawn_location -- an unset key
# is a supported state (a fresh database has no Treasury yet), not a crash.
TREASURY_DBREF_SETTING = "TREASURY_DBREF"

# Why the setting names a DBREF and not a key: keys are not unique in Evennia.
# Two objects called "temple treasury" would make the lookup ambiguous, and the
# ambiguity would resolve differently depending on creation order -- for the one
# object in the game that money is minted into, that is not an acceptable class
# of failure. A dbref is unique by construction.

# Problem codes returned alongside the lookup result. These exist because
# get_treasury() collapses three *different* misconfigurations into one None,
# and the three need different fixes:
#
#   PROBLEM_UNSET       -- nobody has configured a Treasury yet.
#                          Fix: build one, set the setting, reload.
#   PROBLEM_NOT_FOUND   -- the setting names a dbref that does not resolve.
#                          Fix: the dbref is wrong or the object was deleted.
#   PROBLEM_WRONG_TYPE  -- the dbref resolves to something that is not a
#                          Treasury. Fix: the dbref points at the wrong object.
#
# The third is the dangerous one and is the reason the typeclass is checked at
# all: a mistyped dbref that happens to land on a Character would otherwise make
# `@economy mint` create money directly in a player's purse, which is precisely
# the "second mint destination" S4-1 exists to prevent. Refusing is the only
# acceptable answer.
PROBLEM_UNSET = "unset"
PROBLEM_NOT_FOUND = "not_found"
PROBLEM_WRONG_TYPE = "wrong_type"


class Treasury(ObjectParent, DefaultObject):
    """
    An in-world coffer that holds money. There is one canonical instance.

    Not a container: it holds a *balance*, not objects. Coin is an integer in
    an Attribute (S4-2) and there are no coin objects in Stage 4, so there is
    nothing to put inside it and no container cmdset is attached.

    Create and configure it like this:

        @create/drop temple treasury:typeclasses.treasury.Treasury
        (note the resulting #dbref, then in server/conf/settings.py)
        TREASURY_DBREF = "#42"
        @reload

    Anything that reads the Treasury handles its absence (`get_treasury()`
    returns None), so a game with the setting unset runs fine -- the faucet
    simply has no funds, which is the honest state of a temple nobody has
    endowed yet.
    """

    @lazy_property
    def currency(self):
        """
        Wallet handler, identical in shape to Character's (S4-2).

        The Treasury is NOT a special case in the currency system -- it is just
        an object that happens to hold a lot. Same handler, same single int
        Attribute in Copper, same rule that `world/currency.py` is the only
        writer (S4-R2).

        Deliberately no initialisation in `at_object_creation` and no
        `AttributeProperty` (D6, Evennia Reference §11.23). The handler reads
        with `default=0`, so a Treasury that has never been minted into holds
        nothing without an Attribute row existing for it. Two consequences worth
        keeping: re-running creation hooks can never clobber a live balance
        because nothing writes a starting value, and there is no
        `treasury.wallet = 500` shortcut for code outside the currency module to
        reach for.
        """
        return CurrencyHandler(self, db_attribute="wallet")

    def at_object_creation(self):
        """Lock the coffer against being pocketed."""
        super().at_object_creation()
        # Same pattern and same reasoning as Corpse/Creature/ResourceNode: a
        # fixture in the world is not loot. Without this, `get treasury` walks
        # off with the entire money supply of the game -- and since the wallet
        # travels with the object, so does every unspent Copper in it.
        self.locks.add("get:false()")

    def at_pre_puppet(self, *args, **kwargs):
        """
        Refuse to be puppeted.

        Belt-and-braces against an admin `@ic`-ing into the coffer, which would
        give a session a wallet that the faucet is concurrently transferring out
        of. Cheap to forbid, confusing to debug.
        """
        return False


def get_configured_dbref():
    """
    The raw value of the Treasury settings key, or None if unset.

    Exposed separately so `@economy` (C.2) can quote the misconfigured value
    back to the admin. A message that says "TREASURY_DBREF is set to '#4200'
    but nothing with that dbref exists" is actionable; "no Treasury" is not.

    Returns:
        str | int | None: whatever the setting holds.
    """
    return getattr(settings, TREASURY_DBREF_SETTING, None)


def resolve_treasury():
    """
    Resolve the canonical Treasury and say precisely what went wrong if it fails.

    Returns:
        tuple[Object | None, str | None]: `(treasury, problem)`. Exactly one of
            the two is None. `problem` is one of `PROBLEM_UNSET`,
            `PROBLEM_NOT_FOUND`, `PROBLEM_WRONG_TYPE`.

    NO CACHING -- and do not add any. `search_object()` on a dbref is a single
    indexed primary-key lookup, and the callers are all rare: `@economy` and
    `audit()` are admin actions, and the faucet (D.1) is cooldown-gated. What a
    cache would buy is negligible; what it would cost is the worst failure mode
    this function has. A cached `None` from before the Treasury was built
    survives for the rest of the process, so an admin who creates the coffer and
    sets the key sees "no Treasury configured" until they restart and concludes
    their configuration did not take. Correctness beats a lookup nobody was
    waiting on.
    """
    dbref = get_configured_dbref()
    if not dbref:
        return None, PROBLEM_UNSET

    # Broad except on purpose: search_object() with a malformed setting value
    # (a list, a dict, a typo'd non-dbref string) is a configuration error, and
    # a configuration error must not take a command down with a traceback. The
    # trace is logged so it is diagnosable, and the caller gets a problem code
    # it knows how to phrase.
    try:
        matches = search.search_object(dbref)
    except Exception:
        logger.log_trace(
            f"resolve_treasury: {TREASURY_DBREF_SETTING}={dbref!r} could not be searched."
        )
        return None, PROBLEM_NOT_FOUND

    if not matches:
        return None, PROBLEM_NOT_FOUND

    candidate = matches[0]

    # exact=False so a future subclass (a guild vault sharing the behaviour)
    # still qualifies. `is_typeclass` reads the *loaded* typeclass, which is the
    # right thing here: an object whose typeclass path is broken falls back to
    # DefaultObject at load time and would then have no `currency` handler, so
    # treating it as "wrong type" is accurate rather than pedantic.
    if not candidate.is_typeclass(Treasury, exact=False):
        return None, PROBLEM_WRONG_TYPE

    return candidate, None


def get_treasury():
    """
    The canonical Treasury object, or None.

    This is the contract `world/economy_log.py::_read_treasury` already imports
    and depends on, and it is deliberately narrow: callers that only need the
    object get one call and no error vocabulary. Anything that needs to *explain*
    the absence to a human calls `resolve_treasury()` instead.

    Every consumer must handle None. There is no "the Treasury always exists"
    state to program against -- a fresh database genuinely has no Treasury, and a
    faucet with no funding source is a supported situation.

    Returns:
        Object | None: the Treasury.
    """
    treasury, _problem = resolve_treasury()
    return treasury
