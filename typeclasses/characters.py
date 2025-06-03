# typeclasses/characters.py
"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

This implementation uses the Traits contrib to provide a rich
character system with stats, survival needs, and skills, combined
with the Clothing contrib for layered equipment that provides
survival benefits and the Cooldowns contrib for action rate limiting.
"""

from evennia.utils import lazy_property
from evennia.contrib.rpg.traits import TraitHandler
from evennia.contrib.game_systems.clothing.clothing import ClothedCharacter as BaseClothedCharacter
from evennia.contrib.game_systems.cooldowns import CooldownHandler
from django.conf import settings

from .objects import ObjectParent


class Character(ObjectParent, BaseClothedCharacter):
    """
    The Character class implements a three-category trait system combined
    with a clothing system that provides survival benefits and a cooldown
    system for rate-limiting actions.
    
    Traits:
    1. Stats (static traits): Core attributes like strength, dexterity
    2. Traits (gauge traits): Survival needs with auto-decay (hunger, thirst, fatigue)
    3. Skills (counter traits): Learnable abilities that progress over time
    
    Clothing:
    - Layered clothing system with weather protection
    - Reduces trait decay in harsh conditions
    - Provides stat bonuses when worn
    - Integrates with Extended Room weather states
    
    Cooldowns:
    - Rate limits gathering, crafting, and other actions
    - Skill-based cooldown reduction for experienced characters
    - Prevents action spamming and encourages strategic timing
    
    Example usage:
        # Check if character has weather protection
        if character.has_weather_protection("rain"):
            # Reduce or eliminate rain penalties
            
        # Get total warmth from clothing
        warmth = character.get_total_warmth()
        
        # Check if action is on cooldown
        if character.cooldowns.ready("gather"):
            # Allow gathering
    """

    # Define the three trait category handlers
    @lazy_property
    def stats(self):
        """
        Handler for character statistics (strength, dexterity, etc).
        These are static traits that don't change automatically.
        """
        return TraitHandler(self, db_attribute_key="stats", db_attribute_category="traits")
    
    @lazy_property
    def traits(self):
        """
        Handler for survival traits (hunger, thirst, fatigue, health).
        These are gauge traits that can auto-decay over time.
        """
        return TraitHandler(self, db_attribute_key="traits", db_attribute_category="traits")
    
    @lazy_property
    def skills(self):
        """
        Handler for learnable skills (crafting, hunting, etc).
        These are counter traits that track progression.
        """
        return TraitHandler(self, db_attribute_key="skills", db_attribute_category="traits")

    @lazy_property
    def cooldowns(self):
        """
        Handler for action cooldowns.
        Tracks when various actions can be performed again.
        """
        return CooldownHandler(self, db_attribute="cooldowns")

    def at_object_creation(self):
        """
        Called once when the character is first created.
        Sets up all the initial traits with their default values.
        """
        super().at_object_creation()
        
        # Initialize Stats (static traits for base attributes)
        self.stats.add("strength", "Strength", trait_type="static", 
                      base=10, mod=0, mult=1.0)
        self.stats.add("dexterity", "Dexterity", trait_type="static", 
                      base=10, mod=0, mult=1.0)
        self.stats.add("constitution", "Constitution", trait_type="static", 
                      base=10, mod=0, mult=1.0)
        self.stats.add("intelligence", "Intelligence", trait_type="static", 
                      base=10, mod=0, mult=1.0)
        self.stats.add("wisdom", "Wisdom", trait_type="static", 
                      base=10, mod=0, mult=1.0)
        self.stats.add("charisma", "Charisma", trait_type="static", 
                      base=10, mod=0, mult=1.0)
        
        # Initialize Traits (gauge traits for survival needs)
        self.traits.add("hunger", "Hunger", trait_type="gauge", 
                       base=100, mod=0, min=0, rate=-2.0,
                       descs={19: "starving", 39: "very hungry", 59: "hungry", 
                             79: "peckish", 99: "satisfied", 100: "full"})
        
        self.traits.add("thirst", "Thirst", trait_type="gauge",
                       base=100, mod=0, min=0, rate=-3.0,
                       descs={19: "dehydrated", 39: "parched", 59: "thirsty",
                             79: "slightly thirsty", 99: "refreshed", 100: "hydrated"})
        
        self.traits.add("fatigue", "Fatigue", trait_type="gauge",
                       base=100, mod=0, min=0, rate=-1.0,
                       descs={19: "exhausted", 39: "very tired", 59: "tired",
                             79: "slightly tired", 99: "rested", 100: "energized"})
        
        self.traits.add("health", "Health", trait_type="gauge",
                       base=100, mod=0, min=0, rate=0,
                       descs={19: "dead", 39: "critically wounded", 59: "badly hurt",
                             79: "wounded", 99: "bruised", 100: "healthy"})
        
        # Initialize Skills
        skill_descs = {
            9: "untrained", 29: "novice", 49: "apprentice",
            69: "journeyman", 89: "expert", 100: "master"
        }
        
        for skill_name in ["crafting", "hunting", "foraging", 
                          "engineering", "survival", "trading"]:
            self.skills.add(skill_name, skill_name.title(), trait_type="counter",
                           base=0, mod=0, min=0, max=100, descs=skill_descs)
        
        # Initialize crafting tracking
        self.db.known_recipes = []
        self.db.craft_counts = {}
        self.db.best_quality = {}
        self.db.crafting_stats = {
            'total_crafted': 0,
            'total_failed': 0,
            'quality_counts': {}
        }
    
    def can_craft_recipe(self, recipe_class):
        """
        Check if character meets requirements for a recipe.
        
        Args:
            recipe_class: The recipe class to check
            
        Returns:
            tuple: (can_craft, reason)
        """
        # Check skill requirement
        skill_req = getattr(recipe_class, 'skill_requirement', 'crafting')
        difficulty = getattr(recipe_class, 'difficulty', 0)
        
        skill_level = 0
        if skill_req == "engineering":
            skill_level = self.skills.engineering.value
        elif skill_req == "survival":
            skill_level = self.skills.survival.value
        else:
            skill_level = self.skills.crafting.value
        
        if skill_level < difficulty:
            return False, f"Need {skill_req} {difficulty}+"
        
        # Check cooldown
        craft_category = getattr(recipe_class, 'craft_category', 'craft_basic')
        if not self.cooldowns.ready(craft_category):
            time_left = self.cooldowns.time_left(craft_category, use_int=True)
            return False, f"On cooldown ({time_left}s)"
        
        return True, "OK"
    
    # Cooldown-related methods
    
    def get_cooldown_modifier(self, action_type, skill_name=None):
        """
        Calculate cooldown modifier based on relevant skill.
        
        Higher skills reduce cooldowns, encouraging specialization.
        
        Args:
            action_type (str): Type of action ("gather", "craft", etc.)
            skill_name (str, optional): Specific skill to check
            
        Returns:
            float: Multiplier for cooldown duration (0.5 - 1.0)
        """
        if not skill_name:
            # Default skill associations
            skill_map = {
                "gather": "foraging",
                "craft": "crafting",
                "hunt": "hunting",
                "trade": "trading",
                "repair": "engineering",
                "rest": "survival"
            }
            skill_name = skill_map.get(action_type, "survival")
        
        skill = self.skills.get(skill_name)
        if not skill:
            return 1.0
        
        skill_level = skill.value
        
        # Linear reduction: 0 skill = 100% cooldown, 100 skill = 50% cooldown
        # This means masters can perform actions twice as often
        reduction = 0.5 + (0.5 * (100 - skill_level) / 100)
        
        return reduction
    
     # typeclasses/characters.py (uppdaterad apply_cooldown metod)

    def apply_cooldown(self, cooldown_name, base_duration, skill_name=None):
        """
        Apply a cooldown with skill-based reduction.
    
        Args:
            cooldown_name (str): Name of the cooldown
            base_duration (int): Base duration in seconds
            skill_name (str, optional): Skill that affects this cooldown
        
        Returns:
            int: Actual cooldown duration applied
        """
        # Get skill-based reduction
        modifier = self.get_cooldown_modifier(cooldown_name, skill_name)
    
        # Apply constitution bonus for physical actions
        if cooldown_name in ["gather", "hunt", "craft"]:
            con_value = self.stats.constitution.value
            # Each point above 10 gives 1% reduction, max 20% at CON 30
            if con_value > 10:
                con_bonus = min((con_value - 10) * 0.01, 0.20)
                modifier *= (1 - con_bonus)
    
        # Calculate final duration
        actual_duration = int(base_duration * modifier)
    
        # Set the cooldown
        self.cooldowns.add(cooldown_name, actual_duration)
    
        return actual_duration

    # Clothing-related methods for survival benefits
    
    def get_worn_clothes(self, exclude_covered=False):
        """
        Get a list of clothes worn by this character.
        
        This wraps the module function for easier access.
        
        Args:
            exclude_covered (bool): If True, exclude covered items
            
        Returns:
            list: Ordered list of worn clothing items
        """
        from evennia.contrib.game_systems.clothing.clothing import get_worn_clothes
        return get_worn_clothes(self, exclude_covered=exclude_covered)
    
    def has_weather_protection(self, weather_type):
        """
        Check if character has protection against specific weather.
        
        Args:
            weather_type (str): Type of weather ('rain', 'snow', 'wind', etc.)
            
        Returns:
            bool: True if character has adequate protection
        """
        worn_items = self.get_worn_clothes(exclude_covered=True)
        
        for item in worn_items:
            # Check if item provides weather protection
            protections = item.db.weather_protection or []
            if weather_type in protections:
                return True
                
        return False
    
    def get_total_warmth(self):
        """
        Calculate total warmth value from all worn clothing.
        
        Returns:
            int: Total warmth value (0-100+)
        """
        total_warmth = 0
        worn_items = self.get_worn_clothes(exclude_covered=True)
        
        for item in worn_items:
            warmth = item.db.warmth_value or 0
            total_warmth += warmth
            
        return total_warmth
    
    def get_clothing_stat_modifiers(self):
        """
        Get all stat modifiers from worn clothing.
        
        Returns:
            dict: Dictionary of stat modifiers {stat_name: total_modifier}
        """
        modifiers = {}
        worn_items = self.get_worn_clothes(exclude_covered=True)
        
        for item in worn_items:
            item_mods = item.db.stat_modifiers or {}
            for stat, value in item_mods.items():
                if stat in modifiers:
                    modifiers[stat] += value
                else:
                    modifiers[stat] = value
                    
        return modifiers
    
    def apply_clothing_modifiers(self):
        """
        Apply stat modifiers from clothing to character stats.
        
        This should be called whenever clothing changes.
        """
        # First, reset all stat mods to 0
        for stat_name in ["strength", "dexterity", "constitution", 
                         "intelligence", "wisdom", "charisma"]:
            stat = self.stats.get(stat_name)
            if stat:
                stat.mod = 0
        
        # Then apply clothing modifiers
        modifiers = self.get_clothing_stat_modifiers()
        for stat_name, modifier in modifiers.items():
            stat = self.stats.get(stat_name)
            if stat:
                stat.mod = modifier
    
    def get_environmental_protection(self):
        """
        Get a summary of all environmental protections.
        
        Returns:
            dict: Protection levels for different conditions
        """
        protection = {
            "cold": 0,      # Protection against cold/winter
            "heat": 0,      # Protection against heat/summer
            "rain": False,  # Binary - either protected or not
            "wind": False,  # Binary - either protected or not
            "general": 0    # General durability/protection
        }
        
        worn_items = self.get_worn_clothes(exclude_covered=True)
        
        for item in worn_items:
            # Warmth adds to cold protection
            protection["cold"] += item.db.warmth_value or 0
            
            # Check weather protections
            weather_prot = item.db.weather_protection or []
            if "rain" in weather_prot:
                protection["rain"] = True
            if "wind" in weather_prot:
                protection["wind"] = True
                
            # Heat protection (negative warmth values)
            if item.db.warmth_value and item.db.warmth_value < 0:
                protection["heat"] += abs(item.db.warmth_value)
                
            # General protection/armor
            protection["general"] += item.db.protection_value or 0
            
        return protection
    
    # Convenience methods (keeping all the original ones)
    
    def get_stat(self, stat_name):
        """Get a stat value by name."""
        stat = self.stats.get(stat_name)
        return stat.value if stat else None
    
    def get_trait_status(self, trait_name):
        """Get both the value and description of a survival trait."""
        trait = self.traits.get(trait_name)
        if trait:
            return (trait.value, trait.desc())
        return (None, None)
    
    def get_skill_level(self, skill_name):
        """Get both the value and proficiency description of a skill."""
        skill = self.skills.get(skill_name)
        if skill:
            return (skill.value, skill.desc())
        return (None, None)
    
    def modify_trait(self, trait_name, amount):
        """Modify a survival trait by a given amount."""
        trait = self.traits.get(trait_name)
        if trait:
            trait.current += amount
            return True
        return False
    
    def improve_skill(self, skill_name, amount=1):
        """Improve a skill by a given amount."""
        skill = self.skills.get(skill_name)
        if skill:
            skill.current += amount
            return True
        return False
    
    def get_survival_summary(self):
        """Get a formatted summary of all survival traits."""
        summary_parts = []
        for trait_name in ["hunger", "thirst", "fatigue", "health"]:
            trait = self.traits.get(trait_name)
            if trait:
                percent_value = int(trait.percent(formatting=None))
                desc = trait.desc()
                summary_parts.append(f"{trait_name.title()}: {percent_value}% ({desc})")
    
        return "\n".join(summary_parts)

    def get_skill_summary(self):
        """Get a formatted summary of all skills."""
        summary_parts = []
        for skill_name in ["crafting", "hunting", "foraging", 
                          "engineering", "survival", "trading"]:
            skill = self.skills.get(skill_name)
            if skill:
                value = int(skill.value)
                desc = skill.desc()
                summary_parts.append(f"{skill_name.title()}: {value} ({desc})")
    
        return "\n".join(summary_parts)
