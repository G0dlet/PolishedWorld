"""
world/recipe_mastery.py

Per-recipe mastery for PolishedWorld: how many of each recipe a character has
completed. Alpha prerequisite 2, Component M1 (docs/
PolishedWorld_Recipe_Mastery_Decomposition.md, MD1).

NOTHING READS THIS FOR GAMEPLAY YET. M1 is storage with no consumer. M2.1 makes
`do_craft` the single writer, M2.2 turns the count into a roll modifier, M3.1
makes it the transmission gate. Until then the only way in is `@py`.

THE STORE
---------
One Attribute, `recipe_mastery`: a mapping from canonical recipe name
(`MongooseCraftRecipe.name`, the key `knows_recipe` uses) to an int count. The
handler copies `SkillXPHandler`'s shape (`world/skill_xp.py`) on purpose:

* `_store()` is tested through `collections.abc.Mapping`, never
  `isinstance(..., dict)` -- Evennia hands back a `_SaverDict`, which is not a
  `dict` (verified against 6.1.0 when skill_xp shipped).
* The one write site copies to a plain `dict` and assigns the whole mapping
  back with `attributes.add`.
* An invalid amount raises: TypeError for a non-int (and for a bool, which
  subclasses int), ValueError for an int below 1. Same convention as
  `SkillXPHandler` and `CurrencyHandler`. It is a bug in calling code, never a
  condition a player can be in.

No backfill (MD1): every character starts at 0 in every recipe, including
characters who crafted for months before this shipped. Nothing is written at
creation, so the Attribute does not exist until the first completed craft.

Names are taken as given. The handler does not resolve user-typed names
(callers already do, via `_resolve_recipe`) and does not refuse a name the
registry does not know: such an entry is kept, and `all()` shows it.

THE FORMULA (MD3)
-----------------
`modifier(name) = min(MASTERY_CAP, MASTERY_STEP * (count // MASTERY_STEP_SIZE))`
-- +5 per five completed crafts, +20 from the twentieth, which exactly cancels
`improvised_penalty = -20`. It lives here once; the recipe's
`_mastery_modifier()` (M2.2) calls this handler rather than restating it.

THE REGISTRY
------------
`all()` unions stored names with every recipe the registry knows. It reaches
the registry through `world.knowledge.recipe_names()`, not by importing the
crafting contrib's private `_RECIPE_CLASSES` here: BACKLOG *`CmdCraftGated`
recipe-resolver duplication* (Rev 24) requires every new reader of that
registry to live in a module that already reads it. The import is local to
`all()` so this module stays free of Evennia imports at load time, and so
`world/knowledge.py` can import `MASTERY_TRANSMIT_THRESHOLD` from here (M3.1)
without an import cycle.

DISCIPLINES (MD6)
-----------------
Every recipe class names one discipline (`MongooseCraftRecipe.discipline`).
`DISCIPLINES` is the closed set, in display order, with the label `recipes`
titles are built from (M4.2). Display only: nothing mechanical reads a
discipline, and no count is ever summed or averaged across one.

Concurrency: `add()` is a read-modify-write. A character runs one timed action
at a time and Evennia's reactor is single-threaded, so two completions for one
character cannot interleave; two characters have two Attributes. Do not put a
yield, `utils.delay` or deferred between the read and the write.
"""

from collections.abc import Mapping

MASTERY_STEP = 5
"""Roll modifier gained per completed step."""

MASTERY_STEP_SIZE = 5
"""Completed crafts per step."""

MASTERY_CAP = 20
"""Largest modifier mastery can give (reached at the 20th craft)."""

MASTERY_TRANSMIT_THRESHOLD = 5
"""Completed crafts needed to inscribe, scribe or teach a recipe (MD5, M3.1)."""

DISCIPLINES = (
    ("weaving", "Weaver"),
    ("leatherwork", "Leatherworker"),
    ("stonework", "Stoneworker"),
    ("bonework", "Boneworker"),
    ("woodwork", "Woodworker"),
)
"""The craft disciplines as (name, label), in display order (MD6, OQ1)."""

