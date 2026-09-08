"""
Unit tests for the per-skill lifetime XP store. Stage 4.5, Component B.

Written to the pattern in `tests/test_knowledge.py`, the golden reference for
this project (AGENTS.md section 0A).

WHAT IT COVERS
--------------
* world.skill_xp.SkillXPHandler -- the store, its fallback, and its one writer
* typeclasses.characters.Character.skill_xp -- the lazy_property wiring

BASE CLASS
----------
`EvenniaTest`, not `EvenniaTestCase`. Unlike Component A this layer needs a real
object graph: the absent-entry rule reads `char.skills`, and the store is an
Evennia Attribute. `EvenniaCommandTest` would be heavier still and buys nothing
-- Component B adds no command.

DELIBERATE DEVIATION FROM THE DECOMPOSITION
-------------------------------------------
Decomposition section 4 specifies for B.1 that "reading an unbanked skill
returns 0", and for B.2 a written one-time backfill whose headline property is
idempotence. Neither is tested here, because neither is what was built.

The reason is a measurement. `at_object_creation` gives every new character
non-zero skills -- perception 25, stealth 20, athletics 25, hunting 25, craft =
DEX + INT = 20 at default stats. A one-shot migration is therefore one-shot only
for the characters alive when it ran; every character created afterwards would
stand at craft 20 with 0 XP, and Component C would de-level her to 0 on her first
craft. The population a migration must cover has no end, so a migration cannot
close the hole.

Component B therefore derives an absent entry on read (`xp_threshold(.current)`)
and writes nothing. That converts B.2's idempotence from a property a guard must
maintain into a property of there being no write at all -- the same proof shape
`world/currency.py` uses for the wallet. Consequently:

    "unbanked reads 0"          -> TestAbsentEntryDerivesFloor (reads the floor)
    "a skill you don't have"    -> TestAbsentEntryDerivesFloor (still reads 0)
    "the backfill is idempotent"-> TestReadDoesNotWrite (nothing to be idempotent
                                   about; the Attribute is never created by a read)

MUTATION-VERIFIED
-----------------
Three mutations were introduced and measured, not reasoned about. Results, as
run:

1. `add()` banks onto 0 instead of onto the derived floor (`new_total = amount`)
   -- the shape a reasonable person would write without reading the module
   docstring. **4 failures**: all three of `TestFirstBankAddsToFloor`'s
   floor-sensitive tests, plus `TestStoreRoundTrip
   ::test_skills_do_not_leak_into_each_other`, which pins a stored total against
   its floor and therefore catches this too. Worth stating precisely, because an
   earlier draft of this docstring claimed only one class reddened; it was wrong.
2. `isinstance(store, Mapping)` -> `isinstance(store, dict)`, the `_SaverDict`
   trap, at all three sites. **6 failures** across three classes. Note which test
   does *not* fire: `test_stored_value_survives_a_round_trip` asserts on the raw
   Attribute rather than on handler behaviour, so it is a documentation test, not
   a guard.
3. `get()` caches its fallback by calling `_set()`. **8 failures**, five of them
   from `test_floor_holds_across_the_calibration_matrix` -- the matrix is not
   decorative here either: a cached floor computed under one calibration is
   simply a wrong number under the next one, which is exactly the failure mode
   P-5 guarantees we will eventually walk into.

HOW TO RUN
----------
The --settings flag is NOT optional anywhere in this project.

    evennia test --settings settings.py tests                # this package
    evennia test --settings settings.py tests.test_skill_xp  # this module
    # one test:
    evennia test --settings settings.py \
        tests.test_skill_xp.TestFirstBankAddsToFloor.test_first_bank_adds_to_the_derived_floor
"""

from collections.abc import Mapping

from django.test import override_settings

from evennia.utils.test_resources import EvenniaTest

from world.progression import xp_threshold
from world.skill_xp import SkillXPHandler

# Same matrix as tests/test_progression.py, and for the same reason: P-5 states
# in writing that the constants will be recomputed, so anything that depends on
# the curve must be shown to depend on it *correctly* rather than to coincide
# with (6, 20).
CALIBRATIONS = [
    (6, 20),   # shipped
    (6, 7),
    (3, 10),
    (1, 5),
    (20, 25),
    (1, 1),    # degenerate: cost doubles every point
]


