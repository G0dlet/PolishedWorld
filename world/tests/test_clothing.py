# world/tests/test_clothing.py
"""
Tests for the clothing system and survival benefits.
"""

from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from typeclasses.characters import Character
from typeclasses.objects import (
    WinterCloak, LeatherBoots, RainCoat, WorkGloves,
    WoolenHat, EngineeringGoggles, DecorativeScarf,
    CamouflageCloak, SurvivalClothing
)
from typeclasses.rooms import Room
from unittest.mock import patch


class TestClothingSystem(EvenniaTest):
    """Test basic clothing functionality."""
    
    def setUp(self):
        super().setUp()
        self.char = create.create_object(Character, key="TestChar", location=self.room1)
        self.cloak = create.create_object(WinterCloak, key="winter cloak", location=self.char)
        self.boots = create.create_object(LeatherBoots, key="boots", location=self.char)
    
    def test_clothing_creation(self):
        """Test clothing items are created with correct properties."""
        # Check cloak properties
        self.assertEqual(self.cloak.db.clothing_type, "cloak")
        self.assertEqual(self.cloak.db.warmth_value, 25)
        self.assertIn("snow", self.cloak.db.weather_protection)
        self.assertIn("wind", self.cloak.db.weather_protection)
        self.assertIn("rain", self.cloak.db.weather_protection)
        self.assertEqual(self.cloak.db.stat_modifiers.get("constitution"), 1)
        
        # Check boots properties
        self.assertEqual(self.boots.db.clothing_type, "shoes")
        self.assertEqual(self.boots.db.warmth_value, 5)
        self.assertIn("rain", self.boots.db.weather_protection)
        
        # Check visibility properties (from Object inheritance)
        self.assertEqual(self.cloak.db.visibility_size, "large")
        self.assertEqual(self.boots.db.visibility_size, "normal")
    
    def test_wearing_clothing(self):
        """Test wearing clothing items."""
        # Initially not worn
        self.assertFalse(self.cloak.db.worn)
        
        # Wear the cloak
        self.cloak.wear(self.char, True)
        self.assertTrue(self.cloak.db.worn)
        
        # Check it's in worn items
        worn = self.char.get_worn_clothes()
        self.assertIn(self.cloak, worn)
    
    def test_removing_clothing(self):
        """Test removing worn clothing."""
        # Wear then remove
        self.cloak.wear(self.char, True)
        self.cloak.remove(self.char)
        
        self.assertFalse(self.cloak.db.worn)
        worn = self.char.get_worn_clothes()
        self.assertNotIn(self.cloak, worn)
    
    def test_clothing_stat_modifiers(self):
        """Test stat modifiers from clothing."""
        # Check base constitution
        base_con = self.char.stats.constitution.value
        
        # Wear cloak with +1 CON
        self.cloak.wear(self.char, True)
        
        # Verify modifier was applied
        self.assertEqual(self.char.stats.constitution.mod, 1)
        self.assertEqual(self.char.stats.constitution.value, base_con + 1)
        
        # Remove and verify modifier removed
        self.cloak.remove(self.char)
        self.assertEqual(self.char.stats.constitution.mod, 0)
        self.assertEqual(self.char.stats.constitution.value, base_con)
    
    def test_multiple_clothing_modifiers(self):
        """Test multiple items providing stat bonuses."""
        # Create gloves with STR bonus
        gloves = create.create_object(WorkGloves, key="test_gloves", location=self.char)
        
        # Wear both items
        self.cloak.wear(self.char, True)
        gloves.wear(self.char, True)
        
        # Check both modifiers applied
        self.assertEqual(self.char.stats.constitution.mod, 1)  # From cloak
        self.assertEqual(self.char.stats.strength.mod, 1)      # From gloves
    
    def test_warmth_calculation(self):
        """Test total warmth calculation."""
        # No warmth when naked
        self.assertEqual(self.char.get_total_warmth(), 0)
        
        # Wear cloak
        self.cloak.wear(self.char, True)
        self.assertEqual(self.char.get_total_warmth(), 25)
        
        # Wear boots too
        self.boots.wear(self.char, True)
        self.assertEqual(self.char.get_total_warmth(), 30)  # 25 + 5
    
    def test_weather_protection(self):
        """Test weather protection detection."""
        # No protection initially
        self.assertFalse(self.char.has_weather_protection("rain"))
        self.assertFalse(self.char.has_weather_protection("snow"))
        
        # Wear cloak
        self.cloak.wear(self.char, True)
        
        # Now protected from rain, snow, wind
        self.assertTrue(self.char.has_weather_protection("rain"))
        self.assertTrue(self.char.has_weather_protection("snow"))
        self.assertTrue(self.char.has_weather_protection("wind"))
        
        # But not from made-up weather
        self.assertFalse(self.char.has_weather_protection("acid_rain"))
    
    def test_clothing_durability(self):
        """Test clothing condition system."""
        # Start at max durability
        self.assertEqual(self.cloak.db.durability, 100)
        self.assertEqual(self.cloak.db.max_durability, 100)
        
        # Damage it
        self.cloak.db.durability = 50
        condition = self.cloak.get_condition_string()
        self.assertIn("worn but serviceable", condition)
        
        # Damage more
        self.cloak.db.durability = 10
        condition = self.cloak.get_condition_string()
        self.assertIn("badly damaged", condition)
    
    def test_clothing_type_limits(self):
        """Test that clothing type limits are enforced."""
        # Create multiple hats
        hat1 = create.create_object(WoolenHat, key="hat 1", location=self.char)
        hat2 = create.create_object(WoolenHat, key="hat 2", location=self.char)
        
        # Wear first hat - should work
        hat1.wear(self.char, True)
        self.assertTrue(hat1.db.worn)
        
        # Try to wear second hat - should respect limit
        # (This would be enforced by the command, not the object)
        # Just verify we can check the count
        from evennia.contrib.game_systems.clothing.clothing import single_type_count
        worn = self.char.get_worn_clothes()
        hat_count = single_type_count(worn, "hat")
        self.assertEqual(hat_count, 1)
    
    def test_clothing_covering(self):
        """Test clothing covering mechanics."""
        # Create undershirt and top
        undershirt = create.create_object(SurvivalClothing, key="test_undershirt", location=self.char)
        undershirt.db.clothing_type = "undershirt"
        top = create.create_object(SurvivalClothing, key="test_top", location=self.char)
        top.db.clothing_type = "top"
        
        # Wear undershirt first
        undershirt.wear(self.char, True)
        
        # Wear top - should auto-cover undershirt
        top.wear(self.char, True)
        
        # Check covering
        self.assertEqual(undershirt.db.covered_by, top)
        
        # Covered items shouldn't show in description
        visible_worn = self.char.get_worn_clothes(exclude_covered=True)
        self.assertIn(top, visible_worn)
        self.assertNotIn(undershirt, visible_worn)
    
    # I test_clothing.py, uppdatera test_dropped_clothing_visibility metoden:

    def test_dropped_clothing_visibility(self):
        """Test that dropped clothing has appropriate visibility."""
        # Create various clothing items
        cloak = create.create_object(WinterCloak, key="test_cloak_vis", location=self.char)
        hat = create.create_object(WoolenHat, key="test_hat_vis", location=self.char)
        goggles = create.create_object(EngineeringGoggles, key="test_goggles_vis", location=self.char)
    
        # Check visibility properties are set
        self.assertEqual(cloak.db.visibility_size, "large")  # Easy to spot
        self.assertEqual(hat.db.visibility_size, "small")    # Harder to see
        self.assertEqual(goggles.db.luminosity, "shiny")     # Catches light
    
        # Drop them in a room
        cloak.move_to(self.room1)
        hat.move_to(self.room1)
        goggles.move_to(self.room1)
    
        # Test visibility calculations
        # FIX: Anropa calculate_object_visibility på ROOM objektet, inte character
        cloak_vis = self.room1.calculate_object_visibility(cloak, self.char1)
        hat_vis = self.room1.calculate_object_visibility(hat, self.char1)
    
        # Large cloak should be more visible than small hat
        self.assertGreater(cloak_vis, hat_vis)
    
    def test_worn_clothing_not_visible_in_room(self):
        """Test that worn clothing doesn't show in room contents."""
        cloak = create.create_object(WinterCloak, key="test_worn_cloak", location=self.char)
        
        # When worn, should not appear in room's visible objects
        cloak.wear(self.char, True)
        visible_objects = self.room1.get_visible_objects(self.char)
        self.assertNotIn(cloak, visible_objects)
    
    def test_special_clothing_properties(self):
        """Test special properties of specific clothing types."""
        # Test engineering goggles
        goggles = create.create_object(EngineeringGoggles, key="test_eng_goggles", location=self.char)
        self.assertEqual(goggles.db.stat_modifiers.get("intelligence"), 2)
        self.assertEqual(goggles.db.engineering_bonus, 10)
        self.assertEqual(goggles.db.luminosity, "shiny")
        
        # Test work gloves
        gloves = create.create_object(WorkGloves, key="test_work_gloves", location=self.char)
        self.assertEqual(gloves.db.crafting_bonus, 5)
        
        # Test decorative scarf
        scarf = create.create_object(DecorativeScarf, key="test_scarf", location=self.char)
        self.assertEqual(scarf.db.stat_modifiers.get("charisma"), 1)
        self.assertEqual(scarf.db.contrast, "bright")
    
    def test_camouflage_clothing(self):
        """Test camouflage clothing properties."""
        camo_cloak = create.create_object(CamouflageCloak, key="test_camo_cloak", location=self.char)
        
        # Check camouflage properties
        self.assertEqual(camo_cloak.db.contrast, "camouflaged")
        self.assertEqual(camo_cloak.db.camouflage_type, "natural")
        self.assertEqual(camo_cloak.db.stealth_bonus, 20)
        
        # Test visibility when dropped in appropriate environment
        forest_room = create.create_object(Room, key="Forest")
        forest_room.db.desc = "A dense forest with thick undergrowth."
        camo_cloak.move_to(forest_room)
        
        # Should be harder to see in forest
        visibility = forest_room.calculate_object_visibility(camo_cloak, self.char)
        self.assertLess(visibility, 0.5)  # Hard to spot
    
    def test_at_drop_removes_worn_clothing(self):
        """Test that dropping worn clothing removes it."""
        # Wear the cloak
        self.cloak.wear(self.char, True)
        self.assertTrue(self.cloak.db.worn)
        
        # Drop it
        self.cloak.at_drop(self.char)
        
        # Should no longer be worn
        self.assertFalse(self.cloak.db.worn)
        self.assertNotIn(self.cloak, self.char.get_worn_clothes())
    
    def test_clothing_appearance(self):
        """Test clothing appearance shows condition and benefits."""
        # Check appearance includes benefits
        appearance = self.cloak.return_appearance(self.char)
        
        # Should show warmth
        self.assertIn("warmth", appearance.lower())
        self.assertIn("25", appearance)
        
        # Should show weather protection
        self.assertIn("protects against", appearance.lower())
        self.assertIn("snow", appearance.lower())
        
        # Should show stat modifiers
        self.assertIn("constitution +1", appearance.lower())
        
        # Damage it and check condition shows
        self.cloak.db.durability = 30
        appearance = self.cloak.return_appearance(self.char)
        self.assertIn("well-worn and fraying", appearance.lower())


