"""
Tests for Character typeclass and trait systems.
"""
from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from typeclasses.characters import Character


class TestCharacterTraits(EvenniaTest):
    """Test character trait categories and functionality."""
    
    def setUp(self):
        """Set up test character."""
        super().setUp()
        # Create a test character with traits using Evennia's create_object
        self.test_char = create.create_object(
            Character, 
            key="TestChar", 
            location=self.room1
        )
    
    def test_trait_categories_exist(self):
        """Test that all three trait categories are initialized."""
        # Access the properties to ensure they're created
        stats = self.test_char.stats
        traits = self.test_char.traits
        skills = self.test_char.skills
        
        self.assertIsNotNone(stats)
        self.assertIsNotNone(traits)
        self.assertIsNotNone(skills)
        
        # Verify they are TraitHandlers
        self.assertEqual(type(stats).__name__, 'TraitHandler')
        self.assertEqual(type(traits).__name__, 'TraitHandler')
        self.assertEqual(type(skills).__name__, 'TraitHandler')
    
    def test_stat_values(self):
        """Test stat traits have correct default values."""
        # All stats should start at 10
        self.assertEqual(self.test_char.stats.strength.value, 10)
        self.assertEqual(self.test_char.stats.dexterity.value, 10)
        self.assertEqual(self.test_char.stats.constitution.value, 10)
        self.assertEqual(self.test_char.stats.intelligence.value, 10)
        self.assertEqual(self.test_char.stats.wisdom.value, 10)
        self.assertEqual(self.test_char.stats.charisma.value, 10)
        
        # Test stat modification
        self.test_char.stats.strength.base = 15
        self.assertEqual(self.test_char.stats.strength.value, 15)
        
        # Test modifier
        self.test_char.stats.strength.mod = 2
        self.assertEqual(self.test_char.stats.strength.value, 17)
    
    def test_survival_trait_initialization(self):
        """Test survival traits start at correct values."""
        # All survival traits should start at 100 (full)
        self.assertEqual(self.test_char.traits.hunger.value, 100)
        self.assertEqual(self.test_char.traits.thirst.value, 100)
        self.assertEqual(self.test_char.traits.fatigue.value, 100)
        self.assertEqual(self.test_char.traits.health.value, 100)
        
        # Test descriptions
        self.assertEqual(self.test_char.traits.hunger.desc(), "full")
        self.assertEqual(self.test_char.traits.thirst.desc(), "hydrated")
        self.assertEqual(self.test_char.traits.fatigue.desc(), "energized")
        self.assertEqual(self.test_char.traits.health.desc(), "healthy")
    
    def test_survival_trait_decay_rates(self):
        """Test that survival traits have correct decay rates set."""
        # Check decay rates (per second, will be converted to per hour in gametime)
        self.assertEqual(self.test_char.traits.hunger.rate, -2.0)
        self.assertEqual(self.test_char.traits.thirst.rate, -3.0)
        self.assertEqual(self.test_char.traits.fatigue.rate, -1.0)
        self.assertEqual(self.test_char.traits.health.rate, 0)  # Health doesn't auto-decay
    
    def test_survival_trait_modification(self):
        """Test modifying survival traits."""
        # Test direct modification
        self.test_char.traits.hunger.current = 50
        self.assertEqual(self.test_char.traits.hunger.value, 50)
        self.assertEqual(self.test_char.traits.hunger.desc(), "hungry")
        
        # Test boundaries
        self.test_char.traits.hunger.current = -10
        self.assertEqual(self.test_char.traits.hunger.value, 0)  # Should clamp to min
        
        self.test_char.traits.hunger.current = 150
        self.assertEqual(self.test_char.traits.hunger.value, 100)  # Should clamp to max
    
    def test_skill_progression(self):
        """Test skill advancement."""
        # Skills should start at 0
        self.assertEqual(self.test_char.skills.crafting.value, 0)
        self.assertEqual(self.test_char.skills.crafting.desc(), "untrained")
        
        # Test skill increase
        self.test_char.skills.crafting.current = 15
        self.assertEqual(self.test_char.skills.crafting.value, 15)
        self.assertEqual(self.test_char.skills.crafting.desc(), "novice")
        
        # Test skill boundaries
        self.test_char.skills.crafting.current = 150
        self.assertEqual(self.test_char.skills.crafting.value, 100)  # Should clamp to max
    
    def test_convenience_methods(self):
        """Test the convenience methods for accessing traits."""
        # Test get_stat
        self.assertEqual(self.test_char.get_stat("strength"), 10)
        self.assertIsNone(self.test_char.get_stat("invalid_stat"))
        
        # Test get_trait_status
        value, desc = self.test_char.get_trait_status("hunger")
        self.assertEqual(value, 100)
        self.assertEqual(desc, "full")
        
        # Test get_skill_level
        value, desc = self.test_char.get_skill_level("crafting")
        self.assertEqual(value, 0)
        self.assertEqual(desc, "untrained")
        
        # Test modify_trait
        self.assertTrue(self.test_char.modify_trait("hunger", -20))
        self.assertEqual(self.test_char.traits.hunger.value, 80)
        self.assertFalse(self.test_char.modify_trait("invalid_trait", 10))
        
        # Test improve_skill
        self.assertTrue(self.test_char.improve_skill("crafting", 5))
        self.assertEqual(self.test_char.skills.crafting.value, 5)
        self.assertFalse(self.test_char.improve_skill("invalid_skill"))


