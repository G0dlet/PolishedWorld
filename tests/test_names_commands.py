"""
Tests for `recog` and `forget`. Names, Task NM-T5
(docs/PolishedWorld_Combat_Decomposition.md, NM4; Names note UP5, UP7, UP8).

WHY THE PROJECT'S OWN COMMANDS
------------------------------
The contrib's `recog` (rpsystem.py:1123) takes anything in the room as its
target -- a creature, an item, oneself (`:1191`) -- lets the handler's
`SdescError` through (only `RecogError` is caught, `:1230`), and its `forget`
looks in the room too, so a person who has left cannot be forgotten. The
project's commands name only other characters, and `forget` reads the
recogniser's own list, so it works anywhere (UP7).

THE THREE LOCKS (Adam, 2026-11-15, at NM-T5's STOPP)
----------------------------------------------------
1 B -- the list shows a label and how the person looks now only while they
     stand in the same room; anyone else is the label alone, and `forget`
     answers with the label. A live short description (OQ-NM9) must not be
     readable from anywhere.
2 B -- a label held for two people is numbered in the list, and `forget 2-Tess`
     drops the second wherever the forgetter stands.
3 A -- a statue is the person, so it can be recognised.

THE HANDLER'S all() LOSES A DUPLICATE (run, 2026-11-15)
-------------------------------------------------------
`RecogHandler.all()` returns `{label: person}`: with two people held as
*Tess*, one of them is gone from it, while `obj2recog` holds both. The list
and `forget` read `obj2recog`. TestTheList pins it.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_commands
"""

from unittest import mock

from evennia import create_object
from evennia.utils.test_resources import EvenniaCommandTest

from tests.names_fixture import describe

CHARACTER = "typeclasses.characters.Character"
THING = "typeclasses.objects.Object"


def _recog_cmd():
    from commands.names_commands import CmdRecog

    return CmdRecog()


def _forget_cmd():
    from commands.names_commands import CmdForget

    return CmdForget()


