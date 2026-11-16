"""
`who` tells a player how many are abroad, not who. Names, Task NM-T14
(docs/PolishedWorld_Combat_Decomposition.md; the Names note's K1, UP14,
UQ1).

Evennia's `who` gave every player a table of every connected account by
name (`evennia/commands/default/account.py:506-518`), and with
`AUTO_CREATE_CHARACTER_WITH_ACCOUNT = True` an account's name is its
character's key. The project's `CmdWho` gives an account with Builder or
above Evennia's command unchanged (lock 2 A: Builder the name table,
Developer/Admin the session table, as Evennia decides), and anyone else one
sentence with the count (lock 1 A: UP14's *seven travellers are abroad in
the world*, the reader counted, the number in words to twenty).

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
- TestAbroadLine -- the sentence alone, at zero, one, several, twenty and
  past twenty.
- TestWho -- a player's `who` and `doing` give the sentence, with the live
  count and no account name; a Builder's and a Developer's give Evennia's
  table; the account cmdset holds the project's command.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_who
"""

from unittest import mock

import evennia
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands import names_commands
from commands.default_cmdsets import AccountCmdSet
from commands.names_commands import CmdWho, abroad_line


class TestAbroadLine(EvenniaTest):

    def test_the_counts_read_as_sentences(self):
        for count, line in (
            (0, "No travellers are abroad in the world."),
            (1, "One traveller is abroad in the world."),
            (2, "Two travellers are abroad in the world."),
            (7, "Seven travellers are abroad in the world."),
            (20, "Twenty travellers are abroad in the world."),
            (21, "21 travellers are abroad in the world."),
            (130, "130 travellers are abroad in the world."),
        ):
            with self.subTest(count=count):
                self.assertEqual(abroad_line(count), line)


class TestWho(EvenniaCommandTest):

    def who(self, caller, cmdstring="who"):
        # EvenniaCommandTest.call sets `cmdobj.account = self.account` whatever
        # the caller (test_resources.py:432), and `self.account` is a
        # Developer: the command would read the wrong account's permissions.
        with mock.patch.object(self, "account", caller):
            return self.call(CmdWho(), "", caller=caller, cmdstring=cmdstring)

    def test_a_player_reads_the_count_and_no_name(self):
        self.assertFalse(self.account2.check_permstring("Builder"))
        with mock.patch.object(evennia.SESSION_HANDLER, "account_count", return_value=7):
            said = self.who(self.account2)
        self.assertEqual(said, "Seven travellers are abroad in the world.")

    def test_the_count_is_the_live_one(self):
        live = evennia.SESSION_HANDLER.account_count()
        self.assertGreaterEqual(live, 1)
        said = self.who(self.account2)
        self.assertEqual(said, abroad_line(live))
        self.assertNotIn("TestAccount", said)

    def test_doing_is_the_count_too(self):
        said = self.who(self.account2, cmdstring="doing")
        self.assertEqual(said, abroad_line(evennia.SESSION_HANDLER.account_count()))

    def test_a_builder_reads_the_table(self):
        self.account2.permissions.add("Builder")
        said = self.who(self.account2)
        self.assertIn("Accounts:", said)
        self.assertIn("TestAccount", said)
        self.assertNotIn("Protocol", said)

    def test_a_developer_reads_the_session_table(self):
        said = self.who(self.account)
        self.assertIn("Accounts:", said)
        self.assertIn("TestAccount", said)
        self.assertIn("Protocol", said)

    def test_the_account_cmdset_holds_this_who(self):
        cmdset = AccountCmdSet()
        whos = [cmd for cmd in cmdset.commands if cmd.key == "who"]
        self.assertEqual([type(cmd) for cmd in whos], [names_commands.CmdWho])
