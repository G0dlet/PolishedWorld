"""
Tests for the character creation menu (Character Creation, Task CC3.1).

The menu is driven the way a player drives it: `EvMenu` is started on the
character and every line goes through `execute_cmd`, so the EvMenu cmdset,
option matching and the `_default` fallback are all in the path.

The fixture build is STR 7 DEX 9 CON 14 SIZ 8 INT 12 POW 17 CHA 13. Every
number it produces differs from the all-10s default (health 28 not 20; bases
16/29/21/21/26 not 20), so a screen or a write that silently fell back to the
default draft cannot pass. Expected values are written out by hand, never
recomputed from the module under test.
"""

from unittest import mock

from evennia.utils.ansi import strip_ansi
from evennia.utils.evmenu import EvMenu
from evennia.utils.test_resources import EvenniaTest, EvenniaTestCase

from world.chargen_menu import _parse_line

MENU = "world.chargen_menu"

START = {"str": 10, "dex": 10, "con": 10, "siz": 10, "int": 10, "pow": 10, "cha": 10}
FIXTURE = {"str": 7, "dex": 9, "con": 14, "siz": 8, "int": 12, "pow": 17, "cha": 13}
FIXTURE_LINE = "7 9 14 8 12 17 13"

# Derived by hand from FIXTURE: athletics STR+DEX, perception INT+POW,
# stealth DEX+INT, craft DEX+INT, hunting INT+CON.
EXPECTED_BASES = {
    "athletics": 16,
    "perception": 29,
    "stealth": 21,
    "craft": 21,
    "hunting": 26,
}
# The tanner's +10 craft on top.
EXPECTED_FINAL = dict(EXPECTED_BASES, craft=31)


class TestParseLine(EvenniaTestCase):
    """The line reader: form only, never the rules, never a half-applied line."""

    def test_one_pair(self):
        draft, error = _parse_line("str 12", START)
        self.assertIsNone(error)
        self.assertEqual(draft, dict(START, str=12))

    def test_several_pairs_any_case(self):
        draft, error = _parse_line("STR 12 Dex 14", START)
        self.assertIsNone(error)
        self.assertEqual(draft, dict(START, str=12, dex=14))

    def test_seven_numbers_in_order(self):
        draft, error = _parse_line(FIXTURE_LINE, START)
        self.assertIsNone(error)
        self.assertEqual(draft, FIXTURE)

    def test_out_of_range_is_left_to_validate_allocation(self):
        draft, error = _parse_line("str 25", START)
        self.assertIsNone(error)
        self.assertEqual(draft["str"], 25)

    def test_malformed_lines_change_nothing(self):
        before = dict(START)
        for line in ("", "xyz 12", "str twelve", "str 12.5", "str", "1 2 3",
                     "str 12 dex"):
            with self.subTest(line=line):
                draft, error = _parse_line(line, START)
                self.assertIsInstance(error, str)
                self.assertEqual(draft, START)
        self.assertEqual(START, before)

    def test_a_bad_pair_rejects_the_whole_line(self):
        draft, error = _parse_line("str 12 xyz 14", START)
        self.assertIsInstance(error, str)
        self.assertEqual(draft["str"], 10)


class _MenuFixture(EvenniaTest):
    """Start the menu on char1 and capture what it says, ANSI stripped."""

    def setUp(self):
        super().setUp()
        self.out = []
        patcher = mock.patch.object(self.char1, "msg", side_effect=self._capture)
        patcher.start()
        self.addCleanup(patcher.stop)
        EvMenu(self.char1, MENU, startnode="node_allocate", cmd_on_exit=None)

    def _capture(self, text=None, *args, **kwargs):
        if isinstance(text, (tuple, list)):
            text = text[0]
        self.out.append(strip_ansi(str(text)))

    def send(self, *lines):
        """Send lines in order; return what the last one printed."""
        for line in lines:
            self.out.clear()
            self.char1.execute_cmd(line, session=self.session)
        return "\n".join(self.out)

    def node(self):
        menu = self.char1.ndb._evmenu
        return menu.nodename if menu else None

    def state(self):
        """Everything node_done may write, in one comparable value."""
        char = self.char1
        return {
            "stats": {k: char.stats.get(k).base for k in START},
            "skills": {
                k: (char.skills.get(k).base, char.skills.get(k).current)
                for k in EXPECTED_BASES
            },
            "health": char.traits.get("health").base,
            "profession": char.db.profession,
            "complete": char.db.chargen_complete,
        }

    def walk_to_last_confirm(self):
        return self.send(FIXTURE_LINE, "next", "yes", "tanner")


class TestAllocateNode(_MenuFixture):
    """The allocate screen: running total, every violation at once, a gate."""

    def test_start_screen_shows_total_and_descriptions(self):
        text = "\n".join(self.out)
        self.assertIn("Spent 70 of 80.", text)
        self.assertIn("10 left to spend", text)
        self.assertIn("Raw muscle", text)
        self.assertIn("Feeds hunting, health.", text)

    def test_illegal_line_stays_and_lists_every_violation(self):
        text = self.send("str 25 dex 3")
        self.assertEqual(self.node(), "node_allocate")
        self.assertIn("STR is 25", text)
        self.assertIn("DEX is 3", text)
        self.assertIn("Spent 78 of 80.", text)

    def test_next_is_refused_while_anything_is_wrong(self):
        text = self.send("next")
        self.assertEqual(self.node(), "node_allocate")
        self.assertIn("Not yet", text)

    def test_malformed_line_keeps_the_draft(self):
        self.send("str 12")
        text = self.send("str twelve")
        self.assertEqual(self.node(), "node_allocate")
        self.assertIn("whole number", text)
        self.assertIn("Spent 72 of 80.", text)

    def test_legal_build_then_next_reaches_confirm(self):
        self.send(FIXTURE_LINE, "next")
        self.assertEqual(self.node(), "node_confirm_allocation")


