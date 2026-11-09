/*
 * PolishedWorld webclient: the text router (webclient decomposition W5.4).
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
 * Locked at W5.4's STOPP 0 (Adam took every recommendation):
 *   5C  The rule is written and tested now; its two inputs are W6.1's.
 *       Until W6.1 adds the breakpoint check (matchMedia, 80rem) and the
 *       *room lists in text* toggle, PANEL_SHOWN is false and LISTS_IN_TEXT
 *       is true, so every room_contents line is shown: nothing is hidden
 *       before a player can turn the hiding off.
 *
 * Also loads in Node for tests/js/test_pw_text.js through module.exports.
 */
var pw_text = (function () {
    "use strict";

    // W6.1 replaces these two with the layout and the stored toggle.
    var PANEL_SHOWN = false;
    var LISTS_IN_TEXT = true;

    // Whether a text message of this type belongs in the text area (WC4).
    function showInText(type, panelShown, listsInText) {
        if (type !== "room_contents") {
            return true;
        }
        return !panelShown || listsInText;
    }

    function onText(args, kwargs) {
        var type = kwargs ? kwargs.type : undefined;
        return !showInText(type, PANEL_SHOWN, LISTS_IN_TEXT);
    }

    // Mandatory plugin hook; nothing to set up.
    function init() {}

    return { init: init, onText: onText, showInText: showInText };
})();

if (typeof plugin_handler !== "undefined") {
    plugin_handler.add("pw_text", pw_text);
}
if (typeof module !== "undefined" && module.exports) {
    module.exports = { showInText: pw_text.showInText, plugin: pw_text };
}
