"""
Ambient sweeper NPC (BACKLOG Rev 44, feature/sweeper).

Each class pressures one bug:
- TestSweeperTicker -- a leaked or doubled ticker: registration must happen
  once, survive a repeated `at_object_creation`, be removed on delete, and a
  missing ticker must never abort the deletion (`remove` raises KeyError).
  The receipt is `TICKER_HANDLER.all_display()`, the handler's own view, with
  the same expression as the in-game protocol.
- TestSweeperTick -- a second writer creeping in: the tick must reach
  `Room.sweep_expired_corpses()` (not a copied loop), crumble only expired
  corpses, and add no line of its own. Also the `location=None` crash.
- TestSweeperBeat -- wandering off the beat or through locked exits, and
  noisy moves. Moves are passages, so the move call itself is asserted
  (quiet=True), not only where he ends up.
- TestNpcArrivalDoesNotSweep -- someone "fixing" the room hook so NPC
  arrivals sweep. The sweeper sweeps by calling the method; walking in must
  stay a no-op for him, as Rev 44 locked.

The ticker callback is called directly; nothing waits for real time.
"""

from unittest import mock

from evennia import TICKER_HANDLER, create_object
from evennia.objects.models import ObjectDB
from evennia.utils.test_resources import EvenniaTest

from typeclasses.npcs import (
    SWEEPER_BEAT_CATEGORY,
    SWEEPER_BEAT_TAG,
    SWEEPER_IDSTRING,
    SWEEPER_INTERVAL,
)

CHARACTER = "typeclasses.characters.Character"
ROOM = "typeclasses.rooms.Room"
SWEEPER = "typeclasses.npcs.Sweeper"
PLAYER_CORPSE = "typeclasses.corpse.PlayerCorpse"


def exists(obj_id):
    """The receipt used in-game too: is this id still in the database?"""
    return ObjectDB.objects.filter(id=obj_id).exists()


def sweeper_tickers(sweeper):
    """This sweeper's subscriptions, as the handler itself reports them."""
    return [
        k for k in TICKER_HANDLER.all_display()
        if k[4] == SWEEPER_IDSTRING and k[0] == sweeper
    ]