class TestConfirmScreens(_MenuFixture):
    """The player sees the numbers the character will get, bonus included."""

    def test_allocation_confirm_shows_health_and_bases(self):
        text = self.send(FIXTURE_LINE, "next")
        self.assertIn("Health max: 28", text)
        self.assertIn(
            "athletics 16, perception 29, stealth 21, craft 21, hunting 26", text
        )

    def test_back_keeps_the_draft(self):
        text = self.send(FIXTURE_LINE, "next", "back")
        self.assertEqual(self.node(), "node_allocate")
        self.assertIn("Spent 80 of 80.", text)

    def test_profession_list_names_recipes_and_bonus(self):
        text = self.send(FIXTURE_LINE, "next", "yes")
        self.assertIn("tanner", text)
        self.assertIn("linen shirt", text)
        self.assertIn("craft +10", text)

    def test_profession_confirm_shows_base_and_bonus(self):
        text = self.walk_to_last_confirm()
        self.assertEqual(self.node(), "node_confirm_profession")
        self.assertIn("craft 21 -> 31 (+10)", text)
        self.assertIn("Recipes: leather", text)


class TestNoWriteBeforeDone(_MenuFixture):
    """Leaving anywhere before the last yes changes nothing on the character."""

    def setUp(self):
        super().setUp()
        self.before = self.state()

    def test_walking_to_the_last_confirm_writes_nothing(self):
        self.walk_to_last_confirm()
        self.assertEqual(self.state(), self.before)

    def test_quitting_midway_writes_nothing(self):
        self.send(FIXTURE_LINE, "next", "yes", "quit")
        self.assertIsNone(self.node())
        self.assertEqual(self.state(), self.before)


class TestHappyPath(_MenuFixture):
    """The last yes applies the build and the profession, once, and closes."""

    def setUp(self):
        super().setUp()
        self.char1.login_skill_snapshot = {k: 20 for k in EXPECTED_BASES}
        self.walk_to_last_confirm()
        self.text = self.send("yes")

    def test_menu_closes(self):
        self.assertIsNone(self.node())
        self.assertIn("Your character is made", self.text)

    def test_characteristics_and_health(self):
        state = self.state()
        self.assertEqual(state["stats"], FIXTURE)
        self.assertEqual(state["health"], 28)

    def test_skills_carry_bases_and_bonus(self):
        for key, value in EXPECTED_FINAL.items():
            with self.subTest(skill=key):
                skill = self.char1.skills.get(key)
                self.assertEqual((skill.base, skill.current), (value, value))

    def test_profession_and_flag(self):
        self.assertEqual(self.char1.db.profession, "tanner")
        self.assertIs(self.char1.db.chargen_complete, True)

    def test_progress_baseline_is_retaken(self):
        self.assertEqual(self.char1.login_skill_snapshot, EXPECTED_FINAL)


class TestDoneRefuses(_MenuFixture):
    """
    node_done's refusal paths: flag unset unless everything landed, and the
    menu closes only for a character already made. Any other refusal keeps
    it open with `back` and the draft (CC3.2's gate): a closed menu would let
    an unmade character into the world until its next puppet.
    """

    def test_finished_character_is_not_rebuilt(self):
        # No profession on purpose: apply_allocation would accept this
        # character, so only node_done's own guard can stop the rewrite.
        self.char1.db.chargen_complete = True
        before = self.state()
        self.walk_to_last_confirm()
        text = self.send("yes")
        self.assertIn("already made", text)
        self.assertEqual(self.state(), before)
        self.assertIsNone(self.node())

    def test_apply_refusal_changes_nothing(self):
        self.char1.attributes.add("skill_xp", {"craft": 1})
        before = self.state()
        self.walk_to_last_confirm()
        text = self.send("yes")
        self.assertIn("Nothing was changed", text)
        self.assertEqual(self.state(), before)
        self.assertEqual(self.node(), "node_done")
        self.assertIn("Spent 80 of 80.", self.send("back"))

    def test_grant_error_leaves_flag_unset(self):
        self.walk_to_last_confirm()
        with mock.patch(
            "world.professions.grant_profession", side_effect=ValueError("boom")
        ):
            text = self.send("yes")
        self.assertIn("could not be granted (boom)", text)
        self.assertFalse(self.char1.db.chargen_complete)
        self.assertEqual(self.state()["stats"], FIXTURE)

    def test_silent_grant_refusal_leaves_flag_unset(self):
        self.walk_to_last_confirm()
        with mock.patch("world.professions.grant_profession", return_value=[]):
            text = self.send("yes")
        self.assertIn("could not be granted", text)
        self.assertFalse(self.char1.db.chargen_complete)
        self.assertEqual(self.node(), "node_done")

    def test_half_done_recovers_in_the_same_menu(self):
        # The stats land, the grant fails; `back` and the same walk again
        # must finish the character -- apply_allocation accepts a second run
        # because there is still no profession and no banked XP.
        self.walk_to_last_confirm()
        with mock.patch(
            "world.professions.grant_profession", side_effect=ValueError("boom")
        ):
            self.send("yes")
        self.assertEqual(self.node(), "node_done")
        self.send("back", "next", "yes", "tanner", "yes")
        self.assertIsNone(self.node())
        self.assertIs(self.char1.db.chargen_complete, True)
        self.assertEqual(self.state()["profession"], "tanner")
        self.assertEqual(self.state()["skills"]["craft"], (31, 31))
