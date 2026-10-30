"""
Unit tests for `craft` on the shared timed-action slot. Epic A, Tasks TA2.1
and TA2.2.

Until TA2.1 there were no tests for `CmdCraftGated` or for a craft driven end to
end through the recipe pipeline. Everything here is new coverage, and the
classes are arranged by the question each one answers.

WHAT IS WORTH TESTING HERE
--------------------------
1. **The start schedules and nothing else.** No consume, no product, no
   do_craft: the whole collect -> roll -> consume lands at completion.
2. **Completion is the contrib's own pass.** An ingredient given away during the
   wait is not found and nothing is consumed; the product appears only there.
3. **The courtesy checks refuse at start, schedule nothing, and reuse the
   contrib's own sentences** (D5, T14). The dry run must also be shown
   to touch nothing.
4. **Every interruption ends the craft with no product**: move, death, logout.
   An error at completion still empties the slot.
5. **D3 across three commands**: craft, work and rest refuse each other out
   loud and never interrupt, and each one's help says so (T24).
6. **One knob** (D4, TA2.2). The same recipe starts again straight after it
   finished, a completed craft writes no cooldown but the skill-improvement
   window, every recipe takes a positive time, and nothing defines
   craft_cooldown any more.

 THE COMPLETION IS DRIVEN BY HAND
------------------------------------
`delay` is patched WHERE IT IS CONSUMED -- `world.timed_actions.delay` -- so no
real task is queued and the scheduled call can be read back. The completion is
then run by calling the captured callback with the captured arguments, i.e.
the real `_complete_craft`, the real Command instance and the real marker. A
fabricated marker would make every "stale completion is refused" test pass with
the identity check deleted.

 COOLDOWNS
-------------
Crafting stamps none since TA2.2. The one cooldown a completed craft can still
write is the skill-improvement window, `improve_craft`, stamped on a successful
roll when its window is open -- so whether it appears depends on the dice. The
test that guards this therefore compares every key before and after the
completion and allows exactly that one, rather than demanding no write at all.

 THE RECIPE IS THE REAL TWINE
-------------------------------
T18. Twine has consume_policy "raw" -- every completed attempt makes an
item whatever the roll -- and no tool, knowledge or skill floor, so "a product
exists" is deterministic without mocking the dice.

MASTERY (Recipe Mastery M2.1)
-----------------------------
`TestMasteryCounting` drives the real command and completion with the roll
pinned (`world.skillcheck.randint`, as tests/test_cloth_goods.py does). Twine's
"raw" policy is the point: a failure and a fumble still make twine, so those two
tests prove the count is gated on the check, not on the produce branch (RM6).
Counts of 4, 5, 19 and 24 are reached with `add`, then one real craft crosses
the boundary -- only that last craft goes through `do_craft`. The weight-ceiling
case lives in tests/test_set_down.py::TestCraftSetsDown, beside its fixture
(importing that fixture here would make the two modules import each other).

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_craft_command
"""

from unittest import mock

from django.test import override_settings

from evennia.contrib.game_systems.crafting.crafting import CmdCraft
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest

from commands import crafting_commands
from commands.consumption_commands import CmdRest
from commands.crafting_commands import CmdCraftGated, CmdScribe, _complete_craft
from commands.work_commands import CmdWork, _finish_task
from world import recipes, timed_actions
from world.crafting_base import MongooseCraftRecipe
from world.recipes import ClothRecipe, TwineRecipe

from tests.test_work_command import WorkTestBase, _marker_of, captured_messages


TWINE = "twine from fiber-1, fiber-2, fiber-3"
TIRED = 50  # as in tests/test_rest.py: below full, so `rest` reaches start()
INTERRUPT_MSG = "You set your crafting aside; your materials are untouched."


def _joined(seen):
    return "\n".join(seen)


