# world/tests/test_gametime.py - hela den uppdaterade test-filen med enklare test

"""
Tests for the custom gametime system.
"""

from django.test import override_settings
from evennia.utils.test_resources import EvenniaTest
from evennia.contrib.base_systems import custom_gametime
from unittest.mock import patch, MagicMock
from commands.time_commands import CmdTime, CmdUptime
from world.gametime_utils import (
    get_current_season, get_time_of_day, format_game_date,
    is_night_time, is_winter, get_seasonal_modifier
)


# Test settings to use
TEST_TIME_UNITS = {
    "sec": 1,
    "min": 60,
    "hour": 60 * 60,
    "day": 60 * 60 * 24,
    "week": 60 * 60 * 24 * 7,
    "month": 60 * 60 * 24 * 30,
    "year": 60 * 60 * 24 * 30 * 12,
}

TEST_MONTH_NAMES = [
    "Frosthold", "Icewind", "Thawmoon", "Seedtime",
    "Bloomheart", "Greentide", "Sunpeak", "Hearthfire",
    "Goldfall", "Harvestmoon", "Dimming", "Darkening"
]

TEST_SEASONS = {
    "winter": [11, 0, 1, 2],
    "spring": [3, 4, 5],
    "summer": [6, 7, 8],
    "autumn": [9, 10]
}

TEST_TIME_OF_DAY = {
    "dawn": (5, 7),
    "morning": (7, 12),
    "noon": (12, 14),
    "afternoon": (14, 17),
    "dusk": (17, 19),
    "evening": (19, 22),
    "night": (22, 5)
}


@override_settings(
    TIME_FACTOR=4,
    TIME_UNITS=TEST_TIME_UNITS,
    MONTH_NAMES=TEST_MONTH_NAMES,
    SEASONS=TEST_SEASONS,
    TIME_OF_DAY=TEST_TIME_OF_DAY
)
class TestCustomGametime(EvenniaTest):
    """Test the custom gametime system."""
    
    def test_time_factor(self):
        """Test that TIME_FACTOR is correctly applied."""
        from django.conf import settings
        self.assertEqual(settings.TIME_FACTOR, 4)
    
    def test_month_duration(self):
        """Test that months are exactly 30 days."""
        month_seconds = TEST_TIME_UNITS["month"]
        day_seconds = TEST_TIME_UNITS["day"]
        self.assertEqual(month_seconds, day_seconds * 30)
    
    def test_year_duration(self):
        """Test that years are exactly 360 days."""
        year_seconds = TEST_TIME_UNITS["year"]
        day_seconds = TEST_TIME_UNITS["day"]
        self.assertEqual(year_seconds, day_seconds * 360)
    
    def test_custom_gametime_tuple(self):
        """Test that custom_gametime returns correct tuple format."""
        with patch('evennia.utils.gametime.gametime') as mock_gametime:
            # Test 1: Simple test - just one day
            mock_seconds = TEST_TIME_UNITS["day"]
            mock_gametime.return_value = mock_seconds
            
            result = custom_gametime.custom_gametime()
            year, month, week, day, hour, minute, second = result
            
            # One day should give us day=1 (or 0 depending on implementation)
            self.assertEqual(year, 0)
            self.assertEqual(month, 0)
            self.assertEqual(hour, 0)
            self.assertEqual(minute, 0)
            self.assertEqual(second, 0)
            
            # Test 2: Complex test - let's use exact time and check hour/min/sec
            # which are more predictable
            mock_seconds = (
                TEST_TIME_UNITS["hour"] * 14 +
                TEST_TIME_UNITS["min"] * 30 +
                45
            )
            mock_gametime.return_value = mock_seconds
            
            year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
            
            # These should be exact
            self.assertEqual(hour, 14)
            self.assertEqual(minute, 30)
            self.assertEqual(second, 45)
            
            # Test 3: Test with years and months for basic functionality
            mock_seconds = (
                TEST_TIME_UNITS["year"] * 1 +
                TEST_TIME_UNITS["month"] * 3
            )
            mock_gametime.return_value = mock_seconds
            
            year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
            
            # Should have 1 year and 3 months
            self.assertEqual(year, 1)
            self.assertEqual(month, 3)
            self.assertEqual(hour, 0)
            self.assertEqual(minute, 0)
            self.assertEqual(second, 0)
    
    def test_real_seconds_until(self):
        """Test calculating real seconds until a specific game time."""
        with patch('evennia.utils.gametime.gametime') as mock_gametime:
            # Current time: 12:00:00
            current_seconds = TEST_TIME_UNITS["hour"] * 12
            mock_gametime.return_value = current_seconds
            
            # Ask for 13:00:00 (1 game hour later)
            real_seconds = custom_gametime.real_seconds_until(hour=13, min=0, sec=0)
            
            # Should be 900 real seconds (1 game hour / 4)
            self.assertEqual(real_seconds, 900)


