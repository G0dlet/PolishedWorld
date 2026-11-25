"""
world/creature_wounds.py
========================
A creature's hurt (Creatures decomposition, slice CE; Combat Design CR1,
CR2). CE-T1: its numbers, read on demand.

A creature has General Hit Points, not a character's seven locations: the
book keeps locational Hit Points for major villains (core p. 146). What is
stored is `con` and `siz`, set by the creature's prototype (CE3), and, for
the few species whose printed row leaves the formula, `resilience` (CE7).
Everything here is worked out at the read, and the readers write nothing.

    general_hit_points_of(creature) -> int, or None without CON  (p. 146; CE4)
    critical_rating_of(creature)    -> int, or None without CON  (p. 146)
    resilience_of(creature)         -> int, or None without CON  (Monsters p. 12)
    armour_points_of(creature)      -> int, its natural armour   (CE9)

A creature without CON -- the class default is None (CE13) -- has no
numbers: the first three answer None and never raise, so whatever only shows
something can show nothing for it. Armour does not depend on CON, so
`armour_points_of` always answers. Refusing to hurt such a creature is the
door's (CE-T2), not the readers'.

The arithmetic over integers is `world.body`'s, as `wounds.maxima_of` leaves
it to `body.hit_points_max`. The module is imported whole (`from world import
body`), so its readers, which end in `_of`, never shadow body's functions.
"""

from world import body


def general_hit_points_of(creature):
    """
    The creature's General Hit Points, the average of CON and SIZ rounded up
    (core p. 146; Creatures CE4). The maximum: what is left is the door's.

    Returns:
        int, or None for a creature without CON (CE13).
    """
    con = creature.con
    if con is None:
        return None
    return body.general_hit_points(con, creature.siz)


def critical_rating_of(creature):
    """
    The creature's Critical Wound rating, half its General Hit Points rounded
    up (core p. 146).

    Returns:
        int, or None for a creature without CON (CE13).
    """
    hit_points = general_hit_points_of(creature)
    if hit_points is None:
        return None
    return body.critical_rating(hit_points)


def resilience_of(creature):
    """
    The creature's Resilience: its stored `resilience`, else CON x 3 + 10
    (Monsters of Legend p. 12: "generally", with some creatures higher or
    lower; Creatures CE7). Five of the book's twenty animals carry their own.

    Without CON the answer is None even if a `resilience` is stored: a
    creature without CON has no numbers, and Resilience is only tested at
    0 Hit Points, which it cannot reach.

    Returns:
        int, or None for a creature without CON (CE13).
    """
    con = creature.con
    if con is None:
        return None
    stored = creature.resilience
    if stored is not None:
        return stored
    return con * 3 + 10


def armour_points_of(creature):
    """
    The creature's Armour Points: today its natural armour, `natural_ap`
    (Creatures CE9: the one reader, which the caller asks for the blow and
    the door for the Critical Wound table). It does not depend on CON.

    Returns:
        int
    """
    return creature.natural_ap
