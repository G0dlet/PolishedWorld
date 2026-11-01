"""
world/activity_report.py (Launch Minimum L2.3).

Plain ``TestCase``: the report is a file reader with no Evennia or Django in
it, so nothing here needs a database. The one exception is
``TestKindsPinned.test_copy_matches_activity_log``, which imports
``world.activity_log`` inside the test (Django is configured under
``evennia test``) to pin the report's copy of ``KINDS`` to the original.

The fixture is twenty lines in exactly the shapes the sixteen sites write
(L2.2, read live from the protocols), over three game-months chosen so that
month 1 occurs in two game years (0229-01 and 0230-01): a report that grouped
on the month number alone would merge them. Trades: three priced hoods in
0229-01 (10, 12, 30 copper -- median 12, mean 17.3), one priced knife in
0230-01 given by part_b (the mirror case), and one barter with coin on both
sides in 0229-02, which the price list must skip and count as *mixed*.
``dismantle`` and ``repair`` are absent on purpose, so the census has something
to report. The fixture's years all have three digits, which hid an ordering bug
the live clock (year 1) exposed; ``TestMonthOrder`` crosses the digit boundary.

Mutations LM-R1-R7 (STOPP 0, 2026-11-01) and LM-R8 (STOPP 1, 2026-11-02) name
the class that kills each.
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
from unittest import TestCase

from world import activity_report

ROOT = pathlib.Path(__file__).resolve().parents[1]

ANN = ["#7", "Ann"]
BO = ["#8", "Bo"]
CORPSE = ["#31", "corpse of Ann"]
M1 = {"year": 229, "month": 1, "day": 3, "hour": 9}
M2 = {"year": 229, "month": 2, "day": 14, "hour": 17}
M3 = {"year": 230, "month": 1, "day": 2, "hour": 11}


def _line(kind, actor, gt, **fields):
    """One log line in the envelope ``world.activity_log.record`` writes."""
    entry = {
        "ts": "2026-11-01T12:00:00.000+00:00",
        "gt": gt,
        "kind": kind,
        "actor": actor,
        "room": "#2",
        **fields,
    }
    return json.dumps(entry, ensure_ascii=False)


def _trade(gt, a_items, a_copper, b_items, b_copper):
    """A trade line between Ann (part_a, the actor) and Bo (part_b)."""
    return _line(
        "trade", ANN, gt, part_a=ANN, part_b=BO,
        a_items=a_items, b_items=b_items, a_copper=a_copper, b_copper=b_copper,
    )


FIXTURE = [
    # gather x3
    _line("gather", ANN, M1, command="forage", node="berry bush",
          prototype="WILD_BERRIES", yields=["wild berries"], success=True),
    _line("gather", ANN, M1, command="harvest", node="deer carcass",
          prototype="RAW_HIDE", yields=["raw hide"], success=True, part="hide"),
    _line("gather", BO, M2, command="forage", node="herb patch",
          prototype="HEALING_HERB", yields=["healing herb"], success=True),
    # craft x2
    _line("craft", ANN, M1, recipe="leather hood", consumed=["tanned leather"],
          product=["leather hood"], quality=52, tier="standard", duration=30),
    _line("craft", BO, M3, recipe="iron knife", consumed=["iron ingot"],
          product=["iron knife"], quality=61, tier="fine", duration=45),
    # trade x5: three priced hoods, one coin-on-both-sides (mixed), one mirrored knife
    _trade(M1, ["leather hood"], 0, [], 10),
    _trade(M1, ["leather hood"], 0, [], 12),
    _trade(M1, ["leather hood"], 0, [], 30),
    _trade(M2, ["leather hood"], 5, [], 20),
    _trade(M3, [], 25, ["iron knife"], 0),
    # work x3
    _line("work", ANN, M1, task="haul", copper=5, treasury="#10"),
    _line("work", ANN, M2, task="sweep", copper=3, treasury="#10"),
    _line("work", BO, M3, task="haul", copper=5, treasury="#10"),
    # consume x2
    _line("consume", ANN, M1, verb="eat", item="wild berries", gauge="hunger", delta=8),
    _line("consume", BO, M2, verb="drink", item="waterskin", gauge="thirst",
          delta=15, charges_left=4),
    # crumble, knowledge
    _line("crumble", CORPSE, M3, owner=7, lost=["iron knife"]),
    _line("knowledge", BO, M3, verb="learn", recipe="leather hood",
          medium="scroll", carrier="#44"),
    # improve x3
    _line("improve", ANN, M1, skill="survival", old=34, new=35, xp=6),
    _line("improve", ANN, M2, skill="survival", old=35, new=36, xp=7),
    _line("improve", BO, M3, skill="craft", old=41, new=42, xp=6),
]


def _write(lines):
    """Write lines to a temporary file and return its path (caller removes it)."""
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".jsonl", delete=False, encoding="utf-8"
    )
    with handle:
        handle.write("".join(line + "\n" for line in lines))
    return handle.name


class _FileTest(TestCase):
    """Writes ``LINES`` to a temp file and aggregates it through ``main``'s path."""

    LINES = FIXTURE

    def setUp(self):
        self.path = _write(self.LINES)
        self.addCleanup(os.remove, self.path)
        with open(self.path, encoding="utf-8") as handle:
            self.agg = activity_report.aggregate(handle)


