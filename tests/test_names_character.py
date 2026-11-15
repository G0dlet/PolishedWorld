"""
Tests for the character taking the rpsystem contrib. Names, Task NM-T2
(docs/PolishedWorld_Combat_Decomposition.md, NM2, NM3, NM11).

WHAT EACH CLASS PUTS PRESSURE ON
--------------------------------
* TestClassOrder -- `ContribRPCharacter` is last of the three bases, so the
  project's hooks and the clothing contrib's resolve first and the contrib's
  `get_search_result` and display come from it (NM2). The order is asserted by
  name: a reorder that still "works" changes which `get_display_name` wins.
* TestTheContribsCmdsetIsOff -- `ContribRPCharacter.at_object_creation` adds
  `RPSystemCmdSet` persistently (rpsystem.py:1565); it carries `sdesc` and
  `mask`, which players must not have (NM3, UP2, UP9). The set is stored by
  path in `cmdset_storage`, so the test reloads the handler from storage the way
  a server reload does (OQ-NM2).
* TestDisplayName -- what each kind of viewer reads: a stranger the short
  description, a recogniser the recog, oneself the key, `None` the short
  description. No colour code in any of them (NM11). A capital (`ref="t"`)
  is `$You()`'s for both, the first character up and the rest as written
  (NM-T9 lock 1B).
* TestYouCapitalises -- `$You()` capitalises a name at the start of a line only
  if the name starts with a letter (funcparser_callable_you, `name[:1].upper()`);
  the contrib's `|b` stopped it. This is the reason NM11 exists.
* TestStatue -- the statue wraps the same per-viewer name.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_character
"""

from unittest import mock

from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character


SDESC = "a weathered woman"


class _Named(EvenniaTest):
    """char1 (puppeted, Developer) has a short description; char2 looks."""

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.char1.sdesc.add(SDESC)


class TestClassOrder(EvenniaTest):
    def test_the_bases_resolve_in_this_order(self):
        names = [klass.__name__ for klass in Character.__mro__[:7]]
        self.assertEqual(
            names,
            [
                "Character",
                "ObjectParent",
                "ClothedCharacter",
                "ContribRPCharacter",
                "DefaultCharacter",
                "ContribRPObject",
                "DefaultObject",
            ],
        )


class TestTheContribsCmdsetIsOff(EvenniaTest):
    character_typeclass = "typeclasses.characters.Character"

    def _keys(self, char):
        return [cmdset.key for cmdset in char.cmdset.all()]

    def test_a_new_character_has_no_rpsystem_cmdset(self):
        self.assertNotIn("rpsystem_cmdset", self._keys(self.char1))
        self.assertFalse(
            any("rpsystem" in str(path) for path in self.char1.cmdset_storage or [])
        )

    def test_it_stays_off_after_the_handler_reloads_from_storage(self):
        # OQ-NM2: what a server reload does to an object's command sets.
        self.char1.cmdset.update(init_mode=True)
        self.assertNotIn("rpsystem_cmdset", self._keys(self.char1))

    def test_sdesc_and_mask_are_not_commands(self):
        heard = []
        with mock.patch.object(self.char1, "msg", side_effect=lambda *a, **k: heard.append(
            str(a[0]) if a else str(k.get("text"))
        )):
            for line in ("sdesc a tall stranger", "mask a hooded figure"):
                self.char1.execute_cmd(line, session=self.session)
        said = "\n".join(heard)
        # Evennia echoes the whole line it could not match.
        self.assertIn("Command 'sdesc a tall stranger' is not available", said)
        self.assertIn("Command 'mask a hooded figure' is not available", said)
        self.assertEqual(self.char1.sdesc.get(), "A normal person")


