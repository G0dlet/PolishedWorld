from enum import Enum

class Ability(Enum):
    """
    The six abilities
    """

    STR = "strength"
    INT = "intelligence"
    WIS = "wisdom"
    DEX = "dexterity"
    CON = "constitution"
    CHA = "charisma"


ABILITY_REVERSE_MAP = {
    "str": Ability.STR,
    "int": Ability.INT,
    "wis": Ability.WIS,
    "dex": Ability.DEX,
    "con": Ability.CON,
    "CHA": Ability.CHA,
}
