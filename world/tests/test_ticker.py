# world/tests/test_ticker.py
"""
Tests for TickerHandler integration and automation systems.
"""
from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from evennia import TICKER_HANDLER
from typeclasses.rooms import Room
from typeclasses.characters import Character
from typeclasses.objects import Object
from unittest.mock import patch, MagicMock
from world.scripts import (
    update_all_survival,
    update_global_weather,
    regenerate_resources,
    check_food_spoilage,
    check_seasonal_events,
    update_steam_engines,
    get_environmental_effects,
    generate_weather_for_season
)
from django.conf import settings
import datetime


class TestTickerSetup(EvenniaTest):
    """Test ticker initialization and setup."""
    
    def setUp(self):
        super().setUp()
        # Clear any existing tickers
        TICKER_HANDLER.clear()
    
    def tearDown(self):
        # Clean up tickers after each test
        TICKER_HANDLER.clear()
        super().tearDown()
    
    def test_ticker_initialization(self):
        """Test that all tickers can be initialized."""
        from world.scripts import initialize_all_tickers
        
        # Initialize tickers
        initialize_all_tickers()
        
        # Check that tickers were created
        all_tickers = TICKER_HANDLER.all()
        self.assertGreater(len(all_tickers), 0)
        
        # Verify expected ticker IDs exist
        ticker_ids = []
        for ticker_key, (store_key, ticker_obj) in all_tickers.items():
            if hasattr(ticker_obj, 'idstring'):
                ticker_ids.append(ticker_obj.idstring)
        
        expected_ids = [
            "survival_update",
            "weather_update",
            "resource_regen",
            "food_spoilage",
            "seasonal_events",
            "engine_fuel"
        ]
        
        for expected_id in expected_ids:
            self.assertIn(expected_id, ticker_ids)


class TestSurvivalTicker(EvenniaTest):
    """Test survival update ticker functionality."""
    
    def setUp(self):
        super().setUp()
        self.room = create.create_object(Room, key="Test Room")
        self.char = create.create_object(Character, key="Test Char", location=self.room)
        
        # Mock session to simulate online character
        self.mock_session = MagicMock()
        self.mock_session.puppet = self.char
    
    @patch('world.scripts.SESSIONS.get_sessions')
    def test_survival_update(self, mock_get_sessions):
        """Test that survival update processes online characters."""
        mock_get_sessions.return_value = [self.mock_session]
        
        # Set initial trait values
        self.char.traits.hunger.current = 100
        self.char.traits.thirst.current = 100
        self.char.traits.fatigue.current = 100
        
        # Run update
        update_all_survival()
        
        # Verify character was processed
        mock_get_sessions.assert_called_once()
    
    def test_environmental_effects_calculation(self):
        """Test environmental effect calculations."""
        # Test winter night effects
        with patch('world.scripts.gametime.gametime') as mock_time:
            # Mock winter night
            mock_time.return_value.month = 11  # Winter month
            mock_time.return_value.hour = 2    # Night time
            
            effects = get_environmental_effects(self.char)
            
            # Should have cold effects
            self.assertGreater(effects['fatigue_rate_mod'], 1.0)
            self.assertIn("cold", " ".join(effects['messages']).lower())
    
    def test_clothing_protection(self):
        """Test that clothing provides environmental protection."""
        # Create warm clothing
        coat = create.create_object(Object, key="Warm Coat")
        coat.db.warmth = 25
        coat.db.weather_protection = ["rain", "wind", "snow"]
        
        # Mock character wearing the coat
        with patch.object(self.char, 'clothing') as mock_clothing:
            mock_clothing.all.return_value = [coat]
            
            # Test winter protection
            with patch('world.scripts.gametime.gametime') as mock_time:
                mock_time.return_value.month = 11  # Winter
                mock_time.return_value.hour = 2    # Night
                
                effects = get_environmental_effects(self.char)
                
                # Should have reduced or no cold effects due to warm coat
                self.assertLess(effects['fatigue_rate_mod'], 2.0)


