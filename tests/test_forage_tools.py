"""
Unit tests for tool-gated foraging. Alpha content epic, Task AC2.1.

A ResourceNode may name a `required_tool` (a crafting_tool tag-key). `forage`
then refuses anyone not carrying a usable tool with that tag, and wears the
tool by FORAGE_TOOL_WEAR on each successful forage. These are also the first
tests `forage` has ever had, so the no-tool path is pinned as a regression.

WHAT IS WORTH TESTING HERE
--------------------------
1. **A refusal claims nothing.** The check runs before `node.harvest(1)`, so a
   refused forage leaves the node's stock, the inventory and the cooldown as
   they were. A check moved below the harvest would eat a unit per refusal.
2. **"Usable" means what it means at the bench.** Tag in `crafting_tool`, not
   broken, carried. A broken axe, a knife, and an axe lying on the floor are
   all refused (`_usable_tool` mirrors `MongooseCraftRecipe._used_tool()`).
3. **Wear is exact and tied to a yield.** One forage wears the axe by exactly
   FORAGE_TOOL_WEAR; a forage whose spawn fails is refunded and wears nothing
   (the refund class -- the receipt for the mutation "wear above the spawn").
4. **Breaking is not deleting.** The use that takes the axe to 0 says so, and
   the axe stays in the inventory, broken, and is refused next time.
5. **No `required_tool`, no change.** A node without one forages as before,
   and never wears a carried tool.

⚠️ RECEIPTS
-----------
Every "nothing changed" assertion is paired with the message that proves the
command ran (the refusal text, or the spawn-failure text). Without it, a test
whose command silently did nothing would pass every "unchanged" assertion.

⚠️ DISPLAY NAMES
-----------------
char1 has builder-level permissions in the stock fixture, so
`get_display_name(char1)` may append a dbref. Expected messages are therefore
prefixes that stop before the name's end (`.call()` matches with
`startswith`), or `assertIn` against the returned output.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_forage_tools
"""

from unittest import mock

from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest

from commands.foraging_commands import (
    FORAGE_TOOL_WEAR,
    TOOL_TAG_CATEGORY,
    CmdForage,
)
from world.crafting_base import MongooseCraftRecipe


STOCK = 6  # node starts full; regen over a test's runtime is 0 at 1800 game-s/unit
REFUSAL = "You need an axe to gather from the test tree"
SPAWN_FAILED = "You reach out, but something goes wrong"


class ForageToolBase(EvenniaCommandTest):
    """char1 in room1 with a 'test tree' that needs an axe and yields sticks."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.node = self.make_node("test tree", required_tool="axe")

    def make_node(self, key, required_tool=None):
        node = create.create_object(
            "typeclasses.resources.ResourceNode", key=key, location=self.room1
        )
        node.yield_prototype = "stick"
        node.max_yield = STOCK
        node.available = STOCK
        if required_tool:
            node.required_tool = required_tool
        return node

    def make_tool(self, key="test axe", tag="axe", location=None, condition=None):
        tool = create.create_object(
            "typeclasses.tools.Tool",
            key=key,
            location=location or self.char1,
            tags=[(tag, TOOL_TAG_CATEGORY)],
        )
        if condition is not None:
            tool.condition = condition
        return tool

    def forage(self, target="test tree", msg=None):
        return self.call(CmdForage(), target, msg, caller=self.char1)

    def sticks(self):
        return [
            o for o in self.char1.contents
            if o.tags.has("stick", category="crafting_material")
        ]

    def assert_nothing_claimed(self):
        self.assertEqual(self.node.get_available(), STOCK)
        self.assertEqual(self.sticks(), [])
        self.assertTrue(self.char1.cooldowns.ready("forage"))


class TestRefusalClaimsNothing(ForageToolBase):
    """Point 1 and 2: every unusable case is refused, and refusal is free."""

    def test_no_tool_is_refused(self):
        self.forage(msg=REFUSAL)
        self.assert_nothing_claimed()

    def test_broken_axe_is_refused(self):
        axe = self.make_tool(condition=0)
        self.forage(msg=REFUSAL)
        self.assert_nothing_claimed()
        self.assertEqual(axe.condition, 0)

    def test_tool_with_another_tag_is_refused(self):
        knife = self.make_tool(key="test knife", tag="knife")
        self.forage(msg=REFUSAL)
        self.assert_nothing_claimed()
        self.assertEqual(knife.condition, 100)

    def test_axe_on_the_floor_is_refused(self):
        # @spawn drops objects in the room: an axe not picked up does not count.
        axe = self.make_tool(location=self.room1)
        self.forage(msg=REFUSAL)
        self.assert_nothing_claimed()
        self.assertEqual(axe.condition, 100)


class TestUsableAxeIsWorn(ForageToolBase):
    """Point 3: a successful forage takes one unit and wears exactly once."""

    def test_forage_yields_one_stick_and_wears_the_axe(self):
        axe = self.make_tool()
        self.forage(msg="You forage")
        self.assertEqual(self.node.get_available(), STOCK - 1)
        self.assertEqual(len(self.sticks()), 1)
        self.assertEqual(axe.condition, 100 - FORAGE_TOOL_WEAR)
        self.assertFalse(self.char1.cooldowns.ready("forage"))


class TestSpawnFailureIsRefundedAndUnworn(ForageToolBase):
    """Point 3: no yield, no wear. Catches wear moved above the spawn."""

    def test_failed_spawn_refunds_the_node_and_leaves_the_axe(self):
        axe = self.make_tool()
        with mock.patch(
            "commands.foraging_commands.spawn", side_effect=RuntimeError("test")
        ), mock.patch("commands.foraging_commands.logger.log_trace"):
            self.forage(msg=SPAWN_FAILED)
        self.assert_nothing_claimed()
        self.assertEqual(axe.condition, 100)


class TestLastUseBreaksTheAxe(ForageToolBase):
    """Point 4: the breaking use says so, keeps the axe, and the next is refused."""

    def test_axe_breaks_stays_carried_and_is_then_refused(self):
        axe = self.make_tool(condition=FORAGE_TOOL_WEAR)
        output = self.forage(msg="You forage")
        self.assertIn("breaks under the work", output)
        self.assertEqual(axe.condition, 0)
        self.assertTrue(axe.is_broken)
        self.assertIsNotNone(axe.pk)
        self.assertEqual(axe.location, self.char1)

        self.char1.cooldowns.reset("forage")
        self.forage(msg=REFUSAL)
        self.assertEqual(self.node.get_available(), STOCK - 1)

    def test_a_use_that_does_not_break_says_nothing_about_it(self):
        self.make_tool(condition=FORAGE_TOOL_WEAR + 1)
        output = self.forage(msg="You forage")
        self.assertNotIn("breaks", output)


class TestNodeWithoutRequiredTool(ForageToolBase):
    """Point 5: the regression -- forage as it was before AC2.1."""

    def setUp(self):
        super().setUp()
        self.node.delete()
        self.node = self.make_node("test tree")

    def test_forage_needs_no_tool(self):
        self.forage(msg="You forage")
        self.assertEqual(self.node.get_available(), STOCK - 1)
        self.assertEqual(len(self.sticks()), 1)

    def test_carried_axe_is_not_worn(self):
        axe = self.make_tool()
        self.forage(msg="You forage")
        self.assertEqual(axe.condition, 100)


class TestToolVocabularyMatchesCrafting(EvenniaCommandTest):
    """`forage` and the bench must agree on what tags a tool."""

    def test_tag_category_is_the_crafting_contribs(self):
        self.assertEqual(TOOL_TAG_CATEGORY, MongooseCraftRecipe.tool_tag_category)
