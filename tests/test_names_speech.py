"""
Tests for `say`, `emote`, `pose` and `whisper` under the rpsystem contrib.
Names, Task NM-T7 (docs/PolishedWorld_Combat_Decomposition.md, NM3, NM14;
Names note K7, UP19, UP20; OQ-NM8).

WHAT IS THE CONTRIB'S AND WHAT IS THE PROJECT'S
-----------------------------------------------
`emote`, `say` and `pose` are the contrib's (rpsystem.py:903, :946, :1022),
subclassed in commands/names_commands.py and added to CharacterCmdSet, where
they replace Evennia's `say` and `pose` (whose aliases were `:` and `emote`)
by key and alias (K7). The subclasses change two things, both run
2026-11-15: the contrib's parser leaves `/N` of a numbered reference in the
text (*nods to /2a tall man.*, rpsystem.py:426-431, also on Evennia's `main`),
which `parse_emote` removes (lock 1 C, TestTheLeftoverNumber); and its pose
does not catch the parser's EmoteError (`:1104`), so a bad reference was a
traceback.

THE PARSER IS TAKEN AS IT IS (OQ-NM8, lock A, Adam 2026-11-15)
--------------------------------------------------------------
The contrib's emote parser lists a person once per name the emoter has for
them -- a recog and a short description are two rows (rpsystem.py:383-395) --
and counts `N-` in that list, so with *Tall Tom* recognised and *a tall woman*
beside him, `/2-tall` is Tom again; a number past the end gives the last.
Run 2026-11-15. An emote changes nothing in the game, and the numbers its
error offers are the numbers it takes, so the parser is not forked.
TestTheParserAsItIs pins it: if Evennia changes it, these tests say so.

WHISPER (lock 2 A)
------------------
The contrib's `at_pre_say` wraps any speech as `/Me says, "..."` or
`/Me whispers "..."` for its own emote-based say. Evennia's `whisper` goes
through the same hook but does not parse emotes, so since NM-T2 a whisper
arrived as `X whispers: "/Me whispers "hello""` (run). Character.at_pre_say
returns a whisper as it is; Evennia's at_say already names the whisperer
per receiver -- but without a capital, so Character.at_say writes a
whisper's two lines itself, the receiver's name asked for as a sentence
start (`ref="t"`).

A POSE IS LEFT AT THE DOOR (UP19, NM14)
--------------------------------------
Every move with hooks resets the pose to the default (`pose_default`, *is
here.*), and so does death's relocation, which runs without hooks.

`is_statue` is patched to False: tests have no sessions, and a statue's name
is wrapped (*stone statue of ...*).

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_speech
"""

from unittest import mock

from evennia import create_object
from evennia.utils import ansi
from evennia.utils.test_resources import EvenniaCommandTest

from tests.names_fixture import describe

CHARACTER = "typeclasses.characters.Character"


def _cmd(name):
    from commands import default_cmdsets

    cmdset = default_cmdsets.CharacterCmdSet()
    cmdset.at_cmdset_creation()
    for cmd in cmdset.commands:
        if cmd.key == name:
            return cmd.__class__()
    raise AssertionError(f"no {name!r} in CharacterCmdSet")


class _Speech(EvenniaCommandTest):
    """char2 speaks. char1 and char3 listen; char3 is a stranger to char2."""

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        from typeclasses.characters import Character

        patcher = mock.patch.object(Character, "is_statue", new=property(lambda c: False))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.char3 = create_object(CHARACTER, key="Char3", location=self.room1)
        describe(self.char1, self.char2, self.char3)
        for char in (self.char1, self.char3):
            char.msg = mock.Mock()

    def run_as(self, name, args, caller=None):
        return self.call(_cmd(name), args, caller=caller or self.char2)

    def lines(self, char):
        out = []
        for call in char.msg.call_args_list:
            text = call.kwargs.get("text")
            text = text[0] if isinstance(text, tuple) else text
            if text:
                out.append(ansi.strip_ansi(text))
        return out


