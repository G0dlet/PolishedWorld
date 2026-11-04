"""
world/activity_log.py
=====================
One JSON line per economic event, appended to ``server/logs/activity.jsonl``
(Launch Minimum LM2, task L2.1).

What it is for:
    The alpha has to report what players gathered, made, traded and for how
    much (LM1: the minimum is measurement). ``world/economy_log.py`` records
    only mint and burn; this file records everything else, written by the
    code that performs each event (L2.2 wires the sites) and read offline
    after the alpha (L2.3). Nothing in the game reads it.

Why a file and not the database:
    A ``_SaverList`` of ten thousand dicts on a script is the wrong shape for
    a question asked once, and it grows without bound inside the live DB.
    A file of JSON lines is appended in O(1), read by any tool, and backed up
    beside the database (L6.2).

Why a synchronous ``open(path, "a")`` and not ``evennia.utils.logger.log_file``:
    ``log_file`` writes from a thread pool (``utils/logger.py:557-580``) and
    rotates at ``CHANNEL_LOG_ROTATE_SIZE`` (1 MB), copying the last 20 lines
    into the new file (``:439-470``, ``:516-550``). A reader counting trades
    would meet duplicated and possibly reordered lines. A plain append on the
    reactor thread costs microseconds at this scale and keeps the file in
    event order, with no rotation.

Why a write failure never propagates:
    By the time ``record()`` runs, the event has happened (callers record
    after their own writes). Observation must not change what it observes:
    an ``OSError`` is logged once with ``log_err`` and swallowed. This is the
    opposite of the ledger's ordering, deliberately.

Why a wrong kind or a clashing field raises:
    Those are programming errors, found by tests, never by the alpha. A
    misspelt kind would otherwise vanish from every count in the report, and
    a caller's ``room=`` would silently overwrite the room ``record`` computes.

Line shape::

    {"ts": "2026-11-01T13:40:52.123+00:00",
     "gt": {"year": 1, "month": 3, "day": 12, "hour": 14},
     "kind": "craft", "actor": ["#12", "Adam"], "room": "#2",
     "recipe": "twine", ...}

``gt`` is the display-indexed game date (what players see, 1-based), so
seasons can be read back. ``settings.LOG_DIR`` is read on every call, so tests
point it at a temporary directory with ``override_settings``.
"""

import json
import os
from datetime import datetime, timezone

from django.conf import settings
from evennia.utils import logger

from world import gametime_utils

KINDS = frozenset(
    {
        "gather",
        "craft",
        "dismantle",
        "trade",
        "work",
        "consume",
        "repair",
        "knowledge",
        "crumble",
        "improve",
    }
)
FILENAME = "activity.jsonl"
RESERVED = frozenset({"ts", "gt", "kind", "actor", "room"})


def path():
    """Absolute path of the activity log, read from settings on every call."""
    return os.path.join(settings.LOG_DIR, FILENAME)


def _game_stamp():
    """The display-indexed game date and hour (1-based, as players see it)."""
    now = gametime_utils.get_current_time()
    return {
        "year": now["year_display"],
        "month": now["month_display"],
        "day": now["day_of_month_display"],
        "hour": now["hour"],
    }


def record(kind, actor, **fields):
    """
    Append one JSON line describing an economic event.

    Args:
        kind (str): One of ``KINDS``.
        actor (Object): Who performed the event; its dbref and key are logged,
            and its location's dbref as ``room`` (``None`` if it has none).
        **fields: The kind's own data. Values that are not JSON types are
            written as their ``str()``.

    Raises:
        ValueError: ``kind`` is not in ``KINDS``, or a field name is one of
            the reserved keys. Nothing is written.

    Never raises on a write failure: an ``OSError`` is logged and swallowed.
    """
    if kind not in KINDS:
        raise ValueError(f"activity_log: unknown kind {kind!r}")
    clash = RESERVED.intersection(fields)
    if clash:
        raise ValueError(f"activity_log: reserved field name(s) {sorted(clash)}")

    location = getattr(actor, "location", None)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "gt": _game_stamp(),
        "kind": kind,
        "actor": [actor.dbref, actor.key],
        "room": location.dbref if location is not None else None,
        **fields,
    }
    line = json.dumps(entry, default=str, ensure_ascii=False)

    target = path()
    try:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError as err:
        logger.log_err(f"activity_log: could not append to {target}: {err}")
