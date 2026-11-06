"""
Tests for the webclient stylesheet (webclient decomposition W3.2).

The project's web/static/polishedworld/css/webclient.css is linked after
Evennia's webclient/css/webclient.css (kept for its colour classes) and
overrides that file's layout and message rules. These tests read both files
as text; no browser is involved.

Each class names the bug it pressures:

    TestCssReader          the reader these tests rely on misses a rule
                           (inside @media, after a comment) or the contrast
                           arithmetic disagrees with palette.json's own
                           numbers -- every other test would then pass or
                           fail for the wrong reason.
    TestPaletteVariables   a palette colour changes in palette.json and the
                           CSS keeps the old hex; a --pw-* name is invented,
                           declared twice, or misspelt where it is used.
    TestColourRoles        a colour marked text:false (serious, magic, grass,
                           water, ...) is used for text, a focus outline uses
                           a colour below 3:1, or a raw hex bypasses the
                           palette altogether.
    TestAnsiContrast       a base ANSI colour class from the server's
                           ANSI-to-HTML output (|b, |R, |G ...) is unreadable
                           on the text area's surface.
    TestStockOverrides     one of Evennia's stock rules still wins: the black
                           box behind .out, the fixed #input, the 8 px font
                           Evennia sets below 480 px, its monospace body.
    TestMessageWhitespace  the server's runs of spaces collapse again: the
                           banner and every EvTable lose their columns.
                           default_out.js:13 picks the class 'out' only when
                           kwargs is null, but the server always sends an
                           object (wire_formats/evennia_v1.py:103 dumps
                           [cmd, args, kwargs], kwargs {} at least), so a
                           text line gets class="undefined" and .out's
                           pre-wrap never reaches it; parse_html leaves the
                           spaces raw (Evennia 6.1.0).
    TestBreakpoint         a second breakpoint appears, or the one value
                           drifts from the 80rem W6.1's matchMedia will use.
    TestNoExternalCss      the stylesheet pulls a font or file from another
                           host, or a font file at all (WC2, lock 8).
"""

import json
import re
from collections import namedtuple
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import SimpleTestCase

REPO = Path(settings.GAME_DIR)
PROJECT_CSS = REPO / "web" / "static" / "polishedworld" / "css" / "webclient.css"
EVENNIA_CSS = "webclient/css/webclient.css"
PALETTE = REPO / "art" / "palette" / "palette.json"

# The text area's surface; ANSI colour classes must be readable on it.
TEXT_SURFACE = "background"
# The single layout breakpoint (lock 7). W6.1's matchMedia uses this value.
BREAKPOINT = "80rem"
# Effective-colour check covers the 16 base ANSI classes (lock 3).
BASE_ANSI = [".color-%03d" % i for i in range(16)]

Rule = namedtuple("Rule", "media selectors decls")

