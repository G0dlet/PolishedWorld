"""
The short description is composed live from body, state and garment, and
staff set the facts with `@appearance`. Names, Task NM-T15
(docs/PolishedWorld_Combat_Decomposition.md; OQ-NM9; the Names note's UP1,
UP2, UG4).

WHAT EACH TEST PUTS PRESSURE ON
-------------------------------
TestVocabulary is pure: every combination of the vocabulary, the state words
and the prototypes' garment words is composed and checked against the length,
the core that is never dropped, and the drop order -- a word is dropped only
when the text would not fit with it (NMM23). TestComposed reads a character:
the outermost uncovered garment, the hood, the two state readers at their
thresholds, the search. TestMemo counts compositions for one room line to
many readers and after `MEMO_SECONDS` (NMM28). TestAppearanceCommand drives
`@appearance`. TestNameToType is lock 2 A: the word of the fixed core.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_names_sdesc
"""

import itertools
from unittest import mock

from evennia import create_object
from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import EvenniaCommandTest, EvenniaTest

from commands.admin_commands import CmdAppearance
from tests.names_fixture import describe, shown
from world import names, prototypes
from world import sdesc as sdesc_rules
from world.sdesc import compose_text

CHARACTER = "typeclasses.characters.Character"
OBJECT = "typeclasses.objects.Object"
CLOTHING = "typeclasses.clothing.ClothingWithBuffs"

# Every garment word a prototype carries, read from the prototypes module.
GARMENT_WORDS = sorted(
    {value["look_word"] for value in vars(prototypes).values()
     if isinstance(value, dict) and value.get("look_word")}
)
# One SIZ from each band, and one past each end.
SIZES = sorted({lowest for lowest, _ in sdesc_rules.BUILDS} | {6, 7, 19, 3})


def _appear(char, sex="female", age="adult", feature="grey-eyed"):
    char.db.appearance = {"sex": sex, "age": age, "feature": feature}
    char.sdesc.forget()


def _garment(holder, key, clothing_type, look_word=None, conceals=None):
    garment = create_object(CLOTHING, key=key, location=holder)
    garment.db.clothing_type = clothing_type
    if look_word:
        garment.db.look_word = look_word
    if conceals:
        garment.db.conceals = conceals
    return garment


def _expected(state, garment, build, core, noun):
    """The drop order written out: the first that fits."""
    for kept in ((state, garment, build), (state, garment, None), (state, None, None),
                 (None, None, None)):
        words = [w for w in (*kept, core) if w]
        text = f"{sdesc_rules.article(words[0])} {', '.join(words)} {noun}"
        if len(text) <= sdesc_rules.MAX_LENGTH:
            return text
    return text


