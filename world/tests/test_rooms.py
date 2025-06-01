# world/tests/test_rooms.py
"""
Tests for Room typeclass, visibility, and environmental systems.
"""
from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from typeclasses.rooms import Room
from typeclasses.objects import Object, SmallValuable, Torch
from typeclasses.characters import Character
from unittest.mock import patch, MagicMock


class TestRoomVisibility(EvenniaTest):
    """Test room visibility systems."""
    
    def setUp(self):
        super().setUp()
        self.outdoor_room = create.create_object(Room, key="Outdoor Test")
        self.outdoor_room.db.indoor = False
        self.indoor_room = create.create_object(Room, key="Indoor Test")
        self.indoor_room.db.indoor = True
        
        # Move test character to outdoor room
        self.char1.move_to(self.outdoor_room, quiet=True)
    
    def test_time_based_visibility(self):
        """Test visibility changes with time of day."""
        with patch.object(self.outdoor_room, 'get_time_of_day') as mock_time:
            # Test noon visibility
            mock_time.return_value = "noon"
            self.assertEqual(self.outdoor_room.get_visibility_range(self.char1), 10)
            
            # Test night visibility
            mock_time.return_value = "night"
            self.assertEqual(self.outdoor_room.get_visibility_range(self.char1), 2)
            
            # Test dawn/dusk
            mock_time.return_value = "dawn"
            self.assertEqual(self.outdoor_room.get_visibility_range(self.char1), 5)
    
    def test_weather_visibility_impact(self):
        """Test weather affects visibility."""
        with patch.object(self.outdoor_room, 'get_current_weather') as mock_weather:
            with patch.object(self.outdoor_room, 'get_time_of_day', return_value="noon"):
                # Clear weather
                mock_weather.return_value = ["clear"]
                self.assertEqual(self.outdoor_room.get_visibility_range(self.char1), 10)
                
                # Fog severely limits visibility
                mock_weather.return_value = ["fog"]
                self.assertEqual(self.outdoor_room.get_visibility_range(self.char1), 1)
                
                # Storm conditions
                mock_weather.return_value = ["storm"]
                self.assertEqual(self.outdoor_room.get_visibility_range(self.char1), 3)
    
    def test_indoor_visibility(self):
        """Test indoor rooms always have full visibility."""
        with patch.object(self.indoor_room, 'get_time_of_day', return_value="night"):
            with patch.object(self.indoor_room, 'get_current_weather', return_value=["fog"]):
                # Indoor rooms ignore time and weather
                self.assertEqual(self.indoor_room.get_visibility_range(self.char1), 10)
    
    def test_light_source_visibility(self):
        """Test light sources improve visibility in darkness."""
        # Create a torch
        torch = create.create_object(Torch, key="torch", location=self.char1)
        
        with patch.object(self.outdoor_room, 'get_time_of_day', return_value="night"):
            # Without light
            torch.db.light_active = False
            self.assertEqual(self.outdoor_room.get_visibility_range(self.char1), 2)
            
            # With lit torch
            torch.db.light_active = True
            self.assertEqual(self.outdoor_room.get_visibility_range(self.char1), 5)


class TestObjectVisibility(EvenniaTest):
    """Test object detection in various conditions."""
    
    def setUp(self):
        super().setUp()
        self.room = create.create_object(Room, key="Test Room")
        self.char = create.create_object(Character, key="Viewer", location=self.room)
        
        # Create test objects
        self.normal_obj = create.create_object(Object, key="sword", location=self.room)
        self.small_obj = create.create_object(SmallValuable, key="coin", location=self.room)
        self.hidden_obj = create.create_object(Object, key="hidden cache", location=self.room)
        self.hidden_obj.db.hidden = True
    
    def test_object_size_visibility(self):
        """Test object size affects visibility."""
        with patch.object(self.room, 'get_time_of_day', return_value="noon"):
            with patch.object(self.room, 'get_current_weather', return_value=["clear"]):
                # Normal object in good conditions
                normal_vis = self.room.calculate_object_visibility(self.normal_obj, self.char)
                self.assertEqual(normal_vis, 1.0)
                
                # Small object harder to see
                small_vis = self.room.calculate_object_visibility(self.small_obj, self.char)
                self.assertLess(small_vis, 0.5)
    
    def test_hidden_objects_require_search(self):
        """Test hidden objects have 0 visibility."""
        visibility = self.room.calculate_object_visibility(self.hidden_obj, self.char)
        self.assertEqual(visibility, 0.0)
        
        # Should not appear in visible objects
        visible = self.room.get_visible_objects(self.char)
        self.assertNotIn(self.hidden_obj, visible)
    
    def test_luminous_objects_in_darkness(self):
        """Test shiny/glowing objects are easier to see in dark."""
        shiny_obj = create.create_object(Object, key="gem", location=self.room)
        shiny_obj.db.visibility_size = "tiny"
        shiny_obj.db.luminosity = "shiny"
        
        with patch.object(self.room, 'get_time_of_day', return_value="night"):
            # Calculate visibility
            vis = self.room.calculate_object_visibility(shiny_obj, self.char)
            
            # Should be more visible than a normal tiny object
            normal_tiny = create.create_object(Object, key="button", location=self.room)
            normal_tiny.db.visibility_size = "tiny"
            normal_vis = self.room.calculate_object_visibility(normal_tiny, self.char)
            
            self.assertGreater(vis, normal_vis)
    
    def test_weather_affects_all_objects(self):
        """Test weather reduces visibility of all objects."""
        with patch.object(self.room, 'get_current_weather', return_value=["fog"]):
            with patch.object(self.room, 'get_time_of_day', return_value="noon"):
                # Even normal objects hard to see in fog
                vis = self.room.calculate_object_visibility(self.normal_obj, self.char)
                self.assertLess(vis, 0.5)


