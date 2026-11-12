/*
 * Tests for web/static/polishedworld/js/pw_room.js, the location panel
 * (webclient decomposition W5.4). Run from the repo root:
 *     node --test tests/js/test_pw_room.js
 * Not part of `evennia test`. Each describe() names the bug it pressures:
 *   items     a list shows something look does not list, in another order,
 *             or the panel keeps the last room's lists after `name: null`.
 *   writer    no renderer on room, a second renderer, markup written instead
 *             of text, a row left visible when its list is empty, or an
 *             unchanged list rebuilt on every frame.
 *   picture   (visual pass V3.4) the location picture is not the one
 *             `indoor` asks for, stays after the room goes away, or is
 *             rewritten on every frame.
 *   exits     a click sends anything but the exit's key, sends it twice, or
 *             follows the "#" link; Enter or Space on a link reaches
 *             default_in, which would send an empty command or move the focus
 *             (decomp §3 key claims).
 */
"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const FILE = path.join(__dirname, "..", "..", "web", "static", "polishedworld", "js", "pw_room.js");
const { listItems, pictureName } = require(FILE);

// The ids the renderer writes. A literal list (W-z); the same list is in
// tests/test_webclient_template.py ROOM_IDS for the page's side.
const IDS = [
    "pw-room",
    "pw-room-name",
    "pw-room-exits",
    "pw-room-exits-list",
    "pw-room-characters",
    "pw-room-characters-list",
    "pw-room-things",
    "pw-room-things-list",
];

function room(overrides) {
    return Object.assign(
        {
            name: "Temple Clearing", indoor: false,
            exits: [{ name: "north", key: "north" }, { name: "old temple", key: "old temple" }],
            characters: ["tester"],
            things: ["a rabbit", "two stones", "stone statue of TestChar"],
        },
        overrides || {}
    );
}

describe("items", () => {
    it("lists each list in the snapshot's order, exits with their keys", () => {
        assert.deepEqual(
            ["exits", "characters", "things"].map((list) => listItems(room(), list)),
            [
                [{ text: "north", key: "north" }, { text: "old temple", key: "old temple" }],
                [{ text: "tester", key: null }],
                [{ text: "a rabbit", key: null }, { text: "two stones", key: null },
                 { text: "stone statue of TestChar", key: null }],
            ]
        );
    });

    it("lists nothing without a room or before the first frame", () => {
        const empty = { name: null, indoor: false, exits: [], characters: [], things: [] };
        assert.deepEqual(
            [listItems(empty, "exits"), listItems(room({ name: null }), "things"), listItems(null, "characters")],
            [[], [], []]
        );
    });
});

// ------------------------------------------------------------------ writer

function fakeElement(tag, id) {
    const el = {
        tagName: tag, id: id || null, hidden: true, writes: 0, children: [],
        listeners: {}, rebuilds: 0, className: "", href: null, attrs: {}, attrWrites: 0,
    };
    el.setAttribute = (name, value) => { el.attrWrites += 1; el.attrs[name] = String(value); };
    el.removeAttribute = (name) => { el.attrWrites += 1; delete el.attrs[name]; };
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
    el.addEventListener = (type, fn) => { (el.listeners[type] = el.listeners[type] || []).push(fn); };
    return el;
}

