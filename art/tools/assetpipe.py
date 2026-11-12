"""
PolishedWorld asset pipeline: validate and clean pixel art masters.

Offline tooling. Nothing in the game server imports this module, and Pillow
is listed in ``art/tools/requirements.txt`` only. The rules enforced here are
the ones in ``docs/PolishedWorld_Art_Style_Guide.md`` (sections 3-5); the
palette is read from ``art/palette/palette.json``, never duplicated here.

Usage (from the repository root)::

    python art/tools/assetpipe.py validate art/body/*.png
    python art/tools/assetpipe.py clean art/body/body_base.png --out web/static/polishedworld/characters/body
    python art/tools/assetpipe.py split-body --out web/static/polishedworld/characters/body

Exit codes: 0 = everything valid (and cleaned), 1 = at least one file
failed validation, 2 = usage error (bad arguments, unreadable palette).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, UnidentifiedImageError

PALETTE_PATH = Path(__file__).resolve().parents[1] / "palette" / "palette.json"

# Prefix -> native (width, height), style guide section 5. Longer prefixes are
# listed before any prefix they start with, so the first match is the right one.
NATIVE_SIZES: dict[str, tuple[int, int]] = {
    "weather_night_": (32, 32),
    "weather_day_": (32, 32),
    "icon_": (32, 32),
    "status_": (32, 32),
    "season_": (32, 32),
    "item_": (32, 32),
    "body_": (32, 64),
    "frame_": (48, 48),
    # 96x54, the size the webclient's Location panel shows at x1 (visual
    # pass V2.2 lock 1A, style guide Rev 7); 320x180 until V3.4.
    "room_": (96, 54),
    "banner_": (320, 40),
}

# Tool-only files: validated against the zone keys instead of the palette,
# and never cleaned for publishing.
ZONEMAP_NAMES = {"body_zonemap.png"}

BODY_DIR = Path(__file__).resolve().parents[1] / "body"

# The body master's figure edge is drawn in Muted, a one-pixel outline that
# reaches 3:1 against Panel (webclient decomp WC11, W2.3); inner dark details
# such as the eyes stay in Background. Pixels in either colour are left out of
# every zone mask, so tinting a zone in the client never recolours the outline
# or the details (decision B1, Task 2.2; widened to two keys in W2.3).
OUTLINE_KEY = "muted"
DETAIL_KEY = "background"
MASK_EXCLUDED_KEYS = (OUTLINE_KEY, DETAIL_KEY)

# Full pictures (style guide section 5, *Weather icons and pictures*): every
# pixel is painted, so #FF00FF is not their background, and clean would turn
# a stray magenta pixel into a hole (visual pass V3.4).
PICTURE_PREFIXES = ("banner_", "room_")

# The edge checks apply to this master only: it is the one figure the client
# draws on a panel, and its outline is the only thing the masks rely on.
BODY_BASE_NAME = "body_base.png"

# Zone masks are alpha masks for CSS mask-image: only the alpha channel
# matters, the colour is never shown.
MASK_ON = (255, 255, 255, 255)
MASK_OFF = (0, 0, 0, 0)

FILENAME_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*\.png$")

# How many offending pixels to list per colour before summarising.
MAX_COORDS_SHOWN = 3

RGB = tuple[int, int, int]


class PaletteError(Exception):
    """The palette file is missing or malformed (a usage error, exit 2)."""


@dataclass(frozen=True)
class Palette:
    colors: frozenset[RGB]
    chroma_key: RGB
    zone_keys: dict[str, RGB]
    by_key: dict[str, RGB]
    # The surface the body figure is drawn on, and the contrast its edge must
    # reach against it -- both read from palette.json, never restated here.
    edge_surface: RGB
    edge_min_contrast: float


@dataclass
class Report:
    path: Path
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def hex_to_rgb(value: str) -> RGB:
    """'#AABBCC' -> (170, 187, 204). Raises ValueError on anything else."""
    match = re.fullmatch(r"#([0-9A-Fa-f]{6})", value)
    if not match:
        raise ValueError(f"not a #RRGGBB colour: {value!r}")
    digits = match.group(1)
    return (int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16))


def rgb_to_hex(rgb: RGB) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def load_palette(path: Path = PALETTE_PATH) -> Palette:
    """Read palette.json. Tool colours must not collide with motif colours."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        colors = frozenset(hex_to_rgb(c["hex"]) for c in data["colors"])
        chroma = hex_to_rgb(data["chroma_key"])
        zones = {name: hex_to_rgb(h) for name, h in data["zone_keys"].items()}
        by_key = {c["key"]: hex_to_rgb(c["hex"]) for c in data["colors"]}
        edge_surface = hex_to_rgb(data["contrast_surfaces"]["panel"])
        edge_min_contrast = float(data["rules"]["status_min_contrast"])
    except (OSError, ValueError, KeyError, TypeError) as err:
        raise PaletteError(f"cannot read palette {path}: {err}") from err

    tool_colours = {chroma, *zones.values()}
    if tool_colours & colors:
        clash = ", ".join(rgb_to_hex(c) for c in sorted(tool_colours & colors))
        raise PaletteError(f"tool colours overlap motif colours: {clash}")
    if len(set(zones.values())) != len(zones):
        raise PaletteError("two zones share the same key colour")
    for key in MASK_EXCLUDED_KEYS:
        if key not in by_key:
            raise PaletteError(f"palette has no {key!r} colour for outlines")
    return Palette(
        colors=colors, chroma_key=chroma, zone_keys=zones, by_key=by_key,
        edge_surface=edge_surface, edge_min_contrast=edge_min_contrast,
    )


