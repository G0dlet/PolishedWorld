/*
 * PolishedWorld webclient: the survival panel (webclient decomposition
 * W5.2).
 *
 * Shows the `survival` snapshot (world/client_state.py survival_snapshot):
 * hunger, thirst and fatigue, each as numbers, the gauge's own description
 * and a bar. All three count what the character has left, as health does:
 * fatigue is energy (100 fresh, 0 debilitated; Legend's levels in
 * world/fatigue.py, and rest adds to it), so a full bar is always the good
 * end and no bar is drawn inverted.
 *
 * A renderer like pw_char.js, not an Evennia plugin: it registers with
 * pw_state.on("survival") only, so it has to load after pw_state.js and,
 * for the bar rule, after pw_gauge.js.
 *
 * Locked at W5.2's STOPP 0 (Adam took every recommendation):
 *   1   The three gauges only. Starving and Dehydrated begin exactly when
 *       their gauge reaches 0, where its description already says so; the
 *       cold and heat stacks are printed by no command, so the panel may
 *       not show them (WC1). Their worded state belongs to roadmap
 *       *Temperature & exposure* (Temperature Design J1, KP1-KP2), which
 *       names this panel as where it shows once `status` prints it.
 *   2B  The bar's width comes from pw_gauge.js, shared with pw_char.js.
 *   3C  One palette colour per gauge, set in the stylesheet by the bar's
 *       id; the label and the description carry the meaning (WC14).
 *   4   Own <section> after the character panel, static markup (W5.1 1A).
 *   5   Numbers and description as `status` prints them, without the
 *       percentage (W5.1 lock 4). A missing trait hides its row.
 */
(function () {
    "use strict";

    // The server's SURVIVAL_GAUGES, in `status` order
    // (tests/test_webclient_template.py TestSurvivalScript reads this line).
    var GAUGES = ["hunger", "thirst", "fatigue"];

    var gauge = (typeof module !== "undefined" && module.exports)
        ? require("./pw_gauge.js")
        : pw_gauge;

    function survivalView(snapshot) {
        var view = {};
        GAUGES.forEach(function (key) {
            var value = snapshot[key];
            view[key] = value ? {
                numbers: value.current + "/" + value.max,
                desc: String(value.desc),
                bar: gauge.barWidth(Number(value.current), Number(value.max)),
            } : null;
        });
        return view;
    }

    function writeSurvival(byId, view) {
        GAUGES.forEach(function (key) {
            var id = "pw-survival-" + key;
            var row = view[key];
            byId(id).hidden = row === null;
            if (row !== null) {
                byId(id + "-numbers").textContent = row.numbers;
                byId(id + "-desc").textContent = row.desc;
                byId(id + "-bar").style.width = row.bar;
            }
        });
    }

    function start() {
        if (!document.getElementById("pw-survival")) {
            return;   // a page without the panel
        }
        var byId = function (id) {
            return document.getElementById(id);
        };
        pw_state.on("survival", function (snapshot) {
            writeSurvival(byId, survivalView(snapshot));
        });
    }

    if (typeof module !== "undefined" && module.exports) {
        module.exports = { survivalView: survivalView, GAUGES: GAUGES };
    }
    if (typeof pw_state !== "undefined" && typeof document !== "undefined") {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", start);
        } else {
            start();
        }
    }
})();