function load(ids) {
    const elements = {};
    for (const id of ids) {
        elements[id] = fakeElement("x", id);
    }
    const registrations = [];
    const sent = [];
    const sandbox = vm.createContext({
        pw_state: { on(domain, fn) { registrations.push([domain, fn]); } },
        Evennia: { msg(cmd, args, kwargs) { sent.push([cmd, args, kwargs]); } },
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
    const render = (snapshot) => registrations.find((r) => r[0] === "room")[1](snapshot, null);
    return { registrations, elements, sent, render };
}

function shown(elements) {
    const out = { name: elements["pw-room-name"].hidden ? null : elements["pw-room-name"].textContent };
    for (const list of ["exits", "characters", "things"]) {
        const row = elements["pw-room-" + list];
        out[list] = row.hidden ? null : elements["pw-room-" + list + "-list"].children.map(
            (li) => (li.children.length ? li.children[0].textContent : li.textContent)
        );
    }
    return out;
}

describe("writer", () => {
    it("registers one renderer, for room", () => {
        const { registrations } = load(IDS);
        assert.deepEqual(registrations.map((r) => r[0]), ["room"]);
        assert.equal(typeof registrations[0][1], "function");
    });

    it("writes the name and the three lists", () => {
        const { elements, render } = load(IDS);
        render(room());
        assert.deepEqual(shown(elements), {
            name: "Temple Clearing",
            exits: ["north", "old temple"],
            characters: ["tester"],
            things: ["a rabbit", "two stones", "stone statue of TestChar"],
        });
    });

    it("hides a row whose list is empty", () => {
        const { elements, render } = load(IDS);
        render(room());
        render(room({ characters: [] }));
        assert.equal(shown(elements).characters, null);
    });

    it("clears everything when the room goes away", () => {
        const { elements, render } = load(IDS);
        render(room());
        render({ name: null, indoor: false, exits: [], characters: [], things: [] });
        assert.deepEqual(shown(elements), { name: null, exits: null, characters: null, things: null });
    });

    it("does not rebuild a list or rewrite the name when nothing changed", () => {
        const { elements, render } = load(IDS);
        render(room());
        render(room({ characters: ["tester", "warden"] }));
        assert.deepEqual(
            [elements["pw-room-name"].writes, elements["pw-room-exits-list"].rebuilds,
             elements["pw-room-characters-list"].rebuilds, elements["pw-room-things-list"].rebuilds],
            [1, 1, 2, 1]
        );
    });

    it("writes names with markup as text", () => {
        const { elements, render } = load(IDS);
        render(room({ name: "<b>x</b>", things: ["<i>y</i>"] }));
        assert.deepEqual([shown(elements).name, shown(elements).things], ["<b>x</b>", ["<i>y</i>"]]);
    });

    it("registers nothing on a page without the panel", () => {
        assert.deepEqual(load([]).registrations, []);
    });
});

// ---------------------------------------------------------------- picture

function picture(elements) {
    const attrs = elements["pw-room-name"].attrs;
    return Object.prototype.hasOwnProperty.call(attrs, "data-picture") ? attrs["data-picture"] : null;
}

describe("picture", () => {
    it("names the picture by indoor, and none without a room (lock 6)", () => {
        assert.deepEqual(
            [pictureName(room({ indoor: true })), pictureName(room()), pictureName(room({ name: null })),
             pictureName(null)],
            ["room_indoor", "room_outdoor", null, null]
        );
    });

    it("sets the picture on the name and turns it with indoor", () => {
        const { elements, render } = load(IDS);
        render(room());
        assert.equal(picture(elements), "room_outdoor");
        render(room({ name: "Old Temple", indoor: true }));
        assert.equal(picture(elements), "room_indoor");
    });

    it("clears the picture when the room goes away", () => {
        const { elements, render } = load(IDS);
        render(room({ indoor: true }));
        render({ name: null, indoor: false, exits: [], characters: [], things: [] });
        assert.equal(picture(elements), null);
    });

    it("does not rewrite the picture when it has not changed", () => {
        const { elements, render } = load(IDS);
        render(room());
        render(room({ name: "Meadow" }));
        assert.equal(elements["pw-room-name"].attrWrites, 1);
    });
});

// ------------------------------------------------------------------ exits

function exitLink(elements, n) {
    return elements["pw-room-exits-list"].children[n].children[0];
}

function fire(el, type, event) {
    for (const fn of el.listeners[type] || []) {
        fn(event);
    }
}

function event(key) {
    const e = { key: key, prevented: 0, stopped: 0 };
    e.preventDefault = () => { e.prevented += 1; };
    e.stopPropagation = () => { e.stopped += 1; };
    return e;
}

describe("exits", () => {
    it("is a real link that sends the exit's key as a command once", () => {
        const { elements, sent, render } = load(IDS);
        render(room({ exits: [{ name: "old temple(#120)", key: "old temple" }] }));
        const link = exitLink(elements, 0);
        const click = event();
        fire(link, "click", click);
        assert.deepEqual(
            [link.tagName, link.href, link.textContent, JSON.stringify(sent), click.prevented],
            ["a", "#", "old temple(#120)", JSON.stringify([["text", ["old temple"], {}]]), 1]
        );
    });

    it("stops Enter and Space at the link and lets other keys pass", () => {
        const { elements, sent, render } = load(IDS);
        render(room());
        const link = exitLink(elements, 0);
        const keys = ["Enter", " ", "a", "Escape"].map((k) => {
            const e = event(k);
            fire(link, "keydown", e);
            return e.stopped;
        });
        assert.deepEqual([keys, sent.length], [[1, 1, 0, 0], 0]);
    });

    it("leaves characters and things as plain list entries", () => {
        const { elements, render } = load(IDS);
        render(room());
        const entries = ["characters", "things"].map((list) =>
            elements["pw-room-" + list + "-list"].children.map((li) => [li.tagName, li.children.length]));
        assert.deepEqual(entries, [[["li", 0]], [["li", 0], ["li", 0], ["li", 0]]]);
    });
});
