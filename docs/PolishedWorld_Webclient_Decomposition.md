# PolishedWorld — Webclient Decomposition

> **Rev 2 · 2026-11-06** — **Component 2 is done.** W2.4 merged `feature/webclient-assets` as `37844da` (PR #24, tree `9673cad`, the tree `merge-tree` predicted); W2.3 landed on `feature/webclient` as `bf66108` (tree `66a45d6`), with the outline in Muted after two ChatGPT rounds. Each gains a *Shipped* line and a row in §13. W2.3 was built with three choices locked at its start (exclusion set, the edge-contrast rule, the palette as the threshold's source) and one kept (the style guide waits for W8.2); the edge-contrast rule is an addition to the approach above, which named only the outline-colour rule. OQ-W2 and OQ-W3 are closed: the webclient is not an alpha prerequisite, and it gets a dev-board card in *In progress*. The board already held fifteen cards, the upper bound `tests/test_dev_board.py::test_card_count_is_lock_b` enforces for the board's lock B, so the card, the bound (15 → 20) and roadmap Rev 44 travel together on a short branch, `feature/board-cap` (Adam's choice A, 2026-11-06), which keeps the roadmap's rule that a card moves in the same commit as the roadmap line. Testing Ref §21 records the pipeline's tests and how a master is received.
> **Rev 1 · 2026-11-06** — first version. Decomposes PolishedWorld's own webclient (three columns, panels fed by OOB, the text stream untouched) into eight components and nineteen tasks, against live source read the same day: `main` at `efd7d91` (tree `e137be1`), `feature/webclient-assets` at `6f17c54` (tree `40798d8`), Evennia `v6.1.0` (`e5265b7`; the work machine's install reports rev `a89a9b94e`, but the four files this feature leans on hash identical to the tag — §3), *Legend* core pp. 87–88 and 145–146. Six Evennia assumptions carried in by the handoff were checked at source before any lock: three held, one held only in part (an emitter listener *replaces* the previous one; unknown OOB names reach plugins through `onUnknownCmd`), one failed (no stock route carries a per-session client flag), and one holds only from the shell (`evennia reload` runs `collectstatic`, the in-game `reload` does not). A check of the stock client found five external hosts, among them an unpinned `golden-layout.com/files/latest`, which decides WC2. The handoff's proposal for duplicated room lists collided with roadmap [RESOLVED] *A graphical client is additive, never authoritative* (2026-09-09) and was replaced (WC4). Locks WC1–WC16 in §2; Adam took every recommendation (D1–D8). Two BACKLOG entries filed in the same commit (Rev 67).
> **Canonical:** `docs/PolishedWorld_Webclient_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Design sources:** `docs/PolishedWorld_Art_Style_Guide.md` (palette v0.2.1, §5 production rules, §6 Legend UI rules, §7 accessibility, §9 reference mockups, §10 asset pipeline); roadmap decision log, [RESOLVED] *A graphical client is additive, never authoritative*.
**Status:** IN PROGRESS. Component 2 done (W2.1–W2.4); Component 3 next (W3.1).
**Branches:** `feature/webclient-assets` (Component 2, merged by W2.4) and `feature/webclient` (Components 3–8, created from `main` after W2.4, `--no-track`).
**Rough scope:** 19 tasks, ~6–8 sessions at 5 h/week; Component 7 can be cut to BACKLOG without touching anything before it (WC13).
**Roles:** Claude writes code and checks rules against *Legend*; ChatGPT draws pixel art and sets visual direction; Adam is creative director and carries a handoff file between the two wherever §14 says one is needed.
**Philosophy:** skynda långsamt — the server sends what it already knows, in the shape a panel needs, when it changes. No mechanic moves into the client, no number is shown that the server does not hold, and no external host is trusted at runtime.

---

## 1. Why this feature

The stock Evennia webclient is a single text pane in a GoldenLayout frame. PolishedWorld's alpha measures onboarding (roadmap decision (G)), and a new player reads the world faster with a location panel, a clock and their own gauges beside the text than with `status`, `look` and `inventory` typed in turn. The art side is ready to be used: the palette is locked, the style guide fixes the Legend vocabulary for the UI, and the body silhouette and its seven zone masks are published under `web/static/polishedworld/`.

What this feature must not do is make the webclient the game. The text stream stays complete for every session (WC1), so a telnet player and a screen-reader player play the same game; panels are a second view of state the server already sends as text, and the one place where the client hides text (WC4) hides only what a visible panel already shows.

## 2. Decisions locked 2026-11-06 (WC1–WC16)

**WC1 — The text stream stays canonical; every panel datum is also reachable in text.** Roadmap [RESOLVED] 2026-09-09 governs: OOB data goes *alongside* text, never instead of it. Where a panel shows something no player command prints today, this feature adds the command (W5.3 adds a player `time`; Evennia's `@time`, open to players (`commands/default/system.py:731–734`), prints server uptime and the game time as a real-calendar timestamp, `system.py:745–756` — not the project's 13 months, season or weather). *What follows:* no task may remove a line from what a session receives as text; WC4 only splits one message in two.

**WC2 — Own fixed layout; GoldenLayout and every CDN dependency go (D1 = C).** Evennia's `webclient/base.html` loads jQuery 3.2.1, Bootstrap 4.0.0-beta, mustache, popper, GoldenLayout from `golden-layout.com/files/latest` (unpinned, a website rather than a CDN) and favico.js from `cdn.rawgit.com` (§3). The style guide and mockup v3 describe a fixed three-column layout, the accessibility rules need landmarks and a live region in a DOM we control, and a public site must not run an unpinned third-party script. Kept from Evennia, served from Evennia's own static files: `evennia.js`, `webclient_gui.js`, `default_in.js`, `default_out.js`, `history.js` — the input and output plugins fall back to `#inputfield` / `#messagewindow` without GoldenLayout (`default_in.js:16, 52`; `default_out.js:9–12`). jQuery is vendored, version-pinned and hashed (W3.1). *Rejected:* A, keep GoldenLayout from the CDN; B, vendor GoldenLayout — both keep a layout library the design does not use, with its mobile and screen-reader costs.

