/*
 * Tests for web/static/polishedworld/js/pw_text.js, the text-routing plugin
 * (webclient decomposition W5.4, WC4, lock 5C; W6.1, WC14). Run from the
 * repo root:
 *     node --test tests/js/test_pw_text.js
 * Not part of `evennia test`. Each describe() names the bug it pressures:
 *   rule      room_contents is hidden while the room panel is not shown, or
 *             while the player keeps room lists in the text (WC14), or any
 *             other message type is ever hidden.
 *   plugin    the plugin is not registered, claims a text it should leave to
 *             default_out, or hides room_contents before init has read the
 *             layout and the toggle.
 *   storage   the stored toggle is read as on from anything but "true", an
 *             unreadable or missing store turns it on (WC4: off by default
 *             on desktop), or a store that refuses a write throws into the
 *             page (W6.1 lock 7).
 *   links     Enter on a link in the text reaches default_in, which sends an
 *             empty command and cancels the link (decomp §3 key claims); or
 *             the claim reaches past the text: Enter in the command line, on
 *             a panel exit, with a modifier, or Space (which does not
 *             activate a link); or the claim cancels the link itself
 *             (W6.1 lock 3).
 *   layout    the room panel counts as shown below the 80rem breakpoint, a
 *             change of window width is not followed, the toggle does not
 *             show the forced-on state below the breakpoint, a change of the
 *             toggle is not stored or not applied, Enter or Space on the
 *             toggle reaches default_in, or a missing toggle or an
 *             unreadable store breaks init (W6.1 locks 5-7).
 */
"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const FILE = path.join(__dirname, "..", "..", "web", "static", "polishedworld", "js", "pw_text.js");
const { showInText, readStored, writeStored } = require(FILE);

// Literals, not the module's own constants (W-z, W-ai).
const KEY = "pw.roomListsInText";
const QUERY = "(min-width: 80rem)";
const TOGGLE_ID = "pw-room-lists-in-text";
const CONTENTS = { type: "room_contents" };

describe("rule", () => {
    it("hides room_contents only with the panel shown and lists not kept in text", () => {
        // [type, panelShown, listsInText] -> shown in the text area
        const table = [
            ["room_contents", true, false, false],
            ["room_contents", true, true, true],
            ["room_contents", false, false, true],
            ["room_contents", false, true, true],
            ["look", true, false, true],
            ["look", false, true, true],
            [undefined, true, false, true],
            ["Room_Contents", true, false, true],
        ];
        assert.deepEqual(
            table.map((row) => showInText(row[0], row[1], row[2])),
            table.map((row) => row[3])
        );
    });
});

// ------------------------------------------------------------------ storage

function store(initial, options) {
    const data = Object.assign({}, initial || {});
    const writes = [];
    return {
        data, writes,
        getItem(key) {
            if (options && options.readThrows) { throw new Error("SecurityError"); }
            return Object.prototype.hasOwnProperty.call(data, key) ? data[key] : null;
        },
        setItem(key, value) {
            if (options && options.writeThrows) { throw new Error("QuotaExceededError"); }
            writes.push([key, value]);
            data[key] = String(value);
        },
    };
}

describe("storage", () => {
    it("reads on only from the string \"true\" under the toggle's key", () => {
        const table = [
            [store({ [KEY]: "true" }), true],
            [store({ [KEY]: "false" }), false],
            [store({}), false],
            [store({ [KEY]: "yes" }), false],
            [store({ [KEY]: "1" }), false],
            [store({ "pw.other": "true" }), false],
            [store({ [KEY]: "true" }, { readThrows: true }), false],
            [null, false],
            [undefined, false],
        ];
        assert.deepEqual(table.map((row) => readStored(row[0])), table.map((row) => row[1]));
    });

    it("writes \"true\" or \"false\" under the toggle's key", () => {
        const s = store();
        writeStored(s, true);
        writeStored(s, false);
        assert.deepEqual(s.writes, [[KEY, "true"], [KEY, "false"]]);
    });

    it("never throws when the store refuses a write or is missing", () => {
        const outcomes = [store({}, { writeThrows: true }), null, undefined].map((s) => {
            try { writeStored(s, true); return "ok"; } catch (e) { return "threw"; }
        });
        assert.deepEqual(outcomes, ["ok", "ok", "ok"]);
    });
});

