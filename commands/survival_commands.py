# commands/survival_commands.py
"""
Survival-related commands for managing character needs.

These commands allow players to manage their survival traits
like hunger, thirst, and fatigue, with cooldown integration.
"""

from evennia import Command
from evennia.utils import delay
import random


class CmdRest(Command):
    """
    Rest to recover fatigue.
    
    Usage:
        rest
        rest <duration>
        
    Examples:
        rest           - Rest for a standard period
        rest long      - Take an extended rest
        rest short     - Take a quick power nap
        
    Resting helps recover fatigue but makes you vulnerable.
    You cannot perform other actions while resting.
    
    The effectiveness of rest depends on:
    - Your current shelter (indoor vs outdoor)
    - Weather conditions
    - Your survival skill
    - Whether you have proper bedding
    
    There is a cooldown between rest sessions to prevent
    abuse of the system.
    """
    
    key = "rest"
    aliases = ["sleep", "nap", "recover"]
    locks = "cmd:all()"
    help_category = "Survival"
    
    def parse(self):
        """Parse rest duration."""
        self.duration = self.args.strip().lower() if self.args else "normal"
    
    def func(self):
        """Execute the rest command."""
        caller = self.caller
        location = caller.location
        
        # Check if already resting
        if caller.db.is_resting:
            caller.msg("You are already resting.")
            return
        
        # Check cooldown
        if not caller.cooldowns.ready("rest"):
            time_left = caller.cooldowns.time_left("rest", use_int=True)
            caller.msg(f"|yYou are not tired enough to rest again. "
                      f"Wait {time_left} more seconds.|n")
            return
        
        # Check current fatigue
        fatigue_value, fatigue_desc = caller.get_trait_status("fatigue")
        if fatigue_value >= 95:
            caller.msg("You are already fully rested.")
            return
        
        # Determine rest duration and recovery
        duration_map = {
            "short": {"time": 30, "recovery": 15, "desc": "a quick nap"},
            "normal": {"time": 60, "recovery": 30, "desc": "a good rest"},
            "long": {"time": 120, "recovery": 50, "desc": "a long sleep"}
        }
        
        rest_info = duration_map.get(self.duration, duration_map["normal"])
        rest_time = rest_info["time"]
        base_recovery = rest_info["recovery"]
        
        # Calculate recovery bonuses
        recovery_bonus = 0
        
        # Indoor bonus
        if location.db.indoor:
            recovery_bonus += 10
            bonus_msg = "The shelter helps you rest better."
        else:
            bonus_msg = ""
        
        # Weather penalties
        weather = location.get_current_weather()
        if "storm" in weather:
            recovery_bonus -= 20
            bonus_msg = "The storm makes it hard to rest properly."
        elif "rain" in weather:
            recovery_bonus -= 10
            bonus_msg = "The rain disturbs your rest."
        
        # Survival skill bonus
        survival_skill = caller.skills.survival.value
        skill_bonus = survival_skill // 4  # Up to +25 at max skill
        recovery_bonus += skill_bonus
        
        # Total recovery
        total_recovery = max(5, base_recovery + recovery_bonus)
        
        # Set resting state
        caller.db.is_resting = True
        
        # Messages
        caller.msg(f"|cYou settle down for {rest_info['desc']}.|n")
        if bonus_msg:
            caller.msg(f"|x{bonus_msg}|n")
            
        location.msg_contents(
            f"{caller.name} settles down to rest.",
            exclude=caller
        )
        
        # Delayed recovery
        def finish_rest():
            if caller.db.is_resting:
                caller.db.is_resting = False
                caller.modify_trait("fatigue", total_recovery)
                new_fatigue, new_desc = caller.get_trait_status("fatigue")
                
                caller.msg(f"|gYou finish resting and feel {new_desc}.|n")
                caller.msg(f"|xFatigue recovered: +{total_recovery}|n")
                
                location.msg_contents(
                    f"{caller.name} gets up from resting.",
                    exclude=caller
                )
                
                # Apply cooldown
                base_cooldown = 180  # 3 minutes base
                actual_cooldown = caller.apply_cooldown("rest", base_cooldown, "survival")
                
                if skill_bonus > 0:
                    caller.msg("|xYour survival skills help you rest more efficiently.|n")
        
        # Use delay to simulate rest time
        delay(rest_time, finish_rest)
        
        # Inform about duration
        caller.msg(f"|xYou will rest for {rest_time} seconds...|n")


