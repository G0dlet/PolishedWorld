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

from evennia.prototypes.spawner import spawn
from evennia.utils import logger

from commands.command import Command
from world.skillcheck import (
    opposed_check, skill_check, ATTACKER, DEFENDER, CRITICAL, FUMBLE,
)
from world.harvest_templates import get_template, get_part, compute_yield

HUNT_COOLDOWN = 30      # real seconds between hunt attempts, per character
HARVEST_COOLDOWN = 30   # real seconds between harvest attempts, per character
HARVEST_TOOL_BONUS = 10  # circumstance bonus when a knife is carried (no penalty if absent)


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
                # On-use skill improvement (Component B.3). A won hunt trains
                # "hunting". opposed_check returns stalemate unless a side
                # succeeds, so an ATTACKER win always carries a successful
                # attacker roll -> pass that side's own skill_check dict.
                imp = caller.attempt_skill_improvement("hunting", result["attacker"])
                # Caught. at_death() does its own kill messaging, spawns the
                # corpse (from H3.2), and deletes the creature.
                target.at_death(caller)
                # C.1 tick-feedback AFTER the kill line: "you catch it" -> "you
                # got better at hunting".
                text = caller._improvement_feedback(imp)
                if text:
                    caller.msg(text)
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


class CmdHarvest(Command):
    """
    Harvest usable parts from a creature corpse.

    Usage:
        harvest <part> from <corpse>
        harvest <corpse>

    The second form lists what a corpse still has to offer. Each part takes a
    skill check -- a clean success yields it, a botch ruins it, and a near miss
    lets you try again. Soft parts (meat, hide) spoil as the corpse decays, so
    don't dawdle. A knife in hand makes the work a little easier.

    You can harvest once every half-minute or so.
    """

    key = "harvest"
    aliases = ["skin", "butcher"]
    locks = "cmd:all()"
    help_category = "Survival"

    def func(self):
        caller = self.caller

        # 1. Per-character real-time rate limit.
        if not caller.cooldowns.ready("harvest"):
            left = caller.cooldowns.time_left("harvest", use_int=True)
            caller.msg(
                f"Your hands are still unsteady from the last effort. "
                f"Wait {left}s before harvesting again."
            )
            return

        # 2. Parse "<part> from <corpse>" vs a bare "<corpse>" (inspection).
        args = self.args.strip()
        if " from " in args:
            lhs, _, rhs = args.partition(" from ")
            part_name = lhs.strip().lower() or None
            corpse_name = rhs.strip()
        else:
            part_name = None
            corpse_name = args  # may be "" -> auto-pick a lone corpse

        # 3. Resolve the corpse (messages + returns None on miss/ambiguity).
        corpse = self._find_corpse(caller, corpse_name)
        if not corpse:
            return

        # 4. Lazy cleanup: a fully-spent corpse crumbles on interaction (the
        #    no-ticker equivalent of the design's decay cleanup).
        if corpse.is_expired:
            name = corpse.get_display_name(caller)
            caller.msg(f"{name} has rotted away to nothing.")
            caller.location.msg_contents(
                f"{name} crumbles away to nothing.", exclude=caller
            )
            corpse.delete()
            return

        # 5. No part named -> just show what's available and stop (free action).
        if not part_name:
            self._show_parts(caller, corpse)
            return

        # 6. Validate the part against this corpse's template. Typo/unknown part
        #    is a free bailout (no cooldown), like hunt's bad-name path.
        part = get_part(corpse.db.creature_type, part_name)
        if not part:
            valid = ", ".join(get_template(corpse.db.creature_type) or [])
            corpse_label = corpse.get_display_name(caller)
            if valid:
                caller.msg(
                    f"You can't harvest '{part_name}' from {corpse_label}. "
                    f"You could take: {valid}."
                )
            else:
                caller.msg(f"There is nothing worth harvesting on {corpse_label}.")
            return

        corpse_label = corpse.get_display_name(caller)

        # 7. Already taken (or ruined) -> nothing to attempt, free bailout.
        if part_name in corpse.db.harvested:
            caller.msg(f"The {part_name} has already been taken from {corpse_label}.")
            return

        # 8. Decay gate: soft parts pass only while the corpse is fresh enough.
        #    Blocked by world-state, not by the player's effort -> free bailout.
        if corpse.decay_stage > part["max_stage"]:
            caller.msg(
                f"The {part_name} of {corpse_label} is too far gone to be worth taking."
            )
            return

        # 9. Resolve the Mongoose Legend skill check for this part.
        trait = caller.skills.get(part["skill"])
        skill_value = trait.value if trait else 0   # counter .value = current + mod
        modifier = part["difficulty"] + self._tool_modifier(caller)
        outcome = skill_check(skill_value, modifier)
        result = outcome["result"]

        # On-use skill improvement (Component B.3). Trains the part's own skill
        # (usually "hunting"); the per-skill improve cooldown means a harvest
        # moments after the hunt is naturally throttled -- no double-dip.
        imp = caller.attempt_skill_improvement(part["skill"], outcome)

        # 10. Apply the outcome.
        if outcome["success"]:
            is_crit = result == CRITICAL
            qty = compute_yield(part, corpse.db.creature_siz, critical=is_crit)

            # Claim the slot BEFORE spawning so a spawn failure can be refunded
            # cleanly and a retry can't double-dip. Single-threaded reactor makes
            # this atomic against any concurrent harvest.
            corpse.db.harvested[part_name] = True
            spawned = []
            try:
                for _ in range(qty):
                    spawned.append(spawn(part["prototype"])[0])
            except Exception:
                # Refund the claim and bin any partial spawns. Technical failure
                # -> no cooldown penalty (mirrors CmdForage's spawn-fail path).
                del corpse.db.harvested[part_name]
                for obj in spawned:
                    obj.delete()
                logger.log_trace()
                caller.msg("Something goes wrong and you come away empty-handed.")
                return

            for obj in spawned:
                obj.move_to(caller, quiet=True)

            if is_crit:
                caller.msg(
                    f"|gWith rare skill|n you take {qty} {part_name} from {corpse_label}."
                )
            else:
                caller.msg(f"You harvest {qty} {part_name} from {corpse_label}.")
            caller.location.msg_contents(
                f"{caller.get_display_name()} harvests {part_name} from {corpse_label}.",
                exclude=caller,
            )

        elif result == FUMBLE:
            # Botched: the part is ruined, the slot spent.
            corpse.db.harvested[part_name] = True
            caller.msg(f"|rYou botch the work|n and ruin the {part_name} on {corpse_label}.")
            caller.location.msg_contents(
                f"{caller.get_display_name()} botches the harvest, "
                f"ruining part of {corpse_label}.",
                exclude=caller,
            )

        else:
            # Plain failure: no yield, part untouched -> retryable.
            caller.msg(
                f"You can't cleanly take the {part_name} from {corpse_label}. "
                f"You can try again."
            )
        
        # C.1 tick-feedback after the harvest outcome line.
        text = caller._improvement_feedback(imp)
        if text:
            caller.msg(text)

        # 11. An attempt resolved (success/fumble/failure) -> commit the cooldown.
        #     Every earlier `return` is a free bailout that never reaches here.
        caller.cooldowns.add("harvest", HARVEST_COOLDOWN)

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _find_corpse(caller, name):
        """Resolve a Corpse in the room: named search, lone auto-pick, or prompt."""
        corpses = [
            o for o in caller.location.contents
            if o.is_typeclass("typeclasses.corpse.Corpse", exact=False)
        ]
        if not corpses:
            caller.msg("There is no corpse here to harvest.")
            return None
        if name:
            return caller.search(name, candidates=corpses)  # messages on miss
        if len(corpses) == 1:
            return corpses[0]
        names = ", ".join(c.get_display_name(caller) for c in corpses)
        caller.msg(f"Harvest from which corpse? You see: {names}.")
        return None

    @staticmethod
    def _show_parts(caller, corpse):
        """List the corpse's parts with per-part status (available/taken/decayed)."""
        template = get_template(corpse.db.creature_type)
        label = corpse.get_display_name(caller)
        if not template:
            caller.msg(f"There is nothing worth harvesting on {label}.")
            return
        stage = corpse.decay_stage
        lines = []
        for part_name, part in template.items():
            if part_name in corpse.db.harvested:
                status = "already taken"
            elif stage > part["max_stage"]:
                status = "too decayed"
            else:
                status = "available"
            lines.append(f"  {part_name} ({status})")
        caller.msg(
            f"{label} looks {corpse.decay_stage_name}. You could harvest:\n"
            + "\n".join(lines)
        )

    @staticmethod
    def _tool_modifier(caller):
        """+bonus if a knife is carried; no penalty when absent.

        Unlike crafting (which penalises improvised tools), bare-handed
        field-dressing is normal here -- a knife only helps. This keeps a
        knifeless new player from being locked out of the survival payoff.
        """
        for obj in caller.contents:
            if obj.tags.has("knife", category="crafting_tool"):
                return HARVEST_TOOL_BONUS
        return 0