// ---------------------------------------------------------------- the page

function fakeTarget(tagName, inLog) {
    return {
        tagName: tagName,
        closest(selector) { return selector === "#messagewindow" && inLog ? { id: "messagewindow" } : null; },
    };
}

function keyEvent(key, target, modifiers) {
    const event = Object.assign(
        { key: key, target: target, shiftKey: false, ctrlKey: false, altKey: false, metaKey: false,
          prevented: 0, stopped: 0 },
        modifiers || {}
    );
    event.preventDefault = () => { event.prevented += 1; };
    event.stopPropagation = () => { event.stopped += 1; };
    return event;
}

function fakeToggle() {
    const el = { id: TOGGLE_ID, checked: false, disabled: false, listeners: {} };
    el.addEventListener = (type, fn) => { (el.listeners[type] = el.listeners[type] || []).push(fn); };
    el.fire = (type, event) => { (el.listeners[type] || []).forEach((fn) => fn(event || {})); };
    return el;
}

function fakeQuery(matches) {
    const mql = { matches: matches, listeners: [] };
    mql.addEventListener = (type, fn) => { if (type === "change") { mql.listeners.push(fn); } };
    mql.fire = (now) => { mql.matches = now; mql.listeners.forEach((fn) => fn({ matches: now })); };
    return mql;
}

// Loads pw_text.js in its own context, with a window and a document when
// given, and returns what it registered plus the fakes.
function load(options) {
    const added = [];
    const context = {
        plugin_handler: { add(name, plugin) { added.push([name, plugin]); } },
        console: console,
    };
    const queries = [];
    let mql = null;
    let toggle = null;
    if (options) {
        mql = fakeQuery(options.wide);
        toggle = options.noToggle ? null : fakeToggle();
        const win = {
            matchMedia(query) { queries.push(query); return mql; },
        };
        if (options.storageThrows) {
            Object.defineProperty(win, "localStorage", { get() { throw new Error("SecurityError"); } });
        } else {
            win.localStorage = options.storage || store();
        }
        context.window = win;
        context.document = { getElementById(id) { return id === TOGGLE_ID ? toggle : null; } };
    }
    const sandbox = vm.createContext(context);
    vm.runInContext(fs.readFileSync(FILE, "utf8"), sandbox, { filename: FILE });
    return { added, plugin: added[0] && added[0][1], queries, mql, toggle, win: context.window };
}

function started(options) {
    const page = load(options);
    page.plugin.init();
    return page;
}

describe("plugin", () => {
    it("registers once as pw_text with init, onKeydown and onText", () => {
        const { added } = load();
        assert.deepEqual(added.map((a) => a[0]), ["pw_text"]);
        assert.deepEqual(
            [typeof added[0][1].init, typeof added[0][1].onKeydown, typeof added[0][1].onText],
            ["function", "function", "function"]
        );
    });

    it("never claims a look, a plain line or a message without kwargs", () => {
        const { plugin } = started({ wide: true });
        assert.deepEqual(
            [
                plugin.onText(["x"], { type: "look" }),
                plugin.onText(["x"], {}),
                plugin.onText(["x"], undefined),
                plugin.onText(["x"], null),
            ],
            [false, false, false, false]
        );
    });

    it("leaves room_contents to the text area before init", () => {
        const { plugin } = load({ wide: true });
        assert.equal(plugin.onText(["|wExits:|n out"], CONTENTS), false);
    });
});

