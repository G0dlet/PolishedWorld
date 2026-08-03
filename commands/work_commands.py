"""
The temple faucet (Stage 4, Component D.1).

THE ONE LINE THAT MATTERS
-------------------------
The payout is `treasury.currency.transfer_to(caller, ...)`. It is NEVER
`caller.currency.add(...)`.

That is decomposition S4-1 expressed as a fact about this file. `add()` is the
mint primitive and has exactly ONE production caller in the entire codebase --
`CmdEconomy` in `commands/currency_commands.py`. A faucet that minted would be a
second, unbounded, unaudited source of money whose failure stays invisible until
the inflation is obvious. `MINT_SOURCES` does not contain `"faucet"`, so
`add(amount, source="faucet")` raises `ValueError` and `tests/test_currency.py`
asserts that it does -- but the real guard is that this module never reaches for
it at all. `tests/test_work_command.py` greps this file's source for the string
as a regression test, because a comment is not an invariant.

The money the temple hands out was minted into the Treasury once, by an admin,
through `@economy mint`, against a recorded GameGold reserve obligation. The
faucet only moves it.

WHERE THE TEMPLE IS (locked, Component C session)
-------------------------------------------------
There is no `TEMPLE_DBREF`. `work` requires that the canonical Treasury is in
the caller's current room -- the faucet works where the coffer stands.

⚠️ CONSEQUENCE WORTH KNOWING BEFORE YOU MOVE ANYTHING: **moving the Treasury
moves the faucet.** `@tel #<treasury> = #<somewhere>` relocates the temple's
paid work along with it, with no other configuration touched.

Why it is built this way: a second settings key could drift out of alignment
with `TREASURY_DBREF` and produce a temple that advertises work it cannot fund;
it is diegetically exact (you sweep the floor where the temple's money is kept);
"wrong room" and "no Treasury configured" collapse into one code path and one
sentence; and several temples later become free rather than needing a registry.

The cost, stated plainly: an admin who misconfigures `TREASURY_DBREF` while
standing in the temple is told there is no work here, with no diagnostic. That
is correct -- the player is not the admin, and `@economy` already distinguishes
unset / dangling / wrong-typeclass for whoever is meant to fix it.

WHY THE WORK TAKES TIME, AND WHAT THAT COSTS
--------------------------------------------
Sweeping a floor is not instantaneous in the fiction, so `work` is not
instantaneous in the interface: it messages, waits, and only then pays. That is
a deliberate choice with real hazards attached, and each one is handled here
rather than discovered later.

⚠️ **S4-R1 IS THE CONSTRAINT.** The balance read, the sufficiency check, the
debit and the credit must never be separated by a yield point. They are not:
`transfer_to()` performs all four in one unbroken synchronous block, and this
module calls it exactly once, entirely INSIDE `_finish_task()` -- after the
delay, never across it. There is deliberately no affordability check before the
delay. Checking "can the temple pay?" up front and paying twenty seconds later
would be precisely the check-here-commit-there shape the rule forbids, and the
gap would be twenty seconds wide.

What IS checked before the delay is existence and place -- is there a Treasury,
is it in this room -- because making someone wait to be told there is no temple
is bad manners, not because it is load-bearing. Both are re-checked afterwards,
and the re-check is what is trusted.

The other four hazards:

1. **Queueing.** Without a guard, `work sweep` five times schedules five
   payouts. `caller.ndb.working` blocks a second start, in the same shape as
   `ndb.resting` / `ndb._dying` already used in `typeclasses/characters.py`.
2. **Walking away mid-task.** `at_pre_move` clears the flag and says so
   immediately (the `rest` precedent). The location re-check in `_finish_task`
   is the backstop for the paths a move hook never sees -- teleport, death.
3. **`@reload` mid-task.** The delay is NOT persistent, and neither is `ndb`, so
   both die together. The task is silently abandoned; the cooldown was never
   set, so the player simply starts again and loses nothing but the wait. This
   symmetry is the reason `persistent=True` is not used: a persistent task
   would survive into a process where its in-memory marker did not.
4. **Logging out mid-task.** Under statue-logout the body stays in the room, so
   a payout would otherwise move coin into an unattended purse with nobody
   present to have earned it. `_finish_task` requires `has_account`, exactly as
   `_rest_tick` does.

A STALE CALLBACK MUST NOT PAY A NEW TASK
----------------------------------------
Start sweeping, walk out, come back, start sweeping again: the first delay is
still in flight and would land on the second attempt. Each start therefore mints
a unique in-memory marker object and `_finish_task` refuses to act unless the
marker it was given is still the one on the character, by identity. A task key
alone is not enough -- the collision above uses the same key twice.

THE COOLDOWN IS ONLY EVER SET BY A PAYOUT THAT HAPPENED
-------------------------------------------------------
Locked decision: all-or-nothing. A dry Treasury pays nothing, and the cooldown
stays unset. An attempt that gave the player no money must not also cost them
their next attempt. `transfer_to()` returning False means exactly one thing here
(insufficient funds, D7) and touches neither wallet, so there is nothing to roll
back -- the cooldown line simply never runs.

Cooldowns are in real wall-clock seconds via `CooldownHandler` (Evennia
Reference §6), matching `forage`/`hunt`/`repair`/`craft`. Throttling player
action spam is a real-time phenomenon, not a game-time one.

The full chain of all five chores (170 Copper) is deliberately available in one
sitting. The cooldowns are per task, not global, and that is not an oversight:
the real brake on faucet farming is that the Treasury is finite and can run dry,
which is diegetic and self-limiting. A global cooldown would make the differing
per-task values meaningless.
"""