class TestAbsentEntryDerivesFloor(EvenniaTest):
    """
    The absent-entry rule (Component B.2, restated as a fallback).

    The bug this presses on is the one that ends the epic: a skill with no
    stored XP reading as 0. Every character in the game currently has exactly
    that state, and Component C turns `.current` into a cache of
    `level_for_xp(total)`. If this returns 0 for a character standing at craft
    20, her first craft moves her to craft 0 and there is no way to tell her it
    was a bug rather than the design.
    """

    def test_fresh_character_reads_the_floor_for_its_level(self):
        level = int(self.char1.skills.craft.current)
        # Guard the premise: if at_object_creation ever starts characters at 0,
        # this test would pass vacuously and stop protecting anything.
        self.assertGreater(level, 0)

        self.assertEqual(self.char1.skill_xp.get("craft"), xp_threshold(level))

    def test_every_starting_skill_derives_not_zero(self):
        for key in self.char1.skills.all():
            level = int(self.char1.skills.get(key).current)
            self.assertEqual(
                self.char1.skill_xp.get(key),
                xp_threshold(level),
                msg=f"skill {key!r} at level {level} did not derive its floor",
            )

    def test_unknown_skill_reads_zero(self):
        # A key the character has no trait for is the one case that IS 0 -- there
        # is no level to derive a floor from. Distinct from the case above, and
        # the reason `get()` cannot simply be "return xp_threshold(...)".
        self.assertEqual(self.char1.skill_xp.get("basketweaving"), 0)

    def test_object_without_a_skills_handler_reads_zero(self):
        # The handler is duck-typed on `obj`; it must not explode when wired
        # onto something that is not a Character. `self.obj1` is a plain Object.
        handler = SkillXPHandler(self.obj1)
        self.assertEqual(handler.get("craft"), 0)

    def test_floor_tracks_the_level_not_a_captured_constant(self):
        # Derived on read means derived on *every* read. If someone caches the
        # first answer, this goes red.
        self.char1.skills.craft.current = 40
        self.assertEqual(self.char1.skill_xp.get("craft"), xp_threshold(40))

        self.char1.skills.craft.current = 60
        self.assertEqual(self.char1.skill_xp.get("craft"), xp_threshold(60))

    def test_floor_reads_current_not_value(self):
        # `.value` folds in `.mod`. A +20 tool buff worn while the fallback is
        # consulted must not invent an XP floor the character never earned --
        # which the next bank would then freeze in place permanently.
        level = int(self.char1.skills.craft.current)
        self.char1.skills.craft.mod = 20
        self.assertEqual(self.char1.skills.craft.value, level + 20)

        self.assertEqual(self.char1.skill_xp.get("craft"), xp_threshold(level))

    def test_floor_holds_across_the_calibration_matrix(self):
        # The fallback must be the curve's floor, not a number that happens to
        # match at (6, 20). P-5 promises other calibrations.
        level = int(self.char1.skills.craft.current)
        for base, span in CALIBRATIONS:
            with self.subTest(base=base, span=span):
                with override_settings(
                    SKILL_XP_BASE=base, SKILL_XP_DOUBLING_SPAN=span
                ):
                    self.assertEqual(
                        self.char1.skill_xp.get("craft"), xp_threshold(level)
                    )


