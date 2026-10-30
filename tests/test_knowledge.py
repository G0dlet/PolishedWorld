"""
Reference (GOLDEN) unit tests for the recipe-knowledge transmission layer.
Stage 3, Component F.

WHY THIS FILE EXISTS
--------------------
This is the PATTERN TEMPLATE for every PolishedWorld unit test. Each Evennia
testing gotcha that matters is demonstrated here at least once, with a comment
saying WHY. Replicate this structure for other modules; do not invent a new
pattern without a reason. The comments are load-bearing -- they are how an
automation agent (or a future you) learns the house style.

WHAT IT COVERS
--------------
* world.knowledge._can_transmit            -- the shared mastery gate
* world.knowledge.render_recipe_detail(_by_name) -- the pure renderers
* commands.crafting_commands.CmdInscribe    -- writing a scroll (F.1)
* commands.crafting_commands.CmdLearn       -- reading a scroll (F.2)
* CmdRecipes + Scroll.get_display_desc      -- the renderer's two consumers
                                               (TA2.3: the craft duration)

HOW TO RUN
----------
The --settings flag is NOT optional. Without it the runner falls back to
Evennia's DEFAULT settings, your custom Character typeclass never loads, and
.char1 has no `skills`/`knows_recipe` -- every test below would error.

    evennia test --settings settings.py .                     # whole game dir
    evennia test --settings settings.py tests                 # just this package
    evennia test --settings settings.py tests.test_knowledge  # just this module
    # one test:
    evennia test --settings settings.py \
        tests.test_knowledge.TestCanTransmit.test_buffed_value_does_not_confer_authoring_rights

BASE-CLASS CHEAT-SHEET (evennia.utils.test_resources)
-----------------------------------------------------
* EvenniaTestCase    -- plain TestCase, NO db objects. Fastest. Use for pure
                        functions that touch no persistent state.
* EvenniaTest        -- builds .char1/.char2/.room1/.obj1/... in a temp db.
* EvenniaCommandTest -- EvenniaTest + the .call() Command tester.
Always pick the LIGHTEST class that can express the test: a plain TestCase that
never builds the object graph is far cheaper than one that does.
"""

import time
from unittest import mock

from evennia.prototypes.spawner import spawn
from evennia.utils.test_resources import (
    EvenniaTestCase,
    EvenniaTest,
    EvenniaCommandTest,
)

from world.knowledge import (
    _can_transmit,
    render_recipe_detail,
    render_recipe_detail_by_name,
)
from world.crafting_base import MongooseCraftRecipe
from world.recipe_mastery import MASTERY_TRANSMIT_THRESHOLD
from world.recipes import (
    ClothRecipe,
    LeatherBootsRecipe,
    LeatherRecipe,
    TwineRecipe,
)
from commands.crafting_commands import (
    CmdInscribe,
    CmdLearn,
    CmdRecipes,
    CmdScribe,
    CmdTeach,
)


# Canonical recipe NAMES (MongooseCraftRecipe.name), because that is exactly
# what the production code passes around: knows_recipe(), _can_transmit() and the
# scroll's db.recipe stamp all key off the name -- never the class or the
# prototype_key (which live in a separate namespace).
CLOTH = "cloth"                  # requires_knowledge=True, min_skill=20 (E.1)
LEATHER_BOOTS = "leather boots"  # requires_knowledge=True, min_skill=40 (E.1)
TWINE = "twine"                  # requires_knowledge=False (common) -> ungated


