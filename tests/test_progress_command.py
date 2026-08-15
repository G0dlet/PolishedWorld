"""
Unit tests for the `progress` command. Stage 4.5, Component D.1.

Written to the pattern in `tests/test_knowledge.py`, the golden reference for
this project (AGENTS.md section 0A).

WHAT IT COVERS
--------------
* commands.character_commands.CmdProgress -- rewritten by D.1 from a
  session-delta report into a standing-plus-delta report

⚠️ THIS COMMAND HAD NO TESTS AT ALL BEFORE THIS FILE
-----------------------------------------------------
Same hole `improve_skill_on_use` was in before C.1, and the same consequence:
the 391-test baseline this component inherited would have stayed green if
`CmdProgress` had been deleted outright. That matters more than usual here,
because D.1 did not merely restyle the command -- it removed a filtering rule
(locked D-3), and a removed rule leaves no syntax behind to notice.

WHY THE SKIP RULE HAD TO GO, RESTATED SO THE TESTS BELOW READ AS ASSERTIONS
RATHER THAN AS PREFERENCES
---------------------------------------------------------------------------
The command used to list only skills whose `.current` had risen since login.
That was correct while a tick moved the percentage nearly every time. After C.1
a level moves roughly once in dozens of ticks, so "unchanged" became the normal
case and the command answered "No skills have improved since you logged in" for
hours -- the same silence C.2 fixed one level down in the feedback line. The
first two tests below are the ones that would have caught a re-introduction of
the rule.

BASE CLASS
----------
`EvenniaCommandTest` throughout: every assertion here is about what the command
prints, so the command parser is the thing under test and mocking it away would
leave nothing.

⚠️ `self.call()` DOES NOT RUN COMMAND LOCKS
--------------------------------------------
`CmdProgress` is `cmd:all()`, so there is no permission to test and no vacuous
pass to worry about here. Noted anyway, because the next person to add a
lock-bearing command to this file will need `Command.access(caller, "cmd")`
instead (Testing Reference, `.call()` section).

HOW TO RUN
----------
The --settings flag is NOT optional anywhere in this project.

    evennia test --settings settings.py tests
    evennia test --settings settings.py tests.test_progress_command
"""

from django.test import override_settings

from evennia.utils.test_resources import EvenniaCommandTest

from commands.character_commands import CmdProgress
from world.progression import _BAR_EMPTY, _BAR_FULL, xp_threshold


CHARACTER = "typeclasses.characters.Character"