class TestFirstBankAddsToFloor(EvenniaTest):
    """
    THE load-bearing class. One line of production code, one class of test.

    The bug this presses on: `add()` banking onto 0 instead of onto the derived
    floor. It is the natural thing to write, it passes every other test in this
    file, and it silently resets every existing character's progress the first
    time they use a skill. Mutation-verified against exactly that change.
    """

    def test_first_bank_adds_to_the_derived_floor(self):
        level = int(self.char1.skills.craft.current)
        floor = xp_threshold(level)

        total = self.char1.skill_xp.add("craft", 3)

        self.assertEqual(total, floor + 3)
        self.assertEqual(self.char1.skill_xp.get("craft"), floor + 3)

    def test_first_bank_does_not_lower_the_level_it_derives_from(self):
        # The end-to-end statement of the same thing, in the units that matter:
        # after a first bank the total must still buy at least the level the
        # character already had. This is the assertion that would have caught
        # the bug even if `xp_threshold` itself were wrong.
        from world.progression import level_for_xp

        level = int(self.char1.skills.craft.current)
        total = self.char1.skill_xp.add("craft", 1)

        self.assertGreaterEqual(level_for_xp(total), level)

    def test_second_bank_adds_to_the_stored_total(self):
        # Once an entry exists the fallback must get out of the way entirely.
        floor = xp_threshold(int(self.char1.skills.craft.current))

        self.char1.skill_xp.add("craft", 3)
        total = self.char1.skill_xp.add("craft", 4)

        self.assertEqual(total, floor + 7)

    def test_banking_does_not_follow_the_level_afterwards(self):
        # After the first bank the causal direction inverts permanently: XP is
        # the truth and the level is derived from it (P-1). Moving `.current`
        # must no longer move the stored XP.
        self.char1.skill_xp.add("craft", 5)
        stored = self.char1.skill_xp.get("craft")

        self.char1.skills.craft.current = 90

        self.assertEqual(self.char1.skill_xp.get("craft"), stored)


class TestReadDoesNotWrite(EvenniaTest):
    """
    Idempotence, in the form Component B actually achieves it.

    The decomposition's B.2 wanted a backfill guarded so that running it twice
    does not clobber a live value. This build has no backfill: reads derive and
    write nothing, so there is no second run to be safe about. That is a
    stronger guarantee, but only as long as nobody "optimises" the fallback by
    caching it -- which is the bug this class presses on.
    """

    def test_no_attribute_exists_on_a_fresh_character(self):
        self.assertFalse(self.char1.attributes.has("skill_xp"))

    def test_reading_never_creates_the_attribute(self):
        for _ in range(3):
            self.char1.skill_xp.get("craft")
        self.char1.skill_xp.all()

        # ⚠️ `attributes.has()` returns a LIST, not a bool (verified live), so
        # assertFalse is correct and assertIs(..., False) would be wrong.
        self.assertFalse(self.char1.attributes.has("skill_xp"))

    def test_repeated_reads_are_stable(self):
        first = self.char1.skill_xp.get("craft")
        for _ in range(5):
            self.assertEqual(self.char1.skill_xp.get("craft"), first)

    def test_attribute_appears_only_on_the_first_bank(self):
        self.assertFalse(self.char1.attributes.has("skill_xp"))
        self.char1.skill_xp.add("craft", 1)
        self.assertTrue(self.char1.attributes.has("skill_xp"))


class TestStoreRoundTrip(EvenniaTest):
    """
    Persistence mechanics.

    The bug this presses on: `_SaverDict`. Evennia deserialises an Attribute
    container into a `_SaverDict`, for which `isinstance(x, dict)` is **False**
    (verified against Evennia 6.1.0, not assumed). Any membership or copy test
    written with `dict` silently takes the wrong branch, and the store would
    behave as though it were permanently empty -- re-deriving the floor after
    every bank and losing all progress.
    """

    def test_stored_value_survives_a_round_trip(self):
        self.char1.skill_xp.add("craft", 7)
        raw = self.char1.attributes.get("skill_xp")

        self.assertNotIsInstance(raw, dict)      # the trap, asserted directly
        self.assertIsInstance(raw, Mapping)      # and the correct test for it

    def test_skills_do_not_leak_into_each_other(self):
        craft_floor = xp_threshold(int(self.char1.skills.craft.current))
        hunting_floor = xp_threshold(int(self.char1.skills.hunting.current))

        self.char1.skill_xp.add("craft", 10)

        self.assertEqual(self.char1.skill_xp.get("craft"), craft_floor + 10)
        # hunting still derives -- writing one key must not materialise the rest
        self.assertEqual(self.char1.skill_xp.get("hunting"), hunting_floor)
        self.assertNotIn("hunting", self.char1.attributes.get("skill_xp"))

    def test_second_write_preserves_the_first_key(self):
        self.char1.skill_xp.add("craft", 10)
        self.char1.skill_xp.add("hunting", 20)

        stored = dict(self.char1.attributes.get("skill_xp"))
        self.assertEqual(sorted(stored), ["craft", "hunting"])

    def test_stored_totals_are_ints(self):
        # `.current` is a float; the store must not inherit that. A float total
        # would round-trip through the Attribute fine but read strangely and
        # compare badly against xp_threshold's int.
        self.char1.skill_xp.add("craft", 3)
        self.assertIsInstance(self.char1.attributes.get("skill_xp")["craft"], int)


