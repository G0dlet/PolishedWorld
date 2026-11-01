"""
world/activity_log.py (Launch Minimum L2.1, LM2).

Every test points ``LOG_DIR`` at a fresh temporary directory, so the file a
test reads is exactly the file that test wrote. The classes follow the
promises the module makes: one event is one line (and a line holds what the
report will need); many events are many lines, in order, in one file; a
programming error raises and writes nothing; a write failure never raises.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import override_settings

from evennia.utils.test_resources import EvenniaTest

from world import activity_log

FIXED_TIME = {
    "year": 0, "month": 2, "week": 1, "day": 4, "hour": 14, "minute": 5, "second": 0,
    "year_display": 1, "month_display": 3, "day_of_month_display": 12,
}


class _LogDirTest(EvenniaTest):
    """Shared setup: LOG_DIR is a temp dir; helpers to read the lines back."""

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name
        override = override_settings(LOG_DIR=self.tmp)
        override.enable()
        self.addCleanup(override.disable)

    def lines(self):
        target = os.path.join(self.tmp, activity_log.FILENAME)
        if not os.path.exists(target):
            return []
        with open(target, encoding="utf-8") as handle:
            return [json.loads(raw) for raw in handle.read().splitlines()]


class TestOneEventOneLine(_LogDirTest):
    """The line's shape: what L2.3's report will read."""

    def test_path_follows_settings(self):
        self.assertEqual(activity_log.path(), os.path.join(self.tmp, "activity.jsonl"))

    def test_record_appends_one_parseable_line(self):
        activity_log.record("craft", self.char1, recipe="twine")
        (entry,) = self.lines()
        self.assertEqual(entry["kind"], "craft")
        self.assertEqual(entry["actor"], [self.char1.dbref, self.char1.key])
        self.assertEqual(entry["room"], self.char1.location.dbref)
        self.assertEqual(entry["recipe"], "twine")

    def test_ts_is_utc(self):
        activity_log.record("craft", self.char1)
        (entry,) = self.lines()
        self.assertEqual(datetime.fromisoformat(entry["ts"]).utcoffset(), timedelta(0))

    def test_gt_is_the_display_date(self):
        with patch.object(activity_log.gametime_utils, "get_current_time", return_value=FIXED_TIME):
            activity_log.record("gather", self.char1)
        (entry,) = self.lines()
        self.assertEqual(entry["gt"], {"year": 1, "month": 3, "day": 12, "hour": 14})

    def test_actor_without_location_writes_null_room(self):
        self.obj1.location = None  # assignment runs no move hook
        activity_log.record("crumble", self.obj1)
        (entry,) = self.lines()
        self.assertIsNone(entry["room"])

    def test_object_field_is_written_as_its_str(self):
        activity_log.record("trade", self.char1, other=self.char2)
        (entry,) = self.lines()
        self.assertEqual(entry["other"], str(self.char2))


class TestManyEventsInOrder(_LogDirTest):
    """Pressured by LM-M3 (log_file-style rotation with copied tail lines)."""

    def test_fifty_records_are_fifty_lines_in_order_in_one_file(self):
        # ~50 x 200 bytes: past any small rotation threshold, so a writer that
        # rotates or copies tail lines changes the count, the order or the
        # directory listing.
        for seq in range(50):
            activity_log.record("gather", self.char1, seq=seq, item="x" * 100)
        self.assertEqual([entry["seq"] for entry in self.lines()], list(range(50)))
        self.assertEqual(os.listdir(self.tmp), [activity_log.FILENAME])


class TestProgrammingErrorsRaise(_LogDirTest):
    """Pressured by LM-M5 (kind check) and LM-M6 (reserved-name check)."""

    def test_unknown_kind_raises_and_writes_nothing(self):
        with self.assertRaises(ValueError):
            activity_log.record("crafted", self.char1)
        self.assertEqual(self.lines(), [])

    def test_reserved_field_raises_and_writes_nothing(self):
        with self.assertRaises(ValueError):
            activity_log.record("trade", self.char1, room="#99")
        self.assertEqual(self.lines(), [])


class TestWriteFailureNeverRaises(_LogDirTest):
    """Pressured by LM-M4 (OSError propagates)."""

    def test_missing_log_dir_logs_once_and_returns(self):
        missing = os.path.join(self.tmp, "no-such-dir")
        with override_settings(LOG_DIR=missing), patch.object(
            activity_log.logger, "log_err"
        ) as log_err:
            activity_log.record("craft", self.char1, recipe="twine")  # must not raise
        self.assertEqual(log_err.call_count, 1)
        self.assertFalse(os.path.exists(missing))
