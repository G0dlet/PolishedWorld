#!/usr/bin/env python3
"""
PolishedWorld's mutation harness: run a task's tests against deliberate
mistakes and print a summary short enough to paste.

Usage, from anywhere inside the repository, with the game's venv active:

    python tools/mutate.py tools/mutants/he_t1.toml
    python tools/mutate.py tools/mutants/he_t1.toml --only HEM1 HEM3
    python tools/mutate.py tools/mutants/he_t1.toml --parallel 4

The spec is data, read with `tomllib` and never executed:

    modules = ["tests.test_hero_points"]

    [[mutant]]
    id = "HEM1"
    file = "world/hero_points.py"
    old = '''    return stored
    '''
    new = '''    return stored or START
    '''
    expect = "test_stored_zero_reads_zero"   # or a list of names

What the harness holds to (Testing Reference §27.1):

- The unmutated tree runs first. If it is not green, nothing else runs: a
  mutant killed by a suite that was already red proves nothing.
- Each mutant's `old` must occur exactly once in its file, or the mutant is
  SKIPPED with the count -- a string that matches twice mutates a place no
  one chose, and one that matches nowhere mutates nothing.
- Every file is restored from a copy held in memory, never from git (which
  would wipe uncommitted work), and its sha256 is checked against the copy
  before the next mutant. A mismatch stops the run.
- `__pycache__` under the game's packages is emptied before and after each
  run, and Python writes none (`PYTHONDONTWRITEBYTECODE=1`), so a stale
  compiled file never answers for the source.
- stdout and stderr are both read: unittest writes FAIL and ERROR to
  stderr, and a harness that read stdout alone would call every mutant
  survived (lesson 70).
- Mutants run one after another, since they write to the same files; the
  tests inside each run go in parallel through `ForkTestRunner`.
- `expect` names the test the decomposition predicts will kill the mutant.
  A kill by another test is marked `(other: ...)`, so luck is not read as
  the prediction holding (lesson 181).

It imports nothing from Evennia or Django; `evennia test` runs as a
subprocess in the repository root.
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIRS = ("commands", "server", "typeclasses", "web", "world", "tests")
RUNNER = "server.test_runner.ForkTestRunner"
DEFAULT_TIMEOUT = 1800

RAN = re.compile(r"^Ran (\d+) tests? in ([\d.]+)s", re.MULTILINE)
FAILED = re.compile(r"^FAILED \((.*)\)$", re.MULTILINE)
OK = re.compile(r"^OK(?: \(.*\))?$", re.MULTILINE)
CASE = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+)\)", re.MULTILINE)


class SpecError(Exception):
    """The spec file cannot be used as written."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load_spec(path):
    """
    Read and check a spec.

    Returns:
        tuple: (modules, mutants, timeout), mutants as dicts with id, file,
            old, new and expect (a list of names, possibly empty).

    Raises:
        SpecError: on a missing key, a duplicate id or a file outside the
            repository.
    """
    try:
        with open(path, "rb") as handle:
            spec = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as err:
        raise SpecError(f"cannot read {path}: {err}") from err
    modules = spec.get("modules")
    if not modules or not all(isinstance(m, str) for m in modules):
        raise SpecError("`modules` must be a non-empty list of test labels")
    timeout = spec.get("timeout", DEFAULT_TIMEOUT)
    mutants, seen = [], set()
    for number, raw in enumerate(spec.get("mutant", []), start=1):
        missing = [k for k in ("id", "file", "old", "new") if k not in raw]
        if missing:
            raise SpecError(f"mutant #{number} lacks {', '.join(missing)}")
        if raw["id"] in seen:
            raise SpecError(f"mutant id {raw['id']} appears twice")
        seen.add(raw["id"])
        target = (ROOT / raw["file"]).resolve()
        if ROOT not in target.parents or not target.is_file():
            raise SpecError(f"{raw['id']}: {raw['file']} is not a file in the repository")
        if raw["old"] == raw["new"]:
            raise SpecError(f"{raw['id']}: old and new are the same")
        expect = raw.get("expect", [])
        if isinstance(expect, str):
            expect = [expect]
        mutants.append({**raw, "path": target, "expect": list(expect)})
    if not mutants:
        raise SpecError("the spec has no [[mutant]] tables")
    return modules, mutants, timeout


def evennia_command():
    """The `evennia` launcher of the running interpreter's environment."""
    beside = Path(sys.executable).parent / "evennia"
    if beside.exists():
        return str(beside)
    found = shutil.which("evennia")
    if found:
        return found
    raise SpecError("no `evennia` launcher found; activate the game's venv")


def clear_caches():
    for top in CACHE_DIRS:
        base = ROOT / top
        if base.is_dir():
            for cache in base.rglob("__pycache__"):
                shutil.rmtree(cache, ignore_errors=True)


