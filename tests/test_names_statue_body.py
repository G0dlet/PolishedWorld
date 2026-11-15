"""
The statue and the body are named as the looker knows the person. Names,
Task NM-T11 (docs/PolishedWorld_Combat_Decomposition.md; the Names note's
K2, K3).

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
The statue (K2). A character with no account is a statue, and its display
name says so (*stone statue of ...*). Its own lines need the person without
the stone: `Character.living_name`. *turns to weathered stone* is sent when
the character already is a statue (`at_post_unpuppet` runs after the
account has let go), so it names the sleeper through `$Your(sleeper)` and a
mapping that answers with the living name (lock 1 A); *has entered the game*
and *The stone form of ... stirs* are sent when the account is back, through
`$You()` (lock 2 A). The statue's look names the person by `living_name`.

The body (K3). A player's corpse is keyed `corpse`, aliased `body`, and
named *the body of <the owner as the looker knows them>* (lock 3 B); its
owner reads *your body* (lock 4 B), and a body whose owner is gone is *a
body*. The name holds while the owner is a statue, which is most of the
time anyone finds a body.

The readers are `test_names_room_messages._Readers`: char3, a stranger, and
char4, who knows char1 as *mia of the Ford* -- lower-case, so `$You()`'s
capital and a plain format differ.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_statue_body
"""

from evennia import create_object
from evennia.commands.default.general import CmdLook
from evennia.contrib.game_systems.containers.containers import CmdContainerGet
from evennia.utils import ansi
from evennia.utils.test_resources import EvenniaCommandTest

from tests.names_fixture import shown
from tests.test_names_room_messages import LABEL, SEEN_BY_LABEL, _Readers
from typeclasses.corpse import PlayerCorpse
from world import death_contract, room_text

OBJECT = "typeclasses.objects.Object"
STRANGER_SEES = "A weathered woman"   # char1 at the start of a line, for char3


class TestStatueLines(_Readers, EvenniaCommandTest):
    def _logout(self):
        self.account.unpuppet_object(self.session)
        self.assertTrue(self.char1.is_statue)  # receipt: the line came from a statue

    def test_turns_to_stone(self):  # Character.at_post_unpuppet
        self._logout()
        rest = "body slowly turns to weathered stone, their final pose frozen in place."
        self.assert_read(rest, stranger=f"{STRANGER_SEES}'s {rest}",
                         recogniser=f"{SEEN_BY_LABEL}'s {rest}")

    def test_enters_and_stirs(self):  # Character.at_post_puppet
        self._logout()
        for reader in (self.char3, self.char4):
            reader.msg.reset_mock()
        self.account.puppet_object(self.session, self.char1)
        self.assert_read("has entered the game.")
        rest = "stirs, color flowing back into their flesh as they draw breath."
        self.assert_read(rest, stranger=f"The stone form of {shown(self.char1)} {rest}",
                         recogniser=f"The stone form of {LABEL} {rest}")

    def test_the_statue_is_looked_at(self):  # Character.return_appearance
        self._logout()
        for reader, name in ((self.char3, shown(self.char1)), (self.char4, LABEL)):
            with self.subTest(reader=reader.key):
                seen = ansi.strip_ansi(self.char1.return_appearance(reader))
                self.assertIn(f"A weathered stone statue depicting {name}.", seen)
                self.assertNotIn("Char", seen)


class _Body(_Readers, EvenniaCommandTest):
    """char1 dies in room1 and respawns in room2; its body stays in room1."""

    def setUp(self):
        super().setUp()
        self.char1.db.respawn_location = self.room2
        self.knife = create_object(OBJECT, key="flint knife", location=self.char1)
        self.char1.at_character_death()
        self.body = self.bodies()[-1]

    def bodies(self):
        return [obj for obj in self.room1.contents if isinstance(obj, PlayerCorpse)]


class TestBodyNamed(_Body):
    def test_keyed_corpse_aliased_body(self):
        self.assertEqual(self.body.key, "corpse")
        self.assertIn("body", self.body.aliases.all())
        self.assertEqual(self.knife.location, self.body)  # receipt: the death dropped it

    def test_each_reader_reads_their_own_name(self):
        for reader, expected in ((self.char3, f"the body of {shown(self.char1)}"),
                                 (self.char4, f"the body of {LABEL}"),
                                 (self.char1, "your body")):
            with self.subTest(reader=reader.key):
                self.assertEqual(self.body.get_display_name(reader), expected)

    def test_the_owner_asleep_is_not_stone(self):
        self.account.unpuppet_object(self.session)
        self.assertTrue(self.char1.is_statue)
        self.assertEqual(self.body.get_display_name(self.char3), f"the body of {shown(self.char1)}")

    def test_listed_in_the_room(self):
        for reader, expected in ((self.char3, f"the body of {shown(self.char1)}"),
                                 (self.char4, f"the body of {LABEL}")):
            with self.subTest(reader=reader.key):
                names = room_text.numbered_names(self.bodies(), reader)
                self.assertEqual(names, [expected])

    def test_listing_leaves_no_alias(self):
        # Evennia's get_numbered_name stores each reader's form as an alias,
        # which would make a recog searchable by anyone (lock 3 B).
        room_text.numbered_names(self.bodies(), self.char4)
        self.assertNotIn(f"the body of {LABEL}", self.body.aliases.all())
        self.assertFalse(self.body.search(LABEL, candidates=[self.body], quiet=True))

    def test_the_key_names_nobody(self):
        found = self.char3.search("corpse of Char", candidates=self.room1.contents, quiet=True)
        self.assertFalse(found)

    def test_a_body_whose_owner_is_gone(self):
        gone = create_object(PlayerCorpse, key="corpse", aliases=["body"], location=self.room1,
                             attributes=[("owner", 999_999)])
        self.assertEqual(gone.get_display_name(self.char3), "a body")
        self.assertEqual(room_text.numbered_names([gone], self.char3), ["a body"])


class TestTwoBodies(_Body):
    def test_two_of_one_person_are_counted(self):
        self.char1.move_to(self.room1, quiet=True, move_hooks=False)
        self.char1.at_character_death()
        self.assertEqual(len(self.bodies()), 2)
        names = room_text.numbered_names(self.bodies(), self.char3)
        self.assertEqual(names, [f"two bodies of {shown(self.char1)}"])

    def test_told_apart_by_number(self):
        self.char2.at_character_death()
        self.assertEqual(len(self.bodies()), 2)
        seen = set()
        for number in (1, 2):
            out = self.call(CmdLook(), f"{number}-corpse", caller=self.char3)
            seen.add(out.splitlines()[0])
        self.assertEqual(seen, {f"the body of {shown(self.char1)}",
                                f"the body of {shown(self.char2)}"})


class TestTakingBack(_Body):
    def test_the_owner_takes_from_the_corpse(self):
        self.char1.move_to(self.room1, quiet=True, move_hooks=False)
        self.call(CmdContainerGet(), "flint knife from corpse", caller=self.char1)
        self.assertEqual(self.knife.location, self.char1)

    def test_the_help_names_the_corpse(self):
        text = death_contract.help_text()
        self.assertIn("get <item> from corpse|n", text)
        self.assertNotIn("<your name>", text)
