"""
Tests for `wield` and `unwield` (Gear decomposition GR-T8; locks GR4, GR5;
GR-T8's STOPP 0: `hold` is `wield`'s alias, a collapsed or unconscious body
is refused first, and one line goes to the whole room through `$You()`).

The commands hold no rule of the hands: a refusal is `gear.hold`'s reason,
and these tests read it through the command. The red-before-green test is
the staff with a knife in hand, against a command that swaps: the knife is
put away.

The lines are typed here by hand. The fixture characters have their
short descriptions (tests/names_fixture.py) and no sex, so a stranger reads
*their*.
"""

import time
from unittest import mock

from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest

from commands.default_cmdsets import CharacterCmdSet
from commands.gear_commands import CmdUnwield, CmdWield
from tests.names_fixture import describe, shown
from typeclasses.characters import Character
from world import fatigue, gear, wounds

CHARACTER = "typeclasses.characters.Character"


class _Commands(EvenniaCommandTest):
    """char1 carries a stone knife, a club and a quarterstaff; char2 watches."""

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        describe(self.char1, self.char2)
        self.knife = self._carried("stone_knife")
        self.club = self._carried("club")
        self.staff = self._carried("quarterstaff")

    def _carried(self, prototype_key):
        obj = spawn(prototype_key)[0]
        self.addCleanup(lambda: obj.pk and obj.delete())
        obj.location = self.char1
        return obj

    def wield(self, args, expected=None, **kwargs):
        return self.call(CmdWield(), args, expected, caller=self.char1, **kwargs)

    def unwield(self, args, expected=None, **kwargs):
        return self.call(CmdUnwield(), args, expected, caller=self.char1, **kwargs)


class TestWield(_Commands):
    def test_wield_takes_the_right_hand_and_says_so(self):
        self.wield("stone knife", "You take the stone knife in your right hand.")
        self.assertEqual(gear.held(self.char1)["right"], self.knife)

    def test_wield_club_left(self):
        self.wield("club left", "You take the club in your left hand.")
        self.assertEqual(gear.held(self.char1), {"right": None, "left": self.club})

    def test_the_hand_word_is_read_in_any_case(self):
        self.wield("club LEFT", "You take the club in your left hand.")

    def test_a_staff_says_both_hands(self):
        self.wield("quarterstaff", "You take the quarterstaff in both hands.")
        self.assertEqual(gear.held(self.char1), {"right": self.staff, "left": self.staff})

    def test_a_staff_with_a_knife_in_hand_is_refused_and_nothing_is_swapped(self):
        self.wield("stone knife")
        self.wield(
            "quarterstaff",
            "Your quarterstaff needs both hands, and your right hand holds your stone knife.",
        )
        self.assertEqual(gear.held(self.char1), {"right": self.knife, "left": None})

    def test_a_full_named_hand_is_refused_with_gears_reason(self):
        self.wield("stone knife")
        self.wield("club right", "Your right hand already holds your stone knife.")

    def test_a_useless_arm_is_refused_with_gears_reason(self):
        self.char1.db.wound_states = {"left_arm": "maimed"}
        self.wield("club left", "Your left arm is useless.")

    def test_wield_with_nothing_named_asks(self):
        self.wield("", "Wield what?")

    def test_something_not_carried_is_not_found(self):
        self.knife.location = self.room1
        out = self.wield("stone knife")
        self.assertIn("Could not find", out)
        self.assertEqual(gear.held(self.char1), {"right": None, "left": None})


class TestParse(_Commands):
    def _parsed(self, args):
        cmd = CmdWield()
        cmd.args = args
        cmd.parse()
        return cmd.query, cmd.hand

    def test_a_last_word_that_names_a_hand_is_the_hand(self):
        self.assertEqual(self._parsed(" stone knife left"), ("stone knife", "left"))

    def test_a_lone_hand_word_is_an_item(self):
        self.assertEqual(self._parsed(" left"), ("left", None))

    def test_no_hand_word_no_hand(self):
        self.assertEqual(self._parsed(" stone knife"), ("stone knife", None))


