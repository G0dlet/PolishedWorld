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
  TestOneLinePerCharacter  the characters run together on one line again,
                        lose their poses, list the viewer or a statue, or
                        start a line in lower case; a name's capital is not
                        $You()'s (Names NM-T8, K8, NM14; NM-T9 lock 1B).
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
from tests.names_fixture import describe, shown

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
        # Names NM-T2: characters are listed by the short description.
        describe(self.char2)
        sleeper.sdesc.add("a sleeping traveller")
        with _awake("Char2"):
            sent = self._assert_canonical(
                self.room1,
                "|cRoom(%s)|n\nroom_desc\n|wExits:|n out\n"
                f"{shown(self.char2).capitalize()} is here.\n"
                "|wYou see:|n an Obj, an Obj2, and two stones, "
                "|wstone statue of a sleeping traveller|n"
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
        describe(self.char1)
        with mock.patch.object(self.char2, "msg") as heard:
            self.char1.at_post_puppet()
        lines = [c.args[0] if c.args else c.kwargs.get("text") for c in heard.call_args_list]
        lines = [line[0] if isinstance(line, tuple) else line for line in lines]
        # Names NM-T11 lock 2 A: through `$You()`, so per reader and with the
        # capital a name starting a line has (NM-T2 had Evennia's lower case).
        self.assertIn("A weathered woman has entered the game.", [str(line) for line in lines])


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
        self.assertEqual(characters, "\nObj2")  # Names NM-T8: a line each, no heading
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


def _awake_all(*keys):
    """is_statue False for the characters named in `keys`, True for the rest."""
    return mock.patch.object(Character, "is_statue", new=property(lambda c: c.key not in keys))


class TestOneLinePerCharacter(EvenniaTest):
    """Names NM-T8 (K8, NM14): a line per awake character, with its pose."""

    def setUp(self):
        super().setUp()
        describe(self.char1, self.char2)
        self.char3 = create_object(Character, key="Char3", location=self.room1)
        describe(self.char3)
        self.char3.db.pose = "is warming her hands by the fire."

    def _characters(self, **kwargs):
        with _awake_all("Char", "Char2", "Char3"):
            return self.room1.get_display_characters(self.char1, **kwargs)

    def test_two_awake_characters_give_two_lines_with_their_poses(self):
        self.assertEqual(
            self._characters(),
            "\nA broad-shouldered man is here."
            "\nA freckled youth is warming her hands by the fire.")

    def test_no_heading_and_no_commas(self):
        text = self._characters()
        self.assertNotIn("Characters:", text)
        self.assertEqual(len(text.strip().splitlines()), 2)

    def test_the_viewer_is_not_listed(self):
        # The viewer reads their own key (rpsystem.py:1541), so a listed
        # viewer would show as "Char"; the fixture's lines hold no key.
        self.assertNotIn("Char", self._characters())

    def test_a_statue_is_under_you_see_and_not_on_a_line(self):
        with _awake_all("Char", "Char2"):
            characters = self.room1.get_display_characters(self.char1)
            things = self.room1.get_display_things(self.char1)
        self.assertEqual(characters, "\nA broad-shouldered man is here.")
        self.assertIn(f"stone statue of {shown(self.char3)}", things)
        self.assertNotIn("warming", things)  # a statue's pose is not shown

    def test_room_lists_false_is_empty(self):
        self.assertEqual(self._characters(**{room_text.LISTS_KWARG: False}), "")

    def test_no_one_awake_is_empty(self):
        with _awake_all("Char"):
            self.assertEqual(self.room1.get_display_characters(self.char1), "")

    def test_a_recog_gets_the_lines_capital_and_keeps_the_rest(self):
        # NM-T9 lock 1B (which replaced NM-T8's 2A): $You()'s rule -- the
        # first character up, the rest as its holder wrote it.
        self.char1.recog.add(self.char2, "liar of Kvarn")
        self.char1.recog.add(self.char3, "Tess")
        self.assertEqual(
            self._characters(),
            "\nLiar of Kvarn is here.\nTess is warming her hands by the fire.")

    def test_a_pose_kwarg_from_the_caller_does_not_raise(self):
        self.assertIn("is here.", self._characters(pose=False, ref="~"))

    def test_the_lines_reach_the_room_contents_message(self):
        with _awake_all("Char", "Char2", "Char3"):
            lists = room_text.contents_text(self.room1, self.char1)
        self.assertIn(
            "A broad-shouldered man is here.\n"
            "A freckled youth is warming her hands by the fire.\n"
            "|wYou see:|n", lists)
