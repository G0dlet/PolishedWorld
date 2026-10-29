"""
Encumbrance reader (Weight and Encumbrance, Tasks W1.1, W2.1, W2.2).

Pure functions over objects. This module owns no state: it stores nothing,
caches nothing and writes nothing. Every answer is computed from what the
objects carry at the moment of asking, so a `get`, a `drop`, a craft or a
change to STR or SIZ is reflected on the next read without a ticker, a buff
or a migration (decomposition WD3 b: a cache is a second writer).

THE ONE IDEA
------------
ENC is a property of items; encumbrance is a sum over what a holder carries,
compared against STR+SIZ:

    item       : item_enc(obj)              -> int   (the `enc` Attribute)
    holder     : carried_enc(holder)        -> int   (recursive sum, WD4, WD5)
                 enc_after_receiving(holder, obj) -> int   (the sum with obj in, W2.1)
                 enc_without(holder, obj, elsewhere) -> int (the sum with obj out, W2.2)
    band       : band(carried, limit)       -> FREE | OVERLOADED | CEILING (WD2)
    character  : enc_limit(char)            -> int   (STR+SIZ, WD1)
                 encumbrance_state(char)    -> band(carried_enc, enc_limit)

LOCKED DECISIONS (docs/PolishedWorld_Weight_Decomposition.md, Rev 2)
---------------------------------------------------------------------
* A missing `enc` reads 0, silently -- test objects and builder-made objects
  weigh nothing rather than raising. A value `int()` refuses (None, "heavy")
  or a negative one also reads 0, but logs a warning: a negative `enc` would
  make its carrier *lighter*, which is an exploit, not a data slip.
* The walk skips characters by inheritance and exits by `destination`.
  `has_account` is not used: it is `sessions.count()`, so it is False for
  every character without a logged-in session (a logout statue, an NPC,
  the test fixture's char2).
* Depth guard: the holder's own contents are depth 1. An object at
  MAX_DEPTH counts its own `enc` but is not descended into, and a warning is
  logged -- containers never nest (WD5), so reaching the guard means that
  check failed somewhere.
* States are module constants, so W2 and W3 never spell one by hand.

Boundaries (`band`, the one place the rule lives): FREE at or below the
limit; OVERLOADED above it, up to and including OVERLOAD_FACTOR x limit;
CEILING above that.
"""

from evennia.utils import logger
from evennia.utils.utils import inherits_from

# Legend core p.86: "around twenty" items too light to score an ENC of their
# own count as 1 ENC together. Applied wherever they are carried (WD4).
SMALL_ITEMS_PER_ENC = 20

# Legend core p.86 (beasts of burden, "never more than double" their ENC
# Carried), borrowed for people as the ceiling (WD2 -- an adaptation).
OVERLOAD_FACTOR = 2

# Recursion guard. Depth is 2 in practice (a container on a character, WD5).
MAX_DEPTH = 4

# Legend core p.86: -20% to "all tests that require physical actions,
# including Weapon Skill Tests and most tests that have DEX or STR" while the
# character carries more than its limit (W3.1). OVERLOADED and CEILING alike;
# read through Character.physical_modifier() at the moment of each roll.
OVERLOAD_PENALTY = -20

FREE = "free"
OVERLOADED = "overloaded"
CEILING = "ceiling"

_CHARACTER_PATH = "evennia.objects.objects.DefaultCharacter"


def item_enc(obj):
    """
    Return the ENC of one object, never negative.

    Args:
        obj (Object): any typeclassed object.

    Returns:
        int: the `enc` Attribute coerced to int; 0 if missing, malformed or
            negative (the last two with a logged warning).
    """
    raw = obj.attributes.get("enc", default=0)
    try:
        value = int(raw)
    except (TypeError, ValueError, OverflowError):
        logger.log_warn(
            f"encumbrance: {obj.key}(#{obj.id}) has enc={raw!r} "
            f"({type(raw).__name__}); read as 0."
        )
        return 0
    if value < 0:
        logger.log_warn(
            f"encumbrance: {obj.key}(#{obj.id}) has negative enc={raw!r}; read as 0."
        )
        return 0
    return value


def _is_skipped(obj):
    """Characters and exits are never carried weight."""
    return bool(obj.destination) or inherits_from(obj, _CHARACTER_PATH)


def _walk(holder, depth, exclude=None):
    """
    Sum ENC under `holder`; return (enc_total, count_of_items_at_zero).

    `depth` is the depth of `holder`'s contents (1 for the outermost call).
    `exclude` is left out with everything it holds, wherever it sits in the
    tree (W2.2: the sum as if that object were somewhere else).
    """
    total = 0
    zeros = 0
    for obj in holder.contents:
        if obj == exclude or _is_skipped(obj):
            continue
        enc = item_enc(obj)
        if enc:
            total += enc
        else:
            zeros += 1
        if obj.contents:
            if depth >= MAX_DEPTH:
                logger.log_warn(
                    f"encumbrance: {obj.key}(#{obj.id}) holds objects at depth "
                    f"{depth + 1} under {holder.key}(#{holder.id}); not counted."
                )
                continue
            sub_total, sub_zeros = _walk(obj, depth + 1, exclude)
            total += sub_total
            zeros += sub_zeros
    return total, zeros