class _SweeperFixture:
    character_typeclass = CHARACTER
    room_typeclass = ROOM

    def setUp(self):
        super().setUp()
        self.sweeper = create_object(SWEEPER, key="old sweeper", location=self.room1)

    def tearDown(self):
        # The handler's pool is process-global and outlives the test DB
        # rollback; delete through the real path so no subscription leaks.
        if self.sweeper.pk:
            self.sweeper.delete()
        super().tearDown()

    def make_corpse(self, key, expired=True, location=None):
        corpse = create_object(PLAYER_CORPSE, key=key, location=location or self.room1)
        if expired:
            corpse.db.death_time = 1
        self.assertEqual(corpse.is_expired, expired)
        return corpse

    def tag_beat(self, room):
        room.tags.add(SWEEPER_BEAT_TAG, category=SWEEPER_BEAT_CATEGORY)

    def capture(self, obj):
        seen = []
        patcher = mock.patch.object(
            obj, "msg", side_effect=lambda text="", *a, **kw: seen.append(str(text))
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        return seen


class TestSweeperTicker(_SweeperFixture, EvenniaTest):
    def test_creation_registers_one_persistent_ticker(self):
        (key,) = sweeper_tickers(self.sweeper)
        _, callfunc, _, interval, _, persistent = key
        self.assertEqual(
            (callfunc, interval, persistent), ("at_sweeper_tick", SWEEPER_INTERVAL, True)
        )

    def test_repeated_creation_hook_does_not_double_register(self):
        self.sweeper.at_object_creation()
        self.assertEqual(len(sweeper_tickers(self.sweeper)), 1)

    def test_delete_removes_the_ticker(self):
        sweeper = self.sweeper
        sweeper_id = sweeper.id
        before = len(TICKER_HANDLER.all_display())

        sweeper.delete()

        self.assertFalse(exists(sweeper_id))
        self.assertEqual(len(TICKER_HANDLER.all_display()), before - 1)

    def test_missing_ticker_does_not_block_deletion(self):
        TICKER_HANDLER.remove(
            interval=SWEEPER_INTERVAL,
            callback=self.sweeper.at_sweeper_tick,
            idstring=SWEEPER_IDSTRING,
            persistent=True,
        )
        self.assertEqual(sweeper_tickers(self.sweeper), [])
        sweeper_id = self.sweeper.id

        self.sweeper.delete()

        self.assertFalse(exists(sweeper_id))


class TestSweeperTick(_SweeperFixture, EvenniaTest):
    def test_tick_sweeps_through_the_room_method(self):
        expired_id = self.make_corpse("oldcorpse").id
        fresh = self.make_corpse("newcorpse", expired=False)

        with mock.patch.object(
            self.room1, "sweep_expired_corpses", wraps=self.room1.sweep_expired_corpses
        ) as sweep:
            swept = self.sweeper.at_sweeper_tick()

        sweep.assert_called_once_with()
        self.assertEqual(swept, 1)
        self.assertFalse(exists(expired_id))
        self.assertEqual(fresh.location, self.room1)

    def test_crumble_line_is_the_only_line(self):
        self.make_corpse("oldcorpse")
        seen = self.capture(self.char1)

        self.sweeper.at_sweeper_tick()

        # One writer per message: crumble() speaks, the sweeper does not.
        self.assertEqual(len(seen), 1)
        self.assertNotIn("sweeper", seen[0].lower())

    def test_nothing_to_sweep_says_nothing(self):
        seen = self.capture(self.char1)

        with mock.patch.object(
            self.room1, "sweep_expired_corpses", wraps=self.room1.sweep_expired_corpses
        ) as sweep:
            swept = self.sweeper.at_sweeper_tick()

        # Independent receipt that the tick ran.
        sweep.assert_called_once_with()
        self.assertEqual((swept, seen), (0, []))

    def test_no_location_is_a_safe_no_op(self):
        self.sweeper.location = None
        self.assertEqual(self.sweeper.at_sweeper_tick(), 0)


class TestSweeperBeat(_SweeperFixture, EvenniaTest):
    def test_untagged_room_is_off_the_beat(self):
        # Precondition: an exit exists, so staying put is the filter's doing.
        self.assertEqual(self.exit.destination, self.room2)
        with mock.patch.object(self.sweeper, "move_to") as move:
            self.sweeper.at_sweeper_tick()

        move.assert_not_called()
        self.assertEqual(self.sweeper.location, self.room1)

    def test_steps_quietly_onto_a_beat_room(self):
        self.tag_beat(self.room2)
        seen = self.capture(self.char1)

        with mock.patch.object(
            self.sweeper, "move_to", wraps=self.sweeper.move_to
        ) as move:
            self.sweeper.at_sweeper_tick()

        move.assert_called_once_with(self.room2, quiet=True)
        self.assertEqual(self.sweeper.location, self.room2)
        self.assertEqual(seen, [])

    def test_locked_exit_is_not_taken(self):
        self.tag_beat(self.room2)
        self.exit.locks.add("traverse:false()")

        self.sweeper.at_sweeper_tick()

        self.assertEqual(self.sweeper.location, self.room1)

    def test_sweeps_the_room_he_steps_into(self):
        self.tag_beat(self.room2)
        corpse_id = self.make_corpse("oldcorpse", location=self.room2).id

        swept = self.sweeper.at_sweeper_tick()

        self.assertEqual(swept, 1)
        self.assertFalse(exists(corpse_id))


class TestNpcArrivalDoesNotSweep(_SweeperFixture, EvenniaTest):
    def test_walking_in_is_not_sweeping(self):
        corpse_id = self.make_corpse("oldcorpse", location=self.room2).id

        self.sweeper.move_to(self.room2, quiet=True)
        self.assertTrue(exists(corpse_id))

        # Positive twin, same corpse: his tick is what sweeps.
        self.assertEqual(self.sweeper.at_sweeper_tick(), 1)
        self.assertFalse(exists(corpse_id))