class CraftFixtureMixin:
    """Three plant fibres in a character's inventory; start and finish by hand."""

    def give_fibres(self, char):
        fibres = spawn("plant_fiber", "plant_fiber", "plant_fiber")
        for obj in fibres:
            obj.location = char
        return fibres

    def twine_in(self, char):
        return [obj for obj in char.contents if obj.db.recipe == "twine"]

    def start_craft(self, args=TWINE, caller=None):
        """
        Run the real command with `delay` patched where start() consumes it.

        Returns:
            mock.call or None: the scheduled call, or None if nothing was.
        """
        caller = caller or self.char1
        with mock.patch("world.timed_actions.delay") as scheduled:
            self.call(CmdCraftGated(), args, caller=caller)
        return scheduled.call_args if scheduled.called else None

    def finish(self, scheduled):
        """Fire the captured completion: callback(char, cmd, marker)."""
        _seconds, callback, *args = scheduled.args
        callback(*args)


class CraftTestBase(CraftFixtureMixin, EvenniaCommandTest):
    """char1 holding three fibres in room1; char2 listening in room1."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.fibres = self.give_fibres(self.char1)


class TestStartSchedulesOnly(CraftTestBase):
    """Question 1: does starting a craft do anything but occupy the slot?"""

    def test_start_schedules_the_completion_with_the_recipes_duration(self):
        scheduled = self.start_craft()
        self.assertIsNotNone(scheduled)
        seconds, callback, char, cmd, marker = scheduled.args
        self.assertEqual(seconds, TwineRecipe.craft_duration)
        self.assertIs(callback, _complete_craft)
        self.assertIs(char, self.char1)
        self.assertIsInstance(cmd, CmdCraftGated)
        self.assertIs(marker, _marker_of(self.char1))

    def test_the_slot_holds_a_craft_with_no_room_hook(self):
        self.start_craft()
        record = timed_actions.is_busy(self.char1)
        self.assertIsNotNone(record)
        self.assertEqual(record.key, "craft")
        self.assertEqual(record.label, "crafting")
        self.assertEqual(record.interrupt_msg, INTERRUPT_MSG)
        self.assertIsNone(record.on_interrupt)

    def test_nothing_is_consumed_or_made_at_start(self):
        self.assertIsNotNone(self.start_craft())  # receipt: a craft did start
        for obj in self.fibres:
            self.assertIsNotNone(obj.pk)
            self.assertEqual(obj.location, self.char1)
        self.assertEqual(self.twine_in(self.char1), [])

    def test_the_crafter_is_told_and_the_room_sees_the_act_not_the_recipe(self):
        with captured_messages(self.char2) as room:
            with mock.patch("world.timed_actions.delay"):
                self.call(
                    CmdCraftGated(), TWINE, "You set to work on twine.", caller=self.char1
                )
        joined = _joined(room)
        self.assertIn(f"{self.char1.key} begins to craft something.", joined)
        self.assertNotIn("twine", joined)


class TestCompletion(CraftTestBase):
    """Question 2: is the completion the contrib's own pass, in one tick?"""

    def test_completion_makes_twine_consumes_fibres_and_empties_the_slot(self):
        scheduled = self.start_craft()
        self.finish(scheduled)
        self.assertEqual(len(self.twine_in(self.char1)), 1)
        for obj in self.fibres:
            self.assertIsNone(obj.pk)
        self.assertIsNone(timed_actions.is_busy(self.char1))

    def test_an_ingredient_gone_during_the_wait_fails_and_consumes_nothing(self):
        scheduled = self.start_craft()
        gone = self.fibres[2]
        gone.location = self.room1  # dropped, given, bartered -- gone from the pack
        with captured_messages(self.char1) as seen:
            self.finish(scheduled)
        self.assertIn("Could not find 'fiber-3'.", _joined(seen))
        for obj in self.fibres:
            self.assertIsNotNone(obj.pk)
        self.assertEqual(self.twine_in(self.char1), [])
        self.assertIsNone(timed_actions.is_busy(self.char1))

    def test_an_error_at_completion_is_logged_told_and_frees_the_slot(self):
        scheduled = self.start_craft()
        with mock.patch.object(CmdCraft, "func", side_effect=RuntimeError("boom")), \
                mock.patch.object(crafting_commands.logger, "log_trace") as logged, \
                captured_messages(self.char1) as seen:
            self.finish(scheduled)
        logged.assert_called_once()
        self.assertIn("Something went wrong as you finished your crafting.", _joined(seen))
        self.assertIsNone(timed_actions.is_busy(self.char1))