**WC3 — `webclient/base.html` is replaced, not extended.** The CDN lines sit partly outside the template's blocks (`base.html:19, 83–88, 125, 133–134`), so `{% extends %}` with `{{ block.super }}` cannot remove them. The project's `web/templates/webclient/base.html` is a full replacement; `webclient.html` is extended through its `client` block. The cost — a copy that does not follow Evennia upgrades — is paid by a test that renders the page and fails on any `src`/`href` to a host other than the game's own (W3.1), and by Evennia Ref recording which upstream file the copy was taken from.

**WC4 — Room lists travel as their own text message, type `room_contents` (D2 = C).** Today a look is one message, `type: "look"` (`extended_room.py:632`; auto-look after a move at `objects.py:3236`). The project sends a room look as two messages in order: the description (`type: "look"`) and the exits, characters and things (`type: "room_contents"`). A telnet session receives the same text in the same order as now. The webclient shows `room_contents` in the text area unless the room panel is visible **and** the player has not turned on *room lists in text* (a client toggle, default off on desktop, forced on below the layout breakpoint). One function, `room_look(char, room)`, sends both, and both callers — the look command and `Character.at_post_move` — use it (W5.4). *Rejected:* A, the server omits lists for panel sessions (needs the [RESOLVED] entry rewritten and every list-writer to know a flag); B, accept the duplicate.

**WC5 — OOB is a full snapshot per domain (D3 = B).** Four command names: `survival` (locked by roadmap [RESOLVED] 2026-09-09), `char`, `world`, `room`; `map_update` stays reserved for the map. Each is sent whole — never a delta — when a value in it changes or crosses a threshold, at `at_post_puppet`, and when the client asks. A lost or reordered message is corrected by the next one, and a reconnect needs one request. Payload shapes are fixed in W4.1 and documented in Evennia Ref.

**WC6 — The client asks with one inputfunc, `pw_state`.** `server/conf/inputfuncs.py` (loaded by `INPUT_FUNC_MODULES`, `settings_default.py:492`) gains `pw_state(session, *args, **kwargs)`, which sends all four snapshots to that session. The `pw_` prefix is required: a later module in that list overrides an earlier function of the same name (`settings_default.py:489–491`). The webclient calls it on login and on page reload, because a browser reload re-attaches to a puppet that is already puppeted, and `at_post_puppet` does not run again.

**WC7 — No per-session client flag.** The handoff assumed the webclient would tell the server it shows panels. With WC4 the server never needs to know: OOB goes to every session, the webclient routes it, and telnet drops it unless the client negotiated GMCP or MSDP (`telnet_oob.py` `data_out`), in which case a GMCP client receives the same snapshots — harmless and free. `client_options` refuses unknown keys (`inputfuncs.py:167`, error text to the player) and `webclient_options` is stored per account (`:539`), so neither would have been the right home anyway.