class TestRecipeRendering(EvenniaTestCase):
    """
    The renderers are pure functions over a recipe CLASS (or a name that
    resolves to one). They read the in-memory recipe registry but NO database,
    so the plain EvenniaTestCase is the right (fastest) base: no .char1, no
    temp db.
    """

    def test_render_detail_shows_needs(self):
        block = render_recipe_detail(ClothRecipe)
        # Assert on STABLE facts (the quantity + tag), not the ASCII framing --
        # matching the full decorated string would break on every layout tweak.
        self.assertIn("Cloth", block)
        self.assertIn("3x fiber", block)  # consumable_tags = 3x "fiber"

    def test_render_detail_marks_tool_optional_or_absent(self):
        # LeatherRecipe.tool_tag == "knife" -> rendered as optional ...
        self.assertIn("optional", render_recipe_detail(LeatherRecipe))
        # ... ClothRecipe.tool_tag is None -> "none needed".
        self.assertIn("none needed", render_recipe_detail(ClothRecipe))

    def test_render_detail_shows_craft_duration(self):
        # TA2.3: the wait `craft` imposes is visible before you commit to it.
        # The expected text is built from the class attribute, never typed as
        # a literal, so a retune changes test and display together.
        #
        # TWO recipes, because one cannot tell "reads this recipe's value" from
        # "hard-codes this recipe's number"; and neither may equal the base
        # class's value, or reading MongooseCraftRecipe instead would pass.
        # Assert that premise first, so a retune that breaks it fails loudly
        # here instead of silently weakening the test.
        durations = {
            TwineRecipe.craft_duration,
            ClothRecipe.craft_duration,
            MongooseCraftRecipe.craft_duration,
        }
        self.assertEqual(len(durations), 3)
        for recipe in (TwineRecipe, ClothRecipe):
            with self.subTest(recipe=recipe.name):
                self.assertIn(
                    f"{recipe.craft_duration} seconds",
                    render_recipe_detail(recipe),
                )

    def test_render_by_name_resolves_known(self):
        block = render_recipe_detail_by_name(CLOTH)
        self.assertIsNotNone(block)
        self.assertIn("Cloth", block)

    def test_render_by_name_unknown_is_none(self):
        # Unknown / since-removed name -> None; the caller falls back to the
        # scroll's base description.
        self.assertIsNone(render_recipe_detail_by_name("no-such-recipe"))

    def test_render_by_name_blank_is_none(self):
        # Falsy input is guarded before the registry is even touched.
        self.assertIsNone(render_recipe_detail_by_name(""))
        self.assertIsNone(render_recipe_detail_by_name(None))


class TestDurationReachesBothViews(EvenniaCommandTest):
    """
    TA2.3's premise is that render_recipe_detail is SHARED: add the Time line
    once and both `recipes <name>` and `look <scroll>` show it. The rendering
    test above cannot see that -- it calls the renderer itself. These go in
    through each consumer, so a consumer that stops delegating (renders its own
    block, or filters the shared one) fails here, and only here.
    """

    character_typeclass = "typeclasses.characters.Character"

    def test_recipes_detail_shows_duration(self):
        # twine is common (requires_knowledge=False), so CmdRecipes' visibility
        # gate passes without learning anything: this test is about the
        # renderer reaching the command, not about the gate. .call() returns
        # the output with colour codes stripped.
        output = self.call(CmdRecipes(), "twine", caller=self.char1)
        self.assertIn(f"{TwineRecipe.craft_duration} seconds", output)

    def test_scroll_look_shows_duration(self):
        # get_display_desc is the hook `look` reaches (at_look ->
        # return_appearance); calling it directly keeps ExtendedRoom's
        # room-detail handling in the look command out of this test. cloth,
        # not twine: a different value from the test above, and the kind of
        # recipe a scroll actually carries (advanced, learned).
        scroll = spawn("scroll")[0]
        scroll.stamp(CLOTH)
        scroll.move_to(self.char1, quiet=True)
        self.assertIn(
            f"{ClothRecipe.craft_duration} seconds",
            scroll.get_display_desc(self.char1),
        )


