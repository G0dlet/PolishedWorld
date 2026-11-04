"""
`ingame_reports` (BACKLOG, locked 2026-11-04): `commands/report_commands.py`,
`Account.at_post_login`, `world/report_export.py`.

What each class pressures:

- TestCmdsetShape: the four commands, the cmdset's priority above EvMenu's and
  its Union mergetype, and help text that survives subclassing (the
  subclasses carry no docstring; Evennia's command metaclass copies the
  parent's, `command.py:99-102` -- this pins that it still does).
- TestCmdsetOnLogin: the cmdset reaches the account through a real login
  (EvenniaTest's setUp logs in through the session handler, which runs
  `at_post_login`), exactly once, persistently, and a failure there never
  costs the login.
- TestReachableEverywhere: `bug` files from inside character creation -- the
  EvMenu's Replace cmdset at priority 1 removes anything below it, which is
  where upstream's install puts it -- while the menu keeps answering; `idea`
  files OOC; normal play keeps `look` (a Replace at priority 2 would not).
- TestReadLocks: who can read a filed report. One reader per mutation: the
  Admin staff account (upstream's Developer bug lock hides bugs from it), a
  Builder (upstream's idea lock lets it read ideas), a plain player (any
  `all()` lock). Read from the staff menu's own node and from `Msg.access`;
  `manage` is checked with `Command.access`, never `.call()`, which runs no
  locks (lesson: permission tests through `.call()` pass vacuously).
- TestExport: the export's type list is the commands' hub types; it reads
  hubs without creating them; each line carries type, sender, target (never
  the hub), status (never the creation tag) and text, oldest first; a
  duplicate hub cannot hide a report.
"""

import json
import os
import tempfile
from types import SimpleNamespace
from unittest import mock

from evennia.comms.models import Msg
from evennia.contrib.base_systems.ingame_reports import menu as reports_menu
from evennia.contrib.base_systems.ingame_reports import reports as upstream
from evennia.scripts.models import ScriptDB
from evennia.utils import create
from evennia.utils.ansi import strip_ansi
from evennia.utils.evmenu import EvMenuCmdSet
from evennia.utils.test_resources import EvenniaTest

from commands import report_commands
from commands.report_commands import (
    CmdBug,
    CmdIdea,
    CmdReport,
    ReportsCmdSet,
    STAFF_READ_LOCK,
    ensure_reports_cmdset,
)
from world import alpha_contract, report_export


class _Fixture(EvenniaTest):
    """char1 puppeted by account (Developer); capture what char1 and account hear."""

    def setUp(self):
        super().setUp()
        self.out = []
        for target in (self.char1, self.account):
            patcher = mock.patch.object(target, "msg", side_effect=self._capture)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _capture(self, text=None, *args, **kwargs):
        if isinstance(text, (tuple, list)):
            text = text[0]
        self.out.append(strip_ansi(str(text)))

    def send(self, line, by=None):
        """Run one line through the real cmdhandler; return what was printed."""
        self.out.clear()
        (by or self.char1).execute_cmd(line, session=self.session)
        return "\n".join(self.out)

    def repuppet(self):
        self.account.unpuppet_object(self.session)
        self.account.puppet_object(self.session, self.char1)

    @staticmethod
    def reports_to(report_type):
        hub = ScriptDB.objects.get(db_key=f"{report_type}_reports")
        return list(Msg.objects.search_message(receiver=hub).order_by("id"))


class TestCmdsetShape(EvenniaTest):
    def test_four_commands(self):
        keys = {cmd.key for cmd in ReportsCmdSet().commands}
        self.assertEqual(keys, {"bug", "idea", "report", "manage reports"})

    def test_merges_above_a_menu_and_removes_nothing(self):
        menu = EvMenuCmdSet()
        self.assertGreater(ReportsCmdSet.priority, menu.priority)
        self.assertEqual(ReportsCmdSet.mergetype, "Union")

    def test_subclasses_keep_upstream_behaviour_and_help(self):
        for ours, theirs in ((CmdBug, upstream.CmdBug), (CmdIdea, upstream.CmdIdea),
                             (CmdReport, upstream.CmdReport)):
            self.assertTrue(issubclass(ours, theirs))
            self.assertEqual(ours.__doc__, theirs.__doc__)
            self.assertIn("Usage:", ours.__doc__)


class TestCmdsetOnLogin(_Fixture):
    def count(self):
        return sum(
            1 for cset in self.account.cmdset.cmdset_stack if cset.path == ReportsCmdSet.path
        )

    def test_login_put_it_on_the_stack(self):
        # receipt that the hook ran: setUp's login is the only thing that added it
        self.assertEqual(self.count(), 1)

    def test_second_ensure_adds_nothing(self):
        self.assertFalse(ensure_reports_cmdset(self.account))
        self.assertEqual(self.count(), 1)

    def test_added_persistently(self):
        self.account.cmdset.remove(ReportsCmdSet)
        self.assertEqual(self.count(), 0)
        self.assertTrue(ensure_reports_cmdset(self.account))
        self.assertIn(ReportsCmdSet.path, self.account.cmdset_storage)

    def test_failure_is_logged_not_raised(self):
        with mock.patch.object(
            report_commands, "ensure_reports_cmdset", side_effect=RuntimeError("boom")
        ), mock.patch("typeclasses.accounts.logger.log_trace") as trace:
            self.account.at_post_login(session=self.session)
        ours = [c for c in trace.call_args_list if c.args and "ingame_reports" in c.args[0]]
        self.assertEqual(len(ours), 1)


