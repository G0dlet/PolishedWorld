"""
Room

Rooms are simple containers that has no location of their own.

Extended Room Integration:
- Supports 13-month fantasy calendar with custom seasons
- 24-hour day/night cycle with 7 time-of-day periods
- State-based room descriptions (weather, events, etc)
- Room details (virtual lookable objects)
- Random room echoes

Time/Season detection:
    All time-of-day and season queries delegate to
    world/gametime_utils.py, which is the single source of truth
    for in-game time. ExtendedRoom's built-in detection assumes a
    12-month real-world calendar and would break on our 13-month
    year, so we override get_time_of_day() and get_season() below.

Season Mapping (matches settings.py):
- Spring (84 days): Frostmelt, Greenrise, Bloomtide
- Summer (112 days): Brightdawn, Sunpeak, Harvestwarm, Goldendays
- Autumn (84 days): Leaffall, Emberwind, Darkening
- Winter (84 days): Frosthold, Deepsnow, Icewane

Time of Day (7 periods, defined canonically in world/gametime_utils.py):
- Night: 20:00 - 04:00 (wraps midnight)
- Dawn: 04:00 - 06:00
- Morning: 06:00 - 09:00
- Day: 09:00 - 12:00
- Afternoon: 12:00 - 15:00
- Evening: 15:00 - 18:00
- Dusk: 18:00 - 20:00

Description Priority (from most to least specific):
1. Time + Season + State (e.g., "night" + "winter" + "snowing")
2. Time + Season (e.g., "morning" + "spring")
3. Season + State (e.g., "summer" + "hot")
4. Time only (e.g., "afternoon")
5. Season only (e.g., "autumn")
6. State only (e.g., "raining")
7. Base description (fallback)
"""

from evennia.objects.objects import DefaultRoom
from evennia.contrib.grid.extended_room import ExtendedRoom

from .objects import ObjectParent

from world import gametime_utils
from world import weather as weather_logic


