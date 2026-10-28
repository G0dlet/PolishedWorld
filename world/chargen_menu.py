"""
Character creation menu: Points Build, then profession (Character Creation,
Task CC3.1).

    node_allocate -> node_confirm_allocation -> node_profession
                  -> node_confirm_profession -> node_done

Started with `EvMenu(character, "world.chargen_menu",
startnode="node_allocate")`. Launching it on puppet, with `persistent=True`
and `auto_quit=False`, and resuming it after a disconnect or a reload, is
`chargen.start_or_resume_chargen()`'s job (CC3.2), not this module's.

HOW THE MODULE IS READ
----------------------
EvMenu turns every *function* in this module's namespace whose name does not
start with `_` into a node -- including functions imported by name (6.1.0,
`EvMenu._parse_menudata`). So the only public functions here are the five
nodes, helpers carry a leading underscore, and `world.chargen` and
`world.professions` are imported as modules, never `from ... import func`.

WHERE THE STATE LIVES
---------------------
The draft allocation and the chosen profession travel in goto kwargs from
node to node. A persistent EvMenu saves `(nodename, (raw_string, kwargs))`
after every step, so kwargs survive a reload; attributes on
`caller.ndb._evmenu` do not. Nothing else is stored until the last node.

ONE PLACE WRITES
----------------
`node_done` is the only node that changes the character, so leaving the menu
anywhere before it -- `quit`, a disconnect, a crash -- changes nothing. The
rules have one home each: `chargen.validate_allocation()` judges the draft,
`chargen.derive_skill_bases()` and `chargen.derive_health_max()` make the
numbers the confirmation screens show, and `chargen.apply_allocation()` /
`professions.grant_profession()` write them.

Multiplayer: menu state is per caller (kwargs, or the caller's own Attributes
in persistent mode), and every write is to the caller inside one command on
Twisted's single thread, so ten characters in the menu at once share nothing.
"""

import re

from evennia.utils import logger

from world import chargen
from world import professions

# Every characteristic starts at Legend's human average, as at_object_creation
# makes them; 70 of the 80 points are then already placed.
_START_VALUE = 10

# Legend p.5-7, paraphrased to one line each.
_DESCRIPTIONS = {
    "str": "Raw muscle: how much you can lift, push or grip.",
    "dex": "Co-ordination and agility: quick hands, keen eye, light feet.",
    "con": "Health and vitality: how much punishment and weariness you take.",
    "siz": "Bulk and mass: what you can reach over or squeeze through.",
    "int": "How well you learn, reason and put what you know to use.",
    "pow": "Force of will and soul, the root of any magic.",
    "cha": "Force of personality: being heard, noticed and followed.",
}

_INT_TOKEN = re.compile(r"[+-]?\d+")

_ALLOCATE_HELP = (
    "Set characteristics with name-number pairs, one or several per line:\n"
    "  str 12\n"
    "  str 12 dex 14\n"
    "or all seven at once, in the order STR DEX CON SIZ INT POW CHA:\n"
    "  12 14 10 9 13 11 11\n"
    "Each must be 6-18 and all 80 points spent. Type 'next' when the list of "
    "things to fix is empty."
)


def _start_draft():
    """A fresh draft: every characteristic at the starting value."""
    return {key: _START_VALUE for key in chargen.STAT_KEYS}


def _feeds(stat):
    """What reads this characteristic in the alpha, for the allocate screen."""
    readers = [
        skill
        for skill, pair in chargen.SKILL_BASE_PAIRS.items()
        if stat in pair
    ]
    if stat == "con":
        readers.append("health")
    if not readers:
        return "Nothing reads it yet."
    return "Feeds " + ", ".join(readers) + "."