class TestCanTransmit(EvenniaTest):
    """
    The shared mastery gate: a character may transmit a recipe IFF they KNOW it
    AND have completed it MASTERY_TRANSMIT_THRESHOLD (5) times (M3.1). The
    Craft skill and the recipe's min_skill floor are no longer consulted.

    We PIN the Character typeclass. EvenniaTest otherwise builds .char1 from
    settings.BASE_CHARACTER_TYPECLASS; pinning it makes the test state its own
    assumption instead of silently depending on a setting, and keeps it correct
    if that default ever changes.
    """

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        # MUST call super(): it builds .char1/.char2/rooms/etc. Forgetting this
        # is the single most common EvenniaTest mistake -> AttributeError on
        # self.char1.
        super().setUp()
        # Deterministic starting skill. at_object_creation seeds craft from
        # dex+int; we overwrite .current so no test rides on chargen values.
        self._set_craft(40)

    def _set_craft(self, value):
        """Set PERMANENT craft skill (.current) -- the value the gate reads."""
        self.char1.skills.get("craft").current = value

    def _seed(self, recipe_name, count):
        """Record `count` completed crafts of `recipe_name` for char1."""
        self.char1.recipe_mastery.add(recipe_name, count)

    def test_unknown_recipe_never_transmits(self):
        # Not learned -> False, however many times it has been made. Seeding a
        # count far past the threshold makes knows_recipe the only thing that
        # can block here (RM18).
        self._seed(CLOTH, 50)
        self.assertFalse(_can_transmit(self.char1, CLOTH))

    def test_known_below_the_threshold_blocks(self):
        # One craft short of the threshold is not enough (RM16).
        self.char1.learn_recipe(CLOTH)
        self._seed(CLOTH, MASTERY_TRANSMIT_THRESHOLD - 1)
        self.assertFalse(_can_transmit(self.char1, CLOTH))

    def test_known_at_the_threshold_transmits(self):
        # Boundary: the threshold is `>=`, so exactly five passes.
        self.char1.learn_recipe(CLOTH)
        self._seed(CLOTH, MASTERY_TRANSMIT_THRESHOLD)
        self.assertTrue(_can_transmit(self.char1, CLOTH))

    def test_the_craft_floor_no_longer_gates_transmission(self):
        # Permanent Craft one point below the boots' floor, count at the
        # threshold -> True. If the min_skill clause survives beside the count,
        # this fails (RM15).
        floor = LeatherBootsRecipe.min_skill
        self.char1.learn_recipe(LEATHER_BOOTS)
        self._set_craft(floor - 1)
        self._seed(LEATHER_BOOTS, MASTERY_TRANSMIT_THRESHOLD)
        self.assertTrue(_can_transmit(self.char1, LEATHER_BOOTS))

    def test_buffed_value_does_not_confer_authoring_rights(self):
        """
        A fleeting buff must not let you author a lasting scroll.

        Before M3.1 the gate read permanent `.current` against the floor and
        this test guarded against a switch to `.value`. The gate now reads
        completed crafts, but the intent stands: with the count one short and a
        +20 buff lifting `.value` past the floor, the answer is still False. If
        the gate ever consults `.value` of the Craft trait again, this fails
        (RM17).
        """
        floor = LeatherBootsRecipe.min_skill
        self.char1.learn_recipe(LEATHER_BOOTS)
        self._seed(LEATHER_BOOTS, MASTERY_TRANSMIT_THRESHOLD - 1)
        trait = self.char1.skills.get("craft")
        trait.current = floor - 1  # permanent: one below the declared floor
        trait.mod = 20             # simulate a +20 buff to the effective value

        # Prove the buff is genuinely active, so the real assertion below can't
        # pass for the wrong reason.
        self.assertGreaterEqual(trait.value, floor)
        self.assertLess(trait.current, floor)

        self.assertFalse(_can_transmit(self.char1, LEATHER_BOOTS))

    def test_known_name_absent_from_registry_blocks(self):
        # A knowledge tag can outlive its recipe (renamed/removed). knows_recipe
        # is True and the count is at the threshold, but the registry .get is
        # None -> False, and NO crash. Guards the "vanished knowledge" branch.
        self.char1.learn_recipe("ghost recipe")
        self._seed("ghost recipe", MASTERY_TRANSMIT_THRESHOLD)
        self.assertFalse(_can_transmit(self.char1, "ghost recipe"))


