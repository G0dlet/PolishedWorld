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
