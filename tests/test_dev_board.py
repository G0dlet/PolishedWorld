"""
Tests for the public dev board (BACKLOG *Public dev board*, locks A-E).

Each class names the bug it pressures:

    TestParseBoard        the parser files a card in the wrong column: a
                          bullet under an unknown heading lands in the column
                          above it, a sub-bullet becomes a card, a heading in
                          the wrong case opens a column, or the page order
                          follows the file instead of Planned/In progress/Done.
    TestBoardView         the page fails a visitor: a missing or broken file
                          gives a 500 instead of "Board unavailable", the page
                          asks for a login, or a cached read hides a moved
                          card until `evennia reload` (lock C).
    TestRoute             /board/ is served by something else -- Evennia's
                          root patterns follow the project's -- or the name
                          the menu and the help text use stops resolving.
    TestMenuLink          the override replaces Evennia's menu instead of
                          extending it (Home, Characters, Help gone), or the
                          link never appears.
    TestShippedBoard      a typo in a heading of docs/board.md empties a
                          column silently: every bullet in the file must
                          reach the page.
    TestHelpAlphaBoard    the help text names a path the site does not
                          serve, or the paragraph lands inside LM7's claims.
"""

import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from django.conf import settings
from django.urls import resolve, reverse
from evennia.utils.test_resources import EvenniaTest

from web.website.views import board
from world import alpha_contract

BOARD = """\
# Title

Intro text, and a stray bullet before any column:

- not a card

## Done

- Old thing
  - a sub-bullet, not a card
-
* Star bullet

## Planned

- Next thing

## Wishlist

- never shown

## In progress

- Current thing

### A subheading

- not a card either
"""


def _titles(columns):
    return [column["title"] for column in columns]


def _cards(columns, title):
    return next(c["cards"] for c in columns if c["title"] == title)


class TestParseBoard(TestCase):
    def setUp(self):
        self.columns = board.parse_board(BOARD)

    def test_columns_in_page_order_not_file_order(self):
        self.assertEqual(_titles(self.columns), ["Planned", "In progress", "Done"])

    def test_cards_land_in_their_columns(self):
        self.assertEqual(_cards(self.columns, "Planned"), ["Next thing"])
        self.assertEqual(_cards(self.columns, "In progress"), ["Current thing"])
        self.assertEqual(_cards(self.columns, "Done"), ["Old thing", "Star bullet"])

    def test_unknown_heading_closes_the_column_above(self):
        # "Wishlist" follows Planned; its bullet must not join Planned.
        every = [card for column in self.columns for card in column["cards"]]
        self.assertNotIn("never shown", every)

    def test_subheading_closes_the_column(self):
        every = [card for column in self.columns for card in column["cards"]]
        self.assertNotIn("not a card either", every)

    def test_bullet_before_any_column_is_skipped(self):
        every = [card for column in self.columns for card in column["cards"]]
        self.assertNotIn("not a card", every)

    def test_heading_case_must_match(self):
        columns = board.parse_board("## done\n\n- lower-case heading\n")
        self.assertEqual([c["cards"] for c in columns], [[], [], []])

    def test_bullet_with_no_text_is_skipped(self):
        # "- " with a trailing space passes the bullet test; the bare "-" in
        # BOARD never does, so it cannot pressure the empty-card rule.
        columns = board.parse_board("## Done\n\n- \n-   \n- Real card\n")
        self.assertEqual(_cards(columns, "Done"), ["Real card"])

    def test_empty_file_gives_three_empty_columns(self):
        columns = board.parse_board("")
        self.assertEqual(_titles(columns), list(board.COLUMNS))
        self.assertEqual([c["cards"] for c in columns], [[], [], []])


class TestBoardView(EvenniaTest):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "board.md"
        patcher = patch.object(board, "BOARD_PATH", self.path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def _get(self):
        return self.client.get("/board/")

    def test_renders_cards_without_login(self):
        self.path.write_text(BOARD, encoding="utf-8")
        self.client.logout()
        response = self._get()
        self.assertEqual(response.status_code, 200)
        for text in ("Planned", "In progress", "Done", "Current thing"):
            self.assertContains(response, text)
        self.assertNotContains(response, board.UNAVAILABLE)

    def test_missing_file_is_unavailable_not_500(self):
        response = self._get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, board.UNAVAILABLE)

    def test_directory_is_unavailable(self):
        self.path.mkdir()
        self.assertContains(self._get(), board.UNAVAILABLE)

    def test_non_utf8_is_unavailable(self):
        self.path.write_bytes(b"## Done\n\n- caf\xe9\n")
        self.assertContains(self._get(), board.UNAVAILABLE)

    def test_moved_card_shows_on_next_request(self):
        self.path.write_text("## Planned\n\n- Moving card\n", encoding="utf-8")
        first = self._get().context["columns"]
        self.path.write_text("## Done\n\n- Moving card\n", encoding="utf-8")
        second = self._get().context["columns"]
        self.assertEqual(_cards(first, "Planned"), ["Moving card"])
        self.assertEqual(_cards(second, "Done"), ["Moving card"])

    def test_card_text_is_escaped(self):
        self.path.write_text("## Done\n\n- <b>bold</b>\n", encoding="utf-8")
        response = self._get()
        self.assertContains(response, "&lt;b&gt;bold&lt;/b&gt;")
        self.assertNotContains(response, "<b>bold</b>")


class TestRoute(EvenniaTest):
    def test_name_reverses_to_board(self):
        self.assertEqual(reverse("board"), "/board/")

    def test_path_resolves_to_board_view(self):
        self.assertIs(resolve("/board/").func.view_class, board.BoardView)


class TestMenuLink(EvenniaTest):
    def test_link_added_and_evennia_menu_kept(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="%s"' % reverse("board"))
        for name in ("characters", "channels", "help"):
            self.assertContains(response, 'href="%s"' % reverse(name))


class TestShippedBoard(TestCase):
    def setUp(self):
        path = Path(settings.GAME_DIR) / "docs" / "board.md"
        self.text = path.read_text(encoding="utf-8")
        self.columns = board.parse_board(self.text)

    def test_every_bullet_reaches_a_column(self):
        bullets = [
            line for line in self.text.splitlines() if line.startswith(("- ", "* "))
        ]
        cards = sum(len(column["cards"]) for column in self.columns)
        self.assertEqual(cards, len(bullets))

    def test_card_count_is_lock_b(self):
        cards = sum(len(column["cards"]) for column in self.columns)
        self.assertGreaterEqual(cards, 10)
        self.assertLessEqual(cards, 15)

    def test_every_column_has_a_card(self):
        for column in self.columns:
            self.assertTrue(column["cards"], column["title"])


class TestHelpAlphaBoard(EvenniaTest):
    def test_names_the_served_path(self):
        self.assertIn(reverse("board"), alpha_contract.help_text())

    def test_is_the_last_paragraph(self):
        text = alpha_contract.help_text()
        self.assertGreater(text.find(reverse("board")), text.find("To report a bug"))
        self.assertIn(reverse("board"), text.split("\n\n")[-1])
