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

The appearance step (Names NM-T16) takes female, adult, freckled: with the
fixture's SIZ 8 that reads *a small, freckled woman*, and neither the build
nor the noun is the placeholder's or the all-10s draft's (SIZ 10, *lean*).
"""

from unittest import mock

from evennia.utils.ansi import strip_ansi
from evennia.utils.evmenu import EvMenu
from evennia.utils.test_resources import EvenniaTest, EvenniaTestCase

from world import chargen_menu, client_state, sdesc, seed_data, wounds
from world.chargen_menu import _parse_line
from world.seeding import find_seeded, seed_world

MENU = "world.chargen_menu"

START = {"str": 10, "dex": 10, "con": 10, "siz": 10, "int": 10, "pow": 10, "cha": 10}
FIXTURE = {"str": 7, "dex": 9, "con": 14, "siz": 8, "int": 12, "pow": 17, "cha": 13}
FIXTURE_LINE = "7 9 14 8 12 17 13"
# STR 12, DEX 13, CON 7, SIZ 14, INT 16, POW 8, CHA 10: 80 points.
BODY_LINE = "12 13 7 14 16 8 10"
COMBAT_SENTENCE = "These three are read in combat, which is not in the game yet."

# Derived by hand from FIXTURE: athletics STR+DEX, perception INT+POW,
# stealth DEX+INT, craft DEX+INT, hunting INT+CON; the four combat skills
# (BD5, p. 14): brawn STR+SIZ, evade DEX x 2, resilience CON x 2, unarmed
# STR+DEX; and first aid INT+DEX (HL2).
EXPECTED_BASES = {
    "athletics": 16,
    "perception": 29,
    "stealth": 21,
    "craft": 21,
    "hunting": 26,
    "brawn": 15,
    "evade": 18,
    "resilience": 28,
    "unarmed": 16,
    "first_aid": 21,
}
# The tanner's +10 craft on top.
EXPECTED_FINAL = dict(EXPECTED_BASES, craft=31)

# Sex 2, age 2, feature 11, on the appearance step's numbered lists.
APPEARANCE_LINE = "2 2 11"
APPEARANCE = {"sex": "female", "age": "adult", "feature": "freckled"}
# By hand: SIZ 8 is *small* (NM-T15 lock 1), female adult is *woman*.
COMPOSED = "a small, freckled woman"
NO_CHOICES = "Chosen: sex --, age --, feature --."
ALL_CHOSEN = "Chosen: sex female, age adult, feature freckled."


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

    # What the menu runs when it closes; the shipped menu runs "look"
    # (world/chargen.py), which only Arrival's first-screen test needs.
    on_exit = None

    def setUp(self):
        super().setUp()
        self.out = []
        patcher = mock.patch.object(self.char1, "msg", side_effect=self._capture)
        patcher.start()
        self.addCleanup(patcher.stop)
        EvMenu(self.char1, MENU, startnode="node_allocate", cmd_on_exit=self.on_exit)

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
            "hit_points": wounds.health_of(char)[:2],
            "profession": char.db.profession,
            "complete": char.db.chargen_complete,
            "appearance": char.attributes.get("appearance"),
        }

    def walk_to_profession_confirm(self):
        return self.send(FIXTURE_LINE, "next", "yes", "tanner")

    def walk_to_last_confirm(self):
        return self.send(FIXTURE_LINE, "next", "yes", "tanner", "yes",
                         APPEARANCE_LINE, "next")

    def restart_at(self, node, **kwargs):
        """A menu saved at `node` with these kwargs, resumed; what it printed."""
        self.out.clear()
        EvMenu(self.char1, MENU, startnode=node, startnode_input=("", kwargs),
               cmd_on_exit=self.on_exit)
        return "\n".join(self.out)


class TestAllocateNode(_MenuFixture):
    """The allocate screen: running total, every violation at once, a gate."""

    def test_start_screen_shows_total_and_descriptions(self):
        text = "\n".join(self.out)
        self.assertIn("Spent 70 of 80.", text)
        self.assertIn("10 left to spend", text)
        self.assertIn("Raw muscle", text)
        # WN-T6: CON and SIZ feed Hit Points, not a CON x 2 health.
        self.assertIn("Feeds hunting, resilience, Hit Points.", text)
        # BD5: SIZ has its first reader, and DEX feeds Evade and Unarmed.
        self.assertIn("Feeds brawn, Damage Modifier, Hit Points.", text)
        self.assertIn(
            "Feeds athletics, stealth, craft, evade, unarmed, first aid, "
            "Combat Actions, Strike Rank.",
            text,
        )
        # HL2: INT feeds first aid, and the key's underscore is not shown.
        self.assertIn(
            "Feeds perception, stealth, craft, hunting, first aid, "
            "Combat Actions, Strike Rank.",
            text,
        )
        self.assertNotIn("first_aid", text)

    def test_each_derived_value_is_named_by_both_its_characteristics(self):
        # BD9: the choice cannot be redone, so the screen says what it feeds.
        rows = {
            line.split()[0]: line
            for line in self.send("look").splitlines()
            if line.split()
            and line.split()[0] in ("STR", "DEX", "CON", "SIZ", "INT", "POW", "CHA")
        }
        for stat in ("DEX", "INT"):
            with self.subTest(stat=stat):
                self.assertIn("Combat Actions, Strike Rank.", rows[stat])
                self.assertNotIn("Damage Modifier", rows[stat])
        for stat in ("STR", "SIZ"):
            with self.subTest(stat=stat):
                self.assertIn("Damage Modifier", rows[stat])
                self.assertNotIn("Combat Actions", rows[stat])
        # WN-T6: Hit Points are CON + SIZ's, and no one else's.
        for stat in ("CON", "SIZ"):
            with self.subTest(stat=stat):
                self.assertIn("Hit Points.", rows[stat])
        for stat in ("STR", "DEX", "INT", "POW", "CHA"):
            with self.subTest(stat=stat):
                self.assertNotIn("Hit Points", rows[stat])
        for stat in ("CON", "POW", "CHA"):
            with self.subTest(stat=stat):
                self.assertNotIn("Combat Actions", rows[stat])
                self.assertNotIn("Strike Rank", rows[stat])
                self.assertNotIn("Damage Modifier", rows[stat])

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
        self.assertIn("Hit Points: head 5, chest 7, abdomen 6, arms 4, legs 5", text)   # CON 14 + SIZ 8 = 22
        self.assertIn(
            "athletics 16, perception 29, stealth 21, craft 21, hunting 26", text
        )
        # HL2: the last pair, shown as two words.
        self.assertIn("unarmed 16, first aid 21", text)
        self.assertNotIn("first_aid", text)

    def test_allocation_confirm_shows_the_three_derived_values(self):
        # The four characteristics that matter are Alaric's (core p. 9):
        # STR 12, DEX 13, SIZ 14, INT 16. His own seven sum to 86, so the
        # other three are lowered to make a legal 80.
        text = self.send(BODY_LINE, "next")
        self.assertEqual(self.node(), "node_confirm_allocation")
        self.assertIn(
            "Combat Actions 3, Strike Rank 15, Damage Modifier +1D2", text
        )

    def test_the_derived_line_stands_under_hit_points(self):
        lines = self.send(BODY_LINE, "next").splitlines()
        at = lines.index("Hit Points: head 5, chest 7, abdomen 6, arms 4, legs 5")   # CON 7 + SIZ 14 = 21
        self.assertEqual(
            lines[at + 1], "Combat Actions 3, Strike Rank 15, Damage Modifier +1D2"
        )
        self.assertEqual(lines[at + 2], COMBAT_SENTENCE)

    def test_strike_rank_reads_int_as_well_as_dex(self):
        # DEX 13 with INT 6: the average rounds up to 10, not 13.
        text = self.send("13 13 13 13 6 11 11", "next")
        self.assertIn("Combat Actions 2, Strike Rank 10, Damage Modifier +1D2", text)

    def test_a_weak_small_body_reads_a_minus(self):
        text = self.send(FIXTURE_LINE, "next")
        self.assertIn("Combat Actions 2, Strike Rank 11, Damage Modifier -1D4", text)

    def test_back_keeps_the_draft(self):
        text = self.send(FIXTURE_LINE, "next", "back")
        self.assertEqual(self.node(), "node_allocate")
        self.assertIn("Spent 80 of 80.", text)

    def test_profession_list_names_recipes_and_bonus(self):
        text = self.send(FIXTURE_LINE, "next", "yes")
        self.assertIn("tanner", text)
        self.assertIn("linen shirt", text)
        self.assertIn("craft +10", text)
        # Moved from test_professions' TestProfessionList (CC3.3): the
        # package's dict keys never reach the player.
        self.assertNotIn("skill_bonus", text)

    def test_profession_confirm_shows_base_and_bonus(self):
        text = self.walk_to_profession_confirm()
        self.assertEqual(self.node(), "node_confirm_profession")
        self.assertIn("craft 21 -> 31 (+10)", text)
        self.assertIn("Recipes: leather", text)

    def test_the_final_question_has_moved_to_the_appearance(self):
        # NM-T16: the profession's yes is no longer the last one.
        text = self.walk_to_profession_confirm()
        self.assertNotIn("cannot be changed", text)
        self.assertNotIn("Create this character", text)
        self.send("yes")
        self.assertEqual(self.node(), "node_appearance")


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

    def test_characteristics_and_hit_points(self):
        state = self.state()
        self.assertEqual(state["stats"], FIXTURE)
        self.assertEqual(state["hit_points"], (10, 10))
        self.assertIsNone(self.char1.traits.get("health"))

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

    def test_the_appearance_facts_are_written_and_composed(self):
        self.assertEqual(self.state()["appearance"], APPEARANCE)
        self.assertEqual(self.char1.sdesc.get(), COMPOSED)


# ---------------------------------------------------------------------------
# The appearance step (Names NM-T16; OQ-NM9 (1))
# ---------------------------------------------------------------------------


class TestAppearanceStep(_MenuFixture):
    """Three numbered lists, one line parsed like the allocation's, a gate."""

    def setUp(self):
        super().setUp()
        self.walk_to_profession_confirm()
        self.text = self.send("yes")

    def test_the_build_is_shown_from_siz_and_not_chosen(self):
        self.assertEqual(self.node(), "node_appearance")
        self.assertIn("SIZ 8 reads as small.", self.text)
        self.assertNotIn("build 1", self.text)

    def test_the_three_lists(self):
        for shown in ("1 male (he)", "2 female (she)", "3 unstated (they)",
                      "1 young", "2 adult", "3 old",
                      "1 grey-eyed", "11 freckled", "20 weathered"):
            with self.subTest(shown=shown):
                self.assertIn(shown, self.text)
        self.assertIn(NO_CHOICES, self.text)
        self.assertIn("Still to choose: sex, age, feature.", self.text)

    def test_a_pair_by_number_or_by_word(self):
        self.send("sex female")
        text = self.send("AGE 2")
        self.assertEqual(self.node(), "node_appearance")
        self.assertIn("Chosen: sex female, age adult, feature --.", text)
        self.assertIn("Still to choose: feature.", text)

    def test_all_three_on_one_line(self):
        text = self.send(APPEARANCE_LINE)
        self.assertIn(ALL_CHOSEN, text)
        self.assertIn("All three chosen.", text)

    def test_a_line_of_three_words(self):
        text = self.send("female adult freckled")
        self.assertIn(ALL_CHOSEN, text)

    def test_a_choice_off_the_lists_is_refused_with_the_lists_again(self):
        self.send("sex 1")
        before = "Chosen: sex male, age --, feature --."
        for line, said in (
            ("sex 4", "There is no sex 4; choose 1-3."),
            ("age 0", "There is no age 0; choose 1-3."),
            ("feature 21", "There is no feature 21; choose 1-20."),
            ("feature purple", "'purple' is not a feature on the list."),
            ("sex 2 age 9", "There is no age 9"),
            ("2 2 99", "There is no feature 99"),
            ("sex", "Pairs come as a name and a choice"),
            ("1 2", "needs all 3"),
            ("sex 2 colour 1", "Unknown choice 'colour'"),
        ):
            with self.subTest(line=line):
                text = self.send(line)
                self.assertEqual(self.node(), "node_appearance")
                self.assertIn(said, text)
                self.assertIn(before, text)       # the whole line changed nothing
                self.assertIn("20 weathered", text)   # the lists again

    def test_next_is_refused_until_all_three_are_chosen(self):
        self.send("sex 2", "feature 11")
        text = self.send("next")
        self.assertEqual(self.node(), "node_appearance")
        self.assertIn("Not yet -- choose all three first.", text)
        self.assertIn("Chosen: sex female, age --, feature freckled.", text)

    def test_next_with_all_three_reaches_the_confirmation(self):
        self.send(APPEARANCE_LINE, "next")
        self.assertEqual(self.node(), "node_confirm_appearance")

    def test_back_to_the_profession_and_yes_keeps_the_choices(self):
        self.send(APPEARANCE_LINE)
        text = self.send("back")
        self.assertEqual(self.node(), "node_confirm_profession")
        self.assertIn("craft 21 -> 31 (+10)", text)
        self.assertIn(ALL_CHOSEN, self.send("yes"))

    def test_help_gives_the_forms(self):
        self.assertIn("all three at once", self.send("help"))


