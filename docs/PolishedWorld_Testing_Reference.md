# PolishedWorld — Testing Reference (`@py` idioms & gotchas)

> **Rev 6 · 2026-08-15** — **§11 gains two more cases from the Stage 4.5 Component D.1 run, and one of them is the protocol attacking itself.** Rev 5 established that a step expecting an absence needs a receipt that the code ran. D.1 found the mirror image: a step that *writes past a single-writer* manufactures a state production code never promised to handle, and then the prose describing that code reads as a bug report. The protocol told the tester to set `.current` by hand; a later tick moved the skill 40 points at once; the docstring saying "at most ONE point" was the fourth false claim of the epic. **State-mutating cleanup steps must run before the out-of-band writes, not after** — and any protocol step that bypasses a documented writer must say which invariant it is suspending. §11 also records the unit-test twin found by mutation: a guard that looks redundant because a second guard covers every input the tests happen to try (`int(inf * 160)` raises `OverflowError`; nothing else in the class reaches it), and the emptiness-receipt idiom catching a collection comprehension that walked the wrong shape and would otherwise have passed green on an empty set.
> **Rev 5 · 2026-08-13** — **Two new sections, from the Stage 4.5 Component C protocol run.** §11 records the run's most expensive mistake, which was not a bug in the code: a step whose expected outcome was *the level did not change* passed while the code under test was never reached, because the craft it used failed and the success-only gate returned first. Nothing happening and the guard working look identical from outside, so a step expecting an absence must carry an independent receipt that the code ran — and both receipts were available here and neither was demanded. It is the in-game twin of the unit-test trap in the same component (a write-guard cannot be tested by asserting the value afterwards, only by observing the write), and the same question finds both: *what else could produce this observation?* §12 records two argument-shape traps that surface as object-search failures rather than usage errors — `harvest <part> from <corpse>` and multimatch numbering (`rabbit-1`).
> **Rev 4 · 2026-08-03** — **§3's no-comprehensions rule was wrong and is corrected by measurement.** List, set and dict comprehensions *do* see `py`'s eval locals (PEP 709 inlining, Python 3.12+); generator expressions and lambdas do not. Verified on 3.12 and 3.14 during Stage 4.5 A.1. §3 now leads with the cause -- `eval(code, {}, available_vars)` leaves globals empty, so nested function scopes cannot reach the caller's locals -- because the cause is version-independent and the table is not. Adds three diagnostics that actually discriminate, and a warning about the shape of diagnostic that does not: a lambda referencing only its own parameter passes on every version and proves nothing. Adds the argument-passing idiom for verifying a pure module inside the running server, and notes what `evennia shell` cannot prove.
> **Rev 3 · 2026-07-26** — Three additions from Stage 3 Components G–H. §1 corrected: `evennia shell` has **no** `me`/`self`/`here` at all (pure-function use only), and the interactive `py` console **drops pasted lines** from a MUD client, so the rule of thumb now favours atomic one-shot `@py` over the console — the previous advice pointed straight at the trap. §7 hand-stamp harness extended to knowledge carriers and to `ndb` state (`nattributes.add`), which is what made H.1's regression tests deterministic. §10 gained the how of two-party testing: a consent handshake needs two *sessions*, and `@ipuppet` cannot provide them.
> **Rev 2 · 2026-07-13** — Added the lambda-scope `me` gotcha (§3) and a manual-stamp harness note for cooldown isolation (§7), both from Stage 3 Component E.2 disassemble testing.
> **Rev 1 · 2026-07-12** — First committed version. Consolidates the hard-won in-game `@py` testing conventions accumulated through Stage 2–3: one-shot vs interactive console, the `;` client-split gotcha + list-literal idiom, the no-comprehensions rule, reload vs live-data semantics, raw-colour inspection, state-reset idioms, and the `py_compile` fallback diagnostic. Supersedes the informal project-knowledge quick-ref for testing workflow; domain quick-ref tables (calendar/currency/survival) stay in their own docs.
> **Canonical:** `docs/PolishedWorld_Testing_Reference.md` @ G0dlet/PolishedWorld — git wins. If this project-knowledge copy's Rev is lower than the repo's, it's stale — re-upload from the repo.

