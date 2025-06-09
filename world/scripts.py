# world/scripts.py
"""
TickerHandler scripts for Fantasy Steampunk Survival MUD.

This module contains all the ticker functions that are called periodically
to update various game systems automatically:
- Survival trait decay for online characters
- Resource regeneration in rooms
- Weather updates for outdoor areas
- Food spoilage in inventories
- Seasonal announcements
- Steam engine fuel consumption
"""

from evennia import TICKER_HANDLER
from evennia.utils import logger, search
from evennia.server.sessionhandler import SESSIONS
from evennia.objects.models import ObjectDB
from django.conf import settings
import random
from datetime import datetime

# Use the same import as in gametime_utils.py
from evennia.contrib.base_systems import custom_gametime


# Ticker intervals (in real seconds)
SURVIVAL_UPDATE_INTERVAL = 600      # 10 minutes real time = 40 minutes game time
WEATHER_UPDATE_INTERVAL = 900       # 15 minutes real time = 1 game hour
RESOURCE_REGEN_INTERVAL = 3600      # 1 hour real time = 4 game hours
FOOD_SPOILAGE_INTERVAL = 1800       # 30 minutes real time = 2 game hours
SEASON_CHECK_INTERVAL = 21600       # 6 hours real time = 1 game day
ENGINE_FUEL_INTERVAL = 300          # 5 minutes real time = 20 minutes game time


def update_all_survival():
    """
    Update survival traits for all online characters.
    
    This function is called every 10 minutes (real time) and:
    - Applies environmental effects based on location and clothing
    - Modifies trait decay rates based on conditions
    - Sends appropriate messages to players
    """
    try:
        updated_count = 0
        
        for session in SESSIONS.get_sessions():
            character = session.puppet
            if not character or not hasattr(character, 'traits'):
                continue
                
            # Apply environmental effects
            effects = get_environmental_effects(character)
            
            # Apply modifiers to trait decay rates
            if effects:
                apply_trait_modifiers(character, effects)
                
                # Send any environmental messages
                for msg in effects.get("messages", []):
                    character.msg(msg)
            
            updated_count += 1
        
        if updated_count > 0:
            logger.log_info(f"TickerHandler: Updated survival for {updated_count} characters")
            
    except Exception as e:
        logger.log_err(f"TickerHandler error in update_all_survival: {e}")