class CmdEat(Command):
    """
    Eat food to reduce hunger.
    
    Usage:
        eat <food>
        
    Examples:
        eat bread
        eat berries
        
    Eating food restores your hunger level. Different foods
    provide different amounts of nutrition. Cooked food is
    generally more nutritious than raw ingredients.
    
    You can only eat when you're actually hungry to prevent
    food waste.
    """
    
    key = "eat"
    aliases = ["consume"]
    locks = "cmd:all()"
    help_category = "Survival"
    
    def func(self):
        """Execute the eat command."""
        caller = self.caller
        
        if not self.args:
            caller.msg("Eat what?")
            return
        
        # Find the food item
        food = caller.search(self.args, location=caller)
        if not food:
            return
        
        # Check if it's edible
        if not food.tags.has("food", category="item_type"):
            caller.msg(f"You can't eat {food.get_display_name(caller)}.")
            return
        
        # Check hunger level
        hunger_value, hunger_desc = caller.get_trait_status("hunger")
        if hunger_value >= 90:
            caller.msg("You're too full to eat anything right now.")
            return
        
        # Get nutrition value
        nutrition = food.db.nutrition or 10
        
        # Apply to hunger
        caller.modify_trait("hunger", nutrition)
        new_hunger, new_desc = caller.get_trait_status("hunger")
        
        # Message
        caller.msg(f"|gYou eat {food.get_display_name(caller)}.|n")
        caller.msg(f"|xYou feel {new_desc}. (Hunger +{nutrition})|n")
        
        caller.location.msg_contents(
            f"{caller.name} eats {food.get_display_name(caller)}.",
            exclude=caller
        )
        
        # Consume the food
        food.delete()
        
        # No cooldown on eating, but limited by hunger level


class CmdDrink(Command):
    """
    Drink water to reduce thirst.
    
    Usage:
        drink <liquid>
        drink from <source>
        
    Examples:
        drink water
        drink from stream
        
    Drinking restores your thirst level. Clean water is more
    effective than other liquids. Some water sources may
    require purification.
    """
    
    key = "drink"
    locks = "cmd:all()"
    help_category = "Survival"
    
    def func(self):
        """Execute the drink command."""
        caller = self.caller
        
        if not self.args:
            caller.msg("Drink what?")
            return
        
        # Parse "from" syntax
        args = self.args.strip()
        if " from " in args:
            _, source = args.split(" from ", 1)
            # Look for water source in room
            water_source = caller.search(source, location=caller.location)
            if water_source and water_source.tags.has("water_source"):
                self.drink_from_source(water_source)
                return
        
        # Otherwise look for water item
        water = caller.search(args, location=caller)
        if not water:
            return
        
        # Check if it's drinkable
        if not water.tags.has("drink", category="item_type"):
            caller.msg(f"You can't drink {water.get_display_name(caller)}.")
            return
        
        # Check thirst level
        thirst_value, thirst_desc = caller.get_trait_status("thirst")
        if thirst_value >= 90:
            caller.msg("You're not thirsty right now.")
            return
        
        # Get thirst value
        thirst_restore = water.db.thirst_value or 20
        
        # Apply to thirst
        caller.modify_trait("thirst", thirst_restore)
        new_thirst, new_desc = caller.get_trait_status("thirst")
        
        # Message
        caller.msg(f"|gYou drink {water.get_display_name(caller)}.|n")
        caller.msg(f"|xYou feel {new_desc}. (Thirst +{thirst_restore})|n")
        
        caller.location.msg_contents(
            f"{caller.name} drinks {water.get_display_name(caller)}.",
            exclude=caller
        )
        
        # Consume the water
        water.delete()
    
    def drink_from_source(self, source):
        """Drink directly from a water source."""
        caller = self.caller
        
        # Check thirst
        thirst_value, thirst_desc = caller.get_trait_status("thirst")
        if thirst_value >= 90:
            caller.msg("You're not thirsty right now.")
            return
        
        # Direct drinking is less effective than purified water
        thirst_restore = 15
        
        # Risk of illness without purification
        if random.random() < 0.1:  # 10% chance
            caller.msg("|yThe water tastes a bit off...|n")
            # Future: Apply illness effect
        
        # Apply thirst restoration
        caller.modify_trait("thirst", thirst_restore)
        new_thirst, new_desc = caller.get_trait_status("thirst")
        
        caller.msg(f"|gYou drink from {source.get_display_name(caller)}.|n")
        caller.msg(f"|xYou feel {new_desc}. (Thirst +{thirst_restore})|n")
        
        caller.location.msg_contents(
            f"{caller.name} drinks from {source.get_display_name(caller)}.",
            exclude=caller
        )