def _linear(channel: int) -> float:
    c = channel / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: RGB) -> float:
    r, g, b = (_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: RGB, b: RGB) -> float:
    """WCAG 2 contrast ratio, the formula palette.json's contrast_* fields use."""
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def expected_size(name: str) -> tuple[int, int] | None:
    for prefix, size in NATIVE_SIZES.items():
        if name.startswith(prefix):
            return size
    return None


def _read_rgb(path: Path, report: Report) -> Image.Image | None:
    """Open the file as RGB, rejecting any pixel that is not fully opaque.

    Masters carry their background as magenta, not as alpha. A semi- or fully
    transparent pixel means the image was exported wrongly (or anti-aliased),
    and converting it to RGB would silently invent a colour.
    """
    try:
        with Image.open(path) as img:
            img.load()
            rgba = img.convert("RGBA")
    except (OSError, UnidentifiedImageError) as err:
        report.errors.append(f"cannot open image: {err}")
        return None

    alpha_min, _alpha_max = rgba.getchannel("A").getextrema()
    if alpha_min < 255:
        report.errors.append(
            "has transparent pixels; masters must be fully opaque with a "
            "#FF00FF background"
        )
        return None
    return rgba.convert("RGB")


def _colours(img: Image.Image) -> set[RGB]:
    """Every distinct colour in an RGB image (maxcolors = pixel count never overflows)."""
    return {rgb for _count, rgb in img.getcolors(maxcolors=img.width * img.height)}


def _colour_errors(img: Image.Image, allowed: set[RGB], what: str) -> list[str]:
    """One error line per disallowed colour, with a few example coordinates."""
    width, height = img.size
    pixels = img.load()
    bad: dict[RGB, list[tuple[int, int]]] = {}
    for y in range(height):
        for x in range(width):
            rgb = pixels[x, y]
            if rgb not in allowed:
                bad.setdefault(rgb, []).append((x, y))

    lines = []
    for rgb, coords in sorted(bad.items(), key=lambda item: -len(item[1])):
        shown = ", ".join(f"({x},{y})" for x, y in coords[:MAX_COORDS_SHOWN])
        more = len(coords) - MAX_COORDS_SHOWN
        tail = f" and {more} more" if more > 0 else ""
        lines.append(f"{rgb_to_hex(rgb)} is not {what}: {len(coords)} px at {shown}{tail}")
    return lines