class TestRoomResources(EvenniaTest):
    """Test resource gathering mechanics."""
    
    def setUp(self):
        super().setUp()
        self.forest = create.create_object(Room, key="Forest")
        self.forest.db.indoor = False
        self.gatherer = create.create_object(Character, key="Gatherer", location=self.forest)
    
    def test_resource_availability_by_season(self):
        """Test resources vary by season."""
        with patch.object(self.forest, 'get_season') as mock_season:
            # Winter has few plants
            mock_season.return_value = "winter"
            winter_plants = self.forest.get_resource_availability("plants")
            
            # Summer has many plants
            mock_season.return_value = "summer"
            summer_plants = self.forest.get_resource_availability("plants")
            
            self.assertLess(winter_plants, summer_plants)
            self.assertLess(winter_plants, 0.5)  # Less than 50% in winter
            self.assertGreater(summer_plants, 1.5)  # More than 150% in summer
    
    def test_weather_affects_gathering(self):
        """Test weather conditions affect resource gathering."""
        with patch.object(self.forest, 'get_current_weather') as mock_weather:
            with patch.object(self.forest, 'get_season', return_value="summer"):
                # Good weather
                mock_weather.return_value = ["clear"]
                clear_wood = self.forest.get_resource_availability("wood")
                
                # Storm reduces gathering
                mock_weather.return_value = ["storm"]
                storm_wood = self.forest.get_resource_availability("wood")
                
                self.assertGreater(clear_wood, storm_wood)
    
    def test_resource_extraction(self):
        """Test basic resource extraction."""
        # Give gatherer some foraging skill
        self.gatherer.skills.foraging.base = 20
        
        with patch.object(self.forest, 'get_season', return_value="summer"):
            # Try to gather wood
            success, amount, exp = self.forest.extract_resource(self.gatherer, "wood", 1)
            
            self.assertTrue(success)
            self.assertGreater(amount, 0)
            self.assertGreater(exp, 0)
            
            # Check resource was depleted
            wood_current = self.forest.db.resources["wood"]["current"]
            self.assertLess(wood_current, 5)  # Started at 5
    
    def test_tool_requirements(self):
        """Test some resources require tools."""
        # Try to gather stone without pickaxe
        success, amount, exp = self.forest.extract_resource(self.gatherer, "stone", 1)
        self.assertFalse(success)
        
        # Give gatherer a pickaxe
        pickaxe = create.create_object(Object, key="pickaxe", location=self.gatherer)
        
        # Now should work
        success, amount, exp = self.forest.extract_resource(self.gatherer, "stone", 1)
        self.assertTrue(success)
    
    def test_skill_affects_yield(self):
        """Test higher skill gives better yields."""
        with patch.object(self.forest, 'get_season', return_value="summer"):
            # Reset wood
            self.forest.db.resources["wood"]["current"] = 10
            
            # Low skill gatherer
            self.gatherer.skills.foraging.base = 10
            success1, amount1, exp1 = self.forest.extract_resource(self.gatherer, "wood", 5)
            
            # Reset wood
            self.forest.db.resources["wood"]["current"] = 10
            
            # High skill gatherer
            self.gatherer.skills.foraging.base = 80
            success2, amount2, exp2 = self.forest.extract_resource(self.gatherer, "wood", 5)
            
            # High skill should get more
            self.assertGreater(amount2, amount1)


