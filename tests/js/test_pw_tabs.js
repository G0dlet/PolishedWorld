/*
 * Tests for web/static/polishedworld/js/pw_tabs.js, the tab router
 * (webclient decomposition W6.2, WC14). Run from the repo root:
 *     node --test tests/js/test_pw_tabs.js
 * Not part of `evennia test`. Each describe() names the bug it pressures:
 *   rule      a channel line is not told by kwargs.from_channel (channels
 *             carry no type, accounts.py:1326-1330), a say, whisper or pose
 *             misses the Talk tab, a look or an untyped line leaves All, the
 *             client's own err/sys lines vanish from a filtered tab (lock
 *             7A), or a line is shown in a tab it does not belong to.
 *   plugin    the plugin is not registered, claims a line (then default_out
 *             never writes it, and the log loses it), overwrites a class the
 *             client set (err, sys), or throws on a message without kwargs.
 *   tabs      the markup's All is not the start (lock 6A), a click or a key
 *             does not move the selection, the arrows do not wrap, a key the
 *             tabs take reaches default_in (which moves focus to the command
 *             line, decomp §3 key claims), a key they do not take is stopped,
 *             Enter or Space is prevented (the browser turns them into the
 *             click), or a switch does not scroll to the newest line (4A).
 *   unread    a line does not mark the tabs it is shown in, marks the open
 *             tab, or the mark outlives opening the tab (5B).
 *   page      a missing element breaks init or a later line.
 */
"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const FILE = path.join(__dirname, "..", "..", "web", "static", "polishedworld", "js", "pw_tabs.js");
const { tabOf, tabsShowing } = require(FILE);

// Literals, not the module's own constants (W-z, W-ai).
const TABS = ["all", "channels", "talk"];

describe("rule", () => {
    it("files a line under channels, talk, every, or nothing beyond All", () => {
        const table = [
            [{ from_channel: 3 }, "channels"],
            [{ from_channel: 1, type: "say" }, "channels"],
            [{ type: "say" }, "talk"],
            [{ type: "whisper" }, "talk"],
            [{ type: "pose" }, "talk"],
            [{ cls: "err" }, "every"],
            [{ cls: "sys" }, "every"],
            [{ cls: "msg err" }, "every"],
            [{ type: "look" }, null],
            [{ type: "room_contents" }, null],
            [{ type: "Say" }, null],
            [{ type: "inventory" }, null],
            [{ from_channel: null }, null],
            [{ cls: "error" }, null],
            [{}, null],
            [null, null],
            [undefined, null],
        ];
        assert.deepEqual(table.map((row) => tabOf(row[0])), table.map((row) => row[1]));
    });

    it("shows every line in All, and in its own tab", () => {
        const table = [
            [null, ["all"]],
            ["channels", ["all", "channels"]],
            ["talk", ["all", "talk"]],
            ["every", ["all", "channels", "talk"]],
        ];
        assert.deepEqual(table.map((row) => tabsShowing(row[0])), table.map((row) => row[1]));
    });
});

// ---------------------------------------------------------------- the page

function element(id, attrs, page) {
    const el = { id: id, attrs: Object.assign({}, attrs || {}), hidden: false, scrollTop: 0,
                 scrollHeight: 0, listeners: {} };
    el.setAttribute = (name, value) => { el.attrs[name] = String(value); };
    el.getAttribute = (name) => (name in el.attrs ? el.attrs[name] : null);
    el.addEventListener = (type, fn) => { (el.listeners[type] = el.listeners[type] || []).push(fn); };
    el.fire = (type, event) => { (el.listeners[type] || []).forEach((fn) => fn(event || {})); };
    el.focus = () => { page.focused = id; };
    return el;
}

function keyEvent(key, modifiers) {
    const event = Object.assign(
        { key: key, shiftKey: false, ctrlKey: false, altKey: false, metaKey: false, prevented: 0, stopped: 0 },
        modifiers || {}
    );
    event.preventDefault = () => { event.prevented += 1; };
    event.stopPropagation = () => { event.stopped += 1; };
    return event;
}

