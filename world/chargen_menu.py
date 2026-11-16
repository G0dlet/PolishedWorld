"""
Character creation menu: Points Build, then profession (Character Creation,
Task CC3.1), then the body strangers see (Names NM-T16; OQ-NM9).

    node_allocate -> node_confirm_allocation -> node_profession
                  -> node_confirm_profession -> node_appearance
                  -> node_confirm_appearance -> node_done

Started with `EvMenu(character, "world.chargen_menu",
startnode="node_allocate")`. Launching it on puppet, with `persistent=True`
and `auto_quit=False`, and resuming it after a disconnect or a reload, is
`chargen.start_or_resume_chargen()`'s job (CC3.2), not this module's.

HOW THE MODULE IS READ
----------------------
EvMenu turns every *function* in this module's namespace whose name does not
start with `_` into a node -- including functions imported by name (6.1.0,
`EvMenu._parse_menudata`). So the only public functions here are the seven
nodes, helpers carry a leading underscore, and `world.chargen`,
`world.professions` and `world.sdesc` are imported as modules, never
`from ... import func`.

WHERE THE STATE LIVES
---------------------
The draft allocation, the chosen profession and the appearance choices
travel in goto kwargs from node to node. A persistent EvMenu saves
`(nodename, (raw_string, kwargs))` after every step, so kwargs survive a
reload; attributes on `caller.ndb._evmenu` do not. Nothing else is stored
until the last node. The appearance choices ride in their own kwarg,
`appearance`, not in the draft: `validate_allocation` refuses a draft with
keys that are not characteristics. They travel between the profession's
confirmation and the last node; going back past the profession's
confirmation leaves them behind, and the step asks again.

ONE PLACE WRITES
----------------
`node_done` is the only node that changes the character, so leaving the menu
anywhere before it -- `quit`, a disconnect, a crash -- changes nothing. The
rules have one home each: `chargen.validate_allocation()` judges the draft,
`chargen.derive_skill_bases()` and `chargen.derive_health_max()` make the
numbers the confirmation screens show, and `chargen.apply_allocation()` /
`professions.grant_profession()` write them. The appearance's vocabulary is
`world.sdesc`'s, and so is the line its confirmation shows
(`sdesc.compose_text`, without state or garment); `node_done` writes the
facts as `db.appearance`, which `Character.sdesc` composes from from then on.

Multiplayer: menu state is per caller (kwargs, or the caller's own Attributes
in persistent mode), and every write is to the caller inside one command on
Twisted's single thread, so ten characters in the menu at once share nothing.
"""

import re
from collections.abc import Mapping

from evennia.utils import logger

from world import arrival
from world import chargen
from world import client_state
from world import professions
from world import sdesc

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

# The three appearance choices, in the order a line of three gives them
# (Names NM-T16), each with its vocabulary in the order the screen numbers it.
_APPEARANCE_FIELDS = ("sex", "age", "feature")
_APPEARANCE_CHOICES = {
    "sex": sdesc.SEXES,
    "age": sdesc.AGES,
    "feature": sdesc.FEATURES,
}
# What each sex is spoken of as (Names NM-T15b: `Character.gender`).
_PRONOUNS = {"male": "he", "female": "she", "unstated": "they"}
_FEATURE_COLUMNS = 4