class TestHoldIsWield(_Commands):
    def test_hold_reaches_the_same_command(self):
        self.call(CmdWield(), "club", "You take the club in your right hand.",
                  caller=self.char1, cmdstring="hold")

    def test_the_cmdset_answers_to_all_three(self):
        commands = {}
        for cmd in CharacterCmdSet().commands:
            for name in [cmd.key, *cmd.aliases]:
                commands[name] = type(cmd)
        self.assertIn("inventory", commands)   # receipt: the cmdset was built
        self.assertIs(commands["wield"], CmdWield)
        self.assertIs(commands["hold"], CmdWield)
        self.assertIs(commands["unwield"], CmdUnwield)

    def test_every_character_may_use_both(self):
        # `.call()` runs no lock: the lock is read through Command.access.
        for cmd in (CmdWield(), CmdUnwield()):
            self.assertTrue(cmd.access(self.char1, "cmd"))
            self.assertTrue(cmd.access(self.char2, "cmd"))


class TestTheRoomsLine(_Commands):
    """GR5, TR3: the holder by the reader's name, through `$You()`."""

    def test_a_stranger_reads_the_holder_as_they_know_them(self):
        self.wield(
            "stone knife",
            f"{shown(self.char1).capitalize()} takes the stone knife in their right hand.",
            receiver=self.char2,
        )

    def test_a_stranger_reads_both_hands(self):
        self.wield(
            "quarterstaff",
            f"{shown(self.char1).capitalize()} takes the quarterstaff in both hands.",
            receiver=self.char2,
        )

    def test_a_stranger_reads_the_unwield(self):
        self.wield("club")
        self.unwield(
            "club",
            f"{shown(self.char1).capitalize()} puts away the club.",
            receiver=self.char2,
        )

    def test_a_refusal_is_the_holders_alone(self):
        self.wield("stone knife")
        self.wield("club right", "", receiver=self.char2)


class TestUnwield(_Commands):
    def test_unwield_puts_it_away_and_it_is_still_carried(self):
        self.wield("stone knife")
        self.unwield("stone knife", "You put away the stone knife.")
        self.assertEqual(gear.held(self.char1), {"right": None, "left": None})
        self.assertEqual(self.knife.location, self.char1)

    def test_unwield_of_a_staff_frees_both(self):
        self.wield("quarterstaff")
        self.unwield("quarterstaff", "You put away the quarterstaff.")
        self.assertEqual(gear.held(self.char1), {"right": None, "left": None})

    def test_unwield_of_something_not_held(self):
        self.unwield("club", "You aren't holding that.")

    def test_unwield_with_nothing_named_asks(self):
        self.unwield("", "Unwield what?")

    def test_unwield_lets_go_of_the_item_named_not_its_twin(self):
        twin = self._carried("stone_knife")
        found = self.char1.search("stone knife", candidates=self.char1.contents, quiet=True)
        self.assertEqual(set(found), {self.knife, twin})
        first, second = found
        gear.hold(self.char1, first)
        self.unwield("2-stone knife", "You aren't holding that.")
        self.assertEqual(gear.held(self.char1)["right"], first)


class TestTheBodyFirst(_Commands):
    """GR-T8's STOPP 0 (val 2, A): the body's refusal comes before the hands'."""

    def test_a_collapsed_body_cannot_wield(self):
        self.char1.db.collapsed = True
        with mock.patch.object(Character, "arm_collapse"):
            self.wield("stone knife", fatigue.CANNOT_HANDLE)
        self.assertEqual(gear.held(self.char1), {"right": None, "left": None})

    def test_a_collapsed_body_cannot_unwield(self):
        self.wield("stone knife")
        self.char1.db.collapsed = True
        with mock.patch.object(Character, "arm_collapse"):
            self.unwield("stone knife", fatigue.CANNOT_HANDLE)
        self.assertEqual(gear.held(self.char1)["right"], self.knife)

    def test_an_unconscious_body_cannot_wield(self):
        self.char1.db.wound_unconscious = {"location": "head", "until": time.time() + 600}
        self.wield("stone knife", wounds.OUT_COLD)
        self.assertEqual(gear.held(self.char1), {"right": None, "left": None})