// The markup as webclient.html writes it: All selected, every mark hidden.
function fakePage(missing) {
    const page = { focused: null, els: {} };
    const add = (id, attrs) => {
        if (!(missing || []).includes(id)) { page.els[id] = element(id, attrs, page); }
    };
    TABS.forEach((name, i) => {
        add("pw-tab-" + name, { "aria-selected": i === 0 ? "true" : "false", tabindex: i === 0 ? "0" : "-1" });
        add("pw-tab-" + name + "-new", {});
        if (page.els["pw-tab-" + name + "-new"]) { page.els["pw-tab-" + name + "-new"].hidden = true; }
    });
    add("messagewindow", { role: "log", "aria-live": "polite" });
    add("main-sub", { role: "tabpanel", "aria-labelledby": "pw-tab-all" });
    add("main", {});
    if (page.els.main) { page.els.main.scrollHeight = 900; }
    return page;
}

function load(options) {
    const added = [];
    const context = {
        plugin_handler: { add(name, plugin) { added.push([name, plugin]); } },
        console: console,
    };
    let page = null;
    if (options) {
        page = fakePage(options.missing);
        context.window = {};
        context.document = { getElementById(id) { return page.els[id] || null; } };
    }
    vm.runInContext(fs.readFileSync(FILE, "utf8"), vm.createContext(context), { filename: FILE });
    return { added, plugin: added[0] && added[0][1], page };
}

function started(missing) {
    const loaded = load({ missing: missing || [] });
    loaded.plugin.init();
    return loaded;
}

// One value per tab and the panel: what a screen reader and the CSS read.
function selection(page) {
    const el = page.els;
    return {
        selected: TABS.map((n) => el["pw-tab-" + n].getAttribute("aria-selected")),
        tabindex: TABS.map((n) => el["pw-tab-" + n].getAttribute("tabindex")),
        filter: el.messagewindow.getAttribute("data-pw-tab"),
        labelledby: el["main-sub"].getAttribute("aria-labelledby"),
    };
}

function marks(page) {
    return TABS.map((n) => page.els["pw-tab-" + n + "-new"].hidden);
}

const ON = (name) => ({
    selected: TABS.map((n) => (n === name ? "true" : "false")),
    tabindex: TABS.map((n) => (n === name ? "0" : "-1")),
    filter: name,
    labelledby: "pw-tab-" + name,
});

describe("plugin", () => {
    it("registers once as pw_tabs with init and onText, and no document key handler", () => {
        const { added } = load();
        assert.deepEqual(added.map((a) => a[0]), ["pw_tabs"]);
        const p = added[0][1];
        assert.deepEqual([typeof p.init, typeof p.onText, typeof p.onKeydown], ["function", "function", "undefined"]);
    });

    it("never claims a line, so default_out writes every one", () => {
        const { plugin } = started();
        const rows = [{ from_channel: 2 }, { type: "say" }, { type: "look" }, { cls: "err" }, {}, null, undefined];
        assert.deepEqual(rows.map((k) => plugin.onText(["x"], k)), rows.map(() => false));
    });

    it("adds its class to kwargs.cls and keeps the client's own", () => {
        const { plugin } = started();
        const rows = [
            [{ from_channel: 2 }, "pw-tab-channels"],
            [{ type: "whisper" }, "pw-tab-talk"],
            [{ cls: "err" }, "err pw-tab-every"],
            [{ cls: "sys" }, "sys pw-tab-every"],
            [{ type: "look" }, undefined],
            [{}, undefined],
        ];
        rows.forEach((row) => plugin.onText(["x"], row[0]));
        assert.deepEqual(rows.map((row) => row[0].cls), rows.map((row) => row[1]));
    });

    it("tags lines before init, without a page", () => {
        const { plugin } = load();
        const kwargs = { type: "pose" };
        assert.deepEqual([plugin.onText(["x"], kwargs), kwargs.cls], [false, "pw-tab-talk"]);
    });
});

