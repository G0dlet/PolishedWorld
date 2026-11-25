"""
Tests for world.gear -- the weapon and armour tables and their two readers
(Gear decomposition GR-T1; locks IS1, IS2, GR8, GR12-GR16; Legend core
pp. 94-109; Arms of Legend pp. 48-50, 71 ff.) -- for the Weapon class
and the five pure weapons on the wear axis (GR-T2; GR13, GR21, GR24;
Arms of Legend p. 43) -- and for the three armour layers as clothing types
and what shows of them (GR-T3; GR6-GR8, OQ-GR5).

Every expected row is typed here by hand from the decomposition's §3, not
read from the module, so a row that drifts from the book fails by its cell.
"""

from types import MappingProxyType
from unittest import TestCase, mock

from django.conf import settings
from evennia.contrib.game_systems.clothing.clothing import CmdWear, get_worn_clothes
from evennia.prototypes.spawner import spawn
from evennia.utils import create
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.repair_commands import CmdRepair
from typeclasses.clothing import ClothingWithBuffs
from typeclasses.tools import Tool
from typeclasses.weapons import Weapon
from world import body, combat_styles, gear
from world import prototypes as world_prototypes
from world import recipes, sdesc, thermal

WEAPON_FIELDS = (
    "weapon_type", "hand", "damage", "str_min", "dex_min", "size", "reach",
    "manoeuvres", "ap", "hp", "damage_modifier", "range_m", "load",
    "parries_ranged",
)

# §3, in WEAPON_FIELDS order.
EIGHT = {
    "club": ("bludgeon", "1H", "1D6", 7, None, "M", "S",
             ("stun_location",), 4, 4, None, None, None, False),
    "quarterstaff": ("bludgeon", "2H", "1D8", 7, 7, "M", "L",
                     ("stun_location",), 4, 8, None, None, None, False),
    "spear": ("spear", "1H", "1D8+1", 5, 5, "M", "L",
              ("impale",), 4, 5, None, None, None, False),
    "stone_knife": ("knife", "1H", "1D3", None, None, "S", "S",
                    ("bleed", "impale"), 5, 4, None, None, None, False),
    "stone_axe": ("axe", "1H", "1D6", None, 9, "S", "S",
                  ("bleed",), 3, 6, None, None, None, False),
    "target_shield": ("shield", "1H", "1D6", 9, None, "L", "S",
                      ("impale",), 4, 12, None, None, None, True),
    "bow": ("bow", "2H", "1D6", 9, 11, "L", None,
            ("impale",), 4, 4, True, 80, 1, False),
    "sling": ("sling", "1H", "1D8", None, 11, "L", None,
              ("stun_location",), 1, 2, True, 200, 1, False),
}

# §3: (ap, locations, layer, material).
SIX = {
    "linen_cuirass": (2, ("chest",), "armour_padding", "linen"),
    "soft_leather_trews": (1, ("abdomen", "right_leg", "left_leg"),
                           "armour_padding", "soft leather"),
    "hard_leather_hauberk": (2, ("chest", "abdomen"),
                             "armour_flexible", "hard leather"),
    "hard_leather_vambraces": (2, ("right_arm", "left_arm"),
                               "armour_flexible", "hard leather"),
    "bone_armour": (2, ("chest",), "armour_rigid", "bone"),
    "bone_helm": (2, ("head",), "armour_rigid", "bone"),
}

# The rows whose prototypes GR-T12 adds. GR-T12 empties this set.
NOT_YET_MADE = {
    "target_shield", "soft_leather_trews", "hard_leather_hauberk",
    "hard_leather_vambraces", "bone_helm",
}