def get_environmental_effects(character):
    """
    Calculate environmental effects on a character.
    
    Args:
        character: The character to check
        
    Returns:
        dict: Effects dictionary with modifiers and messages
    """
    effects = {
        "hunger_rate_mod": 1.0,
        "thirst_rate_mod": 1.0,
        "fatigue_rate_mod": 1.0,
        "health_drain": 0,
        "messages": []
    }
    
    location = character.location
    if not location:
        return effects
    
    # Get current game time using custom_gametime (returns tuple)
    year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
    
    # Determine season from month
    season = "unknown"
    for season_name, months in settings.SEASONS.items():
        if month in months:
            season = season_name
            break
    
    # Determine time of day
    time_of_day = "night"
    for period, (start, end) in settings.TIME_OF_DAY.items():
        if start <= hour < end or (start > end and (hour >= start or hour < end)):
            time_of_day = period
            break
    
    # Get weather from room
    weather = []
    if hasattr(location, 'get_weather'):
        weather = location.get_weather()
    elif hasattr(location.db, 'weather'):
        weather = location.db.weather if isinstance(location.db.weather, list) else [location.db.weather]
    
    # Calculate clothing protection
    warmth = 0
    protection = {"rain": False, "wind": False, "snow": False}
    
    if hasattr(character, 'clothing'):
        worn_items = character.clothing.all()
        for item in worn_items:
            warmth += item.db.warmth or 0
            if hasattr(item.db, 'weather_protection'):
                for weather_type in item.db.weather_protection:
                    protection[weather_type] = True
    
    # Apply environmental effects based on conditions
    
    # COLD EFFECTS (Winter nights, cold weather)
    if season == "winter" or (time_of_day in ["night", "evening"] and season == "autumn"):
        base_cold = 20 if season == "winter" else 10
        
        if time_of_day == "night":
            base_cold += 10
            
        # Check if character has enough warmth
        warmth_deficit = base_cold - warmth
        
        if warmth_deficit > 15:
            effects["fatigue_rate_mod"] *= 2.0
            effects["health_drain"] = 2
            effects["messages"].append("|rYou are freezing!|n")
        elif warmth_deficit > 5:
            effects["fatigue_rate_mod"] *= 1.5
            effects["health_drain"] = 1
            effects["messages"].append("|yYou are very cold.|n")
        elif warmth_deficit > 0:
            effects["fatigue_rate_mod"] *= 1.2
            effects["messages"].append("|yYou feel chilly.|n")
    
    # HEAT EFFECTS (Summer days)
    elif season == "summer" and time_of_day in ["noon", "afternoon"]:
        if warmth > 30:
            effects["thirst_rate_mod"] *= 2.0
            effects["fatigue_rate_mod"] *= 1.5
            effects["messages"].append("|rYou are overheating!|n")
        elif warmth > 20:
            effects["thirst_rate_mod"] *= 1.5
            effects["fatigue_rate_mod"] *= 1.2
            effects["messages"].append("|yThe heat is making you sweat.|n")
    
    # WEATHER EFFECTS
    if "rain" in weather or "storm" in weather:
        if not protection["rain"]:
            effects["fatigue_rate_mod"] *= 1.3
            if season == "winter":
                effects["health_drain"] += 1
                effects["messages"].append("|bThe cold rain chills you to the bone.|n")
            else:
                effects["messages"].append("|yYou are getting soaked.|n")
    
    if "snow" in weather:
        if not protection["snow"]:
            effects["fatigue_rate_mod"] *= 1.4
            effects["messages"].append("|wSnow clings to your clothes.|n")
    
    if "wind" in weather or "storm" in weather:
        if not protection["wind"]:
            effects["fatigue_rate_mod"] *= 1.2
            if season == "winter":
                effects["messages"].append("|cThe wind cuts through you.|n")
    
    return effects


def apply_trait_modifiers(character, effects):
    """
    Apply environmental modifiers to character traits.
    
    Args:
        character: The character to modify
        effects: Dictionary of effects to apply
    """
    # Modify trait decay rates based on effects
    if hasattr(character.traits.hunger, 'rate'):
        base_rate = -2.0  # Base hunger decay
        character.traits.hunger.rate = base_rate * effects["hunger_rate_mod"]
    
    if hasattr(character.traits.thirst, 'rate'):
        base_rate = -3.0  # Base thirst decay
        character.traits.thirst.rate = base_rate * effects["thirst_rate_mod"]
    
    if hasattr(character.traits.fatigue, 'rate'):
        base_rate = -1.0  # Base fatigue decay
        character.traits.fatigue.rate = base_rate * effects["fatigue_rate_mod"]
    
    # Apply direct health drain if any
    if effects["health_drain"] > 0 and hasattr(character.traits, 'health'):
        character.traits.health.current -= effects["health_drain"]
        if character.traits.health.current <= 0:
            character.msg("|rYou collapse from exposure!|n")
            # TODO: Handle character death/unconsciousness


def update_global_weather():
    """
    Update weather for all outdoor rooms.
    
    This function is called every 15 minutes (1 game hour) and:
    - Changes weather patterns based on season
    - Updates room descriptions
    - Applies weather states to Extended Rooms
    """
    try:
        # Get current season using custom_gametime
        year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
        
        season = "unknown"
        for season_name, months in settings.SEASONS.items():
            if month in months:
                season = season_name
                break
        
        # Get all outdoor rooms
        all_rooms = ObjectDB.objects.filter(
            db_typeclass_path__icontains="typeclasses.rooms.Room"
        )
        
        updated_count = 0
        for room in all_rooms:
            if room.db.indoor:
                continue
                
            # Update weather for this room
            new_weather = generate_weather_for_season(season)
            old_weather = room.db.weather or []
            
            # Only update if weather changed
            if new_weather != old_weather:
                room.db.weather = new_weather
                
                # Set Extended Room states if available
                if hasattr(room, 'set_state'):
                    # Clear old weather states
                    for weather_type in ['clear', 'cloudy', 'rain', 'storm', 'fog', 'snow', 'wind']:
                        try:
                            room.remove_state(weather_type)
                        except:
                            pass  # State might not exist
                    
                    # Set new weather states
                    for weather_type in new_weather:
                        room.set_state(weather_type)
                
                # Announce weather change to room
                announce_weather_change(room, old_weather, new_weather)
                updated_count += 1
        
        if updated_count > 0:
            logger.log_info(f"TickerHandler: Updated weather for {updated_count} outdoor rooms")
            
    except Exception as e:
        logger.log_err(f"TickerHandler error in update_global_weather: {e}")


