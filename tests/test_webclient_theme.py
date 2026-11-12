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
                           text line gets class="undefined" (or, since W6.2,
                           its tab's class) and .out's pre-wrap never
                           reaches it; parse_html leaves the
                           spaces raw (Evennia 6.1.0).
    TestBreakpoint         a second breakpoint appears, or the one value
                           drifts from the query pw_text.js passes to
                           matchMedia (W6.1 lock 5).
    TestNoExternalCss      the stylesheet pulls a font or file from another
                           host, or @imports a stylesheet (WC2). W3.2 lock 8's
                           "no font files" is superseded for headings by the
                           visual pass's WV3: an @font-face may load one of
                           our own files, by a relative url().
    TestHeadingFont        the heading face is not the pinned file (a new
                           binary slipped in), its OFL notice is lost, a
                           heading falls back without a serif stack, the
                           browser fakes a bold because a rule asks for a
                           weight the face lacks, or a control or the text
                           picks the face up (visual pass V1.1, locks 2A, 3A).
    TestChrome             a box or control edge drops below 3:1 against
                           the surfaces (WCAG 1.4.11), a drawer turns
                           transparent over the text, the sections lose their
                           own boxes, the selected tab is told by colour only,
                           a heading loses its rule or outgrows the title, or
                           the ALPHA mark becomes unreadable (visual pass V1.2,
                           locks 1A-4A).
    TestIcons              an icon is missing, points at a file that is not
                           published, is drawn at a scale other than x1, is
                           smoothed instead of pixelated, carries content a
                           screen reader would read, or a published icon is
                           used by nothing (visual pass V3.2).
    TestGaugesAndLists     a gauge's value (numbers and description) leaves
                           the right edge or cannot wrap inside its column, so
                           a long description pushes the row out of its box
                           (V1.3 fix, lock A), an
                           item list loses its marker or "Nothing." gains one,
                           or an exit's arrow is read aloud or lost (V1.3,
                           1A-3A). That a grid gauge stays hidden is
                           TestCharacterFigure's and TestSurvivalBars'
                           test_hidden_wins_in_the_*_panel.
    TestTextTabs           a filtered tab shows lines of another tab or
                           hides the client's err/sys lines, All hides
                           anything, the tab row loses its own grid area
                           (it would scroll with the text or overlap it), or
                           a hidden unread mark shows (W6.2 locks 2A, 5B,
                           7A).
