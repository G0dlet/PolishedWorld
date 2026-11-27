"""
world/skill_base.py
===================
What a character's skill is, with or without its trait (Body decomposition,
slice BD, locks BD3 and BD6; Legend core p. 14).

Every skill starts at its base, the sum of two characteristics (p. 14), so a
skill a character has no trait for is still a number that can be worked
out. One function answers for every reader:

    base_for(char, key)  -> the base from the characteristics, or None
    value_of(char, key)  -> the trait's value if the trait exists, else the base
    trait_kwargs(char, key) -> how one of COMBAT_SKILL_TRAITS or
                               FIRST_AID_TRAITS is added
    ensure_style(char, key) -> a Combat Style's trait, made if missing

Why a safety net (BD6): a reader that went to the trait directly would get
nothing for a character a backfill missed -- `healing.accrue` would grant
nothing, with no message. Through `value_of` the backfill decides what is
shown, not whether healing works.

The base is read from the characteristics' `.base`: it is the number
character creation would have written (`chargen.apply_allocation` sets
`.base`). A trait's `.value` is read, as every roll site and
`world.fatigue` read a skill (OQ-BD2).

Every Common skill's pair lives in `chargen.SKILL_BASE_PAIRS`, and nowhere
else (OQ-BD6: Resilience's stood here for one task, until its trait
existed). A Combat Style's pair is read from `world.combat_styles` and must
stay out of that table: `chargen.apply_allocation` refuses a character with
a pair and no trait, and a style has no trait until it is used (BD3).

SKILL_LADDERS holds the six words every skill reads as, and `ladder(key)`
makes the `descs` table a trait stores. The bands are 0-19, 20-39, 40-59,
60-79, 80-94 and 95 upward. The traits contrib reads a `descs` key as an
UPPER bound, inclusive, and gives the last word to anything above the last
key (`CounterTrait.desc`; `world.improvement.tier_for` and the skills'
"reaches a new tier" line follow the same rule), so a ladder is keyed by
each band's top: LADDER_TOPS. Keyed by band bottoms (0/20/40/60/80/95), as
the five older skills were until BD-T5b, a ladder reads one rung early: 21
as the third word, 81 as the last. A trait keeps the table it was created
with, so `world.character_migrations.backfill_skill_ladders` rewrites it on
older characters. (BACKLOG *`descs` tables are read as upper bounds but
shaped like lower bounds*, decided for the skills 2026-11-22; hunger and
thirst are still keyed the old way.)

COMBAT_SKILL_TRAITS is how the four Common skills combat reads (BD5) are
made into traits: the name and the ladder. Two writers read it and no
others, both through `trait_kwargs`: `Character.at_object_creation` and
`world.character_migrations.backfill_combat_skills` (BD-T5), so a backfilled
character cannot differ from a new one.

FIRST_AID_TRAITS is the same shape for First Aid (Healing decomposition
HL-T4, lock HL2), a Common skill every character has, INT + DEX (p. 14).
It is a table of its own and not a row of COMBAT_SKILL_TRAITS: that table
is what combat reads (BD5), and `backfill_combat_skills` keeps meaning the
four on a database it has already run on. Creation reads both tables;
`world.character_migrations.backfill_first_aid` reads this one.

HEALING_TRAITS is Healing's (HL-T6; HL2, HL3): an Advanced skill, INT + POW
(p. 14), that no character has at creation. Its pair stands in this table and
not in `chargen.SKILL_BASE_PAIRS`, as a Combat Style's does: `apply_allocation`
refuses a character with a base pair and no trait. Knowing the healer's kit's
recipe is having the skill (`knows_healing`), and `ensure_healing` makes the
trait at its base the first time the skill is needed: when a skill list is
shown (`skills`, `progress`, `sheet`) and, from HL-T12, before surgery's test.
A character who does not know the recipe gets nothing.

Combat Styles (BD-T6; BD3, BD4). `base_for` and `value_of` answer for a
style's key with no trait on the character, and `ensure_style` makes the
trait at the base the first time a style is used. Every style shares one
ladder, and each has a row in SKILL_LADDERS so that `ladder(key)` and the
ladder migration cover a style trait like any other. Nothing in production
calls `ensure_style` until ML rolls a style.

Pure over the character's handlers, except `ensure_style`, which writes
one trait: no Django query.
"""

