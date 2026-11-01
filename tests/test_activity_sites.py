"""
Launch Minimum L2.2: the sites whose commands have no test module of their own.

L2.2a: repair. L2.2b adds eat and drink. Each class drives the real command
and reads the line back through ActivityLogMixin; the site's own behaviour is
tested elsewhere (repair in test_encumbrance and test_improvement_engine).

    evennia test --settings settings.py tests.test_activity_sites
"""

from unittest import mock

from evennia import create_object
from evennia.utils.test_resources import EvenniaCommandTest

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