**WC8 — One emitter module, a census of its call sites.** `world/client_state.py` holds the four pure snapshot builders and `push(obj, *domains)`. Emission happens at named sites only (§3, W4.2), and a test counts them with the AST (lesson 200's method) so a new write to a gauge without a push fails a test instead of shipping a stale panel. The room snapshot is built per viewer, because display names depend on the looker (`get_display_name(looker)`; statues of logged-out characters, WC14).

**WC9 — The clock is computed in the browser.** The `world` snapshot carries absolute game seconds (`world.gametime_utils.get_absolute_gametime()`), `TIME_FACTOR` (4) and the server's wall-clock milliseconds at the moment of sending; JS advances the clock locally and renders date, time of day and season with the project's month names. Evennia's game time only runs while the server runs, so the snapshot is re-sent on puppet, on `pw_state`, on each weather change and on each survival tick (every 30 real minutes) — the largest possible drift is one server downtime, corrected at the next connect.

**WC10 — Pixel art scales only by whole factors, rendered `image-rendering: pixelated`.** From the style guide §5. The silhouette shows at ×2 or ×4; icons at ×1 or ×2.

**WC11 — The outline moves to a lighter palette colour (D4 = B).** `#0E1512` against Panel is 1.14:1 and against Panel light 1.43:1, so neither surface makes the outline a graphical object at the 3:1 the style guide requires. ChatGPT redraws the outer outline in a palette colour that is ≥ 3:1 against Panel and occurs nowhere else in the figure — candidates `muted` `#9D9B8C` (5.78:1) and `stone_light` `#B0ADA0` (7.20:1); `stone` `#777C79` is already used inside the figure and cannot be told apart from it by the pipeline. `split-body` then excludes both the new outline colour and Background (inner dark details such as the eyes may stay `#0E1512`) from every mask. The final colour is Adam's and ChatGPT's choice within that constraint (W2.3, §14).

**WC12 — The character panel shows only what the server holds (D5 = B).** The server has one `health` gauge (CON × 2, character creation CC9) and a `fatigue` survival gauge on 0–100; it has no hit locations, no wound levels, no Combat Actions and no Hero Points — all Stage 5, and combat is outside the alpha. The panel shows health with the gauge's own description, the encumbrance band, and the silhouette as an untinted figure. Fatigue sits in the survival panel with the gauge's description, not Legend's level names, until BACKLOG *Fatigue-exhaustion consequence* gives the bands a mechanical meaning. Zone colouring, wound levels per location, the useless-limb state, Combat Actions and Hero Points are BACKLOG *Character panel: Legend combat state* (Rev 67), blocked on Stage 5. *Rejected:* A, the full Legend panel with placeholders — it would show "Intact" for a system that does not exist; C, no character panel before Stage 5.

**WC13 — Inventory, equipment and skills are the last component, and cuttable (D6 = B).** The data exists (`inventory`, worn clothing, `skills`, encumbrance), so Component 7 builds two panels on WC5's pattern. It sits after everything it depends on, so moving it to BACKLOG at any point changes no earlier task.

**WC14 — Accessibility is a lock, not a pass at the end.** From the style guide §7: no state is told apart by colour alone (every gauge has its description as text, every link is a real link); the text area is `role="log"` with `aria-live="polite"`; panels are landmarks (`<aside>` with labels) and are *not* live regions, so a gauge change does not interrupt reading; clickable `|lc…|lt…|le` links degrade to their visible text in screen-reader mode and for non-MXP clients (`ansi.py:438`), so no link ever carries a function the typed command lacks; and WC4's toggle lets a screen-reader player keep room lists in the text.

**WC15 — No wiki tab (D7).** No wiki exists. The rule for later: when one does, it is an external link marked ↗ that opens in a new tab with `rel="noopener"`, never a tab that pretends to be part of the client.

**WC16 — `feature/webclient-assets` merges before the client code starts (D8 = A).** W2.1–W2.2 are done and verified, and nothing in Components 3–6 needs the new outline. W2.3 lands on `feature/webclient` when ChatGPT has delivered; W2.4 merges the assets branch now. In-game and browser protocols in this feature run `evennia reload` **from the shell**, because only the launcher runs `collectstatic` (`evennia_launcher.py:907`) and static files are served from `server/.static` (`service.py:249`).

## 3. Verified source anchors (read 2026-11-06)

Evennia `v6.1.0` (`e5265b7`). On the work machine, `evennia --version` reports rev `a89a9b94e`, and these four files hash identical to the tag (sha256 prefixes): `web/templates/webclient/base.html` `166eded5ac7e`, `web/static/webclient/js/evennia.js` `8c285f3a3dc2`, `.../plugins/goldenlayout.js` `265c7c201c15`, `server/portal/wire_formats/evennia_v1.py` `9be3960e59e4`.

| Anchor | Where | What it establishes |
| --- | --- | --- |
| wire format | `server/portal/webclient.py` (`v1.evennia.com` negotiated, `:195, :203`); `wire_formats/evennia_v1.py:103, :118–131` | `msg(name=(args, kwargs))` reaches the browser as `[name, args, kwargs]`; the name `options` is never sent; `options` is popped from text kwargs, every other kwarg (e.g. `type`) is kept. |
| emitter | `web/static/webclient/js/evennia.js:181–201` | `emitter.on(name, f)` replaces the listener for `name`; unknown names fall to `default`. |
| plugin dispatch | `webclient_gui.js:135–178, 292–301` | `default` → `onDefault` → each plugin's **`onUnknownCmd(cmdname, args, kwargs)`**; returning `true` claims the message. `onText` likewise lets a plugin claim text. |
| type routing (stock) | `plugins/goldenlayout.js` `routeMessage` | `kwargs["type"]` routes text to panes; the pattern W6.2 reimplements without GoldenLayout. |
| fallbacks | `plugins/default_in.js:14–17, 49–53`; `plugins/default_out.js:9–12` | Input and output work with plain `#inputfield` and `#messagewindow`. |
| CDN loads | `web/templates/webclient/base.html:19, 31–34, 83–88, 125, 133–134` | jQuery 3.2.1, Bootstrap 4.0.0-beta (CSS and JS), mustache 2.3.0, GoldenLayout `files/latest`, favico.js via rawgit, popper 1.11.0. Lines 19, 83–88, 125, 133–134 are outside any block (WC3). |
| plugin loading | `base.html:91–123` (`{% block guilib_import %}`) | A plugin file is loaded only by its own `<script>` tag. |
| links | `utils/text2html.py:101–102, 179–197`; `utils/ansi.py:427–439, 514–515`; `settings_default.py:238, 243` | `\|lc cmd \|lt text \|le` → `<a href="#" onclick="Evennia.msg('text',[cmd])">`; stripped to the visible text in screen-reader mode and without MXP; `MXP_ENABLED = True`, `MXP_OUTGOING_ONLY = True`. |
| client options | `server/inputfuncs.py:167–185` (`_CLIENT_OPTIONS`), `:187–294` (`client_options`), `:539–585` (`webclient_options`) | WC7. |
| inputfunc modules | `settings_default.py:489–496` | WC6. |
| telnet OOB | `server/portal/telnet.py` `send_default`; `telnet_oob.py` `data_out` | OOB leaves a telnet session only as negotiated GMCP/MSDP (WC7). |
| static and templates | `settings_default.py:1038–1041` (`STATIC_ROOT = server/.static`, `STATICFILES_DIRS` = game `web/static`); templates DIRS game-first (Evennia Ref §18) | Game files win; served from `STATIC_ROOT`. |
| collectstatic | `server/evennia_launcher.py:802–804, 866, 907, 980, 990, 1011`; `server/service.py:249` | Only the launcher collects (WC16). |
| the look message | `contrib/grid/extended_room/extended_room.py:632`; `objects/objects.py:3230–3236` (`DefaultCharacter.at_post_move`), `:2657` (`at_look(target, **kwargs)` → `return_appearance(looker, **kwargs)`), `:407–415` (`appearance_template`), `:1878–1919` | WC4's two callers, and the kwargs path into `get_display_exits/characters/things`. |
| project look wiring | `commands/default_cmdsets.py:74` (`ExtendedRoomCmdSet`); `typeclasses/rooms.py:301, 317` (`get_display_characters`, `get_display_things`), `:358` (`at_object_receive`, corpse sweep; no `at_object_leave`) | W5.4 and W4.2. |
| character hooks | `typeclasses/characters.py:494` (`at_post_puppet`), `:1470–1509` (`at_post_move`, calls `super()` at `:1500`, overload fatigue at `:1509`), `:1559` / `:1581` (`at_object_leave` / `at_object_receive`), `:1184–1209` (`apply_health_damage`), `:652–653` (`update_health_max`), `:1340–1344` (`at_character_death` refills), `:1727` (rest recovery), `:591` (`encumbrance_state`) | W4.2's sites. |
| survival | `world/survival_ticker.py:37–55` (every online puppet, deduped), `:66` (depletion), `:104–145` (bucket thresholds in `ndb`); `commands/consumption_commands.py:48, 100` (eat, drink) | W4.2's sites; the bucket index is the existing threshold. |
| world | `world/gametime_utils.py:70–163`; `server/conf/settings.py:55–68` (`TIME_FACTOR = 4`, 13 months); `world/weather.py:60–89` (`broadcast_weather_change`, indoor rooms skipped) | WC9. |
| encumbrance | `world/encumbrance.py:72–74, 316` | `free` / `overloaded` / `ceiling`. |
| text commands | `commands/character_commands.py` (`status`/`vitals`, `stats`, `skills`, `progress`, `sheet`); `commands/admin_commands.py:18` (`weather`, staff) | WC1 parity; no player command prints the project's date, season or weather (Evennia's `@time` prints a real-calendar timestamp). |
| *Legend* | core pp. 145–146 (Serious and Major Wounds), pp. 87–88 (Hero Points) | WC12 and the two BACKLOG entries. |

