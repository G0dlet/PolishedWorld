"""
Tests for world/encumbrance.py and the Character properties over it
(Weight and Encumbrance, Tasks W1.1 and W1.2).

Each class presses one bug:

    TestItemEnc           a missing field that raises; "2" summed as text; a
                          negative enc that makes its carrier lighter; a
                          malformed value that crashes `get` in play; a
                          warning on the *missing* case (it must stay silent)
    TestCarriedEnc        a dropped recursion; the twenty-to-one rule off by
                          one; zero-ENC items counted per container instead of
                          over the whole tree (WD4); worn clothing special-cased
    TestWalkSkips         a character or an exit summed as cargo -- and the
                          `has_account` rule, which misses every character
                          without a session (char2 in the fixture)
    TestDepthGuard        an unbounded walk; a guard that fires too early
    TestEncLimit          a constant 20 instead of a live STR+SIZ read
    TestEncumbranceState  `>=` for `>` at either boundary; a ceiling that is
                          not twice the limit

  W1.2 -- the properties on Character:

    TestPropertiesAgree   a property that drifts from its module function in
                          one band only, or returns a float
    TestStateIsRead       a stored or hard-coded state: the spy feeds two
                          different loads and expects two different bands
    TestPatchTarget       a name import (`from world.encumbrance import ...`)
                          of any one function, which a module patch can no
                          longer reach (Testing Reference §11f)
    TestReadOnly          a setter, or an assignment that lands in `db`

THE FIXTURE
-----------
Every test loads `char1` (or a holder) with objects created in place, `enc`
set by hand. Weights are chosen so the alternative bug gives a different
number: a sack at enc 1 holding enc 3 is 4 with the recursion and 1 without.
"""

from unittest import mock

from evennia import create_object
from evennia.utils.test_resources import EvenniaTest

from world.encumbrance import (
    CEILING,
    FREE,
    OVERLOADED,
    carried_enc,
    enc_limit,
    encumbrance_state,
    item_enc,
)

OBJ = "typeclasses.objects.Object"
WARN = "world.encumbrance.logger.log_warn"


def _make(location, key="thing", enc=None):
    obj = create_object(OBJ, key=key, location=location)
    if enc is not None:
        obj.db.enc = enc
    return obj


class TestItemEnc(EvenniaTest):
    def test_missing_enc_is_zero_and_silent(self):
        obj = _make(self.char1)
        with mock.patch(WARN) as warn:
            self.assertEqual(item_enc(obj), 0)
        warn.assert_not_called()

    def test_int_enc_is_read(self):
        self.assertEqual(item_enc(_make(self.char1, enc=2)), 2)

    def test_string_enc_is_coerced(self):
        value = item_enc(_make(self.char1, enc="2"))
        self.assertEqual(value, 2, f"got {value!r} ({type(value).__name__})")
        self.assertIs(type(value), int)

    def test_malformed_string_reads_zero_and_warns(self):
        with mock.patch(WARN) as warn:
            self.assertEqual(item_enc(_make(self.char1, enc="heavy")), 0)
        warn.assert_called_once()

    def test_explicit_none_reads_zero_and_warns(self):
        obj = _make(self.char1)
        obj.attributes.add("enc", None)
        with mock.patch(WARN) as warn:
            self.assertEqual(item_enc(obj), 0)
        warn.assert_called_once()

    def test_negative_reads_zero_and_warns(self):
        with mock.patch(WARN) as warn:
            self.assertEqual(item_enc(_make(self.char1, enc=-20)), 0)
        warn.assert_called_once()


