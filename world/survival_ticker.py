"""
Global survival ticker callback.

Registered with Evennia's TICKER_HANDLER (see server/conf/at_server_startstop.py).
A single module-level callable iterates all currently puppeted characters and
applies survival depletion. Module-level (not a closure/lambda) so the callback
is picklable, which TICKER_HANDLER requires for persistent tickers.

This task (1.2) only enumerates + logs; depletion lands in Task 2.1.
"""

from evennia import SESSION_HANDLER
from evennia.utils import logger


def deplete_all_survival_traits():
    """
    Tick callback: process survival depletion for every online character.

    Iterates logged-in sessions only (get_sessions() filters on logged_in),
    skips logged-in-but-OOC sessions (puppet is None), and dedupes characters
    that have more than one session connected (multisession modes 2-3) so a
    character is never depleted twice in a single tick.

    Offline characters are never touched: they have no session, so they do
    not appear in this loop and take no depletion or damage while logged out.
    """
    seen = set()
    for sess in SESSION_HANDLER.get_sessions():
        char = getattr(sess, "puppet", None)
        if not char or char.id in seen:
            continue
        seen.add(char.id)
        logger.log_info(f"[survival] tick for {char.key} (#{char.id})")
