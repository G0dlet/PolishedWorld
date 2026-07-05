"""
Scripts

Scripts are powerful jacks-of-all-trades. They have no in-game
existence and can be used to represent persistent game systems in some
circumstances. Scripts can also have a time component that allows them
to "fire" regularly or a limited number of times.

There is generally no "tree" of Scripts inheriting from each other.
Rather, each script tends to inherit from the base Script class and
just overloads its hooks to have it perform its function.

"""

from collections.abc import Mapping
from evennia.scripts.scripts import DefaultScript
from evennia.utils import logger
from evennia.prototypes.spawner import spawn
from evennia.utils.search import search_tag
from world import gametime_utils
from world import weather as weather_logic


class Script(DefaultScript):
    """
    This is the base TypeClass for all Scripts. Scripts describe
    all entities/systems without a physical existence in the game world
    that require database storage (like an economic system or
    combat tracker). They
    can also have a timer/ticker component.

    A script type is customized by redefining some or all of its hook
    methods and variables.

    * available properties (check docs for full listing, this could be
      outdated).

     key (string) - name of object
     name (string)- same as key
     aliases (list of strings) - aliases to the object. Will be saved
              to database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     desc (string)      - optional description of script, shown in listings
     obj (Object)       - optional object that this script is connected to
                          and acts on (set automatically by obj.scripts.add())
     interval (int)     - how often script should run, in seconds. <0 turns
                          off ticker
     start_delay (bool) - if the script should start repeating right away or
                          wait self.interval seconds
     repeats (int)      - how many times the script should repeat before
                          stopping. 0 means infinite repeats
     persistent (bool)  - if script should survive a server shutdown or not
     is_active (bool)   - if script is currently running

    * Handlers

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this
                        self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not
                        create a database entry when storing data

    * Helper methods

     create(key, **kwargs)
     start() - start script (this usually happens automatically at creation
               and obj.script.add() etc)
     stop()  - stop script, and delete it
     pause() - put the script on hold, until unpause() is called. If script
               is persistent, the pause state will survive a shutdown.
     unpause() - restart a previously paused script. The script will continue
                 from the paused timer (but at_start() will be called).
     time_until_next_repeat() - if a timed script (interval>0), returns time
                 until next tick

    * Hook methods (should also include self as the first argument):

     at_script_creation() - called only once, when an object of this
                            class is first created.
     is_valid() - is called to check if the script is valid to be running
                  at the current time. If is_valid() returns False, the running
                  script is stopped and removed from the game. You can use this
                  to check state changes (i.e. an script tracking some combat
                  stats at regular intervals is only valid to run while there is
                  actual combat going on).
      at_start() - Called every time the script is started, which for persistent
                  scripts is at least once every server start. Note that this is
                  unaffected by self.delay_start, which only delays the first
                  call to at_repeat().
      at_repeat() - Called every self.interval seconds. It will be called
                  immediately upon launch unless self.delay_start is True, which
                  will delay the first call of this method by self.interval
                  seconds. If self.interval==0, this method will never
                  be called.
      at_pause()
      at_stop() - Called as the script object is stopped and is about to be
                  removed from the game, e.g. because is_valid() returned False.
      at_script_delete()
      at_server_reload() - Called when server reloads. Can be used to
                  save temporary variables you want should survive a reload.
      at_server_shutdown() - called at a full server shutdown.
      at_server_start()

    """

    pass


class WeatherScript(Script):
    """
    Global weather system. Registered via settings.GLOBAL_SCRIPTS, so it
    is auto-created on first server start and re-created if ever deleted.

    State (persistent Attributes):
        db.current_weather  (str): the active global weather state.
        db.previous_weather (str): the state before the last change.

    This is a *global* script (not attached to an object), so self.obj is
    None — we never use self.obj.msg_contents. Broadcasting is added in
    Task 1.3.
    """

    def at_script_creation(self):
        self.key = "weather"
        self.desc = "Global weather system"
        # interval / persistent / repeats come from GLOBAL_SCRIPTS settings,
        # which are authoritative; we only seed initial state here.
        if self.db.current_weather is None:
            self.db.current_weather = "clear"
            self.db.previous_weather = "clear"

    def at_repeat(self):
        """Called every `interval` real seconds while the timer runs."""
        try:
            season = gametime_utils.get_season()
            old = self.db.current_weather
            new = weather_logic.roll_weather(season, current=old)
            if new != old:
                self.db.previous_weather = old
                self.db.current_weather = new
                weather_logic.broadcast_weather_change(new)
        except Exception:
            logger.log_trace()


class CreatureSpawnScript(Script):
    """
    Global respawn ticker. Registered via settings.GLOBAL_SCRIPTS, so it is
    auto-created on first server start and re-created if ever deleted.

    Keeps creature populations topped up in rooms that opt in. A room opts in
    with two pieces of config:

        room.db.spawn_creatures = {"rabbit": 3}   # prototype_key -> target count
        room.tags.add("creature_spawn", category="room_flag")

    The tag is what makes this scale: the script queries only flagged rooms via
    search_tag, never the whole world -- important as the map grows toward the
    long-term Daggerfall-scale vision. The dict key is a creature prototype_key,
    which by convention equals that creature's species tag (rabbit carries
    tags=[("rabbit", "creature")]), so a species can be counted cheaply.

    Spawning is *sparse*: at most one creature per species per room per tick, so
    a depleted room refills gradually instead of a whole herd popping in at once.
    """

    def at_script_creation(self):
        self.key = "creature_spawn"
        self.desc = "Maintains creature populations in spawn-flagged rooms"

    def at_repeat(self):
        """Top up each flagged room by at most one creature per species."""
        try:
            for room in search_tag("creature_spawn", category="room_flag"):
                config = room.db.spawn_creatures
                if not isinstance(config, Mapping):
                    continue
                for prototype_key, target in config.items():
                    if not isinstance(target, int) or target <= 0:
                        continue
                    if self._count_species(room, prototype_key) < target:
                        self._spawn_one(prototype_key, room)
        except Exception:
            # One bad room must never kill the ticker for everyone else.
            logger.log_trace()

    @staticmethod
    def _count_species(room, species):
        """Living creatures of `species` (by species tag) currently in `room`."""
        return sum(
            1 for obj in room.contents
            if obj.tags.has(species, category="creature")
        )

    @staticmethod
    def _spawn_one(species, room):
        """Spawn a single creature of `species` into `room`, silently."""
        spawned = spawn(species)
        if not spawned:
            logger.log_err(f"CreatureSpawnScript: unknown prototype '{species}'")
            return
        # Direct location set = silent placement (no 'a rabbit arrives' spam every
        # interval). Bypassing move hooks is intentional for ambient spawning.
        spawned[0].location = room
