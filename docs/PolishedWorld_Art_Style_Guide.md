# PolishedWorld Art Style Guide

> **Rev 3 · 2026-11-06** — the asset pipeline exists (`art/tools/assetpipe.py`, Tasks 2.1–2.2 on `feature/webclient-assets`): §1 and §2 lose "planned", §5 gains the outline rule and the zone masks, new §10 documents the tool. Open item: the outline's contrast against Panel.
> **Rev 2 · 2026-11-06** — add the reference mockups in `art/reference/` (three WebP files, direction only) to the directory layout and a new §9.
> **Rev 1 · 2026-11-06** — first version: palette v0.2.1 (locked), reserved tool colours, production rules, Legend UI rules, QA checklist.
> **Canonical:** `docs/PolishedWorld_Art_Style_Guide.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**Palette version:** v0.2.1 (locked)
**Status:** Authoritative. This file and `art/palette/` are the single source of truth for all pixel art used by the website and the webclient. Any change to the palette or production rules is made here first, with a new version number.

## 1. Roles and workflow

- **Asset design** (visual direction, palette proposals, asset drawing) is done with ChatGPT.
- **Implementation** (asset pipeline, validation, webclient and website integration, Mongoose Legend rule checks) is done with Claude.
- **Adam** is creative director: approves palette and assets, decides priorities, and carries handoff files between the two. Neither assistant sees the other's conversation, so anything both must follow is written into this guide.

Pipeline:

1. An asset is delivered as one image per asset, at native resolution, on a pure magenta background.
2. The asset is validated and cleaned by `art/tools/assetpipe.py` (§10): name, native size, palette match, magenta removed to transparency.
3. The cleaned file is committed under `web/static/polishedworld/` and used by the client.

## 2. Directory layout

| Path | Contents | Served to players |
|---|---|---|
| `art/palette/` | Palette files (`palette.json`, `palette.hex`, `palette.gpl`) | No |
| `art/reference/` | Concept mockups showing visual direction (WebP) | No |
| `art/body/` | Body masters: `body_base.png`, `body_zonemap.png` | No |
| `art/tools/` | Asset pipeline, its tests and its `requirements.txt` (§10) | No |
| `web/static/polishedworld/` | Pipeline output: cleaned PNG assets and zone masks, served at `/static/polishedworld/` | Yes |

Source folders for other asset types under `art/` are created when their first master arrives.

Source masters live outside `web/static/` because everything under `web/static/` is collected by Evennia and served publicly. The `polishedworld/` namespace keeps our files apart from Evennia's own static files.

## 3. Palette v0.2.1

27 motif colours, maximum 32. Five slots are deliberately left free: add a colour only when a real asset shows it is needed, as a new palette version.

Contrast is the WCAG relative-luminance ratio against Panel `#17231F` and Background `#0E1512`.

- **Text: Yes** means at least 4.5:1 against both surfaces (normal text).
- **Status: Yes** means at least 3:1 against both surfaces (graphical status markers).
- Approval holds only against these two dark surfaces. Any other background (a room image, a banner) needs a separate check.

| Key | Name | Hex | Text | Status | Contrast panel / bg | Note |
|---|---|---|---|---|---|---|
| `background` | Background | `#0E1512` | No | No | 1.14 / 1.00 | Page background |
| `panel` | Panel | `#17231F` | No | No | 1.00 / 1.14 | Panel surface |
| `panel_light` | Panel light | `#24352F` | No | No | 1.25 / 1.43 | Raised panel surface |
| `border_wood` | Border / Wood | `#865638` | No | No | 2.62 / 3.00 | Merged frame and wood colour |
| `copper` | Copper | `#B87943` | Yes | Yes | 4.51 / 5.16 | Metal, accent |
| `gold_link` | Gold / Link | `#D8A657` | Yes | Yes | 7.34 / 8.38 | Merged gold and link colour |
| `highlight` | Highlight | `#F2CC83` | Yes | Yes | 10.60 / 12.11 | Light accent |
| `text` | Text | `#E8DCC4` | Yes | Yes | 11.93 / 13.63 | Primary text |
| `muted` | Muted | `#9D9B8C` | Yes | Yes | 5.78 / 6.61 | Secondary text |
| `health` | Health / OK | `#4CAF50` | Yes | Yes | 5.83 / 6.66 | Intact / OK |
| `deep_green` | Deep green | `#286C39` | No | No | 2.54 / 2.90 | Forest shade |
| `warning` | Warning | `#F0A12B` | Yes | Yes | 7.59 / 8.67 | Warning, minor wound |
| `serious` | Serious | `#D94A40` | No | Yes | 3.86 / 4.41 | Serious wound; not for small text |
| `critical` | Critical | `#C2558A` | No | Yes | 3.83 / 4.37 | Major wound |
| `info` | Info | `#4E9AC7` | Yes | Yes | 5.22 / 5.97 | Information |
| `magic` | Magic | `#9B67CF` | No | Yes | 4.04 / 4.61 | Magic; not for small text |
| `dark_wood` | Dark wood | `#4B3026` | No | No | 1.35 / 1.54 | Wood shade |
| `stone` | Stone | `#777C79` | No | Yes | 3.81 / 4.36 | Stone, neutral graphic symbols |
| `stone_light` | Stone light | `#B0ADA0` | Yes | Yes | 7.20 / 8.22 | Stone highlight |
| `grass` | Grass | `#63864B` | No | Yes | 3.89 / 4.44 | Vegetation; not for small text |
| `water` | Water | `#367D9A` | No | Yes | 3.51 / 4.02 | Water; not for small text |
| `fire` | Fire | `#F47B28` | Yes | Yes | 5.95 / 6.80 | Fire |
| `skin_light` | Skin light | `#E7B98A` | Yes | Yes | 9.03 / 10.32 | Light skin tone |
| `skin_dark` | Skin dark | `#A86E4D` | No | Yes | 3.86 / 4.41 | Dark skin tone |
| `blossom_pink` | Blossom pink | `#EFA0BA` | Yes | Yes | 8.03 / 9.17 | Spring blossom |
| `snow_ice` | Snow / ice | `#D7F0F4` | Yes | Yes | 13.62 / 15.56 | Snow and ice |
| `night_blue` | Night blue | `#172A4A` | No | No | 1.13 / 1.29 | Night scenes; not for text or status |