VAR = re.compile(r"var\(\s*--pw-([A-Za-z0-9_-]+)\s*\)")
RAW_COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgb|rgba|hsl|hsla)\(", re.I)
ANSI_SELECTOR = re.compile(r"^\.color-\d{3}$")


# ---------------------------------------------------------------- readers


def _strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def parse_css(css, media=None):
    """
    Return (rules, at_rules) for a stylesheet.

    rules: Rule(media, selectors, decls) for every style rule, including those
    inside @media blocks (media holds the @media prelude, None at top level).
    decls is a list of (property, value) in source order.
    at_rules: every at-rule prelude seen (@media, @import, @font-face, ...).
    Blocks of other at-rules (@keyframes, @font-face) are not read as rules.
    """
    css = _strip_comments(css)
    rules, at_rules = [], []
    i, n = 0, len(css)
    while i < n:
        brace = css.find("{", i)
        semi = css.find(";", i)
        if semi != -1 and (brace == -1 or semi < brace) and css[i:semi].strip().startswith("@"):
            at_rules.append(css[i:semi].strip())
            i = semi + 1
            continue
        if brace == -1:
            break
        prelude = css[i:brace].strip()
        depth, end = 1, brace + 1
        while depth:
            if end >= n:
                raise ValueError("unbalanced braces after %r" % prelude)
            depth += {"{": 1, "}": -1}.get(css[end], 0)
            end += 1
        body = css[brace + 1:end - 1]
        if prelude.startswith("@media"):
            at_rules.append(prelude)
            inner_rules, inner_at = parse_css(body, prelude)
            rules += inner_rules
            at_rules += inner_at
        elif prelude.startswith("@"):
            at_rules.append(prelude)
        else:
            selectors = tuple(s.strip() for s in prelude.split(","))
            decls = []
            for decl in body.split(";"):
                if ":" in decl:
                    prop, value = decl.split(":", 1)
                    decls.append((prop.strip().lower(), value.strip()))
            rules.append(Rule(media, selectors, decls))
        i = end
    return rules, at_rules


def _luminance(hex_colour):
    h = hex_colour.lstrip("#")
    channels = [int(h[k:k + 2], 16) / 255 for k in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    """WCAG 2.x contrast ratio between two #RRGGBB colours."""
    la, lb = sorted((_luminance(a), _luminance(b)))
    return (lb + 0.05) / (la + 0.05)


def _palette():
    data = json.loads(PALETTE.read_text(encoding="utf-8"))
    return {c["key"]: c for c in data["colors"]}


def _decl_values(rules, selector, props, media=None):
    """Values of props in top-level (or given media) rules naming selector, in order."""
    return [
        value
        for rule in rules
        if rule.media == media and selector in rule.selectors
        for prop, value in rule.decls
        if prop in props
    ]


class _ThemeTest(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.palette = _palette()
        cls.rules, cls.at_rules = parse_css(PROJECT_CSS.read_text(encoding="utf-8"))
        evennia_path = finders.find(EVENNIA_CSS)
        cls.evennia_rules, _ = parse_css(Path(evennia_path).read_text(encoding="utf-8"))

    def root_vars(self):
        """--pw-* declarations in :root, as a list of (name, value)."""
        return [
            (prop[len("--pw-"):], value)
            for rule in self.rules
            if ":root" in rule.selectors
            for prop, value in rule.decls
            if prop.startswith("--pw-")
        ]

    def all_pw_declarations(self):
        return [
            (rule, prop, value)
            for rule in self.rules
            for prop, value in rule.decls
            if prop.startswith("--pw-")
        ]


# ---------------------------------------------------------------- tests


class TestCssReader(SimpleTestCase):
    SAMPLE = """
        @import url("x.css");
        /* .hidden { color: red; } */
        body { color: var(--pw-text); background: #000 }
        @media (min-width: 80rem) { #main, aside { display: grid; } }
        @keyframes blink { to { visibility: hidden; } }
    """

    def test_reader_sees_media_rules_and_skips_comments(self):
        rules, at_rules = parse_css(self.SAMPLE)
        selectors = [r.selectors for r in rules]
        self.assertIn(("body",), selectors)
        self.assertIn(("#main", "aside"), selectors)
        self.assertNotIn((".hidden",), selectors)
        self.assertNotIn(("to",), selectors)
        media = [r.media for r in rules if r.selectors == ("#main", "aside")]
        self.assertEqual(media, ["@media (min-width: 80rem)"])
        self.assertTrue(any(a.startswith("@import") for a in at_rules), at_rules)

    def test_contrast_matches_palette_json(self):
        palette = _palette()
        bg = palette["background"]["hex"]
        for key, colour in palette.items():
            self.assertAlmostEqual(
                contrast(colour["hex"], bg), colour["contrast_background"], delta=0.01, msg=key
            )


class TestPaletteVariables(_ThemeTest):
    def test_every_palette_colour_is_declared_with_its_hex(self):
        declared = dict(self.root_vars())
        for key, colour in self.palette.items():
            self.assertIn(key, declared, "--pw-%s missing" % key)
            self.assertEqual(declared[key].lower(), colour["hex"].lower(), key)

    def test_every_pw_variable_is_a_palette_key(self):
        for name, _value in self.root_vars():
            self.assertIn(name, self.palette, "--pw-%s is not in palette.json" % name)

    def test_each_variable_declared_once_in_root_only(self):
        names = [prop for _rule, prop, _value in self.all_pw_declarations()]
        self.assertEqual(len(names), len(set(names)), "a --pw-* is declared twice")
        for rule, prop, _value in self.all_pw_declarations():
            self.assertEqual(rule.selectors, (":root",), prop)
            self.assertIsNone(rule.media, prop)

    def test_every_var_reference_resolves(self):
        declared = {name for name, _value in self.root_vars()}
        for rule in self.rules:
            for prop, value in rule.decls:
                for name in VAR.findall(value):
                    self.assertIn(name, declared, "%s { %s: %s }" % (rule.selectors, prop, value))


class TestColourRoles(_ThemeTest):
    def test_text_uses_text_colours_only(self):
        for rule in self.rules:
            for prop, value in rule.decls:
                if prop != "color":
                    continue
                for name in VAR.findall(value):
                    self.assertTrue(
                        self.palette[name]["text"], "%s uses text:false %s" % (rule.selectors, name)
                    )

    def test_focus_outline_uses_status_colours_only(self):
        for rule in self.rules:
            for prop, value in rule.decls:
                if prop not in ("outline", "outline-color"):
                    continue
                for name in VAR.findall(value):
                    self.assertTrue(
                        self.palette[name]["status"],
                        "%s outline uses status:false %s" % (rule.selectors, name),
                    )

    def test_no_raw_colour_outside_root_and_ansi(self):
        for rule in self.rules:
            if rule.selectors == (":root",) or all(ANSI_SELECTOR.match(s) for s in rule.selectors):
                continue
            for prop, value in rule.decls:
                self.assertIsNone(
                    RAW_COLOUR.search(value), "%s { %s: %s }" % (rule.selectors, prop, value)
                )


class TestAnsiContrast(_ThemeTest):
    def test_text_surface_is_the_palette_background(self):
        values = _decl_values(self.rules, "#main", ("background", "background-color"))
        self.assertTrue(values, "#main sets no background")
        self.assertEqual(VAR.findall(values[-1]), [TEXT_SURFACE])

    def test_base_colours_readable_on_text_surface(self):
        surface = self.palette[TEXT_SURFACE]["hex"]
        for selector in BASE_ANSI:
            ours = _decl_values(self.rules, selector, ("color",))
            stock = _decl_values(self.evennia_rules, selector, ("color",))
            effective = (ours or stock)[-1]
            self.assertGreaterEqual(
                contrast(effective, surface), 4.5, "%s %s" % (selector, effective)
            )


class TestStockOverrides(_ThemeTest):
    # (selector, accepted properties) -- each must be set by a top-level rule,
    # which wins over Evennia's by source order (same selector, later file).
    REQUIRED = [
        ("body", ("background", "background-color")),
        ("body", ("color",)),
        ("body", ("font-family",)),
        ("body", ("font-size",)),
        ("body", ("line-height",)),
        (".out", ("background", "background-color")),
        (".out", ("color",)),
        (".inp", ("color",)),
        (".sys", ("color",)),
        (".err", ("color",)),
        (".prompt", ("color",)),
        ("#input", ("position",)),
        ("#inputfield", ("background", "background-color")),
        ("#inputfield", ("color",)),
        ("#inputfield", ("font-family",)),
        ("#inputfield", ("font-size",)),
    ]

    def test_stock_rules_overridden(self):
        for selector, props in self.REQUIRED:
            self.assertTrue(
                _decl_values(self.rules, selector, props), "%s does not set %s" % (selector, props)
            )

    def test_input_not_fixed(self):
        self.assertNotIn("fixed", _decl_values(self.rules, "#input", ("position",)))

    def test_text_and_input_are_monospace_panels_are_not(self):
        for selector in ("#main", "#inputfield"):
            families = _decl_values(self.rules, selector, ("font-family",))
            self.assertTrue(families, selector)
            self.assertEqual(families[-1].split(",")[-1].strip(), "monospace", selector)
        body = _decl_values(self.rules, "body", ("font-family",))[-1]
        self.assertIn("system-ui", body)
        self.assertEqual(body.split(",")[-1].strip(), "sans-serif")


class TestMessageWhitespace(_ThemeTest):
    def test_every_message_line_keeps_its_spaces(self):
        values = _decl_values(self.rules, "#messagewindow > div", ("white-space",))
        self.assertEqual(values[-1:], ["pre-wrap"])


class TestBreakpoint(_ThemeTest):
    def test_one_breakpoint(self):
        widths = re.findall(
            r"(?:min|max)-width\s*:\s*([0-9.]+[a-z]+)",
            " ".join(a for a in self.at_rules if a.startswith("@media")),
        )
        self.assertTrue(widths, "no breakpoint")
        self.assertEqual(set(widths), {BREAKPOINT})


class TestNoExternalCss(_ThemeTest):
    def test_no_import_or_font_face(self):
        for at_rule in self.at_rules:
            self.assertFalse(at_rule.startswith(("@import", "@font-face")), at_rule)

    def test_no_url_to_another_host(self):
        for rule in self.rules:
            for prop, value in rule.decls:
                self.assertIsNone(
                    re.search(r"url\(\s*['\"]?\s*(?:[a-z][a-z0-9+.-]*:|//)", value, re.I),
                    "%s { %s: %s }" % (rule.selectors, prop, value),
                )
