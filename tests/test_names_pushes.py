"""
Tests for the room panel's pushes. Names, Task NM-T17
(docs/PolishedWorld_Combat_Decomposition.md §9; Names UP22).

WHAT IS PRESSURED
-----------------
- `recog`, `forget`: the reader's own panel, and no one else's (NMM26 pushes
  the room on `recog`; the no-other test must fail).
- `introduce`: one push per hearer whose recog was written; a hearer who
  kept their own name gets none.
- `pose` and `pose reset`: the room; `pose default` and a refused pose
  nothing.
- What is worn (lock 1 A): `wear` and `remove` in the garment's methods, and
  `cover` and `uncover` in the project's subclasses, forget the short
  description's memo and push the room -- so the reader gets the new text,
  not the one the memo held (NM-T15's `MEMO_SECONDS`). A refused `cover`
  pushes nothing. A gauge crossing pushes nothing (lock 1 A), so there is
  no site to test: the census in tests/test_client_state.py pins that no
  push sits in the fatigue or encumbrance readers.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_pushes
"""

from unittest import mock

from evennia import create_object
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from tests.names_fixture import describe, shown
from tests.test_client_state import ReactorMixin, _awake
from world import client_state

CHARACTER = "typeclasses.characters.Character"
CLOTHING = "typeclasses.clothing.ClothingWithBuffs"


def _commands():
    from commands import names_commands

    return names_commands


