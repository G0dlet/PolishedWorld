# typeclasses/objects.py
"""
Object

The Object is the class for general items in the game world.

This implementation adds visibility properties to all objects,
making them interact with the Extended Room's visibility system.
"""

from evennia.objects.objects import DefaultObject
from evennia.utils import list_to_string
import random


class ObjectParent:
    """
    This is a mixin that can be used to override *all* entities inheriting at
    some distance from DefaultObject (Objects, Exits, Characters and Rooms).

    Just add any method that exists on `DefaultObject` to this class. If one
    of the derived classes has itself defined that same hook already, that will
    take precedence.
    """
    
    def at_object_creation(self):
        """
        Called once when object is first created.
        Sets default visibility properties.
        """
        super().at_object_creation()
        
        # Set default visibility properties
        self.db.visibility_size = "normal"  # tiny, small, normal, large, huge, obvious
        self.db.luminosity = "normal"       # dull, normal, shiny, glowing
        self.db.contrast = "normal"         # dark, normal, bright, camouflaged
        self.db.hidden = False              # Requires active search to find
        self.db.is_light_source = False     # Can provide light
        self.db.light_active = False        # Is currently providing light


class Object(ObjectParent, DefaultObject):
    """
    This is the root Object typeclass, representing all entities that
    have an actual presence in-game.
    
    Objects in this game have visibility properties that affect how
    easily they can be seen in different conditions.
    """
    
    def get_display_name(self, looker=None, **kwargs):
        """
        Get the display name, possibly modified by visibility.
        
        Hard-to-see objects might have their names obscured.
        """
        name = super().get_display_name(looker, **kwargs)
        
        if looker and self.location:
            # Endast beräkna visibility om objektet är i ett rum
            # (inte i någons inventory)
            if hasattr(self.location, 'calculate_object_visibility'):
                visibility = self.location.calculate_object_visibility(self, looker)
            
                # Very hard to see objects might be described vaguely
                if visibility < 0.3:
                    # Describe by size category instead of name
                    size_descriptions = {
                        "tiny": "something tiny",
                        "small": "a small object", 
                        "normal": "an object",
                        "large": "a large shape",
                        "huge": "a huge form"
                    }
                    vague_name = size_descriptions.get(self.db.visibility_size, "something")
                
                    # Add hints based on luminosity
                    if self.db.luminosity == "shiny":
                        vague_name = f"{vague_name} (glinting)"
                    elif self.db.luminosity == "glowing":
                        vague_name = f"{vague_name} (glowing)"
                
                    return f"|x{vague_name}|n"
            
                # Moderately visible objects show normal name but dim
                elif visibility < 0.6:
                    return f"|x{name}|n"
        
        return name
    
    def set_visibility_properties(self, size=None, luminosity=None, 
                                 contrast=None, hidden=None):
        """
        Convenience method to set multiple visibility properties at once.
        
        Args:
            size (str): Object size category
            luminosity (str): How much light it reflects/emits
            contrast (str): How it stands out from environment
            hidden (bool): Whether it requires searching to find
        """
        if size is not None:
            self.db.visibility_size = size
        if luminosity is not None:
            self.db.luminosity = luminosity
        if contrast is not None:
            self.db.contrast = contrast
        if hidden is not None:
            self.db.hidden = hidden
    
    def make_light_source(self, active=False):
        """
        Turn this object into a light source.
        
        Args:
            active (bool): Whether the light is initially on
        """
        self.db.is_light_source = True
        self.db.light_active = active
        self.db.luminosity = "glowing" if active else "normal"
    
    def toggle_light(self):
        """
        Toggle a light source on/off.
        
        Returns:
            bool: New state of the light
        """
        if not self.db.is_light_source:
            return False
        
        self.db.light_active = not self.db.light_active
        self.db.luminosity = "glowing" if self.db.light_active else "normal"
        
        return self.db.light_active
    
    def return_appearance(self, looker, **kwargs):
        """
        Base appearance method for all objects.
        """
        # Get the basic appearance
        text = super().return_appearance(looker, **kwargs)
        
        # Add visibility information if appropriate
        if self.db.is_light_source:
            if self.db.light_active:
                text += "\n\n|yIt is providing light.|n"
            else:
                text += "\n\nIt could provide light if lit."
                
        return text