## 4. Dependency graph

```
W2.1 ✓ ─ W2.2 ✓ ─ W2.4 merge feature/webclient-assets
                      └─ feature/webclient from main
W3.1 template + vendored jQuery ─ W3.2 layout + theme ─┬─ W6.1 text area
W4.1 snapshots + pw_state ─ W4.2 emit sites ─ W4.3 JS state plugin ─┤
                                                     ├─ W5.1 character
                                                     ├─ W5.2 survival
                                                     ├─ W5.3 world + `time`
                                                     └─ W5.4 location + room_look (WC4)
W6.1 ─ W6.2 tabs by type (after W5.4: room_contents routing exists)
W2.3 outline (ChatGPT delivery) ─ before W5.1's protocol, else W5.1 ships with the old outline and W2.3 republishes
W7.1 inventory + equipment ─ W7.2 skills   (cuttable, WC13)
W8.1 merge → W8.2 docs close-out
```

## 5. Component 1 — Art foundation (ChatGPT, Adam)

Done on `main`: palette v0.2.1 and the style guide (Rev 1–3, `f2203d0`, `bcf24b8`, `efd7d91`). No tasks.

## 6. Component 2 — Asset pipeline (Claude; ChatGPT for W2.3's art)

### Task W2.1 — `assetpipe.py validate` and `clean`
- **Shipped:** as *Task 2.1*, `231855e` (tree `819e0ef`) on `feature/webclient-assets`.

