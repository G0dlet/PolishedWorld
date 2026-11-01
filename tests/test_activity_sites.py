"""
Launch Minimum L2.2: the sites whose commands have no test module of their own.

L2.2a: repair. L2.2b: eat and drink. Each class drives the real command
and reads the line back through ActivityLogMixin; the site's own behaviour is
tested elsewhere (repair in test_encumbrance and test_improvement_engine).

    evennia test --settings settings.py tests.test_activity_sites
"""

from unittest import mock

from evennia import create_object
from evennia.utils.test_resources import EvenniaCommandTest

from commands.consumption_commands import CmdDrink, CmdEat
from commands.repair_commands import CmdRepair
from tests.test_activity_log import ActivityLogMixin

TOOL = "typeclasses.tools.Tool"  # a DurableObject: repair accepts it
OBJ = "typeclasses.objects.Object"
ROLL = "commands.repair_commands.skill_check"


class TestRepairIsLogged(ActivityLogMixin, EvenniaCommandTest):
    """
    Every resolved repair spends its materials, so every outcome writes one
    line with the condition before and after. The roll is pinned at the
    command's own `skill_check`; the knife needs no tool (repair_tool_tag "").
    """

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.knife = create_object(TOOL, key="logknife", location=self.char1)
        self.knife.db.condition = 50
        self.knife.db.repair_materials = ["logpatch"]
        self.knife.db.repair_tool_tag = ""
        rag = create_object(OBJ, key="lograg", location=self.char1)
        rag.tags.add("logpatch", category="crafting_material")
        self.rag = rag

    def repair(self, result, success):
        outcome = {"success": success, "result": result, "crit_score": 0}
        with mock.patch(ROLL, return_value=outcome):
            self.call(CmdRepair(), "logknife", caller=self.char1)
        self.assertIsNone(self.rag.pk)  # receipt: the materials were spent

    def test_a_success_logs_before_and_after(self):
        self.repair("success", True)
        (entry,) = self.activity_records("repair")
        self.assertEqual(
            (entry["actor"], entry["item"], entry["consumed"], entry["tier"],
             entry["before"], entry["after"]),
            ([self.char1.dbref, self.char1.key], "logknife", ["lograg"], "success",
             50, self.knife.db.condition),
        )
        self.assertGreater(entry["after"], entry["before"])

    def test_a_plain_failure_still_logs_the_materials_spent(self):
        self.repair("failure", False)
        (entry,) = self.activity_records("repair")
        self.assertEqual(
            (entry["consumed"], entry["before"], entry["after"]),
            (["lograg"], 50, 50),
        )


class TestConsumeIsLogged(ActivityLogMixin, EvenniaCommandTest):
    """
    Eat and drink each write one consume line; `verb` tells them apart
    (`kind` is reserved by record()). `delta` is what the gauge actually
    gained, after the trait's clamp: the near-full case pins that it is not
    simply the item's restore_amount.
    """

    character_typeclass = "typeclasses.characters.Character"

    def test_eating_logs_the_hunger_gained(self):
        food = create_object("typeclasses.consumables.Food", key="logbread", location=self.char1)
        self.char1.traits.hunger.current = 50
        self.call(CmdEat(), "logbread", caller=self.char1)
        self.assertIsNone(food.pk)  # receipt: eaten
        (entry,) = self.activity_records("consume")
        self.assertEqual(
            (entry["verb"], entry["item"], entry["gauge"], entry["delta"]),
            ("eat", "logbread", "hunger", 20),  # Food.restore_amount default
        )
        self.assertEqual(self.char1.traits.hunger.current, 70)

    def test_eating_near_full_logs_the_clamped_gain(self):
        create_object("typeclasses.consumables.Food", key="logbread", location=self.char1)
        top = self.char1.traits.hunger.max
        self.char1.traits.hunger.current = top - 5
        self.call(CmdEat(), "logbread", caller=self.char1)
        (entry,) = self.activity_records("consume")
        self.assertEqual(entry["delta"], 5)

    def test_drinking_logs_the_thirst_gained_and_the_charges_left(self):
        skin = create_object("typeclasses.consumables.Drink", key="logskin", location=self.char1)
        self.char1.traits.thirst.current = 50
        self.call(CmdDrink(), "logskin", caller=self.char1)
        (entry,) = self.activity_records("consume")
        self.assertEqual(
            (entry["verb"], entry["item"], entry["gauge"], entry["delta"],
             entry["charges_left"]),
            ("drink", "logskin", "thirst", 15, skin.charges),
        )
        self.assertEqual(skin.charges, 4)

    def test_an_empty_container_writes_nothing(self):
        skin = create_object("typeclasses.consumables.Drink", key="logskin", location=self.char1)
        skin.charges = 0
        self.call(CmdDrink(), "logskin", "logskin is empty.", caller=self.char1)
        self.assertEqual(self.activity_records(), [])
