"""
Tests for world.skill_base -- a skill's value with or without its trait
(Body decomposition BD-T3; locks BD3, BD6; Legend core p. 14).

The fixture's characteristics are the placeholder 10s, so every pair's base
is 20 until a test moves one. Expected numbers are typed, not read from the
pair tables.

Since BD-T4 a character has Resilience, Evade, Unarmed and Brawn from
creation, so a test of the net removes the trait first: it stands for a
character the backfill missed (BD6).
"""

from evennia.utils.test_resources import EvenniaTest

from world import skill_base
from world.chargen import SKILL_BASE_PAIRS

# The four ladders, typed by hand in band order: 0-19, 20-39, 40-59, 60-79,
# 80-94, 95 upward.
LADDERS = {
    "brawn": ("slight", "wiry", "sturdy", "stout", "burly", "ox-strong"),
    "evade": ("flat-footed", "slow", "wary", "nimble", "quick", "hard to hit"),
    "resilience": ("frail", "soft", "sound", "hardy", "tough", "unbroken"),
    "unarmed": ("harmless", "clumsy", "scrappy", "practised", "hard-fisted", "dangerous"),
}
# Both ends of every band, and far above the last key.
BAND_EDGES = (
    (0, 0), (19, 0), (20, 1), (39, 1), (40, 2), (59, 2),
    (60, 3), (79, 3), (80, 4), (94, 4), (95, 5), (100, 5), (200, 5),
)

NINE = [
    "athletics", "brawn", "craft", "evade", "hunting",
    "perception", "resilience", "stealth", "unarmed",
]


class TestBaseFor(EvenniaTest):
    """
    Pressures the sum: the wrong characteristic, `.value` read for `.base`,
    and a missing characteristic read as zero instead of None.
    """

    def test_resilience_is_con_twice(self):
        self.char1.stats.con.base = 13
        self.assertEqual(skill_base.base_for(self.char1, "resilience"), 26)

    def test_a_chargen_pair_is_read(self):
        # Athletics is STR + DEX.
        self.char1.stats.str.base = 12
        self.char1.stats.dex.base = 13
        self.assertEqual(skill_base.base_for(self.char1, "athletics"), 25)

    def test_the_base_ignores_a_modifier(self):
        # What creation would have written: `.base`, not `.value`.
        self.char1.stats.con.mod = 5
        self.assertEqual(skill_base.base_for(self.char1, "resilience"), 20)

    def test_an_unknown_key_is_none(self):
        self.assertIsNone(skill_base.base_for(self.char1, "juggling"))

    def test_a_missing_characteristic_is_none(self):
        self.char1.stats.remove("con")
        self.assertIsNone(skill_base.base_for(self.char1, "resilience"))

    def test_an_object_without_stats_is_none(self):
        self.assertIsNone(skill_base.base_for(self.room1, "resilience"))


class TestValueOf(EvenniaTest):
    """
    Pressures BD6's net from both sides: the trait ignored when it exists
    (BDM7), and nothing returned when it does not (BDM8).
    """

    def test_without_the_trait_the_base(self):
        self.char1.stats.con.base = 13
        self.char1.skills.remove("resilience")
        self.assertIsNone(self.char1.skills.get("resilience"))
        self.assertEqual(skill_base.value_of(self.char1, "resilience"), 26)

    def test_the_trait_does_not_follow_its_characteristic(self):
        # The other side of the test above: with the trait, CON moves nothing.
        self.char1.stats.con.base = 13
        self.assertEqual(skill_base.value_of(self.char1, "resilience"), 20)

    def test_with_the_trait_its_value(self):
        self.char1.skills.resilience.current = 45
        self.assertEqual(skill_base.value_of(self.char1, "resilience"), 45)

    def test_a_trained_skill_is_not_its_base(self):
        self.char1.skills.athletics.current = 60
        self.assertEqual(skill_base.value_of(self.char1, "athletics"), 60)

    def test_neither_trait_nor_characteristic_is_none(self):
        self.char1.skills.remove("resilience")
        self.char1.stats.remove("con")
        self.assertIsNone(skill_base.value_of(self.char1, "resilience"))


class TestCombatSkillTraits(EvenniaTest):
    """
    Pressures the one table creation and the backfill both read (BD-T4,
    BD-T5): a skill listed with no pair (its base would be None), a ladder
    with a rung missing, and a ladder copied from another skill.
    """

    def test_the_four_and_no_more(self):
        self.assertEqual(
            sorted(skill_base.COMBAT_SKILL_TRAITS),
            ["brawn", "evade", "resilience", "unarmed"],
        )

    def test_every_one_has_a_pair_in_chargens_table(self):
        for key in skill_base.COMBAT_SKILL_TRAITS:
            with self.subTest(skill=key):
                self.assertIn(key, SKILL_BASE_PAIRS)

    def test_names_and_six_rungs(self):
        names = {"brawn": "Brawn", "evade": "Evade",
                 "resilience": "Resilience", "unarmed": "Unarmed"}
        for key, spec in skill_base.COMBAT_SKILL_TRAITS.items():
            with self.subTest(skill=key):
                self.assertEqual(spec["name"], names[key])
                # Upper bounds, in rising order: the contrib reads the dict
                # in the order it was written.
                self.assertEqual(list(spec["descs"]), [19, 39, 59, 79, 94, 100])

    def test_no_word_is_used_twice(self):
        words = [
            word
            for spec in skill_base.COMBAT_SKILL_TRAITS.values()
            for word in spec["descs"].values()
        ]
        self.assertEqual(len(words), 24)
        self.assertEqual(len(set(words)), 24)


class TestTheFourOnACharacter(EvenniaTest):
    """
    Pressures creation (BD5, BD6): a skill left out, a flat placeholder
    instead of the placeholder characteristics' sum (the fixture's Resilience
    must be 20 or healing's numbers move), a ceiling on the trait (P-7), a
    ladder that never reached the trait, and a ladder keyed by the bottom of
    each band, which the contrib reads one rung early.
    """

    character_typeclass = "typeclasses.characters.Character"

    def test_a_fresh_character_has_nine_skills(self):
        self.assertEqual(sorted(self.char1.skills.all()), NINE)

    def test_each_starts_at_the_placeholder_sum(self):
        for key in ("brawn", "evade", "resilience", "unarmed"):
            with self.subTest(skill=key):
                skill = self.char1.skills.get(key)
                self.assertEqual(skill.trait_type, "counter")
                self.assertEqual((skill.base, skill.current, skill.mod), (20, 20, 0))
                self.assertEqual(skill.min, 0)
                self.assertIsNone(skill.max)

    def test_value_of_reads_the_trait(self):
        self.char1.skills.brawn.current = 33
        self.assertEqual(skill_base.value_of(self.char1, "brawn"), 33)

    def test_every_band_reads_its_word_at_both_ends(self):
        # The contrib reads a key as an upper bound. Keyed by each band's
        # bottom (0/20/40/60/80/95) every word comes one rung early: 21 reads
        # the third word and 81 the last.
        for key, words in LADDERS.items():
            skill = self.char1.skills.get(key)
            for value, rung in BAND_EDGES:
                with self.subTest(skill=key, value=value):
                    skill.current = value
                    self.assertEqual(skill.desc(), words[rung])