class CmdStatus(Command):
    """
    Check your survival status and cooldowns.
    
    Usage:
        status
        status full
        
    This command shows your current survival traits (hunger,
    thirst, fatigue, health) as well as any active cooldowns.
    
    Use 'status full' to see all your stats and skills as well.
    """
    
    key = "status"
    aliases = ["stats", "condition"]
    locks = "cmd:all()"
    help_category = "Survival"
    
    def func(self):
        """Display character status."""
        caller = self.caller
        show_full = self.args.strip().lower() == "full"
        
        # Header
        caller.msg("|w===== Character Status =====|n")
        
        # Survival traits
        caller.msg("\n|wSurvival Needs:|n")
        caller.msg(caller.get_survival_summary())
        
        # Active cooldowns
        cooldowns = []
        for cd_name in ["gather", "forage", "rest", "craft", "trade"]:
            if not caller.cooldowns.ready(cd_name):
                time_left = caller.cooldowns.time_left(cd_name, use_int=True)
                cooldowns.append(f"{cd_name}: {time_left}s")
        
        if cooldowns:
            caller.msg("\n|wActive Cooldowns:|n")
            for cd in cooldowns:
                caller.msg(f"  |y{cd}|n")
        else:
            caller.msg("\n|wActive Cooldowns:|n None")
        
        # Environmental conditions
        if caller.location:
            caller.msg("\n|wEnvironmental Conditions:|n")
            
            # Temperature/warmth
            warmth = caller.get_total_warmth()
            season = caller.location.get_season()
            if season == "winter" and warmth < 20:
                caller.msg("  |rYou are cold! (Warmth: {warmth})|n")
            elif season == "summer" and warmth > 30:
                caller.msg("  |yYou are too warm. (Warmth: {warmth})|n")
            else:
                caller.msg(f"  |gTemperature is comfortable. (Warmth: {warmth})|n")
            
            # Weather protection
            weather = caller.location.get_current_weather()
            if "rain" in weather:
                if caller.has_weather_protection("rain"):
                    caller.msg("  |gYou are protected from the rain.|n")
                else:
                    caller.msg("  |yYou are getting wet from the rain.|n")
        
        # Full status includes stats and skills
        if show_full:
            # Stats
            caller.msg("\n|wAttributes:|n")
            for stat_name in ["strength", "dexterity", "constitution",
                            "intelligence", "wisdom", "charisma"]:
                value = caller.get_stat(stat_name)
                caller.msg(f"  {stat_name.title()}: {value}")
            
            # Skills
            caller.msg("\n|wSkills:|n")
            caller.msg(caller.get_skill_summary())
