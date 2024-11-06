"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""

from evennia.objects.objects import DefaultCharacter

from .objects import ObjectParent


class Character(ObjectParent, DefaultCharacter):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like this.

    """

    pass


class CharacterBase(Character):
    def at_object_creation(self):
        super().at_object_creation()
        self.db.strength = 10
        self.db.dexterity = 10
        self.db.constitution = 10
        self.db.intelligence = 10
        self.db.wisdom = 10
        self.db.charisma = 10
        self.db.hp = 10
        self.db.level = 1
        self.db.xp = 0
