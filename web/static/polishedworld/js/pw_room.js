/*
 * PolishedWorld webclient: the location panel (webclient decomposition W5.4).
 *
 * Shows what a bare `look` lists (world/room_text.py): the room's name, its
 * exits, the awake characters and the things -- statues of logged-out
 * characters last among them (WC14) -- from the `room` snapshot
 * (world/client_state.py room_snapshot), which reads the same helper as
 * look (room_text.room_lists, lock 4C). Rows carry look's labels in look's
 * order (WC1).
 *
 * A renderer like pw_world.js, not an Evennia plugin: it registers with
 * pw_state.on("room"), the second renderer there after pw_world.js (W4.3
 * lock 2A allows several), so it loads after pw_state.js.
 *
 * Exits are real links (WC14). A click sends the exit's key as a command,
 * exactly what Evennia's |lc link does in the text area
 * (evennia/utils/text2html.py sub_mxp_links: Evennia.msg("text", [cmd], {})),
 * so a link can do nothing the typed command cannot. Evennia's default_in
 * listens for every keydown on the document (decomp §3 key claims): Enter
 * would send the empty command line and cancel the link's activation, and
 * Space would move the focus to the input. Both stop at the link, as at
 * layout.js's panel buttons; Enter then activates the link natively.
 *
 * Locked at W5.4's STOPP 0 (Adam took every recommendation):
 *   6   Own <section> after #pw-world in the right panel, static markup,
 *       heading "Location"; rows Exits, Characters, You see in look's
 *       order; no counts (look prints none); an empty list hides its row.
 *
 * A list is rebuilt only when its entries change, and every name is
 * written with textContent: object keys can hold any characters.
 *
 * The location picture (visual pass V3.4; Adam took every recommendation at
 * STOPP 0). The room's name gets data-picture, room_indoor or room_outdoor
 * by the snapshot's `indoor`, and the stylesheet draws the file as the
 * name's ::before, left of the name (locks 4, 5). The client knows nothing
 * else about a room, so there are two pictures. A frame without a room
 * (name null) gets no attribute and so no picture (lock 6).
 */
(function () {
    "use strict";

    var LISTS = ["exits", "characters", "things"];

    // The entries a list row shows for a snapshot: {text, key}, where key
    // is what a click sends (exits only, null otherwise).
    function listItems(snapshot, list) {
        if (!snapshot || snapshot.name === null) {
            return [];
        }
        return snapshot[list].map(function (entry) {
            if (list === "exits") {
                return { text: String(entry.name), key: String(entry.key) };
            }
            return { text: String(entry), key: null };
        });
    }

    // Lock 6: no room, no picture.
    function pictureName(snapshot) {
        if (!snapshot || snapshot.name === null) {
            return null;
        }
        return snapshot.indoor ? "room_indoor" : "room_outdoor";
    }

    function start() {
        if (!document.getElementById("pw-room")) {
            return;   // a page without the panel
        }
        var shown = {};   // "name" or a list -> what was last written

        function exitLink(item) {
            var link = document.createElement("a");
            link.href = "#";
            link.className = "pw-room-exit";
            link.textContent = item.text;
            link.addEventListener("click", function (event) {
                event.preventDefault();
                Evennia.msg("text", [item.key], {});
            });
            link.addEventListener("keydown", function (event) {
                if (event.key === "Enter" || event.key === " ") {
                    event.stopPropagation();
                }
            });
            return link;
        }

        function entry(item) {
            var li = document.createElement("li");
            if (item.key === null) {
                li.textContent = item.text;
            } else {
                li.appendChild(exitLink(item));
            }
            return li;
        }

        function writeName(name) {
            if (shown.name === name) {
                return;
            }
            shown.name = name;
            var el = document.getElementById("pw-room-name");
            el.hidden = name === null;
            if (name !== null) {
                el.textContent = name;
            }
        }

        function writePicture(name) {
            if (shown.picture === name) {
                return;
            }
            shown.picture = name;
            var el = document.getElementById("pw-room-name");
            if (name === null) {
                el.removeAttribute("data-picture");
            } else {
                el.setAttribute("data-picture", name);
            }
        }

        function writeList(list, items) {
            var stamp = JSON.stringify(items);
            if (shown[list] === stamp) {
                return;
            }
            shown[list] = stamp;
            document.getElementById("pw-room-" + list).hidden = items.length === 0;
            var ul = document.getElementById("pw-room-" + list + "-list");
            ul.replaceChildren.apply(ul, items.map(entry));
        }

        pw_state.on("room", function (snapshot) {
            var known = !!snapshot && snapshot.name !== null;
            writeName(known ? String(snapshot.name) : null);
            writePicture(pictureName(snapshot));
            LISTS.forEach(function (list) {
                writeList(list, listItems(snapshot, list));
            });
        });
    }

    if (typeof module !== "undefined" && module.exports) {
        module.exports = { listItems: listItems, pictureName: pictureName };
    }
    if (typeof pw_state !== "undefined" && typeof document !== "undefined") {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", start);
        } else {
            start();
        }
    }
})();
