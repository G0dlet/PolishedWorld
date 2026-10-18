"""
Corpse expiry: one writer, three triggers (BACKLOG Rev 43, feature/janitor).

`Corpse.crumble()` is the single writer (P-2) for expiry. Look
(`PlayerCorpse.return_appearance`), harvest (`CmdHarvest` step 4) and a player
entering the room (`Room.at_object_receive`) decide nothing themselves beyond
`is_expired`; they call `crumble()` and do nothing else.

Each class pressures one bug:

- TestCrumbleIsTheSingleWriter -- deleting the body before its contents. That
  is the bug harvest had: `DefaultObject.delete()` teleports contents to their
  `home` instead of deleting them. Also the double-delete crash on a stale
  reference.
- TestEveryPathReachesCrumble -- a call site that keeps its own deletion or
  its own message, i.e. a second writer creeping back in.
- TestHarvestDestroysPlayerLoot -- the observed in-game bug, unmocked, with the
  same expressions as the in-game protocol.
- TestRoomSweep -- the lazy sweep: expired corpses only, puppeted arrivals
  only, and wired into `move_to` for real.

The ids are captured before deletion and checked with
`ObjectDB.objects.filter(id=...).exists()`. Asserting `location == home` (or
its absence) would be the wrong receipt: a relocated item also stops being
inside the corpse.
"""

from contextlib import contextmanager
from unittest import mock

from evennia import create_object
from evennia.objects.models import ObjectDB
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.hunting_commands import CmdHarvest
from typeclasses.corpse import Corpse

CHARACTER = "typeclasses.characters.Character"
ROOM = "typeclasses.rooms.Room"
CORPSE = "typeclasses.corpse.Corpse"
PLAYER_CORPSE = "typeclasses.corpse.PlayerCorpse"
OBJECT = "typeclasses.objects.Object"


@contextmanager
def captured_messages(obj):
    """
    Collect everything `obj.msg()` receives inside the block.

    Same swap-and-restore as `tests/test_work_command.py` and as
    `EvenniaCommandTestMixin.call()` performs on its receivers.
    """
    seen = []
    original = obj.msg

    def collect(text="", *args, **kwargs):
        seen.append(str(text))

    obj.msg = collect
    try:
        yield seen
    finally:
        obj.msg = original


def exists(obj_id):
    """The receipt used in-game too: is this id still in the database?"""
    return ObjectDB.objects.filter(id=obj_id).exists()


class _CorpseFixture:
    """Shared builders. Mixed into the Evennia base classes below."""

    character_typeclass = CHARACTER
    room_typeclass = ROOM

    def make_corpse(self, key, typeclass=PLAYER_CORPSE, expired=True, location=None):
        corpse = create_object(typeclass, key=key, location=location or self.room1)
        if expired:
            # Same expression as the in-game protocol.
            corpse.db.death_time = 1
        # Precondition receipt: without it, a "nothing happened" assertion
        # could pass because the corpse was never expired to begin with.
        self.assertEqual(corpse.is_expired, expired)
        return corpse

    def make_ring(self, corpse, home):
        return create_object(OBJECT, key="janitorring", location=corpse, home=home)


class TestCrumbleIsTheSingleWriter(_CorpseFixture, EvenniaTest):
    """`crumble()` itself: destroy, don't relocate; say it once; never crash twice."""

    def test_contents_are_destroyed_not_relocated(self):
        corpse = self.make_corpse("janitorcorpse")
        ring = self.make_ring(corpse, home=self.room2)
        corpse_id, ring_id = corpse.id, ring.id

        self.assertTrue(corpse.crumble())

        self.assertFalse(exists(ring_id))
        self.assertFalse(exists(corpse_id))
        self.assertFalse(ObjectDB.objects.filter(db_location=self.room2, db_key="janitorring").exists())

    def test_room_hears_one_line_with_the_held_clause(self):
        corpse = self.make_corpse("janitorcorpse")
        self.make_ring(corpse, home=self.room1)

        with captured_messages(self.char1) as seen:
            corpse.crumble()

        lines = [m for m in seen if "crumbles to dust" in m]
        self.assertEqual(len(lines), 1)
        self.assertIn("what it held is lost with it", lines[0])

    def test_an_empty_corpse_claims_nothing_was_lost(self):
        corpse = self.make_corpse("deercorpse", typeclass=CORPSE)

        with captured_messages(self.char1) as seen:
            corpse.crumble()

        lines = [m for m in seen if "crumbles to dust" in m]
        self.assertEqual(len(lines), 1)
        self.assertNotIn("lost with it", lines[0])

    def test_a_second_call_on_a_stale_reference_is_a_quiet_noop(self):
        corpse = self.make_corpse("janitorcorpse")

        self.assertTrue(corpse.crumble())
        # Same Python instance (the idmapper hands every caller this object).
        # Without the pk guard this raises ObjectDoesNotExist.
        self.assertFalse(corpse.crumble())


