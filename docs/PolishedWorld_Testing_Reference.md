# PolishedWorld — Testing Reference (`@py` idioms & gotchas)

> **Rev 2 · 2026-07-13** — Added the lambda-scope `me` gotcha (§3) and a manual-stamp harness note for cooldown isolation (§7), both from Stage 3 Component E.2 disassemble testing.
> **Rev 1 · 2026-07-12** — First committed version. Consolidates the hard-won in-game `@py` testing conventions accumulated through Stage 2–3: one-shot vs interactive console, the `;` client-split gotcha + list-literal idiom, the no-comprehensions rule, reload vs live-data semantics, raw-colour inspection, state-reset idioms, and the `py_compile` fallback diagnostic. Supersedes the informal project-knowledge quick-ref for testing workflow; domain quick-ref tables (calendar/currency/survival) stay in their own docs.
> **Canonical:** `docs/PolishedWorld_Testing_Reference.md` @ G0dlet/PolishedWorld — git wins. If this project-knowledge copy's Rev is lower than the repo's, it's stale — re-upload from the repo.

## Purpose

How to test PolishedWorld systems **in-game** with `@py`, and the environment-specific traps that repeatedly cost time. Read this before writing test lines for any component.

## 1. The `@py` execution model

Two modes, different rules:

- **One-shot `@py <code>`** — a single game command; `py` execs/evals the whole line and returns once. **Namespace does NOT persist** between separate `@py` calls, so any import must be used on the *same* line/expression. `me`, `self`, `here` are injected fresh every call, so they're always available.
- **Interactive console** (`py` with no args → `>>>` prompt; `quit()` to exit) — a real `code.InteractiveConsole`. Namespace persists across lines; `;` and multi-line statements work like normal Python. Use it whenever you need import → use across statements.

Rule of thumb: single-expression check → one-shot `@py`; import-then-use or multi-statement → interactive console (or route around, §2).

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

## 3. No comprehensions / generators in one-shot `@py`, and no free `me` in a lambda

A bare `me`/`self`/`here` inside a **lambda body** in one-shot `@py` → `NameError:
name 'me' is not defined`. They're injected as eval **locals**, and a lambda's
free variables resolve against its `__globals__`, not the eval locals — so the
lambda can't see them. Fixes: bind the object with a walrus in a plain list
literal (everything stays top-level), e.g.
`@py me.msg(str([(o:=spawn("x")[0]).move_to(me), setattr(o.db,"k","v"), o.db.k]))`,
or pass `me` as a lambda **parameter** (`(lambda o, m: o.move_to(m))(obj, me)`).
A lambda that references only its own parameter is fine.

Comprehensions and generator expressions have their own scope and fail under `py`'s exec context. Use list *literals* (`[a, b, c]` — fine), explicit loops in the **interactive console**, or `evennia shell` for anything statistical/looping.

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

## Domain quick-refs

Calendar (13 months / seasons), currency (Gold/Silver/Copper) and survival thresholds live in their domain docs; not duplicated here to avoid drift.
