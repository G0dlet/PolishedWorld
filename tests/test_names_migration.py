"""
Tests for backfill_names. Names, Task NM-T4 (Combat Decomposition NM8,
OQ-NM6; Names UQ7).

WHY A BACKFILL
--------------
`ContribRPCharacter.at_object_creation` (rpsystem.py:1554-1567) writes the
recog dictionaries, the short description and the contrib's command set;
`ContribRPObject.at_object_creation` (:1315-1324) writes the pose. Both run
only for NEW objects. A character made before NM-T2 has none of them, and the
worst consequence is silent: `RecogHandler.add` (:836-837) writes into
`attributes.get("_recog_obj2recog", default={})`. With no Attribute that
default is a fresh dict that is never saved, so the recog works until the next
reload and is then gone. TestTheBug pins that, red against the contrib alone.

WHAT EACH CLASS PUTS PRESSURE ON
--------------------------------
* TestTheBug -- the loss itself, without any backfill.
* TestBackfill -- a stripped character gets the four Attributes and the
  placeholder; a recog added after the backfill is stored and survives a
  fresh handler; a loaded handler drops the recog that was never saved, so
  what a player sees matches what a reload will show; what a character
  already has is kept; a persistent
  rpsystem_cmdset is removed; the contrib's own default description is
  replaced as if missing.
* TestTheBatch -- a second run changes nothing; one broken character does
  not stop the rest; the result is a string `@py` can print.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_migration
"""

from unittest import mock

from evennia import create_object
from evennia.contrib.rpg.rpsystem import RPSystemCmdSet
from evennia.contrib.rpg.rpsystem.rpsystem import RecogHandler, SdescHandler
from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character


PLACEHOLDER = "a quiet traveller"
NAMES_ATTRIBUTES = ("_recog_ref2recog", "_recog_obj2recog", "pose", "pose_default")


def _backfill():
    # Imported per call so that each test is red on its own before the
    # function exists.
    from world.character_migrations import backfill_names

    return backfill_names()


class _Old(EvenniaTest):
    """`self.old` is a character as it was before NM-T2: none of the contrib's data."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.char1.sdesc.add("a weathered woman")
        self.old = create_object(Character, key="Oldtimer", location=self.room1)
        for name in NAMES_ATTRIBUTES + ("_sdesc",):
            self.old.attributes.remove(name)
        # Creation loaded the handlers while the Attributes existed; an older
        # character's handlers never saw them. Read them again from nothing.
        self.old.recog._cache()
        self.old.sdesc._cache()


class TestTheBug(_Old):
    def test_a_recog_added_without_the_backfill_is_lost(self):
        RecogHandler(self.old).add(self.char1, "Mia")
        self.assertIsNone(self.old.attributes.get("_recog_obj2recog"))
        self.assertIsNone(RecogHandler(self.old).get(self.char1))


class TestBackfill(_Old):
    def test_a_stripped_character_gets_the_attributes_and_the_placeholder(self):
        _backfill()
        for name in NAMES_ATTRIBUTES:
            with self.subTest(attribute=name):
                self.assertTrue(self.old.attributes.has(name))
        self.assertEqual(self.old.attributes.get("pose_default"), "is here.")
        self.assertEqual(SdescHandler(self.old).get(), PLACEHOLDER)

    def test_a_recog_added_after_the_backfill_survives_a_fresh_handler(self):
        _backfill()
        self.old.recog.add(self.char1, "Mia")
        self.assertEqual(self.old.attributes.get("_recog_obj2recog"), {self.char1: "Mia"})
        self.assertEqual(RecogHandler(self.old).get(self.char1), "Mia")

    def test_a_loaded_character_stops_showing_a_recog_that_was_never_saved(self):
        # Online through the backfill: the handler holds the unsaved recog
        # until something reads the stored dictionaries back.
        self.old.recog.add(self.char1, "Mia")
        self.assertEqual(self.old.recog.get(self.char1), "Mia")
        _backfill()
        self.assertIsNone(self.old.recog.get(self.char1))

    def test_what_a_character_already_has_is_kept(self):
        self.char2.recog.add(self.char1, "Mia")
        self.char2.sdesc.add("a broad-shouldered man")
        self.char2.db.pose = "is sitting by the fire."
        _backfill()
        self.assertEqual(RecogHandler(self.char2).get(self.char1), "Mia")
        self.assertEqual(SdescHandler(self.char2).get(), "a broad-shouldered man")
        self.assertEqual(self.char2.db.pose, "is sitting by the fire.")

    def test_the_contribs_default_description_is_replaced(self):
        # OQ-NM6: *A normal person* (rpsystem.py:1567) is nobody's choice; a
        # character that has it reads as unbackfilled.
        self.char2.sdesc.add("A normal person")
        _backfill()
        self.assertEqual(SdescHandler(self.char2).get(), PLACEHOLDER)

    def test_a_persistent_rpsystem_cmdset_is_removed(self):
        self.old.cmdset.add(RPSystemCmdSet, persistent=True)
        _backfill()
        self.assertFalse(self.old.cmdset.has(RPSystemCmdSet))
        self.assertFalse(
            any("rpsystem" in str(path) for path in self.old.cmdset_storage or [])
        )


class TestTheBatch(_Old):
    def test_the_result_is_a_string_that_names_the_change(self):
        said = _backfill()
        self.assertIsInstance(said, str)
        self.assertIn("Oldtimer", said)

    def test_a_second_run_changes_nothing(self):
        _backfill()
        before = {name: self.old.attributes.get(name) for name in NAMES_ATTRIBUTES + ("_sdesc",)}
        said = _backfill()
        self.assertIn("changed 0", said)
        after = {name: self.old.attributes.get(name) for name in NAMES_ATTRIBUTES + ("_sdesc",)}
        self.assertEqual(after, before)

    def test_one_broken_character_does_not_stop_the_batch(self):
        broken = mock.Mock()
        broken.key = "Broken"
        broken.attributes.has.side_effect = RuntimeError("no database")
        with mock.patch.object(
            Character.objects, "all_family", return_value=[broken, self.old]
        ):
            said = _backfill()
        self.assertIn("Broken (ERROR: no database)", said)
        self.assertEqual(SdescHandler(self.old).get(), PLACEHOLDER)
