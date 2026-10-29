"""
Tests for world/encumbrance.py and the Character properties over it
(Weight and Encumbrance, Tasks W1.1, W1.2, W2.1 and W2.2).

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

  W2.1 -- the ceiling:

    TestEncAfterReceiving the hook's old formula (`carried_enc + item_enc`),
                          which misses the twentieth item at `enc` 0 (the rule
                          over the merged count, WD4) and a holder's contents;
                          an item already carried counted twice; a character
                          or an exit counted as cargo
    TestCeilingHook       `>=` for `>` (38/20 must get in); a lost giver
                          message; a `try/except` that swallows a raising
                          reader and lets the item in; `super()` ignored.
                          Every refusal also asserts `location`: `.call()`
                          runs no locks, and the message alone is not the move

  W2.2 -- what the player sees:

    TestEncWithout        the hooks' tempting formula (`carried_enc -
                          item_enc`), which misses the twentieth item at
                          `enc` 0; a sack leaving without its contents; a
                          move inside the carried tree read as a change;
                          an item created in place (`elsewhere` None)
    TestCrossingMessages  a message on every move in the band (the *change*
                          condition); before and after swapped in the leave
                          hook; a crossing announced for a `put` into a
                          carried sack; OVERLOADED <-> CEILING announced.
                          Each test asserts the list of crossing messages,
                          so a second copy fails as surely as a missing one
    TestInventoryLine     a line lost on the empty-inventory early return;
                          "(overloaded)" at the limit, or missing at CEILING
    TestRefusalLine       two sentences for one ceiling refusal; a stale flag
                          that silences the contrib's line after a refusal
                          the ceiling never made; a cmdset still on the
                          contrib commands

THE FIXTURE
-----------
Every test loads `char1` (or a holder) with objects created in place, `enc`
set by hand. Weights are chosen so the alternative bug gives a different
number: a sack at enc 1 holding enc 3 is 4 with the recursion and 1 without.
From W2.2 on, an object that has to *move* is created outside the character
and brought in with `move_to`: creation in place runs `at_object_receive`
before `enc` is set (objects.py:1975), so it is not the move under test.
"""

from unittest import mock

from evennia import create_object
from evennia.commands.default.general import CmdGive
from evennia.contrib.game_systems.containers.containers import CmdContainerGet
from evennia.objects.objects import DefaultObject
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.inventory_commands import CONTRIB_REFUSAL, CmdGet, CmdInventory