### Palette files

- `palette.json` – machine-readable source with keys, flags and contrast values. Used by scripts.
- `palette.hex` – plain hex list, one colour per line.
- `palette.gpl` – GIMP palette format, loadable in Pixelorama, LibreSprite and GIMP. Use it when drawing so colours are exact from the start.

All three are generated from the same data and must always agree.

### Known close pairs

| Pair | RGB distance |
|---|---|
| Background – Panel | 21.1 (intentional, UI surfaces) |
| Copper – Skin dark | 21.8 |
| Highlight – Skin light | 23.0 |

Assets drawn directly with the palette are unaffected, since validation requires exact matches. When AI-generated images are quantised, a pixel can land on the wrong colour of a close pair. Keep copper and skin visually separate in motifs and expect manual fixes at review.

## 4. Reserved tool colours

These are never motif colours and must never appear in the client.

- **Chroma key:** `#FF00FF`. Background of every delivered image, removed to transparency by the pipeline. Must not occur inside a motif.
- **Zone keys** (only in `body_zonemap.png`):

| Zone | Key |
|---|---|
| head | `#FF0000` |
| chest | `#00FF00` |
| abdomen | `#0000FF` |
| right_arm | `#FFFF00` |
| left_arm | `#00FFFF` |
| right_leg | `#FF8000` |
| left_leg | `#8000FF` |

## 5. Production rules

### Native sizes

| Asset type | Native size | Typical display |
|---|---|---|
| Icons (panel, status, weather, item) | 32×32 | ×1 or ×2 |
| Body silhouette and zone layers | 32×64 | ×2 or ×4 |
| UI frames (9-slice, 16 px corners) | 48×48 | CSS `border-image` |
| Location images | 320×180 | ×4 (1280×720) |
| Header banners | 320×40 | ×4 (1280×160) |

- Draw at native resolution. Scale only by whole-number factors, with nearest-neighbour, and render with `image-rendering: pixelated`.
- One asset per image. Overview sheets are style references only, never production assets.
- Strict pixel grid: square logical pixels, no anti-aliasing, glow, blur or gradients.
- Palette colours only (plus the reserved tool colours above where allowed).

### File names

English, `snake_case`, no spaces or non-ASCII characters, with a type prefix:

`icon_`, `status_`, `weather_day_`, `weather_night_`, `season_`, `item_`, `body_`, `frame_`, `banner_`, `room_`

Examples: `icon_inventory.png`, `status_thirst.png`, `weather_night_rain.png`, `body_left_arm.png`, `banner_summer_evening.png`, `room_smithy.png`.

### Body silhouette

- Two hand-drawn masters at 32×64, pixel-aligned: `body_base.png` (the figure) and `body_zonemap.png` (each zone filled with its zone key).
- The seven zone layers are extracted from the zone map by script, never drawn or generated separately.
- The zone map must be drawn by hand in a pixel editor. An AI-generated zone map gets anti-aliasing between zones and will fail validation.
- The figure faces the viewer: the character's **right** side is on the **left** of the image.
- **Outline:** the figure's outline (and dark details such as the eyes) is drawn in Background `#0E1512`. Those pixels belong to no zone mask, so tinting a zone in the client never recolours the outline.
- **Zone masks:** `split-body` (§10) writes `body_<zone>.png` for the seven zones: white where the zone is, fully transparent elsewhere. Only the alpha channel matters; the client colours a zone by its wound level through CSS `mask-image`. Masks are never shown directly.
- **Open item:** Background `#0E1512` has only 1.14:1 contrast against Panel, so the outline nearly disappears on a plain panel. To be settled when the client panel is built: either the silhouette sits on Panel light, or the outline moves to a lighter palette colour (which would change the masters and the rule above).

