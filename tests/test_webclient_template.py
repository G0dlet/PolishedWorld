"""
Tests for the webclient page template (webclient decomposition W3.1, WC2/WC3;
W3.2 for the stylesheet order, landmarks and panel buttons).

Each class names the bug it pressures:

    TestPageRenders        /webclient/ is still served by Evennia's own
                           templates (the override is not picked up), or the
                           page errors.
    TestNoExternalHosts    a script, stylesheet or icon is loaded from another
                           host -- a CDN line copied back from upstream, or a
                           commented-out one (the browser ignores it, but it
                           is one uncomment away from shipping).
    TestVendoredJquery     the vendored jQuery is swapped or edited without
                           the pin moving with it, or its MIT notice is lost.
    TestStaticRefsExist    a src/href names a static file that no finder can
                           serve: a typo, or a plugin Evennia moved.
    TestScriptOrder        the plugins load in an order that breaks them:
                           default_in claims every keydown, so history after
                           it loses the arrow keys; default_out claims every
                           text and unknown command, so anything after it
                           never sees a message.
    TestSkeleton           the DOM no longer matches what Evennia's plugins
                           look up by id, or #messagewindow's grandparent is
                           not <main> (default_out scrolls the grandparent).
    TestStylesheetOrder    the project stylesheet loads before Evennia's, so
                           Evennia's stock rules (the black .out, the fixed
                           #input) win again.
    TestLandmarks          a side panel loses its label, Tab no longer
                           reaches input, panels and text in that order, or
                           a panel button stops naming the panel it opens.
    TestLayoutScript       layout.js turns into a plugin; loaded after
                           default_out, it would never see an event.
    TestStateScript        pw_state.js stops registering as a plugin, or its
                           domain list drifts from world.client_state.DOMAINS:
                           a domain the server adds and the client does not
                           claim falls through to default_out's unescaped
                           "Error or Unhandled event" line (W4.3). Its
                           behaviour is tested in Node: tests/js/.
"""

import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import Client
from evennia.utils.test_resources import EvenniaTest

REPO = Path(settings.GAME_DIR)
JQUERY = "polishedworld/vendor/jquery-3.7.1.min.js"
JQUERY_LICENSE = "polishedworld/vendor/jquery-3.7.1.LICENSE.txt"
# sha256 of jquery.min.js from the npm tarball jquery@3.7.1, whose sha512
# matched the registry's dist.integrity (2026-11-06). Base64 form, as the
# SRI string code.jquery.com publishes: sha256-/JqT3SQfawRcv/BIHPThkBvs0OEvtFFmqPF/lYI/Cxo=
JQUERY_SHA256 = "fc9a93dd241f6b045cbff0481cf4e1901becd0e12fb45166a8f17f95823f0b1a"

EXPECTED_SCRIPTS = [
    JQUERY,
    "webclient/js/evennia.js",
    "webclient/js/webclient_gui.js",
    # Project plugins: after webclient_gui.js (which defines plugin_handler),
    # before default_out, which claims every unknown command (W4.3).
    "polishedworld/js/pw_state.js",
    "webclient/js/plugins/history.js",
    "webclient/js/plugins/default_in.js",
    "webclient/js/plugins/default_out.js",
    # Not a plugin (TestLayoutScript): opens and closes the panels below the
    # breakpoint, so its place after default_out costs nothing (W3.2).
    "polishedworld/js/layout.js",
    # Not a plugin (TestGaugeScript): the one bar rule, a global the panel
    # renderers read when they run, so it comes before them (W5.2, lock 2B).
    "polishedworld/js/pw_gauge.js",
    # Not a plugin either (TestCharScript): a renderer that registers with
    # pw_state.on, so it only has to come after pw_state.js (W5.1).
    "polishedworld/js/pw_char.js",
    # The survival panel's renderer, the same kind as pw_char.js (W5.2).
    "polishedworld/js/pw_survival.js",
]

EXPECTED_STYLESHEETS = [
    "webclient/css/webclient.css",  # Evennia's, kept for the color-NNN classes
    "polishedworld/css/webclient.css",  # the project's, overrides by source order
]

