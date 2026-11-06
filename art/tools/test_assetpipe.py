"""
Tasks 2.1 and 2.2: the asset pipeline's validate, clean and split-body steps.

Run from the repository root (outside `evennia test`, which never sees art/):

    python -m unittest discover -s art/tools -v

Every test builds its images in a temporary directory, except TestRealMasters,
which runs the committed masters through the same rules. Each class pressures
one way the pipeline can let a broken asset through:

* TestPaletteFile -- the palette is read from palette.json, and tool colours
  that collide with motif colours are refused before any image is checked.
* TestNaming -- names follow the style guide; the prefix decides the size, so a
  wrong prefix must fail instead of falling back to some default.
* TestSize -- every prefix enforces its own native size.
* TestColours -- the palette match is exact: one channel off by one is a
  failure, and zone keys are not allowed outside the zone map.
* TestTransparency -- masters carry magenta, not alpha; a converted RGBA must
  not hide a half-transparent edge.
* TestZoneMap -- the zone map allows only zone keys and needs all seven.
* TestClean -- only valid masters are written; magenta becomes fully
  transparent and every other pixel keeps its exact colour.
* TestSplitBody -- the seven masks are pure alpha, disjoint, leave the
  outline out, and nothing is written when the masters disagree.
* TestRealMasters -- the committed body masters pass.
* TestPublishedUpToDate -- the files committed under web/static/ are what
  the pipeline produces today, so a master edited without re-running the
  pipeline is caught.
* TestCli -- exit codes 0/1/2 as documented.
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import assetpipe  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
MAGENTA = (255, 0, 255)
OUTLINE = (0x0E, 0x15, 0x12)  # palette "background", used as outline
SKIN = (0xE7, 0xB9, 0x8A)
ZONE_KEYS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
    (0, 255, 255), (255, 128, 0), (128, 0, 255),
]


class _TmpCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.palette = assetpipe.load_palette()

    def tearDown(self):
        self._tmp.cleanup()

    def make(self, name, size=(32, 32), fill=MAGENTA, pixels=None, mode="RGB"):
        """Write a PNG: background `fill`, then {(x, y): colour} on top."""
        img = Image.new(mode, size, fill)
        for (x, y), colour in (pixels or {}).items():
            img.putpixel((x, y), colour)
        path = self.dir / name
        img.save(path)
        return path

    def errors(self, path):
        return assetpipe.validate(path, self.palette).errors


class TestPaletteFile(_TmpCase):
    def test_real_palette_has_27_colours(self):
        self.assertEqual(len(self.palette.colors), 27)
        self.assertEqual(self.palette.chroma_key, MAGENTA)
        self.assertEqual(len(self.palette.zone_keys), 7)

    def test_tool_colour_clash_is_refused(self):
        data = json.loads(assetpipe.PALETTE_PATH.read_text(encoding="utf-8"))
        data["zone_keys"]["head"] = data["colors"][0]["hex"]
        bad = self.dir / "palette.json"
        bad.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(assetpipe.PaletteError):
            assetpipe.load_palette(bad)

    def test_missing_palette_is_a_palette_error(self):
        with self.assertRaises(assetpipe.PaletteError):
            assetpipe.load_palette(self.dir / "nope.json")


class TestNaming(_TmpCase):
    def test_unknown_prefix(self):
        path = self.make("sprite_sword.png", pixels={(5, 5): SKIN})
        self.assertIn("unknown type prefix", self.errors(path)[0])

    def test_uppercase_and_spaces(self):
        for name in ("Icon_sword.png", "icon sword.png", "icon__sword.png"):
            with self.subTest(name=name):
                path = self.make(name, pixels={(5, 5): SKIN})
                self.assertIn("snake_case", self.errors(path)[0])

    def test_weather_night_is_not_shadowed(self):
        path = self.make("weather_night_rain.png", pixels={(5, 5): SKIN})
        self.assertEqual(self.errors(path), [])


class TestSize(_TmpCase):
    def test_each_prefix_enforces_its_native_size(self):
        for prefix, size in assetpipe.NATIVE_SIZES.items():
            with self.subTest(prefix=prefix):
                good = self.make(f"{prefix}x.png", size=size, pixels={(1, 1): SKIN})
                self.assertEqual(self.errors(good), [])
                wrong = (size[0] * 2, size[1])
                bad = self.make(f"{prefix}y.png", size=wrong, pixels={(1, 1): SKIN})
                self.assertIn("expected", self.errors(bad)[0])


class TestColours(_TmpCase):
    def test_off_by_one_is_not_in_palette(self):
        near = (SKIN[0] - 1, SKIN[1], SKIN[2])
        path = self.make("icon_x.png", pixels={(3, 4): near, (5, 5): SKIN})
        errs = self.errors(path)
        self.assertEqual(len(errs), 1)
        self.assertIn("#E6B98A", errs[0])
        self.assertIn("(3,4)", errs[0])

    def test_zone_key_outside_zone_map(self):
        path = self.make("body_base.png", size=(32, 64), pixels={(1, 1): ZONE_KEYS[0]})
        self.assertIn("#FF0000 is not in palette", self.errors(path)[0])

    def test_many_bad_pixels_are_summarised(self):
        img = {(x, 0): (1, 2, 3) for x in range(10)}
        path = self.make("icon_x.png", pixels={**img, (5, 5): SKIN})
        self.assertIn("10 px", self.errors(path)[0])
        self.assertIn("and 7 more", self.errors(path)[0])

    def test_empty_image(self):
        path = self.make("icon_x.png")
        self.assertIn("empty", self.errors(path)[0])

    def test_full_bleed_without_magenta_is_fine(self):
        path = self.make("room_test.png", size=(320, 180), fill=OUTLINE)
        self.assertEqual(self.errors(path), [])


class TestTransparency(_TmpCase):
    def test_opaque_rgba_is_accepted(self):
        path = self.make("icon_x.png", fill=MAGENTA + (255,), mode="RGBA",
                         pixels={(5, 5): SKIN + (255,)})
        self.assertEqual(self.errors(path), [])

    def test_half_transparent_edge_is_rejected(self):
        path = self.make("icon_x.png", fill=MAGENTA + (255,), mode="RGBA",
                         pixels={(5, 5): SKIN + (128,)})
        self.assertIn("transparent", self.errors(path)[0])

    def test_not_an_image(self):
        path = self.dir / "icon_x.png"
        path.write_text("hello", encoding="utf-8")
        self.assertIn("cannot open", self.errors(path)[0])


class TestZoneMap(_TmpCase):
    def zonemap(self, keys):
        return self.make("body_zonemap.png", size=(32, 64),
                         pixels={(i, 0): k for i, k in enumerate(keys)})

    def test_all_seven_zones(self):
        self.assertEqual(self.errors(self.zonemap(ZONE_KEYS)), [])

    def test_missing_zone(self):
        errs = self.errors(self.zonemap(ZONE_KEYS[:-1]))
        self.assertEqual(errs, ["zone left_leg (#8000FF) is missing"])

    def test_palette_colour_in_zone_map(self):
        errs = self.errors(self.zonemap(ZONE_KEYS + [OUTLINE]))
        self.assertIn("#0E1512 is not a zone key", errs[0])


class TestClean(_TmpCase):
    def test_magenta_becomes_transparent_rest_is_exact(self):
        src = self.make("icon_x.png", pixels={(5, 5): SKIN, (6, 5): OUTLINE})
        out = self.dir / "out" / "deeper"
        report = assetpipe.clean(src, out, self.palette)
        self.assertTrue(report.ok, report.errors)
        with Image.open(out / "icon_x.png") as img:
            self.assertEqual(img.mode, "RGBA")
            self.assertEqual(img.getpixel((5, 5)), SKIN + (255,))
            self.assertEqual(img.getpixel((6, 5)), OUTLINE + (255,))
            self.assertEqual(img.getpixel((0, 0)), (0, 0, 0, 0))
            alphas = {v for _count, v in img.getchannel("A").getcolors()}
            self.assertEqual(alphas, {0, 255})

    def test_invalid_master_writes_nothing(self):
        src = self.make("icon_x.png", pixels={(5, 5): (1, 2, 3)})
        out = self.dir / "out"
        report = assetpipe.clean(src, out, self.palette)
        self.assertFalse(report.ok)
        self.assertFalse((out / "icon_x.png").exists())

    def test_zone_map_is_never_published(self):
        src = self.make("body_zonemap.png", size=(32, 64),
                        pixels={(i, 0): k for i, k in enumerate(ZONE_KEYS)})
        out = self.dir / "out"
        report = assetpipe.clean(src, out, self.palette)
        self.assertIn("tool-only", report.errors[0])
        self.assertFalse((out / "body_zonemap.png").exists())


class TestSplitBody(_TmpCase):
    """A 32x64 figure: column x=5 is head (rows 0-2), x=6 is every other zone."""

    def masters(self, base_px=None, zone_px=None):
        zones = list(self.palette.zone_keys.items())
        zmap = {(5, y): zones[0][1] for y in range(3)}
        zmap.update({(6, i): rgb for i, (_z, rgb) in enumerate(zones[1:])})
        bmap = {xy: SKIN for xy in zmap}
        bmap[(5, 1)] = OUTLINE  # an outline pixel inside the head zone
        bmap.update(base_px or {})
        zmap.update(zone_px or {})
        base = self.make("body_base.png", size=(32, 64), pixels=bmap)
        zonemap = self.make("body_zonemap.png", size=(32, 64), pixels=zmap)
        return base, zonemap

    def split(self, base, zonemap):
        out = self.dir / "out"
        return assetpipe.split_body(base, zonemap, out, self.palette), out

    def test_seven_pure_alpha_masks(self):
        report, out = self.split(*self.masters())
        self.assertTrue(report.ok, report.errors)
        names = sorted(p.name for p in out.iterdir())
        self.assertEqual(names, sorted(f"body_{z}.png" for z in self.palette.zone_keys))
        for path in out.iterdir():
            with Image.open(path) as img:
                self.assertEqual((img.mode, img.size), ("RGBA", (32, 64)))
                values = {rgba for _n, rgba in img.getcolors()}
                self.assertEqual(values, {assetpipe.MASK_ON, assetpipe.MASK_OFF})

    def test_outline_is_left_out_and_masks_are_disjoint(self):
        report, out = self.split(*self.masters())
        self.assertTrue(report.ok, report.errors)
        with Image.open(out / "body_head.png") as head:
            self.assertEqual(head.getpixel((5, 0)), assetpipe.MASK_ON)
            self.assertEqual(head.getpixel((5, 1)), assetpipe.MASK_OFF)
        on = []
        for path in out.iterdir():
            with Image.open(path) as img:
                on += [(x, y) for y in range(64) for x in range(32)
                       if img.getpixel((x, y))[3]]
        self.assertEqual(len(on), len(set(on)))
        self.assertEqual(len(on), 2 + 6)

    def test_coverage_mismatch_writes_nothing(self):
        base, zonemap = self.masters(base_px={(20, 20): SKIN})
        report, out = self.split(base, zonemap)
        self.assertIn("cover different pixels", report.errors[0])
        self.assertIn("(20,20)", report.errors[0])
        self.assertFalse(out.exists())

    def test_zone_that_is_all_outline(self):
        base, zonemap = self.masters(base_px={(6, 0): OUTLINE})
        report, out = self.split(base, zonemap)
        self.assertEqual(report.errors, ["zone chest has no pixels inside the outline"])
        self.assertFalse(out.exists())

    def test_invalid_master_is_named(self):
        base, zonemap = self.masters(base_px={(5, 0): (1, 2, 3)})
        report, out = self.split(base, zonemap)
        self.assertTrue(report.errors[0].startswith("body_base.png: #010203"))
        self.assertFalse(out.exists())

    def test_size_mismatch(self):
        base = self.make("body_base.png", size=(32, 64), pixels={(1, 1): SKIN})
        small = Image.new("RGB", (16, 16), MAGENTA)
        masks, errors = assetpipe.build_body_masks(
            Image.open(base).convert("RGB"), small, self.palette)
        self.assertEqual(masks, {})
        self.assertIn("size mismatch", errors[0])

    def test_base_passed_as_zone_map_is_refused(self):
        base, _zonemap = self.masters()
        report, _out = self.split(base, base)
        self.assertIn("body_base.png is not a zone map", report.errors)


class TestRealMasters(unittest.TestCase):
    def test_committed_body_masters_are_valid(self):
        palette = assetpipe.load_palette()
        for name in ("body_base.png", "body_zonemap.png"):
            with self.subTest(name=name):
                report = assetpipe.validate(REPO / "art" / "body" / name, palette)
                self.assertEqual(report.errors, [])


class TestPublishedUpToDate(_TmpCase):
    PUBLISHED = REPO / "web" / "static" / "polishedworld" / "characters" / "body"

    def assert_same_pixels(self, committed, fresh):
        with Image.open(committed) as a, Image.open(fresh) as b:
            self.assertEqual(a.size, b.size, committed.name)
            self.assertEqual(
                a.convert("RGBA").tobytes(), b.convert("RGBA").tobytes(),
                f"{committed.name} is stale: re-run the pipeline (see assetpipe.py)")

    def test_published_body_files_match_the_masters(self):
        fresh = self.dir / "fresh"
        self.assertTrue(assetpipe.clean(REPO / "art/body/body_base.png", fresh, self.palette).ok)
        self.assertTrue(assetpipe.split_body(REPO / "art/body/body_base.png",
                                             REPO / "art/body/body_zonemap.png",
                                             fresh, self.palette).ok)
        names = sorted(p.name for p in fresh.iterdir())
        self.assertEqual(names, sorted(p.name for p in self.PUBLISHED.iterdir()))
        for name in names:
            with self.subTest(name=name):
                self.assert_same_pixels(self.PUBLISHED / name, fresh / name)


class TestCli(_TmpCase):
    def run_cli(self, *argv):
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            code = assetpipe.main(list(argv))
        return code, out.getvalue()

    def test_exit_codes(self):
        good = self.make("icon_good.png", pixels={(5, 5): SKIN})
        bad = self.make("icon_bad.png", pixels={(5, 5): (1, 2, 3)})
        self.assertEqual(self.run_cli("validate", str(good))[0], 0)
        code, text = self.run_cli("validate", str(good), str(bad))
        self.assertEqual(code, 1)
        self.assertIn("1/2 valid", text)
        missing = self.dir / "nope.json"
        self.assertEqual(self.run_cli("validate", str(good), "--palette", str(missing))[0], 2)

    def test_split_body_exit_codes(self):
        out = self.dir / "out"
        code, text = self.run_cli("split-body", "--out", str(out))
        self.assertEqual(code, 0, text)
        self.assertEqual(len(list(out.iterdir())), 7)
        bad = self.make("body_zonemap.png", size=(32, 64), pixels={(0, 0): (1, 2, 3)})
        self.assertEqual(self.run_cli("split-body", "--zonemap", str(bad), "--out", str(out))[0], 1)


if __name__ == "__main__":
    unittest.main()
