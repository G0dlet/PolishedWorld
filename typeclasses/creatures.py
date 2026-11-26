"""
Creature typeclass.

Passive, non-puppetable fauna that players can hunt for food and crafting
materials. A Creature has no AI and does not fight back -- hunting is resolved as
a single Mongoose Legend skill check (commands/hunting_commands.py, Task H2.2),
not as combat rounds. This keeps the hunt -> corpse -> harvest loop decoupled
from a combat system that does not exist yet.

A Creature carries the data the downstream tasks read:

    siz              -- Mongoose Legend SIZ; scales harvest yield (H4).
    natural_ap       -- natural armour, reserved for a future combat/skinning axis.
    harvest_template -- key into the harvest tables (H4.2); decides which parts
                        its corpse yields.
    flee_skill       -- opposed value the hunt check rolls against (H2.2).
    con              -- Mongoose Legend CON, set by the prototype; None for a
                        creature that has none and cannot be hurt (CE3, CE13).
    resilience       -- set only where the book's row leaves CON x 3 + 10
                        (CE7). Both are read through world.creature_wounds.

What the creature's hurt stores -- `general_damage` and `damage_source` --
is not declared here: world.creature_wounds owns it, writes it only in its
door, and reads it through `damage_of` (CE-T2).

`at_death()` is intentionally a minimal stub here: it announces the kill and
removes the creature. Task H3.2 overrides the body to spawn a Corpse first, once
the Corpse typeclass (H3.1) exists. Defining the seam now lets the hunt command
(H2.2) call a stable method without H1.1 depending on code not yet written.
"""

from evennia import AttributeProperty
from evennia.objects.objects import DefaultObject

from .objects import ObjectParent
from evennia.utils.create import create_object

from world import creature_wounds, gametime_utils
from typeclasses.corpse import Corpse


class Creature(ObjectParent, DefaultObject):
    """
    A passive, huntable creature.

    Stationary and non-aggressive. It exists to be found in a room, hunted via a
    skill check, and converted into a harvestable corpse on death. It is a plain
    object (not a Character): no account, no cmdset, no per-creature AI ticker --
    renewability is handled centrally by CreatureSpawnScript (H1.3), which is far
    cheaper than per-creature scripts once many creatures exist.
    """

    # --- Mongoose Legend / harvest data -------------------------------------
    # autocreate=True so every creature has a real db.<attr> row that downstream
    # systems (hunt check, harvest yield) read without a None guard.
    siz = AttributeProperty(default=8, autocreate=True)
    natural_ap = AttributeProperty(default=0, autocreate=True)
    harvest_template = AttributeProperty(default="rabbit", autocreate=True)
    flee_skill = AttributeProperty(default=30, autocreate=True)

    # --- Constitution (Creatures CE3, CE7, CE13) ------------------------------
    # autocreate=False, unlike the four above, and written out because
    # Evennia's default is True: here None *is* the answer -- no CON, no Hit
    # Points -- so a row holding None says nothing, and a read must not write
    # one. Only the prototype writes them.
    con = AttributeProperty(default=None, autocreate=False)
    resilience = AttributeProperty(default=None, autocreate=False)

    def at_object_creation(self):
        """Lock the creature so it cannot be picked up, given, or traded."""
        super().at_object_creation()
        # get:false() -> `get <creature>` is refused. A live animal is not loot;
        # only its corpse (H3) is. This also blocks carrying a creature in
        # inventory or pushing it through barter as if it were an item.
        self.locks.add("get:false()")

    def apply_health_damage(self, amount, *, location, source=None, made=None):
        """
        The one door for a creature's hurt, with a character's name and
        arguments (Creatures CE9; Combat Design PV2, PD1): ML's blow and
        PJ's shot both come here. It puts the amount on the creature
        through `creature_wounds.damage`, which checks and writes, and
        carries out the death the answer gives (CE5).

        Args:
            amount (int): what got through the armour (WO6). 0 or less
                writes nothing.
            location (str): checked as a character's is (WO5) and not used:
                General Hit Points have no locations.
            source (Object, str or None): what dealt the blow; stored. Only
                an object reaches `at_death` as the killer -- a string, as
                the survival ticker gives a character, would be asked to
                `msg()` half-way through the death -- so anything else dies
                with no killer, and the room reads *dies*.
            made (dict or None): the attack roll's successful `skill_check`
                dict, when the source has one.

        Raises:
            ValueError: from `creature_wounds.damage`, before anything is
                written -- among them a creature without CON (CE13).

        Returns:
            dict or None: the door's answer -- None if nothing was written,
                else {"dies", "hit_points"} -- for the caller to read.
        """
        outcome = creature_wounds.damage(self, amount, location, made, source=source)
        if outcome and outcome["dies"]:
            self.at_death(source if isinstance(source, DefaultObject) else None)
        return outcome

    def at_death(self, killer=None):
        """
        Resolve this creature's death.

        H1.1 STUB: announce the kill and delete the creature. Task H3.2 will
        override this to spawn a Corpse (carrying siz / harvest_template /
        death_time) at this location *before* deleting, wiring the
        hunt -> corpse half of the loop.

        Args:
            killer (Object or None): the hunter, for messaging/attribution.

        Guarded against double resolution: if two actions race to kill the same
        creature in one tick, only the first does the work. H2.2 adds a
        hunt-time lock as the primary guard; this `pk` check is defence in depth.
        """
        if not self.pk:
            # Already deleted (e.g. resolved by a concurrent action this tick).
            return

        location = self.location
        if location:
            if killer:
                # The killer per reader (Names NM-T10); the creature by key,
                # one name for every reader, as its corpse is.
                location.msg_contents(
                    f"$You() fells {self.key}.", from_obj=killer, exclude=[killer]
                )
                killer.msg(f"You fell {self.get_display_name(killer)}.")
            else:
                location.msg_contents(f"{self.key} dies.")

        # Spawn the harvestable corpse BEFORE deleting the creature, copying
            # the data H4 needs to compute yields. death_time uses the SAME
            # accessor as Corpse's lazy decay (gametime_utils.get_absolute_gametime)
            # so the elapsed-time diff is meaningful. We already hold `location`.
            create_object(
                Corpse,
                key=f"{self.key} corpse",
                location=location,
                attributes=[
                    ("creature_siz", self.db.siz),
                    ("creature_type", self.db.harvest_template),
                    ("creature_natural_ap", self.db.natural_ap),
                    ("death_time", gametime_utils.get_absolute_gametime()),
                    ("desc", f"The lifeless body of a {self.key}."),
                ],
            )

        self.delete()