class TestCourtesyRefusesAtStart(CraftTestBase):
    """
    Question 3: are the refusals the contrib would give at completion given at
    start instead, in the same words, with nothing scheduled?
    """

    def assert_refused(self, args, expected):
        with mock.patch("world.timed_actions.delay") as scheduled:
            returned = self.call(CmdCraftGated(), args, caller=self.char1)
        self.assertIn(expected, returned)
        scheduled.assert_not_called()
        self.assertIsNone(timed_actions.is_busy(self.char1))
        for obj in self.fibres:
            self.assertIsNotNone(obj.pk)

    def test_no_from_clause_gets_the_usage_line(self):
        # parse() leaves self.recipe empty without "from"/"using".
        self.assert_refused("twine", "Usage: craft <recipe>")

    def test_an_unknown_recipe_gets_the_contribs_answer(self):
        self.assert_refused("frobnicate from fiber-1", "Unknown recipe 'frobnicate'")

    def test_a_missing_ingredient_name_gets_the_search_answer(self):
        self.assert_refused("twine from fiber-1, fiber-2, rock", "Could not find 'rock'.")

    def test_too_few_ingredients_get_the_validation_answer(self):
        self.assert_refused("twine from fiber-1, fiber-2", "Could not craft twine without")

    def test_a_skill_floor_is_refused_at_start(self):
        with mock.patch.object(TwineRecipe, "min_skill", 999):
            self.assert_refused(TWINE, "Your Craft is too unskilled (need 999%).")

    def test_an_unlearned_recipe_is_refused_before_any_search(self):
        # B.2's point survives the split: the knowledge reject runs before the
        # courtesy search, so the inventory is never searched.
        self.assertTrue(ClothRecipe.requires_knowledge)
        with mock.patch.object(type(self.char1), "search") as searched:
            self.assert_refused("cloth from fiber-1", "You don't know how to make that.")
        searched.assert_not_called()


class TestTheDryRunTouchesNothing(CraftTestBase):
    """Question 3b: pre_craft at start runs, and nothing past it does."""

    def test_pre_craft_runs_once_and_do_craft_and_post_craft_never(self):
        real_pre_craft = TwineRecipe.pre_craft
        with mock.patch.object(
            TwineRecipe, "pre_craft", autospec=True, side_effect=real_pre_craft
        ) as pre, mock.patch.object(TwineRecipe, "do_craft") as do, \
                mock.patch.object(TwineRecipe, "post_craft") as post:
            self.assertIsNotNone(self.start_craft())
        pre.assert_called_once()  # receipt: the dry run happened
        do.assert_not_called()
        post.assert_not_called()


class TestEveryEndEmptiesTheSlot(CraftTestBase):
    """Question 4: move, death and logout end the craft with no product."""

    def test_moving_tells_the_crafter_and_the_completion_then_does_nothing(self):
        scheduled = self.start_craft()
        with captured_messages(self.char1) as seen:
            self.char1.move_to(self.room2, quiet=True)
        self.assertIn(INTERRUPT_MSG, _joined(seen))
        self.assertIsNone(timed_actions.is_busy(self.char1))

        with captured_messages(self.char1) as later:
            self.finish(scheduled)
        self.assertEqual(later, [])
        self.assertEqual(self.twine_in(self.char1), [])
        for obj in self.fibres:
            self.assertIsNotNone(obj.pk)

    def test_death_ends_the_craft_audibly_and_first(self):
        scheduled = self.start_craft()
        with captured_messages(self.char1) as seen:
            self.char1.at_character_death()
        lines = [line for line in seen if INTERRUPT_MSG in line or "You have died." in line]
        self.assertEqual(len(lines), 2, seen)
        self.assertIn(INTERRUPT_MSG, lines[0])
        self.assertIn("You have died.", lines[1])
        self.assertIsNone(timed_actions.is_busy(self.char1))

        self.finish(scheduled)
        self.assertEqual(self.twine_in(self.char1), [])

    def test_an_unpuppeted_crafter_gets_nothing_at_completion(self):
        # char2 has an account but no session: the statue-logout state.
        self.assertFalse(self.char2.has_account)
        fibres = self.give_fibres(self.char2)
        scheduled = self.start_craft(caller=self.char2)
        self.assertIsNotNone(scheduled)  # receipt: the craft did begin

        self.finish(scheduled)
        self.assertEqual(self.twine_in(self.char2), [])
        for obj in fibres:
            self.assertIsNotNone(obj.pk)
        self.assertIsNone(timed_actions.is_busy(self.char2))


