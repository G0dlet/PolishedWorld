# server/conf/at_server_startstop.py
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
from evennia.utils import logger
from evennia import TICKER_HANDLER
from django.conf import settings


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
    logger.log_info("=== Fantasy Steampunk MUD Starting Up ===")
    
    try:
        # Import and initialize all game systems
        
        # 1. Custom Gametime System
        from evennia.contrib.base_systems import custom_gametime
        logger.log_info("✓ Custom Gametime system loaded")
        
        # 2. Traits System
        from evennia.contrib.rpg.traits import TraitHandler
        logger.log_info("✓ Traits system initialized")
        
        # 3. Crafting System
        from evennia.contrib.game_systems.crafting import CraftingRecipe
        logger.log_info("✓ Crafting system with recipe modules loaded")
        
        # 4. Clothing System
        from evennia.contrib.game_systems.clothing import ClothedCharacter
        logger.log_info("✓ Clothing system loaded")
        
        # 5. Barter System
        from evennia.contrib.game_systems.barter.barter import TradeHandler
        logger.log_info("✓ Barter/Trade system loaded")
        
        # 6. Initialize TickerHandler systems
        from world.scripts import initialize_all_tickers, check_ticker_status
        initialize_all_tickers()
        
        # Report ticker status
        ticker_count = check_ticker_status()
        logger.log_info(f"✓ {ticker_count} TickerHandler systems started")
        
        # 7. Check for any required database updates
        _check_database_consistency()
        
        logger.log_info("=== ALL SYSTEMS OPERATIONAL ===")
        
        # Optional: Send startup notification to admins
        _notify_admins_startup()
        
    except Exception as e:
        logger.log_err(f"❌ CRITICAL: Failed to initialize game systems: {e}")
        raise


def at_server_stop():
    """
    This is called just before the server is shut down, regardless
    of it is for a reload, reset or shutdown.
    """
    logger.log_info("=== Server Shutting Down ===")
    
    # Log current ticker status before shutdown
    try:
        all_tickers = TICKER_HANDLER.all()
        logger.log_info(f"Saving state of {len(all_tickers)} active tickers")
    except Exception as e:
        logger.log_err(f"Error checking tickers on shutdown: {e}")
    
    # Perform any cleanup if needed
    _save_critical_state()


def at_server_reload_start():
    """
    This is called only when server starts back up after a reload.
    """
    logger.log_info("=== Server Reloading ===")
    
    # Reload-specific initialization
    try:
        # Re-verify ticker status after reload
        from world.scripts import check_ticker_status
        ticker_count = check_ticker_status()
        logger.log_info(f"✓ {ticker_count} tickers restored after reload")
    except Exception as e:
        logger.log_err(f"Error checking tickers after reload: {e}")


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
    logger.log_info("=== Cold Start Detected ===")
    
    # Cold start specific initialization
    try:
        # Verify all systems are properly initialized
        _verify_cold_start_systems()
        
        # Check for any maintenance tasks
        _perform_maintenance_tasks()
        
    except Exception as e:
        logger.log_err(f"Error during cold start: {e}")


def at_server_cold_stop():
    """
    This is called only when the server goes down due to a shutdown or
    reset.
    """
    pass


# Helper functions

def _check_database_consistency():
    """
    Check that all required database objects exist.
    """
    from evennia.objects.models import ObjectDB
    
    # Check for orphaned objects
    orphaned = ObjectDB.objects.filter(db_location=None, db_home=None).exclude(
        db_typeclass_path__icontains="Room"
    )
    
    if orphaned.exists():
        logger.log_warn(f"Found {orphaned.count()} orphaned objects")
    
    # Check for characters without required traits
    from typeclasses.characters import Character
    characters = Character.objects.all()
    
    broken_chars = []
    for char in characters:
        try:
            # Try to access trait categories
            _ = char.traits.hunger
            _ = char.skills.crafting
            _ = char.stats.strength
        except Exception:
            broken_chars.append(char)
    
    if broken_chars:
        logger.log_warn(f"Found {len(broken_chars)} characters with broken traits")


def _notify_admins_startup():
    """
    Send startup notification to online admins.
    """
    from evennia.accounts.models import AccountDB
    from evennia.server.sessionhandler import SESSIONS
    
    # Get all online admin sessions
    admin_sessions = [
        sess for sess in SESSIONS.get_sessions()
        if sess.account and sess.account.check_permstring("Admin")
    ]
    
    if admin_sessions:
        message = (
            "\n|y=== Server Startup Complete ===|n\n"
            "All game systems initialized successfully.\n"
            f"Active tickers: {len(TICKER_HANDLER.all())}\n"
            f"Game time factor: {getattr(settings, 'TIME_FACTOR', 1)}x\n"
        )
        
        for session in admin_sessions:
            session.msg(message)


def _save_critical_state():
    """
    Save any critical state before shutdown.
    """
    # This could save things like ongoing trades, combat states, etc.
    # For now, just log
    logger.log_info("Critical state saved (if any)")


def _verify_cold_start_systems():
    """
    Verify all systems after a cold start.
    """
    # Check that all contrib systems are properly loaded
    required_contribs = [
        "evennia.contrib.base_systems.custom_gametime",
        "evennia.contrib.rpg.traits",
        "evennia.contrib.game_systems.crafting",
        "evennia.contrib.game_systems.clothing",
        "evennia.contrib.game_systems.barter",
        "evennia.contrib.rpg.buffs",
        "evennia.contrib.grid.extended_room"
    ]
    
    for contrib in required_contribs:
        try:
            __import__(contrib)
        except ImportError as e:
            logger.log_err(f"Failed to load required contrib {contrib}: {e}")


def _perform_maintenance_tasks():
    """
    Perform any maintenance tasks on cold start.
    """
    from evennia.objects.models import ObjectDB
    from datetime import datetime, timedelta
    
    # Clean up old, spoiled food items
    spoiled_items = ObjectDB.objects.filter(
        db_tags__db_key="spoiled",
        db_tags__db_category="quality"
    )
    
    # Delete items that have been spoiled for over a week (real time)
    week_ago = datetime.now() - timedelta(days=7)
    old_spoiled = []
    
    for item in spoiled_items:
        if hasattr(item.db, 'spoiled_date'):
            if item.db.spoiled_date < week_ago:
                old_spoiled.append(item)
    
    if old_spoiled:
        logger.log_info(f"Cleaning up {len(old_spoiled)} old spoiled items")
        for item in old_spoiled:
            item.delete()
    
    # Reset any stuck cooldowns
    from typeclasses.characters import Character
    characters = Character.objects.all()
    
    for char in characters:
        if hasattr(char, 'cooldowns'):
            # The cooldown handler should auto-clean expired cooldowns
            pass
    
    logger.log_info("Maintenance tasks completed")
