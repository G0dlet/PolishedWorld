"""
PolishedWorld's test runner: Evennia's, with `--parallel` usable on Python 3.14.

Django's `--parallel` starts one worker process per test subsuite. Python 3.14
changed the default start method on Linux from `fork` to `forkserver`. A
forkserver worker is a fresh interpreter: it does not inherit the parent's
`evennia._init()` (the flat API -- `evennia.create_object` and friends -- is
still None there) or the launcher's settings path, so every worker dies in
`_init_worker` (`No module named 'settings.py'`, `NoneType takes no
arguments`) and the run ends in `multiprocessing.context.TimeoutError`.
A `fork` worker is a copy of the parent after `setup_test_environment()` has
called `evennia._init()`, so it starts initialised. This runner selects `fork`
before Django builds the pool. A serial run (no `--parallel`) is unchanged.

Usage (from the game directory):

    evennia test --settings settings.py \\
        --testrunner server.test_runner.ForkTestRunner --parallel auto tests

`--parallel` takes an optional value (argparse `nargs="?"`), so the word after
it is read as that value: `--parallel tests` fails with *'tests' is not an
integer or the string 'auto'*. Give the value (`auto`, one worker per CPU, or
a number), or put the test labels before `--parallel`. With no label at all
the whole game directory is discovered (the same tests as `tests`).
`DJANGO_TEST_PROCESSES` caps `auto`. The runner is named on the command line,
not in `settings.TEST_RUNNER`, so `settings.py` is not touched.
"""

import multiprocessing

from evennia.server.tests.testrunner import EvenniaTestSuiteRunner
from evennia.utils import logger

START_METHOD = "fork"


def use_fork():
    """
    Make `fork` the multiprocessing start method, if this platform has it.

    Returns:
        bool: True if the start method is now `fork`.
    """
    if START_METHOD not in multiprocessing.get_all_start_methods():
        logger.log_warn(f"test_runner: no '{START_METHOD}' start method here; --parallel may fail")
        return False
    try:
        multiprocessing.set_start_method(START_METHOD, force=True)
    except (RuntimeError, ValueError) as err:
        logger.log_warn(f"test_runner: could not select '{START_METHOD}': {err}")
        return False
    return multiprocessing.get_start_method() == START_METHOD


class ForkTestRunner(EvenniaTestSuiteRunner):
    """`EvenniaTestSuiteRunner`, with worker processes started by `fork`."""

    def __init__(self, *args, **kwargs):
        # Before super(): Django resolves `--parallel auto` against the start
        # method in DiscoverRunner.__init__ (get_max_test_processes).
        use_fork()
        super().__init__(*args, **kwargs)
