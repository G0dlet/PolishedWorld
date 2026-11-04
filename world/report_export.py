"""
A readable export of every in-game report (BACKLOG *In-game bug, idea and
player reports*, lock 5), for the alpha close-out (runbook §8).

Reports are `Msg` rows in `evennia.db3`: the wipe deletes them, and the
close-out's `.backup` keeps them only as a database. This writes one JSON
line per report, oldest first, next to the activity log:

    @py from world.report_export import export_reports; self.msg(str(export_reports()))

Each line:

    {"date": "2026-11-04T19:02:11Z", "id": 12, "sender": [["#7", "tester"]],
     "status": ["in progress"], "target": [["#168", "tester"]],
     "text": "...", "type": "bug"}

`target` is what the report names (`bug hammer = ...`, `report <player> =`),
the hub script left out; `status` is the staff menu's tags, the contrib's
own `report` creation tag left out.

It reads the hubs and never creates one: the contrib's `_get_report_hub`
creates a hub on a miss, which would leave an empty script behind every
export of a type nobody used. Every hub with a type's key is read, so a
duplicate hub cannot hide reports. Read-only; safe with players online.
"""

import json
import os
from datetime import timezone

from django.conf import settings

# The contrib's hub types: `report_type or key` of its three commands
# (`bug`, `idea`, `player`), stored as the script key `<type>_reports`
# (`reports.py:57-74`). A copy, pinned by a test against the commands.
REPORT_TYPES = ("bug", "idea", "player")

# The tag `ReportCmdBase.func` puts on every report it files.
CREATION_TAG = "report"


def _hubs(report_type):
    from evennia.scripts.models import ScriptDB

    # Same filter as `GLOBAL_SCRIPTS.get` for a key not in settings.
    return list(
        ScriptDB.objects.filter(
            db_key__iexact=f"{report_type}_reports", db_obj__isnull=True
        ).order_by("id")
    )


def _pair(entity):
    return [entity.dbref, entity.key]


def report_rows():
    """
    Every report of every type, as dicts, oldest first (ties by id).

    Returns:
        list[dict]: one dict per report, keys as in the module docstring.
    """
    from evennia.comms.models import Msg

    rows = []
    for report_type in REPORT_TYPES:
        seen = set()
        for hub in _hubs(report_type):
            for msg in Msg.objects.search_message(receiver=hub):
                if msg.id in seen:
                    continue
                seen.add(msg.id)
                # Accounts and objects only: the one script receiver the
                # contrib writes is the hub itself.
                targets = list(msg.db_receivers_accounts.order_by("id")) + list(
                    msg.db_receivers_objects.order_by("id")
                )
                created = msg.date_created.astimezone(timezone.utc)
                rows.append(
                    {
                        "type": report_type,
                        "id": msg.id,
                        "date": created.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "sender": [_pair(s) for s in msg.senders],
                        "target": [_pair(t) for t in targets],
                        "status": sorted(
                            t for t in msg.tags.all() if t != CREATION_TAG
                        ),
                        "text": msg.message,
                    }
                )
    rows.sort(key=lambda row: (row["date"], row["id"]))
    return rows


def export_reports(path=None):
    """
    Write `report_rows()` as JSON lines.

    Args:
        path (str, optional): where to write. Default:
            `<LOG_DIR>/reports-<UTC stamp>.jsonl`.

    Returns:
        tuple: (path written, number of reports).
    """
    from datetime import datetime

    rows = report_rows()
    if path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = os.path.join(settings.LOG_DIR, f"reports-{stamp}.jsonl")
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return path, len(rows)