class TestCarriedEnc(EvenniaTest):
    def test_sum(self):
        _make(self.char1, enc=2)
        _make(self.char1, enc=1)
        self.assertEqual(carried_enc(self.char1), 3)

    def test_twenty_at_zero_count_one(self):
        for i in range(20):
            _make(self.char1, key=f"pebble{i}", enc=0)
        self.assertEqual(carried_enc(self.char1), 1)

    def test_nineteen_at_zero_count_nothing(self):
        for i in range(19):
            _make(self.char1, key=f"pebble{i}", enc=0)
        self.assertEqual(carried_enc(self.char1), 0)

    def test_zero_items_count_over_the_whole_tree(self):
        sack = _make(self.char1, key="sack", enc=1)
        for i in range(10):
            _make(self.char1, key=f"loose{i}", enc=0)
            _make(sack, key=f"bagged{i}", enc=0)
        # 1 (the sack) + 20 zero-ENC items across two levels = 1 more.
        self.assertEqual(carried_enc(self.char1), 2)

    def test_container_contents_count_for_the_carrier(self):
        sack = _make(self.char1, key="sack", enc=1)
        _make(sack, key="logs", enc=3)
        self.assertEqual(carried_enc(self.char1), 4)

    def test_container_alone_reads_its_contents(self):
        sack = _make(self.char1, key="sack", enc=1)
        _make(sack, key="logs", enc=3)
        self.assertEqual(carried_enc(sack), 3)

    def test_worn_clothing_counts(self):
        cloak = create_object(
            "evennia.contrib.game_systems.clothing.clothing.ContribClothing",
            key="cloak",
            location=self.char1,
        )
        cloak.db.enc = 1
        cloak.wear(self.char1, True, quiet=True)
        self.assertTrue(cloak.db.worn)  # receipt: wear() actually ran
        self.assertEqual(carried_enc(self.char1), 1)


class TestWalkSkips(EvenniaTest):
    def test_characters_and_exits_are_not_cargo(self):
        # room1 holds char1, char2, obj1, obj2 and the exit (EvenniaTest).
        # char1 is puppeted by the fixture's session, char2 is not: the
        # anvils prove both are skipped, whatever has_account says.
        self.obj1.db.enc = 2
        self.exit.db.enc = 7
        _make(self.char1, key="anvil", enc=5)
        _make(self.char2, key="anvil", enc=6)
        self.assertEqual(carried_enc(self.room1), 2)

    def test_fixture_has_one_puppeted_and_one_unpuppeted_character(self):
        # Receipt for the test above: without it, "puppeted or not" is a
        # claim about a fixture nobody looked at.
        self.assertTrue(self.char1.has_account)
        self.assertFalse(self.char2.has_account)

    def test_character_inside_a_holder_is_skipped(self):
        crate = _make(self.room1, key="crate", enc=1)
        self.char2.location = crate
        _make(self.char2, key="anvil", enc=5)
        self.assertEqual(carried_enc(crate), 0)


class TestDepthGuard(EvenniaTest):
    def _chain(self, length):
        holder = self.char1
        for i in range(length):
            holder = _make(holder, key=f"box{i}", enc=1)

    def test_four_deep_counts_four_silently(self):
        self._chain(4)
        with mock.patch(WARN) as warn:
            self.assertEqual(carried_enc(self.char1), 4)
        warn.assert_not_called()

    def test_five_deep_counts_four_and_warns(self):
        self._chain(5)
        with mock.patch(WARN) as warn:
            self.assertEqual(carried_enc(self.char1), 4)
        warn.assert_called_once()


class TestEncLimit(EvenniaTest):
    def test_default_character_is_twenty(self):
        self.assertEqual(enc_limit(self.char1), 20)

    def test_limit_reads_str_and_siz_live(self):
        self.char1.stats.str.base = 18
        self.char1.stats.siz.base = 18
        self.assertEqual(enc_limit(self.char1), 36)
        self.char1.stats.str.base = 6
        self.char1.stats.siz.base = 6
        self.assertEqual(enc_limit(self.char1), 12)


