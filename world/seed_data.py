"""
The alpha's authored area, as data. Alpha content epic, Task AC3.1.

This module is pure data: no Evennia imports, no logic. `world/seeding.py`
builds it into a database with `seed_world()`; nothing else reads it.

WHY THE WORLD IS DATA IN GIT
----------------------------
A room typed in with `dig` and `desc` lives in one database and nowhere else.
The alpha's area has to come up identically on Adam's dev database, on a fresh
one (AC3.2's setup hook) and on the public test server, so it is written down
here and versioned with the code that depends on it.

SEED IDS
--------
Every room, exit and node has a `seed_id` -- a stable, readable name that the
seeder stores as the tag `(<seed_id>, "seed")` on the object it creates and
looks up before creating it again. The schema:

    alpha.room.<room>                 a room
    alpha.exit.<from-room>.<name>     an exit, named after where it stands
    alpha.node.<room>.<prototype>     a resource node

A seed_id is an identity, not a label: renaming one makes the seeder build a
second object next to the first. Room keys and descs can be reworded freely
here -- but see "CHANGING THIS DATA" below for what that does to a database
that already has the area.

CHANGING THIS DATA
------------------
The seeder skips anything whose seed_id already exists; it never updates an
existing object (no-backfill, and the database is the only writer of a built
world -- a node's `available` and `last_regen`, or a desc a builder edited in
game, must never be overwritten by a re-seed). A change made here therefore
reaches fresh databases only. To push it into an existing one, delete the
object in game and run `seed_world()` again.

THE PLACEMENT RULE (roadmap, Stage 6 entry)
-------------------------------------------
Resource nodes exist only through this seed, and only in `alpha_area` rooms.
At most one node of each prototype per room: two of a kind in one room would
make `forage <node>` a multimatch. `tests/test_seeding.py` asserts all three.

ROOM FIELDS
-----------
    seed_id         see above
    key             the room's name
    desc            the room's description (`db.desc`)
    is_indoor       sheltered: always temperate (world/thermal.py), and no
                    weather echoes (world/weather.py)
    thermal_regime  None = follow season and weather; "cold" / "temperate" /
                    "hot" pins a microclimate (world/thermal.py:thermal_regime)
    spawn_creatures None, or {creature prototype_key: target count}; the
                    seeder also adds the tag CreatureSpawnScript queries
"""

# The one exit that does not start in a seeded room stands in Limbo -- the
# database's DEFAULT_HOME, which the seeder resolves. Limbo itself is created by
# Evennia, not by this seed.
LIMBO = "limbo"

ROOMS = (
    {
        "seed_id": "alpha.room.temple",
        "key": "Old Temple",
        "desc": (
            "Weathered stone pillars hold up a roof of old timber, and the air "
            "inside is still and dry. An altar of grey stone stands at the far "
            "end, worn smooth by many hands. Daylight falls through the open "
            "doorway onto the flagstones."
        ),
        "is_indoor": True,
        "thermal_regime": None,
        "spawn_creatures": None,
    },
    {
        "seed_id": "alpha.room.clearing",
        "key": "Temple Clearing",
        "desc": (
            "A wide clearing opens before the temple steps. Paths of trodden "
            "earth lead north into tall grass, east towards the sound of "
            "running water and west under the trees. A berry bush grows at the "
            "edge, and fallen branches lie where the wind has left them."
        ),
        "is_indoor": False,
        "thermal_regime": None,
        "spawn_creatures": None,
    },
    {
        "seed_id": "alpha.room.meadow",
        "key": "Meadow",
        "desc": (
            "Tall grass and wildflowers sway across an open meadow. Fibrous "
            "plants grow thick among the grass, and a gourd vine trails over "
            "the ground. Small tracks wind between the tussocks."
        ),
        "is_indoor": False,
        "thermal_regime": None,
        "spawn_creatures": {"rabbit": 3},
    },
    {
        "seed_id": "alpha.room.brook",
        "key": "Brook",
        "desc": (
            "A clear brook runs over pebbles here, fed by a spring that wells "
            "up between mossy stones. Its bank is a slope of grey clay, slick "
            "where the water has worked at it."
        ),
        "is_indoor": False,
        "thermal_regime": None,
        "spawn_creatures": None,
    },
    {
        "seed_id": "alpha.room.woods",
        "key": "Edge of the Woods",
        "desc": (
            "Old trees stand close together, their branches meeting overhead. "
            "The ground is soft with fallen leaves. To the north it rises "
            "towards bare rock; to the east the clearing shows between the "
            "trunks."
        ),
        "is_indoor": False,
        "thermal_regime": None,
        "spawn_creatures": {"rabbit": 1},
    },
    {
        "seed_id": "alpha.room.ridge",
        "key": "Stony Ridge",
        "desc": (
            "The trees give way to a bare ridge of broken rock. Stone juts from "
            "the hillside in rough outcrops, and dark nodules of flint lie "
            "scattered among the scree."
        ),
        "is_indoor": False,
        "thermal_regime": None,
        "spawn_creatures": None,
    },
)