class _Pushes(EvenniaCommandTest):
    """
    char2 acts. char1, char3 and char4 are in the room and awake (the test
    patches `is_statue`, which reads the sessions tests do not have); char4
    is in another room. `push` and `push_room` are spies.
    """

    character_typeclass = CHARACTER
    AWAKE = ("Char", "Char2", "Char3")

    def setUp(self):
        super().setUp()
        from typeclasses.characters import Character

        self.char3 = create_object(CHARACTER, key="Char3", location=self.room1)
        self.char4 = create_object(CHARACTER, key="Char4", location=self.room2)
        describe(self.char1, self.char2, self.char3, self.char4)
        patcher = mock.patch.object(
            Character, "is_statue", new=property(lambda c: c.key not in self.AWAKE)
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_cmd(self, cmd, args):
        """Run `cmd` as char2; return (readers pushed `room`, rooms pushed)."""
        with mock.patch.object(client_state, "push") as push, \
                mock.patch.object(client_state, "push_room") as push_room:
            self.call(cmd, args, caller=self.char2)
        readers = [call.args[0] for call in push.call_args_list if "room" in call.args[1:]]
        rooms = [call.args[0] for call in push_room.call_args_list]
        return readers, rooms


class TestRecogAndForget(_Pushes):
    def test_recog_pushes_the_reader_and_no_other(self):
        readers, rooms = self.run_cmd(_commands().CmdRecog(), "freckled as Fred")
        self.assertEqual(self.char2.recog.get(self.char3), "Fred")  # receipt
        self.assertEqual(readers, [self.char2])
        self.assertEqual(rooms, [])

    def test_a_refused_recog_pushes_nothing(self):
        for args in ("nobody as Fred", "freckled as /", "me as Fred"):
            with self.subTest(args=args):
                self.assertEqual(self.run_cmd(_commands().CmdRecog(), args), ([], []))

    def test_the_list_pushes_nothing(self):
        self.assertEqual(self.run_cmd(_commands().CmdRecog(), ""), ([], []))

    def test_forget_pushes_the_reader_and_no_other(self):
        self.char2.recog.add(self.char3, "Fred")
        readers, rooms = self.run_cmd(_commands().CmdForget(), "Fred")
        self.assertIsNone(self.char2.recog.get(self.char3))  # receipt
        self.assertEqual(readers, [self.char2])
        self.assertEqual(rooms, [])

    def test_forget_from_another_room_pushes_the_reader(self):
        self.char2.recog.add(self.char4, "Ada")
        readers, _rooms = self.run_cmd(_commands().CmdForget(), "Ada")
        self.assertEqual(readers, [self.char2])

    def test_a_forget_that_finds_no_one_pushes_nothing(self):
        self.assertEqual(self.run_cmd(_commands().CmdForget(), "Fred"), ([], []))

    def test_the_reader_gets_the_name_in_the_panel(self):
        self.call(_commands().CmdRecog(), "freckled as Fred", caller=self.char2)
        names = [e["name"] for e in client_state.room_snapshot(self.room1, self.char2)["characters"]]
        self.assertIn("Fred", names)
        others = [e["name"] for e in client_state.room_snapshot(self.room1, self.char1)["characters"]]
        self.assertNotIn("Fred", others)


class TestIntroduce(_Pushes):
    def test_each_hearer_whose_recog_was_written(self):
        self.char1.recog.add(self.char2, "Liar")   # keeps their own name (NM5)
        readers, rooms = self.run_cmd(_commands().CmdIntroduce(), "")
        self.assertEqual(self.char3.recog.get(self.char2), "Char2")  # receipt
        self.assertEqual(readers, [self.char3])
        self.assertEqual(rooms, [])

    def test_both_hearers_without_a_name(self):
        readers, _rooms = self.run_cmd(_commands().CmdIntroduce(), "")
        self.assertCountEqual(readers, [self.char1, self.char3])

    def test_to_one_pushes_that_one(self):
        readers, rooms = self.run_cmd(_commands().CmdIntroduce(), "to freckled")
        self.assertEqual(readers, [self.char3])
        self.assertEqual(rooms, [])

    def test_a_failing_write_pushes_nothing_for_that_hearer(self):
        with mock.patch.object(self.char3.recog, "add", side_effect=RuntimeError("x")):
            readers, _rooms = self.run_cmd(_commands().CmdIntroduce(), "")
        self.assertEqual(readers, [self.char1])


class TestPose(_Pushes):
    def test_a_pose_pushes_the_room(self):
        readers, rooms = self.run_cmd(_commands().CmdPose(), "is sitting by the fire")
        self.assertEqual(self.char2.db.pose, "is sitting by the fire.")  # receipt
        self.assertEqual(rooms, [self.room1])
        self.assertEqual(readers, [])

    def test_reset_pushes_the_room(self):
        self.char2.db.pose = "is sitting by the fire."
        _readers, rooms = self.run_cmd(_commands().CmdPose(), "reset")
        self.assertEqual(self.char2.db.pose, "is here.")  # receipt
        self.assertEqual(rooms, [self.room1])

    def test_default_pushes_nothing(self):
        _readers, rooms = self.run_cmd(_commands().CmdPose(), "default is sitting.")
        self.assertEqual(self.char2.db.pose_default, "is sitting.")  # receipt
        self.assertEqual(rooms, [])

    def test_a_refused_pose_pushes_nothing(self):
        for args in ("is pointing at /nobody", "is " + "very " * 20 + "tall"):
            with self.subTest(args=args[:30]):
                self.assertEqual(self.run_cmd(_commands().CmdPose(), args), ([], []))

    def test_the_room_reads_the_pose_on_the_panel(self):
        self.call(_commands().CmdPose(), "is sitting by the fire", caller=self.char2)
        entries = client_state.room_snapshot(self.room1, self.char1)["characters"]
        self.assertIn({"name": shown(self.char2).capitalize(),
                       "pose": "is sitting by the fire."}, entries)


class TestTheCommandSet(EvenniaTest):
    def test_cover_and_uncover_are_the_projects(self):
        from commands.default_cmdsets import CharacterCmdSet

        names_commands = _commands()
        cmdset = CharacterCmdSet()
        cmdset.at_cmdset_creation()
        found = {cmd.key: type(cmd) for cmd in cmdset.commands}
        self.assertIs(found["cover"], names_commands.CmdCover)
        self.assertIs(found["uncover"], names_commands.CmdUncover)
        # the help text is the contrib's
        self.assertIn("Covers a worn item", names_commands.CmdCover.__doc__)
        self.assertIn("Reveals a worn item", names_commands.CmdUncover.__doc__)


# --------------------------------------------------------------------------
# What is worn (lock 1 A)
# --------------------------------------------------------------------------

class TestWorn(ReactorMixin, EvenniaCommandTest):
    """
    char1, puppeted, is a lean, grey-eyed woman of SIZ 11; char2 reads her
    and has a session. `push` is a spy that builds the snapshot each reader
    would get at that moment, so a stale memo shows as the old text.
    """

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        describe(self.char1, self.char2)
        self.char1.stats.siz.base = 11
        self.char1.db.appearance = {"sex": "female", "age": "adult", "feature": "grey-eyed"}
        self.char1.sdesc.forget()
        self.cloak = self._garment("cloak", "fullbody", "cloaked")
        self.tunic = self._garment("tunic", "top", "armoured")
        self.s2 = mock.Mock(name="session of Char2")

    def _garment(self, key, clothing_type, look_word):
        garment = create_object(CLOTHING, key=key, location=self.char1)
        garment.db.clothing_type = clothing_type
        garment.db.look_word = look_word
        return garment

    def _read(self):
        """What char2's panel shows for char1, as a frame built now would."""
        entries = client_state.room_snapshot(self.room1, self.char2)["characters"]
        return [e["name"] for e in entries]

    def act(self, action):
        """
        Fill the memo, run `action`, then the reactor; return the names char2
        read in each room frame pushed to char2, in order.
        """
        frames = []

        def spy(obj, *domains, **kwargs):
            if obj == self.char2 and "room" in domains:
                frames.append(self._read())

        with _awake(self.char2, self.s2):
            self.char1.sdesc.get()                     # the memo holds the old text
            with mock.patch.object(client_state, "push", side_effect=spy):
                action()
                self.reactor.run()
        return frames

    def test_wear_pushes_the_room_with_the_new_text(self):
        frames = self.act(lambda: self.cloak.wear(self.char1, True))
        self.assertEqual(frames, [["A cloaked, lean, grey-eyed woman"]])

    def test_remove_pushes_the_room_with_the_new_text(self):
        self.cloak.wear(self.char1, True)
        self.reactor.run()
        frames = self.act(lambda: self.cloak.remove(self.char1))
        self.assertEqual(frames, [["A lean, grey-eyed woman"]])

    def test_a_worn_garment_given_away(self):
        # at_post_move runs remove() quietly (L3.1): the giver's room is pushed
        self.cloak.wear(self.char1, True)
        self.reactor.run()
        frames = self.act(lambda: self.cloak.move_to(self.char2, quiet=True))
        self.assertEqual(frames[-1:], [["A lean, grey-eyed woman"]])

    def test_cover_and_uncover_push_the_room_with_the_new_text(self):
        self.tunic.wear(self.char1, True)
        self.cloak.wear(self.char1, True)
        self.reactor.run()
        frames = self.act(lambda: self.call(_commands().CmdCover(), "cloak with tunic"))
        self.assertEqual(self.cloak.db.covered_by, self.tunic)  # receipt
        self.assertEqual(frames, [["An armoured, lean, grey-eyed woman"]])
        frames = self.act(lambda: self.call(_commands().CmdUncover(), "cloak"))
        self.assertFalse(self.cloak.db.covered_by)  # receipt
        self.assertEqual(frames, [["A cloaked, lean, grey-eyed woman"]])

    def test_a_refused_cover_or_uncover_pushes_nothing(self):
        self.cloak.wear(self.char1, True)
        self.reactor.run()
        for cmd, args in ((_commands().CmdCover(), "cloak with cloak"),
                          (_commands().CmdCover(), "cloak"),
                          (_commands().CmdUncover(), "cloak")):
            with self.subTest(args=args):
                self.assertEqual(self.act(lambda: self.call(cmd, args)), [])

    def test_a_layer_reader_that_raises_pushes_nothing(self):
        self.tunic.wear(self.char1, True)
        self.cloak.wear(self.char1, True)
        self.call(_commands().CmdCover(), "cloak with tunic")
        self.reactor.run()
        with mock.patch.object(_commands(), "get_worn_clothes", side_effect=RuntimeError("x")):
            frames = self.act(lambda: self.call(_commands().CmdUncover(), "cloak"))
        self.assertFalse(self.cloak.db.covered_by)  # receipt: the uncover itself ran
        self.assertEqual(frames, [])
