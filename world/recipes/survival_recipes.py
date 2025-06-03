# world/recipes/survival_recipes.py
"""
Survival-focused recipes for basic needs.

These recipes create food, water containers, and basic tools
needed for survival in the game world.
"""

from world.recipes.base_recipes import SkillBasedRecipe, SkillAndStatRecipe
from evennia.contrib.game_systems.crafting.crafting import CraftingValidationError
from evennia.utils.utils import iter_to_str


class WaterContainerRecipe(SkillBasedRecipe):
    """Create a basic water container from leather."""
    
    name = "waterskin"
    skill_requirement = "crafting"
    difficulty = 10
    craft_time = 180  # 3 minutes
    craft_category = "craft_basic"
    
    tool_tags = ["knife"]
    consumable_tags = ["leather", "twine"]
    
    output_prototypes = [{
        "key": "waterskin",
        "typeclass": "typeclasses.objects.Container",
        "desc": "A leather waterskin for carrying water.",
        "tags": [
            ("waterskin", "item_type"),
            ("container", "item_type"),
            ("liquid_only", "container_type")
        ],
        "attrs": [
            ("capacity", 3),  # Can hold 3 water items
            ("liquid_only", True),
            ("empty_weight", 0.5),
            ("durability", 50),
            ("max_durability", 50)
        ]
    }]


class CampfireRecipe(SkillBasedRecipe):
    """Build a campfire for cooking and warmth."""
    
    name = "campfire"
    skill_requirement = "survival" 
    difficulty = 5
    craft_time = 120  # 2 minutes
    craft_category = "craft_basic"
    
    tool_tags = []  # No tools needed
    consumable_tags = ["wood", "wood", "wood"]  # Need 3 wood
    
    output_prototypes = [{
        "key": "campfire",
        "typeclass": "typeclasses.objects.Campfire",
        "desc": "A crackling campfire providing warmth and light.",
        "tags": [
            ("campfire", "item_type"),
            ("heat_source", "item_type"),
            ("light_source", "item_type")
        ],
        "attrs": [
            ("burn_time", 3600),  # Burns for 1 hour
            ("is_lit", True),
            ("warmth_radius", 1),  # Warms adjacent rooms
            ("cooking_bonus", 10),  # +10% to cooking skill when used
            ("portable", False)  # Can't be picked up while lit
        ]
    }]
    
    def do_craft(self, **kwargs):
        """Override to check if location allows fires."""
        location = self.crafter.location
        
        # Check if indoor location allows fires
        if location.db.indoor and not location.db.allow_fire:
            self.msg("|rYou cannot build a fire indoors here!|n")
            return []
        
        # Check weather
        weather = location.get_current_weather()
        if "storm" in weather or "heavy_rain" in weather:
            self.msg("|rThe weather is too harsh to build a fire.|n")
            return []
        
        return super().do_craft(**kwargs)


class BreadRecipe(SkillBasedRecipe):
    """Bake bread - a basic food staple."""
    
    name = "bread"
    skill_requirement = "crafting"
    difficulty = 15
    craft_time = 600  # 10 minutes  
    craft_category = "craft_basic"
    
    tool_tags = ["oven", "mixing_bowl"]
    consumable_tags = ["flour", "water", "yeast", "salt"]
    
    output_prototypes = [{
        "key": "loaf of bread",
        "typeclass": "typeclasses.objects.Food", 
        "desc": "A freshly baked loaf of bread with a golden crust.",
        "tags": [
            ("bread", "item_type"),
            ("food", "item_type")
        ],
        "attrs": [
            ("nutrition", 30),  # Base nutrition value
            ("weight", 0.5),
            ("decay_rate", 0.1),  # Decays slowly
            ("uses", 4)  # Can be eaten 4 times
        ]
    }]
    
    def calculate_quality(self):
        """Override to give better nutrition for higher quality."""
        quality_name, quality_modifier = super().calculate_quality()
        
        # Modify the nutrition value in output
        for proto in self.output_prototypes:
            for i, (attr_name, attr_val) in enumerate(proto.get("attrs", [])):
                if attr_name == "nutrition":
                    # Better quality = more nutritious
                    new_nutrition = int(attr_val * quality_modifier)
                    proto["attrs"][i] = ("nutrition", new_nutrition)
                    break
        
        return quality_name, quality_modifier


class PreservedMeatRecipe(SkillBasedRecipe):
    """Create preserved meat that lasts longer."""
    
    name = "preserved meat"
    skill_requirement = "survival"
    difficulty = 25
    craft_time = 900  # 15 minutes
    craft_category = "craft_basic"
    
    tool_tags = ["knife", "smoking_rack"]
    consumable_tags = ["raw_meat", "raw_meat", "salt", "herbs"]
    
    output_prototypes = [{
        "key": "preserved meat",
        "typeclass": "typeclasses.objects.Food",
        "desc": "Strips of meat preserved with salt and smoke.",
        "tags": [
            ("preserved_meat", "item_type"),
            ("food", "item_type")
        ],
        "attrs": [
            ("nutrition", 40),
            ("weight", 0.8),
            ("decay_rate", 0.02),  # Very slow decay
            ("uses", 2)
        ]
    }]


class HerbalTeaRecipe(SkillBasedRecipe):
    """Brew herbal tea for minor healing."""
    
    name = "herbal tea"
    skill_requirement = "survival"
    difficulty = 20
    craft_time = 300
    craft_category = "craft_basic"
    
    tool_tags = ["pot", "campfire"]
    consumable_tags = ["herbs", "herbs", "water"]
    
    output_prototypes = [{
        "key": "herbal tea",
        "typeclass": "typeclasses.objects.Consumable",
        "desc": "A steaming cup of medicinal herbal tea.",
        "tags": [
            ("tea", "item_type"),
            ("drink", "item_type"),
            ("medicine", "item_type")
        ],
        "attrs": [
            ("thirst_value", 15),
            ("healing_value", 10),  # Restores some health
            ("effect_type", "heal_minor"),
            ("uses", 1),
            ("weight", 0.3)
        ]
    }]


class StewRecipe(SkillAndStatRecipe):
    """A hearty stew - excellent nutrition but requires skill."""
    
    name = "hearty stew"
    skill_requirement = "crafting"
    difficulty = 35
    craft_time = 1200  # 20 minutes
    craft_category = "craft_basic"
    
    # Wisdom helps with seasoning
    stat_requirement = "wisdom"
    stat_weight = 0.2
    
    tool_tags = ["pot", "ladle", "campfire"]
    consumable_tags = ["meat", "vegetables", "vegetables", "herbs", "water", "salt"]
    
    output_prototypes = [{
        "key": "pot of hearty stew",
        "typeclass": "typeclasses.objects.Food",
        "desc": "A large pot of thick, savory stew with chunks of meat and vegetables.",
        "tags": [
            ("stew", "item_type"),
            ("food", "item_type")
        ],
        "attrs": [
            ("nutrition", 60),  # Very nutritious
            ("weight", 2.0),
            ("decay_rate", 0.15),  # Spoils moderately fast
            ("uses", 6),  # Feeds multiple people
            ("warmth_bonus", 5)  # Provides warmth when eaten
        ]
    }]
