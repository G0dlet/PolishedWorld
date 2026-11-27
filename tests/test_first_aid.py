"""
Tests for `first_aid`, a Common skill every character has. Healing
decomposition, Task HL-T4 (lock HL2; Legend core p. 14).

WHY ONE TASK
------------
`chargen.apply_allocation` refuses a character with a base pair and no
trait, so the pair (`chargen.SKILL_BASE_PAIRS`), the six words
(`skill_base.SKILL_LADDERS`), the trait at creation and the backfill land
together. `first_aid` stands in a table of its own,
`skill_base.FIRST_AID_TRAITS`: `COMBAT_SKILL_TRAITS` stays what combat
reads (BD5), and `backfill_combat_skills` keeps its meaning on a database it
has already run on.

It is NOT in `improvable_skills`: the label and the call move together
(HL6), in HL-T9, which builds the test that rolls it.

WHAT EACH CLASS PUTS PRESSURE ON
--------------------------------
* TestTheTable -- one row, its name and its six words; `trait_kwargs`
  answers for it.
* TestOnCreation -- a new character has the trait, made as the table says
  (HLM13); `apply_allocation` passes and writes INT + DEX, not INT + POW
  (HLM11). Red against the pair added alone: the allocation is refused.
* TestBackfill -- the character's own INT + DEX; a trained value left as it
  is (HLM12); a second run changes nothing; a character without INT skipped
  by name; one broken character does not stop the rest; `apply_allocation`
  passes for a character made before and backfilled; `value_of` answers the
  base for a character the backfill missed (BD6's net).

The fixture's INT 12, DEX 9 and POW 17 give 21 by INT + DEX and 29 by
INT + POW, so the wrong pair cannot pass. Expected numbers are typed by
hand, never read from the pair table.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_first_aid
"""

from unittest import mock

from evennia import create_object
from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character
from world import skill_base
from world.chargen import apply_allocation

# tests/test_chargen.py's legal allocation.
VALID = {"str": 7, "dex": 9, "con": 14, "siz": 8, "int": 12, "pow": 17, "cha": 13}
OWN_SUM = 21  # INT 12 + DEX 9; INT + POW would give 29

WORDS = ("squeamish", "fumbling", "steady", "deft", "sure-handed", "unflinching")


def _backfill():
    # Imported per call so that each test is red on its own before the
    # function exists.
    from world.character_migrations import backfill_first_aid

    return backfill_first_aid()


class TestTheTable(EvenniaTest):
    def test_one_row(self):
        self.assertEqual(sorted(skill_base.FIRST_AID_TRAITS), ["first_aid"])

    def test_its_name_and_six_words(self):
        spec = skill_base.FIRST_AID_TRAITS["first_aid"]
        self.assertEqual(spec["name"], "First Aid")
        self.assertEqual(list(spec["descs"]), [19, 39, 59, 79, 94, 100])
        self.assertEqual(tuple(spec["descs"].values()), WORDS)

    def test_trait_kwargs_answers_for_it(self):
        kwargs = skill_base.trait_kwargs(self.char1, "first_aid")
        stats = self.char1.stats
        total = int(stats.int.base) + int(stats.dex.base)
        self.assertEqual((kwargs["base"], kwargs["current"]), (total, total))

    def test_it_is_not_a_combat_skill(self):
        self.assertNotIn("first_aid", skill_base.COMBAT_SKILL_TRAITS)

    def test_it_is_not_trainable_yet(self):
        # HL6: the label moves with the call, in HL-T9.
        self.assertNotIn("first_aid", self.char1.improvable_skills)


class TestOnCreation(EvenniaTest):
    def test_a_new_character_has_the_trait_at_int_plus_dex(self):
        trait = self.char1.skills.get("first_aid")
        self.assertIsNotNone(trait)
        stats = self.char1.stats
        total = int(stats.int.base) + int(stats.dex.base)
        self.assertEqual(
            (trait.name, trait.trait_type, trait.base, trait.current, trait.mod),
            ("First Aid", "counter", total, total, 0),
        )
        self.assertEqual(trait.descs, skill_base.ladder("first_aid"))

    def test_the_allocation_writes_int_plus_dex(self):
        derived = apply_allocation(self.char1, VALID)
        self.assertEqual(derived["first_aid"], OWN_SUM)
        trait = self.char1.skills.get("first_aid")
        self.assertEqual((trait.base, trait.current), (OWN_SUM, OWN_SUM))


class _Old(EvenniaTest):
    """`self.old` is a character made before HL-T4: its own characteristics, no `first_aid`."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.old = self._old("Oldtimer")

    def _old(self, key):
        char = create_object(Character, key=key, location=self.room1)
        for stat, value in VALID.items():
            char.stats.get(stat).base = value
        char.skills.remove("first_aid")
        return char


class TestBackfill(_Old):
    def test_the_fixture_has_no_first_aid(self):
        # Receipt: the tests below start from a character that lacks it.
        self.assertIsNone(self.old.skills.get("first_aid"))

    def test_the_characters_own_int_plus_dex(self):
        said = _backfill()
        trait = self.old.skills.get("first_aid")
        self.assertEqual(
            (trait.name, trait.base, trait.current), ("First Aid", OWN_SUM, OWN_SUM)
        )
        self.assertEqual(trait.descs, skill_base.ladder("first_aid"))
        self.assertIn("changed 1 ['Oldtimer']", said)
        # char1 and char2 were made with it.
        self.assertIn("unchanged 2", said)

    def test_a_trained_value_is_left_as_it_is(self):
        self.old.skills.add(
            "first_aid", "First Aid", trait_type="counter",
            base=OWN_SUM, current=47, mod=0, min=0,
        )
        said = _backfill()
        trait = self.old.skills.get("first_aid")
        self.assertEqual((trait.base, trait.current), (OWN_SUM, 47))
        self.assertIn("changed 0 ", said)

    def test_a_second_run_changes_nothing(self):
        _backfill()
        self.old.skills.get("first_aid").current = 33   # trained since
        said = _backfill()
        self.assertIn("changed 0 ", said)
        self.assertEqual(self.old.skills.get("first_aid").current, 33)

    def test_without_int_the_character_is_skipped_by_name(self):
        noint = self._old("Noint")
        noint.stats.remove("int")
        with mock.patch.object(
            Character.objects, "all_family", return_value=[noint, self.old]
        ):
            said = _backfill()
        self.assertIn("skipped 1 ['Noint (no base for first_aid)']", said)
        self.assertIsNone(noint.skills.get("first_aid"))
        # And the next one is still served.
        self.assertEqual(self.old.skills.get("first_aid").current, OWN_SUM)

    def test_one_broken_character_does_not_stop_the_batch(self):
        broken = mock.Mock()
        broken.key = "Broken"
        broken.skills.get.side_effect = RuntimeError("no database")
        with mock.patch.object(
            Character.objects, "all_family", return_value=[broken, self.old]
        ):
            said = _backfill()
        self.assertIn("Broken (ERROR: no database)", said)
        self.assertEqual(self.old.skills.get("first_aid").current, OWN_SUM)

    def test_the_allocation_passes_for_a_backfilled_character(self):
        # HL2: without the trait it refuses; that is why the four parts are one task.
        with self.assertRaises(ValueError):
            apply_allocation(self.old, VALID)
        _backfill()
        derived = apply_allocation(self.old, VALID)
        self.assertEqual(derived["first_aid"], OWN_SUM)

    def test_value_of_answers_the_base_for_a_character_missed(self):
        # BD6's net: a reader is not left with None before the backfill.
        self.assertEqual(skill_base.value_of(self.old, "first_aid"), OWN_SUM)
