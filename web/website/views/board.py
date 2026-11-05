"""
The public dev board: a read-only kanban page at ``/board/`` (BACKLOG *Public
dev board*, locks A-F, 2026-11-04).

``docs/board.md`` is the one source. Three ``## `` headings are columns --
``Planned``, ``In progress``, ``Done`` -- and every top-level bullet under one
is a card. The roadmap stays the truth; the board is its shop window, moved
at epic start and close-out.

Why the file is read on every request (lock C): a moved card shows without an
``evennia reload``. Fifteen cards and a handful of visitors make that cheap,
and nothing is cached, so nothing can go stale. Nothing is written either, so
concurrent visitors share no state and cannot race.

Why a broken source renders a page, not an error (lock D): a missing,
unreadable or non-UTF-8 file shows "Board unavailable" with status 200. The
board is a convenience; it must never put a 500 in front of a visitor or a
traceback in the server log.

``parse_board`` uses the standard library only, so it is tested without a
request and without a database.
"""

from pathlib import Path

from django.conf import settings
from django.views.generic import TemplateView

# Column order on the page. The file may list them in any order.
COLUMNS = ("Planned", "In progress", "Done")

# Read per request through the module global, so a test can patch it.
BOARD_PATH = Path(settings.GAME_DIR) / "docs" / "board.md"

UNAVAILABLE = "Board unavailable"


def parse_board(text):
    """
    Parse the board's Markdown into columns.

    Args:
        text (str): The contents of ``docs/board.md``.

    Returns:
        list: One dict per column, in ``COLUMNS`` order, each
        ``{"title": str, "cards": [str, ...]}``. Cards keep file order.

    Rules (lock D):
        * A line starting ``## `` whose title is in ``COLUMNS`` (exact
          case) opens that column.
        * Any other heading -- an unknown ``## ``, a ``# `` title, a
          ``### `` -- closes the open column, so the bullets under it are
          skipped rather than filed in the column above.
        * A card is a top-level ``- `` or ``* `` bullet with text. Indented
          bullets, empty bullets and bullets outside a column are skipped.
    """
    cards = {title: [] for title in COLUMNS}
    current = None
    for line in text.splitlines():
        if line.startswith("#"):
            title = line[3:].strip() if line.startswith("## ") else None
            current = title if title in cards else None
            continue
        if current is None or not line.startswith(("- ", "* ")):
            continue
        card = line[2:].strip()
        if card:
            cards[current].append(card)
    return [{"title": title, "cards": cards[title]} for title in COLUMNS]


class BoardView(TemplateView):
    """``/board/``: the columns of ``docs/board.md``, no login, no model."""

    template_name = "website/board.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Dev board"
        context["unavailable"] = UNAVAILABLE
        try:
            text = BOARD_PATH.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Missing, a directory, unreadable, or not UTF-8 (lock D).
            context["columns"] = None
        else:
            context["columns"] = parse_board(text)
        return context
