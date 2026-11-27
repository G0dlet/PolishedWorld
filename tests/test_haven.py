"""
Unit tests for `world/haven.py`. Haven Decomposition, Tasks HV-T1 (the Combat
Design's §4.2: PV3, HV2, HV3) and HV-T4 (PV1, TR5, HV1, HV5, HV7).

WHAT IS WORTH TESTING HERE
--------------------------
1. **The reader answers what is stored, as a bool** (`TestIsHaven`). No room
   at all is no haven; a room without the Attribute is none, which is every
   room that existed before the slice; True and False are what they say.
   The string `'yes'` is a haven: `@set here/is_haven = yes` stores it
   (Haven Decomposition §4, P1), and the case stands here so that nobody
   tightens the read to `is True` without seeing it. Every case uses
   `assertIs`, so a reader that hands back what is stored -- None, 'yes' --
   in place of a bool is red.
2. **No other code reads the flag** (`TestHavenCensus`, HV2). The census
   walks the production source and finds every `<x>.db.is_haven`, read or
   written, and every string constant `"is_haven"` -- an `attributes` call,
   a `getattr`, the seeder's `("is_haven", True)`, the seed data's key. It
   holds that they stand only in `world/haven.py`, `world/seeding.py` and
   `world/seed_data.py`.
3. **The census sees what it should and nothing else**
   (`TestHavenCensusFixtures`): a census that saw nothing would pass for
   ever.
4. **The guard reads both rooms, the haven first** (`TestAttackRefusal`).
   Six pairs -- a character against a creature, the reverse, a creature
   against a creature, a character against a character, against a statue,
   against the sweeper -- in a haven with the attacker, the target or both,
   refused with the haven's line whatever `PVP_ENABLED` says. A case with
   only one end in a haven is red when only the other end's room is read; two
   characters in a haven are red when player against player is asked first.
5. **Outside, only a player character against another is refused, and only
   while the switch is off.** A statue is a player character; a creature,
   the sweeper and Evennia's own `DefaultCharacter` are not, so the guard
   cannot quietly widen to `or`, or to Evennia's class.
6. **The line names the target as the attacker sees it** (TR5): the short
   description and never the key, the recog once given, a statue as a
   statue (Haven Decomposition §4, P4). `char2` has a real session here
   (`SecondSessionMixin`): in a bare `EvenniaTest` it is a statue, and the
   stranger's case would read the statue's name. Both lines are written out
   by hand once, so a reword is a decision.
7. **The guard sends nothing** (HV7): the caller sends the line.
8. **`PVP_ENABLED` is read in `world/haven.py` alone, and is False**
   (`TestPvpCensus`, HV5, PV6), with fixtures for the census's walk.

What the seed writes is `tests/test_seeding.py`'s: each seeded room through
`is_haven`, the Attribute on the haven alone, and a re-seed that leaves the
flags as staff left them.

WHAT THE CENSUSES DO NOT READ
-----------------------------
A key or a name held in a variable or built from pieces; Django templates
(`.html`); `tests/`, which patch the constant; `@set` in the game. A reach of
one of those kinds is read by eye when it is written. That the guard writes
nothing is read by eye too: it holds no assignment.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_haven
"""

import ast
import pathlib
import textwrap
from unittest import TestCase, mock

from evennia import create_object
from evennia.utils.test_resources import EvenniaTest

from tests.names_fixture import describe
from tests.test_currency_commands import SecondSessionMixin
from world import haven
from world.haven import HAVEN_REFUSAL, PVP_REFUSAL, attack_refusal, is_haven

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCTION = ("commands", "server", "typeclasses", "web", "world")
ATTRIBUTE = "is_haven"

# The three files that may name the Attribute (HV2, HV3): the reader, the
# seeder that writes it, and the seed data that says where.
ALLOWED = frozenset({"world/haven.py", "world/seeding.py", "world/seed_data.py"})


class TestIsHaven(EvenniaTest):
    """The one reader of the flag (HV2), on a real room."""

    def test_no_room_is_no_haven(self):
        self.assertIs(is_haven(None), False)

    def test_a_room_without_the_attribute_is_no_haven(self):
        self.assertFalse(self.room1.attributes.has(ATTRIBUTE))
        self.assertIs(is_haven(self.room1), False)

    def test_true_is_a_haven(self):
        self.room1.db.is_haven = True
        self.assertIs(is_haven(self.room1), True)

    def test_false_is_no_haven(self):
        self.room1.db.is_haven = False
        self.assertIs(is_haven(self.room1), False)

    def test_the_string_yes_is_a_haven(self):
        # What `@set here/is_haven = yes` stores (P1). A haven, on purpose.
        self.room1.db.is_haven = "yes"
        self.assertIs(is_haven(self.room1), True)

    def test_the_flag_taken_off_is_no_haven(self):
        # `@set here/is_haven =` removes the Attribute (P1).
        self.room1.db.is_haven = True
        self.room1.attributes.remove(ATTRIBUTE)
        self.assertIs(is_haven(self.room1), False)


