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


class MongooseCraftRecipe(CraftingRecipe):
    """Base recipe adding Mongoose Legend d100 skill resolution + sinks."""

    # --- tuning (override per concrete recipe) ---
    name = "mongoose craft base"          # concrete recipes MUST override
    skill_name = "craft"                  # which Character.skills entry to roll
    craft_cooldown = 30                   # realtime seconds, per-recipe
    consume_policy = "raw"                # see module docstring

    # Optional tool: NOT a required tool_tag (so the craft is always possible),
    # but its presence shifts the skill check. Pass it in-game via `using <tool>`.
    tool_tag = None                       # e.g. "knife"; None = no tool interaction
    tool_bonus = 20                       # circumstance bonus when the tool is present
    improvised_penalty = -20              # penalty when absent. Arms of Legend RAW is
                                          # -40 for improvised tools; softened for MVP.

    # We allow extra/optional tools through validation so an optional tool can be
    # supplied without the contrib rejecting it as an unexpected input.
    exact_tools = False

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

    def _tool_modifier(self):
        """+bonus if the optional tool was supplied, penalty if not; 0 if no tool used."""
        if not self.tool_tag:
            return 0
        for obj in self.inputs:
            if obj and hasattr(obj, "tags") and obj.tags.has(
                self.tool_tag, category=self.tool_tag_category
            ):
                return self.tool_bonus
        return self.improvised_penalty

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

        # Contrib input validation (materials/tools). Raises CraftingValidationError
        # on bad inputs; the base craft() catches it and skips do_craft.
        super().pre_craft(**kwargs)

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

        if self._should_consume(tier):
            for obj in self.validated_consumables:
                obj.delete()

        return craft_result
