"""
Room

Rooms are simple containers that has no location of their own.

Extended Room Integration:
- Supports 13-month fantasy calendar with custom seasons
- 24-hour day/night cycle with 8 time-of-day periods
- State-based room descriptions (weather, events, etc)
- Room details (virtual lookable objects)
- Random room echoes

Season Mapping (matches settings.py):
- Spring (84 days): Frostmelt, Greenrise, Bloomtide
- Summer (112 days): Brightdawn, Sunpeak, Harvestwarm, Goldendays
- Autumn (84 days): Leaffall, Emberwind, Darkening
- Winter (84 days): Frosthold, Deepsnow, Icewane

Time of Day (8 periods for granular control):
- Night: 00:00 - 04:00, 20:00 - 24:00
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

    # Time of day definitions as fractions of the day (0.0 - 1.0)
    # 8 periods for granular control over descriptions
    # Note: 'night' uses list of tuples to cover two ranges
    times_of_day = {
        "night_early": (0.0, 0.167),  # 00:00-04:00
        "dawn": (0.167, 0.25),  # 04:00-06:00
        "morning": (0.25, 0.375),  # 06:00-09:00
        "day": (0.375, 0.5),  # 09:00-12:00
        "afternoon": (0.5, 0.625),  # 12:00-15:00
        "evening": (0.625, 0.75),  # 15:00-18:00
        "dusk": (0.75, 0.833),  # 18:00-20:00
        "night_late": (0.833, 1.0),  # 20:00-24:00
    }

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
