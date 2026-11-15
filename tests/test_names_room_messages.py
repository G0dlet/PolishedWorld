"""
The commands' room messages name the actor as each reader knows them.
Names, Task NM-T9 (docs/PolishedWorld_Combat_Decomposition.md, NM12; the
Names note's K4, UP10, UP11).

Every site in `commands/` that told the room who acted (§4: one by `.key`,
twelve by `get_display_name()` with no looker) sends `$You()` through
`msg_contents` with the actor as `from_obj`, so the room's line is resolved
per reader and starts with the capital `$You()` gives (NM-T9 lock 1B).

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
Each site is driven by its real command. Two readers stand in the room:
char3, a stranger, and char4, who has `recog`ed the actor as *mia of the
Ford* and the payee as *bob*. Each must read their own name for the actor --
the short description with its capital, or the label with its capital and
the rest as written -- and neither line may hold a key (`Char`, `Char2`).
A site restored to `get_display_name()` with no looker fails the
recogniser's assertion (NMM14); one restored to `.key` fails both.

The lower-case recog is deliberate: it is the one reader for whom `$You()`'s
capital and a plain format differ, so it tells the two apart.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_room_messages
"""

from unittest import mock

from django.test import override_settings
from evennia import create_object
from evennia.prototypes.spawner import spawn
from evennia.utils import ansi
from evennia.utils.test_resources import EvenniaCommandTest

from commands.consumption_commands import CmdDrink, CmdEat, CmdEmpty
from commands.currency_commands import CmdPay
from commands.foraging_commands import CmdForage, CmdRefill
from commands.hunting_commands import CmdHarvest
from commands.work_commands import TEMPLE_TASKS, CmdWork, _finish_task
from tests.names_fixture import describe, shown
from tests.test_craft_command import CraftFixtureMixin
from tests.test_currency import LedgerIsolationMixin
from tests.test_currency_commands import SecondSessionMixin
from tests.test_work_command import WorkTestBase, _marker_of

CHARACTER = "typeclasses.characters.Character"
LABEL = "mia of the Ford"      # char4's recog of the actor, char1
SEEN_BY_LABEL = "Mia of the Ford"
PAYEE_LABEL = "bob"            # char4's recog of char2


