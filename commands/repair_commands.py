"""
commands/repair_commands.py

CmdRepair: restore a garment's condition via a Craft (tailoring) skill check.

Repair mutates an existing garment in place rather than spawning a new item, so
it is a dedicated command, not a MongooseCraftRecipe (recipes are input -> new
output). Resolving one carried/worn garment by name also sidesteps the crafting
multimatch issue, since we target a single object, not a bag of ingredient tokens.

Model: roll the crafter's Craft skill (world/skillcheck.py), modified by whether
a needle is carried (baseline 0) or improvised (-20), mirroring the tailoring recipes'
optional-tool handling. The result tier decides the condition change; a fumble
damages the garment further. Cloth and twine are consumed on *any* resolved
attempt -- including a plain failure -- so low-skill spam carries a real cost.
"""

from evennia.utils import logger

from commands.command import Command
from world.skillcheck import skill_check, CRITICAL, FUMBLE
from world.crafting_quality import quality_band, SUPERIOR
from world.thermal import apply_thermal_stress
from typeclasses.durable import DurableObject

# Realtime seconds before repair can be re-run (in line with tailoring recipes'
# craft_cooldown ~40).
REPAIR_COOLDOWN = 40

# Default repair materials (a cloth patch stitched with twine), used as the
# fallback when a target sets no db.repair_materials of its own -- garments carry
# no override, so they land here (Task D.4). Tag-keys in the crafting_material
# category, verified against world/recipes.py.
REPAIR_MATERIALS = ("cloth", "twine")

# Craft-tool modifier, mirroring MongooseCraftRecipe. The expected repair tool
# (a needle, for garments) is the baseline (0), not a bonus; working without it
# is penalised (not blocked, so a new player is never locked out). A *superior*
# tool grants a positive modifier (Component G), matching the craft side.
#
# Which tool a target expects is data-driven (Task G.2), parallel to
# db.repair_materials: target.db.repair_tool_tag names the crafting_tool tag-key
# whose presence eases the repair. UNSET (None) -> the garment default below (a
# needle), so existing garments need no prototype change. An item that needs NO
# tool sets it to "" explicitly (e.g. a stone knife: re-hafting is bare-handed),
# which the spawner stores faithfully and _tool_modifier reads as "no tool -> 0".
DEFAULT_REPAIR_TOOL = "needle"   # tag-key used when a target sets no repair_tool_tag
SUPERIOR_TOOL_BONUS = 10         # positive modifier a SUPERIOR repair tool grants,
                                 # matching MongooseCraftRecipe.tool_bonus (+10).
