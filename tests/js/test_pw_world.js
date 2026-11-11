/*
 * Tests for web/static/polishedworld/js/pw_world.js, the world panel
 * (webclient decomposition W5.3). Run from the repo root with Node 20 or
 * later:
 *     node --test tests/js/test_pw_world.js
 * Not part of `evennia test`. Each describe() names the bug it pressures:
 *   parity      the browser's date, time or season differs from what `time`
 *               prints at the same game second. The cases are the committed
 *               table tests/js/fixtures/world_cases.json, which
 *               tests/test_time_command.py checks against the server.
 *   clock       the clock does not advance at time_factor, counts from the
 *               server's wall clock instead of the frame's arrival (lock 2B),
 *               or a new frame does not restart the count.
 *   weather     the weather shows indoors, before any room is known, or
 *               stays hidden outdoors (lock 4A).
 *   writer      a renderer is missing for world or room, more than one timer
 *               runs per page (lock 5), an unchanged line is rewritten every
 *               second, or markup is written instead of text.
 */
"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const FILE = path.join(__dirname, "..", "..", "web", "static", "polishedworld", "js", "pw_world.js");
const TABLE = JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures", "world_cases.json"), "utf8"));
const { worldView, gameSecondsAt, showWeather } = require(FILE);

// The ids the renderer writes. A literal list (W-z); the same list is in
// tests/test_webclient_template.py WORLD_IDS for the page's side.
const IDS = [
    "pw-world",
    "pw-world-date",
    "pw-world-date-value",
    "pw-world-time",
    "pw-world-time-value",
    "pw-world-season",
    "pw-world-season-value",
    "pw-world-weather",
    "pw-world-weather-value",
];

const CAL = TABLE.calendar;

function world(overrides) {
    return Object.assign(
        // Frostmelt 8, 10:52:17 (tests/test_time_command.py PINNED)
        { game_seconds: 604800 + 10 * 3600 + 52 * 60 + 17, time_factor: 4,
          server_ms: 1, weather: "raining", calendar: CAL },
        overrides || {}
    );
}

function room(overrides) {
    return Object.assign(
        { name: "A clearing", indoor: false, exits: [], characters: [], things: [] },
        overrides || {}
    );
}

describe("parity", () => {
    it("has the table's sixteen cases", () => {
        // A literal (W-z), as in tests/test_time_command.py.
        assert.equal(TABLE.cases.length, 16);
    });

    it("says what time prints at every case", () => {
        const got = TABLE.cases.map((c) => worldView(c.seconds, CAL));
        const want = TABLE.cases.map((c) => ({ date: c.date, time: c.time, season: c.season }));
        assert.deepEqual(got, want);
    });
});

describe("clock", () => {
    it("advances time_factor game seconds per real second from the frame's arrival", () => {
        assert.equal(gameSecondsAt(world(), 1000, 1000), 604800 + 39137);
        assert.equal(gameSecondsAt(world(), 1000, 16000), 604800 + 39137 + 60);
    });

    it("ignores the server's wall clock", () => {
        const a = gameSecondsAt(world({ server_ms: 1 }), 500, 3000);
        const b = gameSecondsAt(world({ server_ms: 9e12 }), 500, 3000);
        assert.deepEqual([a, b], [604800 + 39137 + 10, 604800 + 39137 + 10]);
    });

    it("rolls the minute after fifteen real seconds", () => {
        const at = (ms) => worldView(gameSecondsAt(world(), 0, ms), CAL).time;
        assert.deepEqual([at(10000), at(11000)], ["10:52 (day)", "10:53 (day)"]);
    });
});

describe("weather", () => {
    it("shows outdoors", () => {
        assert.equal(showWeather(room()), true);
    });

    it("hides indoors, without a room, and before any room frame", () => {
        assert.deepEqual(
            [showWeather(room({ indoor: true })), showWeather(room({ name: null })), showWeather(null)],
            [false, false, false]
        );
    });
});

// ------------------------------------------------------------------ writer

function fakeElement(id) {
    const el = { id: id, hidden: true, writes: 0, style: {} };
    let text = "";
    Object.defineProperty(el, "textContent", {
        get() { return text; },
        set(value) { el.writes += 1; text = String(value); },
    });
    for (const sink of ["innerHTML", "outerHTML"]) {
        Object.defineProperty(el, sink, {
            set() {
                throw new Error(sink + " written on #" + id);
            },
        });
    }
    el.insertAdjacentHTML = () => {
        throw new Error("insertAdjacentHTML on #" + id);
    };
    return el;
}

