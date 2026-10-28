"""
Legend character creation: Points Build validation, derived skill bases, and
applying an allocation to a character (Character Creation, Task CC1.1).

Everything but `apply_allocation()` is pure -- no database, no typeclass --
which is why it is testable with `EvenniaTestCase`. `apply_allocation()` is
the one stateful entry point and the only code in the project that re-bases
a character's characteristics.

THE RULE (Legend p.9, Points Build; decision CC1)
-------------------------------------------------
80 Characteristic Design Points over the seven characteristics, 1 point per
point, each characteristic 6-18, every point spent. p.9's optional rule that
buys values above 18 at 2 points each is NOT adopted: the ladder's rung 20 is
meant to be a choice, not something a build can purchase past. The constants
below are rules, not balance knobs, which is why they live here and not in
settings.

DERIVED SKILL BASES (decision CC5, Legend p.13-14)
--------------------------------------------------
Athletics STR+DEX, Perception INT+POW, Stealth DEX+INT and Craft DEX+INT are
Legend's own. Hunting is the project's skill; its pair is Legend's Track
(INT+CON, p.65) -- the closest canonical analogue, a pair no other skill uses,
and CON's only skill reader (OQ1, locked 2026-10-26). Derivation reads the
allocation's integers, never a trait's `.value`: a StaticTrait's value is
`(base + mod) * mult` with `mult = 1.0`, i.e. a float.

WHAT `apply_allocation()` DOES NOT DO
-------------------------------------
It writes nothing to `skill_xp` (CC5/CC7: derive, never backfill). An absent
XP entry is derived on read from the skill's `.current`, so the floor follows
the new base with no write. A *present* entry would not follow: lowering a
skill below a banked total lets the next improvement re-derive the old level
from the old XP. That is why a character with banked XP is refused -- CC7's
"no re-spec" enforced in code rather than only in prose.

Multiplayer: everything happens inside one call on one character, on
Twisted's single-threaded reactor, with MULTISESSION_MODE 0. No two writers
can meet on the same character, so no locking is needed. All checks run before
the first write, so a refused call leaves the character exactly as it was.
"""

from collections.abc import Mapping

from evennia.utils import logger
from evennia.utils.evmenu import EvMenu

# Legend p.9 -- rules, not knobs.
DESIGN_POINTS = 80
CHAR_MIN = 6
CHAR_MAX = 18

# The seven characteristics, keyed as in Character.at_object_creation.
STAT_KEYS = ("str", "dex", "con", "siz", "int", "pow", "cha")

# Skill -> the two characteristics its base is the sum of (CC5, OQ1).
SKILL_BASE_PAIRS = {
    "athletics": ("str", "dex"),
    "perception": ("int", "pow"),
    "stealth": ("dex", "int"),
    "craft": ("dex", "int"),
    "hunting": ("int", "con"),
}

# The Attribute SkillXPHandler stores banked XP in (typeclasses/characters.py,
# Character.skill_xp). Read directly: `skill_xp.all()` also lists *derived*
# entries, so it is never empty and cannot answer "has anything been banked?".
SKILL_XP_ATTRIBUTE = "skill_xp"


