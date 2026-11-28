"""
Two doors for one location, and the mark First Aid leaves. Healing, Task
HL-T7 (docs/PolishedWorld_Healing_Decomposition.md §9; Combat Design §4.4,
HL7, WN1, WN9, WN10; *Legend* core pp. 50, 145).

The fixture's char1 has every characteristic at 10, so an arm's maximum is
read from `wounds.maxima_of` rather than written here. The doors are called
on a body set up by assignment to its Attributes: the writer's own rules
are the business of tests/test_wound_states.py, and these tests ask only
what the doors do to a body that is already hurt. Nothing calls the doors
in production until Healing HL-T9; the census holds that
(tests/test_client_state.py, `AWAITING_CALLER`).

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
- `TestMend`: three points to an arm with two of damage land two, and the
  location leaves the stored damage; another location's damage is untouched
  (HLM21); a location is never mended past unhurt (HLM22); a clocked
  location is refused and nothing is written (WN10); an unhurt location and
  no points land nothing; `ALL`, `RANDOM` and a stranger's word are refused;
  *disabled* goes above 0 Hit Points and stays at 0 (p. 145); *maimed* is
  never taken.
- `TestRestoreUse`: a limb at 0 or below loses *disabled* and keeps its
  damage (HL7, 4); another limb's state stays; *maimed* and *severed* are
  never taken (HLM25); what the hand held is held again (GR22).
- `TestTheMark`: a hurt location is marked once and an unhurt one never; the
  stored mark reads back through a `_SaverSet`; a new blow leaves it (p. 50);
  natural healing that makes a location whole takes its mark and leaves a
  hurt one's (HLM23); `mend` does the same; a death empties the marks and
  keeps *maimed* (WN9; HLM24).

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_wound_mend
"""

from collections.abc import Set

from evennia.utils.create import create_object
from evennia.utils.test_resources import EvenniaTest

from world import gear, wounds


class _Body(EvenniaTest):
    """A body hurt by assignment, and the arm's maximum for this fixture."""

    def setUp(self):
        super().setUp()
        self.arm = wounds.maxima_of(self.char1)["right_arm"]

    def hurt(self, **damage):
        self.char1.db.body_damage = dict(damage)

    def stored(self, name):
        return self.char1.attributes.get(name)


class TestMend(_Body):

    def test_three_points_to_an_arm_with_two_land_two(self):
        self.hurt(right_arm=2, head=1)
        self.assertEqual(wounds.mend(self.char1, "right_arm", 3), 2)
        self.assertEqual(wounds.damage_of(self.char1), {"head": 1})

    def test_another_location_is_untouched(self):
        self.hurt(right_arm=2, left_leg=3)
        self.assertEqual(wounds.mend(self.char1, "right_arm", 1), 1)
        self.assertEqual(wounds.damage_of(self.char1), {"right_arm": 1, "left_leg": 3})

    def test_a_location_is_never_mended_past_unhurt(self):
        self.hurt(right_arm=1)
        self.assertEqual(wounds.mend(self.char1, "right_arm", 3), 1)
        self.assertFalse(self.char1.attributes.has("body_damage"))

    def test_a_clocked_location_is_refused_and_nothing_is_written(self):
        self.hurt(left_leg=9, head=1)
        self.char1.db.wound_clocks = {"left_leg": 1000.0}
        self.assertEqual(wounds.mend(self.char1, "left_leg", 3), 0)
        self.assertEqual(wounds.damage_of(self.char1), {"left_leg": 9, "head": 1})

    def test_an_unhurt_location_or_no_points_lands_nothing(self):
        self.hurt(head=1)
        self.assertEqual(wounds.mend(self.char1, "right_arm", 2), 0)
        self.assertEqual(wounds.mend(self.char1, "head", 0), 0)
        self.assertEqual(wounds.damage_of(self.char1), {"head": 1})

    def test_one_location_only(self):
        for word in (wounds.ALL, wounds.RANDOM, "tail"):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    wounds.mend(self.char1, word, 1)

    def test_disabled_goes_above_zero_and_stays_at_zero(self):
        # p. 145, as in `heal`: the limb is useless until it is above 0.
        self.hurt(right_arm=self.arm + 1)
        self.char1.db.wound_states = {"right_arm": wounds.DISABLED}
        self.assertEqual(wounds.mend(self.char1, "right_arm", 1), 1)   # at 0
        self.assertEqual(wounds.states_of(self.char1), {"right_arm": wounds.DISABLED})
        self.assertEqual(wounds.mend(self.char1, "right_arm", 1), 1)   # at 1
        self.assertEqual(wounds.states_of(self.char1), {})
        self.assertFalse(self.char1.attributes.has("wound_states"))

    def test_maimed_is_never_taken(self):
        self.hurt(left_leg=9)
        self.char1.db.wound_states = {"left_leg": wounds.MAIMED}
        self.assertEqual(wounds.mend(self.char1, "left_leg", 9), 9)
        self.assertEqual(wounds.states_of(self.char1), {"left_leg": wounds.MAIMED})