class TestTheWeaponRows(TestCase):
    """
    Pressures GR14: a cell that drifted from the book (GRM2, the club's
    damage), a hand that is not AoL's Category (GRM4's sibling in the row),
    a field missing from one row, and a type or hand outside the shared
    vocabulary.
    """

    def test_each_row_cell_by_cell(self):
        self.assertEqual(set(gear.WEAPONS), set(EIGHT))
        for key, expected in EIGHT.items():
            row = gear.WEAPONS[key]
            for field, value in zip(WEAPON_FIELDS, expected):
                with self.subTest(item=key, field=field):
                    self.assertEqual(row[field], value)

    def test_every_row_has_every_field_and_no_other(self):
        for key, row in gear.WEAPONS.items():
            with self.subTest(item=key):
                self.assertEqual(set(row), set(WEAPON_FIELDS))

    def test_the_hand_is_aols_category(self):
        # Arms of Legend's close combat table (pp. 71 ff.): the quarterstaff
        # alone is 2H in close combat; the bow is 2H at range.
        hands = {key: row["hand"] for key, row in gear.WEAPONS.items()}
        self.assertEqual(hands, {
            "club": "1H", "quarterstaff": "2H", "spear": "1H",
            "stone_knife": "1H", "stone_axe": "1H", "target_shield": "1H",
            "bow": "2H", "sling": "1H",
        })

    def test_types_and_hands_are_the_shared_vocabulary(self):
        for key, row in gear.WEAPONS.items():
            with self.subTest(item=key):
                self.assertIn(row["weapon_type"], combat_styles.WEAPON_TYPES)
                self.assertIn(row["hand"], combat_styles.HANDS)
        self.assertEqual((gear.ONE_HAND, gear.TWO_HANDS), combat_styles.HANDS)

    def test_a_ranged_row_has_no_reach_and_a_melee_row_no_range(self):
        for key, row in gear.WEAPONS.items():
            ranged = row["range_m"] is not None
            with self.subTest(item=key):
                self.assertEqual(ranged, key in ("bow", "sling"))
                self.assertEqual(row["reach"] is None, ranged)
                self.assertEqual(row["load"] is None, not ranged)
                self.assertEqual(row["damage_modifier"] is None, not ranged)

    def test_only_the_shield_parries_a_shot(self):
        self.assertEqual(
            {key for key, row in gear.WEAPONS.items() if row["parries_ranged"]},
            {"target_shield"},
        )

    def test_every_weapon_type_in_a_row_has_a_style_for_its_hand(self):
        # BD4 and GR15: the slice that adds the first weapon of a type adds
        # its style. The sling bullet and a second hand are not weapons here.
        styled = {(row["main"], row["hand"]) for row in combat_styles.STYLES.values()}
        for key, row in gear.WEAPONS.items():
            if row["weapon_type"] == "shield":
                continue   # a shield is always the second hand (GR2)
            with self.subTest(item=key):
                self.assertIn((row["weapon_type"], row["hand"]), styled)


class TestTheArmourRows(TestCase):
    """
    Pressures GR8 and GR12: a row whose locations lost one (GRM3, the
    hauberk on the chest only), a location that is not the body's, a layer
    that is not one of the three, and locations out of the body's order.
    """

    def test_each_row_cell_by_cell(self):
        self.assertEqual(set(gear.ARMOUR), set(SIX))
        for key, (ap, locations, layer, material) in SIX.items():
            row = gear.ARMOUR[key]
            with self.subTest(item=key):
                self.assertEqual(
                    (row["ap"], row["locations"], row["layer"], row["material"]),
                    (ap, locations, layer, material),
                )
                self.assertEqual(set(row), {"ap", "locations", "layer", "material"})

    def test_every_location_is_the_bodys_in_its_order(self):
        for key, row in gear.ARMOUR.items():
            with self.subTest(item=key):
                for location in row["locations"]:
                    self.assertIn(location, body.LOCATIONS)
                self.assertEqual(
                    list(row["locations"]),
                    sorted(row["locations"], key=body.LOCATIONS.index),
                )

    def test_the_three_layers(self):
        self.assertEqual(
            gear.LAYERS, ("armour_rigid", "armour_flexible", "armour_padding")
        )
        for key, row in gear.ARMOUR.items():
            with self.subTest(item=key):
                self.assertIn(row["layer"], gear.LAYERS)

    def test_two_items_in_every_layer(self):
        # GR12: with the linen cuirass and the bone armour.
        for layer in gear.LAYERS:
            with self.subTest(layer=layer):
                self.assertEqual(
                    sum(row["layer"] == layer for row in gear.ARMOUR.values()), 2
                )

    def test_every_location_has_a_piece(self):
        # GR9: every Hit Location has at least one item.
        covered = {loc for row in gear.ARMOUR.values() for loc in row["locations"]}
        self.assertEqual(covered, set(body.LOCATIONS))