IMPROVISED_PENALTY = -20         # penalty when the expected tool is absent/broken.

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
            caller.msg("Repair what? (usage: |wrepair <item>|n)")
            return

        # Resolve the item among what the caller holds or wears (worn garments
        # stay in contents with db.worn set). search() messages on miss/multimatch.
        target = caller.search(target_name, candidates=caller.contents)
        if not target:
            return

        # Only objects on the shared durability axis carry a condition to repair.
        # Garments (ClothingWithBuffs) and tools (Tool) both inherit DurableObject,
        # so this one check covers both -- broadened from the garment-only gate in
        # Task D.4.
        if not isinstance(target, DurableObject):
            caller.msg(f"You can't mend {target.get_display_name(caller)}.")
            return

        current = target.db.condition
        if current is None:
            current = 100
        if current >= 100:
            caller.msg(
                f"Your {target.get_display_name(caller)} is already in good repair."
            )
            return

        # Repair materials are data-driven (Task D.4): a garment is patched with
        # cloth+twine, but a stone knife is re-hafted with stick+fibre. Each item
        # names what mends it via db.repair_materials; unset -> the garment default.
        # func owns the single read so the "you need ..." message and the collect
        # step share one resolved list.
        required = target.db.repair_materials or REPAIR_MATERIALS

        # Gather one of each required material -> free bailout if short.
        materials = self._collect_materials(caller, required)
        if materials is None:
            caller.msg(
                f"You need {' and '.join(required)} to mend your "
                f"{target.get_display_name(caller)}."
            )
            return

        # From here the attempt is committed: materials are consumed and the
        # cooldown set on every outcome. The single-threaded reactor makes the
        # collect-roll-consume sequence atomic against any concurrent repair.
        trait = caller.skills.get("craft")
        skill_value = trait.value if trait else 0     # counter .value = current + mod
        outcome = skill_check(skill_value, self._tool_modifier(caller, target))
        result = outcome["result"]

        for obj in materials:
            obj.delete()
        caller.cooldowns.add("repair", REPAIR_COOLDOWN)

        new = self._resolved_condition(current, outcome)
        target.db.condition = new
        name = target.get_display_name(caller)

        if result == CRITICAL:
            caller.msg(f"|gWith rare skill|n you mend your {name} as good as new.")
        elif outcome["success"]:
            caller.msg(f"You mend your {name}; it's in better shape now ({new}%).")
        elif result == FUMBLE:
            caller.msg(
                f"|rYou botch the work|n and leave your {name} worse than before ({new}%)."
            )
        else:  # plain failure
            caller.msg(
                f"You can't make the repair hold. Your {name} is no better, and "
                f"the materials are wasted."
            )

        # On-use skill improvement (Component B.3). Success-gated + cooldown
        # -limited inside attempt_skill_improvement; repair trains the same
        # "craft" skill as crafting. Placed after the outcome message so a later
        # "your Crafting improves" line (C.1) reads after the repair result.
        imp = caller.attempt_skill_improvement("craft", outcome)
        text = caller._improvement_feedback(imp)
        if text:
            caller.msg(text)

        # A worn garment's effective warmth is read live from condition, so
        # refresh the wearer's thermal buffs to register the change at once.
        # Tools carry no db.worn, so this naturally skips them.
        if target.db.worn:
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
    def _collect_materials(caller, required):
        """
        Find one distinct carried item per required material tag.

        Args:
            required (sequence): crafting_material tag-keys to gather, resolved by
                the caller from the target's db.repair_materials (data-driven per
                item, Task D.4) or the module default.

        Returns the objects to consume, or None if any material is missing (a None
        result consumes nothing). Claimed ids are tracked so two required tags
        never resolve to the same versatile item.
        """
        claimed, claimed_ids = [], set()
        for tag_key in required:
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
    def _tool_modifier(caller, target):
        """Repair-tool modifier for the Craft check, mirroring the craft side.

        Which tool eases a repair is data-driven per target (Task G.2), parallel
        to db.repair_materials:

            target.db.repair_tool_tag UNSET (None) -> DEFAULT_REPAIR_TOOL (needle)
                -- garments need no prototype change and keep the old behaviour.
            target.db.repair_tool_tag == ""        -> no tool: modifier always 0
                -- e.g. a stone knife (re-hafting is bare-handed); this is what
                fixes the old garment-centric bug, where carrying a needle wrongly
                shifted a *stone knife* repair.
            target.db.repair_tool_tag == "<tag>"   -> that crafting_tool tag-key.

        Then, mirroring MongooseCraftRecipe._tool_modifier:

            superior tool carried  -> +SUPERIOR_TOOL_BONUS  (quality > 100)
            plain tool carried     -> 0  (baseline; the expected tool)
            tool absent/broken     -> IMPROVISED_PENALTY

        The target is excluded from the tool search (obj is not target), so an
        item never counts as its own repair tool. A broken tool is skipped
        (is_broken guard) -- broken counts as absent, consistent with the craft
        side's _used_tool(). db.quality is guarded for None (an uncrafted/admin
        tool is a plain baseline tool).
        """
        tag = target.db.repair_tool_tag
        if tag is None:
            tag = DEFAULT_REPAIR_TOOL       # unset -> garment default (a needle)
        if not tag:
            return 0                         # explicit "" -> this item needs no tool

        for obj in caller.contents:
            if (
                obj is not target
                and obj.tags.has(tag, category="crafting_tool")
                and not getattr(obj, "is_broken", False)
            ):
                quality = obj.db.quality
                if quality is not None and quality_band(quality) == SUPERIOR:
                    return SUPERIOR_TOOL_BONUS   # superior tool -> positive modifier
                return 0                          # plain present tool -> baseline
        return IMPROVISED_PENALTY                 # expected tool absent/broken