describe("links", () => {
    it("claims plain Enter on a link in the text and nothing else", () => {
        const { plugin } = load();
        const rows = [
            [keyEvent("Enter", fakeTarget("A", true)), true],
            [keyEvent("Enter", fakeTarget("A", false)), false],
            [keyEvent("Enter", fakeTarget("TEXTAREA", false)), false],
            [keyEvent("Enter", fakeTarget("DIV", true)), false],
            [keyEvent(" ", fakeTarget("A", true)), false],
            [keyEvent("a", fakeTarget("A", true)), false],
            [keyEvent("Enter", fakeTarget("A", true), { shiftKey: true }), false],
            [keyEvent("Enter", fakeTarget("A", true), { ctrlKey: true }), false],
            [keyEvent("Enter", fakeTarget("A", true), { altKey: true }), false],
            [keyEvent("Enter", fakeTarget("A", true), { metaKey: true }), false],
            [keyEvent("Enter", null), false],
        ];
        assert.deepEqual(rows.map((row) => plugin.onKeydown(row[0])), rows.map((row) => row[1]));
    });

    it("lets the browser follow the link: no preventDefault, no stopPropagation", () => {
        const { plugin } = load();
        const event = keyEvent("Enter", fakeTarget("A", true));
        const claimed = plugin.onKeydown(event);
        assert.deepEqual([claimed, event.prevented, event.stopped], [true, 0, 0]);
    });
});

describe("layout", () => {
    it("asks for the stylesheet's one breakpoint, once", () => {
        const { queries } = started({ wide: true });
        assert.deepEqual(queries, [QUERY]);
    });

    it("hides room_contents on desktop by default and shows the toggle off", () => {
        const { plugin, toggle } = started({ wide: true });
        assert.deepEqual(
            [plugin.onText(["x"], CONTENTS), toggle.checked, toggle.disabled],
            [true, false, false]
        );
    });

    it("keeps room_contents on desktop when the stored toggle is on", () => {
        const { plugin, toggle } = started({ wide: true, storage: store({ [KEY]: "true" }) });
        assert.deepEqual(
            [plugin.onText(["x"], CONTENTS), toggle.checked, toggle.disabled],
            [false, true, false]
        );
    });

    it("forces room_contents on below the breakpoint, toggle checked and disabled", () => {
        const { plugin, toggle } = started({ wide: false, storage: store({ [KEY]: "false" }) });
        assert.deepEqual(
            [plugin.onText(["x"], CONTENTS), toggle.checked, toggle.disabled],
            [false, true, true]
        );
    });

    it("follows a change of window width both ways", () => {
        const { plugin, toggle, mql } = started({ wide: true });
        mql.fire(false);
        const narrow = [plugin.onText(["x"], CONTENTS), toggle.checked, toggle.disabled];
        mql.fire(true);
        const wide = [plugin.onText(["x"], CONTENTS), toggle.checked, toggle.disabled];
        assert.deepEqual([narrow, wide], [[false, true, true], [true, false, false]]);
    });

    it("applies and stores a change of the toggle", () => {
        const storage = store();
        const { plugin, toggle } = started({ wide: true, storage: storage });
        toggle.checked = true;
        toggle.fire("change");
        const on = plugin.onText(["x"], CONTENTS);
        toggle.checked = false;
        toggle.fire("change");
        const off = plugin.onText(["x"], CONTENTS);
        assert.deepEqual([on, off, storage.writes], [false, true, [[KEY, "true"], [KEY, "false"]]]);
    });

    it("stops Enter and Space at the toggle, and nothing else", () => {
        const { toggle } = started({ wide: true });
        const events = [keyEvent("Enter", toggle), keyEvent(" ", toggle), keyEvent("a", toggle)];
        events.forEach((event) => toggle.fire("keydown", event));
        assert.deepEqual(events.map((e) => [e.stopped, e.prevented]), [[1, 0], [1, 0], [0, 0]]);
    });

    it("starts from off and still toggles in memory when the store cannot be reached", () => {
        const page = load({ wide: true, storageThrows: true });
        let threw = false;
        try { page.plugin.init(); } catch (e) { threw = true; }
        const before = page.plugin.onText(["x"], CONTENTS);
        page.toggle.checked = true;
        page.toggle.fire("change");
        assert.deepEqual([threw, before, page.plugin.onText(["x"], CONTENTS)], [false, true, false]);
    });

    it("still follows the breakpoint when the page has no toggle", () => {
        const page = load({ wide: true, noToggle: true });
        let threw = false;
        try { page.plugin.init(); } catch (e) { threw = true; }
        const wide = page.plugin.onText(["x"], CONTENTS);
        page.mql.fire(false);
        assert.deepEqual([threw, wide, page.plugin.onText(["x"], CONTENTS)], [false, true, false]);
    });
});