class TestWeatherTicker(EvenniaTest):
    """Test weather update ticker functionality."""
    
    def setUp(self):
        super().setUp()
        self.outdoor_room = create.create_object(Room, key="Outdoor")
        self.outdoor_room.db.indoor = False
        self.indoor_room = create.create_object(Room, key="Indoor")
        self.indoor_room.db.indoor = True
    
    def test_weather_generation(self):
        """Test weather generation for different seasons."""
        # Test winter weather
        winter_weather = generate_weather_for_season("winter")
        self.assertIsInstance(winter_weather, list)
        self.assertTrue(any(w in ["clear", "cloudy", "snow", "fog", "storm"] 
                          for w in winter_weather))
        
        # Test summer weather
        summer_weather = generate_weather_for_season("summer")
        self.assertIsInstance(summer_weather, list)
    
    @patch('world.scripts.gametime.gametime')
    @patch('world.scripts.ObjectDB')
    def test_weather_update_outdoor_only(self, mock_db, mock_time):
        """Test that weather only updates outdoor rooms."""
        # Mock current time for season
        mock_time.return_value.month = 5  # Summer
        
        # Mock database query
        mock_db.objects.filter.return_value = [self.outdoor_room, self.indoor_room]
        
        # Run weather update
        update_global_weather()
        
        # Outdoor room should have weather
        self.assertIsNotNone(self.outdoor_room.db.weather)
        
        # Indoor room should not change
        self.assertIsNone(self.indoor_room.db.weather)


class TestResourceTicker(EvenniaTest):
    """Test resource regeneration ticker."""
    
    def setUp(self):
        super().setUp()
        self.room = create.create_object(Room, key="Forest")
        self.room.tags.add("has_resources")
        
        # Set up resource nodes
        self.room.db.resource_nodes = {
            "berries": {
                "max_amount": 10,
                "current_amount": 2,
                "regen_rate": 3,
                "resource_type": "berries"
            },
            "herbs": {
                "max_amount": 5,
                "current_amount": 0,
                "regen_rate": 1,
                "resource_type": "herbs"
            }
        }
    
    @patch('world.scripts.ObjectDB')
    def test_resource_regeneration(self, mock_db):
        """Test that resources regenerate correctly."""
        mock_db.objects.filter.return_value = [self.room]
        
        # Run regeneration
        regenerate_resources()
        
        # Check berries regenerated
        berries = self.room.db.resource_nodes["berries"]
        self.assertEqual(berries["current_amount"], 5)  # 2 + 3
        
        # Check herbs regenerated
        herbs = self.room.db.resource_nodes["herbs"]
        self.assertEqual(herbs["current_amount"], 1)  # 0 + 1
    
    @patch('world.scripts.ObjectDB')
    def test_resource_max_cap(self, mock_db):
        """Test that resources don't exceed maximum."""
        # Set berries near max
        self.room.db.resource_nodes["berries"]["current_amount"] = 9
        
        mock_db.objects.filter.return_value = [self.room]
        
        # Run regeneration
        regenerate_resources()
        
        # Should cap at max
        berries = self.room.db.resource_nodes["berries"]
        self.assertEqual(berries["current_amount"], 10)  # Capped at max


class TestFoodSpoilageTicker(EvenniaTest):
    """Test food spoilage ticker."""
    
    def setUp(self):
        super().setUp()
        self.fresh_food = create.create_object(Object, key="Fresh Bread")
        self.fresh_food.tags.add("food", category="item_type")
        self.fresh_food.db.freshness = 100
        self.fresh_food.db.decay_rate = 25
    
    @patch('world.scripts.ObjectDB')
    def test_food_decay(self, mock_db):
        """Test that food freshness decreases."""
        mock_db.objects.filter.return_value = [self.fresh_food]
        
        # Run spoilage check
        check_food_spoilage()
        
        # Freshness should decrease
        self.assertEqual(self.fresh_food.db.freshness, 75)  # 100 - 25
    
    @patch('world.scripts.ObjectDB')
    def test_food_spoilage_stages(self, mock_db):
        """Test food spoilage state transitions."""
        # Set food to near spoilage
        self.fresh_food.db.freshness = 60
        self.fresh_food.db.desc = "A fresh loaf of bread"
        
        mock_db.objects.filter.return_value = [self.fresh_food]
        
        # First decay - should become stale
        check_food_spoilage()
        self.assertEqual(self.fresh_food.db.freshness, 35)
        self.assertIn("stale", self.fresh_food.db.desc)
        
        # Continue decay until spoiled
        self.fresh_food.db.freshness = 20
        check_food_spoilage()
        
        # Should be completely spoiled
        self.assertEqual(self.fresh_food.db.freshness, 0)
        self.assertTrue(self.fresh_food.tags.has("spoiled", category="quality"))


