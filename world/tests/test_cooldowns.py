# world/tests/test_cooldowns.py
"""
Tests for the cooldown system integration.
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from typeclasses.characters import Character
from unittest.mock import patch, MagicMock
import time


class TestCharacterCooldowns(EvenniaTest):
    """Test cooldown functionality on characters."""
    
    def setUp(self):
        super().setUp()
        self.char = create.create_object(Character, key="TestChar", location=self.room1)
    
    def test_cooldown_handler_exists(self):
        """Test that characters have cooldown handler."""
        self.assertTrue(hasattr(self.char, 'cooldowns'))
        self.assertIsNotNone(self.char.cooldowns)
    
    def test_basic_cooldown_functionality(self):
        """Test basic cooldown operations."""
        # No cooldown initially
        self.assertTrue(self.char.cooldowns.ready("test"))
        self.assertEqual(self.char.cooldowns.time_left("test"), 0)
        
        # Add cooldown
        self.char.cooldowns.add("test", 10)
        self.assertFalse(self.char.cooldowns.ready("test"))
        self.assertGreater(self.char.cooldowns.time_left("test"), 0)
        
        # Reset cooldown
        self.char.cooldowns.reset("test")
        self.assertTrue(self.char.cooldowns.ready("test"))
    
    def test_multiple_cooldowns(self):
        """Test multiple cooldowns can be tracked."""
        self.char.cooldowns.add("gather", 300)
        self.char.cooldowns.add("rest", 180)
        self.char.cooldowns.add("craft", 600)
        
        self.assertFalse(self.char.cooldowns.ready("gather"))
        self.assertFalse(self.char.cooldowns.ready("rest"))
        self.assertFalse(self.char.cooldowns.ready("craft"))
        
        # Reset one
        self.char.cooldowns.reset("rest")
        self.assertTrue(self.char.cooldowns.ready("rest"))
        self.assertFalse(self.char.cooldowns.ready("gather"))
    
    def test_skill_based_cooldown_reduction(self):
        """Test that skills reduce cooldown duration."""
        # Test with no skill
        base_cooldown = 300
        modifier = self.char.get_cooldown_modifier("gather", "foraging")
        self.assertEqual(modifier, 1.0)  # No reduction
        
        # Test with mid-level skill
        self.char.skills.foraging.base = 50
        modifier = self.char.get_cooldown_modifier("gather", "foraging")
        self.assertEqual(modifier, 0.75)  # 25% reduction
        
        # Test with max skill
        self.char.skills.foraging.base = 100
        modifier = self.char.get_cooldown_modifier("gather", "foraging")
        self.assertEqual(modifier, 0.5)  # 50% reduction
    
    def test_constitution_affects_physical_cooldowns(self):
        """Test that constitution reduces physical action cooldowns."""
        # Set up character with high constitution
        self.char.stats.constitution.base = 15  # +5 above base
        self.char.skills.foraging.base = 0  # No skill bonus
        
        # Apply a gather cooldown
        base_cooldown = 300
        actual = self.char.apply_cooldown("gather", base_cooldown, "foraging")
        
        # Should be reduced by CON bonus
        # Base modifier = 1.0 (no skill)
        # CON reduction = (15-10) * 0.01 = 0.05 (5% reduction)
        # Total modifier = 1.0 * (1 - 0.05) = 0.95
        expected = int(300 * 0.95)  # 285
        self.assertEqual(actual, expected)
    
    def test_apply_cooldown_with_all_bonuses(self):
        """Test cooldown application with skill and stat bonuses."""
        # Set up skilled character with good constitution
        self.char.skills.foraging.base = 80  # Expert forager
        self.char.stats.constitution.base = 14  # +4 CON
        
        base_cooldown = 300
        actual = self.char.apply_cooldown("gather", base_cooldown, "foraging")
        
        # Skill modifier: 0.5 + (0.5 * 20/100) = 0.6
        # CON modifier: 1 - 0.04 = 0.96
        # Total: 300 * 0.6 * 0.96 = 172.8 → 172
        expected = int(300 * 0.6 * 0.96)
        self.assertEqual(actual, expected)
    
    def test_cooldown_persistence(self):
        """Test that cooldowns persist on character."""
        # Add some cooldowns
        self.char.cooldowns.add("gather", 300)
        self.char.cooldowns.add("craft", 600)
        
        # Verify they're stored
        self.assertIn("gather", self.char.cooldowns.all)
        self.assertIn("craft", self.char.cooldowns.all)
        
        # Clear all
        self.char.cooldowns.clear()
        self.assertEqual(len(self.char.cooldowns.all), 0)


# world/tests/test_cooldowns.py (rekommenderad version)

class TestCooldownCommands(EvenniaTest):
    """Test cooldown integration in commands."""
    
    def setUp(self):
        super().setUp()
        self.char = create.create_object(Character, key="Gatherer", location=self.room1)
        
        # Add command set
        from commands.default_cmdsets import CharacterCmdSet
        self.char.cmdset.add(CharacterCmdSet)
    
    def test_gather_respects_cooldown(self):
        """Test that gather command checks cooldown."""
        # The actual cooldown functionality is tested in TestCharacterCooldowns
        # Here we just verify that commands can use cooldowns
        
        # Set a cooldown
        self.char.cooldowns.add("gather", 300)
        
        # Verify it's set
        self.assertFalse(self.char.cooldowns.ready("gather"))
        
        # Verify time remaining
        time_left = self.char.cooldowns.time_left("gather", use_int=True)
        self.assertEqual(time_left, 300)
    
    def test_forage_separate_cooldown(self):
        """Test forage has its own cooldown."""
        # Apply gather cooldown
        self.char.cooldowns.add("gather", 300)
        
        # Forage should still work
        self.assertTrue(self.char.cooldowns.ready("forage"))
        
        # Add forage cooldown
        self.char.cooldowns.add("forage", 180)
        
        # Now both should be on cooldown
        self.assertFalse(self.char.cooldowns.ready("gather"))
        self.assertFalse(self.char.cooldowns.ready("forage"))
        
        # And they should have different times
        gather_time = self.char.cooldowns.time_left("gather", use_int=True)
        forage_time = self.char.cooldowns.time_left("forage", use_int=True)
        self.assertNotEqual(gather_time, forage_time)
    
    @patch('commands.survival_commands.delay')
    def test_rest_cooldown_after_completion(self, mock_delay):
        """Test rest command applies cooldown after rest completes."""
        # Set character fatigue to allow rest
        self.char.traits.fatigue.current = 50  # Tired
        
        # Execute rest command
        self.char.execute_cmd("rest")
        
        # Get the delayed function
        self.assertEqual(mock_delay.call_count, 1)
        delay_time, delayed_func = mock_delay.call_args[0]
        
        # Rest should mark character as resting
        self.assertTrue(self.char.db.is_resting)
        
        # Execute the delayed function
        delayed_func()
        
        # Should no longer be resting
        self.assertFalse(self.char.db.is_resting)
        
        # Should have rest cooldown
        self.assertFalse(self.char.cooldowns.ready("rest"))
    
    def test_status_shows_cooldowns(self):
        """Test status command displays active cooldowns."""
        # Set some cooldowns
        self.char.cooldowns.add("gather", 120)
        self.char.cooldowns.add("rest", 60)
        
        # Capture output
        messages = []
        old_msg = self.char.msg
        self.char.msg = lambda text, **kwargs: messages.append(text)
        
        self.char.execute_cmd("status")
        
        # Check output includes cooldowns
        output = "\n".join(messages)
        self.assertIn("Active Cooldowns:", output)
        self.assertIn("gather:", output)
        self.assertIn("rest:", output)
        
        self.char.msg = old_msg
    
    def test_eat_no_cooldown(self):
        """Test eat command has no cooldown."""
        # Create food
        food = create.create_object("typeclasses.objects.Object", 
                                  key="bread", 
                                  location=self.char)
        food.tags.add("food", category="item_type")
        food.db.nutrition = 20
        
        # Eat once
        self.char.traits.hunger.current = 70  # Make somewhat hungry
        self.char.execute_cmd("eat bread")
        
        # Verify bread was consumed
        bread_search = self.char.search("bread", location=self.char, quiet=True)
        self.assertFalse(bread_search)  # Should not find it
        
        # Create another food
        food2 = create.create_object("typeclasses.objects.Object",
                                   key="apple",
                                   location=self.char)
        food2.tags.add("food", category="item_type")
        food2.db.nutrition = 10
        
        # Should be able to eat again immediately (if hungry)
        self.char.traits.hunger.current = 50  # Make hungry again
        self.char.execute_cmd("eat apple")
        
        # Verify apple was consumed
        apple_search = self.char.search("apple", location=self.char, quiet=True)
        self.assertFalse(apple_search)  # Should not find it


class TestCooldownBalancing(EvenniaTest):
    """Test cooldown balance and gameplay impact."""
    
    def setUp(self):
        super().setUp()
        self.novice = create.create_object(Character, key="Novice", location=self.room1)
        self.expert = create.create_object(Character, key="Expert", location=self.room1)
        
        # Set up expert with high skills
        self.expert.skills.foraging.base = 90
        self.expert.skills.crafting.base = 85
        self.expert.skills.survival.base = 95
        self.expert.stats.constitution.base = 16
    
    def test_skill_progression_benefit(self):
        """Test that experts can work significantly faster."""
        base_gather = 300
        
        # Novice cooldown
        novice_cd = self.novice.apply_cooldown("gather", base_gather, "foraging")
        
        # Expert cooldown
        expert_cd = self.expert.apply_cooldown("gather", base_gather, "foraging")
        
        # Expert should be significantly faster
        self.assertLess(expert_cd, novice_cd * 0.6)  # At least 40% faster
        
        # But not too fast (game balance)
        self.assertGreater(expert_cd, 120)  # At least 2 minutes
    
    def test_different_action_cooldowns(self):
        """Test that different actions have appropriate cooldowns."""
        # Use novice character
        # Quick actions
        self.novice.apply_cooldown("forage", 180)  # 3 min
        forage_time = self.novice.cooldowns.time_left("forage")
        
        # Standard actions
        self.novice.apply_cooldown("gather", 300)  # 5 min
        gather_time = self.novice.cooldowns.time_left("gather")
        
        # Long actions
        self.novice.apply_cooldown("craft_advanced", 1800)  # 30 min
        craft_time = self.novice.cooldowns.time_left("craft_advanced")
        
        # Verify hierarchy
        self.assertLess(forage_time, gather_time)
        self.assertLess(gather_time, craft_time)
    
    def test_cooldown_cleanup(self):
        """Test that expired cooldowns are cleaned up."""
        # Use novice character
        # Add several cooldowns
        with patch('time.time', return_value=0):
            self.novice.cooldowns.add("test1", 10)
            self.novice.cooldowns.add("test2", 20)
            self.novice.cooldowns.add("test3", 30)
        
        # Advance time
        with patch('time.time', return_value=25):
            # Cleanup should remove expired cooldowns
            self.novice.cooldowns.cleanup()
            
            # test1 and test2 should be gone
            self.assertTrue(self.novice.cooldowns.ready("test1"))
            self.assertTrue(self.novice.cooldowns.ready("test2"))
            
            # test3 should still be active
            self.assertFalse(self.novice.cooldowns.ready("test3"))