def reaches(tree):
    """How many times a module names the flag as an Attribute."""
    count = 0
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and node.attr == ATTRIBUTE
                and isinstance(node.value, ast.Attribute) and node.value.attr == "db"):
            count += 1
        elif isinstance(node, ast.Constant) and node.value == ATTRIBUTE:
            count += 1
    return count


def production_census():
    """The production files that name the flag, as paths from the root."""
    found = set()
    for top in PRODUCTION:
        for path in sorted((ROOT / top).rglob("*.py")):
            if reaches(ast.parse(path.read_text(encoding="utf-8"))):
                found.add(path.relative_to(ROOT).as_posix())
    return found


def _fixture(source):
    return reaches(ast.parse(textwrap.dedent(source)))


class TestHavenCensus(TestCase):
    """The flag is named in three files only (HV2)."""

    def test_only_the_reader_and_the_seed_name_the_flag(self):
        self.assertEqual(
            production_census(), ALLOWED,
            "HV2: the flag is read through world.haven.is_haven alone; "
            "a module that reads or writes room.db.is_haven itself is a "
            "second reader. Ask is_haven(room), or say why here.",
        )


class TestHavenCensusFixtures(TestCase):
    """The census counts each form that names the Attribute, and no other."""

    def test_a_read_is_found(self):
        self.assertEqual(_fixture("flag = room.db.is_haven"), 1)

    def test_a_write_is_found(self):
        self.assertEqual(_fixture("room.db.is_haven = True"), 1)

    def test_an_attributes_call_is_found(self):
        self.assertEqual(_fixture('room.attributes.get("is_haven")'), 1)

    def test_getattr_is_found(self):
        self.assertEqual(_fixture('getattr(room.db, "is_haven")'), 1)

    def test_the_seeders_tuple_and_the_datas_key_are_found(self):
        self.assertEqual(_fixture('''
            attributes.append(("is_haven", True))
            row = {"is_haven": False}
        '''), 2)

    def test_the_reader_called_imported_or_named_in_prose_is_not_found(self):
        self.assertEqual(_fixture('''
            """A docstring that names room.db.is_haven."""
            from world.haven import is_haven
            from world import haven
            # a comment on room.db.is_haven
            if haven.is_haven(room) or is_haven(other):
                pass
        '''), 0)


# --- The guard (HV-T4) ----------------------------------------------------

CHARACTER = "typeclasses.characters.Character"
CONSTANT = "PVP_ENABLED"


