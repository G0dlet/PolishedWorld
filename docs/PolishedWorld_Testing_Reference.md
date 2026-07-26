# PolishedWorld — Testing Reference (`@py` idioms & gotchas)

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

## Domain quick-refs

Calendar (13 months / seasons), currency (Gold/Silver/Copper) and survival thresholds live in their domain docs; not duplicated here to avoid drift.
