"""
Book typeclass (Stage 3, Component G.1).

A recipe BOOK is the perishable, bulk sibling of the Scroll (Component F). Where
a scroll carries ONE recipe and is consumed in a single reading, a book carries
MANY recipes and is worn down a little by each study (`learn ... from <book>`,
G.3) until it finally crumbles. It is the async, large-scale spreader of craft
knowledge; the scroll is the one-shot note.

Two inherited spines, one from each base:

* DurableObject gives the 0-100 `condition` wear axis for free -- apply_wear,
  is_broken, condition_line, and the condition-on-`look` injection. The book's
  start condition is set by `scribe` (G.2) from the author's craft outcome, NOT
  hardcoded here; wearing it down and breaking it live in G.3. There is no
  repair path in the MVP -- a spent book is gone, which keeps the sink clean
  (book-repair deferred -> docs/BACKLOG.md).
* Object is the concrete typeclass whose db/attributes handler makes the
  AttributeProperty `condition` autocreate at creation (a bare DurableObject
  mixin has no handler). MRO: Book -> DurableObject -> Object -> ... so
  DurableObject's overrides win while still deferring to Object via super().

Identity lives on the typeclass, mirroring the F.4 lesson for Scroll: `stamp()`
sets BOTH the recipe list (db.recipes) AND a real, stored `key`. The key must be
stored, not a dynamic display name, because the barter contrib lists and matches
trade offers by obj.key (barter.py) -- a dynamic name would leave the trade
window showing a generic "recipe book". `scribe` (G.2) and any test spawn call
stamp(), so a book can never end up recipe-bearing-but-generically-named.

The recipe NAMES are listed on `look` -- a table of contents -- but not each
recipe's full detail block. A book is a traded good in a player-driven economy,
and barter already shows its key ("book of cloth, leather") in the trade window
(F.4), so hiding the names on `look` would be both buyer-hostile and incoherent
with the key. What the names do NOT grant is the craft: knowing a recipe's name
is neither knowing the recipe (you must still `learn` it, wearing the book, G.3)
nor being skilled enough to make it (min_skill) -- the three Stage 3 gates stay
intact. This contrasts with the scroll, which shows its single recipe's FULL
detail on `look` (a scroll is a note you read; a book is a contents list you
work through). Listing names needs no registry access -- db.recipes already
holds the canonical names -- so Book stays free of the _RECIPE_CLASSES coupling.
"""

from typeclasses.objects import Object
from typeclasses.durable import DurableObject


class Book(DurableObject, Object):
    """A perishable, multi-recipe book: named by its stamp, worn down per study."""

    def stamp(self, recipes):
        """Give this book its identity: the recipes it holds, and a distinct key.

        Sets the recipe list AND a real, searchable key ("book of <a>, <b>") in
        one place, so identity never depends on the command that made the book.
        Called by `scribe` (G.2) and by any other creation path (seeds, tests).
        The key is stored (not a dynamic display name) because barter matches and
        lists offers by obj.key; a dynamic name would show a generic book in the
        trade window (the same reason Scroll.stamp sets .key in F.4).

        The condition is NOT touched here: `scribe` sets the book's start
        condition from the author's craft outcome (G.2), and stamping is purely
        about identity, so the two concerns stay separate.

        Args:
            recipes (list[str]): the canonical recipe names to bind into the
                book, in author-declared order. Expected non-empty; scribe
                validates each name and mastery before calling.
        """
        # Store a plain copy so a later mutation of the caller's list cannot
        # reach back into the Attribute. A list Attribute round-trips as a
        # _SaverList, which is fine to read/iterate.
        self.db.recipes = list(recipes)
        self.key = "book of " + ", ".join(recipes)

    def get_display_desc(self, looker, **kwargs):
        """Render flavour + the recipe NAMES + the condition line on `look`.

        Composed self-contained (like Scroll.get_display_desc) rather than
        deferring to DurableObject's base+condition append, because the contents
        line must sit BETWEEN the flavour and the condition line. The condition
        line is still DurableObject's -- we call its condition_line() helper
        directly (it is explicitly a consumer-called renderer), so the colour
        banding stays in one place.

        The recipe NAMES are shown (a table of contents), not each recipe's full
        detail: a book is a traded good and barter already exposes its key, so a
        buyer must be able to read the contents. Names come straight from
        db.recipes (the canonical names), so no registry lookup is needed and
        Book never becomes a _RECIPE_CLASSES consumer. A blank, unstamped book
        (no recipes -- e.g. a raw test spawn) reads as blank so it is never
        mistaken for a finished one.
        """
        recipes = self.db.recipes or []
        if not recipes:
            flavour = "A blank book of bound cloth pages, waiting to be scribed."
        else:
            contents = ", ".join(recipes)
            flavour = (
                "A book of bound cloth pages, closely scribed with craft-notes. "
                f"It holds recipes for: {contents}. Studying any of them would "
                "teach how the work is done -- if your skill is equal to it."
            )
        # Blank line before the condition read, matching DurableObject's spacing.
        return f"{flavour}\n\n{self.condition_line()}"
