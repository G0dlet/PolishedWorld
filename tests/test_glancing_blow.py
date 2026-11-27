"""
*Glancing Blow*: a blow that would give a location a Major Wound gives it a
Serious one instead, for one Hero Point, when the character has a point and
has not switched it off. Hero Points decomposition, Task HE-T6 (Combat
Design §4.13, HP2, HE1, HE2, HE6; *Legend* core pp. 88, 145-146).

The body is the fixture's char1, CON 10 + SIZ 10, **left as a new player's
is**: nothing stored, so two Hero Points and the switch on (HE3, HE6). The
four wound test modules switch *Glancing Blow* off in their base classes
(HE-T5); this one does not, and `_Glancing` is its own base for that reason.
Every number is read from the body's maxima, never typed: on the fixture the
head is 4, so a Major Wound is 8 and one short of it is 7, and a blow of
2 x max + 2 is 10 (Testing Reference §27.2).

The dice are `tests.test_wound_states`'s: `MADE` an attack roll, `WIN` and
`LOSE` the Resilience test's die under `ROLL`. The clock and the alarms are
patched as in tests/test_wound_clocks.py, since an untrimmed Major Wound
starts a clock through the writer.

WHAT EACH CLASS PUTS PRESSURE ON

- `TestTheDoor`: `hero_points.take_for_glancing` -- one fewer stored and True
  when there is a point and the switch is on; False and nothing written
  otherwise (HE6 a).
- `TestTheTrim`: what the door's True does to the blow -- the location left
  at 2 x max - 1, a Serious Wound and only its test, the minutes counted on
  the damage written, a limb *disabled* and never *maimed*, a trimmed 0
  still answered, and `glancing` in the outcome (HE1).
- `TestNoTrim`: where the door is not asked, or says no -- a location
  already at a Major Wound, no points, the switch off, `ALL`, a blow that
  stays below a Major Wound, and every refusal before a point is taken
  (HE1 c, HE2, HE6 a).
"""

from unittest import mock

from evennia.utils.test_resources import EvenniaTest

from tests.test_wound_states import LOSE, MADE, ROLL, WIN
from world import hero_points, wounds

NOW = 1_000_000.0


class _Glancing(EvenniaTest):
    """char1 Fresh, with a respawn point, and *Glancing Blow* as a new
    player's: two points and on, nothing stored."""

    def setUp(self):
        super().setUp()
        self.char1.traits.fatigue.current = 100
        self.char1.db.respawn_location = self.room2
        clock = mock.patch("world.wounds._now")
        self.now = clock.start()
        self.now.return_value = NOW
        alarm = mock.patch("world.wounds.delay")
        alarm.start()
        slot = mock.patch("world.timed_actions.delay")
        slot.start()
        for patcher in (clock, alarm, slot):
            self.addCleanup(patcher.stop)
        self.maxima = wounds.maxima_of(self.char1)

    def heavy(self, key):
        """A blow that takes the unhurt location past a Major Wound."""
        return 2 * self.maxima[key] + 2

    def short(self, key):
        """One short of a Major Wound: where Glancing Blow leaves it."""
        return 2 * self.maxima[key] - 1

    def blow(self, amount, location, roll=WIN, made=MADE):
        """The door, with the die fixed: returns its outcome."""
        with mock.patch(ROLL, return_value=roll):
            return wounds.damage(self.char1, amount, location, made)

    def writer(self, amount, location, roll=WIN, made=MADE):
        """The writer, with the die fixed: what a source would call."""
        with mock.patch(ROLL, return_value=roll), mock.patch.object(self.char1, "msg"):
            self.char1.apply_health_damage(amount, location=location, made=made)

    def hurt(self, **damage):
        """Put damage on the body as if earlier blows had left it."""
        self.char1.db.body_damage = damage

    def body(self):
        return wounds.damage_of(self.char1)

    def states(self):
        if not self.char1.attributes.has("wound_states"):
            return None
        return dict(self.char1.db.wound_states)

    def nothing_spent(self):
        """No point taken: nothing stored, so the body still reads two."""
        self.assertFalse(self.char1.attributes.has("hero_points"))
        self.assertEqual(hero_points.points(self.char1), hero_points.START)


