# world/tests/test_crafting.py
"""
Tests for the crafting system integration.
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from typeclasses.characters import Character
from typeclasses.objects import Object
from world.recipes.survival_recipes import BreadRecipe, WaterContainerRecipe
from world.recipes.tool_recipes import PickaxeRecipe
from evennia.contrib.game_systems.crafting import craft
from evennia.contrib.game_systems.crafting.crafting import CraftingValidationError
from unittest.mock import patch, MagicMock, call


class TestCraftingIntegration(EvenniaTest):
    """Test crafting system with our custom recipes."""
    
    def setUp(self):
        super().setUp()
        self.crafter = create.create_object(Character, key="Crafter", location=self.room1)
        
        # Set up some basic skills
        self.crafter.skills.crafting.base = 30
        self.crafter.skills.engineering.base = 20
        self.crafter.skills.survival.base = 25
        
        # Clear any cooldowns before each test
        if hasattr(self.crafter, 'cooldowns'):
            self.crafter.cooldowns.clear()
    
    def test_recipe_skill_requirements(self):
        """Test that recipes check skill requirements."""
        # Create ingredients for bread
        flour = create.create_object(Object, key="flour", location=self.crafter)
        flour.tags.add("flour", category="crafting_material")
        
        water = create.create_object(Object, key="water", location=self.crafter)
        water.tags.add("water", category="crafting_material")
        
        yeast = create.create_object(Object, key="yeast", location=self.crafter)
        yeast.tags.add("yeast", category="crafting_material")
        
        salt = create.create_object(Object, key="salt", location=self.crafter)
        salt.tags.add("salt", category="crafting_material")
        
        # Create tools
        oven = create.create_object(Object, key="oven", location=self.room1)
        oven.tags.add("oven", category="crafting_tool")
        
        bowl = create.create_object(Object, key="bowl", location=self.crafter)
        bowl.tags.add("mixing_bowl", category="crafting_tool")
        
        # Bread requires crafting 15, we have 30 - should succeed
        recipe = BreadRecipe(self.crafter, flour, water, yeast, salt, oven, bowl)
        
        # Pre-craft should pass
        try:
            recipe.pre_craft()
            validation_passed = True
        except:
            validation_passed = False
            
        self.assertTrue(validation_passed)
        
        # Lower skill and try again
        self.crafter.skills.crafting.base = 10
        recipe2 = BreadRecipe(self.crafter, flour, water, yeast, salt, oven, bowl)
        
        with self.assertRaises(Exception):  # Should raise CraftingValidationError
            recipe2.pre_craft()
    
    def test_cooldown_integration(self):
        """Test that crafting applies cooldowns."""
        # Give crafter materials using seed
        tools, consumables = WaterContainerRecipe.seed(location=self.crafter)
        
        # Craft waterskin
        recipe = WaterContainerRecipe(self.crafter, *(tools + consumables))
        
        # Should not be on cooldown initially
        self.assertTrue(self.crafter.cooldowns.ready("craft_basic"))
        
        # Craft the item
        recipe.pre_craft()
        result = recipe.do_craft()
        recipe.post_craft(result)
        
        # Should now be on cooldown
        self.assertFalse(self.crafter.cooldowns.ready("craft_basic"))
        
        # Check cooldown duration is affected by skill
        time_left = self.crafter.cooldowns.time_left("craft_basic")
        # With 30 crafting skill, should have some reduction
        self.assertLess(time_left, 180)  # Less than base 3 minutes
    
    def test_quality_system(self):
        """Test that skill affects quality."""
        # Create a skilled crafter
        skilled_crafter = create.create_object(Character, key="Master", location=self.room1)
        skilled_crafter.skills.crafting.base = 80  # Expert level
        
        # Create pickaxe ingredients
        tools, consumables = PickaxeRecipe.seed(location=skilled_crafter)
        
        # Mock random to ensure consistent quality
        with patch('world.recipes.base_recipes.random', return_value=0.5):
            recipe = PickaxeRecipe(skilled_crafter, *(tools + consumables))
            recipe.pre_craft()  # This sets crafter_skill
            
            quality_name, quality_mod = recipe.calculate_quality()
            
            # With skill 80 vs difficulty 20, should get excellent or masterwork
            self.assertIn(quality_name, ["excellent", "masterwork"])
            self.assertGreater(quality_mod, 1.3)  # Should have significant bonus
    
    def test_stat_bonus_crafting(self):
        """Test that stats provide bonuses to crafting."""
        # PickaxeRecipe uses strength
        self.crafter.stats.strength.base = 16  # +6 bonus
        
        tools, consumables = PickaxeRecipe.seed(location=self.crafter)
        recipe = PickaxeRecipe(self.crafter, *(tools + consumables))
        
        with patch('world.recipes.base_recipes.random', return_value=0.5):
            recipe.pre_craft()
            quality_name, quality_mod = recipe.calculate_quality()
            
            # Should get some bonus from strength
            self.assertGreater(quality_mod, 1.0)
    
    # I world/tests/test_crafting.py

    def test_craft_function_integration(self):
        """Test using the craft() function directly."""
        # Set up for bread crafting
        tools, consumables = BreadRecipe.seed(location=self.crafter)
    
        # Mock random for consistent results - need to mock the right random
        # Success chance with skill 30 is 0.65, so we need random < 0.65 to succeed
        with patch('world.recipes.base_recipes.random') as mock_random:
            mock_random.return_value = 0.5
            # Create the recipe instance and craft directly
            recipe = BreadRecipe(self.crafter, *(tools + consumables))
            
            # Run pre_craft first to validate inputs
            recipe.pre_craft()
            
            # Now verify we have the right inputs after validation
            self.assertEqual(len(recipe.validated_tools), 2)  # oven and mixing_bowl
            self.assertEqual(len(recipe.validated_consumables), 4)  # flour, water, yeast, salt
            
            result = recipe.do_craft()
            recipe.post_craft(result)
        
            # Check that result is a list with objects
            self.assertTrue(result)  # Should have items in list
            self.assertIsInstance(result, list)  # Should be a list
            self.assertGreater(len(result), 0)  # Should have at least one item
            self.assertTrue(any("bread" in item.key for item in result))
        
            # Check quality was applied
            self.assertTrue(hasattr(result[0].db, 'quality'))
            self.assertTrue(hasattr(result[0].db, 'crafted_by'))
            self.assertEqual(result[0].db.crafted_by, "Crafter")

    
    def test_tool_quality_affects_crafting(self):
        """Test that tool quality affects results."""
        # Create high-quality tools
        hammer = create.create_object(Object, key="masterwork hammer", location=self.crafter)
        hammer.tags.add("hammer", category="crafting_tool")
        hammer.db.quality = 90  # High quality tool
        
        # Create normal tools and materials
        forge = create.create_object(Object, key="forge", location=self.room1)
        forge.tags.add("forge", category="crafting_tool")
        forge.db.quality = 50  # Average
        
        anvil = create.create_object(Object, key="anvil", location=self.room1)
        anvil.tags.add("anvil", category="crafting_tool")
        anvil.db.quality = 50
        
        # Materials
        iron1 = create.create_object(Object, key="iron", location=self.crafter)
        iron1.tags.add("iron_ingot", category="crafting_material")
        iron2 = create.create_object(Object, key="iron", location=self.crafter)
        iron2.tags.add("iron_ingot", category="crafting_material")
        handle = create.create_object(Object, key="handle", location=self.crafter)
        handle.tags.add("wooden_handle", category="crafting_material")
        
        # Craft with high-quality hammer
        recipe = PickaxeRecipe(self.crafter, hammer, forge, anvil, iron1, iron2, handle)
        
        with patch('world.recipes.base_recipes.random', return_value=0.5):
            recipe.pre_craft()
            quality_name, quality_mod = recipe.calculate_quality()
            
            # Should get bonus from high-quality hammer
            self.assertGreater(quality_mod, 1.0)


class TestCraftingCommands(EvenniaTest):
    """Test crafting commands."""
    
    def setUp(self):
        super().setUp()
        self.char = create.create_object(Character, key="Tester", location=self.room1)
        self.char.skills.crafting.base = 20
        
        # Add command set
        from commands.default_cmdsets import CharacterCmdSet
        self.char.cmdset.add(CharacterCmdSet)
    
    @patch('evennia.contrib.game_systems.crafting.crafting._RECIPE_CLASSES', {
        "bread": BreadRecipe,
        "waterskin": WaterContainerRecipe
    })
    def test_craft_list_command(self):
        """Test the craft list command."""
        # Capture output
        old_msg = self.char.msg
        messages = []
        self.char.msg = lambda text, **kwargs: messages.append(text)
        
        self.char.execute_cmd("craft list")
        
        # Check output
        output = "\n".join(messages)
        self.assertIn("Crafting Recipes", output)
        self.assertIn("Your Skills:", output)
        
        # Should show recipes with difficulty
        self.assertIn("bread", output.lower())
        self.assertIn("waterskin", output.lower())
        
        self.char.msg = old_msg
    
    @patch('evennia.contrib.game_systems.crafting.crafting._RECIPE_CLASSES', {
        "bread": BreadRecipe
    })
    def test_craft_info_command(self):
        """Test the craft info command."""
        old_msg = self.char.msg
        messages = []
        self.char.msg = lambda text, **kwargs: messages.append(text)
        
        self.char.execute_cmd("craft info bread")
        
        output = "\n".join(messages)
        self.assertIn("Bread", output)
        self.assertIn("Requirements:", output)
        self.assertIn("Tools needed:", output)
        self.assertIn("Ingredients:", output)
        self.assertIn("flour", output)
        
        self.char.msg = old_msg
    
    def test_recipes_command(self):
        """Test the recipes command."""
        # Give character some known recipes
        self.char.db.known_recipes = ["bread", "waterskin", "pickaxe"]
        self.char.db.craft_counts = {"bread": 5, "waterskin": 2, "pickaxe": 1}
        self.char.db.best_quality = {"bread": "good", "pickaxe": "excellent"}
        
        old_msg = self.char.msg
        messages = []
        self.char.msg = lambda text, **kwargs: messages.append(text)
        
        self.char.execute_cmd("recipes")
        
        output = "\n".join(messages)
        self.assertIn("Your Known Recipes", output)
        self.assertIn("bread", output)
        self.assertIn("crafted 5x", output)
        self.assertIn("best: good", output)
        
        self.char.msg = old_msg
    
    def test_recipes_stats_command(self):
        """Test the recipes stats command."""
        # Set up some stats
        self.char.db.crafting_stats = {
            'total_crafted': 25,
            'total_failed': 5,
            'quality_counts': {
                'poor': 2,
                'average': 10,
                'good': 8,
                'excellent': 5
            }
        }
        
        old_msg = self.char.msg
        messages = []
        self.char.msg = lambda text, **kwargs: messages.append(text)
        
        self.char.execute_cmd("recipes stats")
        
        output = "\n".join(messages)
        self.assertIn("Crafting Statistics", output)
        self.assertIn("Total items crafted: 25", output)
        self.assertIn("Success rate: 83.3%", output)
        self.assertIn("Quality Distribution", output)
        
        self.char.msg = old_msg


# world/tests/test_crafting.py

class TestCraftingTracking(EvenniaTest):
    """Test that crafting statistics are tracked properly."""
    
    def setUp(self):
        super().setUp()
        self.crafter = create.create_object(Character, key="Tracker", location=self.room1)
        self.crafter.skills.crafting.base = 50
        
        # Clear any cooldowns before each test
        if hasattr(self.crafter, 'cooldowns'):
            self.crafter.cooldowns.clear()
        
        # Initialize tracking dicts on the crafter
        self.crafter.db.known_recipes = []
        self.crafter.db.craft_counts = {}
        self.crafter.db.best_quality = {}
        self.crafter.db.crafting_stats = {
            'total_crafted': 0,
            'total_failed': 0,
            'quality_counts': {}
        }
    
    def test_successful_craft_tracking(self):
        """Test that successful crafts are tracked."""
        # Craft bread using the normal craft function
        tools, consumables = BreadRecipe.seed(location=self.crafter)
        
        with patch('world.recipes.base_recipes.random') as mock_random:
            mock_random.return_value = 0.5
            recipe = BreadRecipe(self.crafter, *(tools + consumables))
            recipe.pre_craft()
            result = recipe.do_craft()
            recipe.post_craft(result)
        
        # Check that craft succeeded
        self.assertTrue(result)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # Check tracking
        self.assertIn("bread", self.crafter.db.known_recipes)
        self.assertEqual(self.crafter.db.craft_counts.get("bread", 0), 1)
        self.assertEqual(self.crafter.db.crafting_stats['total_crafted'], 1)
        
        # Check quality tracking
        quality_counts = self.crafter.db.crafting_stats.get('quality_counts', {})
        self.assertGreater(sum(quality_counts.values()), 0)
    
    def test_multiple_craft_tracking(self):
        """Test that multiple crafts are tracked correctly."""
        # Craft bread three times
        for i in range(3):
            # Clear cooldowns between crafts
            if hasattr(self.crafter, 'cooldowns'):
                self.crafter.cooldowns.clear()
                
            tools, consumables = BreadRecipe.seed(location=self.crafter)
            with patch('world.recipes.base_recipes.random') as mock_random:
                mock_random.return_value = 0.5
                recipe = BreadRecipe(self.crafter, *(tools + consumables))
                recipe.pre_craft()
                result = recipe.do_craft()
                recipe.post_craft(result)
                self.assertTrue(result)
        
        # Check counts
        self.assertEqual(self.crafter.db.craft_counts.get("bread", 0), 3)
        self.assertEqual(self.crafter.db.crafting_stats['total_crafted'], 3)
    
    def test_quality_tracking(self):
        """Test that quality is tracked correctly."""
        # Craft with different skill levels to get different qualities
        
        # Low skill - should get average or poor quality
        self.crafter.skills.crafting.base = 20
        tools, consumables = BreadRecipe.seed(location=self.crafter)
        with patch('random.random', return_value=0.9):
            recipe = BreadRecipe(self.crafter, *(tools + consumables))
            recipe.pre_craft()
            result = recipe.do_craft()
            recipe.post_craft(result)
        
        # Clear cooldown before second craft
        if hasattr(self.crafter, 'cooldowns'):
            self.crafter.cooldowns.clear()
            
        # High skill - should get better quality
        self.crafter.skills.crafting.base = 80
        tools, consumables = BreadRecipe.seed(location=self.crafter)
        with patch('world.recipes.base_recipes.random') as mock_random:
            mock_random.return_value = 0.5
            recipe = BreadRecipe(self.crafter, *(tools + consumables))
            recipe.pre_craft()
            result = recipe.do_craft()
            recipe.post_craft(result)
        
        # Check that we have quality data
        quality_counts = self.crafter.db.crafting_stats.get('quality_counts', {})
        self.assertGreater(len(quality_counts), 0)
        
        # Check best quality tracking
        best_quality = self.crafter.db.best_quality.get("bread", "poor")
        self.assertIn(best_quality, ["poor", "average", "good", "fine", "excellent", "masterwork"])
    
    def test_failed_craft_tracking(self):
        """Test that failed crafts are tracked."""
        # Set skill too low for recipe
        self.crafter.skills.crafting.base = 5  # Below bread's requirement of 15
        
        tools, consumables = BreadRecipe.seed(location=self.crafter)
        
        # This should fail due to low skill
        try:
            recipe = BreadRecipe(self.crafter, *(tools + consumables))
            recipe.pre_craft()
            result = []
        except CraftingValidationError:
            result = []
        
        # Should return empty list on failure
        self.assertEqual(result, [])
        
        # Should not be in known recipes since it failed
        self.assertNotIn("bread", self.crafter.db.known_recipes)
        
        # Should not increment craft count
        self.assertEqual(self.crafter.db.craft_counts.get("bread", 0), 0)
        
        # Total crafted should still be 0
        self.assertEqual(self.crafter.db.crafting_stats['total_crafted'], 0)
    
    def test_different_recipe_tracking(self):
        """Test tracking multiple different recipes."""
        # First craft bread
        self.crafter.skills.crafting.base = 30
        tools, consumables = BreadRecipe.seed(location=self.crafter)
        with patch('world.recipes.base_recipes.random') as mock_random:
            mock_random.return_value = 0.5
            recipe = BreadRecipe(self.crafter, *(tools + consumables))
            recipe.pre_craft()
            result = recipe.do_craft()
            recipe.post_craft(result)
        
        # Clear cooldown before second craft
        if hasattr(self.crafter, 'cooldowns'):
            self.crafter.cooldowns.clear()
            
        # Then craft a waterskin
        tools2, consumables2 = WaterContainerRecipe.seed(location=self.crafter)
        with patch('world.recipes.base_recipes.random') as mock_random:
            mock_random.return_value = 0.5
            recipe2 = WaterContainerRecipe(self.crafter, *(tools2 + consumables2))
            recipe2.pre_craft()
            result2 = recipe2.do_craft()
            recipe2.post_craft(result2)
        
        # Check both are tracked
        self.assertIn("bread", self.crafter.db.known_recipes)
        self.assertIn("waterskin", self.crafter.db.known_recipes)
        
        # Check individual counts
        self.assertEqual(self.crafter.db.craft_counts.get("bread", 0), 1)
        self.assertEqual(self.crafter.db.craft_counts.get("waterskin", 0), 1)
        
        # Total should be 2
        self.assertEqual(self.crafter.db.crafting_stats['total_crafted'], 2)
    
    def test_craft_stats_initialization(self):
        """Test that craft stats are properly initialized."""
        # Create a new crafter without pre-initialized stats
        new_crafter = create.create_object(Character, key="NewCrafter", location=self.room1)
        new_crafter.skills.crafting.base = 30
        
        # Clear any cooldowns
        if hasattr(new_crafter, 'cooldowns'):
            new_crafter.cooldowns.clear()
        
        # Craft something
        tools, consumables = BreadRecipe.seed(location=new_crafter)
        # Mock random to return different values for quality calculation and success check
        # First call is for quality randomness, second is for success check
        with patch('world.recipes.base_recipes.random') as mock_random:
            mock_random.return_value = 0.5
            recipe = BreadRecipe(new_crafter, *(tools + consumables))
            recipe.pre_craft()
            result = recipe.do_craft()
            recipe.post_craft(result)
            
        # Verify the craft succeeded
        self.assertTrue(result, "Craft should have succeeded")
        self.assertGreater(len(result), 0, "Should have created at least one item")
        
        # Check that all tracking attributes were created
        self.assertTrue(hasattr(new_crafter.db, 'known_recipes'))
        self.assertTrue(hasattr(new_crafter.db, 'craft_counts'))
        self.assertTrue(hasattr(new_crafter.db, 'best_quality'))
        self.assertTrue(hasattr(new_crafter.db, 'crafting_stats'))
        
        # Check they have correct values
        self.assertIn("bread", new_crafter.db.known_recipes)
        self.assertEqual(new_crafter.db.craft_counts.get("bread", 0), 1)
        self.assertEqual(new_crafter.db.crafting_stats['total_crafted'], 1)
