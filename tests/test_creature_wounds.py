"""
Tests for world.creature_wounds -- a creature's numbers (Creatures
decomposition, slice CE, task CE-T1; Combat Design CR1, CE2-CE4, CE7, CE13)
and its door, `Creature.apply_health_damage` (CE-T2; CR2, CE5, CE9).

Every expected number is the book's -- core p. 146 and *Monsters of Legend*
pp. 12 and 103-122 -- typed here and never computed from the code under
test.
"""

import ast
import pathlib
from unittest import mock

from evennia.prototypes.spawner import spawn
from evennia.utils.create import create_object
from evennia.utils.test_resources import EvenniaTest, EvenniaTestCase
from evennia.utils.utils import class_from_module

from typeclasses.creatures import Creature
from world import creature_wounds as cw
from world import prototypes as world_prototypes
from world import wounds

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCTION = ("commands", "server", "typeclasses", "web", "world")


# Every class here that makes an object is an EvenniaTest, not an
# EvenniaTestCase. A creature made with no home takes settings.DEFAULT_HOME,
# `#2`; under EvenniaTestCase there is no such row, and a `#2` an earlier
# test in the same worker left in the idmapper cache becomes a home that is
# not in the database -- an IntegrityError at teardown, in whichever test
# meets it (a parallel run, 2026-11-26; reproduced by a probe). EvenniaTest
# makes its own rooms first, so `#2` is a row of the test (its Room2).
# A class that makes nothing, such as the census, needs neither.


def _creature(**attributes):
    """A bare Creature with exactly the Attributes given, and no prototype."""
    return create_object(
        Creature, key="testbeast", attributes=list(attributes.items())
    )


def _four(creature):
    """The four readers, in the in-game check's order."""
    return (
        cw.general_hit_points_of(creature),
        cw.critical_rating_of(creature),
        cw.resilience_of(creature),
        cw.armour_points_of(creature),
    )


def _creature_prototypes():
    """Every prototype in world/prototypes.py whose typeclass is a Creature."""
    return [
        value
        for value in vars(world_prototypes).values()
        if isinstance(value, dict)
        and "prototype_key" in value
        and "typeclass" in value
        and issubclass(class_from_module(value["typeclass"]), Creature)
    ]


class TestCreatureCensus(EvenniaTestCase):
    """
    Every creature prototype names its own CON (CE3). The class's `con` is
    None (CE13), so a species that forgets it spawns creatures that cannot
    be hurt -- and nothing else would say so until the first blow.
    """

    def test_the_census_reads_the_rabbit(self):
        # A census that finds nothing passes for ever: hold it to one we know.
        keys = {proto["prototype_key"] for proto in _creature_prototypes()}
        self.assertIn("rabbit", keys)

    def test_every_creature_prototype_names_its_con(self):
        # No subTest: a failing subTest cannot be sent back from a parallel
        # worker (Testing Reference §28.1). The failures are collected.
        bad = [
            (proto["prototype_key"], proto.get("con"))
            for proto in _creature_prototypes()
            if not (type(proto.get("con")) is int and proto["con"] > 0)
        ]
        self.assertEqual(
            bad,
            [],
            "every creature prototype must set `con` to a whole number above "
            "0 (Creatures CE3: CON is stored on the creature and set by the "
            "prototype; the class default None means it cannot be hurt, CE13)",
        )


class TestTheRabbit(EvenniaTest):
    """The rabbit as the prototype makes it (CE2): CON 4, SIZ 4, no armour."""

    def test_four_two_twenty_two_nothing(self):
        # The in-game check's expression: a broken reader or prototype shows
        # here as it would in play.
        rabbit = spawn("rabbit")[0]
        self.assertEqual(_four(rabbit), (4, 2, 22, 0))


