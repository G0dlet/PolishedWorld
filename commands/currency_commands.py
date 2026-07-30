"""
Player-facing currency commands (Stage 4, Component B).

`wallet` reads a balance (B.1). `pay` (B.2) will follow in this module, and the
admin surface (`@economy`, C.2), the temple faucet (`work`, D.1) and the barter
bridge (E) come later -- none of them are anticipated here.

WHERE THE DIVISION OF LABOUR SITS
---------------------------------
`CurrencyHandler` owns the money, the arithmetic and the invariant. This module
owns the *wording*, the *colour* and the *permission to try*. That split is why
the handler's docstrings say "commands colour their own output" (D2) and why
`parse_amount` returns None instead of raising: every condition a player can
actually be in gets a sentence written here, which leaves the handler's
exceptions reserved for what they are meant to catch -- bugs in calling code.
"""

from evennia import Command


class CmdWallet(Command):
    """
    Check what coin you are carrying

    Usage:
        wallet
        purse

    Shows the coin on your person, largest denomination first. Only you can see
    this.

    What you carry, you carry: there is nowhere else to keep coin, it goes with
    you wherever you go, and if you die it stays with your remains for whoever
    finds them first.
    """

    key = "wallet"
    aliases = ["purse"]
    locks = "cmd:all()"
    help_category = "Economy"

    def func(self):
        """Render the balance. Read-only -- writes nothing, not even lazily."""
        caller = self.caller

        # Defensive in the same shape as CmdStatus's `hasattr(char, 'traits')`.
        # Every Character carries the lazy_property, but a cmdset can be merged
        # onto something that is not one, and a sentence beats a traceback.
        if not hasattr(caller, "currency"):
            caller.msg("You have no way to carry coin.")
            return

        # Local, not a module constant: CmdProgress does exactly this, and the
        # rule belongs to the display rather than to the module.
        rule = "|g" + "=" * 40 + "|n"

        if caller.currency.value == 0:
            # NOT format_copper(0), which renders "nothing". That is right for
            # an amount ("you pay nothing") and wrong for a container -- "you
            # are carrying nothing" reads as inventory. B.1 asks for a distinct
            # empty message and this is why.
            body = "  Your purse is empty."
        else:
            # Label coloured, value plain -- the CmdStatus convention. The value
            # stays uncoloured at source (D2) because format_copper's output
            # also lands in ledger entries and test assertions.
            #
            # A negative balance renders with its sign rather than being hidden
            # or flagged here (D4). It is an invariant violation, `@economy
            # audit` (C.2) is what detects and reports it, and an alarm in the
            # player's purse command would be policy in the one place least able
            # to act on it.
            body = f"  |yCarried:|n {caller.currency.format()}"

        caller.msg(f"\n|wPurse:|n\n{rule}\n{body}\n{rule}")