class TestEveryPathReachesCrumble(_CorpseFixture, EvenniaCommandTest):
    """
    With `crumble()` mocked, each trigger must call it exactly once and leave
    the corpse in the database. A call site that also deletes, or also speaks,
    shows up as a missing corpse or a leftover line.
    """

    def setUp(self):
        super().setUp()
        self.corpse = self.make_corpse("janitorcorpse")
        patcher = mock.patch.object(Corpse, "crumble", autospec=True, return_value=True)
        self.crumble = patcher.start()
        self.addCleanup(patcher.stop)

    def assert_only_crumble_acted(self):
        self.crumble.assert_called_once_with(self.corpse)
        self.assertTrue(exists(self.corpse.id))

    def test_look(self):
        self.corpse.return_appearance(self.char1)
        self.assert_only_crumble_acted()

    def test_harvest(self):
        output = self.call(CmdHarvest(), "janitorcorpse")
        self.assert_only_crumble_acted()
        self.assertNotIn("rotted", output)
        self.assertNotIn("crumbles", output)

    def test_room_entry(self):
        self.room1.at_object_receive(self.char1, self.room2)
        self.assert_only_crumble_acted()


class TestHarvestDestroysPlayerLoot(_CorpseFixture, EvenniaCommandTest):
    """The bug seen in-game on c49b19f: harvest teleported the loot home."""

    def test_harvesting_an_expired_player_corpse_destroys_what_it_held(self):
        corpse = self.make_corpse("janitorcorpse")
        ring = self.make_ring(corpse, home=self.room1)
        ring_id = ring.id

        output = self.call(CmdHarvest(), "janitorcorpse")

        self.assertIn("crumbles to dust", output)
        # Identical to in-game protocol step 4.
        self.assertEqual(
            (
                ObjectDB.objects.filter(id=ring_id).exists(),
                ObjectDB.objects.filter(id=ring_id, db_location=self.room1).exists(),
            ),
            (False, False),
        )


class TestRoomSweep(_CorpseFixture, EvenniaTest):
    """`Room.at_object_receive`: the lazy sweep on player arrival."""

    def setUp(self):
        super().setUp()
        # Precondition: the fixture's char1 is puppeted. If not, every
        # "player arrives" test below would exercise the early return.
        self.assertTrue(self.char1.has_account)

    def test_player_entry_sweeps_expired_and_spares_fresh(self):
        expired = self.make_corpse("oldcorpse", expired=True)
        fresh = self.make_corpse("newcorpse", expired=False)
        expired_id = expired.id

        self.room1.at_object_receive(self.char1, self.room2)

        # The receipt that the hook ran: its expired sibling is gone.
        self.assertFalse(exists(expired_id))
        self.assertTrue(exists(fresh.id))
        self.assertEqual(fresh.location, self.room1)

    def test_every_expired_corpse_goes_in_one_entry(self):
        ids = [self.make_corpse(f"oldcorpse{n}").id for n in range(3)]

        self.room1.at_object_receive(self.char1, self.room2)

        self.assertEqual([exists(i) for i in ids], [False, False, False])

    def test_creature_corpses_are_swept_too(self):
        corpse_id = self.make_corpse("deercorpse", typeclass=CORPSE).id

        self.room1.at_object_receive(self.char1, self.room2)

        self.assertFalse(exists(corpse_id))

    def test_an_item_arriving_does_not_sweep(self):
        corpse_id = self.make_corpse("oldcorpse").id

        # The shape of a delete cascade: an unpuppeted object teleported home.
        self.room1.at_object_receive(self.obj1, self.room2, move_type="teleport")
        self.assertTrue(exists(corpse_id))

        # Positive twin, same corpse: proves it was sweepable all along.
        self.room1.at_object_receive(self.char1, self.room2)
        self.assertFalse(exists(corpse_id))

    def test_walking_in_runs_the_sweep(self):
        self.char1.move_to(self.room2, quiet=True)
        corpse_id = self.make_corpse("oldcorpse").id

        with captured_messages(self.char1) as seen:
            self.char1.move_to(self.room1)

        self.assertFalse(exists(corpse_id))
        # The arriving player sees the line (decision 3B).
        self.assertTrue(any("crumbles to dust" in m for m in seen))