def run_tests(modules, parallel, timeout):
    """
    One `evennia test` run of the modules.

    Returns:
        dict: status ("ok", "failed" or "norun"), ran, seconds, failing
            (test method names) and tail (the output's last lines).
    """
    command = [
        evennia_command(), "test", "--settings", "settings.py",
        "--testrunner", RUNNER, *modules, "--parallel", str(parallel),
    ]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    clear_caches()
    started = time.monotonic()
    try:
        done = subprocess.run(
            command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
        output = done.stdout + "\n" + done.stderr
        code = done.returncode
    except subprocess.TimeoutExpired as err:
        output = f"{err.stdout or ''}\n{err.stderr or ''}\nTIMEOUT after {timeout} s"
        code = None
    finally:
        clear_caches()
    seconds = time.monotonic() - started
    return classify(output, code, seconds)


def classify(output, code, seconds):
    """Read a run's combined output: what ran, and what failed."""
    ran = RAN.findall(output)
    failing = sorted({name for _kind, name, _where in CASE.findall(output)})
    tail = "\n".join(output.strip().splitlines()[-15:])
    if not ran:
        status = "norun"
    elif OK.search(output) and code == 0 and not failing:
        status = "ok"
    else:
        status = "failed"
    return {
        "status": status,
        "ran": int(ran[-1][0]) if ran else 0,
        "seconds": seconds,
        "failing": failing,
        "failed_line": (FAILED.findall(output) or [""])[-1],
        "tail": tail,
    }


def expectation(mutant, failing):
    if not mutant["expect"]:
        return ""
    if any(name in failing for name in mutant["expect"]):
        return "(as expected)"
    return "(other: expected " + ", ".join(mutant["expect"]) + ")"


def git_line():
    """The tree the run is a receipt for: branch, HEAD and whether it is clean."""
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT,
            capture_output=True, text=True, check=True).stdout.strip()
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
            capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "git: unreadable"
    return f"{branch} @ {head}" + (" (uncommitted changes)" if dirty else "")


def mutate_one(mutant, originals, modules, parallel, timeout):
    """Apply one mutant, run, restore. Returns its summary line."""
    path = mutant["path"]
    if path not in originals:
        data = path.read_bytes()
        originals[path] = (data, sha256(data))
    data, digest = originals[path]
    text = data.decode("utf-8")
    count = text.count(mutant["old"])
    if count != 1:
        return f"{mutant['id']:<6} SKIPPED  `old` matches {count} times in {mutant['file']}", None
    try:
        path.write_bytes(text.replace(mutant["old"], mutant["new"]).encode("utf-8"))
        result = run_tests(modules, parallel, timeout)
    finally:
        path.write_bytes(data)
        if sha256(path.read_bytes()) != digest:
            raise RuntimeError(f"{mutant['file']} did not restore to its sha256; stop and read it")
    if result["status"] == "ok":
        return f"{mutant['id']:<6} SURVIVED {result['ran']} tests green", result
    if result["status"] == "norun":
        return f"{mutant['id']:<6} NO-RUN   the runner ran no tests (see below)", result
    names = result["failing"]
    shown = ", ".join(names[:3]) + (f" +{len(names) - 3}" if len(names) > 3 else "")
    return (f"{mutant['id']:<6} KILLED   {len(names)} fail  {shown}  "
            f"{expectation(mutant, names)}").rstrip(), result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("spec", help="a TOML file under tools/mutants/")
    parser.add_argument("--only", nargs="+", metavar="ID", help="run only these mutants")
    parser.add_argument("--parallel", default="auto", help="ForkTestRunner workers (default auto)")
    args = parser.parse_args(argv)

    try:
        modules, mutants, timeout = load_spec(args.spec)
        if args.only:
            unknown = set(args.only) - {m["id"] for m in mutants}
            if unknown:
                raise SpecError("no such mutant: " + ", ".join(sorted(unknown)))
            mutants = [m for m in mutants if m["id"] in args.only]
        evennia_command()
    except SpecError as err:
        print(f"mutate: {err}", file=sys.stderr)
        return 2

    print(f"spec     {Path(args.spec).name}  ({len(mutants)} mutants)")
    print(f"tree     {git_line()}")
    print(f"python   {sys.version.split()[0]}  parallel {args.parallel}")
    print(f"modules  {' '.join(modules)}")

    base = run_tests(modules, args.parallel, timeout)
    print(f"baseline {base['status'].upper():<8} {base['ran']} tests  {base['seconds']:.0f} s")
    if base["status"] != "ok":
        print("baseline is not green; no mutant was run.\n" + base["tail"])
        return 1

    originals, counts, details = {}, {}, []
    try:
        for mutant in mutants:
            line, result = mutate_one(mutant, originals, modules, args.parallel, timeout)
            print(line, flush=True)
            word = line.split()[1]
            counts[word] = counts.get(word, 0) + 1
            if result and result["status"] == "norun":
                details.append(f"--- {mutant['id']} ---\n{result['tail']}")
    except KeyboardInterrupt:
        print("interrupted; every file was restored.", file=sys.stderr)
        return 130
    for block in details:
        print(block)
    order = ("KILLED", "SURVIVED", "SKIPPED", "NO-RUN")
    print("summary  " + ", ".join(f"{counts.get(w, 0)} {w.lower()}" for w in order))
    return 0 if counts.get("KILLED", 0) == len(mutants) else 1


if __name__ == "__main__":
    sys.exit(main())