from evennia.utils import logger
from evennia.utils.utils import delay

from commands.command import Command
from typeclasses.treasury import get_treasury
from world.currency import format_copper

# --------------------------------------------------------------------------
# The task table -- the tuning anchor
# --------------------------------------------------------------------------
#
# Lives here rather than in `world/` on the house precedent: FORAGE_COOLDOWN,
# HUNT_COOLDOWN, REPAIR_COOLDOWN and TEACH_COOLDOWN all sit in the command
# module that reads them. One consumer, one small table. If a second consumer
# ever appears (an admin readout, NPC-driven chores) it moves then; moving a
# dict is trivial, and an import indirection bought now for a consumer that may
# never exist is not.
#
# It deliberately does NOT live in `world/currency.py`. That module is
# denomination arithmetic with no game domain in it and no colour (D2); a
# flavour string there would be the first crack in that separation.
#
# Rewards and cooldowns are canonical from PolishedWorld_GameGold_Economy.md's
# task table (Rev 4). NOTE a doc-vs-doc discrepancy flagged rather than silently
# resolved: that document's *prose table* lists five chores and its *code
# sketch* fifty lines below lists three. The table is the source per
# decomposition §6/D; the sketch is illustrative. Recorded for Component F.
#
# Flavour is carried in the data rather than generated from the key, because
# the house puts flavour with the data everywhere else -- `eat` reads
# `obj.consume_message` off the item and gives the room only "X eats Y." There
# is no item here, so the table IS the item.
#
# Keys are short because they are what the player types. `name` is what the
# player reads.
#
# `duration` is how long the chore takes in real seconds, and roughly tracks the
# reward. Kept short on purpose: this is a MUD, and the mechanic that actually
# represents "this took an hour of temple time" is the cooldown, not the wait.
TEMPLE_TASKS = {
    "sweep": {
        "name": "sweep the floors",
        "copper": 25,
        "cooldown": 3600,
        "duration": 20,
        "begin_actor": "You take up a worn broom and begin sweeping the flagstones.",
        "begin_room": "takes up a broom and begins sweeping the flagstones.",
        "done_actor": "The dust is out of the corners and the floor is clean.",
        "done_room": "finishes sweeping the temple floor.",
    },
    "water": {
        "name": "fetch water",
        "copper": 35,
        "cooldown": 3600,
        "duration": 20,
        "begin_actor": "You shoulder the yoke and set off for the well.",
        "begin_room": "shoulders a water yoke and heads for the well.",
        "done_actor": "You set the last full pail down beside the basin, arms aching.",
        "done_room": "returns with full pails and fills the basin.",
    },
    "books": {
        "name": "organize books",
        "copper": 50,
        "cooldown": 7200,
        "duration": 30,
        "begin_actor": "You start sorting the scattered volumes back onto their shelves.",
        "begin_room": "begins sorting scattered volumes back onto the shelves.",
        "done_actor": "Every volume is shelved in its proper order. It took a while.",
        "done_room": "shelves the last of the scattered volumes.",
    },
    "candles": {
        "name": "light the candles",
        "copper": 25,
        "cooldown": 3600,
        "duration": 15,
        "begin_actor": "You take a taper and start working your way along the candle racks.",
        "begin_room": "takes a taper and starts along the candle racks.",
        "done_actor": "The racks are lit, and the hall is warmer for it.",
        "done_room": "lights the last of the candles.",
    },
    "altar": {
        "name": "clean the altar",
        "copper": 35,
        "cooldown": 7200,
        "duration": 25,
        "begin_actor": "You fetch cloth and oil and begin working over the altar stone.",
        "begin_room": "fetches cloth and oil and begins working over the altar stone.",
        "done_actor": "The stone is clean, the wax scraped away, the brass bright.",
        "done_room": "steps back from the altar, the stone clean and the brass bright.",
    },
}


