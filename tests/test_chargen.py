"""
Tests for world/chargen.py (Character Creation, Task CC1.1).

Each class presses one bug:

    TestValidateAllocation   the Legend p.9 boundaries -- 6-18, 80 spent, the
                             "one 20" trap, and the values StaticTrait's base
                             setter would mishandle silently (bool, "12")
    TestDeriveSkillBases     a wrong characteristic pair
    TestApplyAllocation      a forgotten `.current` write, a forgotten health
                             recalculation, a `_SaverDict` refused as a dict
    TestApplyRefuses         a half-applied character; a re-spec over banked XP
                             or over a profession's bonus (CC2.1)
    TestApplyDoesNotWriteXP  a backfill

THE FIXTURE (lesson 74)
-----------------------
VALID has seven distinct values, none of them 10 and CON not 10, so that every
read-back differs from the default character's 10s; and its derived bases
(16/29/21/21/26) differ from today's fixed 25/25/20/20/25 and from each other
where the pairs differ. Under all-10s every pair sums to 20 and a wrong pair,
a skipped write or a skipped health recalculation would all pass unseen. The
expected bases are written out by hand below, never recomputed from
SKILL_BASE_PAIRS -- a test that read the table it checks would prove nothing.
"""

from collections.abc import Mapping

from evennia.utils.test_resources import EvenniaTest, EvenniaTestCase

from world.chargen import (
    CHAR_MAX,
    CHAR_MIN,
    DESIGN_POINTS,
    STAT_KEYS,
    apply_allocation,
    derive_skill_bases,
    validate_allocation,
)
from world.professions import grant_profession
from world.progression import xp_threshold

VALID = {"str": 7, "dex": 9, "con": 14, "siz": 8, "int": 12, "pow": 17, "cha": 13}

EXPECTED_BASES = {
    "athletics": 16,   # STR 7 + DEX 9
    "perception": 29,  # INT 12 + POW 17
    "stealth": 21,     # DEX 9 + INT 12
    "craft": 21,       # DEX 9 + INT 12
    "hunting": 26,     # INT 12 + CON 14 (Track; INT+POW would give 29)
}

ALL_TENS_PLUS_TWENTY = {key: 10 for key in STAT_KEYS} | {"cha": 20}


def _with(**changes):
    """VALID with some values replaced."""
    return VALID | changes


class TestValidateAllocation(EvenniaTestCase):
    """Legend p.9: 80 points, 1 per point, 6-18, all spent."""

    def test_fixture_is_valid(self):
        self.assertEqual(sum(VALID.values()), DESIGN_POINTS)
        self.assertEqual(validate_allocation(VALID), [])

    def test_rule_constants(self):
        # Rules, not knobs: a change here is a change to Legend p.9.
        self.assertEqual((DESIGN_POINTS, CHAR_MIN, CHAR_MAX), (80, 6, 18))

    def test_underspent_is_refused(self):
        errors = validate_allocation(_with(cha=12))
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("79 of 80", errors[0])

    def test_overspent_is_refused(self):
        errors = validate_allocation(_with(cha=14))
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("81 points", errors[0])

    def test_below_minimum_is_refused(self):
        alloc = _with(str=5, cha=15)  # total still 80: only the 5 is wrong
        self.assertEqual(sum(alloc.values()), DESIGN_POINTS)
        errors = validate_allocation(alloc)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("STR is 5", errors[0])

    def test_above_maximum_is_refused(self):
        alloc = _with(pow=19, siz=6)  # total still 80: only the 19 is wrong
        self.assertEqual(sum(alloc.values()), DESIGN_POINTS)
        errors = validate_allocation(alloc)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("POW is 19", errors[0])

    def test_one_twenty_trap_is_refused_on_the_twenty_not_the_sum(self):
        # 10 x 6 + 20 = 80: the sum is legal, the 20 is not.
        self.assertEqual(sum(ALL_TENS_PLUS_TWENTY.values()), DESIGN_POINTS)
        errors = validate_allocation(ALL_TENS_PLUS_TWENTY)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("CHA is 20", errors[0])

    def test_missing_key_is_refused_without_a_sum_error(self):
        alloc = dict(VALID)
        del alloc["siz"]
        errors = validate_allocation(alloc)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("SIZ", errors[0])

    def test_unknown_key_is_refused(self):
        errors = validate_allocation(_with(luck=10))
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("'luck'", errors[0])

    def test_string_value_is_refused(self):
        alloc = _with(dex="9")
        self.assertIs(type(alloc["dex"]), str)  # §11k: the negative case's type
        errors = validate_allocation(alloc)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("DEX must be a whole number", errors[0])

    def test_bool_value_is_refused(self):
        # §11k: why a naive isinstance(value, int) is not enough.
        self.assertIsInstance(True, int)
        errors = validate_allocation(_with(con=True))
        self.assertTrue(any("CON must be a whole number" in e for e in errors), errors)

    def test_non_mapping_is_refused(self):
        for bad in (None, [("str", 10)], "str=10"):
            with self.subTest(bad=bad):
                self.assertEqual(len(validate_allocation(bad)), 1)


