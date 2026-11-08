/*
 * PolishedWorld webclient: the bar rule every panel shares (webclient
 * decomposition W5.2, lock 2B).
 *
 * barWidth() was born in pw_char.js (W5.1, lock 3C) and moved here when the
 * survival panel needed the same rule: two copies would be two knobs for
 * one job. tests/test_webclient_template.py TestGaugeScript checks that no
 * other project script defines it.
 *
 * A library, not a plugin and not a renderer: it registers with nothing and
 * only leaves the global pw_gauge for the panel scripts that load after it
 * (base.html; TestScriptOrder pins the order). Node gets the same object
 * through module.exports (tests/js/test_pw_gauge.js).
 */
var pw_gauge = (function () {
    "use strict";

    // The fill's CSS width for a gauge at current of max. Floor, so the bar
    // reads full only when the gauge is (199/200 is 99%); clamped to its
    // track; empty, not NaN or Infinity, when max is 0 or not a number.
    function barWidth(current, max) {
        if (!(max > 0)) {
            return "0%";
        }
        var fraction = Math.min(Math.max(current / max, 0), 1);
        return Math.floor(fraction * 100) + "%";
    }

    return { barWidth: barWidth };
})();

if (typeof module !== "undefined" && module.exports) {
    module.exports = pw_gauge;
}