def _validate_task_table(tasks):
    """
    Fail at import time on a mistuned table, not in a player's face.

    Same discipline as the `_MINT_SOURCE` / `_BURN_REASON` constants in
    `commands/currency_commands.py`: a typo should be an error the moment the
    module loads, while somebody is looking at it.

    The concrete failure being prevented: `transfer_to()` calls
    `_require_positive()`, which RAISES on a zero or negative amount rather than
    returning False (D7 -- False means "could not afford" and nothing else). A
    chore accidentally tuned to `"copper": 0` would therefore hand a player a
    traceback twenty seconds after they started sweeping, in a delayed callback
    with no command context to report it.

    Args:
        tasks (dict): the table to check.

    Raises:
        ValueError: on any missing key or non-positive number.
    """
    required_text = ("name", "begin_actor", "begin_room", "done_actor", "done_room")
    required_numbers = ("copper", "cooldown", "duration")

    for key, task in tasks.items():
        for field in required_text:
            if not task.get(field):
                raise ValueError(f"TEMPLE_TASKS['{key}'] is missing '{field}'.")
        for field in required_numbers:
            value = task.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(
                    f"TEMPLE_TASKS['{key}']['{field}'] must be a positive int, "
                    f"got {value!r}."
                )


_validate_task_table(TEMPLE_TASKS)


# The cooldown key namespace. Per task, not global -- see the module docstring.
def _cooldown_key(task_key):
    """The `CooldownHandler` key for one chore. Namespaced to avoid collisions."""
    return f"faucet_{task_key}"


def _format_wait(seconds):
    """
    Render a wait as something a person would say.

    `forage` prints a bare `{left}s`, which is fine for a sixty-second cooldown
    and unreadable for a two-hour one -- "6821s" is a number, not an answer.

    Args:
        seconds (int): seconds remaining, as from `time_left(use_int=True)`.

    Returns:
        str: e.g. "45 seconds", "12 minutes", "1 hour 54 minutes".
    """
    seconds = max(int(seconds), 0)
    if seconds < 60:
        return f"{seconds} seconds"

    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if not hours:
        return f"{minutes} minutes" if minutes != 1 else "1 minute"

    hour_part = "1 hour" if hours == 1 else f"{hours} hours"
    if not minutes:
        return hour_part
    minute_part = "1 minute" if minutes == 1 else f"{minutes} minutes"
    return f"{hour_part} {minute_part}"


def _resolve_task(raw):
    """
    Match player input to a chore.

    Args:
        raw (str): whatever the player typed after `work`.

    Returns:
        tuple[str | None, list[str]]: `(task_key, candidates)`. On a unique
            match `task_key` is set and `candidates` is empty. On an ambiguous
            match `task_key` is None and `candidates` holds the keys that
            matched, so the caller can list them. On no match both are empty.

    Three passes, narrowest first, so an exact key always wins over a
    coincidental substring: exact key, then key prefix, then substring of the
    display name (`work floors` should find `sweep`).
    """
    text = raw.strip().lower()
    if not text:
        return None, []

    if text in TEMPLE_TASKS:
        return text, []

    prefixed = [key for key in TEMPLE_TASKS if key.startswith(text)]
    if len(prefixed) == 1:
        return prefixed[0], []
    if prefixed:
        return None, prefixed

    named = [key for key, task in TEMPLE_TASKS.items() if text in task["name"]]
    if len(named) == 1:
        return named[0], []
    return None, named


def _temple_here(caller):
    """
    The Treasury, if it is standing in the caller's room.

    Returns:
        Object | None: the Treasury, or None if there is none configured, it
            does not resolve, or it is somewhere else.

    All three absences are ONE answer on purpose (locked, Component C session).
    They collapse into one sentence for the player -- "there is no work to be
    had here" -- which is true in a forest and true in an unendowed temple, and
    which does not leak configuration state to someone who cannot act on it.
    An admin who needs the three distinguished has `resolve_treasury()` behind
    `@economy`.
    """
    treasury = get_treasury()
    if treasury is None:
        return None
    if not caller.location or treasury.location != caller.location:
        return None
    return treasury


# --------------------------------------------------------------------------
# The delayed payout
# --------------------------------------------------------------------------
#
# A module-level function rather than a closure or a bound method of the
# Command, for two reasons. First, a Command instance is per-invocation and
# keeping one alive for twenty seconds purely to hold a callback is more object
# lifetime than the job needs. Second and more usefully: a module-level function
# is directly callable from a test, which is the difference between testing the
# payout and testing a reactor.


