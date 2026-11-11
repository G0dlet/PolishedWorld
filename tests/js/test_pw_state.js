/*
 * Tests for web/static/polishedworld/js/pw_state.js (webclient decomposition
 * W4.3, OQ-W1). Run from the repo root with Node 20 or later:
 *
 *     node --test tests/js/test_pw_state.js
 *
 * Not part of `evennia test`; the Django suite never sees this file. Each
 * describe() names the bug it pressures:
 *
 *   claims       a domain is not claimed, so its snapshot reaches
 *                default_out and prints as unescaped HTML; or a name that
 *                is not a domain is claimed and silently swallowed.
 *   malformed    a frame whose args[0] is not an object falls through to
 *                default_out instead of being claimed and logged.
 *   idempotent   a repeated identical snapshot renders twice (eat and a
 *                login each send a domain twice, decomp Rev 6), or a
 *                changed one does not render, or `previous` is wrong.
 *   reconnect    after a connection close the first identical snapshot is
 *                swallowed, so a panel that cleared itself stays empty.
 *   replay       a renderer registered after its domain arrived waits for
 *                the next push instead of drawing the snapshot it missed.
 *   isolation    a renderer that throws stops the renderers after it, or
 *                makes onUnknownCmd return something other than true.
 *   registration the browser build does not add itself to plugin_handler
 *                under the name "pw_state", or the global is not the
 *                plugin it adds.
 */
"use strict";

const { describe, it, beforeEach } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const FILE = path.join(__dirname, "..", "..", "web", "static", "polishedworld", "js", "pw_state.js");
const { create, DOMAINS } = require(FILE);

const CHAR = { name: "Tester", health: { current: 10, max: 12 } };

function recorder() {
    const calls = [];
    const fn = (snapshot, previous) => calls.push({ snapshot, previous });
    fn.calls = calls;
    return fn;
}

let state;
beforeEach(() => {
    state = create();
});

describe("claims", () => {
    it("are exactly the four server domains, in the server's order", () => {
        assert.deepEqual(DOMAINS, ["char", "survival", "world", "room"]);
    });

    it("claim each domain and store its snapshot", () => {
        for (const domain of ["char", "survival", "world", "room"]) {
            const snap = { domain };
            assert.equal(state.onUnknownCmd(domain, [snap], { options: {} }), true, domain);
            assert.deepEqual(state.latest(domain), snap, domain);
        }
    });

    it("leave every other name to the next plugin", () => {
        for (const name of ["text", "prompt", "webclient_options", "pw_state", "Char", "rooms", ""]) {
            assert.equal(state.onUnknownCmd(name, [{}], {}), false, JSON.stringify(name));
            assert.equal(state.latest(name), null, JSON.stringify(name));
        }
        // Receipt: the same instance does claim a domain.
        assert.equal(state.onUnknownCmd("char", [CHAR], {}), true);
    });

    it("render only the domain that arrived", () => {
        const onChar = recorder();
        const onRoom = recorder();
        state.on("char", onChar);
        state.on("room", onRoom);
        state.onUnknownCmd("char", [CHAR], {});
        assert.equal(onChar.calls.length, 1);
        assert.equal(onRoom.calls.length, 0);
    });
});

describe("malformed", () => {
    for (const [label, args] of [
        ["args not an array", { 0: CHAR }],
        ["no args", []],
        ["args[0] null", [null]],
        ["args[0] an array", [[CHAR]]],
        ["args[0] a string", ["<b>x</b>"]],
    ]) {
        it(`claims and logs: ${label}`, (t) => {
            const warn = t.mock.method(console, "warn", () => {});
            const onChar = recorder();
            state.on("char", onChar);
            assert.equal(state.onUnknownCmd("char", args, {}), true);
            assert.equal(onChar.calls.length, 0);
            assert.equal(state.latest("char"), null);
            assert.equal(warn.mock.callCount(), 1);
        });
    }
});