def _parse_line(text, draft):
    """
    Read one line of allocate input against a draft.

    Only the *form* is checked here: names, whole numbers, how many. Whether
    the values are legal (6-18, 80 spent) is `validate_allocation`'s job, so a
    line like `str 25` is accepted into the draft and the screen then lists
    the violation -- one home for the rules.

    Args:
        text (str): the raw line, any case.
        draft (Mapping): the current draft. Never mutated.

    Returns:
        tuple: `(new_draft, error)`. On an error, `new_draft` equals `draft`
            and `error` is a message; otherwise `error` is None.
    """
    unchanged = dict(draft)
    tokens = text.lower().split()
    if not tokens:
        return unchanged, "Nothing to read -- type 'help' for the forms."

    if all(_INT_TOKEN.fullmatch(token) for token in tokens):
        if len(tokens) != len(chargen.STAT_KEYS):
            return unchanged, (
                f"A line of numbers needs all {len(chargen.STAT_KEYS)} "
                f"({' '.join(k.upper() for k in chargen.STAT_KEYS)}); "
                f"got {len(tokens)}."
            )
        return dict(zip(chargen.STAT_KEYS, (int(t) for t in tokens))), None

    if len(tokens) % 2:
        return unchanged, "Pairs come as a name and a number, e.g. 'str 12'."

    new = dict(draft)
    for name, value in zip(tokens[::2], tokens[1::2]):
        if name not in chargen.STAT_KEYS:
            return unchanged, (
                f"Unknown characteristic '{name}'; use one of "
                f"{', '.join(chargen.STAT_KEYS)}."
            )
        if not _INT_TOKEN.fullmatch(value):
            return unchanged, (
                f"{name.upper()} needs a whole number, not '{value}'."
            )
        new[name] = int(value)
    return new, None


def _stat_row(draft):
    """`STR 7  DEX 9 ...` on one line."""
    return "  ".join(f"{key.upper()} {draft[key]}" for key in chargen.STAT_KEYS)


def _goto_parse(caller, raw_string, **kwargs):
    """`_default` on allocate: fold the line into the draft, stay."""
    new, error = _parse_line(raw_string, kwargs.get("draft") or _start_draft())
    return "node_allocate", {"draft": new, "notice": error}


def _goto_confirm_allocation(caller, raw_string, **kwargs):
    """`next` on allocate: go on only when the draft is legal."""
    draft = kwargs.get("draft") or _start_draft()
    if chargen.validate_allocation(draft):
        return "node_allocate", {
            "draft": draft,
            "notice": "Not yet -- fix the list below first.",
        }
    return "node_confirm_allocation", {"draft": draft}


def _back_to_allocation(draft):
    """
    The one way on from a refusal that leaves the character unmade (CC3.2).

    Closing the menu there would release a pending character into the world
    until its next puppet -- the gate would leak. Back to the allocation with
    the draft, so the player can try again.
    """
    return {
        "key": ("back", "b"),
        "desc": "return to your characteristics",
        "goto": ("node_allocate", {"draft": draft}),
    }


def _half_done(character, reason):
    """The honest message when the stats landed but the profession did not."""
    logger.log_err(
        f"chargen: {character.key}'s characteristics were applied but the "
        f"profession was not ({reason}); chargen_complete not set."
    )
    return (
        "Your characteristics are set, but your profession could not be "
        f"granted ({reason}). Character creation is not complete: go back and "
        "confirm again, and if this repeats, tell a builder."
    )


def node_allocate(caller, raw_string, **kwargs):
    """Spend 80 points over seven characteristics, each 6-18."""
    draft = dict(kwargs.get("draft") or _start_draft())
    notice = kwargs.get("notice")

    lines = ["|wCharacteristics|n -- spend 80 points, each 6-18.", ""]
    for key in chargen.STAT_KEYS:
        lines.append(
            f"  |w{key.upper()}|n {draft[key]:>3}  {_DESCRIPTIONS[key]} "
            f"{_feeds(key)}"
        )
    total = sum(draft[key] for key in chargen.STAT_KEYS)
    lines += ["", f"Spent {total} of {chargen.DESIGN_POINTS}."]

    errors = chargen.validate_allocation(draft)
    if errors:
        lines += ["", "To fix before 'next':"]
        lines += [f"  - {error}" for error in errors]
    else:
        lines += ["", "All points placed. Type 'next' to see the result."]
    if notice:
        lines += ["", f"|y{notice}|n"]
    lines += ["", "Type e.g. 'str 12', or 'help'."]

    options = (
        {
            "key": ("next", "n"),
            "desc": "see the resulting character",
            "goto": (_goto_confirm_allocation, {"draft": draft}),
        },
        {"key": "_default", "goto": (_goto_parse, {"draft": draft})},
    )
    return ("\n".join(lines), _ALLOCATE_HELP), options