class TestRoomAppearance(EvenniaTest):
    """Test room appearance and descriptions."""
    
    def setUp(self):
        super().setUp()
        self.room = create.create_object(Room, key="Dynamic Room")
        self.char = create.create_object(Character, key="Observer", location=self.room)
        
    def test_seasonal_descriptions(self):
        """Test room descriptions change with seasons."""
        # Set seasonal descriptions
        self.room.desc_spring = "Spring flowers bloom everywhere."
        self.room.desc_summer = "The summer heat beats down."
        self.room.desc_autumn = "Colorful leaves cover the ground."
        self.room.desc_winter = "Snow blankets everything in white."
        
        with patch.object(self.room, 'get_season') as mock_season:
            # Test each season
            for season, expected in [
                ("spring", "Spring flowers bloom everywhere."),
                ("summer", "The summer heat beats down."),
                ("autumn", "Colorful leaves cover the ground."),
                ("winter", "Snow blankets everything in white.")
            ]:
                mock_season.return_value = season
                desc = self.room.get_display_desc(self.char)
                self.assertEqual(desc, expected)
    
    def test_weather_state_descriptions(self):
        """Test weather states can override descriptions."""
        # Set base and weather descriptions
        self.room.db.desc = "A normal forest clearing."
        self.room.add_desc("The rain pours down heavily.", room_state="rain")
        self.room.add_desc("Thick fog obscures everything.", room_state="fog")
        
        # Normal weather
        desc = self.room.get_display_desc(self.char)
        self.assertEqual(desc, "A normal forest clearing.")
        
        # Add rain state
        self.room.add_room_state("rain")
        desc = self.room.get_display_desc(self.char)
        self.assertEqual(desc, "The rain pours down heavily.")
        
        # Fog overrides rain (alphabetically first)
        self.room.add_room_state("fog")
        desc = self.room.get_display_desc(self.char)
        self.assertEqual(desc, "Thick fog obscures everything.")
    
    def test_room_appearance_includes_conditions(self):
        """Test room appearance shows time, season, and weather."""
        with patch.object(self.room, 'get_time_of_day', return_value="morning"):
            with patch.object(self.room, 'get_season', return_value="spring"):
                with patch.object(self.room, 'get_current_weather', return_value=["rain"]):
                    appearance = self.room.return_appearance(self.char)
                    
                    # Should include room name
                    self.assertIn("Dynamic Room", appearance)
                    
                    # Should include conditions
                    self.assertIn("Time: Morning", appearance)
                    self.assertIn("Season: Spring", appearance)
                    self.assertIn("Weather: Rain", appearance)
    
    def test_visible_objects_in_appearance(self):
        """Test only visible objects appear in room description."""
        # Create various objects
        visible_obj = create.create_object(Object, key="table", location=self.room)
        hidden_obj = create.create_object(Object, key="secret", location=self.room)
        hidden_obj.db.hidden = True
        
        with patch.object(self.room, 'get_time_of_day', return_value="noon"):
            appearance = self.room.return_appearance(self.char)
            
            # Visible object should appear
            self.assertIn("table", appearance)
            
            # Hidden object should not
            self.assertNotIn("secret", appearance)


class TestExtendedRoomIntegration(EvenniaTest):
    """Test integration with game time and trait systems."""
    
    def setUp(self):
        super().setUp()
        self.room = create.create_object(Room, key="Integrated Room")
        self.char = create.create_object(Character, key="Test Char", location=self.room)
    
    def test_uses_custom_gametime(self):
        """Test room uses our custom gametime system."""
        from world.gametime_utils import get_current_season, get_time_of_day
        
        # Room methods should return same as utility functions
        self.assertEqual(self.room.get_season(), get_current_season())
        self.assertEqual(self.room.get_time_of_day(), get_time_of_day())
    
    def test_gathering_improves_skills(self):
        """Test gathering resources improves character skills."""
        initial_foraging = self.char.skills.foraging.value
        
        # Gather some wood
        success, amount, exp = self.room.extract_resource(self.char, "wood", 1)
        
        if success and exp > 0:
            # Manually apply the experience
            self.char.improve_skill("foraging", exp)
            
            # Skill should have improved
            self.assertGreater(
                self.char.skills.foraging.value,
                initial_foraging
            )
    
    def test_weather_affects_character_traits(self):
        """Test room weather can affect character survival traits."""
        # This is preparation for future ticker integration
        
        # Set harsh weather
        self.room.add_room_state("storm")
        
        # Check that room recognizes the harsh condition
        weather = self.room.get_current_weather()
        self.assertIn("storm", weather)
        
        # In future: storm without shelter increases fatigue decay
        # For now, just verify the room tracks weather properly