class TestAmountValidation(EvenniaTest):
    """
    D7, applied to XP.

    The bug this presses on: a bad amount silently doing nothing. XP that never
    banks is invisible -- the player's skill simply stops moving, with no error
    anywhere. A traceback is ugly; a skill that quietly stops progressing is
    unfixable because nobody reports it.
    """

    def test_non_int_raises(self):
        with self.assertRaises(TypeError):
            self.char1.skill_xp.add("craft", 2.5)
        with self.assertRaises(TypeError):
            self.char1.skill_xp.add("craft", "3")

    def test_bool_raises(self):
        # bool subclasses int. Without the explicit check, add("craft", True)
        # would quietly bank one XP.
        with self.assertRaises(TypeError):
            self.char1.skill_xp.add("craft", True)

    def test_zero_and_negative_raise(self):
        with self.assertRaises(ValueError):
            self.char1.skill_xp.add("craft", 0)
        with self.assertRaises(ValueError):
            self.char1.skill_xp.add("craft", -5)

    def test_a_rejected_amount_writes_nothing(self):
        with self.assertRaises(ValueError):
            self.char1.skill_xp.add("craft", 0)
        self.assertFalse(self.char1.attributes.has("skill_xp"))


class TestAll(EvenniaTest):
    """
    The visibility surface.

    The bug this presses on: an orphaned entry -- XP banked under a key with no
    matching trait -- being invisible. `add()` deliberately does not raise on an
    unknown key (see the handler docstring: `improve_skill_on_use` already made
    that call in the opposite direction). `all()` unioning stored keys with real
    skills is the compensating control that keeps the mistake findable.
    """

    def test_all_covers_every_skill_even_unbanked(self):
        result = self.char1.skill_xp.all()
        self.assertEqual(sorted(result), sorted(self.char1.skills.all()))
        for key, value in result.items():
            self.assertEqual(
                value, xp_threshold(int(self.char1.skills.get(key).current))
            )

    def test_all_surfaces_an_orphaned_entry(self):
        self.char1.skill_xp.add("basketweaving", 40)
        result = self.char1.skill_xp.all()

        self.assertIn("basketweaving", result)
        self.assertEqual(result["basketweaving"], 40)

    def test_all_returns_a_plain_dict(self):
        self.char1.skill_xp.add("craft", 1)
        result = self.char1.skill_xp.all()
        # `assertIs(type(...), dict)` and not `assertIsInstance` -- a _SaverDict
        # would satisfy assertIsInstance against Mapping and we want to know that
        # callers get something detached from the database.
        self.assertIs(type(result), dict)


class TestNoBypass(EvenniaTest):
    """
    D6, applied to a second Attribute.

    The bug this presses on: someone adding an `AttributeProperty` for
    convenience, which would create a `char.skill_xp = {...}` shortcut and end
    P-2's single-writer rule without anyone noticing at review time. The rule is
    supposed to hold because there is no other way in; this asserts there is no
    other way in.
    """

    def test_skill_xp_is_the_handler_not_an_attribute_shortcut(self):
        self.assertIsInstance(self.char1.skill_xp, SkillXPHandler)

    def test_no_attributeproperty_is_declared_on_the_class(self):
        from evennia import AttributeProperty
        from typeclasses.characters import Character

        declared = Character.__dict__.get("skill_xp")
        self.assertNotIsInstance(declared, AttributeProperty)

    def test_at_object_creation_writes_no_xp(self):
        # Same omission `currency` relies on: no starting value is written, so
        # there is nothing a careless second write could clobber.
        self.assertFalse(self.char1.attributes.has("skill_xp"))