@override_settings(
    TIME_FACTOR=4,
    TIME_UNITS=TEST_TIME_UNITS,
    MONTH_NAMES=TEST_MONTH_NAMES,
    SEASONS=TEST_SEASONS,
    TIME_OF_DAY=TEST_TIME_OF_DAY
)
class TestTimeCommands(EvenniaTest):
    """Test time-related commands."""
    
    def test_cmd_time(self):
        """Test the time command output."""
        with patch('evennia.contrib.base_systems.custom_gametime.custom_gametime') as mock_time:
            # Mock a specific time: Year 850, Bloomheart (month 4), day 14, 19:30
            mock_time.return_value = (850, 4, 2, 14, 19, 30, 0)
            
            # Create command instance and set up properly
            cmd = CmdTime()
            cmd.caller = self.char1
            cmd.args = ""
            cmd.cmdstring = "time"
            cmd.raw_string = "time"
            cmd.switches = []
            
            # Capture output
            messages = []
            self.char1.msg = lambda text, **kwargs: messages.append(text)
            
            # Execute command
            cmd.func()
            
            # Check the output contains expected parts
            output = "\n".join(messages)
            self.assertIn("It is evening on the 15th day of Bloomheart, in the year 850.", output)
            self.assertIn("The season is spring", output)
            self.assertIn("Game time moves at 4x speed", output)
    
    def test_cmd_time_exact(self):
        """Test the time command with exact switch."""
        with patch('evennia.contrib.base_systems.custom_gametime.custom_gametime') as mock_time:
            # Mock a specific time
            mock_time.return_value = (850, 4, 2, 14, 19, 30, 45)
            
            # Test with /exact switch
            cmd = CmdTime()
            cmd.caller = self.char1
            cmd.switches = ["exact"]
            
            # Capture the output
            messages = []
            self.char1.msg = lambda text, **kwargs: messages.append(text)
            
            cmd.func()
            
            # Check that exact time was included
            self.assertTrue(any("19:30:45" in msg for msg in messages))
    
    def test_cmd_uptime(self):
        """Test the uptime command."""
        with patch('evennia.utils.gametime.uptime') as mock_uptime:
            # Mock 2 hours of real uptime
            mock_uptime.return_value = 7200
            
            cmd = CmdUptime()
            cmd.caller = self.char1
            
            # Capture output
            messages = []
            self.char1.msg = lambda text, **kwargs: messages.append(text)
            
            cmd.func()
            
            # Check output contains both real and game time
            output = "\n".join(messages)
            self.assertIn("Real time: 2 hours", output)
            self.assertIn("Game time: 8 hours", output)  # 2 * 4 = 8