def _is_plain_int(value):
    """
    True for an int that is not a bool.

    `bool` subclasses `int`, so `isinstance(True, int)` is True -- and
    StaticTrait's base setter accepts it as 1. A str such as "12" is the
    opposite trap: the setter ignores it silently and leaves the old base.
    Both must be refused here, before anything reaches a trait.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def validate_allocation(alloc):
    """
    Check a Points Build allocation against Legend p.9.

    Every violation is reported, so a menu can print them all at once.

    Args:
        alloc (Mapping): characteristic key -> value, e.g. {"str": 12, ...}.
            Any Mapping is accepted, including Evennia's `_SaverDict`.

    Returns:
        list[str]: human-readable violations; empty means valid.
    """
    if not isinstance(alloc, Mapping):
        return [
            "An allocation must map each characteristic to a value, "
            f"not be a {type(alloc).__name__}."
        ]

    errors = []

    missing = [key for key in STAT_KEYS if key not in alloc]
    if missing:
        errors.append(
            "Missing characteristic(s): "
            + ", ".join(key.upper() for key in missing) + "."
        )

    unknown = [key for key in alloc if key not in STAT_KEYS]
    if unknown:
        errors.append(
            "Unknown characteristic(s): "
            + ", ".join(repr(key) for key in unknown) + "."
        )

    all_ints = True
    for key in STAT_KEYS:
        if key not in alloc:
            continue
        value = alloc[key]
        if not _is_plain_int(value):
            all_ints = False
            errors.append(f"{key.upper()} must be a whole number, not {value!r}.")
        elif not CHAR_MIN <= value <= CHAR_MAX:
            errors.append(
                f"{key.upper()} is {value}; a characteristic must be "
                f"{CHAR_MIN}-{CHAR_MAX}."
            )

    # The total is only meaningful when all seven are present integers;
    # otherwise it would be noise on top of the real error.
    if not missing and all_ints:
        total = sum(alloc[key] for key in STAT_KEYS)
        if total < DESIGN_POINTS:
            errors.append(
                f"{total} of {DESIGN_POINTS} points spent -- "
                f"{DESIGN_POINTS - total} left to spend."
            )
        elif total > DESIGN_POINTS:
            errors.append(
                f"{total} points spent -- {total - DESIGN_POINTS} over "
                f"the {DESIGN_POINTS} available."
            )

    return errors


def derive_skill_bases(stats):
    """
    Derive each common skill's base from the characteristics (CC5).

    Pure: reads the mapping, writes nothing, does not validate. Pass a
    validated allocation; integers in give integers out.

    Args:
        stats (Mapping): characteristic key -> value.

    Returns:
        dict: skill key -> base, e.g. {"athletics": 16, ...}.
    """
    return {
        skill: stats[first] + stats[second]
        for skill, (first, second) in SKILL_BASE_PAIRS.items()
    }



def derive_health_max(con):
    """
    Hit Points maximum from Constitution (decision CC9: CON x 2).

    The one home of the formula: `Character.at_object_creation`,
    `Character.update_health_max()` and the chargen menu's confirmation
    screen all call it, so the number the player is shown is the number the
    character gets. Legend's CON+SIZ table belongs to hit locations (p.11,
    Stage 5). Integers in give integers out; a trait's `.value` is a float.

    Args:
        con (int or float): the Constitution value.

    Returns:
        int or float: the maximum, the same type as `con`.
    """
    return con * 2

def apply_allocation(character, alloc):
    """
    Re-base a fresh character's characteristics, health and skills.

    All checks run before the first write. Then: each characteristic's
    `.base` (StaticTrait -- it has no `.current`, and a written `.current`
    would be stored silently as an extra key), health via the existing
    `update_health_max()` helper (after the stats, since it reads CON), and
    each skill's `.base` AND `.current` (CounterTrait: a later `.base = N`
    does not move `.current`).

    Args:
        character (Character): the character being created.
        alloc (Mapping): a Points Build allocation.

    Returns:
        dict: the derived skill bases, for the confirmation screen.

    Raises:
        ValueError: the allocation is invalid; the character has banked XP
            (CC7: no re-spec); the character already has a profession (its
            skill bonus sits on the bases this would overwrite -- allocation
            comes first, CC2.1); or a characteristic, health or skill trait
            the derivation writes is missing. Nothing is written in any of
            these cases.
    """
    errors = validate_allocation(alloc)
    if errors:
        raise ValueError(" ".join(errors))

    store = character.attributes.get(SKILL_XP_ATTRIBUTE, default=None)
    if isinstance(store, Mapping) and len(store) > 0:
        raise ValueError(
            f"{character.key} has banked skill XP; characteristics are set "
            "once, at creation (no re-spec)."
        )

    if character.db.profession:
        raise ValueError(
            f"{character.key} already follows a profession; characteristics "
            "are set before the profession, never after."
        )

    derived = derive_skill_bases(alloc)

    absent = [key for key in STAT_KEYS if character.stats.get(key) is None]
    if character.traits.get("health") is None:
        absent.append("health")
    absent += [key for key in derived if character.skills.get(key) is None]
    if absent:
        raise ValueError(
            f"{character.key} is missing trait(s): {', '.join(absent)}."
        )

    for key in STAT_KEYS:
        character.stats.get(key).base = alloc[key]

    character.update_health_max()

    for key, base in derived.items():
        skill = character.skills.get(key)
        skill.base = base
        skill.current = base

    return derived


# --- CC3.2: the menu meets a pending character on puppet --------------------

CHARGEN_MENU = "world.chargen_menu"


def mark_chargen_pending(character):
    """
    Stamp a character born through an account as not yet made (CC3.2).

    `db.chargen_complete` has three states:

        None   -- the character predates character creation, or was made
                  without an account (`create`, test fixtures): no menu.
        False  -- born through `Account.create_character`, not yet made: the
                  menu meets it on every puppet until it is done.
        True   -- made. Written once, by `world.chargen_menu.node_done`.

    This function writes False and `node_done` writes True; nothing else
    writes the flag. Absent means "no menu" on purpose -- no backfill
    (decision 10), so characters that existed before this task play on as
    they are, and every test fixture's `char1` (auto-puppeted in setUp by
    `EvenniaTestMixin`) is not dropped into a menu. A made character is never
    stamped back to pending.
    """
    if character.db.chargen_complete is None:
        character.db.chargen_complete = False


def start_or_resume_chargen(character):
    """
    Put a pending character in the creation menu: resume the saved one, or
    start a new one. Returns the menu, or None for a character not pending.

    Called last in `Character.at_post_puppet`. Three cases (spiked against
    6.1.0 on 2026-10-28):

    (a) Reconnect without a reload: the old menu is still in `ndb._evmenu`.
        A new EvMenu would call `close_menu()` on it -- deleting the saved
        state and running `cmd_on_exit` -- and start over at ten in
        everything. So the reference is dropped and the menu rebuilt from
        the saved state instead.
    (b) After a reload, the player reconnecting: `ndb` is empty, while the
        persistent cmdset and `_menutree_saved*` remain. Rebuilt the same
        way. (A reload itself does not call `at_post_puppet`; a player who
        stays connected gets EvMenu's own lazy restore in
        `CmdEvMenuNode.func`, which rebuilds the menu on the first line typed
        and swallows that line.)
    (c) Nothing saved: a new persistent menu at `node_allocate`.

    The rebuild mirrors 6.1.0's `CmdEvMenuNode.func._restore`, which is a
    nested function and cannot be called from here. The draft rides in the
    saved goto kwargs, so the running total survives (a) and (b). If the
    saved state cannot be rebuilt, the trace is logged and a new menu starts:
    the draft is lost, the gate is not.

    `auto_quit=False` leaves no way out but `node_done`; `look` and `help`
    stay as menu commands. Multiplayer: the menu and its saved state are the
    character's own, so ten first logins at once share nothing.
    """
    if character.db.chargen_complete is not False:
        return None

    saved = character.attributes.get("_menutree_saved")
    if saved:
        try:
            menu_class, args, calldict = saved
            startnode = character.attributes.get("_menutree_saved_startnode")
            try:
                node, node_input = startnode
            except (TypeError, ValueError):  # the old single-value form
                node, node_input = startnode, ""
            calldict = dict(calldict)
            if node:
                calldict.update(startnode=node, startnode_input=node_input)
            if character.ndb._evmenu:
                del character.ndb._evmenu
            return menu_class(character, *args, **calldict)
        except Exception:
            logger.log_trace(
                f"chargen: could not resume {character.key}'s saved menu; "
                "starting a new one."
            )

    return EvMenu(
        character,
        CHARGEN_MENU,
        startnode="node_allocate",
        persistent=True,
        auto_quit=False,
        cmd_on_exit="look",
    )