class TestCharacterSurvival(EvenniaTest):
    """Test survival mechanics specific functionality."""
    
    def setUp(self):
        """Set up test character."""
        super().setUp()
        self.char = create.create_object(
            Character,
            key="SurvivalChar",
            location=self.room1
        )
    
    def test_hunger_boundaries(self):
        """Test hunger can't go below 0 or above 100."""
        # Test lower boundary
        self.char.traits.hunger.current = -50
        self.assertEqual(self.char.traits.hunger.value, 0)
        self.assertEqual(self.char.traits.hunger.desc(), "starving")
        
        # Test upper boundary
        self.char.traits.hunger.current = 200
        self.assertEqual(self.char.traits.hunger.value, 100)
        self.assertEqual(self.char.traits.hunger.desc(), "full")
    
    def test_thirst_progression(self):
        """Test thirst descriptions at different levels."""
        thirst_levels = [
            (0, "dehydrated"),
            (15, "dehydrated"),  # Updated based on new bounds
            (30, "parched"),
            (50, "thirsty"),
            (75, "slightly thirsty"),
            (95, "refreshed")
        ]
        
        for value, expected_desc in thirst_levels:
            self.char.traits.thirst.current = value
            self.assertEqual(self.char.traits.thirst.desc(), expected_desc)
    
    def test_survival_summary(self):
        """Test survival summary generation."""
        # Set some test values
        self.char.traits.hunger.current = 75
        self.char.traits.thirst.current = 50
        self.char.traits.fatigue.current = 25
        self.char.traits.health.current = 90
        
        summary = self.char.get_survival_summary()
        
        # Check that all traits are in summary
        self.assertIn("Hunger: 75% (peckish)", summary)
        self.assertIn("Thirst: 50% (thirsty)", summary)
        self.assertIn("Fatigue: 25% (very tired)", summary)
        self.assertIn("Health: 90% (bruised)", summary)
    
    def test_skill_summary(self):
        """Test skill summary generation."""
        # Set some test values
        self.char.skills.crafting.current = 35
        self.char.skills.hunting.current = 15
        self.char.skills.engineering.current = 75
        
        summary = self.char.get_skill_summary()
        
        # Check that skills show correct values and descriptions
        self.assertIn("Crafting: 35 (apprentice)", summary)
        self.assertIn("Hunting: 15 (novice)", summary)
        self.assertIn("Engineering: 75 (expert)", summary)
        self.assertIn("Foraging: 0 (untrained)", summary)


