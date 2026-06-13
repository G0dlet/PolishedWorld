"""
commands/foraging_commands.py
=============================

Player commands for gathering resources from ResourceNode objects.
"""

from evennia.prototypes.spawner import spawn
from evennia.utils import logger

# Assumes the game template's base command. Adjust if yours lives elsewhere.
from commands.command import Command

FORAGE_COOLDOWN = 60  # real seconds between forage attempts, per character


class CmdForage(Command):
    """
    Gather food from a natural resource in your surroundings.

    Usage:
        forage [target]

    Searches your location for something forageable (a berry bush, say) and
    gathers a portion into your hands. Each node holds a limited amount that
    slowly replenishes, so a picked-over bush yields nothing until it recovers.

    You can only forage once every minute or so.
    """

    key = "forage"
    aliases = ["gather", "pick"]
    locks = "cmd:all()"
    help_category = "Survival"

    def func(self):
        caller = self.caller

        # 1. Per-character real-time rate limit.
        if not caller.cooldowns.ready("forage"):
            left = caller.cooldowns.time_left("forage", use_int=True)
            caller.msg(f"You need to catch your breath. Wait {left}s before foraging again.")
            return

        # 2. Forageable nodes here (exclude water sources / unconfigured nodes).
        nodes = [
            o for o in caller.location.contents
            if o.is_typeclass("typeclasses.resources.ResourceNode", exact=False)
            and not o.is_water_source
            and o.yield_prototype
        ]
        if not nodes:
            caller.msg("There is nothing here to forage.")
            return

        # 3. Resolve which node.
        target = self.args.strip()
        if target:
            node = caller.search(target, candidates=nodes)
            if not node:
                return  # search() already messaged the caller
        elif len(nodes) == 1:
            node = nodes[0]
        else:
            names = ", ".join(n.get_display_name(caller) for n in nodes)
            caller.msg(f"Forage what? You could try: {names}.")
            return

        # 4. Claim a unit. Synchronous read-modify-write -> race-safe under
        #    Evennia's reactor; two simultaneous foragers are serialised.
        got = node.harvest(1)
        if got <= 0:
            caller.msg(f"The {node.get_display_name(caller)} has nothing left to pick right now.")
            return

        # 5. Produce the yield; refund the claimed unit if spawning fails.
        try:
            item = spawn(node.yield_prototype)[0]
        except Exception:
            node.available += got
            logger.log_trace()
            caller.msg("You reach out, but something goes wrong and you come away empty-handed.")
            return
        item.move_to(caller, quiet=True)

        # 6. Commit cooldown and announce — only on success.
        caller.cooldowns.add("forage", FORAGE_COOLDOWN)
        caller.msg(f"You forage {item.get_display_name(caller)} from the {node.get_display_name(caller)}.")
        caller.location.msg_contents(
            f"{caller.get_display_name()} forages from the {node.get_display_name()}.",
            exclude=caller,
        )


class CmdRefill(Command):
    """
    Refill a drink container from a nearby water source.

    Usage:
        refill <container>

    If you are at a spring, stream or other source of water, tops up a
    refillable container you are carrying (a waterskin, for instance) to full.
    """

    key = "refill"
    aliases = ["fill"]
    locks = "cmd:all()"
    help_category = "Survival"

    def func(self):
        caller = self.caller

        # 1. Need a water source present in the room.
        has_water = any(
            o.is_water_source
            for o in caller.location.contents
            if o.is_typeclass("typeclasses.resources.ResourceNode", exact=False)
        )
        if not has_water:
            caller.msg("There is no water source here to refill from.")
            return

        # 2. Which container? Must be named and carried.
        target = self.args.strip()
        if not target:
            caller.msg("Refill what?")
            return
        container = caller.search(target, candidates=caller.contents)
        if not container:
            return  # search() already messaged the caller

        # 3. Validate: a refillable Drink.
        if not container.is_typeclass("typeclasses.consumables.Drink", exact=False):
            caller.msg(f"You can't fill the {container.get_display_name(caller)} with water.")
            return
        if not container.refillable:
            caller.msg(f"The {container.get_display_name(caller)} can't be refilled.")
            return

        # 4. A spent container gives out when you dip it again. Checked BEFORE
        #    filling, so the player got the use out of its last fill. Capture
        #    the name first — we must not touch a deleted object afterwards.
        if container.is_worn_out():
            name = container.get_display_name(caller)
            caller.msg(f"You dip the {name} in, but the worn vessel splits apart, ruined beyond use.")
            caller.location.msg_contents(
                f"{caller.get_display_name()}'s {name} falls apart at the water's edge.",
                exclude=caller,
            )
            container.delete()
            return

        # 5. Refill. refill() returns False if already full; it also wears the
        #    container by one point if it tracks durability (opt-in).
        if not container.refill():
            caller.msg(f"The {container.get_display_name(caller)} is already full.")
            return

        caller.msg(f"You fill the {container.get_display_name(caller)} with cool, clear water.")
        caller.location.msg_contents(
            f"{caller.get_display_name()} refills the {container.get_display_name()} at the water's edge.",
            exclude=caller,
        )
