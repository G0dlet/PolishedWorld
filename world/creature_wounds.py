"""
world/creature_wounds.py
========================
A creature's hurt (Creatures decomposition, slice CE; Combat Design CR1,
CR2). CE-T1: its numbers, read on demand. CE-T2: the door, and death at
minus the Critical Wound rating (CE5, CE9).

A creature has General Hit Points, not a character's seven locations: the
book keeps locational Hit Points for major villains (core p. 146). What is
stored is `con` and `siz`, set by the creature's prototype (CE3), and, for
the few species whose printed row leaves the formula, `resilience` (CE7).
Everything here is worked out at the read, and the readers write nothing.

    general_hit_points_of(creature) -> int, or None without CON  (p. 146; CE4)
    critical_rating_of(creature)    -> int, or None without CON  (p. 146)
    resilience_of(creature)         -> int, or None without CON  (Monsters p. 12)
    armour_points_of(creature)      -> int, its natural armour   (CE9)
    damage_of(creature)             -> int, the damage it carries (CE3)
    hit_points_of(creature)         -> int, what is left, or None without CON
    damage(creature, amount, location, made=None, *, source=None)
                                    -> the door behind Creature.apply_health_damage

A creature without CON -- the class default is None (CE13) -- has no
numbers: the first three answer None and never raise, so whatever only shows
something can show nothing for it. Armour does not depend on CON, so
`armour_points_of` always answers. Refusing to hurt such a creature is the
door's (CE-T2), not the readers'.

The arithmetic over integers is `world.body`'s, as `wounds.maxima_of` leaves
it to `body.hit_points_max`. The module is imported whole (`from world import
body`), so its readers, which end in `_of`, never shadow body's functions.

What the door stores is this module's, as `body_damage` is `world.wounds`'s,
and no class declares it (CE-T2's STOPP 0): `general_damage`, the damage
taken -- not the Hit Points left (CE3) -- and `damage_source`, the latest
blow's source. Neither row exists until the door writes it, so a creature
without `general_damage` is unhurt. Read the damage through `damage_of`,
never the row: from CE-T5 the stored figure is not yet healed.
"""

from world import body, wounds

# The door's two Attributes (CE-T2). Not `body_damage`: a creature has no
# body of seven locations, and that name is the wound module's -- the push
# census in tests/test_client_state.py holds every write to it.
DAMAGE = "general_damage"
SOURCE = "damage_source"


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


def damage_of(creature):
    """
    The damage the creature carries: its stored `general_damage`, 0 when it
    has none (CE3: without the row it is unhurt). It writes nothing.

    Returns:
        int
    """
    return creature.attributes.get(DAMAGE, default=0)


def hit_points_of(creature):
    """
    The creature's Hit Points left: its General Hit Points less its damage,
    through `wounds.hit_points`, below 0 if so -- death is at minus the
    Critical Wound rating (CE5), and the state at 0 reads how far down it
    stands (CE6).

    Returns:
        int, or None for a creature without CON (CE13).
    """
    maximum = general_hit_points_of(creature)
    if maximum is None:
        return None
    return wounds.hit_points(maximum, damage_of(creature))


def damage(creature, amount, location, made=None, *, source=None):
    """
    Put `amount` of hurt on the creature and answer for it: the door behind
    `Creature.apply_health_damage`, its one caller, which carries out the
    death (CE9). The amount is what got through the armour (WO6), and is
    written whole: a creature has no *Glancing Blow* (Hero Points are a
    character's).

    Everything is checked before anything is written, in this order, and
    all but the last whatever the amount, so a wrong call fails on every
    call: the place (`wounds.check_location`, WO5; it is checked and not
    used, since General Hit Points have no locations); an attack roll with
    `wounds.ALL`, which has none (WN5); an attack roll that is not a
    success; a creature already deleted, which answers None -- two blows in
    one tick, the first of which killed, are a race and not a wrong call;
    a creature without CON (CE13); an amount of 0 or less, which answers
    None.

    The stored damage grows by the amount, and `damage_source` becomes this
    blow's source: a None removes the row, so it always says what the
    latest call said (CE9; CE-T3's alarm reads it).

    Args:
        made (dict or None): the attack roll's successful `skill_check`
            dict, when the source has one. Read only for whether the hit
            was critical (CE-T4).
        source (Object, str or None): what dealt the blow, as a character's
            door takes it.

    Raises:
        ValueError: as above, before anything is written.

    Returns:
        dict or None: None if nothing was written; else
            {"dies": bool, at minus the Critical Wound rating or below (CE5),
             "hit_points": int, what is left after the blow}.
        Between 0 and minus the rating the creature lives: what follows
        there is CE-T3's.
    """
    wounds.check_location(location)
    if made is not None:
        if location == wounds.ALL:
            raise ValueError("an ALL source has no attack roll to test against (WN5)")
        if not made.get("success"):
            raise ValueError("a wound is tested against a successful attack roll")
    if not creature.pk:
        return None
    if creature.con is None:
        raise ValueError(
            f"{creature.key} has no CON and cannot be hurt (Creatures CE13): "
            "its prototype must set `con`"
        )
    if amount <= 0:
        return None
    total = damage_of(creature) + amount
    creature.attributes.add(DAMAGE, total)
    if source is None:
        creature.attributes.remove(SOURCE)
    else:
        creature.attributes.add(SOURCE, source)
    left = wounds.hit_points(general_hit_points_of(creature), total)
    return {"dies": left <= -critical_rating_of(creature), "hit_points": left}