class TestTheCommandSet(_Speech):
    def _commands(self):
        from commands.default_cmdsets import CharacterCmdSet

        cmdset = CharacterCmdSet()
        cmdset.at_cmdset_creation()
        return cmdset.commands

    def test_say_emote_and_pose_are_the_projects_on_the_contribs(self):
        from evennia.contrib.rpg.rpsystem import rpsystem

        by_key = {cmd.key: cmd for cmd in self._commands()}
        for key, contrib in (
            ("say", rpsystem.CmdSay),
            ("emote", rpsystem.CmdEmote),
            ("pose", rpsystem.CmdPose),
        ):
            with self.subTest(key=key):
                self.assertEqual(by_key[key].__module__, "commands.names_commands")
                self.assertIsInstance(by_key[key], contrib)

    def test_evennias_pose_is_gone_and_colon_is_emote(self):
        general = [
            cmd.key
            for cmd in self._commands()
            if cmd.__module__ == "evennia.commands.default.general" and cmd.key in ("pose", "say")
        ]
        self.assertEqual(general, [])
        owners = [cmd.key for cmd in self._commands() if ":" in cmd.aliases]
        self.assertEqual(owners, ["emote"])

    def test_the_contribs_sdesc_and_mask_are_not_added(self):
        keys = {cmd.key for cmd in self._commands()}
        self.assertNotIn("sdesc", keys)
        self.assertNotIn("mask", keys)


class TestSay(_Speech):
    def test_a_stranger_reads_the_description_a_recogniser_the_label(self):
        self.char1.recog.add(self.char2, "Bob")
        self.run_as("say", "hello")
        self.assertEqual(self.lines(self.char3), ['A broad-shouldered man says, "hello"'])
        self.assertEqual(self.lines(self.char1), ['Bob says, "hello"'])

    def test_no_key_reaches_a_stranger(self):
        self.run_as("say", "hello")
        self.assertNotIn("Char2", " ".join(self.lines(self.char3)))


class TestEmote(_Speech):
    def test_the_third_person_is_named_per_reader(self):
        self.char1.recog.add(self.char3, "Mia")
        self.run_as("emote", "waves at /freckled.")
        self.assertEqual(
            self.lines(self.char1), ["A broad-shouldered man waves at Mia."]
        )

    def test_a_failed_reference_tells_only_the_emoter(self):
        said = self.run_as("emote", "waves at /purple.")
        self.assertIn("No match for", said)
        self.assertEqual(self.lines(self.char1), [])
        self.assertEqual(self.lines(self.char3), [])


class TestTheParserAsItIs(_Speech):
    """OQ-NM8, lock A: the contrib's counting, pinned (run 2026-11-15)."""

    def setUp(self):
        super().setUp()
        self.char4 = create_object(CHARACTER, key="Char4", location=self.room1)
        self.char4.msg = mock.Mock()
        self.char3.sdesc.add("a tall man")
        self.char4.sdesc.add("a tall woman")
        self.char2.recog.add(self.char3, "Tall Tom")

    def test_a_recognised_person_is_listed_twice(self):
        said = self.run_as("emote", "nods to /tall.")
        self.assertIn("1-tall (Tall Tom)", said)
        self.assertIn("2-tall (tall man)", said)
        self.assertIn("3-tall (tall woman)", said)

    def test_two_is_the_same_person_as_one(self):
        self.run_as("emote", "nods to /2-tall.")
        self.assertEqual(self.lines(self.char1), ["A broad-shouldered man nods to a tall man."])

    def test_three_is_the_next_person_and_past_the_end_is_the_last(self):
        for args in ("nods to /3-tall.", "nods to /9-tall."):
            with self.subTest(args=args):
                self.char1.msg.reset_mock()
                self.run_as("emote", args)
                self.assertEqual(
                    self.lines(self.char1), ["A broad-shouldered man nods to a tall woman."]
                )