class TestEnvironmentalEffects(EvenniaTest):
    """Test environmental effects on characters based on clothing."""
    
    def setUp(self):
        super().setUp()
        self.room = create.create_object(Room, key="Test Room")
        self.char = create.create_object(Character, key="TestChar", location=self.room)
        self.room.db.indoor = False
    
    def test_cold_weather_effects(self):
        """Test cold weather effects without protection."""
        with patch.object(self.room, 'get_season', return_value="winter"):
            with patch.object(self.room, 'get_current_weather', return_value=["snow"]):
                effects = self.room.get_environmental_effects(self.char)
                
                # Should have severe cold effects
                self.assertGreater(effects["fatigue_rate_mod"], 1.5)
                self.assertGreater(effects["health_drain"], 0)
                self.assertTrue(any("freezing" in msg for msg in effects["messages"]))
    
    def test_cold_weather_with_protection(self):
        """Test cold weather with warm clothing."""
        # Give character warm clothes
        cloak = create.create_object(WinterCloak, key="test_cold_cloak", location=self.char)
        cloak.wear(self.char, True)
        
        with patch.object(self.room, 'get_season', return_value="winter"):
            with patch.object(self.room, 'get_current_weather', return_value=["clear"]):
                effects = self.room.get_environmental_effects(self.char)
                
                # Should have minimal effects with 25 warmth
                self.assertLess(effects["fatigue_rate_mod"], 1.3)
                self.assertEqual(effects["health_drain"], 0)
    
    def test_rain_without_protection(self):
        """Test rain effects without rain gear."""
        with patch.object(self.room, 'get_season', return_value="spring"):
            with patch.object(self.room, 'get_current_weather', return_value=["rain"]):
                effects = self.room.get_environmental_effects(self.char)
                
                # Should increase fatigue from being wet
                self.assertGreater(effects["fatigue_rate_mod"], 1.0)
                self.assertTrue(any("wet" in msg for msg in effects["messages"]))
    
    def test_rain_with_protection(self):
        """Test rain with proper rain gear."""
        # Give character raincoat
        raincoat = create.create_object(RainCoat, key="test_raincoat", location=self.char)
        raincoat.wear(self.char, True)
        
        with patch.object(self.room, 'get_season', return_value="spring"):
            with patch.object(self.room, 'get_current_weather', return_value=["rain"]):
                effects = self.room.get_environmental_effects(self.char)
                
                # Should have no rain effects
                self.assertEqual(effects["fatigue_rate_mod"], 1.0)
                self.assertFalse(any("wet" in msg for msg in effects["messages"]))
    
    def test_overheating_in_summer(self):
        """Test wearing too much in hot weather."""
        # Wear heavy winter gear
        cloak = create.create_object(WinterCloak, key="test_summer_cloak", location=self.char)
        cloak.wear(self.char, True)
        
        with patch.object(self.room, 'get_season', return_value="summer"):
            with patch.object(self.room, 'get_time_of_day', return_value="noon"):
                effects = self.room.get_environmental_effects(self.char)
                
                # Should increase thirst and fatigue
                self.assertGreater(effects["thirst_rate_mod"], 1.0)
                self.assertGreater(effects["fatigue_rate_mod"], 1.0)
                # Check for any heat-related message
                self.assertTrue(any("heat" in msg.lower() or "overheat" in msg.lower() or "sweat" in msg.lower() 
                                  for msg in effects["messages"]))
    
    def test_indoor_protection(self):
        """Test that indoor rooms protect from weather."""
        self.room.db.indoor = True
        
        with patch.object(self.room, 'get_season', return_value="winter"):
            with patch.object(self.room, 'get_current_weather', return_value=["storm"]):
                effects = self.room.get_environmental_effects(self.char)
                
                # Should have no weather effects indoors
                self.assertEqual(effects["fatigue_rate_mod"], 1.0)
                self.assertEqual(effects["health_drain"], 0)
                self.assertEqual(len(effects["messages"]), 0)
    
    def test_layered_protection(self):
        """Test multiple layers of clothing provide cumulative warmth."""
        # Wear multiple items
        hat = create.create_object(WoolenHat, key="test_layer_hat", location=self.char)
        cloak = create.create_object(WinterCloak, key="test_layer_cloak", location=self.char)
        boots = create.create_object(LeatherBoots, key="test_layer_boots", location=self.char)
        gloves = create.create_object(WorkGloves, key="test_layer_gloves", location=self.char)
        
        hat.wear(self.char, True)
        cloak.wear(self.char, True)
        boots.wear(self.char, True)
        gloves.wear(self.char, True)
        
        # Total warmth should be sum of all
        total_warmth = self.char.get_total_warmth()
        expected = 8 + 25 + 5 + 3  # hat + cloak + boots + gloves
        self.assertEqual(total_warmth, expected)
        
        # Should be well protected in winter
        with patch.object(self.room, 'get_season', return_value="winter"):
            with patch.object(self.room, 'get_current_weather', return_value=["snow"]):
                effects = self.room.get_environmental_effects(self.char)
                
                # Should have no cold effects with 41 warmth
                self.assertEqual(effects["fatigue_rate_mod"], 1.0)
                self.assertEqual(effects["health_drain"], 0)
    
    def test_wind_protection(self):
        """Test wind effects and protection."""
        with patch.object(self.room, 'get_season', return_value="winter"):
            with patch.object(self.room, 'get_current_weather', return_value=["wind"]):
                # Without protection
                effects = self.room.get_environmental_effects(self.char)
                self.assertGreater(effects["fatigue_rate_mod"], 1.0)
                self.assertTrue(any("wind" in msg for msg in effects["messages"]))
                
                # With wind protection
                cloak = create.create_object(WinterCloak, key="test_wind_cloak", location=self.char)
                cloak.wear(self.char, True)
                effects = self.room.get_environmental_effects(self.char)
                # Still cold but wind doesn't add extra penalty
                self.assertLess(effects["fatigue_rate_mod"], 2.0)
    
    def test_storm_conditions(self):
        """Test severe storm combines multiple effects."""
        with patch.object(self.room, 'get_season', return_value="winter"):
            with patch.object(self.room, 'get_current_weather', return_value=["storm"]):
                effects = self.room.get_environmental_effects(self.char)
                
                # Storm in winter should be very harsh
                self.assertGreater(effects["fatigue_rate_mod"], 1.5)
                self.assertGreater(effects["health_drain"], 0)
                
                # Full protection gear
                raincoat = create.create_object(RainCoat, key="test_storm_raincoat", location=self.char)
                cloak = create.create_object(WinterCloak, key="test_storm_cloak", location=self.char)
                raincoat.wear(self.char, True)
                cloak.wear(self.char, True)
                
                effects = self.room.get_environmental_effects(self.char)
                # Should be mostly protected
                self.assertLess(effects["fatigue_rate_mod"], 1.5)


