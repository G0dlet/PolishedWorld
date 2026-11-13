"""
Survival Loop S1.1: drinking at a water source (decomposition SL2).
S1.2: the kind of water on sources and in vessels, and `empty` (SL3).
S1.3: the vessel wears on `condition` and is not mended (SL4, SL5).

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

from commands.consumption_commands import CmdDrink, CmdEmpty
from commands.foraging_commands import CmdRefill
from commands.repair_commands import CmdRepair
from commands.world_commands import CmdRoomLook
from typeclasses.consumables import Drink
from typeclasses.durable import DurableObject
from world.crafting_quality import POOR_FLOOR, POOR, SERVICEABLE, SHODDY, SUPERIOR
from world.recipes import WaterskinRecipe, _WATERSKIN_STATS_BY_BAND
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


class TestKinds(EvenniaCommandTest):
    """Water has a kind; only fresh is in the world (SL3, S1.2)."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.spring = _spring(self.room1)
        self.skin = spawn("waterskin")[0]
        self.skin.location = self.char1
        # S1.2b: a vessel is not drunk at full thirst, so the draught tests
        # start thirsty (unlowered, "keeps the kind" passed on a refusal).
        self.char1.traits.thirst.current = 10

    def _fill(self):
        self.call(CmdRefill(), "skin", "You fill the", caller=self.char1)

    def test_the_spring_is_fresh_without_a_stored_kind(self):
        self.assertEqual(self.spring.water_kind, "fresh")
        self.assertFalse(self.spring.attributes.has("water_kind"))

    def test_a_fill_stamps_the_kind(self):
        self._fill()
        self.assertEqual(self.skin.attributes.get("water_kind"), "fresh")
        self.assertEqual(self.skin.held_kind(), "fresh")

    def test_an_empty_vessel_holds_no_kind(self):
        self.assertIsNone(self.skin.held_kind())

    def test_an_empty_vessel_with_a_stale_kind_holds_none_and_fills(self):
        # A kind left on an empty vessel (an @set, or state from before
        # pour_out) is not what it holds: the spring fills it (SL-M7).
        self.skin.charges = 0
        self.skin.water_kind = "brine"
        self.assertIsNone(self.skin.held_kind())
        self._fill()
        self.assertEqual(self.skin.water_kind, "fresh")

    def test_a_vessel_filled_before_kinds_reads_fresh_and_refills(self):
        self.skin.charges = 3
        self.assertFalse(self.skin.attributes.has("water_kind"))
        self.assertEqual(self.skin.held_kind(), "fresh")
        self._fill()
        self.assertEqual(self.skin.charges, self.skin.max_charges)

    def test_another_kind_is_refused_and_untouched(self):
        self.skin.charges = 2
        self.skin.water_kind = "brine"
        self.call(
            CmdRefill(), "skin", "The waterskin holds brine. Empty it first.",
            caller=self.char1,
        )
        self.assertEqual((self.skin.charges, self.skin.water_kind), (2, "brine"))

    def test_another_kind_is_refused_before_the_split(self):
        self.skin.charges = 2
        self.skin.water_kind = "brine"
        self.skin.condition = 0  # broken: the next dip would split it (S1.3)
        self.call(CmdRefill(), "skin", "The waterskin holds brine.", caller=self.char1)
        self.assertTrue(self.skin.pk)

    def test_after_empty_the_spring_fills_it(self):
        self.skin.charges = 2
        self.skin.water_kind = "brine"
        self.call(CmdEmpty(), "skin", "You upend the waterskin", caller=self.char1)
        self._fill()
        self.assertEqual(self.skin.water_kind, "fresh")
        self.assertEqual(self.skin.charges, self.skin.max_charges)

    def test_the_last_draught_clears_the_kind(self):
        self.skin.charges = 1
        self.skin.water_kind = "fresh"
        self.call(CmdDrink(), "skin", caller=self.char1)
        self.assertEqual(self.skin.charges, 0)
        self.assertIsNone(self.skin.water_kind)

    def test_a_draught_that_leaves_some_keeps_the_kind(self):
        self.skin.charges = 2
        self.skin.water_kind = "fresh"
        self.call(CmdDrink(), "skin", caller=self.char1)
        self.assertEqual(self.skin.water_kind, "fresh")

    def test_the_words_for_a_kind(self):
        self.assertEqual(water.kind_word("fresh"), "fresh water")
        self.assertEqual(water.kind_word("brine"), "brine")