class _Names(EvenniaCommandTest):
    """
    char2 is the player who knows people (no permissions, so the contrib's
    Builder fallback to a key search never hides a miss). char3 and char4 are
    in the room; none of the three has an account, so each is a statue.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.char3 = create_object(CHARACTER, key="Char3", location=self.room1)
        self.char4 = create_object(CHARACTER, key="Char4", location=self.room1)
        describe(self.char1, self.char2, self.char3, self.char4)

    def recog(self, args, caller=None):
        return self.call(_recog_cmd(), args, caller=caller or self.char2)

    def forget(self, args, caller=None):
        return self.call(_forget_cmd(), args, caller=caller or self.char2)

    def held(self, caller=None):
        return dict((caller or self.char2).attributes.get("_recog_obj2recog") or {})

    def here(self):
        return list(self.room1.contents)


class TestRecog(_Names):
    def test_a_word_of_the_description_names_the_person(self):
        said = self.recog("freckled as Tess")
        self.assertIn("You will remember a freckled youth as Tess.", said)
        self.assertEqual(self.char2.recog.get(self.char3), "Tess")
        self.assertEqual(self.held(), {self.char3: "Tess"})

    def test_the_label_then_shows_and_finds_the_person(self):
        self.recog("freckled as Tess")
        self.assertIn("Tess", self.char3.get_display_name(self.char2))
        self.assertNotIn("freckled", self.char3.get_display_name(self.char2))
        found = self.char2.search("Tess", candidates=self.here(), quiet=True)
        self.assertEqual(list(found), [self.char3])

    def test_the_number_picks_the_second_of_two_alike(self):
        for char in (self.char3, self.char4):
            char.sdesc.add("a lanky man")
        first = self.char2.search("1-lanky", candidates=self.here(), quiet=True)[0]
        second = self.char2.search("2-lanky", candidates=self.here(), quiet=True)[0]
        self.assertNotEqual(first, second)
        self.recog("2-lanky as Second")
        self.assertEqual(self.char2.recog.get(second), "Second")
        self.assertIsNone(self.char2.recog.get(first))

    def test_two_alike_without_a_number_is_a_multimatch(self):
        for char in (self.char3, self.char4):
            char.sdesc.add("a lanky man")
        said = self.recog("lanky as Tess")
        self.assertIn("More than one match for 'lanky'", said)
        self.assertEqual(said.count("a lanky man"), 2)
        self.assertEqual(self.held(), {})

    def test_a_new_label_replaces_the_old(self):
        self.recog("freckled as Tess")
        said = self.recog("Tess as Tessa")
        self.assertIn("You will remember Tess as Tessa.", said)
        self.assertEqual(self.held(), {self.char3: "Tessa"})

    def test_a_statue_can_be_recognised(self):
        self.assertTrue(self.char3.is_statue)
        self.recog("freckled as Tess")
        self.assertEqual(self.char2.recog.get(self.char3), "Tess")

    def test_two_viewers_hold_their_own_labels(self):
        self.recog("freckled as Tess", caller=self.char2)
        self.char1.recog.add(self.char3, "Mia")
        self.assertEqual(self.char2.get_sdesc(self.char3), "Tess")
        self.assertEqual(self.char1.get_sdesc(self.char3), "Mia")
        self.assertEqual(self.char4.get_sdesc(self.char3), "a freckled youth")


class TestRecogRefuses(_Names):
    def test_a_creature(self):
        create_object("typeclasses.creatures.Creature", key="rabbit", location=self.room1)
        said = self.recog("rabbit as Bun")
        self.assertIn("Could not find 'rabbit'", said)
        self.assertEqual(self.held(), {})

    def test_an_item(self):
        create_object(THING, key="stone", location=self.room1)
        said = self.recog("stone as Rocky")
        self.assertIn("Could not find 'stone'", said)
        self.assertEqual(self.held(), {})

    def test_oneself(self):
        for query in ("me", "self", "broad-shouldered"):
            with self.subTest(query=query):
                said = self.recog(f"{query} as Hero")
                self.assertNotIn("You will remember", said)
                self.assertEqual(self.held(), {})
                self.assertIsNone(self.char2.recog.get(self.char2))

    def test_no_as_is_the_usage(self):
        said = self.recog("freckled Tess")
        self.assertIn("Usage: recog <description> as <name>", said)
        self.assertEqual(self.held(), {})

    def test_an_empty_label(self):
        for args in ("freckled as ", "freckled as /", "freckled as ...", "freckled as - -"):
            with self.subTest(args=args):
                said = self.recog(args)
                self.assertNotIn("Traceback", said)
                self.assertNotIn("You will remember", said)
                self.assertEqual(self.held(), {})

    def test_a_label_over_sixty_characters(self):
        said = self.recog("freckled as " + "x" * 61)
        self.assertIn("That name is too long to keep in mind.", said)
        self.assertEqual(self.held(), {})
        self.recog("freckled as " + "x" * 60)
        self.assertEqual(self.held(), {self.char3: "x" * 60})

    def test_a_person_who_cannot_be_recognised(self):
        self.char3.locks.add("enable_recog:false()")
        said = self.recog("freckled as Tess")
        self.assertIn("You cannot make out who they are.", said)
        self.assertEqual(self.held(), {})

    def test_a_colour_code_is_not_kept(self):
        self.recog("freckled as |rTess|n")
        self.assertEqual(self.held(), {self.char3: "Tess"})

    def test_a_handler_error_is_one_line(self):
        from evennia.contrib.rpg.rpsystem.rpsystem import RecogError, SdescError

        for error in (SdescError("x"), RecogError("x")):
            with self.subTest(error=type(error).__name__):
                with mock.patch.object(type(self.char2.recog), "add", side_effect=error):
                    said = self.recog("freckled as Tess")
                self.assertNotIn("Traceback", said)
                self.assertNotIn("You will remember", said)


class TestForget(_Names):
    def test_forget_in_another_room(self):
        self.recog("freckled as Tess")
        self.char2.move_to(self.room2, quiet=True)
        said = self.forget("Tess")
        self.assertIn("You let the name Tess go.", said)
        self.assertEqual(self.held(), {})
        self.assertEqual(self.char2.get_sdesc(self.char3), "a freckled youth")

    def test_forget_is_case_insensitive(self):
        self.recog("freckled as Tess")
        self.forget("tess")
        self.assertEqual(self.held(), {})

    def test_an_unknown_label(self):
        self.recog("freckled as Tess")
        said = self.forget("Bob")
        self.assertIn("You know no one as Bob.", said)
        self.assertEqual(self.held(), {self.char3: "Tess"})

    def test_no_label_is_the_usage(self):
        said = self.forget("")
        self.assertIn("Usage: forget <name>", said)

    def test_a_label_held_for_two_asks_which(self):
        self.recog("freckled as Tess")
        self.recog("stooped as Tess")
        self.char2.move_to(self.room2, quiet=True)
        said = self.forget("Tess")
        self.assertIn("You know two people as Tess: 1-Tess, 2-Tess.", said)
        self.assertEqual(len(self.held()), 2)

    def test_the_number_drops_the_one_the_list_numbers(self):
        self.recog("freckled as Tess")
        self.recog("stooped as Tess")
        first, second = sorted((self.char3, self.char4), key=lambda c: c.id)
        self.char2.move_to(self.room2, quiet=True)
        self.forget("2-Tess")
        self.assertEqual(self.held(), {first: "Tess"})

    def test_a_number_past_the_end_drops_nothing(self):
        self.recog("freckled as Tess")
        for args in ("2-Tess", "0-Tess"):
            with self.subTest(args=args):
                said = self.forget(args)
                self.assertIn(f"You know no one as {args}.", said)
                self.assertEqual(self.held(), {self.char3: "Tess"})

    def test_a_label_that_looks_numbered_is_taken_whole(self):
        self.recog("freckled as 2-Tess")
        self.forget("2-Tess")
        self.assertEqual(self.held(), {})

    def test_the_forget_survives_a_fresh_handler(self):
        self.recog("freckled as Tess")
        self.forget("Tess")
        from evennia.contrib.rpg.rpsystem.rpsystem import RecogHandler

        self.assertIsNone(RecogHandler(self.char2).get(self.char3))


class TestTheList(_Names):
    def test_nobody_known(self):
        said = self.recog("")
        self.assertIn("You know no one by name yet.", said)

    def test_present_with_the_look_absent_by_label_alone(self):
        self.recog("freckled as Tess")
        said = self.recog("")
        self.assertIn("Tess (a freckled youth)", said)
        self.char2.move_to(self.room2, quiet=True)
        said = self.recog("")
        self.assertIn("Tess", said)
        self.assertNotIn("freckled", said)

    def test_both_of_a_shared_label_are_listed_and_numbered(self):
        self.recog("freckled as Tess")
        self.recog("stooped as Tess")
        self.assertEqual(len(self.char2.recog.all()), 1)  # the handler's own loss
        said = self.recog("")
        self.assertIn("1-Tess (", said)
        self.assertIn("2-Tess (", said)
        self.assertIn("a freckled youth", said)
        self.assertIn("a stooped elder", said)

    def test_the_list_numbers_in_the_order_forget_counts(self):
        self.recog("freckled as Tess")
        self.recog("stooped as Tess")
        first, second = sorted((self.char3, self.char4), key=lambda c: c.id)
        said = self.recog("")
        self.assertIn(f"1-Tess ({first.sdesc.get()})", said)
        self.assertIn(f"2-Tess ({second.sdesc.get()})", said)

    def test_a_deleted_person_is_not_listed(self):
        self.recog("freckled as Tess")
        self.recog("stooped as Maren")
        self.char3.delete()
        self.char2.recog._cache()
        said = self.recog("")
        self.assertIn("Maren", said)
        self.assertNotIn("Tess", said)


class TestTheCommandSet(EvenniaCommandTest):
    def test_recog_and_forget_are_in_the_character_set(self):
        from commands.default_cmdsets import CharacterCmdSet

        cmdset = CharacterCmdSet()
        cmdset.at_cmdset_creation()
        keys = {cmd.key for cmd in cmdset.commands}
        self.assertIn("recog", keys)
        self.assertIn("forget", keys)