PANEL_LABELS = {
    "pw-panel-left": "Character and survival",
    "pw-panel-right": "World and location",
}
LAYOUT_JS = "polishedworld/js/layout.js"
STATE_JS = "polishedworld/js/pw_state.js"
CHAR_JS = "polishedworld/js/pw_char.js"
GAUGE_JS = "polishedworld/js/pw_gauge.js"
SURVIVAL_JS = "polishedworld/js/pw_survival.js"
FIGURE = "polishedworld/characters/body/body_base.png"
# The ids pw_char.js writes to. A literal list, not one read from the script,
# so an empty list in the script cannot make these tests pass (W-z);
# tests/js/test_pw_char.js holds the same list for the script's side.
CHAR_IDS = (
    "pw-char",
    "pw-char-name",
    "pw-char-figure",
    "pw-char-health",
    "pw-char-health-numbers",
    "pw-char-health-desc",
    "pw-char-health-bar",
    "pw-char-enc",
)
# The ids pw_survival.js writes to (W5.2). Literal for the same reason;
# tests/js/test_pw_survival.js holds the same list.
SURVIVAL_IDS = (
    "pw-survival",
    "pw-survival-hunger",
    "pw-survival-hunger-numbers",
    "pw-survival-hunger-desc",
    "pw-survival-hunger-bar",
    "pw-survival-thirst",
    "pw-survival-thirst-numbers",
    "pw-survival-thirst-desc",
    "pw-survival-thirst-bar",
    "pw-survival-fatigue",
    "pw-survival-fatigue-numbers",
    "pw-survival-fatigue-desc",
    "pw-survival-fatigue-bar",
)
# Every markup sink a renderer must not write (Rev 5 (d)).
MARKUP_SINKS = ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write")

# Any src= or href= whose value starts with a scheme or is protocol-relative.
# Run over the raw page, comments included.
EXTERNAL = re.compile(r"""(?:src|href)\s*=\s*["']?\s*(?:[a-z][a-z0-9+.-]*:|//)""", re.I)


class _Collector(HTMLParser):
    """Collects every tag's attributes, the ids around it, and the ancestor chain of every id."""

    VOID = {"meta", "link", "br", "img", "input", "hr"}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.tags = []  # (tag, attrs dict)
        self.within = []  # per tag in self.tags: the ids of its ancestors
        self.ancestors = {}  # id -> list of ancestor tags, nearest first

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        self.within.append([a["id"] for _, a in self.stack if a.get("id")])
        if "id" in attrs:
            self.ancestors[attrs["id"]] = [t for t, _ in reversed(self.stack)]
        if tag not in self.VOID:
            self.stack.append((tag, attrs))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break


def _static_path(url):
    """'/static/x/y.js' -> 'x/y.js'; None for anything not under STATIC_URL."""
    if url and url.startswith(settings.STATIC_URL):
        return url[len(settings.STATIC_URL):]
    return None


class _PageTest(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.response = Client().get("/webclient/")
        self.html = self.response.content.decode("utf-8")
        self.page = _Collector()
        self.page.feed(self.html)

    def refs(self):
        """Every src/href value on the page, from parsed tags."""
        out = []
        for _tag, attrs in self.page.tags:
            for key in ("src", "href"):
                if attrs.get(key):
                    out.append(attrs[key])
        return out


class TestPageRenders(_PageTest):
    def test_status_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_project_templates_are_used(self):
        origins = {t.name: str(t.origin.name) for t in self.response.templates}
        game_templates = str(REPO / "web" / "templates")
        for name in ("webclient.html", "webclient/base.html"):
            self.assertIn(name, origins)
            self.assertTrue(
                origins[name].startswith(game_templates),
                f"{name} rendered from {origins[name]}, not the project's copy",
            )


class TestNoExternalHosts(_PageTest):
    def test_no_src_or_href_leaves_the_host(self):
        hits = EXTERNAL.findall(self.html)
        self.assertEqual(hits, [], f"external references on /webclient/: {hits}")

    def test_the_check_sees_the_page_refs(self):
        # Receipt that the check above ran against real attributes: the page
        # has its scripts and stylesheet, all local.
        refs = self.refs()
        self.assertGreaterEqual(len(refs), len(EXPECTED_SCRIPTS) + 1)
        for ref in refs:
            self.assertTrue(ref.startswith("/"), ref)
            self.assertFalse(ref.startswith("//"), ref)


class TestVendoredJquery(EvenniaTest):
    def test_hash_matches_pin(self):
        path = REPO / "web" / "static" / JQUERY
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), JQUERY_SHA256)

    def test_mit_notice_kept(self):
        text = (REPO / "web" / "static" / JQUERY_LICENSE).read_text(encoding="utf-8")
        self.assertIn("OpenJS Foundation", text)
        self.assertIn("Permission is hereby granted, free of charge", text)