class TestHitPointsAndRating(EvenniaTest):
    """General Hit Points and the rating, both rounded up (p. 146; CE4)."""

    def test_the_books_example(self):
        # CON 12, SIZ 16: 14 Hit Points, rating 7 (p. 146). An even sum, so it
        # cannot tell up from down -- the next two can.
        beast = _creature(con=12, siz=16)
        self.assertEqual(
            (cw.general_hit_points_of(beast), cw.critical_rating_of(beast)),
            (14, 7),
        )

    def test_an_odd_sum_rounds_up(self):
        # CON 11, SIZ 4: 7.5 is 8, not 7 (CEM1). The rating, 4, is even.
        beast = _creature(con=11, siz=4)
        self.assertEqual(
            (cw.general_hit_points_of(beast), cw.critical_rating_of(beast)),
            (8, 4),
        )

    def test_odd_hit_points_round_the_rating_up(self):
        # CON 10, SIZ 3: 6.5 is 7 Hit Points, and 3.5 is a rating of 4, not 3
        # (CEM2). Every other case here has an even number of Hit Points.
        beast = _creature(con=10, siz=3)
        self.assertEqual(
            (cw.general_hit_points_of(beast), cw.critical_rating_of(beast)),
            (7, 4),
        )


# Monsters of Legend, *Natural life* (pp. 103-122): (CON, printed Resilience).
FORMULA = {                      # three of the fifteen that follow CON x 3 + 10
    "hawk": (4, 22),             # p. 113
    "dog": (11, 43),             # p. 110
    "wolf": (14, 52),
}
PRINTED = {                      # the five that do not (Decomposition §3)
    "deer": (11, 58),            # p. 109; the formula gives 43
    "polar bear": (13, 55),      # p. 105; 49
    "mammoth": (35, 99),         # p. 116; 115
    "sabre tooth tiger": (17, 67),   # p. 121; 61
    "shark": (32, 95),           # p. 119; 106
}


class TestResilience(EvenniaTest):
    """CON x 3 + 10, unless the species stores its own (Monsters p. 12; CE7)."""

    def test_the_formula(self):
        # CEM3: CON x 2 gives 8, 22 and 28.
        got = {name: cw.resilience_of(_creature(con=con, siz=8))
               for name, (con, _) in FORMULA.items()}
        self.assertEqual(got, {name: r for name, (_, r) in FORMULA.items()})

    def test_a_stored_value_goes_before_the_formula(self):
        # CEM4: read after the formula, each of the five gives the formula's.
        got = {name: cw.resilience_of(_creature(con=con, siz=8, resilience=r))
               for name, (con, r) in PRINTED.items()}
        self.assertEqual(got, {name: r for name, (_, r) in PRINTED.items()})


class TestWithoutCon(EvenniaTest):
    """A creature without CON has no numbers, and no reader raises (CE13)."""

    def test_none_from_the_three_and_its_armour_from_the_fourth(self):
        # `is None`, never `or`: a reader that raises or guesses fails here.
        self.assertEqual(_four(_creature(siz=4)), (None, None, None, 0))

    def test_a_stored_resilience_does_not_give_it_one(self):
        # One rule: no CON, no numbers -- not "no CON, unless...".
        self.assertIsNone(cw.resilience_of(_creature(siz=11, resilience=58)))

    def test_armour_does_not_wait_for_con(self):
        self.assertEqual(cw.armour_points_of(_creature(natural_ap=3)), 3)
        self.assertEqual(cw.armour_points_of(_creature(con=4, natural_ap=3)), 3)


class TestNoRowForNone(EvenniaTest):
    """
    `con` and `resilience` are not autocreated (CE-T1's STOPP 0): None is
    the answer, so a row holding None says nothing, and a read must not
    write one. Evennia's default is autocreate=True (CEM4b, CEM4c).
    """

    def test_neither_is_written_at_creation_or_by_the_readers(self):
        beast = _creature(siz=4)
        _four(beast)
        self.assertEqual(
            (bool(beast.attributes.has("con")),
             bool(beast.attributes.has("resilience"))),
            (False, False),
        )

    def test_the_rabbit_stores_its_con_and_no_resilience(self):
        rabbit = spawn("rabbit")[0]
        self.assertEqual(
            (rabbit.attributes.get("con"),
             bool(rabbit.attributes.has("resilience"))),
            (4, False),
        )


# --- CE-T2: the door ------------------------------------------------------

# An attack roll that succeeded: the door only reads whether it did (CE9).
MADE = {"result": "success", "success": True, "roll": 30, "target": 60}
MISSED = {"result": "failure", "success": False, "roll": 90, "target": 60}
ROWS = ("general_damage", "damage_source")


