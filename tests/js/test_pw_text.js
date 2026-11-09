/*
 * Tests for web/static/polishedworld/js/pw_text.js, the text-routing plugin
 * (webclient decomposition W5.4, WC4, lock 5C). Run from the repo root:
 *     node --test tests/js/test_pw_text.js
 * Not part of `evennia test`. Each describe() names the bug it pressures:
 *   rule      room_contents is hidden while the room panel is not shown, or
 *             while the player keeps room lists in the text (WC14), or any
 *             other message type is ever hidden.
 *   plugin    the plugin is not registered, claims a text it should leave to
 *             default_out, or -- before W6.1 gives it a toggle -- hides
 *             room_contents at all.
 */
"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const FILE = path.join(__dirname, "..", "..", "web", "static", "polishedworld", "js", "pw_text.js");
const { showInText } = require(FILE);

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

function load() {
    const added = [];
    const sandbox = vm.createContext({
        plugin_handler: { add(name, plugin) { added.push([name, plugin]); } },
        console: console,
    });
    vm.runInContext(fs.readFileSync(FILE, "utf8"), sandbox, { filename: FILE });
    return added;
}

describe("plugin", () => {
    it("registers once as pw_text with init and onText", () => {
        const added = load();
        assert.deepEqual(added.map((a) => a[0]), ["pw_text"]);
        assert.deepEqual(
            [typeof added[0][1].init, typeof added[0][1].onText],
            ["function", "function"]
        );
    });

    it("never claims a look, a plain line or a message without kwargs", () => {
        const plugin = load()[0][1];
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

    it("leaves room_contents to the text area until W6.1 gives it a toggle", () => {
        const plugin = load()[0][1];
        assert.equal(plugin.onText(["|wExits:|n out"], { type: "room_contents" }), false);
    });
});