"""

import hashlib
import json
import re
from collections import namedtuple
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import SimpleTestCase

REPO = Path(settings.GAME_DIR)
# The heading face (visual pass V1.1). Alegreya[wght].ttf from google/fonts
# commit c30b221beb0c1da59d563feb91ec8656a1fa972a (ofl/alegreya; sha256 of
# the TTF ba5564634b93a8f8ba57b48cd4f1ae7417d2b4656fbac779028679b00de3cf12),
# instanced at wght 700 with fontTools 4.67.0 and brotli 1.2.1:
#   t = TTFont(ttf, recalcTimestamp=False)
#   f = instancer.instantiateVariableFont(t, {"wght": 700}, updateFontNames=True)
#   f.flavor = "woff2"; f.save(out)
# recalcTimestamp=False makes the output byte-for-byte repeatable.
HEADING_FAMILY = "Alegreya"
HEADING_WEIGHT = "700"
HEADING_FONT = "polishedworld/fonts/alegreya-bold.woff2"
HEADING_FONT_SHA256 = "160515d1858004e4c49fa2d6263854ac08571a23020aa62d23a98c2811597d70"
HEADING_LICENSE = "polishedworld/fonts/OFL.txt"
# The selectors set in the heading face (lock 3A): the header's title, the
# ALPHA mark inside it (V1.2) and the panels' h2.
HEADING_SELECTORS = (
    ".pw-title", ".pw-alpha", ".pw-char-name", ".pw-survival-title", ".pw-world-title",
    ".pw-room-title", ".pw-inventory-title",
)
# Controls keep the body's font (lock 3A).
CONTROL_SELECTORS = ('#pw-tabs [role="tab"]', "#inputsend", ".pw-panel-button", "#inputfield")
# Visual pass V1.2. Each panel section is its own box (lock 3A); the panel
# headings (the h2 group, one rule) and the title (lock 2A).
SECTION_SELECTOR = "#pw-panel-left > section"
PANEL_HEADINGS = (".pw-char-name", ".pw-survival-title", ".pw-world-title", ".pw-room-title", ".pw-inventory-title")
# The edges that mark where a box or a control is (WCAG 1.4.11): 3:1 against
# both surfaces, which is the palette's status flag.
EDGE_SELECTORS = (SECTION_SELECTOR, "#main", '#pw-tabs [role="tab"]', ".pw-panel-button", ".pw-alpha")
SELECTED_TAB = '#pw-tabs [role="tab"][aria-selected="true"]'
# Visual pass V3.2: each icon sits on a ::before beside a word that already
# says what it means (WC14), as a CSS background, so it is decoration by
# construction. Selector -> file under polishedworld/ui/icons/.
ICONS = {
    ".pw-char-name::before": "icon_character.png",
    ".pw-survival-title::before": "icon_survival.png",
    ".pw-inventory-title::before": "icon_inventory.png",
    ".pw-world-title::before": "icon_world.png",
    ".pw-room-title::before": "icon_location.png",
    "#pw-room-exits .pw-room-label::before": "icon_exits.png",
    "#pw-room-characters .pw-room-label::before": "icon_characters.png",
    "#pw-room-things .pw-room-label::before": "icon_things.png",
    "#pw-char-health::before": "status_health.png",
    "#pw-survival-hunger::before": "status_hunger.png",
    "#pw-survival-thirst::before": "status_thirst.png",
    "#pw-survival-fatigue::before": "status_fatigue.png",
}
ICON_DIR = "polishedworld/ui/icons/"
# Visual pass V1.3. The lists of things a player reads as items get a square
# marker (lock 2A); the exits get an arrow instead (lock 3A).
ITEM_LISTS = ("#pw-room-characters-list", "#pw-room-things-list", ".pw-inventory-list")
EXIT_ARROW = "#pw-room-exits-list > li::before"
PROJECT_CSS = REPO / "web" / "static" / "polishedworld" / "css" / "webclient.css"
EVENNIA_CSS = "webclient/css/webclient.css"
PALETTE = REPO / "art" / "palette" / "palette.json"
TEXT_JS = REPO / "web" / "static" / "polishedworld" / "js" / "pw_text.js"

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


def font_faces(css):
    """
    The declarations of every top-level @font-face block, as a list of dicts
    {property: value}. parse_css skips at-rule blocks other than @media, so
    the font rules need their own reader.
    """
    css = _strip_comments(css)
    faces = []
    for match in re.finditer(r"@font-face\s*\{([^{}]*)\}", css):
        decls = {}
        for decl in match.group(1).split(";"):
            if ":" in decl:
                prop, value = decl.split(":", 1)
                decls[prop.strip().lower()] = value.strip()
        faces.append(decls)
    return faces


def _family_names(value):
    """A font-family value as a list of names without quotes."""
    return [name.strip().strip("'\"") for name in value.split(",")]


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
        @font-face { font-family: "X"; src: url("../fonts/x.woff2") format("woff2"); }
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

    def test_font_face_reader_sees_the_block(self):
        self.assertEqual(
            font_faces(self.SAMPLE),
            [{"font-family": '"X"', "src": 'url("../fonts/x.woff2") format("woff2")'}],
        )
        self.assertEqual(_family_names('"A B", Georgia, serif'), ["A B", "Georgia", "serif"])

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

    def test_text_router_asks_for_the_same_breakpoint(self):
        # The call form, not a comment that names the value (W-af).
        source = TEXT_JS.read_text(encoding="utf-8")
        calls = re.findall(r"""matchMedia\(\s*["']\(min-width:\s*([0-9.]+[a-z]+)\)["']\s*\)""", source)
        self.assertEqual(calls, [BREAKPOINT])


class TestNoExternalCss(_ThemeTest):
    def test_no_import(self):
        for at_rule in self.at_rules:
            self.assertFalse(at_rule.startswith("@import"), at_rule)

    def test_font_faces_load_only_our_own_files(self):
        # Relative to the stylesheet (polishedworld/css/), so the file is
        # found under polishedworld/fonts/ whatever STATIC_URL is.
        faces = font_faces(PROJECT_CSS.read_text(encoding="utf-8"))
        for face in faces:
            urls = re.findall(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)", face.get("src", ""))
            self.assertTrue(urls, face)
            for _, url in urls:
                self.assertTrue(url.startswith("../fonts/"), url)
                self.assertTrue(url.endswith(".woff2"), url)
                self.assertIsNotNone(finders.find("polishedworld/fonts/" + url[len("../fonts/"):]), url)

    def test_no_url_to_another_host(self):
        for rule in self.rules:
            for prop, value in rule.decls:
                self.assertIsNone(
                    re.search(r"url\(\s*['\"]?\s*(?:[a-z][a-z0-9+.-]*:|//)", value, re.I),
                    "%s { %s: %s }" % (rule.selectors, prop, value),
                )


class TestCharacterFigure(_ThemeTest):
    """
    The silhouette is scaled by a whole factor in the template (×4, WC10);
    without `pixelated` the browser smooths the enlarged pixels into blur.
    The hidden rule keeps the health row hideable whatever display a later
    rule gives it: an author `display` beats the browser's own [hidden].
    """

    def test_figure_renders_pixelated(self):
        self.assertEqual(
            _decl_values(self.rules, ".pw-figure", ("image-rendering",)), ["pixelated"]
        )

    def test_hidden_wins_in_the_character_panel(self):
        self.assertEqual(_decl_values(self.rules, "#pw-char [hidden]", ("display",)), ["none"])


class TestSurvivalBars(_ThemeTest):
    """
    The survival panel (W5.2): the hidden rule keeps a row hideable as the
    character panel's does, and each bar has its own palette colour (lock
    3C). The colour only reinforces: the gauge's label and description say
    which gauge it is and how it stands (WC14).
    """

    def test_hidden_wins_in_the_survival_panel(self):
        self.assertEqual(_decl_values(self.rules, "#pw-survival [hidden]", ("display",)), ["none"])

    def test_each_bar_has_its_colour(self):
        got = {
            key: _decl_values(self.rules, "#pw-survival-%s-bar" % key, ("background",))
            for key in ("hunger", "thirst", "fatigue")
        }
        self.assertEqual(got, {
            "hunger": ["var(--pw-copper)"],
            "thirst": ["var(--pw-water)"],
            "fatigue": ["var(--pw-highlight)"],
        })


class TestWorldPanelHidden(_ThemeTest):
    """
    The world panel (W5.3): its rows start hidden and the weather row hides
    indoors, so the hidden rule must win in that panel as in the others.
    """

    def test_hidden_wins_in_the_world_panel(self):
        self.assertEqual(_decl_values(self.rules, "#pw-world [hidden]", ("display",)), ["none"])


class TestRoomPanelHidden(_ThemeTest):
    """
    The location panel (W5.4): its rows start hidden and a row hides when
    its list is empty, so the hidden rule must win there as in the others.
    """

    def test_hidden_wins_in_the_room_panel(self):
        self.assertEqual(_decl_values(self.rules, "#pw-room [hidden]", ("display",)), ["none"])


class TestInventoryPanelHidden(_ThemeTest):
    """
    The inventory panel (W7.1): its rows start hidden and hide again on a
    char frame without an inventory, so the hidden rule must win there as in
    the others.
    """

    def test_hidden_wins_in_the_inventory_panel(self):
        self.assertEqual(_decl_values(self.rules, "#pw-inventory [hidden]", ("display",)), ["none"])


class TestTextTabs(_ThemeTest):
    """
    The tabs filter one log (W6.2 lock 2A): #messagewindow carries the open
    tab in data-pw-tab, and a line without that tab's class, or the class
    every tab shows (the client's err/sys lines, lock 7A), is not displayed.
    All has no rule: it shows every line. The tab row is a grid area of its
    own in both layouts, so it stays put while <main> scrolls, and a hidden
    unread mark stays hidden (5B).
    """

    FILTERED = ("channels", "talk")

    def test_each_filtered_tab_hides_the_other_lines(self):
        for name in self.FILTERED:
            selector = '#messagewindow[data-pw-tab="%s"] > div:not(.pw-tab-%s):not(.pw-tab-every)' % (name, name)
            self.assertEqual(_decl_values(self.rules, selector, ("display",)), ["none"], selector)

    def test_all_hides_nothing(self):
        for rule in self.rules:
            for selector in rule.selectors:
                self.assertNotIn('data-pw-tab="all"', selector, selector)

    def test_tab_row_is_its_own_grid_area_in_both_layouts(self):
        self.assertEqual(_decl_values(self.rules, "#pw-tabs", ("grid-area",)), ["tabs"])
        media = "@media (min-width: %s)" % BREAKPOINT
        for where in (None, media):
            areas = _decl_values(self.rules, "#clientwrapper", ("grid-template-areas",), where)
            self.assertEqual(len(areas), 1, where)
            rows = re.findall(r'"([^"]*)"', areas[0])
            self.assertEqual([row.split().count("tabs") for row in rows].count(0), len(rows) - 1, rows)
            self.assertEqual(rows.index(next(r for r in rows if "tabs" in r)) + 1,
                             rows.index(next(r for r in rows if "text" in r)), rows)

    def test_hidden_wins_in_the_tabs(self):
        self.assertEqual(_decl_values(self.rules, "#pw-tabs [hidden]", ("display",)), ["none"])


class TestHeadingFont(_ThemeTest):
    def test_one_face_our_file_swapped_in(self):
        faces = font_faces(PROJECT_CSS.read_text(encoding="utf-8"))
        self.assertEqual(len(faces), 1, faces)
        face = faces[0]
        self.assertEqual(_family_names(face["font-family"]), [HEADING_FAMILY])
        self.assertEqual(face["src"], 'url("../fonts/%s") format("woff2")' % HEADING_FONT.rsplit("/", 1)[1])
        self.assertEqual(face["font-weight"], HEADING_WEIGHT)
        self.assertEqual(face["font-style"], "normal")
        self.assertEqual(face["font-display"], "swap")

    def test_hash_matches_pin(self):
        path = finders.find(HEADING_FONT)
        self.assertIsNotNone(path, HEADING_FONT)
        self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), HEADING_FONT_SHA256)

    def test_ofl_notice_kept(self):
        path = finders.find(HEADING_LICENSE)
        self.assertIsNotNone(path, HEADING_LICENSE)
        text = Path(path).read_text(encoding="utf-8")
        self.assertIn("SIL OPEN FONT LICENSE Version 1.1", text)
        self.assertIn("The Alegreya Project Authors", text)

    def test_headings_use_the_face_with_a_serif_fallback(self):
        for selector in HEADING_SELECTORS:
            families = _decl_values(self.rules, selector, ("font-family",))
            self.assertTrue(families, selector)
            names = _family_names(families[-1])
            self.assertEqual(names[0], HEADING_FAMILY, selector)
            self.assertEqual(names[-1], "serif", selector)

    def test_every_rule_with_the_face_asks_for_its_weight(self):
        # A weight the face lacks makes the browser synthesise one.
        for rule in self.rules:
            props = dict(rule.decls)
            if HEADING_FAMILY in _family_names(props.get("font-family", "")):
                self.assertEqual(props.get("font-weight"), HEADING_WEIGHT, rule.selectors)

    def test_controls_and_text_keep_their_fonts(self):
        for rule in self.rules:
            if not set(rule.selectors) & set(CONTROL_SELECTORS + ("body", "#main")):
                continue
            for prop, value in rule.decls:
                if prop in ("font", "font-family"):
                    self.assertNotIn(HEADING_FAMILY, _family_names(value), rule.selectors)