def _finish_task(caller, task_key, marker):
    """
    Complete a chore and pay for it. Runs `duration` seconds after the start.

    Args:
        caller (Object): the worker.
        task_key (str): key into `TEMPLE_TASKS`.
        marker (object): the identity token minted at start time. The payout
            is refused unless this is still the token on the character.

    ⚠️ EVERY early return in this function leaves the cooldown UNSET. That is
    the locked all-or-nothing rule: an attempt that paid nothing must not cost
    the player their next attempt. The single `cooldowns.add()` call sits after
    a successful `transfer_to()` and nowhere else.

    ⚠️ S4-R1: `transfer_to()` is the only balance operation here, it is called
    once, and nothing is read or decided about the Treasury's balance before it.
    """
    # The character was deleted, or the marker is stale -- this callback belongs
    # to an attempt that was cancelled, superseded, or lost to a reload. Silent
    # on purpose: whoever cleared the marker (at_pre_move, a second `work`) has
    # already said whatever needed saying, and a second message here would be a
    # message about an attempt the player has stopped thinking about.
    if not caller.pk or caller.ndb.working is not marker:
        return

    caller.ndb.working = None

    task = TEMPLE_TASKS.get(task_key)
    if not task:
        # Only reachable if the table changed under a live delay (a `@reload`
        # kills the delay, but a hot edit in a test could). Nothing to pay for.
        logger.log_err(f"work: unknown task key {task_key!r} at payout.")
        return

    # Logged out mid-chore. Under statue-logout the body is still standing in
    # the room, so without this the temple would pay coin into an unattended
    # purse. `_rest_tick` guards itself the same way, for the same reason.
    if not caller.has_account:
        return

    # Re-check, and THIS is the check that counts -- the pre-delay one was
    # courtesy. Covers walking out by any route a move hook never sees
    # (teleport, death, the Treasury itself being moved mid-chore).
    treasury = _temple_here(caller)
    if treasury is None:
        caller.msg("You look up from your work. There is no work to be had here.")
        return

    # ---- S4-R1: the check AND the commit, in one call, after the wait ----
    # No affordability read above this line. False means exactly one thing --
    # the coffers cannot cover it (D7) -- because every other failure mode
    # raises, and the table validation at import has screened out the inputs
    # that would raise. `reason` is not persisted (S4-4); transfers are not
    # logged, and a faucet payout is a transfer.
    if not treasury.currency.transfer_to(caller, task["copper"], reason="faucet"):
        # Dry. The work was done and there is nothing to pay with. Diegetic, not
        # an error -- a finite Treasury that can run out is a feature (S4-1),
        # and this is what running out looks like from inside the world.
        caller.msg(
            f"{task['done_actor']}\n"
            "You go looking for the almoner, but the temple's alms box is bare. "
            "There is nothing here to pay you with."
        )
        return

    # Only now, and only here.
    caller.cooldowns.add(_cooldown_key(task_key), task["cooldown"])

    caller.msg(
        f"{task['done_actor']}\n"
        f"The temple pays you |y{format_copper(task['copper'])}|n for your trouble."
    )

    # The room sees the ACT, never the AMOUNT -- the same line `pay` draws, and
    # for the same reason. What a bystander learns from watching should be that
    # you did the work, not what you are carrying afterwards.
    if caller.location:
        caller.location.msg_contents(
            f"{caller.get_display_name()} {task['done_room']}",
            exclude=caller,
        )


