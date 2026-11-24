"""
Tests for world.combat_styles and the style half of world.skill_base --
twelve weapon types and seven Combat Styles as data (Body decomposition
BD-T6; locks BD1-BD4, CS2; OQ-BD3; Gear decomposition GR-T1, lock GR15;
Legend core pp. 14, 124; Arms of Legend pp. 71 ff.).

The fixture's characteristics are the placeholder 10s, so a close style and
a ranged one both start at 20; a test that must tell STR + DEX from DEX x 2
moves one characteristic first. Every expected table is typed here by hand,
not read from the module.
"""

from unittest import TestCase

from evennia.contrib.rpg.traits import TraitHandler
from evennia.utils.test_resources import EvenniaTest

from world import combat_styles, skill_base
from world.chargen import SKILL_BASE_PAIRS
from world.progression import xp_threshold

TWELVE = [
    "sword", "knife", "axe", "bludgeon", "flail", "spear",
    "polearm", "shield", "bow", "crossbow", "sling", "thrown",
]

# key: (name, main type, hand, second-hand type, ranged)
SEVEN = {
    "style_knife": ("Knife", "knife", "1H", None, False),
    "style_mace_shield": ("Mace and Shield", "bludgeon", "1H", "shield", False),
    "style_axe_shield": ("Axe and Shield", "axe", "1H", "shield", False),
    "style_spear_shield": ("Spear and Shield", "spear", "1H", "shield", False),
    "style_bow": ("Bow", "bow", "2H", None, True),
    "style_sling": ("Sling", "sling", "1H", None, True),
    # GR15: the quarterstaff is two-handed in AoL's close combat table.
    "style_staff": ("Staff", "bludgeon", "2H", None, False),
}
CLOSE = [
    "style_axe_shield", "style_knife", "style_mace_shield", "style_spear_shield",
    "style_staff",
]
RANGED = ["style_bow", "style_sling"]

WORDS = ("untried", "green", "drilled", "steady", "seasoned", "deadly")
TOPS = [19, 39, 59, 79, 94, 100]
# Both ends of every band, and far above the last key.
BAND_EDGES = (
    (0, 0), (19, 0), (20, 1), (39, 1), (40, 2), (59, 2),
    (60, 3), (79, 3), (80, 4), (94, 4), (95, 5), (100, 5), (200, 5),
)
NINE = [
    "athletics", "brawn", "craft", "evade", "hunting",
    "perception", "resilience", "stealth", "unarmed",
]


class TestTheVocabulary(TestCase):
    """
    Pressures the data (BD1, BD2, BD4): a type dropped or misspelt, a style
    that names a type outside the list (BDM16) or a hand that is no hand,
    and a row that drifted from the table Adam locked.
    """

    def test_the_twelve_types(self):
        self.assertEqual(list(combat_styles.WEAPON_TYPES), TWELVE)
        self.assertEqual(len(set(combat_styles.WEAPON_TYPES)), 12)

    def test_unarmed_is_no_weapon_type(self):
        self.assertNotIn("unarmed", combat_styles.WEAPON_TYPES)

    def test_the_seven_styles_as_locked(self):
        got = {
            key: (row["name"], row["main"], row["hand"], row["second"], row["ranged"])
            for key, row in combat_styles.STYLES.items()
        }
        self.assertEqual(got, SEVEN)

    def test_every_style_names_types_from_the_list(self):
        for key, row in combat_styles.STYLES.items():
            with self.subTest(style=key):
                self.assertIn(row["main"], combat_styles.WEAPON_TYPES)
                if row["second"] is not None:
                    self.assertIn(row["second"], combat_styles.WEAPON_TYPES)
                self.assertIn(row["hand"], combat_styles.HANDS)

    def test_names_are_unique(self):
        names = [row["name"] for row in combat_styles.STYLES.values()]
        self.assertEqual(len(set(names)), len(names))

    def test_a_ranged_style_reads_dex_twice(self):
        for key in CLOSE:
            self.assertEqual(combat_styles.pair_for(key), ("str", "dex"))
        for key in RANGED:
            self.assertEqual(combat_styles.pair_for(key), ("dex", "dex"))

    def test_an_unknown_style_has_no_pair(self):
        with self.assertRaises(KeyError):
            combat_styles.pair_for("style_juggling")