def _rem(value):
    match = re.fullmatch(r"([0-9.]+)rem", value.strip())
    return float(match.group(1)) if match else None


class TestChrome(_ThemeTest):
    def decl(self, selector, prop):
        values = _decl_values(self.rules, selector, (prop,))
        return values[-1] if values else None

    def test_sections_are_boxes_on_the_panel_surface(self):
        rules = [r for r in self.rules if r.media is None and SECTION_SELECTOR in r.selectors]
        self.assertTrue(rules, SECTION_SELECTOR)
        self.assertIn("#pw-panel-right > section", rules[-1].selectors)
        self.assertEqual(self.decl(SECTION_SELECTOR, "background"), "var(--pw-panel)")
        self.assertIn("var(--pw-copper)", self.decl(SECTION_SELECTOR, "border"))

    def test_sections_are_spaced(self):
        self.assertEqual(self.decl("#pw-panel-left > section + section", "margin-top"), ".5rem")
        self.assertEqual(self.decl("#pw-panel-right > section + section", "margin-top"), ".5rem")

    def test_columns_are_opaque_and_unframed(self):
        # Below the breakpoint a column is a fixed drawer over the text: it
        # must keep a surface of its own.
        self.assertEqual(self.decl("#pw-panel-left", "background"), "var(--pw-background)")
        self.assertEqual(self.decl("#pw-panel-left", "border"), "none")

    def test_box_and_control_edges_reach_3_to_1(self):
        seen = set()
        for rule in self.rules:
            hit = set(rule.selectors) & set(EDGE_SELECTORS + (SELECTED_TAB,))
            if not hit:
                continue
            for prop, value in rule.decls:
                if not prop.startswith("border") or prop.endswith(("radius", "width")):
                    continue
                for name in VAR.findall(value):
                    seen.update(hit)
                    self.assertTrue(
                        self.palette[name]["status"], "%s %s uses %s" % (rule.selectors, prop, name)
                    )
        self.assertEqual(seen - {SELECTED_TAB}, set(EDGE_SELECTORS))

    def test_selected_tab_is_marked_beyond_colour(self):
        self.assertEqual(self.decl(SELECTED_TAB, "font-weight"), "700")
        width = self.decl(SELECTED_TAB, "border-bottom-width")
        self.assertIsNotNone(width)
        self.assertGreaterEqual(int(re.fullmatch(r"(\d+)px", width).group(1)), 3)
        self.assertEqual(self.decl(SELECTED_TAB, "border-bottom-color"), "var(--pw-gold_link)")

    def test_tabs_round_every_corner(self):
        self.assertEqual(self.decl('#pw-tabs [role="tab"]', "border-radius"), ".25rem")

    def test_headings_have_a_rule_and_the_title_leads(self):
        for selector in PANEL_HEADINGS:
            self.assertEqual(_rem(self.decl(selector, "font-size")), 1.125, selector)
            self.assertIn("var(--pw-border_wood)", self.decl(selector, "border-bottom") or "", selector)
        self.assertGreater(_rem(self.decl(".pw-title", "font-size")), 1.125)

    def test_alpha_mark_is_readable_and_shown_in_capitals(self):
        fg = VAR.findall(self.decl(".pw-alpha", "color"))[0]
        bg = VAR.findall(self.decl(".pw-alpha", "background"))[0]
        self.assertGreaterEqual(contrast(self.palette[fg]["hex"], self.palette[bg]["hex"]), 4.5)
        self.assertEqual(self.decl(".pw-alpha", "text-transform"), "uppercase")


