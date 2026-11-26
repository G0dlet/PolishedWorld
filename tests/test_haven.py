"""
Unit tests for `world/haven.py`. Haven Decomposition, Task HV-T1 (the Combat
Design's §4.2: PV3, HV2, HV3).

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

What the seed writes is `tests/test_seeding.py`'s: each seeded room through
`is_haven`, the Attribute on the haven alone, and a re-seed that leaves the
flags as staff left them.

WHAT THE CENSUS DOES NOT READ
-----------------------------
A key held in a variable or built from pieces; Django templates (`.html`);
`tests/`; `@set` in the game. A reach of one of those kinds is read by eye
when it is written.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_haven
"""

import ast
import pathlib
import textwrap
from unittest import TestCase

from evennia.utils.test_resources import EvenniaTest

from world.haven import is_haven

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