class CmdWork(Command):
    """
    Do paid chores for the temple

    Usage:
        work
        work <chore>

    Examples:
        work
        work sweep
        work altar

    The temple pays a few coppers for honest small work. It is not a living --
    it is enough to eat on while you find your feet, and it is meant to be left
    behind for crafting and trade.

    `work` on its own reads the board: what needs doing, what it pays, and
    whether you have done it recently. Each chore has its own waiting period.

    Chores take a little time to do. Walk out part way through and you have done
    nothing and earned nothing.

    The temple pays out of its own coffers, and those coffers are finite. If
    donations have run thin there may be nothing to pay you with, however
    willing you are.
    """

    key = "work"
    locks = "cmd:all()"
    help_category = "Economy"

    # One sentence, three callers (no Treasury, wrong room, no Treasury
    # resolvable). Collapsing them is the locked decision, and a single constant
    # is what stops the three from drifting into three different sentences that
    # would let a player distinguish them again.
    _NO_TEMPLE = "There is no work to be had here."

    def func(self):
        caller = self.caller

        # Defensive in the same shape as CmdWallet/CmdPay. Every Character has
        # the lazy_property, but a cmdset can be merged onto something that is
        # not one, and a sentence beats a traceback.
        if not hasattr(caller, "currency"):
            caller.msg("You have no way to be paid for work.")
            return

        # The place gate comes BEFORE the listing, deliberately: the list of
        # chores is the temple's notice board, and a notice board hangs on a
        # wall. Reading it from a forest would make the faucet a menu that
        # follows you around. This is also the discovery message -- someone who
        # types `work` out of curiosity is told, in world, where it applies.
        treasury = _temple_here(caller)
        if treasury is None:
            caller.msg(self._NO_TEMPLE)
            return

        raw = self.args.strip()
        if not raw:
            self._show_board(caller)
            return

        task_key, candidates = _resolve_task(raw)
        if not task_key:
            if candidates:
                names = ", ".join(f"|w{key}|n" for key in sorted(candidates))
                caller.msg(f"Which one? You could mean: {names}.")
            else:
                caller.msg(
                    f"The temple has no chore like '|w{raw}|n'. "
                    "Try |wwork|n to see what needs doing."
                )
            return

        task = TEMPLE_TASKS[task_key]

        # Already mid-chore. Blocks the queue: without this, five `work sweep`
        # in a row schedule five payouts and the cooldown gate below never sees
        # any of them, because none has fired yet.
        if caller.ndb.working:
            caller.msg("You are already busy with something.")
            return

        cd_key = _cooldown_key(task_key)
        if not caller.cooldowns.ready(cd_key):
            left = caller.cooldowns.time_left(cd_key, use_int=True)
            caller.msg(
                f"You have done that recently; the temple has no need of it again "
                f"for another {_format_wait(left)}."
            )
            return

        # ⚠️ NOTHING about the Treasury's BALANCE is read here. Only that it
        # exists and is in this room, both re-checked at payout. Asking "can it
        # pay?" now and paying later is the check-here-commit-there shape S4-R1
        # exists to forbid, and the gap would be `duration` seconds wide.

        # A fresh identity token per attempt. A task key alone would let a stale
        # callback from an abandoned attempt land on a later one with the same
        # key; `object()` cannot collide with anything, including itself on a
        # second call.
        marker = object()
        caller.ndb.working = marker

        caller.msg(task["begin_actor"])
        if caller.location:
            caller.location.msg_contents(
                f"{caller.get_display_name()} {task['begin_room']}",
                exclude=caller,
            )

        # persistent=False (the default), stated here because it is a decision
        # rather than an omission: the marker is an in-memory object, so a task
        # that survived a reload would wake up holding a reference to nothing.
        # ndb and the delay are meant to die together. See the module docstring.
        delay(task["duration"], _finish_task, caller, task_key, marker)

    def _show_board(self, caller):
        """
        The notice board: every chore, what it pays, and whether it is available.

        The reward is shown, and that is a decision. A temple that pays for
        chores but will not say what it pays is a puzzle, not a temple. Nothing
        is protected by hiding it -- the faucet is a fixed rate, not a market
        price, so a hidden number is hidden only from the player who has not
        tried yet, which is exactly the new player this whole system exists for.
        And the visible low number does the design's own work: 25 Copper next to
        what a crafted item is worth teaches in one glance that this is a
        supplement, not a career. An invisible number lets people imagine it is
        worth grinding.

        What is NOT shown is whether the coffers can currently cover it. That
        would leak Treasury state to players and give them a board that changes
        under their feet; dryness is discovered by trying, in world.
        """
        # Local, not a module constant -- CmdWallet and CmdProgress both do
        # this, and the rule belongs to the display rather than the module.
        rule = "|g" + "=" * 52 + "|n"

        lines = [f"\n|wThe temple's board of small work:|n\n{rule}"]
        for key, task in TEMPLE_TASKS.items():
            cd_key = _cooldown_key(key)
            if caller.cooldowns.ready(cd_key):
                status = "|gready|n"
            else:
                left = caller.cooldowns.time_left(cd_key, use_int=True)
                status = f"|xin {_format_wait(left)}|n"
            # No pipe characters in the layout: Evennia's parser reads `|` as a
            # markup lead-in (Testing Reference §9), so columns are spaces.
            lines.append(
                f"  |w{key:<9}|n {task['name']:<22} "
                f"|y{format_copper(task['copper']):<12}|n {status}"
            )
        lines.append(rule)
        lines.append("  |wwork <chore>|n to take one on.")

        caller.msg("\n".join(lines))
