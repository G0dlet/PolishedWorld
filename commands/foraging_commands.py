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
