"""
Survival condition buffs (Evennia buffs contrib).

These are thin *marker* buffs applied when a survival gauge bottoms out.
They do not tick or damage anything themselves (tickrate stays 0): the HP
damage is applied centrally in the survival ticker, keeping all survival
timing in one place. Their job is flavor messaging on onset/removal, plus a
hook point for future skill-check penalties.

duration = -1  -> permanent; the condition persists until the ticker removes
it when the gauge recovers above its minimum.

playtime stays False: offline safety is guaranteed by the survival ticker
iterating only online characters, not by buff autopause. Setting playtime
True without autopause=True on the handler would be inert and misleading.
"""

from evennia.contrib.rpg.buffs import BaseBuff, Mod


class Starving(BaseBuff):
    key = "starving"
    name = "Starving"
    flavor = "You are wasting away from hunger."
    duration = -1          # permanent until removed by the ticker
    tickrate = 0           # does not self-tick; damage is applied by the ticker
    unique = True

    def at_apply(self, *args, **kwargs):
        self.owner.msg("|rYour stomach twists with hunger pangs.|n")

    def at_remove(self, *args, **kwargs):
        self.owner.msg("|gThe gnawing hunger in your belly begins to ease.|n")


class Dehydrated(BaseBuff):
    key = "dehydrated"
    name = "Dehydrated"
    flavor = "You are dangerously dehydrated."
    duration = -1
    tickrate = 0
    unique = True

    def at_apply(self, *args, **kwargs):
        self.owner.msg("|rYour throat is parched and your head pounds.|n")

    def at_remove(self, *args, **kwargs):
        self.owner.msg("|gThe worst of your thirst subsides.|n")


class ColdStress(BaseBuff):
    """
    Silent thermal marker: the wearer is underdressed for the cold.

    Stacks = cold_stress from world.thermal.thermal_stress, set fresh each tick
    by apply_thermal_stress(). Drives faster hunger depletion and a shorter
    waking day (the awake clock counts `fatigue_rate`, S3.3) via mult mods. Silent on purpose: it is reset (remove+add) every tick, so an onset or
    relief message in its hooks would fire every tick. No message, command or
    `status` line names the stress yet; the worded state with a direction is
    roadmap *Temperature & exposure* (docs/system_designs/
    PolishedWorld_Temperature_Design.md, J1, KP1-KP2).
    """
    key = "cold_stress"
    name = "Cold"
    duration = -1
    tickrate = 0
    unique = True
    maxstacks = 20
    mods = [
        Mod("hunger_rate", "mult", 0, perstack=0.08),
        Mod("fatigue_rate", "mult", 0, perstack=0.08),
    ]


class HeatStress(BaseBuff):
    """
    Silent thermal marker: overdressed for the heat (or a hot climate).

    Stacks = heat_stress from world.thermal.thermal_stress. Drives faster thirst
    depletion and a mildly shorter waking day (S3.3). Silent for the same
    reason as ColdStress.
    """
    key = "heat_stress"
    name = "Overheated"
    duration = -1
    tickrate = 0
    unique = True
    maxstacks = 20
    mods = [
        Mod("thirst_rate", "mult", 0, perstack=0.10),
        Mod("fatigue_rate", "mult", 0, perstack=0.04),
    ]


class DeathWeakness(BaseBuff):
    """
    Timed post-death debuff, Death's Chill: a body clawing back from death
    tires sooner while it recovers.

    Unlike the survival *conditions* (Starving/Dehydrated, duration=-1, cleared
    by the ticker when the gauge recovers), this is SELF-expiring: duration > 0
    makes the buffs contrib schedule its own cleanup via
    utils.delay(duration, cleanup, persistent=True) and fire at_expire when it
    lapses -- verified in evennia/contrib/rpg/buffs/buff.py. No ticker involved.

    Its one mod is a mult on 'fatigue_rate' (Survival Loop S3.5, SL12; Rest
    Design NQ14). Since S3.3 that rate scales the awake clock, not a drain:
    `world.fatigue.advance_clock` adds a tick's game seconds times
    `buffs.check(seconds, "fatigue_rate")` to `db.awake_seconds`, so the
    waking day runs 25% faster while the chill lasts. Hunger and thirst are
    untouched: before S3.5 the chill's two mods sat on 'hunger_rate' and
    'thirst_rate'.

    Read plainly, the mod is small: the buff lasts 300 real seconds and the
    survival tick runs every 600, so at most one tick falls inside it. The
    consequence is the level -- `at_character_death` sets fatigue to Wearied
    (`fatigue.RESPAWN_AT`) and zeroes the clock -- and this buff is its name
    and timer until Rest slice 2 or Temperature give 'fatigue_rate' more to
    do. Rest, not the timer, lifts Wearied; the death message says so.
    """

    key = "death_weakness"
    name = "Death's Chill"
    flavor = "The chill of near-death sits in your bones; the day tires you sooner."
    duration = 300          # real seconds; self-expiring. H7.3 will tune this.
    tickrate = 0            # passive mod only; no self-tick
    unique = True
    maxstacks = 1           # re-death refreshes (via remove-then-add), never stacks
    mods = [
        # "Weak and shaken" is tiredness (SL12): the awake clock's own rate,
        # the check `advance_clock` already makes, so no new integration point.
        # +25%; the respawn level, not this mod, is what the player feels.
        Mod("fatigue_rate", "mult", 0, perstack=0.25),
    ]

    def at_apply(self, *args, **kwargs):
        self.owner.msg("|rYou claw back from the edge of death, weak and shaken.|n")

    def at_expire(self, *args, **kwargs):
        self.owner.msg("|gThe shadow of death lifts; your strength returns.|n")
