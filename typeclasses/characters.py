"""
PolishedWorld Character typeclass

Implements Mongoose Legend characteristics with Evennia's Traits contrib.
Includes survival mechanics (hunger, thirst, fatigue) and skill system.
"""

from evennia import DefaultCharacter
from evennia.utils import lazy_property
from evennia.contrib.rpg.traits import TraitHandler

from .objects import ObjectParent


class Character(ObjectParent, DefaultCharacter):
    """
    PolishedWorld character with Mongoose Legend integration.

    Uses three separate TraitHandlers:
    - stats: Mongoose Legend characteristics (STR, DEX, CON, SIZ, INT, POW, CHA)
    - traits: Survival gauges (hunger, thirst, fatigue, health)
    - skills: Learnable skills using percentile system (0-100%)
    """

    @lazy_property
    def stats(self):
        """
        Handler for Mongoose Legend characteristics (Static traits).

        These are the core attributes that define a character's 
        physical and mental capabilities. Each is calculated as base + mod.
        
        - STR (Strength): Physical power
        - DEX (Dexterity): Agility and reflexes  
        - CON (Constitution): Health and stamina
        - SIZ (Size): Physical mass and reach
        - INT (Intelligence): Reasoning and memory
        - POW (Power): Willpower and magical potency
        - CHA (Charisma): Personality and leadership
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

        These depletable resources affect character survival and performance.
        All use the Gauge type which empties from max (base + mod).
        
        - hunger: Food need (0=starving, 100=full)
        - thirst: Water need (0=dehydrated, 100=hydrated)
        - fatigue: Rest need (0=exhausted, 100=well-rested)
        - health: Hit points (0=dead, max=CON-based)
        
        Supports .rate for automatic changes (e.g., gradual hunger increase).
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

        Mongoose Legend uses a percentile system where skills range 
        from 0-100%. Base represents starting skill, current tracks 
        progress, and mod can apply temporary bonuses/penalties.
        
        Skills will be added dynamically as characters learn them.
        Common skills might include:
        - Athletics, Stealth, Perception
        - Combat skills (Swords, Bows, Unarmed, etc.)
        - Craft skills (Smithing, Carpentry, Cooking, etc.)
        - Lore skills (Nature, History, Magic, etc.)
        """
        return TraitHandler(
            self, 
            db_attribute_key="skills",
            db_attribute_category="skills"
        )
    
    def at_object_creation(self):
        """
        Called once when character is first created.

        Initializes all Mongoose Legend characteristics with base values,
        sets up survival traits at full, and prepares skills system.
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
        # Gauges that deplete and can recover with rate
        # All start at maximum (100) for a fresh, healthy character
        
        self.traits.add(
            "hunger", "Hunger",
            trait_type="gauge",
            base=100,
            mod=0,
            min=0,
            # Rate will be set by game systems (e.g., -0.1 per second = slowly getting hungry)
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
            # Base health derived from CON (Mongoose Legend: HP based on CON)
            base=self.stats.con.value * 2,
            mod=0,
            min=0,
            rate=0,  # Natural healing rate can be set later
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

        # === SKILLS ===
        # Skills start empty and are added as character learns them
        # Using Counter type allows for base skill + improvements (current)
        # Example initialization of common starting skills:
        
        # Basic survival skills everyone starts with
        self.skills.add(
            "perception", "Perception",
            trait_type="counter",
            base=25,  # 25% base chance (INT + POW based in Mongoose Legend)
            current=25,
            mod=0,
            min=0,
            max=100,
            descs={
                0: "oblivious",
                20: "unaware",
                40: "attentive",
                60: "observant",
                80: "sharp",
                95: "eagle-eyed"
            }
        )
        
        self.skills.add(
            "stealth", "Stealth", 
            trait_type="counter",
            base=20,  # DEX + INT based
            current=20,
            mod=0,
            min=0,
            max=100,
            descs={
                0: "clumsy",
                20: "obvious",
                40: "careful",
                60: "sneaky",
                80: "stealthy",
                95: "invisible"
            }
        )
        
        self.skills.add(
            "athletics", "Athletics",
            trait_type="counter", 
            base=25,  # STR + DEX based
            current=25,
            mod=0,
            min=0,
            max=100,
            descs={
                0: "feeble",
                20: "weak",
                40: "capable",
                60: "athletic",
                80: "strong",
                95: "mighty"
            }
        )
      
    def update_health_max(self):
        """
        Helper method to recalculate max health when CON changes.
        Should be called whenever CON is modified.
        """
        new_max = self.stats.con.value * 2
        current_percent = self.traits.health.percent(formatting=None)
        
        self.traits.health.base = new_max
        self.traits.health.current = int(new_max * current_percent / 100)
