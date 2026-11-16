"""
Names a player reads and names a player types (Names, Task NM-T12).

    from world import names
    names.line_start(obj, looker)     # "Mia of the Ford", "A weathered woman"
    names.name_to_type(looker, char)  # "mia of the Ford", "weathered"
    names.name_to_type_here(looker, char)  # the same, or "a weathered woman"
    names.pronoun(char, "your")       # "her", "his", "their"

A NAME TO TYPE IS NOT A NAME TO READ (UP15, K5)
-----------------------------------------------
A line that tells a player what to type must give a word the player's own
search finds (lessons candidate: the harvest refusal once printed the display
name as the thing to type). The lesson's offer printed the teacher's key,
which a stranger cannot type and should not be told. `name_to_type` gives
what this looker can type for that character: their recog, whole and as they
wrote it, or else one word of the short description -- the first after an
article (*a weathered woman* -> *weathered*), as the Names note's UP15 has
it. The student's search (`commands/crafting_commands.py:1457`) is over the
teacher alone and matches the start of any word of either, so one word is
enough; a recog is given whole because it is what the player chose to call
someone. Never the key.

A composed description (NM-T15) begins with its most changeable words, a
state or a garment, which may be gone before the player types them. So for a
character with appearance facts the word is its fixed core's -- the feature,
or *hooded* while a hood is worn -- which is never dropped (NM-T15 lock 2 A).

`name_to_type_here` is for a search over the looker's whole room (NM-T13b
lock 1 C; the `trade` answer line): one word can find two people there --
*normal* finds every new character -- so the word is given only when the
looker's own search with it finds that character alone; otherwise the whole
short description, which finds them exactly unless two share it.

A NAME AT THE START OF A LINE (NM-T12 lock 2 A)
-----------------------------------------------
`line_start` is `$You()`'s rule for a line sent to one reader, which goes
through `msg` and not the funcparser: the name as the reader knows it, the
first character up and the rest as written (`capital`). It works for any
object -- a thing's key gets its capital too. A statue's name starts with a
colour code, and stays as `$You()` would write it: *stone statue of ...*.

A PRONOUN OUTSIDE THE FUNCPARSER (NM-T15b)
-----------------------------------------
`pronoun` is `$pron()` for a line built with `%` or an f-string, such as the
barter contrib's frames: Evennia's own table read for the character's
`gender`, in the third person, as another reads it. It is given the second
person form, as `$pron()` is (*your*, *you*, *yourself*). Anything without a
`gender` reads singular *they*, never *it*.

MULTIPLAYER
-----------
All read state and write nothing.
"""

import string

from evennia.utils.verb_conjugation.pronouns import pronoun_to_viewpoints

from typeclasses.characters import capital
from world import sdesc as sdesc_rules

ARTICLES = frozenset({"a", "an", "the"})


def name_to_type(looker, char):
    """
    The name `looker` can type for `char`: their recog for it, else the word
    of its fixed core -- the feature, or *hooded* -- for a composed
    description (NM-T15 lock 2 A), else the first word of its short
    description that is not an article, else the whole short description.

    Args:
        looker (Object): who will type it.
        char (Object): who it names; a character with `sdesc`, or anything
            else, for which the key is all there is.

    Returns:
        str: never empty for a character with a short description.
    """
    recog = _recog(looker, char)
    if recog:
        return recog
    core = _core_word(char)
    if core:
        return core
    sdesc = _sdesc(char)
    for word in sdesc.split():
        word = word.strip(string.punctuation)
        if word and word.lower() not in ARTICLES:
            return word
    return sdesc.strip()


def name_to_type_here(looker, char):
    """
    The name `looker` can type for `char` in a search over `looker`'s room:
    `name_to_type`'s word when that search finds `char` alone, else the whole
    short description. A recog is given whole either way.

    Args:
        looker (Object): who will type it; its search reads its own room.
        char (Object): who it names.

    Returns:
        str: the name to print.
    """
    recog = _recog(looker, char)
    if recog:
        return recog
    word = name_to_type(looker, char)
    found = looker.search(word, quiet=True)
    if list(found or []) == [char]:
        return word
    return _sdesc(char).strip()


def _recog(looker, char):
    handler = getattr(looker, "recog", None)
    return handler.get(char) if handler is not None else None


def _core_word(char):
    return sdesc_rules.core_word(char) if hasattr(char, "sdesc") else None


def _sdesc(char):
    return char.sdesc.get() if hasattr(char, "sdesc") else char.key


def line_start(obj, looker):
    """`obj`'s name as `looker` reads it, to start a line: `$You()`'s capital."""
    return capital(obj.get_display_name(looker))


def pronoun(char, you_form):
    """
    `char`'s third-person pronoun for `you_form`, as another reads it: what
    `$pron(you_form)` gives every receiver but `char` (funcparser.py:1609).

    Args:
        char (Object): who it names; its `gender`, else singular *they*.
        you_form (str): the second-person form, as `$pron()` takes it --
            *your*, *you*, *yourself*.

    Returns:
        str: *her*, *his*, *their* ... in `you_form`'s case.
    """
    gender = getattr(char, "gender", "plural")
    _, third_person = pronoun_to_viewpoints(you_form, gender=gender)
    return third_person