def generate_weather_for_season(season):
    """
    Generate appropriate weather for the current season.
    
    Args:
        season (str): Current season name
        
    Returns:
        list: Weather states for the room
    """
    # Get seasonal weather probabilities
    weather_probs = settings.SEASONAL_WEATHER.get(season, {
        "clear": 0.5,
        "cloudy": 0.3,
        "rain": 0.2
    })
    
    # Roll for weather
    roll = random.random()
    cumulative = 0
    weather_type = "clear"
    
    for weather, prob in weather_probs.items():
        cumulative += prob
        if roll <= cumulative:
            weather_type = weather
            break
    
    # Build weather state list
    weather = []
    
    if weather_type == "clear":
        weather = ["clear"]
    elif weather_type == "cloudy":
        weather = ["cloudy"]
    elif weather_type == "rain":
        # Rain can become storm
        if random.random() < 0.3:
            weather = ["rain", "storm", "wind"]
        else:
            weather = ["rain"]
    elif weather_type == "fog":
        weather = ["fog"]
    elif weather_type == "snow":
        # Snow often comes with wind
        if random.random() < 0.5:
            weather = ["snow", "wind"]
        else:
            weather = ["snow"]
    elif weather_type == "storm":
        weather = ["rain", "storm", "wind"]
    
    return weather


def announce_weather_change(room, old_weather, new_weather):
    """
    Announce weather changes to everyone in the room.
    
    Args:
        room: The room where weather changed
        old_weather: Previous weather states
        new_weather: New weather states
    """
    # Generate announcement based on weather change
    if "storm" in new_weather and "storm" not in old_weather:
        room.msg_contents("|yDark clouds gather overhead as a storm rolls in.|n")
    elif "rain" in new_weather and "rain" not in old_weather:
        room.msg_contents("|bRain begins to fall from the sky.|n")
    elif "snow" in new_weather and "snow" not in old_weather:
        room.msg_contents("|wSnowflakes begin to drift down from above.|n")
    elif "fog" in new_weather and "fog" not in old_weather:
        room.msg_contents("|xA thick fog rolls in, obscuring visibility.|n")
    elif "clear" in new_weather and "clear" not in old_weather:
        if "storm" in old_weather:
            room.msg_contents("|yThe storm passes, leaving clear skies.|n")
        else:
            room.msg_contents("|yThe weather clears.|n")


def regenerate_resources():
    """
    Regenerate harvestable resources in rooms.
    
    This function is called every hour (real time) and:
    - Regenerates resource nodes in rooms
    - Respawns forageable items
    - Updates room resource states
    """
    try:
        # Get all rooms with resource nodes
        all_rooms = ObjectDB.objects.filter(
            db_typeclass_path__icontains="typeclasses.rooms.Room",
            db_tags__db_key="has_resources"
        )
        
        regenerated_count = 0
        
        for room in all_rooms:
            if not hasattr(room.db, 'resource_nodes'):
                continue
            
            # Check each resource node
            for node_key, node_data in room.db.resource_nodes.items():
                max_amount = node_data.get('max_amount', 5)
                current = node_data.get('current_amount', 0)
                regen_rate = node_data.get('regen_rate', 1)
                
                # Regenerate resources
                if current < max_amount:
                    new_amount = min(current + regen_rate, max_amount)
                    node_data['current_amount'] = new_amount
                    regenerated_count += 1
            
            # Save updated nodes
            room.db.resource_nodes = room.db.resource_nodes
        
        if regenerated_count > 0:
            logger.log_info(f"TickerHandler: Regenerated {regenerated_count} resource nodes")
            
    except Exception as e:
        logger.log_err(f"TickerHandler error in regenerate_resources: {e}")