class TestVocabulary(EvenniaTest):
    def test_every_combination_fits_and_drops_in_order(self):
        self.assertTrue(GARMENT_WORDS)  # receipt: the prototypes were read
        count = 0
        for (sex, age), feature, siz, state, garment, hooded in itertools.product(
            sdesc_rules.NOUNS, sdesc_rules.FEATURES, SIZES,
            (None,) + sdesc_rules.STATE_WORDS, [None] + GARMENT_WORDS, (False, True),
        ):
            text = compose_text(sex, age, feature, siz, state=state, garment=garment,
                                hooded=hooded)
            core = sdesc_rules.HOODED if hooded else feature
            noun = sdesc_rules.NOUNS[(sex, age)]
            expected = _expected(state, garment, sdesc_rules.build_for(siz), core, noun)
            if text != expected:
                self.fail(f"{text!r} != {expected!r}")
            if len(text) > sdesc_rules.MAX_LENGTH or not text.endswith(f"{core} {noun}"):
                self.fail(f"{text!r}")
            count += 1
        self.assertGreater(count, 30000)

    def test_the_core_alone_fits_without_a_drop(self):
        for (sex, age), feature, siz, hooded in itertools.product(
            sdesc_rules.NOUNS, sdesc_rules.FEATURES, SIZES, (False, True)
        ):
            text = compose_text(sex, age, feature, siz, hooded=hooded)
            self.assertIn(sdesc_rules.build_for(siz), text.split(", ")[0])

    def test_the_drop_order(self):
        self.assertEqual(
            compose_text("male", "adult", "grey-eyed", 16, "haggard", "cloaked"),
            "a haggard, cloaked, grey-eyed man",   # 43 with *heavyset*
        )
        self.assertEqual(
            compose_text("female", "old", "black-bearded", 16, "burdened", "bone-clad"),
            "a burdened, black-bearded old woman",  # 46 with *bone-clad*
        )
        self.assertEqual(
            compose_text("male", "adult", "grey-eyed", 10, "haggard", "cloaked"),
            "a haggard, cloaked, lean, grey-eyed man",
        )

    def test_the_article(self):
        self.assertEqual(compose_text("male", "adult", "pale", 11, garment="armoured"),
                         "an armoured, lean, pale man")
        self.assertEqual(compose_text("male", "adult", "pale", 11), "a lean, pale man")
        for word in (sdesc_rules.FEATURES + sdesc_rules.STATE_WORDS + tuple(GARMENT_WORDS)
                     + tuple(w for _, w in sdesc_rules.BUILDS)):
            with self.subTest(word=word):
                self.assertNotRegex(word, r"^(one|uni|eu|hour|honest)")

    def test_the_build_from_siz(self):
        self.assertEqual([sdesc_rules.build_for(s) for s in (6, 7, 8, 11, 12, 15, 16, 18, 21)],
                         ["slight", "slight", "small", "lean", "sturdy", "broad", "heavyset",
                          "hulking", "hulking"])

    def test_the_same_input_gives_the_same_text(self):
        args = ("unstated", "old", "scarred", 11, "burdened", "robed")
        self.assertEqual(compose_text(*args), compose_text(*args))
        self.assertEqual(compose_text(*args), "a burdened, robed, lean, scarred figure")

    def test_a_fact_outside_the_vocabulary_raises(self):
        for args in (("other", "adult", "pale"), ("male", "ancient", "pale"),
                     ("male", "adult", "purple")):
            with self.subTest(args=args), self.assertRaises(ValueError):
                compose_text(*args, 10)

    def test_the_prototypes(self):
        self.assertEqual(spawn("fur_cloak")[0].db.look_word, "cloaked")
        self.assertEqual(spawn("robe")[0].db.look_word, "robed")
        self.assertEqual(spawn("linen_cuirass")[0].db.look_word, "armoured")
        self.assertEqual(spawn("bone_armour")[0].db.look_word, "bone-clad")
        self.assertIsNone(spawn("wool_tunic")[0].db.look_word)
        self.assertIn("feature", spawn("hood")[0].db.conceals)


class _Composed(EvenniaTest):
    """char1 a grey-eyed woman of SIZ 11 (*lean*); char2 looks and searches."""

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        describe(self.char1, self.char2)
        self.char1.stats.siz.base = 11
        _appear(self.char1)

    def read(self):
        self.char1.sdesc.forget()
        return self.char1.sdesc.get()


