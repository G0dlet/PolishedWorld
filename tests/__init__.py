"""
PolishedWorld unit-test package.

All unit tests live under this single top-level folder. This is a deliberate
isolation boundary: an automation agent (OpenCode) may write ONLY inside
tests/, so it can never accidentally touch production modules in world/,
commands/ or typeclasses/ while generating coverage.

Evennia's test runner discovers any module named `test*.py` anywhere on the
path, so a flat tests/ package works fine even though the code under test lives
in sibling packages -- the tests import it with ordinary absolute imports
(`from world.knowledge import ...`).

Run everything with YOUR settings:

    evennia test --settings settings.py .

or just this package:

    evennia test --settings settings.py tests
"""
