/*
 * Tests for web/static/polishedworld/js/pw_survival.js, the survival panel
 * (webclient decomposition W5.2). Run from the repo root with Node 20 or
 * later:
 *     node --test tests/js/test_pw_survival.js
 * Not part of `evennia test`. Each describe() names the bug it pressures:
 *   view        a gauge's words differ from what `status` prints (the
 *               numbers, the gauge's own description), or one gauge's
 *               values land under another's name.
 *   missing     a character without one of the traits (snapshot value null,
 *               or the key absent) throws, or shows numbers it does not have.
 *   direction   the fatigue bar is drawn inverted: the server's gauge counts
 *               energy (100 energetic, 0 exhausted), as hunger and thirst do.
 *   writer      the renderer is not registered for "survival", writes into
 *               the wrong element, writes markup instead of text, or a row
 *               hidden once never shows again.
 */
"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const JS = path.join(__dirname, "..", "..", "web", "static", "polishedworld", "js");
const FILE = path.join(JS, "pw_survival.js");
const GAUGE_FILE = path.join(JS, "pw_gauge.js");
const { survivalView } = require(FILE);

// The ids the renderer writes. A literal list (W-z); the same list is in
// tests/test_webclient_template.py SURVIVAL_IDS for the page's side.
const IDS = [
    "pw-survival",
    "pw-survival-hunger",
    "pw-survival-hunger-numbers",
    "pw-survival-hunger-desc",
    "pw-survival-hunger-bar",
    "pw-survival-thirst",
    "pw-survival-thirst-numbers",
    "pw-survival-thirst-desc",
    "pw-survival-thirst-bar",
    "pw-survival-fatigue",
    "pw-survival-fatigue-numbers",
    "pw-survival-fatigue-desc",
    "pw-survival-fatigue-bar",
];

function snapshot(overrides) {
    return Object.assign(
        {
            hunger: { current: 45, max: 100, desc: "hungry" },
            thirst: { current: 12, max: 100, desc: "dying of thirst" },
            fatigue: { current: 81, max: 100, desc: "rested" },
        },
        overrides || {}
    );
}

describe("view", () => {
    it("says each gauge's numbers and description as status does", () => {
        const view = survivalView(snapshot());
        assert.deepEqual(
            ["hunger", "thirst", "fatigue"].map((k) => [view[k].numbers, view[k].desc]),
            [["45/100", "hungry"], ["12/100", "dying of thirst"], ["81/100", "rested"]]
        );
    });

    it("draws each bar from its own gauge", () => {
        const view = survivalView(snapshot());
        assert.deepEqual(
            [view.hunger.bar, view.thirst.bar, view.fatigue.bar],
            ["45%", "12%", "81%"]
        );
    });
});

describe("missing", () => {
    it("has no row for a null gauge and keeps the others", () => {
        const view = survivalView(snapshot({ thirst: null }));
        assert.equal(view.thirst, null);
        assert.equal(view.hunger.numbers, "45/100");
        assert.equal(view.fatigue.numbers, "81/100");
    });

    it("has no row for a gauge the snapshot lacks", () => {
        const snap = snapshot();
        delete snap.fatigue;
        assert.equal(survivalView(snap).fatigue, null);
    });
});

describe("direction", () => {
    it("draws fatigue full when rested and empty when exhausted", () => {
        const full = survivalView(snapshot({ fatigue: { current: 100, max: 100, desc: "energetic" } }));
        const empty = survivalView(snapshot({ fatigue: { current: 0, max: 100, desc: "exhausted" } }));
        assert.equal(full.fatigue.bar, "100%");
        assert.equal(empty.fatigue.bar, "0%");
    });
});

// ------------------------------------------------------------------ writer

function fakeElement(id) {
    const el = {
        id: id,
        textContent: "",
        hidden: false,
        style: {},
    };
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

// Runs the browser builds of pw_gauge.js and then pw_survival.js in one
// sandbox, in the page's script order, with a fake pw_state and document.
function load(ids) {
    const elements = {};
    for (const id of ids) {
        elements[id] = fakeElement(id);
    }
    const registrations = [];
    const sandbox = vm.createContext({
        pw_state: {
            on(domain, fn) {
                registrations.push([domain, fn]);
            },
        },
        document: {
            readyState: "complete",
            getElementById(id) {
                return Object.prototype.hasOwnProperty.call(elements, id) ? elements[id] : null;
            },
            addEventListener() {
                throw new Error("readyState is complete; nothing to wait for");
            },
        },
        console: console,
    });
    for (const file of [GAUGE_FILE, FILE]) {
        vm.runInContext(fs.readFileSync(file, "utf8"), sandbox, { filename: file });
    }
    return { registrations, elements };
}

describe("writer", () => {
    it("registers one renderer, for survival", () => {
        const { registrations } = load(IDS);
        assert.deepEqual(registrations.map((r) => r[0]), ["survival"]);
        assert.equal(typeof registrations[0][1], "function");
    });

    it("writes each gauge into its own elements", () => {
        const { registrations, elements } = load(IDS);
        registrations[0][1](snapshot(), null);
        const got = {};
        for (const key of ["hunger", "thirst", "fatigue"]) {
            const id = "pw-survival-" + key;
            got[key] = [
                elements[id].hidden,
                elements[id + "-numbers"].textContent,
                elements[id + "-desc"].textContent,
                elements[id + "-bar"].style.width,
            ];
        }
        assert.deepEqual(got, {
            hunger: [false, "45/100", "hungry", "45%"],
            thirst: [false, "12/100", "dying of thirst", "12%"],
            fatigue: [false, "81/100", "rested", "81%"],
        });
    });

    it("writes a description with markup as text", () => {
        const { registrations, elements } = load(IDS);
        registrations[0][1](snapshot({ hunger: { current: 1, max: 100, desc: "<b>x</b>" } }), null);
        assert.equal(elements["pw-survival-hunger-desc"].textContent, "<b>x</b>");
    });

    it("hides a row without its gauge and shows it again", () => {
        const { registrations, elements } = load(IDS);
        const render = registrations[0][1];
        render(snapshot({ thirst: null }), null);
        assert.equal(elements["pw-survival-thirst"].hidden, true);
        assert.equal(elements["pw-survival-hunger"].hidden, false);
        render(snapshot(), null);
        assert.equal(elements["pw-survival-thirst"].hidden, false);
    });

    it("registers nothing on a page without the panel", () => {
        const { registrations } = load([]);
        assert.deepEqual(registrations, []);
    });
});