class TestKeysCannotMeet(TestCase):
    """
    Pressures OQ-BD3: a style whose key could be a Common skill's or a
    weapon type's (a style called Knife beside the type `knife`), and a
    style's pair leaking into chargen's table, where `apply_allocation`
    would refuse every character that has not used the style.
    """

    def test_every_style_key_has_the_prefix(self):
        self.assertEqual(combat_styles.STYLE_PREFIX, "style_")
        for key in combat_styles.STYLES:
            with self.subTest(style=key):
                self.assertTrue(key.startswith("style_"))

    def test_no_common_skill_has_the_prefix(self):
        for key in SKILL_BASE_PAIRS:
            with self.subTest(skill=key):
                self.assertFalse(key.startswith("style_"))

    def test_no_style_is_in_chargens_table(self):
        self.assertEqual(set(combat_styles.STYLES) & set(SKILL_BASE_PAIRS), set())

    def test_no_style_key_is_a_weapon_type(self):
        self.assertEqual(
            set(combat_styles.STYLES) & set(combat_styles.WEAPON_TYPES), set()
        )


class TestAStyleNobodyHasUsed(EvenniaTest):
    """
    Pressures BD3: a style with no trait read as nothing (the red receipt),
    a ranged style reading STR + DEX (BDM14), `.value` read for a
    characteristic's `.base`, and a read that leaves a trait behind.
    """

    character_typeclass = "typeclasses.characters.Character"

    def test_every_style_is_twenty_on_the_placeholders(self):
        for key in SEVEN:
            with self.subTest(style=key):
                self.assertEqual(skill_base.value_of(self.char1, key), 20)
                self.assertEqual(skill_base.base_for(self.char1, key), 20)

    def test_dex_counts_once_in_close_combat_and_twice_at_range(self):
        self.char1.stats.dex.base = 14
        for key in CLOSE:
            with self.subTest(style=key):
                self.assertEqual(skill_base.value_of(self.char1, key), 24)
        for key in RANGED:
            with self.subTest(style=key):
                self.assertEqual(skill_base.value_of(self.char1, key), 28)

    def test_str_moves_only_the_close_styles(self):
        self.char1.stats.str.base = 13
        for key in CLOSE:
            with self.subTest(style=key):
                self.assertEqual(skill_base.value_of(self.char1, key), 23)
        for key in RANGED:
            with self.subTest(style=key):
                self.assertEqual(skill_base.value_of(self.char1, key), 20)

    def test_the_base_ignores_a_modifier(self):
        self.char1.stats.dex.mod = 5
        self.assertEqual(skill_base.value_of(self.char1, "style_bow"), 20)

    def test_reading_makes_no_trait(self):
        for key in SEVEN:
            skill_base.value_of(self.char1, key)
        self.assertEqual(sorted(self.char1.skills.all()), NINE)

    def test_an_unknown_style_is_none(self):
        self.assertIsNone(skill_base.value_of(self.char1, "style_juggling"))

    def test_a_missing_characteristic_is_none(self):
        self.char1.stats.remove("dex")
        self.assertIsNone(skill_base.value_of(self.char1, "style_knife"))