from world.encumbrance import (
    CEILING,
    FREE,
    OVERLOADED,
    carried_enc,
    enc_after_receiving,
    enc_limit,
    enc_without,
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


# --- W2.1 -- the ceiling ---------------------------------------------------


class TestEncAfterReceiving(EvenniaTest):
    """The reader's answer for a move that has not happened yet."""

    def _zeros(self, location, n):
        for i in range(n):
            _make(location, key=f"pebble{i}", enc=0)

    def test_twentieth_item_at_zero_tips_the_merged_count(self):
        _make(self.char1, key="load", enc=40)
        self._zeros(self.char1, 19)
        pebble = _make(self.room1, key="last pebble", enc=0)
        self.assertEqual(carried_enc(self.char1), 40)  # premise: 19 // 20 == 0
        self.assertEqual(enc_after_receiving(self.char1, pebble), 41)

    def test_nineteenth_item_at_zero_does_not(self):
        _make(self.char1, key="load", enc=40)
        self._zeros(self.char1, 18)
        pebble = _make(self.room1, key="last pebble", enc=0)
        self.assertEqual(enc_after_receiving(self.char1, pebble), 40)

    def test_a_holder_counts_with_its_contents(self):
        sack = _make(self.room1, key="sack", enc=1)
        _make(sack, key="stone", enc=3)
        self.assertEqual(enc_after_receiving(self.char1, sack), 4)

    def test_an_item_already_carried_changes_nothing(self):
        _make(self.char1, key="load", enc=36)
        sack = _make(self.char1, key="sack", enc=1)
        stone = _make(sack, key="stone", enc=3)
        self.assertEqual(carried_enc(self.char1), 40)  # premise
        self.assertEqual(enc_after_receiving(self.char1, stone), 40)

    def test_a_character_is_never_cargo(self):
        self.char2.db.enc = 5
        _make(self.char2, key="anvil", enc=5)
        self.assertEqual(enc_after_receiving(self.char1, self.char2), 0)

    def test_nothing_moves(self):
        sack = _make(self.room1, key="sack", enc=1)
        enc_after_receiving(self.char1, sack)
        self.assertEqual(sack.location, self.room1)
        self.assertEqual(carried_enc(self.char1), 0)


class TestCeilingHook(EvenniaCommandTest):
    """`at_pre_object_receive` on the paths a player uses: get, give, move_to."""

    REFUSED = "You cannot carry any more."

    def _load(self, total):
        _make(self.char1, key="load", enc=total)

    def test_get_above_the_ceiling_is_refused(self):
        self._load(39)
        anvil = _make(self.room1, key="anvil", enc=2)
        out = self.call(CmdContainerGet(), "anvil")
        self.assertIn(self.REFUSED, out)
        self.assertEqual(anvil.location, self.room1)
        self.assertEqual(carried_enc(self.char1), 39)

    def test_get_up_to_the_ceiling_is_let_in(self):
        self._load(38)
        anvil = _make(self.room1, key="anvil", enc=2)
        out = self.call(CmdContainerGet(), "anvil")
        self.assertNotIn(self.REFUSED, out)
        self.assertEqual(anvil.location, self.char1)
        self.assertEqual(carried_enc(self.char1), 40)

    def test_give_across_the_ceiling_stays_with_the_giver_and_tells_both(self):
        self._load(39)
        anvil = _make(self.char2, key="anvil", enc=2)
        with mock.patch.object(self.char1, "msg") as receiver_msg:
            out = self.call(CmdGive(), "anvil = Char", caller=self.char2)
        self.assertEqual(anvil.location, self.char2)
        receiver_msg.assert_any_call(self.REFUSED)
        self.assertIn(
            f"{self.char1.get_display_name(self.char2)} cannot carry any more.", out
        )

    def test_the_twentieth_item_at_zero_is_refused_at_the_ceiling(self):
        self._load(40)
        for i in range(19):
            _make(self.char1, key=f"pebble{i}", enc=0)
        pebble = _make(self.room1, key="last pebble", enc=0)
        self.assertFalse(pebble.move_to(self.char1, quiet=True))
        self.assertEqual(pebble.location, self.room1)

    def test_a_sack_is_weighed_with_its_contents(self):
        self._load(37)
        sack = _make(self.room1, key="sack", enc=1)
        _make(sack, key="stone", enc=3)
        self.assertFalse(sack.move_to(self.char1, quiet=True))
        self.assertEqual(sack.location, self.room1)

    def test_moving_an_item_out_of_a_carried_sack_at_the_ceiling(self):
        self._load(36)
        sack = _make(self.char1, key="sack", enc=1)
        stone = _make(sack, key="stone", enc=3)
        self.assertTrue(stone.move_to(self.char1, quiet=True))
        self.assertEqual(stone.location, self.char1)

    def test_a_raising_reader_raises_and_move_to_refuses(self):
        anvil = _make(self.room1, key="anvil", enc=2)
        with mock.patch(
            "world.encumbrance.enc_limit", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(RuntimeError):
                self.char1.at_pre_object_receive(anvil, self.room1)
            with mock.patch("evennia.objects.objects.logger.log_trace") as trace:
                self.assertFalse(anvil.move_to(self.char1, quiet=True))
            trace.assert_called()
        self.assertEqual(anvil.location, self.room1)

    def test_a_refusal_from_super_is_kept(self):
        pebble = _make(self.room1, key="pebble", enc=0)
        with mock.patch.object(
            DefaultObject, "at_pre_object_receive", return_value=False
        ), mock.patch.object(self.char1, "msg") as msg:
            self.assertFalse(self.char1.at_pre_object_receive(pebble, self.room1))
        msg.assert_not_called()


# --- W2.2 -- what the player sees ------------------------------------------

OVER = "You are overloaded."
FREE_AGAIN = "You are no longer overloaded."


def _crossings(msg):
    """The crossing messages a patched `msg` received, in order."""
    texts = [call.args[0] if call.args else call.kwargs.get("text") for call in msg.call_args_list]
    return [text for text in texts if text in (OVER, FREE_AGAIN)]


class TestEncWithout(EvenniaTest):
    """The sum as if one object of the carried tree were elsewhere."""

    def test_one_of_twenty_zeros_leaving_reruns_the_rule(self):
        _make(self.char1, key="load", enc=40)
        pebbles = [_make(self.char1, key=f"pebble{i}", enc=0) for i in range(20)]
        self.assertEqual(carried_enc(self.char1), 41)
        # 40 + 19 // 20; subtracting the leaver's own ENC would say 41
        self.assertEqual(enc_without(self.char1, pebbles[0], self.room1), 40)

    def test_a_carried_sack_leaves_with_its_contents(self):
        _make(self.char1, key="load", enc=10)
        sack = _make(self.char1, key="sack", enc=1)
        _make(sack, key="stone", enc=3)
        self.assertEqual(carried_enc(self.char1), 14)
        self.assertEqual(enc_without(self.char1, sack, self.room1), 10)

    def test_a_move_inside_the_carried_tree_changes_nothing(self):
        _make(self.char1, key="load", enc=10)
        sack = _make(self.char1, key="sack", enc=1)
        stone = _make(self.char1, key="stone", enc=2)
        pebble = _make(sack, key="pebble", enc=3)
        self.assertEqual(carried_enc(self.char1), 16)
        # put the stone into the carried sack (leave: elsewhere is the sack)
        self.assertEqual(enc_without(self.char1, stone, sack), 16)
        # the pebble came out of the carried sack (receive: elsewhere is the sack)
        self.assertEqual(enc_without(self.char1, pebble, sack), 16)
        # elsewhere is the carrier itself
        self.assertEqual(enc_without(self.char1, pebble, self.char1), 16)

    def test_a_character_changes_nothing(self):
        _make(self.char1, key="load", enc=5)
        self.assertEqual(enc_without(self.char1, self.char2, self.room1), 5)

    def test_created_in_place_counts_as_from_nowhere(self):
        _make(self.char1, key="load", enc=10)
        item = _make(self.char1, key="item", enc=2)
        self.assertEqual(enc_without(self.char1, item, None), 10)


class TestCrossingMessages(EvenniaCommandTest):
    """`at_object_receive` / `at_object_leave`: a message on the boundary only."""

    def _load(self, total, holder=None):
        _make(holder or self.char1, key="load", enc=total)

    def test_the_item_that_crosses_says_so_once(self):
        self._load(20)
        anvil = _make(self.room1, key="anvil", enc=1)
        with mock.patch.object(self.char1, "msg") as msg:
            self.assertTrue(anvil.move_to(self.char1, quiet=True))
        self.assertEqual(_crossings(msg), [OVER])
        self.assertEqual(carried_enc(self.char1), 21)

    def test_a_second_item_in_the_band_says_nothing(self):
        self._load(21)
        hammer = _make(self.room1, key="hammer", enc=1)
        with mock.patch.object(self.char1, "msg") as msg:
            self.assertTrue(hammer.move_to(self.char1, quiet=True))
        self.assertEqual(_crossings(msg), [])
        self.assertEqual(carried_enc(self.char1), 22)   # receipt: it moved

    def test_get_across_the_limit_through_the_command(self):
        self._load(20)
        _make(self.room1, key="anvil", enc=1)
        out = self.call(CmdGet(), "anvil")
        self.assertEqual(out.count(OVER), 1)
        self.assertIn("You pick up", out)

    def test_dropping_back_under_says_so_once(self):
        self._load(20)
        anvil = _make(self.room1, key="anvil", enc=1)
        anvil.move_to(self.char1, quiet=True)
        with mock.patch.object(self.char1, "msg") as msg:
            self.assertTrue(anvil.move_to(self.room1, quiet=True))
        self.assertEqual(_crossings(msg), [FREE_AGAIN])
        self.assertEqual(carried_enc(self.char1), 20)

    def test_dropping_one_of_twenty_zeros_at_21_recovers(self):
        self._load(20)
        for i in range(19):
            _make(self.char1, key=f"pebble{i}", enc=0)
        last = _make(self.room1, key="last pebble", enc=0)
        last.move_to(self.char1, quiet=True)
        self.assertEqual(carried_enc(self.char1), 21)
        with mock.patch.object(self.char1, "msg") as msg:
            self.assertTrue(last.move_to(self.room1, quiet=True))
        self.assertEqual(_crossings(msg), [FREE_AGAIN])

    def test_an_item_into_a_carried_sack_at_21_says_nothing(self):
        self._load(19)
        sack = _make(self.char1, key="sack", enc=1)
        stone = _make(self.room1, key="stone", enc=1)
        stone.move_to(self.char1, quiet=True)
        self.assertEqual(carried_enc(self.char1), 21)
        with mock.patch.object(self.char1, "msg") as msg:
            self.assertTrue(stone.move_to(sack, quiet=True))
        self.assertEqual(_crossings(msg), [])
        self.assertEqual(stone.location, sack)            # receipt: it moved
        self.assertEqual(carried_enc(self.char1), 21)

    def test_an_item_out_of_a_carried_sack_at_21_says_nothing(self):
        self._load(19)
        sack = _make(self.char1, key="sack", enc=1)
        stone = _make(sack, key="stone", enc=1)
        self.assertEqual(carried_enc(self.char1), 21)
        with mock.patch.object(self.char1, "msg") as msg:
            self.assertTrue(stone.move_to(self.char1, quiet=True))
        self.assertEqual(_crossings(msg), [])
        self.assertEqual(stone.location, self.char1)      # receipt: it moved

    def test_ceiling_to_overloaded_is_silent(self):
        # A load in place may sit above the ceiling (creation runs no
        # at_pre_object_receive, objects.py:1956-1975); a drop from there
        # stays non-free.
        self._load(40)
        anvil = _make(self.char1, key="anvil", enc=2)
        self.assertEqual(self.char1.encumbrance_state, CEILING)
        with mock.patch.object(self.char1, "msg") as msg:
            self.assertTrue(anvil.move_to(self.room1, quiet=True))
        self.assertEqual(_crossings(msg), [])
        self.assertEqual(self.char1.encumbrance_state, OVERLOADED)

    def test_give_tells_each_side_its_own_crossing(self):
        self._load(20)
        self._load(20, holder=self.char2)
        anvil = _make(self.room1, key="anvil", enc=1)
        anvil.move_to(self.char2, quiet=True)
        with mock.patch.object(self.char1, "msg") as receiver_msg:
            out = self.call(CmdGive(), "anvil = Char", caller=self.char2)
        self.assertEqual(anvil.location, self.char1)
        self.assertEqual(_crossings(receiver_msg), [OVER])
        self.assertEqual(out.count(FREE_AGAIN), 1)
        self.assertEqual(out.count(OVER), 0)


class TestInventoryLine(EvenniaCommandTest):
    """`inventory` ends in the ENC line, whatever clothing printed above it."""

    def test_a_known_load(self):
        _make(self.char1, key="load", enc=5)
        _make(self.char1, key="axe", enc=2)
        out = self.call(CmdInventory(), "")
        self.assertIn("You are carrying:", out)          # receipt: super() ran
        self.assertIn("Carrying 7/20 ENC", out)
        self.assertNotIn("(overloaded)", out)

    def test_at_the_limit_is_not_overloaded(self):
        _make(self.char1, key="load", enc=20)
        out = self.call(CmdInventory(), "")
        self.assertIn("Carrying 20/20 ENC", out)
        self.assertNotIn("(overloaded)", out)

    def test_overloaded_and_ceiling_both_say_so(self):
        load = _make(self.char1, key="load", enc=21)
        out = self.call(CmdInventory(), "")
        self.assertIn("Carrying 21/20 ENC (overloaded)", out)
        load.db.enc = 41
        out = self.call(CmdInventory(), "")
        self.assertIn("Carrying 41/20 ENC (overloaded)", out)

    def test_empty_inventory_still_shows_the_line(self):
        out = self.call(CmdInventory(), "")
        self.assertIn("You are not carrying or wearing anything.", out)
        self.assertIn("Carrying 0/20 ENC", out)


class TestRefusalLine(EvenniaCommandTest):
    """One refusal, one sentence -- and only the ceiling's refusal is trimmed."""

    REFUSED = "You cannot carry any more."

    def test_a_ceiling_refusal_prints_one_sentence(self):
        _make(self.char1, key="load", enc=39)
        anvil = _make(self.room1, key="anvil", enc=2)
        out = self.call(CmdGet(), "anvil")
        self.assertEqual(out.count(self.REFUSED), 1)
        self.assertNotIn(CONTRIB_REFUSAL, out)
        self.assertEqual(anvil.location, self.room1)
        self.assertFalse(self.char1.ndb._enc_refused)

    def test_another_refusal_keeps_the_contrib_line(self):
        # a flag left over from an earlier refusal (a `give` to char1, say)
        self.char1.ndb._enc_refused = True
        anvil = _make(self.room1, key="anvil", enc=0)
        with mock.patch.object(type(anvil), "at_pre_move", return_value=False):
            out = self.call(CmdGet(), "anvil")
        self.assertIn(CONTRIB_REFUSAL, out)
        self.assertNotIn(self.REFUSED, out)
        self.assertEqual(anvil.location, self.room1)

    def test_the_cmdset_uses_the_project_commands(self):
        from commands.default_cmdsets import CharacterCmdSet

        commands = {cmd.key: cmd for cmd in CharacterCmdSet().commands}
        self.assertIsInstance(commands["get"], CmdGet)
        self.assertIsInstance(commands["inventory"], CmdInventory)