class TestReachableEverywhere(_Fixture):
    def test_bug_from_inside_character_creation(self):
        self.char1.db.chargen_complete = False
        self.repuppet()
        self.assertTrue(self.char1.cmdset.has(EvMenuCmdSet))
        self.assertIn("Your report has been filed.", self.send("bug stuck at allocation"))
        self.assertEqual([m.message for m in self.reports_to("bug")], ["stuck at allocation"])
        # Union: the menu still owns everything else
        self.assertTrue(self.char1.cmdset.has(EvMenuCmdSet))
        self.assertIn("Spent 72 of 80.", self.send("str 12"))

    def test_idea_out_of_character(self):
        self.account.unpuppet_object(self.session)
        self.assertIn("Thank you", self.send("idea horses to ride", by=self.account))
        self.assertEqual([m.message for m in self.reports_to("idea")], ["horses to ride"])

    def test_normal_play_keeps_its_commands(self):
        self.assertIn(self.room1.key, self.send("look"))
        self.assertIn("Your report has been filed.", self.send("bug a door echoes"))


class TestReadLocks(_Fixture):
    def setUp(self):
        super().setUp()
        self.warden = create.create_account("Warden", None, "Tidewater-Gate-73", permissions=["Admin"])
        self.builder = create.create_account("Builda", None, "Saltmarsh-Kiln-58", permissions=["Builder"])
        self.player = self.account2  # Player, the default
        self.send("bug the well is dry")
        self.send("idea fishing nets")
        self.send(f"report {self.account2.key} = rude in pub")
        self.filed = {t: self.reports_to(t) for t in report_export.REPORT_TYPES}

    def listed_in_menu(self, reader, report_type):
        """What `manage <type>` lists for `reader`: the menu's own node."""
        hub = ScriptDB.objects.get(db_key=f"{report_type}_reports")
        reader.ndb._evmenu = SimpleNamespace(hub=hub)
        try:
            _text, options = reports_menu.menunode_list_reports(reader, "")
        finally:
            del reader.ndb._evmenu
        return [opt for opt in options if "goto" in opt and "desc" in opt]

    def test_one_report_of_each_type(self):
        self.assertEqual({t: len(v) for t, v in self.filed.items()},
                         {"bug": 1, "idea": 1, "player": 1})

    def test_every_report_carries_the_staff_lock(self):
        for msgs in self.filed.values():
            self.assertEqual(msgs[0].locks.get("read"), STAFF_READ_LOCK)

    def test_admin_staff_reads_every_type_in_the_menu(self):
        for report_type in report_export.REPORT_TYPES:
            self.assertEqual(len(self.listed_in_menu(self.warden, report_type)), 1, report_type)

    def test_builder_reads_none(self):
        for report_type, msgs in self.filed.items():
            self.assertFalse(msgs[0].access(self.builder, "read"), report_type)

    def test_player_reads_none(self):
        for report_type, msgs in self.filed.items():
            self.assertFalse(msgs[0].access(self.player, "read"), report_type)

    def test_manage_is_admin_only(self):
        cmd = upstream.CmdManageReports()
        self.assertTrue(cmd.access(self.warden, "cmd"))
        self.assertFalse(cmd.access(self.builder, "cmd"))
        self.assertFalse(cmd.access(self.player, "cmd"))


class TestExport(_Fixture):
    def setUp(self):
        super().setUp()
        handle, self.path = tempfile.mkstemp(suffix=".jsonl")
        os.close(handle)
        self.addCleanup(os.remove, self.path)

    def lines(self):
        written, count = report_export.export_reports(self.path)
        self.assertEqual(written, self.path)
        with open(self.path, encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle]
        self.assertEqual(len(rows), count)
        return rows

    def test_types_are_the_commands_hub_types(self):
        hub_types = {cmd.report_type or cmd.key for cmd in (CmdBug, CmdIdea, CmdReport)}
        self.assertEqual(set(report_export.REPORT_TYPES), hub_types)

    def test_reads_without_creating_hubs(self):
        before = ScriptDB.objects.filter(db_key__endswith="_reports").count()
        self.assertEqual(self.lines(), [])
        self.assertEqual(ScriptDB.objects.filter(db_key__endswith="_reports").count(), before)

    def test_one_line_per_report_with_its_fields(self):
        self.send(f"bug {self.obj1.key} = it sticks")
        self.send("idea rope bridges")
        self.send(f"report {self.account2.key} = spamming")
        self.reports_to("bug")[0].tags.add("in progress")
        rows = self.lines()
        self.assertEqual([r["type"] for r in rows], ["bug", "idea", "player"])
        bug, idea, player = rows
        self.assertEqual(bug["text"], "it sticks")
        self.assertEqual(bug["target"], [[self.obj1.dbref, self.obj1.key]])
        self.assertEqual(bug["status"], ["in progress"])
        self.assertEqual(bug["sender"], [[self.account.dbref, self.account.key]])
        self.assertEqual(idea["target"], [])
        self.assertEqual(idea["status"], [])
        self.assertEqual(player["target"], [[self.account2.dbref, self.account2.key]])
        self.assertRegex(bug["date"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_a_duplicate_hub_cannot_hide_a_report(self):
        self.send("bug first")
        second = create.create_script(key="bug_reports")
        create.create_message(self.account, "second", receivers=[second], tags=["report"])
        self.assertEqual([r["text"] for r in self.lines()], ["first", "second"])


class TestHelpAlpha(EvenniaTest):
    def test_names_the_three_commands_after_the_staff_paragraph(self):
        text = alpha_contract.help_text()
        staff = text.find("To reach staff")
        for usage in ("bug <message>", "idea <message>", "report <player> = <message>"):
            self.assertGreater(text.find(usage), staff, usage)