class TestCharacterStatModifiers(EvenniaTest):
    """Test stat modifier functionality."""
    
    def setUp(self):
        """Set up test character."""
        super().setUp()
        self.char = create.create_object(
            Character,
            key="ModChar",
            location=self.room1
        )
    
    def test_stat_modifiers(self):
        """Test that stat modifiers work correctly."""
        # Base value
        self.assertEqual(self.char.stats.strength.value, 10)
        
        # Add modifier
        self.char.stats.strength.mod = 3
        self.assertEqual(self.char.stats.strength.value, 13)
        
        # Change base
        self.char.stats.strength.base = 12
        self.assertEqual(self.char.stats.strength.value, 15)  # 12 + 3
        
        # Test multiplier
        self.char.stats.strength.mult = 1.5
        # The result will be a float, so we compare with the exact value
        self.assertEqual(self.char.stats.strength.value, 22.5)  # (12 + 3) * 1.5
    
    def test_gauge_reset(self):
        """Test resetting gauge traits to full."""
        # Deplete some traits
        self.char.traits.hunger.current = 25
        self.char.traits.thirst.current = 10
        
        # Reset them
        self.char.traits.hunger.reset()
        self.char.traits.thirst.reset()
        
        # Should be back to full
        self.assertEqual(self.char.traits.hunger.value, 100)
        self.assertEqual(self.char.traits.thirst.value, 100)
    
    def test_skill_reset(self):
        """Test resetting skills back to base."""
        # Increase skill
        self.char.skills.crafting.current = 50
        
        # Reset
        self.char.skills.crafting.reset()
        
        # Should be back to base (0)
        self.assertEqual(self.char.skills.crafting.value, 0)


