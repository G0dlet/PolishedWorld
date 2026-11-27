"""
Death contract surfaces (BACKLOG: Death contract surfaces, feature/death-contract).

Three player-facing changes ship together: owner-first loot grace on a
PlayerCorpse (the first lock in the project with a time term), the death line
that carries the contract, and a `help death` topic. Each class pressures one
bug:

- TestGraceBoundary -- an off-by-one or an inverted comparison on the grace
  edge. Tested just before, exactly on, and after the boundary, with the clock
  pinned so "exactly on" is exact.
- TestGraceInAHaven -- the grace not reading the room (HV4): a body in a
  haven opening at 72 hours like any other (HVM4, `and` for `or`).
- TestGraceReadsTheBodysRoom -- the wrong room read: the owner's, not the
  body's (HVM5). The looters stand in one room and the body lies in another.
- TestHavenFlagMovesTheAnswer -- the departure (Haven §11, 2) undone without
  anyone seeing: the flag taken off opens a body past the grace at once, and
  the flag set closes one that had opened.
- TestLootInAHavenThroughTheCommand -- the lock right but the route wrong, in
  a haven past the grace.
- TestLookInAHaven -- `look` counting hours in a haven (HVM6), where the span
  has no end and today's count would print one that has run out.
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
  or arrives after Death's Chill announces the comeback (seen in-game); or,
  since Survival Loop S3.5, the rest line missing from the no-body branch
  (SL-M53) or reworded away from the sentence SL12 ratified.
- TestHelpDeath -- `help death` missing (a failed import silently skips the
  whole help module) or saying different numbers from the death line; or the
  rest line dropped from the help text only (SL-M38).
- TestDeathMessageInAHaven -- the death line promising 72 hours to a body
  in a haven (HVM7), or the haven's claim told of a body anywhere (HVM8);
  today's line held word for word, so the haven's branch cannot reword it.
- TestHelpDeathInAHaven -- `help death` silent on the haven's rule (HVM9), or
  still saying that `look` shows how long the claim *has left* (HVM9b).
- TestTheStoredRefusal -- the refusal promising a day that never comes in a
  haven (*You can't take from it yet.*, HVM9c).
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

# Survival Loop S3.5 (SL12): the sentence the decision log ratified.
REST_SENTENCE = "Rest mends the weariness that comes with it."

NOW = 10_000_000          # absolute game seconds; any value far from 0 works
HOUR = 3600
GRACE = PlayerCorpse._PLAYER_GRACE_HOURS
REFUSAL = "That body's belongings are still its owner's to reclaim."
# HV-T3: what the death line and `help death` say of a body in a haven,
# written out by hand so that a change is a decision and not a drift.
HAVEN_CLAIM = "for as long as it lies there only you may take from it."
HAVEN_HELP = "In a haven, only you may take from it, for as long as it lies there."


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


def make_corpse(location, owner, hours_ago=0.0, key="corpse"):
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


# --- The haven (Haven Decomposition HV-T2, HV4) ------------------------------
# room2 is the haven. Unless a test is about which room is read (HVM5), the
# owner and the stranger stand where the body lies, as they would in play, so
# a mutant reading the owner's room changes nothing here and is killed only by
# TestGraceReadsTheBodysRoom (lesson 181).

class HavenTestBase(GraceTestBase):
    def setUp(self):
        super().setUp()
        self.haven = self.room2
        self.haven.db.is_haven = True

    def stand_in(self, room):
        """Put the owner and the stranger in `room`."""
        for char in (self.owner, self.stranger):
            char.move_to(room, quiet=True, move_hooks=False)


class TestGraceInAHaven(HavenTestBase):
    def test_stranger_refused_in_a_haven_past_the_grace(self):
        self.stand_in(self.haven)
        for hours in (GRACE - 1, GRACE + 1, 287):
            corpse = make_corpse(self.haven, self.owner, hours)
            with clock_at():
                self.assertTrue(corpse.grace_active, hours)
                self.assertFalse(corpse.access(self.stranger, "get_from"), hours)

    def test_owner_passes_in_a_haven(self):
        self.stand_in(self.haven)
        for hours in (GRACE - 1, GRACE + 1, 287):
            corpse = make_corpse(self.haven, self.owner, hours)
            with clock_at():
                self.assertTrue(corpse.access(self.owner, "get_from"), hours)

    def test_outside_a_haven_as_today(self):
        refused = make_corpse(self.room1, self.owner, GRACE - 1)
        opened = make_corpse(self.room1, self.owner, GRACE + 1)
        with clock_at():
            self.assertFalse(refused.access(self.stranger, "get_from"))
            self.assertTrue(opened.access(self.stranger, "get_from"))


class TestGraceReadsTheBodysRoom(HavenTestBase):
    def test_body_in_a_haven_with_the_looters_outside(self):
        self.stand_in(self.room1)
        corpse = make_corpse(self.haven, self.owner, GRACE + 1)
        with clock_at():
            self.assertFalse(corpse.access(self.stranger, "get_from"))
            self.assertTrue(corpse.access(self.owner, "get_from"))

    def test_body_outside_with_the_looters_in_a_haven(self):
        self.stand_in(self.haven)
        corpse = make_corpse(self.room1, self.owner, GRACE + 1)
        with clock_at():
            self.assertTrue(corpse.access(self.stranger, "get_from"))


class TestHavenFlagMovesTheAnswer(HavenTestBase):
    """The departure of Haven §11, 2, held so that it is a decision: a staff
    hand on the flag moves the answer, which the weather never can."""

    def test_the_flag_taken_off_opens_a_body_past_the_grace(self):
        self.stand_in(self.haven)
        corpse = make_corpse(self.haven, self.owner, 100)
        with clock_at():
            self.assertFalse(corpse.access(self.stranger, "get_from"))
            self.haven.attributes.remove("is_haven")
            self.assertTrue(corpse.access(self.stranger, "get_from"))

    def test_the_flag_set_closes_a_body_that_had_opened(self):
        corpse = make_corpse(self.room1, self.owner, 100)
        with clock_at():
            self.assertTrue(corpse.access(self.stranger, "get_from"))
            self.room1.db.is_haven = True
            self.assertFalse(corpse.access(self.stranger, "get_from"))


class TestLootInAHavenThroughTheCommand(EvenniaCommandTest):
    """`get <item> from <corpse>` in a haven, past the grace: the route."""

    def setUp(self):
        super().setUp()
        self.assertFalse(self.char1.locks.lock_bypass)
        self.room1.db.is_haven = True
        self.corpse = make_corpse(self.room1, self.char2, GRACE + 1)
        self.item = create_object(OBJECT, key="flint knife", location=self.corpse)

    def test_stranger_refused_in_a_haven_and_item_stays(self):
        with clock_at():
            out = self.call(CmdContainerGet(), "flint knife from corpse")
        self.assertEqual(out.count(REFUSAL), 1)
        self.assertEqual(self.item.location, self.corpse)


class TestLookInAHaven(HavenTestBase):
    def test_the_claim_line_has_no_number(self):
        self.stand_in(self.haven)
        line = "claim on what it holds lasts for as long as it lies here."
        # GRACE + 1, not later: past 96 hours a body in the fastest decay
        # would crumble on look (shortest_keep_game_hours).
        for hours in (0, GRACE + 1):
            corpse = make_corpse(self.haven, self.owner, hours)
            with clock_at():
                mine = corpse.return_appearance(self.owner)
                theirs = corpse.return_appearance(self.stranger)
            self.assertIn(f"Your {line}", mine, hours)
            self.assertIn(f"Its owner's {line}", theirs, hours)
            self.assertNotIn("in-game", mine, hours)
            self.assertNotIn("in-game", theirs, hours)


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
        locked = make_corpse(self.room1, doomed, 0)
        opened = make_corpse(self.room1, doomed, GRACE + 1)
        doomed_id = doomed.id
        doomed.delete()
        self.assertFalse(ObjectDB.objects.filter(id=doomed_id).exists())
        # Names NM-T11: a body whose owner is gone names nobody.
        self.assertEqual(locked.get_display_name(self.stranger), "a body")
        with clock_at():
            self.assertFalse(locked.access(self.stranger, "get_from"))
            self.assertTrue(opened.access(self.stranger, "get_from"))


class TestLootThroughTheCommand(EvenniaCommandTest):
    """`get <item> from <corpse>`: the route the in-game protocol uses."""

    def setUp(self):
        super().setUp()
        self.assertFalse(self.char1.locks.lock_bypass)
        self.corpse = make_corpse(self.room1, self.char2, 0)
        self.item = create_object(OBJECT, key="flint knife", location=self.corpse)

    def test_stranger_refused_once_and_item_stays(self):
        with clock_at():
            out = self.call(CmdContainerGet(), "flint knife from corpse")
        self.assertEqual(out.count(REFUSAL), 1)
        self.assertNotIn("You can't get", out)       # no second writer
        self.assertEqual(self.item.location, self.corpse)

    def test_stranger_takes_after_the_grace(self):
        self.corpse.db.death_time = NOW - (GRACE * HOUR)
        with clock_at():
            out = self.call(CmdContainerGet(), "flint knife from corpse")
        self.assertNotIn(REFUSAL, out)
        self.assertEqual(self.item.location, self.char1)

    def test_owner_takes_inside_the_grace(self):
        self.corpse.db.owner = self.char1.id
        with clock_at():
            out = self.call(CmdContainerGet(), "flint knife from corpse")
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

    def test_the_death_line_says_rest_mends(self):
        # S3.5 (SL12): the sentence as ratified, written out by hand, so a
        # change to REST_LINE is a decision and not a drift.
        lines = self._die(self.char1)
        self.assertIn(REST_SENTENCE, lines[0])
        self.assertEqual(death_contract.REST_LINE, REST_SENTENCE)

    def test_no_body_still_says_rest_mends(self):
        # The second branch (SL-M53): a body that leaves no corpse is just as
        # Wearied.
        with mock.patch("typeclasses.characters.create_object", side_effect=RuntimeError):
            lines = self._die(self.char1)
        self.assertIn("still with you", lines[0])   # receipt: the no-body branch
        self.assertIn(REST_SENTENCE, lines[0])

    def test_the_rest_line_follows_the_chill(self):
        # "it" in the sentence is Death's Chill, so it comes after it.
        line = death_contract.death_message(self.room1)
        self.assertLess(line.index(DeathWeakness.name), line.index(REST_SENTENCE))


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

    def test_help_says_rest_mends(self):
        # SL-M38: the help topic carries the sentence too, after the chill's
        # own paragraph heading.
        from world.help_entries import HELP_ENTRY_DICTS

        text = [d for d in HELP_ENTRY_DICTS if d["key"] == "death"][0]["text"]
        self.assertIn(REST_SENTENCE, text)
        self.assertLess(text.index(f"|w{DeathWeakness.name}|n"), text.index(REST_SENTENCE))


class TestDeathMessageInAHaven(EvenniaTest):
    """The death line reads the body's room (HV4): room2 is a haven, room1 not."""

    def setUp(self):
        super().setUp()
        self.room2.db.is_haven = True
        self.keep = format_game_span(death_contract.shortest_keep_game_hours())
        # Receipt: the two spans differ, so the haven's line can lose one and
        # keep the other.
        self.assertNotEqual(self.keep, format_game_span(GRACE))

    def test_the_haven_line_says_the_claim_and_no_grace_span(self):
        line = death_contract.death_message(self.room2)
        self.assertIn(f"Your body lies at {self.room2.key}.", line)
        self.assertIn(f"It keeps your belongings for at least {self.keep}, and {HAVEN_CLAIM}", line)
        self.assertNotIn(format_game_span(GRACE), line)
        self.assertIn(DeathWeakness.name, line)
        self.assertIn(REST_SENTENCE, line)

    def test_another_room_is_todays_line_word_for_word(self):
        expected = (
            "|RYou have died.|n\n"
            f"Your body lies at {self.room1.key}. It keeps your belongings for at "
            f"least {self.keep}, and for the first {format_game_span(GRACE)} only "
            f"you may take from it. {DeathWeakness.name} will pass. {REST_SENTENCE} "
            "See |whelp death|n."
        )
        self.assertEqual(death_contract.death_message(self.room1), expected)

    def test_no_body_is_todays_line_word_for_word(self):
        expected = (
            "|RYou have died.|n\n"
            "You leave no body behind; what you carried is still with you. "
            f"{DeathWeakness.name} will pass. {REST_SENTENCE} See |whelp death|n."
        )
        self.assertEqual(death_contract.death_message(None), expected)

    def test_a_death_in_a_haven_gets_the_haven_line(self):
        self.char1.move_to(self.room2, quiet=True, move_hooks=False)
        with captured_messages(self.char1) as seen:
            self.char1.at_character_death()
        lines = [line for line in seen if "You have died." in line]
        self.assertEqual(len(lines), 1, seen)
        self.assertIn(HAVEN_CLAIM, lines[0])
        self.assertEqual(lines[0], death_contract.death_message(self.room2))


class TestHelpDeathInAHaven(EvenniaTest):
    def _text(self):
        from world.help_entries import HELP_ENTRY_DICTS

        entries = [d for d in HELP_ENTRY_DICTS if d["key"] == "death"]
        self.assertEqual(len(entries), 1)
        return entries[0]["text"]

    def test_help_names_the_havens_rule_once(self):
        text = self._text()
        # Under *Your claim*, right after the rule it is the exception to.
        self.assertIn(f"After that, anyone who finds it may. {HAVEN_HELP}", text)
        self.assertEqual(text.lower().count("haven"), 1)

    def test_help_says_look_shows_how_long_the_claim_lasts(self):
        # In a haven `look` shows no time left (HV-T2), so "has left" is untrue
        # there; "lasts" holds in both places.
        text = self._text()
        self.assertIn("Looking at the body shows how long your claim lasts.", text)
        self.assertNotIn("has left", text)


class TestTheStoredRefusal(EvenniaTest):
    def test_the_stored_refusal_is_the_whole_line(self):
        # The line is stored on each body as it is made and must hold in a
        # haven too, so it promises no later day.
        corpse = make_corpse(self.room1, self.char1)
        self.assertEqual(corpse.db.get_from_err_msg, REFUSAL)


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
