"""
Activity report -- the offline reader of ``server/logs/activity.jsonl``.

Launch Minimum L2.3. The close-out question of the alpha is *did prices
move?*; this module answers it from the file alone, on any machine:

    python -m world.activity_report server/logs/activity.jsonl
    python -m world.activity_report server/logs/activity.jsonl --json

It reports counts per kind and per game-month, the price list (every trade
where one side gave exactly one item and no coin and the other side gave coin
only), copper paid by ``work`` per actor and per task, skill-improvement ticks
per skill, and a census of the kinds seen against ``KINDS``.

Design notes:

* **No Evennia or Django import, and no import of ``world.activity_log``.**
  That module imports ``django.conf.settings`` and ``evennia.utils.logger`` at
  module level, so reading ``KINDS`` from it would drag a configured Django
  into a script meant to run on a copied log file. ``KINDS`` is therefore a
  copy; ``tests/test_activity_report.py`` pins the copy to the original, and a
  subprocess test pins that importing this module loads neither framework.
* **Game-months are (year, month) pairs.** Every line's ``gt`` carries the
  game year (the L2.1 deviation), and a month number alone would merge the
  same month of two game years. The key is the string ``"YYYY-MM"``, the
  year zero-padded to four digits, so the aggregates survive ``json.dumps``
  and a plain string sort is chronological: unpadded, ``"10-01"`` sorts
  before ``"9-13"`` (found by the L2.3 protocol, where the live year is 1).
* **A malformed line is counted and skipped, never fatal.** The envelope is
  checked (a JSON object with a string ``kind`` and integer ``gt.year`` /
  ``gt.month``); payload fields are read defensively, so a trade with odd
  field types lands in *mixed* rather than raising.
* Standard library only, plain text to stdout.
"""

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict

# Copy of world.activity_log.KINDS -- see the module docstring for why it is a
# copy. tests/test_activity_report.py fails if the two drift apart.
KINDS = frozenset(
    {
        "gather",
        "craft",
        "dismantle",
        "trade",
        "work",
        "consume",
        "repair",
        "knowledge",
        "crumble",
        "improve",
    }
)


def _is_int(value):
    """True for a real int; ``bool`` is an int subclass and is not one here."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value):
    """True for an int or float that is not a ``bool``."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def month_key(year, month):
    """
    The game-month key: ``"0229-01"`` for month 1 of year 229.

    The year is zero-padded to four digits so that the string sort used for
    every month listing is chronological across a digit boundary (years 9 and
    10). Four digits cover game years 0-9999; at ``TIME_FACTOR = 4`` a game
    year is about 91 real days.
    """
    return f"{year:04d}-{month:02d}"


def parse_line(raw):
    """
    Parse one log line.

    Args:
        raw (str): One line of the file, without or with its newline.

    Returns:
        dict or None: The entry, or ``None`` when the line is malformed: not
        JSON, not a JSON object, or missing a string ``kind`` or an integer
        ``gt.year`` / ``gt.month``.
    """
    try:
        entry = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(entry, dict):
        return None
    gt = entry.get("gt")
    if not isinstance(entry.get("kind"), str) or not isinstance(gt, dict):
        return None
    if not (_is_int(gt.get("year")) and _is_int(gt.get("month"))):
        return None
    return entry


def _copper(value):
    """Copper on one side of a trade: ``None`` reads as 0; a bad type is ``None``."""
    if value is None:
        return 0
    if _is_int(value) and value >= 0:
        return value
    return None


def _items(value):
    """Item keys on one side of a trade, or ``None`` if not a list of strings."""
    if isinstance(value, list) and all(isinstance(key, str) for key in value):
        return value
    return None


def price_of(entry):
    """
    The (item, copper) price a trade line states, if it states one.

    A trade states a price when one side gave exactly one item and no coin and
    the other side gave coin only (no items, more than zero copper). Anything
    else -- coin on both sides, items on both sides, two items for coin, a
    gift, odd field types -- states no price and counts as *mixed*.

    Args:
        entry (dict): A parsed ``trade`` line.

    Returns:
        tuple or None: ``(item_key, copper)``, or ``None``.
    """
    a_items = _items(entry.get("a_items"))
    b_items = _items(entry.get("b_items"))
    a_copper = _copper(entry.get("a_copper"))
    b_copper = _copper(entry.get("b_copper"))
    if a_items is None or b_items is None or a_copper is None or b_copper is None:
        return None
    if len(a_items) == 1 and a_copper == 0 and not b_items and b_copper > 0:
        return a_items[0], b_copper
    if len(b_items) == 1 and b_copper == 0 and not a_items and a_copper > 0:
        return b_items[0], a_copper
    return None


def _actor_label(actor):
    """``"#7 Ann"`` from the line's ``[dbref, key]``; anything else as a string."""
    if isinstance(actor, list) and len(actor) == 2:
        return f"{actor[0]} {actor[1]}"
    return str(actor)


