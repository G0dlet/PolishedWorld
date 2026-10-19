"""
Death contract surfaces (BACKLOG: Death contract surfaces, feature/death-contract).

Three player-facing changes ship together: owner-first loot grace on a
PlayerCorpse (the first lock in the project with a time term), the death line
that carries the contract, and a `help death` topic. Each class pressures one
bug:

- TestGraceBoundary -- an off-by-one or an inverted comparison on the grace
  edge. Tested just before, exactly on, and after the boundary, with the clock
  pinned so "exactly on" is exact.
- TestGraceClockIsUnscaled -- building the grace on the env-scaled decay clock.
  Then a cold snap re-locks a corpse that had already opened, and a heatwave
  opens it early.
- TestGraceFailsClosed -- an exception escaping the lockfunc. Evennia's
  LockHandler.check() has no try/except, so it would reach the looter as a
  traceback. A broken corpse must stay owner-only, and the owner must still pass.
- TestDeletedOwner -- an owner lookup that crashes or stays locked forever when
  the owner's character no longer exists.
- TestLootThroughTheCommand -- the lock is right but the route is wrong: the
  refusal printed twice (two writers), the item moving anyway, or the owner
  refused. Same `get ... from ...` the in-game protocol uses.
- TestGraceShorterThanFastestExpiry -- a calibration change that lets a body
  crumble before anyone but its owner may touch it. The bound is derived from
  the modifier tables, not typed.
- TestDeathMessage -- a death line that claims a body that was never made, names
  the wrong room, hard-codes a number, or loses "You have died." (T13 ordering);
  or arrives after Death's Chill announces the comeback (seen in-game).
- TestHelpDeath -- `help death` missing (a failed import silently skips the
  whole help module) or saying different numbers from the death line.
- TestLookShowsTheClaim -- the time-left line shown after the grace, or worded
  for the wrong reader.
- TestFormatGameSpan -- rounding up. Every span is a promise, so it floors.

Clock: `typeclasses.corpse.gametime_utils.get_absolute_gametime` is pinned to
NOW and `death_time` is set relative to it, so hours-since-death are exact.
"""

from contextlib import contextmanager
from unittest import mock

from evennia import create_object
from evennia.contrib.game_systems.containers.containers import CmdContainerGet
from evennia.objects.models import ObjectDB
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from typeclasses import corpse as corpse_module
from typeclasses.corpse import PlayerCorpse
from world import death_contract
from world.death_contract import format_game_span
from world.survival_buffs import DeathWeakness

PLAYER_CORPSE = "typeclasses.corpse.PlayerCorpse"
CHARACTER = "typeclasses.characters.Character"
OBJECT = "typeclasses.objects.Object"

NOW = 10_000_000          # absolute game seconds; any value far from 0 works
HOUR = 3600
GRACE = PlayerCorpse._PLAYER_GRACE_HOURS
REFUSAL = "That body's belongings are still its owner's to reclaim."


@contextmanager
def clock_at(now=NOW):
    """Pin the game clock that corpse.py reads."""
    with mock.patch.object(
        corpse_module.gametime_utils, "get_absolute_gametime", return_value=now
    ):
        yield


@contextmanager
def captured_messages(obj):
    """Collect everything `obj.msg()` receives inside the block."""
    seen = []
    original = obj.msg

    def _capture(text=None, *args, **kwargs):
        if isinstance(text, tuple):
            text = text[0]
        seen.append(str(text))

    obj.msg = _capture
    try:
        yield seen
    finally:
        obj.msg = original


def make_corpse(location, owner, hours_ago=0.0, key="corpse of Owner"):
    corpse = create_object(
        PLAYER_CORPSE, key=key, location=location, attributes=[("owner", owner.id)]
    )
    corpse.db.death_time = NOW - int(hours_ago * HOUR)
    return corpse