class TestCraftWorkAndRestExcludeEachOther(CraftFixtureMixin, WorkTestBase):
    """
    Question 5: D3 across three commands -- refused out loud, never interrupted.

    WorkTestBase gives a funded temple; the Treasury setting is pointed at it as
    tests/test_rest.py does. Fatigue is lowered so `rest` gets past its own
    "You are not tired." gate and reaches start().
    """

    def setUp(self):
        super().setUp()
        self.settings_override = override_settings(TREASURY_DBREF=self.treasury.dbref)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.fatigue = self.char1.traits.get("fatigue")
        self.fatigue.current = TIRED  # bypasses the survival ticker
        self.fibres = self.give_fibres(self.char1)

    def test_work_during_a_craft_is_refused_and_the_craft_still_completes(self):
        scheduled = self.start_craft()
        craft = _marker_of(self.char1)
        self.call(CmdWork(), "sweep", "You are already crafting.", caller=self.char1)
        self.assertIs(_marker_of(self.char1), craft)
        self.finish(scheduled)
        self.assertEqual(len(self.twine_in(self.char1)), 1)

    def test_rest_during_a_craft_is_refused_and_does_not_interrupt_it(self):
        scheduled = self.start_craft()
        craft = _marker_of(self.char1)
        returned = self.call(CmdRest(), "", "You are already crafting.", caller=self.char1)
        self.assertNotIn("settle", returned)
        self.assertIs(_marker_of(self.char1), craft)
        self.finish(scheduled)
        self.assertEqual(len(self.twine_in(self.char1)), 1)

    def test_craft_during_a_chore_is_refused_and_the_chore_still_pays(self):
        self.call(CmdWork(), "sweep", caller=self.char1)
        chore = _marker_of(self.char1)
        with mock.patch("world.timed_actions.delay") as scheduled:
            self.call(CmdCraftGated(), TWINE, "You are already working.", caller=self.char1)
        scheduled.assert_not_called()
        self.assertIs(_marker_of(self.char1), chore)
        _finish_task(self.char1, "sweep", chore)
        self.assertEqual(self.char1.currency.value, 25)

    def test_craft_during_a_craft_is_refused_and_schedules_nothing(self):
        self.assertIsNotNone(self.start_craft())
        craft = _marker_of(self.char1)
        with mock.patch("world.timed_actions.delay") as scheduled:
            self.call(CmdCraftGated(), TWINE, "You are already crafting.", caller=self.char1)
        scheduled.assert_not_called()
        self.assertIs(_marker_of(self.char1), craft)

    def test_craft_during_a_rest_is_refused_and_the_rest_goes_on(self):
        # The sixth pairing: the other five are above and in tests/test_rest.py.
        # It had no test of its own, and `help craft` now says it cannot happen.
        with mock.patch("world.timed_actions.delay"):
            self.call(CmdRest(), "", "You settle down to rest.", caller=self.char1)
        rest = _marker_of(self.char1)
        self.assertEqual(timed_actions.is_busy(self.char1).key, "rest")
        with mock.patch("world.timed_actions.delay") as scheduled:
            self.call(CmdCraftGated(), TWINE, "You are already resting.", caller=self.char1)
        scheduled.assert_not_called()
        self.assertIs(_marker_of(self.char1), rest)


