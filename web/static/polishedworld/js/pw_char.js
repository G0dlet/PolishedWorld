/*
 * PolishedWorld webclient: the character panel (webclient decomposition
 * W5.1).
 *
 * Shows the `char` snapshot (world/client_state.py char_snapshot): the
 * name, health as numbers and its own description, the encumbrance line,
 * and the untinted silhouette (WC12). Zones, wound levels and Legend's
 * combat state are Stage 5 (BACKLOG *Character panel: Legend combat state*).
 *
 * Not an Evennia plugin: it registers a renderer with pw_state.on("char")
 * and never with Evennia's plugin handler (tests/test_webclient_template.py
 * TestCharScript), so it only has to load after pw_state.js. pw_state calls
 * the renderer only when the snapshot changed, and at once if one arrived
 * before this script ran (W4.3 locks 2 and 3).
 *
 * Locked at W5.1's STOPP 0 (Adam took every recommendation):
 *   1A  The markup is static in webclient.html; this file only writes text
 *       and attributes into it, never markup (Rev 5 (d)).
 *   2A  One file per panel. charView() turns a snapshot into the words the
 *       panel shows, and is what tests/js/test_pw_char.js tests in Node; the
 *       writer below it only copies those words into the page.
 *   3C  The bar is a span hidden from screen readers. The text beside it
 *       says everything it shows (WC14), and one colour means no second
 *       copy of the description thresholds lives here.
 *   4   Numbers and description as `status` prints them, without the
 *       percentage (the snapshot has none; computing it here would copy
 *       trait.percent()'s formatting). No health trait: the row is hidden.
 *   5A  The encumbrance line is `inventory`'s, word for word: "(overloaded)"
 *       for both bands above free, since no text names the ceiling (WC1).
 *   6   The figure's alt says the name and the state in words.
 */
(function () {
    "use strict";

    var FREE = "free";

    function barWidth(current, max) {
        // Floor, so the bar reads full only when health is (199/200 is 99%).
        if (!(max > 0)) {
            return "0%";
        }
        var fraction = Math.min(Math.max(current / max, 0), 1);
        return Math.floor(fraction * 100) + "%";
    }

    function charView(snapshot) {
        var name = String(snapshot.name);
        var health = snapshot.health;
        var enc = snapshot.encumbrance;
        var view = {
            name: name,
            health: null,
            alt: name,
            encumbrance: "Carrying " + enc.carried + "/" + enc.limit + " ENC"
                + (enc.band !== FREE ? " (overloaded)" : ""),
        };
        if (health) {
            view.health = {
                numbers: health.current + "/" + health.max,
                desc: String(health.desc),
                bar: barWidth(Number(health.current), Number(health.max)),
            };
            view.alt = name + ", " + health.desc;
        }
        return view;
    }

    function writeChar(byId, view) {
        byId("pw-char-name").textContent = view.name;
        byId("pw-char-figure").setAttribute("alt", view.alt);
        byId("pw-char-health").hidden = view.health === null;
        if (view.health !== null) {
            byId("pw-char-health-numbers").textContent = view.health.numbers;
            byId("pw-char-health-desc").textContent = view.health.desc;
            byId("pw-char-health-bar").style.width = view.health.bar;
        }
        byId("pw-char-enc").textContent = view.encumbrance;
    }

    function start() {
        if (!document.getElementById("pw-char")) {
            return;   // a page without the panel
        }
        var byId = function (id) {
            return document.getElementById(id);
        };
        pw_state.on("char", function (snapshot) {
            writeChar(byId, charView(snapshot));
        });
    }

    if (typeof module !== "undefined" && module.exports) {
        module.exports = { charView: charView };
    }
    if (typeof pw_state !== "undefined" && typeof document !== "undefined") {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", start);
        } else {
            start();
        }
    }
})();