class TestTheDoor(_Glancing):
    def test_a_point_and_the_switch_on_take_one(self):
        self.assertTrue(hero_points.take_for_glancing(self.char1))
        self.assertEqual(self.char1.db.hero_points, 1)

    def test_the_last_point_is_stored_as_zero(self):
        self.char1.db.hero_points = 1
        self.assertTrue(hero_points.take_for_glancing(self.char1))
        self.assertEqual(self.char1.db.hero_points, 0)

    def test_no_points_answer_no_and_write_nothing(self):
        self.char1.db.hero_points = 0
        self.assertFalse(hero_points.take_for_glancing(self.char1))
        self.assertEqual(self.char1.db.hero_points, 0)

    def test_the_switch_off_answers_no_and_writes_nothing(self):
        hero_points.set_glancing(self.char1, False)
        self.assertFalse(hero_points.take_for_glancing(self.char1))
        self.nothing_spent()


class TestTheTrim(_Glancing):
    def test_an_unhurt_head_and_a_heavy_blow_is_a_serious_wound_for_a_point(self):
        outcome = self.blow(self.heavy("head"), "head")
        self.assertEqual(self.body(), {"head": self.short("head")})
        self.assertEqual(hero_points.points(self.char1), 1)
        wound = outcome["wounds"][0]
        self.assertEqual(wound["level"], wounds.SERIOUS)
        self.assertTrue(wound["glancing"])
        self.assertIsNone(wound["state"])
        self.assertFalse(wound["clock"])
        self.assertFalse(outcome["dies"])
        self.assertIsNone(self.states())

    def test_a_lost_test_is_senseless_for_the_damage_written(self):
        outcome = self.blow(self.heavy("head"), "head", roll=LOSE)
        wound = outcome["wounds"][0]
        self.assertTrue(wound["unconscious"])
        self.assertEqual(wound["minutes"], self.short("head"))
        self.assertFalse(outcome["dies"])

    def test_through_the_writer_the_body_is_out_and_no_clock_runs(self):
        self.writer(self.heavy("head"), "head", roll=LOSE)
        self.assertEqual(
            self.char1.db.wound_unconscious["until"],
            NOW + self.short("head") * wounds.MINUTE,
        )
        self.assertFalse(self.char1.attributes.has("wound_clocks"))
        self.assertEqual(self.char1.location, self.room1)

    def test_a_leg_is_disabled_on_a_lost_test_and_never_maimed(self):
        outcome = self.blow(self.heavy("left_leg"), "left_leg", roll=LOSE)
        self.assertEqual(self.body(), {"left_leg": self.short("left_leg")})
        self.assertEqual(outcome["wounds"][0]["state"], wounds.DISABLED)
        self.assertEqual(self.states(), {"left_leg": wounds.DISABLED})
        self.assertFalse(outcome["wounds"][0]["clock"])

    def test_a_hurt_head_takes_only_what_is_left_and_is_out_for_that(self):
        already = self.maxima["head"] + 1
        self.hurt(head=already)
        outcome = self.blow(self.heavy("head"), "head", roll=LOSE)
        self.assertEqual(self.body(), {"head": self.short("head")})
        self.assertEqual(outcome["wounds"][0]["minutes"], self.short("head") - already)

    def test_one_short_and_hit_again_costs_a_point_and_takes_nothing(self):
        self.hurt(head=self.short("head"))
        outcome = self.blow(1, "head", roll=LOSE)
        self.assertIsNotNone(outcome)
        self.assertEqual(self.body(), {"head": self.short("head")})
        self.assertEqual(hero_points.points(self.char1), 1)
        wound = outcome["wounds"][0]
        self.assertEqual(wound["level"], wounds.SERIOUS)
        self.assertTrue(wound["glancing"])
        self.assertFalse(wound["test"]["resisted"])

    def test_one_short_and_a_lost_test_knocks_no_one_out(self):
        self.hurt(head=self.short("head"))
        outcome = self.blow(1, "head", roll=LOSE)
        wound = outcome["wounds"][0]
        self.assertFalse(wound["unconscious"])
        self.assertIsNone(wound["minutes"])

    def test_with_no_attack_roll_it_is_trimmed_all_the_same(self):
        outcome = self.blow(self.heavy("head"), "head", made=None)
        self.assertEqual(self.body(), {"head": self.short("head")})
        self.assertEqual(hero_points.points(self.char1), 1)
        self.assertIsNone(outcome["wounds"][0]["test"])

    def test_a_random_blow_is_trimmed(self):
        key = wounds.location_for(20)
        with mock.patch("world.wounds.randint", return_value=20):
            self.blow(self.heavy(key), wounds.RANDOM)
        self.assertEqual(self.body(), {key: self.short(key)})
        self.assertEqual(hero_points.points(self.char1), 1)

    def test_two_points_answer_two_blows_and_the_third_maims(self):
        for key in ("head", "chest"):
            self.blow(self.heavy(key), key)
        outcome = self.blow(self.heavy("left_leg"), "left_leg")
        self.assertEqual(self.char1.db.hero_points, 0)
        self.assertEqual(outcome["wounds"][0]["state"], wounds.MAIMED)
        self.assertFalse(outcome["wounds"][0]["glancing"])
        self.assertEqual(self.body()["left_leg"], self.heavy("left_leg"))


