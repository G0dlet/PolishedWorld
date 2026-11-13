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
from world import activity_log
from world import client_state
from world import water
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

        # Survival Loop S1.2b (OQ-S6, lock G1): food is not eaten into a full
        # gauge -- it would be deleted for nothing.
        hunger = caller.traits.hunger
        if hunger.current >= hunger.max:
            caller.msg("You aren't hungry.")
            return

        item_key = obj.key  # read before delete(), for the event line
        hunger_before = caller.traits.hunger.current
        caller.traits.hunger.current += obj.restore_amount  # auto-clamps to max
        caller.msg(obj.consume_message.format(key=obj.get_display_name(caller)))
        caller.location.msg_contents(
            f"{caller.key} eats {obj.key}.", exclude=caller
        )
        obj.delete()
        # Launch Minimum L2.2: after the last write (the food deleted). The
        # field is `verb`, not `kind`: `kind` is reserved by record(). `delta`
        # is what the gauge actually gained, after the trait's own clamp.
        activity_log.record(
            "consume",
            caller,
            verb="eat",
            item=item_key,
            gauge="hunger",
            delta=caller.traits.hunger.current - hunger_before,
        )
        # W4.2: hunger moved, and the food left `carried`.
        client_state.push(caller, "survival", "char")


class CmdDrink(Command):
    """
    Drink to restore thirst.

    Usage:
      drink
      drink <source>
      drink <container>

    With no argument you drink at a spring or other water source here,
    from cupped hands. Name a container you carry, a waterskin for
    instance, to drink from it instead; a container is never chosen
    for you.
    """

    key = "drink"
    help_category = "survival"

    def func(self):
        caller = self.caller
        query = self.args.strip()
        if not query:
            # Survival Loop SL2: bare `drink` means the source, never a
            # carried vessel -- its charges are the player's to spend.
            source = water.source_in(caller.location)
            if source is None:
                caller.msg("Drink from what?")
                return
            self._drink_from_source(source)
            return

        obj = caller.search(query)
        if not obj:
            return

        if water.is_source(obj):
            self._drink_from_source(obj)
            return

        if not inherits_from(obj, Drink):
            caller.msg(f"You can't drink from {obj.get_display_name(caller)}.")
            return

        if not obj.pk:
            return

        if obj.is_empty():
            caller.msg(f"{obj.get_display_name(caller)} is empty.")
            return

        # Survival Loop S1.2b (OQ-S6, lock F1): as at the source, a draught is
        # not spent into a full gauge.
        thirst = caller.traits.thirst
        if thirst.current >= thirst.max:
            caller.msg("You aren't thirsty.")
            return

        thirst_before = caller.traits.thirst.current
        caller.traits.thirst.current += obj.restore_amount  # auto-clamps to max
        obj.charges -= 1
        if obj.is_empty():
            obj.pour_out()  # SL3: the kind goes with the last draught
        # Launch Minimum L2.2: after the last write, before the first message.
        activity_log.record(
            "consume",
            caller,
            verb="drink",
            item=obj.key,
            gauge="thirst",
            delta=caller.traits.thirst.current - thirst_before,
            charges_left=obj.charges,
        )
        caller.msg(obj.consume_message.format(key=obj.get_display_name(caller)))
        if obj.is_empty():
            caller.msg(f"{obj.get_display_name(caller)} runs dry.")
        client_state.push(caller, "survival")   # W4.2

    def _drink_from_source(self, source):
        """
        Drink at a water source: three draughts at once, free (SL2).

        A character already at full thirst is told so and nothing is written:
        the source costs nothing, so a line with no gain would only be noise
        in the activity log (S1.1 lock C1). The line has no `charges_left`,
        because a source has none.

        Args:
            source (ResourceNode): A water source in the caller's room.
        """
        caller = self.caller
        thirst = caller.traits.thirst
        if thirst.current >= thirst.max:
            caller.msg("You aren't thirsty.")
            return

        thirst_before = thirst.current
        caller.traits.thirst.current += water.SOURCE_RESTORE  # auto-clamps to max
        # Launch Minimum L2.2: after the last write, before the first message.
        activity_log.record(
            "consume",
            caller,
            verb="drink",
            item=source.key,
            gauge="thirst",
            delta=caller.traits.thirst.current - thirst_before,
        )
        caller.msg(
            f"You kneel at the {source.get_display_name(caller)} and drink from "
            "cupped hands. The water is cold enough to ache."
        )
        caller.location.msg_contents(
            f"{caller.get_display_name()} kneels at the "
            f"{source.get_display_name()} and drinks.",
            exclude=caller,
        )
        client_state.push(caller, "survival")


class CmdEmpty(Command):
    """
    Empty a container.

    Usage:
      empty <container>

    Pour out what a container you carry holds, so it can be filled
    with something else. Emptying does not wear it.
    """

    key = "empty"
    help_category = "survival"

    def func(self):
        caller = self.caller
        query = self.args.strip()
        if not query:
            caller.msg("Empty what?")
            return

        obj = caller.search(query, candidates=caller.contents)
        if not obj:
            return

        name = obj.get_display_name(caller)
        if not inherits_from(obj, Drink) or not obj.refillable:
            caller.msg(f"You can't empty the {name}.")
            return
        if obj.is_empty():
            caller.msg(f"The {name} is already empty.")
            return

        # Survival Loop SL3 / S1.2 lock D: no wear, no log line (water from
        # a source is free), no push (no panel shows what a vessel holds).
        obj.pour_out()
        caller.msg(f"You upend the {name} and let it run out.")
        caller.location.msg_contents(
            f"{caller.get_display_name()} upends the {obj.get_display_name()} "
            "and lets it run out.",
            exclude=caller,
        )


class CmdRest(Command):
    """
    Rest to recover fatigue over time.

    Usage:
      rest

    Begin resting. Use 'rest' again, or move, to stop.

    Crafting, working and resting each take time, and you can only be
    doing one of them at once.
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
