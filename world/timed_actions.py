"""
world/timed_actions.py

The shared home for "this takes time and can be interrupted" (Epic A, TA1.1).

ONE SLOT, ONE BRANCH
--------------------
Every timed player action -- a temple chore, a rest, a craft -- occupies the
SAME slot: `character.ndb.timed_action`. That is the whole point of the module
(decomposition D1). Before it, `rest` and `work` each carried their own ndb flag
and `at_pre_move` grew one hand-written branch per action. With one slot,
`at_pre_move` collapses to a single `interrupt()` call that no future action has
to extend.

The slot holds a `_Record`, and the record's `marker` is an `object()` minted at
start time. Identity -- not equality, not the action key -- is what says "this
callback belongs to the attempt that is still running". A key alone is not
enough: start a chore, walk out, come back and start the same chore again, and
both attempts share the key while only one is live.

WHY ndb AND NOT db
------------------
`delay(..., persistent=False)` and `ndb` die together at `@reload`. A persistent
task would wake in a process where its in-memory marker no longer exists, so it
would either fire against nothing or (worse) against a fresh record it never
started. Non-persistence is the decision (D7), not an omission; an abandoned
action costs the player the wait and nothing else, because nothing is consumed
or paid before the callback runs.

THE TWO WAYS TO ASK "AM I STILL THE ONE?"
-----------------------------------------
`claim()` is DESTRUCTIVE and `is_current()` is NOT, and the difference is not
cosmetic. `work` and `craft` are one-shot: their callback fires once, takes the
slot and leaves it empty, so `claim()` is right. `rest` ticks over and over and
must ask "am I still current?" WITHOUT emptying the slot -- with `claim()` the
first tick would end the rest it was supposed to continue.

Both refuse a stale marker, a deleted character, and an unpuppeted one.

WHAT AN UNPUPPETED CHARACTER MEANS HERE
---------------------------------------
`Character.at_post_unpuppet()` deliberately does NOT call `super()`: the body
stays standing in the room (statue logout), so the object -- and its `ndb` --
outlive the session. That is why every entry point below checks `has_account`,
and why the checks that find it false CLEAR the slot instead of merely refusing.
A slot left occupied on a body nobody is puppeting is a character who is busy
forever, and the live implementations this module replaces both already clean up
on that path (`_finish_task` nulls the marker before its `has_account` check;
`_rest_tick` clears `ndb.resting` in the same branch that refuses).

WHAT THIS MODULE DOES NOT IMPORT
--------------------------------
Nothing from `commands/` or `typeclasses/`. `world/` is the lower layer and does
not reach upward -- notably `_format_wait` lives in `commands/work_commands.py`
and stays there. Durations here are plain seconds.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from evennia.utils.utils import delay


@dataclass(slots=True, eq=False)
class _Record:
    """
    The slot's contents. In-memory only, exactly like the delay it pairs with.

    `slots=True` keeps it cheap and typo-proof (assigning `.lable` raises rather
    than silently adding a field). `eq=False` because two records are never
    compared -- the only identity question asked about a record is about its
    `marker`, by `is`, and a generated `__eq__` over fields would quietly answer
    a different question if anyone ever reached for `==`.

    The generated `__repr__` is the reason this is a dataclass and not a bare
    class with `__slots__`: a record that turns up in a traceback or an `@py`
    readout prints as `_Record(key='work', label='working', ...)` instead of
    `<world.timed_actions._Record object at 0x7f...>`.
    """

    marker: object
    key: str
    label: str
    interrupt_msg: Optional[str] = None
    on_interrupt: Optional[Callable[[Any], None]] = None


def is_busy(char):
    """
    Return the record of the action currently occupying the slot, or None.

    A pure read: it never clears, never messages. Callers use it to BRANCH --
    `CmdRest` needs to tell "already resting" (toggle off) apart from "busy with
    something else" (refuse), and it must be able to ask that without disturbing
    anything.

    Args:
        char (Object): the character to inspect.

    Returns:
        _Record or None: the live record, or None when the slot is empty.
    """
    return char.ndb.timed_action


def start(char, key, seconds, callback, *args,
          label=None, interrupt_msg=None, on_interrupt=None):
    """
    Occupy the slot and schedule `callback` to fire `seconds` from now.

    The callback is invoked as `callback(char, *args, marker)` -- `char` is
    injected by this function and `marker` is appended last, matching the shape
    `_finish_task(caller, task_key, marker)` already has. Injecting `char`
    rather than letting the caller pass it means the callback can never be
    handed a different character than the one whose slot it is about to claim.

    Refusal is EXPLICIT (D3): when the slot is taken, this messages the caller
    naming the action in progress and returns None. The sentence lives here, in
    one place, rather than being retyped at every call site -- a format rule
    spread across three files is three places to forget it.

    Args:
        char (Object): the actor. The slot is per character, never global.
        key (str): machine-readable action key ("work", "rest", "craft").
        seconds (int or float): how long the action takes.
        callback (callable): invoked as `callback(char, *args, marker)`.
        *args: passed through to the callback, between `char` and `marker`.

    Keyword Args:
        label (str): present participle used in the busy message ("working").
            Defaults to `key`.
        interrupt_msg (str): what the actor is told when the action is cut
            short and no explicit reason is supplied to `interrupt()`.
        on_interrupt (callable): called as `on_interrupt(char)` after an
            interrupt, for effects the actor message cannot cover -- the room
            announcement when someone gets up from resting. It does NOT fire on
            normal completion; that is the callback's own business.

    Returns:
        object or None: the identity marker on success, None if already busy.

    Notes:
        `persistent=False` is `delay`'s default and is relied on: see the module
        docstring. `seconds` and `callback` are not validated -- every call site
        is in this repository, and a branch no test can reach is a branch that
        only ever adds surface.
    """
    record = is_busy(char)
    if record is not None:
        char.msg(f"You are already {record.label}.")
        return None

    # `object()` cannot collide with anything, including itself on a second
    # call. That is the entire mechanism: identity, not value.
    marker = object()
    char.ndb.timed_action = _Record(
        marker=marker,
        key=key,
        label=label or key,
        interrupt_msg=interrupt_msg,
        on_interrupt=on_interrupt,
    )
    delay(seconds, callback, char, *args, marker)
    return marker


def is_current(char, marker):
    """
    Non-destructively ask whether `marker` is still the live action.

    For REPEATING callbacks. `_rest_tick` runs many times for one rest and must
    leave the slot standing so the next tick still finds it.

    An unpuppeted character is refused AND cleaned up: the body outlives the
    session (statue logout), so a slot left behind here would never be emptied
    by anything except a reload.

    Args:
        char (Object): the actor.
        marker (object): the token handed out by `start()`.

    Returns:
        bool: True only if this marker is the one in the slot and the character
            is alive in the db and actively puppeted.
    """
    if not char.pk:
        return False
    record = char.ndb.timed_action
    if record is None or record.marker is not marker:
        return False
    if not char.has_account:
        char.ndb.timed_action = None
        return False
    return True


def claim(char, marker):
    """
    Destructively take the slot: the one-shot counterpart to `is_current`.

    For callbacks that fire exactly once (`work`, `craft`). On a matching marker
    the slot is emptied FIRST and unconditionally -- including when the
    character has since logged out -- and only then is `has_account` consulted.
    That ordering is deliberate and mirrors `_finish_task`: an attempt that will
    not be honoured must still stop occupying the slot.

    Args:
        char (Object): the actor.
        marker (object): the token handed out by `start()`.

    Returns:
        bool: True if the caller may proceed with the completion. False for a
            stale marker, a deleted character, or one nobody is puppeting.
    """
    if not char.pk:
        return False
    record = char.ndb.timed_action
    if record is None or record.marker is not marker:
        return False

    char.ndb.timed_action = None

    if not char.has_account:
        return False
    return True


def interrupt(char, reason=None):
    """
    Cut the current action short. A no-op when the slot is empty.

    This is what `at_pre_move` calls unconditionally -- one branch for every
    timed action there will ever be.

    `reason` wins over the record's `interrupt_msg` when supplied. Both spellings
    are needed: movement cuts a rest with "You get up, interrupting your rest."
    (recorded at start), while the `rest` toggle ends the same action with
    "You stop resting." (supplied at the call). One message baked in at start
    could not express both without restarting the action to change its wording.

    An unpuppeted character has the slot cleared but is NOT messaged, and
    `on_interrupt` does not run: messaging is acting, and nobody is there to be
    told or to be seen getting up.

    Args:
        char (Object): the actor.
        reason (str, optional): overrides the recorded interrupt message.

    Returns:
        bool: True if there was an action and it was cleared, else False.
    """
    if not char.pk:
        return False
    record = char.ndb.timed_action
    if record is None:
        return False

    char.ndb.timed_action = None

    if not char.has_account:
        return True

    message = reason if reason is not None else record.interrupt_msg
    if message:
        char.msg(message)
    if record.on_interrupt is not None:
        record.on_interrupt(char)
    return True