class TestIcons(_ThemeTest):
    def merged(self, selector):
        """Every declaration that applies to selector outside @media, last wins."""
        out = {}
        for rule in self.rules:
            if rule.media is None and selector in rule.selectors:
                out.update(dict(rule.decls))
        return out

    def test_every_icon_points_at_its_published_file(self):
        for selector, name in ICONS.items():
            with self.subTest(selector=selector):
                self.assertEqual(
                    self.merged(selector).get("background-image"), 'url("../ui/icons/%s")' % name
                )
                self.assertIsNotNone(finders.find(ICON_DIR + name), name)

    def test_every_published_icon_is_used(self):
        folder = finders.find(ICON_DIR.rstrip("/"))
        self.assertIsNotNone(folder, ICON_DIR)
        self.assertEqual(sorted(p.name for p in Path(folder).iterdir()), sorted(ICONS.values()))

    def test_icons_are_empty_decoration_at_x1_pixelated(self):
        # x1 is the only whole factor that fits beside the text (WC10); an
        # empty content string is skipped by screen readers.
        for selector in ICONS:
            with self.subTest(selector=selector):
                decls = self.merged(selector)
                self.assertEqual(decls.get("content"), '""')
                self.assertEqual(decls.get("width"), "32px")
                self.assertEqual(decls.get("height"), "32px")
                self.assertEqual(decls.get("background-size"), "32px 32px")
                self.assertEqual(decls.get("background-repeat"), "no-repeat")
                self.assertEqual(decls.get("image-rendering"), "pixelated")


