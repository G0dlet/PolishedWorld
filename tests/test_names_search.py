"""
Tests for the search once the character takes the rpsystem contrib. Names,
Task NM-T2 (docs/PolishedWorld_Combat_Decomposition.md, NM9, NM10; moved
from NM-T3 by the lock of 2026-11-15).

WHY THE SEARCH IS THE PROJECT'S
-------------------------------
The contrib's search (`ContribRPObject.get_search_result`, rpsystem.py:1326)
runs its emote parser over the candidates. Three things in it are wrong for
this game, and all three were run before they were written down:

* It matches the start of any word, and nothing exact comes first: with
  *Obj* and *Obj2* in the room, `Obj` is a multimatch (OQ-NM1), and with
  *leather* and a *leather strap* in the pack, so is `leather` (NM10).
* Its candidate map holds one row for the key and one per alias
  (rpsystem.py:383-395), and the `N-` number is counted in that list
  (:490-495). A *plant fiber* with the alias *fiber* matches twice, so
  `1-fiber` and `2-fiber` were the same object.
* A number past the matches gives the last match (`min(..., nmatches - 1)`),
  and `0-` the first. Evennia's own search gives nothing (manager.py:497-501).

So `Character.get_search_result` takes the `N-` number off with the game's own
SEARCH_MULTIMATCH_REGEX before the contrib sees it, keeps the exact names
when there are any, and counts the number in that list.

EXACT MEANS WHAT THE SEARCHER CAN SEE
-------------------------------------
For a thing: its key or an alias. For a character: the recog or short
description the searcher reads, never the key. Narrowing on a character's key
would let `tall` single out the one whose key is *Tall* -- telling a player a
name they have not been given.

THE COMMANDS (NM-T3)
--------------------
TestTheCommandsReachTheirTargets calls `caller.search` the way `hunt`,
`craft ... from` (ingredients and tools), `teach`, `pay ... to` and
`get ... from` call it, with a player as the caller.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_search
"""

from unittest import mock

from evennia import create_object, search_object
from evennia.utils.test_resources import EvenniaTest


THING = "typeclasses.objects.Object"


class _Search(EvenniaTest):
    """char2 is the player (no permissions); char1 is a Developer."""

    character_typeclass = "typeclasses.characters.Character"

    def make(self, key, location=None, aliases=None):
        obj = create_object(THING, key=key, location=location or self.char2)
        if aliases:
            obj.aliases.add(aliases)
        return obj

    def found(self, query, searcher=None):
        return list((searcher or self.char2).search(query, quiet=True) or [])


class TestExactFirst(_Search):
    def test_leather_beats_a_leather_strap_in_either_order(self):
        for order in (("leather", "leather strap"), ("leather strap", "leather")):
            with self.subTest(order=order):
                made = {key: self.make(key) for key in order}
                self.assertEqual(self.found("leather"), [made["leather"]])
                for obj in made.values():
                    obj.delete()

    def test_an_alias_is_exact_too(self):
        hide = self.make("raw hide", aliases=["hide"])
        self.make("hide strip")
        self.assertEqual(self.found("hide"), [hide])

    def test_obj_beats_obj2(self):
        # OQ-NM1: `bug Obj = ...` in tests.test_report_commands.
        self.assertEqual(self.found("Obj", searcher=self.char1), [self.obj1])

    def test_without_an_exact_name_every_match_stays(self):
        strap, belt = self.make("leather strap"), self.make("leather belt")
        self.assertEqual(self.found("leather"), [strap, belt])

    def test_case_does_not_matter(self):
        leather = self.make("leather")
        self.make("leather strap")
        self.assertEqual(self.found("LEATHER"), [leather])


class TestTheNumber(_Search):
    def setUp(self):
        super().setUp()
        self.fibres = [self.make("plant fiber", aliases=["fiber"]) for _ in range(3)]

    def test_each_number_is_its_own_object_through_an_alias(self):
        self.assertEqual(
            [self.found(f"{n}-fiber") for n in (1, 2, 3)],
            [[fibre] for fibre in self.fibres],
        )

    def test_and_through_the_key(self):
        self.assertEqual(self.found("2-plant fiber"), [self.fibres[1]])

    def test_a_number_past_the_matches_finds_nothing(self):
        self.assertEqual(self.found("4-fiber"), [])

    def test_zero_finds_nothing(self):
        self.assertEqual(self.found("0-fiber"), [])

    def test_the_suffix_form_finds_nothing(self):
        self.assertEqual(self.found("fiber-2"), [])

    def test_the_number_counts_in_the_exact_list(self):
        # 1-leather with two leather and a leather strap: the strap is not one
        # of the two the number counts. Made first, so that counting in the
        # unnarrowed list would land on it.
        self.make("leather strap")
        first, second = self.make("leather"), self.make("leather")
        self.assertEqual(self.found("2-leather"), [second])
        self.assertEqual(self.found("1-leather"), [first])

    def test_a_key_that_starts_with_a_number_is_found_whole(self):
        # OQ-NM7, as Evennia's own search does it: the whole string exactly first.
        sword = self.make("2-handed sword")
        self.assertEqual(self.found("2-handed sword"), [sword])

    def test_the_multimatch_list_names_what_to_type(self):
        with mock.patch.object(self.char2, "msg") as heard:
            self.assertIsNone(self.char2.search("fiber"))
        said = heard.call_args.args[0]
        for n in (1, 2, 3):
            self.assertIn(f" {n}-plant fiber [fiber]", said)