def check_food_spoilage():
    """
    Check and update food spoilage for all food items.
    
    This function is called every 30 minutes and:
    - Ages all food items
    - Converts fresh food to preserved/spoiled states
    - Removes completely spoiled items
    """
    try:
        # Get all food items
        food_items = ObjectDB.objects.filter(
            db_tags__db_key="food",
            db_tags__db_category="item_type"
        )
        
        spoiled_count = 0
        
        for item in food_items:
            if not hasattr(item.db, 'freshness'):
                continue
            
            # Age the food
            current_freshness = item.db.freshness
            decay_rate = item.db.decay_rate or 10
            
            new_freshness = max(0, current_freshness - decay_rate)
            item.db.freshness = new_freshness
            
            # Check if state change needed
            if current_freshness > 50 and new_freshness <= 50:
                # Fresh -> Stale
                item.db.desc = item.db.desc.replace("fresh", "slightly stale")
                if item.location and hasattr(item.location, 'msg'):
                    item.location.msg(f"{item.get_display_name(item.location)} is beginning to spoil.")
                spoiled_count += 1
                
            elif current_freshness > 0 and new_freshness <= 0:
                # Stale -> Spoiled
                item.db.desc = "This food has completely spoiled and is inedible."
                item.tags.add("spoiled", category="quality")
                if item.location and hasattr(item.location, 'msg'):
                    item.location.msg(f"{item.get_display_name(item.location)} has spoiled!")
                spoiled_count += 1
        
        if spoiled_count > 0:
            logger.log_info(f"TickerHandler: {spoiled_count} food items changed state")
            
    except Exception as e:
        logger.log_err(f"TickerHandler error in check_food_spoilage: {e}")


def check_seasonal_events():
    """
    Check for seasonal transitions and special events.
    
    This function is called every 6 hours (1 game day) and:
    - Announces season changes
    - Triggers seasonal events
    - Updates seasonal resource availability
    """
    try:
        year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
        
        # Get readable month name
        month_name = settings.MONTH_NAMES[month] if month < len(settings.MONTH_NAMES) else f"Month {month}"
        
        # Check if it's the first day of a new season
        if day == 0:  # First day of month (days are 0-indexed)
            # Check if this month starts a new season
            for season_name, months in settings.SEASONS.items():
                if month == months[0]:  # First month of season
                    logger.log_info(f"Season change: {month_name} begins {season_name}")
                    announce_season_change(season_name)
                    update_seasonal_resources(season_name)
                    break
        
        # Check for special seasonal events
        check_special_events(month, day)
        
    except Exception as e:
        logger.log_err(f"TickerHandler error in check_seasonal_events: {e}")


def announce_season_change(new_season):
    """
    Announce the change of season to all online players.
    
    Args:
        new_season (str): The new season name
    """
    # Get the current month name for flavor
    year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
    month_name = settings.MONTH_NAMES[month] if month < len(settings.MONTH_NAMES) else f"Month {month}"
    
    season_messages = {
        "winter": f"|CThe month of {month_name} brings winter's icy grip! The land is covered in frost and snow. Prepare warm clothing and shelter!|n",
        "spring": f"|GThe month of {month_name} heralds spring! The ice melts and new life emerges. Foraging becomes easier.|n",
        "summer": f"|YThe month of {month_name} brings summer heat! The sun blazes overhead. Stay hydrated and seek shade during midday.|n",
        "autumn": f"|rThe month of {month_name} marks autumn's arrival! The leaves turn golden and the harvest season begins.|n"
    }
    
    message = season_messages.get(new_season, f"|wThe month of {month_name} brings the {new_season} season!|n")
    
    # Send to all online players
    for session in SESSIONS.get_sessions():
        if session.puppet:
            session.puppet.msg(f"\n{message}\n")
    
    logger.log_info(f"TickerHandler: Announced {new_season} season change ({month_name})")