class TestCharacterEdgeCases(EvenniaTest):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test character."""
        super().setUp()
        self.char = create.create_object(
            Character,
            key="EdgeCaseChar",
            location=self.room1
        )
    
    def test_modify_trait_edge_cases(self):
        """Test edge cases for modify_trait method."""
        # Test modifying with extreme values
        self.assertTrue(self.char.modify_trait("hunger", 1000))
        self.assertEqual(self.char.traits.hunger.value, 100)  # Should cap at max
    
        self.assertTrue(self.char.modify_trait("hunger", -2000))
        self.assertEqual(self.char.traits.hunger.value, 0)  # Should cap at min
    
        # Test modifying with float values
        # Note: Gauge traits with integer base will round the result
        self.char.traits.hunger.current = 50
        self.assertTrue(self.char.modify_trait("hunger", 5.5))
        # Since base is an integer, the value gets rounded
        self.assertEqual(self.char.traits.hunger.value, 55)  # 55.5 rounds to 55
    
        # Test modifying non-existent trait
        self.assertFalse(self.char.modify_trait("nonexistent", 10))
    
    def test_improve_skill_edge_cases(self):
        """Test edge cases for improve_skill method."""
        # Test improving beyond max
        self.char.skills.crafting.current = 95
        self.assertTrue(self.char.improve_skill("crafting", 20))
        self.assertEqual(self.char.skills.crafting.value, 100)  # Should cap at max
        
        # Test improving with negative value (skill decrease)
        self.char.skills.hunting.current = 50
        self.assertTrue(self.char.improve_skill("hunting", -10))
        self.assertEqual(self.char.skills.hunting.value, 40)
        
        # Test improving below min
        self.char.skills.foraging.current = 5
        self.assertTrue(self.char.improve_skill("foraging", -10))
        self.assertEqual(self.char.skills.foraging.value, 0)  # Should cap at min
    
    def test_convenience_methods_with_empty_traits(self):
        """Test convenience methods on character without traits."""
        # Create a character and manually remove traits
        empty_char = create.create_object(
            Character,
            key="EmptyChar",
            location=self.room1
        )
        # Don't remove the handlers, just test with non-existent trait names
        
        # Test all convenience methods with non-existent traits
        self.assertIsNone(empty_char.get_stat("nonexistent"))
        self.assertEqual(empty_char.get_trait_status("nonexistent"), (None, None))
        self.assertEqual(empty_char.get_skill_level("nonexistent"), (None, None))
        self.assertFalse(empty_char.modify_trait("nonexistent", 10))
        self.assertFalse(empty_char.improve_skill("nonexistent", 5))
    
    def test_summary_methods_formatting(self):
        """Test summary methods with various trait values."""
        # Set all traits to different values
        self.char.traits.hunger.current = 0
        self.char.traits.thirst.current = 33
        self.char.traits.fatigue.current = 66
        self.char.traits.health.current = 100
        
        summary = self.char.get_survival_summary()
        lines = summary.split('\n')
        self.assertEqual(len(lines), 4)  # Should have 4 lines
        
        # Check each line format
        self.assertTrue(all(': ' in line and '% (' in line and ')' in line for line in lines))
        
        # Set skills to various levels
        self.char.skills.crafting.current = 0
        self.char.skills.hunting.current = 25
        self.char.skills.foraging.current = 50
        self.char.skills.engineering.current = 75
        self.char.skills.survival.current = 90
        self.char.skills.trading.current = 100
        
        skill_summary = self.char.get_skill_summary()
        skill_lines = skill_summary.split('\n')
        self.assertEqual(len(skill_lines), 6)  # Should have 6 lines
        
        # Verify all skill levels are represented
        self.assertIn("untrained", skill_summary)
        self.assertIn("novice", skill_summary)
        self.assertIn("journeyman", skill_summary)
        self.assertIn("expert", skill_summary)
        self.assertIn("master", skill_summary)


class TestTraitModifiersAndMultipliers(EvenniaTest):
    """Test advanced trait modifications with mods and multipliers."""
    
    def setUp(self):
        """Set up test character."""
        super().setUp()
        self.char = create.create_object(
            Character,
            key="ModTestChar",
            location=self.room1
        )
    
    def test_skill_with_modifiers(self):
        """Test skills with mod and mult values."""
        # Test base + mod
        self.char.skills.crafting.base = 20
        self.char.skills.crafting.mod = 10
        self.assertEqual(self.char.skills.crafting.value, 30)  # 20 + 10
        
        # Test with current different from base
        self.char.skills.crafting.current = 40
        self.assertEqual(self.char.skills.crafting.value, 50)  # 40 + 10
        
        # Test with multiplier
        self.char.skills.crafting.mult = 1.5
        self.assertEqual(self.char.skills.crafting.value, 75)  # (40 + 10) * 1.5
        
        # Test that desc() still works correctly with modifiers
        self.assertEqual(self.char.skills.crafting.desc(), "expert")  # 75 is in 70-89 range
    
    def test_survival_trait_modifiers(self):
        """Test survival traits with modifiers don't break gauge behavior."""
        # Gauges use mod differently - it affects max, not current
        self.char.traits.hunger.base = 100
        self.char.traits.hunger.mod = 20
        
        # Max should be base + mod
        self.assertEqual(self.char.traits.hunger.max, 120)
        
        # Current should start at max
        self.char.traits.hunger.reset()
        self.assertEqual(self.char.traits.hunger.value, 120)
        
        # Test with multiplier
        self.char.traits.hunger.mult = 0.5
        self.assertEqual(self.char.traits.hunger.max, 60)  # (100 + 20) * 0.5
    
    def test_stat_modifier_combinations(self):
        """Test various combinations of base, mod, and mult."""
        # Test negative modifier
        self.char.stats.strength.base = 15
        self.char.stats.strength.mod = -3
        self.assertEqual(self.char.stats.strength.value, 12)
    
        # Test fractional multiplier with negative mod
        self.char.stats.strength.mult = 0.8
        # Use assertAlmostEqual for floating point comparison to avoid precision issues
        self.assertAlmostEqual(self.char.stats.strength.value, 9.6, places=1)
    
        # Test zero multiplier (edge case)
        self.char.stats.strength.mult = 0
        self.assertEqual(self.char.stats.strength.value, 0)
    
        # Reset and test large multiplier
        self.char.stats.strength.mult = 3.0
        self.char.stats.strength.mod = 5
        self.assertEqual(self.char.stats.strength.value, 60)  # (15 + 5) * 3