class TestSeasonalTicker(EvenniaTest):
    """Test seasonal event ticker."""
    
    @patch('world.scripts.gametime.gametime')
    @patch('world.scripts.SESSIONS.get_sessions')
    def test_season_change_announcement(self, mock_sessions, mock_time):
        """Test season change announcements."""
        # Mock first day of winter
        mock_time.return_value.month = 11
        mock_time.return_value.day = 1
        
        # Mock online player
        mock_session = MagicMock()
        mock_sessions.return_value = [mock_session]
        
        # Run seasonal check
        check_seasonal_events()
        
        # Should announce winter
        mock_session.puppet.msg.assert_called()
        call_args = str(mock_session.puppet.msg.call_args)
        self.assertIn("Winter", call_args)
    
    def test_seasonal_resource_modifiers(self):
        """Test that seasonal modifiers are applied to resources."""
        from world.scripts import update_seasonal_resources
        
        # Create test room with resources
        room = create.create_object(Room, key="Test Forest")
        room.tags.add("has_resources")
        room.db.resource_nodes = {
            "berries": {
                "base_max_amount": 10,
                "max_amount": 10,
                "resource_type": "berries"
            }
        }
        
        with patch('world.scripts.ObjectDB') as mock_db:
            mock_db.objects.filter.return_value = [room]
            
            # Apply winter modifiers
            update_seasonal_resources("winter")
            
            # Berries should be very rare in winter (0.1 modifier)
            self.assertEqual(room.db.resource_nodes["berries"]["max_amount"], 1)
            
            # Apply summer modifiers
            update_seasonal_resources("summer")
            
            # Berries should be abundant in summer (1.5 modifier)
            self.assertEqual(room.db.resource_nodes["berries"]["max_amount"], 15)


class TestEngineTicker(EvenniaTest):
    """Test steam engine fuel ticker."""
    
    def setUp(self):
        super().setUp()
        self.engine = create.create_object(Object, key="Steam Engine")
        self.engine.db.is_running = True
        self.engine.db.fuel_amount = 10
        self.engine.db.fuel_capacity = 100
        self.engine.db.fuel_consumption_rate = 2
        self.engine.db.max_pressure = 100
        self.engine.db.current_pressure = 50
    
    @patch('world.scripts.ObjectDB')
    def test_fuel_consumption(self, mock_db):
        """Test that engines consume fuel when running."""
        mock_db.objects.filter.return_value = [self.engine]
        
        # Run engine update
        update_steam_engines()
        
        # Fuel should decrease
        self.assertEqual(self.engine.db.fuel_amount, 8)  # 10 - 2
        
        # Pressure should update based on fuel level
        expected_pressure = int(100 * (8 / 100))  # 8% of max
        self.assertEqual(self.engine.db.current_pressure, expected_pressure)
    
    @patch('world.scripts.ObjectDB')
    def test_engine_out_of_fuel(self, mock_db):
        """Test that engines stop when out of fuel."""
        self.engine.db.fuel_amount = 1  # Less than consumption rate
        
        mock_db.objects.filter.return_value = [self.engine]
        
        # Run engine update
        update_steam_engines()
        
        # Engine should stop
        self.assertFalse(self.engine.db.is_running)
        self.assertEqual(self.engine.db.current_pressure, 0)
        self.assertEqual(self.engine.db.fuel_amount, 0)


class TestTickerIntegration(EvenniaTest):
    """Test integration between different ticker systems."""
    
    def setUp(self):
        super().setUp()
        # Create integrated test environment
        self.room = create.create_object(Room, key="Test Environment")
        self.room.db.indoor = False
        self.room.tags.add("has_resources")
        
        self.char = create.create_object(Character, key="Test Character", location=self.room)
        
        # Add some equipment
        self.coat = create.create_object(Object, key="Winter Coat")
        self.coat.db.warmth = 20
        self.coat.db.weather_protection = ["snow", "wind"]
        
        # Add food
        self.food = create.create_object(Object, key="Rations", location=self.char)
        self.food.tags.add("food", category="item_type")
        self.food.db.freshness = 100
    
    @patch('world.scripts.gametime.gametime')
    def test_winter_survival_integration(self, mock_time):
        """Test integrated effects of winter weather on survival."""
        # Set winter conditions
        mock_time.return_value.month = 11  # Winter
        mock_time.return_value.hour = 2    # Night
        
        # Set harsh weather
        self.room.db.weather = ["snow", "wind"]
        
        # Without protection
        effects = get_environmental_effects(self.char)
        
        # Should have significant penalties
        self.assertGreater(effects['fatigue_rate_mod'], 1.5)
        self.assertGreater(effects['health_drain'], 0)
        
        # With protection (mock wearing coat)
        with patch.object(self.char, 'clothing') as mock_clothing:
            mock_clothing.all.return_value = [self.coat]
            
            protected_effects = get_environmental_effects(self.char)
            
            # Should have reduced penalties
            self.assertLess(protected_effects['fatigue_rate_mod'], 
                          effects['fatigue_rate_mod'])
