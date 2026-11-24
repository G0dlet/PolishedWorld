"""
What a blow's wound leaves: the Resilience test and the stored states.
Wounds, Task WN-T8 (docs/PolishedWorld_Wounds_Decomposition.md; Combat
Design §4.4, WO1-WO3, WN5, WN7-WN9; *Legend* core pp. 145-146).

Starvation is the only source of damage in the game and reaches none of
this (WN5), so every case here is a named or random blow put on by hand.
The die is fixed by patching `world.skillcheck.randint`, as
tests/test_encumbrance.py does: the attack roll is a success at 5 against
60, and Resilience (20 on the fixture, CON x 2) rolls 15 to win -- a success
higher within its skill -- or 98 to lose.

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
- `TestRespawn`: WN9 -- death empties the damage and clears *disabled*;
  *maimed* stays. The first test writes the states by hand: on WN-T5's code
  the restore removed the damage and left *disabled* behind (the red). The
  second gets there by play: a maimed leg and a disabled arm, then the
  death. A death by starvation leaves no state (WN5).
- `TestTheTable`: the decomposition's table, row by row, won and lost, on
  the fixture's body (head 4, chest 6, abdomen 5, arms 3, legs 4). A
  limb's Serious Wound lost is *disabled*, won is nothing; a vital
  location's Serious Wound lost is unconsciousness for the damage in
  minutes and no state; a limb's Major Wound is *maimed* and a clock either
  way, unconscious only on a loss; a vital Major Wound is *maimed*, death at
  once on a loss -- through the writer, so a corpse is the receipt -- and
  unconsciousness and a clock on a win. A head that won takes the next blow
  and its test can kill: the door's guard is a death in progress, not a
  vital Major Wound (choice A). A blow that leaves the location above 0
  calls for nothing.
- `TestTheTest`: the modifier handed to `opposed_against` is the whole of
  `physical_modifier()`, read for an overloaded, Wearied body (-50, WN7);
  the skill is Resilience's value. A second blow on a location already
  below 0 is tested again (p. 145); a blow elsewhere does not test it. The
  test's dict comes back whole, `resisting` included (WN8's input).
- `TestNoAttackRoll`: OQ-WN1 under choice B -- with no `made` there is no
  test and nothing a lost test brings (no *disabled*, no death at once), and
  what the wound gives whatever the test still comes (*maimed*, the vital
  Major Wound's unconsciousness and clock). A `made` that failed, or one
  given with `ALL`, is refused before anything is written.
- `TestAllSetsNothing`: WN5 -- `ALL` damage that brings every limb to 0 sets
  no state and rolls no test.
- `TestStatesOverTime`: *disabled* goes when healing lifts the limb above 0
  and stays while it is at 0; a heavier state replaces a lighter one and
  never the other way round; *severed* with `SEVERED_ENABLED` patched on
  replaces *maimed* on a limb and never on a vital location.
- `TestResilienceDoesNotTrainYet`: the wound module calls
  `attempt_skill_improvement` nowhere until ML (WN8).

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_wound_states
"""

import ast
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase
from evennia import create_object
from evennia.utils.test_resources import EvenniaTest

from tests import test_improvement_engine
from typeclasses.corpse import PlayerCorpse
from world import skill_base, skillcheck, wounds

MADE = {"result": "success", "success": True, "roll": 5, "target": 60,
        "margin": 55, "crit_score": 6}
WIN = 15    # Resilience 20: a success, and higher within the skill than 5
LOSE = 98   # a failure, and no fumble
ROLL = "world.skillcheck.randint"


def _states(char):
    """The stored states as a plain dict; None when there is no Attribute."""
    if not char.attributes.has("wound_states"):
        return None
    return dict(char.db.wound_states)


def _corpses(room):
    return [o for o in room.contents if isinstance(o, PlayerCorpse)]


