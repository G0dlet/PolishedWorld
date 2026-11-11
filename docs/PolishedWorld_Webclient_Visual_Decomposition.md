# PolishedWorld — Webclient Visual Pass Decomposition

> **Rev 2 · 2026-11-11** — **V2.1 is done:** the frame and icon briefs left with Adam as two handoff files (`brief_frames_V2.1.md`, `brief_icons_V2.1.md`), not committed (§6). A *Shipped* line, §11's two rows filled, OQ-V3's first half closed. The briefs' edge rule is written into the art style guide (Rev 5, §5 *Frames and icons*) in the same commit, because the guide is where anything both assistants must follow lives (§1).
> **Rev 1 · 2026-11-11** — first version. Decomposes the *Webclient visual pass* (roadmap Rev 71, *Parallel / opportunistic backlog*; decision log, *Order after the webclient*, amended 2026-11-11) into five components and fourteen tasks, against live source read the same day: `main` at `9652eec` (tree `4858607`), the only branch on origin; tags `alpha-20261107` and `alpha-20261111` (→ `399e306`). Sources read before the locks: the roadmap entry, the art style guide Rev 4 (§3, §5, §6, §7, §9, §10), Evennia Ref Rev 31 §19, the mockup `art/reference/webclient_03.webp`, and `web/static/polishedworld/css/webclient.css` and `web/templates/webclient/webclient.html` as they stand on `main`. Locked at STOPP 0 (Adam took every recommendation): WV1–WV8. With roadmap Rev 72, BACKLOG Rev 104 (one entry added) and README Rev 52.
> **Canonical:** `docs/PolishedWorld_Webclient_Visual_Decomposition.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Design sources:** `docs/PolishedWorld_Art_Style_Guide.md` (palette v0.2.1, §5 production rules and prefixes, §7 accessibility, §9 the mockups are direction and the guide wins, §10 asset pipeline); `docs/PolishedWorld_Webclient_Decomposition.md` (WC1–WC16, which this epic inherits unchanged); Evennia Ref §19 (the page, the script order, the four payloads, the push sites).
**Status:** In progress. V2.1 done (Rev 2); the frame and icon deliveries are with ChatGPT.
**Branch:** `feature/webclient-visual`, created from `main` with `--no-track` (lesson 64); art lands on it as its own commits (WV7).
**Rough scope:** 14 tasks, ~5–7 sessions at 5 h/week of Claude's time, plus ChatGPT's deliveries, which set the pace of Component 3. Component 4 can be cut to BACKLOG without touching anything before it (WV5).
**Roles:** Claude writes the CSS, markup, JS and the briefs; ChatGPT draws the pixel art; Adam is creative director, approves each family and carries the briefs and deliveries between the two (style guide §1).
**Philosophy:** skynda långsamt — the merged client already does what it should; this epic changes how it looks, not what the game does. Every picture is decoration over text that is already there, and every new datum a panel shows is first printed by a text command.

---

## 1. Why this feature

The webclient merged on 2026-11-11 (`399e306`, PR #27) shows every panel the decomposition promised, in plain framed boxes with system fonts and no pictures. Next to the reference mockup `webclient_03` it reads as a prototype, and it is the alpha players' first impression of PolishedWorld (decision log, *Order after the webclient*, amended). The roadmap entry sorted the gap into four piles: (1) CSS and markup only; (2) missing art; (3) a small server change; (4) blocked by game systems and not faked (WC12). This epic takes piles 1 and 2 whole, pile 3 as its last and cuttable component, and leaves pile 4 where it is.

What the epic must not do: show a datum the text cannot say (WC1), load anything from another host (WC2), carry information in a picture or a colour alone (style guide §7, WC14), or treat the mockup as a specification (style guide §9 — its Swedish labels, its *Legend* hit locations, its Hero Points and its portrait are direction, not scope).

## 2. Decisions locked 2026-11-11 (WV1–WV8)

**WV1 — The UI is in English.** Every panel heading, label and button uses the words the text stream uses (*Exits*, *Characters*, *Survival*). The mockup's Swedish is direction only (style guide §9). *Rejected:* B, Swedish headings over English text — a player would read two vocabularies for one datum; C, an i18n layer now — no second language exists to translate into.

**WV2 — No new navigation.** The mockup's top bar (*Spel, Logg, Chatt, Anteckningar, Wiki*) is not built. W6.2's tabs (*All, Channels, Talk*) already do what *Logg* and *Chatt* show; they get the mockup's button style where they stand, above the text, so the DOM order, the Tab order and the visual order stay one order (webclient W3.2 lock 6). The header gets the game's name in the heading font and an *ALPHA* mark written as text. No *Notes* (new function, not look). No *Wiki* (WC15: none exists; when one does, it is an external link marked ↗). *Rejected:* B, the tabs moved visually into the header — the visual order would differ from the focus order; C, A plus a *Notes* feature.

**WV3 — One heading font, a book serif under the OFL, served from the game's own static files.** The class is a book serif (the candidates Alegreya and Cinzel, both OFL), closest to the mockup's logo; body and text-area fonts are unchanged. The mechanism: `woff2` files in `web/static/polishedworld/fonts/`, an `@font-face` rule with `font-display: swap` and a fallback stack, and the font's `OFL.txt` beside it, as `vendor/` keeps jQuery's licence. The file is pinned by a hash in a test, as jQuery is (W3.1). The exact face is chosen at V1.1's STOPP 0 from a sample sheet Adam looks at. *Rejected:* B, a pixel font (Pixelify Sans, Silkscreen) — it matches the art but tires in heading after heading; C, no font of our own.

**WV4 — Two tracks that run in parallel.** The CSS track (Component 1) starts at once and needs no art. The art track (Components 2 and 3) is brief → ChatGPT → `assetpipe.py clean` → CSS, family by family as deliveries arrive. Every use of art has a fallback that is the client as it looks before that family lands: a frame falls back to today's CSS border, an icon to nothing. So the branch is mergeable after any task, and a family ChatGPT has not delivered is a family the merge goes without. *Rejected:* B, art first — Claude idles while ChatGPT draws; C, CSS now and art in a later epic — the epic's goal is the mockup's look, and frames and pictures are most of it.

**WV5 — People and conditions are the last component, and cuttable.** Pile 3 — *People here* split into players and NPCs, and the active conditions — is Component 4, after everything else, so cutting it changes no earlier task (WC13's pattern). Each task's first step is the WC1 parity: the text must say what the panel will show. The source showed that both need text work (§3 *text parity*): look's text has one `Characters:` line, and no player command lists conditions. The mockup's other server data — an exit's destination, an icon per item, culture and homeland, an ambient temperature — and a portrait (WV6) go to BACKLOG, *Webclient: mockup elements without server data* (Rev 104). *Rejected:* B, pile 3 to BACKLOG too; C, more of the mockup's server data in this epic.

**WV6 — One brief per asset family, describing properties; no portrait.** Claude writes one brief per family (`frame_`; `icon_` with `status_`; `weather_day_`/`weather_night_`; `season_`; `banner_`; `room_`), each stating the properties the asset must have and how they are checked, not a procedure for drawing it (lesson 245). The briefs are handoff files Adam carries, written in the chat of the task that needs them; §11 records what each one asked for and what was delivered. No portrait: the server stores no appearance, and a generic face would be WC12's *Intact for a system that does not exist*; the style guide's prefix list stays as it is. *Rejected:* B, a portrait per profession with a new `portrait_` prefix; C, one combined brief — one approval would hold up six families.

**WV7 — One branch, `feature/webclient-visual`.** Art lands on it as its own commits (`assets(webclient-visual): …`) next to the CSS that uses it. WC16's separate assets branch existed because the art was ready before the client code; here it arrives after. *Rejected:* B, a second branch for the art, as W2 had.

**WV8 — L6 does not wait.** L6.1 deploys `alpha-20261111` as the runbook says; the pass gets its own annotated tag when it merges (V5.1), and deploying that tag is the live tagged deploy LM10 asks for. *Rejected:* B, L6 waits for the pass.

**Inherited, restated (not new):** WC1 (text stays canonical), WC2 and WC3 (no external host; the host test renders the page and fails on any foreign `src`/`href`), WC10 (whole-factor scaling, `image-rendering: pixelated`), WC12 (the character panel shows only what the server holds), WC14 (accessibility is a lock: every new image is decorative — `alt=""` or a CSS background — and the information beside it stays text), WC15, WC16's `evennia reload` from the shell (only the launcher runs `collectstatic`).

## 3. Verified source anchors (read 2026-11-11, `main` at `9652eec`)

| Anchor | Where | What it fixes |
| --- | --- | --- |
| palette tokens | `web/static/polishedworld/css/webclient.css:25–51` | the 27 colours as `--pw-<key>`, verbatim from `palette.json`; every new rule names a token, never a hex value |
| body font | `webclient.css:64` | `system-ui, "DejaVu Sans", "Segoe UI", Roboto, sans-serif`; WV3 changes headings only |
| tabs | `webclient.css:325–351`; `webclient.html` `#pw-tabs` | the selected tab is shown by weight and a 5 px bottom border as well as colour; V1.2 keeps a non-colour marker |
| send button | `webclient.css:404–413`; `webclient.html` `<button id="inputsend">Send</button>` | Evennia's `default_in.js` finds the button by id; the ▶ is decoration, the name *Send* stays (V1.4) |
| page landmarks | `webclient.html` (`#pw-header`, two `<aside>`, `#pw-tabs`, `<main>`) | DOM order is Tab order (W3.2 lock 6); WV2 adds nothing to the header's order but text |
| prefixes and sizes | `art/tools/assetpipe.py:34–44` (`NATIVE_SIZES`) | every family this epic needs is already known to `validate`: `weather_night_`, `weather_day_`, `icon_`, `status_`, `season_`, `item_` 32×32; `frame_` 48×48; `room_` 320×180; `banner_` 320×40 |
| published assets | `web/static/polishedworld/characters/body/` | the only art served today: `body_base.png` and the seven zone masks |
| weather states | `world/weather.py:23` (`WEATHER_STATES = ("clear", "raining", "snowing", "foggy")`); `world/client_state.py:196` (`"weather": weather.get_current_weather()`) | four states, sent as the key; eight weather icons with day and night (V3.3) |
| times of day | `world/gametime_utils.py:46–54` (`TIMES_OF_DAY`: night, dawn, morning, day, afternoon, evening, dusk) | which periods show a night icon is V3.3's STOPP 0 |
| room payload | `world/client_state.py:201–223` (`room_snapshot`; `"characters"` at `:223`); `world/room_text.py:75` (`room_lists`) | `indoor` exists, so a location picture by indoor/outdoor needs no server change (V3.4); `characters` is one list (V4.1) |
| gauge text | `web/static/polishedworld/js/pw_survival.js:46` (`numbers: value.current + "/" + value.max`); `pw_gauge.js` `barWidth` | the mockup's percentage is not a datum the text prints; V1.3 decides |
| text parity | `typeclasses/rooms.py:335` (`"\n|wCharacters:|n {names}"`); no read of `buffs` in `commands/` | V4.1 and V4.2 each need a text change before a panel change |
| buff writers | `typeclasses/characters.py:1385, 1397–1398`; `world/survival_ticker.py:98, 101`; `world/thermal.py:157, 159` | V4.2's push sites start from these seven lines |
| profession | `world/professions.py` (`character.db.profession`) | the only identity datum under the mockup's name that exists; culture and homeland do not (BACKLOG Rev 104) |

