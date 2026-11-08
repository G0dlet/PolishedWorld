/*
 * Tests for web/static/polishedworld/js/pw_char.js, the character panel
 * (webclient decomposition W5.1). Run from the repo root with Node 20 or
 * later:
 *     node --test tests/js/test_pw_char.js
 * Not part of `evennia test`. Each describe() names the bug it pressures:
 *   view       the panel's words differ from what `status` prints (the
 *              numbers, health's own description), or the figure's alt
 *              does not say the character's state in words (WC14).
 *   no health  a character without a health trait (snapshot health null)
 *              throws, or shows numbers it does not have.
 *   bar        the bar shows full before health is full, runs past its
 *              track, or turns NaN/Infinity on a zero max.
 *   band       the encumbrance line differs from `inventory`'s: free gets a
 *              suffix, or ceiling is not called overloaded (inventory says
 *              overloaded for both, inventory_commands.py:63-64).
 *   writer     the renderer is not registered for "char", writes into the
 *              wrong element, writes markup instead of text, or a health
 *              row hidden once never shows again.
 */
"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const FILE = path.join(__dirname, "..", "..", "web", "static", "polishedworld", "js", "pw_char.js");
const { charView } = require(FILE);

// The ids the renderer writes. A literal list (W-z); the same list is in
// tests/test_webclient_template.py CHAR_IDS for the page's side.
const IDS = [
    "pw-char",
    "pw-char-name",
    "pw-char-figure",
    "pw-char-health",
    "pw-char-health-numbers",
    "pw-char-health-desc",
    "pw-char-health-bar",
    "pw-char-enc",
];

function snapshot(overrides) {
    return Object.assign(
        {
            name: "Tester",
            health: { current: 17, max: 20, desc: "wounded" },
            encumbrance: { carried: 12, limit: 20, band: "free" },
        },
        overrides || {}
    );
}

function gauge(current, max) {
    return { current: current, max: max, desc: "x" };
}

describe("view", () => {
    it("says the numbers and the description as status does", () => {
        const view = charView(snapshot());
        assert.equal(view.name, "Tester");
        assert.equal(view.health.numbers, "17/20");
        assert.equal(view.health.desc, "wounded");
    });

    it("puts the name and the state in the alt", () => {
        assert.equal(charView(snapshot()).alt, "Tester, wounded");
    });
});

describe("no health", () => {
    it("has no health row and an alt of the name alone", () => {
        const view = charView(snapshot({ health: null }));
        assert.equal(view.health, null);
        assert.equal(view.alt, "Tester");
    });
});

describe("bar", () => {
    it("is full only at full health", () => {
        assert.equal(charView(snapshot({ health: gauge(199, 200) })).health.bar, "99%");
        assert.equal(charView(snapshot({ health: gauge(20, 20) })).health.bar, "100%");
    });

    it("stays inside its track", () => {
        assert.equal(charView(snapshot({ health: gauge(25, 20) })).health.bar, "100%");
        assert.equal(charView(snapshot({ health: gauge(-3, 20) })).health.bar, "0%");
    });

    it("is empty, not NaN or Infinity, on a zero max", () => {
        assert.equal(charView(snapshot({ health: gauge(0, 0) })).health.bar, "0%");
        assert.equal(charView(snapshot({ health: gauge(5, 0) })).health.bar, "0%");
    });
});

describe("band", () => {
    const cases = [
        ["free", "Carrying 12/20 ENC"],
        ["overloaded", "Carrying 12/20 ENC (overloaded)"],
        ["ceiling", "Carrying 12/20 ENC (overloaded)"],
    ];
    for (const [band, line] of cases) {
        it(band + " reads as inventory prints it", () => {
            const enc = { carried: 12, limit: 20, band: band };
            assert.equal(charView(snapshot({ encumbrance: enc })).encumbrance, line);
        });
    }
});

// ------------------------------------------------------------------ writer

function fakeElement(id) {
    const el = {
        id: id,
        textContent: "",
        hidden: false,
        style: {},
        attrs: {},
        setAttribute(name, value) {
            this.attrs[name] = String(value);
        },
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

// Runs the browser build in a sandbox with a fake pw_state and document,
// as test_pw_state.js does for its registration. Returns the captured
// registrations and the elements.
function load(ids) {
    const elements = {};
    for (const id of ids) {
        elements[id] = fakeElement(id);
    }
    const registrations = [];
    const sandbox = {
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
    };
    vm.runInNewContext(fs.readFileSync(FILE, "utf8"), sandbox, { filename: FILE });
    return { registrations, elements };
}

describe("writer", () => {
    it("registers one renderer, for char", () => {
        const { registrations } = load(IDS);
        assert.deepEqual(registrations.map((r) => r[0]), ["char"]);
        assert.equal(typeof registrations[0][1], "function");
    });

    it("writes each part into its element", () => {
        const { registrations, elements } = load(IDS);
        registrations[0][1](snapshot({ encumbrance: { carried: 30, limit: 20, band: "overloaded" } }), null);
        assert.equal(elements["pw-char-name"].textContent, "Tester");
        assert.equal(elements["pw-char-figure"].attrs.alt, "Tester, wounded");
        assert.equal(elements["pw-char-health"].hidden, false);
        assert.equal(elements["pw-char-health-numbers"].textContent, "17/20");
        assert.equal(elements["pw-char-health-desc"].textContent, "wounded");
        assert.equal(elements["pw-char-health-bar"].style.width, "85%");
        assert.equal(elements["pw-char-enc"].textContent, "Carrying 30/20 ENC (overloaded)");
    });

    it("writes a name with markup as text", () => {
        const { registrations, elements } = load(IDS);
        registrations[0][1](snapshot({ name: "<b>Bold</b>" }), null);
        assert.equal(elements["pw-char-name"].textContent, "<b>Bold</b>");
    });

    it("hides the health row without health and shows it again", () => {
        const { registrations, elements } = load(IDS);
        const render = registrations[0][1];
        render(snapshot({ health: null }), null);
        assert.equal(elements["pw-char-health"].hidden, true);
        assert.equal(elements["pw-char-figure"].attrs.alt, "Tester");
        render(snapshot(), null);
        assert.equal(elements["pw-char-health"].hidden, false);
    });

    it("registers nothing on a page without the panel", () => {
        const { registrations } = load([]);
        assert.deepEqual(registrations, []);
    });
});
