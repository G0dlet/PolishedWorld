"""
Build the alpha's authored area from `world/seed_data.py`. Alpha content epic,
Task AC3.1.

    from world.seeding import seed_world
    seed_world()   # -> {"rooms": {"created": 6, "skipped": 0}, "exits": ..., "nodes": ...,
                   #     "scrolls": ...}

    from world.seeding import reseed_scroll
    reseed_scroll("tent")   # staff replenishment, one recipe (Launch Minimum L3.3)

IDEMPOTENT, NOT A SYNC
----------------------
Every object the seeder creates carries the tag `(<seed_id>, "seed")`, given
at creation (not added afterwards, so a crash can never leave an untagged
object that the next run would duplicate). Before creating, the seeder looks
the seed_id up; if it exists, it is skipped and left exactly as it is. A second
run is therefore a no-op, and the function is safe on a database that already
has the area (Adam's dev database) as well as on a fresh one (AC3.2's setup
hook). It never updates an existing object -- see seed_data's "CHANGING THIS
DATA" for why and what to do instead.

SCROLLS ARE PLACED ONCE (Launch Minimum L3.3)
---------------------------------------------
A deleted room or node comes back on the next run, because its seed tag went
with it. A scroll is deleted by design -- `learn` consumes it -- and a re-run
that put it back would hand out the recipe again every time an admin re-seeded
to repair something else. So every scroll the seeder places is also recorded in
a ledger (`ServerConfig` key `SCROLL_LEDGER_KEY`, a list of seed_ids), and
`seed_world()` skips a scroll whose seed_id is in the ledger *or* still exists.
The ledger is written after the scroll is spawned and stamped, so it never
claims a scroll that was not made. Replenishing is a staff decision, one recipe
at a time: `reseed_scroll(<recipe>)` ignores the ledger and spawns one scroll
if none carrying that seed tag exists anywhere -- on the floor, in someone's
pack -- and deletes nothing.

FAILURE IS LOUD
---------------
Nothing here catches exceptions. AC3.2 calls this from `at_initial_setup()`,
where an exception stops startup and the step re-runs on the next start
(Alpha Content Decomposition, AD7 / finding 5) -- the right outcome, where a
swallowed error would leave an empty world recorded as built. Limbo, every
node prototype and the scroll prototype are resolved before anything is
created, so bad data fails before half an area exists. A run that dies midway anyway is recovered by
running it again: what was built is skipped, the rest is created.

WHAT IT DOES NOT DO
-------------------
It never creates the Treasury (AD7): `typeclasses/treasury.py` holds that a
database must not silently acquire a money-holding object nobody placed. The
Treasury is an admin step in AC3.2's runbook. It touches no object without one
of its own seed tags.

MULTIPLAYER
-----------
Seeding runs once per database -- from the setup hook before any player exists,
or from an admin `@py`. It takes no lock: two admins seeding the same database
at the same moment could both miss a lookup and build a pair. That is not a
case worth code; it is a case for not doing that.
"""

from django.conf import settings
from evennia.prototypes.prototypes import search_prototype
from evennia.server.models import ServerConfig
from evennia.prototypes.spawner import spawn
from evennia.utils import logger
from evennia.utils.create import create_object
from evennia.utils.search import search_object, search_tag

from world import seed_data

SEED_CATEGORY = "seed"
# Every seeded room carries this; the placement rule is stated against it.
AREA_TAG = ("alpha_area", "seed_area")
# What CreatureSpawnScript.at_repeat queries (typeclasses/scripts.py); a test
# runs the script's own query against the seeded rooms.
SPAWN_TAG = ("creature_spawn", "room_flag")

ROOM_TYPECLASS = "typeclasses.rooms.Room"
EXIT_TYPECLASS = "typeclasses.exits.Exit"

# The prototype `inscribe` spawns and `learn` consumes (world/prototypes.py).
SCROLL_PROTOTYPE = "scroll"
# ServerConfig key: the seed_ids of every scroll the seeder has ever placed.
SCROLL_LEDGER_KEY = "seed.scrolls_placed"