class TestTheLeftoverNumber(_Speech):
    """
    Lock 1 C: the contrib's parser leaves `/N` of a numbered reference in the
    text (rpsystem.py:426-431; run 2026-11-15). parse_emote removes it.
    """

    def setUp(self):
        super().setUp()
        self.char4 = create_object(CHARACTER, key="Char4", location=self.room1)
        self.char4.msg = mock.Mock()
        self.char3.sdesc.add("a tall man")
        self.char4.sdesc.add("a tall woman")

    def test_the_contrib_alone_leaves_it(self):
        from evennia.contrib.rpg.rpsystem.rpsystem import parse_sdescs_and_recogs

        text, _ = parse_sdescs_and_recogs(self.char2, self.room1.contents, "nods to /2-tall.")
        self.assertRegex(text, r"/2\{#[0-9]+v?\}")

    def test_a_numbered_reference_reads_clean(self):
        for args, name in (("nods to /1-tall.", "a tall man"), ("nods to /2-tall.", "a tall woman")):
            with self.subTest(args=args):
                self.char1.msg.reset_mock()
                self.run_as("emote", args)
                self.assertEqual(self.lines(self.char1), [f"A broad-shouldered man nods to {name}."])

    def test_two_numbered_references(self):
        self.run_as("emote", "points at /2-tall, then at /1-tall.")
        self.assertEqual(
            self.lines(self.char1),
            ["A broad-shouldered man points at a tall woman, then at a tall man."],
        )

    def test_a_capital_on_a_numbered_reference(self):
        # /me names the emoter, so the contrib does not add them first.
        self.run_as("emote", "/2-Tall nods to /me.")
        self.assertEqual(
            self.lines(self.char1), ["A tall woman nods to a broad-shouldered man."]
        )

    def test_a_pose_stores_no_number(self):
        self.run_as("pose", "is talking to /2-tall")
        self.assertEqual(self.char2.db.pose, "is talking to a tall woman.")


class TestPose(_Speech):
    def test_the_pose_shows_with_the_name(self):
        self.run_as("pose", "is warming his hands")
        self.assertEqual(self.char2.db.pose, "is warming his hands.")
        self.assertIn(
            "a broad-shouldered man is warming his hands.",
            ansi.strip_ansi(self.char2.get_display_name(self.char1, pose=True)),
        )

    def test_a_reference_that_matches_no_one_is_a_line(self):
        self.char2.db.pose = "is here."
        said = self.run_as("pose", "is looking at /nobody")
        self.assertIn("No match for", said)
        self.assertEqual(self.char2.db.pose, "is here.")

    def test_a_move_resets_it_to_the_default(self):
        self.run_as("pose", "is warming his hands")
        for move_type in ("traverse", "teleport", "move"):
            with self.subTest(move_type=move_type):
                self.char2.db.pose = "is warming his hands."
                self.char2.move_to(
                    self.room2 if self.char2.location == self.room1 else self.room1,
                    quiet=True,
                    move_type=move_type,
                )
                self.assertEqual(self.char2.db.pose, "is here.")

    def test_death_resets_it_too(self):
        self.char2.db.pose = "is warming his hands."
        self.char2.at_character_death()
        self.assertEqual(self.char2.db.pose, "is here.")

    def test_a_character_without_a_default_gets_an_empty_pose(self):
        self.char2.attributes.remove("pose_default")
        self.char2.db.pose = "is warming his hands."
        self.char2.move_to(self.room2, quiet=True)
        self.assertEqual(self.char2.db.pose, "")


class TestWhisper(_Speech):
    def test_the_receiver_reads_the_words_and_no_key(self):
        said = self.run_as("whisper", "freckled = hello there")
        self.assertEqual(
            self.lines(self.char3), ['A broad-shouldered man whispers: "hello there"']
        )
        self.assertNotIn("/Me", said)
        self.assertIn('You whisper to a freckled youth, "hello there"', said)

    def test_a_recogniser_reads_their_label(self):
        self.char3.recog.add(self.char2, "Bob")
        self.run_as("whisper", "freckled = hello")
        self.assertEqual(self.lines(self.char3), ['Bob whispers: "hello"'])

    def test_the_room_hears_nothing(self):
        self.run_as("whisper", "freckled = hello")
        self.assertEqual(self.lines(self.char1), [])