class TestDeriveSkillBases(EvenniaTestCase):
    """CC5 + OQ1: each skill's base is the sum of its own pair."""

    def test_each_skill_reads_its_own_pair(self):
        self.assertEqual(derive_skill_bases(VALID), EXPECTED_BASES)

    def test_integers_in_integers_out(self):
        for skill, base in derive_skill_bases(VALID).items():
            with self.subTest(skill=skill):
                self.assertIs(type(base), int)

    def test_is_pure(self):
        before = dict(VALID)
        derive_skill_bases(VALID)
        self.assertEqual(VALID, before)


class TestApplyAllocation(EvenniaTest):
    """The writes land, on both halves of every CounterTrait."""

    def setUp(self):
        super().setUp()
        self.derived = apply_allocation(self.char1, VALID)

    def test_returns_the_derived_bases(self):
        self.assertEqual(self.derived, EXPECTED_BASES)

    def test_characteristics_read_back(self):
        for key, value in VALID.items():
            with self.subTest(stat=key):
                stat = self.char1.stats.get(key)
                self.assertEqual(stat.base, value)
                self.assertEqual(stat.value, value)

    def test_skills_read_back_on_base_and_current(self):
        for key, base in EXPECTED_BASES.items():
            with self.subTest(skill=key):
                skill = self.char1.skills.get(key)
                self.assertEqual(skill.base, base)
                self.assertEqual(skill.current, base)

    def test_health_max_is_con_times_two_and_full(self):
        health = self.char1.traits.health
        self.assertEqual(health.max, VALID["con"] * 2)  # 28, not the default 20
        self.assertEqual(health.current, health.max)

    def test_accepts_a_saverdict(self):
        self.char1.db.chargen_alloc = VALID
        saved = self.char1.db.chargen_alloc
        # §11k: the round trip really produced the type the gotcha is about.
        self.assertIsInstance(saved, Mapping)
        self.assertNotIsInstance(saved, dict)
        self.assertEqual(validate_allocation(saved), [])


class TestApplyRefuses(EvenniaTest):
    """A refused call writes nothing at all."""

    def _snapshot(self):
        return (
            {key: self.char1.stats.get(key).base for key in STAT_KEYS},
            {key: (self.char1.skills.get(key).base, self.char1.skills.get(key).current)
             for key in EXPECTED_BASES if self.char1.skills.get(key) is not None},
            self.char1.traits.health.max,
        )

    def test_invalid_allocation_raises_and_writes_nothing(self):
        before = self._snapshot()
        self.assertEqual(before[0], {key: 10 for key in STAT_KEYS})
        with self.assertRaises(ValueError) as caught:
            apply_allocation(self.char1, ALL_TENS_PLUS_TWENTY)
        self.assertIn("CHA is 20", str(caught.exception))
        self.assertEqual(self._snapshot(), before)

    def test_banked_xp_is_refused_and_writes_nothing(self):
        # Seeded through the real handler, not by naming the Attribute: a
        # guard reading the wrong Attribute name must fail this test.
        self.char1.skill_xp.add("craft", 5)
        store = self.char1.attributes.get("skill_xp")
        # §11k: the negative case's type and the key the guard checks.
        self.assertIsInstance(store, Mapping)
        self.assertNotIsInstance(store, dict)
        self.assertIn("craft", store)
        before = self._snapshot()
        with self.assertRaises(ValueError) as caught:
            apply_allocation(self.char1, VALID)
        self.assertIn("banked skill XP", str(caught.exception))
        self.assertEqual(self._snapshot(), before)

    def test_profession_is_refused_and_writes_nothing(self):
        # CC2.1: allocation comes before the profession. Seeded through the
        # real writer, so the bonus this guard protects is really there.
        grant_profession(self.char1, "weaver")
        self.assertEqual(self.char1.skills.get("craft").current, 30)  # 20 + 10
        before = self._snapshot()
        with self.assertRaises(ValueError) as caught:
            apply_allocation(self.char1, VALID)
        self.assertIn("profession", str(caught.exception))
        self.assertEqual(self._snapshot(), before)

    def test_missing_skill_is_refused_and_writes_nothing(self):
        self.char1.skills.remove("hunting")
        self.assertIsNone(self.char1.skills.get("hunting"))  # §11k
        before = self._snapshot()
        with self.assertRaises(ValueError) as caught:
            apply_allocation(self.char1, VALID)
        self.assertIn("hunting", str(caught.exception))
        self.assertEqual(self._snapshot(), before)


class TestApplyDoesNotWriteXP(EvenniaTest):
    """CC5/CC7: derive, never backfill (TestReadDoesNotWrite's shape)."""

    def test_no_skill_xp_attribute_after_apply(self):
        self.assertFalse(self.char1.attributes.has("skill_xp"))
        apply_allocation(self.char1, VALID)
        self.assertFalse(self.char1.attributes.has("skill_xp"))

    def test_derived_floor_follows_the_new_base_without_a_write(self):
        apply_allocation(self.char1, VALID)
        for key, base in EXPECTED_BASES.items():
            with self.subTest(skill=key):
                self.assertEqual(self.char1.skill_xp.get(key), xp_threshold(base))
        self.assertFalse(self.char1.attributes.has("skill_xp"))
