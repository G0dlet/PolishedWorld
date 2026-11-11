/*
 * PolishedWorld webclient: the inventory panel (webclient decomposition W7.1).
 *
 * Shows what `inventory` lists: what the character carries and what it
 * wears, from the `inventory` field of the char snapshot
 * (world/client_state.py inventory_lists). The lists ride in char, not in a
 * domain of their own (lock 1), so they and the ENC figure pw_char.js shows
 * always come from the same frame. Rows carry `inventory`'s order: carried,
 * then worn (WC1). The names are plain text, not links (lock 5): the room's
 * things are not links either, and a numbered name ("two ropes") is not
 * something `look` can find.
 *
 * A renderer like pw_room.js, not an Evennia plugin: it registers with
 * pw_state.on("char"), the second renderer there after pw_char.js (W4.3
 * lock 2A allows several), so it loads after pw_state.js.
 *
 * Locked at W7.1's STOPP 0 (Adam took every recommendation):
 *   4   Own <section> last in the left panel, static markup, heading
 *       "Inventory"; rows Carrying and Wearing. Both rows hide until a char
 *       frame carries the field, and again on one that does not.
 *   6   An empty list says "Nothing.", as `inventory` does for an empty table.
 *
 * Char frames come for health too, so a list is rebuilt only when its
 * entries change, and every name is written with textContent: object keys
 * can hold any characters.
 */
(function () {
    "use strict";

    var LISTS = ["carried", "worn"];
    var EMPTY = "Nothing.";

    // The names a row shows for a char snapshot, or null when the inventory
    // is unknown (no frame yet, or a frame without the field).
    function listItems(snapshot, list) {
        if (!snapshot || !snapshot.inventory) {
            return null;
        }
        return snapshot.inventory[list].map(String);
    }

    function start() {
        if (!document.getElementById("pw-inventory")) {
            return;   // a page without the panel
        }
        var shown = {};   // list -> what was last written

        function entry(text, className) {
            var li = document.createElement("li");
            if (className) {
                li.className = className;
            }
            li.textContent = text;
            return li;
        }

        function writeList(list, items) {
            var stamp = JSON.stringify(items);
            if (shown[list] === stamp) {
                return;
            }
            shown[list] = stamp;
            document.getElementById("pw-inventory-" + list).hidden = items === null;
            var ul = document.getElementById("pw-inventory-" + list + "-list");
            if (items === null) {
                ul.replaceChildren();
            } else if (items.length === 0) {
                ul.replaceChildren(entry(EMPTY, "pw-inventory-empty"));
            } else {
                ul.replaceChildren.apply(ul, items.map(function (text) {
                    return entry(text, "");
                }));
            }
        }

        pw_state.on("char", function (snapshot) {
            LISTS.forEach(function (list) {
                writeList(list, listItems(snapshot, list));
            });
        });
    }

    if (typeof module !== "undefined" && module.exports) {
        module.exports = { listItems: listItems };
    }
    if (typeof pw_state !== "undefined" && typeof document !== "undefined") {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", start);
        } else {
            start();
        }
    }
})();
