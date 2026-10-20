"""
`harvest` on a player's body (BACKLOG: *`harvest` treats a player's body as a
rabbit*).

`PlayerCorpse` inherits `creature_type = "rabbit"`, and autocreate stores it on
every player corpse, so before the fix `harvest corpse of <player>` listed the
rabbit's parts and a named part reached `get_part` and the skill roll.
`CmdHarvest` step 4b now refuses on `is_player_corpse`, after the expiry check
(step 4) and before any template lookup.

What each class pressures:

- `TestHarvestRefusesAPlayerBody`: the bug itself, on both paths (the parts
  listing and a named part), with the stored `"rabbit"` left in place so the
  guard is shown not to rest on that data. A named part must not roll, spawn,
  write `harvested` or start the cooldown.
- `TestExpiryStillComesFirst`: a guard moved above step 4 would refuse an
  expired body instead of crumbling it, and its loot would outlive it.
- `TestCreatureCorpsesStillHarvest`: a guard that over-reaches (keyed on the
  Corpse typeclass, or on anything a creature corpse also answers truthily)
  would refuse every harvest in the game.
"""

from unittest import mock

from evennia import create_object
from evennia.objects.models import ObjectDB
from evennia.utils.test_resources import EvenniaCommandTest

from commands.hunting_commands import CmdHarvest

CHARACTER = "typeclasses.characters.Character"
ROOM = "typeclasses.rooms.Room"
CORPSE = "typeclasses.corpse.Corpse"
PLAYER_CORPSE = "typeclasses.corpse.PlayerCorpse"
OBJECT = "typeclasses.objects.Object"

REFUSAL = "That is no quarry, but what remains of someone."
LISTING = "You could harvest:"


class _GuardFixture:
    """Shared builders. Mixed into EvenniaCommandTest below."""

    character_typeclass = CHARACTER
    room_typeclass = ROOM

    def make_corpse(self, key, typeclass=PLAYER_CORPSE, expired=False):
        corpse = create_object(typeclass, key=key, location=self.room1)
        if expired:
            # Same expression as the in-game protocol and test_corpse_expiry.
            corpse.db.death_time = 1
        # Precondition receipt: a refusal on an expired body would be a
        # different test, and a crumble on a fresh one a different bug.
        self.assertEqual(corpse.is_expired, expired)
        return corpse


class TestHarvestRefusesAPlayerBody(_GuardFixture, EvenniaCommandTest):
    """The bug: a player corpse read the rabbit template on both paths."""

    def setUp(self):
        super().setUp()
        self.corpse = self.make_corpse("guardcorpse")
        # The data the bug read is still there; the guard must not need it gone.
        self.assertEqual(
            (
                self.corpse.attributes.get("creature_type"),
                self.corpse.attributes.get("is_player_corpse"),
            ),
            ("rabbit", True),
        )

    def test_listing_is_refused_once_and_lists_nothing(self):
        output = self.call(CmdHarvest(), "guardcorpse")

        self.assertEqual(output.count(REFUSAL), 1)
        self.assertNotIn(LISTING, output)
        self.assertNotIn("meat", output)

    def test_refusal_points_at_the_loot_path(self):
        output = self.call(CmdHarvest(), "guardcorpse")

        self.assertIn("To take something back: get <item> from guardcorpse.", output)

    def test_named_part_is_refused_without_a_roll(self):
        before = set(self.char1.contents)

        with mock.patch("commands.hunting_commands.skill_check") as roll:
            output = self.call(CmdHarvest(), "meat from guardcorpse")

        self.assertEqual(output.count(REFUSAL), 1)
        roll.assert_not_called()
        # Identical to in-game protocol step 3.
        self.assertEqual(
            (dict(self.corpse.db.harvested), set(self.char1.contents) - before),
            ({}, set()),
        )
        # A free bailout: the next harvest elsewhere is not delayed.
        self.assertTrue(self.char1.cooldowns.ready("harvest"))


class TestExpiryStillComesFirst(_GuardFixture, EvenniaCommandTest):
    """Step 4 before step 4b: an expired body crumbles, it is not refused."""

    def test_named_part_on_an_expired_player_corpse_crumbles_it(self):
        corpse = self.make_corpse("guardcorpse", expired=True)
        ring = create_object(OBJECT, key="guardring", location=corpse, home=self.room1)
        corpse_id, ring_id = corpse.id, ring.id

        output = self.call(CmdHarvest(), "bone from guardcorpse")

        self.assertIn("crumbles to dust", output)
        self.assertNotIn(REFUSAL, output)
        self.assertEqual(
            (
                ObjectDB.objects.filter(id=corpse_id).exists(),
                ObjectDB.objects.filter(id=ring_id).exists(),
            ),
            (False, False),
        )


class TestCreatureCorpsesStillHarvest(_GuardFixture, EvenniaCommandTest):
    """The guard does not over-reach: a creature corpse still offers its parts."""

    def test_creature_corpse_lists_its_parts(self):
        corpse = self.make_corpse("guardcarcass", typeclass=CORPSE)
        # Receipt that this is the negative case: no flag on a creature corpse.
        self.assertIsNone(corpse.db.is_player_corpse)

        output = self.call(CmdHarvest(), "guardcarcass")

        self.assertIn(LISTING, output)
        self.assertNotIn(REFUSAL, output)