## 4. Dependency graph

```
Component 1 — CSS track (no art)          Component 2 — briefs (docs)
  V1.1 heading font (WV3)                   V2.1 frames, icons, status
   └─ V1.2 header, headings, tabs           V2.2 weather, season, banner, room
       ├─ V1.3 gauges and lists                    │  (ChatGPT draws; Adam approves)
       └─ V1.4 command line                        ▼
                                          Component 3 — art in the client
            V1.2 ──────────────────────►    V3.1 frames          (needs V2.1's delivery)
                                            V3.2 heading and gauge icons (V2.1)
                                            V3.3 weather and season icons (V2.2)
                                            V3.4 banner and location picture (V2.2)

Component 4 — people and conditions (cuttable, WV5)
  V4.1 players and NPCs (text, payload, panel)
  V4.2 active conditions (text command, payload, push sites)

Component 5 — close-out
  V5.1 merge and tag (WV8) ─► V5.2 documentation
```

**Recommended order:** V2.1 first — ChatGPT's time is the long pole, so the first brief leaves before any CSS is written — then V1.1, V1.2, V2.2, V1.3, V1.4; Component 3 as deliveries arrive, between Component 1 tasks if they come early; then Component 4 (or cut it); then V5.1 and V5.2. Each task is its own STOPP sequence; the order may change at any STOPP 0 if a delivery arrives.

