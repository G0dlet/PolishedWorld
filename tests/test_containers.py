"""
Tests for typeclasses/containers.py (Weight and Encumbrance, Task W4.1).

Each class presses one bug:

    TestCapacityInEnc     `>=` for `>` (7/10 plus 3 must get in); the contrib's
                          item count kept through `super()` (a sack holding
                          nineteen weightless things refuses a twentieth that
                          still fits); the naive formula `carried_enc +
                          item_enc`, which lets the twentieth item at `enc` 0
                          into a full sack (WD4, W2.1 Q1)
    TestNoNesting         a container put inside another; a check keyed on the
                          project's `Container`, which lets the contrib's own
                          `ContribContainer` in (Q3)
    TestCarrierSum        a container that lightens what it holds
    TestPrototypes        a prototype left on `Object`; a capacity left at the
                          contrib's 20; a `get_from` lock lost because
                          `at_object_creation` stopped reaching the contrib

THE FIXTURE
-----------
A sack is created in `room1` with `capacity` 10. Its load is created in place
(nothing under test moves it); the item offered is created in the room, as
`CmdPut` would find it on the putter. The hook is called directly, the way
the contrib's `CmdPut` calls it (`containers.py:279`); `put` itself is
installed and tested through the command in W4.2. Every refusal asserts the
putter's one message, and every acceptance that no message was sent.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_containers
"""

from unittest import mock

from evennia import create_object
from evennia.prototypes.prototypes import search_prototype
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaTest

from typeclasses.containers import Container
from world.encumbrance import carried_enc

CHARACTER = "typeclasses.characters.Character"
CONTAINER = "typeclasses.containers.Container"
CONTRIB_CONTAINER = "evennia.contrib.game_systems.containers.containers.ContribContainer"
OBJ = "typeclasses.objects.Object"
SACK_CAPACITY = 10
FULL = "The large sack is full."
NESTED = "You cannot put a container inside another."


def _make(location, key="thing", enc=None, typeclass=OBJ):
    obj = create_object(typeclass, key=key, location=location)
    if enc is not None:
        obj.db.enc = enc
    return obj


class _SackFixture:
    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.sack = _make(self.room1, key="large sack", enc=1, typeclass=CONTAINER)
        self.sack.capacity = SACK_CAPACITY

    def offer(self, container, item):
        """Call the hook as CmdPut does; return (answer, messages to char1)."""
        with mock.patch.object(self.char1, "msg") as msg:
            answer = container.at_pre_put_in(self.char1, item)
        return answer, [call.args[0] for call in msg.call_args_list]


class TestCapacityInEnc(_SackFixture, EvenniaTest):
    """`capacity` is ENC: 7 + 3 fits a 10, 8 + 3 does not."""

    def test_seven_plus_three_fits(self):
        _make(self.sack, key="load", enc=7)
        item = _make(self.room1, enc=3)
        self.assertEqual(self.offer(self.sack, item), (True, []))

    def test_eight_plus_three_is_refused(self):
        _make(self.sack, key="load", enc=8)
        item = _make(self.room1, enc=3)
        self.assertEqual(self.offer(self.sack, item), (False, [FULL]))

    def test_the_twentieth_weightless_item_tips_a_full_sack(self):
        _make(self.sack, key="load", enc=SACK_CAPACITY)
        for n in range(18):
            _make(self.sack, key=f"bead{n}", enc=0)
        # 18 beads + 1 offered = 19 at enc 0: still 10 ENC, and it fits.
        # Receipt for the contrib's item count too: the sack holds 19 things.
        nineteenth = _make(self.room1, key="bead18", enc=0)
        self.assertEqual(self.offer(self.sack, nineteenth), (True, []))
        nineteenth.move_to(self.sack, quiet=True)
        self.assertEqual(carried_enc(self.sack), SACK_CAPACITY)
        # The twentieth makes 20 at enc 0 = 1 ENC: 11 > 10.
        twentieth = _make(self.room1, key="bead19", enc=0)
        self.assertEqual(self.offer(self.sack, twentieth), (False, [FULL]))

    def test_an_items_own_contents_count(self):
        _make(self.sack, key="load", enc=8)
        pouch = _make(self.room1, key="pouch", enc=0)
        _make(pouch, key="stone", enc=3)
        self.assertEqual(self.offer(self.sack, pouch), (False, [FULL]))


class TestNoNesting(_SackFixture, EvenniaTest):
    """Nothing nests: a container is refused by an empty container."""

    def setUp(self):
        super().setUp()
        self.backpack = _make(self.room1, key="backpack", enc=1, typeclass=CONTAINER)
        self.backpack.capacity = 20

    def test_a_sack_into_a_backpack_is_refused(self):
        self.assertEqual(self.offer(self.backpack, self.sack), (False, [NESTED]))

    def test_a_contrib_container_is_refused_too(self):
        crate = _make(self.room1, key="crate", enc=1, typeclass=CONTRIB_CONTAINER)
        self.assertEqual(self.offer(self.backpack, crate), (False, [NESTED]))

    def test_the_same_weight_that_is_not_a_container_gets_in(self):
        # Receipt: the empty backpack refuses for nesting, not for weight.
        block = _make(self.room1, key="block", enc=1)
        self.assertEqual(self.offer(self.backpack, block), (True, []))


class TestCarrierSum(_SackFixture, EvenniaTest):
    """A container does not lighten its contents (WD5)."""

    def test_a_carried_sack_counts_itself_and_what_it_holds(self):
        _make(self.sack, key="load", enc=4)
        self.sack.move_to(self.char1, quiet=True)
        self.assertEqual(carried_enc(self.char1), 5)


class TestPrototypes(EvenniaTest):
    """The three craftable containers spawn as Container, with AoL capacities."""

    character_typeclass = CHARACTER
    EXPECTED = {"sack": 10, "backpack": 20, "saddlebag": 15}   # AoL pp.28-30

    def test_each_spawns_as_a_container_with_its_capacity(self):
        prototypes = {p["prototype_key"]: p for p in search_prototype(no_db=True)}
        for key, capacity in self.EXPECTED.items():
            with self.subTest(prototype=key):
                obj = spawn(prototypes[key])[0]
                self.assertIs(type(obj), Container)
                self.assertEqual(obj.capacity, capacity)
                self.assertTrue(obj.access(self.char1, "get_from"))