class TestNothingIsWritable(TestCase):
    """
    Pressures the shared row: a reader hands out the same mapping to every
    caller, so one caller's write would change the item for every player.
    """

    def test_a_row_refuses_a_write(self):
        with self.assertRaises(TypeError):
            gear.WEAPONS["club"]["ap"] = 99
        with self.assertRaises(TypeError):
            gear.ARMOUR["bone_armour"]["ap"] = 99
        self.assertEqual(gear.WEAPONS["club"]["ap"], 4)

    def test_a_table_refuses_a_new_row(self):
        with self.assertRaises(TypeError):
            gear.WEAPONS["rock"] = gear.WEAPONS["club"]
        with self.assertRaises(TypeError):
            gear.ARMOUR["tunic"] = gear.ARMOUR["bone_armour"]

    def test_what_is_inside_is_a_tuple(self):
        for row in gear.WEAPONS.values():
            self.assertIsInstance(row["manoeuvres"], tuple)
        for row in gear.ARMOUR.values():
            self.assertIsInstance(row["locations"], tuple)
        self.assertIsInstance(gear.WEAPONS, MappingProxyType)
        self.assertIsInstance(gear.ARMOUR, MappingProxyType)


class TestTheCensus(TestCase):
    """
    Pressures the key a row is found by: a row for a prototype that does not
    exist, which no item can ever read; and a key with a capital letter,
    which no tag can ever match, since Evennia lowers every tag key.
    """

    def _module_prototype_keys(self):
        return {
            value["prototype_key"]
            for value in vars(world_prototypes).values()
            if isinstance(value, dict) and "prototype_key" in value
        }

    def test_every_row_is_a_prototype_or_one_gr_t12_adds(self):
        rows = set(gear.WEAPONS) | set(gear.ARMOUR)
        self.assertEqual(rows - self._module_prototype_keys(), NOT_YET_MADE)

    def test_no_table_shares_a_key(self):
        self.assertEqual(set(gear.WEAPONS) & set(gear.ARMOUR), set())

    def test_every_key_is_lower_case(self):
        for key in list(gear.WEAPONS) + list(gear.ARMOUR):
            with self.subTest(key=key):
                self.assertEqual(key, key.lower())


class TestTheReaders(EvenniaTest):
    """
    Pressures GR16's lookup: a reader keyed by the item's name and not its
    prototype tag (GRM1), an item with no row read as something, and an
    item with two tags read as either of them, or in silence.
    """

    def _spawn(self, key):
        obj = spawn(key)[0]
        self.addCleanup(obj.delete)
        return obj

    def test_a_spawned_club_reads_the_clubs_row(self):
        club = self._spawn("club")
        self.assertIs(gear.weapon(club), gear.WEAPONS["club"])
        self.assertIsNone(gear.armour(club))

    def test_a_spawned_quarterstaff_is_two_handed(self):
        self.assertEqual(gear.weapon(self._spawn("quarterstaff"))["hand"], "2H")

    def test_bone_armour_reads_the_armour_row(self):
        armour = self._spawn("bone_armour")
        self.assertIs(gear.armour(armour), gear.ARMOUR["bone_armour"])
        self.assertIsNone(gear.weapon(armour))

    def test_an_item_with_a_tag_and_no_row_is_none(self):
        robe = self._spawn("robe")
        self.assertIsNone(gear.weapon(robe))
        self.assertIsNone(gear.armour(robe))

    def test_an_object_with_no_tag_is_none(self):
        self.assertIsNone(gear.weapon(self.obj1))
        self.assertIsNone(gear.armour(self.obj1))

    def test_the_name_is_not_the_key(self):
        # An object called "club", made without spawn: no tag, no row.
        fake = create.create_object("typeclasses.objects.Object", key="club")
        self.addCleanup(fake.delete)
        self.assertIsNone(gear.weapon(fake))
        # And a spawned club renamed is still a club.
        club = self._spawn("club")
        club.key = "cudgel"
        self.assertIs(gear.weapon(club), gear.WEAPONS["club"])

    def test_two_tags_read_none_and_are_logged(self):
        club = self._spawn("club")
        club.tags.add("spear", category="from_prototype")
        with mock.patch("world.gear.logger.log_warn") as warn:
            self.assertIsNone(gear.weapon(club))
            self.assertIsNone(gear.armour(club))
        self.assertEqual(warn.call_count, 2)
        self.assertIn("['club', 'spear']", warn.call_args.args[0])

    def test_one_tag_is_not_logged(self):
        club = self._spawn("club")
        with mock.patch("world.gear.logger.log_warn") as warn:
            gear.weapon(club)
            gear.weapon(self.obj1)
        warn.assert_not_called()


