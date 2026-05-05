# -*- coding: utf-8 -*-
"""
Connection screen

This is the text to show the user when they first connect to the game (before
they log in).

To change the login screen in this module, do one of the following:

- Define a function `connection_screen()`, taking no arguments. This will be
  called first and must return the full string to act as the connection screen.
  This can be used to produce more dynamic screens.
- Alternatively, define a string variable in the outermost scope of this module
  with the connection string that should be displayed. If more than one such
  variable is given, Evennia will pick one of them at random.

The commands available to the user when the connection screen is shown
are defined in evennia.default_cmds.UnloggedinCmdSet. The parsing and display
of the screen is done by the unlogged-in "look" command.

"""

from django.conf import settings

from evennia import utils

CONNECTION_SCREEN = r"""
|y
 ____       _ _     _              _   __        __         _     _ 
!  _ \ ___ ! (_)___! !__   ___  __! !  \ \      / /__  _ __! ! __! !
! !_) / _ \! ! / __! '_ \ / _ \/ _` !   \ \ /\ / / _ \! '__! !/ _` !
!  __/ (_) ! ! \__ \ ! ! !  __/ (_! !    \ V  V / (_) ! !  ! ! (_! !
!_!   \___/!_!_!___/_! !_!\___!\__,_!     \_/\_/ \___/!_!  !_!\__,_!
|n
              |W---|n  |WA frontier survival realm|n  |W---|n

         |xPowered by Evennia  -  Mongoose Legend d100|n
""".format(
    settings.SERVERNAME, utils.get_evennia_version("short")
)
