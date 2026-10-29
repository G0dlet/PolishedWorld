"""
CC3.2: the creation menu meets a pending character on puppet, and resumes --
not restarts -- after a disconnect or a reload.

What each class pressures:

- TestBirthStamp: the pending stamp is written by the account's creation
  door and only there. A character made any other way (`create`, test
  fixtures) is not pending, and a made character is never set back.
- TestLaunchCondition: only `False` launches. Reading the flag as `not flag`
  would drop every test fixture's auto-puppeted `char1` and every character
  that predates chargen into the menu. The menu has no `quit`.
- TestResume: a reconnect or a reload continues the saved node with the saved
  draft. A new EvMenu would close the old one (running `cmd_on_exit`) and
  start at ten in everything -- "Spent 70 of 80." instead of 72.
"""

from unittest import mock

from evennia import create_object
from evennia.utils.ansi import strip_ansi
from evennia.utils.evmenu import EvMenuCmdSet
from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character
from world.chargen import mark_chargen_pending, start_or_resume_chargen

FIXTURE_LINE = "7 9 14 8 12 17 13"


class _PuppetFixture(EvenniaTest):
    """char1 is puppeted by the mixin's setUp; capture what it is told."""

    def setUp(self):
        super().setUp()
        self.out = []
        patcher = mock.patch.object(self.char1, "msg", side_effect=self._capture)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _capture(self, text=None, *args, **kwargs):
        if isinstance(text, (tuple, list)):
            text = text[0]
        self.out.append(strip_ansi(str(text)))

    def repuppet(self):
        """Disconnect and reconnect: at_post_unpuppet, then at_post_puppet."""
        self.account.unpuppet_object(self.session)
        self.out.clear()
        self.account.puppet_object(self.session, self.char1)
        return "\n".join(self.out)

    def send(self, *lines):
        """Send lines in order; return what the last one printed."""
        for line in lines:
            self.out.clear()
            self.char1.execute_cmd(line, session=self.session)
        return "\n".join(self.out)

    def in_menu(self):
        return bool(self.char1.cmdset.has(EvMenuCmdSet))

    def node(self):
        menu = self.char1.ndb._evmenu
        return menu.nodename if menu else None


class TestBirthStamp(EvenniaTest):
    def test_account_door_stamps_pending(self):
        char, errors = self.account.create_character(key="Neo")
        self.assertEqual(errors, [])
        self.assertIs(char.db.chargen_complete, False)

    def test_other_doors_do_not(self):
        built = create_object(Character, key="Statue", location=self.room1)
        self.assertIsNone(built.db.chargen_complete)
        self.assertIsNone(self.char1.db.chargen_complete)

    def test_made_character_is_never_unmade(self):
        self.char1.db.chargen_complete = True
        mark_chargen_pending(self.char1)
        self.assertIs(self.char1.db.chargen_complete, True)


class TestLaunchCondition(_PuppetFixture):
    def test_pending_character_meets_the_menu(self):
        self.char1.db.chargen_complete = False
        text = self.repuppet()
        self.assertTrue(self.in_menu())
        self.assertEqual(self.node(), "node_allocate")
        self.assertIn("Spent 70 of 80.", text)
        self.assertTrue(self.char1.attributes.get("_menutree_saved"))

    def test_unstamped_character_does_not(self):
        self.assertIsNone(self.char1.db.chargen_complete)
        self.repuppet()
        self.assertFalse(self.in_menu())
        self.assertIsNone(start_or_resume_chargen(self.char1))

    def test_made_character_does_not(self):
        self.char1.db.chargen_complete = True
        self.repuppet()
        self.assertFalse(self.in_menu())

    def test_the_menu_has_no_quit(self):
        self.char1.db.chargen_complete = False
        self.repuppet()
        self.send("quit")
        self.assertTrue(self.in_menu())
        self.assertEqual(self.node(), "node_allocate")


class TestResume(_PuppetFixture):
    def setUp(self):
        super().setUp()
        self.char1.db.chargen_complete = False
        self.repuppet()
        self.assertIn("Spent 72 of 80.", self.send("str 12"))

    def test_reconnect_keeps_the_draft(self):
        text = self.repuppet()
        self.assertIn("Spent 72 of 80.", text)
        self.assertNotIn("Spent 70 of 80.", text)
        self.assertTrue(self.in_menu())

    def test_reconnect_does_not_close_the_old_menu(self):
        # Called directly, so at_post_puppet's own room look is not in the
        # output: a room line here can only come from close_menu() running
        # cmd_on_exit on the menu still in ndb.
        self.out.clear()
        start_or_resume_chargen(self.char1)
        text = "\n".join(self.out)
        self.assertIn("Spent 72 of 80.", text)
        self.assertNotIn(self.room1.key, text)

    def test_reload_keeps_the_draft(self):
        del self.char1.ndb._evmenu  # what a reload leaves: no ndb, saved state
        text = self.repuppet()
        self.assertIn("Spent 72 of 80.", text)
        self.assertEqual(self.node(), "node_allocate")

    def test_resume_returns_to_the_saved_node(self):
        self.send(FIXTURE_LINE, "next")
        self.assertEqual(self.node(), "node_confirm_allocation")
        self.repuppet()
        self.assertEqual(self.node(), "node_confirm_allocation")
        self.assertIn("Spent 80 of 80.", self.send("back"))