# Example object classes with preset visibility

class SmallValuable(Object):
    """
    Base class for small valuable items like coins, gems, rings.
    These are harder to spot, especially in poor conditions.
    """
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.visibility_size = "tiny"
        self.db.luminosity = "shiny"
        self.db.contrast = "normal"


class Torch(Object):
    """
    A basic torch that can be lit to provide light.
    """
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "A torch made of cloth wrapped around a wooden stick."
        self.db.visibility_size = "normal"
        self.make_light_source(active=False)
        self.db.burn_time = 3600  # 1 hour real time = 4 hours game time
        
    def do_light(self, lighter):
        """
        Light the torch.
        
        Args:
            lighter (Character): Who is lighting it
            
        Returns:
            bool: Success
        """
        if self.db.light_active:
            lighter.msg("The torch is already lit.")
            return False
        
        self.db.light_active = True
        self.db.luminosity = "glowing"
        self.db.desc = "A burning torch casting flickering shadows."
        
        lighter.msg("You light the torch.")
        lighter.location.msg_contents(
            f"{lighter.name} lights a torch.",
            exclude=lighter
        )
        
        # TODO: Add TickerHandler to consume burn_time
        return True
    
    def do_extinguish(self, extinguisher):
        """
        Put out the torch.
        
        Args:
            extinguisher (Character): Who is putting it out
            
        Returns:
            bool: Success
        """
        if not self.db.light_active:
            extinguisher.msg("The torch is not lit.")
            return False
        
        self.db.light_active = False
        self.db.luminosity = "normal"
        self.db.desc = "A torch made of cloth wrapped around a wooden stick."
        
        extinguisher.msg("You extinguish the torch.")
        extinguisher.location.msg_contents(
            f"{extinguisher.name} extinguishes a torch.",
            exclude=extinguisher
        )
        
        return True


class HiddenCache(Object):
    """
    A hidden container that requires searching to find.
    """
    
    def at_object_creation(self):
        super().at_object_creation()
        self.db.desc = "A carefully concealed cache."
        self.db.visibility_size = "small"
        self.db.contrast = "camouflaged"
        self.db.camouflage_type = "natural"
        self.db.hidden = True  # Requires search command


# typeclasses/objects.py (uppdaterad clothing section)
"""
Clothing objects for the survival game.

These clothing items provide various benefits including
weather protection, warmth, and stat bonuses. They also
inherit all standard object properties like visibility.
"""

from evennia.contrib.game_systems.clothing.clothing import ContribClothing


