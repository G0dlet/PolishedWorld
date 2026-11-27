"""
The bandage: an ungated recipe on cloth (Healing Decomposition §8, HL-T5; lock HL5).

Combat Design HL5 gives First Aid one `bandage` with no penalty, or one `cloth`
at -20 %. This file holds the bandage's side of that: the prototype the recipe
spawns, the recipe's card, and the craft itself -- by a character who has
learned nothing, at exactly the floor, one bolt of cloth in and two bandages
out.

The numbers are transcribed here, not imported from world/recipes.py, so a
change to the recipe has to change this file too (HL-T5's STOPP 0):

  * two bandages from one cloth (OQ-HL8): one bandage per cloth would make the
    bandage a tax of craft time on the -20 %; two make a crafter's cloth go
    further than a torn tunic's;
  * no tool: every attempt yields under the inherited raw policy, so a knife
    could only have moved a quality nothing reads (HL5 reads none);
  * Craft 20 %, the floor the input chain forces (cloth sits at 20, and
    tests.test_min_skill_ladder holds no product below a maker of its input),
    and 25 seconds, rung 20's duration, as cloth's;
  * ungated: knowing no recipe is enough (HL5: anyone can make bandages).

The craft is pinned to each tier with the d100, because the yield must not
depend on the roll: a fumble still turns one cloth into two bandages.

The bandage is the first recipe with two of one product, so the two places a
player reads the products were taught to count (HL-T5): the recipe card says
"2x bandage", and the craft line "two bandages" (world.crafting_base
.output_phrase), with the failure and fumble lines in the plural. A single
product still reads as it did.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_bandage
"""

from unittest import mock

from evennia.contrib.game_systems.crafting.crafting import craft
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaTest

from world.crafting_base import output_phrase
from world.knowledge import render_recipe_detail_by_name


MATERIAL = "crafting_material"

BANDAGES_PER_CLOTH = 2
FLOOR = 20
DURATION = 25

# d100 faces for each tier at Craft 20 with no modifier: critical at or below
# ceil(20 / 10) = 2, success at or below 20, fumble on the "00" face. Each with
# the line the crafter reads: the two bandages counted, as one phrase, and the
# failure and fumble lines' verbs in the plural.
FACES = (
    ("critical", 1,
     "Your hands move with rare sureness. You craft two bandages of superior quality!"),
    ("success", 15, "You work the materials into two bandages."),
    ("failure", 50, "The work fights you; two bandages come out poorly made."),
    ("fumble", 100, "You botch the work badly — two bandages are shoddy, barely usable."),
)


class TestBandage(EvenniaTest):
    """Drive the shipped prototype, the recipe registry and the craft."""

    character_typeclass = "typeclasses.characters.Character"

    def give(self, *prototype_keys):
        """Spawn real inputs into char1's inventory."""
        objs = []
        for prototype_key in prototype_keys:
            obj = spawn(prototype_key)[0]
            obj.location = self.char1
            objs.append(obj)
        return objs

    def carried(self, tag):
        return [o for o in self.char1.contents if o.tags.has(tag, category=MATERIAL)]

    def test_the_prototype_builds_a_bandage(self):
        (bandage,) = spawn("bandage")
        self.assertEqual(bandage.key, "bandage")
        self.assertEqual(bandage.db.enc, 0)
        # The tag `treat` and a recipe's consumable_tags will match it by.
        self.assertTrue(bandage.tags.has("bandage", category=MATERIAL))

    def test_the_recipe_card(self):
        detail = render_recipe_detail_by_name("bandage")
        self.assertIsNotNone(detail)
        self.assertIn("1x cloth", detail)
        self.assertIn("none needed", detail)
        self.assertIn(f"Craft {FLOOR}% minimum", detail)
        self.assertIn(f"{DURATION} seconds", detail)
        # Counted in the Needs line's form, not "bandage, bandage".
        self.assertIn(f"Output:|n  {BANDAGES_PER_CLOTH}x bandage\n", detail)

    def test_one_product_reads_as_before(self):
        # Receipt that the counting touches only a repeated name: a single
        # product is its bare display name, with no article.
        (cloth,) = self.give("cloth")
        self.assertEqual(output_phrase([cloth], self.char1), "bolt of cloth")

    def test_one_cloth_makes_two_bandages_on_every_tier(self):
        self.assertEqual(len(FACES), 4)  # guard against a vacuous loop
        # Receipt: the craft below runs on a character who knows no recipe.
        self.assertFalse(self.char1.knows_recipe("bandage"))
        for tier, face, line in FACES:
            with self.subTest(tier=tier):
                (cloth,) = self.give("cloth")
                self.char1.skills.get("craft").current = FLOOR
                with mock.patch("world.skillcheck.randint", return_value=face), \
                        mock.patch.object(self.char1, "msg") as msg:
                    result = craft(self.char1, "bandage", cloth)

                # The contrib's recipe.msg sends text=(message, {"type": "crafting"}).
                said = [
                    str(c.kwargs["text"][0]) for c in msg.call_args_list
                    if isinstance(c.kwargs.get("text"), tuple)
                ]
                self.assertIn(line, said)

                # A refusal returns None: fail on that, not on a TypeError.
                self.assertIsNotNone(result)
                self.assertEqual(len(result), BANDAGES_PER_CLOTH)
                for bandage in result:
                    self.assertEqual(bandage.location, self.char1)
                    self.assertEqual(bandage.db.recipe, "bandage")
                    self.assertTrue(bandage.tags.has("bandage", category="from_prototype"))
                self.assertIsNone(cloth.pk)
                self.assertEqual(self.carried("cloth"), [])
                for bandage in result:
                    bandage.delete()

    def test_below_the_floor_the_cloth_is_kept(self):
        (cloth,) = self.give("cloth")
        self.char1.skills.get("craft").current = FLOOR - 1

        result = craft(self.char1, "bandage", cloth)

        self.assertFalse(result)
        self.assertIsNotNone(cloth.pk)
        self.assertEqual(cloth.location, self.char1)
        self.assertEqual(self.carried("bandage"), [])