**The dev board:** the card *A better-looking webclient: frames, icons and pictures* moves from Planned to In progress in the docs commit that records the first code task, and to Done at V5.2.

## 5. Component 1 — The CSS track (Claude)

### Task V1.1 — The heading font (WV3)
- **Goal:** Panel headings and the header's title are set in a self-hosted OFL book serif.
- **Dependencies:** none.
- **Approach:** first step: read the candidates' sources (the font files and their `OFL.txt`) and produce a sample sheet — the client's real headings in each candidate, at the sizes the panels use — for Adam to choose from at STOPP 0. Then: the chosen face as `woff2` in `web/static/polishedworld/fonts/` with its `OFL.txt`; one `@font-face` rule with `font-display: swap`, a relative `url()` and a fallback stack; the face applied to `.pw-title` and the panels' `h2`. If only TTF is published, the conversion and its tool are recorded in the commit body and Evennia Ref.
- **Testing:** `test_webclient_theme`: the `@font-face` `src` is a path under `/static/polishedworld/fonts/`, the file exists, its hash is the pinned one, `OFL.txt` sits beside it and is non-empty; the host test (WC3) still passes. Browser protocol: DevTools *Network* shows the font from the game's host only; with the file renamed, headings fall back and nothing breaks.
- **Commit:** `feat(webclient): self-hosted heading font (V1.1)`