def validate(path: Path, palette: Palette) -> Report:
    report = Report(path)
    name = path.name

    if not FILENAME_RE.fullmatch(name):
        report.errors.append(
            "file name must be lowercase snake_case ASCII ending in .png"
        )
        return report
    size = expected_size(name)
    if size is None:
        known = ", ".join(NATIVE_SIZES)
        report.errors.append(f"unknown type prefix; expected one of: {known}")
        return report

    img = _read_rgb(path, report)
    if img is None:
        return report

    if img.size != size:
        report.errors.append(
            f"size {img.size[0]}x{img.size[1]}, expected {size[0]}x{size[1]}"
        )
        return report

    if name in ZONEMAP_NAMES:
        allowed = {palette.chroma_key, *palette.zone_keys.values()}
        report.errors += _colour_errors(img, allowed, "a zone key or #FF00FF")
        if not report.errors:
            present = _colours(img)
            for zone, key in palette.zone_keys.items():
                if key not in present:
                    report.errors.append(f"zone {zone} ({rgb_to_hex(key)}) is missing")
    elif name.startswith(PICTURE_PREFIXES):
        allowed = set(palette.colors)
        report.errors += _colour_errors(img, allowed, "in palette v0.2.1 (a picture has no #FF00FF)")
    else:
        allowed = {palette.chroma_key, *palette.colors}
        report.errors += _colour_errors(img, allowed, "in palette v0.2.1")

    if not report.errors and _colours(img) == {palette.chroma_key}:
        report.errors.append("image is empty (only #FF00FF)")
    if not report.errors and name == BODY_BASE_NAME:
        report.errors += _edge_errors(img, palette)
    return report


_N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_N8 = _N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def _touches_background(pixels, size, x, y, key, steps) -> bool:
    """True if a neighbour is the chroma key or lies outside the image.

    Outside the image is background too: the client draws the figure on a
    panel, so a figure pixel on the image border is an edge pixel.
    """
    width, height = size
    for dx, dy in steps:
        nx, ny = x + dx, y + dy
        if not (0 <= nx < width and 0 <= ny < height) or pixels[nx, ny] == key:
            return True
    return False


def _summarise(coords_by_colour: dict[RGB, list[tuple[int, int]]], what: str) -> list[str]:
    lines = []
    for rgb, coords in sorted(coords_by_colour.items(), key=lambda item: -len(item[1])):
        shown = ", ".join(f"({x},{y})" for x, y in coords[:MAX_COORDS_SHOWN])
        more = len(coords) - MAX_COORDS_SHOWN
        tail = f" and {more} more" if more > 0 else ""
        lines.append(f"{rgb_to_hex(rgb)} {what}: {len(coords)} px at {shown}{tail}")
    return lines


def _edge_errors(img: Image.Image, palette: Palette) -> list[str]:
    """The body master's two edge rules (webclient decomp WC11, W2.3).

    1. Every figure pixel that shares a side with the background must reach
       the palette's status contrast against the panel. This is the rule the
       outline exists for; it does not care which colour does the job.
    2. The outline colour may only be the figure's edge (touching the
       background on a side or a corner). Used as an inner fill it would be
       left out of the zone masks without anyone noticing.
    """
    width, height = img.size
    pixels = img.load()
    key = palette.chroma_key
    outline = palette.by_key[OUTLINE_KEY]
    low: dict[RGB, list[tuple[int, int]]] = {}
    inner: dict[RGB, list[tuple[int, int]]] = {}
    for y in range(height):
        for x in range(width):
            rgb = pixels[x, y]
            if rgb == key:
                continue
            if (_touches_background(pixels, img.size, x, y, key, _N4)
                    and contrast_ratio(rgb, palette.edge_surface) < palette.edge_min_contrast):
                low.setdefault(rgb, []).append((x, y))
            if rgb == outline and not _touches_background(pixels, img.size, x, y, key, _N8):
                inner.setdefault(rgb, []).append((x, y))
    threshold = f"{palette.edge_min_contrast:g}:1"
    return (
        _summarise(low, f"on the figure's edge is below {threshold} against "
                        f"{rgb_to_hex(palette.edge_surface)}")
        + _summarise(inner, "is the outline colour but not on the figure's edge")
    )


def clean(path: Path, out_dir: Path, palette: Palette) -> Report:
    """Validate, then write an RGBA copy with the chroma key made transparent.

    Nothing is written unless the master is valid, so a half-broken asset can
    never reach web/static/.
    """
    report = validate(path, palette)
    if not report.ok:
        return report
    if path.name in ZONEMAP_NAMES:
        report.errors.append("zone maps are tool-only and are never published")
        return report

    with Image.open(path) as img:
        rgba = img.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    key = palette.chroma_key
    for y in range(height):
        for x in range(width):
            if pixels[x, y][:3] == key:
                pixels[x, y] = (0, 0, 0, 0)

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        rgba.save(out_dir / path.name, format="PNG", optimize=True)
    except OSError as err:
        report.errors.append(f"cannot write output: {err}")
    return report


