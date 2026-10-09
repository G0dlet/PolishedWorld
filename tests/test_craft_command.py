"""
Unit tests for `craft` on the shared timed-action slot. Epic A, Task TA2.1.

Until TA2.1 there were no tests for `CmdCraftGated` or for a craft driven end to
end through the recipe pipeline. Everything here is new coverage, and the
classes are arranged by the question each one answers.

WHAT IS WORTH TESTING HERE
--------------------------
1. **The start schedules and nothing else.** No consume, no product, no
   cooldown stamp: the whole collect -> roll -> consume lands at completion.
2. **Completion is the contrib's own pass.** An ingredient given away during the
   wait is not found and nothing is consumed; the product appears only there.
3. **The courtesy checks refuse at start, schedule nothing, and reuse the
   contrib's own sentences** (D5, T14). The dry run must also be shown
   to touch nothing.
4. **Every interruption ends the craft with no product**: move, death, logout.
   An error at completion still empties the slot.
5. **D3 across three commands**: craft, work and rest refuse each other out
   loud and never interrupt.
6. **The middle-state invariant**: craft_duration == craft_cooldown in every
   recipe, which is what keeps the cooldown from refusing after the wait
   (T16). Deleted with craft_cooldown in TA2.2.

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
A completed craft stamps `craft:<recipe>` (do_craft) until TA2.2. Each test gets
fresh characters from the fixture, so nothing leaks between tests; no test
completes the same recipe twice. Keys are built through the recipe's own
`_cooldown_key`, so a rename cannot decouple test from code.

 THE RECIPE IS THE REAL TWINE
-------------------------------
T18. Twine has consume_policy "raw" -- every completed attempt makes an
item whatever the roll -- and no tool, knowledge or skill floor, so "a product
exists" is deterministic without mocking the dice.

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
from commands.crafting_commands import CmdCraftGated, _complete_craft
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


def _twine_key(char):
    """The cooldown key do_craft stamps, built by the recipe itself."""
    return TwineRecipe(char)._cooldown_key


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

    def test_no_cooldown_is_stamped_at_start(self):
        # do_craft stamps it. Ready here means do_craft has not run.
        self.assertIsNotNone(self.start_craft())
        self.assertTrue(self.char1.cooldowns.ready(_twine_key(self.char1)))

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
        self.assertFalse(self.char1.cooldowns.ready(_twine_key(self.char1)))

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
        self.assertTrue(self.char1.cooldowns.ready(_twine_key(self.char1)))

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

    def test_a_running_cooldown_is_refused_at_start(self):
        # The middle state (T16): visible double throttling until TA2.2.
        self.char1.cooldowns.add(_twine_key(self.char1), TwineRecipe.craft_cooldown)
        self.assert_refused(TWINE, "You must wait")

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


class TestDurationMatchesCooldown(EvenniaCommandTest):
    """
    Question 6: the middle-state invariant (T16). While both knobs exist,
    equal values are what keep the cooldown from refusing a craft after its
    wait. DELETE this class with craft_cooldown in TA2.2.
    """

    def recipe_classes(self):
        return [
            obj for obj in vars(recipes).values()
            if isinstance(obj, type)
            and issubclass(obj, MongooseCraftRecipe)
            and obj is not MongooseCraftRecipe
        ]

    def test_every_recipe_waits_exactly_as_long_as_its_cooldown(self):
        classes = self.recipe_classes()
        self.assertTrue(classes)  # "all of them" over nothing proves nothing
        for cls in classes:
            with self.subTest(recipe=cls.name):
                self.assertGreater(cls.craft_duration, 0)
                self.assertEqual(cls.craft_duration, cls.craft_cooldown)

    def test_the_base_default_is_thirty_for_both(self):
        self.assertEqual(MongooseCraftRecipe.craft_duration, 30)
        self.assertEqual(MongooseCraftRecipe.craft_cooldown, 30)