class TestClothingCommands(EvenniaTest):
    """Test clothing-related commands."""
    
    def setUp(self):
        super().setUp()
        self.char = create.create_object(Character, key="Tester", location=self.room1)
        self.cloak = create.create_object(WinterCloak, key="cloak", location=self.char)
        
        # Add command set to character
        from commands.default_cmdsets import CharacterCmdSet
        self.char.cmdset.add(CharacterCmdSet)
    
    def test_wear_command(self):
        """Test the wear command."""
        # Execute wear command
        self.char.execute_cmd("wear cloak")
        
        # Check that cloak is worn
        self.assertTrue(self.cloak.db.worn)
        
        # Test with style
        self.char.execute_cmd("wear cloak = draped dramatically")
        self.assertEqual(self.cloak.db.worn, "draped dramatically")
    
    def test_remove_command(self):
        """Test the remove command."""
        # First wear the cloak
        self.cloak.wear(self.char, True)
        self.assertTrue(self.cloak.db.worn)
        
        # Now remove it
        self.char.execute_cmd("remove cloak")
        self.assertFalse(self.cloak.db.worn)
    
    def test_clothing_status_command(self):
        """Test the clothing status command."""
        # Wear some items
        self.cloak.wear(self.char, True)
        boots = create.create_object(LeatherBoots, key="test_boots", location=self.char)
        boots.wear(self.char, True)
        
        self.char.execute_cmd("clothing status")
        # Command should execute without error
        # (actual output testing would require capturing messages)
    
    def test_repair_command_basics(self):
        """Test basic repair command functionality."""
        # Damage the cloak
        self.cloak.db.durability = 50
        
        # Try to repair without materials
        self.char.execute_cmd("repair cloak")
        # Should fail due to lack of materials
        
        # Give character required crafting skill
        self.char.skills.crafting.base = 30
        
        # Try again (still no materials)
        self.char.execute_cmd("repair cloak")
        # Should still fail but for different reason
    
    def test_inventory_shows_worn_items(self):
        """Test that inventory separates worn and carried items."""
        # Have some worn and some carried items
        self.cloak.wear(self.char, True)
        
        carried_item = create.create_object("typeclasses.objects.Object", 
                                          key="backpack", 
                                          location=self.char)
        
        self.char.execute_cmd("inventory")
        # Should show both worn and carried sections
        # (actual output testing would require message capture)
    
    def test_cover_command(self):
        """Test covering clothing with other clothing."""
        # Create items that can cover each other
        shirt = create.create_object(SurvivalClothing, key="shirt", location=self.char)
        shirt.db.clothing_type = "top"
        jacket = create.create_object(SurvivalClothing, key="jacket", location=self.char)
        jacket.db.clothing_type = "outerwear"
        
        # Wear shirt first
        shirt.wear(self.char, True)
        self.assertTrue(shirt.db.worn)
        
        # The cover command should handle wearing the jacket
        # But we need to test the actual command behavior
        # For now, wear the jacket manually before covering
        jacket.wear(self.char, True)
        
        # Now use cover command
        self.char.execute_cmd("cover shirt with jacket")
        
        # Verify shirt is covered by jacket
        self.assertEqual(shirt.db.covered_by, jacket)
    
    def test_uncover_command(self):
        """Test uncovering clothing."""
        # Setup covered clothing
        shirt = create.create_object(SurvivalClothing, key="shirt", location=self.char)
        shirt.db.clothing_type = "top"
        jacket = create.create_object(SurvivalClothing, key="jacket", location=self.char)
        jacket.db.clothing_type = "outerwear"
        
        shirt.wear(self.char, True)
        jacket.wear(self.char, True)
        shirt.db.covered_by = jacket
        
        # Uncover the shirt
        self.char.execute_cmd("uncover shirt")
        
        # Should no longer be covered
        self.assertIsNone(shirt.db.covered_by)