class TestAttackRefusal(SecondSessionMixin, EvenniaTest):
    """
    Who may attack whom, and where (PV1, PV3, HV7). char1 and char2 are
    awake (char2 through a real session); `statue` is a character with none.
    room2 is the haven.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        describe(self.char1, self.char2)
        self.statue = create_object(CHARACTER, key="Char3", location=self.room1)
        describe(self.statue)
        self.rabbit = create_object(
            "typeclasses.creatures.Creature", key="rabbit", location=self.room1)
        self.hare = create_object(
            "typeclasses.creatures.Creature", key="hare", location=self.room1)
        self.sweeper = create_object(
            "typeclasses.npcs.Sweeper", key="sweeper", location=self.room1)
        self.room2.db.is_haven = True

    def pairs(self):
        """The six pairs of HV-T4's testing, as (label, attacker, target)."""
        return [
            ("character against creature", self.char1, self.rabbit),
            ("creature against character", self.rabbit, self.char1),
            ("creature against creature", self.rabbit, self.hare),
            ("character against character", self.char1, self.char2),
            ("character against statue", self.char1, self.statue),
            ("character against sweeper", self.char1, self.sweeper),
        ]

    def refusals(self, attacker_room, target_room, pvp):
        """Each pair placed in the two rooms and asked, with the switch at `pvp`."""
        answers = {}
        with mock.patch.object(haven, CONSTANT, pvp):
            for label, attacker, target in self.pairs():
                attacker.location = attacker_room
                target.location = target_room
                answers[label] = attack_refusal(attacker, target)
        return answers

    def assert_all_refused_by_the_haven(self, attacker_room, target_room):
        # One dict for both settings of the switch, not a subTest: a failing
        # subTest cannot be sent back from a parallel worker (Testing
        # Reference §28.1, lesson 348).
        answers = {}
        for pvp in (False, True):
            for label, line in self.refusals(attacker_room, target_room, pvp).items():
                answers[(label, pvp)] = line
        self.assertEqual(answers, {
            (label, pvp): HAVEN_REFUSAL
            for label, _, _ in self.pairs() for pvp in (False, True)
        })

    def pvp_line(self, attacker, target):
        return PVP_REFUSAL.format(name=target.get_display_name(attacker))

    # The rooms: the haven is asked first, at either end.

    def test_both_in_a_haven_every_pair_is_refused(self):
        self.assert_all_refused_by_the_haven(self.room2, self.room2)

    def test_attacker_in_a_haven_target_outside_is_refused(self):
        self.assert_all_refused_by_the_haven(self.room2, self.room1)

    def test_target_in_a_haven_attacker_outside_is_refused(self):
        self.assert_all_refused_by_the_haven(self.room1, self.room2)

    # Who: outside a haven, player against player alone, while it is off.

    def test_outside_only_a_character_against_a_character_is_refused(self):
        self.assertEqual(self.refusals(self.room1, self.room1, False), {
            "character against creature": None,
            "creature against character": None,
            "creature against creature": None,
            "character against character": self.pvp_line(self.char1, self.char2),
            "character against statue": self.pvp_line(self.char1, self.statue),
            "character against sweeper": None,
        })

    def test_outside_with_the_constant_on_nothing_is_refused(self):
        self.assertEqual(
            self.refusals(self.room1, self.room1, True),
            {label: None for label, _, _ in self.pairs()},
        )

    def test_an_evennia_default_character_is_no_player(self):
        # Choice 1 at HV-T4's STOPP 0: the game's class, not Evennia's.
        other = create_object(
            "evennia.objects.objects.DefaultCharacter", key="other", location=self.room1)
        self.assertIsNone(attack_refusal(self.char1, other))
        self.assertIsNone(attack_refusal(other, self.char1))

    # The name (TR5, P4).

    def test_a_stranger_is_named_by_short_description(self):
        line = attack_refusal(self.char1, self.char2)
        self.assertEqual(line, "You will not raise a hand against a broad-shouldered man.")
        self.assertNotIn(self.char2.key, line)

    def test_a_recog_names_the_target(self):
        self.char1.recog.add(self.char2, "Bob")
        self.assertEqual(
            attack_refusal(self.char1, self.char2), "You will not raise a hand against Bob.")

    def test_a_statue_is_named_as_a_statue(self):
        self.assertEqual(
            attack_refusal(self.char1, self.statue),
            "You will not raise a hand against |wstone statue of a freckled youth|n.",
        )

    def test_the_haven_line_word_for_word(self):
        self.char1.location = self.room2
        self.assertEqual(
            attack_refusal(self.char1, self.rabbit), "No hand is raised in a haven.")

    def test_the_guard_sends_nothing(self):
        self.char1.msg = mock.Mock()
        self.char2.msg = mock.Mock()
        attack_refusal(self.char1, self.char2)
        self.char2.location = self.room2
        attack_refusal(self.char1, self.char2)
        self.char1.msg.assert_not_called()
        self.char2.msg.assert_not_called()


def pvp_reaches(tree):
    """How many times a module names `PVP_ENABLED` in code."""
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == CONSTANT:
            count += 1
        elif isinstance(node, ast.Attribute) and node.attr == CONSTANT:
            count += 1
        elif isinstance(node, ast.alias) and node.name == CONSTANT:
            count += 1
        elif isinstance(node, ast.Constant) and node.value == CONSTANT:
            count += 1
    return count


def pvp_census():
    """The production files that name `PVP_ENABLED`, as paths from the root."""
    found = set()
    for top in PRODUCTION:
        for path in sorted((ROOT / top).rglob("*.py")):
            if pvp_reaches(ast.parse(path.read_text(encoding="utf-8"))):
                found.add(path.relative_to(ROOT).as_posix())
    return found


class TestPvpCensus(TestCase):
    """The switch is the guard's alone (HV5), and it is off (PV6)."""

    def test_only_the_guard_reads_the_constant(self):
        self.assertEqual(
            pvp_census(), {"world/haven.py"},
            "HV5: PVP_ENABLED is read by world.haven.attack_refusal alone; "
            "whoever wants to know whether an attack may begin asks "
            "attack_refusal, or says why here.",
        )

    def test_player_against_player_is_switched_off(self):
        self.assertIs(
            haven.PVP_ENABLED, False,
            "PV6: opening player against player is a decision of its own. It "
            "needs the haven in service, the series note law/crime/bounties "
            "written, and the statue question answered (Combat Design §4.2). "
            "The commit that opens it changes this test and says so.",
        )

    def test_each_form_of_the_constant_is_found(self):
        self.assertEqual(pvp_reaches(ast.parse(textwrap.dedent('''
            on = PVP_ENABLED
            on = haven.PVP_ENABLED
            from world.haven import PVP_ENABLED
            on = getattr(haven, "PVP_ENABLED")
        '''))), 4)

    def test_the_guard_called_or_named_in_prose_is_not_found(self):
        self.assertEqual(pvp_reaches(ast.parse(textwrap.dedent('''
            """A docstring that names PVP_ENABLED."""
            from world.haven import attack_refusal
            # a comment on PVP_ENABLED
            line = attack_refusal(attacker, target)
        '''))), 0)