describe("idempotent", () => {
    it("renders an identical snapshot once", () => {
        const onChar = recorder();
        state.on("char", onChar);
        state.onUnknownCmd("char", [CHAR], {});
        state.onUnknownCmd("char", [JSON.parse(JSON.stringify(CHAR))], {});
        assert.equal(onChar.calls.length, 1);
    });

    it("still claims the repeat", () => {
        state.onUnknownCmd("char", [CHAR], {});
        assert.equal(state.onUnknownCmd("char", [CHAR], {}), true);
    });

    it("renders a change with the previous snapshot", () => {
        const onChar = recorder();
        state.on("char", onChar);
        const hurt = { name: "Tester", health: { current: 7, max: 12 } };
        state.onUnknownCmd("char", [CHAR], {});
        state.onUnknownCmd("char", [hurt], {});
        assert.equal(onChar.calls.length, 2);
        assert.equal(onChar.calls[0].previous, null);
        assert.deepEqual(onChar.calls[1].snapshot, hurt);
        assert.deepEqual(onChar.calls[1].previous, CHAR);
        assert.deepEqual(state.latest("char"), hurt);
    });

    it("compares per domain", () => {
        const onWorld = recorder();
        state.on("world", onWorld);
        state.onUnknownCmd("char", [{ same: 1 }], {});
        state.onUnknownCmd("world", [{ same: 1 }], {});
        assert.equal(onWorld.calls.length, 1);
    });
});

describe("reconnect", () => {
    it("renders the first identical snapshot after a close, with previous", () => {
        const onChar = recorder();
        state.on("char", onChar);
        state.onUnknownCmd("char", [CHAR], {});
        state.onConnectionClose([], {});
        state.onUnknownCmd("char", [CHAR], {});
        assert.equal(onChar.calls.length, 2);
        assert.deepEqual(onChar.calls[1].previous, CHAR);
    });

    it("keeps the latest snapshot across a close", () => {
        state.onUnknownCmd("room", [{ key: "Old Temple" }], {});
        state.onConnectionClose([], {});
        assert.deepEqual(state.latest("room"), { key: "Old Temple" });
    });
});

describe("replay", () => {
    it("draws a domain that arrived before the renderer registered", () => {
        state.onUnknownCmd("survival", [{ hunger: 3 }], {});
        const onSurvival = recorder();
        state.on("survival", onSurvival);
        assert.equal(onSurvival.calls.length, 1);
        assert.deepEqual(onSurvival.calls[0], { snapshot: { hunger: 3 }, previous: null });
    });

    it("draws nothing for a domain that has not arrived", () => {
        const onSurvival = recorder();
        state.on("survival", onSurvival);
        assert.equal(onSurvival.calls.length, 0);
        // Receipt: the renderer is registered and draws the next push.
        state.onUnknownCmd("survival", [{ hunger: 3 }], {});
        assert.equal(onSurvival.calls.length, 1);
    });

    it("rejects an unknown domain or a non-function", () => {
        assert.throws(() => state.on("weather", () => {}), TypeError);
        assert.throws(() => state.on("char", "render"), TypeError);
    });
});

describe("isolation", () => {
    it("runs every renderer and still claims when one throws", (t) => {
        const warn = t.mock.method(console, "warn", () => {});
        const after = recorder();
        state.on("char", () => {
            throw new Error("panel bug");
        });
        state.on("char", after);
        assert.equal(state.onUnknownCmd("char", [CHAR], {}), true);
        assert.equal(after.calls.length, 1);
        assert.equal(warn.mock.callCount(), 1);
    });

    it("keeps the snapshot a throwing renderer saw", (t) => {
        t.mock.method(console, "warn", () => {});
        state.on("char", () => {
            throw new Error("panel bug");
        });
        state.onUnknownCmd("char", [CHAR], {});
        assert.deepEqual(state.latest("char"), CHAR);
    });
});

describe("registration", () => {
    it("adds the global instance to plugin_handler as pw_state", () => {
        const added = [];
        const sandbox = {
            console,
            plugin_handler: { add: (name, plugin) => added.push([name, plugin]) },
        };
        vm.runInNewContext(fs.readFileSync(FILE, "utf8"), sandbox, { filename: FILE });
        assert.equal(added.length, 1);
        assert.equal(added[0][0], "pw_state");
        assert.equal(added[0][1], sandbox.pw_state);
        assert.equal(typeof sandbox.pw_state.init, "function");
        assert.equal(typeof sandbox.pw_state.onUnknownCmd, "function");
    });
});
