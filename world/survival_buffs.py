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

from evennia.contrib.rpg.buffs import BaseBuff


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
