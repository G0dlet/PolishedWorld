"""
Survival Loop S1.2b (OQ-S6): nothing is eaten or drunk into a full gauge.

Lock F1: `drink <vessel>` at full thirst answers "You aren't thirsty." and
spends no draught, as the source already did (S1.1 lock C1). Lock G1: `eat`
at full hunger answers "You aren't hungry." and the food stays. Neither
writes an activity line or pushes. One point short of full still eats and
drinks: the check is the gauge's max, not a margin.

    evennia test --settings settings.py tests.test_full_gauges
"""

from unittest import mock

from evennia import create_object
from evennia.utils.test_resources import EvenniaCommandTest

from commands.consumption_commands import CmdDrink, CmdEat
from tests.test_activity_log import ActivityLogMixin

DRINK = "typeclasses.consumables.Drink"
FOOD = "typeclasses.consumables.Food"
PUSH = "commands.consumption_commands.client_state.push"


class TestVesselAtFullThirst(ActivityLogMixin, EvenniaCommandTest):
    """A carried vessel at full thirst (lock F1)."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.skin = create_object(DRINK, key="fullskin", location=self.char1)
        self.thirst = self.char1.traits.thirst

    def test_full_thirst_spends_no_draught(self):
        self.thirst.current = self.thirst.max
        with mock.patch(PUSH) as push:
            self.call(CmdDrink(), "fullskin", "You aren't thirsty.", caller=self.char1)
        self.assertEqual(self.skin.charges, self.skin.max_charges)
        self.assertEqual(self.activity_records("consume"), [])
        push.assert_not_called()

    def test_one_short_of_full_still_drinks(self):
        self.thirst.current = self.thirst.max - 1
        self.call(CmdDrink(), "fullskin", "You drink from fullskin.", caller=self.char1)
        self.assertEqual(self.skin.charges, self.skin.max_charges - 1)
        self.assertEqual(self.thirst.current, self.thirst.max)

    def test_an_empty_vessel_says_empty_first(self):
        self.skin.charges = 0
        self.thirst.current = self.thirst.max
        self.call(CmdDrink(), "fullskin", "fullskin is empty.", caller=self.char1)


class TestFoodAtFullHunger(ActivityLogMixin, EvenniaCommandTest):
    """Food at full hunger (lock G1)."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.bread = create_object(FOOD, key="fullbread", location=self.char1)
        self.hunger = self.char1.traits.hunger

    def test_full_hunger_keeps_the_food(self):
        self.hunger.current = self.hunger.max
        with mock.patch(PUSH) as push:
            self.call(CmdEat(), "fullbread", "You aren't hungry.", caller=self.char1)
        self.assertTrue(self.bread.pk)
        self.assertEqual(self.bread.location, self.char1)
        self.assertEqual(self.activity_records("consume"), [])
        push.assert_not_called()

    def test_one_short_of_full_still_eats(self):
        self.hunger.current = self.hunger.max - 1
        self.call(CmdEat(), "fullbread", "You eat fullbread.", caller=self.char1)
        self.assertFalse(self.bread.pk)
        self.assertEqual(self.hunger.current, self.hunger.max)