### Task V1.2 — Header, panel headings, tabs
- **Goal:** The header, the panel headings and the text tabs look like the mockup's, within the palette.
- **Dependencies:** V1.1.
- **Approach:** the header: the game's name in the heading font and an *ALPHA* mark as text in a bordered badge (Gold/Link on Panel light). Panel headings: heading font, Highlight, a rule beneath in Border/Wood, room on the left for V3.2's icon. Tabs: the mockup's button style, with the selected tab still marked by more than colour (§3 *tabs*). No change to the DOM order (WV2).
- **Testing:** theme tests that the rules exist and name tokens only; the template's landmark and tab tests unchanged; browser protocol at 1920 px and below the 80 rem breakpoint, and the Tab order walked from the top.
- **Commit:** `feat(webclient): header, panel headings and tabs styled (V1.2)`

### Task V1.3 — Gauges and lists
- **Goal:** Gauges read as the mockup's — label left, numbers right, bar beneath — and the panels' lists get markers, with exits as an arrow and a link.
- **Dependencies:** V1.2.
- **Approach:** STOPP 0 decides the gauge's number: keep `current/max` (what `status` prints) moved to the right, or a percentage the text does not print (§3 *gauge text*; WC1 leans to the former). Lists: a square marker in CSS; exits as `→` from CSS before a link in Gold/Link, so direction is told by the arrow and the link, not by colour.
- **Testing:** `node --test tests/js/*.js` stays green; theme tests for the marker and arrow rules; browser protocol on a room with two exits and a stack of things.
- **Commit:** `feat(webclient): gauges and panel lists styled (V1.3)`

