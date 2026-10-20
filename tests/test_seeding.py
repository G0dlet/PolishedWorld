"""
Unit tests for the alpha area's seed data and seeder. Alpha content epic,
Task AC3.1.

These run the shipped `seed_data` through the shipped `seed_world()` into the
test database: what fails here fails on a fresh database.

WHAT IS WORTH TESTING HERE
--------------------------
1. **A second run builds nothing.** The whole point of the seeder: AC3.2 calls
   it on every fresh database and Adam calls it on his existing one. Counted
   twice -- by the summary and by the database -- because a summary can lie.
2. **It skips, it never syncs.** A desc edited in game survives a re-seed, and
   a deleted object comes back alone. This pins seed_data's "CHANGING THIS
   DATA" promise from both sides.
3. **The placement rule** (roadmap, Stage 6 entry): every ResourceNode in the
   database stands in an `alpha_area` room and carries a seed tag and its
   prototype's `from_prototype` tag; all nine
   node prototypes are placed, at most one of each per room; and each node
   answers to its own key the way `forage` searches, without a multimatch.
4. **Spawn rooms** are found by the query CreatureSpawnScript itself runs, and
   carry the config it reads; rooms that are not spawn rooms are not found.
5. **The Treasury is not seeded** (AD7). It is found by dbref, not by tag, so
   the test counts its typeclass in the whole database.
6. **The data is sound before it is built**: unique seed_ids, every node
   prototype resolves, every room carries its desc, is_indoor and
   thermal_regime, every exit joins the rooms it names, every room can be
   reached from Limbo and every passage leads back, and a missing
   Limbo stops the seeder before it creates anything.

HOW TO RUN
----------
    evennia test --settings settings.py tests.test_seeding
"""
from django.test import override_settings
from evennia.objects.models import ObjectDB
from evennia.prototypes.prototypes import search_prototype
from evennia.utils.search import search_tag
from evennia.utils.test_resources import EvenniaTest

from world import seed_data
from world.thermal import thermal_regime
from world.seeding import (
    AREA_TAG,
    SEED_CATEGORY,
    SPAWN_TAG,
    find_seeded,
    seed_world,
)

NODE_TYPECLASS = "typeclasses.resources.ResourceNode"


def seeded_objects():
    return list(ObjectDB.objects.get_by_tag(category=SEED_CATEGORY))


class SeedingBase(EvenniaTest):
    """room1 stands in for Limbo; char1 is the forager in test 3."""

    character_typeclass = "typeclasses.characters.Character"

    def seed(self):
        return seed_world(limbo=self.room1)


class TestIdempotency(SeedingBase):
    def test_second_run_creates_nothing(self):
        first = self.seed()
        self.assertEqual(first, {
            "rooms": {"created": len(seed_data.ROOMS), "skipped": 0},
            "exits": {"created": len(seed_data.EXITS), "skipped": 0},
            "nodes": {"created": len(seed_data.NODES), "skipped": 0},
        })
        total = len(seed_data.ROOMS) + len(seed_data.EXITS) + len(seed_data.NODES)
        self.assertEqual(len(seeded_objects()), total)

        second = self.seed()
        self.assertEqual(second, {
            "rooms": {"created": 0, "skipped": len(seed_data.ROOMS)},
            "exits": {"created": 0, "skipped": len(seed_data.EXITS)},
            "nodes": {"created": 0, "skipped": len(seed_data.NODES)},
        })
        # The database agrees with the summary.
        self.assertEqual(len(seeded_objects()), total)

    def test_reseed_skips_existing_and_rebuilds_only_the_missing(self):
        self.seed()
        temple = find_seeded("alpha.room.temple")
        temple.db.desc = "edited in game"
        find_seeded("alpha.node.woods.tree").delete()

        summary = self.seed()

        self.assertEqual(summary["nodes"], {"created": 1, "skipped": len(seed_data.NODES) - 1})
        self.assertEqual(summary["rooms"]["created"], 0)
        # Skip, not sync: the builder's edit wins over the seed's desc.
        self.assertEqual(find_seeded("alpha.room.temple").db.desc, "edited in game")
        tree = find_seeded("alpha.node.woods.tree")
        self.assertEqual(tree.location, find_seeded("alpha.room.woods"))


