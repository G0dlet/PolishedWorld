"""
Survival Loop S1.1: drinking at a water source (decomposition SL2).

`world/water.py` holds the room scan that `drink` and `refill` share. Bare
`drink`, or `drink <source>`, gives three draughts at once and never touches
a carried vessel; at full thirst it says so and writes nothing (lock C1). The
source is the seeded prototype, spawned, so its key and aliases are the ones
players meet.

    evennia test --settings settings.py tests.test_water
"""

from unittest import mock

from evennia import create_object
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.consumption_commands import CmdDrink
from commands.foraging_commands import CmdRefill
from tests.test_activity_log import ActivityLogMixin
from world import activity_log, activity_report, water

DRINK = "typeclasses.consumables.Drink"
NODE = "typeclasses.resources.ResourceNode"
OBJ = "typeclasses.objects.Object"
PUSH = "commands.consumption_commands.client_state.push"
SIP = "You kneel at the natural spring and drink from cupped hands."


def _spring(room):
    spring = spawn("spring")[0]
    spring.location = room
    return spring


class TestDraught(EvenniaTest):
    """The source's worth is three of a vessel's draughts (SL2, OQ-S3)."""

    def test_draught_is_a_drinks_default(self):
        cup = create_object(DRINK, key="testcup", location=self.char1)
        self.assertEqual(cup.restore_amount, water.DRAUGHT)

    def test_a_source_gives_forty_five(self):
        self.assertEqual(water.SOURCE_RESTORE, 45)


class TestSourceIn(EvenniaTest):
    """`source_in` finds a water source and nothing else."""

    def test_finds_the_spring(self):
        spring = _spring(self.room1)
        self.assertEqual(water.source_in(self.room1), spring)

    def test_a_node_that_is_not_water_is_not_a_source(self):
        create_object(NODE, key="testbush", location=self.room1)
        self.assertIsNone(water.source_in(self.room1))

    def test_a_plain_object_flagged_as_water_is_not_a_source(self):
        jug = create_object(OBJ, key="testjug", location=self.room1)
        jug.db.is_water_source = True
        self.assertIsNone(water.source_in(self.room1))

    def test_finds_the_spring_among_other_nodes(self):
        create_object(NODE, key="testbush", location=self.room1)
        spring = _spring(self.room1)
        self.assertEqual(water.source_in(self.room1), spring)

    def test_no_room_has_no_water(self):
        self.assertIsNone(water.source_in(None))


class TestDrinkAtSource(ActivityLogMixin, EvenniaCommandTest):
    """Bare `drink` and `drink <source>` beside the seeded spring."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.spring = _spring(self.room1)
        self.thirst = self.char1.traits.thirst

    def test_bare_drink_gives_three_draughts(self):
        self.thirst.current = 10
        self.call(CmdDrink(), "", SIP, caller=self.char1)
        self.assertEqual(self.thirst.current, 55)

    def test_bare_drink_clamps_at_max(self):
        self.thirst.current = self.thirst.max - 20
        self.call(CmdDrink(), "", SIP, caller=self.char1)
        self.assertEqual(self.thirst.current, self.thirst.max)

    def test_named_by_key_or_alias(self):
        for name in ("natural spring", "spring", "water"):
            with self.subTest(name=name):
                self.thirst.current = 10
                self.call(CmdDrink(), name, SIP, caller=self.char1)
                self.assertEqual(self.thirst.current, 55)

    def test_no_source_asks_what(self):
        self.spring.delete()
        self.thirst.current = 10
        self.call(CmdDrink(), "", "Drink from what?", caller=self.char1)
        self.assertEqual(self.thirst.current, 10)
        self.assertEqual(self.activity_records("consume"), [])

    def test_full_thirst_is_told_and_nothing_is_written(self):
        self.thirst.current = self.thirst.max
        with mock.patch(PUSH) as push:
            self.call(CmdDrink(), "", "You aren't thirsty.", caller=self.char1)
        push.assert_not_called()
        self.assertEqual(self.activity_records("consume"), [])
        self.assertEqual(self.thirst.current, self.thirst.max)

    def test_bare_drink_never_takes_a_carried_vessel(self):
        skin = spawn("waterskin")[0]
        skin.location = self.char1
        skin.charges = full = skin.max_charges  # crafted empty; fill it
        self.thirst.current = 10
        self.call(CmdDrink(), "", SIP, caller=self.char1)
        self.assertEqual(skin.charges, full)
        self.assertEqual(self.thirst.current, 55)

    def test_a_named_vessel_beside_the_spring_is_still_the_vessel(self):
        skin = spawn("waterskin")[0]
        skin.location = self.char1
        skin.charges = full = skin.max_charges  # crafted empty; fill it
        self.thirst.current = 10
        self.call(CmdDrink(), "skin", caller=self.char1)
        self.assertEqual(skin.charges, full - 1)
        self.assertEqual(self.thirst.current, 10 + skin.restore_amount)

    def test_a_node_that_is_not_water_is_refused_as_before(self):
        create_object(NODE, key="testbush", location=self.room1)
        self.call(CmdDrink(), "testbush", "You can't drink from", caller=self.char1)

    def test_the_line_names_the_source_and_has_no_charges(self):
        self.thirst.current = 80
        self.call(CmdDrink(), "", caller=self.char1)
        (entry,) = self.activity_records("consume")
        self.assertEqual(
            (entry["verb"], entry["item"], entry["gauge"], entry["delta"]),
            ("drink", "natural spring", "thirst", self.thirst.max - 80),
        )
        self.assertNotIn("charges_left", entry)

    def test_the_report_reads_the_line(self):
        self.thirst.current = 10
        self.call(CmdDrink(), "", caller=self.char1)
        with open(activity_log.path(), encoding="utf-8") as handle:
            agg = activity_report.aggregate(handle)
        self.assertEqual(agg["malformed"], 0)
        self.assertEqual(agg["kinds"], {"consume": 1})

    def test_pushes_survival(self):
        self.thirst.current = 10
        with mock.patch(PUSH) as push:
            self.call(CmdDrink(), "", caller=self.char1)
        push.assert_called_once_with(self.char1, "survival")

    def test_the_room_is_told(self):
        self.thirst.current = 10
        with mock.patch.object(self.char2, "msg") as heard:
            self.call(CmdDrink(), "", caller=self.char1)
        said = " ".join(str(call) for call in heard.call_args_list)
        self.assertIn("kneels at the natural spring and drinks.", said)


class TestRefillAsksTheHelper(EvenniaCommandTest):
    """`refill` finds its water through `world/water.py`."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        _spring(self.room1)
        self.skin = spawn("waterskin")[0]
        self.skin.location = self.char1
        self.skin.charges = 0

    def test_refills_at_the_spring(self):
        self.call(CmdRefill(), "skin", "You fill the", caller=self.char1)
        self.assertEqual(self.skin.charges, self.skin.max_charges)

    def test_no_water_when_the_helper_finds_none(self):
        with mock.patch("commands.foraging_commands.water.source_in", return_value=None):
            self.call(CmdRefill(), "skin", "There is no water source here", caller=self.char1)
        self.assertEqual(self.skin.charges, 0)