class SurvivalClothing(Object, ContribClothing):
    """
    Base class for survival clothing with environmental protection.
    
    This inherits from both Object (for visibility and other game properties)
    and ContribClothing (for the wearing/removing functionality).
    
    Attributes to set on clothing:
        warmth_value (int): How much warmth this provides (0-30)
        weather_protection (list): Types of weather protected against
        stat_modifiers (dict): Stat bonuses when worn
        protection_value (int): General damage protection
        durability (int): How long before it wears out
        repair_materials (list): What's needed to repair
    """
    
    def at_object_creation(self):
        """Set default values for survival clothing."""
        # Call both parent initializers
        Object.at_object_creation(self)
        ContribClothing.at_object_creation(self)
        
        # Survival-specific attributes
        self.db.warmth_value = 0
        self.db.weather_protection = []
        self.db.stat_modifiers = {}
        self.db.protection_value = 0
        self.db.durability = 100
        self.db.max_durability = 100
        self.db.repair_materials = ["cloth"]
        
        # Most clothing has normal visibility when dropped
        self.db.visibility_size = "normal"
        self.db.luminosity = "normal"
        self.db.contrast = "normal"
    
    def wear(self, wearer, wearstyle, quiet=False):
        """
        Override to apply stat modifiers when worn.
        """
        super().wear(wearer, wearstyle, quiet)
        
        # Apply stat modifiers
        if hasattr(wearer, 'apply_clothing_modifiers'):
            wearer.apply_clothing_modifiers()
            
        # Check for set bonuses
        self.check_set_bonuses(wearer)
    
    def remove(self, wearer, quiet=False):
        """
        Override to remove stat modifiers when removed.
        """
        super().remove(wearer, quiet)
        
        # Reapply modifiers (some are now gone)
        if hasattr(wearer, 'apply_clothing_modifiers'):
            wearer.apply_clothing_modifiers()
    
    def at_drop(self, dropper):
        """
        Called when the clothing is dropped.
        Ensures it's removed if worn.
        """
        if self.db.worn:
            self.remove(dropper, quiet=True)
        
        # Call parent drop behavior
        super().at_drop(dropper)
    
    def check_set_bonuses(self, wearer):
        """
        Check if wearing a complete set provides bonuses.
        
        Args:
            wearer: The character wearing this item
        """
        # This can be overridden in specific clothing types
        pass
    
    def get_condition_string(self):
        """
        Get a description of the item's condition.
        
        Returns:
            str: Description of condition
        """
        if not hasattr(self.db, 'durability'):
            return ""
            
        percent = (self.db.durability / self.db.max_durability) * 100
        
        if percent >= 90:
            return "|gpristine condition|n"
        elif percent >= 70:
            return "|ygood condition|n"
        elif percent >= 50:
            return "|yworn but serviceable|n"
        elif percent >= 30:
            return "|rwell-worn and fraying|n"
        elif percent >= 10:
            return "|rbadly damaged|n"
        else:
            return "|rfalling apart|n"
    
    def return_appearance(self, looker, **kwargs):
        """
        Add condition and benefits to clothing appearance.
        """
        # Get base appearance from Object parent
        text = Object.return_appearance(self, looker, **kwargs)
        
        # Add condition if visible
        condition = self.get_condition_string()
        if condition:
            text += f"\n\nIt is in {condition}."
            
        # Add protection info
        benefits = []
        if self.db.warmth_value and self.db.warmth_value > 0:
            benefits.append(f"provides warmth ({self.db.warmth_value})")
        
        if self.db.weather_protection:
            benefits.append(f"protects against: {', '.join(self.db.weather_protection)}")
        
        if self.db.stat_modifiers:
            mod_strings = []
            for stat, mod in self.db.stat_modifiers.items():
                sign = "+" if mod > 0 else ""
                mod_strings.append(f"{stat} {sign}{mod}")
            benefits.append(f"when worn: {', '.join(mod_strings)}")
        
        if benefits:
            text += f"\n\nThis clothing {'; '.join(benefits)}."
            
        return text


# Specific clothing types

class WinterCloak(SurvivalClothing):
    """
    A heavy winter cloak providing excellent cold protection.
    """
    
    def at_object_creation(self):
        super().at_object_creation()
        
        self.key = "heavy winter cloak"
        self.aliases.add = ["cloak", "winter cloak"]
        self.db.desc = "A thick, fur-lined cloak designed for harsh winter conditions."
        
        # Clothing properties
        self.db.clothing_type = "cloak"
        self.db.warmth_value = 25
        self.db.weather_protection = ["snow", "wind", "rain"]
        self.db.stat_modifiers = {"constitution": 1}  # +1 CON from warmth
        self.db.protection_value = 2
        
        # Visible when dropped due to size
        self.db.visibility_size = "large"
        
        # Crafting prep
        self.db.repair_materials = ["fur", "leather", "cloth"]


class LeatherBoots(SurvivalClothing):
    """
    Sturdy leather boots for traveling.
    """
    
    def at_object_creation(self):
        super().at_object_creation()
        
        self.key = "sturdy leather boots"
        self.aliases.add = ["boots", "leather boots"]
        self.db.desc = "Well-crafted leather boots with thick soles."
        
        self.db.clothing_type = "shoes"
        self.db.warmth_value = 5
        self.db.weather_protection = ["rain"]
        self.db.stat_modifiers = {"dexterity": 1}  # +1 DEX from good footing
        self.db.protection_value = 1
        
        self.db.repair_materials = ["leather"]


