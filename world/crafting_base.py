"""
world/crafting_base.py

MongooseCraftRecipe: PolishedWorld's base crafting recipe.

This sits between Evennia's CraftingRecipe and our concrete recipes. It layers
Mongoose Legend skill resolution onto the contrib's lifecycle:

    pre_craft   -> validate inputs (contrib) + knowledge and skill gates
                   (abort, no consume)
    do_craft    -> roll Craft skill (tool, overload and mastery modifiers),
                   count a successful check toward the recipe's mastery
                   (M2.1), map result tier -> quality, spawn output, stamp
                   quality; places nothing (the output has no location)
    post_craft  -> consume materials per policy, then deliver the output
                   through Character.receive_or_set_down (W5.1), then
                   message: the tier-flavoured result line, the set-down line,
                   improvement feedback, the mastery-step line, the tool-break
                   line. Returns only what the crafter holds.

IMPORTANT: this module must NOT be listed in settings.CRAFT_RECIPE_MODULES.
Evennia's _load_recipes() registers every CraftingRecipeBase subclass it finds
*defined* in a recipe module. Concrete recipes import this base; because
callables_from_module() only returns classes whose __module__ is the recipe
module itself, the imported base is not registered as a phantom recipe.

Concrete recipes (world/recipes.py) subclass this and set:
    name              - unique recipe name (used by the `craft` command)
    consumable_tags   - ingredient tag-keys (crafting_material category), repeated per count
    output_prototypes - prototype_key(s) to spawn on a craft
    tool_tag          - OPTIONAL tool tag-key (crafting_tool category) for a bonus; None = none
    craft_duration    - realtime seconds a craft takes: the `craft` command waits
                        this long before the craft resolves (override as needed)

Consume policy (consume_policy):
    "raw"    - every attempt produces an item; quality scales with the result
               tier; materials are always consumed. [MVP default]
    "strict" - failure/fumble produce no item; materials still consumed.
    "wurm"   - as strict (partial-loss-on-failure refinement deferred; whole-object
               deletion makes fractional loss awkward for single-item recipes).
"""

from evennia.prototypes.spawner import spawn
from evennia.contrib.game_systems.crafting import CraftingRecipe, CraftingError

from world.skillcheck import skill_check
from world.crafting_quality import quality_band, SUPERIOR
from world.recipe_mastery import MASTERY_CAP, MASTERY_STEP