describe("tabs", () => {
    it("starts on All, as the markup does", () => {
        const { page } = started();
        assert.deepEqual(selection(page), ON("all"));
    });

    it("selects a tab on click and scrolls the text to the newest line", () => {
        const { page } = started();
        page.els["pw-tab-talk"].fire("click");
        assert.deepEqual([selection(page), page.els.main.scrollTop], [ON("talk"), 900]);
    });

    it("moves selection and focus with the arrows, Home and End, wrapping", () => {
        // [start tab, key] -> tab selected and focused
        const rows = [
            ["all", "ArrowRight", "channels"],
            ["channels", "ArrowRight", "talk"],
            ["talk", "ArrowRight", "all"],
            ["all", "ArrowLeft", "talk"],
            ["talk", "ArrowLeft", "channels"],
            ["talk", "Home", "all"],
            ["all", "End", "talk"],
        ];
        const got = rows.map((row) => {
            const { page } = started();
            page.els["pw-tab-" + row[0]].fire("click");
            page.els["pw-tab-" + row[0]].fire("keydown", keyEvent(row[1]));
            return [selection(page).filter, page.focused];
        });
        assert.deepEqual(got, rows.map((row) => [row[2], "pw-tab-" + row[2]]));
    });

    it("stops the keys it takes, prevents only the moving ones", () => {
        const { page } = started();
        const rows = [
            [keyEvent("Enter"), [1, 0]],
            [keyEvent(" "), [1, 0]],
            [keyEvent("ArrowRight"), [1, 1]],
            [keyEvent("ArrowLeft"), [1, 1]],
            [keyEvent("Home"), [1, 1]],
            [keyEvent("End"), [1, 1]],
            [keyEvent("ArrowUp"), [0, 0]],
            [keyEvent("a"), [0, 0]],
            [keyEvent("Tab"), [0, 0]],
            [keyEvent("ArrowRight", { altKey: true }), [0, 0]],
            [keyEvent("ArrowLeft", { ctrlKey: true }), [0, 0]],
            [keyEvent("Home", { metaKey: true }), [0, 0]],
            [keyEvent("ArrowUp", { shiftKey: true }), [0, 0]],
        ];
        rows.forEach((row) => page.els["pw-tab-all"].fire("keydown", row[0]));
        assert.deepEqual(rows.map((row) => [row[0].stopped, row[0].prevented]), rows.map((row) => row[1]));
    });

    it("leaves selection alone on a key it does not take", () => {
        const { page } = started();
        page.els["pw-tab-all"].fire("keydown", keyEvent("ArrowRight", { altKey: true }));
        const after = [selection(page).filter, page.focused];
        // Receipt that the handler runs at all (W-o): the same key without Alt moves.
        page.els["pw-tab-all"].fire("keydown", keyEvent("ArrowRight"));
        assert.deepEqual([after, selection(page).filter], [["all", null], "channels"]);
    });
});

describe("unread", () => {
    it("marks the closed tabs a line is shown in, never the open one", () => {
        const { plugin, page } = started();
        const steps = [];
        plugin.onText(["x"], { from_channel: 1 });
        steps.push(marks(page));
        plugin.onText(["x"], { type: "say" });
        steps.push(marks(page));
        assert.deepEqual(steps, [[true, false, true], [true, false, false]]);
    });

    it("clears a tab's mark when the tab is opened", () => {
        const { plugin, page } = started();
        plugin.onText(["x"], { from_channel: 1 });
        const before = marks(page);
        page.els["pw-tab-channels"].fire("click");
        assert.deepEqual([before, marks(page)], [[true, false, true], [true, true, true]]);
    });

    it("marks All for a look while another tab is open", () => {
        const { plugin, page } = started();
        page.els["pw-tab-channels"].fire("click");
        plugin.onText(["x"], { type: "look" });
        assert.deepEqual(marks(page), [false, true, true]);
    });

    it("marks every closed tab for the client's own err line", () => {
        const { plugin, page } = started();
        plugin.onText(["x"], { cls: "err" });
        assert.deepEqual(marks(page), [true, false, false]);
    });
});

describe("page", () => {
    it("survives missing elements at init and on later lines", () => {
        const { plugin } = load({ missing: ["messagewindow", "main", "main-sub", "pw-tab-talk", "pw-tab-all-new"] });
        const outcomes = [];
        try { plugin.init(); outcomes.push("ok"); } catch (e) { outcomes.push("threw " + e.message); }
        try { plugin.onText(["x"], { type: "say" }); outcomes.push("ok"); } catch (e) { outcomes.push("threw " + e.message); }
        assert.deepEqual(outcomes, ["ok", "ok"]);
    });

    it("still switches between the tabs that are there", () => {
        const { page } = started(["pw-tab-talk", "pw-tab-talk-new"]);
        page.els["pw-tab-all"].fire("keydown", keyEvent("ArrowLeft"));
        assert.deepEqual([page.els.messagewindow.getAttribute("data-pw-tab"), page.focused],
                         ["channels", "pw-tab-channels"]);
    });
});
