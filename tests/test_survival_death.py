"""
Starvation and thirst followed through the survival tick to a death. Wounds,
Task WN-T1 (docs/PolishedWorld_Wounds_Decomposition.md, §4 P2).

WHY THIS MODULE EXISTS
----------------------
The writer of hurt, `Character.apply_health_damage`, has one call in
production (`world/survival_ticker.py`, `_apply_survival_conditions`), and
before this module only five tests noticed when it changed: each passed
through it on the way to something else (a push, a fatigue penalty, a
blocked heal). Nothing followed a starving body to its death, and the
ticker's promise *one fatal tick -> one corpse* was held by no test. The
wound slice rewrites that chain, so the net is woven first, against the code
as it stands.

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
The tests read what a player could see: dead or not, how many corpses lie
where the body fell, where the body is, whether the condition is on. The
body's hurt is read through one helper, `_hurt`, so the task that moves the
damage onto the locations (WN-T5) changes one function and not every
assertion.

- A gauge at its minimum hurts by one and puts its condition on, for hunger
  and for thirst (both rows of `HEALTH_CONDITIONS`). The one is typed, not
  read from `STARVE_DAMAGE`: an assertion that reads the constant reads the
  value a mutation of it changes, and passes at 0 = 0.
- Both gauges at their minimum hurt by two in ONE call of the writer. The
  spy is the only test that tells a sum from a call per condition: under a
  call per condition the second call never happens on a fatal tick (the
  loop reads thirst again after the respawn has filled it), so the death
  test alone would still see one corpse.
- A body one point from death under both conditions dies once: one corpse
  where it fell, the body at its respawn point, unhurt, both conditions
  gone. The respawn point is room2, since the fixture's fallback (`home`) is
  the room it falls in.
- A fed body is not hurt and its condition comes off. Its hunger is 50, not
  1: the tick depletes the gauges before it reads them.
- A character with no session is not ticked; the fixture's char1 has the
  session and is the receipt that the loop ran.

The tick is driven by calling `survival_ticker._deplete_character`, as
`tests.test_fatigue.TestAwakeTick` does, with the room's weather patched out.
The game clock is left alone: the first tick of a fixture reads 0 game
seconds, so neither the awake test nor natural healing takes part.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_survival_death
"""

from unittest import mock

from evennia.utils.test_resources import EvenniaTest

from typeclasses.corpse import PlayerCorpse
from world import survival_ticker, wounds
from world.survival_buffs import Dehydrated, Starving

WEATHER = "world.survival_ticker.apply_thermal_stress"


def _hurt(char):
    """
    How much hurt the body carries, as one number: the largest damage on
    any location (WN-T5). Starvation's points land on every location, so on
    the fixture's body it is the head's.
    """
    return max((char.db.body_damage or {}).values(), default=0)


class _Tick(EvenniaTest):
    """char1 fed and watered in room1, respawning in room2."""

    def setUp(self):
        super().setUp()
        self.char1.db.respawn_location = self.room2
        self.hunger = self.char1.traits.hunger
        self.thirst = self.char1.traits.thirst

    def tick(self):
        with mock.patch(WEATHER):
            survival_ticker._deplete_character(self.char1)

    def corpses(self):
        return [obj for obj in self.room1.contents if isinstance(obj, PlayerCorpse)]


class TestAGaugeAtItsMinimum(_Tick):
    def test_hunger_at_zero_hurts_one_and_starves(self):
        self.hunger.current = self.hunger.min
        self.tick()
        self.assertEqual(_hurt(self.char1), 1)
        self.assertTrue(self.char1.buffs.has(Starving))
        self.assertFalse(self.char1.buffs.has(Dehydrated))

    def test_thirst_at_zero_hurts_one_and_dehydrates(self):
        self.thirst.current = self.thirst.min
        self.tick()
        self.assertEqual(_hurt(self.char1), 1)
        self.assertTrue(self.char1.buffs.has(Dehydrated))
        self.assertFalse(self.char1.buffs.has(Starving))


class TestBothGaugesAtTheirMinimum(_Tick):
    def test_two_points_in_one_call_of_the_writer(self):
        self.hunger.current = self.hunger.min
        self.thirst.current = self.thirst.min
        with mock.patch.object(
            self.char1, "apply_health_damage", wraps=self.char1.apply_health_damage
        ) as writer:
            self.tick()
        writer.assert_called_once_with(2, location=wounds.ALL, source="survival")
        self.assertEqual(_hurt(self.char1), 2)   # receipt: the call went through

    def test_one_point_from_death_dies_once(self):
        # The fixture's head is 4 (CON + SIZ 20): a Major Wound at 8.
        self.char1.apply_health_damage(7, location=wounds.ALL)
        self.assertEqual(wounds.health_of(self.char1), (1, 8, 12.5))   # receipt
        self.hunger.current = self.hunger.min
        self.thirst.current = self.thirst.min
        self.tick()
        self.assertEqual(len(self.corpses()), 1)
        self.assertEqual(self.char1.location, self.room2)
        self.assertEqual(_hurt(self.char1), 0)
        self.assertFalse(self.char1.buffs.has(Starving))
        self.assertFalse(self.char1.buffs.has(Dehydrated))


class TestAFedBody(_Tick):
    def test_is_not_hurt_and_stops_starving(self):
        self.char1.buffs.add(Starving)
        self.hunger.current = 50
        self.tick()
        self.assertEqual(self.hunger.current, 49)   # receipt: the tick ran
        self.assertEqual(_hurt(self.char1), 0)
        self.assertFalse(self.char1.buffs.has(Starving))


class TestABodyWithNoSession(_Tick):
    def test_is_not_ticked(self):
        self.assertEqual(self.char2.sessions.count(), 0)
        self.char1.traits.hunger.current = 50
        self.char2.traits.hunger.current = 50
        with mock.patch(WEATHER):
            survival_ticker.deplete_all_survival_traits()
        self.assertEqual(self.char1.traits.hunger.current, 49)   # receipt: the loop ran
        self.assertEqual(self.char2.traits.hunger.current, 50)
        self.assertEqual(_hurt(self.char2), 0)