// Runs the browser build of pw_world.js in a sandbox with a fake pw_state,
// document, clock and timer.
function load(ids) {
    const elements = {};
    for (const id of ids) {
        elements[id] = fakeElement(id);
    }
    const registrations = [];
    const timers = [];
    const clock = { now: 0 };
    const sandbox = vm.createContext({
        pw_state: {
            on(domain, fn) {
                registrations.push([domain, fn]);
            },
        },
        document: {
            readyState: "interactive",
            getElementById(id) {
                return Object.prototype.hasOwnProperty.call(elements, id) ? elements[id] : null;
            },
            addEventListener() {
                throw new Error("readyState is interactive; nothing to wait for");
            },
        },
        performance: { now: () => clock.now },
        setInterval(fn, ms) {
            timers.push([fn, ms]);
            return timers.length;
        },
        console: console,
    });
    vm.runInContext(fs.readFileSync(FILE, "utf8"), sandbox, { filename: FILE });
    const renderer = (domain) => registrations.find((r) => r[0] === domain)[1];
    return { registrations, timers, elements, clock, renderer };
}

function values(elements) {
    const out = {};
    for (const key of ["date", "time", "season", "weather"]) {
        const row = elements["pw-world-" + key];
        out[key] = row.hidden ? null : elements["pw-world-" + key + "-value"].textContent;
    }
    return out;
}

describe("writer", () => {
    it("registers one renderer for world and one for room", () => {
        const { registrations } = load(IDS);
        assert.deepEqual(registrations.map((r) => r[0]).sort(), ["room", "world"]);
        assert.ok(registrations.every((r) => typeof r[1] === "function"));
    });

    it("starts one timer per page, at one second", () => {
        const { timers, renderer } = load(IDS);
        renderer("world")(world(), null);
        renderer("world")(world({ game_seconds: 1 }), null);
        renderer("room")(room(), null);
        assert.deepEqual(timers.map((t) => t[1]), [1000]);
    });

    it("writes the date, time, season and outdoor weather on a frame", () => {
        const { elements, renderer } = load(IDS);
        renderer("room")(room(), null);
        renderer("world")(world(), null);
        assert.deepEqual(values(elements), {
            date: "Year 1, Frostmelt 8", time: "10:52 (day)", season: "spring", weather: "raining",
        });
    });

    it("shows nothing before the first world frame", () => {
        const { elements, timers } = load(IDS);
        timers[0][0]();
        assert.deepEqual(values(elements), { date: null, time: null, season: null, weather: null });
    });

    it("advances on the timer from the frame's arrival", () => {
        const { elements, timers, clock, renderer } = load(IDS);
        // Arrival late enough that counting from page load (0) would show
        // 10:55, not 10:53.
        clock.now = 30000;
        renderer("world")(world(), null);
        clock.now = 30000 + 11000;
        timers[0][0]();
        assert.equal(values(elements).time, "10:53 (day)");
    });

    it("hides the weather when the room goes indoors and shows it again", () => {
        const { elements, renderer } = load(IDS);
        renderer("world")(world(), null);
        renderer("room")(room({ indoor: true }), null);
        assert.equal(values(elements).weather, null);
        renderer("room")(room(), null);
        assert.equal(values(elements).weather, "raining");
    });

    it("does not rewrite a line that has not changed", () => {
        const { elements, timers, clock, renderer } = load(IDS);
        renderer("room")(room(), null);
        renderer("world")(world(), null);
        clock.now = 1000;
        timers[0][0]();
        timers[0][0]();
        for (const key of ["date", "time", "season", "weather"]) {
            assert.equal(elements["pw-world-" + key + "-value"].writes, 1, key);
        }
    });

    it("writes a weather word with markup as text", () => {
        const { elements, renderer } = load(IDS);
        renderer("room")(room(), null);
        renderer("world")(world({ weather: "<b>x</b>" }), null);
        assert.equal(elements["pw-world-weather-value"].textContent, "<b>x</b>");
    });

    it("registers nothing and starts no timer on a page without the panel", () => {
        const { registrations, timers } = load([]);
        assert.deepEqual([registrations, timers], [[], []]);
    });
});