from world import combat_styles
from world.chargen import SKILL_BASE_PAIRS

# The top of each band, inclusive; 100 stands for "95 upward", since
# anything above the last key reads the last word.
LADDER_TOPS = (19, 39, 59, 79, 94, 100)

# Skill -> its six words, in band order (Tone Guide section 5: concrete,
# nothing epic). One table for the eleven skills and, below it, the styles:
# creation, both backfills, `ensure_style`, `ensure_healing` and the ladder
# migration read it.
SKILL_LADDERS = {
    "athletics": ("feeble", "weak", "capable", "athletic", "strong", "mighty"),
    "perception": (
        "oblivious", "unaware", "attentive", "observant", "sharp", "eagle-eyed",
    ),
    "stealth": ("clumsy", "obvious", "careful", "sneaky", "stealthy", "invisible"),
    "craft": (
        "unskilled", "novice", "apprentice", "journeyman", "skilled", "master",
    ),
    "hunting": (
        "helpless", "novice", "competent", "tracker", "hunter", "master hunter",
    ),
    "brawn": ("slight", "wiry", "sturdy", "stout", "burly", "ox-strong"),
    "evade": ("flat-footed", "slow", "wary", "nimble", "quick", "hard to hit"),
    "resilience": ("frail", "soft", "sound", "hardy", "tough", "unbroken"),
    "unarmed": (
        "harmless", "clumsy", "scrappy", "practised", "hard-fisted", "dangerous",
    ),
    # The hands and the stomach, what a tired person notices (HL-T4).
    "first_aid": (
        "squeamish", "fumbling", "steady", "deft", "sure-handed", "unflinching",
    ),
    # A surgeon's road, in trades, as Hunting's ends in one (HL-T6).
    "healing": (
        "butcher", "barber", "bonesetter", "physician", "surgeon", "master surgeon",
    ),
}
# Every Combat Style reads the same six words (BD-T6).
SKILL_LADDERS.update(
    {style_key: combat_styles.STYLE_LADDER for style_key in combat_styles.STYLES}
)


def ladder(key):
    """
    The `descs` table for a skill's trait: {top of band: word}, rising.

    A new dict on every call, because a trait stores what it is given.

    Args:
        key (str): a key of SKILL_LADDERS.

    Returns:
        dict: six entries keyed by LADDER_TOPS.

    Raises:
        KeyError: the skill has no ladder.
    """
    return dict(zip(LADDER_TOPS, SKILL_LADDERS[key]))


COMBAT_SKILL_TRAITS = {
    "brawn": {"name": "Brawn", "descs": ladder("brawn")},
    "evade": {"name": "Evade", "descs": ladder("evade")},
    "resilience": {"name": "Resilience", "descs": ladder("resilience")},
    "unarmed": {"name": "Unarmed", "descs": ladder("unarmed")},
}

# First Aid (HL2): every character has it, made as the four are.
FIRST_AID_TRAITS = {
    "first_aid": {"name": "First Aid", "descs": ladder("first_aid")},
}

# Healing (HL2, HL3): an Advanced skill, made only for a character who knows
# the healer's kit's recipe. The pair is here, not in SKILL_BASE_PAIRS.
HEALING_TRAITS = {
    "healing": {"name": "Healing", "pair": ("int", "pow"), "descs": ladder("healing")},
}

# The recipe whose knowledge is the skill (HL3; world/recipes.py).
HEALERS_KIT_RECIPE = "healer's kit"


def base_for(char, key):
    """
    A skill's base, worked out from the character's characteristics (p. 14).

    Args:
        char: a typeclassed object with a `stats` handler.
        key (str): the skill's trait key, e.g. "resilience", or a Combat
            Style's, e.g. "style_knife".

    Returns:
        int or None: the sum of the two characteristics' `.base`; None when
            the key has no pair or the character lacks a characteristic. A
            style's pair is STR + DEX in close combat and DEX x 2 at range.
    """
    pair = SKILL_BASE_PAIRS.get(key)
    if pair is None and key in combat_styles.STYLES:
        pair = combat_styles.pair_for(key)
    if pair is None and key in HEALING_TRAITS:
        pair = HEALING_TRAITS[key]["pair"]
    stats = getattr(char, "stats", None)
    if pair is None or stats is None:
        return None
    total = 0
    for stat_key in pair:
        stat = stats.get(stat_key)
        if stat is None:
            return None
        total += int(stat.base)
    return total


