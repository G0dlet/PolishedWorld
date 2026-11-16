from django.conf import settings
from evennia import Command, GLOBAL_SCRIPTS
from evennia.utils.utils import inherits_from

from world import client_state
from world import sdesc as sdesc_rules
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


# The three facts `@appearance` writes, each with its vocabulary.
_APPEARANCE_CHOICES = {
    "sex": sdesc_rules.SEXES,
    "age": sdesc_rules.AGES,
    "feature": sdesc_rules.FEATURES,
}


class CmdAppearance(Command):
    """
    Set the appearance facts a character's short description is composed from.

    Usage:
      @appearance <character>
      @appearance <character> = sex:<sex>, age:<age>, feature:<feature>

    The first form shows the facts and the description as it reads now. The
    second writes them; a fact left out keeps its value, and a character
    without facts needs all three. Each value must come from the vocabulary:
    sex male, female or unstated; age young, adult or old; one feature.
    The build is read from SIZ, the rest from state and clothing. There is no
    free text (Names NM-T15, Rev 7 D3).
    """

    key = "@appearance"
    aliases = ["appearance"]
    locks = "cmd:perm(Builder)"
    help_category = "Admin"

    def parse(self):
        lhs, equals, rhs = self.args.partition("=")
        self.lhs = lhs.strip()
        self.rhs = rhs.strip() if equals else None

    def func(self):
        caller = self.caller
        if not self.lhs:
            caller.msg(f"Usage: {self.key} <character> [= sex:<s>, age:<a>, feature:<f>]")
            return
        target = caller.search(self.lhs, global_search=True)
        if not target:
            return  # the search has told the caller
        if not inherits_from(target, settings.BASE_CHARACTER_TYPECLASS):
            caller.msg(f"{target.key} is not a character.")
            return
        if self.rhs is None:
            caller.msg(self._shown(target))
            return

        facts = sdesc_rules.facts_of(target) or {}
        for part in self.rhs.split(","):
            name, colon, value = part.partition(":")
            name, value = name.strip().lower(), value.strip().lower()
            if not colon or name not in _APPEARANCE_CHOICES:
                caller.msg(f"Write each fact as name:value, with name one of "
                           f"{', '.join(_APPEARANCE_CHOICES)}.")
                return
            if value not in _APPEARANCE_CHOICES[name]:
                caller.msg(f"{value or 'Nothing'} is not a {name}. Choose one of: "
                           f"{', '.join(_APPEARANCE_CHOICES[name])}.")
                return
            facts[name] = value
        missing = [name for name in _APPEARANCE_CHOICES if name not in facts]
        if missing:
            caller.msg(f"{target.key} has no appearance yet: give {', '.join(missing)} too.")
            return

        target.db.appearance = facts
        target.sdesc.forget()
        caller.msg(self._shown(target))
        if target.location:
            client_state.push_room(target.location)

    @staticmethod
    def _shown(target):
        facts = sdesc_rules.facts_of(target)
        if facts is None:
            return f"{target.key} has no appearance facts and reads as {target.sdesc.get()}."
        listed = ", ".join(f"{name}:{facts[name]}" for name in _APPEARANCE_CHOICES)
        return f"{target.key} ({listed}) reads as {target.sdesc.get()}."
