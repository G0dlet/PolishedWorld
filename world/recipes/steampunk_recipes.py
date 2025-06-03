# world/recipes/steampunk_recipes.py
"""
Steampunk-themed recipes for advanced technology.

These recipes create steam-powered devices, clockwork mechanisms,
and other technological marvels of the steampunk world.
"""

from world.recipes.base_recipes import SkillBasedRecipe, SkillAndStatRecipe
from evennia.contrib.game_systems.crafting.crafting import CraftingValidationError


class SteamEngineRecipe(SkillAndStatRecipe):
    """Build a basic steam engine - the heart of many devices."""
    
    name = "steam engine"
    skill_requirement = "engineering"
    difficulty = 50
    craft_time = 3600  # 1 hour
    craft_category = "craft_advanced"
    
    # Requires both skill and intelligence
    stat_requirement = "intelligence"
    stat_weight = 0.4
    
    tool_tags = ["forge", "precision_tools", "workbench"]
    consumable_tags = ["iron_ingot", "iron_ingot", "copper_pipe", "brass_fitting", 
                      "brass_fitting", "rubber_seal", "coal"]
    
    output_prototypes = [{
        "key": "steam engine",
        "typeclass": "typeclasses.objects.SteamEngine",
        "desc": "A compact steam engine with gleaming brass fittings and copper pipes.",
        "tags": [
            ("steam_engine", "item_type"),
            ("machine_part", "item_type"),
            ("power_source", "crafting_material")
        ],
        "attrs": [
            ("power_output", 100),  # Base power units
            ("fuel_efficiency", 0.7),  # 70% efficient
            ("max_pressure", 150),
            ("weight", 25),
            ("requires_water", True),
            ("requires_coal", True),
            ("maintenance_interval", 7200)  # Needs maintenance every 2 hours of use
        ]
    }]
    
    success_message = "The engine hums to life with a satisfying hiss of steam!"
    failure_message = "The engine sputters and fails. The pressure seals weren't quite right."


class ClockworkMechanismRecipe(SkillAndStatRecipe):
    """Create a precise clockwork mechanism."""
    
    name = "clockwork mechanism"
    skill_requirement = "engineering"
    difficulty = 40
    craft_time = 2400  # 40 minutes
    craft_category = "craft_advanced"
    
    # Dexterity for precision work
    stat_requirement = "dexterity"
    stat_weight = 0.5
    
    tool_tags = ["precision_tools", "magnifying_glass", "workbench"]
    consumable_tags = ["brass_gear", "brass_gear", "brass_gear", "steel_spring", 
                      "steel_spring", "tiny_screws"]
    
    output_prototypes = [{
        "key": "clockwork mechanism",
        "typeclass": "typeclasses.objects.ClockworkDevice",
        "desc": "An intricate assembly of gears and springs that tick with mechanical precision.",
        "tags": [
            ("clockwork", "item_type"),
            ("mechanism", "crafting_material")
        ],
        "attrs": [
            ("precision", 0.95),  # 95% timing accuracy
            ("complexity", 3),  # Complexity level
            ("tick_rate", 60),  # Ticks per minute
            ("wound", False),
            ("max_tension", 1000),
            ("current_tension", 0)
        ]
    }]


class SteamPistolRecipe(SkillBasedRecipe):
    """Craft a steam-powered pistol."""
    
    name = "steam pistol"
    skill_requirement = "engineering"
    difficulty = 60
    craft_time = 2700  # 45 minutes
    craft_category = "craft_advanced"
    
    tool_tags = ["forge", "precision_tools", "weapon_molds"]
    consumable_tags = ["steel_ingot", "brass_fitting", "pressure_chamber", 
                      "wooden_grip", "trigger_mechanism"]
    
    output_prototypes = [{
        "key": "steam pistol",
        "typeclass": "typeclasses.objects.SteamWeapon",
        "desc": "A brass and steel pistol with a small pressure chamber and steam vents.",
        "tags": [
            ("steam_pistol", "item_type"),
            ("weapon", "item_type"),
            ("ranged", "weapon_type")
        ],
        "attrs": [
            ("damage", 15),  # Base damage
            ("range", 10),  # 10 room range
            ("accuracy", 0.7),  # 70% base accuracy
            ("pressure_per_shot", 20),
            ("max_pressure", 100),
            ("current_pressure", 0),
            ("reload_time", 5),  # 5 seconds between shots
            ("weight", 3),
            ("requires_steam_canister", True)
        ]
    }]