class TestConfirmAppearance(_MenuFixture):
    """The composer's line for the draft, the final question, `back`."""

    def setUp(self):
        super().setUp()
        self.text = self.walk_to_last_confirm()

    def test_the_line_and_the_final_question(self):
        self.assertEqual(self.node(), "node_confirm_appearance")
        self.assertIn(f"  {COMPOSED}\n", self.text)
        self.assertIn("This cannot be changed here. Create this character?", self.text)

    def test_the_line_is_the_composers_without_state_or_garment(self):
        with mock.patch.object(
            sdesc, "compose_text", wraps=sdesc.compose_text
        ) as composer:
            self.send("back", "next")
        composer.assert_called_once_with("female", "adult", "freckled", 8)

    def test_back_returns_with_the_choices_and_the_draft(self):
        text = self.send("back")
        self.assertEqual(self.node(), "node_appearance")
        self.assertIn(ALL_CHOSEN, text)
        self.assertIn("SIZ 8 reads as small.", text)

    def test_a_stale_confirmation_goes_back_to_the_step(self):
        text = self.restart_at(
            "node_confirm_appearance", draft=dict(FIXTURE), profession="tanner"
        )
        self.assertIn("Choose how strangers see you first.", text)
        self.assertNotIn("Create this character", text)
        self.send("back")
        self.assertEqual(self.node(), "node_appearance")


