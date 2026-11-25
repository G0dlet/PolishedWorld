"""
Unit tests for Gear GR-T13: `world.gear_migrations.migrate_gear` (GR17).

The old items are built as they were before the slice: a pure weapon a
plain `Object` with its key, `enc` and prototype tag, and no repair data; an
armour piece a garment worn as `top`. Nothing here imports the expected
values from world/prototypes.py: the repair data is transcribed from the
Gear Decomposition section 3.

WHAT EACH TEST PRESSURES
------------------------
- A second run answers (0, 0) -- the red (GR-T13's STOPP 0): a function
  that swaps without asking (GRM44) answers (1, 0), and one that counts what
  it found rather than what it changed (GRM46) answers (1, 1). A second
  swap would not show in the condition: `swap_typeclass` never touches an
  Attribute that exists, so a club worn to 60 stays 60 either way.
- A stone knife and a stone axe stay Tools at their condition: a tool among
  the weapons to swap (GRM45) becomes a Weapon.
- An old club becomes what a new one is: a Weapon, condition 100 stored at
  once (P2: a real Attribute), its `enc`, tag, key and alias untouched, and
  its prototype's repair data.
- A worn old bone armour gets the rigid layer, stays worn, and shows over
  the hauberk in the short description (GR7).
- A club made after the slice is not counted.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_gear_migrations
"""

from evennia.prototypes.spawner import spawn
from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

from typeclasses.objects import Object
from typeclasses.tools import Tool
from typeclasses.weapons import Weapon
from world import gear, sdesc
from world.gear_migrations import migrate_gear

# Section 3, *Mended with*: what each pure weapon is mended with.
REPAIR = {
    "club": (("wood",), "knife"),
    "quarterstaff": (("wood",), "knife"),
    "spear": (("wood", "twine"), "knife"),
    "bow": (("twine",), ""),
    "sling": (("leather",), "knife"),
}


class TestMigrateGear(EvenniaTest):

    character_typeclass = "typeclasses.characters.Character"

    def _old_weapon(self, prototype_key, key=None, enc=1):
        """A pure weapon as it was before GR: an Object with its tag."""
        obj = create.create_object(
            Object, key=key or prototype_key, location=self.char1,
            aliases=["cudgel"] if prototype_key == "club" else None,
        )
        obj.tags.add(prototype_key, category=gear.PROTOTYPE_TAG_CATEGORY)
        obj.db.enc = enc
        obj.db.quality = 30
        self.addCleanup(obj.delete)
        return obj

    def _old_armour(self, prototype_key):
        """An armour piece as it was before GR: the garment, worn as `top`."""
        obj = spawn(prototype_key)[0]
        obj.location = self.char1
        obj.db.clothing_type = "top"
        self.addCleanup(obj.delete)
        return obj

    def _spawn(self, prototype_key):
        obj = spawn(prototype_key)[0]
        obj.location = self.char1
        self.addCleanup(obj.delete)
        return obj

    @staticmethod
    def _reload(obj):
        """The item as the database now has it, not the Python object at hand."""
        return type(obj).objects.get(pk=obj.pk)

    def test_a_second_run_answers_nothing(self):
        self._old_weapon("club")
        self._old_armour("bone_armour")
        self.assertEqual(migrate_gear(), (1, 1))   # receipt: there was work
        self.assertEqual(migrate_gear(), (0, 0))

    def test_a_second_run_leaves_a_worn_club_worn(self):
        club = self._old_weapon("club")
        migrate_gear()
        club = self._reload(club)
        club.condition = 60
        migrate_gear()
        club = self._reload(club)
        self.assertIs(type(club), Weapon)
        self.assertEqual(club.condition, 60)

    def test_an_old_club_becomes_a_new_one(self):
        club = self._old_weapon("club")
        migrate_gear()
        club = self._reload(club)
        self.assertIs(type(club), Weapon)
        # Stored at once, not the property's default on a read (P2).
        self.assertTrue(club.attributes.has("condition"))
        self.assertEqual(club.condition, 100)
        self.assertEqual(club.key, "club")
        self.assertIn("cudgel", club.aliases.all())
        self.assertEqual(club.db.enc, 1)
        self.assertEqual(club.db.quality, 30)
        self.assertTrue(club.tags.has("club", category=gear.PROTOTYPE_TAG_CATEGORY))
        self.assertIsNotNone(gear.weapon(club))

    def test_each_old_weapon_gets_its_prototypes_repair_data(self):
        olds = {key: self._old_weapon(key) for key in REPAIR}
        self.assertEqual(migrate_gear(), (5, 0))
        for key, (materials, tool) in REPAIR.items():
            with self.subTest(item=key):
                obj = self._reload(olds[key])
                self.assertIs(type(obj), Weapon)
                self.assertEqual(tuple(obj.db.repair_materials), materials)
                self.assertEqual(obj.db.repair_tool_tag, tool)

    def test_repair_data_already_there_is_left_as_it_is(self):
        club = self._old_weapon("club")
        club.db.repair_materials = ("wood", "wood")
        migrate_gear()
        self.assertEqual(tuple(self._reload(club).db.repair_materials), ("wood", "wood"))

    def test_the_tools_stay_tools_at_their_condition(self):
        knife = self._spawn("stone_knife")
        axe = self._spawn("stone_axe")
        knife.condition = 12
        axe.condition = 7
        self.assertEqual(migrate_gear(), (0, 0))
        knife, axe = self._reload(knife), self._reload(axe)
        self.assertEqual((type(knife), knife.condition), (Tool, 12))
        self.assertEqual((type(axe), axe.condition), (Tool, 7))

    def test_a_club_made_after_the_slice_is_not_counted(self):
        club = self._spawn("club")
        club.condition = 70
        self.assertEqual(migrate_gear(), (0, 0))
        self.assertEqual(self._reload(club).condition, 70)

    def test_each_old_armour_gets_its_rows_layer(self):
        cuirass = self._old_armour("linen_cuirass")
        bone = self._old_armour("bone_armour")
        self.assertEqual(migrate_gear(), (0, 2))
        self.assertEqual(self._reload(cuirass).db.clothing_type, "armour_padding")
        self.assertEqual(self._reload(bone).db.clothing_type, "armour_rigid")

    def test_a_worn_old_bone_armour_stays_worn_and_its_word_follows(self):
        bone = self._old_armour("bone_armour")
        hauberk = self._spawn("hard_leather_hauberk")
        self.assertTrue(bone.wear(self.char1, True, quiet=True))
        self.assertTrue(hauberk.wear(self.char1, True, quiet=True))
        # Receipt: worn as `top`, the old bone armour shows under the hauberk.
        self.assertEqual(sdesc.garment_word(self.char1), "leather-clad")

        migrate_gear()

        bone = self._reload(bone)
        self.assertTrue(bone.db.worn)
        self.assertEqual(sdesc.garment_word(self.char1), "bone-clad")
        self.assertEqual(gear.armour_at(self.char1, "chest"), 4)
        self.assertEqual(gear.armour_total(self.char1), 6)