class TestGaugesAndLists(_ThemeTest):
    def merged(self, selector):
        out = {}
        for rule in self.rules:
            if rule.media is None and selector in rule.selectors:
                out.update(dict(rule.decls))
        return out

    def test_gauge_value_sits_right_and_wraps_inside_its_column(self):
        # Two columns: the label, and the value (numbers and description in
        # one span, in DOM order). The value column may shrink below its
        # longest word and wraps inside itself, right-aligned, so "Fatigue
        # 0/100 exhausted" stays in a 17rem panel (V1.3 fix, lock A).
        gauge = self.merged(".pw-gauge")
        self.assertEqual(gauge.get("display"), "grid")
        self.assertEqual(gauge.get("grid-template-columns"), "auto minmax(0, 1fr)")
        self.assertEqual(self.merged(".pw-gauge-label").get("grid-column"), "1")
        value = self.merged(".pw-gauge-value")
        self.assertEqual(value.get("grid-column"), "2")
        self.assertEqual(value.get("min-width"), "0")
        self.assertEqual(value.get("text-align"), "right")
        self.assertEqual(value.get("overflow-wrap"), "anywhere")
        for inner in (".pw-gauge-numbers", ".pw-gauge-desc"):
            self.assertNotIn("grid-column", self.merged(inner), inner)
        self.assertEqual(self.merged(".pw-bar").get("grid-column"), "1 / -1")

    def test_item_lists_have_copper_square_markers(self):
        for selector in ITEM_LISTS:
            with self.subTest(selector=selector):
                self.assertEqual(self.merged(selector).get("list-style"), "square inside")
                self.assertEqual(self.merged(selector + " > li::marker").get("color"), "var(--pw-copper)")

    def test_nothing_is_not_an_item(self):
        self.assertEqual(self.merged(".pw-inventory-empty").get("list-style"), "none")

    def test_exits_have_a_silent_arrow_and_no_marker(self):
        self.assertEqual(self.merged("#pw-room-exits-list").get("list-style"), "none")
        decls = [d for r in self.rules if EXIT_ARROW in r.selectors for d in r.decls]
        contents = [v for p, v in decls if p == "content"]
        # A fallback without alt text first, then the one screen readers
        # read as nothing (the panel buttons' pattern).
        self.assertEqual(contents, ['"\\2192"', '"\\2192" / ""'])
        # The gap is a margin: a trailing space in content collapses in Firefox.
        self.assertEqual(self.merged(EXIT_ARROW).get("margin-right"), ".25rem")
        self.assertEqual(self.merged(EXIT_ARROW).get("color"), "var(--pw-gold_link)")