## 6. Mongoose Legend UI rules

Labels and assets follow the Legend core rules:

- **Seven hit locations** for humans: head, chest, abdomen, right arm, left arm, right leg, left leg.
- **Wound levels** per location:
  - Intact: HP at starting value.
  - Minor Wound: HP above 0 but below starting value.
  - Serious Wound: HP 0 or below, but above minus the starting value.
  - Major Wound: HP at or below minus the starting value. At a boundary, the more severe level applies.
- A limb made useless by a failed Resilience test is a separate functional state ("useless arm"), shown with its own symbol or text, not only a wound colour.
- **Fatigue levels:** Fresh, Winded, Tired, Wearied, Exhausted, Debilitated.
- **Combat resources:** Combat Actions and Hero Points. Not Action Points or Luck Points, which belong to other rule systems.
- Combat Actions are shown only where the mechanics justify it (for example during combat). Hero Point limits are not assumed until there is a game design decision.

## 7. Accessibility

No state may be distinguished by colour alone. Shape, symbol or text always carries the information; colour reinforces it. Fatigue icons, for example, change shape level by level, not just colour.

## 8. QA checklist

- [ ] Correct native dimensions and file name prefix.
- [ ] Every motif pixel is an exact palette colour.
- [ ] Background is exactly `#FF00FF` before cleaning, with no magenta inside the motif.
- [ ] No semi-transparent edges, anti-aliasing or interpolated colours.
- [ ] Readable at native size and without colour.
- [ ] Body layers align exactly and follow the right/left convention.
- [ ] Reviewed at real size in the client.
- [ ] Style guide, manifest and any deviations updated together with the files.

## 9. Reference mockups

`art/reference/` holds three concept images that show the agreed visual direction. They are **references, not production assets**: values shown in them are examples, and nothing is cut out of them for use in the client.

| File | Shows |
|---|---|
| `website_05_terminal_preview.webp` | Website landing page with tagline, terminal preview and feature cards |
| `webclient_03.webp` | Webclient layout: character panel with Legend hit locations, fatigue and combat resources, game text, world/location/people/items/exits panels |
| `asset_concept_02.webp` | Asset pack v0.1 overview: icon families, palette swatches, banner and location image formats |

Where a reference image disagrees with this guide (for example zone colours on the body silhouette in `asset_concept_02.webp`, or the palette swatches, which predate v0.2.1), this guide wins.

The mockups were stored as WebP (quality 85) instead of the delivered PNGs to keep the repository small: Git keeps every binary in history permanently, and every clone, including the alpha server's, downloads it. The other concept images from the v0.2.1 design handoff are kept outside the repository.

## 10. Asset pipeline

`art/tools/assetpipe.py` enforces this guide on masters before anything reaches `web/static/`. It is offline tooling: the game server never imports it, and Pillow is listed in `art/tools/requirements.txt` only (`pip install -r art/tools/requirements.txt`). Palette and tool colours are read from `art/palette/palette.json`, never duplicated in the code.

Run from the repository root:

| Command | Does |
|---|---|
| `python art/tools/assetpipe.py validate FILE...` | Checks each master against §3–5. Writes nothing. |
| `python art/tools/assetpipe.py clean FILE... --out DIR` | Validates, then writes an RGBA copy with `#FF00FF` made transparent. Zone maps are refused. |
| `python art/tools/assetpipe.py split-body --out DIR` | Validates `art/body/body_base.png` and `art/body/body_zonemap.png` (override with `--base`/`--zonemap`), then writes the seven zone masks. |

Exit codes: `0` all files passed, `1` at least one failed, `2` usage error (for example an unreadable palette).

What `validate` rejects:

- a name that is not lowercase `snake_case` ASCII `.png`, or has no known type prefix (§5);
- a size other than the prefix's native size;
- any pixel that is not fully opaque (masters carry magenta, not alpha);
- any colour that is not an exact palette colour or `#FF00FF` (one channel off by one fails); in `body_zonemap.png`, any colour that is not a zone key or `#FF00FF`, and a missing zone;
- an image that is only `#FF00FF`.

`split-body` additionally requires both masters to cover exactly the same pixels and every zone to keep at least one pixel inside the outline. Every file is validated and every mask built before the first write, so a failure never leaves a partial set in the output folder.

### Publishing the body silhouette

After changing either body master, regenerate both outputs:

```
python art/tools/assetpipe.py clean art/body/body_base.png --out web/static/polishedworld/characters/body
python art/tools/assetpipe.py split-body --out web/static/polishedworld/characters/body
```

### Tests

```
python -m unittest discover -s art/tools
```

`art/` is not a Python package, so `evennia test` never collects these tests and the game suite does not depend on Pillow. `TestPublishedUpToDate` regenerates the published body files and compares their pixels with the committed ones: a master committed without re-running the commands above fails the suite.
