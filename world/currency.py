"""
Currency denomination maths, parsing and rendering (Stage 4, Component A.1).

The functions in the first half are pure -- no database, no typeclass -- which
is why they are testable with the lightest base class (`EvenniaTestCase`). The
`CurrencyHandler` in the second half (A.2) is the stateful part: it owns the
wallet Attribute and is the ONLY thing in the codebase that writes it (S4-R2).
Keeping both in one module is deliberate: the handler is meaningless without
the denomination rules, and splitting them would put the invariant's two halves
in two files.

THE ONE IDEA
------------
The wallet is a single integer denominated in **Copper** (decomposition S4-2).
Gold and Silver are a *rendering* concern applied at display time and a *parsing*
concern applied at input time -- they are never stored, never summed, never
rounded. Everything in this module exists to keep that boundary honest:

    storage      : int, Copper
    display      : format_copper()      int -> str
    input        : parse_amount()       str -> int | None
    arithmetic   : to_copper()          (g, s, c) -> int
    inspection   : split_denominations() int -> (g, s, c)

`DENOMINATIONS` is the single source of truth for both directions. Splitting,
rendering and parsing all read it, so the display vocabulary and the accepted
input vocabulary cannot drift apart -- add a denomination there and all three
follow.

LOCKED DESIGN DECISIONS (this session; rationale in the session log)
-------------------------------------------------------------------
* D1 -- `parse_amount` requires an explicit denomination. A bare "50" returns
  None. Guessing a default would let `pay 50 to Bob` silently transfer 1/200th
  of what a player intending Silver meant, with no error to notice.
* D2 -- No Evennia colour codes here. `format_copper` output goes into ledger
  entries, exception messages and test assertions as well as onto a screen;
  baked-in `|y` markup is noise in three of those four. Commands colour their
  own output.
* D3 -- Rendering grammar: largest denomination first, zero denominations
  omitted, comma-separated, no "and", capitalised names, no plural "s"
  (the names behave as mass nouns: "3 Copper", as in "three gold"), and the
  empty amount renders as "nothing" rather than "0 Copper".
* D4 -- Negatives are rendered, not rejected. A negative balance is an invariant
  violation that `transfer_to` (S4-R1) prevents and `audit()` (A.3) detects --
  enforcing it *here* would mean the `wallet` command raises a traceback at the
  exact moment a player most needs to see the number. Policy belongs where the
  invariant lives; this module is arithmetic.

NOT IN SCOPE (-> docs/BACKLOG.md)
---------------------------------
Compact multi-denomination input ("2g30s"). The boundary drawn below is
deliberately simple: `parse_amount` accepts exactly two whitespace-separated
tokens, so the attached single-denomination form ("50c") is rejected too. That
keeps the rule explainable in one sentence, and both forms belong to the same
future feature.
"""

from world import economy_log

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

COPPER_PER_SILVER = 100

# Derived, not a second literal. The decomposition writes this as 10_000; it IS
# 10_000, but expressing it as a product means the two constants cannot drift
# out of the documented 1 Gold = 100 Silver = 10,000 Copper relationship if one
# of them is ever tuned. Deliberate (flagged) deviation from the decomp's
# literal spelling; the value is identical.
COPPER_PER_GOLD = 100 * COPPER_PER_SILVER  # 10_000

# Ordered largest-first. This drives split_denominations(), format_copper() AND
# parse_amount()'s vocabulary, so display and input can never disagree about
# what a denomination is worth.
DENOMINATIONS = (
    ("Gold", COPPER_PER_GOLD),
    ("Silver", COPPER_PER_SILVER),
    ("Copper", 1),
)

# Accepted input words -> value in Copper. Built from DENOMINATIONS so it stays
# in sync; the single-letter abbreviations are the only hand-written part.
_DENOMINATION_VALUES = {name.lower(): value for name, value in DENOMINATIONS}
_DENOMINATION_VALUES.update(
    {
        "g": COPPER_PER_GOLD,
        "s": COPPER_PER_SILVER,
        "c": 1,
    }
)


# --------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------