class TestDoneWithoutAppearance(_MenuFixture):
    """
    A menu saved before NM-T16 has a draft and a profession and no choices.
    `node_done` writes nothing for it and sends it to the step (NMM25).
    """

    def setUp(self):
        super().setUp()
        self.before = self.state()

    def test_node_done_without_choices_writes_nothing(self):
        text = self.restart_at("node_done", draft=dict(FIXTURE), profession="tanner")
        self.assertIn("Nothing was changed: choose how strangers see you first.", text)
        self.assertEqual(self.node(), "node_done")
        self.assertEqual(self.state(), self.before)
        self.assertFalse(self.char1.db.chargen_complete)

    def test_back_lands_on_the_step_and_the_character_is_then_made(self):
        self.restart_at("node_done", draft=dict(FIXTURE), profession="tanner")
        text = self.send("back")
        self.assertEqual(self.node(), "node_appearance")
        self.assertIn("SIZ 8 reads as small.", text)
        self.send(APPEARANCE_LINE, "next", "yes")
        self.assertIsNone(self.node())
        self.assertIs(self.char1.db.chargen_complete, True)
        self.assertEqual(self.state()["appearance"], APPEARANCE)

    def test_a_saved_profession_confirmation_leads_to_the_step(self):
        self.restart_at(
            "node_confirm_profession", draft=dict(FIXTURE), profession="tanner"
        )
        text = self.send("yes")
        self.assertEqual(self.node(), "node_appearance")
        self.assertIn(NO_CHOICES, text)

    def test_a_stored_choice_off_the_lists_is_asked_for_again(self):
        # Shown as chosen, it would be a choice `next` then refuses.
        text = self.restart_at(
            "node_appearance", draft=dict(FIXTURE), profession="tanner",
            appearance={"sex": "female", "age": "Adult", "feature": "purple"},
        )
        self.assertIn("Chosen: sex female, age --, feature --.", text)
        self.assertIn("Still to choose: age, feature.", text)

    def test_choices_off_the_lists_are_not_written(self):
        for appearance in (
            {"sex": "female", "age": "adult"},
            dict(APPEARANCE, feature="purple"),
            dict(APPEARANCE, sex="neutral"),
            "female adult freckled",
        ):
            with self.subTest(appearance=appearance):
                text, _ = chargen_menu.node_done(
                    self.char1, "", draft=dict(FIXTURE), profession="tanner",
                    appearance=appearance,
                )
                self.assertIn("Nothing was changed", text)
                self.assertEqual(self.state(), self.before)