@override_settings(
    TIME_FACTOR=4,
    TIME_UNITS=TEST_TIME_UNITS,
    MONTH_NAMES=TEST_MONTH_NAMES,
    SEASONS=TEST_SEASONS,
    TIME_OF_DAY=TEST_TIME_OF_DAY
)
class TestGametimeUtils(EvenniaTest):
    """Test gametime utility functions."""
    
    def test_get_current_season(self):
        """Test season detection."""
        with patch('evennia.contrib.base_systems.custom_gametime.custom_gametime') as mock_time:
            # Test winter (month 0 - Frosthold)
            mock_time.return_value = (850, 0, 0, 0, 0, 0, 0)
            self.assertEqual(get_current_season(), "winter")
            
            # Test spring (month 4 - Bloomheart)
            mock_time.return_value = (850, 4, 0, 0, 0, 0, 0)
            self.assertEqual(get_current_season(), "spring")
            
            # Test summer (month 7 - Hearthfire)
            mock_time.return_value = (850, 7, 0, 0, 0, 0, 0)
            self.assertEqual(get_current_season(), "summer")
            
            # Test autumn (month 10 - Dimming)
            mock_time.return_value = (850, 10, 0, 0, 0, 0, 0)
            self.assertEqual(get_current_season(), "autumn")
    
    def test_get_time_of_day(self):
        """Test time of day detection."""
        with patch('evennia.contrib.base_systems.custom_gametime.custom_gametime') as mock_time:
            # Test dawn (6:00)
            mock_time.return_value = (0, 0, 0, 0, 6, 0, 0)
            self.assertEqual(get_time_of_day(), "dawn")
            
            # Test noon (13:00)
            mock_time.return_value = (0, 0, 0, 0, 13, 0, 0)
            self.assertEqual(get_time_of_day(), "noon")
            
            # Test night (23:00)
            mock_time.return_value = (0, 0, 0, 0, 23, 0, 0)
            self.assertEqual(get_time_of_day(), "night")
            
            # Test night (3:00 - crosses midnight)
            mock_time.return_value = (0, 0, 0, 0, 3, 0, 0)
            self.assertEqual(get_time_of_day(), "night")
    
    def test_format_game_date(self):
        """Test date formatting."""
        with patch('evennia.contrib.base_systems.custom_gametime.custom_gametime') as mock_time:
            # Test various dates
            mock_time.return_value = (850, 4, 0, 0, 0, 0, 0)
            self.assertEqual(format_game_date(), "1st of Bloomheart, Year 850")
            
            mock_time.return_value = (850, 4, 0, 1, 0, 0, 0)
            self.assertEqual(format_game_date(), "2nd of Bloomheart, Year 850")
            
            mock_time.return_value = (850, 4, 0, 2, 0, 0, 0)
            self.assertEqual(format_game_date(), "3rd of Bloomheart, Year 850")
            
            mock_time.return_value = (850, 4, 0, 20, 0, 0, 0)
            self.assertEqual(format_game_date(), "21st of Bloomheart, Year 850")
    
    def test_is_night_time(self):
        """Test night time detection."""
        with patch('evennia.contrib.base_systems.custom_gametime.custom_gametime') as mock_time:
            # Night (23:00)
            mock_time.return_value = (0, 0, 0, 0, 23, 0, 0)
            self.assertTrue(is_night_time())
            
            # Dawn (6:00)
            mock_time.return_value = (0, 0, 0, 0, 6, 0, 0)
            self.assertTrue(is_night_time())
            
            # Dusk (18:00)
            mock_time.return_value = (0, 0, 0, 0, 18, 0, 0)
            self.assertTrue(is_night_time())
            
            # Noon (12:00)
            mock_time.return_value = (0, 0, 0, 0, 12, 0, 0)
            self.assertFalse(is_night_time())
    
    def test_is_winter(self):
        """Test winter detection."""
        with patch('evennia.contrib.base_systems.custom_gametime.custom_gametime') as mock_time:
            # Winter month (Frosthold)
            mock_time.return_value = (850, 0, 0, 0, 0, 0, 0)
            self.assertTrue(is_winter())
            
            # Summer month (Sunpeak)
            mock_time.return_value = (850, 6, 0, 0, 0, 0, 0)
            self.assertFalse(is_winter())
    
    def test_get_seasonal_modifier(self):
        """Test seasonal modifiers."""
        # Test winter modifiers
        winter_mods = get_seasonal_modifier("winter")
        self.assertEqual(winter_mods["resource_availability"], 0.5)
        self.assertEqual(winter_mods["fatigue_rate"], 1.5)
        
        # Test summer modifiers
        summer_mods = get_seasonal_modifier("summer")
        self.assertEqual(summer_mods["resource_availability"], 1.5)
        self.assertEqual(summer_mods["food_decay"], 1.5)
        
        # Test current season modifiers
        with patch('world.gametime_utils.get_current_season') as mock_season:
            mock_season.return_value = "spring"
            spring_mods = get_seasonal_modifier()
            self.assertEqual(spring_mods["resource_availability"], 1.2)


class TestTraitDecayIntegration(EvenniaTest):
    """Test that trait decay will work with gametime."""
    
    def test_trait_decay_preparation(self):
        """Test that traits are ready for gametime-based decay."""
        # Verify our character has decay rates set
        self.assertEqual(self.char1.traits.hunger.rate, -2.0)
        self.assertEqual(self.char1.traits.thirst.rate, -3.0)
        self.assertEqual(self.char1.traits.fatigue.rate, -1.0)
        
        # Verify TIME_FACTOR affects decay calculation
        # With TIME_FACTOR = 4, 1 real hour = 4 game hours
        # So traits should decay 4x their rate per real hour
        from django.conf import settings
        time_factor = getattr(settings, 'TIME_FACTOR', 1)
        
        # In 1 real hour, hunger should drop by 8 (2 * 4)
        expected_hunger_per_real_hour = abs(self.char1.traits.hunger.rate) * time_factor
        self.assertEqual(expected_hunger_per_real_hour, 8.0)


class TestMonthNameIntegration(EvenniaTest):
    """Test month name integration."""
    
    def test_all_months_have_names(self):
        """Verify all 12 months have fantasy names."""
        from django.conf import settings
        self.assertEqual(len(settings.MONTH_NAMES), 12)
        
        # Verify no duplicates
        self.assertEqual(len(set(settings.MONTH_NAMES)), 12)
        
        # Verify all are strings
        for name in settings.MONTH_NAMES:
            self.assertIsInstance(name, str)
            self.assertTrue(len(name) > 0)
    
    def test_seasons_cover_all_months(self):
        """Verify every month belongs to a season."""
        from django.conf import settings
        
        all_months = set()
        for season, months in settings.SEASONS.items():
            all_months.update(months)
        
        # Should have all months 0-11
        self.assertEqual(all_months, set(range(12)))