## Purpose

How to test PolishedWorld systems **in-game** with `@py`, and the environment-specific traps that repeatedly cost time. Read this before writing test lines for any component.

## 1. The `@py` execution model

Two modes, different rules:

- **One-shot `@py <code>`** — a single game command; `py` execs/evals the whole line and returns once. **Namespace does NOT persist** between separate `@py` calls, so any import must be used on the *same* line/expression. `me`, `self`, `here` are injected fresh every call, so they're always available.
- **Interactive console** (`py` with no args → `>>>` prompt; `quit()` to exit) — a real `code.InteractiveConsole`. Namespace persists across lines; `;` and multi-line statements work like normal Python. ⚠️ **But it drops lines when you paste a block from a MUD client**: the client sends the lines faster than the console consumes them, the remainder leaks to the game parser, and you get a wall of `Command '...' is not available`. Reliable only when typed line by line, or over raw telnet.
- **`evennia shell`** (a Django shell outside the game) — ⚠️ **`me`, `self` and `here` do not exist here at all**; touching one raises `NameError`. There is no player session to inject them from. Use it *only* for pure functions and statistics (`skill_check` distributions, registry inspection), never for anything that needs a character. It has its own paste trap — see Evennia Reference §11.16.

Rule of thumb: prefer **atomic one-shot `@py`, one self-contained line per step** (§2's idioms make almost anything fit). Reach for the interactive console only when you must, and type rather than paste. Reach for `evennia shell` only for character-free maths.

## 2. The `;` gotcha — client-side command splitting

Server `py` supports `;` to separate statements (its own help says so) and Evennia's cmdparser does **not** split on `;`. But **many MUD clients split input on `;` before sending**, so `@py a; b` arrives as two lines: `@py a`, then a bare `b` → `Command 'b' is not available`. (Verified 2026-07-12: single-statement `@py` worked; the same line with `;` failed in the client but worked via telnet.)

Portable, client-agnostic workarounds:

- **List-literal idiom** — wrap independent *expressions* (function calls) in one list, no `;`, not a comprehension:

  ```
  @py [me.tags.clear(category="known_recipe"), me.learn_recipe("Cloth")]
  ```

  Elements run left→right; the returned list is echoed harmlessly. Cannot hold statements (`import`, assignment).
- **Telnet** — connect with raw telnet instead of the client; `;`-chained `@py` then works verbatim. Best for import/assignment-heavy setups.
- **Import + assignment in one shot** (no `;`, no persistence) via `__import__`:

  ```
  @py setattr(__import__("commands.crafting_commands", fromlist=["CmdRecipes"]).CmdRecipes, "SHOW_HIDDEN_COUNT", True)
  ```

## 3. Nested scopes in one-shot `@py` — lambdas and generators cannot see `me`; comprehensions can

A bare `me`/`self`/`here` inside a **lambda body** in one-shot `@py` → `NameError:
name 'me' is not defined`. They're injected as eval **locals**, and a lambda's
free variables resolve against its `__globals__`, not the eval locals — so the
lambda can't see them. Fixes: bind the object with a walrus in a plain list
literal (everything stays top-level), e.g.
`@py me.msg(str([(o:=spawn("x")[0]).move_to(me), setattr(o.db,"k","v"), o.db.k]))`,
or pass `me` as a lambda **parameter** (`(lambda o, m: o.move_to(m))(obj, me)`).
A lambda that references only its own parameter is fine.

**Comprehensions are not in the same boat, and Rev 1-3's blanket rule was wrong.**
PEP 709 (Python 3.12) inlines list, set and dict comprehensions into the
enclosing scope, so they *do* see the eval locals. Generator expressions were
not inlined and still fail. Measured on 3.12 and again on 3.14 (Stage 4.5, A.1):

| Construct referencing an outer `me` / `self` | one-shot `@py` |
|---|---|
| list / set / dict comprehension | works |
| generator expression | `NameError` |
| `lambda` body | `NameError` |
| `map(lambda ...)` closing over an outer name | `NameError` |

⚠️ **A diagnostic that does not touch an outer name proves nothing.**
`@py self.msg(str([[n for n in (1,2)], list(map(lambda n: n, (1,2)))]))` returns
`[[1, 2], [1, 2]]` on every version, because neither half references anything
from the eval locals. These three do discriminate:

    @py self.msg(str([type(self).__name__ for n in (1,)]))      -> ['Character']
    @py self.msg(str((lambda n: type(self).__name__)(1)))       -> NameError
    @py self.msg(str(all(type(self).__name__ for n in (1,))))   -> NameError

**The rule worth remembering is the cause, not the table.** `py` runs
`eval(pycode_compiled, {}, available_vars)` (`evennia/commands/default/system.py`),
so *globals is an empty dict*. A nested function scope resolves free variables
against globals, never against the caller's locals. Therefore: **any name used
inside a lambda or generator expression must be passed in as an argument.** That
holds on every Python version; relying on comprehension inlining does not.

The argument-passing form generalises to verifying a whole pure module in one
line, which is how `world/progression.py` was checked inside the running server:

    @py self.msg(str((lambda m: m.xp_threshold(20))(__import__("world.progression", fromlist=["x"]))))

Note that a lambda *nested inside another lambda* is fine — it closes over the
outer lambda's parameter, which is a real closure. Only the step across the eval
boundary is broken. `evennia shell` has none of these problems, but it is a
separate process: it cannot prove that the running server can import a module or
that `@reload` picked up a settings change.

## 4. Wrap non-string returns before `msg()`

`me.msg(x)` reads a tuple as `(text, options)` and mis-renders other types. Always `str()`:

```
@py me.msg(str(sorted(me.known_recipes())))
```

## 5. Reload semantics — module vs live data

- **`@reload` after module-level changes** (new class, new cmdset line, edited method body) — once, after applying the patch.
- **Live data needs no reload.** Tags, attributes and traits are read per-command-invocation, so after `me.learn_recipe(...)` / `me.tags.clear(...)` the *next* command reflects it immediately. No reload between a data change and re-checking.

## 6. Raw-colour inspection

Confirm a render contains only intended colour codes (no stray raw `|`) by echoing with pipes swapped:

```
@py me.msg(("  |wNeeds:|n   1x gourd, 1x twine").replace("|","!"))
```

→ `  !wNeeds:!n   1x gourd, 1x twine`. Any lone `!` that isn't a code marks a raw-pipe bug.

## 7. State-reset idioms

- Known-recipe set: `@py me.tags.clear(category="known_recipe")`
- Inventory (loop → interactive console): `for o in list(me.contents): o.delete()`
- Deterministic cooldown abort: `@py me.cooldowns.add("craft:<name>", 9999)`
- Cooldown **isolation** (e.g. testing a command's own cooldown gate): don't build
  the test item via a craft helper that calls `me.cooldowns.clear()` — that wipes
  the very cooldown under test. Instead spawn + hand-stamp the item
  (`spawn("cloth")[0]` → `o.db.recipe = "cloth"`) so no craft pipeline and no
  blanket `clear()` is involved. (Cost us Component E.2's Test F once.)
- **Hand-stamp knowledge carriers** the same way, bypassing `inscribe`/`scribe`
  (their material cost and cooldown are not what you're testing). The typeclass's
  `stamp()` owns identity, so one line produces a finished carrier:

```
  @py me.msg(str([(b := __import__("evennia.prototypes.spawner", fromlist=["spawn"]).spawn("book")[0]), b.stamp(["cloth", "leather"]), setattr(b, "condition", 100), b.move_to(me.search("Bob"), quiet=True), b.key]))
```

  `Book.stamp(list)` sets `db.recipes` + a real stored `key`; `Scroll.stamp(name)`
  takes a single string. Set `condition` directly (raw-int `AttributeProperty`,
  not a trait).
- **Hand-stamp `ndb` state** with `nattributes.add` — what `obj.ndb.x = y` is sugar
  for. Invaluable for anything with a wall-clock expiry: stamping the state
  directly removes both the timeout race and the sending command's cooldown from
  the test.

```
  @py str(me.search("Bob").nattributes.add("pending_teach", (me, "cloth", 9999999999)))
```

  Remove with `.nattributes.remove("pending_teach")`. Note `ndb` does **not**
  survive `@reload` — usually the point, but it means a reload mid-test silently
  clears what you stamped.
- Retrieve a tagged test object between calls: `search_tag(key)[0]`

## 8. Diagnostic — silent `DefaultObject` fallback

When a typeclass mysteriously loads as `DefaultObject`, suspect a **syntax error in that file first** (Evennia swallows it and falls back). Verify from the shell:

```
python -m py_compile path/to/file.py
```

## 9. Evennia colour parser

`|_` = space, `|/` = line break, `|-` = tab, `||` = literal pipe. Never put a raw `|` in ASCII art / columns — use `!` or `║`. Codes like `|x…|n` (grey) are fine. In command `msg()` output, literal `\n` and literal spaces work (see any `Cmd*` in `commands/character_commands.py`); the `|_`/`|/` forms matter for stored strings (prototypes, attributes).

## 10. Multiplayer note

Read-only commands (e.g. `recipes`) touch no shared state on the single-threaded reactor → no race. For write paths always test: two players same command/same tick, act-on-object-in-use, disconnect mid-action, object deleted mid-use, 10+ in a room.

**Two-party tests need two sessions.** ⚠️ `@ipuppet` *switches* your session to the other character, so it cannot give you both parties at once — you cannot watch an offer arrive, walk the offerer out of the room, and then answer as the recipient. Open a second client (raw telnet is fine) on a second account and puppet the other character there. This also exercises a guard you would otherwise never hit: commands that require a *played* target read `target.has_account`, which is truthy only while a session is connected, so an unpuppeted body is correctly refused.

**Backstop coverage.** Any two-step handshake (offer → accept) must be tested against the world moving in between: offerer leaves the room, offerer logs out, the offer expires, the offer is answered twice. Validating only at offer time is the barter `finish()` bug (Evennia Reference §7.5, `world/barter.py`).

## 11. ⚠️ A step that expects "nothing changed" must prove the code ran

The most expensive kind of false pass: a test step whose expected observation is
an *absence*, satisfied because the code under test was never reached.

Stage 4.5 C.1 shipped a guard that stops a hand-raised skill level from being
written back down. The protocol step read:

```
@py str(self.skills.craft.__setattr__("current", 60))
craft twine from fiber-1, fiber-2, fiber-3
```

— expect the level to still be 60. It was. The craft had **failed**, the
success-only gate returned before the improvement engine was called, and the
guard was never exercised. Nothing happening and the guard working produce the
identical observation.

**The rule:** when the expected outcome is "X did not change", the step must also
carry an independent receipt that the code ran — a success message, a second
value that *did* move, a counter. Here both were available and neither was
demanded: the craft's own outcome line distinguishes success from failure, and
the XP total moves on any tick that reaches the engine.

```
craft twine from fiber-1, fiber-2, fiber-3
    You work the materials into length of twine.     <- success: the tick ran
    The work fights you; ...                          <- failure: it did not
    You botch the work badly ...                      <- fumble: it did not
@py str((int(self.skills.craft.current), self.skill_xp.get("craft")))
    (60, 1191)   <- level held AND the total moved: the guard actually fired
```

This is the in-game twin of a unit-testing trap from the same component. A guard
that writes a cache "only when it changed" cannot be tested by asserting the
value afterwards — the value is identical either way. Only observing the *write*
distinguishes them (spy on the property setter). Same question in both cases:
**what else could produce this observation?**

### 11a. A step that writes past a single writer suspends an invariant — say which

The other half of the same lesson, found in the Component D.1 protocol.

The protocol's cleanup steps set `self.skills.craft.current` directly, to restore
a value after a cap test. `.current` is a **cache with exactly one writer**
(P-2); the lifetime XP total is the truth (P-1). Setting the cache by hand leaves
it below what the total buys, and the next tick correctly snaps the level up to
the truth:

```
craft=20 xp=1195  ->  craft  ->  Your Crafting improves! (+40, now 60%)
```

Forty points in one tick. Nothing is broken — that is P-1 working — but the
production docstring three files away asserted *"a single tick can now move at
most ONE point"*, and it was **this protocol** that created the only state in
which the sentence is false. The claim had held under an assumption nobody wrote
down: that `.current` has no writer but the engine.

**Two rules follow.**

1. **Cleanup that restores a cached value runs *before* the out-of-band writes,
   not after.** A protocol that ends by desynchronising state leaves the next
   session's first observation looking like a regression.
2. **A step that bypasses a documented writer must name the invariant it is
   suspending.** "Set `.current = 40` to restore" is a lie of omission; "set
   `.current = 40`, which desynchronises it from the XP total until the next tick
   repairs it (P-1)" is the same keystroke and tells the reader what they are
   looking at.

This is the second time in one epic that a protocol step manufactured the state
its own spec said could not occur (the first was C.1's F7). Both were found in
play rather than in review, which is an argument for running the protocol, not
against writing it.

### 11b. Mutation testing finds guards that only *look* redundant

A unit-test corollary, from the same component.

`render_progress_bar` clamps its input twice — once on the incoming fraction,
once on the derived cell count. Deleting the first clamp broke **no test**, which
reads as a clear verdict: dead code, tidy it away. It is not. The second clamp
covers `-0.3`, `1.5`, `None` and NaN, and those were exactly the inputs the tests
happened to try. It does not cover infinity, because `int(float("inf") * 160)`
raises `OverflowError` *before* the second clamp is reached.

**The rule:** when a mutation kills a guard and nothing fails, the next question
is not "can it go?" but **"which input class does the surviving guard not
cover?"** Answer it before deleting, and write the test that distinguishes them —
otherwise the mutation run has certified the guard as removable for the next
reader.

The same run produced one more receipt-shaped catch worth copying. A test
collecting skill keys out of a nested data table walked the wrong shape (it
assumed a `"parts"` wrapper that does not exist) and found nothing. It failed
only because it carried an emptiness receipt:

```python
found = {...}
self.assertTrue(found, "no harvest skills found -- the table shape changed")
self.assertLessEqual(found, set(self.char1.improvable_skills))
```

Without line 2 the subset assertion is vacuously true against the empty set, and
the test passes green forever while proving nothing. **Any assertion of the form
"everything in this collection satisfies X" needs a prior assertion that the
collection is non-empty.**

## 12. Command-syntax traps that read as bugs

Two argument-shape errors from Stage 4.5's protocol that produce misleading
messages rather than usage hints:

- **`harvest` requires the connective.** `harvest <part> from <corpse>`. Typing
  `harvest hide from` alone yields `Could not find 'hide from'` — an object-search
  failure on the mis-parsed remainder, not a usage error. Read a `Could not find`
  naming *two* words that were meant to be separate as a syntax problem first.
- **Identical objects need the numbered alias.** Six rabbits in a room make
  `hunt rabbit` return a disambiguation list; `hunt rabbit-1` is the target.
  Evennia's multimatch numbering is per-search, so re-check the list after any
  kill or flight rather than assuming `-1` still names the same animal.

## Domain quick-refs

Calendar (13 months / seasons), currency (Gold/Silver/Copper) and survival thresholds live in their domain docs; not duplicated here to avoid drift.