class TestAppearanceBeforeThePush(_MenuFixture):
    """AV5 for the facts: the panels' push already reads them (NMM24)."""

    def test_the_push_sees_the_facts(self):
        seen = []
        with mock.patch.object(
            client_state, "push",
            side_effect=lambda obj, *domains, **kw: seen.append(sdesc.facts_of(obj)),
        ):
            self.walk_to_last_confirm()
            self.send("yes")
        self.assertIs(self.char1.db.chargen_complete, True)   # receipt: node_done ran
        self.assertEqual(seen[-1], APPEARANCE)


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
        # The facts come after the grant: a half-done character has none.
        self.assertIsNone(self.state()["appearance"])

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
        self.send("back", "next", "yes", "tanner", "yes", APPEARANCE_LINE,
                  "next", "yes")
        self.assertIsNone(self.node())
        self.assertIs(self.char1.db.chargen_complete, True)
        self.assertEqual(self.state()["profession"], "tanner")
        self.assertEqual(self.state()["skills"]["craft"], (31, 31))


# ---------------------------------------------------------------------------
# Arrival (Arrival Decomposition, Task AV-T2; Newcomer Design Z1)
# ---------------------------------------------------------------------------

TEMPLE_KEY = "Old Temple"   # seed_data's key for alpha.room.temple, by hand


