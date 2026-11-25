"""
commands/gear_commands.py

`wield` and `unwield`: a player takes an item in hand and puts it away
(Gear decomposition GR-T8; locks GR4, GR5; GR-T8's STOPP 0).

    wield <item> [right|left]    alias `hold`; anything carried can be held
    unwield <item>

The commands hold no rule of the hands: every refusal is `gear.hold`'s
reason, said to the caller as it comes. The one rule they ask first is the
body's: a collapsed or unconscious body is refused by
`Character.refuse_if_collapsed` (S3.4, WN11), as `eat` and `drink` are.

One line goes to the whole room, the caller included, as the clothing
contrib's `wear` does (clothing.py:288-291): the holder through `$You()`
and `$pron()`, the item through `mapping`, so each reader gets the names
they know (Combat Design TR3).

Not a timed action: *Ready Weapon* costs a Combat Action in a fight
(core p. 128), which is ML's.
"""

from commands.command import Command
from world import fatigue, gear

# The lines (GR-T8's STOPP 0, val 3, A). One string for every reader.
WIELD_ONE = "$You() $conj(take) the {item} in $pron(your) {hand} hand."
WIELD_BOTH = "$You() $conj(take) the {item} in both hands."
UNWIELD = "$You() $conj(put) away the {item}."

WIELD_WHAT = "Wield what?"
UNWIELD_WHAT = "Unwield what?"
NOT_HOLDING = "You aren't holding that."


def _announce(caller, text, obj, hand=None):
    """The line to the room, the caller included (no room, no line)."""
    if caller.location is not None:
        caller.location.msg_contents(
            text, from_obj=caller, mapping={"item": obj, "hand": hand or ""},
        )


class CmdWield(Command):
    """
    take something in hand

    Usage:
      wield <item> [right|left]
      hold <item> [right|left]

    Takes something you carry in your right hand if it is free, and in your
    left otherwise; name a hand to choose it. A shield goes to the left first.
    A two-handed weapon takes both hands and needs both free. Nothing is put
    away for you: free the hand first with |wunwield|n.
    """

    key = "wield"
    aliases = ["hold"]
    locks = "cmd:all()"
    help_category = "General"

    def parse(self):
        """
        Split off a last word that names a hand, when there is something
        before it: `wield club left` names the left hand, `wield left` looks
        for an item called *left*.
        """
        self.query = self.args.strip()
        self.hand = None
        words = self.query.split()
        if len(words) > 1 and words[-1].lower() in gear.HANDS:
            self.hand = words[-1].lower()
            self.query = " ".join(words[:-1])

    def func(self):
        caller = self.caller
        if caller.refuse_if_collapsed(fatigue.CANNOT_HANDLE):
            return
        if not self.query:
            caller.msg(WIELD_WHAT)
            return
        obj = caller.search(self.query, candidates=caller.contents)
        if not obj:
            return
        hands, reason = gear.hold(caller, obj, self.hand)
        if reason:
            caller.msg(reason)
            return
        if len(hands) == len(gear.HANDS):
            _announce(caller, WIELD_BOTH, obj)
        else:
            _announce(caller, WIELD_ONE, obj, hands[0])


class CmdUnwield(Command):
    """
    put away what you hold

    Usage:
      unwield <item>

    Puts away something you hold; you still carry it.
    """

    key = "unwield"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        if caller.refuse_if_collapsed(fatigue.CANNOT_HANDLE):
            return
        query = self.args.strip()
        if not query:
            caller.msg(UNWIELD_WHAT)
            return
        obj = caller.search(query, candidates=caller.contents)
        if not obj:
            return
        if not gear.release(caller, obj):
            caller.msg(NOT_HOLDING)
            return
        _announce(caller, UNWIELD, obj)
