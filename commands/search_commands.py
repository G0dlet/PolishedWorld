# commands/search_commands.py
"""
Search commands for finding hidden objects and resources.

These commands work with the Extended Room's visibility system
to allow players to actively search for hidden items.
"""

from evennia import Command
from evennia.utils import list_to_string
import random


class CmdSearch(Command):
    """
    Search the room for hidden objects or resources.
    
    Usage:
        search
        search <target>
        search for <resource>
        
    Examples:
        search                    - General search of the room
        search bushes            - Search a specific detail  
        search for plants        - Search for forgeable plants
        
    This command allows you to find hidden objects that aren't
    immediately visible. Your success depends on:
    - The visibility conditions (light, weather)
    - Your relevant skills (foraging, survival)
    - The hidden object's concealment level
    
    Some objects can only be found through searching.
    """
    
    key = "search"
    locks = "cmd:all()"
    help_category = "General"
    
    def parse(self):
        """Parse the command input."""
        self.raw = self.raw_string.strip()
        
        # Check for "search for <resource>" pattern
        if " for " in self.args:
            parts = self.args.split(" for ", 1)
            self.search_target = None
            self.resource_type = parts[1].strip()
        else:
            self.search_target = self.args.strip() if self.args else None
            self.resource_type = None
    
    def func(self):
        """Perform the search."""
        caller = self.caller
        location = caller.location
        
        if not location:
            caller.msg("You have nowhere to search.")
            return
        
        # Check if still on cooldown
        if not caller.cooldowns.ready("search"):
            time_left = caller.cooldowns.time_left("search", use_int=True)
            caller.msg(f"You are still recovering from your last search. "
                      f"Wait {time_left} more seconds.")
            return
        
        # Different search types
        if self.resource_type:
            self.search_for_resources()
        elif self.search_target:
            self.search_specific_target()
        else:
            self.search_general()
        
        # Set cooldown (30 seconds base)
        caller.cooldowns.add("search", 30)
    
    def search_general(self):
        """Perform a general search of the room."""
        caller = self.caller
        location = caller.location
        
        # Announce the search
        caller.msg("You carefully search the area...")
        location.msg_contents(
            f"{caller.name} carefully searches the area.",
            exclude=caller
        )
        
        # Get all hidden objects in the room
        hidden_objects = [
            obj for obj in location.contents
            if obj.db.hidden and not obj.has_account
        ]
        
        if not hidden_objects:
            caller.msg("Your search reveals nothing special.")
            return
        
        # Calculate search success for each hidden object
        found_objects = []
        search_skill = caller.skills.foraging.value
        survival_skill = caller.skills.survival.value
        
        # Better skills improve search chances
        base_chance = 0.3 + (search_skill / 200) + (survival_skill / 400)
        
        # Environmental modifiers
        visibility_range = location.get_visibility_range(caller)
        if visibility_range < 3:
            base_chance *= 0.5  # Hard to search in poor visibility
        
        # Check each hidden object
        for obj in hidden_objects:
            # Adjust chance based on object properties
            chance = base_chance
            
            # Tiny objects are harder to find
            if obj.db.visibility_size == "tiny":
                chance *= 0.5
            elif obj.db.visibility_size == "small":
                chance *= 0.7
            
            # Camouflaged objects are harder
            if obj.db.contrast == "camouflaged":
                chance *= 0.5
            
            # Roll for discovery
            if random.random() < chance:
                found_objects.append(obj)
                obj.db.hidden = False  # No longer hidden once found
        
        # Report findings
        if found_objects:
            caller.msg(f"Your search reveals: {list_to_string(found_objects)}!")
            
            # Skill improvement
            if search_skill < 100:
                if caller.improve_skill("foraging", 2):
                    caller.msg("Your foraging skill improves from the careful search.")
        else:
            caller.msg("Your search reveals nothing special.")
    
    def search_specific_target(self):
        """Search a specific target or detail."""
        caller = self.caller
        location = caller.location
        
        # First check if it's a room detail
        if hasattr(location, 'get_detail'):
            detail = location.get_detail(self.search_target)
            if detail:
                caller.msg(f"You carefully examine the {self.search_target}...")
                location.msg_contents(
                    f"{caller.name} carefully examines the {self.search_target}.",
                    exclude=caller
                )
                
                # Details might hide objects
                # For now, just show the detail with search flavor
                caller.msg(f"Your careful examination reveals:\n{detail}")
                return
        
        # Search for a specific visible object
        obj = caller.search(self.search_target, location=location)
        if not obj:
            return
        
        caller.msg(f"You carefully search around {obj.get_display_name(caller)}...")
        location.msg_contents(
            f"{caller.name} searches around {obj.get_display_name(caller)}.",
            exclude=caller
        )
        
        # For now, just give more detailed description
        # Could later hide things "under" or "inside" objects
        desc = obj.db.desc
        if desc:
            caller.msg(f"Your thorough examination reveals: {desc}")
        else:
            caller.msg("Your search reveals nothing special about it.")
    
    def search_for_resources(self):
        """Search specifically for gatherable resources."""
        caller = self.caller
        location = caller.location
        
        # Check if the resource type exists in this room
        resources = location.db.resources or {}
        if self.resource_type not in resources:
            caller.msg(f"You don't think you can find {self.resource_type} here.")
            return
        
        resource = resources[self.resource_type]
        current = resource.get("current", 0)
        
        # Check if any available
        if current == 0:
            caller.msg(f"You search carefully but find no {self.resource_type} available.")
            return
        
        # Calculate how much they can detect
        skill_required = resource.get("skill_required", "foraging")
        skill_level = 0
        if skill_required:
            skill_level = caller.skills.get(skill_required).value
        
        # Better skill reveals more accurate counts
        availability = location.get_resource_availability(self.resource_type)
        effective_amount = int(current * availability)
        
        if skill_level < 20:
            # Vague description
            if effective_amount == 0:
                amount_desc = "no"
            elif effective_amount < 3:
                amount_desc = "very little"
            elif effective_amount < 6:
                amount_desc = "some"
            else:
                amount_desc = "plenty of"
        else:
            # More precise with better skill
            amount_desc = f"about {effective_amount} units of"
        
        caller.msg(f"Your search reveals {amount_desc} {self.resource_type} available here.")
        
        # Small skill gain for searching
        if skill_required and skill_level < 100:
            if random.random() < 0.3:  # 30% chance
                caller.improve_skill(skill_required, 1)