@override_settings(SKILL_XP_BASE=6, SKILL_XP_DOUBLING_SPAN=20)
class TestProgressCommand(EvenniaCommandTest):
    """
    D.1's half of the felt-progress restoration: the pull, not the push.

    The calibration is pinned for the same reason `tests/test_improvement_engine`
    pins it -- one assertion below depends on a level costing more than one
    tick's worth of XP, and at a degenerate calibration that stops being true.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.craft = self.char1.skills.get("craft")
        self.craft.current = 40

    def _output(self):
        return self.call(CmdProgress(), "", caller=self.char1)

    # -- the skip rule is gone -------------------------------------------

    def test_a_skill_that_has_not_moved_is_still_listed(self):
        """
        The assertion this rewrite exists for.

        With the old rule this character -- who has gained nothing this session --
        produced a single line saying so. Anything that re-introduces the rule
        fails here.
        """
        self.char1.login_skill_snapshot = {"craft": 40}

        out = self._output()

        self.assertIn(self.craft.name, out)
        self.assertNotIn("No skills have improved", out)

    def test_every_skill_appears_every_time(self):
        self.char1.login_skill_snapshot = {}

        out = self._output()

        for skill_key in self.char1.skills.all():
            skill = self.char1.skills.get(skill_key)
            self.assertIn(skill.name, out, f"{skill_key} missing from the report")

    # -- the bar ----------------------------------------------------------

    def test_a_trainable_skill_draws_a_bar(self):
        out = self._output()
        self.assertIn(_BAR_EMPTY, out)

    def test_the_bar_moves_on_banked_xp_that_did_not_change_the_percentage(self):
        """
        The single observation that justifies Component D, asserted in the pull
        view as well as the push view.

        Bank one XP short of nothing -- the level cannot move at (6, 20), where
        point 41 costs 12 -- and the rendered bar must still differ. If it does
        not, the command is reporting the level a second time rather than
        reporting progress.
        """
        before = self._output()

        self.char1.skill_xp.add("craft", 5)

        self.assertEqual(int(self.craft.current), 40, "the level was not supposed to move")
        self.assertNotEqual(before, self._output())

    def test_no_xp_figure_reaches_the_player(self):
        """
        P-8, asserted where it is easiest to break: a command with room on the
        line is exactly where someone adds "(6/12 XP)" for debugging and leaves
        it in.
        """
        self.char1.skill_xp.add("craft", 5)

        out = self._output()

        self.assertNotIn(str(self.char1.skill_xp.get("craft")), out)
        self.assertNotIn("XP", out)

    # -- the captions that replace a bar (locked D-4) ----------------------

    def test_an_untrainable_skill_says_so_instead_of_showing_a_dead_bar(self):
        """
        Stealth has no call-site, so its bar could never move. An empty bar there
        reads as broken and a hidden row hides the fact that three of five skills
        are untrained content; the caption is the third option.
        """
        out = self._output()

        self.assertIn("not yet trainable", out)
        stealth = self.char1.skills.get("stealth")
        self.assertNotIn(stealth.key, self.char1.improvable_skills)

    def test_a_maxed_skill_says_so_instead_of_showing_a_frozen_bar(self):
        """
        At the cap `improve_skill_on_use` short-circuits and the total freezes
        inside [threshold(cap), threshold(cap + 1)), so a bar here would show a
        partial fill that never moves again.

        ⚠️ D.2 lifts the cap and this branch dies with it. When that happens this
        test should be deleted, not adjusted -- an adjusted version would be
        asserting a caption for a state that can no longer occur.
        """
        self.craft.current = 100

        out = self._output()

        self.assertIn("at maximum", out)

    # -- the session delta, which survives as a suffix ---------------------

    def test_a_skill_that_grew_this_session_carries_its_gain(self):
        self.char1.login_skill_snapshot = {"craft": 38}

        self.assertIn("+2", self._output())

    def test_a_skill_that_did_not_grow_carries_no_gain_marker(self):
        self.char1.login_skill_snapshot = {"craft": 40}

        # The bar art may legitimately be empty or full; what must not appear is
        # a "+n" against a skill that gained nothing this session.
        self.assertNotIn("+", self._output())

    def test_the_session_delta_is_read_from_current_not_from_value(self):
        """
        A worn tool's +20 must not masquerade as this session's progress. The
        snapshot is taken from `.current` at login, so reading `.value` here
        would invent a gain out of a buff -- and would un-invent it when the tool
        broke.
        """
        self.char1.login_skill_snapshot = {"craft": 40}
        self.craft.mod = 20

        out = self._output()

        self.assertNotIn("+20", out)
        self.assertIn("40%", out)

    # -- degenerate inputs -------------------------------------------------

    def test_a_missing_snapshot_is_not_an_error(self):
        # login_skill_snapshot defaults to None (autocreate=False) and a command
        # run before any puppet snapshot must still work.
        self.char1.login_skill_snapshot = None

        self.assertIn(self.craft.name, self._output())

    def test_a_skill_standing_exactly_on_its_threshold_draws_an_empty_bar(self):
        # The boundary case the derived-floor rule produces on a fresh character:
        # total == threshold(level) exactly, so earned == 0.
        self.char1.skill_xp.add("craft", xp_threshold(41) - xp_threshold(40))

        out = self._output()

        self.assertIn(_BAR_EMPTY, out)
        self.assertNotIn(_BAR_FULL * 20, out)
