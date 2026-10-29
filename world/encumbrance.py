"""
Encumbrance reader (Weight and Encumbrance, Task W1.1).

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
    character  : enc_limit(char)            -> int   (STR+SIZ, WD1)
                 encumbrance_state(char)    -> FREE | OVERLOADED | CEILING (WD2)

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

Boundaries: FREE at or below the limit; OVERLOADED above it, up to and
including OVERLOAD_FACTOR x limit; CEILING above that.
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


def _walk(holder, depth):
    """
    Sum ENC under `holder`; return (enc_total, count_of_items_at_zero).

    `depth` is the depth of `holder`'s contents (1 for the outermost call).
    """
    total = 0
    zeros = 0
    for obj in holder.contents:
        if _is_skipped(obj):
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
            sub_total, sub_zeros = _walk(obj, depth + 1)
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


def enc_limit(char):
    """
    The character's carrying limit: STR + SIZ, read live (WD1).

    Returns:
        int
    """
    return int(char.stats.str.value + char.stats.siz.value)


def encumbrance_state(char):
    """
    Return FREE, OVERLOADED or CEILING for a character (WD2).

    Returns:
        str: one of the module constants.
    """
    carried = carried_enc(char)
    limit = enc_limit(char)
    if carried > OVERLOAD_FACTOR * limit:
        return CEILING
    if carried > limit:
        return OVERLOADED
    return FREE
