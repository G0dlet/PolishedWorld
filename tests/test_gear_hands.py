"""
Tests for what a hand holds (Gear decomposition GR-T7; locks GR2, GR3, GR4,
GR22; GR-T7's STOPP 0: `gear` imports `wounds`, a worn item is not held,
`hold` answers `(hands, reason)`, and each reason names what is in the way).

`db.hands` is written and read only in world/gear.py. Every way an item
leaves the body is tested against the read alone -- no hook in this slice
clears a hand -- and a useless arm against an entry that must stand.

The lines are typed here by hand, not read from the module's constants, so
a reworded reason fails by its words.
"""

from collections.abc import Mapping

from evennia import create_object
from evennia.commands.default.general import CmdDrop, CmdGive
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest

from commands.inventory_commands import CmdPut
from world import body, combat_styles, gear

CHARACTER = "typeclasses.characters.Character"
CONTAINER = "typeclasses.containers.Container"


class _Hands(EvenniaCommandTest):
    """char1 carries a stone knife, a club and a quarterstaff."""

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.knife = self._carried("stone_knife")
        self.club = self._carried("club")
        self.staff = self._carried("quarterstaff")

    def _carried(self, prototype_key):
        obj = spawn(prototype_key)[0]
        self.addCleanup(lambda: obj.pk and obj.delete())
        obj.location = self.char1
        return obj

    def _shield(self):
        """The target shield has no prototype until GR-T12: an object with its tag."""
        obj = create_object(
            "typeclasses.objects.Object", key="target shield", location=self.char1,
        )
        obj.tags.add("target_shield", category=gear.PROTOTYPE_TAG_CATEGORY)
        self.addCleanup(lambda: obj.pk and obj.delete())
        return obj

    def _maim(self, location):
        self.char1.db.wound_states = {location: "maimed"}

    def _stored(self):
        return dict(self.char1.attributes.get("hands") or {})


class TestTheNames(_Hands):
    """GR2: two hands, and they are the arms; not the weapon's category."""

    def test_two_hands_each_with_its_arm(self):
        self.assertEqual(gear.HANDS, ("right", "left"))
        self.assertEqual(dict(gear.ARM_OF), {"right": "right_arm", "left": "left_arm"})
        for arm in gear.ARM_OF.values():
            self.assertIn(arm, body.LOCATIONS)

    def test_the_hands_are_not_the_weapon_category(self):
        self.assertNotEqual(gear.HANDS, combat_styles.HANDS)
        self.assertEqual(combat_styles.HANDS, ("1H", "2H"))

    def test_nothing_held_is_two_empty_hands(self):
        self.assertEqual(gear.held(self.char1), {"right": None, "left": None})
        self.assertEqual(gear.hand_state(self.char1, "right"), gear.EMPTY)


class TestTakingAHand(_Hands):
    """GR4: the default hand, a named hand, the shield, and nothing swapped."""

    def test_the_first_item_takes_the_right_hand(self):
        self.assertEqual(gear.hold(self.char1, self.knife), (("right",), None))
        self.assertEqual(gear.held(self.char1), {"right": self.knife, "left": None})
        self.assertEqual(gear.hand_state(self.char1, "right"), gear.HOLDING)

    def test_the_second_takes_the_left(self):
        gear.hold(self.char1, self.knife)
        self.assertEqual(gear.hold(self.char1, self.club), (("left",), None))
        self.assertEqual(gear.held(self.char1), {"right": self.knife, "left": self.club})

    def test_a_named_hand_is_taken(self):
        self.assertEqual(gear.hold(self.char1, self.club, "left"), (("left",), None))
        self.assertEqual(gear.held(self.char1), {"right": None, "left": self.club})

    def test_a_full_named_hand_refuses_and_names_what_is_in_it(self):
        gear.hold(self.char1, self.knife)
        self.assertEqual(
            gear.hold(self.char1, self.club, "right"),
            ((), "Your right hand already holds your stone knife."),
        )
        self.assertEqual(gear.held(self.char1)["right"], self.knife)

    def test_no_free_hand_names_both(self):
        gear.hold(self.char1, self.knife)
        gear.hold(self.char1, self.club)
        spear = self._carried("spear")
        self.assertEqual(
            gear.hold(self.char1, spear),
            ((), "Your right hand holds your stone knife, and your left hand holds your club."),
        )

    def test_the_shield_takes_the_left_first(self):
        shield = self._shield()
        self.assertEqual(gear.hold(self.char1, shield), (("left",), None))
        self.assertEqual(gear.hold(self.char1, self.knife), (("right",), None))

    def test_the_shield_takes_the_right_when_the_left_is_full(self):
        gear.hold(self.char1, self.club, "left")
        self.assertEqual(gear.hold(self.char1, self._shield()), (("right",), None))

    def test_the_shield_may_be_named_to_the_right(self):
        self.assertEqual(gear.hold(self.char1, self._shield(), "right"), (("right",), None))

    def test_anything_carried_can_be_held(self):
        torch = create_object("typeclasses.objects.Object", key="torch", location=self.char1)
        self.addCleanup(torch.delete)
        self.assertIsNone(gear.weapon(torch))
        self.assertEqual(gear.hold(self.char1, torch), (("right",), None))

    def test_holding_it_again_is_refused(self):
        gear.hold(self.char1, self.knife)
        self.assertEqual(
            gear.hold(self.char1, self.knife, "left"),
            ((), "You are already holding your stone knife."),
        )
        self.assertEqual(self._stored(), {"right": self.knife})

    def test_an_item_not_carried_is_refused(self):
        self.knife.location = self.room1
        self.assertEqual(gear.hold(self.char1, self.knife), ((), "You aren't carrying that."))
        self.assertEqual(self._stored(), {})

    def test_an_unknown_hand_raises(self):
        with self.assertRaises(ValueError):
            gear.hold(self.char1, self.knife, "main")
        with self.assertRaises(ValueError):
            gear.hand_state(self.char1, "off")


