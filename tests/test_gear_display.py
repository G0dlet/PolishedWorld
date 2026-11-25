"""
Tests for who sees the hands (Gear decomposition GR-T9; lock GR5; GR22;
GR-T9's STOPP 0: `inventory` builds its own three tables, a two-handed item
with a useless arm is not held, and the two lines' words).

    TestInventory   a held item under *carrying* as well as *holding* (the
                    red-before-green test, against the contrib's tables); a
                    useless hand not said; the ENC line or its count lost
    TestLook        the line for the owner only; a name not the looker's; a
                    statue that shows what its hands held

The fixture's char1 has a session (`setup_session`), so it is a living body;
char2 has none and is a statue (tests/test_currency_commands.py explains).
The lines are typed here by hand.
"""

from unittest import mock

from evennia.prototypes.spawner import spawn
from evennia.utils.ansi import strip_ansi
from evennia.utils.test_resources import EvenniaCommandTest

from commands.inventory_commands import CmdInventory
from tests.names_fixture import describe, shown
from world import gear

CHARACTER = "typeclasses.characters.Character"
HEADERS = ("You are carrying:", "You are holding:", "You are wearing:")


class _Display(EvenniaCommandTest):
    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        describe(self.char1, self.char2)
        self.knife = self._carried("stone_knife")
        self.club = self._carried("club")
        self.staff = self._carried("quarterstaff")

    def _carried(self, prototype_key, who=None):
        obj = spawn(prototype_key)[0]
        self.addCleanup(lambda: obj.pk and obj.delete())
        obj.location = who or self.char1
        return obj

    def inventory(self):
        return self.call(CmdInventory(), "", caller=self.char1)

    def sections(self, out):
        """The lines under each header, up to the next; the ENC line apart."""
        lines = [line.rstrip() for line in out.split("\n")]
        found, current = {}, None
        for line in lines:
            if line in HEADERS:
                current = line
                found[current] = []
            elif line.startswith("Carrying "):
                current = None
            elif current is not None and line.strip() and set(line.strip()) != {"-"}:
                found[current].append(" ".join(line.split()))
        return found


class TestInventory(_Display):
    def test_a_held_item_is_under_holding_and_not_carrying(self):
        gear.hold(self.char1, self.knife)
        found = self.sections(self.inventory())
        self.assertFalse(any("stone knife" in row for row in found["You are carrying:"]))
        self.assertEqual(list(found), list(HEADERS))
        self.assertIn("a stone knife right hand", found["You are holding:"])
        self.assertTrue(any(row.startswith("a club") for row in found["You are carrying:"]))

    def test_two_hands(self):
        gear.hold(self.char1, self.knife)
        gear.hold(self.char1, self.club)
        rows = self.sections(self.inventory())["You are holding:"]
        self.assertEqual(rows, ["a stone knife right hand", "a club left hand"])

    def test_a_staff_is_one_row_in_both_hands(self):
        gear.hold(self.char1, self.staff)
        rows = self.sections(self.inventory())["You are holding:"]
        self.assertEqual(rows, ["a quarterstaff both hands"])

    def test_nothing_held_says_nothing(self):
        self.assertEqual(self.sections(self.inventory())["You are holding:"], ["Nothing."])

    def test_a_useless_arm_is_said_under_holding(self):
        gear.hold(self.char1, self.club, "left")
        self.char1.db.wound_states = {"right_arm": "maimed"}
        rows = self.sections(self.inventory())["You are holding:"]
        self.assertEqual(rows, ["a club left hand", "Your right arm is useless."])

    def test_what_a_useless_hand_held_is_carried(self):
        gear.hold(self.char1, self.knife)
        self.char1.db.wound_states = {"right_arm": "maimed"}
        found = self.sections(self.inventory())
        self.assertEqual(found["You are holding:"], ["Nothing.", "Your right arm is useless."])
        self.assertTrue(any(row.startswith("a stone knife") for row in found["You are carrying:"]))

    def test_a_held_item_still_counts_towards_enc(self):
        before = [ln for ln in self.inventory().split("\n") if ln.startswith("Carrying ")]
        gear.hold(self.char1, self.staff)
        after = [ln for ln in self.inventory().split("\n") if ln.startswith("Carrying ")]
        self.assertEqual(len(before), 1)
        self.assertEqual(after, before)

    def test_an_empty_inventory_still_ends_in_the_enc_line(self):
        for obj in (self.knife, self.club, self.staff):
            obj.delete()
        out = self.inventory()
        self.assertIn("You are not carrying or wearing anything.", out)
        self.assertTrue(out.rstrip().endswith("Carrying 0/20 ENC"))

    def test_an_empty_inventory_still_says_a_useless_arm(self):
        for obj in (self.knife, self.club, self.staff):
            obj.delete()
        self.char1.db.wound_states = {"left_arm": "disabled"}
        out = self.inventory()
        self.assertIn("You are not carrying or wearing anything.", out)
        self.assertIn("Your left arm is useless.", out)

    def test_the_message_keeps_the_contribs_type(self):
        gear.hold(self.char1, self.knife)
        with mock.patch.object(self.char1, "msg") as msg:
            cmd = CmdInventory()
            cmd.caller, cmd.account, cmd.session = self.char1, self.account, self.session
            cmd.func()
        typed = [c for c in msg.call_args_list
                 if isinstance(c.kwargs.get("text"), tuple)]
        self.assertEqual(len(typed), 1)
        self.assertEqual(typed[0].kwargs["text"][1], {"type": "inventory"})


class TestLook(_Display):
    def look(self, target, looker):
        return strip_ansi(target.return_appearance(looker))

    def test_a_stranger_reads_one_item(self):
        gear.hold(self.char1, self.knife)
        self.assertIn(
            f"{shown(self.char1).capitalize()} is holding stone knife in the right hand.",
            self.look(self.char1, self.char2),
        )

    def test_a_stranger_reads_two(self):
        gear.hold(self.char1, self.knife)
        gear.hold(self.char1, self.club)
        self.assertIn(
            f"{shown(self.char1).capitalize()} is holding stone knife in the right hand"
            " and club in the left hand.",
            self.look(self.char1, self.char2),
        )

    def test_a_stranger_reads_both_hands(self):
        gear.hold(self.char1, self.staff)
        self.assertIn(
            f"{shown(self.char1).capitalize()} is holding quarterstaff in both hands.",
            self.look(self.char1, self.char2),
        )

    def test_the_line_comes_after_the_clothes(self):
        gear.hold(self.char1, self.knife)
        text = self.look(self.char1, self.char2)
        self.assertLess(text.index("is wearing"), text.index("is holding"))

    def test_nothing_held_no_line(self):
        self.assertNotIn("is holding", self.look(self.char1, self.char2))

    def test_a_useless_hand_shows_nothing(self):
        gear.hold(self.char1, self.knife)
        self.char1.db.wound_states = {"right_arm": "maimed"}
        self.assertNotIn("is holding", self.look(self.char1, self.char2))

    def test_the_owner_reads_it_too(self):
        gear.hold(self.char1, self.knife)
        self.assertIn("is holding stone knife in the right hand.", self.look(self.char1, self.char1))

    def test_a_statue_shows_nothing_held(self):
        knife = self._carried("stone_knife", who=self.char2)
        gear.hold(self.char2, knife)
        self.assertFalse(self.char2.has_account)   # receipt: char2 is a statue
        text = self.look(self.char2, self.char1)
        self.assertIn("stone statue", text)
        self.assertNotIn("holding", text)
