"""
Unit tests for the felling chain. Alpha content epic, Task AC2.2.

flint (bare-handed) + stick + twine -> stone axe; the axe is the only way to
take wood from a tree; wood -> club. These tests drive the shipped prototypes
and recipes, not stand-ins: what fails here fails in the game.

WHAT IS WORTH TESTING HERE
--------------------------
1. **Each recipe makes what the registry says it makes.** The stone axe from
   flint + stick + twine, consuming exactly those; the club from wood. Crafting
   goes through the contrib's own `craft()` -- the path every caller reaches.
   Both inherit consume_policy "raw", so a product exists whatever the roll and
   the tests need no mocked dice.
2. **The axe is a working felling tool as spawned.** Tag in `crafting_tool`,
   start condition 40, and the shipped TREE takes it: one forage yields wood
   and leaves the axe at 35 (40 - FORAGE_TOOL_WEAR). This is the in-game
   protocol's step, as the same expression (`axe.condition`).
3. **The tree refuses a bare hand; the flint scatter does not.** The first
   pins TREE's `required_tool`, the second pins that the bootstrap's first
   input needs no tool (a scatter that demanded one would lock the chain).
4. **The club's knife is real.** Crafted with a stone knife, the knife wears
   by the recipe's tool_wear -- the receipt that `tool_tag = "knife"` matched.
5. **ENC is on the items and off the nodes** (AD8), at the values locked for
   Q6. Read through `search_prototype(no_db=True)`, as the registry test does.

⚠️ RECEIPTS
-----------
The refusal test asserts the refusal text before "nothing changed", so a
command that silently did nothing cannot pass it.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_felling_chain
"""

from evennia.contrib.game_systems.crafting.crafting import craft
from evennia.prototypes.prototypes import search_prototype
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest

from commands.foraging_commands import FORAGE_TOOL_WEAR, TOOL_TAG_CATEGORY, CmdForage
from world.recipes import ClubRecipe

MATERIAL = "crafting_material"
AXE_START = 40

# Q6, locked at AC2.2 task start.
ITEM_ENC = {"flint": 0, "wood": 1, "stone_axe": 1, "club": 1}
NODES = ("flint_scatter", "tree")


class FellingBase(EvenniaCommandTest):
    """char1 in room1; helpers spawn the shipped prototypes."""

    character_typeclass = "typeclasses.characters.Character"

    def give(self, *prototype_keys):
        objs = []
        for key in prototype_keys:
            obj = spawn(key)[0]
            obj.location = self.char1
            objs.append(obj)
        return objs

    def place(self, prototype_key):
        node = spawn(prototype_key)[0]
        node.location = self.room1
        return node

    def carried(self, tag):
        return [o for o in self.char1.contents if o.tags.has(tag, category=MATERIAL)]

    def carried_key(self, prototype_key):
        return [o for o in self.char1.contents
                if o.tags.has(prototype_key, category="from_prototype")]

    def forage(self, target, msg=None):
        return self.call(CmdForage(), target, msg, caller=self.char1)


class TestStoneAxeRecipe(FellingBase):
    """Point 1 and 2: flint + stick + twine -> a stone axe, inputs consumed."""

    def test_axe_is_made_from_flint_stick_and_twine(self):
        inputs = self.give("flint", "stick", "twine")
        result = craft(self.char1, "stone axe", *inputs)
        self.assertEqual(len(result), 1)
        axe = result[0]
        self.assertEqual(axe.location, self.char1)
        self.assertTrue(axe.tags.has("axe", category=TOOL_TAG_CATEGORY))
        self.assertEqual(axe.condition, AXE_START)
        for tag in ("flint", "stick", "twine"):
            with self.subTest(consumed=tag):
                self.assertEqual(self.carried(tag), [])


class TestClubRecipe(FellingBase):
    """Point 1 and 4: wood -> a club; a carried knife is the tool it uses."""

    def test_club_is_made_from_wood(self):
        (wood,) = self.give("wood")
        result = craft(self.char1, "club", wood)
        self.assertEqual(len(result), 1)
        self.assertEqual(self.carried_key("club"), result)
        self.assertEqual(self.carried("wood"), [])

    def test_a_knife_shapes_the_club_and_wears(self):
        wood, knife = self.give("wood", "stone_knife")
        start = knife.condition
        result = craft(self.char1, "club", wood, knife)
        self.assertEqual(len(result), 1)
        self.assertEqual(knife.condition, start - ClubRecipe.tool_wear)


class TestTreeNeedsTheAxe(FellingBase):
    """Point 2 and 3: the shipped TREE against a bare hand and the shipped axe."""

    def setUp(self):
        super().setUp()
        self.tree = self.place("tree")
        self.stock = self.tree.get_available()

    def test_bare_hand_is_refused_and_claims_nothing(self):
        self.forage("tree", msg="You need an axe to gather from the tree")
        self.assertEqual(self.tree.get_available(), self.stock)
        self.assertEqual(self.carried("wood"), [])
        self.assertTrue(self.char1.cooldowns.ready("forage"))

    def test_stone_axe_fells_wood_and_wears_to_35(self):
        (axe,) = self.give("stone_axe")
        self.forage("tree", msg="You forage")
        self.assertEqual(len(self.carried("wood")), 1)
        self.assertEqual(self.tree.get_available(), self.stock - 1)
        self.assertEqual(axe.condition, AXE_START - FORAGE_TOOL_WEAR)
        self.assertEqual(axe.condition, 35)


class TestFlintScatterIsBareHanded(FellingBase):
    """Point 3: the chain's first input needs no tool."""

    def test_flint_is_foraged_without_a_tool(self):
        self.place("flint_scatter")
        self.forage("scatter", msg="You forage")
        self.assertEqual(len(self.carried("flint")), 1)


class TestEncOnItemsNotNodes(FellingBase):
    """Point 5: AD8 -- items carry `enc`, nodes do not."""

    def setUp(self):
        super().setUp()
        self.by_key = {p["prototype_key"]: p for p in search_prototype(no_db=True)}

    def _enc(self, key):
        for attr in self.by_key[key].get("attrs", []):
            if attr[0] == "enc":
                return attr[1]
        return None

    def test_items_carry_the_locked_enc(self):
        for key, enc in ITEM_ENC.items():
            with self.subTest(prototype=key):
                self.assertEqual(self._enc(key), enc)

    def test_nodes_carry_none(self):
        for key in NODES:
            with self.subTest(prototype=key):
                self.assertIsNone(self._enc(key))
