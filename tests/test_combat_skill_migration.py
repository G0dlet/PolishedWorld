"""
Tests for backfill_combat_skills. Body decomposition, Task BD-T5 (lock BD6;
Legend core p. 14).

WHY A BACKFILL
--------------
`Character.at_object_creation` adds Resilience, Evade, Unarmed and Brawn
(BD-T4), and it runs only for NEW objects. A character made before has none
of them. Nothing breaks -- `skill_base.value_of` reads the base where the
trait is missing (BD6's net) -- but `skills`, `progress` and `sheet` do not
show the four until the trait exists.

The backfill gives each character the four from ITS OWN characteristics,
not a flat default as `backfill_hunting` did before character creation
existed: a character who chose CON 14 gets Resilience 28.

WHAT EACH CLASS PUTS PRESSURE ON
--------------------------------
* TestBackfill -- own sums and not a flat number (the fixture's four sums
  all differ from 20 and 25); the trait made exactly as creation makes it;
  a skill already there kept whatever its value (BDM12); banked XP under
  another key untouched.
* TestTheBatch -- a second run changes nothing; a character without a
  characteristic is skipped whole and by name and the next one is served;
  one broken character does not stop the rest (BDM13); the result is a
  string `@py` can print.

Expected numbers are typed by hand, never read from the pair table.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_combat_skill_migration
"""

from unittest import mock

from evennia import create_object
from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character

FOUR = ("brawn", "evade", "resilience", "unarmed")

# STR 7, DEX 9, CON 14, SIZ 8 -- tests/test_chargen.py's values.
OWN_STATS = {"str": 7, "dex": 9, "con": 14, "siz": 8}
OWN_SUMS = {
    "brawn": 15,       # STR 7 + SIZ 8
    "evade": 18,       # DEX 9 x 2
    "resilience": 28,  # CON 14 x 2
    "unarmed": 16,     # STR 7 + DEX 9
}


def _backfill():
    # Imported per call so that each test is red on its own before the
    # function exists.
    from world.character_migrations import backfill_combat_skills

    return backfill_combat_skills()


def _facts(char):
    """What a trait is, as a reader meets it: enough to tell two apart."""
    facts = {}
    for key in FOUR:
        trait = char.skills.get(key)
        if trait is None:
            facts[key] = None
            continue
        words = []
        for value in (0, 19, 20, 59, 60, 95, 200):
            trait.current = value
            words.append(trait.desc())
        trait.current = trait.base
        facts[key] = (
            trait.name, trait.trait_type, trait.base, trait.mod,
            trait.min, trait.max, tuple(words),
        )
    return facts


class _Old(EvenniaTest):
    """`self.old` is a character made before BD-T4: its own characteristics, none of the four."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.old = self._old("Oldtimer")

    def _old(self, key, **stats):
        char = create_object(Character, key=key, location=self.room1)
        for stat, value in (OWN_STATS | stats).items():
            char.stats.get(stat).base = value
        for skill in FOUR:
            char.skills.remove(skill)
        return char


class TestBackfill(_Old):
    def test_the_fixture_has_none_of_the_four(self):
        # Receipt: the tests below start from a character that lacks them.
        self.assertEqual([self.old.skills.get(key) for key in FOUR], [None] * 4)

    def test_each_skill_from_the_characters_own_characteristics(self):
        _backfill()
        for key, total in OWN_SUMS.items():
            with self.subTest(skill=key):
                skill = self.old.skills.get(key)
                self.assertEqual((skill.base, skill.current), (total, total))

    def test_a_backfilled_trait_is_a_created_one(self):
        # The same character made today, with the same characteristics set
        # before its skills are re-based -- what the chargen menu does.
        fresh = create_object(Character, key="Fresh", location=self.room1)
        for stat, value in OWN_STATS.items():
            fresh.stats.get(stat).base = value
        for key, total in OWN_SUMS.items():
            fresh.skills.get(key).base = total
            fresh.skills.get(key).current = total
        _backfill()
        self.assertEqual(_facts(self.old), _facts(fresh))

    def test_a_skill_already_there_is_left_as_it_is(self):
        self.old.skills.add(
            "resilience", "Resilience", trait_type="counter",
            base=28, current=60, mod=0, min=0,
        )
        said = _backfill()
        resilience = self.old.skills.get("resilience")
        self.assertEqual((resilience.base, resilience.current), (28, 60))
        # The other three still arrive, and the summary names only those.
        self.assertEqual(self.old.skills.get("brawn").current, 15)
        self.assertIn("Oldtimer (brawn, evade, unarmed)", said)

    def test_banked_xp_under_another_key_is_untouched(self):
        self.old.skill_xp.add("craft", 5)
        before = self.old.skill_xp.get("craft")
        _backfill()
        self.assertEqual(self.old.skill_xp.get("craft"), before)

    def test_healing_reads_the_same_number_before_and_after(self):
        # BD6's net and the backfill agree, so healing does not move.
        from world import healing

        before = healing.resilience(self.old)
        _backfill()
        self.assertEqual((before, healing.resilience(self.old)), (28, 28))


class TestTheBatch(_Old):
    def test_the_result_is_a_string_that_names_the_change(self):
        said = _backfill()
        self.assertIsInstance(said, str)
        self.assertIn("Oldtimer (brawn, evade, resilience, unarmed)", said)

    def test_a_character_with_all_four_is_counted_unchanged(self):
        # char1 and char2 were made with the four; only Oldtimer changes.
        said = _backfill()
        self.assertIn("changed 1 ", said)
        self.assertIn("unchanged 2", said)

    def test_a_second_run_changes_nothing(self):
        _backfill()
        self.old.skills.get("evade").current = 41   # trained since
        before = _facts(self.old)
        said = _backfill()
        self.assertIn("changed 0 ", said)
        self.assertEqual(_facts(self.old), before)

    def test_without_a_characteristic_the_character_is_skipped_whole(self):
        nocon = self._old("Nocon")
        nocon.stats.remove("con")
        with mock.patch.object(
            Character.objects, "all_family", return_value=[nocon, self.old]
        ):
            said = _backfill()
        self.assertIn("skipped 1 ", said)
        self.assertIn("Nocon (no base for resilience)", said)
        # Skipped whole: not three of four.
        self.assertEqual([nocon.skills.get(key) for key in FOUR], [None] * 4)
        # And the next one is still served.
        self.assertEqual(self.old.skills.get("resilience").current, 28)

    def test_one_broken_character_does_not_stop_the_batch(self):
        broken = mock.Mock()
        broken.key = "Broken"
        broken.skills.get.side_effect = RuntimeError("no database")
        with mock.patch.object(
            Character.objects, "all_family", return_value=[broken, self.old]
        ):
            said = _backfill()
        self.assertIn("Broken (ERROR: no database)", said)
        self.assertEqual(self.old.skills.get("resilience").current, 28)
