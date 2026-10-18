"""
Consistency tests: world/material_registry.py against the content that ships.

Alpha Content Epic, Task AC1.1.

WHY THIS FILE EXISTS
--------------------
The registry is hand-maintained prose-as-data. It drifted: LeatherRecipe
shipped on 2026-06-30 and the registry still said tanning was an open
decision, while `feather` and `tusk` were marked EXISTS with no creature that
yields them. Every document that asked the registry "does X exist?" was told
the wrong thing. These tests make the registry answer to the code:

  (a)  status <-> code: an entry is EXISTS iff some prototype carries its tag
       (crafting_material for MATERIALS, crafting_tool for TOOLS).
  (a') an EXISTS entry's own prototype_key carries the entry's tag.
  (b)  no unregistered tags: every such tag on a prototype is a registry key.
  (c)  every EXISTS material is consumed by some recipe.
  (d)  every EXISTS tool is used: some recipe's tool_tag, or some node
       prototype's required_tool (T3).
  (e)  every recipe input (consumable_tags, tool_tag) is an EXISTS entry.
  (f)  every EXISTS prototype_key has a source in code: a node's
       yield_prototype, a harvest part in a template some prototype's
       harvest_template names, or a recipe's output_prototypes.

Checking the consumer without the source (c without f) recreates the feather
error one layer down; (f) closes that.

HOW THE DATA IS READ (same paths production uses)
-------------------------------------------------
* Prototypes: `search_prototype(no_db=True)` loads settings.PROTOTYPE_MODULES
  and returns homogenized copies. Tags arrive as (key, category, data), so a
  tag's category is t[1]; non-reserved keys such as yield_prototype and
  harvest_template arrive as attrs (key, value, category, lockstring).
* Recipes: `_load_recipes()` then `_RECIPE_CLASSES` -- the registry the
  crafting contrib itself resolves `craft <name>` against (keyed on cls.name),
  as world/knowledge.py and commands/crafting_commands.py already do.

Each per-entry check runs in a subTest, so one run names every bad entry.
A guard runs first: an empty prototype or recipe set would make every
"for each ... assert" loop pass vacuously.

(d)'s node branch (T3) landed in AC2.2 with TREE, the first node prototype to
set `required_tool`. Its receipt is the `axe` entry: no recipe names the axe as
its tool_tag, so without the branch (d) fails on it.
"""

from evennia.contrib.game_systems.crafting.crafting import (
    _load_recipes,
    _RECIPE_CLASSES,
)
from evennia.prototypes.prototypes import search_prototype
from evennia.utils.test_resources import EvenniaTestCase

from world import material_registry as reg
from world.harvest_templates import HARVEST_TEMPLATES

MATERIAL_CATEGORY = "crafting_material"
TOOL_CATEGORY = "crafting_tool"

# (registry section, tag category, label) -- materials and tools are checked
# by the same rules, each against its own tag category.
SECTIONS = (
    (reg.MATERIALS, MATERIAL_CATEGORY, "material"),
    (reg.TOOLS, TOOL_CATEGORY, "tool"),
)

# Floors for the vacuity guard, set at AC1.1's counts (30 prototypes, 8
# recipes). A floor, not a census: content added since does not move it.
MIN_PROTOTYPES = 30
MIN_RECIPES = 8


def _prototypes():
    """All module prototypes, homogenized (tags/attrs as tuples)."""
    return search_prototype(no_db=True)


def _recipes():
    """All recipe classes, as the crafting contrib registers them."""
    _load_recipes()
    return list(_RECIPE_CLASSES.values())


def _tags(proto, category):
    """Tag keys on a homogenized prototype in the given category."""
    return {tag[0] for tag in proto.get("tags", []) if tag[1] == category}


def _attr(proto, name):
    """Value of a homogenized attr (e.g. yield_prototype), or None."""
    for attr in proto.get("attrs", []):
        if attr[0] == name:
            return attr[1]
    return None