def update_seasonal_resources(season):
    """
    Update resource availability based on season.
    
    Args:
        season (str): Current season
    """
    # Define seasonal resource modifiers
    seasonal_resources = {
        "winter": {
            "berries": 0.1,      # Very rare in winter
            "herbs": 0.2,        # Some hardy herbs
            "mushrooms": 0.5,    # Some winter varieties
            "roots": 0.8,        # Still available under snow
            "game": 0.7          # Animals harder to find
        },
        "spring": {
            "berries": 0.5,      # Starting to grow
            "herbs": 1.2,        # Abundant fresh growth
            "mushrooms": 1.0,    # Normal availability
            "roots": 1.0,        # Normal availability
            "game": 1.2          # Animals more active
        },
        "summer": {
            "berries": 1.5,      # Peak berry season
            "herbs": 1.0,        # Normal availability
            "mushrooms": 0.7,    # Less in dry weather
            "roots": 0.8,        # Harder ground
            "game": 1.0          # Normal availability
        },
        "autumn": {
            "berries": 0.8,      # Late season berries
            "herbs": 0.7,        # Starting to wither
            "mushrooms": 1.5,    # Peak mushroom season
            "roots": 1.2,        # Harvest season
            "game": 1.3          # Animals preparing for winter
        }
    }
    
    modifiers = seasonal_resources.get(season, {})
    
    # Apply modifiers to all resource nodes
    all_rooms = ObjectDB.objects.filter(
        db_tags__db_key="has_resources"
    )
    
    for room in all_rooms:
        if not hasattr(room.db, 'resource_nodes'):
            continue
            
        for node_key, node_data in room.db.resource_nodes.items():
            resource_type = node_data.get('resource_type', 'generic')
            if resource_type in modifiers:
                # Adjust max amount based on season
                base_max = node_data.get('base_max_amount', 5)
                node_data['max_amount'] = int(base_max * modifiers[resource_type])


def check_special_events(month, day):
    """
    Check for special seasonal events and holidays.
    
    Args:
        month (int): Current month (0-11)
        day (int): Current day (0-29)
    """
    # Define special events (month, day)
    events = {
        (11, 14): "The Winter Solstice approaches! Prepare for the longest night.",
        (2, 0): "The Spring Equinox! Day and night are in balance.",
        (5, 14): "Midsummer Festival! The steam engines run at peak efficiency.",
        (8, 0): "Harvest Festival begins! Time to preserve food for winter.",
    }
    
    event_key = (month, day)
    if event_key in events:
        message = f"|y{events[event_key]}|n"
        for session in SESSIONS.get_sessions():
            if session.puppet:
                session.puppet.msg(f"\n{message}\n")


def update_steam_engines():
    """
    Update fuel consumption for all running steam engines.
    
    This function is called every 5 minutes and:
    - Consumes fuel from running engines
    - Stops engines that run out of fuel
    - Updates pressure levels
    """
    try:
        # Find all steam engine objects
        engines = ObjectDB.objects.filter(
            db_typeclass_path__icontains="SteamEngine"
        )
        
        updated_count = 0
        
        for engine in engines:
            if not engine.db.is_running:
                continue
            
            # Consume fuel
            fuel_consumed = engine.db.fuel_consumption_rate or 1
            current_fuel = engine.db.fuel_amount or 0
            
            if current_fuel >= fuel_consumed:
                engine.db.fuel_amount = current_fuel - fuel_consumed
                
                # Update pressure based on fuel
                max_pressure = engine.db.max_pressure or 100
                pressure_percent = (engine.db.fuel_amount / engine.db.fuel_capacity) if engine.db.fuel_capacity else 0
                engine.db.current_pressure = int(max_pressure * pressure_percent)
                
                updated_count += 1
            else:
                # Out of fuel - stop engine
                engine.db.is_running = False
                engine.db.current_pressure = 0
                engine.db.fuel_amount = 0
                
                if engine.location:
                    engine.location.msg_contents(
                        f"{engine.get_display_name(engine.location)} sputters and dies as it runs out of fuel!"
                    )
                
                updated_count += 1
        
        if updated_count > 0:
            logger.log_info(f"TickerHandler: Updated {updated_count} steam engines")
            
    except Exception as e:
        logger.log_err(f"TickerHandler error in update_steam_engines: {e}")