class TestRestoreUse(_Body):

    def test_a_limb_at_zero_loses_disabled_and_keeps_its_damage(self):
        self.hurt(right_arm=self.arm)
        self.char1.db.wound_states = {"right_arm": wounds.DISABLED}
        self.assertTrue(wounds.restore_use(self.char1, "right_arm"))
        self.assertFalse(self.char1.attributes.has("wound_states"))
        self.assertEqual(wounds.damage_of(self.char1), {"right_arm": self.arm})

    def test_below_zero_too_and_another_limb_keeps_its_state(self):
        self.hurt(right_arm=self.arm + 2, left_arm=self.arm)
        self.char1.db.wound_states = {"right_arm": wounds.DISABLED,
                                      "left_arm": wounds.DISABLED}
        self.assertTrue(wounds.restore_use(self.char1, "right_arm"))
        self.assertEqual(wounds.states_of(self.char1), {"left_arm": wounds.DISABLED})

    def test_maimed_and_severed_are_never_taken(self):
        for state in (wounds.MAIMED, wounds.SEVERED):
            with self.subTest(state=state):
                self.char1.db.wound_states = {"left_leg": state}
                self.assertFalse(wounds.restore_use(self.char1, "left_leg"))
                self.assertEqual(wounds.states_of(self.char1), {"left_leg": state})

    def test_nothing_to_take_and_one_location_only(self):
        self.assertFalse(wounds.restore_use(self.char1, "right_arm"))
        self.assertFalse(self.char1.attributes.has("wound_states"))
        with self.assertRaises(ValueError):
            wounds.restore_use(self.char1, wounds.ALL)

    def test_what_the_hand_held_is_held_again(self):
        # GR22: a hand reads its arm lazily, and its entry stands.
        stick = create_object("typeclasses.objects.Object", key="hlt7stick",
                              location=self.char1)
        hands, reason = gear.hold(self.char1, stick, gear.RIGHT)
        self.assertEqual((hands, reason), ((gear.RIGHT,), None))
        self.hurt(right_arm=self.arm)
        self.char1.db.wound_states = {"right_arm": wounds.DISABLED}
        self.assertIsNone(gear.held(self.char1)[gear.RIGHT])
        wounds.restore_use(self.char1, "right_arm")
        self.assertEqual(gear.held(self.char1)[gear.RIGHT], stick)


class TestTheMark(_Body):

    def test_a_hurt_location_is_marked_once(self):
        self.hurt(right_arm=2)
        self.assertTrue(wounds.mark_tended(self.char1, "right_arm"))
        self.assertFalse(wounds.mark_tended(self.char1, "right_arm"))
        self.assertEqual(wounds.tended_of(self.char1), frozenset({"right_arm"}))

    def test_an_unhurt_location_is_never_marked(self):
        self.hurt(head=1)
        self.assertFalse(wounds.mark_tended(self.char1, "right_arm"))
        self.assertFalse(self.char1.attributes.has("wound_tended"))
        with self.assertRaises(ValueError):
            wounds.mark_tended(self.char1, wounds.RANDOM)

    def test_the_stored_mark_reads_back_through_a_saver_set(self):
        # The first set an Attribute holds in the project (lesson candidate 36).
        self.hurt(right_arm=2, left_leg=1)
        wounds.mark_tended(self.char1, "right_arm")
        wounds.mark_tended(self.char1, "left_leg")
        self.char1.attributes.reset_cache()
        stored = self.stored("wound_tended")
        self.assertIsInstance(stored, Set)
        self.assertNotIsInstance(stored, (set, frozenset))
        self.assertEqual(wounds.tended_of(self.char1), frozenset({"right_arm", "left_leg"}))

    def test_a_new_blow_leaves_the_mark(self):
        # p. 50: no First Aid again *until it has fully healed*.
        self.hurt(right_arm=1)
        wounds.mark_tended(self.char1, "right_arm")
        wounds.damage(self.char1, 1, "right_arm")
        self.assertEqual(wounds.damage_of(self.char1), {"right_arm": 2})
        self.assertEqual(wounds.tended_of(self.char1), frozenset({"right_arm"}))

    def test_natural_healing_takes_the_mark_of_a_location_made_whole(self):
        self.hurt(right_arm=1, left_arm=3)
        wounds.mark_tended(self.char1, "right_arm")
        wounds.mark_tended(self.char1, "left_arm")
        self.assertEqual(wounds.heal(self.char1, 1), 1)
        self.assertEqual(wounds.tended_of(self.char1), frozenset({"left_arm"}))
        self.assertEqual(wounds.heal(self.char1, 2), 2)
        self.assertFalse(self.char1.attributes.has("wound_tended"))

    def test_mend_takes_the_mark_of_a_location_made_whole(self):
        self.hurt(right_arm=2, left_leg=2)
        wounds.mark_tended(self.char1, "right_arm")
        wounds.mark_tended(self.char1, "left_leg")
        wounds.mend(self.char1, "right_arm", 1)
        self.assertEqual(wounds.tended_of(self.char1), frozenset({"right_arm", "left_leg"}))
        wounds.mend(self.char1, "right_arm", 1)
        self.assertEqual(wounds.tended_of(self.char1), frozenset({"left_leg"}))
        wounds.mend(self.char1, "left_leg", 2)
        self.assertFalse(self.char1.attributes.has("wound_tended"))

    def test_a_death_empties_the_marks_and_keeps_maimed(self):
        # WN9: the damage goes and *maimed* stays; the mark goes with the damage.
        self.hurt(right_arm=2, left_leg=9)
        self.char1.db.wound_states = {"left_leg": wounds.MAIMED}
        wounds.mark_tended(self.char1, "right_arm")
        wounds.restore_at_respawn(self.char1)
        self.assertFalse(self.char1.attributes.has("wound_tended"))
        self.assertEqual(wounds.tended_of(self.char1), frozenset())
        self.assertEqual(wounds.states_of(self.char1), {"left_leg": wounds.MAIMED})
