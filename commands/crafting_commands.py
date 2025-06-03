# commands/crafting_commands.py
"""
Crafting-related commands for the survival game.

Extends the basic crafting command with additional features
like recipe browsing and skill integration.
"""

from evennia.contrib.game_systems.crafting.crafting import CmdCraft as BaseCmdCraft
from evennia.contrib.game_systems.crafting.crafting import craft
from evennia import Command
from evennia.utils import list_to_string, evtable
from django.conf import settings


class CmdCraft(BaseCmdCraft):
    """
    Craft items from recipes using tools and materials.
    
    Usage:
        craft <recipe> [from <ingredients>] [using <tools>]
        craft list [category]
        craft info <recipe>
        
    Examples:
        craft bread from flour, water, yeast using oven
        craft pickaxe from iron, wood using forge, hammer
        craft list survival
        craft info "steam engine"
        
    The crafting system uses your skills and the quality of your
    tools to determine the outcome. Higher skill levels result in
    better quality items with improved stats.
    
    Categories:
        survival - Food, water, basic necessities
        tools - Tools and equipment
        clothing - Armor and weather protection
        steampunk - Advanced machinery and devices
        
    Your current crafting-related skills affect success rates:
        - crafting: General crafting ability
        - engineering: For complex mechanical items
        - survival: For wilderness and food crafts
    """
    
    key = "craft"
    aliases = ["create", "make", "build"]
    help_category = "Crafting"
    
    def func(self):
        """Execute the craft command."""
        if not self.args:
            self.caller.msg("Usage: craft <recipe> [from <ingredient>,...] [using <tool>,...]")
            self.caller.msg("       craft list [category]")
            self.caller.msg("       craft info <recipe>")
            return
        
        # Check for subcommands
        if self.args.startswith("list"):
            self.list_recipes()
            return
        elif self.args.startswith("info"):
            self.show_recipe_info()
            return
        
        # Otherwise, do normal crafting
        super().func()
    
    def list_recipes(self):
        """List available recipes, optionally filtered by category."""
        from evennia.contrib.game_systems.crafting.crafting import _load_recipes, _RECIPE_CLASSES
        
        _load_recipes()
        
        # Parse category filter
        args = self.args.split(None, 1)
        category = args[1].lower() if len(args) > 1 else None
        
        # Get character's skills for display
        crafting_skill = self.caller.skills.crafting.value
        engineering_skill = self.caller.skills.engineering.value
        survival_skill = self.caller.skills.survival.value
        
        # Build recipe list
        recipes_by_category = {
            "survival": [],
            "tools": [],
            "clothing": [],
            "steampunk": [],
            "other": []
        }
        
        for recipe_name, recipe_class in _RECIPE_CLASSES.items():
            # Categorize based on module or recipe properties
            if hasattr(recipe_class, 'craft_category'):
                if 'steampunk' in recipe_class.__module__:
                    cat = "steampunk"
                elif 'clothing' in recipe_class.__module__:
                    cat = "clothing"
                elif 'tool' in recipe_class.__module__:
                    cat = "tools"
                elif 'survival' in recipe_class.__module__:
                    cat = "survival"
                else:
                    cat = "other"
            else:
                cat = "other"
            
            # Get skill info
            skill_req = getattr(recipe_class, 'skill_requirement', 'crafting')
            difficulty = getattr(recipe_class, 'difficulty', 0)
            
            # Check if player can attempt this
            if skill_req == "engineering":
                current_skill = engineering_skill
            elif skill_req == "survival":
                current_skill = survival_skill
            else:
                current_skill = crafting_skill
            
            can_attempt = current_skill >= difficulty
            
            # Format entry
            if can_attempt:
                status = "|g✓|n"
            else:
                status = "|r✗|n"
            
            entry = f"{status} {recipe_name:<20} ({skill_req} {difficulty}+)"
            
            recipes_by_category[cat].append((difficulty, entry))
        
        # Display results
        if category and category in recipes_by_category:
            # Show single category
            self.caller.msg(f"\n|wCrafting Recipes - {category.title()}:|n")
            recipes = sorted(recipes_by_category[category], key=lambda x: x[0])
            for _, entry in recipes:
                self.caller.msg(f"  {entry}")
        else:
            # Show all categories
            self.caller.msg("\n|wCrafting Recipes:|n")
            self.caller.msg("|xUse 'craft list <category>' to filter|n")
            
            for cat in ["survival", "tools", "clothing", "steampunk", "other"]:
                if recipes_by_category[cat]:
                    self.caller.msg(f"\n|w{cat.title()}:|n")
                    recipes = sorted(recipes_by_category[cat], key=lambda x: x[0])
                    for _, entry in recipes[:10]:  # Show first 10
                        self.caller.msg(f"  {entry}")
                    if len(recipes) > 10:
                        self.caller.msg(f"  |x... and {len(recipes) - 10} more|n")
        
        # Show skill summary
        self.caller.msg(f"\n|wYour Skills:|n")
        self.caller.msg(f"  Crafting: {crafting_skill}")
        self.caller.msg(f"  Engineering: {engineering_skill}")
        self.caller.msg(f"  Survival: {survival_skill}")
    
    def show_recipe_info(self):
        """Show detailed info about a specific recipe."""
        from evennia.contrib.game_systems.crafting.crafting import _load_recipes, _RECIPE_CLASSES
        
        _load_recipes()
        
        # Get recipe name
        args = self.args.split(None, 1)
        if len(args) < 2:
            self.caller.msg("Usage: craft info <recipe name>")
            return
        
        recipe_name = args[1].lower()
        
        # Find recipe
        recipe_class = None
        for rname, rclass in _RECIPE_CLASSES.items():
            if rname.lower() == recipe_name or recipe_name in rname.lower():
                recipe_class = rclass
                recipe_name = rname
                break
        
        if not recipe_class:
            self.caller.msg(f"No recipe found matching '{recipe_name}'.")
            return
        
        # Display recipe info
        self.caller.msg(f"\n|w{recipe_name.title()}|n")
        if hasattr(recipe_class, '__doc__') and recipe_class.__doc__:
            self.caller.msg(f"|x{recipe_class.__doc__.strip()}|n")
        
        # Requirements
        skill_req = getattr(recipe_class, 'skill_requirement', 'crafting')
        difficulty = getattr(recipe_class, 'difficulty', 0)
        
        self.caller.msg(f"\n|wRequirements:|n")
        self.caller.msg(f"  Skill: {skill_req} {difficulty}+")
        
        # Tools
        if recipe_class.tool_tags:
            self.caller.msg(f"\n|wTools needed:|n")
            for tool in recipe_class.tool_tags:
                self.caller.msg(f"  - {tool}")
        
        # Ingredients
        if recipe_class.consumable_tags:
            self.caller.msg(f"\n|wIngredients:|n")
            # Count duplicates
            ing_counts = {}
            for ing in recipe_class.consumable_tags:
                ing_counts[ing] = ing_counts.get(ing, 0) + 1
            
            for ing, count in ing_counts.items():
                if count > 1:
                    self.caller.msg(f"  - {ing} x{count}")
                else:
                    self.caller.msg(f"  - {ing}")
        
        # Output
        self.caller.msg(f"\n|wCreates:|n")
        for proto in recipe_class.output_prototypes:
            key = proto.get('key', 'unknown item')
            self.caller.msg(f"  - {key}")
        
        # Craft time
        craft_time = getattr(recipe_class, 'craft_time', 300)
        minutes = craft_time // 60
        seconds = craft_time % 60
        if minutes:
            time_str = f"{minutes}m {seconds}s" if seconds else f"{minutes}m"
        else:
            time_str = f"{seconds}s"
        self.caller.msg(f"\n|wCraft time:|n {time_str}")
        
        # Check if player can attempt
        current_skill = 0
        if skill_req == "engineering":
            current_skill = self.caller.skills.engineering.value
        elif skill_req == "survival":
            current_skill = self.caller.skills.survival.value
        else:
            current_skill = self.caller.skills.crafting.value
        
        if current_skill >= difficulty:
            self.caller.msg(f"\n|gYou have the skill to attempt this recipe.|n")
        else:
            needed = difficulty - current_skill
            self.caller.msg(f"\n|rYou need {needed} more {skill_req} skill to attempt this.|n")


