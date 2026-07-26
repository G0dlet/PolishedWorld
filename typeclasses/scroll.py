"""
Scroll typeclass (Stage 3, Components F.3 + F.4).

A recipe scroll you can READ without consuming it. `inscribe` (F.1) stamps a
recipe onto the instance; `learn` (F.2) consumes it to teach that recipe; `look`
(F.3) shows what it teaches. F.4 moves the scroll's IDENTITY here too: its name,
its flavour, and its readable detail all derive from one stamp (db.recipe), so
every scroll is self-describing no matter how it was created.

Why identity lives on the typeclass, not in CmdInscribe:

* One source of truth. inscribe, future book-seeding (G), and test spawns all
  call stamp(), so a scroll can never end up stamped-but-unnamed (the "all
  scrolls read 'recipe scroll' until you look" confusion) or named-but-blank.
* The key must be a REAL stored key, not a dynamic get_display_name: the barter
  contrib lists and matches trade offers by obj.key (barter.py list()/offer
  matching), so a dynamic display name would leave the trade window showing a
  generic "recipe scroll". stamp() therefore sets .key.
* Flavour and detail render LIVE from the stamp (not a baked db.desc), so a
  retuned recipe shows correct numbers, and a blank scroll reads "blank" while a
  stamped one reads "inscribed" -- from the same code, every creation path.

No visibility gate on `look`: to read a scroll you must hold it, and if you hold
it you could already `learn` it for free -- reading is strictly weaker than the
access you already have, so possession IS the gate. Resolution and rendering
live in world.knowledge, so this typeclass never touches the crafting contrib's
private recipe registry.
"""

from typeclasses.objects import Object
from world.knowledge import render_recipe_detail_by_name


class Scroll(Object):
    """A one-use recipe scroll: named/described by its stamp, consumed by `learn`."""

    def stamp(self, recipe_name):
        """Give this scroll its identity: what it teaches, and a distinct key.

        Sets the recipe stamp AND a real, searchable key ("scroll of <recipe>")
        in one place. Called by inscribe and by any other creation path (seeds,
        tests) so identity never depends on the command. The key is stored (not
        a dynamic display name) because barter matches and lists offers by
        obj.key; a dynamic name would show a generic scroll in the trade window.

        Args:
            recipe_name (str): the canonical recipe name to inscribe.
        """
        self.db.recipe = recipe_name
        self.key = f"scroll of {recipe_name}"

    def get_display_desc(self, looker, **kwargs):
        """Render flavour + recipe detail from the stamp (F.4).

        Flavour now derives from db.recipe rather than a baked db.desc, so it is
        correct for every creation path: a blank scroll (no stamp) reads
        "blank", a stamped one reads "inscribed". render_recipe_detail_by_name
        appends the Needs/Tool/Skill/Output block when the recipe still resolves;
        a dangling stamp (recipe removed) shows flavour only and never errors on
        `look`.
        """
        recipe_name = self.db.recipe
        if not recipe_name:
            return "A blank scroll of woven cloth, waiting to be inscribed."

        flavour = (
            "A scroll of woven cloth, closely inscribed with craft-notes. "
            "Studying it would teach how the work is done."
        )
        detail = render_recipe_detail_by_name(recipe_name)
        return f"{flavour}\n{detail}" if detail else flavour