def _require_int(value, label):
    """
    Return `value` as an int, raising TypeError if it is not a genuine integer.

    Why this is strict rather than an int() coercion: the wallet is an integer
    Attribute and the audit invariant (A.3) sums wallets exactly. A float that
    reaches storage -- from `to_copper(gold=1.5)`, say -- would make that sum
    non-exact and the corruption would surface far from its cause. Truncating
    silently would be worse still, because it destroys money without a word.

    `bool` is excluded explicitly: it is an int subclass in Python, so
    `to_copper(True)` would otherwise quietly mean one Gold.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an int, got {type(value).__name__}: {value!r}")
    return value


# --------------------------------------------------------------------------
# Arithmetic
# --------------------------------------------------------------------------


def to_copper(gold=0, silver=0, copper=0):
    """
    Convert a denominated amount into a single Copper integer.

    Args:
        gold (int): Gold coins. Defaults to 0.
        silver (int): Silver coins. Defaults to 0.
        copper (int): Copper coins. Defaults to 0.

    Returns:
        int: the total in Copper. May be negative if the inputs are; this
            function does no policy checking (D4).

    Raises:
        TypeError: if any argument is not an int (see `_require_int`).

    Example:
        >>> to_copper(gold=1, silver=2, copper=3)
        10203
    """
    _require_int(gold, "gold")
    _require_int(silver, "silver")
    _require_int(copper, "copper")
    return gold * COPPER_PER_GOLD + silver * COPPER_PER_SILVER + copper


def split_denominations(copper):
    """
    Split a Copper integer into its (gold, silver, copper) components.

    The inverse of `to_copper` for any integer input, positive or negative:
    `to_copper(*split_denominations(n)) == n` always holds. That round-trip
    property is the module's core invariant and is tested directly.

    Negative amounts split component-wise with the sign carried on each part
    (-10_500 -> (-1, -5, 0)) rather than relying on Python's floor division,
    which would give (-2, 95, 0) -- arithmetically correct but useless to a
    caller and a broken round-trip for rendering.

    Args:
        copper (int): an amount in Copper.

    Returns:
        tuple[int, int, int]: (gold, silver, copper), each carrying the sign of
            the input.

    Raises:
        TypeError: if `copper` is not an int.
    """
    _require_int(copper, "copper")

    sign = -1 if copper < 0 else 1
    remainder = abs(copper)

    parts = []
    for _name, value in DENOMINATIONS:
        qty, remainder = divmod(remainder, value)
        parts.append(sign * qty)

    return tuple(parts)


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def format_copper(copper):
    """
    Render a Copper integer as a human-readable denominated string.

    Grammar is locked (D3): largest first, zero denominations omitted,
    comma-separated, no "and", capitalised names, no plural "s". Zero renders as
    "nothing", not "0 Copper" -- an empty purse is a state, not a quantity.

    A negative amount takes ONE leading minus for the whole sum
    (-10_500 -> "-1 Gold, 5 Silver"), not a minus per component, which would
    read as three separate debts.

    Args:
        copper (int): an amount in Copper.

    Returns:
        str: the rendered amount. Never empty; never coloured (D2).

    Raises:
        TypeError: if `copper` is not an int.

    Examples:
        >>> format_copper(0)
        'nothing'
        >>> format_copper(10203)
        '1 Gold, 2 Silver, 3 Copper'
        >>> format_copper(10000)
        '1 Gold'
    """
    _require_int(copper, "copper")

    if copper == 0:
        return "nothing"

    sign = "-" if copper < 0 else ""
    quantities = split_denominations(abs(copper))

    parts = [
        f"{qty} {name}"
        for (name, _value), qty in zip(DENOMINATIONS, quantities)
        if qty
    ]

    return sign + ", ".join(parts)


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


def parse_amount(text):
    """
    Parse player input like "50 copper" or "1 g" into a Copper integer.

    Returns None on anything unparseable rather than raising, so the calling
    command owns the wording of the error -- `pay` and `offer` want to say
    different things about the same bad input.

    Accepted: exactly two whitespace-separated tokens, a non-negative decimal
    integer followed by a denomination. Denominations are case-insensitive, may
    be the full word or the single-letter abbreviation (g/s/c), and a trailing
    plural "s" on a full word is tolerated ("3 coppers") because players type it.

    Rejected (-> None): a bare number with no denomination (D1); negative or
    fractional numbers; a denomination with no number; the attached compact form
    ("50c") and the multi-denomination compact form ("2g30s"), both deferred to
    BACKLOG; empty or whitespace-only input; anything else.

    NOT rejected: zero. "0 copper" parses to 0, because 0 is a perfectly
    parseable amount that simply is not a payable one -- rejecting a payment of
    nothing is the command's business (B.2), and folding the two cases together
    here would force `pay` to report a syntax error for a syntactically fine
    instruction.

    Args:
        text (str | None): raw player input.

    Returns:
        int | None: the amount in Copper, or None if unparseable.

    Examples:
        >>> parse_amount("50 copper")
        50
        >>> parse_amount("1 g")
        10000
        >>> parse_amount("50") is None
        True
    """
    if not text or not isinstance(text, str):
        return None

    tokens = text.strip().lower().split()
    if len(tokens) != 2:
        return None

    number_token, denomination_token = tokens

    # str.isdigit() alone is not enough: it accepts superscripts and other
    # non-ASCII digit-like characters ("2".isdigit() is True) that int() then
    # refuses, turning a bad-input case into a crash. Requiring ASCII first
    # makes the check total. It also rejects "-5", "1.5", "+5" and "1e3" for
    # free, since none of those are all-digits.
    if not (number_token.isascii() and number_token.isdigit()):
        return None

    value = _DENOMINATION_VALUES.get(denomination_token)
    if value is None and denomination_token.endswith("s"):
        # Tolerate "coppers"/"golds". Checked only AFTER an exact lookup fails,
        # because "s" is itself the abbreviation for Silver -- stripping first
        # would turn a valid "3 s" into an empty token.
        value = _DENOMINATION_VALUES.get(denomination_token[:-1])

    if value is None:
        return None

    return int(number_token) * value


# --------------------------------------------------------------------------
# Wallet handler (A.2)
# --------------------------------------------------------------------------
#
# THE MINT/TRANSFER SEPARATION (decomposition S4-1)
# -------------------------------------------------
# Money can only enter the world through the crypto-exchange path. The design
# guard for that is not a comment or a review habit -- it is that creating money
# and moving money are two structurally different methods:
#
#   add()         -- CREATES money. Validates its source against MINT_SOURCES,
#                    writes a ledger entry, and is expected to have exactly ONE
#                    caller in the whole codebase (the bootstrap tranche, C.1).
#   transfer_to() -- MOVES money. Never calls add(). Cannot change the total
#                    amount in the world even if it is buggy, because it
#                    decrements one wallet by exactly what it increments the
#                    other by.
#   burn()        -- DESTROYS money. The Stage 8 exchange-back consumer. Built
#                    now so the ledger is complete from its first entry.
#
# The temple faucet (Component D) is the reason this matters in practice: it
# looks like it hands out money, and the whole point is that it does not -- it
# calls transfer_to() from the Treasury. A faucet that could mint would be an
# unbounded money supply, and the failure would be invisible until inflation
# made it obvious. Hence the load-bearing test: add(source="faucet") raises.


MINT_SOURCES = frozenset({"crypto_exchange", "admin_correction"})

# Symmetric with MINT_SOURCES on purpose. An unvalidated free-text burn reason
# would let the ledger fill with tags nobody recognises while the invariant
# still balances perfectly -- audit() green, and no way to answer "why did
# 40,000 Copper disappear in March".
BURN_REASONS = frozenset({"crypto_exchange", "admin_correction"})


class CurrencyHandler:
    """
    Per-object wallet, stored as a single int Attribute denominated in Copper.

    Wired onto Character via `@lazy_property` in the same way as
    `stats`/`traits`/`skills`/`cooldowns`, and onto the Treasury the same way in
    C.1 -- the Treasury is not a special case, it is just an object that happens
    to hold a lot.

    NO ATTRIBUTE IS DECLARED ANYWHERE FOR THIS
    ------------------------------------------
    Deliberate (D6). There is no `AttributeProperty` on Character and no
    `at_object_creation` initialisation, which means there is no tempting
    `char.wallet = 500` shortcut for anything outside this module to reach for.
    S4-R2 ("no code outside world/currency.py writes the wallet") is enforced by
    there being no other way in, rather than by review vigilance.

    It also removes a whole class of bug rather than guarding against it. The
    handler reads the Attribute with `default=0`, so a character who has never
    touched money simply has none, and the Attribute is not created until the
    first mutation. Existing characters therefore need **no backfill** -- and
    since there is no backfill, the `TraitHandler.add(force=True)` shape of trap
    the decomposition warns about (Evennia Reference 3.5) cannot occur here:
    there is nothing that could clobber a live balance because there is nothing
    that writes a starting value.

    ERROR CONVENTION (D7)
    ---------------------
    `False` means exactly one thing: **insufficient funds**. Everything else --
    a target with no wallet, a non-int amount, paying yourself, an unrecognised
    mint source -- raises, because those are bugs in the calling code and not
    conditions a player can be in. If they returned `False` too, a typo in a
    command would be indistinguishable from poverty, and `pay` would tell a rich
    player they were broke.

    Note that `add()` returns the new balance rather than a bool: it has no
    expected-failure mode at all. Do not "fix" that to a bool for symmetry --
    and equally, do not write `if wallet.burn(...)` expecting a balance, since a
    balance of 0 is falsy and perfectly valid.
    """

    def __init__(self, obj, db_attribute="wallet"):
        """
        Args:
            obj (Object): the object whose wallet this is.
            db_attribute (str): Attribute key for the balance. Matches the
                `CooldownHandler(self, db_attribute="cooldowns")` house style.
        """
        self.obj = obj
        self._db_attribute = db_attribute

    # -- reading -----------------------------------------------------------

    @property
    def value(self):
        """
        Current balance in Copper.

        Returns:
            int: the balance; 0 if the Attribute has never been written.
        """
        # `or 0` covers an Attribute explicitly set to None, which .get()'s
        # default does not catch -- it only fires when the key is absent.
        return self.obj.attributes.get(self._db_attribute, default=0) or 0

    def can_afford(self, amount):
        """
        Whether this wallet holds at least `amount`.

        ⚠️ S4-R1: this is a *read*. Never call it, await something, and then
        debit -- the balance can change in between. Inside `transfer_to()` the
        check and the debit are one unbroken synchronous sequence, which is the
        only reason it is safe there. Commands may call this to decide what to
        *say*; they must not use it to decide that a later debit will succeed.

        Args:
            amount (int): amount in Copper.

        Returns:
            bool: True if the balance covers `amount`.
        """
        self._require_positive(amount)
        return self.value >= amount

    def format(self):
        """
        The balance rendered for display, e.g. "1 Gold, 2 Silver".

        Returns:
            str: uncoloured (D2); commands apply their own markup.
        """
        return format_copper(self.value)

    # -- internal ----------------------------------------------------------

    def _set(self, amount):
        """
        Write the balance. The ONLY place the wallet Attribute is written.

        Private by convention and by intent: every public method funnels through
        here, so there is exactly one line in the codebase that can change a
        balance, and it is trivially auditable.
        """
        self.obj.attributes.add(self._db_attribute, amount)

    @staticmethod
    def _require_positive(amount):
        """
        Reject anything that is not a positive int.

        `bool` is excluded explicitly because it subclasses `int` -- without
        this, `transfer_to(target, True)` would move one Copper.
        """
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError(f"amount must be an int, got {type(amount).__name__}: {amount!r}")
        if amount <= 0:
            raise ValueError(f"amount must be positive, got {amount}")

    # -- mint / burn primitives -------------------------------------------

    def add(self, amount, source):
        """
        MINT: create new money into this wallet. Expects exactly one caller.

        `source` is mandatory and positional-free on purpose -- writing
        `wallet.add(500)` is a TypeError, so money cannot be created by someone
        who was thinking of a generic "add to balance" helper.

        Args:
            amount (int): positive amount in Copper to create.
            source (str): must be in `MINT_SOURCES`.

        Returns:
            int: the new balance.

        Raises:
            TypeError: if `amount` is not an int.
            ValueError: if `amount` is not positive, or `source` is not a
                recognised mint source.
        """
        self._require_positive(amount)

        if source not in MINT_SOURCES:
            # The message names the design rule rather than just the constant,
            # because the person hitting this is usually about to argue with it.
            raise ValueError(
                f"Invalid mint source {source!r}. Gold enters the world only via the "
                f"exchange path; valid sources are {sorted(MINT_SOURCES)}. "
                f"To move existing money (faucet, wages, payment), use transfer_to()."
            )

        # Ledger BEFORE mutation: if recording fails, no money is created. The
        # invariant is only trustworthy if this ordering never inverts.
        economy_log.append(economy_log.KIND_MINT, amount, source, recipient=self.obj)

        new_balance = self.value + amount
        self._set(new_balance)
        return new_balance

    def burn(self, amount, reason):
        """
        BURN: destroy money from this wallet. The Stage 8 exchange-back path.

        Args:
            amount (int): positive amount in Copper to destroy.
            reason (str): must be in `BURN_REASONS`.

        Returns:
            bool: False if the balance does not cover `amount` (nothing is
                mutated and nothing is logged); True on success.

        Raises:
            TypeError: if `amount` is not an int.
            ValueError: if `amount` is not positive, or `reason` is not a
                recognised burn reason.
        """
        self._require_positive(amount)

        if reason not in BURN_REASONS:
            raise ValueError(
                f"Invalid burn reason {reason!r}; valid reasons are {sorted(BURN_REASONS)}."
            )

        current = self.value
        if current < amount:
            return False

        economy_log.append(economy_log.KIND_BURN, amount, reason, recipient=self.obj)

        self._set(current - amount)
        return True

    # -- transfer ----------------------------------------------------------

    def transfer_to(self, target, amount, reason=None):
        """
        Move money from this wallet to another. Cannot create or destroy money.

        ⚠️ S4-R1 -- THE critical sequence of this stage. The balance read, the
        sufficiency check, the debit and the credit happen with no yield point
        between them. Evennia's reactor is single-threaded, so an unbroken
        synchronous block cannot be interleaved with another command: two
        players spending the same coin in the same tick is impossible *because*
        of this property, not because of a lock. Introducing a `yield`, a
        `utils.delay`, or a deferred call anywhere between the check and the
        credit reopens the duplication window for the entire economy.

        Deliberately NOT logged (S4-4): transfers are the normal business of the
        game, and the invariant -- not a transaction log -- is what proves
        nothing was created. `reason` is accepted for call-site readability and
        for future use; it is not persisted today.

        Args:
            target (Object): recipient. Must have a `currency` handler.
            amount (int): positive amount in Copper.
            reason (str, optional): free-text label, not persisted.

        Returns:
            bool: False if this wallet cannot cover `amount` -- and in that case
                NEITHER wallet is touched. True on success.

        Raises:
            TypeError: if `amount` is not an int, or `target` has no wallet.
            ValueError: if `amount` is not positive, or `target` is self.
        """
        self._require_positive(amount)

        if target is self.obj:
            # Not a runtime condition anyone can be in -- a self-payment is
            # always a caller bug or unvalidated input. Returning False would
            # conflate it with poverty (D7). B.2 catches `pay ... to me` first
            # and says something friendly; this is the backstop.
            raise ValueError("Cannot transfer currency to self.")

        target_wallet = getattr(target, "currency", None)
        if not isinstance(target_wallet, CurrencyHandler):
            raise TypeError(
                f"{target!r} has no currency handler; cannot receive a transfer."
            )

        # ---- BEGIN ATOMIC SECTION -- no yields past this line ----
        current = self.value
        if current < amount:
            return False

        self._set(current - amount)
        target_wallet._set(target_wallet.value + amount)
        # ---- END ATOMIC SECTION ----

        return True

    def __repr__(self):
        return f"<CurrencyHandler({self.obj}): {self.value} copper>"