class AutomatonCoreRecipe(SkillAndStatRecipe):
    """Create the core for a mechanical automaton."""
    
    name = "automaton core"
    skill_requirement = "engineering"
    difficulty = 80
    craft_time = 7200  # 2 hours
    craft_category = "craft_advanced"
    
    stat_requirement = "intelligence"
    stat_weight = 0.6  # Very INT dependent
    
    tool_tags = ["advanced_workbench", "precision_tools", "arcane_calibrator"]
    consumable_tags = ["clockwork_mechanism", "steam_engine", "brass_chassis",
                      "control_rods", "control_rods", "memory_gears", "soul_gem"]
    
    output_prototypes = [{
        "key": "automaton core",
        "typeclass": "typeclasses.objects.AutomatonCore",
        "desc": "A complex fusion of clockwork and steam technology, pulsing with potential.",
        "tags": [
            ("automaton_core", "item_type"),
            ("advanced_component", "crafting_material")
        ],
        "attrs": [
            ("core_type", "basic"),
            ("power_capacity", 1000),
            ("instruction_set", "simple"),  # Can follow simple commands
            ("sentience_level", 0.1),  # Barely sentient
            ("activation_phrase", ""),  # Set when activated
            ("owner", ""),
            ("maintenance_log", [])
        ]
    }]
    
    def do_craft(self, **kwargs):
        """Special handling for soul gem consumption."""
        # Check for soul gem quality
        soul_gem = None
        for cons in self.validated_consumables:
            if "soul_gem" in cons.tags.get(category="item_type", return_list=True):
                soul_gem = cons
                break
        
        if soul_gem and hasattr(soul_gem.db, 'soul_quality'):
            # Better soul = better automaton
            quality_bonus = soul_gem.db.soul_quality / 100.0
            for proto in self.output_prototypes:
                for i, (attr_name, attr_val) in enumerate(proto.get("attrs", [])):
                    if attr_name == "sentience_level":
                        new_sentience = attr_val + (quality_bonus * 0.5)
                        proto["attrs"][i] = ("sentience_level", new_sentience)
                        break
        
        return super().do_craft(**kwargs)


class PressureGaugeRecipe(SkillBasedRecipe):
    """A pressure gauge for monitoring steam devices."""
    
    name = "pressure gauge"
    skill_requirement = "engineering"
    difficulty = 30
    craft_time = 900  # 15 minutes
    craft_category = "craft_basic"
    
    tool_tags = ["precision_tools", "workbench"]
    consumable_tags = ["brass_casing", "glass_face", "pressure_spring", "tiny_screws"]
    
    output_prototypes = [{
        "key": "pressure gauge",
        "typeclass": "typeclasses.objects.SteamComponent",
        "desc": "A brass gauge with a glass face showing pressure readings.",
        "tags": [
            ("pressure_gauge", "item_type"),
            ("steam_component", "crafting_material"),
            ("monitoring_device", "item_type")
        ],
        "attrs": [
            ("max_reading", 200),  # PSI
            ("accuracy", 0.95),
            ("warning_threshold", 150),
            ("critical_threshold", 180),
            ("weight", 0.5)
        ]
    }]


class SteamJetpackRecipe(SkillAndStatRecipe):
    """An advanced personal flight device."""
    
    name = "steam jetpack"
    skill_requirement = "engineering"
    difficulty = 90  # Master-level recipe
    craft_time = 10800  # 3 hours
    craft_category = "craft_advanced"
    
    stat_requirement = "intelligence"
    stat_weight = 0.4
    
    tool_tags = ["advanced_forge", "precision_tools", "pressure_testing_rig"]
    consumable_tags = ["steam_engine", "steam_engine", "brass_chassis", "leather_straps",
                      "pressure_regulator", "thrust_nozzles", "control_mechanism", "padding"]
    
    # Can't succeed without very high skill
    exact_consumables = True
    exact_tools = True
    
    output_prototypes = [{
        "key": "steam jetpack",
        "typeclass": "typeclasses.objects.SteamJetpack",
        "desc": "A marvel of engineering: twin brass engines mounted on a reinforced frame.",
        "tags": [
            ("jetpack", "item_type"),
            ("steam_device", "item_type"),
            ("flight_capable", "capability")
        ],
        "attrs": [
            ("flight_duration", 300),  # 5 minutes per fuel load
            ("max_altitude", 5),  # 5 rooms high
            ("fuel_capacity", 10),
            ("current_fuel", 0),
            ("thrust_power", 200),
            ("weight", 40),
            ("worn_on", "back"),
            ("requires_training", True)  # Need flight training to use safely
        ]
    }]
    
    error_skill_too_low = (
        "This is far too complex for your current skill level. "
        "Only a true master engineer could hope to create a {outputs}."
    )
    
    success_message = (
        "With a final adjustment, the jetpack roars to life! "
        "The twin engines pulse with barely-contained power. "
        "You've created something truly extraordinary!"
    )