MASTERY_TITLES = (
    (20, "Master"),
    (10, "Journeyman"),
    (5, "Apprentice"),
)
"""
Title tiers as (count, rank), highest first (MD6, M4.2). A discipline's title
comes from the highest count on any ONE of its recipes, never the sum: twenty
different crafts made once each are breadth, not mastery. `recipes` walks this
tuple in order and takes the first tier met, so only the highest shows; it
prints the rank before the discipline's label ("Apprentice Leatherworker").
"""


class RecipeMasteryHandler:
    """
    Per-character completed-craft counter, one int per recipe name.

    Wired onto Character as `@lazy_property` `recipe_mastery`. The handler and
    the Attribute share the name, as `skill_xp` does: `char.recipe_mastery` is
    this handler, `char.attributes.get("recipe_mastery")` is the stored mapping.
    """

    def __init__(self, obj, db_attribute="recipe_mastery"):
        """
        Args:
            obj (Object): the object whose counts these are. Duck-typed: only
                `obj.attributes` is used.
            db_attribute (str): Attribute key for the mapping.
        """
        self.obj = obj
        self._db_attribute = db_attribute

    # -- reading -----------------------------------------------------------

    def _store(self):
        """
        Returns:
            Mapping or None: the stored mapping (a `_SaverDict` when read back
                from the database), or None if nothing has been written.
        """
        return self.obj.attributes.get(self._db_attribute, default=None)

    def count(self, recipe_name):
        """
        Completed crafts of one recipe.

        Args:
            recipe_name (str): canonical recipe name.

        Returns:
            int: the stored count, or 0 if none is stored. A pure read: it
                never creates the Attribute.
        """
        store = self._store()
        if isinstance(store, Mapping):
            stored = store.get(recipe_name)
            if stored is not None:
                return int(stored)
        return 0

    def step(self, recipe_name):
        """
        Returns:
            int: completed steps, `count // MASTERY_STEP_SIZE`. M2.1 compares
                this before and after a write to decide whether to speak.
        """
        return self.count(recipe_name) // MASTERY_STEP_SIZE

    def modifier(self, recipe_name):
        """
        Returns:
            int: the roll modifier mastery gives this recipe (MD3), 0..MASTERY_CAP.
        """
        return min(MASTERY_CAP, MASTERY_STEP * self.step(recipe_name))

    def all(self):
        """
        Every recipe this character has a count for, or could have.

        Returns:
            dict: `{recipe_name: count}` as a plain dict, sorted by name, over
                the union of stored names and the recipe registry. The union
                keeps an orphan (a stored name the registry no longer knows)
                visible instead of silent.
        """
        # Local import: see the module docstring, THE REGISTRY.
        from world.knowledge import recipe_names

        names = set(recipe_names())
        store = self._store()
        if isinstance(store, Mapping):
            names.update(store.keys())
        return {name: self.count(name) for name in sorted(names)}

    # -- writing -----------------------------------------------------------

    @staticmethod
    def _require_positive(amount):
        """
        Reject anything that is not an int >= 1. `bool` is refused explicitly
        because it subclasses int: without that, `add(name, True)` would count
        a craft.
        """
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError(f"amount must be an int, got {type(amount).__name__}: {amount!r}")
        if amount < 1:
            raise ValueError(f"amount must be at least 1, got {amount}")

    def add(self, recipe_name, amount=1):
        """
        Count completed crafts of a recipe. The only write site.

        Args:
            recipe_name (str): canonical recipe name.
            amount (int): crafts to add, >= 1.

        Returns:
            int: the new count.

        Raises:
            TypeError: `amount` is not an int, or is a bool.
            ValueError: `amount` is below 1.

        Validation runs before the read, so a rejected call leaves the store
        exactly as it was (and creates no Attribute).
        """
        self._require_positive(amount)
        store = self._store()
        updated = dict(store) if isinstance(store, Mapping) else {}
        new_count = self.count(recipe_name) + amount
        updated[recipe_name] = new_count
        self.obj.attributes.add(self._db_attribute, updated)
        return new_count

    def __repr__(self):
        store = self._store()
        stored = dict(store) if isinstance(store, Mapping) else {}
        return f"<RecipeMasteryHandler({self.obj}): {stored}>"
