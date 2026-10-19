"""

Lockfuncs

Lock functions are functions available when defining lock strings,
which in turn limits access to various game systems.

All functions defined globally in this module are assumed to be
available for use in lockstrings to determine access. See the
Evennia documentation for more info on locks.

A lock function is always called with two arguments, accessing_obj and
accessed_obj, followed by any number of arguments. All possible
arguments should be handled with *args, **kwargs. The lock function
should handle all eventual tracebacks by logging the error and
returning False.

Lock functions in this module extend (and will overload same-named)
lock functions from evennia.locks.lockfuncs.

"""

# def myfalse(accessing_obj, accessed_obj, *args, **kwargs):
#    """
#    called in lockstring with myfalse().
#    A simple logger that always returns false. Prints to stdout
#    for simplicity, should use utils.logger for real operation.
#    """
#    print "%s tried to access %s. Access denied." % (accessing_obj, accessed_obj)
#    return False

from evennia.utils import logger


def corpse_grace(accessing_obj, accessed_obj, *args, **kwargs):
    """
    Owner-first loot grace for a PlayerCorpse (lock string: `corpse_grace()`).

    Passes for the corpse's owner at any time, and for anyone once the grace
    has run out (`PlayerCorpse.grace_active`, an unscaled clock that never
    runs backwards). Takes no arguments: the owner is read from the corpse's
    `owner` Attribute at check time, so the id lives in one place.

    `owner` is a character id, stamped by `at_character_death()`. A deleted
    owner never matches an id again, so their body simply opens when the grace
    ends -- no lookup, no special case.

    Silent on purpose: the refusal line is the corpse's `get_from_err_msg`,
    printed by the command, so there is one writer per line.

    Evennia's LockHandler.check() calls lock functions without a try/except,
    so an exception here would reach the looter as a traceback. Instead it is
    logged and the check FAILS CLOSED: a broken corpse stays owner-only rather
    than being opened to everyone. The owner test runs first and needs no
    clock, so an owner is never locked out by a bad timestamp.
    """
    try:
        owner_id = accessed_obj.attributes.get("owner")
        if owner_id is not None and getattr(accessing_obj, "id", None) == owner_id:
            return True
        return not accessed_obj.grace_active
    except Exception:
        logger.log_trace(f"corpse_grace: check failed for {accessing_obj} on {accessed_obj}")
        return False
