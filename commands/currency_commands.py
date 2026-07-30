"""
Player-facing currency commands (Stage 4, Component B).

Two commands: `wallet` reads a balance (B.1), `pay` moves one (B.2). Together
they are the whole player-facing surface onto `world/currency.py` in this stage.
The admin surface (`@economy`, C.2), the temple faucet (`work`, D.1) and the
barter bridge (E) come later and are deliberately not anticipated here.

WHERE THE DIVISION OF LABOUR SITS
---------------------------------
`CurrencyHandler` owns the money, the arithmetic and the invariant. This module
owns the *wording*, the *colour* and the *permission to try*. That split is why
the handler's docstrings say "commands colour their own output" (D2) and why
`parse_amount` returns None instead of raising: every condition a player can
actually be in gets a sentence written here, which leaves the handler's
exceptions reserved for what they are meant to catch -- bugs in calling code.

The practical consequence is that every raising path in `CurrencyHandler` needs
a matching guard in `CmdPay.func()` BEFORE the call, or a player typo surfaces
as a traceback. Those guards are marked in place. If a new raising condition is
ever added to the handler, this file is the other half of that change.

THE ATOMICITY RULE AS IT APPLIES HERE (S4-R1)
---------------------------------------------
`can_afford()` is not called anywhere in this module, and that is deliberate.
`transfer_to()` already performs the read, the sufficiency check, the debit and
the credit as one unbroken synchronous block, returning False -- having touched
nothing -- when the balance does not cover the amount. Calling `can_afford()`
first would be a second read of the same fact, and it would write out the
check-here-commit-there *shape* that S4-R1 exists to forbid. A later editor
looking for somewhere to put a confirmation prompt would find a gap sitting
ready for one. There is no gap if the check never leaves the handler.

Reading the balance AFTER a returned False, in order to say "you only have X",
is a different thing and is safe: reading to phrase is not reading to decide.

⚠️ This is a deliberate deviation from the decomposition's §6/B.2, which sketches
"check affordability, then a single transfer_to". Flagged for the decomp at
Component B close.

NO CONFIRMATION PROMPT
----------------------
Locked this session, after considering one. A yield-based "are you sure?" would
be the first yield point in the codebase, sitting in the one command where the
stage's central race rule applies. Most of the protection it would offer is
already provided by D1: `parse_amount` demands an explicit denomination, so the
dangerous mistake -- meaning Silver and typing a bare number -- is a syntax
error rather than a silent transfer of a hundredth of the intended sum. What
remains is socially recoverable, since there are no NPC vendors and a
misdirected payment is in another player's hands rather than destroyed. Echoing
the rendered amount back to both parties is the cheap version of a confirmation
and is what this module does instead. If playtesting shows people fat-fingering
the denomination, the fix is a threshold constant plus an ndb two-step, never a
yield -> docs/BACKLOG.md.

WHY PAYMENT IS SAME-ROOM, PERMANENTLY
-------------------------------------
Not an MVP shortcut. Coin is carried on the body and stays with the corpse to be
looted, so carrying a lot is a real risk a player chooses to take. A global
`pay` would cancel that risk outright -- empty your pockets remotely before
walking into the forest and the decision costs nothing. The intended answer to
"I don't want to carry this" is a bank or a post office: a *place*, reached by a
journey that can itself go wrong. Remote payment is therefore rejected by
design, not deferred; see docs/BACKLOG.md so no future session reads "deferred"
and builds it.
"""

from evennia import Command

from world.currency import format_copper, parse_amount


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