class CmdRecipes(Command):
    """
    View your known recipes and crafting statistics.
    
    Usage:
        recipes
        recipes stats
        
    Shows all recipes you've successfully crafted before,
    along with your crafting statistics and achievements.
    """
    
    key = "recipes"
    aliases = ["known_recipes"]
    locks = "cmd:all()"
    help_category = "Crafting"
    
    def func(self):
        """Display known recipes or stats."""
        if self.args.strip() == "stats":
            self.show_crafting_stats()
        else:
            self.show_known_recipes()
    
    def show_known_recipes(self):
        """Display recipes the player has successfully crafted."""
        known_recipes = self.caller.db.known_recipes or []
        
        if not known_recipes:
            self.caller.msg("You haven't successfully crafted any recipes yet.")
            self.caller.msg("Use |wcraft list|n to see available recipes.")
            return
        
        self.caller.msg("|wYour Known Recipes:|n")
        
        # Group by category
        by_category = {}
        for recipe_name in known_recipes:
            # Simple categorization
            if any(word in recipe_name for word in ["bread", "stew", "tea", "preserved"]):
                cat = "Food & Drink"
            elif any(word in recipe_name for word in ["armor", "cloak", "goggles", "coat"]):
                cat = "Clothing"
            elif any(word in recipe_name for word in ["pickaxe", "tools", "forge", "workbench"]):
                cat = "Tools"
            elif any(word in recipe_name for word in ["steam", "clockwork", "automaton", "pressure"]):
                cat = "Steampunk"
            else:
                cat = "Other"
            
            by_category.setdefault(cat, []).append(recipe_name)
        
        # Display by category
        for cat, recipes in sorted(by_category.items()):
            self.caller.msg(f"\n|w{cat}:|n")
            for recipe in sorted(recipes):
                count = self.caller.db.craft_counts.get(recipe, 0)
                quality = self.caller.db.best_quality.get(recipe, "average")
                self.caller.msg(f"  {recipe:<25} (crafted {count}x, best: {quality})")
    
    def show_crafting_stats(self):
        """Display crafting statistics."""
        stats = self.caller.db.crafting_stats or {}
        
        self.caller.msg("|wCrafting Statistics:|n")
        
        total_crafted = stats.get('total_crafted', 0)
        total_failed = stats.get('total_failed', 0)
        total_attempts = total_crafted + total_failed
        
        if total_attempts > 0:
            success_rate = (total_crafted / total_attempts) * 100
        else:
            success_rate = 0
        
        self.caller.msg(f"\nTotal items crafted: {total_crafted}")
        self.caller.msg(f"Failed attempts: {total_failed}")
        self.caller.msg(f"Success rate: {success_rate:.1f}%")
        
        # Quality breakdown
        quality_counts = stats.get('quality_counts', {})
        if quality_counts:
            self.caller.msg("\n|wQuality Distribution:|n")
            for quality in ["poor", "average", "good", "fine", "excellent", "masterwork"]:
                count = quality_counts.get(quality, 0)
                if count > 0:
                    percent = (count / total_crafted) * 100
                    self.caller.msg(f"  {quality:<12} {count:>4} ({percent:>5.1f}%)")
        
        # Most crafted
        craft_counts = self.caller.db.craft_counts or {}
        if craft_counts:
            self.caller.msg("\n|wMost Crafted Items:|n")
            sorted_items = sorted(craft_counts.items(), key=lambda x: x[1], reverse=True)
            for recipe, count in sorted_items[:5]:
                self.caller.msg(f"  {recipe:<25} {count}x")
        
        # Skill levels
        self.caller.msg("\n|wCrafting Skills:|n")
        self.caller.msg(f"  Crafting: {self.caller.skills.crafting.value}")
        self.caller.msg(f"  Engineering: {self.caller.skills.engineering.value}")
        self.caller.msg(f"  Survival: {self.caller.skills.survival.value}")