def node_confirm_allocation(caller, raw_string, **kwargs):
    """Show what the allocation makes: health max and the five skill bases."""
    draft = dict(kwargs.get("draft") or _start_draft())
    back = {
        "key": ("back", "b"),
        "desc": "change the characteristics",
        "goto": ("node_allocate", {"draft": draft}),
    }
    errors = chargen.validate_allocation(draft)
    if errors:
        # Only reachable through a stale saved menu; show why, offer back.
        return "This allocation is not legal:\n  " + "\n  ".join(errors), (back,)

    bases = chargen.derive_skill_bases(draft)
    text = "\n".join(
        [
            "|wYour characteristics|n",
            "  " + _stat_row(draft),
            "",
            f"Health max: {chargen.derive_health_max(draft['con'])}",
            "Skill bases: "
            + ", ".join(f"{skill} {base}" for skill, base in bases.items()),
            "",
            "Keep these and choose a profession?",
        ]
    )
    options = (
        {
            "key": ("yes", "y"),
            "desc": "choose a profession",
            "goto": ("node_profession", {"draft": draft}),
        },
        back,
    )
    return text, options


def node_profession(caller, raw_string, **kwargs):
    """The four packages, with their recipes and skill bonus."""
    draft = dict(kwargs.get("draft") or _start_draft())
    lines = ["|wChoose a profession|n -- it cannot be changed later.", ""]
    options = []
    for key, package in professions.PROFESSIONS.items():
        bonus = ", ".join(
            f"{skill} +{points}"
            for skill, points in package["skill_bonus"].items()
        )
        recipes = ", ".join(package["recipes"])
        lines.append(f"  |w{key:<11}|n {recipes}  ({bonus})")
        options.append(
            {
                "key": key,
                "desc": f"{recipes} ({bonus})",
                "goto": (
                    "node_confirm_profession",
                    {"draft": draft, "profession": key},
                ),
            }
        )
    options.append(
        {
            "key": ("back", "b"),
            "desc": "back to your characteristics",
            "goto": ("node_confirm_allocation", {"draft": draft}),
        }
    )
    return "\n".join(lines), tuple(options)


def node_confirm_profession(caller, raw_string, **kwargs):
    """Show the profession's effect on this character before the final yes."""
    draft = dict(kwargs.get("draft") or _start_draft())
    key = kwargs.get("profession")
    back = {
        "key": ("back", "b"),
        "desc": "choose another profession",
        "goto": ("node_profession", {"draft": draft}),
    }
    package = professions.PROFESSIONS.get(key)
    if package is None:
        # Only reachable through a stale saved menu.
        return f"There is no profession '{key}'.", (back,)

    bases = chargen.derive_skill_bases(draft)
    lines = [f"|w{key.capitalize()}|n", ""]
    for skill, points in package["skill_bonus"].items():
        lines.append(
            f"  {skill} {bases[skill]} -> {bases[skill] + points} (+{points})"
        )
    lines += [
        "  Recipes: " + ", ".join(package["recipes"]),
        "",
        "  " + _stat_row(draft),
        "",
        "This cannot be changed. Create this character?",
    ]
    options = (
        {
            "key": ("yes", "y"),
            "desc": "create the character",
            "goto": ("node_done", {"draft": draft, "profession": key}),
        },
        back,
    )
    return "\n".join(lines), options


def node_done(caller, raw_string, **kwargs):
    """
    Every write, in one place; on success, close the menu.

    Order: refuse a finished character (this node writes the flag, so the
    guard lives here -- the helpers' own refusals key on other stamps);
    refuse an unknown profession; `apply_allocation` (refuses before its first
    write); `grant_profession`; the flag; the `progress` baseline. A refusal
    by `apply_allocation` changes nothing. A refusal by `grant_profession`
    after the stats landed leaves the flag not set: the character has no
    profession and no banked XP, so going `back` and confirming again may
    apply again.
    Returning no options closes the menu, and `cmd_on_exit` shows the room:
    that happens on success and for a character already made. Every other
    refusal keeps the menu open with one option, `back` to the allocation
    (CC3.2 -- a closed menu would let an unmade character into the world).
    """
    draft = kwargs.get("draft")
    key = kwargs.get("profession")

    if caller.db.chargen_complete:
        return "Your character is already made; nothing was changed.", None
    if key not in professions.PROFESSIONS:
        return (
            f"Nothing was changed: there is no profession '{key}'.",
            _back_to_allocation(draft),
        )

    try:
        chargen.apply_allocation(caller, draft)
    except ValueError as err:
        return f"Nothing was changed: {err}", _back_to_allocation(draft)

    try:
        professions.grant_profession(caller, key)
    except ValueError as err:
        return _half_done(caller, str(err)), _back_to_allocation(draft)
    if caller.db.profession != key:
        return _half_done(caller, "the grant was refused"), _back_to_allocation(draft)

    caller.db.chargen_complete = True
    caller.snapshot_skill_baseline()
    return (
        f"Your character is made. You follow the {key}'s trade; the world "
        "is yours to make something of."
    ), None
