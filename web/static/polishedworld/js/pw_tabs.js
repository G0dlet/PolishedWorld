/*
 * PolishedWorld webclient: the tabs over the text (webclient decomposition
 * W6.2, WC14).
 *
 * Channel and conversation text can be read in a tab of its own; All shows
 * everything. The census read at W6.2's start (Evennia 6.1.0): say and
 * whisper carry kwargs.type "say"/"whisper" (objects.py at_say, :2914-2917),
 * pose carries "pose" (commands/default/general.py:772), and a channel line
 * carries no type at all but kwargs.from_channel, the channel's id
 * (accounts.py channel_msg, :1326-1330). page is untyped and stays in All.
 *
 * A plugin, like pw_text.js: webclient_gui.js hands every text message to
 * the plugins' onText in <script> order, with the same kwargs object, until
 * one returns true. This one never returns true. It adds its tab's class to
 * kwargs.cls and passes the line on, and default_out.js writes
 * <div class='<kwargs.cls>'> (default_out.js:13-14) -- so every line is one
 * node in #messagewindow, the page's one live region, and a tab is a filter
 * on it (webclient.css, data-pw-tab). It loads after pw_text.js, so a
 * room_contents line that one hides never reaches a tab or marks one.
 *
 * Locked at W6.2's STOPP 0 (Adam took every recommendation):
 *   1A  Tabs All, Channels (from_channel) and Talk (say, whisper, pose).
 *   2A  One log, filtered: no line is written twice, the link claim in
 *       pw_text.js (closest("#messagewindow")) holds for every tab, and
 *       default_out keeps scrolling. A line hidden by the filter is
 *       display:none, so a screen reader does not read it in that tab;
 *       the Orca pass (BACKLOG, trigger W8.1) checks this.
 *   3A  WAI-ARIA tabs: role="tablist" over the text, role="tab" buttons
 *       controlling #main-sub (role="tabpanel", named by the selected tab),
 *       a roving tabindex, and ArrowLeft/ArrowRight (wrapping), Home and End
 *       moving selection and focus at once. Those keys are stopped at the
 *       tab and prevented (no page scroll); Enter and Space are stopped and
 *       never prevented, so the browser still turns them into the click.
 *       default_in.js would otherwise move focus to the command line on any
 *       of them (decomp §3 key claims). Keys with Alt, Ctrl, Meta or Shift
 *       are left alone (Alt+Left is the browser's Back; Shift+Up is
 *       history.js).
 *   4A  A switch scrolls <main> (default_out's scroller) to the newest line.
 *   5B  A line marks every closed tab it is shown in with a visible "new"
 *       inside the tab's name, until that tab is opened. Not a live region.
 *   6A  The page starts on All, as the markup does; nothing is stored.
 *   7A  The client's own lines (kwargs.cls "err" or "sys",
 *       webclient_gui.js:192, 208) show in every tab.
 *   8A  Below the breakpoint the same row, scrolling sideways if it must.
 *
 * Also loads in Node for tests/js/test_pw_tabs.js through module.exports.
 */
var pw_tabs = (function () {
    "use strict";

    var TABS = ["all", "channels", "talk"];
    var TALK_TYPES = ["say", "whisper", "pose"];
    var EVERY_CLASSES = ["err", "sys"];

    var open = "all";
    var started = false;

    // The tab a line belongs to besides All: "channels", "talk", "every"
    // (shown in all tabs) or null (All only). Lock 1A, 7A.
    function tabOf(kwargs) {
        if (!kwargs) {
            return null;
        }
        if (kwargs.from_channel !== undefined && kwargs.from_channel !== null) {
            return "channels";
        }
        if (TALK_TYPES.indexOf(kwargs.type) !== -1) {
            return "talk";
        }
        var classes = typeof kwargs.cls === "string" ? kwargs.cls.split(/\s+/) : [];
        for (var i = 0; i < classes.length; i++) {
            if (EVERY_CLASSES.indexOf(classes[i]) !== -1) {
                return "every";
            }
        }
        return null;
    }

    // The tabs a line of that kind is shown in.
    function tabsShowing(tab) {
        if (tab === "every") {
            return TABS.slice();
        }
        return tab ? ["all", tab] : ["all"];
    }

    function byId(id) {
        return typeof document === "undefined" ? null : document.getElementById(id);
    }

    function setMark(name, shown) {
        var mark = byId("pw-tab-" + name + "-new");
        if (mark) {
            mark.hidden = !shown;
        }
    }

    // The tabs on the page, in order: a missing button drops out of the ring.
    function present() {
        return TABS.filter(function (name) { return byId("pw-tab-" + name) !== null; });
    }

    function select(name, focus) {
        open = name;
        TABS.forEach(function (other) {
            var tab = byId("pw-tab-" + other);
            if (tab) {
                tab.setAttribute("aria-selected", other === name ? "true" : "false");
                tab.setAttribute("tabindex", other === name ? "0" : "-1");
            }
        });
        setMark(name, false);
        var log = byId("messagewindow");
        if (log) {
            log.setAttribute("data-pw-tab", name);
        }
        var panel = byId("main-sub");
        if (panel) {
            panel.setAttribute("aria-labelledby", "pw-tab-" + name);
        }
        var main = byId("main");
        if (main) {
            main.scrollTop = main.scrollHeight;
        }
        var button = byId("pw-tab-" + name);
        if (focus && button) {
            button.focus();
        }
    }

    // The tab a moving key goes to from `name`, or null for any other key.
    // Modifiers are ruled out by the caller.
    function target(name, event) {
        var ring = present();
        var at = ring.indexOf(name);
        switch (event.key) {
        case "ArrowRight":
            return ring[(at + 1) % ring.length];
        case "ArrowLeft":
            return ring[(at - 1 + ring.length) % ring.length];
        case "Home":
            return ring[0];
        case "End":
            return ring[ring.length - 1];
        default:
            return null;
        }
    }

    function onTabKeydown(name, event) {
        if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) {
            return;
        }
        if (event.key === "Enter" || event.key === " ") {
            event.stopPropagation();
            return;
        }
        var next = target(name, event);
        if (next) {
            event.stopPropagation();
            event.preventDefault();
            select(next, true);
        }
    }

    function onText(args, kwargs) {
        var tab = tabOf(kwargs);
        if (tab) {
            kwargs.cls = typeof kwargs.cls === "string" && kwargs.cls ? kwargs.cls + " pw-tab-" + tab : "pw-tab-" + tab;
        }
        if (started) {
            tabsShowing(tab).forEach(function (name) {
                if (name !== open) {
                    setMark(name, true);
                }
            });
        }
        return false;
    }

    function init() {
        if (typeof document === "undefined") {
            return;
        }
        TABS.forEach(function (name) {
            var tab = byId("pw-tab-" + name);
            if (!tab) {
                return;
            }
            tab.addEventListener("click", function () {
                select(name, false);
            });
            tab.addEventListener("keydown", function (event) {
                onTabKeydown(name, event);
            });
        });
        select("all", false);
        started = true;
    }

    return { init: init, onText: onText, tabOf: tabOf, tabsShowing: tabsShowing };
})();

if (typeof plugin_handler !== "undefined") {
    plugin_handler.add("pw_tabs", pw_tabs);
}
if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        tabOf: pw_tabs.tabOf,
        tabsShowing: pw_tabs.tabsShowing,
        plugin: pw_tabs,
    };
}
