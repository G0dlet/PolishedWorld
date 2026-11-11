/*
 * PolishedWorld webclient: side panels as drawers below the layout
 * breakpoint (webclient decomposition W3.2).
 *
 * Not an Evennia plugin: it never registers with the plugin handler, so its
 * place after default_out.js costs nothing (tests/test_webclient_template.py
 * TestLayoutScript). Above the breakpoint the stylesheet hides the buttons
 * and shows both panels, whatever state this script left behind.
 *
 * Each header button names its panel with aria-controls and reports its
 * state with aria-expanded; the panel gets the class pw-open. One panel is
 * open at a time. Escape, the button again, or a click outside the panel
 * closes it.
 *
 * Evennia's default_in.js listens for keydown on the document and claims
 * keys for the command line: Enter sends the focused field's text (empty
 * here) and cancels the key, and any other key, Space and Escape included,
 * moves focus to #inputfield. A panel button would then never open from the
 * keyboard. So Enter and Space on a panel button stop at the button (the
 * browser still turns them into a click), and Escape with a panel open is
 * handled in the capture phase, before default_in sees it.
 */
(function () {
    "use strict";

    var BUTTONS = ".pw-panel-button";

    function buttons() {
        return Array.prototype.slice.call(document.querySelectorAll(BUTTONS));
    }

    function panelFor(button) {
        return document.getElementById(button.getAttribute("aria-controls"));
    }

    function openButton() {
        var open = buttons().filter(function (button) {
            return button.getAttribute("aria-expanded") === "true";
        });
        return open.length ? open[0] : null;
    }

    function setOpen(button, open) {
        var panel = panelFor(button);
        if (!panel) {
            return;
        }
        button.setAttribute("aria-expanded", open ? "true" : "false");
        panel.classList.toggle("pw-open", open);
        if (open) {
            panel.focus();
        }
    }

    function closeOthers(except) {
        buttons().forEach(function (button) {
            if (button !== except) {
                setOpen(button, false);
            }
        });
    }

    function init() {
        buttons().forEach(function (button) {
            button.addEventListener("click", function () {
                var open = button.getAttribute("aria-expanded") !== "true";
                closeOthers(button);
                setOpen(button, open);
            });
            button.addEventListener("keydown", function (event) {
                if (event.key === "Enter" || event.key === " ") {
                    event.stopPropagation();
                }
            });
        });

        document.addEventListener("keydown", function (event) {
            var button = openButton();
            if (event.key !== "Escape" || !button) {
                return;
            }
            event.stopPropagation();
            setOpen(button, false);
            button.focus();
        }, true);

        document.addEventListener("click", function (event) {
            var button = openButton();
            if (!button) {
                return;
            }
            var panel = panelFor(button);
            if ((panel && panel.contains(event.target)) || event.target.closest(BUTTONS)) {
                return;
            }
            setOpen(button, false);
        });
    }

    function start() {
        try {
            init();
        } catch (err) {
            // The command line must keep working if the drawers cannot start.
            if (window.console) {
                window.console.error("PolishedWorld layout.js:", err);
            }
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }
})();
