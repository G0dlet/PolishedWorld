"""
Tests for the skill ladders -- the six words a skill reads as -- and for
backfill_skill_ladders (Body decomposition, Task BD-T5b; BACKLOG *`descs`
tables are read as upper bounds but shaped like lower bounds*, decided
2026-11-22 for the skills).

THE DECISION
------------
A skill's bands are 0-19, 20-39, 40-59, 60-79, 80-94 and 95 upward. The
traits contrib reads a `descs` key as an inclusive UPPER bound and gives the
last word to anything above the last key, so a ladder is keyed by each
band's top: 19, 39, 59, 79, 94, 100. The five older skills were keyed
0/20/40/60/80/95 and read one rung early (25 as the third word, 81 as the
last).

A trait keeps the table it was created with, so characters made before
carry the old one until `backfill_skill_ladders()` has run.

WHAT EACH CLASS PUTS PRESSURE ON
--------------------------------
* TestTheTable -- a word changed or moved, a skill without a ladder, a
  ladder that is not six ascending tops.
* TestEveryBand -- every skill on a real character, at both ends of every
  band (a key off by one fails one end of one band); the hunting backfill's
  defaults drifting from creation.
* TestTheTierLine -- the "reaches a new tier" line follows the same bands,
  through the stored table.
* TestBackfill -- an old table left in place; a value moved by the
  migration; a skill invented for a character that lacks it; the write not
  reaching the database.
* TestTheBatch -- a second run that writes; one broken character stopping
  the rest.

Every word and number is typed by hand.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_skill_ladders
"""

from unittest import mock

from evennia import create_object
from evennia.contrib.rpg.traits import TraitHandler
from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character
from world import skill_base
from world.improvement import tier_for

TOPS = [19, 39, 59, 79, 94, 100]

# Band order: 0-19, 20-39, 40-59, 60-79, 80-94, 95 upward.
LADDERS = {
    "athletics": ("feeble", "weak", "capable", "athletic", "strong", "mighty"),
    "brawn": ("slight", "wiry", "sturdy", "stout", "burly", "ox-strong"),
    "craft": ("unskilled", "novice", "apprentice", "journeyman", "skilled", "master"),
    "evade": ("flat-footed", "slow", "wary", "nimble", "quick", "hard to hit"),
    "hunting": ("helpless", "novice", "competent", "tracker", "hunter", "master hunter"),
    "perception": ("oblivious", "unaware", "attentive", "observant", "sharp", "eagle-eyed"),
    "resilience": ("frail", "soft", "sound", "hardy", "tough", "unbroken"),
    "stealth": ("clumsy", "obvious", "careful", "sneaky", "stealthy", "invisible"),
    "unarmed": ("harmless", "clumsy", "scrappy", "practised", "hard-fisted", "dangerous"),
}
FIVE_OLDER = ("athletics", "craft", "hunting", "perception", "stealth")

# Both ends of every band, and far above the last key.
BAND_EDGES = (
    (0, 0), (19, 0), (20, 1), (39, 1), (40, 2), (59, 2),
    (60, 3), (79, 3), (80, 4), (94, 4), (95, 5), (100, 5), (200, 5),
)


def old_table(key):
    """The table a character made before BD-T5b carries: keyed by band bottoms."""
    return dict(zip((0, 20, 40, 60, 80, 95), LADDERS[key]))


def _backfill():
    # Imported per call so that each test is red on its own before the
    # function exists.
    from world.character_migrations import backfill_skill_ladders

    return backfill_skill_ladders()


class TestTheTable(EvenniaTest):
    def test_nine_skills_with_these_words(self):
        # The Combat Styles' rows (BD-T6) share one ladder and are pressed
        # in tests/test_combat_styles.py; every other row is one of the nine.
        self.assertEqual(
            {
                key: tuple(words)
                for key, words in skill_base.SKILL_LADDERS.items()
                if not key.startswith("style_")
            },
            LADDERS,
        )
        self.assertEqual(len(skill_base.SKILL_LADDERS), 9 + 6)

    def test_a_ladder_is_keyed_by_the_top_of_each_band(self):
        for key, words in LADDERS.items():
            with self.subTest(skill=key):
                ladder = skill_base.ladder(key)
                self.assertEqual(list(ladder), TOPS)
                self.assertEqual(tuple(ladder.values()), words)

    def test_each_call_gives_its_own_dict(self):
        # A trait stores what it is given; two traits must not share one.
        first = skill_base.ladder("craft")
        first[19] = "changed"
        self.assertEqual(skill_base.ladder("craft")[19], "unskilled")

    def test_an_unknown_skill_has_no_ladder(self):
        with self.assertRaises(KeyError):
            skill_base.ladder("juggling")


