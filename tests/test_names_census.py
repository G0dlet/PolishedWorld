"""
No room message names a character by key, or with no looker. Names, Task
NM-T10 (docs/PolishedWorld_Combat_Decomposition.md, NM12; the Names note's
UP10, UP11).

A room message is resolved per reader only when the character in it goes
through `$You()` or `mapping`: `msg_contents` then calls
`get_display_name(looker=receiver)` for each reader. A `.key` names the
character to everyone by its true name, and a `get_display_name()` with no
looker names it as nobody in particular knows it. This census reads the
source of every production module and finds both.

WHAT IT READS
-------------
Every call to `msg_contents` in `commands/`, `typeclasses/` and `world/`.
The message is the first argument (or `text=`); when that is a bare name,
every assignment to that name in the same function is read as well, and so
is the `mapping=` argument (a `.key` there is a string, shown to every
reader as it is). In those it flags:

- `<name>.key` or `<name>.name`, where `<name>` is one of RECEIVERS -- the
  names this codebase binds to a character -- or `self` inside a class in
  CHARACTER_CLASSES. `self.key` in a Creature or a Corpse names the thing
  itself, not a character, and is not flagged;
- any `<expr>.get_display_name()` with no argument at all, whatever it is
  called on (NM-T10 lock 2 B): a new one fails here until someone has said
  what it names.

The known sites are pinned exactly, with their reason (KNOWN). A site fixed
while still listed fails too, so the list cannot go stale.

WHAT IT DOES NOT READ
---------------------
- Lines sent with `for_contents` (`Character.at_post_puppet`'s *has entered
  the game*, NM-T11) or with `msg` one receiver at a time.
- Evennia's own `msg_contents` calls. `Character.announce_move_from` and
  `announce_move_to` hand Evennia a `$You()` template (NM-T10 lock 1 A); the
  site tests in `test_names_room_messages` read those lines.
- A message built in another function and passed in.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_census
"""

import ast
import pathlib
import textwrap
from unittest import TestCase

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCTION = ("commands", "typeclasses", "world")

# Names this codebase binds to a character when it tells a room about one.
RECEIVERS = frozenset({"caller", "char", "killer", "target", "student", "teacher"})
# Classes whose `self` is a character.
CHARACTER_CLASSES = frozenset({"Character"})
NAME_ATTRIBUTES = ("key", "name")

# (file, function) -> the faults found there, sorted. Each with its reason.
KNOWN = {
    # Not a character: the water source, the vessel, the resource node and
    # the container are objects; one name for every reader is right (NM-T9).
    ("commands/consumption_commands.py", "CmdDrink._drink_from_source"):
        ["source.get_display_name()"],
    ("commands/consumption_commands.py", "CmdEmpty.func"):
        ["obj.get_display_name()"],
    ("commands/foraging_commands.py", "CmdForage.func"):
        ["node.get_display_name()"],
    ("commands/foraging_commands.py", "CmdRefill.func"):
        ["container.get_display_name()"],
    # NM-T11's: the statue's two lines, converted with the statue's look.
    ("typeclasses/characters.py", "Character.at_post_unpuppet"): ["self.key"],
    ("typeclasses/characters.py", "Character.at_post_puppet"): ["self.key"],
}


def _message(call):
    """The message expression of a `msg_contents` call, or None."""
    if call.args:
        return call.args[0]
    for keyword in call.keywords:
        if keyword.arg == "text":
            return keyword.value
    return None


def _assigned(func, name):
    """Every value assigned to `name` in `func`."""
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
                yield node.value
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            if isinstance(node.target, ast.Name) and node.target.id == name and node.value:
                yield node.value


def _faults_in(expression, self_is_character):
    """The faults in one message expression, as source text."""
    found = []
    for node in ast.walk(expression):
        if (isinstance(node, ast.Attribute) and node.attr in NAME_ATTRIBUTES
                and isinstance(node.value, ast.Name)):
            owner = node.value.id
            if owner in RECEIVERS or (owner == "self" and self_is_character):
                found.append(ast.unparse(node))
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get_display_name"
                and not node.args and not node.keywords):
            found.append(ast.unparse(node))
    return found


