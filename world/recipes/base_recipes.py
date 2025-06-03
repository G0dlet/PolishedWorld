# world/recipes/base_recipes.py
"""
Base recipe classes for the crafting system.

This module provides base classes that integrate crafting with
our skill system and quality mechanics.
"""

from evennia.contrib.game_systems.crafting.crafting import CraftingRecipe, CraftingValidationError
from evennia.utils import gametime, iter_to_str
from random import random, randint
from django.conf import settings


class SkillBasedRecipe(CraftingRecipe):
    """
    Base recipe class that integrates with our skill system.
    
    This adds:
    - Skill requirements and checks
    - Quality variations based on crafter skill
    - Tool quality considerations  
    - Integration with cooldown system
    
    Additional properties:
        skill_requirement (str): Primary skill needed
        difficulty (int): Minimum skill level (0-100)
        quality_levels (dict): Maps skill ranges to quality outputs
        craft_time (int): Base crafting time in seconds
        craft_category (str): Category for cooldowns ("craft_basic", "craft_advanced", etc)
    """
    
    # Base properties
    skill_requirement = "crafting"
    difficulty = 0
    craft_time = 300  # 5 minutes base
    craft_category = "craft_basic"
    
    # Quality mapping based on skill vs difficulty
    quality_levels = {
        -20: "poor",      # 20+ below difficulty
        -10: "average",   # 10-19 below
        0: "good",        # At difficulty
        10: "fine",       # 10+ above
        20: "excellent",  # 20+ above
        30: "masterwork"  # 30+ above (requires master skill)
    }
    
    # Messages
    error_skill_too_low = "You need at least {difficulty} {skill_name} to craft {outputs}."
    error_on_cooldown = "You are too tired to craft. Wait {time_left} seconds."
    
    # I world/recipes/base_recipes.py

    def pre_craft(self, **kwargs):
        """
        Validate inputs and check skill requirements.
        """
        # Do normal validation first
        super().pre_craft(**kwargs)
    
        # Check if crafter is on cooldown
        if hasattr(self.crafter, 'cooldowns') and not self.crafter.cooldowns.ready(self.craft_category):
            time_left = self.crafter.cooldowns.time_left(self.craft_category, use_int=True)
            err = self.error_on_cooldown.format(time_left=time_left)
            self.msg(err)
            raise CraftingValidationError(err)
    
        # Check skill requirement
        if hasattr(self.crafter, 'skills'):
            # ÄNDRING: Använd skills direkt istället för get_skill_level
            skill = getattr(self.crafter.skills, self.skill_requirement, None)
            if skill:
                skill_level = skill.value
                skill_desc = skill.desc() if hasattr(skill, 'desc') else "unknown"
            else:
                skill_level = 0
                skill_desc = "untrained"
        else:
            # Fallback for testing or NPCs
            skill_level = 0
            skill_desc = "untrained"
        
        if skill_level < self.difficulty:
            err = self.error_skill_too_low.format(
                difficulty=self.difficulty,
                skill_name=self.skill_requirement,
                outputs=iter_to_str([proto.get('key', 'item') for proto in self.output_prototypes])
            )
            self.msg(err)
            raise CraftingValidationError(err)
    
        # Store skill level for use in do_craft
        self.crafter_skill = skill_level

    def calculate_quality(self):
        """
        Calculate output quality based on skill and other factors.
    
        Returns:
            tuple: (quality_name, quality_modifier)
        """
        # Base quality from skill vs difficulty
        skill_diff = self.crafter_skill - self.difficulty
    
        # Find appropriate quality level
        quality_name = "average"
        for threshold in sorted(self.quality_levels.keys(), reverse=True):
            if skill_diff >= threshold:
                quality_name = self.quality_levels[threshold]
                break
    
        # Calculate quality modifier for item stats
        base_modifier = 1.0 + (skill_diff / 100.0)  # +1% per skill point above difficulty
    
        # Tool quality bonus (if applicable)
        tool_bonus = 0
        for tool in self.validated_tools:
            # FIXA: Kontrollera att quality finns och har ett värde
            if hasattr(tool, 'db') and hasattr(tool.db, 'quality') and tool.db.quality is not None:
                tool_bonus += (tool.db.quality - 50) / 200.0  # -25% to +25% based on tool quality
            # Om inget quality är satt, anta standard quality (50)
            else:
                tool_bonus += 0  # Ingen bonus/penalty för verktyg utan quality
    
        if self.validated_tools:
            tool_bonus /= len(self.validated_tools)
    
        total_modifier = base_modifier + tool_bonus
    
        # Add some randomness (±10%)
        total_modifier *= (0.9 + random() * 0.2)
    
        # Clamp between 0.5 and 2.0
        total_modifier = max(0.5, min(2.0, total_modifier))
    
        return quality_name, total_modifier

    def do_craft(self, **kwargs):
        """
        Perform the crafting with quality variations.
        """
        # Calculate quality
        quality_name, quality_modifier = self.calculate_quality()
        
        # Success chance based on skill
        success_chance = 0.5 + (self.crafter_skill / 200.0)  # 50-100% based on skill
        
        if random() > success_chance:
            self.msg("|rYour crafting attempt fails! The materials are ruined.|n")
            return []
        
        # Create items with quality modifications
        created_items = []
        for prototype in self.output_prototypes:
            # Copy prototype to avoid modifying original
            modified_proto = prototype.copy()
            
            # Add quality to key
            if quality_name != "average":
                modified_proto["key"] = f"{quality_name} {modified_proto['key']}"
            
            # Apply quality modifier to relevant attributes
            if "attrs" not in modified_proto:
                modified_proto["attrs"] = []
            
            # Add quality-related attributes
            modified_proto["attrs"].extend([
                ("quality", quality_name),
                ("quality_modifier", quality_modifier),
                ("crafted_by", self.crafter.key),
                ("craft_date", gametime.gametime())
            ])
            
            # Spawn the item
            from evennia.prototypes.spawner import spawn
            items = spawn(modified_proto)
            created_items.extend(items)
        
        # Apply crafting skill improvement
        if self.crafter_skill < 100 and hasattr(self.crafter, 'improve_skill'):
            # More skill gain for harder recipes
            skill_gain = max(1, (self.difficulty // 20))
            if self.crafter.improve_skill(self.skill_requirement, skill_gain):
                self.msg(f"|gYour {self.skill_requirement} skill improves!|n")
        
        return created_items
    
    # I world/recipes/base_recipes.py (i SkillBasedRecipe)

    def post_craft(self, craft_result, **kwargs):
        """
        Handle post-crafting cleanup and cooldowns.
        """
        # Call parent to handle consumables and messages
        result = super().post_craft(craft_result, **kwargs)
    
        if craft_result:
            # Track successful craft
            if hasattr(self.crafter, 'db'):
                # Add to known recipes
                if not hasattr(self.crafter.db, 'known_recipes'):
                    self.crafter.db.known_recipes = []
                if self.name not in self.crafter.db.known_recipes:
                    self.crafter.db.known_recipes.append(self.name)
            
                # Update craft count
                if not hasattr(self.crafter.db, 'craft_counts'):
                    self.crafter.db.craft_counts = {}
                self.crafter.db.craft_counts[self.name] = self.crafter.db.craft_counts.get(self.name, 0) + 1
            
                # Track quality
                for item in craft_result:
                    if hasattr(item.db, 'quality'):
                        quality = item.db.quality
                        if not hasattr(self.crafter.db, 'best_quality'):
                            self.crafter.db.best_quality = {}
                        current_best = self.crafter.db.best_quality.get(self.name, "poor")
                        quality_order = ["poor", "average", "good", "fine", "excellent", "masterwork"]
                        if quality in quality_order and current_best in quality_order:
                            if quality_order.index(quality) > quality_order.index(current_best):
                                self.crafter.db.best_quality[self.name] = quality
                    
                        # Update stats
                        if not hasattr(self.crafter.db, 'crafting_stats'):
                            self.crafter.db.crafting_stats = {'total_crafted': 0, 'total_failed': 0, 'quality_counts': {}}
                        self.crafter.db.crafting_stats['total_crafted'] += 1
                        quality_counts = self.crafter.db.crafting_stats.get('quality_counts', {})
                        quality_counts[quality] = quality_counts.get(quality, 0) + 1
                        self.crafter.db.crafting_stats['quality_counts'] = quality_counts
        
            # Apply cooldown
            if hasattr(self.crafter, 'apply_cooldown'):
                actual_cooldown = self.crafter.apply_cooldown(
                    self.craft_category, 
                    self.craft_time,
                    self.skill_requirement
                )
            
                # Show quality message
                for item in craft_result:
                    if hasattr(item, 'db') and hasattr(item.db, 'quality'):
                        quality = item.db.quality
                        if quality != "average":
                            self.msg(f"|yYou created a {quality} quality item!|n")
    
        return result


class SkillAndStatRecipe(SkillBasedRecipe):
    """
    Advanced recipe that also considers character stats.
    
    Some recipes benefit from specific stats:
    - STR for heavy work (smithing)
    - DEX for precision work (clockwork)
    - INT for complex recipes (engineering)
    """
    
    # Additional properties
    stat_requirement = None  # e.g., "strength"
    stat_weight = 0.3  # How much the stat affects outcome (0-1)
    
    def calculate_quality(self):
        """Override to include stat bonuses."""
        quality_name, quality_modifier = super().calculate_quality()
        
        # Add stat bonus if applicable
        if self.stat_requirement and hasattr(self.crafter, 'get_stat'):
            stat_value = self.crafter.get_stat(self.stat_requirement)
            if stat_value:
                # Each point above 10 gives a small bonus
                stat_bonus = (stat_value - 10) * 0.02 * self.stat_weight
                quality_modifier += stat_bonus
        
        # Re-clamp after stat bonus
        quality_modifier = max(0.5, min(2.0, quality_modifier))
        
        return quality_name, quality_modifier
