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
from world.recipes import ClothRecipe, LeatherRecipe
from commands.crafting_commands import CmdInscribe, CmdLearn


# Canonical recipe NAMES (MongooseCraftRecipe.name), because that is exactly
# what the production code passes around: knows_recipe(), _can_transmit() and the
# scroll's db.recipe stamp all key off the name -- never the class or the
# prototype_key (which live in a separate namespace).
CLOTH = "cloth"                  # requires_knowledge=True, NO min_skill -> floor 0
LEATHER_BOOTS = "leather boots"  # requires_knowledge=True, min_skill=30
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


class TestCanTransmit(EvenniaTest):
    """
    The shared mastery gate: a character may transmit a recipe IFF they KNOW it
    AND their PERMANENT Craft skill meets the recipe's min_skill floor.

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

    def test_unknown_recipe_never_transmits(self):
        # Not learned -> False, no matter how high the skill.
        self._set_craft(100)
        self.assertFalse(_can_transmit(self.char1, CLOTH))

    def test_known_recipe_with_zero_floor_transmits(self):
        # cloth has no min_skill (floor 0): knowing it is sufficient.
        self.char1.learn_recipe(CLOTH)
        self.assertTrue(_can_transmit(self.char1, CLOTH))

    def test_known_but_below_skill_floor_blocks(self):
        # leather boots demand Craft 30; 20 permanent is not enough.
        self.char1.learn_recipe(LEATHER_BOOTS)
        self._set_craft(20)
        self.assertFalse(_can_transmit(self.char1, LEATHER_BOOTS))

    def test_known_at_exact_floor_transmits(self):
        # Boundary: the floor is `>=`, so exactly 30 passes. Testing the
        # boundary itself (not just 29/31) is where off-by-one gate bugs show.
        self.char1.learn_recipe(LEATHER_BOOTS)
        self._set_craft(30)
        self.assertTrue(_can_transmit(self.char1, LEATHER_BOOTS))

    def test_buffed_value_does_not_confer_authoring_rights(self):
        """
        THE load-bearing test for this whole module.

        The gate reads PERMANENT skill (trait.current), NEVER effective
        trait.value. A +20 buff pushes .value to 40 (over the boots' 30 floor)
        while .current stays 20 (under it). A fleeting buff must not let you
        author a lasting scroll -> the gate must still return False.

        If someone ever "simplifies" _can_transmit to read .value, THIS is the
        test that fails. That is precisely its job.
        """
        self.char1.learn_recipe(LEATHER_BOOTS)
        trait = self.char1.skills.get("craft")
        trait.current = 20  # permanent: below the 30 floor
        trait.mod = 20      # simulate a +20 buff -> value == 40

        # Prove the buff is genuinely active, so the real assertion below can't
        # pass for the wrong reason.
        self.assertGreaterEqual(trait.value, 30)
        self.assertLess(trait.current, 30)

        self.assertFalse(_can_transmit(self.char1, LEATHER_BOOTS))

    def test_known_name_absent_from_registry_blocks(self):
        # A knowledge tag can outlive its recipe (renamed/removed). knows_recipe
        # is True but the registry .get is None -> False, and NO crash. Guards
        # the "vanished knowledge" branch.
        self.char1.learn_recipe("ghost recipe")
        self.assertFalse(_can_transmit(self.char1, "ghost recipe"))


class TestInscribeCommand(EvenniaCommandTest):
    """
    `inscribe <recipe>` (F.1): a mastered recipe + a bolt of cloth -> a one-use
    scroll. EvenniaCommandTest adds .call(), which runs the command and captures
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

    def _give_cloth(self):
        """Spawn the real cloth prototype into char1's hands; return it."""
        cloth = spawn("cloth")[0]
        cloth.move_to(self.char1, quiet=True)
        return cloth

    def _stamped_scrolls(self):
        """Every scroll in char1's inventory that carries a recipe stamp."""
        return [o for o in self.char1.contents if o.db.recipe]

    def test_inscribe_creates_scroll_and_consumes_cloth(self):
        self.char1.learn_recipe(CLOTH)
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
            "You can't inscribe a recipe you haven't mastered.",
            caller=self.char1,
        )
        self.assertFalse(self._stamped_scrolls())

    def test_inscribe_without_material_is_refused(self):
        # Knows the recipe but holds no cloth.
        self.char1.learn_recipe(CLOTH)
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
        self.char1.learn_recipe(CLOTH)
        cloth = self._give_cloth()
        self.char1.cooldowns.add("inscribe", 9999)

        self.call(
            CmdInscribe(), CLOTH,
            "Your hand is still cramped",
            caller=self.char1,
        )
        self.assertIsNotNone(cloth.pk)          # cloth NOT consumed
        self.assertFalse(self._stamped_scrolls())


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
