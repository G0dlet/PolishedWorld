"""
Tasks 2.1, 2.2 and W2.3: the asset pipeline's validate, clean and split-body
steps, and the body master's edge rules.

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
* TestPictures -- a banner or location picture is a full rectangle (style
  guide section 5): #FF00FF in it fails, since clean would turn it into a
  hole (visual pass V3.4).
* TestColours -- the palette match is exact: one channel off by one is a
  failure, and zone keys are not allowed outside the zone map.
* TestTransparency -- masters carry magenta, not alpha; a converted RGBA must
  not hide a half-transparent edge.
* TestZoneMap -- the zone map allows only zone keys and needs all seven.
* TestClean -- only valid masters are written; magenta becomes fully
  transparent and every other pixel keeps its exact colour.
* TestSplitBody -- the seven masks are pure alpha, disjoint, leave the
  outline and the inner details out, and nothing is written when the
  masters disagree.
* TestContrast -- the contrast formula reproduces every contrast_panel
  figure in palette.json, so the edge rule measures what the palette says.
* TestBodyEdge -- the figure's edge reaches the palette's contrast against
  Panel (side neighbours only, the image border counts as background, the
  threshold comes from the palette), the outline colour is never an inner
  fill, and only body_base.png is held to either rule.
* TestRealMasters -- the committed body masters pass.
* TestPublishedUpToDate -- the files committed under web/static/ are what
  the pipeline produces today, so a master edited without re-running the
  pipeline is caught; for the cleaned families (FAMILIES: the webclient's
  icons since visual pass V3.2, its frames since V3.1, its weather and
  season icons since V3.3, its banners and location pictures since V3.4)
  also every master is valid, and a published file without a master, or a
  master never published, fails.
* TestCli -- exit codes 0/1/2 as documented.
"""

from __future__ import annotations

import dataclasses
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
OUTLINE = (0x9D, 0x9B, 0x8C)  # palette "muted", the figure's edge (W2.3)
DETAIL = (0x0E, 0x15, 0x12)  # palette "background", inner dark details
DARK_WOOD = (0x4B, 0x30, 0x26)  # 1.35:1 against Panel
# The prefixes of full pictures, which carry no magenta (visual pass V3.4).
PICTURES = ("banner_", "room_")
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
                fill = DETAIL if prefix in PICTURES else MAGENTA
                good = self.make(f"{prefix}x.png", size=size, fill=fill, pixels={(1, 1): SKIN})
                self.assertEqual(self.errors(good), [])
                wrong = (size[0] * 2, size[1])
                bad = self.make(f"{prefix}y.png", size=wrong, fill=fill, pixels={(1, 1): SKIN})
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
        # 96x54 since visual pass V3.4 (V2.2 lock 1A): the size the Location
        # panel shows at x1.
        path = self.make("room_test.png", size=(96, 54), fill=DETAIL)
        self.assertEqual(self.errors(path), [])


class TestPictures(_TmpCase):
    def test_magenta_in_a_picture_fails(self):
        for name, size in (("banner_x.png", (320, 40)), ("room_x.png", (96, 54))):
            with self.subTest(name=name):
                path = self.make(name, size=size, fill=DETAIL, pixels={(3, 4): MAGENTA})
                errs = self.errors(path)
                self.assertEqual(len(errs), 1, errs)
                self.assertIn("#FF00FF", errs[0])
                self.assertIn("(3,4)", errs[0])

    def test_an_icon_keeps_magenta_as_its_background(self):
        path = self.make("weather_day_x.png", pixels={(5, 5): SKIN})
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
        errs = self.errors(self.zonemap(ZONE_KEYS + [DETAIL]))
        self.assertIn("#0E1512 is not a zone key", errs[0])


