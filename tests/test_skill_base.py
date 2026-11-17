"""
Tests for world.skill_base -- a skill's value with or without its trait
(Body decomposition BD-T3; locks BD3, BD6; Legend core p. 14).

The fixture's characteristics are the placeholder 10s, so every pair's base
is 20 until a test moves one. Expected numbers are typed, not read from the
pair tables.
"""

from evennia.utils.test_resources import EvenniaTest

from world import skill_base
from world.chargen import SKILL_BASE_PAIRS


def add_skill(char, key, value):
    """A counter trait shaped like the character's own skills."""
    char.skills.add(
        key, key.title(), trait_type="counter",
        base=value, current=value, mod=0, min=0,
    )


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
        self.assertIsNone(self.char1.skills.get("resilience"))
        self.assertEqual(skill_base.value_of(self.char1, "resilience"), 20)

    def test_with_the_trait_its_value(self):
        add_skill(self.char1, "resilience", 45)
        self.assertEqual(skill_base.value_of(self.char1, "resilience"), 45)

    def test_a_trained_skill_is_not_its_base(self):
        self.char1.skills.athletics.current = 60
        self.assertEqual(skill_base.value_of(self.char1, "athletics"), 60)

    def test_neither_trait_nor_characteristic_is_none(self):
        self.char1.stats.remove("con")
        self.assertIsNone(skill_base.value_of(self.char1, "resilience"))


class TestPendingPairs(EvenniaTest):
    """
    Pressures OQ-BD6's hand-over: a pair moved into chargen's table and
    left behind here would be two answers to one question.
    """

    def test_no_key_in_both_tables(self):
        self.assertEqual(set(skill_base.PENDING_PAIRS) & set(SKILL_BASE_PAIRS), set())