### Task W2.2 — `split-body` and the published body assets
- **Shipped:** as *Task 2.2*, `6f17c54` (tree `40798d8`); served at `/static/polishedworld/characters/body/`, verified in a browser on the work machine.

### Task W2.3 — The outline in a lighter palette colour (WC11)
- **Goal:** The silhouette's outline reaches ≥ 3:1 against Panel, and tinting a zone never recolours it.
- **Dependencies:** W2.4 (lands on `feature/webclient`); ChatGPT's redrawn `body_base.png` and `body_zonemap.png` (§14).
- **Approach:** `OUTLINE_KEY` becomes a tuple of keys: the chosen colour plus `background`; `split-body` excludes every pixel in any of them. `validate` gains one check for body masters: every pixel in the outline colour is 8-adjacent to `#FF00FF`, so the colour can only be the figure's one-pixel edge and never an inner fill — the property WC11 needs and the one the pipeline can test. Republish with `clean` and `split-body`. Style guide §5: the outline sentence and the open item are rewritten (docs commit on `main`, batched with W8.2 or earlier if Adam prefers).
- **Testing** (`art/tools`, `python -m unittest discover -s art/tools`): a fixture figure with the new outline colour yields masks with no outline pixel set; a fixture with inner `#0E1512` eyes yields masks without them; a fixture using the outline colour as an inner fill is refused by `validate`; the contrast of the chosen colour against Panel is asserted ≥ 3.0 from `palette.json`.
- **Commit:** `feat(art): outline in <colour>, split-body excludes outline and background (webclient W2.3)`
- **Shipped (Rev 2):** `bf66108` on `feature/webclient`, tree `66a45d6`; 43 tests (32 + 11: `TestContrast` 2, `TestBodyEdge` 9); mutations WM1–WM8 killed. Locked at the task's start (Adam took every recommendation): **(a)** both Muted and Background are left out of the masks — written as `OUTLINE_KEY = "muted"`, `DETAIL_KEY = "background"` and `MASK_EXCLUDED_KEYS`, not a tuple-valued `OUTLINE_KEY`; **(b)** `validate` holds `body_base.png` to two rules: the outline-colour rule above (8 neighbours), and an **edge-contrast rule** this approach did not name — every figure pixel sharing a side with the background or the image border reaches the threshold against Panel. The contrast rule is the property WC11 is for; the outline rule alone would have passed the first delivery; **(c)** the surface and the threshold are read from `palette.json` (`contrast_surfaces.panel`, `rules.status_min_contrast`), never restated; **(d)** the style guide §5 is rewritten at W8.2, so `main`'s guide describes `main`'s assets until the merge. The master took two rounds: the first brief said *recolour the dark pixels on the edge*, and eight hair pixels at the top of the head (y=5, `dark_wood`, 1.35:1) had never had an outline; the second named them. Republishing changed `body_base.png` and `body_head.png` only (head loses the eight pixels); the other six masks are byte-identical. WM3 (*the image border is not background*) survived its first run on a fixture gap and was killed after the fixture was fixed (Testing Ref §21.2).

### Task W2.4 — Merge `feature/webclient-assets` (WC16)
- **Goal:** The pipeline and the published body assets are on `main`, so the client branch starts from them.
- **Dependencies:** W2.2.
- **Approach:** `assetpipe` tests (32) and, per the test-suite policy, the full suite once on the branch tip (ForkTestRunner `--parallel auto`, `"#10"` stashed); PR with a merge commit; delete the branch. Testing Ref gains its section for the asset pipeline (validate / clean / split-body, the browser check of `/static/polishedworld/characters/body/`), as the handoff promised.
- **Commit:** merge commit; docs commit on `main` for Testing Ref.
- **Shipped (Rev 2):** PR #24 merged as `37844da` (tree `9673cad`, parents `cc82061` and `6f17c54`), branch deleted on origin. Receipts: `assetpipe` 32 OK on the branch tip (`6f17c54`); the full suite 1159 OK in 472 s on `main` after the merge (work machine, ForkTestRunner `--parallel auto`, `"#10"` stashed). The branch-tip suite run did happen, but its result line was cut by a `tail -4` in the delivered command (Testing Ref §13); the run on `main` reads the tree the merge was predicted to produce, so it is the receipt. Testing Ref §21 landed in this Rev's docs commit; the board card and roadmap Rev 44 follow on `feature/board-cap`.

## 7. Component 3 — Client shell (Claude, `feature/webclient`)

