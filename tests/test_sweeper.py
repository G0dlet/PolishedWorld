"""
Ambient sweeper NPC (BACKLOG Rev 44, feature/sweeper).

Each class pressures one bug:
- TestSweeperScript -- a leaked or doubled timer: exactly one Script after a
  repeated `at_object_creation` (`scripts.add` never deduplicates), gone with
  the object, persistent and on the right interval, and its `at_repeat`
  reaching the tick. Unit tests cannot reload the server; whether the timer
  survives `reload` is receipted in-game only (it is what the ticker failed).
- TestSweeperTick -- a second writer creeping in: the tick must reach
  `Room.sweep_expired_corpses()` (not a copied loop), crumble only expired
  corpses, and add no line of its own. Also the `location=None` crash.
- TestSweeperBeat -- wandering off the beat or through locked exits, and
  noisy moves. Moves are passages, so the move call itself is asserted
  (quiet=True), not only where he ends up.
- TestNpcArrivalDoesNotSweep -- someone "fixing" the room hook so NPC
  arrivals sweep. The sweeper sweeps by calling the method; walking in must
  stay a no-op for him, as Rev 44 locked.

The timer callback is called directly; nothing waits for real time.
"""

from unittest import mock

from evennia import create_object
from evennia.objects.models import ObjectDB
from evennia.scripts.models import ScriptDB
from evennia.utils.test_resources import EvenniaTest

from typeclasses.npcs import (
    SWEEPER_BEAT_CATEGORY,
    SWEEPER_BEAT_TAG,
    SWEEPER_INTERVAL,
    SWEEPER_SCRIPT_KEY,
)

CHARACTER = "typeclasses.characters.Character"
ROOM = "typeclasses.rooms.Room"
SWEEPER = "typeclasses.npcs.Sweeper"
PLAYER_CORPSE = "typeclasses.corpse.PlayerCorpse"


def exists(obj_id):
    """The receipt used in-game too: is this id still in the database?"""
    return ObjectDB.objects.filter(id=obj_id).exists()


def sweeper_scripts(sweeper):
    """This sweeper's timer Scripts, as the database reports them."""
    return list(sweeper.scripts.get(SWEEPER_SCRIPT_KEY))


class _SweeperFixture:
    character_typeclass = CHARACTER
    room_typeclass = ROOM

    def setUp(self):
        super().setUp()
        self.sweeper = create_object(SWEEPER, key="old sweeper", location=self.room1)

    def tearDown(self):
        # Delete through the real path so the Script's timer task is stopped,
        # not left running past the test DB rollback.
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


class TestSweeperScript(_SweeperFixture, EvenniaTest):
    def test_creation_gives_one_persistent_timer(self):
        (script,) = sweeper_scripts(self.sweeper)
        self.assertEqual(
            (script.typeclass_path, script.interval, script.persistent, script.is_active),
            ("typeclasses.npcs.SweeperScript", SWEEPER_INTERVAL, True, True),
        )

    def test_repeated_creation_hook_does_not_double_the_timer(self):
        self.sweeper.at_object_creation()
        self.assertEqual(len(sweeper_scripts(self.sweeper)), 1)

    def test_delete_takes_the_timer_with_it(self):
        (script,) = sweeper_scripts(self.sweeper)
        sweeper_id, script_id = self.sweeper.id, script.id

        self.sweeper.delete()

        self.assertFalse(exists(sweeper_id))
        self.assertFalse(ScriptDB.objects.filter(id=script_id).exists())

    def test_at_repeat_reaches_the_tick(self):
        (script,) = sweeper_scripts(self.sweeper)
        with mock.patch.object(self.sweeper, "at_sweeper_tick") as tick:
            script.at_repeat()
        tick.assert_called_once_with()

    def test_tick_error_is_logged_not_raised(self):
        (script,) = sweeper_scripts(self.sweeper)
        with mock.patch.object(
            self.sweeper, "at_sweeper_tick", side_effect=RuntimeError("boom")
        ), mock.patch("typeclasses.npcs.logger.log_trace") as log_trace:
            script.at_repeat()
        log_trace.assert_called_once_with()


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