class TestClean(_TmpCase):
    def test_magenta_becomes_transparent_rest_is_exact(self):
        src = self.make("icon_x.png", pixels={(5, 5): SKIN, (6, 5): DETAIL})
        out = self.dir / "out" / "deeper"
        report = assetpipe.clean(src, out, self.palette)
        self.assertTrue(report.ok, report.errors)
        with Image.open(out / "icon_x.png") as img:
            self.assertEqual(img.mode, "RGBA")
            self.assertEqual(img.getpixel((5, 5)), SKIN + (255,))
            self.assertEqual(img.getpixel((6, 5)), DETAIL + (255,))
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
    """A 32x64 figure: a 3x3 head at x=4-6, y=1-3, and x=9 is every other zone.

    The head has the outline colour on its left edge at (4, 2) and an inner
    detail in Background at its centre (5, 2), which touches no background, so
    the fixture passes the edge rules and both exclusions are exercised.
    """

    HEAD = [(x, y) for y in range(1, 4) for x in range(4, 7)]

    def masters(self, base_px=None, zone_px=None):
        zones = list(self.palette.zone_keys.items())
        zmap = {xy: zones[0][1] for xy in self.HEAD}
        zmap.update({(9, 1 + i): rgb for i, (_z, rgb) in enumerate(zones[1:])})
        bmap = {xy: SKIN for xy in zmap}
        bmap[(4, 2)] = OUTLINE  # the edge, inside the head zone
        bmap[(5, 2)] = DETAIL  # an eye: inner, never tinted
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
            self.assertEqual(head.getpixel((5, 1)), assetpipe.MASK_ON)
            self.assertEqual(head.getpixel((4, 2)), assetpipe.MASK_OFF, "outline")
            self.assertEqual(head.getpixel((5, 2)), assetpipe.MASK_OFF, "inner detail")
        on = []
        for path in out.iterdir():
            with Image.open(path) as img:
                on += [(x, y) for y in range(64) for x in range(32)
                       if img.getpixel((x, y))[3]]
        self.assertEqual(len(on), len(set(on)))
        self.assertEqual(len(on), 7 + 6)

    def test_coverage_mismatch_writes_nothing(self):
        base, zonemap = self.masters(base_px={(20, 20): SKIN})
        report, out = self.split(base, zonemap)
        self.assertIn("cover different pixels", report.errors[0])
        self.assertIn("(20,20)", report.errors[0])
        self.assertFalse(out.exists())

    def test_zone_that_is_all_outline(self):
        base, zonemap = self.masters(base_px={(9, 1): OUTLINE})
        report, out = self.split(base, zonemap)
        self.assertEqual(report.errors, ["zone chest has no pixels inside the outline"])
        self.assertFalse(out.exists())

    def test_invalid_master_is_named(self):
        base, zonemap = self.masters(base_px={(5, 1): (1, 2, 3)})
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


class TestContrast(_TmpCase):
    def test_formula_reproduces_the_palette_figures(self):
        data = json.loads(assetpipe.PALETTE_PATH.read_text(encoding="utf-8"))
        panel = assetpipe.hex_to_rgb(data["contrast_surfaces"]["panel"])
        for colour in data["colors"]:
            with self.subTest(key=colour["key"]):
                ratio = assetpipe.contrast_ratio(assetpipe.hex_to_rgb(colour["hex"]), panel)
                self.assertEqual(round(ratio, 2), colour["contrast_panel"])

    def test_threshold_and_surface_come_from_the_palette(self):
        self.assertEqual(self.palette.edge_surface, (0x17, 0x23, 0x1F))
        self.assertEqual(self.palette.edge_min_contrast, 3.0)


