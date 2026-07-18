"""
Scroll typeclass (Stage 3, Component F.3).

A recipe scroll you can READ without consuming it. `inscribe` (F.1) stamps the
recipe name onto the instance (db.recipe); `learn` (F.2) consumes it to teach
that recipe. This adds the third verb -- `look` -- so a player can inspect what
a scroll teaches, and what it will demand of them, BEFORE deciding to study or
trade it.

Why a typeclass override rather than a `read` command or a baked-in desc:

* get_display_desc hangs the detail off the existing `look`, exactly as
  DurableObject hangs its condition line there -- one consistent surface where
  players inspect things, no new command, no ExtendedRoom `look` clash.
* It renders LIVE from the recipe registry, so a scroll written today still
  shows correct ingredients if the recipe is retuned later. Baking the detail
  into db.desc at inscribe-time would freeze stale numbers.

No visibility gate here, on purpose: to read a scroll you must hold it, and if
you hold it you could already `learn` it for free -- reading is strictly weaker
than the access you already have, so possession IS the gate. Resolution and
rendering live in world.knowledge, so this typeclass never touches the crafting
contrib's private recipe registry.
"""

from typeclasses.objects import Object
from world.knowledge import render_recipe_detail_by_name


class Scroll(Object):
    """A one-use recipe scroll: readable on `look`, consumed by `learn`."""

    def get_display_desc(self, looker, **kwargs):
        """Append the inscribed recipe's detail block to the scroll's desc.

        super() yields the flavour desc -- the blank-scroll text from the
        prototype, or the per-recipe line `inscribe` writes onto db.desc.
        render_recipe_detail_by_name adds the Needs/Tool/Skill/Output block when
        the scroll carries a recipe stamp that still exists in the registry; a
        blank scroll or a dangling stamp returns None, so `look` simply shows the
        base desc and never errors.
        """
        base = super().get_display_desc(looker, **kwargs)
        detail = render_recipe_detail_by_name(self.db.recipe)
        if not detail:
            return base
        return f"{base}\n{detail}" if base else detail
