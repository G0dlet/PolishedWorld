"""
Currency denomination maths, parsing and rendering (Stage 4, Component A.1).

A dependency-free module: no Evennia import, no database, no typeclass. Every
function here is pure, which is why the whole of A.1 can be tested with the
lightest test base class (`EvenniaTestCase`) and why the wallet handler (A.2,
same module) can lean on it without any layering problem.

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