class TestTwoHands(_Hands):
    """GR2, GR4: a two-handed row takes both hands and needs both free."""

    def test_a_staff_takes_both_hands_and_is_stored_under_both(self):
        self.assertEqual(gear.hold(self.char1, self.staff), (("right", "left"), None))
        self.assertEqual(gear.held(self.char1), {"right": self.staff, "left": self.staff})
        self.assertEqual(self._stored(), {"right": self.staff, "left": self.staff})

    def test_a_named_hand_does_not_halve_a_staff(self):
        self.assertEqual(gear.hold(self.char1, self.staff, "left"), (("right", "left"), None))

    def test_a_staff_with_one_hand_full_is_refused_and_says_what_is_in_the_way(self):
        gear.hold(self.char1, self.knife)
        self.assertEqual(
            gear.hold(self.char1, self.staff),
            ((), "Your quarterstaff needs both hands, and your right hand holds your stone knife."),
        )
        self.assertEqual(self._stored(), {"right": self.knife})

    def test_a_staff_with_a_useless_arm_is_refused(self):
        self._maim("left_arm")
        self.assertEqual(
            gear.hold(self.char1, self.staff),
            ((), "Your quarterstaff needs both hands, and your left arm is useless."),
        )

    def test_releasing_a_staff_frees_both(self):
        gear.hold(self.char1, self.staff)
        self.assertEqual(gear.release(self.char1, self.staff), ("right", "left"))
        self.assertEqual(gear.held(self.char1), {"right": None, "left": None})


class TestRelease(_Hands):
    def test_release_names_the_hand_it_left(self):
        gear.hold(self.char1, self.knife)
        gear.hold(self.char1, self.club)
        self.assertEqual(gear.release(self.char1, self.club), ("left",))
        self.assertEqual(gear.held(self.char1), {"right": self.knife, "left": None})

    def test_release_of_what_is_not_held_is_empty(self):
        self.assertEqual(gear.release(self.char1, self.knife), ())


class TestEveryWayOut(_Hands):
    """
    GR3: each way an item leaves the body empties the hand at the read, with
    no hook in this slice. The assignment is the red-before-green test.
    """

    def setUp(self):
        super().setUp()
        gear.hold(self.char1, self.knife)

    def _empty(self):
        self.assertEqual(gear.held(self.char1), {"right": None, "left": None})
        self.assertEqual(self._stored(), {})

    def test_an_assignment_to_location_empties_the_hand(self):
        self.knife.location = self.room1
        self._empty()

    def test_drop_empties_the_hand(self):
        self.call(CmdDrop(), "stone knife", caller=self.char1)
        self.assertEqual(self.knife.location, self.room1)
        self._empty()

    def test_give_empties_the_hand_and_the_receiver_holds_nothing(self):
        self.call(CmdGive(), "stone knife to Char2", caller=self.char1)
        self.assertEqual(self.knife.location, self.char2)
        self._empty()
        self.assertEqual(gear.held(self.char2), {"right": None, "left": None})

    def test_put_empties_the_hand(self):
        sack = create_object(CONTAINER, key="large sack", location=self.char1)
        self.addCleanup(sack.delete)
        sack.capacity = 10
        self.call(CmdPut(), "stone knife in large sack", caller=self.char1)
        self.assertEqual(self.knife.location, sack)
        self._empty()

    def test_a_delete_empties_the_hand(self):
        self.knife.delete()
        self._empty()

    def test_death_empties_the_hand(self):
        self.char1.at_character_death()
        self.assertNotEqual(self.knife.location, self.char1)
        self._empty()