class TestEmpty(EvenniaCommandTest):
    """`empty <vessel>` pours it out: no wear, the room told (S1.2 lock D)."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.skin = spawn("waterskin")[0]
        self.skin.location = self.char1
        self.skin.charges = 4
        self.skin.water_kind = "fresh"

    def test_empties_and_clears_the_kind(self):
        self.call(CmdEmpty(), "skin", "You upend the waterskin and let it run out.",
                  caller=self.char1)
        self.assertEqual(self.skin.charges, 0)
        self.assertIsNone(self.skin.water_kind)

    def test_wears_nothing(self):
        self.skin.condition = 40
        self.call(CmdEmpty(), "skin", caller=self.char1)
        self.assertEqual(self.skin.condition, 40)

    def test_an_empty_vessel_says_so(self):
        self.skin.charges = 0
        self.call(CmdEmpty(), "skin", "The waterskin is already empty.", caller=self.char1)

    def test_a_non_vessel_is_refused(self):
        rock = create_object(OBJ, key="testrock", location=self.char1)
        self.call(CmdEmpty(), "testrock", "You can't empty the testrock.", caller=self.char1)
        self.assertTrue(rock.pk)

    def test_a_vessel_that_cannot_be_refilled_is_refused(self):
        self.skin.refillable = False
        self.call(CmdEmpty(), "skin", "You can't empty the waterskin.", caller=self.char1)
        self.assertEqual(self.skin.charges, 4)

    def test_only_a_carried_vessel(self):
        self.skin.location = self.room1
        self.call(CmdEmpty(), "skin", "Could not find 'skin'.", caller=self.char1)
        self.assertEqual(self.skin.charges, 4)

    def test_no_argument_asks_what(self):
        self.call(CmdEmpty(), "", "Empty what?", caller=self.char1)

    def test_the_room_is_told(self):
        with mock.patch.object(self.char2, "msg") as heard:
            self.call(CmdEmpty(), "skin", caller=self.char1)
        said = " ".join(str(call) for call in heard.call_args_list)
        self.assertIn("upends the waterskin and lets it run out.", said)

    def test_writes_no_activity_line_and_pushes_nothing(self):
        with mock.patch("world.activity_log.record") as record, \
                mock.patch("world.client_state.push") as push:
            self.call(CmdEmpty(), "skin", caller=self.char1)
        record.assert_not_called()
        push.assert_not_called()


class TestVesselWear(EvenniaCommandTest):
    """S1.3: the vessel wears on `condition` (SL4) and is not mended (SL5)."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        _spring(self.room1)
        self.skin = spawn("waterskin")[0]
        self.skin.location = self.char1

    def _dip(self):
        self.skin.charges = 0  # drunk dry between fills
        return self.call(CmdRefill(), "skin", caller=self.char1)

    def test_band_starts_are_todays_refill_counts(self):
        counts = {
            band: start // Drink.REFILL_WEAR
            for band, (_charges, start) in _WATERSKIN_STATS_BY_BAND.items()
        }
        self.assertEqual(
            counts, {SUPERIOR: 12, SERVICEABLE: 10, POOR: 6, SHODDY: 3}
        )

    def test_the_recipe_writes_the_start_condition(self):
        for quality, start in ((105, 96), (100, 80), (POOR_FLOOR, 48), (0, 24)):
            with self.subTest(quality=quality):
                skin = spawn("waterskin")[0]
                skin.db.quality = quality
                WaterskinRecipe._finalize_item(mock.Mock(), skin, None)
                self.assertEqual(skin.condition, start)
                self.assertFalse(skin.attributes.has("durability"))

    def test_a_serviceable_skin_fills_ten_times_and_splits_on_the_eleventh(self):
        self.skin.condition = 80
        for fill in range(10):
            with self.subTest(fill=fill):
                out = self._dip()
                self.assertTrue(out.startswith("You fill the"), out)
        self.assertEqual(self.skin.condition, 0)
        self.assertTrue(self.skin.pk)  # the last fill is still drunk
        out = self._dip()
        self.assertTrue(out.startswith("You dip the waterskin in, but"), out)
        self.assertFalse(self.skin.pk)

    def test_a_full_skin_is_not_worn(self):
        self.skin.charges = self.skin.max_charges
        self.call(CmdRefill(), "skin", "The waterskin is already full.", caller=self.char1)
        self.assertEqual(self.skin.condition, 100)

    def test_drinking_wears_nothing(self):
        self.skin.charges = 3
        self.char1.traits.thirst.current = 10
        self.call(CmdDrink(), "skin", caller=self.char1)
        self.assertEqual(self.skin.condition, 100)

    def test_a_stale_durability_is_not_read(self):
        self.skin.db.durability = 0
        out = self._dip()
        self.assertTrue(out.startswith("You fill the"), out)
        self.assertEqual(self.skin.condition, 100 - Drink.REFILL_WEAR)

    def test_look_shows_the_condition(self):
        self.skin.condition = 72
        out = self.call(CmdRoomLook(), "skin", caller=self.char1)
        self.assertIn("Condition: 72%", out)

    def test_repair_refuses_and_keeps_the_materials(self):
        self.skin.condition = 40
        cloth, twine = spawn("cloth", "twine")
        cloth.location = twine.location = self.char1
        self.call(CmdRepair(), "skin", "You can't mend waterskin.", caller=self.char1)
        self.assertTrue(cloth.pk and twine.pk)
        self.assertEqual(self.skin.condition, 40)
        self.assertTrue(self.char1.cooldowns.ready("repair"))

    def test_other_durables_stay_mendable(self):
        self.assertTrue(DurableObject.mendable)
        self.assertFalse(Drink.mendable)
