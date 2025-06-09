# world/tests/test_ticker_integration.py
"""
Full integration tests for the TickerHandler system with all game systems.
"""
from evennia.utils.test_resources import EvenniaTest
from evennia.utils import create
from evennia import TICKER_HANDLER
from typeclasses.rooms import Room
from typeclasses.characters import Character
from typeclasses.objects import Object
from unittest.mock import patch, MagicMock
from world.scripts import initialize_all_tickers
from django.conf import settings
import datetime


class TestFullTickerIntegration(EvenniaTest):
    """Test full integration of all ticker systems."""
    
    def setUp(self):
        super().setUp()
        
        # Clear and initialize tickers
        TICKER_HANDLER.clear()
        initialize_all_tickers()
        
        # Create test world
        self.setup_test_world()
    
    def tearDown(self):
        TICKER_HANDLER.clear()
        super().tearDown()
    
    def setup_test_world(self):
        """Create a complete test environment."""
        # Create outdoor and indoor rooms
        self.outdoor_room = create.create_object(Room, key="Forest Clearing")
        self.outdoor_room.db.indoor = False
        self.outdoor_room.tags.add("has_resources")
        self.outdoor_room.db.resource_nodes = {
            "berries": {
                "max_amount": 10,
                "current_amount": 5,
                "regen_rate": 2,
                "resource_type": "berries",
                "base_max_amount": 10
            }
        }
        
        self.indoor_room = create.create_object(Room, key="Cozy Cabin")
        self.indoor_room.db.indoor = True
        
        # Create test character
        self.char = create.create_object(Character, key="Test Survivor", 
                                       location=self.outdoor_room)
        
        # Create survival items
        self.create_survival_items()
        
        # Create steam engine
        self.engine = create.create_object(Object, key="Steam Engine",
                                         location=self.indoor_room)
        self.engine.db.typeclass_path = "typeclasses.objects.SteamEngine"
        self.engine.db.is_running = True
        self.engine.db.fuel_amount = 50
        self.engine.db.fuel_capacity = 100
        self.engine.db.fuel_consumption_rate = 5
        self.engine.db.max_pressure = 100
    
    def create_survival_items(self):
        """Create various survival items for testing."""
        # Winter clothing
        self.coat = create.create_object(Object, key="Fur-lined Coat")
        self.coat.db.warmth = 25
        self.coat.db.weather_protection = ["snow", "wind", "rain"]
        self.coat.db.clothing_type = "outerwear"
        
        # Food items
        self.bread = create.create_object(Object, key="Fresh Bread", 
                                        location=self.char)
        self.bread.tags.add("food", category="item_type")
        self.bread.db.freshness = 100
        self.bread.db.decay_rate = 20
        self.bread.db.hunger_value = 30
        
        self.preserved_food = create.create_object(Object, key="Dried Meat",
                                                  location=self.char)
        self.preserved_food.tags.add("food", category="item_type")
        self.preserved_food.tags.add("preserved", category="quality")
        self.preserved_food.db.freshness = 100
        self.preserved_food.db.decay_rate = 5  # Slower decay
        self.preserved_food.db.hunger_value = 25
    
    @patch('world.scripts.SESSIONS.get_sessions')
    @patch('world.scripts.gametime.gametime')
    def test_winter_survival_scenario(self, mock_time, mock_sessions):
        """Test complete winter survival scenario."""
        # Setup: Winter night with storm
        mock_time.return_value.month = 11  # Dimming (Winter)
        mock_time.return_value.hour = 2    # Night
        mock_time.return_value.day = 15    # Mid-month
        
        # Mock character as online
        mock_session = MagicMock()
        mock_session.puppet = self.char
        mock_sessions.return_value = [mock_session]
        
        # Set harsh weather
        self.outdoor_room.db.weather = ["snow", "storm", "wind"]
        
        # Initial state
        self.char.traits.hunger.current = 80
        self.char.traits.thirst.current = 70
        self.char.traits.fatigue.current = 60
        self.char.traits.health.current = 100
        
        # Test 1: Without protection
        from world.scripts import update_all_survival
        
        messages_received = []
        self.char.msg = lambda text, **kwargs: messages_received.append(text)
        
        update_all_survival()
        
        # Should receive cold warnings
        self.assertTrue(any("freezing" in msg.lower() for msg in messages_received))
        
        # Test 2: With protection
        messages_received.clear()
        
        # Mock wearing warm coat
        with patch.object(self.char, 'clothing') as mock_clothing:
            mock_clothing.all.return_value = [self.coat]
            
            update_all_survival()
            
            # Should not be freezing anymore
            self.assertFalse(any("freezing" in msg.lower() for msg in messages_received))
    
    @patch('world.scripts.gametime.gametime')
    @patch('world.scripts.ObjectDB')
    def test_seasonal_transition(self, mock_db, mock_time):
        """Test transition from winter to spring."""
        # Start at last day of winter
        mock_time.return_value.month = 1   # Icewind (last winter month)
        mock_time.return_value.day = 30    # Last day
        
        from world.scripts import check_seasonal_events, update_seasonal_resources
        
        # Run end of winter check
        check_seasonal_events()
        
        # Move to first day of spring
        mock_time.return_value.month = 2   # Mudmelt (first spring month)
        mock_time.return_value.day = 1     # First day
        
        # Mock online session for announcement
        mock_session = MagicMock()
        with patch('world.scripts.SESSIONS.get_sessions') as mock_sessions:
            mock_sessions.return_value = [mock_session]
            
            check_seasonal_events()
            
            # Should announce spring
            mock_session.puppet.msg.assert_called()
            call_args = str(mock_session.puppet.msg.call_args)
            self.assertIn("Spring", call_args)
        
        # Check resource updates
        mock_db.objects.filter.return_value = [self.outdoor_room]
        update_seasonal_resources("spring")
        
        # Berry nodes should have spring modifier (1.0x for berries)
        berries = self.outdoor_room.db.resource_nodes["berries"]
        # Spring berries are 0.5x, so max should be 5
        self.assertEqual(berries["max_amount"], 5)
    
    @patch('world.scripts.ObjectDB')
    def test_complete_resource_cycle(self, mock_db):
        """Test resource gathering and regeneration cycle."""
        from world.scripts import regenerate_resources
        
        # Initial state: some berries available
        berries = self.outdoor_room.db.resource_nodes["berries"]
        self.assertEqual(berries["current_amount"], 5)
        
        # Simulate gathering (manually reduce)
        berries["current_amount"] = 1
        
        # Mock database return
        mock_db.objects.filter.return_value = [self.outdoor_room]
        
        # Run regeneration
        regenerate_resources()
        
        # Should regenerate by regen_rate (2)
        self.assertEqual(berries["current_amount"], 3)
        
        # Run again
        regenerate_resources()
        self.assertEqual(berries["current_amount"], 5)
        
        # Run multiple times - should cap at max
        for _ in range(5):
            regenerate_resources()
        
        self.assertEqual(berries["current_amount"], 10)  # Capped at max
    
    @patch('world.scripts.ObjectDB')
    def test_food_lifecycle(self, mock_db):
        """Test complete food spoilage lifecycle."""
        from world.scripts import check_food_spoilage
        
        # Mock database to return our food items
        mock_db.objects.filter.return_value = [self.bread, self.preserved_food]
        
        # Initial state
        self.assertEqual(self.bread.db.freshness, 100)
        self.assertEqual(self.preserved_food.db.freshness, 100)
        
        # Run spoilage multiple times
        for i in range(5):
            check_food_spoilage()
        
        # Bread should decay faster
        self.assertEqual(self.bread.db.freshness, 0)  # 100 - (20*5) = 0
        self.assertTrue(self.bread.tags.has("spoiled", category="quality"))
        
        # Preserved food should decay slower
        self.assertEqual(self.preserved_food.db.freshness, 75)  # 100 - (5*5) = 75
        self.assertFalse(self.preserved_food.tags.has("spoiled", category="quality"))
    
    @patch('world.scripts.ObjectDB')
    def test_steam_engine_operation(self, mock_db):
        """Test steam engine fuel consumption cycle."""
        from world.scripts import update_steam_engines
        
        mock_db.objects.filter.return_value = [self.engine]
        
        initial_fuel = self.engine.db.fuel_amount
        
        # Run engine for several cycles
        for i in range(5):
            update_steam_engines()
        
        # Fuel should decrease
        expected_fuel = initial_fuel - (5 * self.engine.db.fuel_consumption_rate)
        self.assertEqual(self.engine.db.fuel_amount, expected_fuel)
        
        # Engine should still be running
        self.assertTrue(self.engine.db.is_running)
        
        # Run until fuel exhausted
        self.engine.db.fuel_amount = 3  # Less than consumption rate
        update_steam_engines()
        
        # Engine should stop
        self.assertFalse(self.engine.db.is_running)
        self.assertEqual(self.engine.db.fuel_amount, 0)
        self.assertEqual(self.engine.db.current_pressure, 0)
    
    def test_ticker_persistence(self):
        """Test that tickers are marked as persistent."""
        all_tickers = TICKER_HANDLER.all()
        
        # Check that all our tickers are persistent
        for ticker_key, (store_key, ticker_obj) in all_tickers.items():
            if hasattr(ticker_obj, 'persistent'):
                self.assertTrue(ticker_obj.persistent,
                              f"Ticker {getattr(ticker_obj, 'idstring', 'unknown')} should be persistent")
    
    @patch('world.scripts.SESSIONS.get_sessions')
    @patch('world.scripts.gametime.gametime')
    @patch('world.scripts.ObjectDB')
    def test_full_game_hour(self, mock_db, mock_time, mock_sessions):
        """Simulate a full game hour with all systems active."""
        # Setup time: Summer afternoon
        mock_time.return_value.month = 6   # Sunshine (Summer)
        mock_time.return_value.hour = 14   # Afternoon
        mock_time.return_value.day = 15
        
        # Mock online character
        mock_session = MagicMock()
        mock_session.puppet = self.char
        mock_sessions.return_value = [mock_session]
        
        # Mock database returns
        mock_db.objects.filter.side_effect = lambda **kwargs: {
            'db_typeclass_path__icontains="typeclasses.rooms.Room"': [self.outdoor_room],
            'db_tags__db_key="has_resources"': [self.outdoor_room],
            'db_tags__db_key="food"': [self.bread],
            'db_typeclass_path__icontains="SteamEngine"': [self.engine],
        }.get(str(kwargs), [])
        
        # Set summer weather
        self.outdoor_room.db.weather = ["clear"]
        
        # Move character outdoors without protection
        self.char.location = self.outdoor_room
        
        # Run all ticker systems once
        from world.scripts import (
            update_all_survival,
            update_global_weather,
            regenerate_resources,
            check_food_spoilage,
            update_steam_engines
        )
        
        # Initial states
        initial_thirst = self.char.traits.thirst.value
        initial_bread_freshness = self.bread.db.freshness
        initial_fuel = self.engine.db.fuel_amount
        
        # Run all systems
        update_all_survival()      # Should increase thirst in summer heat
        update_global_weather()    # Might change weather
        regenerate_resources()     # Should increase berries
        check_food_spoilage()      # Should decay bread
        update_steam_engines()     # Should consume fuel
        
        # Verify changes occurred
        # Note: We can't check exact thirst change without implementing the trait decay
        # but we can verify the systems ran without errors
        
        # Food should have decayed
        self.assertLess(self.bread.db.freshness, initial_bread_freshness)
        
        # Engine should have consumed fuel
        self.assertLess(self.engine.db.fuel_amount, initial_fuel)
        
        # Resources should have regenerated
        berries = self.outdoor_room.db.resource_nodes["berries"]
        self.assertGreater(berries["current_amount"], 0)


