# commands/default_cmdsets.py (uppdaterad med survival commands)
"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.

"""

from evennia import default_cmds
from commands.time_commands import CmdTime, CmdUptime
from commands.search_commands import CmdSearch, CmdLight
from commands.resource_commands import CmdGather, CmdForage
from commands.survival_commands import CmdRest, CmdEat, CmdDrink, CmdStatus
from evennia.contrib.grid.extended_room import ExtendedRoomCmdSet
from evennia.contrib.game_systems.clothing.clothing import ClothedCharacterCmdSet
from commands.clothing_commands import CmdClothingStatus, CmdRepair


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands like `look`,
    `get`, etc available on in-game Character objects. It is merged with
    the `AccountCmdSet` when an Account puppets a Character.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        # Add time-related commands
        self.add(CmdTime())
        self.add(CmdUptime())

        # Add Extended Room commands (includes enhanced look)
        self.add(ExtendedRoomCmdSet)
        
        # Add search and light commands
        self.add(CmdSearch())
        self.add(CmdLight())
        
        # Add resource gathering commands
        self.add(CmdGather())
        self.add(CmdForage())
        
        # Add survival commands
        self.add(CmdRest())
        self.add(CmdEat())
        self.add(CmdDrink())
        self.add(CmdStatus())

        # Add clothing commands
        self.add(ClothedCharacterCmdSet)
        self.add(CmdClothingStatus())
        self.add(CmdRepair())


class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    This is the cmdset available to the Account at all times. It is
    combined with the `CharacterCmdSet` when the Account puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """

    key = "DefaultAccount"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """

    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    This cmdset is made available on Session level once logged in. It
    is empty by default.
    """

    key = "DefaultSession"

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
