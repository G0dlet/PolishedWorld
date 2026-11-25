"""
The short description, composed live (Names, Task NM-T15; OQ-NM9).

    from world import sdesc
    sdesc.compose(char)          # "a haggard, cloaked, lean, grey-eyed man"
    sdesc.compose_text("female", "adult", "freckled", 11)  # "a lean, freckled woman"
    sdesc.core_word(char)        # "grey-eyed", or "hooded"; None without facts
    char.sdesc.get()             # the composed text, memoised for a second

THE FIXED CORE AND THE LIVING PART (OQ-NM9 (1)-(3))
---------------------------------------------------
Three facts are chosen once and stored as facts, not text, in
`char.db.appearance = {"sex": ..., "age": ..., "feature": ...}`: the sex
(`SEXES`), an age band (`AGES`) and one feature (`FEATURES`). The build is no
fact: it is read from SIZ on every composition (`BUILDS`). The fixed core is
the evidence (Names UG4); the living part is the moment: at most one state
word, the bad end only and the worst first (`STATE_READERS`), and the word of
the outermost garment that is not covered, in `SHOWING_TYPES` order --
`fullbody`, the three armour layers outermost first, `top` (Gear GR7) --
carried on the garment itself (`db.look_word`). A garment without a word shows
nothing and still hides the one beneath; an armour piece without a word is
passed over, since it is the piece that covers the chest that carries one
(Gear OQ-GR5), and a helm hides no breastplate. A worn garment with `"feature"` in
`db.conceals` (the hood) puts *hooded* in the feature's place; recognition is
untouched (UP9 lands later on higher levels of `conceals`).

THE ORDER AND THE LENGTH (OQ-NM9 (4))
-------------------------------------
article + [state], [garment], [build], [feature or *hooded*] + noun, the
adjectives separated by commas. Over `MAX_LENGTH` the build is dropped, then
the garment, then the state; the feature (or *hooded*), the noun and the
article are never dropped. The same facts, SIZ, state and garment give the
same text.

LIVE, BEHIND A MEMO (OQ-NM9 (5))
--------------------------------
`LiveSdescHandler.get()` composes for a character with facts and keeps the
text for `MEMO_SECONDS`: `msg_contents` asks for `get_display_name` once per
entry in `mapping` per receiver (objects.py:1163), so a room line to fifteen
readers is one composition, not twenty-eight (the design pass's probe: about
8.6 ms without the memo, 0.34 ms with). Without facts, or when `compose`
raises, it returns the stored `_sdesc` -- the contrib's text -- and a raise is
logged; the fallback is memoised too, so a broken composer logs once a
second, not once per receiver. `forget()` drops the memo (`@appearance`).

The search reads `sdesc.get()` like every contrib reader (`rpsystem.py:391`),
so a shown word finds the character and a dropped or hidden one does not
(OQ-NM9 (6)).

MULTIPLAYER
-----------
Composition reads state and writes nothing. The memo lives on the handler of
the one cached object, in the one reactor thread. A text read within a second
of a change can be the old one; `@appearance` forgets it at once.
"""

import time

from evennia.contrib.game_systems.clothing.clothing import get_worn_clothes
from evennia.contrib.rpg.rpsystem.rpsystem import SdescHandler
from evennia.utils import logger

from world import encumbrance
from world import fatigue as fatigue_rules
from world import gear

# The text of a character without appearance facts: older characters after
# NM-T4's backfill (OQ-NM6), and a new one until NM-T16's chargen step writes
# its facts. Lower case: the contrib and $You() add the capital at a line's start.
PLACEHOLDER = "a quiet traveller"

# Names UP1: under Armageddon's 35 plus an article, below the contrib's 60.
MAX_LENGTH = 40

# How long a composed text is kept (OQ-NM9 (5)).
MEMO_SECONDS = 1.0

# -- the vocabulary (UQ9; locked at NM-T15's STOPP, Adam: kör) --------------

SEXES = ("male", "female", "unstated")
AGES = ("young", "adult", "old")

