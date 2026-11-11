/*
 * Tests for web/static/polishedworld/js/pw_inventory.js, the inventory
 * panel (webclient decomposition W7.1). Run from the repo root:
 *     node --test tests/js/test_pw_inventory.js
 * Not part of `evennia test`. Each describe() names the bug it pressures:
 *   items     a list shows something the snapshot does not hold, in another
 *             order, or an unknown inventory (no frame yet, or a char frame
 *             without the field) is taken for an empty one.
 *   writer    no renderer on char, a second renderer, markup written instead
 *             of text, an empty list shown as nothing instead of "Nothing."
 *             (lock 6), rows left visible without an inventory, or an
 *             unchanged list rebuilt on every char frame -- and char frames
 *             come for health too, not only for the inventory.
 */
"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const FILE = path.join(__dirname, "..", "..", "web", "static", "polishedworld", "js", "pw_inventory.js");
const { listItems } = require(FILE);

// The ids the renderer writes. A literal list (W-z); the same list is in
// tests/test_webclient_template.py INVENTORY_IDS for the page's side.
const IDS = [
    "pw-inventory",
    "pw-inventory-carried",
    "pw-inventory-carried-list",
    "pw-inventory-worn",
    "pw-inventory-worn-list",
];

function char(inventory) {
    const snapshot = {
        name: "Char",
        health: { current: 12, max: 12, desc: "unhurt" },
        encumbrance: { carried: 3, limit: 20, band: "free" },
    };
    if (inventory !== undefined) {
        snapshot.inventory = inventory;
    }
    return snapshot;
}

const FULL = { carried: ["a pebble", "two ropes"], worn: ["a shirt"] };

describe("items", () => {
    it("lists each list in the snapshot's order", () => {
        assert.deepEqual(
            [listItems(char(FULL), "carried"), listItems(char(FULL), "worn")],
            [["a pebble", "two ropes"], ["a shirt"]]
        );
    });

    it("knows nothing without a frame or without the field, and an empty list is known", () => {
        assert.deepEqual(
            [listItems(null, "carried"), listItems(char(), "worn"),
             listItems(char({ carried: [], worn: [] }), "worn")],
            [null, null, []]
        );
    });
});

// ------------------------------------------------------------------ writer

function fakeElement(tag, id) {
    const el = {
        tagName: tag, id: id || null, hidden: true, writes: 0, children: [],
        rebuilds: 0, className: "",
    };
    let text = "";
    Object.defineProperty(el, "textContent", {
        get() { return text; },
        set(value) { el.writes += 1; text = String(value); },
    });
    for (const sink of ["innerHTML", "outerHTML"]) {
        Object.defineProperty(el, sink, {
            set() { throw new Error(sink + " written on " + (id || tag)); },
        });
    }
    el.insertAdjacentHTML = () => { throw new Error("insertAdjacentHTML on " + (id || tag)); };
    el.appendChild = (child) => { el.children.push(child); return child; };
    el.replaceChildren = (...kids) => { el.rebuilds += 1; el.children = kids; };
    return el;
}

function load(ids) {
    const elements = {};
    for (const id of ids) {
        elements[id] = fakeElement("x", id);
    }
    const registrations = [];
    const sandbox = vm.createContext({
        pw_state: { on(domain, fn) { registrations.push([domain, fn]); } },
        document: {
            readyState: "interactive",
            getElementById(id) {
                return Object.prototype.hasOwnProperty.call(elements, id) ? elements[id] : null;
            },
            createElement(tag) { return fakeElement(tag); },
            addEventListener() { throw new Error("readyState is interactive; nothing to wait for"); },
        },
        console: console,
    });
    vm.runInContext(fs.readFileSync(FILE, "utf8"), sandbox, { filename: FILE });
    const render = (snapshot) => registrations.find((r) => r[0] === "char")[1](snapshot, null);
    return { registrations, elements, render };
}

function shown(elements) {
    const out = {};
    for (const list of ["carried", "worn"]) {
        out[list] = elements["pw-inventory-" + list].hidden
            ? null
            : elements["pw-inventory-" + list + "-list"].children.map((li) => li.textContent);
    }
    return out;
}

describe("writer", () => {
    it("registers one renderer, for char", () => {
        const { registrations } = load(IDS);
        assert.deepEqual(registrations.map((r) => r[0]), ["char"]);
        assert.equal(typeof registrations[0][1], "function");
    });

    it("writes both lists", () => {
        const { elements, render } = load(IDS);
        render(char(FULL));
        assert.deepEqual(shown(elements), { carried: ["a pebble", "two ropes"], worn: ["a shirt"] });
    });

    it("says Nothing. for an empty list, marked as the empty entry", () => {
        const { elements, render } = load(IDS);
        render(char({ carried: [], worn: ["a shirt"] }));
        const only = elements["pw-inventory-carried-list"].children;
        assert.deepEqual(
            [shown(elements), only.map((li) => li.className)],
            [{ carried: ["Nothing."], worn: ["a shirt"] }, ["pw-inventory-empty"]]
        );
    });

    it("hides both rows again when a char frame has no inventory", () => {
        const { elements, render } = load(IDS);
        render(char(FULL));
        const before = shown(elements);
        render(char());
        assert.deepEqual([before.worn, shown(elements)], [["a shirt"], { carried: null, worn: null }]);
    });

    it("does not rebuild a list when nothing in it changed", () => {
        const { elements, render } = load(IDS);
        render(char(FULL));
        render(char({ carried: ["a pebble", "two ropes"], worn: [] }));
        render(char({ carried: ["a pebble", "two ropes"], worn: [] }));
        assert.deepEqual(
            [elements["pw-inventory-carried-list"].rebuilds, elements["pw-inventory-worn-list"].rebuilds],
            [1, 2]
        );
    });

    it("writes names with markup as text", () => {
        const { elements, render } = load(IDS);
        render(char({ carried: ["<b>x</b>"], worn: [] }));
        assert.deepEqual(shown(elements).carried, ["<b>x</b>"]);
    });

    it("registers nothing on a page without the panel", () => {
        // The same load registers one with the panel (W-o).
        assert.deepEqual([load(IDS).registrations.length, load([]).registrations.length], [1, 0]);
    });
});
