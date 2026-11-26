"""
Tests for world.creature_wounds -- a creature's numbers (Creatures
decomposition, slice CE, task CE-T1; Combat Design CR1, CE2-CE4, CE7, CE13)
and its door, `Creature.apply_health_damage` (CE-T2; CR2, CE5, CE9), the
state at 0 Hit Points on stored points in time (CE-T3; CE6), the
Critical Wound table rolled in the door (CE-T4; CE8), and healing counted
at the read (CE-T5; CE10, CE11).

Every expected number is the book's -- core pp. 145-147 and *Monsters of
Legend* pp. 12 and 103-122, and core p. 86's healing table -- typed here and never computed from the code
under test.
"""

import ast
import pathlib
from unittest import mock

from django.test import override_settings
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
ROWS = ("general_damage", "damage_source", "hurt_state", "heal_anchor")


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
    corpse, a second death of its own -- fails here first. CE-T3 added the
    alarm, `_state_due`.
    """

    def test_the_door_and_hunt(self):
        self.assertEqual(
            _callers_of_at_death(),
            {("commands/hunting_commands.py", "CmdHunt.func"),
             ("typeclasses/creatures.py", "Creature.apply_health_damage"),
             ("world/creature_wounds.py", "_state_due")},
            "Creatures CE9: a creature dies by `at_death` only, from the door, "
            "its alarm and `hunt`; a new caller is a new road to death",
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
        self.assertEqual(_rows(rabbit), (False, False, False, False))


# CE-T3: the die, the clock and the alarm, patched in the module (Testing
# Reference §27.2). The rabbit's Resilience is 22: 15 wins, 50 loses.
ROLL = "world.skillcheck.randint"
WIN, LOSE = 15, 50
# CE-T4: the Critical Wound table's 1D20, the module's own die. It stands at
# 1 unless a test says otherwise: row 01, Dazed, tests nothing and stores
# nothing, so a blow above the rating changes no state the test reads.
DIE = "world.creature_wounds.randint"
NOW = 1000.0
FALL = "rabbit sags onto its side, breathing fast and shallow."


class _AtZero(EvenniaTest):
    """
    `world.creature_wounds.time` and `.delay` patched, and the die; every
    line to a room recorded as (room, text, from_obj). An alarm is fired by
    calling `cw._state_due` by hand, in the order the test writes.

    CE-T5: the game clock is patched where the module reads it,
    `world.gametime_utils.get_absolute_gametime` (the module is imported
    whole), and stands at 0 unless a test moves it: an anchor of 0 is
    falsy, so every test that hurts at 0 presses `is None` against a
    truth test. A corpse takes the same time; no test reads it.
    """

    def setUp(self):
        super().setUp()
        self.clock = self._patch(mock.patch("world.creature_wounds.time"))
        self.clock.time.return_value = NOW
        self.alarm = self._patch(mock.patch("world.creature_wounds.delay"))
        self.roll = self._patch(mock.patch(ROLL, return_value=WIN))
        self.die = self._patch(mock.patch(DIE, return_value=1))
        self.told = self._patch(mock.patch.object(
            type(self.room1), "msg_contents", autospec=True))
        self.game = self._patch(mock.patch(
            "world.gametime_utils.get_absolute_gametime", return_value=0))

    def _patch(self, patcher):
        found = patcher.start()
        self.addCleanup(patcher.stop)
        return found

    def at(self, seconds):
        """The clock `seconds` after NOW."""
        self.clock.time.return_value = NOW + seconds

    def game_at(self, seconds):
        """The game clock at `seconds` of game time (CE-T5)."""
        self.game.return_value = seconds

    def lines(self):
        return [(c.args[0], c.args[1], c.kwargs.get("from_obj"))
                for c in self.told.call_args_list]


def _answer(dies, hit_points, test=None, state=None, row=None, effects=(),
            row_test=None):
    return {"dies": dies, "hit_points": hit_points, "test": test, "state": state,
            "row": row, "effects": effects, "row_test": row_test}


# A blow of 3 on a rabbit is above its rating of 2 (CE-T4), and the die's 1
# is row 01.
DAZED_ROW = {"row": 1, "effects": ("dazed",)}


class TestTheDoor(_AtZero):
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
            (_answer(False, 3), 3, True),
            (_answer(False, 2), 2, True),
            (_answer(False, 1, **DAZED_ROW), 1, True),
        ])

    def test_death_is_at_minus_the_rating(self):
        # CE5: the rule, not the example. At 0 and at -1 it lives and
        # tests (CE-T3; the die wins here); at -2 it dies (CEM5 dies at 0).
        seen = []
        for amount in (4, 5, 6):
            rabbit = _rabbit_in(self.room1)
            answer = rabbit.apply_health_damage(amount, location="chest")
            seen.append((answer["dies"], answer["hit_points"], answer["state"]))
        self.assertEqual(seen, [(False, 0, "standing"), (False, -1, "standing"),
                                (True, -2, None)])

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
            (_answer(False, 1, **DAZED_ROW), _answer(True, -2),
             None, 1),
        )

    def test_the_source_reaches_at_death(self):
        # CEM8 (`at_death(None)`): the room would read *dies*, not the killer.
        rabbit = _rabbit_in(self.room1)
        rabbit.apply_health_damage(6, location="chest", source=self.char1)
        self.assertEqual(self.lines(),
                         [(self.room1, "$You() fells rabbit.", self.char1)])

    def test_a_source_that_is_not_an_object_dies_without_a_killer(self):
        # A string, as the survival ticker gives a character: at_death would
        # call "survival".msg() half-way through the death.
        rabbit = _rabbit_in(self.room1)
        answer = rabbit.apply_health_damage(6, location=wounds.ALL,
                                            source="survival")
        self.assertEqual(
            (answer["dies"], self.lines(), len(_corpses(self.room1))),
            (True, [(self.room1, "rabbit dies.", None)], 1),
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
        self.assertEqual((answers, _rows(rabbit)),
                         ([None, None], (False, False, False, False)))

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
                if _rows(creature) != (False, False, False, False):
                    bad.append((name, amount, _rows(creature)))
        self.assertEqual(bad, [])

    def test_a_successful_roll_and_every_place_are_taken(self):
        seen = []
        for location in (wounds.RANDOM, "head", "left_leg"):
            rabbit = _rabbit_in(self.room1)
            seen.append(rabbit.apply_health_damage(1, location=location,
                                                   made=MADE))
        self.assertEqual(seen, [_answer(False, 3)] * 3)

    def test_a_deleted_creature_answers_nothing(self):
        # Two blows in one tick: the first kills and deletes, the second
        # holds the same reference.
        rabbit = _rabbit_in(self.room1)
        rabbit.apply_health_damage(6, location="chest")
        self.assertIsNone(rabbit.apply_health_damage(3, location="chest"))


# --- CE-T3: the state at 0 Hit Points -------------------------------------


class TestAtZero(_AtZero):
    """
    A rabbit taken to 0 by a blow of 4 tests Resilience (p. 146; CE6):
    won, it stands and tests again a round on; lost, it falls senseless and
    dies its rating in Combat Actions on -- 2 x 2.5 seconds.
    """

    def _zero(self, roll, **kwargs):
        self.roll.return_value = roll
        rabbit = _rabbit_in(self.room1)
        answer = rabbit.apply_health_damage(4, location="chest", **kwargs)
        return rabbit, answer

    def test_lost_it_falls_and_dies_five_seconds_on(self):
        # Red before green; CEM10 (the time in rounds) gives NOW + 10.
        rabbit, answer = self._zero(LOSE)
        self.assertEqual(
            (answer["state"], answer["test"]["success"], cw.state_of(rabbit),
             self.lines(), self.alarm.call_args),
            ("dying", False, {"kind": "dying", "due": NOW + 5},
             [(self.room1, FALL, None)],
             mock.call(5.0, cw._state_due, rabbit, "dying", NOW + 5,
                       persistent=True)),
        )

    def test_before_its_time_the_alarm_waits_and_at_it_one_corpse(self):
        rabbit, _ = self._zero(LOSE)
        self.at(3)
        cw._state_due(rabbit, "dying", NOW + 5)
        early = (bool(rabbit.pk), self.alarm.call_args)
        self.at(5)
        cw._state_due(rabbit, "dying", NOW + 5)
        self.assertEqual(
            (early, rabbit.pk, len(_corpses(self.room1))),
            ((True, mock.call(2.0, cw._state_due, rabbit, "dying", NOW + 5,
                              persistent=True)), None, 1),
        )

    def test_won_it_stands_says_nothing_and_falls_on_a_later_loss(self):
        rabbit, answer = self._zero(WIN)
        first = (answer["state"], answer["test"]["success"],
                 cw.state_of(rabbit), self.lines())
        self.at(5)
        self.roll.return_value = WIN
        cw._state_due(rabbit, "standing", NOW + 5)
        again = cw.state_of(rabbit)
        self.at(10)
        self.roll.return_value = LOSE
        cw._state_due(rabbit, "standing", NOW + 10)
        fell = (cw.state_of(rabbit), self.lines())
        self.at(15)
        cw._state_due(rabbit, "dying", NOW + 15)
        self.assertEqual(
            (first, again, fell, rabbit.pk, len(_corpses(self.room1))),
            (("standing", True, {"kind": "standing", "due": NOW + 5}, []),
             {"kind": "standing", "due": NOW + 10},
             ({"kind": "dying", "due": NOW + 15}, [(self.room1, FALL, None)]),
             None, 1),
        )

    def test_ninety_six_loses_at_any_resilience(self):
        seen = []
        for roll in (95, 96):
            self.roll.return_value = roll
            beast = _creature(con=4, siz=4, resilience=95)
            beast.move_to(self.room1, quiet=True, move_hooks=False)
            seen.append(beast.apply_health_damage(4, location="chest")["state"])
        self.assertEqual(seen, ["standing", "dying"])

    def test_the_test_is_plain_not_against_the_attack_roll(self):
        # CEM9: the attack roll's 30 taken off the test turns a 15 into a loss.
        rabbit, answer = self._zero(WIN, made=MADE)
        self.assertEqual(answer["state"], "standing")

    def test_a_blow_at_zero_tests_nothing_and_moves_no_time(self):
        # An earlier death is not bought back, and no test is rolled twice
        # (CEM11b tests at every blow at 0).
        seen = []
        for roll in (WIN, LOSE):
            rabbit, _ = self._zero(roll)
            self.at(2)
            self.roll.return_value = LOSE if roll == WIN else WIN
            second = rabbit.apply_health_damage(1, location="chest")
            seen.append((second, cw.state_of(rabbit)))
            self.at(0)
        self.assertEqual(
            (seen, self.alarm.call_count),
            ([(_answer(False, -1, None, "standing"),
               {"kind": "standing", "due": NOW + 5}),
              (_answer(False, -1, None, "dying"),
               {"kind": "dying", "due": NOW + 5})], 2),
        )

    def test_the_killer_in_the_room_is_named_and_gone_is_not(self):
        # CEM12 passes the killer wherever it stands.
        seen = []
        for leaves in (False, True):
            rabbit, _ = self._zero(LOSE, source=self.char1)
            self.char1.move_to(self.room2 if leaves else self.room1, quiet=True,
                               move_hooks=False)
            self.told.reset_mock()
            self.at(5)
            cw._state_due(rabbit, "dying", NOW + 5)
            seen.append([line[1:] for line in self.lines()])
            self.at(0)
        self.assertEqual(seen, [[("$You() fells rabbit.", self.char1)],
                                [("rabbit dies.", None)]])

    def test_nothing_or_a_deleted_creature_and_the_alarm_says_nothing(self):
        # P1: after a reload the creature's place holds None; in the same
        # process a deleted Creature, whose pk is None.
        rabbit, _ = self._zero(LOSE)
        rabbit.delete()
        self.told.reset_mock()
        self.at(5)
        cw._state_due(None, "dying", NOW + 5)
        cw._state_due(rabbit, "dying", NOW + 5)
        self.assertEqual((self.lines(), len(_corpses(self.room1))), ([], 0))

    def test_hunt_first_and_the_alarm_late_leave_one_corpse(self):
        # P2: one road to death, and the pk guard holds.
        rabbit, _ = self._zero(LOSE)
        rabbit.at_death(self.char1)
        self.at(5)
        cw._state_due(rabbit, "dying", NOW + 5)
        self.assertEqual(len(_corpses(self.room1)), 1)

    def test_a_stale_alarm_does_nothing(self):
        # CEM11: an alarm that does not read the state again re-tests here.
        rabbit, _ = self._zero(WIN)
        self.at(5)
        cw._state_due(rabbit, "standing", NOW + 5)   # won again: NOW + 10
        self.roll.return_value = LOSE
        cw._state_due(rabbit, "standing", NOW + 5)   # the old alarm, late
        self.assertEqual(cw.state_of(rabbit), {"kind": "standing", "due": NOW + 10})


# --- CE-T4: the Critical Wound table --------------------------------------

# Core p. 147, cell by cell: the category (the book's merged cells read as
# Dazed for 01-07 and Stunned for 08-14), the effects in the order the cell
# names them, and the test the row calls for. Knocked prone, knocked down
# and falls prone are one key, "prone" (CE-T4's STOPP 0); 1D3 Combat
# Actions are ML's and not rolled.
BOOK = (
    ("Dazed", ("dazed",), None),                                    # 01
    ("Dazed", ("dazed",), None),                                    # 02
    ("Dazed", ("knocked_back", "dazed"), None),                     # 03
    ("Dazed", ("knocked_back", "dazed"), None),                     # 04
    ("Dazed", ("prone", "dazed"), None),                            # 05
    ("Dazed", ("prone", "dazed"), None),                            # 06
    ("Dazed", ("dazed",), "senseless"),                             # 07
    ("Stunned", ("stunned",), None),                                # 08
    ("Stunned", ("stunned",), None),                                # 09
    ("Stunned", ("knocked_back", "stunned"), None),                 # 10
    ("Stunned", ("knocked_back", "stunned"), None),                 # 11
    ("Stunned", ("prone", "stunned"), None),                        # 12
    ("Stunned", ("prone", "stunned"), None),                        # 13
    ("Stunned", ("stunned",), "senseless"),                         # 14
    ("Arm Disabled", ("arm_disabled", "dazed", "drops_held"), None),  # 15
    ("Leg Disabled", ("leg_disabled", "dazed", "prone"), None),     # 16
    ("Abdominal Injury", ("stunned",), "death"),                    # 17
    ("Chest Injury", ("stunned",), "death"),                        # 18
    ("Head Injury", ("stunned",), "death"),                         # 19
    ("Fatal Injury", ("fatal",), None),                             # 20
)
CRIT = {"result": "critical", "success": True, "roll": 3, "target": 60}
OUT_LINE = "rabbit drops where it stands, its sides still rising and falling."
WAKE = "rabbit twitches, then struggles back onto its feet."


class TestTheTable(EvenniaTestCase):
    """The table as data (CE8): makes no object, so needs no rooms."""

    def test_the_twenty_rows_cell_by_cell(self):
        # A wrong cell, or the table one row out (n for n - 1).
        table = cw.CRITICAL_TABLE
        seen = tuple((row.category, row.effects, row.test) for row in table)
        bad = [(number, got, want)
               for number, (got, want) in enumerate(zip(seen, BOOK), start=1)
               if got != want]
        self.assertEqual((type(table), len(table), bad), (tuple, 20, []))


class TestTheRoll(_AtZero):
    """
    When the table is rolled and which row it gives (p. 147; CE8): a single
    blow above the rating, 1D20 less the Armour Points, plus the damage on a
    critical hit; below 1 is no row, above 20 is row 20.
    """

    def _blow(self, amount, die, natural_ap=0, **kwargs):
        self.die.return_value = die
        rabbit = _rabbit_in(self.room1)
        rabbit.natural_ap = natural_ap
        return rabbit, rabbit.apply_health_damage(amount, location="chest",
                                                  **kwargs)

    def test_a_blow_at_the_rating_rolls_nothing_and_one_above_rolls(self):
        # Red before green. CEM13 (at or above) rolls for the 2.
        _, at = self._blow(2, 1)
        rolled_at = self.die.call_args_list[:]
        _, above = self._blow(3, 1)
        self.assertEqual(
            ((at["row"], rolled_at), (above["row"], self.die.call_args_list)),
            ((None, []), (1, [mock.call(1, 20)])),
        )

    def test_a_blow_that_kills_outright_rolls_nothing(self):
        # CEM13b: the table before death outright (STOPP 0, choice 1).
        _, answer = self._blow(6, 20)
        self.assertEqual((answer, self.die.call_count, self.roll.call_count),
                         (_answer(True, -2), 0, 0))

    def test_the_broos_armour_is_taken_off_the_roll(self):
        # p. 147: 13 less 3 is row 10. CEM14 adds the armour: row 16.
        _, answer = self._blow(3, 13, natural_ap=3)
        self.assertEqual((answer["row"], answer["effects"]),
                         (10, ("knocked_back", "stunned")))

    def test_below_one_is_no_row(self):
        # 3 less 3 and 2 less 3. CEM14c (below 0) reads the 0 as row 20.
        seen = [self._blow(3, die, natural_ap=3)[1] for die in (3, 2)]
        self.assertEqual(seen, [_answer(False, 1)] * 2)

    def test_a_critical_adds_the_damage_and_a_success_does_not(self):
        # CEM14b leaves the critical at 10.
        seen = [self._blow(3, 10, made=made)[1]["row"] for made in (MADE, CRIT)]
        self.assertEqual(seen, [10, 13])

    def test_above_twenty_is_row_twenty(self):
        # 19 plus 4: the rabbit at 0 dies of row 20, not of its Hit Points.
        rabbit, answer = self._blow(4, 19, made=CRIT)
        self.assertEqual(
            (answer, rabbit.pk, len(_corpses(self.room1))),
            (_answer(True, 0, row=20, effects=("fatal",)), None, 1),
        )

    def test_every_rows_effects_reach_the_answer_and_none_is_stored(self):
        # CE8: the fight's rows are handed back and stored nowhere. The
        # test is won wherever a row calls for one.
        bad = []
        for number in range(1, 21):
            self.die.return_value = number
            rabbit = _rabbit_in(self.room1)
            before = {a.key for a in rabbit.attributes.all()}
            answer = rabbit.apply_health_damage(3, location="chest")
            if (answer["row"], answer["effects"]) != (number, BOOK[number - 1][1]):
                bad.append((number, answer["row"], answer["effects"]))
            if rabbit.pk:
                added = {a.key for a in rabbit.attributes.all()} - before
                # CE-T5: the first blow anchors the healing.
                if added != {"general_damage", "heal_anchor"}:
                    bad.append((number, sorted(added)))
        self.assertEqual(bad, [])


class TestTheRowsThatTest(_AtZero):
    """
    The rows the door carries out (CE8): 17-19 test Resilience or die, 20
    dies, 07 and 14 test Resilience or are knocked senseless -- with Hit
    Points left, awake after the blow's damage in minutes (p. 145); at 0 or
    below, dying (STOPP 0, choices 5 and 6).
    """

    def _row(self, number, amount, *rolls, beast=None):
        self.die.return_value = number
        self.roll.side_effect = list(rolls)
        target = beast or _rabbit_in(self.room1)
        return target, target.apply_health_damage(amount, location="chest",
                                                  source=self.char1)

    def test_rows_seventeen_to_nineteen_lost_kill_and_won_live(self):
        # CEM15 kills without the test: the won rabbits die too.
        seen = []
        for number in (17, 18, 19):
            for roll in (LOSE, WIN):
                self.told.reset_mock()
                rabbit, answer = self._row(number, 3, roll)
                seen.append((number, answer["dies"],
                             answer["row_test"]["success"], bool(rabbit.pk),
                             [line[1:] for line in self.lines()]))
        killed = [("$You() fells rabbit.", self.char1)]
        self.assertEqual(seen, [
            (17, True, False, False, killed), (17, False, True, True, []),
            (18, True, False, False, killed), (18, False, True, True, []),
            (19, True, False, False, killed), (19, False, True, True, []),
        ])

    def test_row_twenty_kills_with_no_test(self):
        rabbit, answer = self._row(20, 3, WIN)
        self.assertEqual(
            (answer, self.roll.call_count, rabbit.pk, len(_corpses(self.room1))),
            (_answer(True, 1, row=20, effects=("fatal",)), 0, None, 1),
        )

    def test_rows_seven_and_fourteen_lost_knock_it_out_for_the_damage_in_minutes(self):
        # p. 145, three points: 180 seconds. CEM16 counts rounds: 15. Early,
        # the alarm sets itself again for what is left; at its time the
        # rabbit wakes with its Hit Point and no state.
        seen = []
        for number in (7, 14):
            self.told.reset_mock()
            self.at(0)
            rabbit, answer = self._row(number, 3, LOSE)
            fell = (answer["state"], cw.state_of(rabbit), self.lines(),
                    self.alarm.call_args)
            self.at(179)
            cw._state_due(rabbit, "out", NOW + 180)
            early = (cw.state_of(rabbit), self.alarm.call_args)
            self.at(180)
            cw._state_due(rabbit, "out", NOW + 180)
            seen.append((number, fell, early, cw.state_of(rabbit),
                         self.lines()[1:], cw.hit_points_of(rabbit), rabbit))
        out = {"kind": "out", "due": NOW + 180}
        self.assertEqual(
            [s[:6] for s in seen],
            [(number, ("out", out, [(self.room1, OUT_LINE, None)],
                       mock.call(180, cw._state_due, rabbit, "out", NOW + 180,
                                 persistent=True)),
              (out, mock.call(1.0, cw._state_due, rabbit, "out", NOW + 180,
                              persistent=True)),
              None, [(self.room1, WAKE, None)], 1)
             for number, *_, rabbit in seen],
        )

    def test_row_seven_won_with_hit_points_left_changes_nothing(self):
        rabbit, answer = self._row(7, 3, WIN)
        self.assertEqual(
            (answer, cw.state_of(rabbit), self.lines()),
            (_answer(False, 1, row=7, effects=("dazed",),
                     row_test=answer["row_test"]), None, []),
        )
        self.assertTrue(answer["row_test"]["success"])

    def test_row_seven_lost_at_zero_is_dying_with_no_test_at_zero(self):
        # Choice 5: senseless at 0 is the book's dying (p. 146). CEM15b
        # knocks it out instead: the room reads the wrong line.
        rabbit, answer = self._row(7, 4, LOSE, LOSE)
        self.assertEqual(
            (answer["state"], answer["test"], answer["row_test"]["success"],
             cw.state_of(rabbit), self.lines(), self.roll.call_count),
            ("dying", None, False, {"kind": "dying", "due": NOW + 5},
             [(self.room1, FALL, None)], 1),
        )

    def test_row_seven_won_at_zero_then_tests_at_zero(self):
        # Two rules, each with its trigger (choice 5): the row's test won,
        # the test at 0 lost.
        rabbit, answer = self._row(7, 4, WIN, LOSE)
        self.assertEqual(
            (answer["row_test"]["success"], answer["test"]["success"],
             answer["state"], self.lines()),
            (True, False, "dying", [(self.room1, FALL, None)]),
        )

    def test_out_taken_to_zero_is_dying_with_no_line_and_no_senseless_test(self):
        # Choice 6. CON 12 and SIZ 16: 14 Hit Points and a rating of 7
        # (p. 146's example), Resilience 46. 8 on row 07, lost: out for
        # eight minutes at 6. 8 more on row 07: -2, above -7. No row test
        # (CEM16c rolls one and the room reads the fall), and dying from
        # now, 7 x 2.5 seconds (CEM16b keeps it out).
        beast = _creature(con=12, siz=16)
        beast.move_to(self.room1, quiet=True, move_hooks=False)
        _, first = self._row(7, 8, LOSE, beast=beast)
        self.at(10)
        _, second = self._row(7, 8, LOSE, beast=beast)
        lines = [line[1] for line in self.lines()]
        self.at(20)
        calls = self.alarm.call_count
        cw._state_due(beast, "out", NOW + 480)   # the old alarm
        self.assertEqual(
            (first["state"], second["hit_points"], second["row"],
             second["row_test"], second["test"], second["state"],
             cw.state_of(beast), lines, self.alarm.call_count - calls,
             bool(beast.pk)),
            ("out", -2, 7, None, None, "dying",
             {"kind": "dying", "due": NOW + 10 + 17.5},
             ["testbeast drops where it stands, its sides still rising and falling."],
             0, True),
        )


# --- CE-T5: healing at the read --------------------------------------------

# Game seconds. Core p. 86: Resilience 11-30 heals a Hit Point per 48 hours
# (the rabbit's 22), 31-50 per 36 (the CON 12, SIZ 16 beast's 46), 91+ per 12.
H = 3600


@override_settings(TIME_FACTOR=4)
class TestHealing(_AtZero):
    """
    CE11: one point per interval of game time, counted at the read from
    `heal_anchor`, which only the door writes -- to now on a blow that finds
    no damage left or no anchor, else on by whole intervals -- and on by the
    time a creature lies senseless when the door knocks it out. Nothing heals
    under a state. CE10: `is_hurt`. TIME_FACTOR is held at 4: the knock-out's
    real minutes become game seconds by it.
    """

    def _hit(self, creature, amount, seconds):
        self.game_at(seconds)
        return creature.apply_health_damage(amount, location="chest",
                                            source=self.char1)

    def _read(self, creature, *seconds):
        found = []
        for at in seconds:
            self.game_at(at)
            found.append(cw.damage_of(creature))
        return found

    def _beast(self, **extra):
        beast = _creature(con=12, siz=16, **extra)
        beast.move_to(self.room1, quiet=True, move_hooks=False)
        return beast

    def test_three_points_read_three_just_under_48_hours_and_two_at_it(self):
        # The red: without healing, 3 at 48 hours. Whole intervals only.
        rabbit = _rabbit_in(self.room1)
        self._hit(rabbit, 3, 0)
        self.assertEqual(self._read(rabbit, 48 * H - 1, 48 * H), [3, 2])

    def test_it_never_reads_below_nothing(self):
        # Without the floor, 144 hours would read 0 and 1000 hours -17, and
        # the Hit Points would pass the maximum.
        rabbit = _rabbit_in(self.room1)
        self._hit(rabbit, 3, 0)
        found = self._read(rabbit, 144 * H, 1000 * H)
        self.assertEqual((found, cw.hit_points_of(rabbit)), ([0, 0], 4))

    def test_the_read_writes_nothing(self):
        # CEM18: a read that writes the healed figure (or the anchor) would
        # change the rows here.
        rabbit = _rabbit_in(self.room1)
        self._hit(rabbit, 3, 0)
        before = {a.key: a.value for a in rabbit.attributes.all()}
        self.game_at(100 * H)
        cw.damage_of(rabbit)
        cw.hit_points_of(rabbit)
        cw.is_hurt(rabbit)
        after = {a.key: a.value for a in rabbit.attributes.all()}
        self.assertEqual(after, before)

    def test_a_blow_lands_on_the_healed_figure_and_keeps_the_part_interval(self):
        # 3 at 0; at 50 hours one point has healed, so a blow of 1 makes 3,
        # and the anchor moves to 48, not 50 (CEM17): the next point at 96.
        # The anchor of 0 is an anchor, not a missing one.
        rabbit = _rabbit_in(self.room1)
        self._hit(rabbit, 3, 0)
        answer = self._hit(rabbit, 1, 50 * H)
        self.assertEqual(
            (answer["hit_points"], rabbit.attributes.get("heal_anchor"),
             self._read(rabbit, 96 * H - 1, 96 * H)),
            (1, 48 * H, [3, 2]),
        )

    def test_death_is_counted_on_the_healed_figure(self):
        # CEM18b: 3 at 0, healed to 1 at 96 hours; 3 more is 4, 0 Hit Points
        # and a test (won). On the stored 3 it would be 6, -2, and dead.
        rabbit = _rabbit_in(self.room1)
        self._hit(rabbit, 3, 0)
        answer = self._hit(rabbit, 3, 96 * H)
        self.assertEqual(
            (answer["dies"], answer["hit_points"], answer["state"], bool(rabbit.pk)),
            (False, 0, "standing", True),
        )

    def test_a_blow_after_full_healing_anchors_at_now(self):
        # CEM17b: 1 at 0, whole again by 48 hours; a blow of 1 at 200 hours
        # is a new wound, healed at 248 and not at once.
        rabbit = _rabbit_in(self.room1)
        self._hit(rabbit, 1, 0)
        self._hit(rabbit, 1, 200 * H)
        self.assertEqual(
            (rabbit.attributes.get("heal_anchor"),
             self._read(rabbit, 248 * H - 1, 248 * H)),
            (200 * H, [1, 0]),
        )

    def test_damage_without_an_anchor_does_not_heal_until_the_door_anchors_it(self):
        # A creature hurt before CE-T5 (STOPP 0, choice 2). CEM17c reads a
        # missing anchor as 0, the epoch, and heals it whole at 1000 hours.
        rabbit = _rabbit_in(self.room1)
        rabbit.attributes.add("general_damage", 1)
        before = self._read(rabbit, 1000 * H)
        answer = self._hit(rabbit, 1, 1000 * H)
        self.assertEqual(
            (before, answer["hit_points"], rabbit.attributes.get("heal_anchor"),
             self._read(rabbit, 1048 * H - 1, 1048 * H)),
            ([1], 2, 1000 * H, [2, 1]),
        )

    def test_a_stored_resilience_sets_the_interval(self):
        # Resilience 95 is the 91+ row, 12 hours; the formula's 46 would be
        # 36 and read 3 at 12.
        beast = self._beast(resilience=95)
        self._hit(beast, 3, 0)
        self.assertEqual(self._read(beast, 12 * H - 1, 12 * H), [3, 2])

    def test_without_con_the_readers_raise_nothing_and_it_is_not_hurt(self):
        # CE13, choice 4: no interval without Resilience, so the stored
        # figure; `interval_for(None)` would raise. `is_hurt` is False, since
        # the door never hurts such a creature.
        old = _creature(siz=4)
        old.attributes.add("general_damage", 2)
        self.game_at(1000 * H)
        self.assertEqual((cw.damage_of(old), cw.is_hurt(old)), (2, False))

    def test_standing_at_zero_does_not_heal(self):
        # CEM19: 4 at 0 is 0 Hit Points, the test won; at 100 hours two
        # points would have healed.
        rabbit = _rabbit_in(self.room1)
        answer = self._hit(rabbit, 4, 0)
        self.assertEqual((answer["state"], self._read(rabbit, 100 * H)),
                         ("standing", [4]))

    def _knocked_out(self):
        # 1 at 0; at 35 hours 55 minutes 8 more, row 07 lost: out for eight
        # minutes with 5 Hit Points left, 480 real seconds, 1920 game seconds.
        beast = self._beast()
        self._hit(beast, 1, 0)
        self.die.return_value = 7
        self.roll.return_value = LOSE
        answer = self._hit(beast, 8, 35 * H + 55 * 60)
        self.roll.return_value = WIN
        return beast, answer

    def test_senseless_it_does_not_heal(self):
        beast, answer = self._knocked_out()
        self.assertEqual(
            (answer["state"], answer["hit_points"], self._read(beast, 100 * H)),
            ("out", 5, [9]),
        )

    def test_the_time_senseless_is_not_counted_once_it_wakes(self):
        # The anchor moves on by the 1920 game seconds senseless. CEM19b
        # (no move) and CEM19c (480, the real seconds) both read 8 at
        # 36 hours 8 minutes.
        beast, _ = self._knocked_out()
        self.at(480)
        cw._state_due(beast, "out", NOW + 480)
        self.assertEqual(
            (cw.state_of(beast), beast.attributes.get("heal_anchor"),
             self._read(beast, 36 * H + 8 * 60, 36 * H + 32 * 60)),
            (None, 1920, [9, 8]),
        )

    def test_is_hurt(self):
        rabbit = _rabbit_in(self.room1)
        whole = cw.is_hurt(rabbit)
        self._hit(rabbit, 1, 0)
        hurt = cw.is_hurt(rabbit)
        self.game_at(48 * H)
        self.assertEqual(
            (whole, hurt, cw.is_hurt(rabbit), rabbit.attributes.get("general_damage")),
            (False, True, False, 1),
        )