# (the lowest SIZ of the band, its word), low to high. Points Build sets SIZ
# 6-18; a value below the first band reads as the first, above the last as
# the last.
BUILDS = (
    (0, "slight"),
    (8, "small"),
    (10, "lean"),
    (12, "sturdy"),
    (14, "broad"),
    (16, "heavyset"),
    (18, "hulking"),
)

FEATURES = (
    "grey-eyed", "dark-eyed", "red-bearded", "black-bearded", "red-haired",
    "fair-haired", "dark-haired", "grey-haired", "bald", "shaven-headed",
    "freckled", "scarred", "pock-marked", "broken-nosed", "hook-nosed",
    "gap-toothed", "sun-browned", "pale", "heavy-browed", "weathered",
)

NOUNS = {
    ("male", "young"): "youth",
    ("male", "adult"): "man",
    ("male", "old"): "old man",
    ("female", "young"): "youth",
    ("female", "adult"): "woman",
    ("female", "old"): "old woman",
    ("unstated", "young"): "figure",
    ("unstated", "adult"): "figure",
    ("unstated", "old"): "figure",
}

# What a hood shows in the feature's place.
HOODED = "hooded"

# The state words. Wet has its two words and no reader until Temperature KP7;
# wounds have neither until Combat's wound slice (WO2).
FATIGUE_WORD = "haggard"
LOAD_WORD = "burdened"
WET_WORDS = ("wet", "soaked")
STATE_WORDS = (FATIGUE_WORD, LOAD_WORD) + WET_WORDS

# The clothing types that can show, outermost first (Gear GR7): a cloak hides
# the armour under it, and armour shows over a tunic. The order is written out
# here, where it is read; the layers' names are gear's.
SHOWING_TYPES = (
    "fullbody",
    gear.ARMOUR_RIGID, gear.ARMOUR_FLEXIBLE, gear.ARMOUR_PADDING,
    "top",
)

_VOWELS = frozenset("aeiou")


# -- the state readers (OQ-NM9 (2)) -------------------------------------------


def _wounds(char):
    """Combat's wound slice fills this from the wound levels (WO2)."""
    return None


def _wet(char):
    """Temperature KP7 fills this (*wet*, *soaked*); nothing reads wet yet."""
    return None


def _fatigue(char):
    """*haggard* from Exhausted down: the gauge at 20 or below."""
    gauge = char.traits.fatigue
    if gauge is None:
        return None
    exhausted = fatigue_rules.LEVELS[1].upper
    return FATIGUE_WORD if gauge.value <= exhausted else None


def _load(char):
    """*burdened* above the limit: OVERLOADED, and CEILING above it."""
    state = encumbrance.encumbrance_state(char)
    return LOAD_WORD if state in (encumbrance.OVERLOADED, encumbrance.CEILING) else None


# Worst first; the first that gives a word is shown.
STATE_READERS = (_wounds, _wet, _fatigue, _load)


# -- composition ----------------------------------------------------------------


def build_for(siz):
    """The build word for a SIZ value."""
    word = BUILDS[0][1]
    for lowest, band_word in BUILDS:
        if siz >= lowest:
            word = band_word
    return word


def article(word):
    """*a* or *an* before `word`. The vocabulary has no word the vowel rule misreads."""
    return "an" if word[:1].lower() in _VOWELS else "a"


def _text(adjectives, noun):
    words = [word for word in adjectives if word]
    first = words[0] if words else noun
    body = f"{', '.join(words)} {noun}" if words else noun
    return f"{article(first)} {body}"


