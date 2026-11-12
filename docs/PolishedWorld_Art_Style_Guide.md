# PolishedWorld Art Style Guide

> **Rev 7 · 2026-11-12** — what the webclient visual pass's second briefs state (visual decomposition V2.2), written here because both assistants follow it (§1): §5's size table gives the location picture as 96×54, the size that fits the client's *Location* panel at ×1 (`assetpipe.py` still says 320×180 for `room_` and follows at V3.4); §5's file-name examples use the names the client will ask for; a new §5 subsection *Weather icons and pictures*; §8 tells pictures from motifs on a background.
> **Rev 6 · 2026-11-12** — the webclient's first UI family exists (webclient visual decomposition V3.2, on `feature/webclient-visual`): §2 gains `art/ui/<family>/` and its published counterpart `web/static/polishedworld/ui/<family>/`, §10 the command that publishes the icons, and §10's *Tests* the family table in `TestPublishedUpToDate`.
> **Rev 5 · 2026-11-11** — new §5 subsection *Frames and icons*: the edge-contrast property the webclient visual pass's first briefs state (visual decomposition V2.1), written here because both assistants follow it (§1). `validate` does not check it yet.
> **Rev 4 · 2026-11-11** — the outline rule after WC11 (webclient decomposition W2.3, shipped on `main` with the webclient merge `399e306`): §5's outline is Muted `#9D9B8C`, the edge-contrast rule is written as the property, and the Rev 3 open item is closed; §10 lists the body master's two edge checks in `validate`.
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
| `art/ui/<family>/` | Webclient UI masters, one folder per family: `icons/` (`icon_`, `status_`) since the visual pass's V3.2; `frames/` (`frame_`) from V3.1 | No |
| `web/static/polishedworld/` | Pipeline output: cleaned PNG assets and zone masks, served at `/static/polishedworld/`. The body under `characters/body/`; each UI family under `ui/<family>/`, mirroring `art/ui/<family>/` | Yes |

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
| Location pictures | 96×54 | ×1, beside the room's name |
| Header banners | 320×40 | ×1 or ×2 |

- Draw at native resolution. Scale only by whole-number factors, with nearest-neighbour, and render with `image-rendering: pixelated`.
- One asset per image. Overview sheets are style references only, never production assets.
- Strict pixel grid: square logical pixels, no anti-aliasing, glow, blur or gradients.
- Palette colours only (plus the reserved tool colours above where allowed).
- *(Rev 7)* The location picture was 320×180 here until the webclient visual pass (V2.2 lock 1A): the *Location* panel is 224 px wide inside its frame, so that size could not be shown at a whole factor. `assetpipe.py`'s `NATIVE_SIZES` changes with the first delivery (visual decomposition V3.4); until then `validate` rejects a 96×54 `room_` file.

### File names

English, `snake_case`, no spaces or non-ASCII characters, with a type prefix:

`icon_`, `status_`, `weather_day_`, `weather_night_`, `season_`, `item_`, `body_`, `frame_`, `banner_`, `room_`

Examples: `icon_inventory.png`, `status_thirst.png`, `weather_night_raining.png`, `body_left_arm.png`, `banner_summer.png`, `room_indoor.png`.

A file that the client picks by a game value is named by that value as the game writes it: the weather states are `clear`, `raining`, `snowing` and `foggy` (`world/weather.py`), the seasons `spring`, `summer`, `autumn` and `winter`, a room is `indoor` or `outdoor`.

### Body silhouette

- Two hand-drawn masters at 32×64, pixel-aligned: `body_base.png` (the figure) and `body_zonemap.png` (each zone filled with its zone key).
- The seven zone layers are extracted from the zone map by script, never drawn or generated separately.
- The zone map must be drawn by hand in a pixel editor. An AI-generated zone map gets anti-aliasing between zones and will fail validation.
- The figure faces the viewer: the character's **right** side is on the **left** of the image.
- **Outline:** the figure's outer outline is drawn in Muted `#9D9B8C` (5.78:1 against Panel), the figure's one-pixel edge and nowhere else; inner dark details such as the eyes may stay Background `#0E1512` (1.14:1 against Panel, too dark for an edge). Neither colour belongs to any zone mask, so tinting a zone in the client never recolours the outline or the details.
- **Edge contrast:** every figure pixel that shares a side with the background, or with the image border, reaches the palette's `status_min_contrast` (3:1) against Panel. This is the property the outline exists for, and `validate` checks it (§10) whichever colour does the job. Describe it in a brief to the illustrator as this property, not as a procedure ("recolour the dark edge pixels" missed eight hair pixels that had never had an outline).
- **Zone masks:** `split-body` (§10) writes `body_<zone>.png` for the seven zones: white where the zone is, fully transparent elsewhere. Only the alpha channel matters; the client colours a zone by its wound level through CSS `mask-image`. Masks are never shown directly.