class TestBodyEdge(_TmpCase):
    """A 4x4 block at x=10-13, y=10-13 on the 32x64 body canvas."""

    BLOCK = [(x, y) for y in range(10, 14) for x in range(10, 14)]

    def base(self, extra=None, name="body_base.png", size=(32, 64), fill=SKIN):
        px = {xy: fill for xy in self.BLOCK}
        px.update(extra or {})
        return self.make(name, size=size, pixels=px)

    def test_bright_edge_passes(self):
        self.assertEqual(self.errors(self.base()), [])

    def test_dark_pixel_on_a_side_edge_fails(self):
        errs = self.errors(self.base({(10, 11): DARK_WOOD}))
        self.assertEqual(len(errs), 1)
        self.assertIn("#4B3026 on the figure's edge is below 3:1 against #17231F", errs[0])
        self.assertIn("(10,11)", errs[0])

    def test_dark_pixel_inside_passes(self):
        self.assertEqual(self.errors(self.base({(11, 11): DARK_WOOD})), [])

    def test_corner_contact_alone_is_not_an_edge(self):
        # A notch at (10, 10) gives (11, 11) one background neighbour, on a
        # corner only. An outline drawn in steps has many such pixels, and
        # they are not where the figure's edge is seen.
        path = self.base({(10, 10): MAGENTA, (11, 11): DARK_WOOD})
        self.assertEqual(self.errors(path), [])

    def test_image_border_counts_as_background(self):
        # (0, 30) has figure on its other three sides: the image border is
        # its only background contact.
        px = {(x, y): SKIN for x in range(3) for y in range(28, 33)}
        px[(0, 30)] = DARK_WOOD
        path = self.make("body_base.png", size=(32, 64), pixels=px)
        errs = self.errors(path)
        self.assertEqual(len(errs), 1)
        self.assertIn("(0,30)", errs[0])

    def test_outline_colour_as_inner_fill_fails(self):
        errs = self.errors(self.base({(11, 11): OUTLINE}))
        self.assertEqual(len(errs), 1)
        self.assertIn("#9D9B8C is the outline colour but not on the figure's edge", errs[0])

    def test_outline_colour_touching_background_on_a_corner_passes(self):
        path = self.base({(10, 10): MAGENTA, (11, 11): OUTLINE})
        self.assertEqual(self.errors(path), [])

    def test_threshold_is_the_palettes(self):
        path = self.base({(10, 11): DARK_WOOD})
        lenient = dataclasses.replace(self.palette, edge_min_contrast=1.0)
        self.assertEqual(assetpipe.validate(path, lenient).errors, [])
        strict = dataclasses.replace(self.palette, edge_min_contrast=10.0)
        self.assertTrue(assetpipe.validate(self.base(), strict).errors)

    def test_only_the_body_base_is_held_to_the_edge_rules(self):
        icon = self.make("icon_x.png", pixels={(5, 5): DARK_WOOD, (6, 5): OUTLINE})
        self.assertEqual(self.errors(icon), [])
        zone_mask_name = self.base({(10, 11): DARK_WOOD}, name="body_head.png")
        self.assertEqual(self.errors(zone_mask_name), [])


class TestRealMasters(unittest.TestCase):
    def test_committed_body_masters_are_valid(self):
        palette = assetpipe.load_palette()
        for name in ("body_base.png", "body_zonemap.png"):
            with self.subTest(name=name):
                report = assetpipe.validate(REPO / "art" / "body" / name, palette)
                self.assertEqual(report.errors, [])


class TestPublishedUpToDate(_TmpCase):
    PUBLISHED = REPO / "web" / "static" / "polishedworld" / "characters" / "body"
    # The families published by `clean` alone: master folder -> published
    # folder. The body is not here; it also needs split-body (above).
    FAMILIES = {
        "icons": (REPO / "art" / "ui" / "icons",
                  REPO / "web" / "static" / "polishedworld" / "ui" / "icons"),
        "frames": (REPO / "art" / "ui" / "frames",
                   REPO / "web" / "static" / "polishedworld" / "ui" / "frames"),
        "world": (REPO / "art" / "ui" / "world",
                  REPO / "web" / "static" / "polishedworld" / "ui" / "world"),
        "pictures": (REPO / "art" / "ui" / "pictures",
                     REPO / "web" / "static" / "polishedworld" / "ui" / "pictures"),
    }

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

    def test_published_families_match_their_masters(self):
        for family, (masters, published) in self.FAMILIES.items():
            with self.subTest(family=family):
                fresh = self.dir / family
                names = sorted(p.name for p in masters.glob("*.png"))
                self.assertTrue(names, f"no masters in {masters}")
                for name in names:
                    report = assetpipe.clean(masters / name, fresh, self.palette)
                    self.assertTrue(report.ok, f"{family}/{name}: {report.errors}")
                self.assertEqual(sorted(p.name for p in published.iterdir()), names)
                for name in names:
                    self.assert_same_pixels(published / name, fresh / name)


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
