"""
world/activity_log.py (Launch Minimum L2.1, LM2).

Every test points ``LOG_DIR`` at a fresh temporary directory, so the file a
test reads is exactly the file that test wrote. The classes follow the
promises the module makes: one event is one line (and a line holds what the
report will need); many events are many lines, in order, in one file; a
programming error raises and writes nothing; a write failure never raises.

It also exports what the site tests use (L2.2): ``ActivityLogMixin`` gives any
test class a fresh ``LOG_DIR`` and a ``last_record()`` reader, and
``TestSiteCensus`` pins how many ``activity_log.record(`` calls production code
makes, file by file (lesson 200), so adding or losing a site is a deliberate
change to a number.

Importing from here is safe: the mixin and the two readers are not
``TestCase`` subclasses, so a module that imports them does not collect and
re-run this module's tests.
"""

import ast
import json
import os
import pathlib
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from evennia.utils.test_resources import EvenniaTest

from world import activity_log

FIXED_TIME = {
    "year": 0, "month": 2, "week": 1, "day": 4, "hour": 14, "minute": 5, "second": 0,
    "year_display": 1, "month_display": 3, "day_of_month_display": 12,
}


def records(log_dir, kind=None):
    """Every line in ``log_dir``'s activity log, parsed; only ``kind`` if given."""
    target = os.path.join(log_dir, activity_log.FILENAME)
    if not os.path.exists(target):
        return []
    with open(target, encoding="utf-8") as handle:
        entries = [json.loads(raw) for raw in handle.read().splitlines()]
    return [entry for entry in entries if kind is None or entry["kind"] == kind]


def last_record(log_dir, kind=None):
    """The last line (of ``kind``, if given), or None when there is none."""
    found = records(log_dir, kind)
    return found[-1] if found else None


class ActivityLogMixin:
    """
    A fresh, empty ``LOG_DIR`` per test, and readers for the lines written to it.

    Put it FIRST in the bases (``class T(ActivityLogMixin, SomeFixture)``) so
    the fixture's own ``setUp`` runs inside ``super().setUp()`` and the
    override is in place before the test body. ``record()`` reads
    ``settings.LOG_DIR`` on every call, so nothing else needs patching.

    Every site test filters by kind: from L2.2b, a craft or a dismantle that
    ticks a skill writes an ``improve`` line too, so "the last line" alone
    would be the wrong question.
    """

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.activity_dir = tmp.name
        override = override_settings(LOG_DIR=self.activity_dir)
        override.enable()
        self.addCleanup(override.disable)

    def activity_records(self, kind=None):
        return records(self.activity_dir, kind)

    def last_record(self, kind=None):
        return last_record(self.activity_dir, kind)


class _LogDirTest(ActivityLogMixin, EvenniaTest):
    """Shared setup for this module's own tests."""

    def setUp(self):
        super().setUp()
        self.tmp = self.activity_dir

    def lines(self):
        return self.activity_records()


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
    """Pressured by LM-M5 (kind check) and LM-M5b (reserved-name check)."""

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


# --------------------------------------------------------------------------- census

REPO = pathlib.Path(__file__).resolve().parent.parent
PRODUCTION = ("commands", "server", "typeclasses", "web", "world")

# Every activity_log.record( call in production code, per file: sixteen.
# L2.2a landed the ten production sites, L2.2b the six circulation sites.
SITES = {
    "commands/consumption_commands.py": 3,  # eat, drink, drink at a source (Survival Loop S1.1)
    "commands/crafting_commands.py": 6,     # dismantle, inscribe, scribe, learn x3
    "commands/foraging_commands.py": 1,     # forage
    "commands/hunting_commands.py": 1,      # harvest
    "commands/repair_commands.py": 1,       # repair
    "commands/work_commands.py": 1,         # work (paid path)
    "typeclasses/characters.py": 1,         # improve (attempt_skill_improvement)
    "typeclasses/corpse.py": 1,             # crumble
    "world/barter.py": 1,                   # trade (_finish_and_clear)
    "world/crafting_base.py": 1,            # craft (post_craft)
}


def _record_calls(tree):
    """Calls spelled ``activity_log.record(...)`` in one parsed module."""
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "record"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "activity_log"
    )


def census():
    """{relative path: call count} over the production packages."""
    found = {}
    for package in PRODUCTION:
        for path in sorted((REPO / package).rglob("*.py")):
            count = _record_calls(ast.parse(path.read_text(encoding="utf-8")))
            if count:
                found[path.relative_to(REPO).as_posix()] = count
    return found


class TestSiteCensus(SimpleTestCase):
    """
    Pressured by LM-M8 (a site dropped). Counts call sites with the AST, not
    tests (lesson 183): a site deleted with its test, or a thirteenth added
    without one, both change this dict. A ``from world.activity_log import
    record`` would hide a site from the census; the import style is the
    module, so the spelling counted here is the only one in use.
    """

    def test_every_site_is_counted_file_by_file(self):
        self.assertEqual(census(), SITES)

    def test_no_site_imports_record_by_name(self):
        offenders = []
        for package in PRODUCTION:
            for path in sorted((REPO / package).rglob("*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if (
                        isinstance(node, ast.ImportFrom)
                        and node.module == "world.activity_log"
                    ):
                        offenders.append(path.relative_to(REPO).as_posix())
        self.assertEqual(offenders, [])