# "from" and "to" are seed_ids (or LIMBO). Every passage inside the area is two
# exits, one each way; the Limbo exit is one-way -- Limbo is admin space.
EXITS = (
    {"seed_id": "alpha.exit.limbo.temple", "key": "temple", "aliases": [],
     "from": LIMBO, "to": "alpha.room.temple"},

    {"seed_id": "alpha.exit.temple.out", "key": "out", "aliases": ["o"],
     "from": "alpha.room.temple", "to": "alpha.room.clearing"},
    {"seed_id": "alpha.exit.clearing.temple", "key": "temple", "aliases": ["in"],
     "from": "alpha.room.clearing", "to": "alpha.room.temple"},

    {"seed_id": "alpha.exit.clearing.north", "key": "north", "aliases": ["n"],
     "from": "alpha.room.clearing", "to": "alpha.room.meadow"},
    {"seed_id": "alpha.exit.meadow.south", "key": "south", "aliases": ["s"],
     "from": "alpha.room.meadow", "to": "alpha.room.clearing"},

    {"seed_id": "alpha.exit.clearing.east", "key": "east", "aliases": ["e"],
     "from": "alpha.room.clearing", "to": "alpha.room.brook"},
    {"seed_id": "alpha.exit.brook.west", "key": "west", "aliases": ["w"],
     "from": "alpha.room.brook", "to": "alpha.room.clearing"},

    {"seed_id": "alpha.exit.clearing.west", "key": "west", "aliases": ["w"],
     "from": "alpha.room.clearing", "to": "alpha.room.woods"},
    {"seed_id": "alpha.exit.woods.east", "key": "east", "aliases": ["e"],
     "from": "alpha.room.woods", "to": "alpha.room.clearing"},

    {"seed_id": "alpha.exit.woods.north", "key": "north", "aliases": ["n"],
     "from": "alpha.room.woods", "to": "alpha.room.ridge"},
    {"seed_id": "alpha.exit.ridge.south", "key": "south", "aliases": ["s"],
     "from": "alpha.room.ridge", "to": "alpha.room.woods"},
)

# One node of each of the nine node prototypes. The stone axe's three inputs
# (flint, stick, fiber for twine) sit in three different rooms and the tree it
# fells two steps from the temple, so that distance means something once
# weight does (AD8).
NODES = (
    {"seed_id": "alpha.node.clearing.berry_bush",
     "room": "alpha.room.clearing", "prototype": "berry_bush"},
    {"seed_id": "alpha.node.clearing.stick_deadfall",
     "room": "alpha.room.clearing", "prototype": "stick_deadfall"},
    {"seed_id": "alpha.node.meadow.fiber_plant",
     "room": "alpha.room.meadow", "prototype": "fiber_plant"},
    {"seed_id": "alpha.node.meadow.gourd_vine",
     "room": "alpha.room.meadow", "prototype": "gourd_vine"},
    {"seed_id": "alpha.node.brook.spring",
     "room": "alpha.room.brook", "prototype": "spring"},
    {"seed_id": "alpha.node.brook.clay_bank",
     "room": "alpha.room.brook", "prototype": "clay_bank"},
    {"seed_id": "alpha.node.woods.tree",
     "room": "alpha.room.woods", "prototype": "tree"},
    {"seed_id": "alpha.node.ridge.stone_outcrop",
     "room": "alpha.room.ridge", "prototype": "stone_outcrop"},
    {"seed_id": "alpha.node.ridge.flint_scatter",
     "room": "alpha.room.ridge", "prototype": "flint_scatter"},
)
