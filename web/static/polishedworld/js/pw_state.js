/*
 * PolishedWorld webclient: the state plugin (webclient decomposition W4.3).
 *
 * The server pushes four domains -- char, survival, world, room -- as OOB
 * messages whose single argument is the snapshot (world/client_state.py,
 * push: `msg(domain=((snapshot,), {}))`; kwargs carry only `options`).
 * webclient_gui.js has no listener for those names, so they reach every
 * plugin's onUnknownCmd in <script> order until one returns true
 * (webclient_gui.js:167-179). default_out.js claims every name and prints it
 * as unescaped markup (default_out.js:43-54), so this file must load before
 * it: base.html puts it where project plugins go, and
 * tests/test_webclient_template.py pins the order and checks that DOMAINS
 * below matches the server's tuple.
 *
 * This plugin keeps the latest snapshot per domain and hands it to the
 * renderers panels register with pw_state.on(domain, fn). A renderer is
 * called as fn(snapshot, previous) and owns its DOM; it must write names as
 * text (textContent), since object keys can hold any characters.
 *
 * Locked at W4.3's STOPP 0:
 *   1A  No pw_state request on connect. Login and a browser reload already
 *       get all four (at_post_puppet), and `evennia reload` changes no game
 *       state, so the last snapshot stays true until the next push. The
 *       pw_state input function remains for a manual pull.
 *   2A  Several renderers per domain; one registered late is called at once
 *       with the latest snapshot (previous null).
 *   3A  A snapshot equal to the last one (same JSON) is claimed but not
 *       rendered: eat and a login each send a domain twice. A connection
 *       close forgets the comparison, not the snapshots, so the first frame
 *       after a reconnect always renders.
 *   4A  The four names are always claimed, a malformed frame included (it
 *       is logged), and a renderer that throws is logged and skipped, so
 *       nothing of ours ever reaches default_out.
 *
 * Also loads in Node for tests/js/test_pw_state.js, which gets the factory
 * through module.exports; the browser gets one instance as the global
 * pw_state.
 */
function createPwState() {
    "use strict";

    var DOMAINS = ["char", "survival", "world", "room"];

    var latest = {};     // domain -> last snapshot received
    var stamps = {};     // domain -> its JSON; emptied on connection close
    var renderers = {};  // domain -> [fn, ...]

    function isDomain(name) {
        return DOMAINS.indexOf(name) !== -1;
    }

    function isSnapshot(value) {
        return value !== null && typeof value === "object" && !Array.isArray(value);
    }

    function render(domain, fn, snapshot, previous) {
        try {
            fn(snapshot, previous);
        } catch (err) {
            console.warn("pw_state: a " + domain + " renderer failed", err);
        }
    }

    function receive(domain, snapshot) {
        var stamp = JSON.stringify(snapshot);
        if (stamps[domain] === stamp) {
            return;
        }
        var previous = Object.prototype.hasOwnProperty.call(latest, domain) ? latest[domain] : null;
        latest[domain] = snapshot;
        stamps[domain] = stamp;
        var fns = (renderers[domain] || []).slice();
        for (var i = 0; i < fns.length; i++) {
            render(domain, fns[i], snapshot, previous);
        }
    }

    // Plugin hook: claim the four domains, leave every other name alone.
    function onUnknownCmd(cmdname, args, kwargs) {
        if (!isDomain(cmdname)) {
            return false;
        }
        if (!Array.isArray(args) || !isSnapshot(args[0])) {
            console.warn("pw_state: malformed " + cmdname + " frame", args);
            return true;
        }
        receive(cmdname, args[0]);
        return true;
    }

    // Plugin hook: called for every plugin when the websocket closes.
    function onConnectionClose(args, kwargs) {
        stamps = {};
    }

    function on(domain, fn) {
        if (!isDomain(domain)) {
            throw new TypeError("pw_state.on: unknown domain " + JSON.stringify(domain));
        }
        if (typeof fn !== "function") {
            throw new TypeError("pw_state.on: renderer for " + domain + " is not a function");
        }
        (renderers[domain] = renderers[domain] || []).push(fn);
        if (Object.prototype.hasOwnProperty.call(latest, domain)) {
            render(domain, fn, latest[domain], null);
        }
    }

    function getLatest(domain) {
        return Object.prototype.hasOwnProperty.call(latest, domain) ? latest[domain] : null;
    }

    // Mandatory plugin hook; the plugin looks nothing up in the DOM.
    function init() {}

    return {
        init: init,
        onUnknownCmd: onUnknownCmd,
        onConnectionClose: onConnectionClose,
        on: on,
        latest: getLatest,
        DOMAINS: DOMAINS.slice(),
    };
}

var pw_state = createPwState();

if (typeof plugin_handler !== "undefined") {
    plugin_handler.add("pw_state", pw_state);
}
if (typeof module !== "undefined" && module.exports) {
    module.exports = { create: createPwState, DOMAINS: createPwState().DOMAINS };
}
