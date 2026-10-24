"""
Unit tests for the initial-setup hook. Alpha content epic, Task AC3.2.

The hook (server/conf/at_initial_setup.py) is four lines; what is worth
testing is the contract between those lines and Evennia's caller,
evennia/server/initial_setup.py at v6.1.0.

WHAT IS WORTH TESTING HERE
--------------------------
1. **No game import at module level.** Evennia swallows an ImportError raised
   while it imports the hook module and records the step as done: an empty
   world, for good. The test walks the module's source (AST, not grep, so a
   comment or a docstring mentioning `world` cannot trip it, and an import
   tucked under a module-level `if`/`try` cannot hide) and allows only the
   standard library, evennia and django. The walker itself is tested first on
   a fixture, so a walker that sees nothing cannot pass the real check.
2. **Evennia's own caller reaches the hook, and the hook seeds.** Calls go
   through `evennia.server.initial_setup.at_initial_setup()`, the function
   `handle_setup()` runs, with `seed_world` mocked. An empty hook, a renamed
   hook or a wrong AT_INITIAL_SETUP_HOOK_MODULE all fail here.
3. **Failure is loud.** A seed error and a broken `world.seeding` import both
   come out of Evennia's caller instead of being caught on the way: that is
   what stops startup and leaves the step to be re-run.
4. **The log carries the receipt.** Evennia's "Running at_initial_setup()
   hook." line is followed by the hook's summary line with the counts.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_initial_setup_hook
"""
import ast
import inspect
import sys
from unittest.mock import patch

from evennia.server import initial_setup as evennia_setup
from evennia.utils.test_resources import BaseEvenniaTestCase

from server.conf import at_initial_setup as hook

FRAMEWORK_PACKAGES = {"evennia", "django"}
EVENNIA_HOOK_LINE = "Initial setup: Running at_initial_setup() hook."
SUMMARY = {
    "rooms": {"created": 6, "skipped": 0},
    "exits": {"created": 11, "skipped": 0},
    "nodes": {"created": 9, "skipped": 0},
}


class _ModuleLevelImports(ast.NodeVisitor):
    """Collect (module, lineno) for every import that runs at import time."""

    def __init__(self):
        self.found = []

    def visit_FunctionDef(self, node):
        # A function body runs when called, not when the module is imported.
        # Its decorators and default values do run at import time.
        for expr in node.decorator_list + node.args.defaults + node.args.kw_defaults:
            if expr is not None:
                self.visit(expr)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Import(self, node):
        self.found.extend((alias.name, node.lineno) for alias in node.names)

    def visit_ImportFrom(self, node):
        self.found.append(("." * node.level + (node.module or ""), node.lineno))

    def visit_Call(self, node):
        name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
        if name in ("__import__", "import_module"):
            target = node.args[0] if node.args else None
            value = target.value if isinstance(target, ast.Constant) else "<dynamic>"
            self.found.append((value, node.lineno))
        self.generic_visit(node)


def module_level_imports(source):
    walker = _ModuleLevelImports()
    walker.visit(ast.parse(source))
    return walker.found


def forbidden(imports):
    """The imports whose top-level package is neither stdlib nor framework."""
    allowed = FRAMEWORK_PACKAGES | set(sys.stdlib_module_names)
    return [(mod, line) for mod, line in imports if mod.split(".")[0] not in allowed]


class TestModuleLevelImports(BaseEvenniaTestCase):
    def test_walker_sees_import_time_code_and_skips_function_bodies(self):
        fixture = (
            "import os\n"
            "from world.seeding import seed_world\n"
            "if True:\n"
            "    import typeclasses.rooms\n"
            "try:\n"
            "    from . import sibling\n"
            "except ImportError:\n"
            "    pass\n"
            "class Holder:\n"
            "    from commands import default_cmdsets\n"
            "x = __import__('utils.helpers')\n"
            "def hook():\n"
            "    from world.seeding import seed_world\n"
        )
        found = module_level_imports(fixture)
        self.assertIn(("os", 1), found)  # the walker sees allowed imports too
        self.assertEqual(
            forbidden(found),
            [
                ("world.seeding", 2),
                ("typeclasses.rooms", 4),
                (".", 6),
                ("commands", 10),
                ("utils.helpers", 11),
            ],
        )

    def test_hook_module_imports_only_framework_at_module_level(self):
        found = module_level_imports(inspect.getsource(hook))
        # Receipt that the real file was parsed: the logger import is there.
        self.assertIn("evennia.utils", [mod for mod, _ in found])
        self.assertEqual(forbidden(found), [])

    def test_the_function_does_import_the_seeder(self):
        # The other half of the rule: the import moved inside, not away.
        tree = ast.parse(inspect.getsource(hook.at_initial_setup))
        inner = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertEqual(inner, ["world.seeding"])


class TestEvenniaCallsTheHook(BaseEvenniaTestCase):
    def test_evennia_setup_reaches_the_hook_which_seeds_once(self):
        with patch("world.seeding.seed_world", return_value=SUMMARY) as seed:
            evennia_setup.at_initial_setup()
        seed.assert_called_once_with()

    def test_a_seed_failure_comes_out_of_evennia_setup(self):
        error = RuntimeError("seed_world: DEFAULT_HOME '#2' does not exist")
        with patch("world.seeding.seed_world", side_effect=error):
            with self.assertRaises(RuntimeError) as caught:
                evennia_setup.at_initial_setup()
        self.assertIs(caught.exception, error)

    def test_a_broken_seeding_import_comes_out_of_evennia_setup(self):
        # None in sys.modules makes `from world.seeding import ...` raise
        # ImportError -- the exception class Evennia swallows at module level.
        with patch.dict(sys.modules, {"world.seeding": None}):
            with self.assertRaises(ImportError):
                evennia_setup.at_initial_setup()

    def test_the_summary_is_logged_after_evennia_hook_line(self):
        with patch("world.seeding.seed_world", return_value=SUMMARY), patch.object(
            hook.logger, "log_info"
        ) as log_info:
            evennia_setup.at_initial_setup()
        lines = [call.args[0] for call in log_info.call_args_list]
        self.assertEqual(
            lines,
            [
                EVENNIA_HOOK_LINE,
                "Initial setup: seeded the alpha area: "
                "rooms 6 created / 0 skipped, exits 11 created / 0 skipped, "
                "nodes 9 created / 0 skipped.",
            ],
        )