# GR-T2. The five pure weapons: their recipe, and what mends them (§3).
PURE_WEAPONS = {
    "club": (recipes.ClubRecipe, ("wood",), "knife"),
    "quarterstaff": (recipes.QuarterstaffRecipe, ("wood",), "knife"),
    "spear": (recipes.SpearRecipe, ("wood", "twine"), "knife"),
    "bow": (recipes.BowRecipe, ("twine",), ""),
    "sling": (recipes.SlingRecipe, ("leather",), "knife"),
}

# Quality stamped by the craft -> start condition (GR21; the garments' table):
# superior, serviceable, poor, shoddy.
BY_QUALITY = ((105, 100), (100, 90), (50, 70), (0, 50))


class TestThePureWeapons(EvenniaTest):
    """
    Pressures GR13 and GR21: a weapon without the durable mixin (GRM5), a
    recipe that skips the quality call (GRM6), repair data that is missing
    or wrong (GRM7, the club's tool unset), and the two tool-weapons
    dragged onto the weapons' starting table.
    """

    def _spawn(self, key):
        obj = spawn(key)[0]
        self.addCleanup(obj.delete)
        return obj

    def test_each_spawns_as_a_weapon_at_100(self):
        for key in PURE_WEAPONS:
            with self.subTest(item=key):
                obj = self._spawn(key)
                self.assertIs(type(obj), Weapon)
                self.assertEqual(obj.condition, 100)
                # A real Attribute, not the property's default (P2).
                self.assertTrue(obj.attributes.has("condition"))
                self.assertTrue(obj.mendable)
                self.assertIsNotNone(gear.weapon(obj))

    def test_each_names_what_mends_it(self):
        for key, (_, materials, tool) in PURE_WEAPONS.items():
            with self.subTest(item=key):
                obj = self._spawn(key)
                self.assertEqual(tuple(obj.db.repair_materials), materials)
                # "" is no tool; None would fall back to a needle.
                self.assertEqual(obj.db.repair_tool_tag, tool)

    def test_quality_sets_the_start_condition(self):
        for key, (recipe, _, _) in PURE_WEAPONS.items():
            for quality, start in BY_QUALITY:
                with self.subTest(item=key, quality=quality):
                    obj = self._spawn(key)
                    obj.db.quality = quality
                    recipe._finalize_item(mock.Mock(), obj, None)
                    self.assertEqual(obj.condition, start)

    def test_a_superior_weapon_is_called_so(self):
        club = self._spawn("club")
        club.db.quality = 105
        recipes.ClubRecipe._finalize_item(mock.Mock(), club, None)
        self.assertIn("superior club", club.aliases.all())

    def test_the_stone_knife_and_axe_keep_their_prototypes_condition(self):
        # GR21's exception: their condition is the prototype's (BACKLOG
        # Superior-tool longevity), at every band.
        for key, recipe in (("stone_knife", recipes.StoneKnifeRecipe),
                            ("stone_axe", recipes.StoneAxeRecipe)):
            for quality, _ in BY_QUALITY:
                with self.subTest(item=key, quality=quality):
                    obj = self._spawn(key)
                    obj.db.quality = quality
                    recipe._finalize_item(mock.Mock(), obj, None)
                    self.assertIs(type(obj), Tool)
                    self.assertEqual(obj.condition, 40)


class TestMendingAWeapon(EvenniaCommandTest):
    """
    Pressures GR24's repair data through the command a player types: a club
    mended with the garments' cloth and twine (the red receipt), and a bow
    eased or hindered by a needle.
    """

    character_typeclass = "typeclasses.characters.Character"

    def test_each_asks_for_its_own_materials(self):
        for key, (_, materials, _) in PURE_WEAPONS.items():
            with self.subTest(item=key):
                obj = spawn(key)[0]
                self.addCleanup(obj.delete)
                obj.location = self.char1
                obj.condition = 60
                self.call(
                    CmdRepair(), key,
                    f"You need {' and '.join(materials)} to mend your {key}.",
                    caller=self.char1,
                )
                self.assertEqual(obj.condition, 60)
                obj.location = None


# -- G2: the layers -------------------------------------------------------------

def _armour_prototypes():
    """Every prototype in world/prototypes.py that has an armour row."""
    return {
        value["prototype_key"]: value
        for value in vars(world_prototypes).values()
        if isinstance(value, dict) and value.get("prototype_key") in gear.ARMOUR
    }


