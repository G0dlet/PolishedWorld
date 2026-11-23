"""
A character made before Wounds WN-T6: the `health` trait as
`Character.at_object_creation` created it until then (CON x 2, the word
table as its descs). Nothing in the game reads it any more (WN2b); the tests
that hold that promise add it with `made_before_wn` and show that what the
screens print is still the wound module's.
"""
from world import wounds


def made_before_wn(char, base=20):
    """Give `char` the old trait, full at `base`; returns the trait."""
    char.traits.add(
        "health", "Health",
        trait_type="gauge",
        base=base,
        mod=0,
        min=0,
        rate=0,
        descs=dict(wounds.HEALTH_WORDS),
    )
    return char.traits.get("health")
