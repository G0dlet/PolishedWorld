"""
Inventory commands (Weight and Encumbrance, Tasks W2.2 and W4.2).

Three contrib commands, each extended by one thing and otherwise unchanged.
CmdInventory and CmdGet replace their contrib command in
commands/default_cmdsets.py; CmdPut adds one the cmdset did not have.

    CmdInventory  clothing's worn/carried split (clothing.py:642), with what
                  is held between them (Gear GR-T9, GR5), plus one line:
                  "Carrying 7/20 ENC", with " (overloaded)" outside FREE.
                  The number is the in-game receipt every weight protocol
                  reads.
    CmdGet        the containers contrib's `get` and `get ... from`
                  (containers.py:152), minus the contrib's own refusal line
                  when the ceiling hook (Character.at_pre_object_receive,
                  W2.1) has already said why.
    CmdPut        the containers contrib's `put <obj> in <container>`
                  (containers.py:227), minus the contrib's own refusal line
                  when the container's `at_pre_put_in` (Container, or
                  ObjectParent for anything else) has already said why
                  (W4.2 Q2).

CmdGet and CmdPut call `super().func()`, so a fix upstream reaches them
(W2.2 Q3, W4.2 Q1). CmdInventory builds its own tables since GR-T9: the
contrib's filter is inside its `func` (clothing.py:673), and a held item
must not stand under *carrying* (GR5; GR-T9's STOPP 0, val 1). It builds
them with the contrib's own tools, and a change to the contrib's tables
does not reach it.
"""

from evennia.contrib.game_systems.clothing.clothing import (
    CmdInventory as ClothingCmdInventory,
)
from evennia.contrib.game_systems.containers.containers import CmdContainerGet
from evennia.contrib.game_systems.containers.containers import CmdPut as ContribCmdPut
from evennia.utils import crop, group_objects_by_key_and_desc
from evennia.utils.ansi import raw as raw_ansi

from world import encumbrance, gear

# clothing.py:664 -- the contrib's line for an empty inventory, kept word for word.
EMPTY = "You are not carrying or wearing anything."

# The headers, the contrib's two (clothing.py:682, :695) and GR5's between.
CARRYING = "|wYou are carrying:|n"
HOLDING = "|wYou are holding:|n"
WEARING = "You are wearing:|n"
NOTHING = " Nothing."
BOTH_HANDS = "both hands"

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

    Shows what you carry, what you hold and in which hand, and what you
    wear. The last line is the ENC you carry against your limit (STR+SIZ);
    above the limit you are overloaded. What you hold is carried too.
    """

    def _table(self, objs):
        """The contrib's table for a list of items (clothing.py:674-683)."""
        table = self.styled_table(border="header")
        for key, desc, _ in group_objects_by_key_and_desc(objs, caller=self.caller):
            table.add_row(f"{key}|n", "{}|n".format(crop(raw_ansi(desc or ""), width=50) or ""))
        return str(table) if table.nrows > 0 else NOTHING

    def _holding(self, hands):
        """GR5: each held item once, with its hand; a staff is in both."""
        table = self.styled_table(border="header")
        seen = []
        for hand in gear.HANDS:
            obj = hands[hand]
            if obj is None or obj in seen:
                continue
            seen.append(obj)
            both = hands[gear.RIGHT] == hands[gear.LEFT]
            # Named as the contrib's tables name an item (utils.py:1844).
            table.add_row(
                f"{obj.get_numbered_name(1, self.caller, return_string=True)}|n",
                BOTH_HANDS if both else f"{hand} hand",
            )
        return str(table) if table.nrows > 0 else NOTHING

    def _useless(self):
        """GR22: one line per useless arm, the words `wield` refuses with."""
        return [
            " " + gear.ARM_USELESS.format(hand=hand)
            for hand in gear.HANDS
            if gear.hand_state(self.caller, hand) == gear.USELESS
        ]

    def func(self):
        caller = self.caller
        items = caller.contents
        if not items:
            caller.msg("\n".join([EMPTY, *self._useless()]))
        else:
            hands = gear.held(caller)
            in_hand = [obj for obj in hands.values() if obj is not None]
            loose = [obj for obj in items if not obj.db.worn and obj not in in_hand]
            worn = [obj for obj in items if obj.db.worn]
            lines = [
                CARRYING, self._table(loose),
                HOLDING, self._holding(hands), *self._useless(),
                WEARING, self._table(worn),
            ]
            caller.msg(text=("\n".join(lines), {"type": "inventory"}))
        # The ENC line comes last, on an empty inventory too.
        # One read of each number; the band is the reader's rule over them.
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