class TestTickerPerformance(EvenniaTest):
    """Test performance aspects of the ticker system."""
    
    def setUp(self):
        super().setUp()
        TICKER_HANDLER.clear()
    
    def tearDown(self):
        TICKER_HANDLER.clear()
        super().tearDown()
    
    def test_ticker_initialization_performance(self):
        """Test that ticker initialization is fast."""
        import time
        
        start_time = time.time()
        initialize_all_tickers()
        elapsed = time.time() - start_time
        
        # Should initialize in under 1 second
        self.assertLess(elapsed, 1.0,
                       f"Ticker initialization took {elapsed:.2f}s, should be under 1s")
    
    @patch('world.scripts.SESSIONS.get_sessions')
    @patch('world.scripts.ObjectDB')
    def test_survival_update_scaling(self, mock_db, mock_sessions):
        """Test survival update performance with many characters."""
        # Create many mock characters
        mock_chars = []
        for i in range(50):
            mock_char = MagicMock()
            mock_char.traits = MagicMock()
            mock_char.location = self.room1
            mock_char.msg = MagicMock()
            
            mock_session = MagicMock()
            mock_session.puppet = mock_char
            mock_chars.append(mock_session)
        
        mock_sessions.return_value = mock_chars
        
        # Time the update
        import time
        from world.scripts import update_all_survival
        
        start_time = time.time()
        update_all_survival()
        elapsed = time.time() - start_time
        
        # Should handle 50 characters in under 1 second
        self.assertLess(elapsed, 1.0,
                       f"Survival update for 50 characters took {elapsed:.2f}s")