### Frames and icons

- **Edge contrast:** every motif pixel that shares a side with `#FF00FF`, or with the image border, is a colour with **Status: Yes** in §3, so it reaches 3:1 against both Panel and Background. A frame drawn for buttons, whose surface is Panel light, also leaves Water off that edge (2.80:1 against Panel light). Border/Wood (2.62:1 against Panel), Dark wood, Deep green, the surfaces and Night blue may be used inside a motif but never on its edge. `validate` checks edge contrast only for `body_base.png` (§10); for frames and icons the delivery is checked in the browser (webclient visual decomposition V3.1–V3.2).
- **Frames** are 9-slice at 48×48 with 16 px corners (CSS `border-image`). The centre 16×16 is never shown and is delivered as `#FF00FF`; each edge piece repeats along the box without a seam.
- **Icons** always stand beside a word that says the same thing (§7). They are told apart in greyscale by shape, and carry no text.

### Weather icons and pictures

- **Night is told by shape** (§7): every `weather_night_` icon contains a moon or stars, and no `weather_day_` icon does. The day and night icons of one state share the same weather motif.
- **Banners and location pictures are full rectangles.** Every pixel is painted, nothing is transparent and `#FF00FF` is not used; where a picture should melt into what is behind it, that colour is painted (Background behind a banner, Panel behind a location picture). The edge-contrast rule above is for motifs on a background and does not apply: all 27 colours may be used anywhere in a picture. No frame is drawn into a picture.
- **A set of banners is one landscape:** terrain, buildings, trunks and paths stand on the same pixels in every file of the set, and only the season's dress changes. A banner shows no time of day and no falling weather, because it is shown at every hour and the weather has its own icon.
- **A location picture says only what the game knows about the room** — today, indoors or outdoors. It shows no season, time of day, weather, lit fire, particular trade or creature. The mood of every picture is the tone guide's (`docs/PolishedWorld_Tone_Guide.md`).

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
- [ ] Background is exactly `#FF00FF` before cleaning, with no magenta inside the motif. A banner or location picture has no `#FF00FF` at all.
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
- an image that is only `#FF00FF`;
- in `body_base.png`, a figure pixel on the edge (sharing a side with `#FF00FF` or the image border) below 3:1 against Panel, and a Muted pixel that is not on the figure's edge (it touches neither `#FF00FF` nor the image border on any side or corner) — an inner fill in the outline colour would silently fall out of every zone mask. The outline colour is the tool's `OUTLINE_KEY`; the surface and the threshold are read from `palette.json` (`contrast_surfaces.panel`, `rules.status_min_contrast`), never restated.

`split-body` additionally requires both masters to cover exactly the same pixels and every zone to keep at least one pixel inside the outline. Every file is validated and every mask built before the first write, so a failure never leaves a partial set in the output folder.

### Publishing the body silhouette

After changing either body master, regenerate both outputs:

```
python art/tools/assetpipe.py clean art/body/body_base.png --out web/static/polishedworld/characters/body
python art/tools/assetpipe.py split-body --out web/static/polishedworld/characters/body
```

### Publishing a UI family

A family published by `clean` alone (the icons; the frames from V3.1) is regenerated whole after any master in it changes, so a removed master also leaves the published folder:

```
rm -f web/static/polishedworld/ui/icons/*.png
python art/tools/assetpipe.py clean art/ui/icons/*.png --out web/static/polishedworld/ui/icons
```

### Tests

```
python -m unittest discover -s art/tools
```

`art/` is not a Python package, so `evennia test` never collects these tests and the game suite does not depend on Pillow. `TestPublishedUpToDate` regenerates the published body files and compares their pixels with the committed ones: a master committed without re-running the commands above fails the suite. Its family table (`FAMILIES`) does the same for every family published by `clean` alone, and also fails on a published file without a master or a master never published.