class TestHelpStatesTheRule(EvenniaCommandTest):
    """
    Question 5, for the player (T24): each command on the shared slot says in
    its own help that craft, work and rest cannot run side by side.

    The text is read through `get_help()`, the method `help <command>` calls
    (Evennia v6.1.0 `Command.get_help` returns `self.__doc__`), so an override
    that builds help some other way is still checked. Whitespace is normalised
    because each docstring wraps the sentence at a different place: what is
    tested is what the player reads, not where the lines break. Whether
    `help craft` reaches CmdCraftGated rather than the contrib's stock CmdCraft
    is a cmdset question, and the in-game protocol checks it.

    A fourth consumer of `timed_actions.start()` changes RULE and joins
    COMMANDS.
    """

    RULE = (
        "Crafting, working and resting each take time, and you can only be "
        "doing one of them at once."
    )
    COMMANDS = (CmdCraftGated, CmdWork, CmdRest)

    def test_each_slot_command_states_the_rule_exactly_once(self):
        self.assertEqual(len(self.COMMANDS), 3)
        for cmdclass in self.COMMANDS:
            with self.subTest(command=cmdclass.__name__):
                shown = " ".join(cmdclass().get_help(self.char1, None).split())
                self.assertEqual(shown.count(self.RULE), 1)


class TestNothingThrottlesARepeat(CraftTestBase):
    """
    Question 6: with craft_cooldown gone (D4, TA2.2), does anything but the
    wait itself stand between one craft and the next?
    """

    def test_the_same_recipe_starts_again_straight_after_it_finished(self):
        self.finish(self.start_craft())
        self.assertEqual(len(self.twine_in(self.char1)), 1)  # receipt: do_craft ran
        self.give_fibres(self.char1)
        self.assertIsNotNone(self.start_craft())

    def test_a_completed_craft_writes_no_cooldown_but_the_skill_window(self):
        # Every key, before and after: catches a stamp under any name and
        # through any method of the handler, not just add() of `craft:*`.
        before = set(self.char1.cooldowns.all)
        self.finish(self.start_craft())
        self.assertEqual(len(self.twine_in(self.char1)), 1)  # receipt: do_craft ran
        written = set(self.char1.cooldowns.all) - before
        self.assertLessEqual(written, {"improve_craft"}, written)


class TestOneKnob(EvenniaCommandTest):
    """
    Question 6b: is craft_duration the only time knob (D4)? A recipe that
    still defined craft_cooldown would carry an attribute nothing reads --
    silent in play, so only a test can catch it. AGENTS.md section 4 tells the
    data agent this test exists.
    """

    def recipe_classes(self):
        return [
            obj for obj in vars(recipes).values()
            if isinstance(obj, type)
            and issubclass(obj, MongooseCraftRecipe)
            and obj is not MongooseCraftRecipe
        ]

    def test_every_recipe_takes_a_positive_time(self):
        classes = self.recipe_classes()
        self.assertTrue(classes)  # "all of them" over nothing proves nothing
        for cls in classes:
            with self.subTest(recipe=cls.name):
                self.assertGreater(cls.craft_duration, 0)

    def test_neither_the_base_nor_any_recipe_defines_craft_cooldown(self):
        classes = self.recipe_classes()
        self.assertTrue(classes)
        for cls in [MongooseCraftRecipe, *classes]:
            with self.subTest(recipe=cls.name):
                self.assertFalse(hasattr(cls, "craft_cooldown"))


ROLL = "world.skillcheck.randint"
# At craft 60 with twine (no tool, no floor): crit band is ceil(60/10) = 6.
CRITICAL_ROLL, SUCCESS_ROLL, FAILURE_ROLL, FUMBLE_ROLL = 1, 30, 90, 100
STEP_LINE = "Your hands know this recipe a little better."
CAP_LINE = "You could make this in your sleep."


