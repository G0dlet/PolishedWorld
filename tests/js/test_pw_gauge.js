/*
 * Tests for web/static/polishedworld/js/pw_gauge.js, the one bar rule every
 * panel uses (webclient decomposition W5.2, lock 2B). Run from the repo root
 * with Node 20 or later:
 *     node --test tests/js/test_pw_gauge.js
 * Not part of `evennia test`. Each describe() names the bug it pressures:
 *   floor     the bar shows full before the gauge is full (rounding up).
 *   clamp     the bar runs past its track, or below empty.
 *   zero max  the width turns NaN% or Infinity% on a max of 0.
 *   browser   the browser build does not leave pw_gauge as a global, so
 *             the panel scripts loaded after it cannot find it.
 */
"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const FILE = path.join(__dirname, "..", "..", "web", "static", "polishedworld", "js", "pw_gauge.js");
const { barWidth } = require(FILE);

describe("floor", () => {
    it("is full only at full", () => {
        assert.equal(barWidth(199, 200), "99%");
        assert.equal(barWidth(200, 200), "100%");
    });

    it("rounds every partial width down", () => {
        assert.equal(barWidth(1, 3), "33%");
        assert.equal(barWidth(2, 3), "66%");
    });
});

describe("clamp", () => {
    it("stays inside its track", () => {
        assert.equal(barWidth(25, 20), "100%");
        assert.equal(barWidth(-3, 20), "0%");
    });
});

describe("zero max", () => {
    it("is empty, not NaN or Infinity", () => {
        assert.equal(barWidth(0, 0), "0%");
        assert.equal(barWidth(5, 0), "0%");
    });
});

describe("browser", () => {
    it("leaves pw_gauge as a global with barWidth", () => {
        const sandbox = {};
        vm.runInNewContext(fs.readFileSync(FILE, "utf8"), sandbox, { filename: FILE });
        assert.equal(typeof sandbox.pw_gauge, "object");
        assert.equal(sandbox.pw_gauge.barWidth(1, 2), "50%");
    });
});
