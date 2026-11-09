"""
Tests for world/room_text.py and the look wiring (webclient decomposition
W5.4, WC4): a room look travels as two text messages, the description
(`type: "look"`) and the room's lists (`type: "room_contents"`), whose
joined text is exactly what one look message carried before.

Each class names the bug it pressures:

  TestCanonicalText     the split changes the text a session receives: a line
                        lost, doubled, reordered, or a blank line from an
                        empty second message (lock 2A). Pinned per room
                        fixture against today's single message and against a
                        literal, so a broken default path cannot agree with
                        itself (W-ai).
  TestTwoMessagesInOrder  one of the three callers -- the move, the look
                        command, the puppet (lock 1A) -- still sends one
                        message, sends the lists first, or sends the look
                        twice because DefaultCharacter's hook still runs; or
                        the command answers every session on the puppet
                        instead of the one that typed it, as the contrib's did.
  TestOtherLooksUnchanged  looking at an object, `look here` (lock 3A), a
                        location that is not a project Room, or a room the
                        looker may not view starts sending two messages.
  TestHookMro           a class added to Character's bases defines one of
                        the two hooks Character no longer passes up (W-ab);
                        the behaviour test above goes with it (W-ac).
  TestLookIsTheKey      `look`, `l` or `ls` still reaches the contrib's
                        command instead of the project's.
  TestOneHelper         the room's text or the client snapshot builds a list
                        from a copy of its own again (lock 4C).
"""

from unittest import mock

from evennia import create_object
from evennia.commands.cmdparser import cmdparser
from evennia.contrib.grid.extended_room.extended_room import CmdExtendedRoomLook
from evennia.objects.objects import DefaultCharacter, DefaultObject
from evennia.utils.test_resources import EvenniaTest

from commands.world_commands import CmdRoomLook
from typeclasses.characters import Character
from world import client_state, room_text

ROOM = "typeclasses.rooms.Room"
EXIT = "typeclasses.exits.Exit"
OBJECT = "typeclasses.objects.Object"


def _texts(spy):
    """(text, type) for every text message a data_out spy saw, in order."""
    out = []
    for call in spy.call_args_list:
        text = call.kwargs.get("text")
        if text is None:
            continue
        if isinstance(text, tuple):
            body = text[0]
            kwargs = text[1] if len(text) > 1 else {}
            out.append((body, kwargs.get("type")))
        else:
            out.append((text, None))
    return out


def _types(spy):
    return [kind for _text, kind in _texts(spy)]


def _awake(key):
    """is_statue False for the character named `key` only."""
    return mock.patch.object(Character, "is_statue", new=property(lambda c: c.key != key))


class _RoomLookTest(EvenniaTest):
    def _room_look(self, room):
        with mock.patch.object(self.session, "data_out") as spy:
            room_text.room_look(self.char1, room)
        return _texts(spy)

    def _cell(self):
        cell = create_object(ROOM, key="Cell")
        cell.db.desc = "Bare stone walls."
        return cell


class TestCanonicalText(_RoomLookTest):
    def _assert_canonical(self, room, literal):
        today = room.return_appearance(self.char1)
        self.assertEqual(today, literal)  # the default path itself is pinned
        sent = self._room_look(room)
        self.assertEqual("\n".join(text for text, _kind in sent), today)
        return sent

    def test_empty_room_is_one_message(self):
        cell = self._cell()
        sent = self._assert_canonical(cell, "|cCell(%s)|n\nBare stone walls." % cell.dbref)
        self.assertEqual([kind for _text, kind in sent], ["look"])

    def test_exits_only(self):
        cell = self._cell()
        create_object(EXIT, key="north", location=cell, destination=self.room2)
        sent = self._assert_canonical(
            cell, "|cCell(%s)|n\nBare stone walls.\n|wExits:|n north" % cell.dbref)
        self.assertEqual(sent[1], ("|wExits:|n north", "room_contents"))

    def test_characters_and_things(self):
        for _ in range(2):
            create_object(OBJECT, key="stone", location=self.room1)
        sleeper = create_object(Character, key="Sleeper", location=self.room1)
        self.assertTrue(sleeper.is_statue)  # receipt: a statue, not awake
        with _awake("Char2"):
            sent = self._assert_canonical(
                self.room1,
                "|cRoom(%s)|n\nroom_desc\n|wExits:|n out\n"
                "|wCharacters:|n Char2\n"
                "|wYou see:|n an Obj, an Obj2, and two stones, |wstone statue of Sleeper|n"
                % self.room1.dbref)
        self.assertEqual([kind for _text, kind in sent], ["look", "room_contents"])
        self.assertTrue(sent[1][0].startswith("|wExits:|n"))