class TestTheLayersInConfiguration(TestCase):
    """
    Pressures GR6-GR8 and OQ-GR5 where they are data: a layer missing from
    the contrib's order or standing after `top`, a layer given a type limit
    (one helm would refuse a breastplate), the showing order changed (GRM8,
    GRM9), a prototype whose type is not its row's layer (GRM10), and an
    armour piece with a word that does not cover the chest, or one that
    does and has none -- either lets the order of `contents` choose the word.
    """

    def test_the_layers_stand_just_before_top_outermost_first(self):
        order = list(settings.CLOTHING_TYPE_ORDERED)
        top = order.index("top")
        self.assertEqual(tuple(order[top - 3:top]), gear.LAYERS)

    def test_no_layer_has_a_type_limit(self):
        for layer in gear.LAYERS:
            with self.subTest(layer=layer):
                self.assertNotIn(layer, settings.CLOTHING_TYPE_LIMIT)

    def test_autocover_is_not_set(self):
        # GR7: it goes by type, and the contrib reads cannot-cover-with from it.
        self.assertFalse(hasattr(settings, "CLOTHING_TYPE_AUTOCOVER"))

    def test_what_shows_and_in_which_order(self):
        self.assertEqual(
            sdesc.SHOWING_TYPES,
            ("fullbody", "armour_rigid", "armour_flexible", "armour_padding", "top"),
        )

    def test_every_armour_prototype_wears_its_rows_layer(self):
        found = _armour_prototypes()
        self.assertEqual(set(found), set(gear.ARMOUR) - NOT_YET_MADE)
        for key, prototype in found.items():
            with self.subTest(item=key):
                self.assertEqual(prototype["clothing_type"], gear.ARMOUR[key]["layer"])

    def test_an_armour_piece_has_a_word_if_and_only_if_it_covers_the_chest(self):
        found = _armour_prototypes()
        self.assertEqual(len(found), 2)   # GR-T12 adds four; guard against a vacuous loop
        for key, prototype in found.items():
            with self.subTest(item=key):
                self.assertEqual(
                    bool(prototype.get("look_word")),
                    "chest" in gear.ARMOUR[key]["locations"],
                )

    def test_a_garment_carries_no_armour_values_of_its_own(self):
        # GR16: Armour Points are the row's; ENC is the `enc` Attribute.
        self.assertFalse(hasattr(ClothingWithBuffs, "armor_points"))
        self.assertFalse(hasattr(ClothingWithBuffs, "encumbrance"))


class TestTheLayersWorn(EvenniaCommandTest):
    """
    Pressures GR6 and GR7 through the command a player types: the contrib's
    `wear` refusing a cuirass over a tunic, as it did while both were a `top`
    (GRM10); the word read from the tunic or the cuirass when bone armour
    lies over both (GRM8); and the cloak not hiding the armour (GRM9).
    """

    character_typeclass = "typeclasses.characters.Character"

    def _give(self, key):
        obj = spawn(key)[0]
        self.addCleanup(obj.delete)
        obj.location = self.char1
        return obj

    def _wear_all(self):
        pieces = [self._give(key) for key in ("wool_tunic", "linen_cuirass", "bone_armour")]
        for piece in pieces:
            result = self.call(CmdWear(), piece.key, caller=self.char1)
            with self.subTest(item=piece.key):
                self.assertNotIn("can't wear", result)
                self.assertTrue(piece.db.worn)
        return pieces

    def test_armour_goes_on_over_a_tunic_and_reads_from_the_outside_in(self):
        self._wear_all()
        self.assertEqual(
            [garment.key for garment in get_worn_clothes(self.char1)],
            ["bone armour", "linen cuirass", "wool tunic"],
        )

    def test_the_word_is_the_outermost_pieces(self):
        tunic, cuirass, bone = self._wear_all()
        self.assertEqual(sdesc.garment_word(self.char1), "bone-clad")
        bone.remove(self.char1, quiet=True)
        self.assertEqual(sdesc.garment_word(self.char1), "armoured")
        cuirass.remove(self.char1, quiet=True)
        self.assertIsNone(sdesc.garment_word(self.char1))   # the tunic has no word

    def test_a_cloak_hides_the_armour(self):
        self._wear_all()
        cloak = self._give("fur_cloak")
        self.call(CmdWear(), "fur cloak", caller=self.char1)
        self.assertTrue(cloak.db.worn)
        self.assertEqual(sdesc.garment_word(self.char1), "cloaked")

    def test_warmth_is_the_sum_of_the_three(self):
        self._wear_all()
        self.assertEqual(thermal.worn_warmth(self.char1), 2 + 1 + 1)