class Room(ObjectParent, ExtendedRoom, DefaultRoom):
    """
    Extended Room with seasonal and time-of-day descriptions.

    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.

    Calendar System:
    ----------------
    - 13 months per year (not 12)
    - 28 days per month (4 weeks)
    - 364 days per year total
    - Extended summer season (4 months instead of 3)

    Usage Examples:
    ---------------

    Setting seasonal descriptions:
        @desc/spring The meadow bursts with colorful wildflowers.
        @desc/summer Dry grass crunches beneath your feet in the heat.
        @desc/autumn Red and gold leaves carpet the ground.
        @desc/winter Fresh snow blankets everything in pristine white.

    Setting time-of-day descriptions:
        @desc/dawn The first light of dawn paints the sky pink and gold.
        @desc/morning The morning sun illuminates the clearing.
        @desc/afternoon The midday heat shimmers off the rocks.
        @desc/dusk Long shadows stretch across the ground.
        @desc/night The stars shine brightly overhead.

    Combining time and season (most specific):
        @desc/morning/spring The dawn chorus fills the air as birds welcome spring.
        @desc/night/winter The frozen stars glitter in the cold winter night.

    Using state-based embedded tags:
        @desc A forest clearing.
              $state(morning, Morning mist rises from the damp earth.)
              $state(night, Moonlight filters through the canopy above.)
              $state(raining, Rain drips from the leaves all around.)
              $state(snowing, Snowflakes drift down through the branches.)

    Adding room details (virtual lookable objects):
        detail tree = An ancient oak with carved initials: "PW 2024"
        detail stream = Crystal-clear water burbles over smooth stones.
        detail sky = $state(dawn, The sky glows orange and pink.)
                     $state(night, Stars glitter like diamonds.)

    Setting room states (weather, conditions):
        roomstate flooded   (toggle a custom state on/off)
        @desc/flooded Water covers the floor ankle-deep.
        roomstate raining   (weather system will do this automatically)
        @desc/raining Rain falls steadily all around.

    Adding random atmospheric echoes:
        @py self.location.db.room_messages = ["A bird calls.", "Wind rustles leaves."]
        @py self.location.room_message_rate = 120  # seconds between messages
        @py self.location.start_repeat_broadcast_messages()

    Querying room state:
        time                        # Shows current time and season
        @py self.location.get_time_and_season()  # Returns ('morning', 'spring')
        @py self.location.get_season()           # Returns 'spring'
        @py self.location.get_time_of_day()      # Returns 'morning'

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects.
    """

    # ============================================================
    # Calendar Configuration (matches settings.py)
    # ============================================================

    months_per_year = 13
    hours_per_day = 24

    # Season definitions as fractions of the year (0.0 - 1.0)
    # Based on 364-day year (13 months × 28 days)
    # Matches SEASON_MONTHS from settings.py:
    #   Spring: [1, 2, 3]    = Frostmelt, Greenrise, Bloomtide
    #   Summer: [4, 5, 6, 7] = Brightdawn, Sunpeak, Harvestwarm, Goldendays
    #   Autumn: [8, 9, 10]   = Leaffall, Emberwind, Darkening
    #   Winter: [11, 12, 13] = Frosthold, Deepsnow, Icewane
    seasons_per_year = {
        "spring": (0.0, 84 / 364),  # Days 1-84 (Months 1-3)
        "summer": (84 / 364, 196 / 364),  # Days 85-196 (Months 4-7) ← EXTENDED
        "autumn": (196 / 364, 280 / 364),  # Days 197-280 (Months 8-10)
        "winter": (280 / 364, 1.0),  # Days 281-364 (Months 11-13)
    }

    # Time of day definitions, kept here for ExtendedRoom compatibility
    # (e.g. so the @desc command recognizes these period names).
    # The CANONICAL detection logic lives in world/gametime_utils.py;
    # see get_time_of_day() override below.
    #
    # 7 periods. `night` wraps midnight (20:00-04:00) but ExtendedRoom
    # expects a single (start, end) tuple per key, so we list the
    # 20:00-24:00 portion here as a placeholder. The full wrapping
    # range is implemented in gametime_utils.TIMES_OF_DAY.
    times_of_day = {
        "night":     (20 / 24, 1.0),    # placeholder; full range wraps
        "dawn":      (4 / 24, 6 / 24),  # 04:00-06:00
        "morning":   (6 / 24, 9 / 24),  # 06:00-09:00
        "day":       (9 / 24, 12 / 24), # 09:00-12:00
        "afternoon": (12 / 24, 15 / 24),# 12:00-15:00
        "evening":   (15 / 24, 18 / 24),# 15:00-18:00
        "dusk":      (18 / 24, 20 / 24),# 18:00-20:00
    }

    # ============================================================
    # Time/Season Overrides — delegate to world/gametime_utils
    # ============================================================
    # ExtendedRoom's default get_time_of_day() and get_season() use
    # evennia.utils.gametime + datetime.fromtimestamp, which assumes
    # a 12-month real-world calendar and breaks on our 13-month year
    # (datetime cannot represent month=13).
    #
    # We override both to delegate to gametime_utils, which wraps
    # custom_gametime() and applies our calendar conventions.

    def get_time_of_day(self):
        """
        Return the current time-of-day period name as a string.

        One of: 'night', 'dawn', 'morning', 'day',
        'afternoon', 'evening', 'dusk'.

        Used by ExtendedRoom for selecting time-based descriptions
        (e.g. desc_morning, $timeofday(night, ...) tags).
        """
        return gametime_utils.get_time_of_day()

    def get_season(self):
        """
        Return the current season name as a string.

        One of: 'spring', 'summer', 'autumn', 'winter'.

        Used by ExtendedRoom for selecting seasonal descriptions
        (e.g. desc_winter, $state(summer, ...) tags).
        """
        return gametime_utils.get_season()

    @property
    def room_states(self):
        """
        Override: dynamically include the current time-of-day and
        season alongside manually-set room_state tags.

        Why this exists:
            ExtendedRoom's get_stateful_desc() and $state() FuncParser
            both check self.room_states (tag-based). The contrib does
            NOT automatically tag rooms with the current time-of-day;
            it only consults get_season() as a fallback in Stage 3 of
            the priority chain. That means desc_morning, desc_night,
            etc. never fire unless something has set the tag manually.

            We inject the current period auto-detected via our
            gametime_utils overrides, so descriptions and $state()
            fragments work without requiring a global ticker to write
            tags into the database every period.

        Behavior:
            - Time-of-day is auto-added unless one is already pinned
              manually (via `roomstate dawn` etc.). Manual wins.
            - Season is auto-added unless one is already pinned
              manually. Manual wins.
            - Custom states (raining, flooded, etc.) are unaffected.

        Returns:
            list: sorted state names (parent's tags + auto-detected).
        """
        states = list(super().room_states)
        times = set(self.times_of_day.keys())
        seasons = set(self.seasons_per_year.keys())

        # Inject current time-of-day if no time is manually pinned
        if not any(s in times for s in states):
            current_time = self.get_time_of_day()
            if current_time:
                states.append(current_time)

        # Inject current season if no season is manually pinned
        if not any(s in seasons for s in states):
            current_season = self.get_season()
            if current_season:
                states.append(current_season)

        # Inject global weather unless a weather state is manually pinned
        # (microclimate override — e.g. a swamp pinned 'foggy' ignores the
        # global weather). 'clear' is never injected: clear weather = the
        # room's normal desc, no fragment.
        weathers = set(weather_logic.WEATHER_STATES)
        if not any(s in weathers for s in states):
            current_weather = weather_logic.get_current_weather()
            if current_weather and current_weather != "clear":
                states.append(current_weather)

        return states

    # ============================================================
    # Room Helper Methods
    # ============================================================

    def get_time_and_season(self):
        """
        Get current time and season information together.

        Convenience method for checking both at once.

        Returns:
            tuple: (time_of_day, season) as strings

        Example:
            >>> room.get_time_and_season()
            ('morning', 'spring')

            >>> time, season = self.location.get_time_and_season()
            >>> self.msg(f"It is {time} in {season}.")
        """
        return (self.get_time_of_day(), self.get_season())

    def get_display_name(self, looker, **kwargs):
        """
        Displays the name of the room.

        Can be customized to show current season or time in room name.

        Args:
            looker: The object looking at the room
            **kwargs: Additional arguments

        Returns:
            str: The room name
        """
        name = super().get_display_name(looker, **kwargs)

        # Uncomment to add season indicator to room names:
        # season = self.get_season().capitalize()
        # return f"{name} ({season})"

        # Or add both time and season:
        # time, season = self.get_time_and_season()
        # return f"{name} ({time.capitalize()}, {season.capitalize()})"

        return name

    def get_display_characters(self, looker, **kwargs):    # ← NY
        """
        Override: exclude statue-state characters from the Characters list.
        They are rendered under 'You see:' via get_display_things instead.
        """
        characters = [
            obj for obj in self.contents_get(content_type="character")
            if obj != looker
            and obj.access(looker, "view")
            and not getattr(obj, "is_statue", False)
        ]
        if not characters:
            return ""
        names = ", ".join(c.get_display_name(looker, **kwargs) for c in characters)
        return f"\n|wCharacters:|n {names}"

    def get_display_things(self, looker, **kwargs):        # ← NY
        """
        Override: append statue-state characters to the 'You see:' line
        so they appear as objects rather than characters.
        """
        base = super().get_display_things(looker, **kwargs)
        
        statues = [
            obj for obj in self.contents_get(content_type="character")
            if obj != looker
            and obj.access(looker, "view")
            and getattr(obj, "is_statue", False)
        ]
        if not statues:
            return base
        
        statue_names = ", ".join(
            s.get_display_name(looker, **kwargs) for s in statues
        )
        
        if base:
            return f"{base}, {statue_names}"
        return f"\n|wYou see:|n {statue_names}"

    def at_object_creation(self):
        """
        Called when room is first created.

        Sets up initial room state and properties.
        """
        super().at_object_creation()

        # Set a default description if none exists
        if not self.db.desc:
            self.db.desc = "You see nothing special."

        # Initialize room message rate (for atmospheric echoes)
        # 0 = disabled (no random messages)
        if not self.db.room_message_rate:
            self.db.room_message_rate = 0