def _rabbit_in(room):
    """A rabbit as the prototype makes it, standing in `room`."""
    rabbit = spawn("rabbit")[0]
    rabbit.move_to(room, quiet=True, move_hooks=False)
    return rabbit


def _rows(creature):
    """Which of the door's two Attributes the creature holds."""
    return tuple(bool(creature.attributes.has(key)) for key in ROWS)


def _corpses(room):
    return [obj for obj in room.contents if obj.key == "rabbit corpse"]


def _callers_of_at_death():
    """(file, qualified function) of every `X.at_death(...)` in production."""
    found = set()
    for top in PRODUCTION:
        for path in sorted((ROOT / top).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            rel = path.relative_to(ROOT).as_posix()

            def walk(node, stack):
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                          ast.ClassDef)):
                        walk(child, stack + [child.name])
                        continue
                    if (isinstance(child, ast.Call)
                            and isinstance(child.func, ast.Attribute)
                            and child.func.attr == "at_death"):
                        found.add((rel, ".".join(stack)))
                    walk(child, stack)

            walk(tree, [])
    return found


class TestTheRoadsToDeath(EvenniaTestCase):
    """
    One road to a creature's death, `at_death`, and its callers by name
    (CE9). A caller that reaches it some other way -- a `delete()` with no
    corpse, a second death of its own -- fails here first. CE-T3 adds the
    alarm.
    """

    def test_the_door_and_hunt(self):
        self.assertEqual(
            _callers_of_at_death(),
            {("commands/hunting_commands.py", "CmdHunt.func"),
             ("typeclasses/creatures.py", "Creature.apply_health_damage")},
            "Creatures CE9: a creature dies by `at_death` only, from the door "
            "and from `hunt`; a new caller is a new road to death",
        )


class TestHitPointsLeft(EvenniaTest):
    """`hit_points_of` and `damage_of` read; neither writes (CE3)."""

    def test_unhurt_and_without_con(self):
        rabbit = spawn("rabbit")[0]
        old = _creature(siz=4)
        self.assertEqual(
            (cw.damage_of(rabbit), cw.hit_points_of(rabbit),
             cw.damage_of(old), cw.hit_points_of(old)),
            (0, 4, 0, None),
        )

    def test_no_row_at_creation_or_by_the_readers(self):
        rabbit = spawn("rabbit")[0]
        cw.damage_of(rabbit)
        cw.hit_points_of(rabbit)
        self.assertEqual(_rows(rabbit), (False, False))