_APPEARANCE_HELP = (
    "Choose by number or by word, one or several per line:\n"
    "  sex 2\n"
    "  feature freckled\n"
    "  age 2 feature 11\n"
    "or all three at once, in the order sex, age, feature:\n"
    "  2 2 11\n"
    "Your build is not chosen: it follows the SIZ you set. Type 'next' when "
    "all three are chosen, or 'back' to return to your profession."
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


def _pick(field, token):
    """
    One appearance value from its number on the screen or its word.

    Returns:
        tuple: `(word, error)`; exactly one of them is None.
    """
    choices = _APPEARANCE_CHOICES[field]
    if _INT_TOKEN.fullmatch(token):
        number = int(token)
        if 1 <= number <= len(choices):
            return choices[number - 1], None
        return None, f"There is no {field} {number}; choose 1-{len(choices)}."
    if token in choices:
        return token, None
    return None, f"'{token}' is not a {field} on the list."


def _parse_appearance(text, choices):
    """
    Read one line of appearance input against the choices made so far.

    As `_parse_line`: a value outside the lists rejects the whole line and
    changes nothing. Unlike the allocation, there is no rule beyond the lists,
    so a number out of range is refused here, at once.

    Args:
        text (str): the raw line, any case.
        choices (Mapping): field -> word chosen so far. Never mutated.

    Returns:
        tuple: `(new_choices, error)`. On an error, `new_choices` equals
            `choices` and `error` is a message; otherwise `error` is None.
    """
    unchanged = dict(choices)
    tokens = text.lower().split()
    if not tokens:
        return unchanged, "Nothing to read -- type 'help' for the forms."

    if tokens[0] in _APPEARANCE_FIELDS:
        if len(tokens) % 2:
            return unchanged, "Pairs come as a name and a choice, e.g. 'sex 2'."
        pairs = list(zip(tokens[::2], tokens[1::2]))
    else:
        if len(tokens) != len(_APPEARANCE_FIELDS):
            return unchanged, (
                f"A line of choices needs all {len(_APPEARANCE_FIELDS)} "
                f"({', '.join(_APPEARANCE_FIELDS)}); got {len(tokens)}."
            )
        pairs = list(zip(_APPEARANCE_FIELDS, tokens))

    new = dict(choices)
    for field, token in pairs:
        if field not in _APPEARANCE_FIELDS:
            return unchanged, (
                f"Unknown choice '{field}'; use one of "
                f"{', '.join(_APPEARANCE_FIELDS)}."
            )
        word, error = _pick(field, token)
        if error:
            return unchanged, error
        new[field] = word
    return new, None


def _choices(kwargs):
    """
    The appearance choices in a node's kwargs, as a new dict holding only the
    fields whose value is on its list. A menu saved before NM-T16 has none,
    and anything else stored there is left out, so the step asks for it again
    instead of showing a choice `next` would refuse.
    """
    stored = kwargs.get("appearance")
    if not isinstance(stored, Mapping):
        return {}
    return {
        field: stored[field]
        for field in _APPEARANCE_FIELDS
        if stored.get(field) in _APPEARANCE_CHOICES[field]
    }


def _complete_appearance(choices):
    """
    The three appearance facts when every one is chosen from the lists, as a
    new dict; else None (none chosen yet, a menu saved before NM-T16, or a
    value the lists no longer hold).
    """
    try:
        facts = {field: choices[field] for field in _APPEARANCE_FIELDS}
    except (TypeError, KeyError):
        return None
    if any(facts[field] not in _APPEARANCE_CHOICES[field] for field in facts):
        return None
    return facts


def _siz(draft):
    """The draft's SIZ, the build's source; the starting value for a stale draft."""
    try:
        return int(draft["siz"])
    except (TypeError, KeyError, ValueError):
        return _START_VALUE


def _goto_parse_appearance(caller, raw_string, **kwargs):
    """`_default` on the appearance step: fold the line into the choices, stay."""
    new, error = _parse_appearance(raw_string, _choices(kwargs))
    return "node_appearance", dict(kwargs, appearance=new, notice=error)


def _goto_confirm_appearance(caller, raw_string, **kwargs):
    """`next` on the appearance step: go on only when all three are chosen."""
    if _complete_appearance(_choices(kwargs)) is None:
        return "node_appearance", dict(
            kwargs, notice="Not yet -- choose all three first."
        )
    return "node_confirm_appearance", dict(kwargs, notice=None)


def _back_to_appearance(draft, profession, appearance):
    """
    The way on from a later node reached without the appearance (NM-T16).

    A menu saved before this task stood at the profession's confirmation or
    at `node_done` with no choices; as `_back_to_allocation`, the menu stays
    open, and the player chooses before anything is written.
    """
    return {
        "key": ("back", "b"),
        "desc": "choose how strangers see you",
        "goto": (
            "node_appearance",
            {"draft": draft, "profession": profession, "appearance": appearance},
        ),
    }


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
        "Keep this profession and choose how strangers see you?",
    ]
    options = (
        {
            "key": ("yes", "y"),
            "desc": "choose how strangers see you",
            "goto": (
                "node_appearance",
                {
                    "draft": draft,
                    "profession": key,
                    "appearance": _choices(kwargs),
                },
            ),
        },
        back,
    )
    return "\n".join(lines), options


def node_appearance(caller, raw_string, **kwargs):
    """
    Choose, once, the body strangers see: sex, age and one feature (OQ-NM9 (1)).

    The build is shown and not chosen: it is read from the draft's SIZ, as
    the composer reads `stats.siz` once the character is made.
    """
    draft = dict(kwargs.get("draft") or _start_draft())
    profession = kwargs.get("profession")
    choices = _choices(kwargs)
    notice = kwargs.get("notice")
    siz = _siz(draft)

    lines = [
        "|wHow strangers see you|n -- chosen once.",
        "",
        f"Your build follows your SIZ: SIZ {siz} reads as "
        f"{sdesc.build_for(siz)}.",
        "",
        "|wSex|n",
        "  " + "   ".join(
            f"{number} {sex} ({_PRONOUNS[sex]})"
            for number, sex in enumerate(sdesc.SEXES, 1)
        ),
        "|wAge|n",
        "  " + "   ".join(
            f"{number} {age}" for number, age in enumerate(sdesc.AGES, 1)
        ),
        "|wFeature|n",
    ]
    features = list(enumerate(sdesc.FEATURES, 1))
    for start in range(0, len(features), _FEATURE_COLUMNS):
        row = features[start:start + _FEATURE_COLUMNS]
        lines.append(
            "".join(f"{number:>3} {word:<14}" for number, word in row).rstrip()
        )

    lines += ["", "Chosen: " + ", ".join(
        f"{field} {choices.get(field, '--')}" for field in _APPEARANCE_FIELDS
    ) + "."]
    missing = [field for field in _APPEARANCE_FIELDS if field not in choices]
    if missing:
        lines.append("Still to choose: " + ", ".join(missing) + ".")
    else:
        lines.append("All three chosen. Type 'next' to see how you read.")
    if notice:
        lines += ["", f"|y{notice}|n"]
    lines += ["", "Type e.g. 'sex 2', 'feature freckled', or 'help'."]

    carried = {"draft": draft, "profession": profession, "appearance": choices}
    options = (
        {
            "key": ("next", "n"),
            "desc": "see how strangers will read you",
            "goto": (_goto_confirm_appearance, carried),
        },
        {
            "key": ("back", "b"),
            "desc": "back to your profession",
            "goto": ("node_confirm_profession", carried),
        },
        {"key": "_default", "goto": (_goto_parse_appearance, carried)},
    )
    return ("\n".join(lines), _APPEARANCE_HELP), options