def find_seeded(seed_id):
    """
    Return the object carrying `(seed_id, "seed")`, or None.

    More than one match means someone duplicated a seeded object by hand; the
    first is used and the rest reported, never deleted -- deleting is not the
    seeder's job.
    """
    matches = list(search_tag(seed_id, category=SEED_CATEGORY))
    if len(matches) > 1:
        logger.log_warn(
            f"seed_world: {len(matches)} objects carry seed tag {seed_id!r}; "
            f"using {matches[0].dbref}"
        )
    return matches[0] if matches else None


def _resolve_limbo(limbo):
    """The object Limbo-side exits stand in: the argument, else DEFAULT_HOME."""
    if limbo is not None:
        return limbo
    dbref = settings.DEFAULT_HOME
    matches = search_object(dbref)
    if not matches:
        raise RuntimeError(
            f"seed_world: DEFAULT_HOME {dbref!r} does not exist -- "
            "no Limbo to put the area's entrance in"
        )
    return matches[0]


def _prototype(prototype_key):
    """The shipped prototype dict for `prototype_key`; raises if there is none."""
    found = search_prototype(key=prototype_key, no_db=True)
    if len(found) != 1:
        raise ValueError(
            f"seed_world: prototype {prototype_key!r} matched {len(found)} prototypes"
        )
    return found[0]


def _check_prototypes():
    """Fail before building anything if a node or the scroll prototype is unknown."""
    for node in seed_data.NODES:
        _prototype(node["prototype"])
    _prototype(SCROLL_PROTOTYPE)


def _room(seed_id):
    """A room this seed built; raises if it is missing (rooms are built first)."""
    room = find_seeded(seed_id)
    if room is None:
        raise RuntimeError(f"seed_world: seeded room {seed_id!r} not found")
    return room


def _seed_rooms(counts):
    for spec in seed_data.ROOMS:
        if find_seeded(spec["seed_id"]):
            counts["skipped"] += 1
            continue
        attributes = [("desc", spec["desc"]), ("is_indoor", bool(spec["is_indoor"]))]
        tags = [(spec["seed_id"], SEED_CATEGORY), AREA_TAG]
        if spec["thermal_regime"]:
            attributes.append(("thermal_regime", spec["thermal_regime"]))
        if spec["spawn_creatures"]:
            attributes.append(("spawn_creatures", dict(spec["spawn_creatures"])))
            tags.append(SPAWN_TAG)
        create_object(
            typeclass=ROOM_TYPECLASS,
            key=spec["key"],
            attributes=attributes,
            tags=tags,
        )
        counts["created"] += 1


def _seed_exits(counts, limbo):
    for spec in seed_data.EXITS:
        if find_seeded(spec["seed_id"]):
            counts["skipped"] += 1
            continue
        source = limbo if spec["from"] == seed_data.LIMBO else _room(spec["from"])
        create_object(
            typeclass=EXIT_TYPECLASS,
            key=spec["key"],
            aliases=list(spec["aliases"]),
            location=source,
            destination=_room(spec["to"]),
            tags=[(spec["seed_id"], SEED_CATEGORY)],
        )
        counts["created"] += 1


def _seed_nodes(counts):
    for spec in seed_data.NODES:
        if find_seeded(spec["seed_id"]):
            counts["skipped"] += 1
            continue
        # The shipped prototype itself, plus where the node stands and its
        # seed tag -- so the node is tagged ("<key>", "from_prototype") like
        # anything `@spawn <key>` makes. Not a child prototype: a child without
        # a prototype_key gets a hashed one from the spawner, and a child that
        # repeats its parent's key is refused ("tries to parent itself").
        # search_prototype returns a shallow copy of the module's dict, so
        # top-level keys are ours to replace; tags gets a new list, never an
        # in-place append into one the module might share.
        prototype = _prototype(spec["prototype"])
        prototype["location"] = _room(spec["room"])
        prototype["tags"] = list(prototype.get("tags", [])) + [(spec["seed_id"], SEED_CATEGORY)]
        spawned = spawn(prototype)
        if not spawned:
            raise RuntimeError(f"seed_world: spawning {spec['seed_id']!r} failed")
        counts["created"] += 1


def _placed_scrolls():
    """The seed_ids in the scroll ledger, as a set (empty on a fresh database)."""
    return set(ServerConfig.objects.conf(SCROLL_LEDGER_KEY, default=list))