class TestPlacementRule(SeedingBase):
    def test_every_resource_node_is_seeded_and_in_the_alpha_area(self):
        self.seed()
        nodes = [o for o in ObjectDB.objects.all() if o.is_typeclass(NODE_TYPECLASS, exact=False)]
        self.assertEqual(len(nodes), len(seed_data.NODES))  # vacuity guard
        for node in nodes:
            with self.subTest(node=node.key):
                seed_id = node.tags.get(category=SEED_CATEGORY)
                self.assertTrue(seed_id)
                # Spawned from its shipped prototype, and tagged as such.
                prototype = next(n["prototype"] for n in seed_data.NODES if n["seed_id"] == seed_id)
                self.assertTrue(node.tags.has(prototype, category="from_prototype"))
                self.assertTrue(node.location.tags.has(AREA_TAG[0], category=AREA_TAG[1]))

    def test_all_node_prototypes_are_placed_once_per_room_at_most(self):
        shipped = {
            p["prototype_key"] for p in search_prototype(no_db=True)
            if p.get("typeclass") == NODE_TYPECLASS
        }
        placed = [n["prototype"] for n in seed_data.NODES]
        self.assertEqual(set(placed), shipped)
        pairs = [(n["room"], n["prototype"]) for n in seed_data.NODES]
        self.assertEqual(len(pairs), len(set(pairs)))

    def test_each_node_answers_to_its_own_key_as_forage_searches(self):
        self.seed()
        for spec in seed_data.ROOMS:
            room = find_seeded(spec["seed_id"])
            self.char1.location = room
            # The same candidates CmdForage builds (commands/foraging_commands.py).
            nodes = [o for o in room.contents if o.is_typeclass(NODE_TYPECLASS, exact=False)]
            for node in nodes:
                with self.subTest(room=room.key, node=node.key):
                    self.assertEqual(self.char1.search(node.key, candidates=nodes), node)


class TestSpawnRooms(SeedingBase):
    def test_spawn_rooms_are_found_by_the_scripts_query_with_their_config(self):
        self.seed()
        expected = {
            r["seed_id"]: r["spawn_creatures"] for r in seed_data.ROOMS if r["spawn_creatures"]
        }
        self.assertTrue(expected)  # vacuity guard
        # CreatureSpawnScript.at_repeat's own query (typeclasses/scripts.py).
        found = list(search_tag(SPAWN_TAG[0], category=SPAWN_TAG[1]))
        self.assertEqual(
            {r.tags.get(category=SEED_CATEGORY) for r in found}, set(expected)
        )
        for room in found:
            seed_id = room.tags.get(category=SEED_CATEGORY)
            with self.subTest(room=seed_id):
                self.assertEqual(dict(room.db.spawn_creatures), expected[seed_id])
                for creature in room.db.spawn_creatures:
                    proto = search_prototype(key=creature, no_db=True)
                    self.assertEqual(len(proto), 1)


class TestNoTreasury(SeedingBase):
    def test_no_treasury_exists_after_seeding(self):
        self.seed()
        self.assertTrue(seeded_objects())  # vacuity guard: seeding ran
        treasuries = ObjectDB.objects.filter(db_typeclass_path__startswith="typeclasses.treasury")
        self.assertEqual(treasuries.count(), 0)


class TestSeedData(SeedingBase):
    def test_seed_ids_are_unique(self):
        ids = [x["seed_id"] for x in seed_data.ROOMS + seed_data.EXITS + seed_data.NODES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_node_prototype_resolves_to_a_resource_node(self):
        for spec in seed_data.NODES:
            with self.subTest(node=spec["seed_id"]):
                found = search_prototype(key=spec["prototype"], no_db=True)
                self.assertEqual(len(found), 1)
                self.assertEqual(found[0]["typeclass"], NODE_TYPECLASS)

    def test_rooms_carry_their_data(self):
        self.seed()
        for spec in seed_data.ROOMS:
            with self.subTest(room=spec["seed_id"]):
                room = find_seeded(spec["seed_id"])
                self.assertEqual(room.key, spec["key"])
                self.assertEqual(room.db.desc, spec["desc"])
                self.assertEqual(room.db.is_indoor, spec["is_indoor"])
                self.assertEqual(room.db.thermal_regime, spec["thermal_regime"])
        # What is_indoor is for: the temple is temperate whatever the season.
        self.assertEqual(thermal_regime(find_seeded("alpha.room.temple")), "temperate")

    def test_exits_join_the_rooms_they_name(self):
        self.seed()
        for spec in seed_data.EXITS:
            with self.subTest(exit=spec["seed_id"]):
                ex = find_seeded(spec["seed_id"])
                source = (self.room1 if spec["from"] == seed_data.LIMBO
                          else find_seeded(spec["from"]))
                self.assertEqual(ex.location, source)
                self.assertEqual(ex.destination, find_seeded(spec["to"]))
        limbo_exits = [e for e in seed_data.EXITS if e["from"] == seed_data.LIMBO]
        self.assertEqual(len(limbo_exits), 1)

    def test_every_room_is_reachable_and_every_passage_leads_back(self):
        # Walks the built exits, not the data, so a mistyped "to" shows up as
        # what it is in game: a one-way trap or a room nobody can reach.
        self.seed()
        rooms = {find_seeded(r["seed_id"]) for r in seed_data.ROOMS}
        reached, frontier = set(), [self.room1]
        while frontier:
            here = frontier.pop()
            for ex in here.exits:
                there = ex.destination
                if there in rooms and there not in reached:
                    reached.add(there)
                    frontier.append(there)
        self.assertEqual(reached, rooms)
        for room in rooms:
            for ex in room.exits:
                with self.subTest(exit=f"{room.key} -> {ex.key}"):
                    self.assertIn(room, [back.destination for back in ex.destination.exits])

    @override_settings(DEFAULT_HOME="#999999")
    def test_missing_limbo_stops_before_anything_is_built(self):
        with self.assertRaises(RuntimeError):
            seed_world()
        self.assertEqual(seeded_objects(), [])
