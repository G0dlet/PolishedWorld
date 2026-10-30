"""
Shared recipe-knowledge transmission gate (Stage 3, Component F).

The written and taught knowledge channels -- `inscribe` (F, scroll), `scribe`
(G, book) and `teach` (H, live) -- all answer the same question before they let
a character pass a recipe on: *are you actually qualified to teach this one?*
Rather than copy that rule into three commands, it lives here once.

The rule (locked in the decomposition, section 2 "Delad behorighets-regel";
revised by per-recipe mastery, M3.1):

    a character may transmit a recipe iff they KNOW it AND have COMPLETED it
    at least MASTERY_TRANSMIT_THRESHOLD (5) times.

Two deliberate choices:

* Completed crafts (`char.recipe_mastery`), not the Craft skill. Until M3.1
  this read the permanent Craft skill against the recipe's `min_skill` floor;
  the floor still gates *crafting* the recipe, but no longer *passing it on*.
  The count carries over the old rule's reason for reading `.current` and not
  `.value`: it is written only by a successful `do_craft`
  (`world/crafting_base.py`), so no buff, tool or situational modifier can
  confer the standing to author a lasting scroll.

* A pure threshold, no roll. Mastery is a gate, not a gamble: if you meet the
  bar you always succeed at *writing it down* (the reader still needs the skill
  to craft from it). This matches the Legend "professional teacher" flavour
  (Legend.pdf p.72-73) without importing the Teaching skill as a gate (Teaching
  is an amplifier, deferred to BACKLOG).

Coupling note: `_can_transmit` reads the crafting contrib's private
`_RECIPE_CLASSES` registry (via `_load_recipes()` + an exact `.get`), the same
coupling `_resolve_recipe` (B.2) and `CmdDisassemble` (E.2) already carry. It is
the THIRD consumer of that registry -- logged as the one shared entry in
docs/BACKLOG.md, not a new one.
"""

from collections import Counter

from evennia.contrib.game_systems.crafting.crafting import (
    _load_recipes,
    _RECIPE_CLASSES,
)

from world.recipe_mastery import MASTERY_TRANSMIT_THRESHOLD


def recipe_names():
    """
    Every canonical recipe name the registry knows.

    Returns:
        list[str]: `MongooseCraftRecipe.name` for each registered recipe,
            sorted.

    This exists so that `world/recipe_mastery.py` can union its stored counts
    with the registry without importing the contrib's private
    `_RECIPE_CLASSES` itself. BACKLOG *`CmdCraftGated` recipe-resolver
    duplication* (Rev 24) requires any new reader of that registry to live in a
    module that already reads it; this module already does, via
    `_can_transmit`.
    """
    _load_recipes()
    return sorted(_RECIPE_CLASSES)


def _can_transmit(char, recipe_name):
    """
    Return True if `char` may inscribe/scribe/teach the recipe `recipe_name`.

    Args:
        char (Character): the would-be author/teacher. Must expose
            knows_recipe() and a `recipe_mastery` handler (a puppeted
            Character always does).
        recipe_name (str): the canonical recipe-registry name
            (MongooseCraftRecipe.name, e.g. "cloth"), NOT a prototype_key. The
            caller is expected to have already resolved a user-typed name to
            this canonical form (e.g. via _resolve_recipe).

    Returns:
        bool: True iff `char` knows the recipe AND has completed it at least
            MASTERY_TRANSMIT_THRESHOLD times (`char.recipe_mastery.count`).
            False if the recipe is unknown to `char`, has been removed from the
            registry, or has been completed fewer times than that. The recipe's
            `min_skill` floor is not consulted.

    Notes:
        The "common / ungated recipe" case is intentionally NOT handled here: a
        common recipe is knowable by everyone, so there is nothing to transmit,
        which is a different message ("Everyone already knows this.") from
        "you haven't made enough of these". Callers check requires_knowledge
        first.
    """
    if not char.knows_recipe(recipe_name):
        return False

    # Exact-key resolve: recipe_name is already canonical, so no fuzzy match is
    # wanted (a prefix collision must not resolve a different recipe). A recipe
    # since removed resolves to None -> cannot be transmitted.
    _load_recipes()
    cls = _RECIPE_CLASSES.get(recipe_name)
    if cls is None:
        return False

    # Completed crafts, not the Craft skill: the count only grows through a
    # successful do_craft, so nothing temporary can lift it. See module
    # docstring.
    return char.recipe_mastery.count(recipe_name) >= MASTERY_TRANSMIT_THRESHOLD