class TestAutoDecaySimulation(EvenniaTest):
    """Test auto-decay behavior (without actual time passing)."""
    
    def setUp(self):
        """Set up test character."""
        super().setUp()
        self.char = create.create_object(
            Character,
            key="DecayTestChar",
            location=self.room1
        )
    
    def test_decay_rates_are_set(self):
        """Verify decay rates are properly configured."""
        # Check all decay rates
        self.assertEqual(self.char.traits.hunger.rate, -2.0)
        self.assertEqual(self.char.traits.thirst.rate, -3.0)
        self.assertEqual(self.char.traits.fatigue.rate, -1.0)
        self.assertEqual(self.char.traits.health.rate, 0)
        
        # Verify rates are negative (decay) except health
        self.assertLess(self.char.traits.hunger.rate, 0)
        self.assertLess(self.char.traits.thirst.rate, 0)
        self.assertLess(self.char.traits.fatigue.rate, 0)
        self.assertEqual(self.char.traits.health.rate, 0)
    
    def test_manual_decay_simulation(self):
        """Simulate decay by manually adjusting values."""
        # Start with known values
        self.char.traits.hunger.current = 100
        self.char.traits.thirst.current = 100
        self.char.traits.fatigue.current = 100
        
        # Simulate 1 hour of decay manually
        self.char.traits.hunger.current += self.char.traits.hunger.rate
        self.char.traits.thirst.current += self.char.traits.thirst.rate
        self.char.traits.fatigue.current += self.char.traits.fatigue.rate
        
        # Check values decreased correctly
        self.assertEqual(self.char.traits.hunger.value, 98)  # 100 - 2
        self.assertEqual(self.char.traits.thirst.value, 97)  # 100 - 3
        self.assertEqual(self.char.traits.fatigue.value, 99)  # 100 - 1
        
        # Simulate many hours until hitting bottom
        self.char.traits.hunger.current = 5
        self.char.traits.hunger.current += self.char.traits.hunger.rate * 3  # 3 hours
        self.assertEqual(self.char.traits.hunger.value, 0)  # Should stop at 0
    
    def test_trait_descriptions_during_decay(self):
        """Test that descriptions update correctly as traits decay."""
        # Test hunger descriptions at each threshold
        hunger_thresholds = [
            (100, "full"),
            (95, "satisfied"),
            (75, "peckish"),
            (55, "hungry"),
            (35, "very hungry"),
            (15, "starving"),
            (0, "starving")
        ]
        
        for value, expected_desc in hunger_thresholds:
            self.char.traits.hunger.current = value
            self.assertEqual(
                self.char.traits.hunger.desc(), 
                expected_desc,
                f"At hunger {value}, expected '{expected_desc}' but got '{self.char.traits.hunger.desc()}'"
            )


class TestCharacterCreationVariations(EvenniaTest):
    """Test creating characters in different ways."""
    
    def test_multiple_character_creation(self):
        """Test that multiple characters have independent traits."""
        char1 = create.create_object(Character, key="Char1", location=self.room1)
        char2 = create.create_object(Character, key="Char2", location=self.room1)
        
        # Modify char1's traits
        char1.stats.strength.base = 15
        char1.traits.hunger.current = 50
        char1.skills.crafting.current = 30
        
        # Verify char2's traits are unaffected
        self.assertEqual(char2.stats.strength.value, 10)
        self.assertEqual(char2.traits.hunger.value, 100)
        self.assertEqual(char2.skills.crafting.value, 0)
        
        # Verify modifications stuck to char1
        self.assertEqual(char1.stats.strength.value, 15)
        self.assertEqual(char1.traits.hunger.value, 50)
        self.assertEqual(char1.skills.crafting.value, 30)
    
    def test_character_persistence_simulation(self):
        """Test that trait values would persist (without actual save/load)."""
        char = create.create_object(Character, key="PersistChar", location=self.room1)
        
        # Modify various traits
        char.stats.intelligence.mod = 3
        char.traits.thirst.current = 75
        char.skills.engineering.current = 45
        
        # Get the underlying data (this is what would be saved)
        stats_data = char.attributes.get("stats", category="traits")
        traits_data = char.attributes.get("traits", category="traits")
        skills_data = char.attributes.get("skills", category="traits")
        
        # Verify data structures exist
        self.assertIsNotNone(stats_data)
        self.assertIsNotNone(traits_data)
        self.assertIsNotNone(skills_data)
        
        # Verify our modifications are in the data
        self.assertEqual(stats_data.get("intelligence", {}).get("mod"), 3)
        self.assertEqual(traits_data.get("thirst", {}).get("current"), 75)
        self.assertEqual(skills_data.get("engineering", {}).get("current"), 45)
