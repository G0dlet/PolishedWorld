"""
Inventory commands (Weight and Encumbrance, Task W2.2).

Two contrib commands, each extended by one thing and otherwise unchanged.
Both replace their contrib command in commands/default_cmdsets.py.

    CmdInventory  clothing's worn/carried split (clothing.py:642), plus one
                  line: "Carrying 7/20 ENC", with " (overloaded)" outside
                  FREE. The number is the in-game receipt every weight
                  protocol reads.
    CmdGet        the containers contrib's `get` and `get ... from`
                  (containers.py:152), minus the contrib's own refusal line
                  when the ceiling hook (Character.at_pre_object_receive,
                  W2.1) has already said why.

Neither copies the contrib's `func`: both call `super().func()`, so a fix
upstream reaches them (W2.2 Q3).
"""

from evennia.contrib.game_systems.clothing.clothing import (
    CmdInventory as ClothingCmdInventory,
)
from evennia.contrib.game_systems.containers.containers import CmdContainerGet

from world import encumbrance

# containers.py:211 -- what CmdContainerGet says for any refused move_to.
CONTRIB_REFUSAL = "This can't be picked up."


class CmdInventory(ClothingCmdInventory):
    """
    view inventory

    Usage:
      inventory
      inv

    Shows what you carry and what you wear. The last line is the ENC you
    carry against your limit (STR+SIZ); above the limit you are overloaded.
    """

    def func(self):
        # The line goes after super(), so clothing's early return on an empty
        # inventory (clothing.py:664) still ends in "Carrying 0/20 ENC".
        # One read of each number; the band is the reader's rule over them.
        super().func()
        caller = self.caller
        carried = encumbrance.carried_enc(caller)
        limit = encumbrance.enc_limit(caller)
        line = f"Carrying {carried}/{limit} ENC"
        if encumbrance.band(carried, limit) != encumbrance.FREE:
            line += " (overloaded)"
        caller.msg(line)


class CmdGet(CmdContainerGet):
    """
    pick up something

    Usage:
      get <obj>
      get <obj> from <container>

    Picks up an object from your location or a container and puts it in
    your inventory.
    """

    # W2.2 Q3. On a ceiling refusal the hook says "You cannot carry any
    # more." and sets caller.ndb._enc_refused; the contrib then sends
    # CONTRIB_REFUSAL for the same refused move_to. While the flag is set,
    # that one line is dropped here -- every other line passes, and so does
    # the same line after any other refusal. The flag is cleared before and
    # after the contrib's func: ndb is never saved, and a flag that a `give`
    # set on this character earlier must not silence this `get`.

    def func(self):
        caller = self.caller
        caller.ndb._enc_refused = False
        try:
            super().func()
        finally:
            caller.ndb._enc_refused = False

    def msg(self, text=None, to_obj=None, from_obj=None, session=None, **kwargs):
        if text == CONTRIB_REFUSAL and self.caller.ndb._enc_refused:
            return
        super().msg(text=text, to_obj=to_obj, from_obj=from_obj, session=session, **kwargs)