def carried_enc(holder):
    """
    Total ENC carried by `holder`, its own ENC excluded.

    Recursive (a container's contents count fully for its carrier, WD5);
    items at `enc` 0 are counted over the whole tree and add one ENC per
    SMALL_ITEMS_PER_ENC (WD4).

    Args:
        holder (Object): a character, a container, any object with contents.

    Returns:
        int
    """
    total, zeros = _walk(holder, 1)
    return total + zeros // SMALL_ITEMS_PER_ENC


def _is_carried_by(obj, holder):
    """
    True when `obj`'s location chain reaches `holder` within MAX_DEPTH hops.

    One hop is depth 1 (directly in `holder`), so this reaches exactly the
    objects `_walk(holder, 1)` counts: moving one of them to `holder` does not
    change `holder`'s sum.
    """
    loc = obj.location
    for _ in range(MAX_DEPTH):
        if loc is None:
            return False
        if loc == holder:
            return True
        loc = loc.location
    return False


def enc_after_receiving(holder, obj):
    """
    The value `carried_enc(holder)` would have with `obj` in `holder` (W2.1).

    `obj` counts as one more item at depth 1: its own ENC, its contents
    through the same walk, and the twenty-to-one rule applied once over the
    merged count of items at `enc` 0 (WD4) -- the sum of two rounded-down
    parts would undercount. Two cases change nothing and return the current
    sum: `obj` is already in `holder`'s carried tree (a `get` from a carried
    sack), or `obj` is something the walk never counts (a character, an exit).

    Args:
        holder (Object): the would-be carrier.
        obj (Object): the arriving object.

    Returns:
        int
    """
    if _is_skipped(obj) or _is_carried_by(obj, holder):
        return carried_enc(holder)
    total, zeros = _walk(holder, 1)
    enc = item_enc(obj)
    if enc:
        total += enc
    else:
        zeros += 1
    if obj.contents:
        sub_total, sub_zeros = _walk(obj, 2)
        total += sub_total
        zeros += sub_zeros
    return total + zeros // SMALL_ITEMS_PER_ENC


def enc_without(holder, obj, elsewhere):
    """
    The value `carried_enc(holder)` has with `obj` at `elsewhere` (W2.2).

    `obj` is in `holder`'s carried tree when this is asked: the leave hook
    asks before the move, the receive hook after it. Its own ENC and
    everything it holds are left out, and the twenty-to-one rule runs once
    over what remains (WD4) -- subtracting `item_enc(obj)` from the sum would
    miss the twentieth item at `enc` 0. When `elsewhere` is `holder` or
    inside its carried tree (a `put` into a carried sack, a `get` from one)
    the item stays carried, and the current sum is returned. A character or
    an exit changes nothing without a case of its own: the walk never
    counted it.
    `elsewhere` is None when an object is created in place
    (`create_object(location=holder)`, objects.py:1975): it was nowhere.

    Args:
        holder (Object): the carrier.
        obj (Object): the moving object, in `holder`'s carried tree.
        elsewhere (Object or None): where `obj` is going, or came from.

    Returns:
        int
    """
    if elsewhere is not None and (
        elsewhere == holder or _is_carried_by(elsewhere, holder)
    ):
        return carried_enc(holder)
    total, zeros = _walk(holder, 1, exclude=obj)
    return total + zeros // SMALL_ITEMS_PER_ENC


def enc_limit(char):
    """
    The character's carrying limit: STR + SIZ, read live (WD1).

    Returns:
        int
    """
    return int(char.stats.str.value + char.stats.siz.value)


def band(carried, limit):
    """
    Return FREE, OVERLOADED or CEILING for a sum against a limit (WD2).

    The one place the band rule lives: `encumbrance_state` reads a character
    through it, and the crossing messages and the inventory line (W2.2) put
    their own sums through it.

    Args:
        carried (int): an ENC sum.
        limit (int): the carrier's limit.

    Returns:
        str: one of the module constants.
    """
    if carried > OVERLOAD_FACTOR * limit:
        return CEILING
    if carried > limit:
        return OVERLOADED
    return FREE


def encumbrance_state(char):
    """
    Return FREE, OVERLOADED or CEILING for a character (WD2).

    `carried_enc` and `enc_limit` are looked up in this module on every
    call, so a patch of either reaches the answer (W1.2's spy and patch
    tests).

    Returns:
        str: one of the module constants.
    """
    return band(carried_enc(char), enc_limit(char))