class TestFixtureCounts(_FileTest):
    """Counts per kind and per (year, month). Pressured by LM-R3 (year dropped)."""

    def test_fixture_is_twenty_lines(self):
        self.assertEqual(len(FIXTURE), 20)
        self.assertEqual(self.agg["lines"], 20)
        self.assertEqual(self.agg["malformed"], 0)

    def test_counts_per_kind(self):
        self.assertEqual(
            self.agg["kinds"],
            {"consume": 2, "craft": 2, "crumble": 1, "gather": 3,
             "improve": 3, "knowledge": 1, "trade": 5, "work": 3},
        )

    def test_counts_per_game_month_keep_the_year(self):
        months = self.agg["months"]
        self.assertEqual(list(months), ["0229-01", "0229-02", "0230-01"])
        self.assertEqual(
            months["0229-01"],
            {"consume": 1, "craft": 1, "gather": 2, "improve": 1, "trade": 3, "work": 1},
        )
        self.assertEqual(
            months["0229-02"],
            {"consume": 1, "gather": 1, "improve": 1, "trade": 1, "work": 1},
        )
        self.assertEqual(
            months["0230-01"],
            {"craft": 1, "crumble": 1, "improve": 1, "knowledge": 1, "trade": 1, "work": 1},
        )


class TestMonthOrder(TestCase):
    """
    Month listings are chronological across a digit boundary. Pressured by
    LM-R8 (year not zero-padded): unpadded, "10-01" sorts before "9-13".
    """

    def test_months_sort_across_a_digit_boundary(self):
        y9 = {"year": 9, "month": 13, "day": 1, "hour": 8}
        y10 = {"year": 10, "month": 1, "day": 1, "hour": 8}
        y1 = {"year": 1, "month": 2, "day": 1, "hour": 8}
        lines = [
            _trade(y10, ["leather hood"], 0, [], 14),
            _trade(y9, ["leather hood"], 0, [], 11),
            _trade(y1, ["leather hood"], 0, [], 9),
        ]
        agg = activity_report.aggregate(lines)
        expected = ["0001-02", "0009-13", "0010-01"]
        self.assertEqual(list(agg["months"]), expected)
        self.assertEqual(list(agg["prices"]["leather hood"]), expected)


class TestPriceList(_FileTest):
    """
    The two price rows and the skipped barter. Pressured by LM-R1 (coin on the
    item side allowed), LM-R2 (mirror case dropped) and LM-R4 (median -> mean).
    """

    def test_exactly_two_price_rows(self):
        self.assertEqual(
            self.agg["prices"],
            {
                "iron knife": {"0230-01": {"n": 1, "min": 25, "median": 25, "max": 25}},
                "leather hood": {"0229-01": {"n": 3, "min": 10, "median": 12, "max": 30}},
            },
        )

    def test_coin_on_both_sides_is_mixed(self):
        self.assertEqual(self.agg["trades"], {"priced": 4, "mixed": 1})
        self.assertNotIn("0229-02", self.agg["prices"]["leather hood"])


class TestPriceRule(TestCase):
    """``price_of`` on single lines: what states a price and what does not."""

    def _price(self, a_items, a_copper, b_items, b_copper):
        line = _trade(M1, a_items, a_copper, b_items, b_copper)
        return activity_report.price_of(json.loads(line))

    def test_item_for_coin_both_ways(self):
        self.assertEqual(self._price(["hood"], 0, [], 9), ("hood", 9))
        self.assertEqual(self._price([], 9, ["hood"], 0), ("hood", 9))

    def test_null_copper_on_the_item_side_reads_as_zero(self):
        self.assertEqual(self._price(["hood"], None, [], 9), ("hood", 9))

    def test_shapes_that_state_no_price(self):
        self.assertIsNone(self._price(["hood", "hood"], 0, [], 18))  # two items
        self.assertIsNone(self._price(["hood"], 0, ["knife"], 0))    # item for item
        self.assertIsNone(self._price(["hood"], 0, [], 0))           # a gift
        self.assertIsNone(self._price([], 5, [], 9))                 # coin for coin
        self.assertIsNone(self._price(["hood"], 0, ["knife"], 9))    # item+coin for item
        self.assertIsNone(self._price(["hood"], 0, [], "9"))         # bad type
        self.assertIsNone(self._price(["hood"], 0, [], True))        # bool is not copper