class TestCreatures(_Search):
    def setUp(self):
        super().setUp()
        self.rabbits = [
            create_object(
                "typeclasses.creatures.Creature", key="rabbit", location=self.room1
            )
            for _ in range(2)
        ]
        self.rabbits[0].aliases.add("bunny")

    def test_by_key_two_is_a_multimatch(self):
        self.assertEqual(self.found("rabbit"), self.rabbits)

    def test_by_number(self):
        self.assertEqual(self.found("2-rabbit"), [self.rabbits[1]])

    def test_by_alias(self):
        self.assertEqual(self.found("bunny"), [self.rabbits[0]])


class TestCharacters(_Search):
    def setUp(self):
        super().setUp()
        self.char1.sdesc.add("a weathered woman with grey eyes")

    def test_a_word_of_the_description_finds_her(self):
        self.assertEqual(self.found("weathered"), [self.char1])

    def test_several_words_find_her(self):
        self.assertEqual(self.found("weathered grey"), [self.char1])

    def test_her_key_finds_nothing_for_a_player(self):
        self.assertEqual(self.found(self.char1.key), [])

    def test_a_builder_who_matched_nothing_finds_by_key(self):
        self.char2.sdesc.add("a broad-shouldered man")
        self.assertEqual(self.found(self.char2.key, searcher=self.char1), [self.char2])

    def test_me(self):
        self.assertEqual(self.found("me"), [self.char2])

    def test_a_dbref_through_the_global_search(self):
        # TR6, UP18: staff tools and scripts find a character by dbref.
        self.assertEqual(list(search_object(self.char1.dbref)), [self.char1])

    def test_exact_does_not_reveal_a_key(self):
        # Two strangers whose descriptions both start with "tall"; one is keyed
        # "Tall". A player typing "tall" must get both, not the keyed one.
        tall = create_object(
            "typeclasses.characters.Character", key="Tall", location=self.room1
        )
        tall.sdesc.add("a tall man")
        other = create_object(
            "typeclasses.characters.Character", key="Other", location=self.room1
        )
        other.sdesc.add("a tall woman")
        self.assertCountEqual(self.found("tall"), [tall, other])

    def test_an_exact_description_wins(self):
        man = create_object(
            "typeclasses.characters.Character", key="Man", location=self.room1
        )
        man.sdesc.add("a tall man")
        scarred = create_object(
            "typeclasses.characters.Character", key="Scarred", location=self.room1
        )
        scarred.sdesc.add("a tall man with a scar")
        self.assertEqual(self.found("a tall man"), [man])


class TestTheCommandsReachTheirTargets(_Search):
    """
    Each command that names a target, with `caller.search` called the way the
    command calls it (NM-T3). The arguments are copied from the line named in
    each test; a command that changes how it searches should change its test.

    char2 is the caller throughout: a player, so no Builder fallback can find a
    character by key and hide a miss.
    """

    def setUp(self):
        super().setUp()
        self.char1.sdesc.add("a weathered woman")

    def test_hunt_reaches_the_second_rabbit(self):
        # commands/hunting_commands.py:76 -- caller.search(name, candidates=creatures)
        rabbits = [
            create_object("typeclasses.creatures.Creature", key="rabbit", location=self.room1)
            for _ in range(2)
        ]
        self.assertEqual(
            self.char2.search("2-rabbit", candidates=rabbits, quiet=True), [rabbits[1]]
        )

    def test_craft_reaches_each_numbered_ingredient(self):
        # commands/crafting_commands.py:315 -- caller.search(key, location=caller).
        # The contrib alone gave the same plant fiber for 1- and 2-.
        fibres = [self.make("plant fiber", aliases=["fiber"]) for _ in range(3)]
        found = [
            self.char2.search(f"{n}-fiber", location=self.char2, quiet=True)
            for n in (1, 2, 3)
        ]
        self.assertEqual(found, [[fibre] for fibre in fibres])

    def test_craft_reaches_the_tool_by_its_exact_name(self):
        # commands/crafting_commands.py:324 -- caller.search(key)
        knife = self.make("knife")
        self.make("knife sheath", location=self.room1)
        self.assertEqual(self.char2.search("knife", quiet=True), [knife])

    def test_teach_reaches_the_student_by_what_the_teacher_sees(self):
        # commands/crafting_commands.py:1222 -- caller.search(student_name)
        self.assertEqual(self.char2.search("weathered", quiet=True), [self.char1])
        self.assertEqual(self.char2.search(self.char1.key, quiet=True), [])

    def test_pay_reaches_the_payee_by_the_exact_description(self):
        # commands/currency_commands.py:249 -- caller.search(target_name)
        other = create_object(
            "typeclasses.characters.Character", key="Other", location=self.room1
        )
        other.sdesc.add("a weathered woman with a limp")
        self.assertEqual(
            self.char2.search("a weathered woman", quiet=True), [self.char1]
        )

    def test_get_from_reaches_the_numbered_thing_inside(self):
        # evennia/contrib/game_systems/containers/containers.py:138, :142 --
        # the container by caller.search(rhs), then the thing with
        # caller.search(lhs, location=container). CmdGet is the contrib's.
        sack = create_object(
            "typeclasses.containers.Container", key="large sack", location=self.room1
        )
        fibres = [self.make("plant fiber", location=sack, aliases=["fiber"]) for _ in range(2)]
        container = self.char2.search("sack")
        self.assertEqual(container, sack)
        self.assertEqual(
            self.char2.search("2-fiber", location=container, quiet=True), [fibres[1]]
        )