class TestStaticRefsExist(_PageTest):
    def test_every_static_ref_is_findable(self):
        static_refs = [p for p in map(_static_path, self.refs()) if p]
        self.assertGreaterEqual(len(static_refs), len(EXPECTED_SCRIPTS) + 1)
        missing = [p for p in static_refs if not finders.find(p)]
        self.assertEqual(missing, [])


class TestScriptOrder(_PageTest):
    def test_scripts_in_load_bearing_order(self):
        srcs = [_static_path(a["src"]) for t, a in self.page.tags if t == "script" and a.get("src")]
        self.assertEqual(srcs, EXPECTED_SCRIPTS)


class TestSkeleton(_PageTest):
    def test_ids_evennia_plugins_look_up(self):
        for element_id in ("messagewindow", "inputfield", "inputsend", "prompt", "clientwrapper"):
            self.assertIn(element_id, self.page.ancestors, element_id)

    def test_messagewindow_grandparent_is_main(self):
        ancestors = self.page.ancestors["messagewindow"]
        self.assertEqual(ancestors[1], "main", ancestors)

    def test_two_side_panels(self):
        asides = [a.get("id") for t, a in self.page.tags if t == "aside"]
        self.assertEqual(asides, ["pw-panel-left", "pw-panel-right"])


class TestStylesheetOrder(_PageTest):
    def test_project_stylesheet_after_evennias(self):
        hrefs = [
            _static_path(a["href"])
            for t, a in self.page.tags
            if t == "link" and a.get("rel") == "stylesheet"
        ]
        self.assertEqual(hrefs, EXPECTED_STYLESHEETS)


class TestLandmarks(_PageTest):
    def _index(self, predicate, what):
        for i, (tag, attrs) in enumerate(self.page.tags):
            if predicate(tag, attrs):
                return i
        self.fail("not on the page: %s" % what)

    def test_panel_labels(self):
        labels = {a.get("id"): a.get("aria-label") for t, a in self.page.tags if t == "aside"}
        self.assertEqual(labels, PANEL_LABELS)

    def test_tab_order_input_then_panels_then_text(self):
        inputfield = self._index(lambda t, a: a.get("id") == "inputfield", "#inputfield")
        send = self._index(lambda t, a: a.get("id") == "inputsend", "#inputsend")
        first_aside = self._index(lambda t, a: t == "aside", "<aside>")
        main = self._index(lambda t, a: t == "main", "<main>")
        self.assertLess(inputfield, send)
        self.assertLess(send, first_aside)
        self.assertLess(first_aside, main)

    def test_no_positive_tabindex(self):
        for tag, attrs in self.page.tags:
            if "tabindex" in attrs:
                self.assertLessEqual(int(attrs["tabindex"]), 0, (tag, attrs))

    def test_panel_buttons_control_the_panels(self):
        buttons = [a for t, a in self.page.tags if t == "button" and a.get("aria-controls")]
        self.assertEqual(sorted(a["aria-controls"] for a in buttons), sorted(PANEL_LABELS))
        for attrs in buttons:
            self.assertEqual(attrs.get("type"), "button", attrs)
            self.assertEqual(attrs.get("aria-expanded"), "false", attrs)


class TestLayoutScript(EvenniaTest):
    def test_not_a_plugin(self):
        path = finders.find(LAYOUT_JS)
        self.assertIsNotNone(path, LAYOUT_JS)
        self.assertNotIn("plugin_handler", Path(path).read_text(encoding="utf-8"))