def _sourced_prototype_keys(prototypes, recipes):
    """prototype_keys that code can actually produce today (check f)."""
    sourced = set()
    for proto in prototypes:
        yielded = _attr(proto, "yield_prototype")
        if yielded:
            sourced.add(yielded)
        template = HARVEST_TEMPLATES.get(_attr(proto, "harvest_template"))
        if template:
            sourced.update(part["prototype"] for part in template.values())
    for cls in recipes:
        sourced.update(cls.output_prototypes or [])
    return sourced


class TestMaterialRegistry(EvenniaTestCase):
    """The registry's claims, checked against prototypes, recipes and sources."""

    def setUp(self):
        super().setUp()
        self.prototypes = _prototypes()
        self.recipes = _recipes()
        self.by_key = {p["prototype_key"]: p for p in self.prototypes}
        self.sourced = _sourced_prototype_keys(self.prototypes, self.recipes)
        self.consumed = {t for cls in self.recipes for t in (cls.consumable_tags or [])}
        self.tool_tags = {cls.tool_tag for cls in self.recipes
                          if getattr(cls, "tool_tag", None)}
        # T3: a node's required_tool uses a tool as much as a recipe does.
        # Read through _attr() -- required_tool arrives as a homogenized attr.
        self.tool_tags |= {_attr(p, "required_tool") for p in self.prototypes
                           if _attr(p, "required_tool")}

    def _carried(self, category):
        """Every tag key in `category` carried by any prototype."""
        return set().union(*(_tags(p, category) for p in self.prototypes))

    def test_guard_data_is_not_empty(self):
        """Without data every loop below passes vacuously -- refuse that."""
        self.assertGreaterEqual(len(self.prototypes), MIN_PROTOTYPES)
        self.assertGreaterEqual(len(self.recipes), MIN_RECIPES)
        self.assertTrue(self.sourced)

    def test_a_exists_iff_some_prototype_carries_tag(self):
        for section, category, label in SECTIONS:
            carried = self._carried(category)
            for key, entry in section.items():
                with self.subTest(label=label, key=key, status=entry["status"]):
                    self.assertEqual(key in carried, entry["status"] == reg.EXISTS)

    def test_a_prime_exists_prototype_key_carries_its_tag(self):
        for section, category, label in SECTIONS:
            for key, entry in section.items():
                if entry["status"] != reg.EXISTS:
                    continue
                with self.subTest(label=label, key=key, proto=entry["prototype_key"]):
                    proto = self.by_key.get(entry["prototype_key"])
                    self.assertIsNotNone(proto, "prototype_key not in PROTOTYPE_MODULES")
                    self.assertIn(key, _tags(proto, category))

    def test_b_no_unregistered_tags_on_prototypes(self):
        for section, category, label in SECTIONS:
            for proto in self.prototypes:
                for tag in _tags(proto, category):
                    with self.subTest(label=label, proto=proto["prototype_key"], tag=tag):
                        self.assertIn(tag, section)

    def test_c_every_exists_material_is_consumed(self):
        for key, entry in reg.MATERIALS.items():
            if entry["status"] != reg.EXISTS:
                continue
            with self.subTest(material=key):
                self.assertIn(key, self.consumed)

    def test_d_every_exists_tool_is_used(self):
        for key, entry in reg.TOOLS.items():
            if entry["status"] != reg.EXISTS:
                continue
            with self.subTest(tool=key):
                self.assertIn(key, self.tool_tags)

    def test_e_every_recipe_input_is_an_exists_entry(self):
        for cls in self.recipes:
            for tag in cls.consumable_tags or []:
                with self.subTest(recipe=cls.name, consumable=tag):
                    self.assertIn(tag, reg.MATERIALS)
                    self.assertEqual(reg.MATERIALS[tag]["status"], reg.EXISTS)
            tool = getattr(cls, "tool_tag", None)
            if tool:
                with self.subTest(recipe=cls.name, tool=tool):
                    self.assertIn(tool, reg.TOOLS)
                    self.assertEqual(reg.TOOLS[tool]["status"], reg.EXISTS)

    def test_f_every_exists_prototype_has_a_source(self):
        for section, _category, label in SECTIONS:
            for key, entry in section.items():
                if entry["status"] != reg.EXISTS:
                    continue
                with self.subTest(label=label, key=key, proto=entry["prototype_key"]):
                    self.assertIn(entry["prototype_key"], self.sourced)