class MongooseCraftRecipe(CraftingRecipe):
    """Base recipe adding Mongoose Legend d100 skill resolution + sinks."""

    # --- tuning (override per concrete recipe) ---
    name = "mongoose craft base"          # concrete recipes MUST override
    skill_name = "craft"                  # which Character.skills entry to roll
    craft_duration = 30                   # realtime seconds a craft TAKES (Epic A).
                                          # Read by the `craft` command before
                                          # craft() runs: the wait lives in the
                                          # command, because craft() is synchronous
                                          # by construction. The only time knob: it
                                          # replaced craft_cooldown (D4, TA2.2).
    consume_policy = "raw"                # see module docstring
    min_skill = 0                         # Component F: HARD skill floor (effective
                                          # Craft %) required to *attempt* this recipe.
                                          # 0 = ungated (default); advanced recipes
                                          # override (F.2). Enforced in pre_craft BEFORE
                                          # consume; orthogonal to the tool modifier
                                          # (the roll) and Stage 3's knowledge-gate.

    # Stage 3 knowledge-gate declaration (Component A.2). Mirrors min_skill's
    # "0 = ungated default" shape: False = common/ungated (a fresh character
    # can craft it), True = must be LEARNED first (see the known-recipe set on
    # Character). DECLARATION ONLY -- the enforcing gate lives in Component B;
    # this attribute just tells that gate which recipes to care about.
    # Orthogonal to min_skill (a skill floor) and the tool modifier (the roll).
    requires_knowledge = False

    # Per-recipe mastery (MD6): the craft discipline this recipe belongs to,
    # one of the names in world.recipe_mastery.DISCIPLINES. DISPLAY ONLY --
    # `recipes` groups by it and reads titles from it (M4.2); no check, roll or
    # gate ever reads it, and it is not Legend's PROFESSIONS. Every concrete
    # recipe declares its own; the base stays None so a recipe that forgets
    # fails the registry test instead of inheriting a default.
    discipline = None

    # Optional tool: NOT a required tool_tag (so the craft is always possible),
    # but its ABSENCE penalises the skill check. A recipe's tool_tag is the tool
    # it is designed around, so *having* it is the baseline (modifier 0), not a
    # bonus; only a *superior* tool grants a positive modifier (Component G).
    tool_tag = None                       # e.g. "knife"; None = no tool interaction
    tool_bonus = 10                       # Component G: positive modifier a *superior* tool
                                          # (quality > 100) grants on the craft check. A plain
                                          # present tool stays baseline (0); only a critical-
                                          # crafted tool reaches this. +10 keeps the quality
                                          # ceiling drift measured (new max = 111).
    improvised_penalty = -20              # penalty when the tool is absent. Arms of Legend
                                          # RAW is -40 for improvised tools; softened for MVP.

    # We allow extra/optional tools through validation so an optional tool can be
    # supplied without the contrib rejecting it as an unexpected input.
    exact_tools = False

    # Tool-wear sink (Component D). A completed craft nicks the used tool's
    # condition by this much (Task D.1). Overridable per recipe; a fumble-scaled
    # variant (tool_wear_on_fumble) is deferred to a later balance pass (§13).
    tool_wear = 5

    # Result-tier -> base quality (Mongoose Legend Item Quality bands). A critical
    # adds the critical score on top (Legend core: bonus == modified skill // 10).
    QUALITY_BY_TIER = {"critical": 100, "success": 100, "failure": 50, "fumble": 25}

    # Tier-flavoured messages. {outputs} is filled with the crafted item name(s).
    tier_messages = {
        "critical": "Your hands move with rare sureness. You craft {outputs} of superior quality!",
        "success": "You work the materials into {outputs}.",
        "failure": "The work fights you; {outputs} comes out poorly made.",
        "fumble": "You botch the work badly \u2014 {outputs} is shoddy, barely usable.",
    }
    # Shown when a non-raw policy yields no item at all.
    fail_no_item_message = "Your attempt fails and the materials are wasted."

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _skill_value(self):
        """Effective Craft skill (counter trait .value = current + mod), 0 if absent."""
        skills = getattr(self.crafter, "skills", None)
        trait = skills.get(self.skill_name) if skills else None
        return trait.value if trait else 0

    def _physical_modifier(self):
        """
        The crafter's physical-test modifier (W3.1), 0 without the seam.

        getattr-guarded like `_skill_value`: a crafter that is not a
        Character (no `physical_modifier`) rolls without the penalty instead
        of crashing the craft.
        """
        reader = getattr(self.crafter, "physical_modifier", None)
        return reader() if reader else 0

    def _mastery_modifier(self):
        """
        The recipe's mastery modifier for this crafter (M2.2, MD3), 0 without
        the handler.

        getattr-guarded like `_physical_modifier`: a crafter that is not a
        Character rolls without mastery instead of crashing the craft. The
        formula lives once, in RecipeMasteryHandler.modifier; this only asks.
        It is read before do_craft's write (M2.1), so the craft that reaches a
        step rolls at the old modifier and the next one gets the new.
        """
        mastery = getattr(self.crafter, "recipe_mastery", None)
        return mastery.modifier(self.name) if mastery is not None else 0

    def _used_tool(self):
        """The supplied *usable* tool matching this recipe's tool_tag, or None.

        Single source of truth for "which input is the tool": _tool_modifier
        (the check modifier) and the D.1 wear sink both read this, so they can
        never disagree about which object is the tool.

        Scans self.inputs -- NOT self.validated_tools. A MongooseCraftRecipe
        declares its tool through our own optional `tool_tag`, never the
        contrib's required `tool_tags`; the contrib's validation therefore
        leaves validated_tools EMPTY. self.inputs is where the actually-supplied
        tool reliably lives, so we scan it here (the old _tool_modifier body).

        A BROKEN tool (condition 0, Task D.2) is treated as NOT PRESENT: it is
        skipped here, so _tool_modifier falls to improvised_penalty and the wear
        sink finds nothing to nick. getattr-guarded because a non-durable tool
        (a future station/furnace) has no is_broken and is never "broken".
        """
        if not self.tool_tag:
            return None
        for obj in self.inputs:
            if (
                obj
                and hasattr(obj, "tags")
                and obj.tags.has(self.tool_tag, category=self.tool_tag_category)
                and not getattr(obj, "is_broken", False)
            ):
                return obj
        return None

    def _tool_modifier(self):
        """Tool modifier for the craft check (RAW-aligned, Arms of Legend).

        The recipe's tool_tag is the tool the craft is *designed around*, so
        having it is the baseline (0), not a bonus -- lacking it is what shifts
        the check. The one way ABOVE baseline is a *superior* tool (Component G):
        a tool crafted at the critical tier (quality > 100) grants +tool_bonus,
        reintroducing the positive modifier the Component A flip removed.

            no tool_tag            -> 0             (recipe needs no tool)
            superior tool present  -> +tool_bonus   (quality > 100)
            plain tool present     -> 0             (baseline; the expected tool)
            tool absent/improvised -> improvised_penalty

        The superior tier is read from the tool's OWN db.quality -- which do_craft
        already stamped on it when it was crafted (every output, tools included, is
        stamped before _finalize_item). So no separate "is this superior" flag is
        needed: the number that made it superior lives on the object, and this is a
        pure read (no race conditions under the serial reactor).

        db.quality guard: a tool that was NOT crafted (spawned/admin-made, e.g. the
        metal knife prototype, which has no craft recipe yet) carries
        db.quality = None. quality_band(None) would raise, and such a tool is a
        plain baseline tool anyway, so None short-circuits to 0 before banding.

        A broken tool never reaches the superior/baseline branch: _used_tool()
        skips is_broken tools, so a broken *superior* tool returns None here and
        falls to improvised_penalty -- broken counts as absent, by design.
        """
        if not self.tool_tag:
            return 0
        tool = self._used_tool()
        if tool is None:
            return self.improvised_penalty          # absent or broken -> penalty
        quality = tool.db.quality
        if quality is not None and quality_band(quality) == SUPERIOR:
            return self.tool_bonus                   # superior tool -> positive modifier
        return 0                                      # plain present tool -> baseline

    def _quality_for(self, outcome):
        """Map a skill_check outcome to a stamped quality value."""
        tier = outcome["result"]
        quality = self.QUALITY_BY_TIER.get(tier, 50)
        if tier == "critical":
            quality += outcome["crit_score"]
        return quality

    def _should_produce(self, tier):
        """Whether an item is spawned for this tier under the active policy."""
        if self.consume_policy == "raw":
            return True
        return tier in ("critical", "success")

    def _should_consume(self, tier):
        """Whether the validated consumables are deleted (always, for our policies)."""
        return True

    def _finalize_item(self, obj, outcome):
        """Hook for item-specific quality effects on a freshly crafted object.

        Called once per spawned object, after `quality` is stamped and before
        post_craft delivers it to the crafter. Default is a no-op; subclasses
        translate quality into concrete stats (charges, durability, ...).
        """
        pass

    # ------------------------------------------------------------------
    # lifecycle overrides
    # ------------------------------------------------------------------

    def pre_craft(self, **kwargs):
        # Reset per-attempt state FIRST, so that if validation below raises,
        # post_craft (always called) sees rolled=False and consumes nothing.
        self.rolled = False
        self.skill_outcome = None
        self.improvement_result = None
        self.tool_broke = None
        self.mastery_step = None

        # Contrib input validation (materials/tools). Raises CraftingValidationError
        # on bad inputs; the base craft() catches it and skips do_craft.
        super().pre_craft(**kwargs)

        # Knowledge-gate (Component B.1) -- Stage 3's THIRD orthogonal gate and the
        # authoritative backstop for EVERY code path that reaches craft() (the
        # command, barter-craft, scripts). Placed after input validation and BEFORE
        # the skill-gate: "can you make this at all?" is asked before "are you
        # skilled enough?". requires_knowledge (Component A.2) marks the advanced
        # recipes; the common survival/tool recipes inherit False and skip this
        # branch entirely, so the gate only ever fires on learnable recipes.
        #
        # The getattr guard mirrors this module's defensive crafter-access (cf.
        # _skill_value / attempt_skill_improvement): the world layer
        # never assumes crafter is a Character, so a crafter that lacks the
        # knows_recipe helper cannot "know" an advanced recipe and is refused --
        # the safe default for a knowledge-gated good. The check is read-only
        # (tags.has), so there is nothing to consume and no race under the
        # single-threaded reactor. We raise before do_craft -> rolled stays False
        # -> post_craft consumes nothing. self.name is the canonical registry name,
        # matching the key learn_recipe/knows_recipe store on the Character.
        if self.requires_knowledge and not (
            getattr(self.crafter, "knows_recipe", None)
            and self.crafter.knows_recipe(self.name)
        ):
            self.msg("You don't know how to make that.")
            raise CraftingError(f"{self.name}: recipe unknown to crafter.")

        # Skill-gate (Component F.1). A HARD floor: advanced recipes set min_skill;
        # a crafter below it is refused HERE -- after inputs are valid and before
        # any consume. We raise before do_craft, so rolled stays False and
        # post_craft consumes nothing. Reads EFFECTIVE skill
        # (_skill_value() = counter .value = current + mod), so a temporary buff can
        # lift someone over the bar -- intended: the gate asks "are you good enough
        # to *attempt* this right now". Deliberately does NOT apply the tool modifier
        # (nor the overload penalty, W3.1 -- same reasoning):
        # that penalty shifts the ROLL in do_craft ("how well"), not the gate ("may
        # you try"), so a skilled but tool-less crafter passes here and then rolls at
        # -20. Orthogonal to Stage 3's knowledge-gate. min_skill defaults to 0
        # (ungated), so trivial survival recipes are never blocked.
        if self._skill_value() < self.min_skill:
            self.msg(f"Your Craft is too unskilled (need {self.min_skill}%).")
            raise CraftingError(f"{self.name} requires Craft {self.min_skill}%.")

    def do_craft(self, **kwargs):
        # A real attempt is happening.
        self.rolled = True
        # Three modifiers, all read here at the roll -- for a timed craft, when
        # the timer completes: the tool, the crafter's overload penalty (W3.1)
        # and the recipe's mastery (M2.2, MD3). Mastery is a MODIFIER, never
        # part of the skill value: the skill stays the crafter's, and nothing
        # about improvement (which reads skill.current) sees it (MD7).
        outcome = skill_check(
            self._skill_value(),
            self._tool_modifier() + self._physical_modifier() + self._mastery_modifier(),
        )
        self.skill_outcome = outcome
        tier = outcome["result"]

        # Tool-wear sink (Component D.1). A *completed* attempt wears the used
        # tool. Placed here -- after rolled=True, before the produce/consume
        # branch -- so wear ties to a real craft and never to an invalid-input,
        # knowledge or skill-floor bail (all raise before do_craft runs).
        # _used_tool() reads self.inputs (validated_tools is empty for our
        # optional-tool recipes; see its docstring) and nicks the tool, never a
        # consumable. hasattr-guarded: a future station/furnace could carry the
        # tool tag without being a DurableObject, and only wearable tools wear.
        tool = self._used_tool()
        if tool is not None and hasattr(tool, "apply_wear"):
            # _used_tool() only returns a NON-broken tool, so any drop to 0 here
            # is this craft breaking it. Capture the display name now for the
            # post_craft notice; the tool is NOT deleted (Task D.2 reconcile of
            # decomposition §9 D.1's delete()) -- it lingers broken so it counts
            # as absent next craft and can still be repaired (Task D.4).
            if tool.apply_wear(self.tool_wear) <= 0:
                self.tool_broke = tool.get_display_name(looker=self.crafter)

        # On-use skill improvement (Component B.3). Gated inside
        # attempt_skill_improvement (success + cooldown); a failed check simply
        # returns None. Placed before the produce/consume branch so growth ties
        # to the skill *check* succeeding, not to whether an item was yielded.
        # getattr-guarded to match this module's defensive crafter access -- a
        # crafter is normally a Character, but the world layer shouldn't assume it.
        # Capture the summary (not discard it): post_craft threads it into the
        # player-facing feedback after the craft-result message (C.1). None when
        # gated out -- the common case.
        improve = getattr(self.crafter, "attempt_skill_improvement", None)
        self.improvement_result = improve(self.skill_name, outcome) if improve else None

        # Per-recipe mastery (Recipe Mastery M2.1, MD2). The single writer of
        # recipe_mastery: one completed craft per successful CHECK. Gated on
        # outcome["success"], NOT on the _should_produce branch below: under the
        # "raw" policy every recipe inherits, that branch is taken on failure
        # and fumble too (lesson 177), so a gate there would count failures.
        # A product later set down at the weight ceiling still counts -- the
        # write happens here, before delivery. For a timed craft this runs at
        # completion, like the roll. getattr-guarded like
        # attempt_skill_improvement: a crafter without the handler neither
        # counts nor errors.
        # mastery_step is set only when the roll MODIFIER rose, not the step:
        # past the cap the step keeps climbing (25, 30, ...) while the modifier
        # stays at MASTERY_CAP, and nothing the player can feel has changed.
        mastery = getattr(self.crafter, "recipe_mastery", None)
        if mastery is not None and outcome["success"]:
            before = mastery.modifier(self.name)
            mastery.add(self.name)
            if mastery.modifier(self.name) > before:
                self.mastery_step = mastery.step(self.name)

        if not self._should_produce(tier):
            return None  # non-raw policies: failure/fumble yield nothing

        quality = self._quality_for(outcome)
        result = spawn(*self.output_prototypes)
        for obj in result:
            obj.db.quality = quality
            obj.db.crafted_by = self.crafter.key
            # Stamp the recipe name so reverse-engineering (Component E.2) knows
            # what this item teaches. self.name is the canonical registry name
            # (the same key knows_recipe/learn_recipe use). Only player-crafted
            # output carries it: spawned/loot/admin items leave db.recipe None,
            # so disassemble bites only on crafted goods (the design intent, and
            # it also seeds the BACKLOG maker's-mark).
            obj.db.recipe = self.name
            self._finalize_item(obj, outcome)
        # The products are not placed here: post_craft delivers them, after
        # the inputs are consumed, so the inputs' ENC is gone when the
        # products arrive (W5.1).
        return result

    def post_craft(self, craft_result, **kwargs):
        # Aborted before any roll (invalid inputs, an unlearned recipe or a skill
        # floor): pre_craft / the contrib already messaged the reason. Consume
        # nothing.
        if not self.rolled:
            return craft_result

        tier = self.skill_outcome["result"]
        # Consume first, then deliver (W5.1): the products land where the
        # inputs' ENC no longer counts, as in inscribe and scribe. A product
        # delivered first could be set down for a load that is about to go,
        # and its "You are overloaded." would stand -- delete() is silent.
        if self._should_consume(tier):
            for obj in self.validated_consumables:
                obj.delete()

        set_down = []
        if craft_result:
            set_down = self.crafter.receive_or_set_down(craft_result)
            outputs = ", ".join(
                obj.get_display_name(looker=self.crafter) for obj in craft_result
            )
            template = self.tier_messages.get(tier, "You finish crafting {outputs}.")
            self.msg(template.format(outputs=outputs))
            if set_down:
                self.msg(self.crafter.set_down_message(set_down))
        else:
            self.msg(self.fail_no_item_message)

        # C.1 tick-feedback: right after the craft-result line so "you made X"
        # and "your Crafting improved" read as one beat. getattr-guarded to match
        # this module's defensive crafter access; improvement_result is None when
        # the improvement attempt was gated out.
        feedback = getattr(self.crafter, "_improvement_feedback", None)
        if feedback and self.improvement_result:
            text = feedback(self.improvement_result)
            if text:
                self.msg(text)

        # Mastery step (M2.1): after the improvement line and before the tool
        # break, so the beat reads "you made X / your skill improves / you know
        # this better / your tool breaks". Set in do_craft only when this craft
        # raised the recipe's roll modifier; the line that reaches the cap is
        # the last one the recipe will ever say.
        if self.mastery_step:
            if self.mastery_step * MASTERY_STEP >= MASTERY_CAP:
                self.msg("You could make this in your sleep.")
            else:
                self.msg("Your hands know this recipe a little better.")

        # Tool-break notice (Component D.2). Emitted after the craft-result line
        # and any improvement feedback, so the beat reads "you make X / your
        # skill improves / your tool breaks". Set in do_craft only when this
        # craft wore the tool down to 0; the tool persists (no delete) as an
        # absent/improvised tool until repaired (Task D.4).
        if self.tool_broke:
            self.msg(f"Your {self.tool_broke} finally gives out and breaks apart.")

        # Only what the crafter holds goes back: the contrib's CmdCraft.func
        # sets `obj.location = caller` on every object returned
        # (crafting.py:1096-1098), and would carry a set-down product back
        # into the inventory past the ceiling (W5.1 Q3).
        if set_down:
            return [obj for obj in craft_result if obj not in set_down]
        return craft_result
