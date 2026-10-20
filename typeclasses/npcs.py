"""
Ambient NPCs (BACKLOG Rev 44, feature/sweeper).

Sweeper -- an old sweeper with a broom who wanders a tagged beat of rooms and
"sweeps" by calling `Room.sweep_expired_corpses()`, the same path the
puppeted-arrival hook uses. He makes no deletion decision of his own: he acts
only where `is_expired` is already true, and every deletion goes through
`Corpse.crumble()`, which also writes the only room line. A sweep that finds
nothing says nothing.

Why a timer, against the lazy-first principle: lazy evaluation fits *state
that is read on demand* (store a timestamp, compute when looked at). The
sweeper's point is movement over time; there is no state to compute later.
The cost is one persistent Script and one short step per interval.

Why a Script and not TICKER_HANDLER: in this project every
`TICKER_HANDLER.add` in `at_server_start` saves the handler's storage -- in a
fresh process, only what was just added -- before `TICKER_HANDLER.restore()`
runs, so any other persistent ticker is wiped on each start (verified in-game on 2026-10-19, see BACKLOG).
A Script is its own database row with `db_persistent=True` by default, and
its timer is resumed by `update_scripts_after_server_start`; tickers never
touch it.

Lifecycle (verified against Evennia v6.1.0):
- Created once, in `at_object_creation`. `scripts.add()` creates a new
  Script on *every* call, so a key guard keeps repeated calls to one.
- Removed with the object: `DefaultObject.delete()` calls `script.delete()`
  on each Script on the object, which also stops its timer.

Movement is restricted to rooms tagged `sweeper_beat` (category `npc_route`),
so he never wanders into areas nobody chose for him. If no beat exit is
traversable he stays where he is until the next tick. Moves are quiet: no
"leaves"/"arrives" line once a minute; players see him with `look`.
"""

import random

from evennia.objects.objects import DefaultObject
from evennia.utils import logger

from .objects import ObjectParent
from .scripts import Script

SWEEPER_INTERVAL = 60
SWEEPER_SCRIPT_KEY = "sweeper_tick"
SWEEPER_BEAT_TAG = "sweeper_beat"
SWEEPER_BEAT_CATEGORY = "npc_route"


class SweeperScript(Script):
    """Drives one Sweeper: calls his tick every `SWEEPER_INTERVAL` seconds."""

    def at_script_creation(self):
        self.key = SWEEPER_SCRIPT_KEY
        self.desc = "Walks the sweeper's beat and sweeps expired corpses"
        self.interval = SWEEPER_INTERVAL
        self.persistent = True

    def at_repeat(self, **kwargs):
        """Called every `interval` real seconds while the timer runs."""
        try:
            self.obj.at_sweeper_tick()
        except Exception:
            # Same pattern as WeatherScript: log, keep the timer alive.
            logger.log_trace()


class Sweeper(ObjectParent, DefaultObject):
    """An old sweeper who walks his beat and sweeps expired corpses."""

    def at_object_creation(self):
        """Lock him in place for `get` and give him his one timer Script."""
        super().at_object_creation()
        self.locks.add("get:false()")
        if not self.db.desc:
            self.db.desc = (
                "A stooped old man in a patched grey coat, leaning on a broom "
                "worn down to a stub. He hums tunelessly to himself."
            )
        if not self.scripts.get(SWEEPER_SCRIPT_KEY):
            self.scripts.add(SweeperScript)

    def beat_exits(self):
        """
        Exits he may take from where he stands.

        Returns:
            list: traversable exits whose destination is on his beat.
        """
        location = self.location
        if location is None:
            return []
        return [
            exi
            for exi in location.exits
            if exi.destination
            and exi.destination.tags.has(SWEEPER_BEAT_TAG, category=SWEEPER_BEAT_CATEGORY)
            and exi.access(self, "traverse")
        ]

    def walk_beat(self):
        """
        Take one quiet step along the beat, if any step is possible.

        Returns:
            bool: True if he moved.
        """
        exits = self.beat_exits()
        if not exits:
            return False
        destination = random.choice(exits).destination
        return bool(self.move_to(destination, quiet=True))

    def at_sweeper_tick(self, *args, **kwargs):
        """
        Timer callback (from `SweeperScript.at_repeat`): step along the
        beat, then sweep where he stands.

        Stepping first means he sweeps the room he arrives in, and still
        sweeps when he is stuck. Safe when he has no location (the timer can
        fire while he is stored away with `location=None`): `beat_exits()`
        returns no exits and `None` has no sweep method, so both steps no-op.

        Returns:
            int: corpses crumbled this tick (a receipt for tests and @py).
        """
        self.walk_beat()
        location = self.location
        sweep = getattr(location, "sweep_expired_corpses", None)
        if sweep is None:
            return 0
        return sweep()