def render_recipe_detail(cls):
    """
    Render a resolved recipe class as its Needs/Tool/Skill/Time/Output detail block.

    Pure presentation: takes an already-resolved recipe CLASS and returns the
    coloured multi-line string, performing NO visibility check. The caller
    decides who may see it -- CmdRecipes (C.2) gates on known/common, a Scroll
    (F.3) gates on physical possession. Sharing one renderer keeps the `recipes`
    detail view and the `look <scroll>` view from ever drifting apart.

    Args:
        cls (type): a MongooseCraftRecipe subclass (already resolved by the
            caller, e.g. via _resolve_recipe or an exact registry get).

    Returns:
        str: the formatted, Evennia-coloured detail block. The leading newline
            is intentional -- it spaces the block off from a command prompt or a
            preceding description line.
    """
    # Ingredients: consumable_tags is a flat list where duplicates encode
    # quantity (["fiber","fiber","fiber"] -> 3x fiber). Counter preserves
    # first-seen order (py3.7+), so display order matches declaration order.
    tags = list(getattr(cls, "consumable_tags", []) or [])
    if tags:
        counts = Counter(tags)
        needs = ", ".join(f"{qty}x {tag}" for tag, qty in counts.items())
    else:
        needs = "nothing"

    # Tool: a single optional tag or None. Tools are never hard-required --
    # absence only costs the -20 improvised modifier -- so we say "optional".
    tool_tag = getattr(cls, "tool_tag", None)
    tool = (
        f"{tool_tag} (optional; improvising takes a penalty)"
        if tool_tag
        else "none needed"
    )

    floor = getattr(cls, "min_skill", 0) or 0
    skill = f"Craft {floor}% minimum" if floor > 0 else "no minimum"

    # Time: the realtime wait the `craft` command imposes before the craft
    # resolves (Epic A), shown so the cost is visible before a player commits
    # to it. Read directly, not via getattr like the lines above: the base
    # class defines craft_duration and TestOneKnob holds every recipe to > 0,
    # so a default here could only ever show a number `craft` does not wait.
    # Plain seconds rather than work's _format_wait: world/ does not import
    # from commands/ (see world/timed_actions.py). Under a minute the two
    # read the same; a longer craft would read "90 seconds", still true.
    duration = f"{cls.craft_duration} seconds"

    # Output: output_prototypes holds prototype KEYS, not display names.
    # Prettify the key (underscores -> spaces) for now; resolving the
    # prototype's real key/desc and correct article/pluralisation (e.g.
    # "a pair of leather boots") is deferred -> docs/BACKLOG.md.
    outputs = list(getattr(cls, "output_prototypes", []) or [])
    produced = ", ".join(o.replace("_", " ") for o in outputs) if outputs else "something"

    lines = [
        f"\n|w{cls.name.title()}|n",
        "|g" + "=" * 50 + "|n",
        f"  |wNeeds:|n   {needs}",
        f"  |wTool:|n    {tool}",
        f"  |wSkill:|n   {skill}",
        f"  |wTime:|n    {duration}",
        f"  |wOutput:|n  {produced}",
        "|g" + "=" * 50 + "|n",
    ]
    return "\n".join(lines)


def render_recipe_detail_by_name(recipe_name):
    """
    Resolve a canonical recipe name and render its detail block, or None.

    A name-taking wrapper around render_recipe_detail that keeps ALL access to
    the contrib's private _RECIPE_CLASSES registry inside this module. The Scroll
    typeclass (F.3) holds only a stamped name (obj.db.recipe), not a class; by
    resolving here it calls this and never touches the registry itself, so the
    scroll does not become yet another registry consumer (the coupling is logged
    once in docs/BACKLOG.md).

    Exact-key resolve: the caller passes a canonical stamp (written by inscribe),
    not user input, so no fuzzy match is wanted -- a prefix collision must not
    mis-resolve. A blank, unknown, or since-removed name returns None so the
    caller can fall back to showing just the base description.

    Args:
        recipe_name (str | None): the canonical recipe name, or a falsy value.

    Returns:
        str | None: the detail block, or None if there is nothing to render.
    """
    if not recipe_name:
        return None
    _load_recipes()
    cls = _RECIPE_CLASSES.get(recipe_name)
    if cls is None:
        return None
    return render_recipe_detail(cls)