def _scroll_row(recipe_name):
    """The SCROLLS row for `recipe_name`; raises ValueError if there is none."""
    for spec in seed_data.SCROLLS:
        if spec["recipe"] == recipe_name:
            return spec
    raise ValueError(
        f"no seeded scroll for recipe {recipe_name!r} -- "
        f"world/seed_data.py SCROLLS names: "
        f"{', '.join(row['recipe'] for row in seed_data.SCROLLS)}"
    )


def _place_scroll(spec):
    """
    Spawn one scroll for `spec`, stamp it, and record it in the ledger.

    Tagged and placed at spawn, as the nodes are, so it is never an untagged
    object; stamped right after, through `Scroll.stamp` -- the scroll's identity
    (`db.recipe` and its key) is never set by hand. The ledger write comes last.
    """
    prototype = _prototype(SCROLL_PROTOTYPE)
    prototype["location"] = _room(spec["room"])
    prototype["tags"] = list(prototype.get("tags", [])) + [(spec["seed_id"], SEED_CATEGORY)]
    spawned = spawn(prototype)
    if not spawned:
        raise RuntimeError(f"seed_world: spawning {spec['seed_id']!r} failed")
    scroll = spawned[0]
    scroll.stamp(spec["recipe"])
    placed = _placed_scrolls()
    placed.add(spec["seed_id"])
    ServerConfig.objects.conf(SCROLL_LEDGER_KEY, sorted(placed))
    return scroll


def _seed_scrolls(counts):
    placed = _placed_scrolls()
    for spec in seed_data.SCROLLS:
        # The ledger catches a scroll that was placed and learned; find_seeded
        # catches one that exists without a ledger entry (a dev database that
        # was seeded by hand, or a run that died between spawn and ledger).
        if spec["seed_id"] in placed or find_seeded(spec["seed_id"]):
            counts["skipped"] += 1
            continue
        _place_scroll(spec)
        counts["created"] += 1


def reseed_scroll(recipe_name):
    """
    Put one scroll of `recipe_name` back in its seeded room, if none exists.

    The staff replenishment path (Launch Minimum LM9: *manual, for the alpha*;
    the runbook line is L4.1's). It ignores the ledger -- that is what makes it
    a deliberate act rather than a side effect of `seed_world()` -- but not the
    world: while a scroll with this seed tag exists anywhere, it spawns nothing.
    It never deletes.

    Args:
        recipe_name (str): a recipe with a row in `seed_data.SCROLLS`.

    Returns:
        Scroll or None: the new scroll, or None if one already exists.

    Raises:
        ValueError: no SCROLLS row names `recipe_name` (a typo must not make
            a scroll the seed does not know about).
        RuntimeError: the seeded room does not exist (run `seed_world()` first).
    """
    spec = _scroll_row(recipe_name)
    if find_seeded(spec["seed_id"]) is not None:
        return None
    return _place_scroll(spec)


def seed_world(limbo=None):
    """
    Build every room, exit and node in `world/seed_data.py` that does not
    exist yet, and place every scroll that has never been placed.

    Args:
        limbo (Object, optional): where the area's entrance exit stands.
            Defaults to settings.DEFAULT_HOME; tests pass their own room.

    Returns:
        dict: {"rooms" | "exits" | "nodes" | "scrolls":
            {"created": int, "skipped": int}}. A scroll in the ledger counts as
            skipped whether or not it still exists.

    Raises:
        RuntimeError, ValueError: no Limbo, an unknown node or scroll
            prototype, or a failed spawn. Deliberately uncaught -- see the
            module docstring.
    """
    limbo = _resolve_limbo(limbo)
    _check_prototypes()

    summary = {
        "rooms": {"created": 0, "skipped": 0},
        "exits": {"created": 0, "skipped": 0},
        "nodes": {"created": 0, "skipped": 0},
        "scrolls": {"created": 0, "skipped": 0},
    }
    # Order matters: exits, nodes and scrolls look their rooms up by seed tag.
    _seed_rooms(summary["rooms"])
    _seed_exits(summary["exits"], limbo)
    _seed_nodes(summary["nodes"])
    _seed_scrolls(summary["scrolls"])
    return summary
