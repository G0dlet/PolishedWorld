# commands/clothing_commands.py
"""
Enhanced clothing commands for the survival game.

These extend the basic clothing commands to show
protection values and condition.
"""

from evennia.contrib.game_systems.clothing.clothing import CmdWear as BaseCmdWear
from evennia.contrib.game_systems.clothing.clothing import CmdRemove as BaseCmdRemove
from evennia.contrib.game_systems.clothing.clothing import CmdInventory as BaseCmdInventory
from evennia import Command
from evennia.utils import evtable


class CmdWear(BaseCmdWear):
    """
    Puts on an item of clothing you are holding.

    Usage:
      wear <obj> [=] [wear style]

    Examples:
      wear red shirt
      wear scarf wrapped loosely about the shoulders
      wear blue hat = at a jaunty angle

    Wearing clothing provides various benefits:
    - Protection from weather conditions
    - Warmth in cold environments
    - Stat bonuses
    - Special crafting or skill bonuses

    The benefits are shown when you look at the item.
    """
    
    def func(self):
        """Execute the wear command with benefit notifications."""
        # First do the normal wear operation
        super().func()
        
        # If wear was successful, show benefits
        if self.rhs or not hasattr(self, 'clothing'):
            # Get the clothing item we just wore
            if hasattr(self, 'lhs'):
                clothing = self.caller.search(
                    self.lhs, 
                    candidates=self.caller.contents,
                    quiet=True
                )
                if clothing and clothing.db.worn:
                    # Show what benefits this provides
                    self.show_clothing_benefits(clothing)
    
    def show_clothing_benefits(self, clothing):
        """Display the benefits of wearing this clothing."""
        benefits = []
        
        if clothing.db.warmth_value and clothing.db.warmth_value > 0:
            benefits.append(f"|wWarmth:|n +{clothing.db.warmth_value}")
            
        if clothing.db.weather_protection:
            protections = ", ".join(clothing.db.weather_protection)
            benefits.append(f"|wWeather Protection:|n {protections}")
            
        if clothing.db.stat_modifiers:
            for stat, mod in clothing.db.stat_modifiers.items():
                sign = "+" if mod > 0 else ""
                benefits.append(f"|w{stat.title()}:|n {sign}{mod}")
                
        if hasattr(clothing.db, 'crafting_bonus') and clothing.db.crafting_bonus:
            benefits.append(f"|wCrafting:|n +{clothing.db.crafting_bonus}%")
            
        if hasattr(clothing.db, 'engineering_bonus') and clothing.db.engineering_bonus:
            benefits.append(f"|wEngineering:|n +{clothing.db.engineering_bonus}%")
            
        if benefits:
            self.caller.msg(f"\n|yBenefits:|n {', '.join(benefits)}")


