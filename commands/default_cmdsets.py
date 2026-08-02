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
from evennia.contrib.grid import extended_room
from evennia.contrib.game_systems.crafting.crafting import CraftingCmdSet
from evennia.contrib.game_systems.containers.containers import CmdContainerGet
from commands import character_commands
from commands.admin_commands import CmdWeather
from commands.consumption_commands import CmdEat, CmdDrink, CmdRest
from commands.foraging_commands import CmdForage, CmdRefill
from commands.hunting_commands import CmdHunt, CmdHarvest
from commands.repair_commands import CmdRepair
from commands.currency_commands import CmdWallet, CmdPay, CmdEconomy
from commands.work_commands import CmdWork
from commands.crafting_commands import (
    CmdCraftGated,
    CmdRecipes,
    CmdDisassemble,
    CmdInscribe,
    CmdScribe,
    CmdTeach,
    CmdLearn,
)
from world.barter import CmdPWTrade
# Clothing commands. Verified: NOT re-exported from the package __init__, must
# come from the submodule. We cherry-pick individual commands rather than adding
# ClothedCharacterCmdSet, which subclasses Evennia's DEFAULT CharacterCmdSet
# (clothing.py:702) and would re-run a foreign at_cmdset_creation on top of ours.
from evennia.contrib.game_systems.clothing.clothing import (
    CmdWear,
    CmdRemove,
    CmdCover,
    CmdUncover,
    CmdInventory,
)

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
        self.add(character_commands.CmdStatus())
        self.add(character_commands.CmdStats())
        self.add(character_commands.CmdSkills())
        self.add(character_commands.CmdSheet())
        self.add(character_commands.CmdProgress())
        self.add(character_commands.CmdChooseProfession())

        # Extended Room commands for seasonal/time-based room descriptions
        self.add(extended_room.ExtendedRoomCmdSet)

        self.add(CmdWeather())

        self.add(CmdEat())
        self.add(CmdDrink())
        self.add(CmdRest())

        self.add(CmdForage())
        self.add(CmdRefill())
        self.add(CmdHunt())
        self.add(CmdHarvest())

        self.add(CraftingCmdSet)
        # CmdCraftGated (key="craft") is added AFTER CraftingCmdSet so it
        # overrides the contrib's stock CmdCraft in the merged set: an unknown
        # advanced recipe is rejected before ingredient search (Component B.2).
        # pre_craft (B.1) stays the authoritative backstop for craft() callers
        # that bypass this command (barter-craft, scripts).
        self.add(CmdCraftGated())
        # CmdRecipes (key="recipes", alias "recipe") -- discovery surface for
        # Stage 3 (Component C.1): solves that stock `craft` lists nothing.
        # Unique key/alias, so no collision with look/ExtendedRoomCmdSet
        # (the H7.3b lesson). Read-only; no state added.
        self.add(CmdRecipes())
        # CmdDisassemble (key="disassemble", alias "salvage") -- the first item
        # knowledge channel (Component E.2). Unique key/alias, no collision.
        # Reverse-engineers player-crafted goods (E.1 stamp); Craft-gated so it
        # doesn't undercut the paid scroll/teach channels.
        self.add(CmdDisassemble())
        # CmdInscribe (key="inscribe") -- the first *written* knowledge channel
        # (Component F.1). A master crafter writes a one-use recipe scroll another
        # player can `learn` from. Unique key -> no ExtendedRoomCmdSet clash.
        self.add(CmdInscribe())
        # CmdScribe (key="scribe") -- the *bulk* written channel (Component G.2):
        # a professional crafter binds several mastered recipes into a perishable
        # book others `learn ... from`. Unique key -> no ExtendedRoomCmdSet clash.
        self.add(CmdScribe())
        # CmdTeach (key="teach") -- the LIVE knowledge channel (Component H.1):
        # offer a mastered recipe to another player in the room; they accept with
        # `learn <recipe> from <teacher>`. Unique key -- verified against the
        # default CharacterCmdSet and every contrib cmdset we merge in, and
        # deliberately NOT keyed `accept`: barter's CmdAccept lives in
        # CmdsetTrade, which is added at the same priority (0) as this set, and
        # Evennia's Union merge drops the LATER set's same-keyed command on a
        # priority tie -- a global `accept` here would silently disable accepting
        # inside a trade. (The H7.3b look/ExtendedRoomCmdSet lesson, again.)
        self.add(CmdTeach())
        # CmdLearn (key="learn") -- closes the scroll channel (Component F.2):
        # study a scroll to gain its recipe permanently, consuming the scroll.
        # Extended to books in G.3 and to live teachers in H.1: `learn` is the
        # student's verb for every knowledge carrier, so the teach handshake needs
        # no new key at all.
        self.add(CmdLearn())
        self.add(CmdRepair())

        # Currency (Stage 4, Component B). Both keys verified free against the
        # default CharacterCmdSet and every contrib we merge, including barter's
        # runtime CmdsetTrade (decomposition section 5).
        # CmdWallet (key="wallet", alias "purse") -- read-only balance. "coins"
        # is deliberately NOT an alias: when CoinPile lands in Stage 5 it would
        # read as both a command and an object lying in the room.
        self.add(CmdWallet())
        # CmdPay (key="pay") -- the only player-facing way to move coin outside
        # a trade session. Same-room by design, not by omission (see the module
        # docstring). Deliberately NOT keyed on `give`, which the default cmdset
        # owns for objects: coin is an integer, not an object (S4-2), and must
        # not learn object verbs it cannot honour.
        self.add(CmdPay())
        # CmdEconomy (key="@economy") -- Developer-locked admin surface, and the
        # only production caller of the mint primitive (C.2). Note this is the
        # FIRST cmd:perm(Developer) command in the codebase: CmdWeather above is
        # perm(Builder), which is right for weather and wrong here. Builders
        # build rooms; they do not create money.
        self.add(CmdEconomy())
        # CmdWork (key="work") -- the temple faucet (Component D.1), the
        # cold-start answer for a player with nothing and no crypto. Key
        # verified free against the whole inventory: zero hits for `work` as a
        # key or alias anywhere in Evennia's default cmdsets, in any contrib we
        # merge, or in our own commands.
        #
        # It pays by TRANSFERRING out of the Treasury and never by minting
        # (S4-1). `add()` keeps exactly one production caller, CmdEconomy above.
        self.add(CmdWork())

        self.add(CmdPWTrade())

        # Clothing: wear/remove/cover/uncover. CmdInventory overrides the
        # default 'inventory' (inv, i) to split worn vs carried items — useful
        # once clothing exists; drop that one line if you'd rather keep default inv.
        self.add(CmdWear())
        self.add(CmdRemove())
        self.add(CmdCover())
        self.add(CmdUncover())
        self.add(CmdInventory())

        # Corpse/container looting: replaces stock 'get' with a version that also
        # supports 'get <obj> from <container>' (checks the container's get_from
        # lock). Deliberately NOT the full ContainerCmdSet -- that bundles
        # CmdContainerLook, which would clobber extended_room's seasonal look.
        # Plain 'get <obj>' is unchanged. Full put/storage containers are a
        # later task (see decomp section 13).
        self.add(CmdContainerGet())


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
