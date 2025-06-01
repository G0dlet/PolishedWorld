# typeclasses/rooms.py
"""
Rooms

Rooms are simple containers that has no location of their own.

This implementation extends the ExtendedRoom contrib to add:
- Dynamic descriptions based on time, weather, and season
- Resource nodes for gathering
- Weather states that affect gameplay
- Advanced visibility system for exits and objects
- Integration with the custom gametime system
"""

from evennia.contrib.grid.extended_room import ExtendedRoom as BaseExtendedRoom
from evennia.utils import list_to_string, lazy_property
from evennia import FuncParser
from django.conf import settings
import random
import re

from .objects import ObjectParent


class Room(ObjectParent, BaseExtendedRoom):
    """
    Extended Room with dynamic descriptions and visibility system.
    
    This room type supports:
    - Seasonal descriptions that change automatically
    - Weather states that affect visibility and gameplay
    - Resource nodes for gathering materials
    - Advanced visibility calculations for objects and exits
    - Integration with the custom gametime system
    
    The visibility system considers:
    - Time of day (day/night cycle)
    - Weather conditions (fog, rain, storm)
    - Object properties (size, luminosity, contrast)
    - Light sources carried by characters
    """
    
    # Override parent class settings to match our fantasy calendar
    months_per_year = 12
    hours_per_day = 24
    
    # Seasons aligned with our fantasy calendar
    seasons_per_year = {
        "winter": (11 / 12, 3 / 12),    # Darkening through Thawmoon
        "spring": (3 / 12, 6 / 12),     # Seedtime through Greentide
        "summer": (6 / 12, 9 / 12),     # Sunpeak through Goldfall
        "autumn": (9 / 12, 11 / 12),    # Harvestmoon through Dimming
    }
    
    # Time of day for descriptions (matching our TIME_OF_DAY setting)
    times_of_day = {
        "night": (22 / 24, 5 / 24),     # 22:00 - 04:59
        "dawn": (5 / 24, 7 / 24),       # 05:00 - 06:59
        "morning": (7 / 24, 12 / 24),   # 07:00 - 11:59
        "noon": (12 / 24, 14 / 24),     # 12:00 - 13:59
        "afternoon": (14 / 24, 17 / 24), # 14:00 - 16:59
        "dusk": (17 / 24, 19 / 24),     # 17:00 - 18:59
        "evening": (19 / 24, 22 / 24),  # 19:00 - 21:59
    }
    
    def at_object_creation(self):
        """
        Called when room is first created.
        Sets up resource nodes and default states.
        """
        super().at_object_creation()
        
        # Set default room type
        self.db.indoor = False  # Most rooms are outdoor by default
        
        # Initialize resource nodes
        self.db.resources = {
            "wood": {
                "base_amount": 5,
                "current": 5,
                "respawn_time": 3600,  # 1 real hour = 4 game hours
                "skill_required": "foraging",
                "min_skill": 0,
                "tool_required": None,
                "seasonal_modifier": {"spring": 1.2, "summer": 1.5, "autumn": 1.3, "winter": 0.5}
            },
            "stone": {
                "base_amount": 3,
                "current": 3,
                "respawn_time": 7200,  # 2 real hours
                "skill_required": "foraging",
                "min_skill": 0,
                "tool_required": "pickaxe",
                "seasonal_modifier": {"spring": 1.0, "summer": 1.0, "autumn": 1.0, "winter": 0.8}
            },
            "plants": {
                "base_amount": 8,
                "current": 8,
                "respawn_time": 1800,  # 30 minutes
                "skill_required": "foraging",
                "min_skill": 0,
                "tool_required": None,
                "seasonal_modifier": {"spring": 1.5, "summer": 2.0, "autumn": 1.0, "winter": 0.1}
            },
            "water": {
                "base_amount": -1,  # Unlimited
                "current": -1,
                "respawn_time": 0,
                "skill_required": None,
                "min_skill": 0,
                "tool_required": "container",
                "seasonal_modifier": {"spring": 1.2, "summer": 0.8, "autumn": 1.0, "winter": 1.5}
            }
        }
        
        # Weather states this room can have - include 'wind'
        self.db.possible_weather = ["clear", "cloudy", "rain", "storm", "fog", "snow", "wind"]
        
        # Set initial weather
        self.add_room_state("clear")
    
    def get_season(self):
        """
        Override to use our custom gametime system.
        
        Returns:
            str: Current season based on game calendar
        """
        from world.gametime_utils import get_current_season
        return get_current_season()
    
    def get_time_of_day(self):
        """
        Override to use our custom gametime system.
        
        Returns:
            str: Current time of day
        """
        from world.gametime_utils import get_time_of_day
        # The utility returns times that match our setup
        return get_time_of_day()
    
    def _get_funcparser(self, looker):
        """
        Get the FuncParser for handling $state() tags.
        Override to ensure our custom func_state works properly.
        """
        def custom_func_state(roomstate, *args, room=None, **kwargs):
            """Custom state function that properly handles states."""
            if not room:
                room = self
            
            roomstate = str(roomstate).lower()
            text = ", ".join(str(arg) for arg in args)
        
            # Check if state is active
            if roomstate in room.room_states or roomstate == room.get_time_of_day():
                return text
            elif roomstate == "default" and not room.room_states:
                return text
        
            return ""  # Return empty string if state not active
    
        return FuncParser(
            {"state": custom_func_state},
            looker=looker,
            room=self,
        )

    def get_current_weather(self):
        """
        Get the current weather states affecting this room.
        
        Returns:
            list: Active weather states
        """
        # Filter room states to only weather-related ones
        weather_states = []
        possible_weather = self.db.possible_weather or []
        
        for state in self.room_states:
            if state in possible_weather:
                weather_states.append(state)
        
        return weather_states if weather_states else ["clear"]
    
    def get_visibility_range(self, looker):
        """
        Calculate how many rooms away the looker can see from this room.
        
        Visibility is affected by:
        - Time of day (day=10, dusk/dawn=5, night=2)
        - Weather conditions (fog=1, storm=3, rain=7)
        - Indoor/outdoor status (indoor always has full visibility)
        - Light sources carried by the looker
        
        Args:
            looker (Character): The character trying to see
            
        Returns:
            int: Number of rooms visible in each direction (0-10)
        """
        # Base visibility for outdoor rooms during daytime
        base_visibility = 10
        
        # Indoor rooms always have full visibility
        if self.db.indoor:
            return base_visibility
        
        # Time of day affects visibility dramatically
        current_time = self.get_time_of_day()
        time_visibility = {
            "dawn": 5,      # Low sun angle creates long shadows
            "morning": 8,   # Good visibility as sun rises
            "noon": 10,     # Maximum visibility
            "afternoon": 8, # Still good visibility
            "dusk": 5,      # Sun setting reduces visibility
            "evening": 3,   # Twilight visibility
            "night": 2      # Minimal natural light
        }
        
        # Get base visibility from time
        visibility = time_visibility.get(current_time, 10)
        
        # Check for weather impacts (use the worst condition)
        weather_conditions = self.get_current_weather()
        weather_limits = {
            "fog": 1,        # Dense fog severely limits vision
            "storm": 3,      # Storm conditions with rain and wind
            "rain": 7,       # Light rain has minor impact
            "snow": 5,       # Snow reflects light but obscures distance
            "cloudy": 9,     # Overcast slightly reduces visibility
            "clear": 10      # No weather impediment
        }
        
        # Apply worst weather condition
        for condition in weather_conditions:
            if condition in weather_limits:
                visibility = min(visibility, weather_limits[condition])
        
        # Light sources help in darkness
        if current_time in ["night", "evening", "dusk", "dawn"]:
            # Check if looker has a light source
            for obj in looker.contents:
                if obj.db.is_light_source and obj.db.light_active:
                    # Light source provides minimum visibility of 5
                    visibility = max(visibility, 5)
                    break
        
        return visibility
    
    def get_resource_availability(self, resource_type):
        """
        Get the effective availability of a resource considering season and weather.
        
        Args:
            resource_type (str): Type of resource to check
            
        Returns:
            float: Multiplier for resource availability (0.0 - 2.0)
        """
        if resource_type not in self.db.resources:
            return 0.0
        
        resource = self.db.resources[resource_type]
        base_modifier = 1.0
        
        # Apply seasonal modifier
        season = self.get_season()
        seasonal_mods = resource.get("seasonal_modifier", {})
        base_modifier *= seasonal_mods.get(season, 1.0)
        
        # Apply weather modifiers
        weather = self.get_current_weather()
        if "storm" in weather or "snow" in weather:
            base_modifier *= 0.5  # Harsh weather reduces gathering
        elif "rain" in weather:
            base_modifier *= 0.8  # Light rain has minor impact
        
        # Special case: water is more available in rain/snow
        if resource_type == "water" and ("rain" in weather or "snow" in weather):
            base_modifier *= 2.0
        
        return base_modifier
    
    def calculate_object_visibility(self, obj, looker):
        """
        Calculate visibility chance for a specific object.
        
        Args:
            obj (Object): The object to check visibility for
            looker (Character): The character trying to see
            
        Returns:
            float: Visibility chance (0.0 - 1.0)
        """
        base_visibility = 1.0
        
        # Get object visibility properties
        size = obj.db.visibility_size or "normal"
        luminosity = obj.db.luminosity or "normal"
        contrast = obj.db.contrast or "normal"
        hidden = obj.db.hidden or False
        
        # Hidden objects require active searching
        if hidden:
            return 0.0
        
        # Size modifiers
        size_mods = {
            "tiny": 0.3,      # Coins, rings, small gems
            "small": 0.5,     # Keys, pouches, small tools
            "normal": 1.0,    # Standard objects
            "large": 1.2,     # Furniture, large containers
            "huge": 1.5       # Vehicles, structures
        }
        base_visibility *= size_mods.get(size, 1.0)
        
        # Time and weather affect visibility
        current_time = self.get_time_of_day()
        weather = self.get_current_weather()
        
        # Track if we have light for later calculations
        has_light = False
        
        # Darkness penalties
        if current_time in ["night", "evening"]:
            base_visibility *= 0.5
            
            # Dark objects are harder to see at night
            if contrast == "dark":
                base_visibility *= 0.7  # Additional -30%
            
            # Check for light sources FIRST before applying shiny bonus
            for item in looker.contents:
                if item.db.is_light_source and item.db.light_active:
                    has_light = True
                    # Light source dramatically improves visibility
                    base_visibility *= 3.0  # Triple visibility with light
                    break
            
            # Shiny objects easier to see with any light
            if luminosity == "shiny":
                if has_light:
                    base_visibility *= 1.2  # Additional +20% for shiny with light
                else:
                    base_visibility *= 1.5  # +50% for shiny in darkness (self-luminous)
        
        # Daylight bonuses
        elif current_time in ["noon", "morning", "afternoon"]:
            if luminosity == "shiny":
                base_visibility *= 1.2  # +20% in sunlight
        
        # Weather impacts
        if "fog" in weather:
            base_visibility *= 0.3
        elif "rain" in weather or "storm" in weather:
            base_visibility *= 0.7
        elif "snow" in weather:
            base_visibility *= 0.8
        
        # Camouflaged objects in matching environments
        if contrast == "camouflaged":
            # Determine if environment matches
            room_desc = self.db.desc or ""
            if any(word in room_desc.lower() for word in ["forest", "grass", "leaves"]):
                if obj.db.camouflage_type == "natural":
                    base_visibility *= 0.5
        
        return min(max(base_visibility, 0.0), 1.0)
    
    def get_visible_objects(self, looker, candidates=None):
        """
        Filter objects based on visibility.
        
        Args:
            looker (Character): The character looking
            candidates (list, optional): Objects to check. If None, use room contents
            
        Returns:
            list: Objects that are visible to the looker
        """
        if candidates is None:
            candidates = self.contents
        
        visible = []
        for obj in candidates:
            # Always see characters and exits
            if obj.is_typeclass("typeclasses.characters.Character") or \
               obj.is_typeclass("typeclasses.exits.Exit"):
                visible.append(obj)
                continue
            
            # Calculate visibility for other objects
            visibility_chance = self.calculate_object_visibility(obj, looker)
            
            # Always see obvious items
            if obj.db.visibility_size == "obvious":
                visible.append(obj)
            # Random chance for others based on visibility
            elif random.random() < visibility_chance:
                visible.append(obj)
        
        return visible
    
    def extract_resource(self, gatherer, resource_type, amount=1):
        """
        Attempt to extract resources from this room.
        
        Args:
            gatherer (Character): Character attempting to gather
            resource_type (str): Type of resource to gather
            amount (int): Amount to try to gather
            
        Returns:
            tuple: (success, actual_amount, skill_gain)
        """
        if resource_type not in self.db.resources:
            return (False, 0, 0)
        
        resource = self.db.resources[resource_type]
        
        # Check if resource is available
        current = resource.get("current", 0)
        if current == 0:
            return (False, 0, 0)
        
        # Check skill requirements
        skill_required = resource.get("skill_required")
        min_skill = resource.get("min_skill", 0)
        
        if skill_required:
            gatherer_skill = gatherer.get_skill_level(skill_required)[0] or 0
            if gatherer_skill < min_skill:
                gatherer.msg(f"You need at least {min_skill} {skill_required} to gather {resource_type} here.")
                return (False, 0, 0)
        
        # Check tool requirements
        tool_required = resource.get("tool_required")
        if tool_required:
            has_tool = any(obj.key.lower() == tool_required.lower() 
                          for obj in gatherer.contents)
            if not has_tool:
                gatherer.msg(f"You need a {tool_required} to gather {resource_type}.")
                return (False, 0, 0)
        
        # Calculate actual amount based on availability
        availability = self.get_resource_availability(resource_type)
        skill_bonus = 1.0
        if skill_required:
            skill_level = gatherer.get_skill_level(skill_required)[0] or 0
            skill_bonus = 1.0 + (skill_level / 100.0)  # Up to 2x at max skill
        
        # Determine actual gathered amount
        max_gather = min(amount, current) if current > 0 else amount
        actual_amount = int(max_gather * availability * skill_bonus)
        actual_amount = max(1, actual_amount)  # Always get at least 1 if successful
        
        # Update resource if not unlimited
        if current > 0:
            resource["current"] = max(0, current - actual_amount)
        
        # Calculate skill gain (more gain for harder resources)
        skill_gain = 1
        if skill_required and gatherer_skill < 100:
            difficulty_bonus = 1 + (min_skill / 20)  # Harder resources give more XP
            skill_gain = int(difficulty_bonus)
        
        return (True, actual_amount, skill_gain)
    
    def get_display_exits(self, looker, **kwargs):
        """
        Get the exit display, considering visibility range.
        
        This extends the default to only show exits within visibility range.
        """
        if not looker:
            return ""
        
        # Get base visibility range
        visibility_range = self.get_visibility_range(looker)
        
        # Get all exits
        exits = []
        for exit in self.exits:
            # For exits, check if we can see into the destination
            if visibility_range > 0:
                exits.append(exit)
        
        if not exits:
            return ""
        
        # Format the exit display
        exit_strings = []
        for exit in exits:
            # Check if we can see what's beyond this exit
            can_see_beyond = visibility_range > 1
            if can_see_beyond and exit.destination:
                # Might show a preview of what's beyond
                exit_strings.append(f"|c{exit.key}|n")
            else:
                exit_strings.append(f"|C{exit.key}|n")
        
        return f"|wExits:|n {list_to_string(exit_strings)}"
    
    def get_display_things(self, looker, **kwargs):
        """
        Get the 'things' component of the object description.
        
        This filters objects based on visibility before display.
        """
        if not looker:
            return ""
        
        # Get visible objects only
        things = []
        for thing in self.contents_get(exclude=looker):
            # Skip exits (handled separately)
            if thing.destination:
                continue
                
            # Check visibility
            if thing in self.get_visible_objects(looker, [thing]):
                things.append(thing)
        
        if not things:
            return ""
        
        # Group by visibility category for better display
        obvious_things = []
        normal_things = []
        hard_to_see = []
        
        for thing in things:
            visibility = self.calculate_object_visibility(thing, looker)
            if thing.db.visibility_size == "obvious" or visibility > 0.8:
                obvious_things.append(thing)
            elif visibility > 0.5:
                normal_things.append(thing)
            else:
                hard_to_see.append(thing)
        
        thing_strings = []
        
        # Format different visibility groups
        if obvious_things:
            for thing in obvious_things:
                thing_strings.append(thing.get_display_name(looker, **kwargs))
        
        if normal_things:
            for thing in normal_things:
                thing_strings.append(thing.get_display_name(looker, **kwargs))
        
        if hard_to_see:
            # These are barely visible
            for thing in hard_to_see:
                thing_strings.append(f"|x{thing.get_display_name(looker, **kwargs)}|n")
        
        return f"|wYou see:|n {list_to_string(thing_strings)}"
    
    def return_appearance(self, looker, **kwargs):
        """
        Main appearance method - including visibility filtering.
        """
        if not looker:
            return ""
        
        # Get the dynamic description based on time/season/weather
        visible_string = f"|c{self.get_display_name(looker, **kwargs)}|n"
        desc = self.get_display_desc(looker, **kwargs)
        
        # Add current conditions to description
        time_of_day = self.get_time_of_day()
        weather = self.get_current_weather()
        season = self.get_season()
        
        # Add atmospheric conditions
        condition_string = f"\n|xTime: {time_of_day.title()}, Season: {season.title()}, Weather: {', '.join(weather).title()}|n"
        
        # Get exits and things with visibility filtering
        exits = self.get_display_exits(looker, **kwargs)
        things = self.get_display_things(looker, **kwargs)
        
        # Build final appearance
        string = f"{visible_string}\n{desc}{condition_string}"
        if exits:
            string += f"\n{exits}"
        if things:
            string += f"\n{things}"
        
        return string
