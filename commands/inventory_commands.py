"""
Inventory commands (Weight and Encumbrance, Tasks W2.2 and W4.2).

Three contrib commands, each extended by one thing and otherwise unchanged.
CmdInventory and CmdGet replace their contrib command in
commands/default_cmdsets.py; CmdPut adds one the cmdset did not have.

    CmdInventory  clothing's worn/carried split (clothing.py:642), plus one
                  line: "Carrying 7/20 ENC", with " (overloaded)" outside
                  FREE. The number is the in-game receipt every weight
                  protocol reads.
    CmdGet        the containers contrib's `get` and `get ... from`
                  (containers.py:152), minus the contrib's own refusal line
                  when the ceiling hook (Character.at_pre_object_receive,
                  W2.1) has already said why.
    CmdPut        the containers contrib's `put <obj> in <container>`
                  (containers.py:227), minus the contrib's own refusal line
                  when the container's `at_pre_put_in` (Container, or
                  ObjectParent for anything else) has already said why
                  (W4.2 Q2).

None copies the contrib's `func`: each calls `super().func()`, so a fix
upstream reaches them (W2.2 Q3, W4.2 Q1).
"""

from evennia.contrib.game_systems.clothing.clothing import (
    CmdInventory as ClothingCmdInventory,
)
from evennia.contrib.game_systems.containers.containers import CmdContainerGet
from evennia.contrib.game_systems.containers.containers import CmdPut as ContribCmdPut

from world import encumbrance

# containers.py:211 -- what CmdContainerGet says for any refused move_to.
CONTRIB_REFUSAL = "This can't be picked up."

# containers.py:280 -- what the contrib's CmdPut says when the container's
# at_pre_put_in refuses.
PUT_REFUSAL = "You can't put that there."


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
    your inventory. What you pick up counts toward the ENC you carry, shown
    by 'inventory': above your limit you are overloaded, and you cannot take
    anything that would put you above twice your limit.
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


class CmdPut(ContribCmdPut):
    """
    put something in a container

    Usage:
      put <obj> in <container>

    Puts something you carry into a container you carry or one nearby. A
    container holds ENC, not a number of things: a sack holds 10, a
    saddlebag 15 and a backpack 20. What is inside still counts toward the
    ENC you carry. A container never goes inside another container.
    """

    # W4.2 Q2. A project at_pre_put_in that refuses says why and sets
    # caller.ndb._put_refused; the contrib then sends PUT_REFUSAL for the same
    # refusal. While the flag is set, that one line is dropped here -- every
    # other line passes, and so does the same line after a refusal that did
    # not set the flag (the contrib's own ContribContainer). The flag is
    # cleared before and after the contrib's func, as in CmdGet, so a flag
    # left over from anything earlier never silences this `put`.

    def func(self):
        caller = self.caller
        caller.ndb._put_refused = False
        try:
            super().func()
        finally:
            caller.ndb._put_refused = False

    def msg(self, text=None, to_obj=None, from_obj=None, session=None, **kwargs):
        if text == PUT_REFUSAL and self.caller.ndb._put_refused:
            return
        super().msg(text=text, to_obj=to_obj, from_obj=from_obj, session=session, **kwargs)