class TestNoTrim(_Glancing):
    def test_a_head_already_at_a_major_wound_costs_nothing(self):
        major = 2 * self.maxima["head"]
        self.hurt(head=major)
        outcome = self.blow(1, "head")
        self.assertEqual(self.body(), {"head": major + 1})
        self.assertFalse(outcome["wounds"][0]["glancing"])
        self.nothing_spent()

    def test_no_points_the_major_wound_stands(self):
        self.char1.db.hero_points = 0
        outcome = self.blow(self.heavy("head"), "head")
        self.assertEqual(self.body(), {"head": self.heavy("head")})
        self.assertEqual(outcome["wounds"][0]["state"], wounds.MAIMED)
        self.assertTrue(outcome["wounds"][0]["clock"])
        self.assertEqual(self.char1.db.hero_points, 0)

    def test_switched_off_the_major_wound_stands_and_the_points_are_kept(self):
        hero_points.set_glancing(self.char1, False)
        outcome = self.blow(self.heavy("head"), "head")
        self.assertEqual(self.body(), {"head": self.heavy("head")})
        self.assertEqual(outcome["wounds"][0]["state"], wounds.MAIMED)
        self.assertFalse(outcome["wounds"][0]["glancing"])
        self.nothing_spent()

    def test_all_takes_no_point_and_kills_as_today(self):
        outcome = self.blow(self.heavy("head"), wounds.ALL, made=None)
        self.assertTrue(outcome["dies"])
        self.assertEqual(self.body()["head"], self.heavy("head"))
        self.nothing_spent()

    def test_a_blow_that_stays_below_a_major_wound_does_not_ask(self):
        with mock.patch.object(
                hero_points, "take_for_glancing", wraps=hero_points.take_for_glancing) as door:
            outcome = self.blow(self.maxima["head"] + 1, "head")
        door.assert_not_called()
        self.assertFalse(outcome["wounds"][0]["glancing"])
        self.nothing_spent()

    def test_a_failed_attack_roll_is_refused_before_a_point_is_taken(self):
        failed = dict(MADE, result="failure", success=False)
        with self.assertRaises(ValueError):
            self.blow(self.heavy("head"), "head", made=failed)
        self.assertEqual(self.body(), {})
        self.nothing_spent()

    def test_a_dying_body_is_refused_before_a_point_is_taken(self):
        self.char1.ndb._dying = True
        self.assertIsNone(self.blow(self.heavy("head"), "head"))
        self.nothing_spent()