class TestEncumbranceState(EvenniaTest):
    def _load(self, total):
        _make(self.char1, key="load", enc=total)

    def test_constants_are_the_documented_strings(self):
        self.assertEqual((FREE, OVERLOADED, CEILING), ("free", "overloaded", "ceiling"))

    def test_empty_is_free(self):
        self.assertEqual(encumbrance_state(self.char1), FREE)

    def test_at_the_limit_is_free(self):
        self._load(20)
        self.assertEqual(encumbrance_state(self.char1), FREE)

    def test_one_over_the_limit_is_overloaded(self):
        self._load(21)
        self.assertEqual(encumbrance_state(self.char1), OVERLOADED)

    def test_at_twice_the_limit_is_overloaded(self):
        self._load(40)
        self.assertEqual(encumbrance_state(self.char1), OVERLOADED)

    def test_one_over_twice_the_limit_is_ceiling(self):
        self._load(41)
        self.assertEqual(encumbrance_state(self.char1), CEILING)

    def test_boundaries_follow_the_live_limit(self):
        self.char1.stats.str.base = 6
        self.char1.stats.siz.base = 6
        self._load(24)
        self.assertEqual(encumbrance_state(self.char1), OVERLOADED)
        _make(self.char1, key="straw", enc=1)
        self.assertEqual(encumbrance_state(self.char1), CEILING)


# --- W1.2: Character properties -------------------------------------------

PATCH = "world.encumbrance.{}"


class TestPropertiesAgree(EvenniaTest):
    def _triple(self):
        c = self.char1
        return (c.carried_enc, c.enc_limit, c.encumbrance_state)

    def _module(self):
        c = self.char1
        return (carried_enc(c), enc_limit(c), encumbrance_state(c))

    def test_properties_match_the_module_in_every_band(self):
        self.assertEqual(self._triple(), (0, 20, FREE))
        _make(self.char1, key="load", enc=30)
        self.assertEqual(self._triple(), (30, 20, OVERLOADED))
        _make(self.char1, key="more", enc=20)
        self.assertEqual(self._triple(), (50, 20, CEILING))
        self.assertEqual(self._triple(), self._module())

    def test_properties_follow_a_new_limit(self):
        _make(self.char1, key="load", enc=50)
        self.char1.stats.str.base = 18
        self.char1.stats.siz.base = 18
        self.assertEqual(self._triple(), (50, 36, OVERLOADED))
        self.assertEqual(self._triple(), self._module())

    def test_numbers_are_ints(self):
        _make(self.char1, key="load", enc=3)
        self.assertIsInstance(self.char1.carried_enc, int)
        self.assertIsInstance(self.char1.enc_limit, int)


class TestStateIsRead(EvenniaTest):
    def test_state_reads_carried_enc_on_every_call(self):
        # premises: an empty inventory, limit 20, so the real band is FREE
        self.assertEqual(self.char1.carried_enc, 0)
        self.assertEqual(self.char1.enc_limit, 20)
        self.assertEqual(self.char1.encumbrance_state, FREE)
        with mock.patch(PATCH.format("carried_enc"), return_value=41) as spy:
            self.assertEqual(self.char1.encumbrance_state, CEILING)
            self.assertTrue(spy.called)
        with mock.patch(PATCH.format("carried_enc"), return_value=21) as spy:
            self.assertEqual(self.char1.encumbrance_state, OVERLOADED)
            self.assertTrue(spy.called)


class TestPatchTarget(EvenniaTest):
    def test_each_property_goes_through_the_module(self):
        c = self.char1
        # premise: the sentinels differ from the real answers
        self.assertEqual((c.carried_enc, c.enc_limit, c.encumbrance_state), (0, 20, FREE))
        with mock.patch(PATCH.format("carried_enc"), return_value=7), mock.patch(
            PATCH.format("enc_limit"), return_value=13
        ), mock.patch(PATCH.format("encumbrance_state"), return_value="sentinel"):
            self.assertEqual(
                (c.carried_enc, c.enc_limit, c.encumbrance_state), (7, 13, "sentinel")
            )


class TestReadOnly(EvenniaTest):
    def test_assignment_raises_and_stores_nothing(self):
        for name in ("carried_enc", "enc_limit", "encumbrance_state"):
            with self.subTest(name=name):
                with self.assertRaises(AttributeError):
                    setattr(self.char1, name, 5)
                self.assertFalse(self.char1.attributes.has(name))
        self.assertEqual(self.char1.carried_enc, 0)