def census(tree):
    """{function's qualified name: sorted faults} for one module's AST."""
    result = {}

    def visit(node, prefix, klass):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, f"{prefix}{child.name}.", child.name)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = f"{prefix}{child.name}"
                own = _own_calls(child)
                faults = []
                for call in own:
                    message = _message(call)
                    if message is None:
                        continue
                    expressions = [message]
                    if isinstance(message, ast.Name):
                        expressions += list(_assigned(child, message.id))
                    expressions += [k.value for k in call.keywords if k.arg == "mapping"]
                    for expression in expressions:
                        faults += _faults_in(expression, klass in CHARACTER_CLASSES)
                if faults:
                    result[qual] = sorted(faults)
                # A nested def keeps its class's `self`.
                visit(child, f"{qual}.", klass)
            else:
                visit(child, prefix, klass)

    visit(tree, "", None)
    return result


def _own_calls(func):
    """`msg_contents` calls made in `func` itself, not in a def nested in it."""
    nested = {
        id(inner)
        for child in ast.walk(func)
        if child is not func and isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        for inner in ast.walk(child)
    }
    return [
        node for node in ast.walk(func)
        if id(node) not in nested and isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute) and node.func.attr == "msg_contents"
    ]


def production_census():
    """{(file, function): faults} over every production module."""
    found = {}
    for top in PRODUCTION:
        for path in sorted((ROOT / top).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            if "/migrations/" in rel:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for qual, faults in census(tree).items():
                found[(rel, qual)] = faults
    return found


def _fixture(source):
    return census(ast.parse(textwrap.dedent(source)))


class TestNamesCensus(TestCase):
    """The production modules hold exactly the known sites (NM12)."""

    def test_room_messages_are_pinned(self):
        self.assertEqual(production_census(), KNOWN)

    def test_the_census_reads_something(self):
        # Receipt that the walk finds calls at all: the modules hold dozens
        # of `msg_contents`, and a census that saw none would pass the pin
        # only if KNOWN were empty.
        calls = 0
        for top in PRODUCTION:
            for path in (ROOT / top).rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                calls += sum(
                    1 for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "msg_contents"
                )
        self.assertGreater(calls, 20)


class TestCensusFixtures(TestCase):
    """The census fails on each of the two faults, and on nothing else."""

    def test_a_key_is_found(self):
        found = _fixture('''
            def _announce(char):
                char.location.msg_contents(f"{char.key} gets up.", exclude=char)
        ''')
        self.assertEqual(found, {"_announce": ["char.key"]})

    def test_a_key_in_a_template_is_found(self):
        found = _fixture('''
            class Character:
                def collapse(self):
                    self.location.msg_contents(FALL_ROOM.format(name=self.key), exclude=self)
        ''')
        self.assertEqual(found, {"Character.collapse": ["self.key"]})

    def test_a_name_without_a_looker_is_found(self):
        found = _fixture('''
            class CmdSit:
                def func(self):
                    caller = self.caller
                    caller.location.msg_contents(f"{caller.get_display_name()} sits.")
        ''')
        self.assertEqual(found, {"CmdSit.func": ["caller.get_display_name()"]})

    def test_a_message_built_first_is_read(self):
        found = _fixture('''
            def _announce(char):
                text = f"{char.name} gets up."
                char.location.msg_contents(text, exclude=char)
        ''')
        self.assertEqual(found, {"_announce": ["char.name"]})

    def test_you_and_mapping_pass(self):
        found = _fixture('''
            class Character:
                def rest(self):
                    self.location.msg_contents(
                        "$You() settles down.", from_obj=self, exclude=self)
                    self.location.msg_contents(
                        "{a} nods to {b}.", mapping={"a": self, "b": self.location})
        ''')
        self.assertEqual(found, {})

    def test_a_key_in_the_mapping_is_found(self):
        found = _fixture('''
            class Character:
                def nod(self):
                    self.location.msg_contents("{a} nods.", mapping={"a": self.key})
        ''')
        self.assertEqual(found, {"Character.nod": ["self.key"]})

    def test_self_outside_a_character_is_not_a_character(self):
        found = _fixture('''
            class Creature:
                def at_death(self, killer=None):
                    self.location.msg_contents(f"{self.key} dies.")
        ''')
        self.assertEqual(found, {})