class TestDisplayName(_Named):
    def test_a_stranger_reads_the_short_description(self):
        self.assertEqual(self.char1.get_display_name(self.char2), SDESC)

    def test_a_recogniser_reads_the_recog(self):
        self.char2.recog.add(self.char1, "Mia")
        self.assertEqual(self.char1.get_display_name(self.char2), "Mia")

    def test_oneself_reads_the_key(self):
        self.assertEqual(self.char1.get_display_name(self.char1), self.char1.key)

    def test_no_looker_reads_the_short_description(self):
        self.assertEqual(self.char1.get_display_name(None), SDESC)

    def test_the_contribs_case_markers_still_apply(self):
        # `ref` is how an emote's `/Tall` asks for a capital (rpsystem.py:1612).
        self.assertEqual(
            self.char1.get_display_name(self.char2, ref="#0t"), "A weathered woman"
        )
        self.assertEqual(
            self.char1.get_display_name(self.char2, ref="#0^"), "A WEATHERED WOMAN"
        )

    def test_a_recog_gets_the_capital_a_line_start_asks_for(self):
        # NM-T9 lock 1B: one rule at the start of a line, $You()'s -- the
        # first character up, the rest as written (funcparser.py:1270-1272).
        self.char2.recog.add(self.char1, "mia of the Ford")
        self.assertEqual(
            self.char1.get_display_name(self.char2, ref="#0t"), "Mia of the Ford"
        )

    def test_a_recog_is_otherwise_as_written(self):
        # Only the capital is asked for; `/mia` (v) or `/MIA` (^) in an emote
        # does not rewrite what a player chose to call someone.
        self.char2.recog.add(self.char1, "mia of the Ford")
        for ref in ("#0v", "#0^", "#0~", "#0"):
            with self.subTest(ref=ref):
                self.assertEqual(
                    self.char1.get_display_name(self.char2, ref=ref), "mia of the Ford"
                )

    def test_the_capital_leaves_the_rest_of_a_description_as_written(self):
        self.char1.sdesc.add("a woman from Kvarn")
        self.assertEqual(
            self.char1.get_display_name(self.char2, ref="#0t"), "A woman from Kvarn"
        )

    def test_a_line_start_reads_as_you_writes_it(self):
        # The same name at the start of a line whether `$You()` or `ref="t"`
        # asks for it (NM-T9 lock 1B): a description with a proper noun for a
        # stranger, a lower-case recog for a recogniser.
        def you_line():
            others = [o for o in self.room1.contents if o != self.char2]
            with mock.patch.object(self.char2, "msg") as msg:
                self.room1.msg_contents("$You() waits.", from_obj=self.char1, exclude=others)
            return msg.call_args.kwargs["text"][0]

        self.char1.sdesc.add("a woman from Kvarn")
        for recog in (None, "mia"):
            if recog:
                self.char2.recog.add(self.char1, recog)
            with self.subTest(recog=recog):
                self.assertEqual(
                    you_line(), f"{self.char1.get_display_name(self.char2, ref='t')} waits.")
        self.assertEqual(you_line(), "Mia waits.")  # receipt: the recog was read

    def test_no_colour_code_for_any_viewer(self):
        self.char2.recog.add(self.char1, "Mia")
        shown = [
            self.char1.get_display_name(self.char2),
            self.char1.get_display_name(self.char1),
            self.char2.get_display_name(self.char1),
            self.char1.get_display_name(None),
        ]
        for name in shown:
            with self.subTest(name=name):
                self.assertNotIn("|b", name)
                self.assertNotIn("|m", name)


class TestYouCapitalises(_Named):
    def test_a_short_description_is_capitalised_at_the_start_of_a_line(self):
        with mock.patch.object(self.char2, "msg") as heard:
            self.room1.msg_contents("$You() $conj(wave).", from_obj=self.char1)
        # msg_contents sends text=(message, kwargs) (objects.py, msg_contents).
        text = heard.call_args.kwargs["text"]
        text = text[0] if isinstance(text, tuple) else text
        self.assertEqual(text, "A weathered woman waves.")


class TestStatue(_Named):
    def test_the_statue_wraps_the_name_its_viewer_reads(self):
        # char2 has no account, so it is a statue (Character.is_statue).
        self.char2.sdesc.add("a broad-shouldered man")
        self.assertEqual(
            self.char2.get_display_name(self.char1), "|wstone statue of a broad-shouldered man|n"
        )
        self.char1.recog.add(self.char2, "Tor")
        self.assertEqual(self.char2.get_display_name(self.char1), "|wstone statue of Tor|n")
