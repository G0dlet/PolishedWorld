"""
Initial-setup hook: build the alpha area on a fresh database. Alpha content
epic, Task AC3.2.

Evennia calls `at_initial_setup()` once per database, on the first start,
after it has created Account #1, its character and Limbo, and before it
restarts the server once. settings.AT_INITIAL_SETUP_HOOK_MODULE points here.

WHAT EVENNIA DOES WITH THIS MODULE (evennia/server/initial_setup.py, v6.1.0)
---------------------------------------------------------------------------
The template this file replaced said tracebacks here are "QUIETLY ignored".
That is half true, and the true half is the dangerous one:

* An ImportError (or ValueError) raised while Evennia IMPORTS this module is
  swallowed. The hook returns, the step is saved as done
  (ServerConfig "last_initial_setup_step") and never runs again: the server
  comes up with an empty world, recorded as built.
* Any exception raised while `at_initial_setup()` RUNS is re-raised. Startup
  stops ("Error in initial setup. Stopping Server + Portal."), the step is
  not saved, and the next `evennia start` resumes from it and calls this
  function again.

So every game import lives inside the function, where a broken import is the
second kind of failure, not the first. tests/test_initial_setup_hook.py walks
this module's source and refuses any module-level import that is not the
standard library, evennia or django. Nothing here catches exceptions either
(AD7): a seed that fails must stop the server, not leave an empty world.

Running again after a failure is safe because `seed_world()` is idempotent:
what the failed run built is skipped and the rest is created.

THE STARTUP LOG
---------------
Evennia's line "Initial setup: Running at_initial_setup() hook." is written
after this module was imported and before this function runs. It proves the
import, not the seed. The summary line this function logs afterwards is the
receipt that the area was built.

WHAT IT DOES NOT DO
-------------------
It creates no Treasury and sets no dbref setting (AD7, typeclasses/treasury.py):
those are admin steps in the fresh-database runbook. It runs before any player
can connect, so there is no concurrent access to guard against.
"""
from evennia.utils import logger


def at_initial_setup():
    """
    Seed the alpha area into the fresh database. Called once, without
    arguments, by Evennia's initial setup.

    Raises:
        Whatever importing or running world.seeding raises -- deliberately
        uncaught, see the module docstring.
    """
    from world.seeding import seed_world

    summary = seed_world()
    counts = ", ".join(
        f"{kind} {result['created']} created / {result['skipped']} skipped"
        for kind, result in summary.items()
    )
    logger.log_info(f"Initial setup: seeded the alpha area: {counts}.")