### Task V1.4 — The command line
- **Goal:** The command line and its send button look like the mockup's.
- **Dependencies:** V1.2.
- **Approach:** the field framed in Gold/Link when focused; the button shows ▶ while its accessible name stays *Send* (visible text replaced by a decorative glyph and a visually hidden *Send*, or `aria-label` — STOPP 0); the id `inputsend` and the button's place in the DOM unchanged (§3 *send button*). Below the breakpoint, the same.
- **Testing:** the template test that `#inputsend` exists keeps passing and a new test reads the button's accessible name; browser protocol: clicking ▶ sends, and Enter sends as today.
- **Commit:** `feat(webclient): command line styled (V1.4)`

## 6. Component 2 — Briefs (Claude writes, Adam carries)

A brief task commits nothing to the branch: its result is a handoff file in the chat and a row in §11, recorded in this document on `main` (a Rev), so the catalogue does not grow by one file per brief.

### Task V2.1 — Briefs: frames, heading icons, gauge icons
- **Goal:** ChatGPT has what it needs to draw the frames and the icons.
- **Dependencies:** none.
- **Approach:** two briefs. **Frames** (`frame_`, 48×48, 9-slice with 16 px corners, style guide §5): which surfaces get one (panels, the text area, buttons — STOPP 0), and the properties: palette colours only on `#FF00FF`; the 16 px edge strips repeat without a seam; the corners carry the ornament; the centre 16×16 is not shown (the panel's background colour is); the inner edge reads against Panel. **Icons** (`icon_` for each panel heading; `status_` for health, hunger, thirst, fatigue; 32×32): one motif per file, readable at ×1 without colour, distinct in silhouette from its neighbours, each edge pixel against transparency at 3:1 against Panel (the property the body's outline exists for, §5).
- **Testing:** Adam reads each brief before carrying it; §11 gains the rows.
- **Commit:** `docs(webclient-visual): frame and icon briefs (V2.1)` (on `main`)
- **Shipped (Rev 2):** two handoff files carried by Adam, `brief_frames_V2.1.md` and `brief_icons_V2.1.md`, each self-contained: the 27 hex values with a *Status* column, the mockup as direction, the properties as requirements and a checklist ChatGPT ticks before delivery. Locked at STOPP 0 (Adam took every recommendation): **(1A)** two frames — `frame_panel` on each section of the side panels and on the text area, `frame_button` on the tabs, the ▶ button and the *ALPHA* badge; the command line's focus edge stays CSS; **(2A)** eight `icon_` files, the five panel headings and the location panel's three list labels, named by the text's words (WV1): `character`, `survival`, `inventory`, `world`, `location`, `exits`, `characters`, `things`; **(3A)** four `status_` files, `health`, `hunger`, `thirst`, `fatigue` — one fatigue icon, not one per Legend level (WC12); it stands beside the word, so §7's shape-per-level rule does not apply to it; **(4A)** two self-contained briefs with checklists. **Found at STOPP 0:** today's panel border, Border/Wood `#865638`, is 2.62:1 against Panel, under the 3:1 a graphical edge needs; and `assetpipe validate` checks edge contrast only for `body_base.png`. So the briefs state the edge as a property — every pixel touching magenta or the image border is a *Status: Yes* colour (≥ 3:1 against Panel and Background), and on `frame_button` not Water, which reaches 2.80:1 against the button's Panel light — and V3.1–V3.2 check it in the browser.

### Task V2.2 — Briefs: weather, season, banner, location
- **Goal:** ChatGPT has what it needs to draw the world panel's icons and the two pictures.
- **Dependencies:** none (after V2.1 by order, not by need).
- **Approach:** **Weather** — eight files, `weather_day_<state>` and `weather_night_<state>` for the four states in `world/weather.py:23`. **Seasons** — four `season_` files. **Banner** — `banner_` at 320×40, how many (one per season is the default; times of day are not) decided at STOPP 0. **Location** — `room_` at 320×180, the default two (`room_indoor`, `room_outdoor`), since `indoor` is the only room datum the client has. Properties as V2.1's, plus for the pictures: legible at ×1 in a 17 rem panel, no text in the image, and no figure that reads as a specific person.
- **Testing:** as V2.1.
- **Commit:** `docs(webclient-visual): weather, season, banner and location briefs (V2.2)` (on `main`)