class TestEnsureStyle(EvenniaTest):
    """
    Pressures the first use (BD3): a trait made at a flat number instead of
    the base, a second call that makes a second trait or writes over a
    trained value (BDM15), a ceiling on the trait (P-7), a Common skill
    accepted as a style, and a trait written with no base to give it.
    """

    character_typeclass = "typeclasses.characters.Character"

    def test_the_trait_is_made_at_the_base(self):
        self.char1.stats.str.base = 12
        self.char1.stats.dex.base = 13
        close = skill_base.ensure_style(self.char1, "style_spear_shield")
        ranged = skill_base.ensure_style(self.char1, "style_bow")
        self.assertEqual((close.base, close.current, close.mod), (25, 25, 0))
        self.assertEqual((ranged.base, ranged.current, ranged.mod), (26, 26, 0))

    def test_the_trait_carries_the_styles_name(self):
        for key, row in SEVEN.items():
            with self.subTest(style=key):
                trait = skill_base.ensure_style(self.char1, key)
                self.assertEqual(trait.name, row[0])
                self.assertIs(self.char1.skills.get(key).name, trait.name)

    def test_no_ceiling(self):
        trait = skill_base.ensure_style(self.char1, "style_knife")
        self.assertIsNone(trait.max)
        trait.current = 140
        self.assertEqual(trait.current, 140)

    def test_twice_makes_one_trait(self):
        skill_base.ensure_style(self.char1, "style_knife")
        skill_base.ensure_style(self.char1, "style_knife")
        self.assertEqual(sorted(self.char1.skills.all()), sorted(NINE + ["style_knife"]))

    def test_a_trained_value_is_kept(self):
        skill_base.ensure_style(self.char1, "style_knife").current = 47
        self.char1.stats.dex.base = 15   # the base a new trait would get moves
        again = skill_base.ensure_style(self.char1, "style_knife")
        self.assertEqual((again.base, again.current), (20, 47))

    def test_value_of_then_reads_the_trait(self):
        skill_base.ensure_style(self.char1, "style_bow").current = 33
        self.char1.stats.dex.base = 15
        self.assertEqual(skill_base.value_of(self.char1, "style_bow"), 33)

    def test_the_trait_is_in_the_database(self):
        skill_base.ensure_style(self.char1, "style_sling")
        fresh = TraitHandler(
            self.char1, db_attribute_key="skills", db_attribute_category="skills"
        )
        self.assertEqual(fresh.get("style_sling").current, 20)

    def test_an_unknown_key_raises(self):
        with self.assertRaises(KeyError):
            skill_base.ensure_style(self.char1, "style_juggling")

    def test_a_common_skill_is_no_style(self):
        self.char1.skills.remove("evade")
        with self.assertRaises(KeyError):
            skill_base.ensure_style(self.char1, "evade")
        self.assertIsNone(self.char1.skills.get("evade"))

    def test_without_a_base_nothing_is_written(self):
        self.char1.stats.remove("dex")
        self.assertIsNone(skill_base.ensure_style(self.char1, "style_knife"))
        self.assertEqual(sorted(self.char1.skills.all()), NINE)


class TestAStyleAmongTheSkills(EvenniaTest):
    """
    Pressures what a style trait meets once it exists: `skills.all()` not
    listing it, the XP handler having no floor for it, a ladder that never
    reached the trait or reads a rung early, and the ladder migration
    passing a style by or inventing one.
    """

    character_typeclass = "typeclasses.characters.Character"

    def test_a_fresh_character_has_no_style(self):
        self.assertEqual(sorted(self.char1.skills.all()), NINE)

    def test_a_used_style_is_listed(self):
        skill_base.ensure_style(self.char1, "style_mace_shield")
        self.assertIn("style_mace_shield", self.char1.skills.all())

    def test_the_xp_handler_derives_its_entry(self):
        self.char1.stats.str.base = 14
        skill_base.ensure_style(self.char1, "style_axe_shield")
        self.assertEqual(
            self.char1.skill_xp.all()["style_axe_shield"], xp_threshold(24)
        )

    def test_every_style_has_the_shared_ladder(self):
        for key in SEVEN:
            with self.subTest(style=key):
                self.assertEqual(tuple(skill_base.SKILL_LADDERS[key]), WORDS)
                self.assertEqual(
                    list(skill_base.ladder(key).items()), list(zip(TOPS, WORDS))
                )

    def test_a_style_reads_its_word_at_both_ends_of_every_band(self):
        trait = skill_base.ensure_style(self.char1, "style_knife")
        for value, rung in BAND_EDGES:
            with self.subTest(value=value):
                trait.current = value
                self.assertEqual(trait.desc(), WORDS[rung])

    def test_the_ladder_migration_covers_a_style(self):
        from world.character_migrations import backfill_skill_ladders

        trait = skill_base.ensure_style(self.char1, "style_knife")
        trait.descs = dict(zip((0, 20, 40, 60, 80, 95), WORDS))
        trait.current = 25
        self.assertEqual(trait.desc(), "drilled")   # one rung early
        result = backfill_skill_ladders()
        self.assertIn("style_knife", result)
        self.assertEqual(self.char1.skills.get("style_knife").desc(), "green")
        self.assertEqual(self.char1.skills.get("style_knife").current, 25)

    def test_the_ladder_migration_invents_no_style(self):
        from world.character_migrations import backfill_skill_ladders

        backfill_skill_ladders()
        self.assertEqual(sorted(self.char1.skills.all()), NINE)

    def test_no_style_is_declared_improvable(self):
        # BD8: styles get their own rule in ML; the fixed set stays as it is.
        self.assertEqual(
            set(self.char1.improvable_skills) & set(combat_styles.STYLES), set()
        )
