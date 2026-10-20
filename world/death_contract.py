"""
The death contract, in player words (BACKLOG: Death contract surfaces).

The death-consequence policy (roadmap decision log, Death-consequence policy)
promises a dead player three things: the body lies where they fell, it keeps
their belongings for days -- owner-first for a while -- and Death's Chill
passes. Two surfaces say so: the line `at_character_death()` sends, and the
`help death` topic. Both are built HERE, from the live constants, so they cannot
drift apart or drift from the code: change `_PLAYER_GRACE_HOURS`, the expiry
window, the decay tables or `DeathWeakness` and both texts follow on the next
reload.

Numbers are derived, never typed:

    grace         PlayerCorpse._PLAYER_GRACE_HOURS (unscaled game-hours)
    shortest keep PlayerCorpse._PLAYER_EXPIRY_HOURS / the fastest decay
                  modifier the tables allow -- a floor that is true in any
                  season and weather, which is why the text says "at least"
    real time     game time / settings.TIME_FACTOR

Every span is rounded DOWN (`format_game_span`). The texts make promises, and a
floor never promises more than the code keeps.

Import note: `typeclasses.corpse` imports this module lazily (inside
`PlayerCorpse.return_appearance`), because this module imports it at the top.
"""

from django.conf import settings

from typeclasses import corpse as _corpse
from typeclasses.corpse import PlayerCorpse
from world.survival_buffs import DeathWeakness

HOURS_PER_GAME_DAY = 24


def fastest_decay_modifier():
    """
    The largest decay multiplier the season and weather tables can produce.

    Absent seasons and weathers are neutral (1.0), hence the 1.0 floor in each
    max(). Cold storage only slows decay (x0.25), so it never raises the bound.
    """
    season = max([1.0, *_corpse._SEASON_MODIFIERS.values()])
    weather = max([1.0, *_corpse._WEATHER_MODIFIERS.values()])
    return season * weather


def shortest_keep_game_hours():
    """Unscaled game-hours a player corpse lasts in the fastest-decaying world."""
    return PlayerCorpse._PLAYER_EXPIRY_HOURS / fastest_decay_modifier()


def grace_game_hours():
    """Unscaled game-hours during which only the owner may loot."""
    return PlayerCorpse._PLAYER_GRACE_HOURS


def _plural(count, word):
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def format_game_span(hours):
    """
    Render game-hours as whole in-game days, or whole hours under a day.

    Rounds down: 95.9 h is "3 in-game days", 0.5 h is "less than an in-game
    hour".
    """
    hours = max(0.0, float(hours))
    if hours >= HOURS_PER_GAME_DAY:
        return _plural(int(hours // HOURS_PER_GAME_DAY), "in-game day")
    if hours >= 1:
        return _plural(int(hours), "in-game hour")
    return "less than an in-game hour"


def format_real_span(game_hours):
    """Render game-hours as whole real hours at the configured TIME_FACTOR."""
    real_hours = int(max(0.0, float(game_hours)) // settings.TIME_FACTOR)
    return _plural(real_hours, "real hour")


def death_message(body_room=None):
    """
    The lines a character receives on dying, as one string.

    Args:
        body_room (Object | None): the room the corpse lies in, or None when no
            corpse was made (no location, or the spawn failed). Without a body
            the text claims none, and says the belongings stayed with the
            character -- which is what `at_character_death()` does then.

    Returns:
        str: "You have died." (unchanged first line, so T13's ordering and the
        comment that quotes it stay true) followed by the contract line.
    """
    chill = DeathWeakness.name
    if body_room is not None:
        contract = (
            f"Your body lies at {body_room.key}. It keeps your belongings for at "
            f"least {format_game_span(shortest_keep_game_hours())}, and for the "
            f"first {format_game_span(grace_game_hours())} only you may take "
            f"from it. {chill} will pass. See |whelp death|n."
        )
    else:
        contract = (
            f"You leave no body behind; what you carried is still with you. "
            f"{chill} will pass. See |whelp death|n."
        )
    return f"|RYou have died.|n\n{contract}"


def help_text():
    """The full `help death` text, built from the same values as `death_message`."""
    keep = shortest_keep_game_hours()
    grace = grace_game_hours()
    chill_minutes = int(DeathWeakness.duration // 60)
    return (
        "Death is not the end of your character.\n\n"
        "When you die, your body stays where you fell, and everything you "
        "carried (bar the rare soulbound item) goes into it. You return to life at your respawn point. "
        "Coin in your purse stays with you.\n\n"
        f"|wYour body|n keeps your belongings for at least "
        f"{format_game_span(keep)} (about {format_real_span(keep)}); longer in "
        "the cold, shorter in summer heat and rain. Then it crumbles, and "
        "whatever is still inside is lost.\n\n"
        f"|wYour claim|n: for the first {format_game_span(grace)} (about "
        f"{format_real_span(grace)}) only you may take from your body. After "
        "that, anyone who finds it may. Looking at the body shows how long "
        "your claim has left.\n\n"
        f"|w{DeathWeakness.name}|n: a weakness that passes on its own after "
        f"about {_plural(chill_minutes, 'real minute')}.\n\n"
        "The world's clock stands still while the server is down, so downtime "
        "does not shorten either window.\n\n"
        "To take something back: |wget <item> from corpse of <your name>|n"
    )


def help_entry():
    """The file-help dict for `world/help_entries.py`."""
    return {
        "key": "death",
        "aliases": ["dying"],
        "category": "Survival",
        "text": help_text(),
    }
