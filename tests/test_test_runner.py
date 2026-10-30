"""
Tests for server/test_runner.py (the fork-based parallel test runner).

    TestForkTestRunner   a runner that stops selecting `fork` (the 3.14
                         `forkserver` default comes back and every worker
                         dies in `_init_worker`); a runner that is no longer
                         Evennia's (no `evennia._init()` in the parent)

The real receipt is a `--parallel` run of the suite; these pin the two facts
that run depends on.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_test_runner
"""

import multiprocessing
from unittest import TestCase

from evennia.server.tests.testrunner import EvenniaTestSuiteRunner

from server.test_runner import ForkTestRunner


class TestForkTestRunner(TestCase):
    def setUp(self):
        self.before = multiprocessing.get_start_method(allow_none=True)

    def tearDown(self):
        multiprocessing.set_start_method(self.before, force=True)

    def test_it_is_evennias_runner(self):
        self.assertTrue(issubclass(ForkTestRunner, EvenniaTestSuiteRunner))

    def test_building_it_selects_fork(self):
        multiprocessing.set_start_method("spawn", force=True)   # not fork
        ForkTestRunner()
        self.assertEqual(multiprocessing.get_start_method(), "fork")
