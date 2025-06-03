# world/recipes/clothing_recipes.py
"""
Clothing and armor crafting recipes.

These recipes create various clothing items that provide
protection from weather and combat.
"""

from world.recipes.base_recipes import SkillBasedRecipe, SkillAndStatRecipe


class LeatherArmorRecipe(SkillAndStatRecipe):
    """Craft leather armor for protection."""
    
    name = "leather armor"
    skill_requirement = "crafting"
    difficulty = 30
    craft_time = 1800  # 30 minutes
    craft_category = "craft_basic"
    
    # Strength helps with working thick leather
    stat_requirement = "strength"
    stat_weight = 0.3
    
    tool_tags = ["leather_tools", "workbench"]
    consumable_tags = ["leather", "leather", "leather", "leather_strips", "buckles"]
    
    output_prototypes = [{
        "key": "leather armor",
        "typeclass": "typeclasses.objects.LeatherArmor",
        "desc": "A sturdy set of leather armor with reinforced panels.",
        "tags": [
            ("armor", "item_type"),
            ("leather_armor", "item_type")
        ],
        "attrs": [
            ("clothing_type", "outerwear"),
            ("protection_value", 5),  # Base armor
            ("warmth_value", 10),
            ("weather_protection", ["wind"]),
            ("durability", 100),
            ("max_durability", 100),
            ("repair_materials", ["leather"]),
            ("weight", 5)
        ]
    }]


class WinterCloakRecipe(SkillBasedRecipe):
    """Craft a warm winter cloak."""
    
    name = "winter cloak"
    skill_requirement = "crafting"
    difficulty = 25
    craft_time = 1200  # 20 minutes
    craft_category = "craft_basic"
    
    tool_tags = ["sewing_kit", "scissors"]
    consumable_tags = ["wool_cloth", "wool_cloth", "fur_lining", "thread", "clasp"]
    
    output_prototypes = [{
        "key": "winter cloak",
        "typeclass": "typeclasses.objects.WinterCloak",
        "desc": "A heavy woolen cloak lined with warm fur.",
        "tags": [
            ("cloak", "item_type"),
            ("winter_gear", "item_type")
        ],
        "attrs": [
            ("clothing_type", "cloak"),
            ("warmth_value", 25),
            ("weather_protection", ["snow", "wind", "rain"]),
            ("stat_modifiers", {"constitution": 1}),
            ("durability", 80),
            ("max_durability", 80),
            ("repair_materials", ["wool_cloth", "fur"]),
            ("weight", 3)
        ]
    }]


class EngineerGogglesRecipe(SkillBasedRecipe):
    """Craft specialized engineering goggles."""
    
    name = "engineer goggles"
    skill_requirement = "engineering"  # Requires engineering to make properly
    difficulty = 40
    craft_time = 1500  # 25 minutes
    craft_category = "craft_basic"
    
    tool_tags = ["precision_tools", "lens_grinder"]
    consumable_tags = ["brass_frame", "glass_lens", "glass_lens", "leather_strap", "tiny_gears"]
    
    output_prototypes = [{
        "key": "engineering goggles",
        "typeclass": "typeclasses.objects.EngineeringGoggles",
        "desc": "Brass-framed goggles with multiple adjustable lenses.",
        "tags": [
            ("goggles", "item_type"),
            ("engineering_gear", "item_type")
        ],
        "attrs": [
            ("clothing_type", "goggles"),
            ("stat_modifiers", {"intelligence": 2}),
            ("engineering_bonus", 10),
            ("magnification", 3),
            ("durability", 60),
            ("max_durability", 60),
            ("repair_materials", ["brass", "glass"]),
            ("weight", 0.5)
        ]
    }]


class RaincoatRecipe(SkillBasedRecipe):
    """Craft a waterproof raincoat."""
    
    name = "raincoat"
    skill_requirement = "crafting"
    difficulty = 20
    craft_time = 900  # 15 minutes
    craft_category = "craft_basic"
    
    tool_tags = ["sewing_kit", "waterproofing_kit"]
    consumable_tags = ["canvas_cloth", "canvas_cloth", "oil_treatment", "buttons"]
    
    output_prototypes = [{
        "key": "waterproof raincoat",
        "typeclass": "typeclasses.objects.RainCoat",
        "desc": "A long coat treated with oils to repel water.",
        "tags": [
            ("raincoat", "item_type"),
            ("weather_gear", "item_type")
        ],
        "attrs": [
            ("clothing_type", "outerwear"),
            ("warmth_value", 10),
            ("weather_protection", ["rain", "wind"]),
            ("durability", 70),
            ("max_durability", 70),
            ("repair_materials", ["canvas_cloth", "oil"]),
            ("weight", 2)
        ]
    }]
