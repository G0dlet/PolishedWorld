"""
commands/hunting_commands.py
============================

Player command for hunting passive creatures.

Hunting is resolved as a single Mongoose Legend OPPOSED skill test -- the
hunter's Hunting skill against the creature's flee_skill -- not as combat rounds.
Creatures do not fight back (see typeclasses/creatures.py), which keeps the
hunt -> corpse -> harvest loop decoupled from a combat system that does not exist
yet. A win routes through Creature.at_death() (Corpse spawn lands in Task H3.2).
"""

from random import choice

from commands.command import Command
from world.skillcheck import opposed_check, ATTACKER, DEFENDER, FUMBLE

HUNT_COOLDOWN = 30  # real seconds between hunt attempts, per character


class CmdHunt(Command):
    """
    Hunt a wild creature for meat and materials.

    Usage:
        hunt <creature>

    Pits your Hunting skill against the creature's instinct to flee. Success
    brings the animal down; a clean escape sends it bolting from the area;
    sometimes neither of you gains the upper hand and you can try again.

    Hunting is tiring -- you can only attempt it every half-minute or so.
    """

    key = "hunt"
    aliases = ["stalk"]
    locks = "cmd:all()"
    help_category = "Survival"

    def func(self):
        caller = self.caller

        # 1. Per-character real-time rate limit.
        if not caller.cooldowns.ready("hunt"):
            left = caller.cooldowns.time_left("hunt", use_int=True)
            caller.msg(
                f"You are still recovering from the chase. "
                f"Wait {left}s before hunting again."
            )
            return

        # 2. Need a target name.
        target_name = self.args.strip()
        if not target_name:
            caller.msg("Hunt what?")
            return

        # 3. Resolve the target among huntable creatures in the room.
        creatures = [
            o for o in caller.location.contents
            if o.is_typeclass("typeclasses.creatures.Creature", exact=False)
        ]
        if not creatures:
            caller.msg("There is nothing here to hunt.")
            return
        target = caller.search(target_name, candidates=creatures)
        if not target:
            return  # search() already messaged the caller (no-match / multimatch)

        # 4. Race guard: claim the creature for this hunt. ndb is per-process and
        #    set+checked synchronously within this single reactor tick, so two
        #    hunters cannot both pass this gate for the same creature. The
        #    Creature.at_death() pk-check is a second line of defence.
        if target.ndb.hunted_by is not None and target.ndb.hunted_by is not caller:
            caller.msg(
                f"Someone else is already hunting {target.get_display_name(caller)}."
            )
            return
        target.ndb.hunted_by = caller

        try:
            # 5. Resolve the opposed Legend skill test.
            hunting = caller.skills.get("hunting")
            hunting_value = hunting.value if hunting else 0  # counter .value = current + mod
            flee = target.db.flee_skill or 0

            result = opposed_check(hunting_value, flee)
            winner = result["winner"]

            # 6. The attempt happened -> commit the cooldown for every resolved
            #    outcome (win / flee / stalemate). Bailouts above (no target,
            #    bad name, on cooldown) never reach here, so they are free.
            caller.cooldowns.add("hunt", HUNT_COOLDOWN)

            if winner == ATTACKER:
                # Caught. at_death() does its own kill messaging, spawns the
                # corpse (from H3.2), and deletes the creature.
                target.at_death(caller)
                return

            if winner == DEFENDER:
                # Clean escape -> the animal flees the area.
                self._flee(caller, target)
                return

            # STALEMATE: inconclusive. A hunter fumble gets a mishap flavour but
            # is still no-kill/no-flee, matching the rulebook's "re-roll later".
            if result["attacker"]["result"] == FUMBLE:
                caller.msg(
                    "You stumble at the worst moment and lose your line on it. "
                    "You can try again."
                )
            else:
                caller.msg(
                    "You can't get a clean shot; the quarry keeps its distance. "
                    "You can try again."
                )
        finally:
            # Release the claim if the creature still exists. A kill deletes it
            # (pk becomes None), taking its ndb with it, so only clear when live.
            if target.pk:
                target.ndb.hunted_by = None

    @staticmethod
    def _flee(caller, creature):
        """
        Send a creature bolting out of the room on a clean escape.

        Prefers moving it through a random traversable exit so it stays in the
        world (the spawn cap then self-heals naturally via CreatureSpawnScript).
        Despawns it only when the room has no exit to flee through.
        """
        name = creature.get_display_name(caller)
        caller.msg(f"{name} breaks away and bolts before you can close in.")
        caller.location.msg_contents(
            f"{name} bolts away, startled.", exclude=caller
        )

        exits = [ex for ex in creature.location.exits if ex.access(creature, "traverse")]
        if exits:
            # move_hooks=False: a passive animal has no traversal hooks worth
            # firing, and we don't want enter/leave spam in the destination room.
            creature.move_to(choice(exits).destination, quiet=True, move_hooks=False)
        else:
            creature.delete()
