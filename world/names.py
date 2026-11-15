"""
Names a player reads and names a player types (Names, Task NM-T12).

    from world import names
    names.line_start(obj, looker)     # "Mia of the Ford", "A weathered woman"
    names.name_to_type(looker, char)  # "mia of the Ford", "weathered"

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

A NAME AT THE START OF A LINE (NM-T12 lock 2 A)
-----------------------------------------------
`line_start` is `$You()`'s rule for a line sent to one reader, which goes
through `msg` and not the funcparser: the name as the reader knows it, the
first character up and the rest as written (`capital`). It works for any
object -- a thing's key gets its capital too. A statue's name starts with a
colour code, and stays as `$You()` would write it: *stone statue of ...*.

MULTIPLAYER
-----------
Both read state and write nothing.
"""

import string

from typeclasses.characters import capital

ARTICLES = frozenset({"a", "an", "the"})


def name_to_type(looker, char):
    """
    The name `looker` can type for `char`: their recog for it, else the first
    word of its short description that is not an article, else the whole
    short description.

    Args:
        looker (Object): who will type it.
        char (Object): who it names; a character with `sdesc`, or anything
            else, for which the key is all there is.

    Returns:
        str: never empty for a character with a short description.
    """
    recog_handler = getattr(looker, "recog", None)
    recog = recog_handler.get(char) if recog_handler is not None else None
    if recog:
        return recog
    sdesc = char.sdesc.get() if hasattr(char, "sdesc") else char.key
    for word in sdesc.split():
        word = word.strip(string.punctuation)
        if word and word.lower() not in ARTICLES:
            return word
    return sdesc.strip()


def line_start(obj, looker):
    """`obj`'s name as `looker` reads it, to start a line: `$You()`'s capital."""
    return capital(obj.get_display_name(looker))
