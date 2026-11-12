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
 *   icons       (visual pass V3.3) a weather or season gets no icon or
 *               another's, the night icon shows outside the period night
 *               or not in it (lock 1), an unknown key gets an icon name
 *               (lock 5), the tables drift from the server's words, or an
 *               icon is not set, not cleared indoors, or rewritten every
 *               second.
 */
"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const FILE = path.join(__dirname, "..", "..", "web", "static", "polishedworld", "js", "pw_world.js");
const TABLE = JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures", "world_cases.json"), "utf8"));
const {
    worldView, gameSecondsAt, showWeather, weatherIcon, seasonIcon,
    WEATHER_KEYS, SEASON_KEYS, NIGHT_PERIODS,
} = require(FILE);

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
        const got = TABLE.cases.map((c) => {
            const v = worldView(c.seconds, CAL);
            return { date: v.date, time: v.time, season: v.season };
        });
        const want = TABLE.cases.map((c) => ({ date: c.date, time: c.time, season: c.season }));
        assert.deepEqual(got, want);
    });

    it("names the period that time prints in brackets", () => {
        const got = TABLE.cases.map((c) => worldView(c.seconds, CAL).period);
        const want = TABLE.cases.map((c) => /\((\w+)\)$/.exec(c.time)[1]);
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
    const el = { id: id, hidden: true, writes: 0, style: {}, attrs: {}, attrWrites: 0 };
    el.setAttribute = (name, value) => {
        el.attrWrites += 1;
        el.attrs[name] = String(value);
    };
    el.removeAttribute = (name) => {
        el.attrWrites += 1;
        delete el.attrs[name];
    };
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

function iconsOf(elements) {
    const out = {};
    for (const key of ["season", "weather"]) {
        const attrs = elements["pw-world-" + key].attrs;
        out[key] = Object.prototype.hasOwnProperty.call(attrs, "data-icon") ? attrs["data-icon"] : null;
    }
    return out;
}

const at = (h, m) => h * 3600 + m * 60;

describe("icons", () => {
    it("keeps the server's words", () => {
        // Literals, as the DOMAINS lists in test_pw_state.js and
        // tests/test_client_state.py; tests/test_webclient_theme.py
        // TestWorldIcons reads the same tables from pw_world.js and
        // compares them with the server.
        assert.deepEqual(
            [WEATHER_KEYS, SEASON_KEYS, NIGHT_PERIODS],
            [["clear", "raining", "snowing", "foggy"], ["spring", "summer", "autumn", "winter"], ["night"]]
        );
    });

    it("names a day and a night icon for every weather", () => {
        const got = WEATHER_KEYS.map((w) => [weatherIcon(w, "day"), weatherIcon(w, "night")]);
        assert.deepEqual(got, [
            ["weather_day_clear", "weather_night_clear"],
            ["weather_day_raining", "weather_night_raining"],
            ["weather_day_snowing", "weather_night_snowing"],
            ["weather_day_foggy", "weather_night_foggy"],
        ]);
    });

    it("is night in the period night and in no other (lock 1)", () => {
        const got = CAL.times_of_day.map((span) => [span[0], weatherIcon("clear", span[0])]);
        assert.deepEqual(got, CAL.times_of_day.map((span) => [
            span[0], span[0] === "night" ? "weather_night_clear" : "weather_day_clear",
        ]));
    });

    it("turns at 20:00 and at 04:00", () => {
        const icon = (s) => weatherIcon("foggy", worldView(s, CAL).period);
        assert.deepEqual(
            [icon(at(3, 59)), icon(at(4, 0)), icon(at(19, 59)), icon(at(20, 0))],
            ["weather_night_foggy", "weather_day_foggy", "weather_day_foggy", "weather_night_foggy"]
        );
    });

    it("names an icon for every season", () => {
        assert.deepEqual(SEASON_KEYS.map(seasonIcon),
            ["season_spring", "season_summer", "season_autumn", "season_winter"]);
    });

    it("names nothing for a key it does not know (lock 5)", () => {
        assert.deepEqual(
            [weatherIcon("cloudy", "day"), weatherIcon("undefined", "night"), weatherIcon("", "day"),
             seasonIcon("monsoon"), seasonIcon("")],
            [null, null, null, null, null]
        );
    });
});

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

    it("sets the season and weather icons on a frame", () => {
        const { elements, renderer } = load(IDS);
        renderer("room")(room(), null);
        renderer("world")(world(), null);
        assert.deepEqual(iconsOf(elements), { season: "season_spring", weather: "weather_day_raining" });
    });

    it("turns the weather icon to night on the timer at 20:00", () => {
        const { elements, timers, clock, renderer } = load(IDS);
        renderer("room")(room(), null);
        renderer("world")(world({ game_seconds: 604800 + at(19, 59) + 50 }), null);
        assert.equal(iconsOf(elements).weather, "weather_day_raining");
        clock.now = 3000;   // twelve game seconds later: 20:00:02
        timers[0][0]();
        assert.equal(iconsOf(elements).weather, "weather_night_raining");
    });

    it("clears the weather icon indoors and sets it again outdoors", () => {
        const { elements, renderer } = load(IDS);
        renderer("room")(room(), null);
        renderer("world")(world(), null);
        renderer("room")(room({ indoor: true }), null);
        assert.deepEqual(iconsOf(elements), { season: "season_spring", weather: null });
        renderer("room")(room(), null);
        assert.equal(iconsOf(elements).weather, "weather_day_raining");
    });

    it("sets no icon for a weather it does not know, and keeps the word", () => {
        const { elements, renderer } = load(IDS);
        renderer("room")(room(), null);
        renderer("world")(world(), null);
        renderer("world")(world({ weather: "cloudy" }), null);
        assert.deepEqual([iconsOf(elements).weather, values(elements).weather], [null, "cloudy"]);
    });

    it("does not rewrite an icon that has not changed", () => {
        const { elements, timers, clock, renderer } = load(IDS);
        renderer("room")(room(), null);
        renderer("world")(world(), null);
        clock.now = 1000;
        timers[0][0]();
        timers[0][0]();
        for (const key of ["season", "weather"]) {
            assert.equal(elements["pw-world-" + key].attrWrites, 1, key);
        }
    });

    it("registers nothing and starts no timer on a page without the panel", () => {
        const { registrations, timers } = load([]);
        assert.deepEqual([registrations, timers], [[], []]);
    });
});