class TestInscribeCommand(EvenniaCommandTest):
    """
    `inscribe <recipe>` (F.1): a mastered recipe + a bolt of cloth -> a one-use
    scroll. Mastered means known AND completed MASTERY_TRANSMIT_THRESHOLD times
    (M3.1), so every test that expects to get past the gate seeds the count. EvenniaCommandTest adds .call(), which runs the command and captures
    what it .msg()'d back.

    .call() note for anyone extending this file: `.call(cmd, args, msg=EXPECTED)`
    does a PREFIX match on the ansi-stripped output. If a command emits SEVERAL
    separate .msg() calls to the SAME receiver, join the expected pieces with `|`
    in `msg=` -- NOT `||`. The runner sets `msg_sep = "|" if noansi else "||"`
    and `noansi` defaults True (evennia/utils/test_resources.py), so `||` only
    works if you pass `noansi=False`. Our knowledge commands msg exactly once
    per path, so no separator appears here. For a command that messages more
    than one receiver, pass a dict: `msg={obj_a: "...", obj_b: "..."}`.

    We assert the MESSAGE *and* the SIDE-EFFECTS (object created / consumed): a
    green message with the wrong world-state is a false pass, and those are the
    bugs that matter.
    """

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        self.char1.skills.get("craft").current = 40  # clears every floor we use

    def _master(self, recipe_name):
        """Learn `recipe_name` and record enough crafts to pass it on."""
        self.char1.learn_recipe(recipe_name)
        self.char1.recipe_mastery.add(recipe_name, MASTERY_TRANSMIT_THRESHOLD)

    def _give_cloth(self):
        """Spawn the real cloth prototype into char1's hands; return it."""
        cloth = spawn("cloth")[0]
        cloth.move_to(self.char1, quiet=True)
        return cloth

    def _stamped_scrolls(self):
        """Every scroll in char1's inventory that carries a recipe stamp."""
        return [o for o in self.char1.contents if o.db.recipe]

    def test_inscribe_creates_scroll_and_consumes_cloth(self):
        self._master(CLOTH)
        cloth = self._give_cloth()

        self.call(
            CmdInscribe(), CLOTH,
            "You carefully inscribe the cloth recipe onto a scroll.",
            caller=self.char1,
        )

        # A scroll stamped with the recipe now exists ...
        scrolls = [o for o in self.char1.contents if o.db.recipe == CLOTH]
        self.assertEqual(len(scrolls), 1)
        # ... and the cloth was spent. A deleted Evennia object has pk == None.
        self.assertIsNone(cloth.pk)

    def test_inscribe_unknown_recipe_is_rejected(self):
        cloth = self._give_cloth()
        self.call(
            CmdInscribe(), "no-such-recipe",
            "You don't know of any recipe by that name.",
            caller=self.char1,
        )
        self.assertFalse(self._stamped_scrolls())
        self.assertIsNotNone(cloth.pk)  # nothing consumed

    def test_inscribe_common_recipe_is_refused(self):
        # twine is common (requires_knowledge=False): nothing to transmit.
        self._give_cloth()
        self.call(
            CmdInscribe(), TWINE,
            "Everyone already knows this.",
            caller=self.char1,
        )
        self.assertFalse(self._stamped_scrolls())

    def test_inscribe_unmastered_recipe_is_refused(self):
        # char1 has NOT learned leather boots -> the mastery gate blocks it.
        self._give_cloth()
        self.call(
            CmdInscribe(), LEATHER_BOOTS,
            "You haven't made enough of these to inscribe it.",
            caller=self.char1,
        )
        self.assertFalse(self._stamped_scrolls())

    def test_inscribe_one_craft_short_is_refused(self):
        # Known, but completed one time fewer than the threshold: refused with
        # the gate's line, and the cloth is kept.
        self.char1.learn_recipe(CLOTH)
        self.char1.recipe_mastery.add(CLOTH, MASTERY_TRANSMIT_THRESHOLD - 1)
        cloth = self._give_cloth()
        self.call(
            CmdInscribe(), CLOTH,
            "You haven't made enough of these to inscribe it.",
            caller=self.char1,
        )
        self.assertFalse(self._stamped_scrolls())
        self.assertIsNotNone(cloth.pk)

    def test_inscribe_without_material_is_refused(self):
        # Knows the recipe but holds no cloth.
        self._master(CLOTH)
        self.call(
            CmdInscribe(), CLOTH,
            "You need a bolt of cloth",
            caller=self.char1,
        )
        self.assertFalse(self._stamped_scrolls())

    def test_inscribe_on_cooldown_keeps_material(self):
        # Force the cooldown active. Documented project idiom: add() a huge
        # duration so cooldowns.ready() is deterministically False. The guard
        # runs BEFORE material is spent, so the cloth must survive.
        self._master(CLOTH)
        cloth = self._give_cloth()
        self.char1.cooldowns.add("inscribe", 9999)

        self.call(
            CmdInscribe(), CLOTH,
            "Your hand is still cramped",
            caller=self.char1,
        )
        self.assertIsNotNone(cloth.pk)          # cloth NOT consumed
        self.assertFalse(self._stamped_scrolls())


class TestScribeGate(EvenniaCommandTest):
    """
    `scribe` passes every recipe through the shared gate (M3.1). Getting past
    it at the threshold is covered where a book is bound (test_set_down,
    test_improvement_engine); this pins the refusal one craft short.
    """

    character_typeclass = "typeclasses.characters.Character"

    def test_scribe_one_craft_short_is_refused(self):
        # Craft 60 clears SCRIBE_MIN_CRAFT (50), so only the per-recipe gate
        # can refuse. The inputs are kept and no book is bound.
        self.char1.skills.get("craft").current = 60
        self.char1.learn_recipe(CLOTH)
        self.char1.recipe_mastery.add(CLOTH, MASTERY_TRANSMIT_THRESHOLD - 1)
        inputs = spawn("cloth", "cloth", "twine")
        for obj in inputs:
            obj.move_to(self.char1, quiet=True)

        self.call(
            CmdScribe(), CLOTH,
            "You haven't made enough cloth to scribe it.",
            caller=self.char1,
        )
        self.assertFalse([o for o in self.char1.contents if o.db.recipes])
        self.assertTrue(all(obj.pk for obj in inputs))