# Initialization function to set up all tickers
def initialize_all_tickers():
    """
    Initialize all ticker handlers.
    Called from at_server_start().
    """
    logger.log_info("Initializing TickerHandler systems...")
    
    # Clear any existing tickers to avoid duplicates
    TICKER_HANDLER.clear()
    
    # 1. Survival system ticker
    TICKER_HANDLER.add(
        interval=SURVIVAL_UPDATE_INTERVAL,
        callback=update_all_survival,
        idstring="survival_update",
        persistent=True
    )
    logger.log_info(f"✓ Survival ticker: every {SURVIVAL_UPDATE_INTERVAL}s")
    
    # 2. Weather system ticker
    TICKER_HANDLER.add(
        interval=WEATHER_UPDATE_INTERVAL,
        callback=update_global_weather,
        idstring="weather_update",
        persistent=True
    )
    logger.log_info(f"✓ Weather ticker: every {WEATHER_UPDATE_INTERVAL}s")
    
    # 3. Resource regeneration ticker
    TICKER_HANDLER.add(
        interval=RESOURCE_REGEN_INTERVAL,
        callback=regenerate_resources,
        idstring="resource_regen",
        persistent=True
    )
    logger.log_info(f"✓ Resource ticker: every {RESOURCE_REGEN_INTERVAL}s")
    
    # 4. Food spoilage ticker
    TICKER_HANDLER.add(
        interval=FOOD_SPOILAGE_INTERVAL,
        callback=check_food_spoilage,
        idstring="food_spoilage",
        persistent=True
    )
    logger.log_info(f"✓ Food spoilage ticker: every {FOOD_SPOILAGE_INTERVAL}s")
    
    # 5. Seasonal events ticker
    TICKER_HANDLER.add(
        interval=SEASON_CHECK_INTERVAL,
        callback=check_seasonal_events,
        idstring="seasonal_events",
        persistent=True
    )
    logger.log_info(f"✓ Seasonal ticker: every {SEASON_CHECK_INTERVAL}s")
    
    # 6. Steam engine ticker
    TICKER_HANDLER.add(
        interval=ENGINE_FUEL_INTERVAL,
        callback=update_steam_engines,
        idstring="engine_fuel",
        persistent=True
    )
    logger.log_info(f"✓ Engine ticker: every {ENGINE_FUEL_INTERVAL}s")
    
    logger.log_info("All TickerHandler systems initialized!")


# Utility function to check ticker status
def check_ticker_status():
    """
    Check and report status of all tickers.
    Useful for debugging.
    """
    all_tickers = TICKER_HANDLER.all()
    
    logger.log_info("=== Active Tickers ===")
    for ticker_data in all_tickers:
        if isinstance(ticker_data, dict):
            callback = ticker_data.get('callback', 'Unknown')
            interval = ticker_data.get('interval', 0)
            idstring = ticker_data.get('idstring', '')
            logger.log_info(f"- {idstring}: {callback} every {interval}s")
    
    return len(all_tickers)


# Convenience functions that match the get_date/get_time pattern from my original code
def get_season():
    """Get current season from custom_gametime."""
    year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
    
    for season_name, months in settings.SEASONS.items():
        if month in months:
            return season_name
    return "unknown"


def get_month_name(month):
    """Get month name from index."""
    if 0 <= month < len(settings.MONTH_NAMES):
        return settings.MONTH_NAMES[month]
    return f"Month {month}"


# Debug helper to test gametime
def test_gametime():
    """Test that custom gametime is working correctly."""
    from evennia.utils import logger
    try:
        year, month, week, day, hour, minute, second = custom_gametime.custom_gametime()
        season = get_season()
        month_name = get_month_name(month)
        
        logger.log_info("=== Custom Gametime Test ===")
        logger.log_info(f"Date: Year {year}, Month {month} ({month_name}), Day {day}")
        logger.log_info(f"Time: {hour:02d}:{minute:02d}:{second:02d}")
        logger.log_info(f"Season: {season}")
        logger.log_info("Custom gametime working correctly!")
        return True
    except Exception as e:
        logger.log_err(f"Custom gametime error: {e}")
        return False
