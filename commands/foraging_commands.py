"""
commands/foraging_commands.py
=============================

Player commands for gathering resources from ResourceNode objects.

Some nodes need a tool: a node whose `required_tool` names a tag-key (a tree
naming "axe", say) can only be foraged by a character carrying a usable tool
with that tag in the `crafting_tool` category. The check runs before the node
gives anything up, so a refusal claims nothing and costs no cooldown. A forage
that succeeds wears the tool by FORAGE_TOOL_WEAR; a tool worn to 0 is broken,
not deleted, and counts as absent until it is repaired -- the same rule a
broken tool follows at the crafting bench.
"""

from evennia.prototypes.spawner import spawn
from evennia.utils import logger

# Assumes the game template's base command. Adjust if yours lives elsewhere.
from commands.command import Command

FORAGE_COOLDOWN = 60  # real seconds between forage attempts, per character

# Wear a successful forage puts on the node's required tool. Same value as
# MongooseCraftRecipe.tool_wear, deliberately not the same knob: felling and
# crafting are different actions and must stay separately calibratable.
FORAGE_TOOL_WEAR = 5

# The tag category a required tool must carry: the crafting contrib's
# CraftingRecipe.tool_tag_category, kept as a literal so a survival command
# does not import the crafting layer. A test pins the two together.
TOOL_TAG_CATEGORY = "crafting_tool"


def _usable_tool(caller, tool_tag):
    """
    The first tool `caller` carries that satisfies `tool_tag`, or None.

    Mirrors MongooseCraftRecipe._used_tool(): the tag must be in the
    crafting_tool category, and a broken tool counts as not present.
    is_broken is getattr-guarded because a tagged object need not be a
    DurableObject; a non-durable tool is never broken. Only what is carried
    counts -- a tool lying on the floor does not.
    """
    for obj in caller.contents:
        if obj.tags.has(tool_tag, category=TOOL_TAG_CATEGORY) and not getattr(
            obj, "is_broken", False
        ):
            return obj
    return None


class CmdForage(Command):
    """
    Gather food from a natural resource in your surroundings.

    Usage:
        forage [target]

    Searches your location for something forageable (a berry bush, say) and
    gathers a portion into your hands. Each node holds a limited amount that
    slowly replenishes, so a picked-over bush yields nothing until it recovers.

    Some things need a tool: you cannot fell a tree without an axe in your
    hands. Gathering with a tool wears it down, and a worn-out tool is broken
    until it is repaired.

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

        # 4. Tool check, BEFORE the node gives anything up: a refusal claims
        #    nothing, so there is nothing to refund and no cooldown to set.
        tool = None
        required = node.required_tool
        if required:
            tool = _usable_tool(caller, required)
            if tool is None:
                article = "an" if required[0].lower() in "aeiou" else "a"
                caller.msg(
                    f"You need {article} {required} to gather from the "
                    f"{node.get_display_name(caller)}."
                )
                return

        # 5. Claim a unit. Synchronous read-modify-write -> race-safe under
        #    Evennia's reactor; two simultaneous foragers are serialised.
        got = node.harvest(1)
        if got <= 0:
            caller.msg(f"The {node.get_display_name(caller)} has nothing left to pick right now.")
            return

        # 6. Produce the yield; refund the claimed unit if spawning fails.
        try:
            item = spawn(node.yield_prototype)[0]
        except Exception:
            node.available += got
            logger.log_trace()
            caller.msg("You reach out, but something goes wrong and you come away empty-handed.")
            return
        item.move_to(caller, quiet=True)

        # 7. Wear the tool -- only now, after the yield exists, so the refund
        #    path above never wears a tool for a forage that produced nothing.
        #    hasattr-guarded: only a DurableObject wears. A tool worn to 0 is
        #    NOT deleted (crafting's D.2 rule); it lingers broken, counts as
        #    absent next time, and can still be repaired.
        broke = False
        if tool is not None and hasattr(tool, "apply_wear"):
            broke = tool.apply_wear(FORAGE_TOOL_WEAR) <= 0

        # 8. Commit cooldown and announce — only on success.
        caller.cooldowns.add("forage", FORAGE_COOLDOWN)
        caller.msg(f"You forage {item.get_display_name(caller)} from the {node.get_display_name(caller)}.")
        caller.location.msg_contents(
            f"{caller.get_display_name()} forages from the {node.get_display_name()}.",
            exclude=caller,
        )
        if broke:
            caller.msg(f"Your {tool.get_display_name(caller)} breaks under the work.")


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