class TestTeachGate(EvenniaCommandTest):
    """
    `teach <recipe> to <player>` and the student's `learn <recipe> from
    <teacher>` both run the shared gate (M3.1): teach when the offer is made,
    learn again against the live teacher when it is accepted.

    `has_account` is `sessions.count()`, and the test harness gives only char1
    a session, so char2 would be refused as "isn't someone you can teach". The
    property is patched on the class for the duration of each test.
    """

    character_typeclass = "typeclasses.characters.Character"

    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(
            type(self.char1), "has_account",
            new_callable=mock.PropertyMock, return_value=1,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.char1.learn_recipe(CLOTH)

    def test_teach_one_craft_short_is_refused(self):
        self.char1.recipe_mastery.add(CLOTH, MASTERY_TRANSMIT_THRESHOLD - 1)
        self.call(
            CmdTeach(), f"{CLOTH} to {self.char2.key}",
            "You haven't made enough of these to teach it.",
            caller=self.char1,
        )
        self.assertFalse(self.char2.ndb.pending_teach)

    def test_teach_at_the_threshold_makes_the_offer(self):
        self.char1.recipe_mastery.add(CLOTH, MASTERY_TRANSMIT_THRESHOLD)
        self.call(
            CmdTeach(), f"{CLOTH} to {self.char2.key}",
            "You offer to teach",
            caller=self.char1,
        )
        self.assertEqual(self.char2.ndb.pending_teach[:2], (self.char1, CLOTH))

    def test_accept_rechecks_the_teacher(self):
        # The fourth caller. The count cannot fall, so the offer is planted
        # directly with a teacher one craft short; accepting it is refused, the
        # student learns nothing and the offer is retired.
        self.char1.recipe_mastery.add(CLOTH, MASTERY_TRANSMIT_THRESHOLD - 1)
        self.char2.ndb.pending_teach = (self.char1, CLOTH, time.time() + 60)

        said = self.call(
            CmdLearn(), f"{CLOTH} from {self.char1.key}", caller=self.char2,
        )
        self.assertIn("can't teach you that", said)
        self.assertFalse(self.char2.knows_recipe(CLOTH))
        self.assertIsNone(self.char2.ndb.pending_teach)


class TestLearnCommand(EvenniaCommandTest):
    """
    `learn <scroll>` (F.2): study a stamped scroll to gain the recipe. The
    scroll is consumed ONLY when it teaches something new -- an already-known or
    blank scroll is left intact for someone who can still use it.
    """

    character_typeclass = "typeclasses.characters.Character"

    def _give_scroll(self, recipe_name=CLOTH, stamped=True):
        """Spawn a scroll into char1's hands; stamp it unless stamped=False."""
        scroll = spawn("scroll")[0]
        if stamped:
            # stamp() is the production API `inscribe` uses: it sets db.recipe
            # AND a searchable key, so `learn scroll` can find it by name.
            scroll.stamp(recipe_name)
        scroll.move_to(self.char1, quiet=True)
        return scroll

    def test_learn_grants_recipe_and_consumes_scroll(self):
        self.assertFalse(self.char1.knows_recipe(CLOTH))
        scroll = self._give_scroll(CLOTH)

        self.call(CmdLearn(), "scroll", "You study", caller=self.char1)

        self.assertTrue(self.char1.knows_recipe(CLOTH))
        self.assertIsNone(scroll.pk)  # scroll spent

    def test_learn_already_known_keeps_scroll(self):
        # learn_recipe() returns False when already known -> be kind, don't burn
        # a still-useful scroll.
        self.char1.learn_recipe(CLOTH)
        scroll = self._give_scroll(CLOTH)

        self.call(
            CmdLearn(), "scroll",
            "You already know this recipe.",
            caller=self.char1,
        )
        self.assertIsNotNone(scroll.pk)  # scroll intact

    def test_learn_blank_scroll_teaches_nothing(self):
        # An un-stamped scroll (db.recipe is None) has nothing to teach and is
        # NOT consumed.
        scroll = self._give_scroll(stamped=False)
        self.call(
            CmdLearn(), "scroll",
            "There's nothing to learn from that.",
            caller=self.char1,
        )
        self.assertIsNotNone(scroll.pk)

    def test_learn_without_target_asks_what(self):
        self.call(CmdLearn(), "", "Study what?", caller=self.char1)
