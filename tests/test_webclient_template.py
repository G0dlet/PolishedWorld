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
    "webclient/js/plugins/history.js",
    "webclient/js/plugins/default_in.js",
    "webclient/js/plugins/default_out.js",
    # Not a plugin (TestLayoutScript): opens and closes the panels below the
    # breakpoint, so its place after default_out costs nothing (W3.2).
    "polishedworld/js/layout.js",
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

# Any src= or href= whose value starts with a scheme or is protocol-relative.
# Run over the raw page, comments included.
EXTERNAL = re.compile(r"""(?:src|href)\s*=\s*["']?\s*(?:[a-z][a-z0-9+.-]*:|//)""", re.I)


class _Collector(HTMLParser):
    """Collects every tag's attributes and the ancestor chain of every id."""

    VOID = {"meta", "link", "br", "img", "input", "hr"}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.tags = []  # (tag, attrs dict)
        self.ancestors = {}  # id -> list of ancestor tags, nearest first

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
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