class _SeededMenu(_MenuFixture):
    """The menu on a seeded database: room1 stands in for Limbo, as in
    tests/test_seeding.py, and char1's home is room1 until it is made."""

    def setUp(self):
        super().setUp()
        seed_world(limbo=self.room1)
        self.temple = find_seeded(seed_data.ARRIVAL_ROOM)
        self.assertEqual(self.char1.home, self.room1)   # receipt: Limbo's stand-in

    def where(self):
        return self.char1.location, self.char1.home


class TestDoneArrives(_SeededMenu):
    """
    Pressures AV-T2's placement: arrival after the last refusal (AVM5), before
    the push (AVM6), and never for a character already made (AVM7).
    """

    def test_a_made_character_stands_in_the_temple_and_calls_it_home(self):
        self.walk_to_last_confirm()
        self.send("yes")
        self.assertIs(self.char1.db.chargen_complete, True)
        self.assertEqual(self.where(), (self.temple, self.temple))

    def test_the_push_already_sees_the_temple(self):
        # AV5: the Location panel's first real content is the temple.
        seen = []
        with mock.patch.object(
            client_state, "push",
            side_effect=lambda obj, *domains, **kw: seen.append((obj.location, domains)),
        ):
            self.walk_to_last_confirm()
            self.send("yes")
        self.assertIs(self.char1.db.chargen_complete, True)   # receipt: node_done ran
        self.assertEqual(seen[-1], (self.temple, client_state.DOMAINS))

    def test_the_temple_reads_the_newcomer_by_the_composed_description(self):
        # NM-T16's protocol in a test: a stranger in the temple sees the
        # newcomer arrive by the text just composed, and finds them by a word.
        self.char2.move_to(self.temple, quiet=True, move_hooks=False)
        heard = []
        with mock.patch.object(
            self.char2, "msg",
            side_effect=lambda text=None, *a, **kw: heard.append(
                strip_ansi(str(text[0] if isinstance(text, (tuple, list)) else text))
            ),
        ):
            self.walk_to_last_confirm()
            self.send("yes")
            found = self.char2.search("freckled")
        self.assertIn(
            "A small, freckled woman steps unsteadily out of a shadowed corner",
            "\n".join(heard),
        )
        self.assertEqual(found, self.char1)

    def test_an_unknown_profession_moves_nothing(self):
        # Not reachable through the menu's options; node_done guards it anyway.
        chargen_menu.node_done(self.char1, "", draft=dict(FIXTURE), profession="nobody")
        self.assertFalse(self.char1.db.chargen_complete)
        self.assertEqual(self.where(), (self.room1, self.room1))

    def test_an_apply_refusal_moves_nothing(self):
        self.char1.attributes.add("skill_xp", {"craft": 1})
        self.walk_to_last_confirm()
        self.assertIn("Nothing was changed", self.send("yes"))
        self.assertEqual(self.where(), (self.room1, self.room1))

    def test_a_grant_error_moves_nothing(self):
        self.walk_to_last_confirm()
        with mock.patch(
            "world.professions.grant_profession", side_effect=ValueError("boom")
        ):
            self.send("yes")
        self.assertFalse(self.char1.db.chargen_complete)
        self.assertEqual(self.where(), (self.room1, self.room1))

    def test_a_silent_grant_refusal_moves_nothing(self):
        self.walk_to_last_confirm()
        with mock.patch("world.professions.grant_profession", return_value=[]):
            self.send("yes")
        self.assertFalse(self.char1.db.chargen_complete)
        self.assertEqual(self.where(), (self.room1, self.room1))

    def test_a_character_already_made_is_not_moved(self):
        self.char1.move_to(self.room2, quiet=True, move_hooks=False)
        self.char1.db.chargen_complete = True
        self.walk_to_last_confirm()
        self.assertIn("already made", self.send("yes"))
        self.assertEqual(self.where(), (self.room2, self.room1))


class TestArrivalFirstScreen(_SeededMenu):
    """
    The shipped menu closes with `look`. With the move's hooks the temple
    would be read twice (AV4); with no move it would be the stand-in Limbo.
    """

    on_exit = "look"

    def test_the_temple_is_read_once_after_the_closing_line(self):
        self.walk_to_last_confirm()
        text = self.send("yes")
        self.assertIn("Your character is made", text)
        self.assertEqual(text.count(TEMPLE_KEY), 1)
        self.assertIn("Weathered stone pillars", text)
        self.assertLess(text.index("Your character is made"), text.index(TEMPLE_KEY))


class TestDoneUnseeded(_MenuFixture):
    """AV6: no arrival room, and the character is still made, where it stands."""

    def test_made_where_it_stands(self):
        self.walk_to_last_confirm()
        self.assertIn("Your character is made", self.send("yes"))
        self.assertIs(self.char1.db.chargen_complete, True)
        self.assertEqual((self.char1.location, self.char1.home), (self.room1, self.room1))