def _spread(values):
    """Count, min, median and max of a list of copper amounts."""
    return {
        "n": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def aggregate(lines):
    """
    Aggregate an iterable of raw log lines.

    Args:
        lines (iterable of str): The file's lines. Blank lines are ignored and
            not counted as malformed (a trailing newline is not damage).

    Returns:
        dict: Plain JSON-serializable aggregates -- ``lines`` (well-formed
        lines), ``malformed``, ``kinds``, ``months``, ``prices``, ``trades``,
        ``work``, ``improve`` and ``census``.
    """
    total = 0
    malformed = 0
    kinds = Counter()
    months = defaultdict(Counter)
    prices = defaultdict(lambda: defaultdict(list))
    trades = Counter({"priced": 0, "mixed": 0})
    work_actor = Counter()
    work_task = Counter()
    improve = defaultdict(lambda: {"ticks": 0, "xp": 0})

    for raw in lines:
        if not raw.strip():
            continue
        entry = parse_line(raw)
        if entry is None:
            malformed += 1
            continue
        total += 1
        kind = entry["kind"]
        month = month_key(entry["gt"]["year"], entry["gt"]["month"])
        kinds[kind] += 1
        months[month][kind] += 1

        if kind == "trade":
            price = price_of(entry)
            if price is None:
                trades["mixed"] += 1
            else:
                item, copper = price
                prices[item][month].append(copper)
                trades["priced"] += 1
        elif kind == "work":
            copper = entry.get("copper")
            if _is_int(copper):
                work_actor[_actor_label(entry.get("actor"))] += copper
                work_task[str(entry.get("task"))] += copper
        elif kind == "improve":
            row = improve[str(entry.get("skill"))]
            row["ticks"] += 1
            xp = entry.get("xp")
            if _is_number(xp):
                row["xp"] += xp

    seen = set(kinds)
    return {
        "lines": total,
        "malformed": malformed,
        "kinds": dict(sorted(kinds.items())),
        "months": {key: dict(sorted(months[key].items())) for key in sorted(months)},
        "prices": {
            item: {key: _spread(prices[item][key]) for key in sorted(prices[item])}
            for item in sorted(prices)
        },
        "trades": dict(trades),
        "work": {
            "by_actor": dict(sorted(work_actor.items())),
            "by_task": dict(sorted(work_task.items())),
        },
        "improve": {skill: improve[skill] for skill in sorted(improve)},
        "census": {
            "seen": sorted(seen & KINDS),
            "missing": sorted(KINDS - seen),
            "unknown": sorted(seen - KINDS),
        },
    }


def render(agg, source=""):
    """
    The plain-text report.

    Args:
        agg (dict): The result of ``aggregate()``.
        source (str, optional): The file name, shown in the header.

    Returns:
        str: The report, lines joined with newlines.
    """
    out = [f"activity report: {source}" if source else "activity report"]
    out.append(f"lines {agg['lines']} · malformed {agg['malformed']}")

    out.append("")
    out.append("per kind")
    if not agg["kinds"]:
        out.append("  (none)")
    for kind, count in agg["kinds"].items():
        out.append(f"  {kind:<10} {count}")

    out.append("")
    out.append("per game-month")
    if not agg["months"]:
        out.append("  (none)")
    for key, counts in agg["months"].items():
        cells = " · ".join(f"{kind} {count}" for kind, count in counts.items())
        out.append(f"  {key}  {cells}")

    out.append("")
    out.append("price list (copper; one item against coin only)")
    if not agg["prices"]:
        out.append("  (none)")
    for item, by_month in agg["prices"].items():
        for key, row in by_month.items():
            out.append(
                f"  {item:<20} {key}  n={row['n']}  min {row['min']}"
                f"  median {row['median']}  max {row['max']}"
            )
    trades = agg["trades"]
    out.append(f"  trades: {trades['priced']} priced · {trades['mixed']} mixed")

    out.append("")
    out.append("work (copper paid)")
    if not agg["work"]["by_actor"]:
        out.append("  (none)")
    for label, copper in agg["work"]["by_actor"].items():
        out.append(f"  actor  {label:<20} {copper}")
    for task, copper in agg["work"]["by_task"].items():
        out.append(f"  task   {task:<20} {copper}")

    out.append("")
    out.append("improve (ticks per skill)")
    if not agg["improve"]:
        out.append("  (none)")
    for skill, row in agg["improve"].items():
        out.append(f"  {skill:<20} ticks {row['ticks']}  xp {row['xp']}")

    census = agg["census"]
    out.append("")
    out.append(
        f"census: {len(census['seen'])} of {len(KINDS)} kinds seen"
        f"; missing: {', '.join(census['missing']) or '-'}"
        f"; unknown: {', '.join(census['unknown']) or '-'}"
    )
    return "\n".join(out)


def main(argv=None):
    """
    Command-line entry point.

    Args:
        argv (list, optional): Arguments without the program name; defaults to
            ``sys.argv[1:]``.

    Returns:
        int: 0 on success, 1 if the file cannot be read.
    """
    parser = argparse.ArgumentParser(
        prog="python -m world.activity_report",
        description="Offline counts and the price list from activity.jsonl.",
    )
    parser.add_argument("path", help="the activity log, e.g. server/logs/activity.jsonl")
    parser.add_argument("--json", action="store_true", help="dump the aggregates as JSON")
    args = parser.parse_args(argv)

    try:
        # errors="replace": a corrupt byte makes its line malformed (counted,
        # skipped) instead of a UnicodeDecodeError ending the report.
        with open(args.path, encoding="utf-8", errors="replace") as handle:
            agg = aggregate(handle)
    except OSError as err:
        print(f"activity_report: cannot read {args.path}: {err}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(agg, indent=2, ensure_ascii=False))
    else:
        print(render(agg, args.path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