### Task W3.1 — The page template and its dependencies (WC2, WC3)
- **Goal:** `/webclient` loads only files from the game's own host, and Evennia's core plugins still connect, send and receive.
- **Dependencies:** W2.4.
- **Approach:** `web/templates/webclient/base.html` replaces Evennia's (header comment names the upstream file and its sha256 prefix `166eded5ac7e`); scripts: vendored jQuery (`web/static/polishedworld/vendor/jquery-<version>.min.js`, a 3.x release at least two weeks old, MIT notice kept, sha256 pinned by a test), then `evennia.js`, `webclient_gui.js`, `default_in.js`, `default_out.js`, `history.js`, then the project's plugins. `web/templates/webclient/webclient.html` extends it and fills `client` with the skeleton W3.2 styles: `#messagewindow` inside `<main>`, `#inputfield`, two `<aside>` columns.
- **Testing:** `tests/test_webclient_template.py` (Django test client on `EvenniaTest`, the base `tests/test_dev_board.py` uses for its view tests): the page renders 200; no `src`/`href` in it starts with `http` or `//`; the vendored file's sha256 matches the pin; every script tag points at a file that exists in a static directory. Browser protocol after a shell `evennia reload`: DevTools Network shows only `localhost:4001`; `look` echoes; history recall with the arrow keys works.
- **Mutations:** add a CDN `<script>` (the host test must fail); change one byte of the vendored file (the hash test must fail).
- **Commit:** `feat(webclient): own base template, vendored jQuery, no external hosts (W3.1)`