class TestEveryBand(EvenniaTest):
    character_typeclass = "typeclasses.characters.Character"

    def test_every_skill_reads_its_word_at_both_ends_of_every_band(self):
        for key, words in LADDERS.items():
            skill = self.char1.skills.get(key)
            for value, rung in BAND_EDGES:
                with self.subTest(skill=key, value=value):
                    skill.current = value
                    self.assertEqual(skill.desc(), words[rung])

    def test_the_hunting_backfill_makes_the_same_ladder(self):
        from world.character_migrations import HUNTING_SKILL_DEFAULTS

        self.assertEqual(
            list(HUNTING_SKILL_DEFAULTS["descs"].items()),
            list(zip(TOPS, LADDERS["hunting"])),
        )


class TestTheTierLine(EvenniaTest):
    character_typeclass = "typeclasses.characters.Character"

    def test_a_tier_starts_at_the_bottom_of_its_band(self):
        stored = self.char1.skills.get("craft").descs
        self.assertEqual(
            [tier_for(value, stored) for value in (19, 20, 39, 40, 94, 95)],
            ["unskilled", "novice", "novice", "apprentice", "skilled", "master"],
        )


class _Old(EvenniaTest):
    """
    `self.old` carries the five older skills as they were made before
    BD-T5b: the old tables, and values that differ from the placeholders.
    """

    character_typeclass = "typeclasses.characters.Character"

    VALUES = {  # key: (base, current, mod)
        "athletics": (16, 25, 0),
        "craft": (21, 47, 5),
        "hunting": (26, 26, 0),
        "perception": (29, 81, 0),
        "stealth": (21, 21, 0),
    }

    def setUp(self):
        super().setUp()
        self.old = create_object(Character, key="Oldtimer", location=self.room1)
        self._age(self.old)

    def _age(self, char):
        for key, (base, current, mod) in self.VALUES.items():
            skill = char.skills.get(key)
            skill.descs = old_table(key)
            skill.base, skill.current, skill.mod = base, current, mod

    def _values(self, char):
        return {
            key: (char.skills.get(key).base, char.skills.get(key).current,
                  char.skills.get(key).mod)
            for key in self.VALUES
        }


class TestBackfill(_Old):
    def test_the_fixture_reads_one_rung_early(self):
        # Receipt: the old table is on the trait and reads as it did in play.
        self.assertEqual(self.old.skills.get("athletics").desc(), "capable")    # 25
        self.assertEqual(self.old.skills.get("perception").desc(), "eagle-eyed")  # 81

    def test_every_older_skill_gets_the_new_table(self):
        _backfill()
        for key in FIVE_OLDER:
            with self.subTest(skill=key):
                self.assertEqual(
                    list(self.old.skills.get(key).descs.items()),
                    list(zip(TOPS, LADDERS[key])),
                )

    def test_the_words_now_follow_the_bands(self):
        _backfill()
        self.assertEqual(self.old.skills.get("athletics").desc(), "weak")     # 25
        self.assertEqual(self.old.skills.get("perception").desc(), "sharp")   # 81
        self.assertEqual(self.old.skills.get("craft").desc(), "apprentice")   # 47 + 5

    def test_no_value_moves(self):
        _backfill()
        self.assertEqual(self._values(self.old), self.VALUES)

    def test_the_new_table_is_in_the_database(self):
        _backfill()
        fresh = TraitHandler(
            self.old, db_attribute_key="skills", db_attribute_category="skills"
        )
        self.assertEqual(
            list(fresh.get("hunting").descs.items()),
            list(zip(TOPS, LADDERS["hunting"])),
        )

    def test_a_missing_skill_is_not_invented(self):
        self.old.skills.remove("hunting")
        said = _backfill()
        self.assertIsNone(self.old.skills.get("hunting"))
        self.assertIn("Oldtimer (athletics, craft, perception, stealth)", said)

    def test_banked_xp_is_untouched(self):
        self.old.skill_xp.add("craft", 5)
        before = self.old.skill_xp.get("craft")
        _backfill()
        self.assertEqual(self.old.skill_xp.get("craft"), before)


class TestTheBatch(_Old):
    def test_the_result_is_a_string_that_names_the_change(self):
        said = _backfill()
        self.assertIsInstance(said, str)
        self.assertIn("Oldtimer (athletics, craft, hunting, perception, stealth)", said)

    def test_a_character_made_today_is_counted_unchanged(self):
        # char1 and char2 were made with the new tables; only Oldtimer changes.
        said = _backfill()
        self.assertIn("changed 1 ", said)
        self.assertIn("unchanged 2", said)

    def test_a_second_run_changes_nothing(self):
        _backfill()
        said = _backfill()
        self.assertIn("changed 0 ", said)
        self.assertIn("unchanged 3", said)
        self.assertEqual(self._values(self.old), self.VALUES)

    def test_one_broken_character_does_not_stop_the_batch(self):
        broken = mock.Mock()
        broken.key = "Broken"
        broken.skills.get.side_effect = RuntimeError("no database")
        with mock.patch.object(
            Character.objects, "all_family", return_value=[broken, self.old]
        ):
            said = _backfill()
        self.assertIn("Broken (ERROR: no database)", said)
        self.assertEqual(self.old.skills.get("athletics").desc(), "weak")
