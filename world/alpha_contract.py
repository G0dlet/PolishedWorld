"""
The cohort contract, in player words (Launch Minimum LM7, task L4.2).

A closed alpha asks invited players to spend real weeks in a world that will
be wiped. LM7 decides what they are told before they agree to that, and in
which order: the world is wiped at close-out; how death works (`help death`);
every economic act is logged; some accounts are automated test players
(decomposition Rev 2); GameGold is not part of the alpha and nothing minted is
a promise of value; a wipe before close-out is announced ahead; how to reach
staff.

Two surfaces carry it, and both read from HERE so they cannot drift apart:

    help alpha          `help_entry()`, listed in `world/help_entries.py`
    connection screen   `CONNECTION_LINE`, in `server/conf/connection_screens.py`

The text carries no number that goes stale. The alpha's length and its
close-out checks live in the roadmap (LM10), where they are decided; the one number here,
the seven days of a wipe notice, is the rule itself, not a schedule.

This module imports nothing from Django or Evennia on purpose: the connection
screen imports it at server start, and a failing import there takes the login
screen with it.
"""

WIPE_NOTICE_DAYS = 7

# Shown before login. Plain text plus colour codes: the connection screen
# module runs its string through `str.format()`, so no braces here.
CONNECTION_LINE = "|wThis is a closed alpha - read |yhelp alpha|w after you log in.|n"


def help_text():
    """The full `help alpha` text, one claim per paragraph, in LM7's order."""
    return (
        "This is a closed alpha: a small, invited group testing the world "
        "before it opens.\n\n"
        "|wThe world is wiped when the alpha ends.|n Characters, everything "
        "they carry and everything they made are gone. Nothing carries over.\n\n"
        "|wDeath|n has consequences here. Read |whelp death|n before you take "
        "risks.\n\n"
        "|wEvery economic act is logged|n: gathering, crafting, trading, "
        "working, eating and drinking, repairing, learning and improving a "
        "skill. Staff read the log to see how the game is played.\n\n"
        "|wSome accounts are automated test players|n, run by staff. They "
        "follow the same rules as you, and they are left out when staff read "
        "the log.\n\n"
        "|wGameGold is not part of the alpha.|n Coin here is game coin. "
        "Nothing minted, earned or traded in the alpha is a promise of value "
        "outside it.\n\n"
        "|wUpdates during the alpha keep your character.|n If a change ever "
        "cannot, the world is wiped early instead, and that is announced at "
        f"least {WIPE_NOTICE_DAYS} days ahead on the connection screen and in "
        "this entry.\n\n"
        "|wTo reach staff|n, use |wpage <name> = <message>|n; your invitation "
        "names the staff accounts. For anything the whole group may hit, say "
        "it on the Public channel: |wpub <message>|n."
    )


def help_entry():
    """The file-help dict for `world/help_entries.py`."""
    return {
        "key": "alpha",
        "aliases": ["cohort", "contract"],
        "category": "General",
        "text": help_text(),
    }
