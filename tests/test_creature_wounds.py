"""
Tests for world.creature_wounds -- a creature's numbers (Creatures
decomposition, slice CE, task CE-T1; Combat Design CR1, CE2-CE4, CE7, CE13).

Every expected number is the book's -- core p. 146 and *Monsters of Legend*
pp. 12 and 103-122 -- typed here and never computed from the code under
test.
"""

from evennia.prototypes.spawner import spawn
from evennia.utils.create import create_object
from evennia.utils.test_resources import EvenniaTest, EvenniaTestCase
from evennia.utils.utils import class_from_module

from typeclasses.creatures import Creature
from world import creature_wounds as cw
from world import prototypes as world_prototypes


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