class TestMasteryCounting(CraftTestBase):
    """
    M2.1: do_craft is the single writer, gated on a successful check.

    The bugs this presses on, one per test group: counting on the produce
    branch, which "raw" always takes (RM6); writing at the command instead of
    at completion (RM8); speaking on every success (RM9); and speaking again
    past the cap, where the modifier no longer moves (RM11).
    """

    def setUp(self):
        super().setUp()
        self.char1.skills.get("craft").current = 60

    def craft(self, roll, fresh_fibres=False):
        """One real craft through the command and its completion, roll pinned."""
        if fresh_fibres:
            self.give_fibres(self.char1)
        scheduled = self.start_craft()
        self.assertIsNotNone(scheduled, "the craft never started")
        with mock.patch(ROLL, return_value=roll), captured_messages(self.char1) as seen:
            self.finish(scheduled)
        return _joined(seen)

    def count(self):
        return self.char1.recipe_mastery.count("twine")

    def test_a_success_counts_one(self):
        self.craft(SUCCESS_ROLL)
        self.assertEqual(self.count(), 1)

    def test_a_critical_counts_and_a_second_craft_reads_two(self):
        self.craft(CRITICAL_ROLL)
        self.assertEqual(self.count(), 1)
        self.craft(SUCCESS_ROLL, fresh_fibres=True)
        self.assertEqual(self.count(), 2)

    def test_a_failure_yields_twine_and_never_counts(self):
        self.craft(FAILURE_ROLL)
        self.assertEqual(len(self.twine_in(self.char1)), 1)   # "raw": it still yields
        self.assertEqual(self.count(), 0)
        self.assertFalse(self.char1.attributes.has("recipe_mastery"))

    def test_a_fumble_yields_twine_and_never_counts(self):
        self.craft(FUMBLE_ROLL)
        self.assertEqual(len(self.twine_in(self.char1)), 1)
        self.assertEqual(self.count(), 0)

    def test_the_fifth_success_says_the_step_line_once(self):
        self.char1.recipe_mastery.add("twine", 4)
        said = self.craft(SUCCESS_ROLL)
        self.assertEqual(self.count(), 5)
        self.assertEqual(said.count(STEP_LINE), 1)
        self.assertNotIn(CAP_LINE, said)

    def test_the_sixth_success_is_silent(self):
        self.char1.recipe_mastery.add("twine", 5)
        said = self.craft(SUCCESS_ROLL)
        self.assertEqual(self.count(), 6)
        self.assertNotIn(STEP_LINE, said)

    def test_the_twentieth_says_the_cap_line(self):
        self.char1.recipe_mastery.add("twine", 19)
        said = self.craft(SUCCESS_ROLL)
        self.assertEqual(self.count(), 20)
        self.assertIn(CAP_LINE, said)
        self.assertNotIn(STEP_LINE, said)

    def test_a_step_past_the_cap_is_silent(self):
        # 24 -> 25 raises the step from 4 to 5 but not the modifier (20 -> 20).
        self.char1.recipe_mastery.add("twine", 24)
        said = self.craft(SUCCESS_ROLL)
        self.assertEqual(self.count(), 25)
        self.assertNotIn(CAP_LINE, said)
        self.assertNotIn(STEP_LINE, said)

    def test_a_timed_craft_counts_at_completion_not_at_the_command(self):
        scheduled = self.start_craft()
        self.assertEqual(self.count(), 0)
        with mock.patch(ROLL, return_value=SUCCESS_ROLL):
            self.finish(scheduled)
        self.assertEqual(self.count(), 1)

    def test_scribing_a_book_counts_nothing(self):
        # MD2: only do_craft writes. Scribe rolls its own check (and succeeds
        # here, which the bound book receipts), but no recipe gains a count.
        self.char1.learn_recipe("cloth")
        for obj in spawn("cloth", "cloth", "twine"):
            obj.location = self.char1
        with mock.patch(ROLL, return_value=SUCCESS_ROLL):
            said = self.call(CmdScribe(), "cloth", caller=self.char1)
        self.assertIn("You bind a book", said)
        self.assertFalse(self.char1.attributes.has("recipe_mastery"))

    def test_a_crafter_without_the_handler_neither_counts_nor_errors(self):
        # obj1 is a plain Object: no recipe_mastery, no skills. Roll 1 is a
        # critical at any target, so the success branch is reached.
        recipe = TwineRecipe(self.obj1, *self.fibres)
        recipe.pre_craft()
        with mock.patch(ROLL, return_value=CRITICAL_ROLL):
            result = recipe.do_craft()
        self.assertTrue(recipe.skill_outcome["success"])   # receipt: the gate was reached
        self.assertTrue(result)
        self.assertIsNone(recipe.mastery_step)
        self.assertFalse(self.obj1.attributes.has("recipe_mastery"))