class TestTheDoor(EvenniaTest):
    """
    `Creature.apply_health_damage` on a rabbit: 4 General Hit Points and a
    Critical Wound rating of 2 (CE-T1), so it dies at -2 (CE5).
    """

    def test_one_two_and_three_points_it_lives(self):
        seen = []
        for amount in (1, 2, 3):
            rabbit = _rabbit_in(self.room1)
            answer = rabbit.apply_health_damage(amount, location="chest")
            seen.append((answer, cw.hit_points_of(rabbit), bool(rabbit.pk)))
        self.assertEqual(seen, [
            ({"dies": False, "hit_points": 3}, 3, True),
            ({"dies": False, "hit_points": 2}, 2, True),
            ({"dies": False, "hit_points": 1}, 1, True),
        ])

    def test_death_is_at_minus_the_rating(self):
        # CE5: the rule, not the example. At 0 and at -1 it lives (what
        # happens there is CE-T3's); at -2 it dies (CEM5 dies at 0).
        seen = []
        for amount in (4, 5, 6):
            rabbit = _rabbit_in(self.room1)
            seen.append(rabbit.apply_health_damage(amount, location="chest"))
        self.assertEqual(seen, [
            {"dies": False, "hit_points": 0},
            {"dies": False, "hit_points": -1},
            {"dies": True, "hit_points": -2},
        ])

    def test_six_at_once_leaves_one_corpse_and_no_rabbit(self):
        rabbit = _rabbit_in(self.room1)
        rabbit.apply_health_damage(6, location="chest")
        self.assertEqual((rabbit.pk, len(_corpses(self.room1))), (None, 1))

    def test_three_and_three_add_up(self):
        # CEM7: a door that sets the damage and does not add it leaves the
        # rabbit at 1 Hit Point after the second blow.
        rabbit = _rabbit_in(self.room1)
        first = rabbit.apply_health_damage(3, location="chest")
        second = rabbit.apply_health_damage(3, location="chest")
        self.assertEqual(
            (first, second, rabbit.pk, len(_corpses(self.room1))),
            ({"dies": False, "hit_points": 1}, {"dies": True, "hit_points": -2},
             None, 1),
        )

    def test_the_source_reaches_at_death(self):
        # CEM8 (`at_death(None)`): the room would read *dies*, not the killer.
        rabbit = _rabbit_in(self.room1)
        with mock.patch.object(type(self.room1), "msg_contents",
                               autospec=True) as told:
            rabbit.apply_health_damage(6, location="chest", source=self.char1)
        self.assertEqual(
            [(c.args[1], c.kwargs.get("from_obj")) for c in told.call_args_list],
            [("$You() fells rabbit.", self.char1)],
        )

    def test_a_source_that_is_not_an_object_dies_without_a_killer(self):
        # A string, as the survival ticker gives a character: at_death would
        # call "survival".msg() half-way through the death.
        rabbit = _rabbit_in(self.room1)
        with mock.patch.object(type(self.room1), "msg_contents",
                               autospec=True) as told:
            answer = rabbit.apply_health_damage(6, location=wounds.ALL,
                                                source="survival")
        self.assertEqual(
            (answer["dies"], [c.args[1] for c in told.call_args_list],
             len(_corpses(self.room1))),
            (True, ["rabbit dies."], 1),
        )

    def test_the_latest_source_is_stored_and_none_clears_it(self):
        rabbit = _rabbit_in(self.room1)
        rabbit.apply_health_damage(1, location="chest", source=self.char1)
        stored = rabbit.attributes.get("damage_source")
        rabbit.apply_health_damage(1, location="chest", source=self.char2)
        replaced = rabbit.attributes.get("damage_source")
        rabbit.apply_health_damage(1, location="chest")
        self.assertEqual(
            (stored, replaced, bool(rabbit.attributes.has("damage_source"))),
            (self.char1, self.char2, False),
        )

    def test_nothing_for_zero_and_less(self):
        rabbit = _rabbit_in(self.room1)
        answers = [rabbit.apply_health_damage(amount, location="chest",
                                              source=self.char1)
                   for amount in (0, -1)]
        self.assertEqual((answers, _rows(rabbit)), ([None, None], (False, False)))

    def test_every_refusal_writes_nothing_whatever_the_amount(self):
        # CEM6: a refusal after the write leaves a row. No subTest (Testing
        # Reference §28.1): the failures are collected.
        old = _creature(siz=4)
        old.move_to(self.room1, quiet=True, move_hooks=False)
        cases = (
            ("a place that is none", None, "tail", None),
            ("ALL with an attack roll (WN5)", None, wounds.ALL, MADE),
            ("an attack roll that missed", None, "chest", MISSED),
            ("a creature without CON (CE13)", old, "chest", None),
        )
        bad = []
        for name, target, location, made in cases:
            for amount in (3, 0):
                creature = target or _rabbit_in(self.room1)
                try:
                    creature.apply_health_damage(amount, location=location,
                                                 made=made, source=self.char1)
                except ValueError:
                    pass
                else:
                    bad.append((name, amount, "no ValueError"))
                if _rows(creature) != (False, False):
                    bad.append((name, amount, _rows(creature)))
        self.assertEqual(bad, [])

    def test_a_successful_roll_and_every_place_are_taken(self):
        seen = []
        for location in (wounds.RANDOM, "head", "left_leg"):
            rabbit = _rabbit_in(self.room1)
            seen.append(rabbit.apply_health_damage(1, location=location,
                                                   made=MADE))
        self.assertEqual(seen, [{"dies": False, "hit_points": 3}] * 3)

    def test_a_deleted_creature_answers_nothing(self):
        # Two blows in one tick: the first kills and deletes, the second
        # holds the same reference.
        rabbit = _rabbit_in(self.room1)
        rabbit.apply_health_damage(6, location="chest")
        self.assertIsNone(rabbit.apply_health_damage(3, location="chest"))