def compose_text(sex, age, feature, siz, state=None, garment=None, hooded=False):
    """
    The short description for these facts, this SIZ, this state and garment.

    Args:
        sex (str): one of SEXES.
        age (str): one of AGES.
        feature (str): one of FEATURES.
        siz (int): the SIZ value the build is read from.
        state (str, optional): a state word, or None.
        garment (str, optional): the garment's word, or None.
        hooded (bool): *hooded* in the feature's place.

    Returns:
        str: at most MAX_LENGTH characters for the vocabulary's words.

    Raises:
        ValueError: a fact outside the vocabulary.
    """
    if (sex, age) not in NOUNS:
        raise ValueError(f"no noun for sex {sex!r}, age {age!r}")
    if feature not in FEATURES:
        raise ValueError(f"unknown feature {feature!r}")
    noun = NOUNS[(sex, age)]
    core = HOODED if hooded else feature
    build = build_for(siz)
    # Drop the build, then the garment, then the state (OQ-NM9 (4)).
    for kept in (
        (state, garment, build),
        (state, garment, None),
        (state, None, None),
        (None, None, None),
    ):
        text = _text((*kept, core), noun)
        if len(text) <= MAX_LENGTH:
            return text
    return text


def facts_of(char):
    """`char`'s appearance facts as a dict, or None when it has none."""
    appearance = char.attributes.get("appearance")
    try:
        return {key: appearance[key] for key in ("sex", "age", "feature")}
    except (TypeError, KeyError):
        return None


def _showing(char):
    """The worn garments nothing covers."""
    return get_worn_clothes(char, exclude_covered=True)


def garment_word(char, showing=None):
    """
    The outermost showing garment's word, in `SHOWING_TYPES` order.

    A garment without a word ends the search with None: it hides the one
    beneath. An armour piece without a word is passed over instead (Gear
    OQ-GR5): only a piece that covers the chest carries a word, so a helm
    or vambraces lie over nothing the word could come from. With one piece
    per layer and location (GR-T4), at most one worn piece in a layer has a
    word, and the order of `contents` never chooses between two.
    """
    showing = _showing(char) if showing is None else showing
    for clothing_type in SHOWING_TYPES:
        for garment in showing:
            if garment.db.clothing_type != clothing_type:
                continue
            word = garment.db.look_word or None
            if word is None and clothing_type in gear.LAYERS:
                continue
            return word
    return None


def is_hooded(char, showing=None):
    """True when a showing garment conceals the feature."""
    showing = _showing(char) if showing is None else showing
    return any("feature" in (garment.db.conceals or ()) for garment in showing)


def state_word(char):
    """The worst state word, or None."""
    for reader in STATE_READERS:
        word = reader(char)
        if word:
            return word
    return None


def compose(char):
    """
    `char`'s short description, composed now. Raises without valid facts.
    """
    facts = facts_of(char)
    if facts is None:
        raise ValueError(f"{char!r} has no appearance facts")
    showing = _showing(char)
    return compose_text(
        facts["sex"],
        facts["age"],
        facts["feature"],
        char.stats.siz.value,
        state=state_word(char),
        garment=garment_word(char, showing),
        hooded=is_hooded(char, showing),
    )


def core_word(char):
    """
    The word of the fixed core a player can type for `char` -- the feature, or
    *hooded* -- when it is in the text shown; else None (no facts, or a text
    the composer could not make).
    """
    facts = facts_of(char)
    if facts is None:
        return None
    try:
        word = HOODED if is_hooded(char) else facts["feature"]
    except Exception:
        return None
    shown = char.sdesc.get().replace(",", " ").split()
    return word if word in shown else None


class LiveSdescHandler(SdescHandler):
    """
    The contrib's handler (`rpsystem.py:660`) with a live `get()`.

    `add` and the stored `_sdesc` are the contrib's: the text of a character
    without facts, and the fallback for a composer that raises.
    """

    def __init__(self, obj):
        super().__init__(obj)
        self._memo = None   # (text, time.monotonic() when it was made)

    def get(self):
        if facts_of(self.obj) is None:
            return super().get()
        now = time.monotonic()
        if self._memo is not None and now - self._memo[1] < MEMO_SECONDS:
            return self._memo[0]
        try:
            text = compose(self.obj)
        except Exception:
            logger.log_trace(f"Names: could not compose the short description of {self.obj.dbref}")
            text = super().get()
        self._memo = (text, now)
        return text

    def forget(self):
        """Drop the memo, so the next `get()` composes."""
        self._memo = None