class WorkGloves(SurvivalClothing):
    """
    Protective gloves for crafting and gathering.
    """
    
    def at_object_creation(self):
        super().at_object_creation()
        
        self.key = "work gloves"
        self.aliases.add = ["gloves"]
        self.db.desc = "Thick leather gloves reinforced for heavy work."
        
        self.db.clothing_type = "gloves"
        self.db.warmth_value = 3
        self.db.stat_modifiers = {"strength": 1}  # +1 STR for grip
        self.db.protection_value = 1
        
        # Special crafting bonus
        self.db.crafting_bonus = 5  # +5% success rate
        self.db.repair_materials = ["leather", "cloth"]


class RainCoat(SurvivalClothing):
    """
    Waterproof coat for wet weather.
    """
    
    def at_object_creation(self):
        super().at_object_creation()
        
        self.key = "waterproof raincoat"
        self.aliases.add = ["raincoat", "coat"]
        self.db.desc = "A long coat treated with oils to repel water."
        
        self.db.clothing_type = "outerwear"
        self.db.warmth_value = 10
        self.db.weather_protection = ["rain", "wind"]
        self.db.protection_value = 1
        
        # Slightly shiny from waterproofing
        self.db.luminosity = "shiny"
        
        self.db.repair_materials = ["cloth", "oil"]


class WoolenHat(SurvivalClothing):
    """
    Simple warm hat.
    """
    
    def at_object_creation(self):
        super().at_object_creation()
        
        self.key = "woolen hat"
        self.aliases.add = ["hat"]
        self.db.desc = "A simple but warm woolen hat."
        
        self.db.clothing_type = "hat"
        self.db.warmth_value = 8
        self.db.weather_protection = ["wind"]
        
        # Small and easy to miss if dropped
        self.db.visibility_size = "small"
        
        self.db.repair_materials = ["cloth"]


class EngineeringGoggles(SurvivalClothing):
    """
    Specialized goggles for engineering work.
    """
    
    def at_object_creation(self):
        super().at_object_creation()
        
        self.key = "engineering goggles"
        self.aliases.add = ["goggles"]
        self.db.desc = "Brass-framed goggles with adjustable lenses."
        
        self.db.clothing_type = "goggles"
        self.db.stat_modifiers = {"intelligence": 2}  # +2 INT for precision
        self.db.protection_value = 1
        
        # Shiny brass catches light
        self.db.luminosity = "shiny"
        self.db.visibility_size = "small"
        
        # Special engineering bonus
        self.db.engineering_bonus = 10  # +10% success rate
        self.db.repair_materials = ["brass", "glass", "leather"]


class DecorativeScarf(SurvivalClothing):
    """
    A beautiful scarf that can be worn in various styles.
    """
    
    def at_object_creation(self):
        super().at_object_creation()
        
        self.key = "decorative silk scarf"
        self.aliases.add = ["scarf", "silk scarf"]
        self.db.desc = "A beautifully patterned silk scarf with vibrant colors."
        
        self.db.clothing_type = "accessory"
        self.db.warmth_value = 2
        self.db.stat_modifiers = {"charisma": 1}  # +1 CHA for style
        
        # Bright and noticeable
        self.db.contrast = "bright"
        self.db.luminosity = "shiny"
        
        self.db.repair_materials = ["silk", "thread"]


# Special hidden/camouflaged clothing

class CamouflageCloak(SurvivalClothing):
    """
    A cloak designed to blend into natural environments.
    """
    
    def at_object_creation(self):
        super().at_object_creation()
        
        self.key = "camouflage cloak"
        self.aliases.add = ["cloak", "camo cloak"]
        self.db.desc = "A cloak dyed in mottled greens and browns to blend with foliage."
        
        self.db.clothing_type = "cloak"
        self.db.warmth_value = 15
        self.db.weather_protection = ["rain", "wind"]
        self.db.protection_value = 1
        
        # Hard to see when dropped in nature
        self.db.contrast = "camouflaged"
        self.db.camouflage_type = "natural"
        
        # Gives stealth bonus when worn
        self.db.stealth_bonus = 20  # +20% harder to detect
        
        self.db.repair_materials = ["cloth", "dye"]
