"""
Tests for W5.1: every product site sets the surplus down at the ceiling.

Weight and Encumbrance, Task W5.1 (docs/PolishedWorld_Weight_Decomposition.md,
Rev 9 Q0-Q6). Five sites make a new object for a character -- craft, forage,
harvest, inscribe, scribe -- and all five deliver it through
`Character.receive_or_set_down`: into the hands through `move_to`, so the
ceiling hook (W2.1) runs, or into the room when it refuses.

WHAT EACH CLASS PUTS PRESSURE ON
--------------------------------
* TestReceiveOrSetDown -- the method itself: the refusal is silent (enc_quiet),
  the refused object lands in the room and not at `location` None, a batch
  fills in order, and a character with no location keeps the object (Q6).
* TestCraftSetsDown -- through the command, never the recipe alone (Q3): the
  contrib's CmdCraft.func moves every object `craft()` returns into the
  inventory (crafting.py:1096-1098), so a recipe-only test passes while the
  contrib carries the product back. Also the order inside post_craft: inputs
  are consumed BEFORE the product arrives, so an ENC-neutral craft at the
  ceiling keeps its product (the waterskin test).
* TestForageSetsDown -- the yield exists, so the node stays decremented and the
  cooldown is set even though the stone is on the floor.
* TestHarvestSetsDownPartWay -- a batch refused part-way: the counted surplus
  is in the room, the rest in hand, and "You harvest 6 ..." stays true.
* TestInscribeSetsDown, TestScribeSetsDown -- inputs consumed, product on the
  floor, one line.

Every set-down asserts the caller's lines: the site's own result line, then
exactly one set-down line, and no "You cannot carry any more." Below the
ceiling the existing tests of each site are the regression.

THE FIXTURE
-----------
The default character's limit is 20 (STR 10 + SIZ 10), so the ceiling is 40.
A load is created directly in the character (`create_object(location=...)`
runs no pre-receive hook), which also lets a test start ABOVE the ceiling --
the state a drained STR leaves behind. Rolls are pinned with
`world.skillcheck.randint` to a plain success.
"""

from contextlib import contextmanager
from unittest import mock

from evennia import create_object
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.crafting_commands import CmdCraftGated, CmdInscribe, CmdScribe
from commands.foraging_commands import CmdForage
from commands.hunting_commands import CmdHarvest
from tests.test_craft_command import CraftFixtureMixin
from world.encumbrance import OVERLOAD_FACTOR, carried_enc, enc_limit

CHARACTER = "typeclasses.characters.Character"
ROOM = "typeclasses.rooms.Room"
OBJ = "typeclasses.objects.Object"
CORPSE = "typeclasses.corpse.Corpse"
NODE = "typeclasses.resources.ResourceNode"
WARN = "typeclasses.characters.logger.log_warn"
RNG = "world.skillcheck.randint"

LIMIT = 20
CEILING = OVERLOAD_FACTOR * LIMIT   # 40
PLAIN_SUCCESS = 30   # succeeds at every target here, no critical, no fumble
REFUSED = "You cannot carry any more."
SET_DOWN = "; you set "   # both forms: "... set it down." / "... set them down."


@contextmanager
def said(char):
    """
    Collect the text of every line `char.msg()` receives inside the block.

    Like tests/test_work_command.captured_messages, but a recipe's msg sends
    `(text, {"type": "crafting"})` -- the text is the tuple's first element.
    """
    seen = []

    def collect(text="", *args, **kwargs):
        seen.append(str(text[0] if isinstance(text, tuple) else text))

    original = char.msg
    char.msg = collect
    try:
        yield seen
    finally:
        char.msg = original


def _make(location, key="thing", enc=None):
    obj = create_object(OBJ, key=key, location=location)
    if enc is not None:
        obj.db.enc = enc
    return obj