class GraceTestBase(EvenniaTest):
    def setUp(self):
        super().setUp()
        # Guard: a superuser bypasses every lock, which would make the
        # non-owner assertions below pass for the wrong reason.
        self.assertFalse(self.char1.locks.lock_bypass)
        self.assertFalse(self.char2.locks.lock_bypass)
        self.owner, self.stranger = self.char1, self.char2


class TestGraceBoundary(GraceTestBase):
    def test_lock_string_is_the_grace_lock(self):
        corpse = make_corpse(self.room1, self.owner)
        self.assertIn("corpse_grace()", corpse.locks.get("get_from"))

    def test_owner_passes_at_death_and_throughout(self):
        for hours in (0, GRACE / 2, GRACE - 0.01, GRACE, GRACE * 3):
            corpse = make_corpse(self.room1, self.owner, hours)
            with clock_at():
                self.assertTrue(corpse.access(self.owner, "get_from"), hours)

    def test_stranger_refused_inside_the_grace(self):
        for hours in (0, 1, GRACE - 1, GRACE - 0.01):
            corpse = make_corpse(self.room1, self.owner, hours)
            with clock_at():
                self.assertTrue(corpse.grace_active, hours)
                self.assertFalse(corpse.access(self.stranger, "get_from"), hours)

    def test_stranger_passes_exactly_on_the_boundary(self):
        corpse = make_corpse(self.room1, self.owner, GRACE)
        with clock_at():
            self.assertFalse(corpse.grace_active)
            self.assertTrue(corpse.access(self.stranger, "get_from"))

    def test_stranger_passes_after_the_grace(self):
        corpse = make_corpse(self.room1, self.owner, GRACE + 1)
        with clock_at():
            self.assertTrue(corpse.access(self.stranger, "get_from"))

    def test_the_same_corpse_opens_as_the_clock_moves(self):
        """One object observed changing, not two objects sampled once (§11i)."""
        corpse = make_corpse(self.room1, self.owner, 0)
        with clock_at(NOW + (GRACE * HOUR) - 1):
            self.assertFalse(corpse.access(self.stranger, "get_from"))
        with clock_at(NOW + GRACE * HOUR):
            self.assertTrue(corpse.access(self.stranger, "get_from"))


class TestGraceClockIsUnscaled(GraceTestBase):
    def _with_modifier(self, value):
        return mock.patch.object(
            PlayerCorpse, "decay_modifier", new_callable=mock.PropertyMock, return_value=value
        )

    def test_heat_does_not_open_early(self):
        corpse = make_corpse(self.room1, self.owner, GRACE - 1)
        with clock_at(), self._with_modifier(3.0):
            # Receipt the patch took effect: scaled time is past the grace.
            self.assertGreater(corpse._elapsed_game_hours(), GRACE)
            self.assertFalse(corpse.access(self.stranger, "get_from"))

    def test_cold_does_not_relock(self):
        corpse = make_corpse(self.room1, self.owner, GRACE + 1)
        with clock_at(), self._with_modifier(0.0625):
            self.assertLess(corpse._elapsed_game_hours(), GRACE)
            self.assertTrue(corpse.access(self.stranger, "get_from"))

    def test_raw_clock_is_the_unscaled_span(self):
        corpse = make_corpse(self.room1, self.owner, 10)
        with clock_at(), self._with_modifier(2.0):
            self.assertEqual(corpse._raw_elapsed_game_hours(), 10)
            self.assertEqual(corpse._elapsed_game_hours(), 20)


