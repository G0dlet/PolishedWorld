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
        
        # === MONGOOSE LEGEND CHARACTERISTICS ===
        
        self.stats.add(
            "str", "Strength",
            trait_type="static",
            base=10,
            mod=0
        )
        
        self.stats.add(
            "dex", "Dexterity", 
            trait_type="static",
            base=10,
            mod=0
        )
        
        self.stats.add(
            "con", "Constitution",
            trait_type="static", 
            base=10,
            mod=0
        )
        
        self.stats.add(
            "siz", "Size",
            trait_type="static",
            base=10,
            mod=0
        )
        
        self.stats.add(
            "int", "Intelligence",
            trait_type="static",
            base=10, 
            mod=0
        )
        
        self.stats.add(
            "pow", "Power",
            trait_type="static",
            base=10,
            mod=0
        )
        
        self.stats.add(
            "cha", "Charisma",
            trait_type="static",
            base=10,
            mod=0
        )

        # === SURVIVAL TRAITS ===
        
        self.traits.add(
            "hunger", "Hunger",
            trait_type="gauge",
            base=100,
            mod=0,
            min=0,
            rate=0,
            descs={
                0: "starving",
                20: "famished", 
                40: "hungry",
                60: "peckish",
                80: "satisfied",
                95: "full"
            }
        )
        
        self.traits.add(
            "thirst", "Thirst",
            trait_type="gauge", 
            base=100,
            mod=0,
            min=0,
            rate=0,
            descs={
                0: "dying of thirst",
                20: "parched",
                40: "thirsty", 
                60: "could drink",
                80: "hydrated",
                95: "quenched"
            }
        )
        
        self.traits.add(
            "fatigue", "Fatigue",
            trait_type="gauge",
            base=100, 
            mod=0,
            min=0,
            rate=0,
            descs={
                0: "exhausted",
                20: "drained",
                40: "tired",
                60: "weary", 
                80: "rested",
                95: "energetic"
            }
        )
        
        self.traits.add(
            "health", "Health",
            trait_type="gauge",
            base=self.stats.con.value * 2,
            mod=0,
            min=0,
            rate=0,
            descs={
                0: "dead",
                10: "near death",
                25: "critically wounded",
                50: "badly hurt",
                75: "injured",
                90: "bruised",
                100: "healthy"
            }
        )