class TestComposed(_Composed):
    def test_the_core(self):
        self.assertEqual(self.read(), "a lean, grey-eyed woman")
        self.assertEqual(self.char1.get_display_name(self.char2), "a lean, grey-eyed woman")

    def test_no_facts_gives_the_stored_text(self):
        self.char1.attributes.remove("appearance")
        self.assertEqual(self.read(), shown(self.char1))

    def test_a_new_character_reads_the_placeholder(self):
        new = create_object(CHARACTER, key="Newcomer", location=self.room1)
        self.assertEqual(new.sdesc.get(), "a quiet traveller")

    def test_the_cloak_over_the_tunic(self):
        _garment(self.char1, "wool tunic", "top").wear(self.char1, True, quiet=True)
        self.assertEqual(self.read(), "a lean, grey-eyed woman")   # the tunic has no word
        _garment(self.char1, "fur cloak", "fullbody", "cloaked").wear(self.char1, True, quiet=True)
        self.assertEqual(self.read(), "a cloaked, lean, grey-eyed woman")

    def test_a_covered_garment_does_not_show(self):
        robe = _garment(self.char1, "robe", "fullbody", "robed")
        cuirass = _garment(self.char1, "linen cuirass", "armour_padding", "armoured")
        robe.wear(self.char1, True, quiet=True)
        cuirass.wear(self.char1, True, quiet=True)
        self.assertEqual(self.read(), "a robed, lean, grey-eyed woman")
        robe.db.covered_by = cuirass
        self.assertEqual(self.read(), "an armoured, lean, grey-eyed woman")

    def test_a_garment_without_a_word_hides_the_one_beneath(self):
        _garment(self.char1, "linen cuirass", "armour_padding", "armoured").wear(self.char1, True, quiet=True)
        _garment(self.char1, "plain mantle", "fullbody").wear(self.char1, True, quiet=True)
        self.assertEqual(self.read(), "a lean, grey-eyed woman")

    # Gear OQ-GR5: an armour piece without a word is passed over. Both orders,
    # since the contrib's sort reverses `contents` within a type.
    def test_a_wordless_piece_worn_first_does_not_silence_its_layer(self):
        _garment(self.char1, "helm", "armour_rigid").wear(self.char1, True, quiet=True)
        _garment(self.char1, "bone armour", "armour_rigid", "bone-clad").wear(
            self.char1, True, quiet=True)
        self.assertEqual(self.read(), "a bone-clad, lean, grey-eyed woman")

    def test_a_wordless_piece_worn_last_does_not_silence_its_layer(self):
        _garment(self.char1, "bone armour", "armour_rigid", "bone-clad").wear(
            self.char1, True, quiet=True)
        _garment(self.char1, "helm", "armour_rigid").wear(self.char1, True, quiet=True)
        self.assertEqual(self.read(), "a bone-clad, lean, grey-eyed woman")

    def test_a_wordless_piece_does_not_silence_the_layer_beneath(self):
        _garment(self.char1, "linen cuirass", "armour_padding", "armoured").wear(
            self.char1, True, quiet=True)
        _garment(self.char1, "helm", "armour_rigid").wear(self.char1, True, quiet=True)
        self.assertEqual(self.read(), "an armoured, lean, grey-eyed woman")

    def test_the_hood_replaces_the_feature(self):
        hood = _garment(self.char1, "hood", "hat", conceals=("feature",))
        hood.wear(self.char1, True, quiet=True)
        self.assertEqual(self.read(), "a lean, hooded woman")
        self.assertEqual(self.char2.search("grey-eyed", quiet=True), [])
        self.assertEqual(list(self.char2.search("hooded", quiet=True)), [self.char1])
        hood.remove(self.char1, quiet=True)
        self.assertEqual(self.read(), "a lean, grey-eyed woman")

    def test_fatigue_at_twenty_shows(self):
        fatigue = self.char1.traits.fatigue
        fatigue.current = 21
        self.assertEqual(self.read(), "a lean, grey-eyed woman")
        fatigue.current = 20
        self.assertEqual(self.read(), "a haggard, lean, grey-eyed woman")
        fatigue.current = 0
        self.assertEqual(self.read(), "a haggard, lean, grey-eyed woman")

    def test_overloaded_shows(self):
        limit = self.char1.enc_limit
        load = create_object(OBJECT, key="stone", location=self.char1)
        load.db.enc = limit
        self.assertEqual(self.read(), "a lean, grey-eyed woman")   # FREE at the limit
        load.db.enc = limit + 1
        self.assertEqual(self.read(), "a burdened, lean, grey-eyed woman")

    def test_fatigue_is_worse_than_load(self):
        self.char1.traits.fatigue.current = 5
        create_object(OBJECT, key="stone", location=self.char1).db.enc = self.char1.enc_limit + 1
        self.assertEqual(self.read(), "a haggard, lean, grey-eyed woman")

    def test_the_search_finds_by_a_shown_word(self):
        self.char1.stats.siz.base = 16
        self.char1.traits.fatigue.current = 10
        _garment(self.char1, "fur cloak", "fullbody", "cloaked").wear(self.char1, True, quiet=True)
        self.assertEqual(self.read(), "a haggard, cloaked, grey-eyed woman")  # *heavyset* dropped
        for word in ("cloaked", "cloak", "haggard", "grey-eyed"):
            with self.subTest(word=word):
                self.char1.sdesc.forget()
                self.assertEqual(list(self.char2.search(word, quiet=True)), [self.char1])
        self.char1.sdesc.forget()
        self.assertEqual(self.char2.search("heavyset", quiet=True), [])

    def test_a_composer_that_raises_gives_the_stored_text_and_logs(self):
        with mock.patch("world.sdesc.compose", side_effect=RuntimeError("x")), \
                mock.patch("world.sdesc.logger.log_trace") as trace:
            self.assertEqual(self.read(), shown(self.char1))
        trace.assert_called_once()

    def test_bad_facts_give_the_stored_text(self):
        self.char1.db.appearance = {"sex": "female", "age": "adult", "feature": "purple"}
        with mock.patch("world.sdesc.logger.log_trace") as trace:
            self.assertEqual(self.read(), shown(self.char1))
        trace.assert_called_once()