class CmdClothingStatus(Command):
    """
    Check your clothing and environmental protection.
    
    Usage:
        clothing status
        clothes
        
    Shows what you're wearing, your total protection values,
    and what weather conditions you're protected against.
    """
    
    key = "clothing status"
    aliases = ["clothes", "clothing"]
    locks = "cmd:all()"
    help_category = "Survival"
    
    def func(self):
        """Display comprehensive clothing status."""
        caller = self.caller
        
        # Get worn items
        worn_items = caller.get_worn_clothes(exclude_covered=True)
        
        if not worn_items:
            caller.msg("You are not wearing any clothing.")
            return
        
        # Create output table
        table = evtable.EvTable(
            "|wItem|n",
            "|wType|n", 
            "|wCondition|n",
            "|wBenefits|n",
            border="header"
        )
        
        # Track totals
        total_warmth = 0
        total_protection = 0
        weather_protections = set()
        stat_totals = {}
        
        # Add each worn item
        for item in worn_items:
            # Get condition
            if hasattr(item, 'get_condition_string'):
                condition = item.get_condition_string()
            else:
                condition = "|gunknown|n"
                
            # Build benefits string
            benefits = []
            
            warmth = item.db.warmth_value or 0
            if warmth > 0:
                benefits.append(f"warmth:{warmth}")
                total_warmth += warmth
                
            protection = item.db.protection_value or 0
            if protection > 0:
                benefits.append(f"armor:{protection}")
                total_protection += protection
                
            if item.db.weather_protection:
                weather_protections.update(item.db.weather_protection)
                
            if item.db.stat_modifiers:
                for stat, mod in item.db.stat_modifiers.items():
                    if stat in stat_totals:
                        stat_totals[stat] += mod
                    else:
                        stat_totals[stat] = mod
            
            benefit_str = ", ".join(benefits) if benefits else "none"
            
            table.add_row(
                item.get_display_name(caller),
                item.db.clothing_type or "untyped",
                condition,
                benefit_str
            )
        
        # Display table
        caller.msg("|wWorn Clothing:|n")
        caller.msg(str(table))
        
        # Display totals
        caller.msg("\n|wTotal Protection:|n")
        
        # Warmth level
        warmth_desc = self.get_warmth_description(total_warmth)
        caller.msg(f"  |wWarmth:|n {total_warmth} ({warmth_desc})")
        
        # Armor
        if total_protection > 0:
            caller.msg(f"  |wArmor:|n {total_protection}")
            
        # Weather
        if weather_protections:
            caller.msg(f"  |wWeather Protection:|n {', '.join(sorted(weather_protections))}")
        else:
            caller.msg("  |wWeather Protection:|n none")
            
        # Stats
        if stat_totals:
            stat_strings = []
            for stat, total in sorted(stat_totals.items()):
                sign = "+" if total > 0 else ""
                stat_strings.append(f"{stat}: {sign}{total}")
            caller.msg(f"  |wStat Modifiers:|n {', '.join(stat_strings)}")
            
        # Environmental assessment
        self.show_environmental_readiness(caller, total_warmth, weather_protections)
    
    def get_warmth_description(self, warmth):
        """Get descriptive text for warmth level."""
        if warmth >= 60:
            return "|rsweltering|n"
        elif warmth >= 40:
            return "|yvery warm|n"
        elif warmth >= 25:
            return "|gwarm|n"
        elif warmth >= 15:
            return "|gcomfortable|n"
        elif warmth >= 8:
            return "|ycool|n"
        elif warmth >= 3:
            return "|ychilly|n"
        else:
            return "|bcold|n"
    
    def show_environmental_readiness(self, caller, warmth, weather_protections):
        """Show how ready the character is for current conditions."""
        if not caller.location:
            return
            
        # Get current conditions
        season = caller.location.get_season()
        weather = caller.location.get_current_weather()
        time_of_day = caller.location.get_time_of_day()
        
        caller.msg(f"\n|wEnvironmental Readiness:|n")
        caller.msg(f"  Current: {season} {time_of_day}, weather: {', '.join(weather)}")
        
        warnings = []
        
        # Check warmth for season
        if season == "winter":
            if warmth < 20:
                warnings.append("|rYou need more warm clothing for winter!|n")
            elif warmth < 30:
                warnings.append("|yYou could use more warmth for winter.|n")
        elif season == "summer" and warmth > 30:
            warnings.append("|yYou're overdressed for summer heat.|n")
            
        # Check weather protection
        for condition in weather:
            if condition in ["rain", "storm"] and "rain" not in weather_protections:
                warnings.append("|yYou lack rain protection.|n")
            elif condition == "snow" and "snow" not in weather_protections:
                warnings.append("|yYou lack snow protection.|n")
                
        if warnings:
            for warning in warnings:
                caller.msg(f"  {warning}")
        else:
            caller.msg("  |gYou are well-equipped for current conditions.|n")


class CmdRepair(Command):
    """
    Repair damaged clothing using materials.
    
    Usage:
        repair <clothing>
        
    Repairing clothing requires the appropriate materials
    and crafting skill. The materials needed depend on
    the type of clothing.
    """
    
    key = "repair"
    aliases = ["mend", "fix"]
    locks = "cmd:all()"
    help_category = "Crafting"
    
    def func(self):
        """Execute repair command."""
        if not self.args:
            self.caller.msg("Usage: repair <clothing item>")
            return
            
        # Find the item
        clothing = self.caller.search(self.args, candidates=self.caller.contents)
        if not clothing:
            return
            
        # Check if it's clothing
        if not hasattr(clothing, 'db') or not hasattr(clothing.db, 'durability'):
            self.caller.msg(f"{clothing.get_display_name(self.caller)} cannot be repaired.")
            return
            
        # Check condition
        if clothing.db.durability >= clothing.db.max_durability:
            self.caller.msg(f"{clothing.get_display_name(self.caller)} doesn't need repairs.")
            return
            
        # Check materials
        required_materials = clothing.db.repair_materials or ["cloth"]
        available_materials = []
        
        for mat_type in required_materials:
            # Look for material in inventory
            material = self.caller.search(
                mat_type, 
                candidates=self.caller.contents,
                quiet=True
            )
            if material:
                available_materials.append(material)
            else:
                self.caller.msg(f"You need {mat_type} to repair this.")
                return
                
        # Check skill
        skill_level = self.caller.get_skill_level("crafting")[0] or 0
        repair_difficulty = 30  # Base difficulty
        
        # Adjust difficulty based on damage
        damage_percent = 100 - ((clothing.db.durability / clothing.db.max_durability) * 100)
        if damage_percent > 70:
            repair_difficulty += 20
        elif damage_percent > 50:
            repair_difficulty += 10
            
        if skill_level < repair_difficulty:
            self.caller.msg(
                f"You need at least {repair_difficulty} crafting skill to repair this "
                f"(you have {skill_level})."
            )
            return
            
        # Perform repair
        # TODO: This will consume materials when crafting system is implemented
        repair_amount = min(20 + (skill_level // 10), clothing.db.max_durability - clothing.db.durability)
        clothing.db.durability += repair_amount
        
        self.caller.msg(
            f"You repair {clothing.get_display_name(self.caller)}. "
            f"It is now at {clothing.db.durability}/{clothing.db.max_durability} durability."
        )
        
        # Improve skill slightly
        if skill_level < 100:
            self.caller.improve_skill("crafting", 1)