def build_body_masks(
    base: Image.Image, zonemap: Image.Image, palette: Palette
) -> tuple[dict[str, Image.Image], list[str]]:
    """Return {zone: RGBA mask} from two valid RGB masters, or the errors.

    The two masters must cover exactly the same pixels; a mismatch means one
    of them was edited without the other, and the masks would no longer line
    up with the figure. Pure function: nothing is written here.
    """
    if base.size != zonemap.size:
        return {}, [f"size mismatch: base {base.size}, zone map {zonemap.size}"]

    width, height = base.size
    bpx, zpx = base.load(), zonemap.load()
    key = palette.chroma_key
    excluded = {palette.by_key[k] for k in MASK_EXCLUDED_KEYS}
    zone_of = {rgb: zone for zone, rgb in palette.zone_keys.items()}

    mismatches = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if (bpx[x, y] == key) != (zpx[x, y] == key)
    ]
    if mismatches:
        shown = ", ".join(f"({x},{y})" for x, y in mismatches[:MAX_COORDS_SHOWN])
        return {}, [
            f"base and zone map cover different pixels: {len(mismatches)} px at {shown}"
        ]

    masks = {zone: Image.new("RGBA", base.size, MASK_OFF) for zone in palette.zone_keys}
    counts = dict.fromkeys(palette.zone_keys, 0)
    for y in range(height):
        for x in range(width):
            zone = zone_of.get(zpx[x, y])
            if zone is not None and bpx[x, y] not in excluded:
                masks[zone].putpixel((x, y), MASK_ON)
                counts[zone] += 1

    empty = [zone for zone, n in counts.items() if n == 0]
    if empty:
        return {}, [f"zone {zone} has no pixels inside the outline" for zone in empty]
    return masks, []


def split_body(base_path: Path, zonemap_path: Path, out_dir: Path, palette: Palette) -> Report:
    """Validate both body masters, then write body_<zone>.png alpha masks.

    All masks are built in memory before the first write, so a validation
    error never leaves a partial set behind.
    """
    report = Report(zonemap_path)
    for path in (base_path, zonemap_path):
        sub = validate(path, palette)
        report.errors += [f"{path.name}: {err}" for err in sub.errors]
    if zonemap_path.name not in ZONEMAP_NAMES:
        report.errors.append(f"{zonemap_path.name} is not a zone map")
    if not report.ok:
        return report

    with Image.open(base_path) as b_img, Image.open(zonemap_path) as z_img:
        masks, errors = build_body_masks(
            b_img.convert("RGB"), z_img.convert("RGB"), palette
        )
    if errors:
        report.errors += errors
        return report

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        for zone, mask in masks.items():
            mask.save(out_dir / f"body_{zone}.png", format="PNG", optimize=True)
    except OSError as err:
        report.errors.append(f"cannot write output: {err}")
    return report


def _print_reports(reports: list[Report], verb: str) -> int:
    failed = 0
    for rep in reports:
        if rep.ok:
            print(f"OK    {rep.path}")
        else:
            failed += 1
            print(f"FAIL  {rep.path}")
            for line in rep.errors:
                print(f"      - {line}")
    print(f"{len(reports) - failed}/{len(reports)} {verb}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p_val = sub.add_parser("validate", help="check masters against the style guide")
    p_val.add_argument("files", nargs="+", type=Path)
    p_cln = sub.add_parser("clean", help="validate, then write transparent copies")
    p_cln.add_argument("files", nargs="+", type=Path)
    p_cln.add_argument("--out", type=Path, required=True, help="output directory")
    p_spl = sub.add_parser("split-body", help="write the seven zone alpha masks")
    p_spl.add_argument("--base", type=Path, default=BODY_DIR / "body_base.png")
    p_spl.add_argument("--zonemap", type=Path, default=BODY_DIR / "body_zonemap.png")
    p_spl.add_argument("--out", type=Path, required=True, help="output directory")
    for p in (p_val, p_cln, p_spl):
        p.add_argument("--palette", type=Path, default=PALETTE_PATH)
    args = parser.parse_args(argv)

    try:
        palette = load_palette(args.palette)
    except PaletteError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    if args.command == "validate":
        return _print_reports([validate(f, palette) for f in args.files], "valid")
    if args.command == "clean":
        return _print_reports([clean(f, args.out, palette) for f in args.files], "cleaned")
    report = split_body(args.base, args.zonemap, args.out, palette)
    return _print_reports([report], "split")


if __name__ == "__main__":
    sys.exit(main())
