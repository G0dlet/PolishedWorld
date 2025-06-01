# commands/resource_commands.py
"""
Resource gathering commands for the survival game.

These commands allow players to gather resources from rooms,
integrating with the Extended Room's resource system.
"""

from evennia import Command
from evennia.utils import create, list_to_string
import random


class CmdGather(Command):
    """
    Gather resources from the environment.
    
    Usage:
        gather <resource>
        gather <amount> <resource>
        
    Examples:
        gather wood
        gather 5 stone
        gather plants
        
    This command allows you to gather resources from the current
    location. Success depends on:
    - Resource availability (season, weather)
    - Required skills and tools
    - Your skill level (higher skill = more yield)
    
    Different resources may require different tools:
    - Wood: No tool required (hands)
    - Stone: Requires a pickaxe
    - Plants: No tool required
    - Water: Requires a container
    
    Your gathering skills will improve with practice.
    """
    
    key = "gather"
    aliases = ["collect", "harvest", "forage"]
    locks = "cmd:all()"
    help_category = "Survival"
    
    def parse(self):
        """Parse the arguments."""
        args = self.args.strip().split()
        
        if not args:
            self.resource_type = None
            self.amount = 1
            return
        
        # Check if first arg is a number
        try:
            self.amount = int(args[0])
            self.resource_type = " ".join(args[1:]) if len(args) > 1 else None
        except ValueError:
            self.amount = 1
            self.resource_type = " ".join(args)
    
    def func(self):
        """Execute the gather command."""
        caller = self.caller
        location = caller.location
        
        if not location:
            caller.msg("You have nowhere to gather from.")
            return
        
        if not self.resource_type:
            # List available resources
            self.list_resources()
            return
        
        # Check cooldown
        if not caller.cooldowns.ready("gather"):
            time_left = caller.cooldowns.time_left("gather", use_int=True)
            caller.msg(f"You are still tired from gathering. "
                      f"Wait {time_left} more seconds.")
            return
        
        # Attempt to gather
        resources = location.db.resources or {}
        if self.resource_type not in resources:
            caller.msg(f"You can't gather {self.resource_type} here.")
            return
        
        # Use the room's extraction method
        success, gathered, skill_gain = location.extract_resource(
            caller, self.resource_type, self.amount
        )
        
        if not success:
            return  # Error message already sent by extract_resource
        
        # Create the gathered resources
        self.create_gathered_items(gathered)
        
        # Apply skill gain
        resource = resources[self.resource_type]
        skill_type = resource.get("skill_required", "foraging")
        if skill_type and skill_gain > 0:
            if caller.improve_skill(skill_type, skill_gain):
                caller.msg(f"Your {skill_type} skill improves!")
        
        # Set cooldown based on amount gathered
        base_cooldown = 300  # 5 minutes base
        actual_cooldown = base_cooldown * (1 + gathered / 5)
        # Reduce cooldown with higher skill
        if skill_type:
            skill_level = caller.skills.get(skill_type).value
            actual_cooldown *= (1 - skill_level / 200)  # Up to 50% reduction
        
        caller.cooldowns.add("gather", int(actual_cooldown))
    
    def list_resources(self):
        """List available resources in the room."""
        caller = self.caller
        location = caller.location
        
        resources = location.db.resources or {}
        if not resources:
            caller.msg("There are no gatherable resources here.")
            return
        
        caller.msg("|wAvailable resources:|n")
        
        for res_type, res_data in resources.items():
            current = res_data.get("current", 0)
            tool = res_data.get("tool_required", "none")
            skill = res_data.get("skill_required", "none")
            min_skill = res_data.get("min_skill", 0)
            
            # Get availability with seasonal modifiers
            availability = location.get_resource_availability(res_type)
            
            # Determine amount description
            if current < 0:
                amount_desc = "unlimited"
            elif current == 0:
                amount_desc = "|rdepleted|n"
            else:
                effective = int(current * availability)
                if effective == 0:
                    amount_desc = "|runavailable (seasonal)|n"
                elif effective < 3:
                    amount_desc = "|yscarce|n"
                elif effective < 6:
                    amount_desc = "|gmoderate|n"
                else:
                    amount_desc = "|Gplentiful|n"
            
            # Build info string
            info_parts = [f"|c{res_type}|n: {amount_desc}"]
            if tool != "none" and tool:
                info_parts.append(f"tool: {tool}")
            if skill != "none" and skill:
                if min_skill > 0:
                    info_parts.append(f"requires: {skill} {min_skill}+")
                else:
                    info_parts.append(f"skill: {skill}")
            
            caller.msg(f"  {' - '.join(info_parts)}")
    
    def create_gathered_items(self, amount):
        """
        Create the actual gathered items.
        
        Args:
            amount (int): Number of items to create
        """
        caller = self.caller
        location = caller.location
        
        # Define prototypes for different resources
        resource_prototypes = {
            "wood": {
                "key": "piece of wood",
                "aliases": ["wood"],
                "desc": "A sturdy piece of wood suitable for crafting.",
                "tags": [("material", "crafting"), ("wood", "material_type")],
                "weight": 2.0,
                "value": 1
            },
            "stone": {
                "key": "rough stone",
                "aliases": ["stone"],
                "desc": "A chunk of rough stone that could be worked.",
                "tags": [("material", "crafting"), ("stone", "material_type")],
                "weight": 5.0,
                "value": 1
            },
            "plants": {
                "key": "edible plants",
                "aliases": ["plants", "herbs"],
                "desc": "A handful of edible plants and herbs.",
                "tags": [("food", "crafting"), ("plants", "material_type")],
                "weight": 0.5,
                "value": 2,
                "nutrition": 10
            },
            "water": {
                "key": "water",
                "aliases": ["water"],
                "desc": "Fresh water in your container.",
                "tags": [("drink", "crafting"), ("water", "material_type")],
                "weight": 1.0,
                "value": 1,
                "thirst_value": 20
            }
        }
        
        prototype = resource_prototypes.get(self.resource_type)
        if not prototype:
            # Generic resource
            prototype = {
                "key": self.resource_type,
                "desc": f"Some gathered {self.resource_type}.",
                "tags": [("material", "crafting")],
                "weight": 1.0
            }
        
        # Create the items
        created_items = []
        for i in range(amount):
            obj = create.create_object(
                "typeclasses.objects.Object",
                key=prototype["key"],
                location=caller
            )
            
            # Set properties
            obj.aliases.add(prototype.get("aliases", []))
            obj.db.desc = prototype["desc"]
            for tag_tuple in prototype.get("tags", []):
                obj.tags.add(*tag_tuple)
            
            # Set optional properties
            for attr in ["weight", "value", "nutrition", "thirst_value"]:
                if attr in prototype:
                    obj.db.set(attr, prototype[attr])
            
            created_items.append(obj)
        
        # Message about gathering
        if amount == 1:
            caller.msg(f"You gather {created_items[0].get_display_name(caller)}.")
        else:
            caller.msg(f"You gather {amount} {prototype['key']}s.")
        
        location.msg_contents(
            f"{caller.name} gathers some {self.resource_type}.",
            exclude=caller
        )