## 7. Component 3 — Art in the client (Claude, per family as delivered)

Each task starts when its family is delivered and Adam has approved it. The masters go under `art/<family>/` (style guide §2: source folders are created when their first master arrives), the cleaned files under `web/static/polishedworld/` in a folder per family (the folder names are V3.1's STOPP 0 and the style guide's next Rev). Every task runs `assetpipe.py validate` and `clean`, and extends `TestPublishedUpToDate`'s idea to its family: a published file must be what `clean` makes of its master.

### Task V3.1 — Frames
- **Goal:** Panels, the text area and the buttons wear the delivered frames.
- **Dependencies:** V2.1's frame delivery; V1.2.
- **Approach:** `border-image` with a slice of 16 and a border width of 16 px × a whole factor (WC10), `repeat` or `round` per the delivery's edges; `border-style` and colour kept under it, so a missing file shows today's border (WV4).
- **Testing:** a theme test that every `border-image` `url()` resolves to a committed file; the published-up-to-date test; browser protocol at ×1 and ×2 and with the file renamed.
- **Commit:** `assets(webclient-visual): frames` and `feat(webclient): panel frames (V3.1)`

### Task V3.2 — Heading and gauge icons
- **Goal:** Each panel heading and each gauge carries its icon.
- **Dependencies:** V2.1's icon delivery; V1.2, V1.3.
- **Approach:** icons as CSS backgrounds (decorative by construction), at ×1 or ×2; the heading's text unchanged.
- **Testing:** theme test that every icon `url()` resolves; the published-up-to-date test; a check that no heading's text changed (template tests).
- **Commit:** `assets(webclient-visual): icons` and `feat(webclient): heading and gauge icons (V3.2)`

### Task V3.3 — Weather and season icons
- **Goal:** The world panel shows the weather and season as icons beside their words.
- **Dependencies:** V2.2's weather and season deliveries.
- **Approach:** `pw_world.js` maps the weather key and the browser's own period and season (WC9) to a file name; STOPP 0 decides which periods count as night. Indoors the weather row behaves as today.
- **Testing:** `tests/js/test_pw_world.js` for the mapping; a Python test that the JS map's weather keys are exactly `WEATHER_STATES` (the pattern of the `DOMAINS` comparison); browser protocol through `weather` (staff) changes and a night.
- **Commit:** `assets(webclient-visual): weather and season icons` and `feat(webclient): weather and season icons (V3.3)`

### Task V3.4 — Banner and location picture
- **Goal:** The header shows a banner and the location panel a picture, both decorative.
- **Dependencies:** V2.2's banner and room deliveries; V1.2.
- **Approach:** banner by season, picture by `indoor` (§3 *room payload*); both `alt=""`; below the breakpoint, whether they show is STOPP 0 (a phone has no room to spare).
- **Testing:** theme and template tests; browser protocol walking indoors and out, and across a season change.
- **Commit:** `assets(webclient-visual): banner and location pictures` and `feat(webclient): banner and location picture (V3.4)`

## 8. Component 4 — People and conditions (Claude; cuttable, WV5)

### Task V4.1 — Players and NPCs
- **Goal:** Text and panel tell players and NPCs apart in a room.
- **Dependencies:** none (after Component 1 by order).
- **Approach:** first step: a census of what `room_lists` puts in `characters` (players, ambient NPCs from `typeclasses/npcs.py`, creatures) and how each is told apart today. Then the text first (WC1): look's `Characters:` line (§3 *text parity*) becomes two, or stays one with a marker — STOPP 0. Then the payload (`characters` split in `room_snapshot`, `pw_room.js`), and the panel.
- **Testing:** `test_room_look` and `test_client_state` for the text and the payload; `tests/js/test_pw_room.js`; in-game protocol with a second account, the sweeper and a creature in one room.
- **Commit:** `feat(webclient): players and NPCs apart in text and panel (V4.1)`