class TestMemo(_Composed):
    def test_one_composition_for_a_room_line_to_many_readers(self):
        readers = [create_object(CHARACTER, key=f"Reader{n}", location=self.room1)
                   for n in range(12)]
        for reader in readers + [self.char2]:
            reader.msg = mock.Mock()
        self.char1.sdesc.forget()
        with mock.patch("world.sdesc.compose", wraps=sdesc_rules.compose) as compose:
            self.room1.msg_contents("$You() waves to {target}.", from_obj=self.char1,
                                    exclude=[self.char1], mapping={"target": self.char2})
        self.assertEqual(compose.call_count, 1)
        said = readers[0].msg.call_args.kwargs["text"][0]
        # char2 has no account: a statue (NM-T11).
        self.assertEqual(said, "A lean, grey-eyed woman waves to "
                               "|wstone statue of a broad-shouldered man|n.")

    def test_a_new_composition_after_the_memo(self):
        self.char1.sdesc.forget()
        clock = iter((100.0, 100.5, 100.0 + sdesc_rules.MEMO_SECONDS))
        with mock.patch("world.sdesc.time.monotonic", side_effect=lambda: next(clock)), \
                mock.patch("world.sdesc.compose", wraps=sdesc_rules.compose) as compose:
            for _ in range(3):
                self.char1.sdesc.get()
        self.assertEqual(compose.call_count, 2)

    def test_forget(self):
        self.char1.sdesc.get()
        self.char1.traits.fatigue.current = 5
        self.assertEqual(self.char1.sdesc.get(), "a lean, grey-eyed woman")  # within the memo
        self.char1.sdesc.forget()
        self.assertEqual(self.char1.sdesc.get(), "a haggard, lean, grey-eyed woman")


class TestNameToType(_Composed):
    def test_the_core_word_before_the_first(self):
        self.char1.traits.fatigue.current = 10
        _garment(self.char1, "fur cloak", "fullbody", "cloaked").wear(self.char1, True, quiet=True)
        self.char1.sdesc.forget()
        self.assertEqual(names.name_to_type(self.char2, self.char1), "grey-eyed")

    def test_hooded(self):
        _garment(self.char1, "hood", "hat", conceals=("feature",)).wear(self.char1, True, quiet=True)
        self.char1.sdesc.forget()
        self.assertEqual(names.name_to_type(self.char2, self.char1), "hooded")

    def test_a_recog_still_wins(self):
        self.char2.recog.add(self.char1, "Mia")
        self.assertEqual(names.name_to_type(self.char2, self.char1), "Mia")

    def test_without_facts_the_first_word(self):
        self.assertEqual(names.name_to_type(self.char1, self.char2), "broad-shouldered")

    def test_a_composer_that_raises_falls_back_to_the_first_word(self):
        with mock.patch("world.sdesc.compose", side_effect=RuntimeError("x")), \
                mock.patch("world.sdesc.logger.log_trace"):
            self.char1.sdesc.forget()
            self.assertEqual(names.name_to_type(self.char2, self.char1), "weathered")

    def test_here_the_whole_text_when_the_word_finds_two(self):
        third = create_object(CHARACTER, key="Char3", location=self.room1)
        third.stats.siz.base = 11
        _appear(third)
        self.char1.sdesc.forget()
        self.assertEqual(names.name_to_type_here(self.char2, self.char1),
                         "a lean, grey-eyed woman")

    def test_here_the_word_when_it_finds_one(self):
        self.assertEqual(names.name_to_type_here(self.char2, self.char1), "grey-eyed")