class TestStateScript(EvenniaTest):
    def setUp(self):
        super().setUp()
        path = finders.find(STATE_JS)
        self.assertIsNotNone(path, STATE_JS)
        self.source = Path(path).read_text(encoding="utf-8")

    def test_registers_as_plugin(self):
        self.assertIn('plugin_handler.add("pw_state", pw_state)', self.source)

    def test_domains_match_the_server(self):
        from world.client_state import DOMAINS

        found = re.findall(r"^\s*var DOMAINS = \[([^\]]*)\];", self.source, re.M)
        self.assertEqual(len(found), 1, "one DOMAINS literal in %s" % STATE_JS)
        names = re.findall(r'"([a-z_]+)"', found[0])
        self.assertEqual(tuple(names), DOMAINS)


class TestCharScript(EvenniaTest):
    """
    pw_char.js is a renderer, not a plugin: registering with plugin_handler
    would put it in the onUnknownCmd chain beside pw_state. It writes the
    snapshot as text only (Rev 5 (d)): a character name can hold markup.
    """

    def setUp(self):
        super().setUp()
        path = finders.find(CHAR_JS)
        self.assertIsNotNone(path, CHAR_JS)
        self.source = Path(path).read_text(encoding="utf-8")

    def test_not_a_plugin(self):
        self.assertNotIn("plugin_handler", self.source)

    def test_registers_for_char(self):
        # The call, not the bare name: the header comment names it too (W-g).
        self.assertIn('pw_state.on("char", function', self.source)

    def test_never_writes_markup(self):
        for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
            self.assertNotIn(sink, self.source, sink)


class TestCharPanel(_PageTest):
    """
    The character panel's markup (W5.1, WC10, WC12, WC14): it sits in the
    left panel, holds every id the renderer writes, shows the figure at a
    whole factor with words in its alt, and nothing in a panel is a live
    region, so a gauge change never interrupts the text being read.
    """

    def _index(self, element_id):
        for i, (_tag, attrs) in enumerate(self.page.tags):
            if attrs.get("id") == element_id:
                return i
        self.fail("not on the page: #%s" % element_id)

    def test_every_id_the_renderer_writes(self):
        for element_id in CHAR_IDS:
            self._index(element_id)

    def test_inside_the_left_panel(self):
        for element_id in CHAR_IDS:
            i = self._index(element_id)
            self.assertIn("pw-panel-left", self.page.within[i], element_id)

    def test_section_named_by_its_heading(self):
        tag, attrs = self.page.tags[self._index("pw-char")]
        self.assertEqual(tag, "section")
        self.assertEqual(attrs.get("aria-labelledby"), "pw-char-name")

    def test_figure_has_words(self):
        tag, attrs = self.page.tags[self._index("pw-char-figure")]
        self.assertEqual(tag, "img")
        self.assertTrue((attrs.get("alt") or "").strip(), attrs)
        self.assertEqual(_static_path(attrs.get("src")), FIGURE)

    def test_figure_at_four_times_native(self):
        with open(finders.find(FIGURE), "rb") as png:
            header = png.read(24)
        self.assertEqual(header[12:16], b"IHDR")
        width = int.from_bytes(header[16:20], "big")
        height = int.from_bytes(header[20:24], "big")
        _tag, attrs = self.page.tags[self._index("pw-char-figure")]
        self.assertEqual((int(attrs["width"]), int(attrs["height"])), (4 * width, 4 * height))

    def test_bar_is_hidden_from_screen_readers(self):
        # The fill sits in its track; the track hides both, since the text
        # beside it already says everything the bar shows (WC14).
        i = self._index("pw-char-health-bar")
        track_tag, track = self.page.tags[i - 1]
        self.assertEqual((track_tag, track.get("class")), ("span", "pw-bar"))
        self.assertEqual(track.get("aria-hidden"), "true", track)

    def test_no_live_region_in_the_panels(self):
        for i, (tag, attrs) in enumerate(self.page.tags):
            inside = {"pw-panel-left", "pw-panel-right"} & set(self.page.within[i] + [attrs.get("id")])
            if not inside:
                continue
            self.assertNotIn("aria-live", attrs, (tag, attrs))
            self.assertNotIn(attrs.get("role"), ("log", "status", "alert", "timer", "marquee"), (tag, attrs))


def _read_static(name):
    path = finders.find(name)
    if path is None:
        raise AssertionError("not found: %s" % name)
    return Path(path).read_text(encoding="utf-8")


