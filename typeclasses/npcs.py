"""
Ambient NPCs (BACKLOG Rev 44, feature/sweeper).

Sweeper -- an old sweeper with a broom who wanders a tagged beat of rooms and
"sweeps" by calling `Room.sweep_expired_corpses()`, the same path the
puppeted-arrival hook uses. He makes no deletion decision of his own: he acts
only where `is_expired` is already true, and every deletion goes through
`Corpse.crumble()`, which also writes the only room line. A sweep that finds
nothing says nothing.

Why a ticker, against the lazy-first principle: lazy evaluation fits *state
that is read on demand* (store a timestamp, compute when looked at). The
sweeper's point is movement over time; there is no state to compute later.
The cost is one persistent subscription and one short step per interval.
The project already runs global tickers (survival, garment wear, see
`server/conf/at_server_startstop.py`); this is the first per-object one.

Lifecycle (verified against Evennia v6.1.0 `scripts/tickerhandler.py`):
- Registered once, in `at_object_creation`. A persistent ticker survives
  reload and shutdown, so `at_init` (run on every cache load) does not touch it.
  Re-adding builds the same store key and only overwrites the entry.
- Removed explicitly in `at_object_delete`. The handler would also drop it on
  the next tick once the object has no pk, but an explicit removal gives a
  receipt that does not wait for real time.
- `TICKER_HANDLER.remove` raises `KeyError` when nothing matches, and
  `at_object_delete` returning False aborts the deletion -- so the KeyError is
  caught and the hook always returns the parent's verdict.

Movement is restricted to rooms tagged `sweeper_beat` (category `npc_route`),
so he never wanders into areas nobody chose for him. If no beat exit is
traversable he stays where he is until the next tick. Moves are quiet: no
"leaves"/"arrives" line once a minute; players see him with `look`.
"""

import random

from evennia import TICKER_HANDLER
from evennia.objects.objects import DefaultObject

from .objects import ObjectParent

SWEEPER_INTERVAL = 60
SWEEPER_IDSTRING = "sweeper"
SWEEPER_BEAT_TAG = "sweeper_beat"
SWEEPER_BEAT_CATEGORY = "npc_route"


class Sweeper(ObjectParent, DefaultObject):
    """An old sweeper who walks his beat and sweeps expired corpses."""

    def at_object_creation(self):
        """Lock him in place for `get` and subscribe his one ticker."""
        super().at_object_creation()
        self.locks.add("get:false()")
        if not self.db.desc:
            self.db.desc = (
                "A stooped old man in a patched grey coat, leaning on a broom "
                "worn down to a stub. He hums tunelessly to himself."
            )
        TICKER_HANDLER.add(
            interval=SWEEPER_INTERVAL,
            callback=self.at_sweeper_tick,
            idstring=SWEEPER_IDSTRING,
            persistent=True,
        )

    def at_object_delete(self):
        """
        Unsubscribe the ticker before the object goes.

        Returns:
            bool: the parent's verdict; False would abort the deletion.
        """
        try:
            TICKER_HANDLER.remove(
                interval=SWEEPER_INTERVAL,
                callback=self.at_sweeper_tick,
                idstring=SWEEPER_IDSTRING,
                persistent=True,
            )
        except KeyError:
            # Never registered, or already removed: nothing to clean up, and
            # the deletion must not be blocked by it.
            pass
        return super().at_object_delete()

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
        Ticker callback: step along the beat, then sweep where he stands.

        Stepping first means he sweeps the room he arrives in, and still
        sweeps when he is stuck. Safe when he has no location (the ticker can
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
