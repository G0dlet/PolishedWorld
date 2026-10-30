"""
Tests for typeclasses/containers.py and `put` (Weight and Encumbrance, Tasks
W4.1 and W4.2).

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

W4.2, through the commands (`self.call`):

    TestPutRoundTrip      `put` or `get ... from` that does not move the item,
                          or moves it in a way that changes the carrier's sum
    TestPutOneLine        the contrib's "You can't put that there." after a
                          refusal that already said why (filter or flag gone);
                          `put` into a corpse or a character, which the
                          contrib allows on the `get_from` lock -- the owner's
                          corpse during the grace, anything for a superuser --
                          when ObjectParent has no `at_pre_put_in` (Q3)
    TestPutStaleFlag      a flag left over from earlier that silences the
                          contrib's line after a refusal nobody explained (the
                          clear before `func`, Q2)
    TestGetFromAtCeiling  a ceiling check that charges an item taken out of a
                          carried sack as new weight, or lets one from a sack
                          on the floor through (W2.1, via `get ... from`)
    TestPutInstalled      the cmdset's `put` missing, or the contrib's own

THE FIXTURE
-----------
A sack is created in `room1` with `capacity` 10. Its load is created in place
(nothing under test moves it); the item offered is created in the room, as
`CmdPut` would find it on the putter. The hook is called directly, the way
the contrib's `CmdPut` calls it (`containers.py:279`). The W4.2 classes run
`put` and `get` as commands; each refusal there asserts the caller's whole
output, line for line, and that the item has not moved.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_containers
"""

from unittest import mock

from evennia import create_object
from evennia.prototypes.prototypes import search_prototype
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.inventory_commands import CONTRIB_REFUSAL, PUT_REFUSAL, CmdGet, CmdPut
from typeclasses.containers import Container
from world.encumbrance import carried_enc

CHARACTER = "typeclasses.characters.Character"
CONTAINER = "typeclasses.containers.Container"
CONTRIB_CONTAINER = "evennia.contrib.game_systems.containers.containers.ContribContainer"
OBJ = "typeclasses.objects.Object"
SACK_CAPACITY = 10
FULL = "The large sack is full."
NESTED = "You cannot put a container inside another."
LOCKED = "You can't put things in that."   # containers.py:270, ObjectParent
CEILING = "You cannot carry any more."
PLAYER_CORPSE = "typeclasses.corpse.PlayerCorpse"


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


# --- W4.2 -- put and get through the commands ---------------------------------


class _PutFixture(_SackFixture):
    """The W4.1 sack, plus a helper that returns the caller's output as lines."""

    def lines(self, cmd, args):
        return self.call(cmd, args).splitlines()


class TestPutRoundTrip(_PutFixture, EvenniaCommandTest):
    """`put` into a carried sack and `get ... from` it move the item and nothing else."""

    def test_put_in_and_get_back_out(self):
        self.sack.move_to(self.char1, quiet=True)
        stone = _make(self.char1, key="stone", enc=3)
        before = carried_enc(self.char1)
        self.call(CmdPut(), "stone in large sack")
        self.assertEqual(stone.location, self.sack)
        self.assertEqual(carried_enc(self.char1), before)
        self.call(CmdGet(), "stone from large sack")
        self.assertEqual(stone.location, self.char1)
        self.assertEqual(carried_enc(self.char1), before)


class TestPutOneLine(_PutFixture, EvenniaCommandTest):
    """Every refusal through `put` is one line, and the item stays put."""

    def assertRefused(self, args, line, item):
        self.assertEqual(self.lines(CmdPut(), args), [line])
        self.assertEqual(item.location, self.char1)
        self.assertFalse(self.char1.ndb._put_refused)

    def test_a_full_carried_sack(self):
        self.sack.move_to(self.char1, quiet=True)
        _make(self.sack, key="load", enc=8)
        stone = _make(self.char1, key="stone", enc=3)
        self.assertRefused("stone in large sack", FULL, stone)

    def test_a_sack_into_a_backpack(self):
        backpack = _make(self.room1, key="backpack", enc=1, typeclass=CONTAINER)
        backpack.capacity = 20
        self.sack.move_to(self.char1, quiet=True)
        self.assertRefused("large sack in backpack", NESTED, self.sack)

    def test_your_own_corpse_during_the_grace(self):
        corpse = create_object(PLAYER_CORPSE, key="corpse", location=self.room1)
        corpse.db.owner = self.char1.id
        # Receipts: the lock lets the owner through, so the line is the hook's.
        self.assertTrue(corpse.grace_active)
        self.assertTrue(corpse.access(self.char1, "get_from"))
        stone = _make(self.char1, key="stone", enc=1)
        self.assertRefused("stone in corpse", LOCKED, stone)

    def test_a_superuser_into_a_character(self):
        self.account.is_superuser = True
        self.account.save()
        # The bypass is cached per object; puppeting refreshes it
        # (accounts.py:552), so the test does what a login would.
        self.char1.locks.cache_lock_bypass(self.char1)
        # Receipt: a superuser passes the get_from lock Char2 does not have.
        self.assertTrue(self.char2.access(self.char1, "get_from"))
        stone = _make(self.char1, key="stone", enc=1)
        self.assertRefused("stone in Char2", LOCKED, stone)


class TestPutStaleFlag(_PutFixture, EvenniaCommandTest):
    """A flag set before the command does not silence a refusal nobody explained."""

    def test_the_contrib_container_keeps_both_of_its_lines(self):
        # The contrib's own class says why itself (containers.py:101) and sets
        # no flag, so the contrib's line after it must survive a stale flag.
        crate = _make(self.room1, key="crate", enc=1, typeclass=CONTRIB_CONTAINER)
        crate.capacity = 0
        stone = _make(self.char1, key="stone", enc=1)
        self.char1.ndb._put_refused = True
        self.assertEqual(
            self.lines(CmdPut(), "stone in crate"),
            ["You can't fit anything else in a crate.", PUT_REFUSAL],
        )
        self.assertEqual(stone.location, self.char1)


class TestGetFromAtCeiling(_PutFixture, EvenniaCommandTest):
    """At the ceiling (40 at limit 20), a floor sack is new weight; a carried one is not."""

    def test_from_a_sack_on_the_floor_is_refused(self):
        _make(self.char1, key="load", enc=40)
        stone = _make(self.sack, key="stone", enc=1)
        self.assertEqual(self.lines(CmdGet(), "stone from large sack"), [CEILING])
        self.assertEqual(stone.location, self.sack)

    def test_from_a_carried_sack_is_let_through(self):
        _make(self.char1, key="load", enc=38)
        self.sack.move_to(self.char1, quiet=True)
        stone = _make(self.sack, key="stone", enc=1)
        self.assertEqual(carried_enc(self.char1), 40)
        out = self.call(CmdGet(), "stone from large sack")
        self.assertNotIn(CEILING, out)
        self.assertNotIn(CONTRIB_REFUSAL, out)
        self.assertEqual(stone.location, self.char1)
        self.assertEqual(carried_enc(self.char1), 40)


class TestPutInstalled(EvenniaTest):
    """The character cmdset's `put` is the project's, not the contrib's."""

    character_typeclass = CHARACTER

    def test_the_cmdset_uses_the_project_put(self):
        from commands.default_cmdsets import CharacterCmdSet

        commands = {cmd.key: cmd for cmd in CharacterCmdSet().commands}
        self.assertIsInstance(commands.get("put"), CmdPut)
