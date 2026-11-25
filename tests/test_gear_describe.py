"""
Tests for what an item says of itself on `look` (Gear decomposition
GR-T11; lock GR23): one line from the row, between the description and
the condition, a need the looker does not meet in red.

GR-T11's STOPP 0: a weapon's line in sentences, the book's letters and
dice, the hand in words, no *Needs* when nothing is needed; an armour's
line by layer, Armour Points spelled out, the locations in the row's
order; the stone knife and axe read as every weapon; `|r` on the unmet
need alone, met at `>=`, and plain for a looker with nothing to compare.

Every expected line is typed here by hand from §3's rows and STOPP 0's
forms, not built from the module, so a line that drifts fails whole.
"""

from evennia.prototypes.spawner import spawn
from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

from world import gear

CHARACTER = "typeclasses.characters.Character"

WEAPON_LINES = {
    "club": "A bludgeon for one hand. Damage 1D6, Size M, Reach S. Needs STR 7.",
    "quarterstaff": (
        "A bludgeon for two hands. Damage 1D8, Size M, Reach L. Needs STR 7 and DEX 7."),
    "spear": "A spear for one hand. Damage 1D8+1, Size M, Reach L. Needs STR 5 and DEX 5.",
    "stone_knife": "A knife for one hand. Damage 1D3, Size S, Reach S.",
    "stone_axe": "An axe for one hand. Damage 1D6, Size S, Reach S. Needs DEX 9.",
    "target_shield": "A shield for one hand. Damage 1D6, Size L, Reach S. Needs STR 9.",
    "bow": (
        "A bow for two hands. Damage 1D6, Size L, Range 80 m, Load 1. "
        "Needs STR 9 and DEX 11."),
    "sling": "A sling for one hand. Damage 1D8, Size L, Range 200 m, Load 1. Needs DEX 11.",
}

ARMOUR_LINES = {
    "linen_cuirass": "Padding armour: 2 Armour Points on the chest.",
    "soft_leather_trews": (
        "Padding armour: 1 Armour Point on the abdomen, right leg, and left leg."),
    "hard_leather_hauberk": "Flexible armour: 2 Armour Points on the chest and abdomen.",
    "hard_leather_vambraces": (
        "Flexible armour: 2 Armour Points on the right arm and left arm."),
    "bone_armour": "Rigid armour: 2 Armour Points on the chest.",
    "bone_helm": "Rigid armour: 2 Armour Points on the head.",
}

HAND_WORDS = {"1H": "one hand", "2H": "two hands"}


class _Look(EvenniaTest):
    character_typeclass = CHARACTER

    def _tagged(self, prototype_key):
        """Any object with the tag `spawn` gives: five rows have no prototype
        until GR-T12, and the line reads the tag only."""
        obj = create.create_object("typeclasses.objects.Object", key=prototype_key)
        obj.tags.add(prototype_key, category=gear.PROTOTYPE_TAG_CATEGORY)
        self.addCleanup(obj.delete)
        return obj

    def _spawn(self, prototype_key):
        obj = spawn(prototype_key)[0]
        self.addCleanup(obj.delete)
        return obj

    def _with(self, **values):
        """char1 with these characteristics."""
        for key, value in values.items():
            getattr(self.char1.stats, key).base = value
        return self.char1


class TestTheLines(_Look):
    """With a looker that has no characteristics: every line plain."""

    def test_each_weapon_line(self):
        self.assertEqual(len(WEAPON_LINES), len(gear.WEAPONS))
        for key, expected in WEAPON_LINES.items():
            with self.subTest(item=key):
                self.assertEqual(gear.describe(self._tagged(key), self.obj1), expected)

    def test_each_armour_line(self):
        self.assertEqual(len(ARMOUR_LINES), len(gear.ARMOUR))
        for key, expected in ARMOUR_LINES.items():
            with self.subTest(item=key):
                self.assertEqual(gear.describe(self._tagged(key), self.obj1), expected)

    def test_no_row_no_line(self):
        self.assertIsNone(gear.describe(self._spawn("wool_tunic"), self.obj1))
        self.assertIsNone(gear.describe(self.obj2, self.obj1))


