"""
`hunt` run to its outcome through `CmdHunt`, with both dice pinned (Skill-Check
Forms decomposition, SC-T3, SC4).

The hunt calls `opposed_check(hunting, flee_skill, attacker_mod=physical)` and
nothing else decides it, so the corrected judge (OC1, SC2) and the over-100 %
rule (OC2, SC3) reach it without an edit to `commands/hunting_commands.py`.
These tests read what became of the quarry, not what the command printed:

- a kill leaves a `Corpse` in the room and no creature;
- a flight leaves no corpse and no creature in the room (the creature moved
  through the room's exit, or was deleted where there is none --
  `hunting_commands.py:167-173`), so `pk` alone cannot tell it from a kill;
- a stalemate leaves the creature where it was.

Receipts in every test, whatever the outcome: before the command, the
hunter's physical modifier is 0 and the trait's value is the number meant, so
the target is exactly that value; after it, the patch has rolled exactly two
dice (hunter, then quarry). The skill-improvement roll after a kill uses
`world.improvement`'s own `randint` and is not counted.

Each test was red against `main`'s `world/skillcheck.py` (killed, fled, fled).
"""

from unittest import mock

from evennia import create_object
from evennia.utils.test_resources import EvenniaCommandTest

from commands.hunting_commands import CmdHunt
from tests.test_activity_log import ActivityLogMixin

CHARACTER = "typeclasses.characters.Character"
ROOM = "typeclasses.rooms.Room"
CREATURE = "typeclasses.creatures.Creature"
CORPSE = "typeclasses.corpse.Corpse"
ROLL = "world.skillcheck.randint"
QUARRY = "sct3deer"


class _HuntFixture:
    character_typeclass = CHARACTER
    room_typeclass = ROOM

    def setUp(self):
        super().setUp()
        self.char1.cooldowns.clear()
        # Fresh: the fatigue term of physical_modifier() is 0 (S3.2), and the
        # fixture carries nothing, so overload's term is 0 too.
        self.char1.traits.fatigue.current = 100

    def hunt(self, hunting, flee_skill, dice):
        """Run `hunt` at exactly `hunting` against `flee_skill`; return the quarry."""
        quarry = create_object(CREATURE, key=QUARRY, location=self.room1)
        quarry.db.flee_skill = flee_skill

        trait = self.char1.skills.get("hunting")
        trait.mod = hunting - trait.current   # counter: value = current + mod
        self.assertEqual(self.char1.physical_modifier(), 0)
        self.assertEqual(trait.value, hunting)

        with mock.patch(ROLL, side_effect=list(dice)) as die:
            self.call(CmdHunt(), QUARRY, caller=self.char1)
        self.assertEqual(die.call_count, 2)
        return quarry

    def in_room(self, typeclass):
        return [o for o in self.room1.contents if o.is_typeclass(typeclass, exact=False)]

    def assertKilled(self, quarry):
        self.assertIsNone(quarry.pk)
        self.assertEqual(len(self.in_room(CORPSE)), 1)
        self.assertEqual(self.in_room(CREATURE), [])

    def assertFled(self, quarry):
        self.assertEqual(self.in_room(CORPSE), [])
        self.assertEqual(self.in_room(CREATURE), [])
        # Moved through the fixture's exit, or deleted where there is none.
        if quarry.pk:
            self.assertEqual(quarry.location, self.room2)

    def assertStillThere(self, quarry):
        self.assertEqual(self.in_room(CORPSE), [])
        self.assertEqual(self.in_room(CREATURE), [quarry])


class TestHuntUnderTheCorrectedOpposedTest(ActivityLogMixin, _HuntFixture, EvenniaCommandTest):
    def test_an_automatic_success_outside_the_skill_does_not_fell_the_quarry(self):
        # OC1: hunting 3 rolling 05 against flee 30 rolling 04. The hunter's
        # 05 lies outside his skill and counts 0; the quarry's 04 is within.
        # Before SC-T1: the higher raw roll won, and the quarry was killed.
        self.assertFled(self.hunt(3, 30, [5, 4]))

    def test_a_quarrys_success_is_lost_to_the_hunters_excess(self):
        # OC2: hunting 120 against flee 30 -> excess 20, targets 100 and 10.
        # 97 fails at 100; the quarry's 20 is a success at 30 but a failure at
        # 10. Both fail: a stalemate. Before SC-T2: the quarry fled.
        self.assertStillThere(self.hunt(120, 30, [97, 20]))

    def test_the_excess_turns_a_flight_into_a_kill(self):
        # OC2: hunting 120 against flee 90 -> excess 20, targets 100 and 70.
        # The quarry's 85 is a success at 90 and a failure at 70, so the
        # hunter's 50 wins on level. Before SC-T2: the higher 85 won, a flight.
        self.assertKilled(self.hunt(120, 90, [50, 85]))