class TestGaugeScript(EvenniaTest):
    """
    pw_gauge.js holds the one bar rule (W5.2, lock 2B): a library the panel
    renderers read, never a plugin and never a renderer itself. Two copies
    of barWidth would be two knobs for one job, so the rule is defined in
    this file and nowhere else among the project's scripts.
    """

    def setUp(self):
        super().setUp()
        self.source = _read_static(GAUGE_JS)

    def test_not_a_plugin_nor_a_renderer(self):
        self.assertNotIn("plugin_handler", self.source)
        self.assertNotIn("pw_state", self.source)

    def test_bar_rule_defined_once(self):
        js_dir = Path(finders.find(GAUGE_JS)).parent
        owners = sorted(
            p.name for p in js_dir.glob("*.js")
            if "function barWidth" in p.read_text(encoding="utf-8")
        )
        self.assertEqual(owners, ["pw_gauge.js"])

    def test_renderers_read_it(self):
        for name in (CHAR_JS, SURVIVAL_JS):
            self.assertIn("pw_gauge", _read_static(name), name)


class TestSurvivalScript(EvenniaTest):
    """
    pw_survival.js is a renderer like pw_char.js (W5.2): registered with
    pw_state.on, never with plugin_handler; it writes text only, and its
    gauge list is the server's, in the server's order.
    """

    def setUp(self):
        super().setUp()
        self.source = _read_static(SURVIVAL_JS)

    def test_not_a_plugin(self):
        self.assertNotIn("plugin_handler", self.source)

    def test_registers_for_survival(self):
        # The call, not the bare name: the header comment names it too (W-g).
        self.assertIn('pw_state.on("survival", function', self.source)

    def test_never_writes_markup(self):
        for sink in MARKUP_SINKS:
            self.assertNotIn(sink, self.source, sink)

    def test_gauges_match_the_server(self):
        from world.client_state import SURVIVAL_GAUGES

        found = re.findall(r"^\s*var GAUGES = \[([^\]]*)\];", self.source, re.M)
        self.assertEqual(len(found), 1, "one GAUGES literal in %s" % SURVIVAL_JS)
        names = re.findall(r'"([a-z_]+)"', found[0])
        self.assertEqual(tuple(names), SURVIVAL_GAUGES)


class TestSurvivalPanel(_PageTest):
    """
    The survival panel's markup (W5.2, WC12, WC14): its own section in the
    left panel, after the character panel, named by its heading, holding
    every id the renderer writes; each bar is hidden from screen readers
    because the words beside it say the same. TestCharPanel's live-region
    test already covers everything in the left panel.
    """

    def _index(self, element_id):
        for i, (_tag, attrs) in enumerate(self.page.tags):
            if attrs.get("id") == element_id:
                return i
        self.fail("not on the page: #%s" % element_id)

    def test_every_id_the_renderer_writes(self):
        for element_id in SURVIVAL_IDS:
            self._index(element_id)

    def test_inside_the_left_panel_after_the_character(self):
        for element_id in SURVIVAL_IDS:
            i = self._index(element_id)
            self.assertIn("pw-panel-left", self.page.within[i], element_id)
            self.assertNotIn("pw-char", self.page.within[i], element_id)
        self.assertGreater(self._index("pw-survival"), self._index("pw-char"))

    def test_section_named_by_its_heading(self):
        tag, attrs = self.page.tags[self._index("pw-survival")]
        self.assertEqual(tag, "section")
        heading = attrs.get("aria-labelledby")
        self.assertEqual(heading, "pw-survival-title")
        self.assertEqual(self.page.tags[self._index(heading)][0], "h2")

    def test_rows_in_status_order(self):
        rows = [self._index("pw-survival-" + key) for key in ("hunger", "thirst", "fatigue")]
        self.assertEqual(rows, sorted(rows))

    def test_bars_are_hidden_from_screen_readers(self):
        for key in ("hunger", "thirst", "fatigue"):
            i = self._index("pw-survival-%s-bar" % key)
            track_tag, track = self.page.tags[i - 1]
            self.assertEqual((track_tag, track.get("class")), ("span", "pw-bar"), key)
            self.assertEqual(track.get("aria-hidden"), "true", key)