def value_of(char, key):
    """
    A skill's value: the trait's if the character has it, the base if not.

    Args:
        char: a typeclassed object with `skills` and `stats` handlers.
        key (str): the skill's trait key.

    Returns:
        int, float or None: the trait's `.value`; else `base_for(char, key)`.
    """
    skills = getattr(char, "skills", None)
    trait = skills.get(key) if skills is not None else None
    if trait is not None:
        return trait.value
    return base_for(char, key)


def trait_kwargs(char, key):
    """
    What `char.skills.add(key, name, **kwargs)` takes for a skill every
    character has from creation: a combat skill, or First Aid.

    The one place the shape of those traits is written, for creation and
    for the backfills. No `max`: a CounterTrait with a max clamps inside its
    own setter (D.2, P-7).

    Args:
        char: a typeclassed object with a `stats` handler.
        key (str): a key of COMBAT_SKILL_TRAITS or FIRST_AID_TRAITS.

    Returns:
        dict or None: the keyword arguments, with `base` and `current` at
            `base_for(char, key)`; None when that base cannot be worked out.

    Raises:
        KeyError: `key` is in neither table.
    """
    if key not in COMBAT_SKILL_TRAITS and key not in FIRST_AID_TRAITS:
        raise KeyError(key)
    return _counter_kwargs(char, key)


def _counter_kwargs(char, key):
    """The shape of a skill trait at its base; None when there is no base."""
    base = base_for(char, key)
    if base is None:
        return None
    return {
        "trait_type": "counter",
        "base": base,
        "current": base,
        "mod": 0,
        "min": 0,
        "descs": ladder(key),
    }


def ensure_style(char, style_key):
    """
    A Combat Style's trait, made at its base if the character lacks it (BD3).

    The first use of a style is what turns it into a trait. An existing
    trait is returned as it is: a trained value is never written over.

    Multiplayer: the read and the write are one synchronous stretch on
    Twisted's single-threaded reactor, so two calls cannot both find the
    trait missing.

    Args:
        char: a typeclassed object with `skills` and `stats` handlers.
        style_key (str): a key of `combat_styles.STYLES`.

    Returns:
        Trait or None: the style's trait; None when the trait is missing
            and its base cannot be worked out (a characteristic is absent),
            in which case nothing is written.

    Raises:
        KeyError: `style_key` is not a Combat Style (a Common skill's key
            included: those are made at creation).
    """
    style = combat_styles.STYLES[style_key]
    existing = char.skills.get(style_key)
    if existing is not None:
        return existing
    kwargs = _counter_kwargs(char, style_key)
    if kwargs is None:
        return None
    char.skills.add(style_key, style["name"], **kwargs)
    return char.skills.get(style_key)


def knows_healing(char):
    """
    Whether a character has the Healing skill: it knows the kit's recipe (HL3).

    Args:
        char: a typeclassed object; one without `knows_recipe` (no
            Character) does not.

    Returns:
        bool: True if the character has learned the healer's kit's recipe.
    """
    knows = getattr(char, "knows_recipe", None)
    return bool(knows is not None and knows(HEALERS_KIT_RECIPE))


def ensure_healing(char):
    """
    The Healing trait, made at its base if a character who knows the recipe
    lacks it (HL3, `ensure_style`'s form; OQ-HL7).

    Called the first time the skill is needed: by the commands that list
    skills, and from HL-T12 before surgery's test. An existing trait is
    returned as it is: a trained value is never written over.

    Multiplayer: the read and the write are one synchronous stretch on
    Twisted's single-threaded reactor, so two calls cannot both find the
    trait missing.

    Args:
        char: a typeclassed object with `skills` and `stats` handlers.

    Returns:
        Trait or None: the trait; None, with nothing written, when the
            character does not know the healer's kit's recipe or a
            characteristic is missing.
    """
    if not knows_healing(char):
        return None
    existing = char.skills.get("healing")
    if existing is not None:
        return existing
    kwargs = _counter_kwargs(char, "healing")
    if kwargs is None:
        return None
    char.skills.add("healing", HEALING_TRAITS["healing"]["name"], **kwargs)
    return char.skills.get("healing")
