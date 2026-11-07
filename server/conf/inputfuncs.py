"""
Input functions

Input functions are always called from the client (they handle server
input, hence the name).

This module is loaded by being included in the
`settings.INPUT_FUNC_MODULES` tuple.

All *global functions* included in this module are considered
input-handler functions and can be called by the client to handle
input.

An input function must have the following call signature:

    cmdname(session, *args, **kwargs)

Where session will be the active session and *args, **kwargs are extra
incoming arguments and keyword properties.

A special command is the "default" command, which is will be called
when no other cmdname matches. It also receives the non-found cmdname
as argument.

    default(session, cmdname, *args, **kwargs)

"""

# def oob_echo(session, *args, **kwargs):
#     """
#     Example echo function. Echoes args, kwargs sent to it.
#
#     Args:
#         session (Session): The Session to receive the echo.
#         args (list of str): Echo text.
#         kwargs (dict of str, optional): Keyed echo text
#
#     """
#     session.msg(oob=("echo", args, kwargs))
#
#
# def default(session, cmdname, *args, **kwargs):
#     """
#     Handles commands without a matching inputhandler func.
#
#     Args:
#         session (Session): The active Session.
#         cmdname (str): The (unmatched) command name
#         args, kwargs (any): Arguments to function.
#
#     """
#     pass


def pw_state(session, *args, **kwargs):
    """
    The webclient asks for every panel's state (WC6): sends all four
    `world.client_state` snapshots to this session only.

    This is the client's pull, for whenever it wants its state again.
    Character.at_post_puppet already pushes all four on every puppet, a
    page reload included: a reload is a new session, and
    Account.puppet_object calls at_post_puppet on every path that ends in
    a puppet (evennia/accounts/accounts.py:554). An `evennia reload` does
    not: ServerSession.at_sync restores the puppet without the hook
    (evennia/server/serversession.py:127), so an open page gets nothing
    new until it asks.

    Sends nothing when the session has no puppet (logged in but OOC).

    The `pw_` prefix keeps this from colliding with a same-named function
    in a later INPUT_FUNC_MODULES entry (settings_default.py:489-491). The
    import is inside the function because every module-level callable
    *defined* here becomes an input function the client can call
    (utils.callables_from_module, utils.py:1492).
    """
    from world.client_state import DOMAINS, push

    puppet = getattr(session, "puppet", None)
    if puppet is None:
        return
    push(puppet, *DOMAINS, session=session)
