"""
Tests for L3.1 -- a worn garment that leaves its wearer by any path is no
longer worn (typeclasses/clothing.py, ClothingWithBuffs.at_post_move).

Each class presses one bug:

    TestDropLeavesTheBody      the wearer's cold stress is stale until the next
                               tick (worn_warmth is live and drops by itself;
                               the stress stacks only move through remove())
    TestGiveLeavesTheBody      the receiver counts the garment worn -- LM-M9's
                               named killer
    TestPutLeavesTheBody       a garment put in a sack keeps its flag
    TestCoveringLayerLeaves    the hook clears the flag directly instead of
                               calling remove(), leaving the undershirt
                               covered by a garment no longer on the body; also
                               pins that a covered layer stays on, warms and
                               cannot be dropped on its own
    TestGetStillClears         the hook breaks `get`, or at_get stops running;
                               pins the live order (the hook runs BEFORE at_get)
    TestTradeRefusesWornGarment
                               a garment worn after it was offered is carried
                               off the body by barter's assignment, which runs
                               no hook (world/barter.py:64 is the only guard)

The stress assertions read the ColdStress stacks in a room pinned to "cold"
(band 4-8): naked is 4, a warmth-1 hood is 3. The readings are the same
expressions the in-game protocol uses.
"""

from unittest import mock

from evennia import create_object
from evennia.commands.default.general import CmdDrop, CmdGive
from evennia.contrib.game_systems.clothing.clothing import CmdRemove, get_worn_clothes
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.inventory_commands import CmdGet, CmdPut
from tests.test_activity_log import ActivityLogMixin
from tests.test_barter_currency import TradeFixtureMixin
from tests.test_currency import LedgerIsolationMixin
from typeclasses.clothing import ClothingWithBuffs
from world.thermal import apply_thermal_stress, worn_warmth

CHARACTER = "typeclasses.characters.Character"
CLOTHING = "typeclasses.clothing.ClothingWithBuffs"
CONTAINER = "typeclasses.containers.Container"

NAKED_COLD = 4      # COMFORT_BANDS["cold"][0] - 0
HOODED_COLD = 3     # COMFORT_BANDS["cold"][0] - 1


def cold_stacks(char):
    """The ColdStress stack count, 0 when the buff is absent."""
    buff = char.buffs.get("cold_stress")
    return buff.stacks if buff else 0


def _garment(location, key, clothing_type, warmth=1):
    garment = create_object(CLOTHING, key=key, location=location, home=location)
    garment.db.clothing_type = clothing_type
    garment.db.warmth = warmth
    return garment


class _WornHoodFixture:
    """char1 in a cold room, wearing a warmth-1 hood; stress set from it."""

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        self.room1.db.thermal_regime = "cold"
        self.hood = _garment(self.char1, "hood", "hat")
        apply_thermal_stress(self.char1)
        apply_thermal_stress(self.char2)
        self.hood.wear(self.char1, True, quiet=True)


class TestFixtureReadsTheStress(_WornHoodFixture, EvenniaTest):
    """The receipt that the stress reading moves at all before anything leaves."""

    def test_wearing_the_hood_lowers_cold_stress_at_once(self):
        self.assertTrue(self.hood.db.worn)
        self.assertEqual(worn_warmth(self.char1), 1)
        self.assertEqual(cold_stacks(self.char1), HOODED_COLD)
        self.assertEqual(cold_stacks(self.char2), NAKED_COLD)


class TestDropLeavesTheBody(_WornHoodFixture, EvenniaCommandTest):
    def test_drop_clears_the_flag(self):
        self.call(CmdDrop(), "hood")
        self.assertEqual(self.hood.location, self.room1)
        self.assertFalse(self.hood.db.worn)

    def test_drop_recomputes_the_wearers_stress_without_a_tick(self):
        # worn_warmth would read 0 here with or without the hook -- it walks
        # contents live. The stacks are what only remove() moves.
        self.call(CmdDrop(), "hood")
        self.assertEqual(worn_warmth(self.char1), 0)
        self.assertEqual(cold_stacks(self.char1), NAKED_COLD)


class TestGiveLeavesTheBody(_WornHoodFixture, EvenniaCommandTest):
    def test_the_receiver_does_not_wear_it(self):
        before = worn_warmth(self.char2)
        self.call(CmdGive(), "hood to Char2")
        self.assertEqual(self.hood.location, self.char2)
        self.assertFalse(self.hood.db.worn)
        self.assertEqual(get_worn_clothes(self.char2), [])
        self.assertEqual(worn_warmth(self.char2), before)

    def test_the_giver_is_cold_again(self):
        self.call(CmdGive(), "hood to Char2")
        self.assertEqual(cold_stacks(self.char1), NAKED_COLD)


