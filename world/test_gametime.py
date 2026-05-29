"""
Empirical verification of custom_gametime() indexing behavior.

Background:
    Evennia documentation and source comments are ambiguous about
    whether custom_gametime() returns 0-indexed or 1-indexed
    month/week/day values. The math in time_to_tuple()
    (seconds // divisor) suggests 0-indexed, but GitHub issue #1753
    indicates Griatch may have changed this to 1-indexed at some
    point. The truth depends on the exact Evennia version installed.

Usage (from in-game, as a builder/admin):
    @py from world.test_gametime import verify; verify()

This file can be deleted after the indexing question is resolved
and gametime_utils.py is built. Or kept as a regression check.
"""

import inspect

from django.conf import settings
from evennia.contrib.base_systems import custom_gametime as cgt


def verify():
    """Print a comprehensive diagnostic of custom_gametime behavior."""
    line = "=" * 64
    print(f"\n{line}\ncustom_gametime() indexing verification\n{line}")

    # 1. Settings context (so output is interpretable in isolation)
    print("\n[settings]")
    print(f"  TIME_FACTOR     = {settings.TIME_FACTOR}")
    print(f"  TIME_GAME_EPOCH = {settings.TIME_GAME_EPOCH}")
    print(f"  TIME_UNITS keys = {list(settings.TIME_UNITS.keys())}")

    # 2. Empirical: what the function actually returns RIGHT NOW
    print("\n[live tuple] format = (year, month, week, day, hour, min, sec)")
    rel = cgt.custom_gametime(absolute=False)
    abs_ = cgt.custom_gametime(absolute=True)
    print(f"  custom_gametime(absolute=False) = {rel}")
    print(f"      (time since server start)")
    print(f"  custom_gametime(absolute=True)  = {abs_}")
    print(f"      (time since TIME_GAME_EPOCH)")

    # 3. Definitive: print the actual source of the running code.
    #    This is more reliable than docs because it shows what's
    #    really installed on this server.
    print("\n[source: custom_gametime]")
    print(inspect.getsource(cgt.custom_gametime))
    print("[source: time_to_tuple]")
    print(inspect.getsource(cgt.time_to_tuple))

    # 4. Decision hints
    print(line)
    print("INTERPRETATION GUIDE")
    print(line)
    print("Look at month/week/day positions in the absolute=True tuple:")
    print("  - All ZERO near start    -> 0-indexed (raw time_to_tuple)")
    print("  - month/week/day == 1    -> 1-indexed (post-#1753 change)")
    print("  - Anything else          -> read [source] sections above")
    print(line)