class CmdLight(Command):
    """
    Light or extinguish a light source.
    
    Usage:
        light <object>
        extinguish <object>
        
    Examples:
        light torch
        extinguish lantern
        
    Light sources help you see better in dark conditions.
    They reveal more objects and increase visibility range.
    """
    
    key = "light"
    aliases = ["extinguish", "douse", "ignite"]
    locks = "cmd:all()"
    help_category = "General"
    
    def func(self):
        """Execute the light command."""
        caller = self.caller
        
        if not self.args:
            caller.msg(f"What do you want to {self.cmdstring}?")
            return
        
        # Find the target
        target = caller.search(self.args, location=caller)
        if not target:
            return
        
        # Check if it's a light source
        if not target.db.is_light_source:
            caller.msg(f"{target.get_display_name(caller)} is not a light source.")
            return
        
        # Determine action
        if self.cmdstring in ["light", "ignite"]:
            # Try to light it
            if hasattr(target, 'do_light'):
                target.do_light(caller)
            else:
                # Generic lighting
                if target.db.light_active:
                    caller.msg(f"{target.get_display_name(caller)} is already lit.")
                else:
                    target.toggle_light()
                    caller.msg(f"You light {target.get_display_name(caller)}.")
                    caller.location.msg_contents(
                        f"{caller.name} lights {target.get_display_name(caller)}.",
                        exclude=caller
                    )
        else:
            # Try to extinguish it
            if hasattr(target, 'do_extinguish'):
                target.do_extinguish(caller)
            else:
                # Generic extinguishing
                if not target.db.light_active:
                    caller.msg(f"{target.get_display_name(caller)} is not lit.")
                else:
                    target.toggle_light()
                    caller.msg(f"You extinguish {target.get_display_name(caller)}.")
                    caller.location.msg_contents(
                        f"{caller.name} extinguishes {target.get_display_name(caller)}.",
                        exclude=caller
                    )
