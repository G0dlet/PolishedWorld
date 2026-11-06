"""
PolishedWorld asset pipeline: validate and clean pixel art masters.

Offline tooling. Nothing in the game server imports this module, and Pillow
is listed in ``art/tools/requirements.txt`` only. The rules enforced here are
the ones in ``docs/PolishedWorld_Art_Style_Guide.md`` (sections 3-5); the
palette is read from ``art/palette/palette.json``, never duplicated here.

Usage (from the repository root)::

    python art/tools/assetpipe.py validate art/body/*.png
    python art/tools/assetpipe.py clean art/body/body_base.png --out web/static/polishedworld/characters/body

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
    "room_": (320, 180),
    "banner_": (320, 40),
}

# Tool-only files: validated against the zone keys instead of the palette,
# and never cleaned for publishing.
ZONEMAP_NAMES = {"body_zonemap.png"}

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
    except (OSError, ValueError, KeyError, TypeError) as err:
        raise PaletteError(f"cannot read palette {path}: {err}") from err

    tool_colours = {chroma, *zones.values()}
    if tool_colours & colors:
        clash = ", ".join(rgb_to_hex(c) for c in sorted(tool_colours & colors))
        raise PaletteError(f"tool colours overlap motif colours: {clash}")
    if len(set(zones.values())) != len(zones):
        raise PaletteError("two zones share the same key colour")
    return Palette(colors=colors, chroma_key=chroma, zone_keys=zones)


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
    else:
        allowed = {palette.chroma_key, *palette.colors}
        report.errors += _colour_errors(img, allowed, "in palette v0.2.1")

    if not report.errors and _colours(img) == {palette.chroma_key}:
        report.errors.append("image is empty (only #FF00FF)")
    return report


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
    p_val.add_argument("--palette", type=Path, default=PALETTE_PATH)
    p_cln.add_argument("--palette", type=Path, default=PALETTE_PATH)
    args = parser.parse_args(argv)

    try:
        palette = load_palette(args.palette)
    except PaletteError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    if args.command == "validate":
        return _print_reports([validate(f, palette) for f in args.files], "valid")
    return _print_reports([clean(f, args.out, palette) for f in args.files], "cleaned")


if __name__ == "__main__":
    sys.exit(main())