class _CeilingFixture:
    character_typeclass = CHARACTER
    room_typeclass = ROOM

    def load_to(self, total, zeros=0):
        """
        Give char1 one load of `total` ENC and `zeros` items at enc 0.

        Asserts the sum and the limit, so a test's arithmetic is checked
        before it is relied on.
        """
        _make(self.char1, key="sdload", enc=total)
        for i in range(zeros):
            _make(self.char1, key=f"sdpebble{i}", enc=0)
        self.assertEqual(
            (carried_enc(self.char1), enc_limit(self.char1)),
            (total + zeros // 20, LIMIT),
        )

    def assert_one_set_down_after(self, lines, result_marker, set_down_line):
        """The result line, then exactly one set-down line, and no refusal."""
        downs = [i for i, line in enumerate(lines) if SET_DOWN in line]
        self.assertEqual(
            [lines[i] for i in downs], [set_down_line], f"lines were: {lines!r}"
        )
        result = next(
            i for i, line in enumerate(lines) if result_marker in line and SET_DOWN not in line
        )
        self.assertLess(result, downs[0])
        self.assertNotIn(REFUSED, "\n".join(lines))

    def held(self, pred):
        return [o for o in self.char1.contents if pred(o)]

    def on_floor(self, pred):
        return [o for o in self.room1.contents if pred(o)]


# ---------------------------------------------------------------- the method


class TestReceiveOrSetDown(_CeilingFixture, EvenniaTest):
    """The one way a product reaches its maker (Q1, Q2, Q6)."""

    def fresh(self, key="sdthing", enc=1):
        """An object at location None, as spawn() leaves a product."""
        obj = _make(None, key=key, enc=enc)
        self.assertIsNone(obj.location)
        return obj

    def test_below_the_ceiling_it_is_taken(self):
        self.load_to(CEILING - 1)
        obj = self.fresh()
        self.assertEqual(self.char1.receive_or_set_down([obj]), [])
        self.assertEqual(obj.location, self.char1)

    def test_above_the_ceiling_it_is_set_down_silently(self):
        self.load_to(CEILING)
        obj = self.fresh()
        with said(self.char1) as seen:
            set_down = self.char1.receive_or_set_down([obj])
        self.assertEqual(set_down, [obj])
        self.assertEqual(obj.location, self.room1)
        # enc_quiet: the hook refused, said nothing, flagged nothing.
        self.assertNotIn(REFUSED, "\n".join(seen))
        self.assertFalse(self.char1.ndb._enc_refused)

    def test_a_batch_fills_in_order_then_sets_down(self):
        self.load_to(CEILING - 2)
        first, second, third = (self.fresh(key=f"sdpart{i}") for i in range(3))
        set_down = self.char1.receive_or_set_down([first, second, third])
        self.assertEqual(set_down, [third])
        self.assertEqual(
            [o.location for o in (first, second, third)],
            [self.char1, self.char1, self.room1],
        )

    def test_with_no_location_the_character_keeps_it_and_a_warning_is_logged(self):
        self.load_to(CEILING)
        self.char1.location = None
        obj = self.fresh()
        with mock.patch(WARN) as warn:
            set_down = self.char1.receive_or_set_down([obj])
        self.assertEqual(set_down, [])
        self.assertEqual(obj.location, self.char1)
        warn.assert_called_once()
        self.assertEqual(carried_enc(self.char1), CEILING + 1)

    def test_the_line_names_one_and_counts_several(self):
        one = self.fresh(key="scroll")
        two = self.fresh(key="hide")
        self.assertEqual(
            self.char1.set_down_message([one]),
            "You cannot carry the scroll; you set it down.",
        )
        self.assertEqual(
            self.char1.set_down_message([one, two]),
            "You cannot carry 2 of them; you set them down.",
        )


# ------------------------------------------------------------------- craft


class TestCraftSetsDown(_CeilingFixture, CraftFixtureMixin, EvenniaCommandTest):
    """craft, through the command and its timed completion (Q3)."""

    def setUp(self):
        super().setUp()
        self.char1.skills.get("craft").current = 100
        self.char1.learn_recipe("sack")

    def give(self, *protos):
        objs = spawn(*protos)
        for obj in objs:
            obj.location = self.char1
        return objs

    def craft(self, args):
        """Start, then run the real completion with the roll pinned."""
        scheduled = self.start_craft(args)
        self.assertIsNotNone(scheduled, "the craft never started")
        with mock.patch(RNG, return_value=PLAIN_SUCCESS), said(self.char1) as seen:
            self.finish(scheduled)
        return seen

    @staticmethod
    def is_sack(obj):
        return obj.db.recipe == "sack"

    def test_a_product_past_the_ceiling_is_set_down_and_the_inputs_are_spent(self):
        self.load_to(CEILING)
        cloth = self.give("cloth", "cloth")
        lines = self.craft("sack from cloth-1, cloth-2")
        sacks = self.on_floor(self.is_sack)
        self.assertEqual((len(sacks), self.held(self.is_sack)), (1, []))
        # The receipt that the craft ran: its consumption is unchanged.
        self.assertEqual([obj.pk for obj in cloth], [None, None])
        self.assert_one_set_down_after(
            lines, "large sack", f"You cannot carry the {sacks[0].key}; you set it down."
        )
        self.assertEqual(carried_enc(self.char1), CEILING)

    def test_a_product_set_down_at_the_ceiling_still_counts(self):
        # Recipe Mastery M2.1: the count is written in do_craft, before
        # delivery, so where the product lands does not matter.
        self.load_to(CEILING)
        self.give("cloth", "cloth")
        self.craft("sack from cloth-1, cloth-2")
        self.assertEqual(len(self.on_floor(self.is_sack)), 1)   # receipt: set down
        self.assertEqual(self.char1.recipe_mastery.count("sack"), 1)

    def test_one_under_the_ceiling_the_product_is_in_hand(self):
        self.load_to(CEILING - 1)
        self.give("cloth", "cloth")
        lines = self.craft("sack from cloth-1, cloth-2")
        self.assertEqual(len(self.held(self.is_sack)), 1)
        self.assertEqual(self.on_floor(self.is_sack), [])
        self.assertNotIn(SET_DOWN, "\n".join(lines))

    def test_inputs_are_spent_before_the_product_arrives(self):
        # gourd (ENC 1) + twine (0) -> waterskin (ENC 1): neutral. At the
        # ceiling the waterskin fits only once the gourd is gone.
        self.load_to(CEILING - 1)
        self.give("raw_gourd", "twine")
        self.assertEqual(carried_enc(self.char1), CEILING)
        lines = self.craft("waterskin from gourd, twine")
        skins = self.held(lambda o: o.db.recipe == "waterskin")
        self.assertEqual(len(skins), 1)
        self.assertNotIn(SET_DOWN, "\n".join(lines))
        self.assertEqual(carried_enc(self.char1), CEILING)


# ------------------------------------------------------------------ forage


class TestForageSetsDown(_CeilingFixture, EvenniaCommandTest):
    """forage: the yield is on the floor, the node and the cooldown as usual."""

    STOCK = 6

    def setUp(self):
        super().setUp()
        self.node = create_object(NODE, key="sdoutcrop", location=self.room1)
        self.node.yield_prototype = "stone"
        self.node.max_yield = self.STOCK
        self.node.available = self.STOCK

    @staticmethod
    def is_stone(obj):
        return obj.tags.has("stone", category="crafting_material")

    def test_a_yield_past_the_ceiling_is_set_down(self):
        self.load_to(CEILING)
        lines = self.call(CmdForage(), "sdoutcrop").splitlines()
        stones = self.on_floor(self.is_stone)
        self.assertEqual((len(stones), self.held(self.is_stone)), (1, []))
        self.assertEqual(self.node.available, self.STOCK - 1)
        self.assertFalse(self.char1.cooldowns.ready("forage"))
        self.assert_one_set_down_after(
            lines, "You forage", f"You cannot carry the {stones[0].key}; you set it down."
        )


# ----------------------------------------------------------------- harvest


class TestHarvestSetsDownPartWay(_CeilingFixture, EvenniaCommandTest):
    """harvest: six portions, room for two (the twenty-to-one rule)."""

    def test_the_counted_surplus_is_on_the_floor_and_the_rest_in_hand(self):
        # 40 ENC plus 17 items at enc 0: two more fit (19), the twentieth tips.
        self.load_to(CEILING, zeros=17)
        create_object(CORPSE, key="sdcarcass", location=self.room1)
        self.char1.skills.get("hunting").current = 100

        def is_meat(obj):
            return obj.key == "raw rabbit meat"

        with mock.patch(RNG, return_value=PLAIN_SUCCESS), mock.patch(
            "commands.hunting_commands.compute_yield", return_value=6
        ):
            lines = self.call(CmdHarvest(), "meat from sdcarcass").splitlines()
        self.assertEqual(
            (len(self.held(is_meat)), len(self.on_floor(is_meat))), (2, 4)
        )
        self.assert_one_set_down_after(
            lines, "You harvest 6 meat", "You cannot carry 4 of them; you set them down."
        )


# ---------------------------------------------------------- inscribe, scribe


class TestInscribeSetsDown(_CeilingFixture, EvenniaCommandTest):
    """inscribe is ENC-neutral (cloth 0 -> scroll 0): only a character already
    above the ceiling -- a drained STR -- sets its scroll down."""

    def test_above_the_ceiling_the_scroll_is_set_down_and_the_cloth_spent(self):
        self.load_to(CEILING + 1)
        self.char1.skills.get("craft").current = 40
        self.char1.learn_recipe("cloth")
        cloth = spawn("cloth")[0]
        cloth.location = self.char1

        lines = self.call(CmdInscribe(), "cloth").splitlines()

        scrolls = self.on_floor(lambda o: o.db.recipe == "cloth")
        self.assertEqual(len(scrolls), 1)
        self.assertIsNone(cloth.pk)
        self.assert_one_set_down_after(
            lines,
            "You carefully inscribe",
            f"You cannot carry the {scrolls[0].key}; you set it down.",
        )


class TestScribeSetsDown(_CeilingFixture, EvenniaCommandTest):
    """scribe: cloth, cloth, twine (all enc 0) -> a book of ENC 1."""

    def test_a_book_past_the_ceiling_is_set_down_and_the_inputs_spent(self):
        self.load_to(CEILING)
        self.char1.skills.get("craft").current = 60   # SCRIBE_MIN_CRAFT is 50
        self.char1.learn_recipe("cloth")
        inputs = spawn("cloth", "cloth", "twine")
        for obj in inputs:
            obj.location = self.char1

        with mock.patch(RNG, return_value=PLAIN_SUCCESS):
            lines = self.call(CmdScribe(), "cloth").splitlines()

        books = self.on_floor(lambda o: o.is_typeclass("typeclasses.books.Book", exact=False))
        self.assertEqual(len(books), 1)
        self.assertEqual([obj.pk for obj in inputs], [None, None, None])
        self.assert_one_set_down_after(
            lines, "You bind a book", f"You cannot carry the {books[0].key}; you set it down."
        )