class TestGraceFailsClosed(GraceTestBase):
    def test_bad_death_time_denies_stranger_without_raising(self):
        corpse = make_corpse(self.room1, self.owner, GRACE * 3)
        corpse.db.death_time = "not a time"
        with clock_at(), mock.patch("server.conf.lockfuncs.logger.log_trace") as trace:
            self.assertFalse(corpse.access(self.stranger, "get_from"))
        self.assertEqual(trace.call_count, 1)   # receipt: the except branch ran

    def test_bad_death_time_still_lets_the_owner_in(self):
        corpse = make_corpse(self.room1, self.owner, 0)
        corpse.db.death_time = "not a time"
        with clock_at():
            self.assertTrue(corpse.access(self.owner, "get_from"))

    def test_lockfunc_on_a_non_corpse_denies(self):
        thing = create_object(OBJECT, key="crate", location=self.room1)
        thing.locks.add("get_from:corpse_grace()")
        with mock.patch("server.conf.lockfuncs.logger.log_trace") as trace:
            self.assertFalse(thing.access(self.stranger, "get_from"))
        self.assertEqual(trace.call_count, 1)


class TestDeletedOwner(GraceTestBase):
    def test_deleted_owner_body_stays_locked_then_opens(self):
        doomed = create_object(CHARACTER, key="Doomed", location=self.room1)
        locked = make_corpse(self.room1, doomed, 0, key="corpse of Doomed")
        opened = make_corpse(self.room1, doomed, GRACE + 1, key="corpse of Doomed")
        doomed_id = doomed.id
        doomed.delete()
        self.assertFalse(ObjectDB.objects.filter(id=doomed_id).exists())
        with clock_at():
            self.assertFalse(locked.access(self.stranger, "get_from"))
            self.assertTrue(opened.access(self.stranger, "get_from"))


class TestLootThroughTheCommand(EvenniaCommandTest):
    """`get <item> from <corpse>`: the route the in-game protocol uses."""

    def setUp(self):
        super().setUp()
        self.assertFalse(self.char1.locks.lock_bypass)
        self.corpse = make_corpse(self.room1, self.char2, 0, key="corpse of Owner")
        self.item = create_object(OBJECT, key="flint knife", location=self.corpse)

    def test_stranger_refused_once_and_item_stays(self):
        with clock_at():
            out = self.call(CmdContainerGet(), "flint knife from corpse of Owner")
        self.assertEqual(out.count(REFUSAL), 1)
        self.assertNotIn("You can't get", out)       # no second writer
        self.assertEqual(self.item.location, self.corpse)

    def test_stranger_takes_after_the_grace(self):
        self.corpse.db.death_time = NOW - (GRACE * HOUR)
        with clock_at():
            out = self.call(CmdContainerGet(), "flint knife from corpse of Owner")
        self.assertNotIn(REFUSAL, out)
        self.assertEqual(self.item.location, self.char1)

    def test_owner_takes_inside_the_grace(self):
        self.corpse.db.owner = self.char1.id
        with clock_at():
            out = self.call(CmdContainerGet(), "flint knife from corpse of Owner")
        self.assertNotIn(REFUSAL, out)
        self.assertEqual(self.item.location, self.char1)


class TestGraceShorterThanFastestExpiry(EvenniaTest):
    def test_grace_below_the_fastest_expiry(self):
        fastest = max([1.0, *corpse_module._SEASON_MODIFIERS.values()]) * max(
            [1.0, *corpse_module._WEATHER_MODIFIERS.values()]
        )
        self.assertEqual(death_contract.fastest_decay_modifier(), fastest)
        self.assertLess(GRACE, PlayerCorpse._PLAYER_EXPIRY_HOURS / fastest)

    def test_corpse_in_fastest_decay_is_open_before_it_expires(self):
        corpse = make_corpse(self.room1, self.char1, death_contract.shortest_keep_game_hours() - 0.01)
        with clock_at(), mock.patch.object(
            PlayerCorpse, "decay_modifier", new_callable=mock.PropertyMock,
            return_value=death_contract.fastest_decay_modifier(),
        ):
            self.assertFalse(corpse.is_expired)
            self.assertFalse(corpse.grace_active)


