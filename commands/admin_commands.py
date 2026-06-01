from evennia import Command, GLOBAL_SCRIPTS
from world.weather import WEATHER_STATES, broadcast_weather_change


class CmdWeather(Command):
    """
    View or set the global weather (staff only).

    Usage:
      weather              - show current/previous weather
      weather <state>      - force a weather state and broadcast it

    Valid states: clear, raining, snowing, foggy

    Note: forcing bypasses the season filter on purpose (so you can test
    'snowing' in summer). The automatic roller still respects the season.
    """
    key = "weather"
    locks = "cmd:perm(Builder)"
    help_category = "Admin"

    def func(self):
        script = GLOBAL_SCRIPTS.weather
        arg = self.args.strip().lower()
        if not arg:
            self.caller.msg(
                f"Current weather: {script.db.current_weather} "
                f"(previous: {script.db.previous_weather})"
            )
            return
        if arg not in WEATHER_STATES:
            self.caller.msg(f"Invalid state. Choose: {', '.join(WEATHER_STATES)}")
            return
        script.db.previous_weather = script.db.current_weather
        script.db.current_weather = arg
        broadcast_weather_change(arg)
        self.caller.msg(f"Weather set to: {arg}")
