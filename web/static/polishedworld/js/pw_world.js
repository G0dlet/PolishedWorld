/*
 * PolishedWorld webclient: the world panel (webclient decomposition W5.3).
 *
 * Shows what the `time` command prints (commands/world_commands.py
 * time_lines), row for row and word for word: Date, Time with its period,
 * Season and, outdoors, Weather (WC1). The clock runs here (WC9): the
 * `world` snapshot (world/client_state.py world_snapshot) carries the game
 * second, time_factor and the calendar tables, so no month name, season or
 * period boundary is written in this file.
 *
 * A renderer like pw_survival.js, not an Evennia plugin. It registers with
 * pw_state.on("world") and pw_state.on("room") -- the room's `indoor` flag
 * decides the weather row -- so it has to load after pw_state.js.
 *
 * Locked at W5.3's STOPP 0 (Adam took every recommendation):
 *   1A  The command's key is `time` (aliases date, clock); it replaces the
 *       extended_room contrib's `time`.
 *   2B  The clock counts from the frame's arrival, read with
 *       performance.now(), not from the server's wall clock (server_ms):
 *       a browser whose clock is off by two minutes would otherwise show
 *       the game eight minutes off until a reload. The renderer is
 *       registered before any frame can arrive: the deferred scripts run
 *       before jQuery's ready, where Evennia.init opens the websocket
 *       (webclient_gui.js:286-289), so a frame is never replayed late.
 *   3B  Parity with the server is one committed table,
 *       tests/js/fixtures/world_cases.json, checked from both sides.
 *   4A  The weather row shows only with a known room that is not indoors,
 *       as `time` prints it.
 *   5   One one-second timer per page, started with the script; a row is
 *       written only when its text changes.
 *   6   Own <section> first in the right panel, static markup, one row per
 *       line of `time` with its label; the mockup's temperature is printed
 *       by no command, so it is not here.
 *
 * Weather and season icons (visual pass V3.3; Adam took every
 * recommendation at STOPP 0). The script only names the icon: it sets the
 * row's data-icon to the file's stem (weather_night_raining, season_summer)
 * and the stylesheet maps each name to its file, so every icon is a CSS
 * background, decoration by construction (WC14).
 *   1   Night is the one period `night` (20:00-04:00), as the server's
 *       is_nighttime() says; dawn and dusk are day.
 *   5   A key this file does not know gets no data-icon, so no icon: the
 *       word stands alone (WV4).
 * The three tables are the server's words. tests/test_webclient_theme.py
 * reads them from this file and compares them with world/weather.py
 * WEATHER_STATES, gametime_utils' seasons and is_nighttime().
 */
(function () {
    "use strict";

    var ROWS = ["date", "time", "season", "weather"];
    var WEATHER_KEYS = ["clear", "raining", "snowing", "foggy"];
    var SEASON_KEYS = ["spring", "summer", "autumn", "winter"];
    var NIGHT_PERIODS = ["night"];

    function pad2(n) {
        return (n < 10 ? "0" : "") + n;
    }

    // The game second as `time` would read it at real time nowMs, for a
    // frame that arrived at receivedMs (both on the same clock, lock 2B).
    function gameSecondsAt(snapshot, receivedMs, nowMs) {
        return snapshot.game_seconds + (nowMs - receivedMs) * snapshot.time_factor / 1000;
    }

    // Date, Time and Season at a game second, as world.gametime_utils gives
    // them: custom_gametime()'s divisions, display values one-based.
    function worldView(seconds, calendar) {
        var rest = Math.floor(seconds);
        var part = {};
        calendar.units.forEach(function (unit) {
            part[unit[0]] = Math.floor(rest / unit[1]);
            rest = rest % unit[1];
        });
        var month = part.month + 1;
        var fraction = (part.hour * 3600 + part.min * 60 + rest) / 86400;
        var period = "day";   // get_time_of_day()'s fallback
        for (var i = 0; i < calendar.times_of_day.length; i++) {
            var span = calendar.times_of_day[i];
            if (span[1] <= fraction && fraction < span[2]) {
                period = span[0];
                break;
            }
        }
        var season = "spring";   // get_season()'s fallback
        var names = Object.keys(calendar.seasons);
        for (var j = 0; j < names.length; j++) {
            if (calendar.seasons[names[j]].indexOf(month) !== -1) {
                season = names[j];
                break;
            }
        }
        return {
            date: "Year " + (part.year + 1) + ", " + calendar.month_names[part.month] + " "
                + (part.week * 7 + part.day + 1),
            time: pad2(part.hour) + ":" + pad2(part.min) + " (" + period + ")",
            season: season,
            period: period,
        };
    }

    // Lock 1: the weather icon's day or night half follows the period.
    function weatherIcon(weather, period) {
        if (WEATHER_KEYS.indexOf(weather) === -1) {
            return null;
        }
        return (NIGHT_PERIODS.indexOf(period) === -1 ? "weather_day_" : "weather_night_") + weather;
    }

    function seasonIcon(season) {
        return SEASON_KEYS.indexOf(season) === -1 ? null : "season_" + season;
    }

    // Lock 4A: a known room, outdoors.
    function showWeather(room) {
        return !!room && room.name !== null && !room.indoor;
    }

    function start() {
        if (!document.getElementById("pw-world")) {
            return;   // a page without the panel
        }
        var world = null;
        var received = 0;
        var room = null;
        var shown = {};   // row -> text last written, null when hidden
        var icons = {};   // row -> data-icon last written, null when none

        function write(key, text) {
            if (shown[key] === text) {
                return;
            }
            shown[key] = text;
            document.getElementById("pw-world-" + key).hidden = text === null;
            if (text !== null) {
                document.getElementById("pw-world-" + key + "-value").textContent = text;
            }
        }

        // Lock 5: no name, no attribute.
        function writeIcon(key, name) {
            if (icons[key] === name) {
                return;
            }
            icons[key] = name;
            var row = document.getElementById("pw-world-" + key);
            if (name === null) {
                row.removeAttribute("data-icon");
            } else {
                row.setAttribute("data-icon", name);
            }
        }

        function draw() {
            if (world === null) {
                return;
            }
            var view = worldView(gameSecondsAt(world, received, performance.now()), world.calendar);
            view.weather = showWeather(room) ? String(world.weather) : null;
            ROWS.forEach(function (key) {
                write(key, view[key]);
            });
            writeIcon("season", seasonIcon(view.season));
            writeIcon("weather", view.weather === null ? null : weatherIcon(view.weather, view.period));
        }

        pw_state.on("world", function (snapshot) {
            world = snapshot;
            received = performance.now();
            draw();
        });
        pw_state.on("room", function (snapshot) {
            room = snapshot;
            draw();
        });
        setInterval(draw, 1000);
    }

    if (typeof module !== "undefined" && module.exports) {
        module.exports = {
            worldView: worldView, gameSecondsAt: gameSecondsAt, showWeather: showWeather,
            weatherIcon: weatherIcon, seasonIcon: seasonIcon,
            WEATHER_KEYS: WEATHER_KEYS, SEASON_KEYS: SEASON_KEYS, NIGHT_PERIODS: NIGHT_PERIODS,
        };
    }
    if (typeof pw_state !== "undefined" && typeof document !== "undefined") {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", start);
        } else {
            start();
        }
    }
})();