class _Readers:
    """
    char3 (a stranger) and char4 (a recogniser) in room1, their `msg` caught.

    Mixed in before the test base, so `setUp` runs after the base's own and
    char1 and char2 exist.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.char3 = create_object(CHARACTER, key="Char3", location=self.room1, home=self.room1)
        self.char4 = create_object(CHARACTER, key="Char4", location=self.room1, home=self.room1)
        describe(self.char1, self.char2, self.char3, self.char4)
        self.char4.recog.add(self.char1, LABEL)
        self.char4.recog.add(self.char2, PAYEE_LABEL)
        for reader in (self.char3, self.char4):
            reader.msg = mock.Mock()

    def lines(self, reader):
        out = []
        for call in reader.msg.call_args_list:
            text = call.kwargs.get("text", call.args[0] if call.args else None)
            text = text[0] if isinstance(text, tuple) else text
            if text:
                out.append(ansi.strip_ansi(str(text)))
        return out

    def assert_read(self, rest, stranger=None, recogniser=None):
        """
        Each reader has exactly one line ending in `rest`, which names the
        actor as they know them: `<Short description> <rest>` for the
        stranger, `<Label> <rest>` for the recogniser (or the full lines given).
        """
        stranger = stranger or f"{shown(self.char1)[:1].upper()}{shown(self.char1)[1:]} {rest}"
        recogniser = recogniser or f"{SEEN_BY_LABEL} {rest}"
        for reader, expected in ((self.char3, stranger), (self.char4, recogniser)):
            with self.subTest(reader=reader.key):
                read = [line for line in self.lines(reader) if line.endswith(rest)]
                self.assertEqual(read, [expected])
                self.assertNotIn("Char", read[0])


class TestConsumption(_Readers, EvenniaCommandTest):
    def test_eat(self):  # consumption_commands.py:62, by .key
        create_object("typeclasses.consumables.Food", key="testbread", location=self.char1)
        self.char1.traits.hunger.current = 50
        self.call(CmdEat(), "testbread", caller=self.char1)
        self.assert_read("eats testbread.")

    def test_drink_at_a_source(self):  # :193
        spawn("spring")[0].location = self.room1
        self.char1.traits.thirst.current = 10
        self.call(CmdDrink(), "", caller=self.char1)
        self.assert_read("kneels at the natural spring and drinks.")

    def test_empty(self):  # :240
        skin = spawn("waterskin")[0]
        skin.location = self.char1
        skin.charges = 4
        skin.water_kind = "fresh"
        self.call(CmdEmpty(), "skin", caller=self.char1)
        self.assert_read("upends the waterskin and lets it run out.")


class TestForaging(_Readers, EvenniaCommandTest):
    def test_forage(self):  # foraging_commands.py:171
        node = create_object("typeclasses.resources.ResourceNode", key="test tree",
                             location=self.room1)
        node.yield_prototype = "stick"
        node.max_yield = node.available = 6
        self.call(CmdForage(), "test tree", "You forage", caller=self.char1)
        self.assert_read("forages from the test tree.")

    def _skin_at_the_spring(self):
        spawn("spring")[0].location = self.room1
        skin = spawn("waterskin")[0]
        skin.location = self.char1
        skin.charges = 0
        return skin

    def test_a_vessel_splits(self):  # :240, a possessive
        skin = self._skin_at_the_spring()
        skin.condition = 0
        self.call(CmdRefill(), "skin", "You dip the waterskin in, but", caller=self.char1)
        self.assertFalse(skin.pk)  # receipt: the split branch ran
        rest = "waterskin falls apart at the water's edge."
        self.assert_read(rest, stranger=f"A weathered woman's {rest}",
                         recogniser=f"{SEEN_BY_LABEL}'s {rest}")

    def test_refill(self):  # :255
        self._skin_at_the_spring()
        self.call(CmdRefill(), "skin", "You fill the", caller=self.char1)
        self.assert_read("refills the waterskin at the water's edge.")


@override_settings(TREASURY_DBREF="")
class TestWork(_Readers, WorkTestBase):
    def setUp(self):
        super().setUp()
        override = override_settings(TREASURY_DBREF=self.treasury.dbref)
        override.enable()
        self.addCleanup(override.disable)

    def test_begin_and_done(self):  # work_commands.py:609, :468
        self.call(CmdWork(), "sweep", caller=self.char1)
        self.assert_read(TEMPLE_TASKS["sweep"]["begin_room"])
        _finish_task(self.char1, "sweep", _marker_of(self.char1))
        self.assert_read(TEMPLE_TASKS["sweep"]["done_room"])


class TestCraft(_Readers, CraftFixtureMixin, EvenniaCommandTest):
    def test_craft(self):  # crafting_commands.py:280
        self.give_fibres(self.char1)
        self.assertIsNotNone(self.start_craft())  # receipt: a craft started
        self.assert_read("begins to craft something.")


class TestHarvest(_Readers, EvenniaCommandTest):
    def _harvest(self, result, success):
        create_object("typeclasses.corpse.Corpse", key="testcarcass", location=self.room1)
        outcome = {"success": success, "result": result, "crit_score": 0}
        with mock.patch("commands.hunting_commands.skill_check", return_value=outcome):
            self.call(CmdHarvest(), "meat from testcarcass", caller=self.char1)

    def _read_starting(self, fragment):
        for reader, name in ((self.char3, "A weathered woman"), (self.char4, SEEN_BY_LABEL)):
            with self.subTest(reader=reader.key):
                read = [line for line in self.lines(reader) if fragment in line]
                self.assertEqual(len(read), 1, read)
                self.assertTrue(read[0].startswith(f"{name} {fragment}"), read[0])
                self.assertNotIn("Char", read[0])

    def test_a_success(self):  # hunting_commands.py:338
        self._harvest("success", True)
        self._read_starting("harvests meat from ")

    def test_a_botch(self):  # :347
        self._harvest("fumble", False)
        self._read_starting("botches the harvest, ruining part of ")


class TestPay(_Readers, SecondSessionMixin, LedgerIsolationMixin, EvenniaCommandTest):
    def test_two_characters_each_as_the_reader_knows_them(self):  # currency_commands.py:324
        self.char1.currency.add(1_000, source="admin_correction")
        self.call(CmdPay(), f"5 silver to {shown(self.char2)}", caller=self.char1)
        self.assert_read(
            "some coin.",
            stranger=f"A weathered woman hands {shown(self.char2)} some coin.",
            recogniser=f"{SEEN_BY_LABEL} hands {PAYEE_LABEL} some coin.",
        )