class TestWornIsNotHeld(_Hands):
    """GR-T7's STOPP 0 (val 2, A): a worn item cannot be held, and is not."""

    def setUp(self):
        super().setUp()
        self.robe = self._carried("robe")

    def test_a_worn_item_is_refused(self):
        self.robe.wear(self.char1, True, quiet=True)
        self.assertEqual(gear.hold(self.char1, self.robe), ((), "You are wearing your robe."))
        self.assertEqual(self._stored(), {})

    def test_a_held_item_put_on_leaves_the_hand(self):
        self.assertEqual(gear.hold(self.char1, self.robe), (("right",), None))
        self.robe.wear(self.char1, True, quiet=True)
        self.assertEqual(gear.held(self.char1), {"right": None, "left": None})
        self.assertEqual(self._stored(), {})

    def test_taken_off_again_it_is_not_held_again(self):
        gear.hold(self.char1, self.robe)
        self.robe.wear(self.char1, True, quiet=True)
        gear.held(self.char1)
        self.robe.remove(self.char1, quiet=True)
        self.assertEqual(gear.held(self.char1), {"right": None, "left": None})


class TestAUselessArm(_Hands):
    """GR22: the hand reads empty, its entry stands, and a healed arm holds again."""

    def test_a_maimed_arm_reads_empty_and_keeps_its_entry(self):
        gear.hold(self.char1, self.knife)
        self._maim("right_arm")
        self.assertEqual(gear.held(self.char1), {"right": None, "left": None})
        self.assertEqual(gear.hand_state(self.char1, "right"), gear.USELESS)
        self.assertEqual(self._stored(), {"right": self.knife})

    def test_with_the_state_gone_the_hand_holds_again(self):
        gear.hold(self.char1, self.knife)
        self._maim("right_arm")
        gear.held(self.char1)
        self.char1.attributes.remove("wound_states")
        self.assertEqual(gear.held(self.char1), {"right": self.knife, "left": None})

    def test_each_state_makes_the_hand_useless(self):
        for state in ("disabled", "maimed", "severed"):
            self.char1.db.wound_states = {"left_arm": state}
            self.assertEqual(gear.hand_state(self.char1, "left"), gear.USELESS, state)

    def test_a_leg_does_not_touch_a_hand(self):
        gear.hold(self.char1, self.knife)
        self._maim("right_leg")
        self.assertEqual(gear.held(self.char1)["right"], self.knife)

    def test_a_named_useless_hand_is_refused(self):
        self._maim("right_arm")
        self.assertEqual(
            gear.hold(self.char1, self.knife, "right"),
            ((), "Your right arm is useless."),
        )
        self.assertEqual(self._stored(), {})

    def test_the_default_passes_a_useless_hand(self):
        self._maim("right_arm")
        self.assertEqual(gear.hold(self.char1, self.knife), (("left",), None))

    def test_no_usable_hand_free_names_both(self):
        gear.hold(self.char1, self.club, "left")
        self._maim("right_arm")
        self.assertEqual(
            gear.hold(self.char1, self.knife),
            ((), "Your right arm is useless, and your left hand holds your club."),
        )

    def test_what_a_useless_hand_held_moves_to_the_other(self):
        gear.hold(self.char1, self.knife)
        self._maim("right_arm")
        self.assertEqual(gear.hold(self.char1, self.knife), (("left",), None))
        self.assertEqual(self._stored(), {"left": self.knife})

    def test_an_item_that_left_is_cleared_even_under_a_useless_arm(self):
        gear.hold(self.char1, self.knife)
        self._maim("right_arm")
        self.knife.location = self.room1
        gear.held(self.char1)
        self.assertEqual(self._stored(), {})


class TestTheStoredValue(_Hands):
    """GR3: the one writer stores a Mapping, and the reader survives anything else."""

    def test_the_stored_value_is_a_mapping_of_hands(self):
        gear.hold(self.char1, self.knife)
        stored = self.char1.attributes.get("hands")
        self.assertIsInstance(stored, Mapping)
        self.assertEqual(set(stored), {"right"})

    def test_anything_else_stored_reads_as_nothing_held_and_is_replaced(self):
        self.char1.db.hands = ["right", self.knife]
        self.assertEqual(gear.held(self.char1), {"right": None, "left": None})
        self.assertIsInstance(self.char1.attributes.get("hands"), Mapping)
        self.assertEqual(gear.hold(self.char1, self.knife), (("right",), None))

    def test_a_key_that_is_not_a_hand_is_dropped(self):
        self.char1.db.hands = {"right": self.knife, "tail": self.club}
        self.assertEqual(gear.held(self.char1), {"right": self.knife, "left": None})
        self.assertEqual(self._stored(), {"right": self.knife})