class TestPutLeavesTheBody(_WornHoodFixture, EvenniaCommandTest):
    def test_put_in_a_carried_sack_clears_the_flag(self):
        sack = create_object(CONTAINER, key="large sack", location=self.char1)
        sack.capacity = 10
        self.call(CmdPut(), "hood in large sack")
        self.assertEqual(self.hood.location, sack)
        self.assertFalse(self.hood.db.worn)
        self.assertEqual(cold_stacks(self.char1), NAKED_COLD)


class TestCoveringLayerLeaves(_WornHoodFixture, EvenniaCommandTest):
    """A top covers an undershirt (the contrib's default autocover)."""

    def setUp(self):
        super().setUp()
        self.undershirt = _garment(self.char1, "undershirt", "undershirt")
        self.top = _garment(self.char1, "tunic", "top")
        self.undershirt.wear(self.char1, True, quiet=True)
        self.top.wear(self.char1, True, quiet=True)

    def test_a_covered_layer_still_warms(self):
        self.assertEqual(self.undershirt.db.covered_by, self.top)
        self.assertEqual(worn_warmth(self.char1), 3)  # hood + top + covered undershirt

    def test_a_covered_layer_cannot_be_dropped_on_its_own(self):
        self.call(CmdDrop(), "undershirt")
        self.assertEqual(self.undershirt.location, self.char1)
        self.assertTrue(self.undershirt.db.worn)

    def test_dropping_the_cover_uncovers_and_keeps_the_layer_worn(self):
        self.call(CmdDrop(), "tunic")
        self.assertFalse(self.top.db.worn)
        self.assertEqual(self.undershirt.location, self.char1)
        self.assertTrue(self.undershirt.db.worn)
        self.assertFalse(self.undershirt.db.covered_by)
        self.assertEqual(worn_warmth(self.char1), 2)  # hood + undershirt

    def test_the_uncovered_layer_can_then_be_removed(self):
        # Under a direct clear the undershirt would answer "You have to take
        # off tunic first." for a tunic lying on the floor.
        self.call(CmdDrop(), "tunic")
        self.call(CmdRemove(), "undershirt")
        self.assertFalse(self.undershirt.db.worn)


class TestGetStillClears(_WornHoodFixture, EvenniaCommandTest):
    def _get_with_spy(self):
        """Run `get hood`; return the hood's flag as at_get saw it."""
        seen = []
        original = ClothingWithBuffs.at_get

        def record_then_call(garment, getter):
            seen.append(garment.db.worn)
            return original(garment, getter)

        with mock.patch.object(
            ClothingWithBuffs, "at_get", autospec=True, side_effect=record_then_call
        ):
            self.call(CmdGet(), "hood")
        return seen

    def test_get_after_drop_still_works_and_at_get_still_runs(self):
        self.call(CmdDrop(), "hood")
        seen = self._get_with_spy()
        self.assertEqual(self.hood.location, self.char1)
        self.assertFalse(self.hood.db.worn)
        self.assertEqual(len(seen), 1)

    def test_a_leaked_flag_is_cleared_before_at_get_runs(self):
        # A direct assignment runs no hook, so the flag rides along to the
        # floor. `get` calls move_to first and at_get after (general.py:472-475,
        # containers.py:209-224): the hook has already cleared it.
        self.hood.location = self.room1
        self.assertTrue(self.hood.db.worn)
        seen = self._get_with_spy()
        self.assertEqual(self.hood.location, self.char1)
        self.assertFalse(self.hood.db.worn)
        self.assertEqual(len(seen), 1)
        self.assertFalse(seen[0])


class TestTradeRefusesWornGarment(
    ActivityLogMixin, TradeFixtureMixin, LedgerIsolationMixin, EvenniaTest
):
    """
    The trade path has no hook: barter moves by `location =` assignment
    (barter.py:369, 371). Offer-time refusal is pinned in
    test_barter_currency.py; this pins the finish-time guard at
    world/barter.py:64, the one that stops a garment worn AFTER it was offered.
    """

    def test_a_garment_worn_after_the_offer_stays_on_the_body(self):
        hood = _garment(self.char1, "hood", "hat")
        self.handler.offer(self.char1, hood)
        self.handler.offer(self.char2, currency=100)
        hood.wear(self.char1, True, quiet=True)
        self._complete()
        self.assertEqual(hood.location, self.char1)
        self.assertTrue(hood.db.worn)
        self.assertEqual(self.char2.currency.value, self.START_BALANCE)
