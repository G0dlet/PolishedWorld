# world/recipes/tool_recipes.py
"""
Tool and equipment crafting recipes.

These recipes create the tools needed for other crafting,
as well as gathering and survival equipment.
"""

from world.recipes.base_recipes import SkillBasedRecipe, SkillAndStatRecipe


class PickaxeRecipe(SkillAndStatRecipe):
    """Craft a pickaxe for mining stone."""
    
    name = "pickaxe"
    skill_requirement = "crafting"
    difficulty = 20
    craft_time = 600  # 10 minutes
    craft_category = "craft_basic"
    
    # Strength helps forge better tools
    stat_requirement = "strength"
    stat_weight = 0.4
    
    tool_tags = ["forge", "anvil", "hammer"]
    consumable_tags = ["iron_ingot", "iron_ingot", "wooden_handle"]
    
    output_prototypes = [{
        "key": "pickaxe",
        "typeclass": "typeclasses.objects.Tool",
        "desc": "A sturdy pickaxe with an iron head and wooden handle.",
        "tags": [
            ("pickaxe", "item_type"),
            ("tool", "item_type"),
            ("pickaxe", "crafting_tool")  # Can be used as tool in recipes
        ],
        "attrs": [
            ("tool_type", "mining"),
            ("efficiency", 1.0),  # Modified by quality
            ("durability", 100),
            ("max_durability", 100),
            ("repair_materials", ["iron_ingot"]),
            ("weight", 4),
            ("quality", 50)  # Base quality
        ]
    }]
    
    def calculate_quality(self):
        """Tools get bonus durability from quality."""
        quality_name, quality_modifier = super().calculate_quality()
        
        # Apply quality to tool stats
        for proto in self.output_prototypes:
            attrs = proto.get("attrs", [])
            for i, (attr_name, attr_val) in enumerate(attrs):
                if attr_name == "efficiency":
                    attrs[i] = ("efficiency", attr_val * quality_modifier)
                elif attr_name == "max_durability":
                    attrs[i] = ("max_durability", int(attr_val * quality_modifier))
                elif attr_name == "durability":
                    # Current durability matches max
                    max_dur = int(100 * quality_modifier)
                    attrs[i] = ("durability", max_dur)
                elif attr_name == "quality":
                    attrs[i] = ("quality", int(50 * quality_modifier))
        
        return quality_name, quality_modifier


class PrecisionToolsRecipe(SkillBasedRecipe):
    """Craft precision tools for engineering work."""
    
    name = "precision tools"
    skill_requirement = "engineering"
    difficulty = 45
    craft_time = 2400  # 40 minutes
    craft_category = "craft_advanced"
    
    tool_tags = ["forge", "grindstone", "workbench"]
    consumable_tags = ["steel_ingot", "steel_ingot", "brass_fitting", "leather_wrap", "tool_case"]
    
    output_prototypes = [{
        "key": "precision tools",
        "typeclass": "typeclasses.objects.ToolKit",
        "desc": "A leather case containing finely-crafted precision instruments.",
        "tags": [
            ("precision_tools", "item_type"),
            ("tool", "item_type"),
            ("precision_tools", "crafting_tool"),
            ("toolkit", "container_type")
        ],
        "attrs": [
            ("tool_type", "precision"),
            ("engineering_bonus", 15),
            ("contains_tools", [
                "fine_pliers", "jewelers_screwdriver", "calipers",
                "miniature_hammer", "tension_wrench"
            ]),
            ("durability", 80),
            ("max_durability", 80),
            ("repair_materials", ["steel_ingot"]),
            ("weight", 2)
        ]
    }]


class WorkbenchRecipe(SkillAndStatRecipe):
    """Build a workbench for crafting."""
    
    name = "workbench"
    skill_requirement = "crafting"
    difficulty = 35
    craft_time = 3600  # 1 hour
    craft_category = "craft_basic"
    
    stat_requirement = "strength"
    stat_weight = 0.3
    
    tool_tags = ["hammer", "saw", "measuring_tape"]
    consumable_tags = ["wooden_plank", "wooden_plank", "wooden_plank", "wooden_plank",
                      "iron_nails", "iron_nails", "vise"]
    
    output_prototypes = [{
        "key": "sturdy workbench",
        "typeclass": "typeclasses.objects.CraftingStation",
        "desc": "A solid wooden workbench with a built-in vise and tool storage.",
        "tags": [
            ("workbench", "item_type"),
            ("crafting_station", "item_type"),
            ("workbench", "crafting_tool"),
            ("furniture", "item_type")
        ],
        "attrs": [
            ("station_type", "general"),
            ("crafting_bonus", 10),  # +10% success rate
            ("tool_storage", 20),  # Can store 20 items
            ("portable", False),  # Too heavy to move easily
            ("weight", 50),
            ("workshop_level", 1)  # Basic workshop
        ]
    }]


class ForgeRecipe(SkillAndStatRecipe):
    """Build a forge for metalworking - needed for advanced crafting."""
    
    name = "forge"
    skill_requirement = "engineering"
    difficulty = 60
    craft_time = 7200  # 2 hours
    craft_category = "craft_advanced"
    
    stat_requirement = "strength"
    stat_weight = 0.5  # Very physical work
    
    tool_tags = ["hammer", "tongs", "masonry_tools"]
    consumable_tags = ["stone_block", "stone_block", "stone_block", "stone_block",
                      "iron_grate", "bellows", "chimney_pipe", "fire_bricks"]
    
    output_prototypes = [{
        "key": "smithing forge",
        "typeclass": "typeclasses.objects.Forge",
        "desc": "A stone forge with bellows and chimney, ready for metalworking.",
        "tags": [
            ("forge", "item_type"),
            ("crafting_station", "item_type"),
            ("forge", "crafting_tool"),
            ("heat_source", "capability")
        ],
        "attrs": [
            ("station_type", "metalworking"),
            ("max_temperature", 1500),  # Celsius
            ("fuel_type", "coal"),
            ("fuel_capacity", 20),
            ("current_fuel", 0),
            ("crafting_bonus", 20),  # +20% for metal recipes
            ("portable", False),
            ("weight", 200),
            ("workshop_level", 2),  # Advanced workshop
            ("requires_chimney", True)
        ]
    }]
    
    def pre_craft(self, **kwargs):
        """Check if location can support a forge."""
        super().pre_craft(**kwargs)
        
        location = self.crafter.location
        if location.db.indoor and not location.db.workshop:
            err = "You need a proper workshop space to build a forge!"
            self.msg(err)
            raise CraftingValidationError(err)