def node_confirm_appearance(caller, raw_string, **kwargs):
    """The short description these choices and this SIZ give, before the final yes."""
    draft = dict(kwargs.get("draft") or _start_draft())
    profession = kwargs.get("profession")
    choices = _choices(kwargs)
    back = _back_to_appearance(draft, profession, choices)
    facts = _complete_appearance(choices)
    if facts is None:
        # Only reachable through a stale saved menu.
        return "Choose how strangers see you first.", (back,)

    # The body without the moment: no state, no garment (OQ-NM9 (1)).
    line = sdesc.compose_text(
        facts["sex"], facts["age"], facts["feature"], _siz(draft)
    )
    text = "\n".join(
        [
            "|wHow strangers see you|n",
            "",
            "Strangers will read you as:",
            "",
            f"  {line}",
            "",
            "What you wear shows too, and so does exhaustion or a heavy load.",
            "",
            "This cannot be changed here. Create this character?",
        ]
    )
    options = (
        {
            "key": ("yes", "y"),
            "desc": "create the character",
            "goto": (
                "node_done",
                {"draft": draft, "profession": profession, "appearance": facts},
            ),
        },
        back,
    )
    return text, options


def node_done(caller, raw_string, **kwargs):
    """
    Every write, in one place; on success, close the menu.

    Order: refuse a finished character (this node writes the flag, so the
    guard lives here -- the helpers' own refusals key on other stamps);
    refuse an unknown profession; refuse a draft without the three appearance
    choices (a menu saved before Names NM-T16) and send it to the appearance
    step; `apply_allocation` (refuses before its first write);
    `grant_profession`; the appearance facts (`db.appearance`, after every
    refusal, so a refused or half-done character keeps none and chooses
    again on the way back); the flag; the `progress` baseline; arrival
    (`arrival.arrive`: the arrival room becomes location and home, Arrival
    AV-T2; the room reads the newcomer by the description just composed);
    the push of all four panels, after the move so the Location panel shows
    where the character now stands (AV5). A refusal by
    `apply_allocation` changes nothing. A refusal by `grant_profession` after
    the stats landed leaves the flag not set: the character has no profession
    and no banked XP, so going `back` and confirming again may apply again.
    Returning no options closes the menu, and `cmd_on_exit` shows the room:
    that happens on success and for a character already made. Every other
    refusal keeps the menu open with one option, `back` to the allocation,
    or to the appearance step for a draft without it (CC3.2 -- a closed menu
    would let an unmade character into the world).
    Arrival never blocks the flag: on a database without the arrival room,
    or if the move fails, `arrive` logs and the character is made where it
    stands (AV6).
    """
    draft = kwargs.get("draft")
    key = kwargs.get("profession")
    facts = _complete_appearance(_choices(kwargs))

    if caller.db.chargen_complete:
        return "Your character is already made; nothing was changed.", None
    if key not in professions.PROFESSIONS:
        return (
            f"Nothing was changed: there is no profession '{key}'.",
            _back_to_allocation(draft),
        )
    if facts is None:
        return (
            "Nothing was changed: choose how strangers see you first.",
            _back_to_appearance(draft, key, _choices(kwargs)),
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

    # Names NM-T16: before arrival, so the room reads the newcomer by the
    # composed text, and before the push (AV5). A character without facts is
    # never memoised; the forget is for a text read before this write anyway.
    caller.db.appearance = facts
    caller.sdesc.forget()
    caller.db.chargen_complete = True
    caller.snapshot_skill_baseline()
    # Arrival AV-T2: after every refusal, before the push (AV5). Never raises.
    arrival.arrive(caller)
    # W4.2: at_post_puppet pushed the placeholder values; these are final.
    client_state.push(caller, *client_state.DOMAINS)
    return (
        f"Your character is made. You follow the {key}'s trade; the world "
        "is yours to make something of."
    ), None