class CmdPay(Command):
    """
    Hand coin to someone standing with you

    Usage:
        pay <amount> <denomination> to <person>

    Examples:
        pay 5 silver to Bob
        pay 1 g to the innkeeper
        pay 250 copper to Mara

    Coin changes hands where hands can reach: you both have to be in the same
    room. There is no way to send coin to someone elsewhere, and that is the
    point -- what you carry, you carry, with all the risk that implies.

    Always name the denomination. `pay 50 to Bob` is refused rather than guessed
    at: guessing wrong between Copper and Silver is wrong by a factor of a
    hundred, and neither of you would notice until much later.

    Onlookers see that coin changed hands. Only the two of you see how much.
    """

    key = "pay"
    locks = "cmd:all()"
    help_category = "Economy"

    # One string, two callers (empty args, malformed args). A usage line that
    # drifts between two copies is a bug players report as "the help is wrong".
    _USAGE = (
        "Pay what, to whom? (usage: |wpay <amount> <denomination> to <person>|n, "
        "e.g. |wpay 5 silver to Bob|n)"
    )

    def func(self):
        caller = self.caller

        if not hasattr(caller, "currency"):
            caller.msg("You have no coin to pay with.")
            return

        raw = self.args.strip()
        if not raw:
            caller.msg(self._USAGE)
            return

        # rpartition, not partition: split on the LAST " to ", the same choice
        # CmdTeach makes. Today nothing in the amount half can contain " to ",
        # but the target half is a free-form name and the separator belongs
        # next to the thing it separates.
        amount_input, sep, target_name = raw.rpartition(" to ")
        amount_input, target_name = amount_input.strip(), target_name.strip()
        if not sep or not amount_input or not target_name:
            caller.msg(self._USAGE)
            return

        # ⚠️ Amount is parsed BEFORE the target is resolved. The decomposition
        # sketches the other order; this is a deliberate (flagged) swap, and the
        # reason is the validate-then-commit principle the decomp itself cites
        # (Evennia Reference §11.9): caller.search() has a SIDE EFFECT -- it
        # messages the player on a miss or a multimatch. Everything that is pure
        # validation belongs before the first side-effecting call. Concretely,
        # a player who mistypes both halves should be told what is wrong with
        # their amount, not handed "Could not find 'Bpb'" about a target they
        # were never going to reach. Parsing is free and local; there is no
        # reason to touch the world first.
        amount = parse_amount(amount_input)
        if amount is None:
            # D1 meets the player here. parse_amount returns None instead of
            # raising precisely so this sentence lives in the command -- `offer`
            # (E.1) will want to say something different about the same input.
            caller.msg(
                f"'|w{amount_input}|n' isn't an amount of coin I can read. Name the "
                "denomination too, like |w5 silver|n or |w30 copper|n."
            )
            return

        if amount <= 0:
            # parse_amount cannot return a negative -- the digit check rejects a
            # leading minus -- but it CAN return 0, since "0 copper" is a
            # perfectly good parse and simply not a payable amount. The <= keeps
            # this guard total instead of depending on that upstream detail
            # staying true. Without it, transfer_to raises ValueError, which is
            # the right answer for a caller bug and the wrong one for a typo.
            caller.msg("Paying nothing is not a payment.")
            return

        # The same-room rule is enforced by NOT overriding the default: the
        # local candidate set is `self.contents + [location] + location.contents`
        # (verified live against Evennia main, objects/objects.py
        # ::get_search_candidates). Someone in another room -- or inside a
        # container in this one -- is simply not a candidate and resolves as a
        # clean miss, which is the right answer for the vehicles and enterable
        # containers we do not have yet. search() emits its own miss and
        # multimatch messages, so a falsy result here is already fully reported.
        #
        # Known hole, stated rather than assumed away: a #dbref makes the search
        # global BEFORE the use_dbref permission check, so Builder+ can pay
        # across the world. Acceptable -- staff can already move coin with @py.
        target = caller.search(target_name)
        if not target:
            return

        if target == caller:
            # transfer_to raises ValueError on self-payment (D7), where it is a
            # caller bug rather than a player condition. This catch is what
            # keeps that backstop from ever reaching a player as a traceback.
            caller.msg("You move coin from one hand to the other. You are no richer.")
            return

        # NOTE the room ITSELF is in the candidate set, so `pay 1 copper to
        # <room>` reaches this line. This guard is load-bearing, not decorative:
        # transfer_to raises TypeError on a target with no handler (D7).
        if not hasattr(target, "currency"):
            caller.msg(f"{target.get_display_name(caller)} has no use for coin.")
            return

        # has_account is `self.sessions.count()` (verified live), so it is true
        # only while a session is CONNECTED. Under our statue-logout a
        # logged-out body stays standing in the room, which makes it a visible,
        # plausible target -- and paying it would hand over coin with no
        # witness, no notification and no chance to refuse, which is exactly
        # what the room broadcast below exists to prevent. Settling up with
        # someone who just logged out is a fair thing to want; it wants a bank.
        #
        # Kept as a SEPARATE message from the guard above on purpose. CmdTeach
        # folds its two conditions into one line because both mean "not a played
        # character"; here they are different situations -- paying a rock versus
        # paying a sleeping friend -- and one message would be confusing in the
        # case where the target is obviously a person.
        #
        # NOTE for C.1: the Treasury will have a wallet and no account, so it
        # lands here. Correct for Stage 4 -- Treasury funding is an admin action
        # and `donate` was deliberately not claimed (decomp §5). If player
        # donations ever become a feature, this is the guard to revisit.
        if not target.has_account:
            caller.msg(
                f"{target.get_display_name(caller)} is in no state to take coin."
            )
            return

        # ---- S4-R1: the check AND the commit, in one call ----
        # No can_afford above it, nothing between. False means exactly one thing
        # here -- insufficient funds (D7) -- because every other failure mode
        # raises and has been screened out by the guards above.
        # `reason` is not persisted (S4-4); it is here for call-site legibility.
        if not caller.currency.transfer_to(target, amount, reason="pay"):
            # Safe to read now: nothing is being decided on this number, it is
            # only being said. format() renders "nothing" for an empty purse,
            # which reads correctly in this sentence.
            caller.msg(
                "You don't have that much on you; your purse holds "
                f"|y{caller.currency.format()}|n."
            )
            return

        rendered = format_copper(amount)
        caller.msg(f"You pay {target.get_display_name(caller)} |y{rendered}|n.")
        target.msg(f"{caller.get_display_name(target)} pays you |y{rendered}|n.")

        # The room sees the ACT, never the AMOUNT.
        #
        # Silence would make payment unwitnessable, and since transfers are not
        # logged (S4-4) the room is the only evidence layer this design has for
        # "did you pay me?". Broadcasting the figure instead would tell every
        # bystander what the goods were worth and roughly what the payer is
        # carrying, which is real intelligence in a player-driven economy -- the
        # same argument that kept `teach` from probing a student's known set.
        # The house already draws this line: `eat` gives the eater the flavour
        # text and the room only "X eats Y."
        #
        # Guarded on location because an object with no room has nobody to tell,
        # and both parties have already been messaged directly.
        if caller.location:
            caller.location.msg_contents(
                f"{caller.get_display_name()} hands {target.get_display_name()} "
                "some coin.",
                exclude=[caller, target],
            )