class TestTwoMessagesInOrder(_RoomLookTest):
    def test_move_sends_look_then_room_contents(self):
        self.char1.location = self.room2
        with mock.patch.object(self.session, "data_out") as spy:
            self.assertTrue(self.char1.move_to(self.room1))
        self.assertEqual([k for k in _types(spy) if k], ["look", "room_contents"])

    def test_look_command_sends_look_then_room_contents(self):
        cmd = CmdRoomLook()
        cmd.caller, cmd.session, cmd.args = self.char1, self.session, ""
        with mock.patch.object(self.session, "data_out") as spy:
            cmd.func()
        self.assertEqual(_types(spy), ["look", "room_contents"])

    def test_look_command_answers_only_the_typing_session(self):
        # The contrib's look answers through Command.msg, which picks the
        # session that typed it; a second session on the puppet hears nothing.
        other = mock.Mock(name="second session on the same puppet")
        cmd = CmdRoomLook()
        cmd.caller, cmd.session, cmd.args = self.char1, self.session, ""
        with mock.patch.object(self.char1.sessions, "all",
                               return_value=[self.session, other]), \
                mock.patch.object(self.session, "data_out") as spy:
            self.char1.msg("receipt")
            self.assertEqual(other.data_out.call_count, 1)  # receipt: other is reachable
            other.data_out.reset_mock()
            spy.reset_mock()
            cmd.func()
        self.assertEqual(_types(spy), ["look", "room_contents"])
        other.data_out.assert_not_called()

    def test_puppet_sends_look_then_room_contents(self):
        with mock.patch.object(self.session, "data_out") as spy:
            self.char1.at_post_puppet()
        sent = _texts(spy)
        self.assertEqual([k for _t, k in sent if k], ["look", "room_contents"])
        self.assertIn("You become |cChar|n.", sent[0][0])  # DefaultCharacter's line kept

    def test_puppet_still_tells_the_room(self):
        with mock.patch.object(self.char2, "msg") as heard:
            self.char1.at_post_puppet()
        lines = [c.args[0] if c.args else c.kwargs.get("text") for c in heard.call_args_list]
        self.assertIn("Char has entered the game.", [str(line) for line in lines])


class TestOtherLooksUnchanged(_RoomLookTest):
    def _command(self, args):
        cmd = CmdRoomLook()
        cmd.caller, cmd.session, cmd.args = self.char1, self.session, args
        with mock.patch.object(self.session, "data_out") as spy:
            cmd.func()
        return _texts(spy)

    def test_looking_at_an_object_is_one_look(self):
        sent = self._command("Obj2")
        self.assertEqual([kind for _t, kind in sent], ["look"])
        self.assertIn("Obj2", sent[0][0])

    def test_look_here_is_one_look_with_the_lists(self):
        sent = self._command("here")
        self.assertEqual([kind for _t, kind in sent], ["look"])
        self.assertIn("|wExits:|n out", sent[0][0])

    def test_a_location_that_is_not_a_room_is_one_look(self):
        box = create_object(OBJECT, key="crate")
        create_object(OBJECT, key="nail", location=box)
        sent = self._room_look(box)
        self.assertEqual([kind for _t, kind in sent], ["look"])
        self.assertIn("nail", sent[0][0])

    def test_a_room_the_looker_may_not_view_is_one_refusal(self):
        cell = self._cell()
        with mock.patch.object(cell, "access", return_value=False):
            sent = self._room_look(cell)
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][1], "look")
        self.assertTrue(sent[0][0].startswith("Could not view"), sent[0][0])


class TestHookMro(EvenniaTest):
    def _owners(self, name):
        return [k for k in Character.__mro__ if name in vars(k)]

    def test_at_post_move_owners(self):
        self.assertEqual(self._owners("at_post_move"), [Character, DefaultCharacter, DefaultObject])

    def test_at_post_puppet_owners(self):
        self.assertEqual(self._owners("at_post_puppet"), [Character, DefaultCharacter, DefaultObject])


class TestLookIsTheKey(EvenniaTest):
    def setUp(self):
        super().setUp()
        from commands.default_cmdsets import CharacterCmdSet

        self.cmdset = CharacterCmdSet()
        self.cmdset.at_cmdset_creation()

    def test_look_l_and_ls_reach_this_command(self):
        for typed in ("look", "l", "ls"):
            matches = cmdparser(typed, self.cmdset, self.char1)
            self.assertEqual(len(matches), 1, typed)
            self.assertIs(type(matches[0][2]), CmdRoomLook, typed)

    def test_the_contrib_look_is_gone(self):
        owners = [type(cmd) for cmd in self.cmdset.commands if "look" in cmd._keyaliases]
        self.assertEqual(owners, [CmdRoomLook])
        self.assertTrue(issubclass(CmdRoomLook, CmdExtendedRoomLook))


class TestOneHelper(EvenniaTest):
    def _phantom(self):
        """room_lists answering with entries the real room does not hold."""
        lists = {"exits": [self.exit], "characters": [self.obj2],
                 "things": ["a phantom"], "statues": [self.obj1]}
        return mock.patch("world.room_text.room_lists", return_value=lists)

    def test_the_rooms_list_lines_read_room_lists(self):
        # Obj2 is no character, Obj no statue and nothing is called
        # "phantom": only lines built from room_lists can list them so.
        with self._phantom():
            characters = self.room1.get_display_characters(self.char1)
            things = self.room1.get_display_things(self.char1)
        self.assertEqual(characters, "\n|wCharacters:|n Obj2")
        self.assertEqual(things, "|wYou see:|n a phantom, Obj")

    def test_the_snapshot_reads_room_lists(self):
        with self._phantom():
            snap = client_state.room_snapshot(self.room1, self.char1)
        self.assertEqual(snap["characters"], ["Obj2"])
        self.assertEqual(snap["things"], ["a phantom", "Obj"])

    def test_the_copy_in_client_state_is_gone(self):
        self.assertFalse(hasattr(client_state, "_thing_names"))

    def test_lists_shape(self):
        lists = room_text.room_lists(self.room1, self.char1)
        self.assertEqual(lists["exits"], [self.exit])
        self.assertEqual(lists["characters"], [])
        self.assertEqual(lists["statues"], [self.char2])
        self.assertEqual(lists["things"], ["an Obj", "an Obj2"])
