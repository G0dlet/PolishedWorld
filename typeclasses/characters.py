"""
PolishedWorld Character typeclass

Implements Mongoose Legend characteristics with Evennia's Traits contrib.
"""

from evennia import DefaultCharacter
from evennia.utils import lazy_property
from evennia.contrib.rpg.traits import TraitHandler

from .objects import ObjectParent


class Character(ObjectParent, DefaultCharacter):
    """
    PolishedWorld character with Mongoose Legend integration.
    """

    @lazy_property
    def stats(self):
        """
        Handler for Mongoose Legend characteristics (Static traits).
        """
        return TraitHandler(
            self, 
            db_attribute_key="stats",
            db_attribute_category="stats"
        )
    
    @lazy_property
    def traits(self):
        """
        Handler for survival traits (Gauge traits with rate support).
        """
        return TraitHandler(
            self, 
            db_attribute_key="traits",
            db_attribute_category="traits"
        )
    
    @lazy_property
    def skills(self):
        """
        Handler for learnable skills (Counter traits).
        """
        return TraitHandler(
            self, 
            db_attribute_key="skills",
            db_attribute_category="skills"
        )
    
    def at_object_creation(self):
        """
        Called once when character is first created.
        """
        super().at_object_creation()
        
        # We'll add traits here in the next commits
