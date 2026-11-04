"""
In-game bug, idea and player reports (BACKLOG *In-game bug, idea and player
reports -- `ingame_reports`*, locked 2026-11-04).

The commands are Evennia's `evennia.contrib.base_systems.ingame_reports`
(verified at the pinned v6.1.0). Two things differ from installing its
`ReportsCmdSet` on the AccountCmdSet, as its docstring suggests:

1. One read lock for all three report types, `read:pperm(Admin)`.
   Upstream stores bugs as `read:pperm(Developer)` (`reports.py:249`) and
   ideas as `read:pperm(Builder)` (`:282`), and the staff menu shows only
   the reports its reader passes (`menu.py:57`). The alpha's staff account
   is Admin, so it would open `manage bugs` and see an empty list with no
   error. Developer and superuser pass Admin through the hierarchy. The
   lock is written onto each `Msg` when it is filed, so a change here
   reaches new reports only.

2. Its own cmdset, at priority 2 with mergetype Union, on the account's
   cmdset stack. Character creation is an EvMenu with `auto_quit=False`
   (`world/chargen.py`); the menu's cmdset is priority 1, mergetype
   Replace (`evmenu.py:460-461`), and the cmdhandler merges the account's
   and the puppet's cmdsets in one pool by priority. A command on the
   AccountCmdSet (priority -10) is replaced while the menu is open -- the
   player who is stuck in creation, the one who most needs `bug`, could
   not reach it. Merged last at priority 2, Union adds these four commands
   to whatever is active, menus included, and removes nothing.

The cmdset is added lazily, by `ensure_reports_cmdset()` from
`Account.at_post_login`: an account that predates this module gets it at
its next login, so nothing is backfilled.

Multiplayer: each report is its own `Msg` row, so there is no shared
counter to race. The per-type hub script is created on first use by the
contrib's `_get_report_hub`, inside one command's `func` on the reactor
thread; two commands cannot interleave there.
"""

from evennia.commands.cmdset import CmdSet
from evennia.contrib.base_systems.ingame_reports import reports

# One lock for every type: what the alpha's Admin staff account can read.
STAFF_READ_LOCK = "read:pperm(Admin)"

# Above EvMenu's priority 1 (chargen, `manage`), so Union reaches into menus.
REPORTS_CMDSET_PRIORITY = 2

# The three subclasses change only the lock. No docstrings on purpose: a
# Command subclass without one takes its parent's (`command.py:99-102` at
# v6.1.0), so `help bug` stays upstream's text.


class CmdBug(reports.CmdBug):
    report_locks = STAFF_READ_LOCK


class CmdIdea(reports.CmdIdea):
    report_locks = STAFF_READ_LOCK


class CmdReport(reports.CmdReport):
    report_locks = STAFF_READ_LOCK


class ReportsCmdSet(CmdSet):
    """`bug`, `idea`/`ideas`, `report` and staff's `manage <type>`."""

    key = "PolishedWorld Reports"
    priority = REPORTS_CMDSET_PRIORITY
    mergetype = "Union"

    def at_cmdset_creation(self):
        self.add(CmdBug())
        self.add(CmdIdea())
        self.add(CmdReport())
        self.add(reports.CmdManageReports())


def ensure_reports_cmdset(account):
    """
    Put `ReportsCmdSet` on the account's cmdset stack once.

    Args:
        account (Account): the account that just logged in.

    Returns:
        bool: True if the cmdset was added now, False if it was already there.

    Persistent, so it survives `reload`; the `has` check keeps a second
    login from stacking a second copy (the commands would still resolve,
    but every login would grow the stored path list).
    """
    if account.cmdset.has(ReportsCmdSet):
        return False
    account.cmdset.add(ReportsCmdSet, persistent=True)
    return True
