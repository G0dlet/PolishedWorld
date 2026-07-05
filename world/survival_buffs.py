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
    by apply_thermal_stress(). Drives faster hunger/fatigue depletion via mult
    mods. Silent on purpose: it is reset (remove+add) every tick, so onset and
    relief messaging is handled elsewhere (bucket-transition pattern), never here.
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
    and mild fatigue depletion. Silent for the same reason as ColdStress.
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
    Timed post-death debuff: a body clawing back from death burns through food
    and water faster while it recovers.

    Unlike the survival *conditions* (Starving/Dehydrated, duration=-1, cleared
    by the ticker when the gauge recovers), this is SELF-expiring: duration > 0
    makes the buffs contrib schedule its own cleanup via
    utils.delay(duration, cleanup, persistent=True) and fire at_expire when it
    lapses -- verified in evennia/contrib/rpg/buffs/buff.py. No ticker involved.

    The mult mods on 'hunger_rate'/'thirst_rate' are consumed by the exact same
    buffs.check(base, "<key>_rate") calls the survival ticker already makes in
    _deplete_character, so a just-respawned character grows hungry and thirsty
    ~25% faster for the duration. No new integration point is introduced, and
    because respawn resets hunger/thirst to max, this is felt pressure -- not a
    death spiral.

    Design note: this deliberately targets hunger/thirst rather than fatigue,
    because fatigue currently has no consequence when it bottoms out (deferred
    to the future skill-check resolver). Once fatigue exhaustion carries a real
    penalty, switch these mods back to 'fatigue_rate' -- thematically "weak and
    shaken" fits fatigue better than appetite.
    """

    key = "death_weakness"
    name = "Death's Chill"
    flavor = "The chill of near-death lingers; hunger and thirst gnaw as you mend."
    duration = 300          # real seconds; self-expiring. H7.3 will tune this.
    tickrate = 0            # passive mod only; no self-tick
    unique = True
    maxstacks = 1           # re-death refreshes (via remove-then-add), never stacks
    mods = [
        # A body clawing back from death burns through food and water faster
        # while it recovers. These hit hunger_rate/thirst_rate -- the exact
        # checks the survival ticker already makes -- so the penalty is FELT now
        # via the death chokepoint (hungrier/thirstier -> starve -> the same
        # apply_health_damage path we built in H7.2). We avoid fatigue_rate:
        # fatigue has no zero-consequence yet, so that mod would be inert.
        # Modest +25%; hunger/thirst reset to max on respawn, so this is real
        # pressure -- not a death spiral. Dial after playtesting.
        Mod("hunger_rate", "mult", 0, perstack=0.25),
        Mod("thirst_rate", "mult", 0, perstack=0.25),
    ]

    def at_apply(self, *args, **kwargs):
        self.owner.msg("|rYou claw back from the edge of death, weak and shaken.|n")

    def at_expire(self, *args, **kwargs):
        self.owner.msg("|gThe shadow of death lifts; your strength returns.|n")