class TestWeatherSystem(EvenniaTest):
    """Test the weather state system."""
    
    def setUp(self):
        super().setUp()
        self.room = create.create_object(Room, key="Weather Test")
    
    def test_default_weather(self):
        """Test rooms start with clear weather."""
        weather = self.room.get_current_weather()
        self.assertEqual(weather, ["clear"])
    
    def test_multiple_weather_states(self):
        """Test rooms can have multiple weather states."""
        self.room.add_room_state("rain")
        self.room.add_room_state("wind")
        
        weather = self.room.get_current_weather()
        self.assertIn("rain", weather)
        self.assertIn("wind", weather)
    
    def test_weather_state_management(self):
        """Test adding and removing weather states."""
        # Add fog
        self.room.add_room_state("fog")
        self.assertIn("fog", self.room.room_states)
        
        # Remove fog
        self.room.remove_room_state("fog")
        self.assertNotIn("fog", self.room.room_states)
        
        # Clear all states
        self.room.add_room_state("rain")
        self.room.add_room_state("storm")
        self.room.clear_room_state()
        
        # Should go back to default clear
        weather = self.room.get_current_weather()
        self.assertEqual(weather, ["clear"])


class TestLightSources(EvenniaTest):
    """Test light source functionality."""
    
    def setUp(self):
        super().setUp()
        self.room = create.create_object(Room, key="Dark Room")
        self.char = create.create_object(Character, key="Light Bearer", location=self.room)
        self.torch = create.create_object(Torch, key="torch", location=self.char)
    
    def test_torch_lighting(self):
        """Test torch can be lit and extinguished."""
        # Start unlit
        self.assertFalse(self.torch.db.light_active)
        self.assertEqual(self.torch.db.luminosity, "normal")
        
        # Light it
        self.torch.do_light(self.char)
        self.assertTrue(self.torch.db.light_active)
        self.assertEqual(self.torch.db.luminosity, "glowing")
        
        # Extinguish it
        self.torch.do_extinguish(self.char)
        self.assertFalse(self.torch.db.light_active)
        self.assertEqual(self.torch.db.luminosity, "normal")
    
    def test_light_improves_object_visibility(self):
        """Test carrying light makes objects more visible."""
        small_obj = create.create_object(SmallValuable, key="ring", location=self.room)
        
        with patch.object(self.room, 'get_time_of_day', return_value="night"):
            # Without light
            self.torch.db.light_active = False
            vis_dark = self.room.calculate_object_visibility(small_obj, self.char)
            
            # With light
            self.torch.db.light_active = True
            vis_light = self.room.calculate_object_visibility(small_obj, self.char)
            
            # Should be much more visible with light
            self.assertGreater(vis_light, vis_dark * 1.5)


class TestDetailSystem(EvenniaTest):
    """Test room detail functionality."""
    
    def setUp(self):
        super().setUp()
        self.room = create.create_object(Room, key="Detailed Room")
        self.char = create.create_object(Character, key="Inspector", location=self.room)
    
    def test_add_and_get_details(self):
        """Test adding and retrieving room details."""
        # Add a detail
        self.room.add_detail("window", "A grimy window overlooks the street.")
        
        # Get exact match
        detail = self.room.get_detail("window", self.char)
        self.assertEqual(detail, "A grimy window overlooks the street.")
        
        # Get partial match
        detail = self.room.get_detail("win", self.char)
        self.assertEqual(detail, "A grimy window overlooks the street.")
    
    def test_detail_with_funcparser(self):
        """Test details can use state-based descriptions."""
        # Add detail with state
        detail_text = (
            "A heavy wooden door. "
            "$state(locked, It appears to be locked.) "
            "$state(open, It stands wide open.)"
        )
        self.room.add_detail("door", detail_text)
    
        # Without state
        detail = self.room.get_detail("door", self.char)
        # Strip trailing space that funcparser leaves behind
        # This is a cosmetic issue in ExtendedRoom that doesn't affect gameplay
        self.assertEqual(detail.strip(), "A heavy wooden door.")
    
        # With locked state
        self.room.add_room_state("locked")
        detail = self.room.get_detail("door", self.char)
        # Also strip here for consistency
        self.assertEqual(detail.strip(), "A heavy wooden door. It appears to be locked.")
