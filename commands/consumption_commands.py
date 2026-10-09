"""
Consumption commands: eat and drink.

These apply gauge restoration that items only describe (see
typeclasses/consumables.py): Food -> hunger, Drink -> thirst. Restoration
auto-clamps to the gauge max via the trait setter, so no manual upper bound
is needed. Condition buffs (starving/dehydrated) are cleared by the survival
ticker on its next pass once the gauge is back above zero.
"""

from evennia.utils.utils import inherits_from
from commands.command import Command
from world import timed_actions
from typeclasses.consumables import Food, Drink


class CmdEat(Command):
    """
    Eat something to restore hunger.

    Usage:
      eat <food>
    """

    key = "eat"
    help_category = "survival"

    def func(self):
        caller = self.caller
        if not self.args.strip():
            caller.msg("Eat what?")
            return

        obj = caller.search(self.args.strip())
        if not obj:
            return  # search() already messaged the caller

        if not inherits_from(obj, Food):
            caller.msg(f"You can't eat {obj.get_display_name(caller)}.")
            return

        if not obj.pk:
            return  # already consumed (defensive; see notes)

        caller.traits.hunger.current += obj.restore_amount  # auto-clamps to max
        caller.msg(obj.consume_message.format(key=obj.get_display_name(caller)))
        caller.location.msg_contents(
            f"{caller.key} eats {obj.key}.", exclude=caller
        )
        obj.delete()


class CmdDrink(Command):
    """
    Drink from a container to restore thirst.

    Usage:
      drink <container>
    """

    key = "drink"
    help_category = "survival"

    def func(self):
        caller = self.caller
        if not self.args.strip():
            caller.msg("Drink from what?")
            return

        obj = caller.search(self.args.strip())
        if not obj:
            return

        if not inherits_from(obj, Drink):
            caller.msg(f"You can't drink from {obj.get_display_name(caller)}.")
            return

        if not obj.pk:
            return

        if obj.is_empty():
            caller.msg(f"{obj.get_display_name(caller)} is empty.")
            return

        caller.traits.thirst.current += obj.restore_amount  # auto-clamps to max
        obj.charges -= 1
        caller.msg(obj.consume_message.format(key=obj.get_display_name(caller)))
        if obj.is_empty():
            caller.msg(f"{obj.get_display_name(caller)} runs dry.")


class CmdRest(Command):
    """
    Rest to recover fatigue over time.

    Usage:
      rest

    Begin resting. Use 'rest' again, or move, to stop.
    """

    key = "rest"
    help_category = "survival"

    def func(self):
        """
        Toggle resting.

        `rest` occupies the shared timed-action slot (Epic A), so this asks the
        slot what is going on and branches on WHICH action holds it:

        - a rest: toggle it off (`stop_resting`).
        - anything else: fall through to `start_resting()`, whose `start()`
          refuses with "You are already <label>." (D3, T2). The other action
          is NOT interrupted -- `rest` during a chore is answered, not used as
          a way to cancel the chore.
        - nothing: start resting.

        The branch reads the record's `key`, not its `label`: the label is
        player-facing wording and free to change; the key is the identity.
        """
        caller = self.caller
        record = timed_actions.is_busy(caller)
        if record is not None and record.key == "rest":
            caller.stop_resting()
            return
        caller.start_resting()