class TestAppearanceCommand(EvenniaCommandTest):
    """char1 is puppeted by the test account, a Developer; char2 has no account."""

    character_typeclass = CHARACTER

    def setUp(self):
        super().setUp()
        describe(self.char1, self.char2)

    def test_it_sets_the_facts_and_pushes_the_room(self):
        with mock.patch("commands.admin_commands.client_state.push_room") as push:
            self.call(CmdAppearance(), "Char2 = sex:female, age:old, feature:freckled",
                      "Char2 (sex:female, age:old, feature:freckled) reads as a lean, "
                      "freckled old woman.", caller=self.char1)
        self.assertEqual(self.char2.db.appearance,
                         {"sex": "female", "age": "old", "feature": "freckled"})
        push.assert_called_once_with(self.room1)

    def test_one_fact_changes_and_the_memo_is_forgotten(self):
        self.call(CmdAppearance(), "Char2 = sex:male, age:adult, feature:pale", caller=self.char1)
        self.assertEqual(self.char2.sdesc.get(), "a lean, pale man")
        self.call(CmdAppearance(), "Char2 = feature:scarred", caller=self.char1)
        self.assertEqual(self.char2.sdesc.get(), "a lean, scarred man")

    def test_by_dbref_from_another_room(self):
        self.char2.move_to(self.room2, quiet=True)
        self.call(CmdAppearance(), f"#{self.char2.id} = sex:unstated, age:young, feature:bald",
                  caller=self.char1)
        self.assertEqual(self.char2.sdesc.get(), "a lean, bald figure")

    def test_by_key_from_another_room(self):
        self.char2.move_to(self.room2, quiet=True)
        self.call(CmdAppearance(), "Char2 = sex:unstated, age:young, feature:bald",
                  caller=self.char1)
        self.assertEqual(self.char2.sdesc.get(), "a lean, bald figure")

    def test_show(self):
        self.call(CmdAppearance(), "Char2", "Char2 has no appearance facts and reads as a "
                  "broad-shouldered man.", caller=self.char1)

    def test_a_value_outside_the_vocabulary(self):
        said = self.call(CmdAppearance(), "Char2 = sex:female, age:adult, feature:purple",
                         caller=self.char1)
        self.assertIn("purple is not a feature. Choose one of: grey-eyed", said)
        self.assertIsNone(self.char2.db.appearance)

    def test_a_name_outside_the_three(self):
        said = self.call(CmdAppearance(), "Char2 = height:tall", caller=self.char1)
        self.assertIn("Write each fact as name:value", said)

    def test_all_three_for_a_first_appearance(self):
        said = self.call(CmdAppearance(), "Char2 = sex:female", caller=self.char1)
        self.assertIn("Char2 has no appearance yet: give age, feature too.", said)
        self.assertIsNone(self.char2.db.appearance)

    def test_a_non_character(self):
        stone = create_object(OBJECT, key="stone", location=self.room1)
        said = self.call(CmdAppearance(), f"#{stone.id} = sex:male", caller=self.char1)
        self.assertIn("stone is not a character.", said)
        self.assertIsNone(stone.db.appearance)

    def test_a_player_cannot(self):
        self.assertFalse(CmdAppearance().access(self.char2, "cmd"))
        self.assertTrue(CmdAppearance().access(self.char1, "cmd"))

    def test_it_is_in_the_character_set(self):
        from commands.default_cmdsets import CharacterCmdSet

        cmdset = CharacterCmdSet()
        cmdset.at_cmdset_creation()
        self.assertIn("@appearance", [cmd.key for cmd in cmdset.commands])
