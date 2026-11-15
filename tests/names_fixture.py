"""
Distinct short descriptions for the fixture characters. Names, Task NM-T2.

Since NM-T2 a character is shown to others by its short description, and the
contrib gives every new one the same: *A normal person* (rpsystem.py:1567).
A test that asks *who* did something cannot tell two of those apart, so a test
that reads a character's name gives each fixture character its own here, and
asserts `shown(char)` where it used to assert the key.

Not a test module: the name does not start with `test_`, so the runner does
not collect it.
"""

SHORT_DESCRIPTIONS = {
    "Char": "a weathered woman",
    "Char2": "a broad-shouldered man",
    "Char3": "a freckled youth",
    "Char4": "a stooped elder",
}


def describe(*chars):
    """Give each character its fixture short description; return them."""
    for char in chars:
        char.sdesc.add(SHORT_DESCRIPTIONS[char.key])
    return chars


def shown(char):
    """The short description a stranger reads for a fixture character."""
    return SHORT_DESCRIPTIONS[char.key]