class CmdForage(Command):
    """
    Quick command to search for and gather edible plants.
    
    Usage:
        forage
        
    This is a shortcut that combines searching for plants
    and gathering them if found. It's useful for quick
    sustenance gathering.
    """
    
    key = "forage"
    locks = "cmd:all()"
    help_category = "Survival"
    
    def func(self):
        """Execute forage command."""
        caller = self.caller
        location = caller.location
        
        if not location:
            caller.msg("You have nowhere to forage.")
            return
        
        # Check if plants are available
        resources = location.db.resources or {}
        if "plants" not in resources:
            caller.msg("There's nothing to forage here.")
            return
        
        # Check cooldown
        if not caller.cooldowns.ready("gather"):
            time_left = caller.cooldowns.time_left("gather", use_int=True)
            caller.msg(f"You are still tired from gathering. "
                      f"Wait {time_left} more seconds.")
            return
        
        # Quick search animation
        caller.msg("You search the area for edible plants...")
        location.msg_contents(
            f"{caller.name} forages for food.",
            exclude=caller
        )
        
        # Use the gather functionality
        success, gathered, skill_gain = location.extract_resource(
            caller, "plants", 3  # Try to gather up to 3
        )
        
        if success and gathered > 0:
            # Create simple food items
            for i in range(gathered):
                food = create.create_object(
                    "typeclasses.objects.Object",
                    key="handful of berries",
                    location=caller
                )
                food.aliases.add(["berries", "food"])
                food.db.desc = "A handful of foraged berries and edible plants."
                food.tags.add("food", category="item_type")
                food.db.nutrition = 15
                food.db.weight = 0.3
            
            if gathered == 1:
                caller.msg("You find a handful of berries.")
            else:
                caller.msg(f"You find {gathered} handfuls of berries.")
            
            # Skill improvement
            if skill_gain > 0 and caller.improve_skill("foraging", skill_gain):
                caller.msg("Your foraging skill improves!")
            
            # Set shorter cooldown for foraging
            caller.cooldowns.add("gather", 180)  # 3 minutes
        else:
            caller.msg("You don't find anything edible.")