class _Body(EvenniaTest):
    """The fixture's body, CON 10 + SIZ 10; Fresh, so the modifier is 0."""

    def setUp(self):
        super().setUp()
        self.char1.traits.fatigue.current = 100
        self.char1.db.respawn_location = self.room2

    def blow(self, amount, location, roll, made=MADE):
        """The door, with the die fixed: returns its outcome."""
        with mock.patch(ROLL, return_value=roll):
            return wounds.damage(self.char1, amount, location, made)

    def writer(self, amount, location, roll, made=MADE):
        """The writer, with the die fixed: what a source would call."""
        with mock.patch(ROLL, return_value=roll):
            self.char1.apply_health_damage(amount, location=location, made=made)


class TestRespawn(_Body):
    def test_a_death_keeps_maimed_and_clears_disabled(self):
        # A premise written by hand: the states as a blow would leave them.
        self.char1.db.wound_states = {"left_leg": "maimed", "right_arm": "disabled"}
        self.char1.apply_health_damage(8, location=wounds.ALL)   # the head's Major Wound
        self.assertEqual(self.char1.location, self.room2)
        self.assertEqual(_states(self.char1), {"left_leg": "maimed"})

    def test_a_maimed_leg_and_a_disabled_arm_then_a_death(self):
        self.writer(8, "left_leg", WIN)    # Major: maimed whatever the test
        self.writer(3, "right_arm", LOSE)  # Serious, lost: disabled
        self.assertEqual(_states(self.char1), {"left_leg": "maimed", "right_arm": "disabled"})
        self.char1.apply_health_damage(8, location=wounds.ALL)
        self.assertEqual(self.char1.location, self.room2)
        self.assertIsNone(self.char1.db.body_damage)
        self.assertEqual(_states(self.char1), {"left_leg": "maimed"})

    def test_a_death_by_starvation_leaves_no_state(self):
        self.char1.apply_health_damage(8, location=wounds.ALL)
        self.assertEqual(len(_corpses(self.room1)), 1)
        self.assertIsNone(_states(self.char1))


class TestTheTable(_Body):
    def test_a_limbs_serious_wound_lost_is_disabled(self):
        outcome = self.blow(4, "left_leg", LOSE)
        self.assertEqual(outcome["wounds"][0]["level"], wounds.SERIOUS)
        self.assertEqual(_states(self.char1), {"left_leg": "disabled"})
        self.assertFalse(outcome["dies"])

    def test_a_limbs_serious_wound_won_is_nothing(self):
        outcome = self.blow(4, "left_leg", WIN)
        self.assertTrue(outcome["wounds"][0]["test"]["resisted"])
        self.assertIsNone(_states(self.char1))

    def test_a_vital_serious_wound_lost_knocks_out_for_the_damage_in_minutes(self):
        wound = self.blow(5, "head", LOSE)["wounds"][0]   # head 4: -1, Serious
        self.assertEqual((wound["level"], wound["unconscious"], wound["minutes"]),
                         (wounds.SERIOUS, True, 5))
        self.assertFalse(wound["clock"])
        self.assertIsNone(_states(self.char1))

    def test_a_vital_serious_wound_won_is_nothing(self):
        self.assertEqual(self.blow(4, "chest", WIN)["wounds"], [])   # chest 6: 2, Minor
        wound = self.blow(2, "chest", WIN)["wounds"][0]   # 0: Serious
        self.assertFalse(wound["unconscious"])
        self.assertIsNone(_states(self.char1))

    def test_a_limbs_major_wound_lost_maims_knocks_out_and_starts_a_clock(self):
        wound = self.blow(8, "left_leg", LOSE)["wounds"][0]
        self.assertEqual((wound["level"], wound["state"]), (wounds.MAJOR, wounds.MAIMED))
        self.assertEqual((wound["unconscious"], wound["minutes"], wound["clock"]), (True, 8, True))
        self.assertEqual(_states(self.char1), {"left_leg": "maimed"})

    def test_a_limbs_major_wound_won_maims_and_starts_a_clock(self):
        wound = self.blow(8, "left_leg", WIN)["wounds"][0]
        self.assertEqual((wound["unconscious"], wound["clock"]), (False, True))
        self.assertEqual(_states(self.char1), {"left_leg": "maimed"})

    def test_a_vital_major_wound_lost_is_death_at_once(self):
        self.writer(8, "head", LOSE)
        self.assertEqual(len(_corpses(self.room1)), 1)
        self.assertEqual(self.char1.location, self.room2)
        # The respawn emptied the damage and kept the head maimed (WN9, OQ-WN2).
        self.assertIsNone(self.char1.db.body_damage)
        self.assertEqual(_states(self.char1), {"head": "maimed"})

    def test_a_vital_major_wound_won_is_unconsciousness_and_a_clock_not_death(self):
        self.writer(8, "head", WIN)
        self.assertEqual(_corpses(self.room1), [])
        self.assertEqual(self.char1.location, self.room1)
        self.assertEqual(self.char1.db.body_damage["head"], 8)
        self.assertEqual(_states(self.char1), {"head": "maimed"})
        self.char1.attributes.remove("body_damage")
        outcome = self.blow(8, "head", WIN)
        self.assertEqual(
            (outcome["dies"], outcome["wounds"][0]["unconscious"], outcome["wounds"][0]["clock"]),
            (False, True, True))

    def test_a_survived_head_takes_the_next_blow_and_its_test_can_kill(self):
        # The door's guard is a death in progress, not a vital Major Wound:
        # a head that won its test is wounded again and tested again.
        self.writer(8, "head", WIN)
        self.writer(1, "head", LOSE)
        self.assertEqual(len(_corpses(self.room1)), 1)
        self.assertEqual(self.char1.location, self.room2)

    def test_a_blow_that_leaves_the_location_above_zero_calls_for_nothing(self):
        with mock.patch("world.wounds.opposed_against") as test:
            outcome = self.blow(3, "left_leg", LOSE)
        test.assert_not_called()
        self.assertEqual(outcome, {"dies": False, "wounds": []})
        self.assertIsNone(_states(self.char1))