class TestWorkAndImprove(_FileTest):
    """Copper paid per actor and per task; improve ticks and xp per skill."""

    def test_work_per_actor_and_per_task(self):
        self.assertEqual(
            self.agg["work"],
            {"by_actor": {"#7 Ann": 8, "#8 Bo": 5}, "by_task": {"haul": 10, "sweep": 3}},
        )

    def test_improve_per_skill(self):
        self.assertEqual(
            self.agg["improve"],
            {"craft": {"ticks": 1, "xp": 6}, "survival": {"ticks": 2, "xp": 13}},
        )


class TestCensus(_FileTest):
    """Kinds seen against ``KINDS``."""

    LINES = FIXTURE + [_line("haggle", ANN, M1)]

    def test_missing_and_unknown(self):
        census = self.agg["census"]
        self.assertEqual(census["missing"], ["dismantle", "repair"])
        self.assertEqual(census["unknown"], ["haggle"])
        self.assertEqual(len(census["seen"]), 8)
        self.assertEqual(self.agg["kinds"]["haggle"], 1)


class TestEmptyFile(_FileTest):
    """An empty file is a report of zeros, not an exception."""

    LINES = []

    def test_zeros(self):
        agg = self.agg
        self.assertEqual((agg["lines"], agg["malformed"]), (0, 0))
        self.assertEqual(agg["kinds"], {})
        self.assertEqual(agg["months"], {})
        self.assertEqual(agg["prices"], {})
        self.assertEqual(agg["trades"], {"priced": 0, "mixed": 0})
        self.assertEqual(agg["work"], {"by_actor": {}, "by_task": {}})
        self.assertEqual(agg["improve"], {})
        self.assertEqual(agg["census"]["missing"], sorted(activity_report.KINDS))

    def test_render_does_not_raise(self):
        text = activity_report.render(self.agg, "empty.jsonl")
        self.assertIn("lines 0 · malformed 0", text)
        self.assertIn("trades: 0 priced · 0 mixed", text)


class TestMalformedLines(_FileTest):
    """A malformed line is counted and skipped, not fatal. Pressured by LM-R5."""

    LINES = (
        FIXTURE[:10]
        + [
            "{not json",
            "[1, 2, 3]",
            json.dumps({"kind": "gather"}),                        # no gt
            json.dumps({"kind": "gather", "gt": {"year": 229}}),   # no month
            json.dumps({"kind": 7, "gt": M1}),                      # kind not a str
            "",                                                     # blank: not counted
        ]
        + FIXTURE[10:]
    )

    def test_counted_and_skipped(self):
        self.assertEqual(self.agg["malformed"], 5)
        self.assertEqual(self.agg["lines"], 20)
        self.assertEqual(self.agg["kinds"]["gather"], 3)


class TestRender(_FileTest):
    """The text report shows the aggregates; ``--json`` round-trips them."""

    def test_text_has_the_price_rows_and_the_census(self):
        text = activity_report.render(self.agg, "fixture.jsonl")
        self.assertIn("median 12", text)
        self.assertIn("trades: 4 priced · 1 mixed", text)
        self.assertIn("census: 8 of 10 kinds seen; missing: dismantle, repair", text)

    def test_aggregates_are_json(self):
        self.assertEqual(json.loads(json.dumps(self.agg)), self.agg)


class TestKindsPinned(TestCase):
    """The report's copy of ``KINDS`` is the log's. Pressured by LM-R6."""

    def test_copy_matches_activity_log(self):
        from world import activity_log  # Django is configured under `evennia test`

        self.assertEqual(activity_report.KINDS, activity_log.KINDS)


class TestStandalone(_FileTest):
    """
    The report runs as ``python -m`` on a bare interpreter and loads neither
    Django nor Evennia. Pressured by LM-R7 (KINDS imported from activity_log).
    """

    def _run(self, *args, code=None):
        env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
        cmd = [sys.executable, "-m", "world.activity_report", *args]
        if code is not None:
            cmd = [sys.executable, "-c", code, *args]
        return subprocess.run(
            cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60
        )

    def test_import_loads_no_framework(self):
        code = (
            "import sys; sys.path.insert(0, '.')\n"
            "from world import activity_report\n"
            "activity_report.main([sys.argv[1], '--json'])\n"
            "leaked = sorted({m.split('.')[0] for m in sys.modules} & {'django', 'evennia'})\n"
            "print('LEAKED', leaked, file=sys.stderr)\n"
        )
        result = self._run(self.path, code=code)
        self.assertIn("LEAKED []", result.stderr, result.stderr)

    def test_module_run_prints_the_report(self):
        result = self._run(self.path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("trades: 4 priced · 1 mixed", result.stdout)

    def test_json_switch(self):
        result = self._run(self.path, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), self.agg)

    def test_missing_file_exits_one(self):
        result = self._run(self.path + ".nope")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot read", result.stderr)