class TestTheCensus(_Look):
    """Every shown field of every row is in its line: a field added to the
    line's code but dropped from a row, or the reverse, shows here."""

    def test_every_weapon_field_shows(self):
        for key, row in gear.WEAPONS.items():
            line = gear.describe(self._tagged(key), self.obj1)
            with self.subTest(item=key):
                self.assertIn(f" {row['weapon_type']} for ", line)
                self.assertIn(f" for {HAND_WORDS[row['hand']]}.", line)
                self.assertIn(f"Damage {row['damage']},", line)
                self.assertIn(f"Size {row['size']}", line)
                for field, label in (("reach", "Reach"), ("range_m", "Range"),
                                     ("load", "Load"), ("str_min", "STR"),
                                     ("dex_min", "DEX")):
                    if row[field] is None:
                        self.assertNotIn(f"{label} ", line)
                    else:
                        self.assertIn(f"{label} {row[field]}", line)

    def test_every_armour_field_shows(self):
        for key, row in gear.ARMOUR.items():
            line = gear.describe(self._tagged(key), self.obj1)
            with self.subTest(item=key):
                self.assertTrue(line.startswith(row["layer"].split("_")[1].capitalize()))
                self.assertIn(f": {row['ap']} Armour Point", line)
                for location in row["locations"]:
                    self.assertIn(location.replace("_", " "), line)


class TestTheColour(_Look):
    def test_a_need_not_met_is_red(self):
        line = gear.describe(self._tagged("club"), self._with(str=6))
        self.assertTrue(line.endswith(" Needs |rSTR 7|n."))

    def test_a_need_met_exactly_is_plain(self):
        line = gear.describe(self._tagged("club"), self._with(str=7))
        self.assertTrue(line.endswith(" Needs STR 7."))

    def test_each_need_is_coloured_on_its_own(self):
        bow = self._tagged("bow")
        self.assertTrue(gear.describe(bow, self._with(str=9, dex=10)).endswith(
            " Needs STR 9 and |rDEX 11|n."))
        self.assertTrue(gear.describe(bow, self._with(str=8, dex=10)).endswith(
            " Needs |rSTR 9|n and |rDEX 11|n."))

    def test_a_looker_with_no_characteristics_sees_it_plain(self):
        self.assertEqual(
            gear.describe(self._tagged("bow"), self.obj1), WEAPON_LINES["bow"])


class TestLook(_Look):
    """The line between the description and the condition (GR23)."""

    def test_a_club_reads_description_line_condition(self):
        club = self._spawn("club")
        self.assertEqual(
            club.get_display_desc(self._with(str=10)),
            f"{club.db.desc}\n\n{WEAPON_LINES['club']}\n\nCondition: |g100%|n",
        )

    def test_a_stone_knife_reads_as_every_weapon(self):
        knife = self._spawn("stone_knife")
        self.assertEqual(
            knife.get_display_desc(self.char1),
            f"{knife.db.desc}\n\n{WEAPON_LINES['stone_knife']}\n\nCondition: |y40%|n",
        )

    def test_a_piece_of_armour_reads_its_line(self):
        cuirass = self._spawn("linen_cuirass")
        self.assertEqual(
            cuirass.get_display_desc(self.char1),
            f"{cuirass.db.desc}\n\n{ARMOUR_LINES['linen_cuirass']}\n\nCondition: |g100%|n",
        )

    def test_a_tunic_has_no_line(self):
        tunic = self._spawn("wool_tunic")
        self.assertEqual(
            tunic.get_display_desc(self.char1), f"{tunic.db.desc}\n\nCondition: |g100%|n")
