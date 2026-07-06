"""
commands/repair_commands.py

CmdRepair: restore a garment's condition via a Craft (tailoring) skill check.

Repair mutates an existing garment in place rather than spawning a new item, so
it is a dedicated command, not a MongooseCraftRecipe (recipes are input -> new
output). Resolving one carried/worn garment by name also sidesteps the crafting
multimatch issue, since we target a single object, not a bag of ingredient tokens.

Model: roll the crafter's Craft skill (world/skillcheck.py), modified by whether
a needle is carried (+20) or improvised (-20), mirroring the tailoring recipes'
optional-tool handling. The result tier decides the condition change; a fumble
damages the garment further. Cloth and twine are consumed on *any* resolved
attempt -- including a plain failure -- so low-skill spam carries a real cost.
"""

from evennia.utils import logger

from commands.command import Command
from world.skillcheck import skill_check, CRITICAL, FUMBLE
from world.thermal import apply_thermal_stress
from typeclasses.clothing import ClothingWithBuffs

# Realtime seconds before repair can be re-run (in line with tailoring recipes'
# craft_cooldown ~40).
REPAIR_COOLDOWN = 40

# Consumed per resolved attempt: a cloth patch stitched with twine. Tag-keys in
# the crafting_material category, verified against world/recipes.py.
REPAIR_MATERIALS = ("cloth", "twine")

# Craft-tool modifier, mirroring MongooseCraftRecipe (tool_bonus /
# improvised_penalty). A needle helps; bare-handed stitching is penalised, not
# blocked, so a new player is never locked out.
NEEDLE_BONUS = 20
IMPROVISED_PENALTY = -20

# Condition change by result tier (locked this session). Critical fully renews;
# success is a solid patch; failure wastes materials for no gain; a fumble
# leaves the garment worse than before.
CRIT_RESTORE_TO = 100      # absolute target on a critical
SUCCESS_RESTORE = 30       # added, capped at 100
FUMBLE_DAMAGE = 10         # subtracted, floored at 0


class CmdRepair(Command):
    """
    Repair a worn or carried garment, restoring its condition.

    Usage:
      repair <garment>

    Stitches a cloth patch onto the garment with twine, testing your Craft
    skill. A carried needle makes the work easier. Success restores condition;
    a critical repair makes it as good as new; a botch damages it further.
    Cloth and twine are used up whether or not the repair goes well.
    """

    key = "repair"
    aliases = ["mend"]
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller

        # Cooldown gate -> free bailout, nothing consumed.
        if not caller.cooldowns.ready("repair"):
            left = caller.cooldowns.time_left("repair", use_int=True)
            caller.msg(f"Your hands need a moment. Try repairing again in {left}s.")
            return

        target_name = self.args.strip()
        if not target_name:
            caller.msg("Repair what? (usage: |wrepair <garment>|n)")
            return

        # Resolve the garment among what the caller holds or wears (worn items
        # stay in contents with db.worn set). search() messages on miss/multimatch.
        garment = caller.search(target_name, candidates=caller.contents)
        if not garment:
            return

        # Only our clothing carries a condition to repair.
        if not isinstance(garment, ClothingWithBuffs):
            caller.msg(f"You can't mend {garment.get_display_name(caller)}.")
            return

        current = garment.db.condition
        if current is None:
            current = 100
        if current >= 100:
            caller.msg(f"Your {garment.get_display_name(caller)} is already in good repair.")
            return

        # Gather one of each required material -> free bailout if short.
        materials = self._collect_materials(caller)
        if materials is None:
            caller.msg(f"You need {' and '.join(REPAIR_MATERIALS)} to patch a garment.")
            return

        # From here the attempt is committed: materials are consumed and the
        # cooldown set on every outcome. The single-threaded reactor makes the
        # collect-roll-consume sequence atomic against any concurrent repair.
        trait = caller.skills.get("craft")
        skill_value = trait.value if trait else 0     # counter .value = current + mod
        outcome = skill_check(skill_value, self._tool_modifier(caller))
        result = outcome["result"]

        for obj in materials:
            obj.delete()
        caller.cooldowns.add("repair", REPAIR_COOLDOWN)

        new = self._resolved_condition(current, outcome)
        garment.db.condition = new
        name = garment.get_display_name(caller)

        if result == CRITICAL:
            caller.msg(f"|gWith rare skill|n you make your {name} as good as new.")
        elif outcome["success"]:
            caller.msg(f"You patch your {name}; it's in better shape now ({new}%).")
        elif result == FUMBLE:
            caller.msg(
                f"|rYou botch the stitching|n and leave your {name} worse than before ({new}%)."
            )
        else:  # plain failure
            caller.msg(
                f"You can't make the patch hold. Your {name} is no better, and the "
                f"cloth and twine are wasted."
            )

        # On-use skill improvement (Component B.3). Success-gated + cooldown
        # -limited inside attempt_skill_improvement; repair trains the same
        # "craft" skill as crafting. Placed after the outcome message so a later
        # "your Crafting improves" line (C.1) reads after the repair result.
        caller.attempt_skill_improvement("craft", outcome)

        # A worn garment's effective warmth is read live from condition, so        # refresh the wearer's thermal buffs to register the change at once --
        # mirroring the wear/remove hooks in typeclasses/clothing.py.
        if garment.db.worn:
            apply_thermal_stress(caller)

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _resolved_condition(current, outcome):
        """
        New condition from a skill_check outcome. Pure -> unit-testable without RNG.

        critical -> full renewal; success -> +restore (capped); fumble -> -damage
        (floored); plain failure -> unchanged (materials still wasted by caller).
        """
        result = outcome["result"]
        if result == CRITICAL:
            return CRIT_RESTORE_TO
        if outcome["success"]:
            return min(100, current + SUCCESS_RESTORE)
        if result == FUMBLE:
            return max(0, current - FUMBLE_DAMAGE)
        return current

    @staticmethod
    def _collect_materials(caller):
        """
        Find one distinct carried item per required material tag.

        Returns the objects to consume, or None if any material is missing (a
        None result consumes nothing). Claimed ids are tracked so two required
        tags never resolve to the same versatile item.
        """
        claimed, claimed_ids = [], set()
        for tag_key in REPAIR_MATERIALS:
            match = next(
                (o for o in caller.contents
                 if o.id not in claimed_ids
                 and o.tags.has(tag_key, category="crafting_material")),
                None,
            )
            if match is None:
                return None
            claimed.append(match)
            claimed_ids.add(match.id)
        return claimed

    @staticmethod
    def _tool_modifier(caller):
        """+NEEDLE_BONUS if a needle is carried, else the improvised penalty."""
        for obj in caller.contents:
            if obj.tags.has("needle", category="crafting_tool"):
                return NEEDLE_BONUS
        return IMPROVISED_PENALTY