class TestTheTest(_Body):
    def spy(self):
        return mock.patch("world.wounds.opposed_against", wraps=skillcheck.opposed_against)

    def test_the_modifier_is_the_whole_physical_modifier(self):
        self.char1.traits.fatigue.current = 40                       # Wearied: -30
        load = create_object("typeclasses.objects.Object", key="load", location=self.char1)
        load.db.enc = 21                                             # past the limit: -20
        self.assertEqual(self.char1.physical_modifier(), -50)        # the premise
        with self.spy() as test:
            self.blow(4, "left_leg", LOSE)
        test.assert_called_once_with(
            MADE, skill_base.value_of(self.char1, "resilience"), -50)

    def test_the_test_comes_back_whole(self):
        test = self.blow(4, "left_leg", WIN)["wounds"][0]["test"]
        self.assertIs(test["made"], MADE)
        self.assertEqual(test["resisting"]["roll"], WIN)

    def test_a_second_blow_on_a_location_below_zero_is_tested_again(self):
        with self.spy() as test:
            self.blow(4, "left_leg", WIN)     # 0: tested
            self.blow(1, "left_leg", LOSE)    # -1: wounded again, tested again
        self.assertEqual(test.call_count, 2)
        self.assertEqual(_states(self.char1), {"left_leg": "disabled"})

    def test_a_blow_elsewhere_does_not_test_a_wounded_location(self):
        self.blow(4, "left_leg", WIN)
        with self.spy() as test:
            outcome = self.blow(1, "chest", LOSE)
        test.assert_not_called()
        self.assertEqual(outcome["wounds"], [])
        self.assertIsNone(_states(self.char1))

    def test_random_tests_the_location_the_table_names(self):
        with mock.patch("world.wounds.randint", return_value=1):     # right leg
            outcome = self.blow(4, wounds.RANDOM, LOSE)
        self.assertEqual(outcome["wounds"][0]["location"], "right_leg")
        self.assertEqual(_states(self.char1), {"right_leg": "disabled"})


