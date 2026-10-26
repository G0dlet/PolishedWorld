"""
Unit tests for the clay chain. Alpha content epic, Task AC2.3.

clay (dug bare-handed from a clay bank) -> sling bullet. These tests drive the
shipped prototypes and recipe, not stand-ins: what fails here fails in the game.

WHAT IS WORTH TESTING HERE
--------------------------
1. **The recipe makes one bullet from one lump, for anyone.** Crafting goes
   through the contrib's own `craft()`, which runs `pre_craft` -- where the
   knowledge gate lives. char1 has learned nothing, so a bullet coming out is
   the receipt that the recipe is ungated, not only that the flag says so. The
   recipe inherits consume_policy "raw": a product exists whatever the roll.
2. **The clay bank needs no tool, and `forage clay` finds it.** The node has
   no "clay" alias; the in-game command reaches it through Evennia's fuzzy key
   match. The test uses the protocol's exact expression, so a renamed node or
   an alias that multimatches fails here before it fails in the game.
3. **ENC is on the items and off the node** (AD8), at the values locked for
   Q6. 0 is "too light to score", counted 20 to 1 by the weight mechanic --
   never weightless. Read through `search_prototype(no_db=True)`.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_clay_chain
"""

from evennia.contrib.game_systems.crafting.crafting import craft
from evennia.prototypes.prototypes import search_prototype
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest

from commands.foraging_commands import CmdForage

MATERIAL = "crafting_material"

# Q6, locked at AC2.3 task start.
ITEM_ENC = {"clay": 0, "sling_bullet": 0}
NODES = ("clay_bank",)


class ClayBase(EvenniaCommandTest):
    """char1 in room1; helpers spawn the shipped prototypes."""

    character_typeclass = "typeclasses.characters.Character"

    def give(self, *prototype_keys):
        objs = []
        for key in prototype_keys:
            obj = spawn(key)[0]
            obj.location = self.char1
            objs.append(obj)
        return objs

    def carried(self, tag):
        return [o for o in self.char1.contents if o.tags.has(tag, category=MATERIAL)]

    def carried_key(self, prototype_key):
        return [o for o in self.char1.contents
                if o.tags.has(prototype_key, category="from_prototype")]


class TestSlingBulletRecipe(ClayBase):
    """Point 1: one clay -> one sling bullet, by a character who knows nothing."""

    def test_a_fresh_character_rolls_one_bullet_from_one_clay(self):
        (clay,) = self.give("clay")
        result = craft(self.char1, "sling bullet", clay)
        self.assertEqual(len(result), 1)
        self.assertEqual(self.carried_key("sling_bullet"), result)
        self.assertEqual(self.carried("clay"), [])


class TestClayBankIsBareHanded(ClayBase):
    """Point 2: the shipped CLAY_BANK, a bare hand and the in-game expression."""

    def test_forage_clay_digs_a_lump_without_a_tool(self):
        bank = spawn("clay_bank")[0]
        bank.location = self.room1
        stock = bank.get_available()
        self.call(CmdForage(), "clay", "You forage", caller=self.char1)
        self.assertEqual(len(self.carried("clay")), 1)
        self.assertEqual(bank.get_available(), stock - 1)


class TestEncOnItemsNotNodes(ClayBase):
    """Point 3: AD8 -- items carry `enc`, the node does not."""

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
