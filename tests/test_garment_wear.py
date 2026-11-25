"""
Tests for world.garment_wear -- the garment wear tick -- as GR-T6 changes it
(Gear decomposition §7; lock GR20; Arms of Legend p. 58): whoever fought
within the tick's window has every worn garment wear one level harsher.

The module had no tests of its own. The unmarked cases below pin today's
behaviour (common outdoors 2, the indoor shift) so the fight's step is
read against it. The thermal regime is patched; the clock is patched in
world.gear.
"""

from unittest import mock

from evennia.utils import create
from evennia.utils.test_resources import EvenniaTest

from typeclasses.clothing import ClothingWithBuffs
from world import garment_wear, gear

WINDOW = 10800          # the tick's interval, as at_server_startstop hands it in
NOW = 1_000_000.0


class _Worn(EvenniaTest):
    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.garment = create.create_object(
            ClothingWithBuffs, key="wool tunic", location=self.char1)
        self.garment.db.clothing_type = "top"
        self.garment.wear(self.char1, True, quiet=True)
        self.garment.db.condition = 100
        self.room1.db.is_indoor = False

    def tick(self, regime="temperate", window=WINDOW, fought_at=None):
        """One pass of the tick over char1; returns the condition lost."""
        if fought_at is not None:
            self.char1.db.fought_at = fought_at
        with mock.patch.object(garment_wear, "thermal_regime", return_value=regime), \
                mock.patch.object(gear.time, "time", return_value=NOW):
            garment_wear._wear_character(self.char1, window)
        return 100 - self.garment.db.condition


class TestAFightInTheTick(_Worn):
    """
    Pressures GR20: the step taken towards *protected* instead (GRM19), a
    window that never closes (GRM20), and the stamp read from the garment
    and not the wearer (GRM21).
    """

    def test_an_unmarked_wearer_loses_two_outdoors(self):
        self.assertEqual(self.tick(), 2)

    def test_a_marked_wearer_loses_four_outdoors(self):
        self.assertEqual(self.tick(fought_at=NOW - 60), 4)

    def test_indoors_a_marked_wearer_is_basic(self):
        # Two steps towards protected, one back: basic, 1.
        self.room1.db.is_indoor = True
        self.assertEqual(self.tick(fought_at=NOW - 60), 1)

    def test_rigorous_stays_rigorous(self):
        # The cold already makes it rigorous; the fight cannot go past it.
        self.assertEqual(self.tick(regime="cold", fought_at=NOW - 60), 4)

    def test_a_stamp_older_than_the_window_does_nothing(self):
        self.assertEqual(self.tick(fought_at=NOW - WINDOW - 1), 2)

    def test_without_a_window_a_fight_is_not_read(self):
        # `wear_all_garments()` from @py, as at_server_startstop's comment says.
        self.assertEqual(self.tick(window=None, fought_at=NOW - 60), 2)


class TestTheTickHandsInItsWindow(EvenniaTest):
    """Pressures the window reaching the per-character pass from the ticker."""

    def test_the_window_is_passed_on(self):
        session = mock.Mock(puppet=self.char1)
        with mock.patch.object(garment_wear.SESSION_HANDLER, "get_sessions",
                               return_value=[session]), \
                mock.patch.object(garment_wear, "_wear_character") as worn:
            garment_wear.wear_all_garments(window=WINDOW)
        worn.assert_called_once_with(self.char1, WINDOW)