class TestNoAttackRoll(_Body):
    def test_a_limbs_serious_wound_with_no_roll_is_not_disabled(self):
        with mock.patch("world.wounds.opposed_against") as test:
            wound = self.blow(4, "left_leg", LOSE, made=None)["wounds"][0]
        test.assert_not_called()
        self.assertIsNone(wound["test"])
        self.assertIsNone(_states(self.char1))

    def test_a_vital_major_wound_with_no_roll_maims_and_does_not_kill(self):
        self.writer(8, "head", LOSE, made=None)
        self.assertEqual(self.char1.location, self.room1)
        self.assertEqual(_states(self.char1), {"head": "maimed"})
        self.char1.attributes.remove("body_damage")
        wound = self.blow(8, "head", LOSE, made=None)["wounds"][0]
        self.assertEqual((wound["unconscious"], wound["clock"], wound["dies"]), (True, True, False))

    def test_a_failed_roll_is_refused_before_anything_is_written(self):
        failed = dict(MADE, result="failure", success=False)
        with self.assertRaises(ValueError):
            self.char1.apply_health_damage(4, location="left_leg", made=failed)
        self.assertIsNone(self.char1.db.body_damage)

    def test_a_roll_with_all_is_refused_before_anything_is_written(self):
        with self.assertRaises(ValueError):
            self.char1.apply_health_damage(1, location=wounds.ALL, made=MADE)
        self.assertIsNone(self.char1.db.body_damage)


class TestAllSetsNothing(_Body):
    def test_all_that_brings_every_limb_to_zero_sets_no_state_and_rolls_nothing(self):
        with mock.patch("world.wounds.opposed_against") as test:
            outcome = wounds.damage(self.char1, 7, wounds.ALL)   # head 4: 7 is one short of Major
        test.assert_not_called()
        self.assertEqual(outcome, {"dies": False, "wounds": []})
        self.assertEqual(self.char1.db.body_damage["left_leg"], 4)   # Hit Points 0
        self.assertIsNone(_states(self.char1))


class TestStatesOverTime(_Body):
    def test_disabled_goes_when_healing_lifts_the_limb_above_zero(self):
        self.blow(5, "left_leg", LOSE)                  # leg 4: -1, disabled
        self.assertEqual(wounds.heal(self.char1, 1), 1)  # 0: still disabled
        self.assertEqual(_states(self.char1), {"left_leg": "disabled"})
        self.assertEqual(wounds.heal(self.char1, 1), 1)  # 1: above 0
        self.assertIsNone(_states(self.char1))

    def test_healing_leaves_maimed(self):
        self.blow(8, "left_leg", WIN)
        wounds.heal(self.char1, 8)
        self.assertIsNone(self.char1.db.body_damage)
        self.assertEqual(_states(self.char1), {"left_leg": "maimed"})

    def test_a_heavier_state_replaces_a_lighter_one_and_not_the_other_way(self):
        self.blow(4, "left_leg", LOSE)
        self.assertEqual(_states(self.char1), {"left_leg": "disabled"})
        self.blow(4, "left_leg", WIN)                   # 8: Major
        self.assertEqual(_states(self.char1), {"left_leg": "maimed"})
        self.blow(1, "left_leg", LOSE)                  # wounded again, lost
        self.assertEqual(_states(self.char1), {"left_leg": "maimed"})

    def test_severed_when_switched_on_and_only_on_a_limb(self):
        with mock.patch.object(wounds, "SEVERED_ENABLED", True):
            self.blow(8, "left_leg", WIN)
            self.blow(8, "head", WIN)
        self.assertEqual(_states(self.char1), {"left_leg": "severed", "head": "maimed"})

    def test_severed_is_switched_off(self):
        self.assertFalse(wounds.SEVERED_ENABLED)
        self.blow(8, "left_leg", WIN)
        self.assertEqual(_states(self.char1), {"left_leg": "maimed"})


class TestResilienceDoesNotTrainYet(SimpleTestCase):
    def test_the_wound_module_calls_no_improvement(self):
        path = Path(__file__).resolve().parent.parent / "world" / "wounds.py"
        self.assertEqual(
            # Through the module: a TestCase imported by name would run here too.
            test_improvement_engine.TestImprovementCallSiteCensus._sites(
                ast.parse(path.read_text())), 0,
            "WN8: Resilience's improvement call lands with ML, in "
            "wounds.resilience_test, with the winner's own skill_check dict.",
        )
