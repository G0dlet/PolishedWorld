/*
 * PolishedWorld webclient: the text router (webclient decomposition W5.4,
 * W6.1).
 *
 * The server sends a look at the room you stand in as two text messages
 * (world/room_text.py room_look, WC4): the description with
 * kwargs.type "look", then the exits, characters and things with
 * kwargs.type "room_contents". The location panel (pw_room.js) shows the
 * same lists, so WC4 lets the client leave room_contents out of the text
 * area -- but only while the panel is shown and the player has not asked to
 * keep room lists in the text, so a screen-reader player and a narrow
 * window never lose a line (WC1, WC14).
 *
 * A plugin, unlike the panel renderers: webclient_gui.js hands every text
 * message to the plugins' onText in <script> order until one returns true,
 * and default_out.js claims all of them, so this file loads before it,
 * where base.html marks project plugins (tests/test_webclient_template.py
 * pins the order). Returning true here means "claimed, not shown"; false
 * passes the line on to default_out.
 *
 * Locked at W5.4's STOPP 0:
 *   5C  The rule is written and tested once (showInText); its two inputs
 *       come from W6.1.
 * Locked at W6.1's STOPP 0 (Adam took every recommendation):
 *   3A  Enter on a link in the text (an |lc link, <a href="#" onclick=...>)
 *       is claimed here, in onKeydown, so default_in never sees it: there
 *       the command line is not focused, so it would send an empty command
 *       and preventDefault the link's own activation (decomp §3 key
 *       claims). Nothing is prevented or stopped, so the browser follows
 *       the link. Space does not activate a link and is not claimed.
 *   5A  The panel counts as shown only at the stylesheet's one breakpoint,
 *       matchMedia (min-width: 80rem), followed on "change". Below it the
 *       panel is a drawer and the lists are forced into the text, whether
 *       the drawer is open or not.
 *   6A  The toggle is a checkbox at the end of the location panel. Below
 *       the breakpoint it shows the forced state: checked and disabled. It
 *       stops Enter and Space at itself (key claims), and never prevents
 *       them, so Space still ticks it.
 *   7A  Stored in localStorage under pw.roomListsInText as "true"/"false".
 *       Anything else, or a store that cannot be read, is off (WC4: off by
 *       default on desktop); a refused write keeps the choice in memory
 *       for the session.
 *   8A  The toggle applies to lines that arrive after it changes. Lines
 *       already written are left as they are: default_out keeps no type on
 *       them (decomp §3 message class).
 * Before init both inputs say "show", so nothing is hidden until the page
 * has read the layout and the store.
 *
 * Also loads in Node for tests/js/test_pw_text.js through module.exports.
 */
var pw_text = (function () {
    "use strict";

    var STORAGE_KEY = "pw.roomListsInText";
    var TOGGLE_ID = "pw-room-lists-in-text";

    // The two inputs of the rule (lock 5C). Set by init and its listeners.
    var panelShown = false;
    var listsInText = false;

    var storage = null;
    var toggle = null;

    // Whether a text message of this type belongs in the text area (WC4).
    function showInText(type, panelShown, listsInText) {
        if (type !== "room_contents") {
            return true;
        }
        return !panelShown || listsInText;
    }

    // The stored toggle: on only for the string "true" (lock 7A).
    function readStored(store) {
        try {
            return Boolean(store) && store.getItem(STORAGE_KEY) === "true";
        } catch (e) {
            return false;
        }
    }

    function writeStored(store, value) {
        if (!store) {
            return;
        }
        try {
            store.setItem(STORAGE_KEY, value ? "true" : "false");
        } catch (e) {
            // Full or refused: the choice lives in memory for this session.
        }
    }

    // A link inside the text area, not one in a panel (lock 3A).
    function isTextLink(target) {
        return Boolean(target) && target.tagName === "A" &&
            typeof target.closest === "function" && target.closest("#messagewindow") !== null;
    }

    function onKeydown(event) {
        if (event.key !== "Enter" || event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) {
            return false;
        }
        return isTextLink(event.target);
    }

    function onText(args, kwargs) {
        var type = kwargs ? kwargs.type : undefined;
        return !showInText(type, panelShown, listsInText);
    }

    // The checkbox shows what the rule does: forced on below the breakpoint.
    function syncToggle() {
        if (!toggle) {
            return;
        }
        toggle.checked = !panelShown || listsInText;
        toggle.disabled = !panelShown;
    }

    function init() {
        if (typeof window === "undefined" || typeof document === "undefined") {
            return;
        }
        try {
            storage = window.localStorage;
        } catch (e) {
            storage = null;
        }
        listsInText = readStored(storage);

        var wide = window.matchMedia("(min-width: 80rem)");
        panelShown = wide.matches;
        wide.addEventListener("change", function (event) {
            panelShown = event.matches;
            syncToggle();
        });

        toggle = document.getElementById(TOGGLE_ID);
        if (toggle) {
            toggle.addEventListener("change", function () {
                listsInText = toggle.checked;
                writeStored(storage, listsInText);
            });
            toggle.addEventListener("keydown", function (event) {
                if (event.key === "Enter" || event.key === " ") {
                    event.stopPropagation();
                }
            });
        }
        syncToggle();
    }

    return {
        init: init, onKeydown: onKeydown, onText: onText, showInText: showInText,
        readStored: readStored, writeStored: writeStored,
    };
})();

if (typeof plugin_handler !== "undefined") {
    plugin_handler.add("pw_text", pw_text);
}
if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        showInText: pw_text.showInText,
        readStored: pw_text.readStored,
        writeStored: pw_text.writeStored,
        plugin: pw_text,
    };
}
