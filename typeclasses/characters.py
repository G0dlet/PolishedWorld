# typeclasses/characters.py
"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

This implementation uses the Traits contrib to provide a rich
character system with stats, survival needs, and skills.
"""

from evennia.objects.objects import DefaultCharacter
from evennia.utils import lazy_property
from evennia.contrib.rpg.traits import TraitHandler
from django.conf import settings

from .objects import ObjectParent


class Character(ObjectParent, DefaultCharacter):
    """
    The Character class implements a three-category trait system:
    
    1. Stats (static traits): Core attributes like strength, dexterity
    2. Traits (gauge traits): Survival needs with auto-decay (hunger, thirst, fatigue)
    3. Skills (counter traits): Learnable abilities that progress over time
    
    The survival traits decay based on game time, using the custom gametime
    system. With TIME_FACTOR = 4:
    - 1 real hour = 4 game hours
    - Traits decay per game hour as configured
    
    Example usage:
        # Access stats
        character.stats.strength.value  # Returns current strength
        
        # Check survival needs
        if character.traits.hunger.value < 20:
            character.msg("You are very hungry!")
            
        # Improve skills
        character.skills.crafting.current += 5
        
    The survival traits use auto-decay rates:
        - Hunger: -2 per game hour
        - Thirst: -3 per game hour  
        - Fatigue: -1 per game hour
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
        # All start at 100 (full) and decay toward 0
        # Note: In Evennia's desc() implementation, the dict key represents the
        # upper bound (inclusive) for that description, not the lower bound.
        # 
        # IMPORTANT: The rate is per SECOND in the trait system, but we'll
        # use a TickerHandler to update per game hour instead
        self.traits.add("hunger", "Hunger", trait_type="gauge", 
                       base=100, mod=0, min=0, rate=-2.0,  # Will be applied per game hour
                       descs={19: "starving", 39: "very hungry", 59: "hungry", 
                             79: "peckish", 99: "satisfied", 100: "full"})
        
        self.traits.add("thirst", "Thirst", trait_type="gauge",
                       base=100, mod=0, min=0, rate=-3.0,  # Will be applied per game hour
                       descs={19: "dehydrated", 39: "parched", 59: "thirsty",
                             79: "slightly thirsty", 99: "refreshed", 100: "hydrated"})
        
        self.traits.add("fatigue", "Fatigue", trait_type="gauge",
                       base=100, mod=0, min=0, rate=-1.0,  # Will be applied per game hour
                       descs={19: "exhausted", 39: "very tired", 59: "tired",
                             79: "slightly tired", 99: "rested", 100: "energized"})
        
        self.traits.add("health", "Health", trait_type="gauge",
                       base=100, mod=0, min=0, rate=0,  # No auto-decay
                       descs={19: "dead", 39: "critically wounded", 59: "badly hurt",
                             79: "wounded", 99: "bruised", 100: "healthy"})
        
        # Initialize Skills (counter traits for progression)
        # All start at 0 and can progress to 100
        # The dict key is the upper bound for each skill level description
        skill_descs = {
            9: "untrained",    # 0-9
            29: "novice",      # 10-29
            49: "apprentice",  # 30-49
            69: "journeyman",  # 50-69
            89: "expert",      # 70-89
            100: "master"      # 90-100
        }
        
        self.skills.add("crafting", "Crafting", trait_type="counter",
                       base=0, mod=0, min=0, max=100, descs=skill_descs)
        
        self.skills.add("hunting", "Hunting", trait_type="counter",
                       base=0, mod=0, min=0, max=100, descs=skill_descs)
        
        self.skills.add("foraging", "Foraging", trait_type="counter",
                       base=0, mod=0, min=0, max=100, descs=skill_descs)
        
        self.skills.add("engineering", "Engineering", trait_type="counter",
                       base=0, mod=0, min=0, max=100, descs=skill_descs)
        
        self.skills.add("survival", "Survival", trait_type="counter",
                       base=0, mod=0, min=0, max=100, descs=skill_descs)
        
        self.skills.add("trading", "Trading", trait_type="counter",
                       base=0, mod=0, min=0, max=100, descs=skill_descs)
    
    # Convenience methods for common operations
    
    def get_stat(self, stat_name):
        """
        Get a stat value by name.
        
        Args:
            stat_name (str): Name of the stat (e.g., 'strength')
            
        Returns:
            int: The stat's current value, or None if not found
        """
        stat = self.stats.get(stat_name)
        return stat.value if stat else None
    
    def get_trait_status(self, trait_name):
        """
        Get both the value and description of a survival trait.
        
        Args:
            trait_name (str): Name of the trait (e.g., 'hunger')
            
        Returns:
            tuple: (value, description) or (None, None) if not found
        """
        trait = self.traits.get(trait_name)
        if trait:
            return (trait.value, trait.desc())
        return (None, None)
    
    def get_skill_level(self, skill_name):
        """
        Get both the value and proficiency description of a skill.
        
        Args:
            skill_name (str): Name of the skill (e.g., 'crafting')
            
        Returns:
            tuple: (value, description) or (None, None) if not found
        """
        skill = self.skills.get(skill_name)
        if skill:
            return (skill.value, skill.desc())
        return (None, None)
    
    def modify_trait(self, trait_name, amount):
        """
        Modify a survival trait by a given amount.
        
        Args:
            trait_name (str): Name of the trait to modify
            amount (int/float): Amount to add (positive) or subtract (negative)
            
        Returns:
            bool: True if successful, False if trait not found
        """
        trait = self.traits.get(trait_name)
        if trait:
            trait.current += amount
            return True
        return False
    
    def improve_skill(self, skill_name, amount=1):
        """
        Improve a skill by a given amount.
        
        Args:
            skill_name (str): Name of the skill to improve
            amount (int): Amount to increase skill by (default 1)
            
        Returns:
            bool: True if successful, False if skill not found
        """
        skill = self.skills.get(skill_name)
        if skill:
            skill.current += amount
            return True
        return False
    
    def get_survival_summary(self):
        """
        Get a formatted summary of all survival traits.
    
        Returns:
            str: Formatted string showing all survival trait statuses
        """
        summary_parts = []
        for trait_name in ["hunger", "thirst", "fatigue", "health"]:
            trait = self.traits.get(trait_name)
            if trait:
                # Get the raw percentage value without formatting
                percent_value = int(trait.percent(formatting=None))
                desc = trait.desc()
                summary_parts.append(f"{trait_name.title()}: {percent_value}% ({desc})")
    
        return "\n".join(summary_parts)

    def get_skill_summary(self):
        """
        Get a formatted summary of all skills.
    
        Returns:
            str: Formatted string showing all skill levels
        """
        summary_parts = []
        for skill_name in ["crafting", "hunting", "foraging", 
                          "engineering", "survival", "trading"]:
            skill = self.skills.get(skill_name)
            if skill:
                # Convert to int for cleaner display
                value = int(skill.value)
                desc = skill.desc()
                summary_parts.append(f"{skill_name.title()}: {value} ({desc})")
    
        return "\n".join(summary_parts)
    
    def get_time_info(self):
        """
        Get current game time information relevant to the character.
        
        Returns:
            dict: Dictionary with time-related information
        """
        from world.gametime_utils import (
            get_current_season, get_time_of_day, 
            format_game_date, get_seasonal_modifier
        )
        
        return {
            "date": format_game_date(),
            "time_of_day": get_time_of_day(),
            "season": get_current_season(),
            "seasonal_modifiers": get_seasonal_modifier(),
        }
    
    def apply_seasonal_fatigue_modifier(self):
        """
        Apply seasonal modifiers to fatigue rate.
        This will be called by the TickerHandler.
        
        Note: This is preparation for the TickerHandler step.
        """
        from world.gametime_utils import get_seasonal_modifier
        
        modifiers = get_seasonal_modifier()
        fatigue_mod = modifiers.get("fatigue_rate", 1.0)
        
        # Store the modifier for use by TickerHandler
        self.db.seasonal_fatigue_modifier = fatigue_mod
        
        return fatigue_mod