class TestDeathMessage(EvenniaTest):
    def _die(self, char):
        with captured_messages(char) as seen:
            char.at_character_death()
        return [line for line in seen if "You have died." in line]

    def test_line_names_the_body_room_and_the_contract(self):
        lines = self._die(self.char1)
        self.assertEqual(len(lines), 1)
        line = lines[0]
        self.assertTrue(line.startswith("|RYou have died.|n"))
        self.assertIn(self.room1.key, line)
        self.assertIn(format_game_span(death_contract.shortest_keep_game_hours()), line)
        self.assertIn(format_game_span(GRACE), line)
        self.assertIn(DeathWeakness.name, line)
        # Receipt that the room came from a real corpse.
        corpse = [o for o in self.room1.contents if o.is_typeclass(PLAYER_CORPSE)]
        self.assertEqual(len(corpse), 1)
        self.assertEqual(corpse[0].db.owner, self.char1.id)

    def test_no_body_claimed_when_the_corpse_spawn_fails(self):
        with mock.patch("typeclasses.characters.create_object", side_effect=RuntimeError):
            lines = self._die(self.char1)
        self.assertEqual(len(lines), 1)
        self.assertNotIn("Your body lies", lines[0])
        self.assertIn("still with you", lines[0])
        self.assertIn(DeathWeakness.name, lines[0])

    def test_died_is_read_before_the_chill_applies(self):
        """The death line precedes DeathWeakness.at_apply's own message."""
        with captured_messages(self.char1) as seen:
            self.char1.at_character_death()
        died = [i for i, line in enumerate(seen) if "You have died." in line]
        chill = [i for i, line in enumerate(seen) if "claw back from the edge" in line]
        # Receipt that both writers ran, once each, before comparing order.
        self.assertEqual((len(died), len(chill)), (1, 1), seen)
        self.assertLess(died[0], chill[0], seen)

    def test_line_is_exactly_the_shared_builder(self):
        lines = self._die(self.char1)
        self.assertEqual(lines[0], death_contract.death_message(self.room1))


class TestHelpDeath(EvenniaCommandTest):
    def test_help_death_answers(self):
        from evennia.commands.default.help import CmdHelp

        from commands.default_cmdsets import CharacterCmdSet

        out = self.call(CmdHelp(), "death", cmdset=CharacterCmdSet())
        self.assertIn("Your claim", out)

    def test_help_and_death_line_use_the_same_numbers(self):
        from world.help_entries import HELP_ENTRY_DICTS

        entries = [d for d in HELP_ENTRY_DICTS if d["key"] == "death"]
        self.assertEqual(len(entries), 1)
        text = entries[0]["text"]
        line = death_contract.death_message(self.room1)
        for span in (
            format_game_span(death_contract.shortest_keep_game_hours()),
            format_game_span(GRACE),
        ):
            self.assertIn(span, text)
            self.assertIn(span, line)
        self.assertIn(DeathWeakness.name, text)


class TestLookShowsTheClaim(GraceTestBase):
    def test_owner_and_stranger_read_different_words(self):
        corpse = make_corpse(self.room1, self.owner, 0)
        with clock_at():
            self.assertIn("Your claim", corpse.return_appearance(self.owner))
            self.assertIn("Its owner's claim", corpse.return_appearance(self.stranger))

    def test_time_left_counts_down(self):
        corpse = make_corpse(self.room1, self.owner, GRACE - 30)
        with clock_at():
            self.assertIn("about 1 in-game day more", corpse.return_appearance(self.stranger))

    def test_no_claim_line_after_the_grace(self):
        corpse = make_corpse(self.room1, self.owner, GRACE)
        with clock_at():
            self.assertNotIn("claim", corpse.return_appearance(self.stranger))


class TestFormatGameSpan(EvenniaTest):
    def test_floors(self):
        cases = {
            96: "4 in-game days",
            95.9: "3 in-game days",
            24: "1 in-game day",
            23.9: "23 in-game hours",
            1: "1 in-game hour",
            0.5: "less than an in-game hour",
            -5: "less than an in-game hour",
        }
        for hours, expected in cases.items():
            self.assertEqual(format_game_span(hours), expected, hours)