### Task W3.2 — Layout and theme
- **Goal:** The three-column layout of mockup v3 in the palette, usable on a phone.
- **Dependencies:** W3.1.
- **Approach:** `web/static/polishedworld/css/webclient.css`: palette as CSS custom properties named by `palette.json` keys (`--pw-panel`, `--pw-text`, …); CSS grid, left panel / text / right panel; below one breakpoint the panels collapse behind two buttons and the text area takes the width (WC4's toggle is then forced on). Landmarks and labels per WC14; a skip link to the input. Fonts are local or system only (WC2).
- **Testing:** a test reads `palette.json` and asserts every `--pw-*` value in the CSS equals its palette colour (a palette change cannot drift from the CSS); browser protocol at 1920 px and at 390 px (DevTools device mode); the keyboard reaches input, panels and links in order.
- **Commit:** `feat(webclient): three-column layout, palette variables, mobile collapse (W3.2)`

## 8. Component 4 — OOB protocol (Claude)

### Task W4.1 — Snapshot builders and `pw_state` (WC5, WC6)
- **Goal:** One module answers *what does each panel show for this character*, and a client can ask for all of it.
- **Dependencies:** none (server only; can run beside Component 3).
- **Approach:** `world/client_state.py`: `char_snapshot(char)`, `survival_snapshot(char)`, `world_snapshot()`, `room_snapshot(room, viewer)` — pure, built from existing readers only (`trait.current/max/desc()`, `encumbrance_state`, `gametime_utils`, `get_current_weather`, the room's `get_display_*` sources and `get_display_name(viewer)`); `push(obj, *domains)` sends `obj.msg(<domain>=((), snapshot))` for each. Every builder is `getattr`-guarded like the survival ticker, and `push` never raises (it runs inside hooks where an exception turns a completed move into "You cannot go there", lesson from `objects.py:1331`). `server/conf/inputfuncs.py`: `pw_state(session, *args, **kwargs)` pushes all four to that session's puppet, nothing without a puppet. `at_post_puppet` pushes all four.
- **Testing** (`tests/test_client_state.py`): each snapshot's keys and types; `room_snapshot` names a statue the way `look` does for the same viewer; `pw_state` with and without a puppet (spy on `session.msg`); `push` with a builder that raises sends nothing and does not raise.
- **Commit:** `feat(webclient): client_state snapshots and the pw_state inputfunc (W4.1)`

### Task W4.2 — The emit sites, and their census (WC8)
- **Goal:** Every change a panel shows is followed by a push; no other place pushes.
- **Dependencies:** W4.1.
- **Approach:** `survival` after the ticker's depletion and warnings (`survival_ticker.py`), after eat and drink (`consumption_commands.py:48, 100`), after rest recovery (`characters.py:1727`), after the overload step (`:1509`); `char` after `apply_health_damage` (`:1209`) and from `Character.at_object_receive` / `at_object_leave` when the moved object changes the encumbrance band; `room` to every puppet in the room from `Room.at_object_receive` and a new `Room.at_object_leave` (one snapshot per viewer); `world` to every online puppet from `broadcast_weather_change` and with each survival tick (WC9). Two more writers exist today and push too: `update_health_max` (`characters.py:652–653`, max follows CON), `at_character_death` (`:1340–1344`, health and the survival gauges refilled at respawn) — the census finds any later one.
- **Testing:** an AST census (`tests/test_client_state.py::TestPushCensus`) that pins the `push(` call sites per file and every `.current` write to `hunger`/`thirst`/`fatigue`/`health` in production code, so a new writer without a push fails; per-site tests that the right domain is pushed (spy); a fan-out test: three characters in a room, a fourth arrives, three `room` snapshots go out, each with the viewer's own names.
- **Mutations:** drop the push after eat (the census and the eat test must fail); push `room` to the mover only (the fan-out test must fail).
- **Commit:** `feat(webclient): push snapshots where state changes; census of the sites (W4.2)`

### Task W4.3 — The JS state plugin
- **Goal:** The browser keeps the latest snapshot per domain and hands it to the panel that draws it.
- **Dependencies:** W3.1, W4.1.
- **Approach:** `web/static/polishedworld/js/pw_state.js`, a plugin added through `plugin_handler.add`; `onUnknownCmd` claims `char`, `survival`, `world`, `room` (returns `true`) and leaves every other name alone; `onLoggedIn` and page load send `Evennia.msg("pw_state", [], {})`; panels register a render function per domain. No `emitter.on` (it would replace a listener, §3).
- **Testing:** OQ-W1 decides whether JS gets unit tests (`node --test`) or browser protocol only; either way the protocol shows each domain arriving in DevTools → WS and a browser reload re-filling every panel.
- **Commit:** `feat(webclient): state plugin, onUnknownCmd for the four domains (W4.3)`

## 9. Component 5 — Panels (Claude; ChatGPT for icons later)

Each panel task: the server half is already in W4; the task adds the HTML/CSS/JS renderer, the text parity check (WC1) and its protocol.

### Task W5.1 — Character
- **Goal:** Name, health with its description and numbers as text, the encumbrance band, the untinted silhouette (WC12).
- **Dependencies:** W3.2, W4.3. W2.3 before the protocol if delivered (§4).
- **Approach:** silhouette `<img>` at ×4 (WC10) with `alt` naming the character's state in words; the health bar never carries meaning alone (WC14).
- **Testing:** browser protocol: take damage (staff `@py` against `apply_health_damage`; read the value first and restore the value read, not the one displayed); the panel and `status` agree.
- **Commit:** `feat(webclient): character panel (W5.1)`

### Task W5.2 — Survival
- **Goal:** Hunger, thirst and fatigue, each as a bar and the gauge's own description.
- **Dependencies:** W3.2, W4.3.
- **Approach:** the first step of the task reads live what other survival state a player feels (cold/heat stress stacks, `Starving`/`Dehydrated` buffs) and locks whether it joins this panel; nothing is added that `status` does not also print (WC1).
- **Testing:** eat and drink move the panel and `status` together; a survival tick (or `@py` on the ticker) moves it without a command.
- **Commit:** `feat(webclient): survival panel (W5.2)`

### Task W5.3 — World, and a player `time` command
- **Goal:** Date, time of day, season and weather, advancing in the browser (WC9), and the same in text.
- **Dependencies:** W3.2, W4.3.
- **Approach:** JS clock from the `world` snapshot; month and season names from the snapshot, not duplicated in JS. The first step checks `time` against Evennia's `@time` under `CMD_IGNORE_PREFIXES` (typed `time` may already reach `@time`); if they collide, the key is `date`. The command (aliases `date`, `clock` where free) prints date, time of day, season and, outdoors, the weather — from the same `world_snapshot()` so the two cannot disagree.
- **Testing:** `time` output against `gametime_utils` at a pinned game time; the browser clock matches `time` after five real minutes (four times as fast); an indoor room shows no weather in either.
- **Commit:** `feat(webclient): world panel and the time command (W5.3)`

### Task W5.4 — Location, and `room_look` (WC4)
- **Goal:** Room name, clickable exits, characters and things in the panel; the text stream split into `look` + `room_contents` in the same order.
- **Dependencies:** W3.2, W4.3.
- **Approach:** `world/room_text.py::room_look(char, room)` renders the description with `get_display_exits/characters/things` returning empty through a kwarg, then the three lists alone, and sends two messages. A project subclass of `CmdExtendedRoomLook` replaces the stock one in the cmdset; `Character.at_post_move` stops reaching `DefaultCharacter`'s look (read the MRO first: `Character(ObjectParent, ClothedCharacter)`) and calls `room_look`. Looking at anything other than the current room is unchanged. Exits in the panel use `|lc`; the client routes `room_contents` per WC4.
- **Testing:** the concatenated text of the two messages equals today's single message for the same room and viewer (the canonical-text test, per room fixture: empty room, exits only, characters and things); the move path and the look command both send two messages in order; a telnet session (staff test account) sees no change.
- **Mutations:** swap the two sends (order test fails); drop `room_contents` (canonical-text test fails).
- **Commit:** `feat(webclient): location panel; look sends room_contents as its own message (W5.4)`

## 10. Component 6 — The text area (Claude)

### Task W6.1 — Accessible log, links, the room-lists toggle
- **Goal:** The text area reads well with a screen reader and a keyboard (WC14).
- **Dependencies:** W3.2.
- **Approach:** `role="log"`, `aria-live="polite"`, scroll that does not steal focus; links reachable by Tab; the *room lists in text* toggle (stored in the browser, WC4); a screen-reader pass with Orca on the work machine.
- **Testing:** browser protocol with Orca: a `look`, a `say` from a second account, a link activated from the keyboard.
- **Commit:** `feat(webclient): accessible text log, keyboard links, room-lists toggle (W6.1)`

### Task W6.2 — Tabs by message type
- **Goal:** Channel and conversation text can be read in its own tab; *All* shows everything.
- **Dependencies:** W6.1, W5.4.
- **Approach:** first step: a census of the `type` values the server sends today (Evennia defaults and project commands), recorded in Evennia Ref; then the routing plugin claims typed text for its tabs, unclaimed text falls to `default_out`. No wiki tab (WC15).
- **Testing:** a channel message appears in *Channels* and *All*, a `look` only in *All*.
- **Commit:** `feat(webclient): tabs routed by message type (W6.2)`

## 11. Component 7 — Inventory, equipment, skills (Claude; cuttable, WC13)

### Task W7.1 — Inventory and equipment
- **Goal:** Carried and worn items, with the encumbrance figure `inventory` prints.
- **Dependencies:** W4.1, W5.1. A fifth domain, `inventory`, joins WC5's list and the census.
- **Commit:** `feat(webclient): inventory and equipment panel (W7.1)`

### Task W7.2 — Skills
- **Goal:** Skill values as `skills` prints them, updated when an improvement lands.
- **Dependencies:** W7.1. A sixth domain, `skills`.
- **Commit:** `feat(webclient): skills panel (W7.2)`

## 12. Component 8 — Close-out (Claude)

### Task W8.1 — Merge
Full suite once on the branch tip (ForkTestRunner `--parallel auto`), merge commit, branch deleted.

### Task W8.2 — Documentation
Decomp Rev 2 (records, *Shipped* lines); Testing Ref section for the webclient (browser protocols as run); Evennia Ref section (the webclient's plugin, OOB and template seams as read in §3, payload shapes); BACKLOG; style guide §5 (WC11) if not landed with W2.3; README if a document is added.

## 13. Records

| Task | Commit | Tree | Notes |
| --- | --- | --- | --- |
| W2.1 | `231855e` | `819e0ef` | as *Task 2.1* |
| W2.2 | `6f17c54` | `40798d8` | as *Task 2.2* |
| W2.4 | `37844da` | `9673cad` | merge, PR #24; suite 1159 OK on `main` |
| W2.3 | `bf66108` | `66a45d6` | on `feature/webclient`; 43 art tests, WM1–WM8 |

## 14. Handoffs to ChatGPT

Adam carries one file per delivery. Claude writes it when the task that needs the art is next or can run in parallel:

| Handoff | Needed by | Content |
| --- | --- | --- |
| Outline colour *(delivered in two rounds, 2026-11-06)* | W2.3 | Redraw both body masters with the outer outline in one palette colour ≥ 3:1 against Panel and absent elsewhere in the figure (`muted` or `stone_light` suggested); inner dark details may stay Background; the two masters keep exactly the same coverage; the zone map stays hand-drawn. |
| Panel icons | W5.2–W5.3, when Adam wants icons | Status and weather icons at 32×32 per style guide §5, names from its prefix list. Not needed for any task to ship: every panel works with text alone (WC14). |

## 15. Open questions (each with the task that closes it)

- **OQ-W1 — JS unit tests.** `node --test` for the pure JS (clock arithmetic, routing decision) if Node is installed on both machines; browser protocol only otherwise. Closes at W4.3.
- **OQ-W2 — Order against L6.3.** *Closed (Rev 2): taken as recommended; recorded in roadmap Rev 44 (on `feature/board-cap`).* Recommendation: the webclient is not an alpha prerequisite (the stock client works; decision (G) measures onboarding, which this helps but does not gate), so invitations do not wait for it. Closes when Adam decides; recorded in the roadmap at W8.2 or earlier.
- **OQ-W3 — A dev-board card.** *Closed (Rev 2): taken as recommended; the card lands with `feature/board-cap`, which raises the board test's upper bound from 15 to 20.* Recommendation: one card, *Webclient*, In progress, moved at W8.1. Closes when Adam decides.
- **OQ-W4 — jQuery version.** The newest 3.x release at least two weeks old that the five kept Evennia plugins run under; if any breaks, the version Evennia pins (3.2.1). Closes at W3.1.

## 16. Consequences worth reading twice

- WC4 changes what every `look` sends: two messages instead of one. The text is identical, but anything that reads `type: "look"` downstream (a client trigger, a log) sees the lists move to `room_contents`.
- WC3 means an Evennia upgrade does not update the webclient's page. The host test catches a reintroduced CDN, not an upstream fix; Evennia Ref names the file and hash the copy came from, and an upgrade compares them.
- WC12 means the silhouette carries no information in the alpha. It is the figure the Stage 5 panel will colour, shown now so the layout does not move when that lands.