### Task V4.2 — Active conditions
- **Goal:** A player can list their active conditions as text, and the character panel shows the same list.
- **Dependencies:** none.
- **Approach:** first step: a census of the buffs a player can carry (the seven writer lines in §3 *buff writers*) and which are conditions a player should see. Then a text home — a section of `status` or its own command, STOPP 0 — then `conditions: [str]` in `char`, with pushes at the writers added to `TestPushCensus` (WC8).
- **Testing:** command tests, `test_client_state` (payload and census), `tests/js/test_pw_char.js`; in-game protocol: get cold, starve a little, die once (`DeathWeakness`), and read the text and the panel each time.
- **Commit:** `feat(webclient): active conditions in text and panel (V4.2)`

## 9. Component 5 — Close-out (Claude)

### Task V5.1 — Merge and tag (WV8)
- **Goal:** `feature/webclient-visual` is on `main` and tagged.
- **Dependencies:** every task not cut.
- **Approach:** the full suite once on the merge result (a local `--no-ff` merge in a detached HEAD, `"#10"` stashed), trees compared; PR with a merge commit; annotated tag `alpha-YYYYMMDD`. The runbook names the new tag at V5.2.
- **Testing:** the suite's count predicted first (`git grep -c 'def test_' -- tests`), then run; `node --test tests/js/*.js`; `python -m unittest discover -s art/tools`.
- **Commit:** the merge commit.

### Task V5.2 — Documentation
- **Goal:** The docs say what the merged client is.
- **Dependencies:** V5.1.
- **Approach:** Evennia Ref §19 (fonts, assets, any payload change from Component 4); Testing Ref §22; the style guide's next Rev (published folders, the families that exist); this document DONE; roadmap ✅; the dev board card to Done; runbook (the tag); the lessons batch read against the register (handoff candidate (a)).
- **Commit:** one or more docs commits on `main`, split at STOPP 0.

## 10. Records

| Task | Commit | Tree | Note |
| --- | --- | --- | --- |
| — | | | |

## 11. Handoffs to ChatGPT

| Brief | Task | Files asked for | Delivered |
| --- | --- | --- | --- |
| Frames | V2.1 | `frame_panel.png`, `frame_button.png`, 48×48, 9-slice with 16 px corners (brief `brief_frames_V2.1.md`, sent 2026-11-11) | |
| Icons | V2.1 | `icon_character`, `icon_survival`, `icon_inventory`, `icon_world`, `icon_location`, `icon_exits`, `icon_characters`, `icon_things`, `status_health`, `status_hunger`, `status_thirst`, `status_fatigue`, 32×32 (brief `brief_icons_V2.1.md`, sent 2026-11-11) | |
| Weather | V2.2 | `weather_day_<state>.png`, `weather_night_<state>.png` for clear, raining, snowing, foggy | |
| Seasons | V2.2 | `season_spring/summer/autumn/winter.png` | |
| Banner | V2.2 | `banner_*.png`, 320×40 (count decided at V2.2) | |
| Location | V2.2 | `room_indoor.png`, `room_outdoor.png`, 320×180 (default) | |

## 12. Open questions (each with the task that closes it)

- **OQ-V1 — The home machine's Node version.** Not read since OQ-W1 closed. Until it is, the JS tests run at work or in the sandbox. Closes at the first session on the home machine.
- **OQ-V2 — Percentage or numbers on a gauge.** V1.3.
- **OQ-V3 — Which surfaces get a frame, and which periods are night.** *Surfaces closed (Rev 2): V2.1 lock 1A.* The night periods close at V3.3.

## 13. Consequences worth reading twice

- WV4 makes every family optional at merge time. A family that never arrives is not a failed task; its row in §11 stays empty and V5.2 says so.
- A frame image replaces a border that today carries the panels' outline. If a delivered frame's inner edge fails 3:1 against Panel, the panels lose their edge for low-vision players; V2.1's brief states the property and V3.1's protocol checks it.
- Component 4 changes what `look` sends (V4.1) and what `char` carries (V4.2). Anything downstream that reads `Characters:` or `char`'s keys sees the change, as WC4's split was seen.
- A font is a binary in history forever, as the mockups are (style guide §9). Only the face chosen is committed, in `woff2`, and only the weights the client uses.
