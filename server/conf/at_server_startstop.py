"""
Server startstop hooks

This module contains functions called by Evennia at various
points during its startup, reload and shutdown sequence. It
allows for customizing the server operation as desired.

This module must contain at least these global functions:

at_server_init()
at_server_start()
at_server_stop()
at_server_reload_start()
at_server_reload_stop()
at_server_cold_start()
at_server_cold_stop()

"""
from evennia import TICKER_HANDLER
from world.survival_ticker import deplete_all_survival_traits
from world.garment_wear import wear_all_garments

# Survival depletion ticker interval (seconds).
# 10s during dev for fast feedback; set to 600 before merging to main.
SURVIVAL_TICK_INTERVAL = 10   # TODO: 600 before merge

# Garment wear ticker interval (seconds). Prod target 10800 = 3 real-hours =
# 12 game-hours @ TIME_FACTOR 4, giving a common-worn garment ~3.6 game-weeks.
# 30s during dev so wear is observable in a session.
WEAR_TICK_INTERVAL = 30   # TODO: 10800 before merge

def at_server_init():
    """
    This is called first as the server is starting up, regardless of how.
    """
    pass


def at_server_start():
    """
    This is called every time the server starts up, regardless of
    how it was shut down.
    """
    # Survival depletion ticker. Re-adding with the same
    # interval+callback+idstring is idempotent (overwrites in place),
    # so running this on every start is safe.
    TICKER_HANDLER.add(
        interval=SURVIVAL_TICK_INTERVAL,
        callback=deplete_all_survival_traits,
        idstring="survival",
        persistent=True,
    )

    # Garment wear ticker. Same idempotent re-add pattern; distinct idstring.
    TICKER_HANDLER.add(
        interval=WEAR_TICK_INTERVAL,
        callback=wear_all_garments,
        idstring="garment_wear",
        persistent=True,
    )


def at_server_stop():
    """
    This is called just before the server is shut down, regardless
    of it is for a reload, reset or shutdown.
    """
    pass


def at_server_reload_start():
    """
    This is called only when server starts back up after a reload.
    """
    pass


def at_server_reload_stop():
    """
    This is called only time the server stops before a reload.
    """
    pass


def at_server_cold_start():
    """
    This is called only when the server starts "cold", i.e. after a
    shutdown or a reset.
    """
    pass


def at_server_cold_stop():
    """
    This is called only when the server goes down due to a shutdown or
    reset.
    """
    pass
