"""
Tests for server/conf/at_server_startstop.py: the two global tickers.

The garment wear interval shipped at its dev value (30 s, "TODO: 10800 before
merge") from 2026-07-02 until 2026-11-07 -- through every merge, including the
launch minimum and two alpha tags -- because a TODO comment is a claim nobody
reads at merge time. These tests make the values claims a test reads:

* TestTickIntervals -- both intervals pinned to their calibrated values, and
  at_server_start registers exactly the two tickers with them.
* TestNoMergeMarkers -- no production module carries a "before merge" marker,
  so the next dev value parked behind one fails here instead of shipping.
"""

import pathlib
import re
import tempfile
from unittest import TestCase, mock

from server.conf import at_server_startstop as startstop
from world.garment_wear import wear_all_garments
from world.survival_ticker import deplete_all_survival_traits

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCTION = ("commands", "server", "typeclasses", "web", "world")
MARKER = re.compile(r"before\s+merg", re.IGNORECASE)


class TestTickIntervals(TestCase):
    """Pressures the calibrated values and that the start hook uses them."""

    def test_survival_tick_is_ten_real_minutes(self):
        self.assertEqual(startstop.SURVIVAL_TICK_INTERVAL, 600)

    def test_wear_tick_is_three_real_hours(self):
        # 12 game-hours at TIME_FACTOR 4: world/garment_wear.py's calibration.
        self.assertEqual(startstop.WEAR_TICK_INTERVAL, 10800)

    def test_start_registers_exactly_the_two_tickers(self):
        with mock.patch.object(startstop, "TICKER_HANDLER") as handler:
            startstop.at_server_start()
        self.assertEqual(handler.add.call_args_list, [
            mock.call(interval=600, callback=deplete_all_survival_traits,
                      idstring="survival", persistent=True),
            mock.call(interval=10800, callback=wear_all_garments,
                      idstring="garment_wear", persistent=True),
        ])


class TestNoMergeMarkers(TestCase):
    """Pressures the guard: a "before merge" marker in production code fails."""

    @staticmethod
    def _marked(root):
        found = []
        for top in PRODUCTION:
            for path in sorted((root / top).rglob("*.py")):
                for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if MARKER.search(line):
                        found.append(f"{path.relative_to(root).as_posix()}:{n}")
        return found

    def test_no_production_module_waits_for_a_merge(self):
        self.assertEqual(self._marked(ROOT), [])

    def test_the_guard_sees_a_marker(self):
        # Receipt that the scan reads what it claims to, in a scratch tree
        # rather than the repo (a parallel run must never see the probe).
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "world").mkdir()
            (root / "world" / "probe.py").write_text(
                "X = 1   # TODO: 2 before merge\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "note.py").write_text(
                "# before merging, read this\n", encoding="utf-8")
            self.assertEqual(self._marked(root), ["world/probe.py:1"])
