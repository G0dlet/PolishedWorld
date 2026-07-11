"""
world/crafting_base.py

MongooseCraftRecipe: PolishedWorld's base crafting recipe.

This sits between Evennia's CraftingRecipe and our concrete recipes. It layers
Mongoose Legend skill resolution onto the contrib's lifecycle:

    pre_craft   -> validate inputs (contrib) + cooldown gate (abort, no consume)
    do_craft    -> roll Craft skill, map result tier -> quality, spawn output,
                   stamp quality, start the per-recipe cooldown
    post_craft  -> tier-flavoured message + consume materials per policy

IMPORTANT: this module must NOT be listed in settings.CRAFT_RECIPE_MODULES.
Evennia's _load_recipes() registers every CraftingRecipeBase subclass it finds
*defined* in a recipe module. Concrete recipes import this base; because
callables_from_module() only returns classes whose __module__ is the recipe
module itself, the imported base is not registered as a phantom recipe.

Concrete recipes (world/recipes.py) subclass this and set:
    name              - unique recipe name (used by the `craft` command + cooldown key)
    consumable_tags   - ingredient tag-keys (crafting_material category), repeated per count
    output_prototypes - prototype_key(s) to spawn on a craft
    tool_tag          - OPTIONAL tool tag-key (crafting_tool category) for a bonus; None = none
    craft_cooldown    - realtime seconds before this recipe can be re-run (override as needed)

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


class MongooseCraftRecipe(CraftingRecipe):
    """Base recipe adding Mongoose Legend d100 skill resolution + sinks."""

    # --- tuning (override per concrete recipe) ---
    name = "mongoose craft base"          # concrete recipes MUST override
    skill_name = "craft"                  # which Character.skills entry to roll
    craft_cooldown = 30                   # realtime seconds, per-recipe
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

    @property
    def _cooldown_key(self):
        """Per-recipe cooldown key, so different recipes don't block each other."""
        return f"craft:{self.name}"

    def _skill_value(self):
        """Effective Craft skill (counter trait .value = current + mod), 0 if absent."""
        skills = getattr(self.crafter, "skills", None)
        trait = skills.get(self.skill_name) if skills else None
        return trait.value if trait else 0

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
        it enters the crafter's inventory. Default is a no-op; subclasses
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
        # _skill_value / cooldowns / attempt_skill_improvement): the world layer
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
        # a crafter below it is refused HERE -- after inputs are valid, before the
        # cooldown gate and before any consume. We raise before do_craft, so rolled
        # stays False and post_craft consumes nothing. Reads EFFECTIVE skill
        # (_skill_value() = counter .value = current + mod), so a temporary buff can
        # lift someone over the bar -- intended: the gate asks "are you good enough
        # to *attempt* this right now". Deliberately does NOT apply the tool modifier:
        # that penalty shifts the ROLL in do_craft ("how well"), not the gate ("may
        # you try"), so a skilled but tool-less crafter passes here and then rolls at
        # -20. Orthogonal to Stage 3's knowledge-gate. min_skill defaults to 0
        # (ungated), so trivial survival recipes are never blocked.
        if self._skill_value() < self.min_skill:
            self.msg(f"Your Craft is too unskilled (need {self.min_skill}%).")
            raise CraftingError(f"{self.name} requires Craft {self.min_skill}%.")

        # Cooldown gate. Only reached once inputs are valid. Abort WITHOUT
        # consuming (we raise before do_craft; rolled stays False).
        cooldowns = getattr(self.crafter, "cooldowns", None)
        if cooldowns and not cooldowns.ready(self._cooldown_key):
            left = cooldowns.time_left(self._cooldown_key, use_int=True)
            self.msg(f"You must wait {left}s before crafting {self.name} again.")
            raise CraftingError(f"{self.name} is on cooldown.")

    def do_craft(self, **kwargs):
        # A real attempt is happening.
        self.rolled = True
        outcome = skill_check(self._skill_value(), self._tool_modifier())
        self.skill_outcome = outcome
        tier = outcome["result"]

        # The time sink applies to every completed attempt, regardless of tier.
        cooldowns = getattr(self.crafter, "cooldowns", None)
        if cooldowns:
            cooldowns.add(self._cooldown_key, self.craft_cooldown)

        # Tool-wear sink (Component D.1). A *completed* attempt wears the used
        # tool. Placed here -- after rolled=True and the cooldown add, before the
        # produce/consume branch -- so wear ties to a real craft and never to a
        # cooldown-abort or invalid-input bail (both raise before do_craft runs).
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

        if not self._should_produce(tier):
            return None  # non-raw policies: failure/fumble yield nothing

        quality = self._quality_for(outcome)
        result = spawn(*self.output_prototypes)
        for obj in result:
            obj.db.quality = quality
            obj.db.crafted_by = self.crafter.key
            self._finalize_item(obj, outcome)
            # Self-contained: place the result in the crafter's inventory. The
            # `craft` command would also do this; setting location is idempotent.
            obj.location = self.crafter
        return result

    def post_craft(self, craft_result, **kwargs):
        # Aborted before any roll (cooldown or invalid inputs): pre_craft / the
        # contrib already messaged the reason. Consume nothing.
        if not self.rolled:
            return craft_result

        tier = self.skill_outcome["result"]
        if craft_result:
            outputs = ", ".join(
                obj.get_display_name(looker=self.crafter) for obj in craft_result
            )
            template = self.tier_messages.get(tier, "You finish crafting {outputs}.")
            self.msg(template.format(outputs=outputs))
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

        # Tool-break notice (Component D.2). Emitted after the craft-result line
        # and any improvement feedback, so the beat reads "you make X / your
        # skill improves / your tool breaks". Set in do_craft only when this
        # craft wore the tool down to 0; the tool persists (no delete) as an
        # absent/improvised tool until repaired (Task D.4).
        if self.tool_broke:
            self.msg(f"Your {self.tool_broke} finally gives out and breaks apart.")

        if self._should_consume(tier):
            for obj in self.validated_consumables:
                obj.delete()

        return craft_result
